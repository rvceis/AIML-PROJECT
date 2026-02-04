

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionImg2ImgPipeline,
    AutoencoderKL,
    UNet2DConditionModel,
    DDPMScheduler,
    EulerDiscreteScheduler,
    EulerAncestralDiscreteScheduler
)
from transformers import CLIPTextModel, CLIPTokenizer
from PIL import Image
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict
import os

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
    
    def forward(self, x):
        # Apply circular padding
        if self.pad_h > 0 or self.pad_w > 0:
            x = F.pad(x, (self.pad_w, self.pad_w, self.pad_h, self.pad_h), mode='circular')
        
        # Apply convolution
        return self.conv(x)


class LoRATextileGenerator:
    
    
    def __init__(self, 
                 base_model_id: str = "runwayml/stable-diffusion-v1-5",
                 lora_base_path: Optional[str] = None):
        
        self.base_model_id = base_model_id
        self.lora_base_path = lora_base_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            '..', 'textile_loras_trained'
        )
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.dtype = torch.float16 if self.device == "cuda" else torch.float32
        
        # Model components
        self.base_pipeline = None
        self.current_style = None
        self.loaded_pipelines: Dict[str, StableDiffusionPipeline] = {}
        
        # Available styles
        self.available_styles = ['bandhani', 'batik', 'ikat']
        
        logger.info(f"LoRATextileGenerator initialized - Device: {self.device}, dtype: {self.dtype}")
        logger.info(f"LoRA base path: {self.lora_base_path}")
        
        # Verify LoRA adapters exist
        self._verify_lora_adapters()
    
    def _verify_lora_adapters(self):
        """Verify that LoRA adapter directories exist"""
        missing = []
        for style in self.available_styles:
            lora_path = os.path.join(self.lora_base_path, f"{style}_lora")
            if not os.path.exists(lora_path):
                missing.append(style)
                logger.warning(f"LoRA adapter not found for style '{style}' at: {lora_path}")
        
        if missing:
            logger.warning(f"Missing LoRA adapters for: {', '.join(missing)}")
        else:
            logger.info(f"All LoRA adapters found for styles: {', '.join(self.available_styles)}")
    
    def _apply_circular_padding_to_vae(self, vae):
        """Apply circular padding to VAE Conv2D layers for seamless tiling"""
        logger.info("Applying circular padding to VAE for seamless patterns...")
        
        def apply_circular_to_module(module):
            """Recursively apply circular padding to Conv2d layers"""
            conv_count = 0
            
            for name, child in list(module.named_children()):
                if isinstance(child, nn.Conv2d):
                    # Replace Conv2d with CircularConv2d
                    setattr(module, name, CircularConv2d(child))
                    conv_count += 1
                else:
                    # Recursively process child modules
                    conv_count += apply_circular_to_module(child)
            
            return conv_count
        
        total_conv = apply_circular_to_module(vae)
        logger.info(f"Applied circular padding to {total_conv} Conv2D layers in VAE")
        return vae
    
    def load_style_pipeline(self, style: str):
        """
        Load pipeline for a specific style with its LoRA adapter
        
        Args:
            style: One of 'bandhani', 'batik', 'ikat'
        """
        if style not in self.available_styles:
            raise ValueError(f"Style '{style}' not supported. Available: {', '.join(self.available_styles)}")
        
        # Return if already loaded
        if style in self.loaded_pipelines:
            logger.info(f"Pipeline for '{style}' already loaded")
            self.current_style = style
            return self.loaded_pipelines[style]
        
        logger.info(f"Loading pipeline for style: {style}")
        
        try:
            # Load base pipeline
            logger.info(f"Loading base model: {self.base_model_id}")
            pipeline = StableDiffusionPipeline.from_pretrained(
                self.base_model_id,
                torch_dtype=self.dtype,
                safety_checker=None,  # Disable for textile patterns
                requires_safety_checker=False
            )
            
            # Apply circular padding to VAE for seamless patterns
            pipeline.vae = self._apply_circular_padding_to_vae(pipeline.vae)
            
            # Load LoRA weights
            lora_path = os.path.join(self.lora_base_path, f"{style}_lora")
            
            if os.path.exists(lora_path):
                logger.info(f"Loading LoRA adapter from: {lora_path}")
                pipeline.load_lora_weights(lora_path)
                logger.info(f"LoRA adapter loaded successfully for {style}")
            else:
                logger.warning(f"LoRA adapter not found at {lora_path}, using base model only")
            
            # Move to device
            pipeline = pipeline.to(self.device)
            
            # Enable memory optimizations
            if self.device == "cuda":
                try:
                    # Enable memory efficient attention
                    pipeline.enable_xformers_memory_efficient_attention()
                    logger.info("xformers memory efficient attention enabled")
                except Exception as e:
                    logger.warning(f"xformers not available: {e}")
                
                try:
                    # Enable VAE slicing for lower memory usage
                    pipeline.enable_vae_slicing()
                    logger.info("VAE slicing enabled")
                except Exception as e:
                    logger.warning(f"VAE slicing failed: {e}")
            
            # Cache pipeline
            self.loaded_pipelines[style] = pipeline
            self.current_style = style
            
            logger.info(f"Pipeline loaded successfully for style: {style}")
            return pipeline
        
        except Exception as e:
            logger.error(f"Failed to load pipeline for style '{style}': {str(e)}")
            raise
    
    def unload_style_pipeline(self, style: str):
        """Unload a specific style pipeline to free memory"""
        if style in self.loaded_pipelines:
            del self.loaded_pipelines[style]
            torch.cuda.empty_cache()
            logger.info(f"Unloaded pipeline for style: {style}")
    
    def unload_all_pipelines(self):
        """Unload all pipelines to free memory"""
        self.loaded_pipelines.clear()
        self.current_style = None
        torch.cuda.empty_cache()
        logger.info("Unloaded all pipelines")
    
    def _build_prompt(
        self,
        prompt: str,
        style: str,
        pattern: Optional[str] = None,
        color_1: Optional[str] = None,
        color_2: Optional[str] = None
    ) -> str:
        """Build enhanced prompt for textile pattern generation"""
        
        # Start with style prefix
        full_prompt = f"traditional {style} textile pattern"
        
        # Add pattern details if specified
        if pattern:
            full_prompt += f", {pattern} design"
        
        # Add user prompt
        full_prompt += f", {prompt}"
        
        # Add color information
        color_parts = []
        if color_1:
            color_parts.append(color_1)
        if color_2:
            color_parts.append(color_2)
        
        if color_parts:
            full_prompt += f", {' and '.join(color_parts)} colors"
        
        # Add quality enhancers
        full_prompt += ", high quality, detailed fabric texture, seamless repeating pattern"
        
        return full_prompt
    
    def _get_negative_prompt(self) -> str:
        """Get negative prompt to avoid unwanted features"""
        return (
            "blurry, low quality, distorted, watermark, text, signature, "
            "human, face, people, body parts, photographic, realistic photo, "
            "border, frame, split image"
        )
    
    def generate(
        self,
        prompt: str,
        style: str = "bandhani",
        pattern: Optional[str] = None,
        color_1: Optional[str] = None,
        color_2: Optional[str] = None,
        num_inference_steps: int = 25,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        image_size: int = 512,
    ) -> Tuple[Image.Image, int]:
        """
        Generate a seamless textile pattern using trained LoRA adapter
        
        Args:
            prompt: Text description of the pattern
            style: Textile style - one of 'bandhani', 'batik', 'ikat'
            pattern: Pattern subgroup (optional)
            color_1: Primary color (optional)
            color_2: Secondary color (optional)
            num_inference_steps: Number of denoising steps (default: 50)
            guidance_scale: Classifier-free guidance scale (default: 7.5)
            seed: Random seed for reproducibility
            image_size: Output image size (default: 512x512 for SD v1.5)
        
        Returns:
            Tuple of (PIL Image, seed used)
        """
        # Validate style
        if style not in self.available_styles:
            raise ValueError(f"Style '{style}' not supported. Available: {', '.join(self.available_styles)}")
        
        # Load pipeline for style
        pipeline = self.load_style_pipeline(style)
        
        # Set seed
        if seed is None:
            seed = int(torch.randint(0, 2**31, (1,)).item())
        
        generator = torch.Generator(device=self.device).manual_seed(seed)
        
        # Build enhanced prompt
        full_prompt = self._build_prompt(prompt, style, pattern, color_1, color_2)
        negative_prompt = self._get_negative_prompt()
        
        logger.info(f"Generating {style} pattern: {full_prompt[:100]}... (seed: {seed}, steps: {num_inference_steps})")
        
        try:
            # Generate image
            with torch.no_grad():
                result = pipeline(
                    prompt=full_prompt,
                    negative_prompt=negative_prompt,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    generator=generator,
                    height=image_size,
                    width=image_size
                )
            
            image = result.images[0]
            
            logger.info(f"Successfully generated {style} pattern (size: {image_size}x{image_size})")
            return image, seed
        
        except Exception as e:
            logger.error(f"Failed to generate pattern: {str(e)}")
            raise
    
    def generate_img2img(
        self,
        image: Image.Image,
        prompt: str,
        style: str = "bandhani",
        pattern: Optional[str] = None,
        color_1: Optional[str] = None,
        color_2: Optional[str] = None,
        strength: float = 0.7,
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        image_size: int = 512,
    ) -> Tuple[Image.Image, int]:
        """
        Generate pattern using image-to-image with reference image
        
        Args:
            image: Reference image (PIL Image)
            prompt: Text description
            style: Textile style
            pattern: Pattern subgroup (optional)
            color_1: Primary color (optional)
            color_2: Secondary color (optional)
            strength: How much to transform the reference (0.0-1.0)
            num_inference_steps: Number of denoising steps
            guidance_scale: Classifier-free guidance scale
            seed: Random seed for reproducibility
            image_size: Output image size
        
        Returns:
            Tuple of (PIL Image, seed used)
        """
        # Validate style
        if style not in self.available_styles:
            raise ValueError(f"Style '{style}' not supported. Available: {', '.join(self.available_styles)}")
        
        logger.info(f"Loading img2img pipeline for style: {style}")
        
        try:
            # Load base model
            img2img_pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
                self.base_model_id,
                torch_dtype=self.dtype,
                safety_checker=None,
                requires_safety_checker=False
            )
            
            # Apply circular padding
            img2img_pipeline.vae = self._apply_circular_padding_to_vae(img2img_pipeline.vae)
            
            # Load LoRA
            lora_path = os.path.join(self.lora_base_path, f"{style}_lora")
            if os.path.exists(lora_path):
                img2img_pipeline.load_lora_weights(lora_path)
                logger.info(f"LoRA loaded for img2img: {style}")
            
            img2img_pipeline = img2img_pipeline.to(self.device)
            
            # Enable optimizations
            if self.device == "cuda":
                try:
                    img2img_pipeline.enable_xformers_memory_efficient_attention()
                    img2img_pipeline.enable_vae_slicing()
                except:
                    pass
            
            # Prepare reference image
            ref_image = image.convert('RGB').resize((image_size, image_size), Image.Resampling.LANCZOS)
            
            # Set seed
            if seed is None:
                seed = int(torch.randint(0, 2**31, (1,)).item())
            
            generator = torch.Generator(device=self.device).manual_seed(seed)
            
            # Build prompt
            full_prompt = self._build_prompt(prompt, style, pattern, color_1, color_2)
            negative_prompt = self._get_negative_prompt()
            
            logger.info(f"Generating img2img {style} pattern with strength {strength}")
            
            # Generate
            with torch.no_grad():
                result = img2img_pipeline(
                    prompt=full_prompt,
                    negative_prompt=negative_prompt,
                    image=ref_image,
                    strength=strength,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    generator=generator
                )
            
            output_image = result.images[0]
            
            # Clean up
            del img2img_pipeline
            torch.cuda.empty_cache()
            
            logger.info(f"Successfully generated img2img {style} pattern")
            return output_image, seed
        
        except Exception as e:
            logger.error(f"Failed to generate img2img pattern: {str(e)}")
            raise
    
    def is_loaded(self) -> bool:
        """Check if any pipeline is loaded"""
        return len(self.loaded_pipelines) > 0
    
    def get_loaded_styles(self) -> list:
        """Get list of currently loaded styles"""
        return list(self.loaded_pipelines.keys())
