@echo off
REM ============================================
REM Setup Stable Diffusion Models
REM Auto-downloads models from HuggingFace
REM ============================================

echo.
echo ============================================================
echo  Stable Diffusion - Model Setup
echo ============================================================
echo.

cd /d "%~dp0..\services\stable-diffusion"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo [INFO] Install Python 3.10.6 or higher
    pause
    exit /b 1
)

REM Check if huggingface_hub is installed
python -c "import huggingface_hub" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing HuggingFace Hub...
    pip install huggingface_hub
    echo.
)

echo [INFO] Starting model download...
echo.

REM Run setup script
python setup_models.py %*

if errorlevel 1 (
    echo.
    echo [ERROR] Model setup failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Setup Complete!
echo ============================================================
echo.
echo You can now:
echo   1. Start Stable Diffusion: scripts\start-stable-diffusion.bat
echo   2. Use text-to-image in ChatBot
echo   3. Check models: scripts\check-sd-models.bat
echo.
pause
