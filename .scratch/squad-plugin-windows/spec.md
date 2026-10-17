Status: ready-for-agent (BA final; QA blackbox confirm pending on C1-C6 wording; O2 and O3 for Tech Lead and PO)

# Spec: squad-plugin-windows, the plugin runs on native Windows

**One line:** on native Windows (Git Bash + Python 3.14, no WSL) the PO can start a Manager, spawn every role and use the PO inbox from a plain prompt with no env vars set, and nothing changes on Linux or macOS. Source: `issue.md` (Bug 1, Bug 2, CRLF, Done when) and the PO's inbox error. Business AC below; technical AC live in the tickets (`issues/`).

## Problem Statement

As PO on a Windows PC I cannot run the squad at all:
- `squad-start` (new scope and `--resume`) dies with `WinError 193`; `squad-spawn` never starts.
- Once `squad-spawn` is started by hand it dies on the emoji in the tab label (`🦀 Manager`), and only works with `PYTHONUTF8=1` set by hand.
- The PO inbox mod shows `Inbox ⚠ squad-inbox list failed: Traceback (most recent call last):`, so I never see what the Manager asks me.
- A Windows checkout can turn the scripts into CRLF files.

## Solution

The plugin never depends on how the OS starts scripts, on the OS text encoding, or on Unix-only modules. A fix lives in the plugin, never in the caller's environment (`PYTHONUTF8=1` is a stopgap, not a fix). Because nobody in the squad can run Windows, the squad proves what it can on Linux (non-UTF-8 locale, no `fcntl`, no `/proc`) and hands the PO a short Windows checklist (story 12).

## Findings the BA made (read before the stories)

- **F0: three independent causes can each give the PO's traceback** (QA blackbox measured all three on 0.3.2, `evidence/qab-review-of-spec.md`): (a) no `fcntl` on Windows (F1), (b) *printing* non-ASCII (`→`) to stdout/stderr under a non-UTF-8 locale, `UnicodeEncodeError`, (c) *reading* a file or template without `encoding=` (`UnicodeDecodeError`). Stories 7-10 must hold with all three simulated at once and with each alone. A fix for reading files alone does not pass them.
- **F1: the inbox traceback is probably not Bug 2 alone.** `bin/squadinbox.py:8` does `import fcntl`; `fcntl` does not exist on Windows, so `squad-inbox` would crash at import with `ModuleNotFoundError`. The file reads there already use `encoding="utf-8"` (`read_text`, binary writes). The PO's full traceback is still missing, so this is a strong guess. Stories 7-9 are written so they hold either way. `squadinbox.py` uses `flock` for the write lock (`:195-214`), so Windows needs another lock, and the same no-lost-write guarantee (story 9).
- **F2: text-mode writes on Windows turn `\n` into `\r\n`.** `write_text`, `open(..., "w")` and `os.fdopen(fd, "w")` in `squad-start`, `squad-migrate`, `squad-usage`, `squadlabel.py`, `squadprocess.py` would then rewrite `scope.md`, `roster.md`, `process-log.md` with CRLF: whole-file diffs and parse breaks on the Linux side of a shared repo. Story 6 covers it. This cannot be proven on Linux, so it goes on the PO checklist.
- **F3: more Unix-only code that must not crash a Windows run.** `squad-notify` reads `/proc` and opens a tty with `O_NOCTTY`; `squad-respawn` and `squad-retire` call `jq`; `squad-spawn` uses `readlink -f`. See O1, O2.

## Glossary (business terms this scope adds)

- **Plain prompt:** a Git Bash window on Windows, started by the user, with no `PYTHONUTF8`, `PYTHONIOENCODING` or `LC_ALL` set and no activated virtualenv.
- **Simulated Windows run:** on Linux, `PYTHONUTF8=0 LC_ALL=C` (non-UTF-8 locale), a launcher test that proves `bash` is called explicitly, and `fcntl` hidden. It proves the code path, not Windows itself.

## User Stories

### Starting a scope

1. **As the PO, I want `squad-start "<text>" --touches <paths>` to start a Manager from a plain prompt, so I can begin work on Windows without setting anything.**
   - Given a Windows project with a squad, a plain prompt and herdr running, When I run `squad-start "<text>" --touches bin`, Then a scope folder and brief exist and a Manager tab is open and ready, and no `WinError` or traceback is printed.
2. **As the PO, I want `squad-start --resume <name>` to bring back the Manager of an unfinished scope or goal the same way.**
   - Given an existing scope with its Manager gone, When I run `squad-start --squad <squad> --resume <name>`, Then a Manager tab with the RESPAWN prompt is open and ready.
