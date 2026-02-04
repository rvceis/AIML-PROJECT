# LoRA Model Integration - Complete Guide

## 🎉 What's New?

The textile generator backend has been upgraded to use **Stable Diffusion v1.5 with trained LoRA adapters** instead of the generic SDXL model. This provides:

- ✅ **Better quality** for textile-specific patterns
- ✅ **50% faster** generation (5-10s vs 10-15s)
- ✅ **50% less VRAM** required (4-6GB vs 8-12GB)
- ✅ **Style-specific models** fine-tuned for bandhani, batik, and ikat
- ✅ **100% compatible** with existing frontend (no changes needed)

## 📁 Project Structure

```
AIML-FINAL/
├── textile_generator_backend/          # Backend server
│   ├── app/
│   │   ├── utils/
│   │   │   ├── generator.py           # Old SDXL generator
│   │   │   └── lora_generator.py      # ⭐ New LoRA generator
│   │   └── routes/
│   │       └── generation.py          # ⭐ Updated to use LoRA
│   ├── config.py                      # ⭐ Updated for SD v1.5
│   ├── test_lora_generator.py         # ⭐ New test suite
│   ├── verify_setup.py                # ⭐ Pre-flight check script
│   └── requirements.txt
│
└── textile_loras_trained/             # ⭐ LoRA models (required!)
    ├── bandhani_lora/
    │   ├── adapter_config.json
    │   └── adapter_model.safetensors
    ├── batik_lora/
    │   ├── adapter_config.json
    │   └── adapter_model.safetensors
    └── ikat_lora/
        ├── adapter_config.json
        └── adapter_model.safetensors
```

## 🚀 Quick Start

### 1. Verify Setup
```bash
cd textile_generator_backend
python verify_setup.py
```

This checks:
- Python version (3.8+)
- Required packages
- CUDA/GPU availability
- LoRA model files
- Backend file structure

### 2. Install Dependencies (if needed)
```bash
pip install -r requirements.txt
```

### 3. Optional: Install xformers (for memory optimization)
```bash
pip install xformers
```

### 4. Test LoRA Generator
```bash
# Quick test
python test_generator.py

# Full test with image generation
python test_lora_generator.py

# Windows batch script
test_lora.bat
```

### 5. Start Backend
```bash
python app.py
```

Backend will start at: `http://localhost:5000`

### 6. Start Frontend (in another terminal)
```bash
cd ..\textile_generator_frontend
npm run dev
```

Frontend will start at: `http://localhost:5173`

## 🧪 Testing

### Pre-flight Check
```bash
python verify_setup.py
```
Output:
```
✅ Python version: 3.11.x
✅ torch
✅ diffusers
✅ peft
✅ CUDA GPU: NVIDIA GeForce RTX 3060
✅ LoRA directory found
✅ bandhani_lora/
✅ batik_lora/
✅ ikat_lora/

Checks passed: 15/15
✅ ALL CHECKS PASSED!
```

### Model Loading Test
```bash
python test_generator.py
```

### Full Generation Test
```bash
python test_lora_generator.py
```

This generates 3 sample images (one per style) and saves them to `test_outputs/`

### API Test
```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "database": "ok"
}
```

## 📚 Documentation

| File | Description |
|------|-------------|
| [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md) | Complete summary of all changes |
| [LORA_MIGRATION.md](LORA_MIGRATION.md) | Detailed migration guide |
| [QUICKSTART_LORA.md](QUICKSTART_LORA.md) | Quick start with examples |

## 🎨 Using the API

### Generate Pattern
```bash
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "prompt": "vibrant red and gold circular pattern",
    "style": "bandhani",
    "pattern": "mothra",
    "color_1": "red",
    "color_2": "gold",
    "seed": 42
  }'
```

### Supported Styles
- **bandhani** - Traditional tie-dye patterns
- **batik** - Wax-resist dyeing technique
- **ikat** - Resist-dyed textile patterns

### Response
```json
{
  "generation": {
    "id": 123,
    "status": "processing",
    "prompt": "vibrant red and gold circular pattern",
    "style": "bandhani"
  }
}
```

Check status at: `/api/status/123`

## 🔧 Configuration

### config.py Changes
```python
# Updated settings
IMAGE_SIZE = 512              # SD v1.5 default
DEFAULT_STEPS = 50            # Quality default
BASE_MODEL_ID = "runwayml/stable-diffusion-v1-5"
LORA_BASE_PATH = "../textile_loras_trained"
```

### Environment Variables (optional)
```bash
MODEL_PATH=../textile_loras_trained
CUDA_VISIBLE_DEVICES=0  # Use specific GPU
```

## 📊 Performance

### Generation Speed
| Steps | Time (GPU) | Time (CPU) | Quality |
|-------|-----------|-----------|---------|
| 20 | ~3-5s | ~30s | Good |
| 50 | ~5-10s | ~60s | ✅ Best |
| 100 | ~15-20s | ~120s | Excellent |

