@echo off
title CipherCraft GUI
echo ================================================
echo             STARTING CIPHERCRAFT GUI
echo ================================================
echo.

:: Set working directory to where the batch file is located
cd /d "%~dp0"

:: Run the GUI application
python -m src.ui.gui

:: If there was an error, pause so the user can see the message
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error starting the GUI. Press any key to exit...
    pause > nul
)
