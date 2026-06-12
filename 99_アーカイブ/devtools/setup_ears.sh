#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "[Second Brain] Setting up Transcription Environment (Mac/Linux)..."
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH."
    echo "Please install Python 3.10+ and try again."
    exit 1
fi

# 1.5 Check FFmpeg (Required for Whisper)
if ! command -v ffmpeg &> /dev/null; then
    echo "[Warning] FFmpeg not found."
    echo "FFmpeg is required for Whisper to process audio."
    echo "Please install it manually. For example, on macOS with Homebrew:"
    echo "  brew install ffmpeg"
    echo ""
    read -p "Press Enter to continue anyway (setup might compile minimal tools but runtime needs ffmpeg)... "
else
    echo "[Info] FFmpeg is available."
fi

# 2. Create venv
if [ ! -d "transcription/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "transcription/venv"
fi

# 3. Install Requirements
echo "Installing dependencies..."
source "transcription/venv/bin/activate"
python3 -m pip install -r "transcription/requirements.txt"

echo ""
echo "Setup complete! You can now run 'bash start_ears.sh'."
