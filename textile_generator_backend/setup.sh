#!/bin/bash
# Setup script for Textile Pattern Generator Backend (Linux/Mac)

echo "===================================="
echo "Textile Pattern Generator - Setup"
echo "===================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

echo "[1/5] Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to create virtual environment"
    exit 1
fi

echo "[2/5] Activating virtual environment..."
source venv/bin/activate

echo "[3/5] Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel

echo "[4/5] Installing PyTorch with CUDA 11.8 support..."
echo "This will download ~2.6GB, please wait..."
python -m pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 --index-url https://download.pytorch.org/whl/cu118
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install PyTorch with CUDA"
    echo "Fallback: Installing CPU-only version..."
    python -m pip install torch==2.0.1 torchvision==0.15.2
fi

echo "[5/5] Installing remaining dependencies..."
python -m pip install -r requirements.txt

echo ""
echo "===================================="
echo "Setup Complete!"
echo "===================================="
echo ""
echo "To verify CUDA is available, run:"
echo "  ./venv/bin/python -c \"import torch; print('CUDA Available:', torch.cuda.is_available())\""
echo ""
echo "To start the server, run:"
echo "  ./venv/bin/python app.py"
echo ""
