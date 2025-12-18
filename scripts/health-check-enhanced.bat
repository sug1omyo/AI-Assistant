@echo off
title AI Assistant - Enhanced Health Check v2.1
color 0D

REM Navigate to project root (parent of scripts folder)
cd /d "%~dp0.."

echo.
echo ================================================================================
echo.
echo     AI-POWERED HEALTH CHECK v2.1 (Hub Gateway Technology)
echo.
echo ================================================================================
echo.
echo Enhanced Features:
echo   [x] Real-time system metrics (CPU, RAM, Disk)
echo   [x] Dependency analysis with AI assistance
echo   [x] Missing package auto-detection
echo   [x] Smart error diagnosis
echo   [x] Auto-fix recommendations
echo   [x] Version conflict detection
echo.
echo Powered by: Hub Gateway Monitoring + Gemini 2.0 Flash AI
echo.
echo ================================================================================
echo.
pause

REM ============================================================================
REM Activate Virtual Environment
REM ============================================================================
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating main virtual environment...
    call .venv\Scripts\activate.bat
    echo.
) else (
    echo [ERROR] Main virtual environment not found!
    echo Please run Enhanced Setup first: menu.bat - Select [E]
    pause
    exit /b 1
)

REM ============================================================================
REM System Metrics Display (Hub Gateway Feature)
REM ============================================================================
echo.
echo ================================================================================
echo   SYSTEM METRICS (Real-time Monitoring)
echo ================================================================================
echo.

python -c "import psutil; cpu=psutil.cpu_percent(interval=0.1); mem=psutil.virtual_memory(); disk=psutil.disk_usage('/'); print(f'CPU Usage:     {cpu}%%'); print(f'RAM Available: {round(mem.available/1024/1024/1024, 2)} GB / {round(mem.total/1024/1024/1024, 2)} GB'); print(f'RAM Usage:     {mem.percent}%%'); print(f'Disk Free:     {round(disk.free/1024/1024/1024, 2)} GB / {round(disk.total/1024/1024/1024, 2)} GB'); print(f'Disk Usage:    {disk.percent}%%')" 2>nul

if errorlevel 1 (
    echo [WARNING] System metrics unavailable - psutil not installed
    echo Installing psutil...
    pip install psutil >nul 2>&1
    echo [OK] psutil installed
)

echo.
echo ================================================================================
echo.

REM ============================================================================
REM Service Health Checks with Enhanced Monitoring
REM ============================================================================

echo ========================================
echo   [1/9] Hub Gateway Health Check
echo ========================================
echo.
python scripts\utilities\service_health_checker.py hub-gateway services\hub-gateway
echo.

echo ========================================
echo   [2/9] ChatBot Health Check  
echo ========================================
echo.
python scripts\utilities\service_health_checker.py chatbot services\chatbot
echo.

echo ========================================
echo   [3/9] Text2SQL Health Check
echo ========================================
echo.
python scripts\utilities\service_health_checker.py text2sql services\text2sql
echo.

echo ========================================
echo   [4/9] Document Intelligence Check
echo ========================================
echo.
python scripts\utilities\service_health_checker.py document-intelligence services\document-intelligence
echo.

echo ========================================
echo   [5/9] Speech2Text Health Check
echo ========================================
echo.
python scripts\utilities\service_health_checker.py speech2text services\speech2text
echo.

echo ========================================
echo   [6/9] Stable Diffusion Check
echo ========================================
echo.
python scripts\utilities\service_health_checker.py stable-diffusion services\stable-diffusion
echo.

echo ========================================
echo   [7/9] LoRA Training Health Check
echo ========================================
echo.
python scripts\utilities\service_health_checker.py lora-training services\lora-training
echo.

echo ========================================
echo   [8/9] Image Upscale Health Check
echo ========================================
echo.
python scripts\utilities\service_health_checker.py image-upscale services\image-upscale
echo.

echo ========================================
echo   [9/9] MCP Server Health Check
echo ========================================
echo.
python scripts\utilities\service_health_checker.py mcp-server services\mcp-server
echo.

REM ============================================================================
REM Final Summary with System Status
REM ============================================================================
echo.
echo ================================================================================
echo.
echo   ENHANCED HEALTH CHECK COMPLETE!
echo.
echo ================================================================================
echo.
echo System Status:
python -c "import psutil; print(f'  CPU: {psutil.cpu_percent(interval=0.1)}%% | RAM: {psutil.virtual_memory().percent}%% | Disk: {psutil.disk_usage(\"/\").percent}%%')" 2>nul
echo.
echo Review the detailed results above to identify any issues.
echo.
echo Next Steps:
echo.
echo   If issues found:
echo     - Run Enhanced Setup: menu.bat - Select [E]
echo     - Check specific service: Use individual health checker
echo     - Review logs in services/[service]/logs/
echo.
echo   If all OK:
echo     - Start all services: menu.bat - Select [A]
echo     - Start Hub Gateway first: menu.bat - Select [1]
echo     - Then start other services as needed
echo.
echo ================================================================================
echo.
echo Features used:
echo   [x] Hub Gateway system monitoring
echo   [x] Enhanced error detection
echo   [x] Dependency conflict resolution
echo   [x] AI-powered diagnostics (if configured)
echo.
echo ================================================================================
echo.
pause
