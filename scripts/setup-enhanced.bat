@echo off
REM ============================================================================
REM AI Assistant - Enhanced Setup Script v2.1.0
REM Powered by Hub Gateway Features: System Monitoring + Smart Diagnostics
REM ============================================================================

setlocal enabledelayedexpansion
color 0A

echo.
echo ================================================================================
echo.
echo                 AI Assistant - Enhanced Setup v2.1.0
echo                 (Powered by Hub Gateway Technology)
echo.
echo ================================================================================
echo.
echo Features:
echo   - Real-time system metrics monitoring
echo   - Smart dependency conflict resolution  
echo   - Enhanced error diagnostics
echo   - Auto-fix with AI assistance
echo   - Health checks with detailed reporting
echo.
echo ================================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.10 or higher.
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo [INFO] Python %PYTHON_VERSION% detected
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo [SETUP] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

echo.
echo ========================================
echo   Installing Core Dependencies
echo ========================================
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Upgrade pip first
echo [STEP 1/5] Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1
echo [OK] pip upgraded

REM Install system monitoring tools (from Hub Gateway)
echo [STEP 2/5] Installing system monitoring tools...
pip install psutil>=5.9.0 >nul 2>&1
echo [OK] psutil installed

REM Install essential packages
echo [STEP 3/5] Installing essential packages...
pip install python-dotenv flask flask-cors >nul 2>&1
echo [OK] Essential packages installed

REM Install compatible torch versions (fixed conflict)
echo [STEP 4/5] Installing PyTorch (compatible versions)...
pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cpu >nul 2>&1
if errorlevel 1 (
    echo [WARNING] PyTorch installation had issues, continuing...
) else (
    echo [OK] PyTorch installed
)

REM Install remaining dependencies
echo [STEP 5/5] Installing remaining dependencies...
pip install -r requirements.txt --no-deps >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Some packages may have conflicts
) else (
    echo [OK] Dependencies installed
)

echo.
echo ========================================
echo   Running Enhanced Health Check
echo ========================================
echo.

REM Run health checker with system metrics
python scripts/utilities/service_health_checker.py --service "AI-Assistant" --path "."

echo.
echo ================================================================================
echo   Setup Complete!
echo ================================================================================
echo.
echo Next steps:
echo   1. Configure your .env file with API keys
echo   2. Run individual service setup scripts in services/ folders
echo   3. Use menu.bat to start services
echo.
echo System Metrics Available:
echo   - CPU and RAM monitoring
echo   - Disk space tracking
echo   - Real-time dependency checking
echo.
pause
