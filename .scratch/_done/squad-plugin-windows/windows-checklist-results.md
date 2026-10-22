# Windows checklist results: squad 0.3.4 (sha c1954741518a33078fc5c7c2a66009139015cc89)

**Verdict:** 12 of 13 items pass or pass with a note; **T fails (10 test failures)**, **W3's CR check fails because the Manager's own edit script writes CRLF**, and **W7 (the pane answer) is waiting on the PO**.

**Run by:** Claude on the PO's machine, 2026-10-17, native Windows 11, Git Bash, Python 3.14.6, herdr running. **Path form typed:** Git Bash `/c/Users/...` only (the backslash form was not tried).

## Results

| # | Result | Evidence |
|---|---|---|
| 0a | pass | `python3 --version` → 3.14.6 (Store alias, reports a real version) |
| 0b | pass | `jq-1.8.2` |
| 0c | pass | `which bash` → `/usr/bin/bash` = `C:\Program Files\Git\usr\bin\bash.exe`, not System32. Git 2.56.0.windows.2 |
| env | pass | `[$PYTHONUTF8][$PYTHONIOENCODING]` printed `[][]` |
| W1 | pass | `squad-start --squad chk --resume resume-check` from `Guardian - Learn 🦀`: rc 0, tab `🦀 Manager`, no WinError 193, no traceback |
| W2 | pass | New scope started, rc 0, Manager tab ready, `scope.md` had 0 CR bytes right after `squad-start` |
| W3 | **fail (CR check)** | Four agents spawned (tech-lead, dev, qa-whitebox, qa-blackbox), each `squad-spawn` rc 0, emoji tab labels, no `UnicodeDecodeError`. **`roster.md` CR count 11, `scope.md` CR 16** after the Manager edited them. See finding 2 |
| W4 | pass | `--dry-run` for manager, dev, qa-blackbox: rc 0, `would run:` printed |
| W5 | pass | `squad-inbox list` prints `→ 🦀 é` titles correctly |
| W6 | pass | `list --json` rc 0, valid JSON |
| W7 | **pending PO** | Observed so far: the mod band `Inbox 1 to answer [ Open inbox (i) ]` drew in the Manager's screen, and changed to `2 to answer` after an item was added from outside (the mod runs `squad-inbox list` on Windows, no `⚠`). **Not yet seen:** an `answer` event with `source: "pane"` and a `delivered` event in `scopes/resume-check/inbox.jsonl` |
| W8 | pass | Real CRLF bytes in `--body-file`; stored body `line one\nline two\n\nthree`; answer row ends `…<br>é 🦀 note` with no trailing `<br>`; 0 CR bytes in `escalations.md` and `inbox.jsonl`; 0 literal `\r` |
| W9 | pass (with deviation) | Two concurrent loops of 20 `add` from one shell (not two windows): 40 titles, 0 duplicates, 0 missing, unique ids, 0 errors, no `PermissionError` |
| W10 | pass | `squad-process show qa-blackbox` and `squad-usage` print, no traceback. `squad-usage` listed a row for all 5 agents |
| W11 | pass | `squad-retire` and `squad-close --scope` rc 0, tabs closed, worktree removed, scope archived to `scopes/_done/`, `process-log.md` 0 CR |
| W12 | pass | Clone with `core.autocrlf=true`: 0 files not `w/lf`. Clone sha equals the installed sha |
| T | **fail** | 102 tests, **5 failures + 5 errors**, 10 skipped (all with reasons). Details in finding 1 |

## Findings for the fixer

### 1. T: 10 test failures on Windows (not green)

**Summary:** the five named files do not reach "0 failures and 0 errors". Every failure looks like a test-harness assumption, not a product bug, but `RUNNING-ON-WINDOWS.md` promises 0.

