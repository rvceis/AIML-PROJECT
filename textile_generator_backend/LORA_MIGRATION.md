# LoRA Model Integration

## Overview
The backend has been updated to use **Stable Diffusion v1.5 with trained LoRA adapters** instead of SDXL. This provides better results for textile pattern generation with style-specific fine-tuned models.

## Changes Made

### 1. New LoRA Generator (`app/utils/lora_generator.py`)
- **Base Model**: `runwayml/stable-diffusion-v1-5`
- **LoRA Adapters**: Three trained adapters for different styles:
  - `bandhani_lora` - Traditional tie-dye patterns
  - `batik_lora` - Wax-resist dyeing technique
  - `ikat_lora` - Resist-dyed textile patterns
- **Features**:
  - Circular padding for seamless patterns
  - Style-specific LoRA loading
  - Memory optimization for GPU
  - Support for text-to-image and image-to-image generation

### 2. Updated Configuration (`config.py`)
```python
# Old (SDXL-based)
IMAGE_SIZE = 1024
SDXL_MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"

# New (SD v1.5 + LoRA)
IMAGE_SIZE = 512
BASE_MODEL_ID = "runwayml/stable-diffusion-v1-5"
LORA_BASE_PATH = "../textile_loras_trained"
```

### 3. Updated Route Handler (`app/routes/generation.py`)
- Replaced `TextileGenerator` with `LoRATextileGenerator`
- Automatically loads correct LoRA adapter based on requested style
- No changes to API interface (frontend compatible)

## Model Files

The trained LoRA models are located in:
```
textile_loras_trained/
├── bandhani_lora/
│   ├── adapter_config.json
│   └── adapter_model.safetensors
├── batik_lora/
│   ├── adapter_config.json
│   └── adapter_model.safetensors
├── ikat_lora/
│   ├── adapter_config.json
│   └── adapter_model.safetensors
└── training_summary.json
```

### Training Details
- **Base Model**: Stable Diffusion v1.5
- **Training**: 4 epochs per style
- **LoRA Rank**: 16
- **LoRA Alpha**: 32
- **Resolution**: 512x512
- **Training Date**: February 4, 2026

## API Compatibility

### ✅ No Frontend Changes Required

The API endpoints remain the same:

**POST /api/generate**
```json
{
  "prompt": "vibrant red and gold with circular dots",
  "style": "bandhani",
  "pattern": "mothra",
  "color_1": "red",
  "color_2": "gold",
  "seed": 42
}
```

**Response**
```json
{
  "generation": {
    "id": 123,
    "status": "processing",
    "prompt": "...",
    "style": "bandhani"
  }
}
```

## Performance

### Memory Usage
- **SD v1.5 + LoRA**: ~4-6 GB VRAM
- **Previous SDXL**: ~8-12 GB VRAM

### Generation Speed
- **Steps**: 50 (default)
- **Time**: ~5-10 seconds per image (on GPU)
- **Quality**: Higher for textile-specific patterns due to fine-tuning

## Testing

### Test Generation
```bash
curl -X POST http://localhost:5000/api/test-generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "vibrant red and gold circular pattern",
    "style": "bandhani"
  }'
```

### Check Health
```bash
curl http://localhost:5000/api/health
```

### Generate Pattern
```bash
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "prompt": "intricate floral design with blue and white",
    "style": "batik",
    "pattern": "floral_batik",
    "color_1": "blue",
    "color_2": "white"
  }'
```

## Migration Notes

### Before Starting Backend
1. **Ensure LoRA models are present**:
   ```
   textile_loras_trained/
   ├── bandhani_lora/
   ├── batik_lora/
   └── ikat_lora/
   ```

2. **Install dependencies** (if not already):
   ```bash
   pip install peft>=0.13.0
   pip install diffusers>=0.30.0
   pip install transformers>=4.45.0
   ```

3. **Verify CUDA** (for GPU acceleration):
   ```bash
   python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
   ```

### Rollback to SDXL (if needed)
To revert to the previous SDXL-based generator:

1. In `app/routes/generation.py`:
   ```python
   from app.utils.generator import TextileGenerator
   generator = TextileGenerator()
   ```

2. In `config.py`:
   ```python
   IMAGE_SIZE = 1024
   SDXL_MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
   ```

## Advantages of LoRA Integration

1. **Style-Specific Quality**: Each style has a dedicated fine-tuned model
2. **Lower Memory**: SD v1.5 uses less VRAM than SDXL
3. **Faster Generation**: Smaller model = faster inference
4. **Seamless Patterns**: Circular padding ensures tileable textures
5. **Specialized Training**: Models trained on 3000+ samples per style

## Troubleshooting

### Error: "LoRA adapter not found"
- Ensure `textile_loras_trained` folder is in the correct location
- Check that all three style folders exist with `adapter_model.safetensors`

### Error: "CUDA out of memory"
- Try running on CPU (slower but works)
- Reduce batch size in generation
- Close other GPU-intensive applications

### Error: "Module 'peft' not found"
```bash
pip install peft>=0.13.0
```

### Slow Generation
- First load downloads SD v1.5 model (~4GB)
- Subsequent generations are faster
- Enable xformers for memory efficiency:
  ```bash
  pip install xformers
  ```

## Support

For issues or questions:
1. Check logs: `logs/app.log`
2. Test with: `python testapi.bat` or `test_generator.py`
3. Review training notebook: `textile-last.ipynb`
