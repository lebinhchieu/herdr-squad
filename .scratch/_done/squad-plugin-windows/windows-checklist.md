# Windows checklist for the PO

Twelve steps (W1-W12; W7 is the pane check from `issue-po-inbox.md` section 1) after the 0a-0c checks, about 15 minutes, in Git Bash. Stop at the first failure and send me the full error text.

## What the squad proved on Linux, and what only you can prove

- **Proved on Linux** (simulated Windows: non-UTF-8 locale, `squad-spawn` not directly executable, `fcntl` hidden, no `bash`, no `jq`): the launcher path, UTF-8 in and out, the inbox list and answer, the lock fallback logic, LF on a `core.autocrlf=true` clone, Linux output unchanged.
- **Only Windows proves:** real tabs and agents opening, `\n` not turning into `\r\n` on write, the real Windows file lock, how Claude Code starts `squad-inbox` for the mod.

## Known limit, read before W9

If two Git Bash windows replace the same file at the same moment, Windows may refuse one `os.replace` with `PermissionError`. This is a known gap that was not fixed (`promote.md`). The lock itself must still work. If W9 shows a `PermissionError` on a rename, re-run only the failed `add` lines; if all 40 titles are then there, once each, report W9 as **"known limit hit"**, not as failed. Any other error, a duplicate title or a title still missing is a fail.

## Before you start

- **0a** `python3 --version` prints a version (a Microsoft Store stub that opens the Store is a fail). The Store alias that reports a real version (the PO has 3.14.6 this way) works; it is not a fail. The pane starts `python3 <plugin>/bin/squad-inbox`, so this is the `python3` the pane uses.
- **0b** `jq --version` prints a version. `jq` is a documented prerequisite: if it is missing, install it first; that is not a plugin bug.
- **0c** `bash --version` is Git's (`which bash` shows a `Git\...` path), not `C:\Windows\System32\bash.exe`. Also `git --version`.
- Git Bash, herdr running (`HERDR_ENV=1`).
- The plugin version under test, from its cache. Its sha: `__________`
- **No `PYTHONUTF8` or `PYTHONIOENCODING`.** `echo "[$PYTHONUTF8][$PYTHONIOENCODING]"` must print `[][]`.
- A project path with a space and an emoji (like `Guardian - Learn 🦀`) and a squad with one scope whose Manager is not running. Note which form you typed: `/c/Users/...` or `C:\Users\...`. Run W1 once from each form if time allows. A backslash path or a path cut at the space in an error is a real finding: send the exact form and the full error.
- `CR` check used below: `grep -c $'\r' <file>` must print `0`.

## Steps

| # | Run | You should see | ✓ |
|---|---|---|---|
| W1 | From the space-and-emoji project path: `squad-start --squad <squad> --resume <scope>` | A Manager tab titled `🦀 Manager`, ready. No `WinError 193`, no traceback. | |
| W2 | `squad-start "windows check scratch" --squad <squad> --touches docs --yes`, then the CR check on the new `scope.md` | New scope folder, Manager tab, no traceback. CR count `0`. | |
| W3 | In that Manager (space-and-emoji path, no env vars exported), have it spawn a Tech Lead, a Developer, QA whitebox and QA blackbox. CR check on `roster.md` and `scope.md` (both): `grep -c $'\r'` on each. | Four tabs with their emoji labels, each ready. No `UnicodeDecodeError`. CR count `0` on each; a count other than `0` is a fail: send the file. | |
| W4 | `squad-spawn <role> <name> --scope <scope> --dry-run` for `manager`, `dev`, `qa-blackbox` | Each prints `would run:` and exits 0. | |
| W5 | `squad-inbox list` in the scope folder (`SCOPE_DIR` set). If you try `squad-inbox answer --option N` by hand, add `</dev/null`: with only `--option` it waits on stdin (same on Linux, by design). | The list prints, including any `→` in a title. Not `squad-inbox list failed`. | |
| W6 | `squad-inbox list --json` | JSON prints, exit 0. | |
| W7 | **Pane check (iteration 2, the one that was never confirmed).** In a Manager session of the scratch squad, run `/inbox`. Note the item list. Answer one answer-item from the pane. Then run `tail -5 <scope>/inbox.jsonl` and read the last lines. | The pane lists the items with no `⚠ squad-inbox list failed` line. After the answer, `inbox.jsonl` has an `answer` event with `source: "pane"`, then a `delivered` event, and the Manager receives the answer. A pane that shows `⚠` or `ENOENT`/`WinError 193`, or an answer with no `source: pane` event, is a fail: send the full pane text and the last 10 lines of `inbox.jsonl`. |
| W8 | `squad-inbox add --kind read --title "é → 🦀 check" --body-file <a file saved with CRLF endings, e.g. from Notepad>`, then `squad-inbox list`, then `squad-inbox answer <id> --source chat --option <letter> --note "é 🦀 note" </dev/null` on an answer item (do not pipe the note through `echo`: it adds a newline, so the row ends in `<br>`). CR check on `escalations.md`, and `grep -cF '\r' inbox.jsonl` (text `\r`, not a CR byte). | The title and note read back as typed. The body has no stray `\r`, and the answer row has no trailing `<br>`. CR counts `0`. | |
| W9 | Open two Git Bash windows. In each run `for i in $(seq 20); do squad-inbox add --kind read --title "w9 $i" --body-file <file>; done` at the same time. Then `squad-inbox list --json` and count the `w9` titles. | 40 titles, none twice, no error from the lock. A `PermissionError` on a rename that clears on re-run is the known limit above. | |
| W10 | `squad-process show qa-blackbox`, then `squad-usage` | Both print, no traceback. | |
| W11 | `squad-retire <a name from W3>`, then `squad-close --scope <scratch scope>`. CR check on `process-log.md`. | Both finish, the tabs close, no traceback. If one says `jq` is missing (you skipped 0b), that is a fail unless the message names `jq` and what to install. | |
| W12 | `git clone -c core.autocrlf=true <plugin repo> x && cd x && git ls-files --eol \| grep -v "w/lf"` | Nothing listed (binary files show `w/-text`: ignore those). | |

## Test run (separate line, not a numbered step)

- **T** In Git Bash, from the plugin folder: `cd tests && python3 -m unittest test_squadinbox test_squadinbox_win test_po_inbox_contract test_po_inbox_mod test_squadinbox_answer -v` (this is `tests/RUNNING-ON-WINDOWS.md`; `run_suite.py` needs `fcntl` and cannot run on Windows). You should see `OK` with some tests skipped, each with a reason, and **0 failures and 0 errors**. Send me the last 5 lines and every `skipped` line. A failure is not a skip: send its full text, it may be a product bug.

## Not on this list (decided by the PO in E3)

- Toast notifications and `/proc` features: unsupported on Windows (PO, E3 (a)). `squad-respawn`, `squad-retire`, `squad-close` and `squad-usage` must not crash: W10 and W11.
- A step for "no `bash`" is dropped: it is proved on Linux.
- **Hooks (BA's C6):** the squad proves on Linux only that the hook scripts do not crash on a sample payload. Whether Claude Code really fires them on Windows is **not verified**. One cheap look, no step number: after W3, `squad-usage` should show a row for each agent. A Stop-hook event line in `usage-events.jsonl` is a bonus. Tell me what you see.

## Clean up

- Delete the scratch scope from W2 and the items from W8 and W9.

## What to send back

- 0a-0c, W1-W12 and T as pass, fail or skipped.
- The full error text for each fail.
- The sha from "Before you start" and the path form you used.
