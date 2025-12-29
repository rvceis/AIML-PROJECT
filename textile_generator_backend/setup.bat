@echo off
REM Setup script for Textile Pattern Generator Backend (Windows)
echo ====================================
echo Textile Pattern Generator - Setup
echo ====================================
echo.

REM Check Python version
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10 or higher
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

echo [4/5] Installing PyTorch with CUDA 11.8 support...
echo This will download ~2.6GB, please wait...
python -m pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 --index-url https://download.pytorch.org/whl/cu118
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install PyTorch with CUDA
    echo Fallback: Installing CPU-only version...
    python -m pip install torch==2.0.1 torchvision==0.15.2
)

echo [5/5] Installing remaining dependencies...
python -m pip install -r requirements.txt

echo.
echo ====================================
echo Setup Complete!
echo ====================================
echo.
echo To verify CUDA is available, run:
echo   venv\Scripts\python.exe -c "import torch; print('CUDA Available:', torch.cuda.is_available())"
echo.
echo To start the server, run:
echo   venv\Scripts\python.exe app.py
echo.
pause