3. **As the PO, I want a clear message when `bash` cannot be found, so I know what to install instead of reading a traceback.**
   - Given `bash` is not on `PATH`, When I run `squad-start` (new or `--resume`), Then it exits non-zero with one line that names `bash` and says to install Git for Windows or put its `bin` on `PATH`, and no scope folder, workspace rename or tab is left half-done.

### Spawning roles

4. **As the PO, I want every role to spawn, so a whole pod can run on Windows.**
   - Given a project path with spaces (e.g. `C:\Users\x\workspace\Guardian - Learn`) and a tab label with an emoji, When `squad-spawn` runs for each role (manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, dev, designer, token-coach), Then each tab opens, is named as the label says, and the agent is ready, with no env vars set.
   - Also `--dry-run` prints its plan with no error.
5. **As the PO, I want the Manager's own shell to spawn the pod without my help, so I do not need to export anything for the roles it starts.**
   - Given a Manager started by story 1 or 2 (it inherits no `PYTHONUTF8`), When it spawns the Tech Lead, a Developer, QA whitebox and QA blackbox, Then all four start. This is the item the issue lists as "not verified"; it proves the fix is in the plugin.
6. **As the PO, I want the files the plugin writes on Windows to be UTF-8 with LF line endings, so a repo shared with Linux shows no whole-file diffs and nothing is garbled.**
   - Given `scope.md`, `roster.md`, `process-log.md`, label files and inbox files with emoji and accented text, When a plugin command rewrites them on Windows, Then every file reads back byte for byte except the intended change: UTF-8, `\n` only, emoji intact.
   - `squad-start`'s edit of `touches:` in `scope.md` is the first case to check.
   - **Proof split:** UTF-8 round trip (emoji, accents, byte for byte) is proved on Linux. `\n` not turning into `\r\n` **only Windows proves**: the PO checklist counts CR bytes in the files each step writes (`grep -c $'\r' <file>` prints `0`). A Linux test that checks the write call is a technical check and does not count as this proof.

### The PO inbox

7. **As the PO, I want the inbox mod to list what my Manager asks, so I can answer.**
   - Given a Manager session on Windows with an `inbox.jsonl` and `escalations.md` that contain emoji, accents and `<`/`|` characters, When the mod refreshes, Then the list shows each item and no error line (`squad-inbox list failed`) appears. The same must hold when the PO's `squad-inbox list` runs from a plain prompt.
   - **Printing counts:** `squad-inbox list`, `list --json`, `list --open` and `read` print non-ASCII (`→`, emoji) to a pipe or terminal under a non-UTF-8 locale (`LC_ALL=C PYTHONUTF8=0`) with exit 0 and empty stderr. An `encoding=` on `open()` alone does not satisfy this (F0).
8. **As the PO, I want to answer an item (pick an option, type a note) and have it reach the Manager, so the work unblocks.**
   - Given an open item, When I answer it with text containing emoji, Then the `escalations.md` row holds my answer unchanged, `inbox.jsonl` records the answer, and the item shows as answered.
