# Board fixture: what is in it and the steps for a broken environment

Squad `fix` (repo `repo/`; stored as `dot-claude/` because git ignores `.claude/squads`, the copy renames it to `.claude/`), a second squad `other` (`repo2/`, stands for another repo), a Claude config dir (`claude-config/`), recorded herdr files (`herdr/`). All names are fixture names. Make a fresh copy first (every step below changes only the copy):

    python3 tests/board_fixtures.py --now        # prints squad, repo, herdr_json, config_dir ...  (here: $FX = the printed root)

`--now` shifts message times so the fixture clock (2026-11-04T10:00Z) is the real now: task 05 then reads "40 min". Without it times are fixed and ages are large. In Python: `board_fixtures.copy_fixture(now=...)`, `cleanup(fx)`.
Board flags used below (`--squad`, `--no-open`, `--port`, `--herdr-json FILE`) are built in tickets 03 and 08; steps 1-5 are checked in a browser after those tickets.

## The givens
| Given | Where |
|---|---|
| 3 goals; `alpha` has 4 scopes | `goals/{alpha,beta,gamma}`, scopes with `goal:` in `scopes/` |
| 6 lone open scopes | `scopes/`: `checkout`, `search`, `questions`, `parked`, `broken-parked`, the long-name scope |
| 20 done scopes | `scopes/_done/` (`closed-release` has `report/data.json`); `done-02/scope.md` is made CRLF by the copy helper on purpose (a tracked CRLF file would fail `test_windows_safe`) |
| Tasks in every stage | scope `checkout`, tickets 01-09 in `repo/.scratch/checkout-tasks/issues/` |
| Ticket id with no ticket | message with task `REV-8` in `checkout/messages.jsonl` |
| Open question / answered question | `scopes/questions` (E1 open, E2 answered) |
| Parked / broken `open-questions.md` | `scopes/parked`, `scopes/broken-parked` |
| Missing source | `scopes/search` has no `messages.jsonl` and no `escalations.md`; ticket folder `.scratch/search` has no `tickets:` line |
| Transcripts | `claude-config/projects/-fixture-repo/`: manager has a night (11.5 h gap ended by a human record, 11.2 h gap ended by a `system` record); `fix-dev-02` has a 30 min gap across the US DST change 2026-11-01 06:00Z |
| Missing transcript | `fix-qab-checkout` has a session id and no file |
| Herdr | `herdr/agents.json` (blocked `fix-dev-02`, working, idle, one agent of `other`; `fix-dev-03` retired = not listed); `herdr/not-running.json` |

Task stages in `checkout`: 01 todo, unassigned (no owner in roster) · 02 in progress · 03 returned, 3 FAIL · 04 blocked · 05 checking, 1 of 2 PASS (handed in 40 min before the fixture clock, waiting on QA blackbox) · 06 ready for review (both PASS, branch tip = passed sha, unmerged) · 07 sha changed after PASS (branch has a later commit) · 08 merged · 09 done (ticket `Status: done`). `scope.md` of `checkout` has `tickets: checkout-tasks`.
Branches `squad/fix/checkout/fix-dev-NN` are built in the copy (a fixture folder cannot hold a `.git`); the commit ids go into `messages.jsonl`.

## Where each format comes from (real files, REV-4)
| Fixture file | Copied in shape from |
|---|---|
| `messages.jsonl` | `.claude/squads/board/scopes/dashboard/messages.jsonl` (hook `squad-log-message`) |
| `escalations.md`, `inbox.jsonl` | `tests/fixtures/inbox/home/`; the row keys are computed by `squadinbox.row_key` |
| `roster.md`, `scope.md`, `goal.md` | `templates/scope/`, `templates/goal/`, the dashboard scope's `roster.md` |
| `open-questions.md` | `tasks/decision-parked-questions.md` (the scope dashboard) |
| `report/data.json` | `scope.status` and `generated_at` of a real `squad-report` output |
| `herdr/*.json` | `herdr agent list` (all fields of one agent) and the `server_not_running` error, names changed |
| transcripts | record shapes of `~/.claude*/projects/*/*.jsonl`: `timestamp`, `cwd`, `gitBranch`, `isSidechain`, `origin.kind`, `agent-name` |
`_make_fixture.py` writes all static files (run once, commit the output; tests never run it).

## Steps for the broken environment (T02.AC4)
Each step has an undo. `$SCOPE`=`$FX/repo/.claude/squads/fix/scopes/checkout`, `$SQ`=`$FX/repo/.claude/squads/fix`. Start the board with: `bin/squad-board --squad "$SQ" --no-open --port 8765 &` and note `$!` (the PID).

1. **`board-ui.json` unwritable.** `chmod 444 "$SQ/board-ui.json"` after the page has saved once (or `touch "$SQ/board-ui.json"` first). Root ignores `chmod`: then make it a folder instead: `mkdir "$SQ/board-ui.json"`. Expect: the page keeps the layout in the browser and says it is not saved to the squad. Undo: `chmod 644 "$SQ/board-ui.json"` / `rmdir "$SQ/board-ui.json"`.
2. **Browser storage blocked.** In the browser tool, open the page with an init script that makes storage throw: `Object.defineProperty(window,'localStorage',{get(){throw new DOMException('blocked','SecurityError')}})`. With `playwright-cli`, add it as an init script before `goto`. Or in Chrome: Settings, Privacy, Site settings, Cookies: "Block all cookies", then reload. Undo: close the session / set the cookie setting back.
3. **Server stop and restart.** `kill "$PID"` (the PID noted at start; never `pkill`), watch the page say "not updating" after 3 failed polls, then start it again with the same command and port. Expect: the page comes back by itself. Undo: it is the restart.
4. **New events in the message log.** `python3 tests/board_fixtures.py append-message "$SCOPE" --type FAIL --task 03 --sender fix-qaw-checkout --text "FAIL 03: new finding"` (or `printf '%s\n' '{"ts":"...","type":"PASS","task":"03",...}' >> "$SCOPE/messages.jsonl"`). Expect "N new" to count it on the next poll. Undo: delete the last line: `python3 -c "import sys;p=sys.argv[1];l=open(p,encoding='utf-8').read().splitlines(True);open(p,'w',encoding='utf-8',newline='\n').writelines(l[:-1])" "$SCOPE/messages.jsonl"`.
5. **Answer a question by CLI.** `SQUAD_ROLE=manager python3 bin/squad-inbox --home "$SQ/scopes/questions" answer E1 --option a --source chat` (writes only the copy). Expect the question to leave Needs you on the next poll. Undo: copy `escalations.md` and `inbox.jsonl` of `scopes/questions` from the fixture again: `cp tests/fixtures/board/repo/dot-claude/squads/fix/scopes/questions/{escalations.md,inbox.jsonl} "$SQ/scopes/questions/"`.

Last: stop the board by PID (`kill "$PID"`), then `python3 -c "import shutil,sys;shutil.rmtree(sys.argv[1])" "$FX"`.
