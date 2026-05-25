@echo off
title AURA Assistant Launcher
echo ======================================================================
echo           🌌 AURA - REMOTE DEPLOYMENT & LAUNCHER WIZARD
echo ======================================================================
echo.

:: Ensure working directory is the script's directory
cd /d "%~dp0"

:: Clean up any existing ngrok or hanging backend processes to prevent port/tunnel conflicts
echo [*] Cleaning up any running ngrok instances...
taskkill /f /im ngrok.exe >nul 2>&1

:: Detect virtual environment python
set PYTHON_EXE=
if exist "venv\Scripts\python.exe" (
    set PYTHON_EXE="venv\Scripts\python.exe"
) else if exist "..\venv\Scripts\python.exe" (
    set PYTHON_EXE="..\venv\Scripts\python.exe"
)

if not "%PYTHON_EXE%"=="" (
    echo [*] Detected virtual environment Python: %PYTHON_EXE%
) else (
    echo [!] WARNING: No virtual environment Python found. Falling back to system python.
    set PYTHON_EXE=python
)

echo [*] Launching AURA Backend in a new window...
start cmd /k "title AURA Backend && cd /d "%~dp0" && %PYTHON_EXE% run_aura.py"

echo [*] Waiting 3 seconds for backend to start up...
timeout /t 3 >nul

echo [*] Exposing AURA Backend to your permanent static URL...
:: We explicitly pass your static domain here so ngrok always uses the exact same address!
start cmd /k "title AURA Secure Tunnel && ngrok http --url=handball-gown-bobtail.ngrok-free.dev 8000"

echo.
echo ======================================================================
echo AURA backend and secure tunnel have been launched!
echo This launcher window will now close in 3 seconds...
echo ======================================================================
timeout /t 3 >nul
exit
