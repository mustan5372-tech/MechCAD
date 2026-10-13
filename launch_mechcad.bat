@echo off
rem MechCAD Windows Desktop Launcher
set SCRIPT_DIR=%~dp0
start "" "%SCRIPT_DIR%.venv\Scripts\pythonw.exe" "%SCRIPT_DIR%run_mechcad.py" %*
