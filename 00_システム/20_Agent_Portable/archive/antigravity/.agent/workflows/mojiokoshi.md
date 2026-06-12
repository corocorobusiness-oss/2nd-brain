---
description: Transcribe an audio file using 00_システム\devtools\start_ears.bat
---

1. Identify the target audio file mentioned by the user.
2. Copy the audio file to the transcription watch directory: `.\02_音声`.
   - Use `run_command` with `Copy-Item`.
3. Launch the transcription service to process the file.
   - Run `.\00_システム\devtools\start_ears.bat`.
   - Set `WaitMsBeforeAsync` to 5000 (5 seconds) to allow it to initialize or check for an existing instance.
   - Note: If `start_ears.bat` is already running, this new instance will exit safely, but the existing instance will pick up the new file.
4. Notify the user that the transcription has started and the result will appear in `.\03_知識ベース\00_文字起こしログ` shortly.

