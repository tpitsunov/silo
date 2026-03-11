# CLI Reference

SILO comes packaged with several handy CLI utilities to manage skill development.

## `silo init`
Create a new skill from a minimal boilerplate template.

**Usage:**
```bash
silo init <filename> [--secrets SEC1,SEC2]
```

**Parameters:**
*   `<filename>`: The name of the file to create, e.g. `github_skill.py`.
*   `--secrets`: A comma-separated list of required keys, e.g., `GITHUB_TOKEN,OPENAI_API_KEY`.

This command automatically generates a file compliant with `PEP 723`, meaning the script explicitly specifies `silo` as an inline dependency for `uv`.

## `silo test`

Run a skill in a simulated "headless agent" environment.

**Usage:**
```bash
silo test <script> [command] [--args...]
```

**Parameters:**
*   `<script>`: The path to the skill.
*   `[command]`: The function within the script to test.

**Why use it?** An LLM agent doesn't see colors, progress bars, or confirmation prompts. It needs plain text or JSON output. `silo test` forces SILO to run in "Headless Mode". It checks that the skill generates its markdown manifest (`SKILL.md`) correctly, ensures authentication fallbacks don't hang execution, and ensures output is cleanly parsable format.

## `silo doctor`

Diagnose the environment to ensure compatibility with SILO.

**Usage:**
```bash
silo doctor
```

It verifies:
*   Python versions (requires 3.9+).
*   Presence of `uv` (recommended).
*   OS Keychain integration.
*   Critical framework dependencies (e.g., `pydantic`).
