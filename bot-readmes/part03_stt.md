# Part 3: Speech Recognition

This bot focuses on capturing audio and converting it to text.

## Responsibilities
- Integrate Whisper (local or API) for speech-to-text in `main.py`.
- Ensure microphone input is handled smoothly.
- Handle errors such as missing audio or timeouts gracefully.

## How to Do It
1. Verify `ffmpeg` is installed for Whisper.
2. Review the `record_and_transcribe` logic in `main.py`.
3. Test recognition with sample audio to confirm accuracy.
4. Keep code formatted with Black and flake8.
