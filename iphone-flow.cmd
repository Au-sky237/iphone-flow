@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Create the Python environment first. See docs\INSTALL.md.
    echo py -3.12 -m venv .venv
    pause
    exit /b 1
)
set "PATH=%~dp0tools\bin;%PATH%"
".venv\Scripts\python.exe" launch.py --flows
if errorlevel 1 pause