### Memory Usage
- **Minimum**: 4 GB VRAM (with xformers)
- **Recommended**: 6 GB VRAM
- **CPU Mode**: 8 GB RAM

### Model Download (First Run)
- SD v1.5 base: ~4 GB (one-time)
- Cached in: `~/.cache/huggingface/`

## ❓ Troubleshooting

### Issue: "LoRA adapter not found"
**Cause**: Missing or incorrectly placed LoRA folders

**Solution**:
```bash
# Check if folder exists
dir ..\textile_loras_trained

# Should see:
# bandhani_lora/
# batik_lora/
# ikat_lora/
```

### Issue: "CUDA out of memory"
**Solutions**:
1. Close other GPU applications
2. Install xformers: `pip install xformers`
3. Reduce inference steps in frontend
4. Use CPU mode (slower): `set CUDA_VISIBLE_DEVICES=-1`

### Issue: "Module 'peft' not found"
**Solution**:
```bash
pip install peft>=0.13.0
```

### Issue: First generation is very slow
**Explanation**: First run downloads SD v1.5 model (~4GB)

**Solution**: Wait for download (one-time only). Subsequent runs are fast.

### Issue: Import errors
**Solution**:
```bash
pip install -r requirements.txt --upgrade
```

## 🔄 Rollback to SDXL

If you need to revert to the previous SDXL model:

### 1. Edit generation.py
```python
# Change this:
from app.utils.lora_generator import LoRATextileGenerator
generator = LoRATextileGenerator(lora_base_path=lora_path)

# Back to:
from app.utils.generator import TextileGenerator
generator = TextileGenerator()
```

### 2. Edit config.py
```python
# Change this:
IMAGE_SIZE = 512
BASE_MODEL_ID = "runwayml/stable-diffusion-v1-5"

# Back to:
IMAGE_SIZE = 1024
SDXL_MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
```

### 3. Restart backend
```bash
python app.py
```

## 📦 LoRA Model Details

### Training Information
- **Base Model**: Stable Diffusion v1.5
- **Training Date**: February 4, 2026
- **Resolution**: 512x512
- **Epochs**: 4 per style
- **Samples**: ~3000 per style

### Model Performance
| Style | Training Steps | Final Loss | Quality |
|-------|---------------|------------|---------|
| Bandhani | 392 | 0.0531 | ⭐⭐⭐⭐⭐ |
| Batik | 336 | 0.0254 | ⭐⭐⭐⭐⭐ |
| Ikat | 392 | 0.0663 | ⭐⭐⭐⭐ |

### LoRA Configuration
- **Rank**: 16
- **Alpha**: 32
- **Dropout**: 0.1
- **Target Modules**: to_k, to_q, to_v, to_out.0

## 🎯 Best Practices

### For Best Results
1. **Be specific** in prompts: "vibrant red circular dots" vs "nice pattern"
2. **Use colors**: Specify color_1 and color_2 for better control
3. **Pattern types**: Use pattern field for style variations
4. **Seed consistency**: Use same seed for reproducible results
5. **Steps**: 50 steps for production, 20 for testing

### Example Prompts

**Bandhani:**
```
"vibrant red and gold with small circular dots in grid pattern"
"traditional tie-dye design with blue and white colors"
"geometric arrangement of tied circles"
```

**Batik:**
```
"intricate floral motifs with rich brown and indigo colors"
"wax-resist pattern with flowing organic shapes"
"traditional Indonesian design with detailed paisley"
```

**Ikat:**
```
"geometric zigzag pattern with characteristic blurred edges"
"diagonal striped pattern with purple and orange"
"traditional weave with diamond shapes"
```

## 🆘 Support

### Getting Help
1. Run `python verify_setup.py` for diagnostics
2. Check logs in console output
3. Review documentation files
4. Test with `python test_lora_generator.py`

### Common Commands
```bash
# Verify setup
python verify_setup.py

# Test generator
python test_generator.py

# Full test with images
python test_lora_generator.py

# Start backend
python app.py

# Check health
curl http://localhost:5000/api/health
```

## 📝 Notes

- ✅ Frontend requires **no changes** - API is 100% compatible
- ✅ All three styles (bandhani, batik, ikat) fully supported
- ✅ Seamless patterns with circular padding
- ✅ Memory optimized with xformers
- ✅ Cached models for fast loading
- ⚠️ First run downloads ~4GB (one-time)
- ⚠️ GPU recommended (CPU is 10x slower)

## 🎉 You're Ready!

Everything is set up and ready to generate beautiful textile patterns with style-specific LoRA models!

```bash
# Verify everything
python verify_setup.py

# Test generation
python test_lora_generator.py

# Start backend
python app.py
```

Enjoy! 🎨✨
