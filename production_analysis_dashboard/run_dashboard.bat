@echo off
chcp 65001 >nul
setlocal

echo === Production Analysis Dashboard ===

title Production Analysis Dashboard

:: Settings
set DEFAULT_PORT=8504
set VENV_PATH=.venv

:: Args
set PORT=%1
if "%PORT%"=="" set PORT=%DEFAULT_PORT%

set HEADLESS_OPT=
if /I "%2"=="headless" set HEADLESS_OPT=--server.headless true

set DO_INSTALL=0
if /I "%3"=="install" set DO_INSTALL=1

echo Port: %PORT%
echo Headless: %HEADLESS_OPT%
echo Install requirements: %DO_INSTALL%
echo.

:: Activate venv if present
if exist "%VENV_PATH%\Scripts\activate.bat" (
    call "%VENV_PATH%\Scripts\activate.bat"
)

:: Install requirements if requested
if "%DO_INSTALL%"=="1" (
    echo Installing requirements...
    pip install -r requirements.txt || goto :error
)

:: Open browser only when not headless
if not defined HEADLESS_OPT start http://localhost:%PORT%

echo Starting Streamlit...
streamlit run app.py --server.port %PORT% %HEADLESS_OPT%
goto :eof

:error
echo [ERROR] Failed to prepare environment.
pause
