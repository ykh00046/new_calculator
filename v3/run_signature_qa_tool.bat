@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title Signature QA Tool

echo ========================================
echo  Signature QA Tool
echo ========================================
echo.
echo Starting application...
echo.

cd /d "%~dp0"
python -m signature_qa_tool.main

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo  Error: Application failed to start
    echo ========================================
    echo.
    echo Please check:
    echo - Python is installed and in PATH
    echo - PySide6 is installed: pip install PySide6
    echo - All dependencies are installed: pip install -r requirements.txt
    echo.
    pause
)
