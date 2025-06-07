# Part 9: Testing and Quality Assurance

This bot ensures the code base stays reliable and consistent.

## Responsibilities
- Write unit tests for database functions and helper utilities.
- Add integration tests for the CLI and web dashboard.
- Configure continuous integration to run `black --check` and `flake8`.

## How to Do It
1. Use `pytest` to create tests inside a new `tests/` directory.
2. Mock external APIs (OpenAI, ElevenLabs) so tests run offline.
3. Document how to run the tests:
   ```bash
   pytest
   ```
