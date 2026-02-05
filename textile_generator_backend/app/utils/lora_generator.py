

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
    EulerAncestralDiscreteScheduler,
    DPMSolverMultistepScheduler,
    LMSDiscreteScheduler
)
from transformers import CLIPTextModel, CLIPTokenizer
from PIL import Image
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict
import os
from colorsys import rgb_to_hsv, hsv_to_rgb

logger = logging.getLogger(__name__)


def hex_to_color_name(hex_color: str) -> str:
    """Convert hex color to descriptive color name for better prompting"""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Normalize to 0-1
    r_norm, g_norm, b_norm = r/255.0, g/255.0, b/255.0
    
    # Color naming based on hue and brightness
    h, s, v = rgb_to_hsv(r_norm, g_norm, b_norm)
    
    # Return both hex and color name for better prompting
    if v < 0.2:
        return "black"
    elif v > 0.95 and s < 0.1:
        return "white"
    elif s < 0.1:
        return "gray"
    
    h_degrees = h * 360
    
    if h_degrees < 30 or h_degrees >= 330:
        return "red"
    elif 30 <= h_degrees < 60:
        return "orange"
    elif 60 <= h_degrees < 90:
        return "yellow"
    elif 90 <= h_degrees < 150:
        return "green"
    elif 150 <= h_degrees < 210:
        return "cyan"
    elif 210 <= h_degrees < 270:
        return "blue"
    elif 270 <= h_degrees < 330:
        return "purple"
    
    return "colored"



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
            else:
                # Check for adapter_model.safetensors or adapter_config.json
                adapter_file = os.path.join(lora_path, "adapter_model.safetensors")
                config_file = os.path.join(lora_path, "adapter_config.json")
                if os.path.exists(adapter_file):
                    logger.info(f"✓ LoRA adapter found for '{style}': {os.path.getsize(adapter_file) / (1024*1024):.1f}MB")
                elif os.path.exists(config_file):
                    logger.info(f"✓ LoRA config found for '{style}' (weights may be loaded separately)")
                else:
                    missing.append(style)
                    logger.warning(f"No adapter files found in {lora_path}")
        
        if missing:
            logger.warning(f"⚠ Missing or incomplete LoRA adapters for: {', '.join(missing)}")
        else:
            logger.info(f"✓ All LoRA adapters verified for styles: {', '.join(self.available_styles)}")
    
    def verify_models_loaded(self) -> Dict[str, bool]:
        """Verify all models are loaded and working correctly"""
        results = {}
        logger.info("=" * 60)
        logger.info("VERIFYING MODEL LOADING...")
        logger.info("=" * 60)
        
        for style in self.available_styles:
            try:
                logger.info(f"\nVerifying {style.upper()} model...")
                pipeline = self.load_style_pipeline(style)
                
                # Check pipeline components
                checks = {
                    'vae': pipeline.vae is not None,
                    'tokenizer': pipeline.tokenizer is not None,
                    'text_encoder': pipeline.text_encoder is not None,
                    'unet': pipeline.unet is not None,
                    'scheduler': pipeline.scheduler is not None,
                }
                
                all_ok = all(checks.values())
                results[style] = all_ok
                
                for component, ok in checks.items():
                    status = "✓" if ok else "✗"
                    logger.info(f"  {status} {component}: {'loaded' if ok else 'MISSING'}")
                
                # Log LoRA status
                lora_path = os.path.join(self.lora_base_path, f"{style}_lora")
                if os.path.exists(lora_path):
                    logger.info(f"  ✓ LoRA adapter: loaded from {lora_path}")
                else:
                    logger.warning(f"  ⚠ LoRA adapter: NOT FOUND at {lora_path}")
                
                logger.info(f"✓ {style.upper()} model verification: PASS" if all_ok else f"✗ {style.upper()} model verification: FAIL")
                
            except Exception as e:
                results[style] = False
                logger.error(f"✗ {style.upper()} model verification FAILED: {str(e)}")
        
        logger.info("\n" + "=" * 60)
        logger.info("MODEL VERIFICATION COMPLETE")
        logger.info(f"Device: {self.device.upper()}")
        logger.info(f"Data Type: {self.dtype}")
        logger.info("=" * 60 + "\n")
        
        return results
    
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
            
            # Enable memory optimizations for faster inference on limited VRAM
            if self.device == "cuda":
                try:
                    # Enable memory efficient attention (xFormers) - 40% speed improvement
                    pipeline.enable_xformers_memory_efficient_attention()
                    logger.info("✓ xFormers memory efficient attention enabled (40% faster)")
                except Exception as e:
                    logger.warning(f"xFormers not available, falling back to attention slicing: {e}")
                    try:
                        pipeline.enable_attention_slicing()
                        logger.info("✓ Attention slicing enabled")
                    except:
                        pass
                
                try:
                    # Enable VAE tiling for reduced memory usage
                    pipeline.enable_vae_tiling()
                    logger.info("✓ VAE tiling enabled (reduced memory pressure)")
                except Exception as e:
                    logger.warning(f"VAE tiling not available: {e}")
                
                try:
                    # Use faster scheduler - DPM++ Multistep (15-20% faster than Euler)
                    pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
                        pipeline.scheduler.config,
                        use_karras_sigmas=True,
                        algorithm_type="dpmsolver++"
                    )
                    logger.info("✓ DPM++ Multistep scheduler enabled (15-20% faster)")
                except Exception as e:
                    logger.warning(f"Could not set DPM++ scheduler: {e}")
            
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
        """Build optimized prompt for textile pattern generation (within 77 token CLIP limit)"""
        
        # Concise style prefixes
        style_prefixes = {
            'bandhani': "Indian tie-dye pattern",
            'batik': "Indonesian batik pattern",
            'ikat': "double-ikat pattern"
        }
        
        # Concise pattern details
        pattern_details = {
            'bandhani': {
                'leheriya': "wave lines",
                'mothra': "dot grid",
                'ekdali': "clusters dots",
                'shikari': "dense dots",
                'gharchola': "checkered",
            },
            'batik': {
                'parang': "knife motifs",
                'kawung': "palm shapes",
                'mega_mendung': "clouds",
                'truntum': "star flowers",
                'ceplok': "medallions",
            },
            'ikat': {
                'patola': "geometry",
                'pochampally': "rhombus",
                'telia_rumal': "stripes",
                'sambalpuri': "temple motifs",
                'geringsing': "interlocking",
            }
        }
        
        style_key = style.lower()
        base = style_prefixes.get(style_key, f"{style} textile")
        
        # Add pattern detail if specified
        if pattern and style_key in pattern_details:
            pattern_detail = pattern_details[style_key].get(pattern.lower(), "")
            if pattern_detail:
                base += f", {pattern_detail}"
        
        # Build prompt: style, pattern, user input, colors
        parts = [base]
        
        # Add user prompt
        if prompt:
            parts.append(prompt)
        
        # Add colors
        if color_1:
            color_name_1 = hex_to_color_name(color_1)
            parts.append(f"{color_name_1} base")
        if color_2:
            color_name_2 = hex_to_color_name(color_2)
            parts.append(f"{color_name_2} accent")
        
        # Add minimal quality keywords
        parts.append("seamless pattern, crisp, high quality")
        
        full_prompt = ", ".join(parts)
        logger.info(f"Generated prompt for {style}: {full_prompt}")
        return full_prompt
    
    def _build_img2img_prompt(
        self,
        style: str,
        pattern: Optional[str] = None,
        color_1: Optional[str] = None,
        color_2: Optional[str] = None
    ) -> str:
        """Build minimal prompt for img2img (reference image focused, no user prompt)"""
        
        # Concise style prefixes
        style_prefixes = {
            'bandhani': "Indian tie-dye",
            'batik': "batik pattern",
            'ikat': "ikat pattern"
        }
        
        # Minimal pattern details
        pattern_details = {
            'bandhani': {
                'leheriya': "wave",
                'mothra': "dots",
                'ekdali': "clusters",
                'shikari': "dense",
                'gharchola': "checkered",
            },
            'batik': {
                'parang': "motifs",
                'kawung': "shapes",
                'mega_mendung': "clouds",
                'truntum': "flowers",
                'ceplok': "medallions",
            },
            'ikat': {
                'patola': "geometry",
                'pochampally': "rhombus",
                'telia_rumal': "stripes",
                'sambalpuri': "motifs",
                'geringsing': "interlocking",
            }
        }
        
        style_key = style.lower()
        base = style_prefixes.get(style_key, f"{style} textile")
        parts = [base]
        
        # Add pattern detail if specified
        if pattern and style_key in pattern_details:
            pattern_detail = pattern_details[style_key].get(pattern.lower(), "")
            if pattern_detail:
                parts.append(pattern_detail)
        
        # Add colors ONLY (no user prompt)
        if color_1:
            color_name_1 = hex_to_color_name(color_1)
            parts.append(color_name_1)
        if color_2:
            color_name_2 = hex_to_color_name(color_2)
            parts.append(color_name_2)
        
        full_prompt = ", ".join(parts)
        logger.info(f"Generated img2img prompt for {style}: {full_prompt}")
        return full_prompt
    
    def _get_negative_prompt(self) -> str:
        """Get negative prompt to avoid unwanted features (optimized for token limit)"""
        return (
            "blurry, distorted, pixelated, noisy, artifacts, "
            "text, watermark, human, face, people, "
            "photographic, 3d, border, incomplete, "
            "asymmetrical, broken pattern, uneven colors"
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
            
            # Build minimal prompt (colors and style only, ignore user prompt for img2img)
            full_prompt = self._build_img2img_prompt(style, pattern, color_1, color_2)
            negative_prompt = self._get_negative_prompt()
            
            logger.info(f"Generating img2img {style} pattern with strength {strength} (reference image focused)")
            
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
