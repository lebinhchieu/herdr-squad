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

# Iteration 2: the PO inbox on Windows, follow-ups

**One line:** after 0.3.3 the `squad-inbox` CLI works on Windows but the pane that starts it was never shown to run, a CRLF body keeps a stray `\r`, the Manager writes plain notes as answer rows, and the test suite fails on Windows for reasons that are not product bugs. Source: `issue-po-inbox.md` ("Done when"). Tasks A-D of `$SCOPE_DIR/iterations/2.md`. Stories 1-13 above still hold; these add to them. Technical AC live in the tickets.

## Findings the BA made (iteration 2)

- **F4: `tests/run_suite.py` imports `fcntl` (line 14), so the runner itself cannot start on Windows.** "Skip the Windows-only failures" is not enough for story 17 on its own: the PO needs a written way to run the test files on Windows (for example one file at a time with `python3 -m unittest`). Tech Lead / Team Lead decide the form.
- **F5: `agents/manager.md` line 95 says "rows written by hand still work".** That sentence is the likely cause of the hand-written rows E5-E8; story 16 removes the permission, not only adds a new rule.
- **F6: the pane's three `$.process.run` calls were never run by the real Claude Code host on Windows.** Linux can prove the argv and that the pane still works on Linux; only Windows proves the host starts it (story 14, proof split).

## User Stories (iteration 2)

14. **As the PO on Windows, I want the inbox pane to start `squad-inbox` by itself, so I can see and answer what my Manager asks from the pane.** (task A)
    - Given the plugin at a path with a space and an emoji (like `C:\Users\x\Guardian - Learn 🦀\...`) and a Manager session with `inbox.jsonl` and `escalations.md`, When the pane lists, answers an item and marks it delivered, Then **every** call the pane makes to `squad-inbox` is started as `python3` followed by the script's full path, **as separate arguments** (the path is one argument, never split at the space), and none runs the extensionless script directly.
    - Given an open answer item, When I answer it from the pane, Then `inbox.jsonl` holds an `answer` event with `source: pane` and then a `delivered` event, and `escalations.md` holds my answer.
    - Given a plugin copy where `bin/squad-inbox` is **not executable** (so a direct start fails like `ENOENT` or `WinError 193`) and `python3` on `PATH`, When the pane lists and answers, Then it works with no `squad-inbox list failed` line. With the exec bit set (Linux), the rows, events and screen text equal 0.3.3's apart from ids and timestamps.
    - Given `python3` cannot start, When the pane refreshes, Then the pane shows its normal error line (one line, no freeze, no blank pane).
    - **Proof split:** Linux (QA blackbox, `claude plugin test` with a stub host and a recording stand-in for `python3`; the pane's answer being taken by a live Manager is the PO's run): the argv above for each of the pane's calls, and the pane behaves as on 0.3.3 (same list, same answer row, same events). **Only Windows proves** that the Claude Code host's `$.process.run` starts it: the PO runs the issue's section 1 check (checklist W7, extended). If W7 fails, the squad has not met this story.
15. **As the PO, I want a body file with Windows line endings stored as plain lines, so my inbox shows no stray break or hidden `\r`.** (task B)
    - Given `--body-file` with CRLF endings (`line one\r\nline two\r\n\r\n- bullet\r\n`), When I run `squad-inbox add` (kind read and kind answer), Then the stored body is `line one\nline two\n\n- bullet`: no `\r` in `inbox.jsonl` or `escalations.md` (`grep -c $'\r'` prints `0`), and the answer row ends with `- bullet` and **no trailing `<br>`**.
    - Given a body file with lone CR endings (old Mac style, `a\rb\r`), Then each CR counts as one line break: stored `a\nb`.
    - Given a body with mixed endings (LF, CRLF, CR in one file), Then the result is the same lines as the all-LF file, one break each.
    - Given a body with LF endings, or the body on stdin (quoted heredoc), Then the stored result is **byte-identical to 0.3.3**.
    - Edge cases (QA blackbox B3): a CRLF at the very end, a blank CRLF line and a body with non-ASCII (é, →, 🦀) store clean. A body that is empty, or only `\r\n`, is refused exactly as on 0.3.3 ("an item needs a body", non-zero), not stored.
    - Out of scope (BA decision): the `--title` text, the answer text from `squad-inbox answer`, `--options` and `--rec`. The issue names only the body file. If the PO wants them too, that is a new item.
    - **Proof split:** all of it is provable on Linux (the CRLF is in the file, not made by the OS). The Windows checklist adds one CRLF body file (W8).
16. **As the PO, I want the Manager's notes that need no answer to show under "to read", so the inbox does not claim things wait on me that don't.** (task C)
    - Given `agents/manager.md` as the Manager reads it, Then it says in one place that a note that needs no answer (informational, "READ, not blocking", progress, a result) goes in with `squad-inbox add --kind read --title ...` and a quoted-heredoc body, and that a row for it is **never written by hand** in `escalations.md`.
    - And the sentence that lets hand-written rows stand (F5) is gone or is reversed into the rule above.
    - And `--kind answer` stays the only way an item that waits on the PO is written (`add` writes the row); the existing rules (one `add` per Bash call, reply is the printed line only, no merge/push/deploy items) are unchanged.
    - Given a scratch Manager home, When a read item is added, Then `squad-inbox list` counts it under "to read" and `escalations.md` gets **no** row for it (regression check of the existing behaviour, on Linux).
    - And the same text still sends a question that needs the PO's answer to an answer item (`--kind answer`), so the two cases are not blurred; and no other file in `agents/` differs from 0.3.3.
    - **Bar (agreed with QA blackbox):** the instruction text, plus the command it shows run verbatim in a scratch home (quoted heredoc; `|`, quotes, `$` and backticks in the body survive). QA blackbox may read `agents/manager.md`: it is a role instruction, not code. If their settings deny it, the Tech Lead pastes the diff into the task's evidence folder.
    - **Proof split:** the instruction text is checked by reading it. Whether a live Manager obeys it **only a real Manager session shows**: the PO sees at the next check-in whether informational notes arrive as read items. Clearing the old rows E5-E8 in `scopes/scene-split` is the PO's call and not part of this iteration.
