@echo off
setlocal
cd /d "%~dp0"
set "PROJECT_PYTHON=python"
if exist ".venv\Scripts\python.exe" set "PROJECT_PYTHON=%~dp0.venv\Scripts\python.exe"
"%PROJECT_PYTHON%" -m PyInstaller --noconfirm --onefile --windowed --name JV_Analyzer --icon "assets\logo.ico" --add-data "assets;assets" main.py
pause
