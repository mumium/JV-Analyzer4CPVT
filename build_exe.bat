@echo off
setlocal
cd /d "%~dp0"
set "PROJECT_PYTHON=python"
if exist ".venv\Scripts\python.exe" set "PROJECT_PYTHON=%~dp0.venv\Scripts\python.exe"
"%PROJECT_PYTHON%" -m PyInstaller --noconfirm --clean packaging\JV_Analyzer.spec
if errorlevel 1 goto failed
"%~dp0dist\JV_Analyzer.exe" --self-test "%~dp0dist\self-test.json"
if errorlevel 1 goto failed
echo Build and self-test succeeded: dist\JV_Analyzer.exe
if /i not "%~1"=="--no-pause" pause
exit /b 0

:failed
echo Build or self-test failed. Check the output and dist\self-test.json.
if /i not "%~1"=="--no-pause" pause
exit /b 1
