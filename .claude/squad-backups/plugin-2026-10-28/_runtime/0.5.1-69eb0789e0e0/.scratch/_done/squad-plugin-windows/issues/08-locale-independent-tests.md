# T2d Locale-independent existing tests

Status: ready-for-agent
Type: task
Source: dev-3 flag at T2b hand-in; Tech Lead FINAL (option b)
Touches: existing tests `tests/test_squad_label.py`, `test_squad_notify.py`, `test_squad_migrate.py`, `test_squad_usage.py`, `test_squad_usage_hook.py`, `test_squad_close.py`, `test_squad_respawn.py`, `test_squad_retire.py`, `test_squad_spawn.py`, `test_squad_log_message.py`; one `bin/` change: the `bin/squad-close` inline snippet.
Blocked by: 03 (T2b, build on 2396faf). Blocks 04 and 05.

## What
Fixtures-only. Test text reads/writes in those files name `encoding="utf-8"` so they pass under `PYTHONUTF8=0 LC_ALL=C PYTHONIOENCODING=cp1252` and in a UTF-8 locale. Do NOT touch doc-reading tests (`test_instructions`, `test_templates`, `test_process_*`).
One `bin/` nit: the `squad-close` inline snippet (`python3 -X utf8 -c`) prints blocker lines with `\r\n` on Windows, which would land in `$blockers`; add `sys.stdout.reconfigure(newline="\n")` as the snippet's first statement, with a test of the bytes.

## Technical AC (Tech Lead)
1. The ten files pass in the cp1252 env and the default env.
2. No change in `bin/` except the `squad-close` snippet line.
3. A bytes test for the `squad-close` snippet output: LF only.
4. Run tests with `PYTHONDONTWRITEBYTECODE=1`.

## Comments