9. **As the PO, I want the inbox not to lose or double a row when two things write at once (the mod and a Manager's `squad-inbox add`), the same as on Linux.**
   - Given two writers acting at the same moment, When both finish, Then every row from both is present once, and no half-written line exists.
   - **Proof split:** Linux, with `fcntl` hidden: 2 writers x 50 rows in parallel give 100 rows, none doubled, every line valid JSON (proves the fallback lock logic only). Windows: two Git Bash windows add 20 rows each at the same time and the list shows 40 (checklist W9); only that proves the real Windows lock.
10. **As the PO, I want the other helpers and the hooks not to crash a Windows session.**
    - Given a Windows session, When `squad-label`, `squad-usage`, `squad-process`, `squad-respawn`, `squad-retire`, `squad-close`, `squad-log-message`, `squad-usage-hook` (the Stop hook that fires the cost rules) and `squad-notify` run, Then each ends in one of two ways and never with a traceback: (a) **exit 0 and nothing on stderr**, or (b) **one line on stderr that names the cause (for example the missing tool, `jq`) and a non-zero exit.**
    - Printing non-ASCII follows story 7 (F0). Toasts (`squad-notify`) are **unsupported on Windows** (PO, E3): they take path (a), nothing shown, exit 0, empty stderr.
    - Hooks: fed a sample payload under the simulated Windows run, `squad-usage-hook` and `squad-log-message` take path (a) or (b) as above. That the real Claude Code hook runs them on real Windows is **not verified** in this scope; the checklist says so and the PO decides at check-in whether to add it (BA decision for C6: widening to "hooks must fire on Windows" would be a scope change, not mine to make).
    - *Scope settled by O1 (closed).*

### Checkout and no regression

11. **As the PO, I want a Windows checkout to keep LF in `bin/*` and every text file, so bash scripts keep working.**
    - Given a clone on Windows with `core.autocrlf=true`, When I run `git ls-files --eol`, Then the working tree shows `w/lf` for every `bin/` script and every text file, and binary files are untouched. Today the index is already LF (all 386 tracked files are `i/lf`); only the checkout converts. **No tracked text file may stay CRLF** (none does today).
   - **Proved on Linux, no simulation:** `git clone -c core.autocrlf=true` gives 0 CR in `bin/` (today: 17 files have CR), `git ls-files --eol` shows only `w/lf`, `git add --renormalize .` changes nothing, `git check-attr eol bin/squad-spawn` says `lf`. The PO step (W12) is a spot check.
12. **As the PO, I want a short checklist to run on real Windows at check-in, so I can sign the part nobody here can test.**
    - Given the pod's evidence, When the check-in comes, Then I get **at most 12 numbered steps** (BA decision; QA blackbox's draft is `evidence/windows-checklist.md`) for a plain Git Bash prompt, each with the command and the one thing to see (stories 1-9 and 11, the CR counts of story 6 merged into the steps that write the files, and the two-window step of story 9), and a line saying what the squad proved on Linux and what only Windows can prove, including "hooks firing on real Windows: not verified".
13. **As the PO, I want Linux and macOS to behave exactly as before.**
    - Given the Linux suite (`CLAUDE.md` → Running tests), When it runs on the final branch with `--tz`, Then it is green, and **every test file the tickets touch** (listed in the receipt) also passes under `PYTHONUTF8=0 LC_ALL=C`.
   - Under a UTF-8 locale, the output of every read-only command is **byte-identical to 0.3.2**, and the files written are byte-identical (QA blackbox diffs against a `git archive` of 0.3.2).

## Out of scope (BA decision)

- `squad-spawn --dry` vs `--dry-run`: no change (the issue says so).
- Unquoted paths in the `would run:` dry-run line: cosmetic, optional; do it only if free.
- Rewriting `squad-spawn` in Python (an issue option): not required; Git Bash is the supported shell, and `bash` is a stated prerequisite (story 3).
- WSL, macOS fixes, PowerShell/cmd as the shell: not supported targets.

## Open points

Touches now (PO, E2): `bin`, `.gitattributes`, `tests`, `hooks/po-inbox`. F1 is confirmed as the likely cause by the Manager (`squadinbox.py:8` import, `:214` `flock`); the PO is asked to confirm.

- **O1 (closed, PO via Manager E3 (a)):** required = stories 1-9, 11-13. Story 10 = `squad-respawn`, `squad-retire`, `squad-close`, `squad-usage` (and the other helpers) must not crash; toasts (`squad-notify`) are unsupported on Windows and do nothing quietly.
- **O2 (prerequisite, to the Tech Lead):** `squad-respawn`/`squad-retire` need `jq`, which Git for Windows does not ship. Either remove the `jq` use or state it as a prerequisite with a clear message (as `bash` in story 3). BA has no preference; the message must name the missing tool.
- **O3 (fact, PO; no traceback given, so F1 `fcntl` is the working cause):** how Claude Code starts `squad-inbox` for the mod on Windows (the script has no extension), and the full traceback. If the first run of `squad-inbox` itself fails with `WinError 193`, story 7 needs a launcher too. Ask the PO to paste the traceback; until it arrives, assume F1.

## Agreement

- BA: final. QA blackbox: agrees to the 13 stories subject to C1-C6 (`$SCOPE_DIR/evidence/qab-review-of-spec.md`); all six are applied (BA 2026-10-17). C1 printing named in stories 7 and 10; C2 story 10 is exit 0 with empty stderr, or one line naming the cause and non-zero; C3 LF is Windows-only proof; C4 story 11 proved on Linux with a `core.autocrlf=true` clone; C5 story 13 names every touched test file and byte-identity vs 0.3.2; C6 hooks: no-crash with a sample payload, real firing on Windows not verified and listed in the checklist (widening it is the PO's call). Checklist length: at most 12 steps (story 12); prerequisite checks 0a-0c do not count. QA blackbox's sign-off on story 10 follows E3 (answered: PO picked (a)).
