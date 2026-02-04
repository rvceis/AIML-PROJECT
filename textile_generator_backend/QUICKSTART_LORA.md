# Quick Start Guide - LoRA Integration

## Prerequisites

1. **LoRA Models**: Ensure the `textile_loras_trained` folder is present in the parent directory:
   ```
   AIML-FINAL/
   ├── textile_generator_backend/
   └── textile_loras_trained/
       ├── bandhani_lora/
       ├── batik_lora/
       └── ikat_lora/
   ```

2. **Python Environment**: Python 3.8+ with pip

3. **GPU (Recommended)**: NVIDIA GPU with CUDA support for faster generation

## Installation

### 1. Install Dependencies
```bash
cd textile_generator_backend
pip install -r requirements.txt
```

### 2. Optional: Install xformers (for memory optimization)
```bash
pip install xformers
```

## Testing

### Quick Test (Model Loading Only)
```bash
python test_generator.py
```

### Full Test (With Generation)
```bash
python test_generator.py --generate
```

### LoRA-Specific Test
```bash
python test_lora_generator.py
```

This will:
- Test all 3 styles (bandhani, batik, ikat)
- Generate sample images
- Save outputs to `test_outputs/` folder
- Display timing and performance metrics

## Running the Backend

### Option 1: Using quickstart script
```bash
quickstart.bat
```

### Option 2: Manual start
```bash
python app.py
```

The backend will start on `http://localhost:5000`

## API Testing

### 1. Check Health
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

### 2. Test Generation (Quick)
```bash
curl -X POST http://localhost:5000/api/test-generate ^
  -H "Content-Type: application/json" ^
  -d "{\"prompt\": \"vibrant pattern\", \"style\": \"bandhani\"}"
```

### 3. Full Generation (With Auth)
```bash
# First, register a user
curl -X POST http://localhost:5000/api/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": \"test@example.com\", \"password\": \"password123\"}"

# Login to get token
curl -X POST http://localhost:5000/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": \"test@example.com\", \"password\": \"password123\"}"

# Generate pattern (replace <TOKEN> with actual token)
curl -X POST http://localhost:5000/api/generate ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer <TOKEN>" ^
  -d "{\"prompt\": \"vibrant red and gold circular pattern\", \"style\": \"bandhani\", \"color_1\": \"red\", \"color_2\": \"gold\"}"
```

## Frontend Integration

The API is **fully compatible** with the existing frontend. No changes needed!

### Start Backend
```bash
cd textile_generator_backend
python app.py
```

### Start Frontend (in another terminal)
```bash
cd textile_generator_frontend
npm run dev
```

Frontend will be at: `http://localhost:5173`

## Key Differences from SDXL

| Feature | SDXL (Old) | SD v1.5 + LoRA (New) |
|---------|------------|----------------------|
| Image Size | 1024x1024 | 512x512 |
| VRAM Usage | 8-12 GB | 4-6 GB |
| Generation Time | ~10-15s | ~5-10s |
| Model Size | ~7 GB | ~4 GB |
| Style Quality | Generic | Style-specific (fine-tuned) |

## Troubleshooting

### Issue: "LoRA adapter not found"
**Solution**: Verify folder structure:
```bash
cd ..
dir textile_loras_trained
```
You should see 3 folders: bandhani_lora, batik_lora, ikat_lora

### Issue: "CUDA out of memory"
**Solutions**:
1. Close other GPU applications
2. Reduce number of inference steps in frontend
3. Run on CPU (slower): Set `CUDA_VISIBLE_DEVICES=-1`

### Issue: First generation is slow
**Explanation**: First run downloads SD v1.5 model (~4GB) from HuggingFace
**Solution**: Wait for download to complete (one-time only)

### Issue: Import error for 'peft'
**Solution**:
```bash
pip install peft>=0.13.0
```

## Performance Tips

1. **Enable xformers**: Reduces memory usage by ~30%
   ```bash
   pip install xformers
   ```

2. **Adjust inference steps**: 
   - Fast: 20-30 steps
   - Quality: 50 steps (default)
   - Best: 75-100 steps

3. **GPU Memory**: Close other applications using GPU

4. **Cache models**: Models are cached in `~/.cache/huggingface/`

## Verifying Integration

Run this checklist:

- [ ] LoRA folders exist in parent directory
- [ ] Dependencies installed (`pip list | grep peft`)
- [ ] Test script passes (`python test_generator.py`)
- [ ] Backend starts without errors
- [ ] Health check returns `model_loaded: true`
- [ ] Test generation succeeds
- [ ] Frontend connects and generates patterns

## Support

For issues:
1. Check logs in console output
2. Run test scripts for diagnostics
3. Review [LORA_MIGRATION.md](LORA_MIGRATION.md) for detailed information
4. Check HuggingFace cache: `~/.cache/huggingface/`

## Next Steps

1. **Test with Frontend**: Open frontend and generate patterns
2. **Adjust Prompts**: Experiment with different prompts and styles
3. **Monitor Performance**: Check generation times and quality
4. **Production Deploy**: See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
