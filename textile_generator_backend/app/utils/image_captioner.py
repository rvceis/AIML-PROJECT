"""Image captioning using BLIP model for reference image understanding"""
import torch
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import logging
from typing import Optional
from app.utils.gpu_config import get_gpu_config

logger = logging.getLogger(__name__)


class ImageCaptioner:
    """BLIP-based image captioner for generating prompts from reference images"""
    
    def __init__(self, model_id: str = "Salesforce/blip-image-captioning-base"):
        """
        Initialize the image captioner
        
        Args:
            model_id: HuggingFace model ID for BLIP
        """
        self.model_id = model_id
        self.gpu_config = get_gpu_config()
        self.device = self.gpu_config.device
        self.dtype = self.gpu_config.dtype_optimized
        
        self.processor = None
        self.model = None
        self._is_loaded = False
        
        logger.info(f"ImageCaptioner initialized - Device: {self.device}")
    
    def load_model(self):
        """Load BLIP model for image captioning with extended timeout"""
        if self._is_loaded:
            logger.info("Captioning model already loaded")
            return
        
        try:
            logger.info(f"Loading BLIP captioning model from {self.model_id}...")
            logger.info("This may take several minutes on first download (~1GB)")
            
            # Set longer timeout for slow connections
            import os
            os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '600'  # 10 minutes
            
            # Load processor first (small, fast)
            logger.info("Downloading processor config...")
            self.processor = BlipProcessor.from_pretrained(
                self.model_id,
                resume_download=True,
                force_download=False,
                local_files_only=False
            )
            logger.info("Processor loaded")
            
            # Load model weights (large, slow)
            logger.info("Downloading model weights (~990MB)... Please wait, do not interrupt")
            self.model = BlipForConditionalGeneration.from_pretrained(
                self.model_id,
                torch_dtype=self.dtype,
                resume_download=True,
                force_download=False,
                local_files_only=False,
                low_cpu_mem_usage=True
            ).to(self.device)
            logger.info("Model weights loaded successfully")
            
            self.model.eval()  # Set to evaluation mode
            
            self._is_loaded = True
            logger.info("BLIP captioning model ready for use")
            
        except Exception as e:
            logger.error(f"Failed to load captioning model: {str(e)}")
            logger.warning("Reference image captioning will not be available")
            raise
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._is_loaded
    
    def caption_image(
        self,
        image: Image.Image,
        max_length: int = 50,
        num_beams: int = 4,
        prompt_prefix: str = "a textile pattern with"
    ) -> str:
        """
        Generate a caption/prompt from a reference image
        
        Args:
            image: PIL Image to caption
            max_length: Maximum length of generated caption
            num_beams: Number of beams for beam search
            prompt_prefix: Prefix to add to the generated caption
        
        Returns:
            Generated caption string
        """
        if not self._is_loaded:
            self.load_model()
        
        try:
            # Preprocess image
            inputs = self.processor(image, return_tensors="pt").to(self.device)
            
            # Generate caption
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=num_beams,
                    early_stopping=True
                )
            
            # Decode caption
            caption = self.processor.decode(outputs[0], skip_special_tokens=True)
            
            # Add textile-specific context
            enhanced_caption = f"{prompt_prefix} {caption}"
            
            logger.info(f"Generated caption: {enhanced_caption}")
            return enhanced_caption
            
        except Exception as e:
            logger.error(f"Failed to caption image: {str(e)}")
            raise
    
    def unload_model(self):
        """Unload model to free memory"""
        if self._is_loaded:
            self.model = None
            self.processor = None
            self._is_loaded = False
            self.gpu_config.clear_gpu_cache()
            logger.info("Captioning model unloaded")


# Global captioner instance
_captioner = None


def get_image_captioner() -> ImageCaptioner:
    """Get or create the global image captioner instance"""
    global _captioner
    if _captioner is None:
        _captioner = ImageCaptioner()
    return _captioner
