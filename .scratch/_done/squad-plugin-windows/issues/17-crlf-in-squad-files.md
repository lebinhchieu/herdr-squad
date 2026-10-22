# J The Manager and Team Lead never write CRLF into squad files (and the W8 grep)

Status: ready-for-agent
Type: task
Source: `windows-checklist-results.md` Finding 2 (W3 CR check: `roster.md` CR 11, `scope.md` CR 16) and the "W8's `\r` command" note
Touches: `agents/manager.md` (line 28 only), `agents/team-lead.md` (line 28 only), `tests/test_crlf_squad_files.py` (new), `.scratch/squad-plugin-windows/windows-checklist.md` (W3 and W8 rows only), this ticket file. `bin/*` only if the reader test of AC 4 fails for a helper (named in the hand-in; the fix is the smallest strip of `\r`).
Does not touch: `tests/test_squadinbox*.py`, `tests/test_po_inbox_mod.py`, `hooks/`, `templates/`, `process.md`, `plugin.json`. Ticket 16 owns the first four; no file is shared with it.
Harness: `unittest` from inside `tests/` (`cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_crlf_squad_files test_manager_inbox_read test_team_lead_role test_team_lead_perms test_windows_safe`). Base: main `c195474`, `--base c195474`, fresh Developer name.
Blocked by: none. Parallel with 16.

## Decision (Tech Lead): (a) as the fix, (c) as a test, no helper
- **(a)** the two instructions tell the role to open the file with `newline="\n"`. This removes the cause: the Manager's own script wrote through Python's default text mode, which Windows translates.
- **(c)** is **not a code change**. Audit by reading, 2026-10-17: every Python reader of `roster.md`/`scope.md` (`squad-usage`, `squad-start`, `squad-migrate`) uses `read_text`, which already folds `\r\n` to `\n` (text-mode universal newlines) and the table readers `.strip()` each cell; the bash readers (`squad-close` awk on columns 2-4, never the last column; `squad-spawn` `grep` with `[[:space:]]*$` and `tr -d '[:space:]'`; `squad-close:75` grep) are CR-safe by the same reasons. The claim is cheap to make true forever, so it becomes a test (AC 4). A reader that fails is fixed with the smallest strip of `\r`; none is expected.
- **(b) rejected:** a `squad-roster set` helper is a new command, a new test surface and a new thing to learn for one line of wording (ADR 0011 already states the write rule for `bin/`). Revisit only if a role still writes CRLF after this change.
- Not changed: `templates/squad/process.md:42` ("small script that keeps the rest") says nothing about line ends; touching it needs a process-version bump and a history copy. Listed as a follow-up for the PO, not part of this ticket.

## What
1. `agents/manager.md:28` (the **The roster.** bullet): after "with a small script that keeps the rest of the file, never `command > file`" add one sentence. It names the Python call: `open(path, "w", encoding="utf-8", newline="\n")` (default text mode writes CRLF on Windows, and a `\r` breaks bash `$(...)` parsing, ADR 0011), and the check `grep -c $'\r' <file>` must print `0`. Keep every other sentence of the bullet, in order. Plain ASCII in the added text.
2. `agents/team-lead.md:28` (the **Roster:** bullet): the same sentence, shorter allowed, same Python call and the same check.
3. `.scratch/squad-plugin-windows/windows-checklist.md`:
   - **W8:** replace `grep -c '\\r' inbox.jsonl` with `grep -cF '\r' inbox.jsonl` (literal backslash-r, prints 0 on a clean file; the old form counted every line holding `r` in Git Bash). No other word of the row changes.
   - **W3:** the CR check line reads `roster.md` and `scope.md` (both): `grep -c $'\r'` on each; the "You should see" cell says a count other than `0` is a fail: send the file. 0a-0c, W1-W12 and T stay in the same order; W7 stays marked open for the PO; T's text keeps the five files and `0 failures and 0 errors`.

## Technical AC (Tech Lead, with QAW and QAB)
1. **J1/J2 wording.** `test_crlf_squad_files.py` selects the roster bullet of each file by its leading label (`- **The roster.**`, `- **Roster:**`), reading as UTF-8, and asserts it contains `newline="\n"`, `encoding="utf-8"` and `$'\r'`, and that the original text (`small script`, `never` `command > file`, `re-reads the file just before writing` in the Team Lead's) is still there. Each assertion fails on `c195474` and passes on the tip (failing run quoted in `dev-evidence.md`).
2. **The example works.** The test runs the instruction's Python call verbatim in a subprocess on a temp `roster.md`-shaped file: result has 0 CR bytes and only the intended line changed. A one-off (not committed) run with text-mode translation forced to CRLF (QAB: `sitecustomize` wrapper of `open` with `newline` default `\r\n`) shows the `newline="\n"` form still writes LF and the form without it writes CRLF. LIMIT: not real Windows; the PO's rerun of W3 is the proof.
3. **J4 Linux unchanged.** `git diff c195474 HEAD -- agents/` shows only the two added sentences (`git diff -U0` quoted). `bin/` has no diff unless AC 4 forced one.
4. **J3 readers tolerate CRLF.** In the same new test file, a scratch squad (reuse the scaffolding of `tests/test_squad_usage.py`, `test_squad_close.py`, `test_squad_spawn.py`, `test_squad_retire.py`, `test_squad_respawn.py`; name what is reused) holds an LF `roster.md`/`scope.md` and a CRLF copy of each. For each of `squad-usage --get <agent>`, `squad-usage` (table), `squad-close --scope <s> --dry-run`, `squad-spawn <role> <name> --scope <s> --dry-run` (the `goal:` and `design:` greps) and `squad-retire`'s Team Lead branch (`squad-usage --get` path), stdout, stderr and exit code of the CRLF run equal the LF run, and no output line contains `\r`. `squad-respawn` and `squad-label`: run them too if the scaffolding makes it cheap; if not, say in the hand-in why (`squad-label` reads neither file). A failing helper gets the smallest fix and is reported to the Tech Lead before it is committed.
5. **W8-grep (QAB).** `grep -cF '\r' <file>` on a file with one literal backslash-r prints `1`, on a clean file prints `0`; run both and quote them. The old command in the same Git Bash claim is gone from the checklist.
6. **W3-chk / X.** `git diff -U0 c195474 HEAD -- .scratch/squad-plugin-windows/windows-checklist.md` touches only the W3 and W8 rows; the list of row ids (0a, 0b, 0c, W1-W12, T) is identical before and after (quote `grep -o '^| W\?[0-9a-cT]*' ...`).
7. **Diff scope.** `git diff --stat c195474 HEAD` lists only the Touches paths. `git merge-base --is-ancestor c195474 HEAD` printed in the hand-in.
8. `tests/test_windows_safe.py` still passes (the new test file opens with `encoding="utf-8"` and `newline="\n"` where it writes). UTF-8 locale and `PYTHONUTF8=0 LC_ALL=C PYTHONIOENCODING=cp1252`: both pass for the new file. The Developer runs only the files it touched or read; the Tech Lead runs `--tz` on the integration sha.

## Comments
- Role-instruction change (`agents/manager.md`, `agents/team-lead.md`): the Manager listed it for the PO in iteration 5 ("J may change agents/manager.md and team-lead.md"). Prompt text only; no live run.
- Promotion (Tech Lead, integration task): one bullet in ADR 0011 "Rules for `bin/`" or a new line under it: a role that edits a squad file by script writes it with `newline="\n"`; readers rely on text-mode `read_text` for CRLF tolerance. See `promote.md`.