17. **As the PO on Windows, I want the test suite to say "skipped, and why" instead of failing for things that are not bugs, so a red test on Windows means a real problem.** (task D)
    - Given the 12 Windows failures of `issue-po-inbox.md` in `test_squadinbox`, `test_squadinbox_win`, `test_po_inbox_contract`, `test_po_inbox_mod` and `test_squadinbox_answer`, When those files run on real Windows, Then there are **0 failures and 0 errors**, and each skipped test prints a reason that names its cause: no `termios`/`pty`; symlink privilege; file modes; `os.execv`; a simulated-Windows test that needs a real `fcntl`; POSIX-only paths. (A fixture that writes in text mode is fixed by writing LF, or skipped with its reason; fixing is preferred.)
    - A skip is **conditional on Windows or on the missing module**, never unconditional. On Linux **no test is skipped for these causes**: the number of tests run per file equals 0.3.3's, and the suite is green.
    - Check on Linux (QA blackbox D4): forcing the Windows condition (patching `sys.platform`/`os.name`, or hiding the module the skip keys on) skips exactly the listed tests and no more.
    - A test that fails on Windows for a cause **not** in the list is not skipped. It is reported to the Team Lead as a possible product bug.
    - The way to run the test files on Windows is written down in one place a PO can find under `tests/` (F4): the command, what it skips and why. The PO does not need the runner `run_suite.py` to work on Windows.
    - No product code changes under this story (`tests/` only).
    - **Proof split:** Linux proves the skips are conditional (same test count, no skips, green, also under `PYTHONUTF8=0 LC_ALL=C`) and that each reason is a real sentence. **Only Windows proves** the 0 failures: the PO runs the documented command at check-in (new checklist line). The squad does not claim "green on Windows".
18. **As the PO, I want Linux and macOS exactly as before, and the Windows checklist to match.** (integration)
    - Given the final branch, Then the full suite with `--tz` is green; every touched test file also passes under `PYTHONUTF8=0 LC_ALL=C`; under a UTF-8 locale the output of every read-only command and the files written are byte-identical to 0.3.3 (QA blackbox diffs against a `git archive` of `59a8d1b`), except the intended changes of stories 14-17.
    - And `.scratch/squad-plugin-windows/windows-checklist.md` still has **at most 12 numbered steps** (W1-W12) plus a separate line for the test run (story 17), and says what to send back on a failure: W7 now includes "answer one item from the pane, then see an `answer` event with `source: pane` and a `delivered` event in `inbox.jsonl`" (the issue's section 1 check); W8 includes one CRLF `--body-file` with CR count `0` (story 15). It notes that a bare `squad-inbox answer --option` reads stdin and needs `</dev/null`, and that `python3` may be the Store alias (0a).
    - And the ADR 0011 D6 text is updated to the decision that holds (story 14), see "For promotion".

## For promotion (to the Tech Lead; one line each)

- **Rule:** the pane runs `python3 <plugin root>/bin/squad-inbox ...` as separate arguments (updates ADR 0011 D6; the "would open a T5" sentence is then done).
- **Rule:** `--body-file` input is normalised: CRLF and lone CR become LF before the `<br>` conversion.
- **Rule:** a Manager writes only an item that waits on the PO as an answer item; every other note is a read item; an `escalations.md` row is never written by hand.
- **Rule:** Windows-only test failures are skipped with a named reason; the skip is conditional, and Linux runs every test. `tests/run_suite.py` needs `fcntl`, so on Windows the files run one by one.
- **Glossary:** no new term. `Escalation` (CONTEXT.md) already says an escalation is an answer item; "read item" is used by the inbox docs and by ADR 0007 (check, add to the glossary only if missing).

## Out of scope (iteration 2, BA decision)

- E5-E8 in `scopes/scene-split` (PO's call). `E7` saying RESOLVED in an open row: same.
- Real Windows runs by the squad (impossible here); the PO does them at check-in.
- Making `run_suite.py` run on Windows; the Store-alias `python3` note (issue Notes) beyond the checklist's existing 0a step.
- Changing the order or number of the pane's calls; new pane features.

## Agreement (iteration 2)

- BA: final for iteration 2 (2026-10-17). QA blackbox proposed A1-E2 (`$SCOPE_DIR/evidence/iter2/qab-proposed-ac.md`); all merged into stories 14-18. Their five open points: (1) A2 by `claude plugin test` with a stub, real run is the PO's: yes; (2) answer-note CRLF: out of scope; (3) C3 bar = instruction text + runnable example: yes; (4) D = skip with reasons plus a written way to run the files on Windows: yes; (5) QA blackbox may read `agents/manager.md`: yes (their settings decide; fallback above). One correction to their B3: an empty or only-CRLF body is refused as on 0.3.3, not exit 0. QA blackbox confirmed stories 14-18 and this Agreement, including the B3 correction (2026-10-17).
