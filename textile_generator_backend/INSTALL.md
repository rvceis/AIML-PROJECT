# Textile Pattern Generator - Backend Setup Guide

## Quick Setup (Recommended)

### Windows
```bash
setup.bat
```

### Linux/Mac
```bash
chmod +x setup.sh
./setup.sh
```

The setup script will:
1. Create a virtual environment
2. Install PyTorch with CUDA 11.8 support (or CPU version as fallback)
3. Install all required dependencies
4. Verify installation

## Manual Setup

If you prefer to set up manually:

### 1. Create Virtual Environment
```bash
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Install PyTorch with CUDA Support

**For NVIDIA GPU (CUDA 11.8):**
```bash
pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 --index-url https://download.pytorch.org/whl/cu118
```

**For CPU only:**
```bash
pip install torch==2.0.1 torchvision==0.15.2
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Verify CUDA Installation
```bash
python -c "import torch; print('CUDA Available:', torch.cuda.is_available())"
```

## Running the Application

### Using Virtual Environment (Windows)
```bash
venv\Scripts\python.exe app.py
```

### Using Virtual Environment (Linux/Mac)
```bash
./venv/bin/python app.py
```

### After Activation
```bash
python app.py
```

The server will start at `http://localhost:8000`

## Requirements

- **Python:** 3.10 or higher
- **GPU (Optional but Recommended):** NVIDIA GPU with CUDA 11.8
- **RAM:** Minimum 8GB (16GB recommended for GPU)
- **Disk Space:** ~10GB for models and dependencies

## Key Dependencies

- `torch==2.0.1+cu118` - PyTorch with CUDA support
- `transformers==4.35.2` - Hugging Face transformers
- `diffusers==0.21.4` - Stable Diffusion pipelines
- `Flask==2.3.3` - Web framework
- `Pillow==10.1.0` - Image processing
- Additional dependencies in `requirements.txt`

## New Features

### Reference Image Support
Upload a reference image to generate patterns inspired by it. The system uses BLIP (Salesforce/blip-image-captioning-base) to automatically generate descriptive prompts from your images.

**Configuration:**
By default, captioning is **disabled** to avoid network timeouts during BLIP model downloads. To enable:

In `config.py`:
```python
CAPTIONING_ENABLED = True  # Enable BLIP captioning
CAPTIONING_LOCAL_ONLY = False  # Allow network downloads
```

Or via environment variables:
```env
CAPTIONING_ENABLED=true
CAPTIONING_LOCAL_ONLY=false
```

**Behavior:**
- When **disabled**: Backend ignores reference images and uses only text prompts
- When **enabled**: Backend downloads BLIP model (~1GB) on first use and generates captions from reference images
- When **local-only**: Backend only uses cached BLIP weights (no network access)

**API Endpoint:**
```
POST /api/caption-image
```
Returns 503 when captioning is disabled.

## Troubleshooting

### CUDA Not Available
If CUDA shows as unavailable:
1. Ensure NVIDIA drivers are installed
2. Install CUDA Toolkit 11.8
3. Reinstall PyTorch with CUDA support

### Out of Memory Errors
- Reduce image size
- Lower num_inference_steps
- Use CPU instead of GPU for testing

### Module Import Errors
```bash
pip install -r requirements.txt --force-reinstall
```

## Environment Variables

Create a `.env` file:
```env
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///textile_generator.db
```

## Support

For issues or questions, refer to the main project documentation.
