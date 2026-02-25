@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================
echo  Production Hub - Install Dependencies
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

:: Install requirements
echo Installing requirements...
pip install -r requirements.txt -q

if %errorlevel% equ 0 (
    echo.
    echo [OK] Installation complete!
) else (
    echo.
    echo [ERROR] Installation failed
)

echo.
pause
