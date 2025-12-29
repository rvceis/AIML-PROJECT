import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from diffusers import (
    StableDiffusionXLPipeline,
    AutoencoderKL,
    UNet2DConditionModel,
    EulerDiscreteScheduler
)
from transformers import CLIPTextModel, CLIPTextModelWithProjection, CLIPTokenizer
from PIL import Image
import logging
from pathlib import Path
from typing import Optional, Tuple
import os
from app.utils.gpu_config import get_gpu_config

logger = logging.getLogger(__name__)


class CircularConv2d(nn.Module):
    """Wrapper for Conv2d with circular padding for seamless tiling"""
    
    def __init__(self, conv_layer):
        super().__init__()
        self.conv = conv_layer
        
        # Extract padding from original conv layer
        if isinstance(conv_layer.padding, int):
            self.pad_h = self.pad_w = conv_layer.padding
        else:
            self.pad_h, self.pad_w = conv_layer.padding
        
        # Set conv padding to 0 since we'll handle it manually
        self.conv.padding = (0, 0)
    
    def forward(self, x, *args, **kwargs):
        # Apply circular padding
        if self.pad_h > 0 or self.pad_w > 0:
            x = F.pad(x, (self.pad_w, self.pad_w, self.pad_h, self.pad_h), mode='circular')
        
        # Apply convolution with any additional args (like scale parameter)
        return self.conv(x, *args, **kwargs)


