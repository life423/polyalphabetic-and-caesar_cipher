@echo off
setlocal EnableDelayedExpansion

echo ===================================================
echo         CIPHER TOOLS APPLICATION LAUNCHER
echo ===================================================

:: Check if the Python script exists
if not exist "scripts\run_cipher_app.py" (
    echo Error: Cannot find scripts\run_cipher_app.py in the current directory.
    echo Current directory: %CD%
    echo Please ensure you are running this batch file from the correct location.
    echo.
    pause
    exit /b 1
)

:: Try to find Python - check multiple possible commands
set PYTHON_CMD=none
set PYTHON_FOUND=false

:: Try py launcher first (preferred on Windows)
py --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=py
    set PYTHON_FOUND=true
    goto :python_found
)

:: Try python command
python --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=python
    set PYTHON_FOUND=true
    goto :python_found
)

:: Try python3 command
python3 --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=python3
    set PYTHON_FOUND=true
    goto :python_found
)

:: No Python found
if "%PYTHON_FOUND%"=="false" (
    echo Error: Python is not installed or not in the PATH.
    echo.
    echo Please install Python 3.7 or later from https://www.python.org/downloads/
    echo After installing, ensure Python is added to your PATH.
    echo.
    echo Alternatively, you can specify the full path to Python by editing
    echo this batch file and changing PYTHON_CMD to the full path of your 
    echo Python executable.
    echo.
    pause
    exit /b 1
)

:python_found
:: Get Python version
for /f "tokens=2" %%V in ('%PYTHON_CMD% --version 2^>^&1') do (
    set PYTHON_VERSION=%%V
)

echo Found Python %PYTHON_VERSION% using command: %PYTHON_CMD%

:: Check for dependencies
echo Checking for required dependencies...
%PYTHON_CMD% -c "import tkinter" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Warning: tkinter module not found. GUI mode may not work.
    echo.
)

:: Run the application
echo.
echo Starting Cipher Tools App...
%PYTHON_CMD% scripts\run_cipher_app.py

set EXIT_CODE=%ERRORLEVEL%
if %EXIT_CODE% neq 0 (
    echo.
    echo Application exited with error code %EXIT_CODE%
    echo.
    echo If you're experiencing issues, try running:
    echo %PYTHON_CMD% -m pip install -r requirements.txt
    echo.
    echo If the problem persists, please check the following:
    echo - Ensure all dependencies are installed
    echo - Verify Python %PYTHON_VERSION% is compatible with the application
    echo - Check for any error messages above
)

pause
exit /b %EXIT_CODE%
