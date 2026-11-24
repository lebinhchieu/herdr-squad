# Architecture: squad-board (scope dashboard)

Status: final · Author: board-arch-dashboard · PO accepted I1-I7 and every cut (`tasks/po-decision-e7.md`, 2026-11-04). Inputs: po-feedback-v3, features.md v3, decision-parked-questions, design-v4, ADR 0004/0007/0009/0014, the code named in each row. "verified" = run or read in this session.

## 1. Components and boundaries
Python stdlib only. One process, 127.0.0.1. Reads squad files, git, `herdr`; writes only `board-ui.json`.
| Component | Does | Reuses (verified) |
|---|---|---|
| `bin/squad-board` + `bin/squadboard.py` | CLI (`--squad NAME\|PATH`, `--goal`, `--scope`, `--port`, `--no-open`), `ThreadingHTTPServer`, routes, cache | style of `squad-report`; no new dependency |
| Readers (`bin/squadboard_*.py`, one per source) | `read(selection) -> {data, quality, unknown:[source]}`; never raise; a missing source returns `unknown:<source>`. Those that feed the picker also offer `summary(scope)` | `squadledger.build`; `squadinbox` snapshot with `write=False` (CLI `--no-write`); `squadtranscript.iter_records`; `squadreport.collect`; roster/scope.md parsers of `squadreport.py` |
| Shared helpers | `squadboard_time.py` (ISO in, epoch out); `squadboard_git.py` (the git calls); `squadtickets.py` (ticket folder finder, moved out of `squadreport_tasks.py`) | `squadreport_tasks._find_tickets` (line 53), `squadtranscript.find_transcript` / `agent_sessions` |
| JSON state API | `GET /api/squads` (picker rows, summary facts) · `GET /api/state?squad=&goal=G` or `&scope=S` · `GET /api/worktime?...` (heavy, separate) · `GET /api/file?path=` · `PUT /api/ui` | new |
| Page | static files in `templates/board/`, no build, no CDN, Mango Parrot light tokens; see §1a | design-v5 |
| `board-ui.json` | `<squad folder>/board-ui.json`, version field, atomic write (temp + `os.replace`), last write wins | features 14 |
| `open-questions.md` | parked questions, one per `## Q<n>`, per level (scope, goal, squad); written only by `squad-inbox park/unpark/resolve`; the reader accepts hand edits and skips a block it cannot parse | decision-parked-questions |

**Selection rule (PO point 2, enforced by the server).** `/api/state` and `/api/worktime` answer `400 selection required` without `goal=` or `scope=`. A goal pulls its scopes and goal Manager; a scope pulls its own folder, roster, transcripts, branches. Nothing reads other scopes.
**Picker (`/api/squads`) is a summary, not a view.** Feature 11 puts "needs you N, stuck N, tasks 3 of 5, agents working, last active, N new" on every row, so the picker does read every scope, but only the cheap sources: `messages.jsonl`, `escalations.md`, `inbox.jsonl`, ticket files, the ledger, folder and file mtimes. Git costs two calls for the whole squad, not one per scope (`for-each-ref refs/heads/squad/<squad>/*` with `%(committerdate:unix)` and `--merged main`). Transcripts are never parsed; their mtime comes from one directory scan, cached by (path, mtime). This replaces the draft line "the picker never opens a transcript or runs git"; the cost is to be measured in the picker task (target under 1 s for 25 scopes, else rows fill in two steps).
**Cost per refresh (selected scope).** Files: `messages.jsonl`, `escalations.md`, `inbox.jsonl`, `roster.md`, `scope.md`, ticket folder (all small). Git: one `git worktree list --porcelain` and one `for-each-ref squad/<squad>/<scope>/*`. `herdr agent list` returns every agent of the machine: filter by roster names. Transcripts: parsed only by `/api/worktime`, cached in memory by (path, mtime, size). Measured: a 13 MB transcript parses in 0.1 s (1,196 timed records), a cold scope of ~10 transcripts is about 1 s. Finding transcripts opens the first 50 lines of each of the 566 files in the project dir: 0.13 s for this scope, 0.28 s for `accounts/autoswitch`. No on-disk cache.

