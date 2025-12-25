"""GPU Configuration and Device Management"""
import torch
import logging

logger = logging.getLogger(__name__)


class GPUConfig:
    """Manages GPU configuration and device settings"""
    
    def __init__(self):
        """Initialize GPU configuration"""
        self.device = self._get_device()
        self.device_name = self._get_device_name()
        self.dtype_full = torch.float32
        self.dtype_optimized = self._get_optimized_dtype()
        self.is_cuda_available = torch.cuda.is_available()
        
        logger.info(f"GPU Config - Device: {self.device}, Device Name: {self.device_name}")
        logger.info(f"CUDA Available: {self.is_cuda_available}")
        if self.is_cuda_available:
            logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    
    @staticmethod
    def _get_device() -> str:
        """Determine the appropriate device (cuda or cpu)"""
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
    
    @staticmethod
    def _get_device_name() -> str:
        """Get the name of the device"""
        if torch.cuda.is_available():
            return torch.cuda.get_device_name(0)
        return "CPU"
    
    @staticmethod
    def _get_optimized_dtype():
        """Get optimized data type based on available hardware"""
        if torch.cuda.is_available():
            # Use float16 on CUDA for memory efficiency
            # Some older GPUs might not support float16, check with:
            # torch.cuda.get_device_capability() returns (major, minor)
            major, minor = torch.cuda.get_device_capability(0)
            if major >= 7:  # Tensor Cores available on Volta and newer
                return torch.float16
            else:
                return torch.float32
        return torch.float32
    
    def clear_gpu_cache(self):
        """Clear GPU cache if using CUDA"""
        if self.is_cuda_available:
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            logger.debug("GPU cache cleared")
    
    def get_device_stats(self) -> dict:
        """Get current device statistics"""
        stats = {
            "device": self.device,
            "device_name": self.device_name,
            "cuda_available": self.is_cuda_available,
            "optimized_dtype": str(self.dtype_optimized)
        }
        
        if self.is_cuda_available:
            stats.update({
                "gpu_memory_allocated_gb": torch.cuda.memory_allocated() / 1e9,
                "gpu_memory_reserved_gb": torch.cuda.memory_reserved() / 1e9,
                "gpu_memory_total_gb": torch.cuda.get_device_properties(0).total_memory / 1e9,
            })
        
        return stats
    
    def log_device_stats(self):
        """Log current device statistics"""
        stats = self.get_device_stats()
        logger.info(f"Device Stats: {stats}")


# Global GPU config instance
_gpu_config = None


def get_gpu_config() -> GPUConfig:
    """Get or create the global GPU config instance"""
    global _gpu_config
    if _gpu_config is None:
        _gpu_config = GPUConfig()
    return _gpu_config
