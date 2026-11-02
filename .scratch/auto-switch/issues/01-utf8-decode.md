Status: ready-for-agent

# 01: decode captured child output as UTF-8 with replace

`cautoswitch` crashed with `UnicodeDecodeError ... cp1252` when a child printed a byte such as 0x90.
Every text-reading `subprocess` call now uses `encoding="utf-8", errors="replace"`.

Files: `bin/caproc.py`, `bin/cautoswitch`, `bin/cwake`, `windows/autoswitch.py`. `bin/cdefault` and `bin/cswitch` are bash (no change).
Design: no helper wraps the calls, so each call got the two arguments. The `/proc/<pid>/environ` and `cmdline` reads got them too.

## Comments