### 1a. Page layout (PO point: "panels fit their content, no dead space")
- **Height is never stored.** A panel's height is its content height, capped at a max (then it scrolls inside), measured by `ResizeObserver`. The grid is CSS grid with `grid-auto-flow: dense` and a small row unit (8 px); each panel sets `grid-row-end: span ceil(h / unit)`. Dense flow fills every hole, so a short table next to a tall panel leaves no gap (the case in the PO's screenshot).
- **What `board-ui.json` stores per panel:** order, column span (1..N), hidden, optional max-height. Drag = reorder; resize = column span (and the max-height cap). No pixel x/y, no row index. A saved layout therefore survives a font-size change, a window resize, a panel with 1 or 8 rows.
- **One pure function** `layout.pack(panels, cols, unit)` (in `layout.js`) turns that state plus measured heights into grid spans; the drag engine only edits the state. This keeps the engine testable without drag events.
- Visual rules (snap feedback, Small/Normal/Extra large) stay with the Designer (`design-v5.md`).
- **Page files** (served by `/static/<name>`, each a Developer task): `index.html` + `board.css` (shell, tokens); `board.js` (poll, picker, header, time format, saved state, "not updating"); `layout.js` (grid, drag, resize, fit); `panel_inbox.js`, `panel_tasks.js`, `panel_agents.js`, `panel_files.js`, `panel_scopes.js`; `timeline.js` (Work time, swimlanes, the `TLE` engine of the prototype). A panel file registers `PANELS.x` + `COLDEF.x` (as in `proto-v4.html`); cutting a panel = delete its file and its name in the order list.

