@echo off
cd /d "%~dp0"
title Second Brain - Gemini Ears
chcp 65001 >nul

echo [Second Brain] Initializing Infinite Ears (Gemini Edition)...
echo.



:: Activate and Run
:: call devtools\transcription\venv\Scripts\activate
echo Listening on:  ..\..\02_音声/
echo Output to:    ..\..\03_知識ベース/00_文字起こしログ/
echo.
"%~dp0transcription\venv\Scripts\python.exe" "%~dp0transcription\transcribe_watch.py"

echo.
echo Program stopped.
if %ERRORLEVEL% neq 0 (
    echo.
    echo Program stopped with error.
    pause
)
