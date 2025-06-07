# Part 4: Text-to-Speech

This bot makes the assistant speak.

## Responsibilities
- Connect to the ElevenLabs API for high-quality speech.
- Provide a fallback to the local `pyttsx3` library if the API fails.
- Keep audio playback non-blocking so other tasks can run.

## How to Do It
1. Read the `speak_text` function in `main.py`.
2. Add error handling around the ElevenLabs API request.
3. Make sure the TTS system works on all platforms (Windows/Linux/Mac).
4. Format code with Black and run flake8.
