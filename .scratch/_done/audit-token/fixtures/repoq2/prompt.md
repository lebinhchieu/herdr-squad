In the current directory is a small Python codebase. Use the Read, Grep and Glob tools only (no code execution).
Question: (1) which Python files under `src/` call the function `load` of the module config (directly, through the module, or through an import alias; `reload` and other functions are different functions; mentions in comments, docstrings or other directories do not count)? (2) What is the current default `timeout_s` in seconds?
Reply with ONLY one JSON object, no prose, no code fence:
{"callers": ["src/<file>.py", ...], "timeout_s": <number>}