**Constraints for the plan.**
- Read-only means: call `squad-inbox list --json --no-write` (plain `list` writes `seen` events into `inbox.jsonl` under a lock; `write=not args.no_write`, `squadinbox.py:613`). Never write a squad file except `board-ui.json`.
- Security: bind 127.0.0.1; reject a `Host` header that is not 127.0.0.1/localhost (DNS rebinding); `PUT /api/ui` needs a random token the page gets at load; `/api/file` serves only real paths under the squad folder or `.scratch` (resolve symlinks, `..`), and sends HTML with `Content-Security-Policy: sandbox`. `docs/adr` is not served (the ADR list is cut).
- Polling every 5 s; each reader has a time budget and returns `unknown:<source>` on timeout. The page says "not updating" after 3 failures.
- Code split so tasks do not collide: one module per reader, one test file per reader, shared helpers first. The page is built after the API shape is frozen (`schema_version` in every response, additive only, as `data.json`).
- Windows (ADR 0011): subprocess `git`, `herdr` by name; no `fcntl` in the board; paths with `pathlib`. A missing `herdr` or `git` is `unknown`, not an error.
- `_find_tickets` moves to `squadtickets.py`; `squadreport_tasks.py` imports it (behaviour unchanged, `test_squadreport_tasks.py` keeps passing).
- Other repos: `--squad PATH` only (BA default). No scan. Every reader takes a `repo_root` (git root, `.scratch`, transcripts dir name come from that squad's repo); the file allow-list is per squad.
- `squad-start` prints the board command and does not open it (I7a).

## 2. The data table
Quality: **exact** (a recorded value), **approx** (derived or a model), **unknown** (not recorded). Effort: S under a day of one Developer, M 1-3 days, L more.
| Item | Source today | Quality | Gap | Effort · what changes | Risk | Verdict |
|---|---|---|---|---|---|---|
| Inbox: open questions, answers to read, age, blocks, options, recommendation | `squad-inbox --home H list --json --no-write` (version 1; `--home` goes before `list`) | exact; escalation row age is by day, first-seen second sits in `inbox.jsonl` | none | S · reader | none | v1; age from the `seen` event, "since first seen" |
| Permission banner | `herdr agent list` status `blocked` (JSON: `name`, `agent_status`, `pane_id`, `cwd`) | exact | needs herdr running | S | herdr absent → "unknown: herdr" | v1 |
| Agents now | herdr status + `roster.md`; "last activity" = transcript file mtime | exact | herdr is machine-wide | S | none | v1 |
| Tasks: stage, owner, who it waits on, returns, FAIL reason, current review wait | `squadledger.build`, `messages.jsonl`, ticket `Status:` | exact for verdicts; stage derived | ledger `branch` field is text-parsed: match by agent | S · reader + stage function | a token like `REV-8` is not a ticket: a row needs a ticket file or plan row | v1 |
| Scope → ticket folder link | `_find_tickets` guesses | approx | not stored | S · optional `tickets: <feature-slug>` line in `scope.md` (Manager writes it at plan) | additive | v1 guess, v2 line (I3) |
| Last active (task, scope, goal) | newest of `messages.jsonl` ts, branch tip commit time, transcript file mtime | exact for message and commit; mtime stands in for the last record | none | S · **use file mtime, do not parse transcripts**; max over the roster's files (sub-agent files too) | none | v1 |
| Goals and scopes lists, picker row facts | `goals/*/goal.md`, `scopes/*/scope.md` (brief = first bold line), `_done/`; row facts from the cheap sources in §1 | exact | brief format by convention | S/M | `goal:` empty = "no goal" | v1 |
| Goal view | `goal.md` Scopes table cells shown **as written**; done/open split by folder | exact (text), no derived status | none | S | none | v1 |
| Branches, tip, merged (for "ready for review" only; no list panel) | `squadboard_git`: `for-each-ref` (tip sha, date), `--merged main`, `worktree list --porcelain` to map agent → branch | exact | none | S | filter by `squad/<squad>/<scope>/*` | v2 |
| Ready for PO review | ledger PASS set vs branch tip sha (prefix match as `squadledger._canon`) | exact | none | S | tip moved → "sha changed after PASS" | v2 |
| Files: artifacts, ui-design, reports, evidence, drafts, goal `shared/decisions.md`, answered questions | folder listing of `tasks/`, `ui-design/`, `evidence/`, `report/`, ticket `evidence.md`; time = mtime | exact (mtime) | none | S + file route security | agent HTML in the page origin → CSP sandbox | v2 |
| Parked questions | `open-questions.md` (new) | exact once written | file, 3 commands, Manager rule, one-line ADR 0007 amendment | M · `squad-inbox park/unpark/resolve`, tests, `manager.md` rule, `process.md` bump (ADR 0005) | hand edits; two writers = `flock` already in `squadinbox` | v1 |
| Work time per agent | `squadreport.collect` over transcripts (`_classify`) | approx: a model of "working" | see §4 | S reuse; M for cache and a per-agent API | the report's display step drops short segments (§4) | v2 |
| Work time per task | `squadreport_tasks._Ctx.at`: latest task message, roster `Owns`, overhead | approx | roster holds only the current `Owns` | M · always show the "unattributed" share | must say "approx" | v2 |
| Commit marks, HANDIN/FAIL/PASS/BLOCKED/DECISION marks | `git log`, `messages.jsonl` (copies within 120 s count once) | exact | `messages.jsonl` holds only `SendMessage` calls | S | none | v2 |
| PO wait (open question → answer) | `inbox.jsonl` `seen` → `answer` | exact to the second after first sync | none | S | none | v2 |
| Idle (night) periods | gaps ended by a human/plugin record = `idle`; any gap over `stall_s` = `stalled` | exact boundaries, approx meaning | §4 | S | none | v2 |
| Worktree and branch per slice (timeline detail) | transcript `cwd`/`gitBranch` (on every record; `squadtranscript._file_records` drops them) | exact per record | 2 fields unread | S · additive fields + tests of `squadtranscript` | `gitBranch` can be `HEAD`: accept only `squad/*`, else keep last | **optional, last task**: BA called it low value; the Manager may drop it. Nothing else depends on it |
| Scope status | folder: `scopes/S` open, `scopes/_done/S` closed; `report/data.json` `scope.status` after a report | exact (open/closed) | no iteration `Status:` line exists in `1.md` or the template | S | none | v1, folder only |
| Close date of a scope or goal | folder mtime of `_done/<s>`; **tested:** `mv` keeps mtime, 4 of 4 closed scopes show folder mtime = `report/data.json` `generated_at` to the second | approx | wrong if something is added to the scope's top folder after close | none | a later touch moves it | BA's AC3 as written; fallback `generated_at`; no `closed:` line |
| Layout engine, picker, filter | `board-ui.json`; picker = §1 | exact | none | S data; the layout engine is the largest UI cost | see §1a | v1 |
| Open another repo's squad | `--squad PATH`; that repo's `.claude/squads/<n>` | exact | `repo_root` per reader; transcripts in `~/.claude*/projects` by that repo's dir name | M | wrong repo → wrong branches | v2, by path only |
| Local time, zone chip, saved UI state, font size | browser `Intl`; `board-ui.json` | exact | none | S | zone unreadable → "UTC"; file unwritable → browser copy | v1 |

### 2a. Cut (PO accepted, 2026-11-04). Do not build.
Exact time per task (stopwatch; show approx) · artifact-to-slice (show the file list with mtime) · derived goal status (show table cells as written) · tokens, cost, context, idle share, parallelism, respawn gap, digest (one link "open report") · PO's own working time and why an agent was idle (show "unknown") · ADR list · worktree list panel (path, ahead N) · scan of other repos · median review wait. Timeline: option 1 (swimlanes); option 2 only if asked, as a tab.

## 3. Irreversible choices (PO decided E7: all as recommended)
| # | Choice | Decided |
|---|---|---|
| I1 | Server and page stack | (a) stdlib `http.server` + vanilla JS, no build |
| I2 | Work-time source | (a) transcripts only (ADR 0014) |
| I3 | New files the squad must keep | `open-questions.md`, `board-ui.json`, optional `tickets:` line in `scope.md` |
| I4 | Parked-question format | (a) markdown `## Q<n>` blocks, strict writer, lenient reader |
| I5 | Cache | (a) memory only, keyed by (path, mtime, size) |
| I6 | ADR changes | New ADR in Task 01 (draft: `tasks/adr-draft-0020-dashboard.md`); amend 0007 in one line; `process.md` bump |
| I7 | `squad-start` opens the board | (a) no, it prints the command |
No new irreversible choice appeared since. Layout state (§1a) lives in `board-ui.json`, which I3 covers; it carries a version field, so it can change.

## 4. Work-time view: what the transcripts really give (verified)
- **Fields.** Every conversation record has `timestamp` (ms), `cwd`, `gitBranch`, `isSidechain`. `origin.kind` (human, peer, task-notification, plugin) is only on records the harness injects (one 1,600-record session: 8 `human`, 4 `peer`, 2 `task-notification`). Bookkeeping records have `cwd: null`. Worktree = the `.worktrees/<squad>/<scope>/<agent>` prefix of `cwd`; branch = `gitBranch` only when it starts with `squad/`.
- **Gap rule.** `_classify` classes the gap before a record by that record: tool/assistant → `working` (flag `stalled` over `stall_s` = 300 s); task notification or `run_suite.py` → `waiting`; peer record after an unanswered ASK/BLOCKED → `blocking` on that peer; human/plugin → `idle` (or `blocking` on the PO inside an open escalation). Exact on the record; "working" is a model.
- **"30 s".** Code default `MIN_SEGMENT_DEFAULT = 30` (`squadreport_tasks.py:19`); shipped `templates/report/config.json` sets `min_segment_s: 60`. It acts **only when drawing**: `_segments` merges a short piece into a same-bucket neighbour or **drops it**. Totals are computed before. **The board draws from the unfiltered pieces and merges only for readability.**
- **Night (session 7b00cc8b, 55 h, 3 gaps over 1 h).** Two (4.7 h, 12.8 h) end in a human record → `idle`. The third (**11.2 h**) ends in a `system` record → `_classify` says `working`, `stalled`: **a night gap can be counted as work.** Use both: idle (human-ended) and `stalled` (any gap over `stall_s`), and let the page collapse any gap over N minutes (default 60) whatever its bucket. A respawn is a new file; the time between files is `respawn_gap`, not agent time.
- **Per-task view.** Three layers of `_Ctx.at`; unattributed is shown. 58% attributed on the one real scope measured: say "approx".
- **Zoom.** The API returns pieces `[start, end, bucket, on, task, worktree, branch]` in UTC seconds for a requested `from`/`to`; zoom is a request, not a page trick. `worktree`/`branch` are empty until the optional task lands.

## 5. Open points for the Manager
1. Close date (feature 4 AC3) holds on real data; no change to `squad-close`.
2. The board sets its own min-segment value (not 30/60 from the report); the axis can show second-level pieces.
3. No real goal exists to test the goal reader; the first goal run is the first real check.
4. Picker facts (§1) read every scope's small files: measure in the picker task; fallback is two-step loading.
5. Per-slice worktree/branch is the one optional item (§2); decide keep or drop when planning.

## 6. Touched files per module (for the task split)
Rule: one module per reader, one test file per reader. "Ex" = existing file edited. Order: M0 first, readers parallel, page after the API is frozen.
| Module | New files | Existing files edited | Tests (new) |
|---|---|---|---|
| M0 foundation | `bin/squadboard_time.py`, `bin/squadboard_git.py`, `bin/squadtickets.py` | `bin/squadreport_tasks.py` (import `squadtickets`) | `test_squadboard_time.py`, `test_squadboard_git.py`, `test_squadtickets.py`; `test_squadreport_tasks.py` must still pass |
| M1 server + CLI | `bin/squad-board`, `bin/squadboard.py` | `bin/squad-start` (print the command only), `README.md` | `test_squadboard_server.py` (400 without selection, Host check, token, file route allow-list, CSP) |
| M2 picker / lists | `bin/squadboard_list.py` | none | `test_squadboard_list.py` |
| M3 inbox reader | `bin/squadboard_inbox.py` | none (calls `squad-inbox --no-write`) | `test_squadboard_inbox.py` |
| M4 parked questions (writer + rule) | none | `bin/squadinbox.py` (park/unpark/resolve), `bin/squad-inbox` if flags need wiring, `agents/manager.md`, `templates/squad/process/*.md` + version bump (ADR 0005), `docs/adr/0007-...md` one line | `test_squadinbox_park.py` |
| M5 tasks + ready for review | `bin/squadboard_tasks.py` | none | `test_squadboard_tasks.py` |
| M6 agents + permission banner | `bin/squadboard_agents.py` | none | `test_squadboard_agents.py` |
| M7 last active | `bin/squadboard_active.py` | none | `test_squadboard_active.py` |
| M8 files | `bin/squadboard_files.py` | none | `test_squadboard_files.py` |
| M9 work time | `bin/squadboard_worktime.py` | `bin/squadreport_tasks.py` only if `_segments` needs an `unfiltered` switch (additive) | `test_squadboard_worktime.py` |
| M10 optional: slice worktree/branch | none | `bin/squadtranscript.py` (`_file_records` adds `cwd`, `gitBranch`) | extend `test_squadtranscript.py` |
| M11 scope.md `tickets:` line | none | `templates/scope/scope.md`, `agents/manager.md` (same edit as M4, so do them in one task), `bin/squadreport_tasks.py` or `squadtickets.py` reads it | extend `test_squadtickets.py` |
| M12 page shell + layout | `templates/board/index.html`, `board.css`, `board.js`, `layout.js` | none | `test_squadboard_page.py` (browser: PO's short-next-to-tall case at 3 font sizes, 1/3/8-row panels, no dead gap) |
| M13 panels | `templates/board/panel_inbox.js`, `panel_tasks.js`, `panel_agents.js`, `panel_files.js`, `panel_scopes.js` | none | one browser test file for all panels (`test_squadboard_panels.py`) |
| M14 work-time page | `templates/board/timeline.js` | none | `test_squadboard_timeline.py` |
| M15 docs (Task 01) | `docs/adr/0020-dashboard-replaces-removed-board.md` | `docs/adr/0009-board-removed.md` (status line), `docs/adr/0007-...md`, `CONTEXT.md` | none |
Notes: M3 and M4 touch different files (reader vs the `squadinbox.py` writer), so they can run in parallel. M4 and M11 both edit `agents/manager.md` and `process`: one Developer, one task. `squadreport_tasks.py` is edited by M0 and maybe M9: order M0 before M9.

## Advisor note (LC-25)
- Question: are I1-I7 and the cut list right before the PO sees them?
- Advice: test the night, `origin`, close-date and cold-cost claims before handing in; add rows for scope status, layout, filter, other repos.
- Done: ran them; two claims changed (close date holds; a night gap can read as work); rows added. The PO accepted all. Final pass (layout fit, picker facts, module split) added no irreversible choice, so no new advisor call.
