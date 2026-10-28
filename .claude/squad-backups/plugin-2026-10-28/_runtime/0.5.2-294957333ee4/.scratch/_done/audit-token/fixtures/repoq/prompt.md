In the current directory is a small Python codebase. Use the Read, Grep and Glob tools only (no code execution).
Question: (1) which files under `src/` call the function `load(` imported from config (exclude config.py itself and comments or docs)? (2) What is the current default timeout in seconds?
Reply with ONLY one JSON object, no prose, no code fence:
{"callers": ["src/<file>.py", ...], "timeout_s": <number>}