class TextileGenerator:
    """SDXL-based textile pattern generator with LoRA and circular padding"""
    
    def __init__(self, 
                 model_id: str = "stabilityai/stable-diffusion-xl-base-1.0",
                 lora_path: Optional[str] = None):
        """
        Initialize the textile pattern generator
        
        Args:
            model_id: HuggingFace model ID for SDXL base
            lora_path: Path to directory containing LoRA adapter weights
        """
        self.model_id = model_id
        self.lora_path = lora_path
        
        # Get GPU configuration
        self.gpu_config = get_gpu_config()
        self.device = self.gpu_config.device
        self.dtype_gpu = self.gpu_config.dtype_optimized
        self.dtype_cpu = torch.float32
        
        self.pipe = None
        self.vae = None
        self.unet = None
        self.text_encoder = None
        self.text_encoder_2 = None
        self.tokenizer = None
        self.tokenizer_2 = None
        self.scheduler = None
        self._is_loaded = False
        
        logger.info(f"TextileGenerator initialized - Device: {self.device}, GPU dtype: {self.dtype_gpu}")
        self.gpu_config.log_device_stats()
    
    def _apply_circular_padding_to_vae(self):
        """Apply circular padding to VAE Conv2D layers for seamless tiling"""
        logger.info("Applying circular padding to VAE for seamless patterns...")
        
        def apply_circular_to_module(module, prefix=''):
            """Recursively apply circular padding to Conv2d layers"""
            conv_count = 0
            
            for name, child in list(module.named_children()):
                if isinstance(child, nn.Conv2d):
                    # Replace Conv2d with CircularConv2d
                    setattr(module, name, CircularConv2d(child))
                    conv_count += 1
                else:
                    # Recursively process child modules
                    conv_count += apply_circular_to_module(child, prefix + name + '.')
            
            return conv_count
        
        total_conv = apply_circular_to_module(self.vae)
        logger.info(f"Applied circular padding to {total_conv} Conv2D layers in VAE")
    
    def load_model(self):
        """Load SDXL base model using the full pipeline for proper VAE handling"""
        if self._is_loaded:
            logger.info("Model already loaded")
            return
        
        try:
            logger.info(f"Loading SDXL pipeline from {self.model_id}...")
            logger.info(f"Target device: {self.device}, Dtype: {self.dtype_gpu}")
            
            # Load the full SDXL pipeline with fp16 fix VAE
            logger.info("Loading SDXL pipeline with fixed VAE...")
            try:
                # Use the fixed VAE variant
                fixed_vae = AutoencoderKL.from_pretrained(
                    "madebyollin/sdxl-vae-fp16-fix",
                    torch_dtype=self.dtype_gpu
                )
                # Load from local cache first, no fp16 variant to avoid large downloads
                self.pipe = StableDiffusionXLPipeline.from_pretrained(
                    self.model_id,
                    vae=fixed_vae,
                    torch_dtype=self.dtype_gpu,
                    use_safetensors=True,
                    local_files_only=True  # Use cached files only
                )
                logger.info("Loaded SDXL pipeline from cache with fixed VAE")
            except:
                # If local cache fails, download without fp16 variant
                logger.info("Cache not found, downloading standard model...")
                self.pipe = StableDiffusionXLPipeline.from_pretrained(
                    self.model_id,
                    torch_dtype=self.dtype_gpu,
                    use_safetensors=True,
                    resume_download=True
                )
                logger.info("Loaded standard SDXL pipeline")
            
            # Move pipeline to device
            self.pipe = self.pipe.to(self.device)
            
            # Load LoRA weights if provided
            # NOTE: LoRA weights need to be in diffusers format, not PEFT format
            # Skipping LoRA loading - use base SDXL model only
            if False and self.lora_path and os.path.exists(self.lora_path):
                logger.info(f"Loading LoRA adapter from {self.lora_path}...")
                try:
                    self.pipe.load_lora_weights(self.lora_path, weight_name="adapter_model.safetensors")
                    logger.info("LoRA adapter loaded successfully")
                except Exception as lora_error:
                    logger.warning(f"Could not load LoRA weights: {lora_error}")
                    logger.info("Continuing with base SDXL model only")
            else:
                logger.info("Using base SDXL model (LoRA disabled)")
            
            # Enable memory optimizations
            if self.device == "cuda":
                try:
                    self.pipe.enable_xformers_memory_efficient_attention()
                    logger.info("xformers memory efficient attention enabled")
                except Exception as e:
                    logger.warning(f"xformers not available: {e}")
                
                # Enable memory-saving features for 4GB GPU
                self.pipe.enable_attention_slicing("auto")
                self.pipe.enable_vae_slicing()
                self.pipe.enable_vae_tiling()
                logger.info("Memory-saving features enabled for low VRAM")
            
            self._is_loaded = True
            self.gpu_config.log_device_stats()
            logger.info("SDXL pipeline loaded successfully")
        
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            self.gpu_config.clear_gpu_cache()
            raise
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._is_loaded
    
    def generate(
        self,
        prompt: str,
        style: str = "block_print",
        color_1: Optional[str] = None,
        color_2: Optional[str] = None,
        num_inference_steps: int = 25,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        image_size: int = 512,
    ) -> Tuple[Image.Image, int]:
        """
        Generate a seamless textile pattern using SDXL pipeline
        
        Args:
            prompt: Text description of the pattern
            style: Textile style (bandhani, ikat, block_print, paisley)
            color_1: Primary color (optional)
            color_2: Secondary color (optional)
            num_inference_steps: Number of denoising steps
            guidance_scale: Classifier-free guidance scale
            seed: Random seed for reproducibility
            image_size: Output image size (default 512x512)
        
        Returns:
            Tuple of (PIL Image, seed used)
        """
        if not self._is_loaded:
            self.load_model()
        
        # Set seed
        if seed is None:
            seed = int(torch.randint(0, 2**31, (1,)).item())
        
        generator = torch.Generator(device=self.device).manual_seed(seed)
        
        # Build enhanced prompt
        full_prompt = self._build_prompt(prompt, style, color_1, color_2)
        negative_prompt = self._get_negative_prompt()
        
        logger.info(f"Generating pattern: {full_prompt[:100]}... (seed: {seed})")
        
        try:
            # Use the pipeline's __call__ method (handles all preprocessing/postprocessing)
            image = self.pipe(
                prompt=full_prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                height=image_size,
                width=image_size,
                generator=generator,
            ).images[0]
            
            # Clear cache
            if self.device == "cuda":
                torch.cuda.empty_cache()
            
            self.gpu_config.log_device_stats()
            logger.info(f"Pattern generated successfully")
            return image, seed
        
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            if self.device == "cuda":
                torch.cuda.empty_cache()
            self.gpu_config.log_device_stats()
            raise
    
    def _build_prompt(
        self,
        base_prompt: str,
        style: str,
        color_1: Optional[str],
        color_2: Optional[str],
    ) -> str:
        """Build enhanced prompt with style and color information"""
        style_descriptions = {
            "bandhani": "traditional Indian tie-dye bandhani dots, circular motifs",
            "ikat": "resist-dyed ikat pattern, blurred edges, woven fabric",
            "block_print": "hand-stamped block print, botanical motifs",
            "paisley": "ornate paisley, teardrop boteh shapes, Persian motifs",
        }
        
        style_desc = style_descriptions.get(style, "textile fabric pattern")
        
        # Concise prompt under 77 tokens
        prompt = f"professional textile design, {base_prompt}, {style_desc}"
        prompt += ", seamless pattern"
        
        if color_1:
            prompt += f", {color_1} color"
        if color_2:
            prompt += f" and {color_2}"
        
        prompt += ", high quality, detailed"
        
        return prompt
    
    def _get_negative_prompt(self) -> str:
        """Get negative prompt for better generation"""
        return (
            "ugly, distorted, blurry, low quality, bad quality, worst quality, "
            "watermark, text, signature, human, face, people, person, figure, "
            "bad proportions, deformed, asymmetrical edges, irregular pattern, "
            "noise, artifacts, jpeg artifacts, pixelated, grainy, "
            "3d render, cgi, cartoon, anime, drawing, sketch, painting, "
            "modern digital art, abstract art, collage, photomontage"
        )
    
    def unload_model(self):
        """Unload model to free memory"""
        if self._is_loaded:
            self.pipe = None
            self.scheduler = None
            self._is_loaded = False
            
            if self.device == "cuda":
                torch.cuda.empty_cache()
            
            self.gpu_config.log_device_stats()
            logger.info("Model unloaded and GPU memory cleared")
