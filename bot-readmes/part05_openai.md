# Part 5: OpenAI Interaction

This bot handles communication with the Chat API and defines tool functions.

## Responsibilities
- Manage the message history and send prompts to OpenAI in `main.py`.
- Define callable tools in `tools.py` for things like time queries or memory storage.
- Keep API costs low by truncating old conversation history.

## How to Do It
1. Review `tools.py` for existing tool functions.
2. Update `main.py` to send function schemas to OpenAI.
3. Ensure responses are parsed correctly and errors are logged.
4. Run `black` and `flake8` after modifications.
