@echo off
title CipherCraft Launcher
echo ================================================
echo             STARTING CIPHERCRAFT 
echo ================================================
echo.

:: Set working directory to where the batch file is located
cd /d "%~dp0"

:: Try to find Python - check multiple possible commands
set PYTHON_CMD=none
set PYTHON_FOUND=false

:: Try py launcher first (preferred on Windows)
py --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=py
    set PYTHON_FOUND=true
    goto :run_app
)

:: Try python command
python --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=python
    set PYTHON_FOUND=true
    goto :run_app
)

:: Try python3 command
python3 --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=python3
    set PYTHON_FOUND=true
    goto :run_app
)

:: No Python found
echo Error: Python is not installed or not in the PATH.
echo.
echo Please install Python 3.7 or later from https://www.python.org/downloads/
echo After installing, ensure Python is added to your PATH.
echo.
pause
exit /b 1

:run_app
:: Run the Python launcher script
%PYTHON_CMD% cipher_launcher.py

:: If there was an error, pause so the user can see the message
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error occurred. Exit code: %ERRORLEVEL%
    echo.
    pause > nul
)
