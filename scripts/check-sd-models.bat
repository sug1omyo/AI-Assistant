@echo off
REM ============================================
REM Check Stable Diffusion Models
REM Lists downloaded models and their sizes
REM ============================================

echo.
echo ============================================================
echo  Stable Diffusion - Model Check
echo ============================================================
echo.

cd /d "%~dp0..\services\stable-diffusion"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

REM Run check
python setup_models.py --check

echo.
pause
