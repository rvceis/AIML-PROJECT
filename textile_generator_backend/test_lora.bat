@echo off
echo ================================
echo LoRA Generator Test Script
echo ================================
echo.

echo [1/3] Testing model loading...
python test_generator.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Model loading test failed!
    pause
    exit /b 1
)

echo.
echo [2/3] Testing pattern generation (all styles)...
python test_lora_generator.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Pattern generation test failed!
    pause
    exit /b 1
)

echo.
echo [3/3] All tests passed!
echo.
echo Check 'test_outputs' folder for generated images.
echo.
pause
