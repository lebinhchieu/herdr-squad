# squad plugin 0.3.1 does not run on native Windows (`squad-start`, `squad-label`)

**Status:** needs-triage · **Plugin:** herdr-squad / squad 0.3.1 · **Found:** 2026-10-17 running `/squad:squad-start --resume scene-split`

**Two independent bugs, both on native Windows (Git Bash + Python 3.14 from the Microsoft install, not WSL).** `squad-start` can't launch `squad-spawn` at all, and once launched by hand, `squad-label` crashes decoding herdr's output. Workaround below. Nothing was left half-started by the failures.

## Bug 1: `squad-start` cannot run `squad-spawn` (`WinError 193`)

- **Symptom:** `squad-start --squad village --resume scene-split` ends with `OSError: [WinError 193] %1 is not a valid Win32 application`.
- **Cause:** `bin/squad-start` line 141 (resume) and line 230 (new scope or goal) call `subprocess.run([str(PLUGIN / "bin" / "squad-spawn"), ...])`. `squad-spawn` is a bash script (`#!/usr/bin/env bash`, no extension). On Windows, `CreateProcess` ignores shebangs, so it cannot run it. On Linux and macOS this works, which is why it was never caught.
- **Fix options:**
  - **Preferred:** run it through bash explicitly, `["bash", str(path), ...]`, on `os.name == "nt"` (or always). Resolve bash once, `shutil.which("bash")`, and fail with a clear message if it is missing.
  - Or rewrite `squad-spawn` in Python. Bigger change, and removes the bash dependency for every caller.
- **Check the same pattern elsewhere:** any other `subprocess` call that runs a plugin script by path. In `bin/` I only found the two in `squad-start`; `squad-respawn`, `squad-retire` and `squad-close` are bash and call each other from bash, which works under Git Bash.

## Bug 2: Python helpers decode subprocess output as cp1252

- **Symptom:** after Bug 1 is bypassed, `squad-spawn` dies with `UnicodeDecodeError: 'charmap' codec can't decode byte 0x90 in position 399`, raised from `squad-label` line 114 (called by `squad-spawn`). A `_readerthread` traceback comes first.
- **Cause:** `subprocess.run(..., capture_output=True, text=True)` with no `encoding=` uses the locale encoding, cp1252 on Windows. herdr prints UTF-8, and the tab label contains an emoji (`🦀 Manager`).
- **Call sites with `text=True` and no encoding:**
  - `bin/squad-label:31` (`herdr` wrapper, the one that crashed)
  - `bin/squad-notify:80`
  - `bin/squad-start:43`, `:71`, `:141`, `:230`
  - `bin/squad-migrate:46`
  - check `squadlabel.py`, `squadinbox.py`, `squadprocess.py` too
- **Fix:** pass `encoding="utf-8", errors="replace"` at every call site (or one shared helper), and read and write files with `encoding="utf-8"`. Setting `PYTHONUTF8=1` from the launcher is a stopgap, not a fix.
- **Verified:** with `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` the dry run (`squad-spawn --dry-run`) and the real spawn both succeed.

## Smaller things seen

- **CRLF line endings:** 13 files in `bin/` have CRLF (`file` reports it). Bash ran `squad-spawn` anyway here, so it is not the blocker, but it will break any script that bash parses strictly. Add a `.gitattributes` with `* text=auto eol=lf` (or `bin/* eol=lf`) so Windows checkouts keep LF.
- **Flag name:** `squad-spawn --dry` is rejected, the flag is `--dry-run`. No change needed, just easy to trip on.
- **Paths with spaces:** the project path is `C:\Users\84084\workspace\Guardian - Learn`. The real spawn worked, but the `would run:` dry-run line prints unquoted paths (cosmetic).

## Repro

1. Windows 11, Git Bash, Python 3.14 (`python` on PATH), herdr running (`HERDR_ENV=1`), plugin installed from the cache.
2. In a project with a squad that has a scope: `squad-start --squad village --resume scene-split`. Bug 1 fires.
3. `SQUAD_DIR=<project>/.claude/squads/village bash <plugin>/bin/squad-spawn manager village-mgr-scene-split --scope scene-split --prompt x --dry-run`. Bug 2 fires unless `PYTHONUTF8=1` is set.

## Workaround used today

```bash
export SQUAD_DIR="$PWD/.claude/squads/village" PYTHONUTF8=1 PYTHONIOENCODING=utf-8
bash "<plugin>/bin/squad-spawn" manager village-mgr-scene-split --scope scene-split \
  --prompt 'RESPAWN: you are village-mgr-scene-split, restarted for scope scene-split. Read $SQUAD_DIR/process.md, then your notes $SCOPE_DIR/roles/village-mgr-scene-split.notes.md if it exists, then the brief and the roster, and continue where the files say.'
```

Result: Manager tab `w4:t2`, pane `w4:p2`, status ready.

## Not verified (check after the fix)

- **The Manager's own shell** was started without `PYTHONUTF8=1`, so when it spawns the pod (`squad-spawn` for tech, dev, qaw, qab) Bug 2 may hit again. If it does, that proves the fix must live in the plugin, not in the caller's environment.
- `squad-respawn`, `squad-retire`, `squad-close`, `squad-notify`, `squad-usage` and the hooks were not exercised on Windows at all.

## Done when

- `squad-start "<text>" --touches <paths>` (new scope) and `squad-start --resume <name>` both start a Manager from a plain Git Bash prompt, with no env vars set.
- `squad-spawn` for every role works for a project path containing spaces and an emoji tab label.
