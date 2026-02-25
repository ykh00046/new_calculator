@echo off
chcp 65001 > nul
cd /d "%~dp0"

:: Start Manager Hidden (minimized to tray)
start /min python manager.py
