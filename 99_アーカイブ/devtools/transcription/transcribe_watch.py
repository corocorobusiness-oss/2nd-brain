import sys
import time
import os
import shutil
import datetime
import whisper
import psutil
import atexit

# --- Configuration ---
# Calculate paths relative to this script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
WATCH_DIR = os.path.join(BASE_DIR, "02_音声")
PROCESSED_DIR = os.path.join(WATCH_DIR, "processed")
OUTPUT_DIR = os.path.join(BASE_DIR, "03_知識ベース", "00_文字起こしログ")

def get_lock_file():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "transcribe.lock")

def clean_lock_file():
    lock_file = get_lock_file()
    if os.path.exists(lock_file):
        try: os.remove(lock_file)
        except OSError: pass

def check_single_instance():
    # Simple lock mechanism to prevent multiple instances
    lock_file = get_lock_file()
    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            if psutil.pid_exists(pid):
                print(f"[Info] Another instance is already running (PID: {pid}). Exiting.")
                return False
            else:
                print("[Info] Found stale lock file. Removing...")
                clean_lock_file()
        except: clean_lock_file()
    
    try:
        with open(lock_file, 'w') as f: f.write(str(os.getpid()))
        atexit.register(clean_lock_file)
        return True
    except: return False

def process_file(filepath, filename, model):
    print(f"\n[Processing] {filename}")
    try:
        # Transcribe directly using Whisper
        print(f"  Transcribing with Whisper (Base)...")
        result = model.transcribe(filepath, verbose=False, language="ja") # verbose=False for cleaner output
        text = result["text"]

        # Save Output
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        out_filename = f"{date_str}_Transcript_{os.path.splitext(filename)[0]}.md"
        out_path = os.path.join(OUTPUT_DIR, out_filename)
        
        header_text = f"# 文字起こし: {os.path.splitext(filename)[0]}\n\n"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(header_text + text)
        
        print(f"  -> Saved transcript to: {out_filename}")
        
        # Archive
        shutil.move(filepath, os.path.join(PROCESSED_DIR, filename))
        print("  -> Archived original audio file.")
        return True

    except Exception as e:
        print(f"[Error] Failed processing {filename}: {e}")
        return False

def main():
    # Ensure directories exist
    os.makedirs(WATCH_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not check_single_instance():
        sys.exit(0)

    print("=== Second Brain Transcription Tool (Run-Once) ===")
    
    # 1. Check for files first to avoid loading model if empty
    target_files = []
    valid_extensions = [".mp3", ".wav", ".m4a", ".mp4", ".mpeg", ".mpga", ".aac", ".ogg"]
    
    print(f"Scanning directory: {WATCH_DIR}")
    for filename in os.listdir(WATCH_DIR):
        filepath = os.path.join(WATCH_DIR, filename)
        if os.path.isfile(filepath):
            ext = os.path.splitext(filename)[1].lower()
            if ext in valid_extensions:
                target_files.append((filepath, filename))

    if not target_files:
        print("No audio files found. Exiting.")
        return

    print(f"Found {len(target_files)} audio file(s).")

    # 2. Load Model
    print("[System] Loading Whisper Model (base)... This may take a moment.")
    try:
        model = whisper.load_model("base")
        print("[System] Model loaded.")
    except Exception as e:
        print(f"[FATAL] Failed to load Whisper model: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 3. Process Files
    count_success = 0
    for filepath, filename in target_files:
        if process_file(filepath, filename, model):
            count_success += 1
            
    print("-" * 30)
    print(f"Done. Processed {count_success}/{len(target_files)} files.")
    print("Exiting.")

if __name__ == "__main__":
    main()
