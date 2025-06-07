# Part 1: Environment Setup

This bot prepares the development environment so the others can run the code without issues.

## Responsibilities
- Install Python 3.8+ and FFmpeg.
- Create a virtual environment and install requirements for each subproject.
- Copy `.env.example` to `.env` and fill in API keys.
- Verify that `python -m py_compile` and `black --check` run cleanly.

## How to Do It
1. Install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r real-voice-assistant/requirements.txt
   pip install -r assistant-dashboard/requirements.txt
   pip install -r realtime-voice-assistant/requirements.txt || true
   ```
2. Copy the environment template:
   ```bash
   cp real-voice-assistant/.env.example real-voice-assistant/.env
   # edit the file and add your API keys
   ```
3. Run checks:
   ```bash
   python -m py_compile real-voice-assistant/*.py assistant-dashboard/app.py
   black --check real-voice-assistant/*.py assistant-dashboard/app.py
   ```
