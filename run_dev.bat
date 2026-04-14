@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "VENV_PYTHON=%ROOT_DIR%.venv\Scripts\python.exe"

echo [INFO] Source launcher: run_dev.bat
echo [INFO] For deployed packages, run DHR_Generator.exe from the extracted package folder.

cd /d "%ROOT_DIR%v3"

if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" main.py
    goto :end
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [WARN] .venv Python not found. Falling back to py -3.
    py -3 main.py
    goto :end
)

echo [WARN] .venv Python not found. Falling back to PATH python.
python main.py

:end
pause
