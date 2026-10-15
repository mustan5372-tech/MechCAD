@echo off
setlocal enabledelayedexpansion
title MechCAD - Professional 3D Parametric CAD

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

rem 1. Locate Virtual Environment Python
if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe"
    set "PYTHONW_EXE=%SCRIPT_DIR%.venv\Scripts\pythonw.exe"
) else if exist "%SCRIPT_DIR%venv\Scripts\python.exe" (
    set "PYTHON_EXE=%SCRIPT_DIR%venv\Scripts\python.exe"
    set "PYTHONW_EXE=%SCRIPT_DIR%venv\Scripts\pythonw.exe"
) else (
    set "PYTHON_EXE=python"
    set "PYTHONW_EXE=pythonw"
)

rem 2. Debug / Console Mode flag
if "%1"=="--debug" (
    echo [MechCAD] Starting in debug console mode...
    "%PYTHON_EXE%" "%SCRIPT_DIR%run_mechcad.py" %*
    if errorlevel 1 pause
    exit /b %errorlevel%
)

if "%1"=="--console" (
    echo [MechCAD] Starting in console mode...
    "%PYTHON_EXE%" "%SCRIPT_DIR%run_mechcad.py" %*
    if errorlevel 1 pause
    exit /b %errorlevel%
)

rem 3. Standard Desktop Launch
rem Use pythonw for clean windowed CAD desktop experience without background terminal
if exist "%PYTHONW_EXE%" (
    start "" "%PYTHONW_EXE%" "%SCRIPT_DIR%run_mechcad.py" %*
) else (
    start "" "%PYTHON_EXE%" "%SCRIPT_DIR%run_mechcad.py" %*
)

exit /b 0
