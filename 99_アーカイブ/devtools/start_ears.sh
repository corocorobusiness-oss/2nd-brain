#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "[Second Brain] Initializing Infinite Ears (Gemini Edition)..."
echo ""

echo "Listening on:  ../../02_音声/"
echo "Output to:    ../../03_知識ベース/00_文字起こしログ/"
echo ""

# Activate and Run
source "transcription/venv/bin/activate"
python3 "transcription/transcribe_watch.py"

echo ""
echo "Program stopped."