| Test | Failure | Cause |
|---|---|---|
| `test_squadinbox_answer.InvalidUtf8Test.test_refused_and_nothing_written` (5 subtests: `add --title Q\xff`, `add --options Q\xff`, `answer --text`, `answer --note`, `withdraw --reason`) | `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff` at `subprocess.list2cmdline` | Windows cannot pass invalid-UTF-8 bytes in argv, so the test fails before the CLI starts. Skip on Windows |
| `test_squadinbox.AddReadTest.test_add_answer_row_on_top` | `…line \| two<br><br>three` vs expected `<br>three` | The test writes its body file in text mode, so `\n` becomes `\r\n`. A blank line then gives `<br><br>`. Write the fixture with `newline="\n"` |
| `test_squadinbox.RowWriterTest.test_each_break_becomes_one_br` (`'\r\n'` case) | `t0<br>one<br><br>two` vs `t0<br>one<br>two` | Same text-mode fixture issue |
| `test_squadinbox_answer.AnswerTest.test_round_trip` | `'line one\r\nline two\r\r\nthree' != 'line one\nline two\r\nthree'` | The test pipes stdin with `text=True`, which doubles the line ends. Send bytes |
| `test_squadinbox_answer.AnswerTest.test_stdin_meaning` | `'the note\r\nsecond' != 'the note\nsecond'` | Same stdin text-mode issue |
| `test_po_inbox_mod.PoInboxModTest.test_plugin_test_passes` | 2 failures in `mod.test.ts`: `active: manager with SCOPE_DIR` and `…only GOAL_DIR` | Expected `/h/scope/inbox.jsonl`, got `C:\h\scope\inbox.jsonl`. The test hard-codes POSIX paths |

**Verified by hand:** the CLI itself handles real CRLF bytes correctly (W8). Only the test helpers produce the doubled `\r`.

### 2. W3: the Manager rewrites `scope.md` and `roster.md` as CRLF

**Summary:** both files are pure LF after `squad-start` and pure CRLF after the Manager edits them. The cause is the Manager's own Python, not `squad-spawn`.

- **Cause:** `agents/manager.md` line 28 says to edit `roster.md` "with a small script that keeps the rest of the file". The script the Manager wrote was `open(p,'w',encoding='utf-8').write(s)` with no `newline="\n"`. Windows turns every `\n` into `\r\n`.
- **Evidence:** the Manager's transcript (`ada0160b-…jsonl`) has the heredoc; `scope.md` went CR 0 → 16, `roster.md` 0 → 11, mtimes match the edits.
- **Why it matters:** ADR 0011 D1 says a `\r` breaks bash `$(...)` parsing. `squad-retire` and `squad-close` still worked on the CRLF roster here, so the damage was not seen.
- **Fix options:** (a) say `newline="\n"` in `manager.md` (and the Team Lead's equivalent line), (b) add a small `squad-roster set` helper so no role writes the file by hand, (c) have the readers strip `\r`.

### 3. Smaller things

- **Trust prompt:** `squad-start` into a never-trusted folder fails with `agent_not_ready` (the Manager waits on Claude Code's "trust this folder" prompt). It rolled back cleanly (no scope left), but it leaves the Manager tab running under the old name, so the retry would collide. Linux behaves the same. A one-line hint ("open the tab and trust the folder") would save time.
- **W8's `\r` command:** `grep -c '\\r' inbox.jsonl` counts every line containing `r` in this Git Bash. Use `grep -cF '\r' inbox.jsonl` (gives 0 when clean).
- **Dry run:** `would run:` prints the project path unquoted (`…/Guardian - Learn 🦀`), as in the first issue. Cosmetic.
- **Orphan tab:** `chk-orphan-trust` (tab `w5:t2`) is the first Manager that waited on the trust prompt. It is idle and still open.

## Deviations from the checklist

- **Project:** a scratch repo `C:\Users\84084\workspace\winchk\Guardian - Learn 🦀` (space and emoji), not the real project.
- **W3 and W11:** the Manager was driven by a prompt from this session, not typed by the PO.
- **W8:** CRLF bytes written with `printf`, not Notepad.
- **W9:** two background loops in one Git Bash, not two windows.

## Clean up

- Delete `C:\Users\84084\workspace\winchk` and close tab `w5:t2` when done.
