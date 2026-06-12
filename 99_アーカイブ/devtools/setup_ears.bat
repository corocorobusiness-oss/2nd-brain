@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Second Brain - Setup Ears

echo [Second Brain] Setting up Transcription Environment...
echo.

:: 1. Check Python
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.10+ and try again.
    exit /b 1
)

:: 1.5 Check/Install FFmpeg (Required for Whisper)
ffmpeg -version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [Info] FFmpeg not found. Attempting to install via Winget...
    winget install "Gyan.FFmpeg" --accept-source-agreements --accept-package-agreements
    if %ERRORLEVEL% neq 0 (
        echo [Warning] Failed to install FFmpeg. You may need to install it manually.
        echo Please download from https://ffmpeg.org/download.html and add to PATH.
        exit /b 1
    ) else (
        echo [Info] FFmpeg installed. You may need to restart the terminal.
        refreshenv >nul 2>&1
    )
)

:: 2. Create venv
if not exist "transcription\venv" (
    echo Creating virtual environment...
    python -m venv "transcription\venv"
)

:: 3. Install Requirements
echo Installing dependencies...
call "transcription\venv\Scripts\activate"
python -m pip install -r "transcription\requirements.txt"



echo.
echo Setup complete! You can now run 'start_ears.bat'.
:: pause REMOVED for automation compatibility
exit /b 0
