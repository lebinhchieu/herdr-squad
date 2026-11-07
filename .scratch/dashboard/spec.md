# Dashboard features (BA, FINAL)

Status: **final** (2026-11-04). = v3 + the PO's answer E7 (`tasks/po-decision-e7.md`: all cuts, defaults A/B/C/E and the ignore list accepted; timeline option 1; layout-fit point). Author: board-ba-dashboard. Layout base: prototype A. Effort per data item: see `architecture.md` (Architect). Tickets: `tasks/issues/`.
**Binding AC = the tickets in `tasks/issues/` (global ids `T07.AC3`, one Given/When/Then each, agreed with QA blackbox, see `business-ac-agreement.md`). The AC text in the sections below is background; if they differ, the ticket wins.**
The PO wants one rearrangeable local page for **one goal or one scope at a time**. Dropped by the PO: message feed, context limit. Rank = the PO's wishes, then how much the PO needs it to act. `#` = section number.

## Ranked list, value and final verdict
Value = how much the PO needs it to act or to know. Only what the PO really needs is built. **Iter 1** is built first; **iter 2** after iter 1 passes.
| # | Feature | The PO question it answers | Value | Final | Iter |
|---|---|---|---|---|---|
| 11 | Picker (mandatory choice) | Which goal or scope am I looking at? Where do I need to go? | high | keep | 1 |
| 2 | Inbox: questions, answers, permission banner | What waits on me? | high | keep | 1 |
| 3 | Tasks | Who is stuck? What happened to each task? | high | keep | 1 |
| 12 | Last active | What went quiet? | high | keep | 1 |
| 4 | Goal view and scope view | What is in this goal or scope? | high | keep | 1 |
| 7a | Passed (flag in Tasks) | What can I review and merge now? | high | keep (replaces the worktree list) | 1 |
| 16 | New since I last looked (dot and count) | What happened while I was away? | high | keep (PO: yes) | 1 |
| 6 | Open the board (`squad-board` flags, `--squad PATH`) | How do I get here from a goal start? | high | keep; other repos by path only; `squad-start` prints the command only | 1 |
| 13 | Parked questions | Which question can wait? | medium | keep | 1 |
| 5 | Agents now | Who is working, idle, blocked? | medium | keep, small | 1 |
| 14 | Saved UI state | Does it come back as I left it? | medium | keep | 1 |
| 15 | Font size | Can I read it? | medium | keep | 1 |
| 1 | Layout engine (drag, hide, resize, **fit**) | Can I arrange it? Does it use the screen? | medium (PO asked) | keep; column choose cut; **fit rule is new (PO)** | 1 |
| tz | Time zone rule | Is the time mine? | medium | keep | 1 |
| 8 | Files (reports, designs, goal decisions) | Where is what the squad made for me? | medium | keep; open a file from the page: yes | 2 |
| 10 | Work time (swimlanes = timeline option 1) | Where did the time go? | medium | keep, trimmed | 2 |

## Cut by the PO (E7, 2026-11-04). Not built.
Exact time per task · artifact-to-slice marks · worktree and branch per slice · goal status derived from scopes (the Scopes table cells show as written) · tokens, cost, idle share, parallelism, respawn and cache counts · PO's own time · ADR list panel (9) · worktree list panel (7b: only the "passed" flag stays) · scan of other repos for the picker · median review wait · column picker (my cut under "all recommendations"; the Manager may restore it) · timeline options 2 and 3 (option 2 later as a tab only if the PO asks).

## Report review (point 4): what `squad-report` offers
Read: `bin/squadreport_digest.py` (12 signal kinds), the existing report of 2026-10-29 for a real closed scope (not re-run; a newer schema would not change the value calls) `.claude/squads/plugin/scopes/_done/po-inbox-tui/report/data.json` (1 scope, 11 agents, 14 h), `bin/squadreport.py`. The report is a **retro** (time and cost after the fact); the board is **live** (who needs me now). Most signals answer a retro question.
| Report fact | Real PO question? | Value | Live board |
|---|---|---|---|
| Open escalations and their wait (`po_wait`: E1 626 s, E2 162 s) | Yes: what waits on me, since when | high | **keep** as the age of an open item (feature 2); the total of closed waits = low |
| Task returns with the FAIL reason (`returns_list`, `most_returns`: "task 01 came back 4 times") | Yes: what went wrong | high | **keep** per task (feature 3) |
| Tasks passed (`tasks_passed`), task window, `cycle_s` | Yes: how far along | medium | keep as counts "3 of 5 done" and "started 2 h ago"; no % |
| Task stage facts: handed in, waiting on which checker (`review_waits`) | Yes: who is stuck | high | **keep** the current wait ("waiting on QA blackbox, 40 min"); the median (`review_wait` signal) = ignore |
| Time per agent: working, waiting, blocked on PO (`buckets_s`, `blocking_s.po`) | Yes: where did time go, how long was I the bottleneck | medium | keep in Work time (10), as bands per agent |
| Time per task (matrix, `attributed`: 58% tied to a task) | Partly: approx only | medium | keep with the word "approx"; the share (`attribution_low`) is a warning to show, not a metric |
| Idle share (`idle_share`: "61.5% idle") | No: most idle is waiting for the PO or a peer by design; it reads as waste but is not | low | **ignore** as a number; idle stays a colour in the bands |
| Cost in USD per task, role, scope (`top_cost_*`, `scope_overhead`, `rework_cost`, `respawns`, cache expiries) | Not a PO question while working; it is a price-table estimate (report shows -8% vs reported) | low | **ignore** on the board; stays in the closing report and for the Token Coach |
| Parallelism, respawn gap, stalled time, tokens, sessions, iterations table, per-role totals | No | low | **ignore** |
Facts the report lacks and the PO needs live (new, all from data already read, no new squad input):
- **Needs me count per goal and scope** (picker, feature 11): open questions + answers to read + ready to merge.
- **Passed** (7a): every checker PASS on the branch tip, not merged. The PO alone merges, so this is an action, not a status.
- **New since I last looked** (16): events (HANDIN, FAIL, PASS, BLOCKED, DECISION in `messages.jsonl`) after the time the PO last had this page open, shown as a count and a dot on a task or picker row. Not a feed: no text list.
- **Quiet**: an in-progress task whose live owner has no activity for a long time shows its age as plain text "quiet 3 h" (feature 12 data; the limit is a setting, default 60 min).
## Ignore list (accepted by the PO, E7). Not built
Cost in USD and tokens · idle share and parallelism · median review wait · respawn and cache-expiry counts · per-role totals · iteration cost table · closed-wait total · ADR list · worktree path and ahead count · scan of other repos for the picker (a squad in another repo opens by path only) · message feed · context limit · progress % · dark theme · writes from the page except `board-ui.json`.

## Cross-cutting rules
- A source that is missing shows "unknown: <source>", never an empty "all good". A missing transcript shows "no data", never 0.
- The page says "updated hh:mm:ss" (browser zone), refreshes every 5 s, says "not updating" after 3 failed refreshes. Tab title: `(N) <squad>` when N > 0, else `<squad>`. Age words: `under 1 min ago`, `N min ago`, `N h ago`, `N d ago`. No `%` character in any visible text. Local only: 127.0.0.1. At 1000 px wide nothing overlaps; below it the page scrolls sideways.
- Read-only: no button changes squad data; the one file written is `board-ui.json`. Where the PO must act, the page shows the command to copy (`squad-inbox answer E2`).
- Light Mango Parrot palette; mango only for "needs you". **No % anywhere**: no data holds progress; counts ("3 of 5 done") and words are fine.
- **Time zone.** Data stays UTC. Every date and time shows in the browser's zone, the header shows the offset ("+07"); one place formats times; ages do not depend on the zone; "today" = the local day; zone unreadable = UTC with the label "UTC". AC: browser at +07, ts `2026-11-03T02:00:00Z` shows 09:00 and the header "+07"; near midnight UTC the local date shows.
- **Needs-you count** (tab title, picker rows, "N more need you"): open questions + answers to read + branches ready to merge (feature 3, AC4) + permission prompts (banner, squad-wide). Parked questions are excluded.
- **One choice at a time** (feature 11). A panel shows rows of the chosen goal or scope only. Squad-wide items (permission banner, tab-title count, squad-level parked questions) show under every choice.

## 11. Picker: the PO must choose a goal or a scope (iteration 1, PO point 2)
- **Why:** a squad has many goals and scopes over time. The PO never needs all data of all scopes, and one page of everything is noise. The first thing the PO does is choose where to look, so choosing must be fast and the list must show where he is needed.
- **Rules**
  - **No all-data view.** There is no "all", no "all goals", no "all scopes", no total of data across choices (except the squad-wide needs-you counts below). The board shows exactly one goal (with its scopes) or one scope. With no choice, it shows only the picker; no panels, no layout.
  - **Landing screen = picker** when nothing is chosen. It is one list, top to bottom: (1) **Recent**, the last 5 choices of this squad as chips (open or done); (2) **Open**: goals and lone scopes, each one row; (3) **Done (N)**, collapsed. A search box on top (focus with `/`).
  - **Row facts** (name, brief, then at most 6): **needs you N** (mango; the count defined in the cross-cutting rules), **stuck N** (tasks with an open BLOCKED, plus returned tasks), tasks "3 of 5 done", agents working now, last active (feature 12), "N new" (feature 16). A goal row shows the sum of its scopes and expands to its scopes; goals start collapsed unless a scope under them needs the PO.
  - **Order in Open:** needs you (most first), then stuck, then last active (newest first). Lone scopes show the tag "no goal". A done scope of an open goal stays under that goal, marked done; a closed goal and a closed lone scope are in Done, newest close first (close date from folder time, approx).
  - **Search** matches name and brief of every row, Done included (Done opens while a match is inside). Enter opens the first match. Nothing matches: "Nothing matches '<text>'".
  - **Choice always visible:** the header shows `goal G` or `goal G > scope S` and a switcher button that opens the same picker as a sheet over the page; Esc or a pick closes it. The "N need you elsewhere" line (below) is in the header too.
  - **Needs-you elsewhere:** the permission banner and tab-title count count the whole squad. When the choice hides open items, the header says "N more need you in <goal or scope>, …" and each name switches the choice.
  - **Opening:** priority is (1) `squad-board --goal G | --scope S`, (2) the URL (`#/goal/G`, `#/scope/S`, so reload, bookmark and the browser back button work; back from a choice returns to the picker), (3) the saved last choice of this squad, (4) the picker. A choice that is closed still opens, read-only, marked "closed". `--goal` and `--scope` together are refused. An unknown name lists the squad's goals and scopes and starts no server.
  - **Remembered (feature 14):** the last choice and the 5 recent ones, per squad, in `board-ui.json` and the browser copy. A saved choice whose folder is in neither the live place nor `_done/` opens the picker with "saved choice <name> not found". Two windows may show different choices; the saved one is the last changed.
- **AC1.** Given 3 goals, 6 lone scopes and 20 done scopes, when the board opens with no flag and no saved choice, then only the picker shows: Open rows (needs-you first), Done collapsed as "Done (20)", no task, inbox or work-time panel, and no way to see everything at once.
- **AC2.** Given the PO types "inbox" in the search, then only rows whose name or brief match show, done ones included, and Enter opens the first.
- **AC3.** Given the PO chose scope S1 yesterday and S1 is still open, when the board opens with no flag, then S1 shows and the header has the switcher; given S1 was closed since, then S1 still opens, read-only, marked "closed"; given its folder is gone, then the picker shows "saved choice S1 not found".
- **AC4.** Given `squad-board --goal G` and a saved scope choice, then G shows (flag wins). Given `--goal G --scope S`, then the command refuses and starts nothing.
- **AC5.** Given scope S3 has an open question and the PO chose S1, then the header says "1 more needs you in S3", the tab count includes it, and clicking "S3" shows S3.
- **AC6.** Given the PO opens a goal, then every panel shows only its scopes' rows (and the goal Manager); given the PO opens one of its scopes, only that scope.
- **AC7.** Given a chosen scope is closed while the page is open, then the page shows it read-only with "closed" and a link back to the picker; it does not fail. Given the PO opens a Done row, then it opens the same way.

## 4. Goal view and scope view (iteration 1; with 11 this replaces the old Goals and Scopes list)
- **Why:** after choosing, the PO sees the data of that choice.
- **Goal view:** goal brief and Scopes strip (each scope: brief, stage, needs you, blocked, tasks "x of y", last active; a click drills down to the scope), then the same panels as a scope with a **Scope** column, rows of all its scopes, plus the goal Manager's own inbox items and parked questions. **Scope view:** the panels for that scope, with the goal named in the header ("goal G" or "no goal") and a link up to the goal.
- **Data:** open: `goals/<g>/goal.md` (brief, Scopes table with Depends on and Status), `scopes/<s>/scope.md` (brief, team, `goal:`), newest `iterations/<n>.md` Status. Done: `goals/_done/<g>/`, `scopes/_done/<s>/`. Only the template `templates/goal/goal.md` was read; no real goal folder exists yet: re-check the fields on a real goal.
- **AC1.** Given goal G with scopes S1 (2 tasks open) and S2 (done), then the goal view lists S1 and S2, S2 marked done, and the Tasks panel shows S1's tasks with a Scope column.
- **AC2.** Given a lone scope, then the header says "no goal". Given a closed scope, then its panels are read-only with its close date (approx).
- **AC3.** Given a goal with no scope yet, then "No scopes in this goal".

## 1. Layout engine
- **Why:** PO asked to rearrange the layout. **Rules:** drag and hide panels, show again from one list of hidden panels; resize. No column picker (cut). Saved per squad (feature 14), one layout for every choice. "Reset layout". The picker has no layout.
- **Fit rule (PO, E7: "worktrees & files panels do not fit; dead space"):** a panel is as tall as its content, up to a maximum height, then it scrolls inside; the grid packs panels tight, with no empty block beside or under a panel and no offset; after a drag or resize the panels snap back to the packed grid. Holds at every font step and for a panel with 1, 3 or 8 rows. The Worktrees panel is gone.
- **AC1.** Given the PO moves a panel and resizes another, when reloaded, then both stay. **AC2.** Given the PO hides Needs you, it comes back from the hidden list; the permission banner cannot be hidden. **AC3.** Given the PO presses Reset layout, then the default layout returns. **AC4 (fit).** Given a panel with 1 row next to a panel with 8 rows (Normal font), then the short one is only as tall as its rows, no blank grid area is larger than one panel gap, and the layout has no panel offset below or right of its neighbour. **AC5.** Given the font is Small, Normal, then Large, the same holds. **AC6.** Given the PO drags a panel to an odd spot, then on release it snaps into the packed grid.

## 2. Inbox (questions, answers to read, permission banner)
- **Why:** the squad waits on the PO. **Data (verified):** `squad-inbox list --json` (ADR 0007: id, kind answer/read, state, title, age, blocks, options, recommendation). Banner: `herdr agent list` status `blocked` = a permission prompt only the PO can answer in that pane (MSG-10). Items follow the choice; the banner and tab count are squad-wide.
- **AC1.** Given 2 open questions and 1 unread item in the choice, then 3 rows, oldest first: id, title, age, what it blocks; nothing open: "Nothing needs you". **AC2.** Options and a recommendation show in the row. **AC3.** Given the PO answers (CLI), when the page refreshes, the item leaves and the tab count drops. **AC4.** Given an agent waits on a permission prompt, a banner above all panels names the agent and its pane, whatever the choice.

## 3. Tasks
- **Why:** every task, and what happened to it. **Data (verified):** `squad-ledger --json` (sha, handin_from, verdicts, returns, open BLOCKED), `messages.jsonl` (HANDIN, FAIL with reason, PASS, BLOCKED, DECISION; ts, from), `roster.md` Owns, ticket files (title, `Status:`).
- A row is a task only if it has a ticket file or a plan-table row (not a token like `REV-8`). Sources: `.scratch/<feature>/issues/NN-*.md` and drafts in `$SCOPE_DIR/tasks/`.
- **Stage (facts, derived):** todo, in progress, returned (a FAIL on the current sha), blocked (open BLOCKED), passed (every checker PASS on the current sha, not in `main`), e.g. "checking, 1 of 2 PASS, waiting on QA blackbox". **Passed** is also the 7a flag: every checker PASS on the branch tip and not merged; a moved tip shows "sha changed after PASS"; merged shows "merged". Branch = git branch whose agent name matches the owner (not the ledger `branch` text).
- **Detail (click):** agents involved, steps in time order with the FAIL reason, first line only; no feed.
- **Gap:** the scope-to-ticket-folder link is not stored (`squadreport_tasks.py:_find_tickets` guesses): Manager decision below.
- **AC1.** Tasks in all stages: each row has id, title, stage, owner, who it waits on, last active, "N new". **AC2.** A task with 3 FAIL shas shows "3 returns", the reason readable. **AC3.** One checker PASS, one missing: the row names the missing checker, not "passed". **AC4.** Given all checkers PASS the tip and the branch is unmerged, then the row shows "passed". **AC5.** Opening a task lists agents and steps.

## 5. Agents now (small panel)
- **Data (verified):** `herdr agent list` (working, idle, blocked, done, unknown) joined to `roster.md` (role, owns, live or retired); last activity = newest transcript record or message. Of the choice only.
- **AC1.** 5 live and 1 retired: 5 rows with role, task, status, minutes since last activity; the retired one behind a click. **AC2.** herdr not running: "status unknown: herdr not running", roles still list.

## 6. Open the board (`squad-board`)
- **Why:** open it from the start of a goal or scope (PO answer 1). New CLI (ADR 0009 removed the old one): `squad-board [--squad NAME|PATH] [--goal G | --scope S] [--port N] [--no-open]`. `--squad` = a folder under `<git root>/.claude/squads/` or a path to any squad folder, also in another repo (repeatable); one squad here = that one; several and none named = refuse and list. Server on 127.0.0.1. `--goal/--scope`: feature 11 (flag wins). Per-scope squads only (ADR 0004): a flat squad shows "flat squad: not supported". `squad-start` does not open it: it prints the command (PO decision A = no, so ADR 0009's "Manager tab only" line stays). Other repos: by `--squad PATH` only, never scanned.
- **AC1.** `squad-board --squad plugin` opens `plugin` on its picker or saved choice; a squad switch is in the header. **AC2.** `--squad <path in another repo>` opens that squad. **AC3.** An unknown squad lists squads and starts no server.

## 7. Worktrees and branches: only "passed" (7a, in Tasks; 7b cut)
- Data (verified): `git branch`, `git worktree list`, ledger verdicts; Developer branch `squad/<squad>/<scope>/<agent>` (`bin/squad-spawn`). Merged = reachable from main. The list of worktree paths and "ahead by N" (7b) is cut (value low); the PO needs only the flag in Tasks (feature 3, AC4). Branches of other scopes never show under this choice.

## 8. Files (iteration 2; absorbs the goal and scope decisions of old feature 9)
- **Why:** PO answer 3: everything made for the PO. **Data (verified):** scope `tasks/*.md`, `ui-design/`, `promote.md`, `report/report.html` + `data.json` (only after squad-report or squad-close), `evidence/` and ticket `evidence.md`; goal `shared/` and `shared/decisions.md`; answered questions with the PO's answer. Time = file modified time (the squad folder is git-ignored). ADRs are not listed.
- **AC1.** A scope with a feature list, 3 prototypes and promote.md: each lists with name, kind, last changed. **AC2.** A click opens an HTML or markdown file in the browser (files under the squad folder and `.scratch` only; PO decision C = yes). **AC3.** A live scope without a report: "no report yet (made at close)".

## 10. Work-time view (iteration 2; Designer offers 3 timeline prototypes)
Goal (PO answer 5, point 3): which time worked which task. **Shape: swimlanes, one lane per agent (timeline option 1; E7).** PO needs: zoom into a range, hide idle periods (night, no work), time on the x-axis. Not an event list. Cut (E7): exact time per task, worktree/branch per slice, artifact marks. Pieces are drawn from the unfiltered data; only merging for readability is allowed (Architect §4), and a night gap must not read as work.
| Fact | Source | Quality | Keep |
|---|---|---|---|
| Per agent: working, waiting, blocked on PO or a peer, idle | Transcripts (`squadtranscript.py`, `squadreport.py`); gap classed by the record that ends it (ADR 0014); gaps under `min_segment_s` (30 s) dropped | Real, a model of "working", not a stopwatch | **keep** (the bands) |
| Task of a slice | Latest message naming a task, then roster `Owns`, else overhead | **Approx** (58% on a real scope) | keep, word "approx", the unattributed share visible |
| Commit marks, merge time | `git log` | Exact | keep (shows output) |
| Hand-in, FAIL, PASS, BLOCKED times | `messages.jsonl` (copies within 120 s count once) | Exact | keep as marks |
**Cannot be known:** the PO's own working time; work before an agent's first task message; two tasks at once; a deleted transcript (`no_transcript:<agent>`); why an agent was idle. Follows the choice; times follow the zone rule.
- **AC1.** A Developer on task 03 for 2 h: a bar for 03 split working/waiting/idle. **AC2.** Unattributed time shows a row with its share. **AC3.** No transcript: "no transcript", no time invented. **AC4.** Approx figures carry "approx". **AC5.** (PO point 3) the PO can zoom to a time range, hide idle stretches longer than a set gap, and every bar has a time axis in the local zone.

## 12. Last active (iteration 1, PO item 7)
- **Why:** what is moving and what went quiet. **Derived: newest of commit, message and transcript time**, read-only. Task: newest message naming it, newest commit on the owner's branch touching it, the owner's newest transcript record only while it is in progress, blocked or returned (approx). Scope: newest of its tasks, any scope message, any commit on `squad/<squad>/<scope>/*`, any roster-agent transcript. Goal: newest of its scopes, goal messages, goal Manager transcript.
- **Unknown:** "no activity recorded"; a source missing: newest of the rest with "partial: <source> missing". Never "just now" or 0 for unknown. Shown as an age; local time on hover. An in-progress task with a live owner and no activity over the quiet limit (fixed 60 min, no setting) shows "quiet 3 h".
- **AC1.** A task last messaged 3 days ago whose owner works now shows "a few min ago, approx"; done: the last message or commit. **AC2.** No message, commit or transcript: "no activity recorded"; transcript deleted but a commit exists: that time with "partial: transcript missing". **AC3.** A goal's time = its newest scope's, or later if the goal Manager acted.

## 13. Parked questions (iteration 1, PO item 8; Manager decision `tasks/decision-parked-questions.md`)
- **Why:** the PO cannot answer some questions now; he parks them to clear "Needs you" and returns later. **Decided:** a parked question is its own record in `open-questions.md` in the folder of its level (scope, goal, or squad), entries `## Q<n>` with `Status: parked | resolved`, `Parked:`, text, optional `Blocks:` and `From:` (`E3`, `E3 #2`), `Resolved:`. Commands (not the page): `squad-inbox park|unpark|resolve`. Parking does not answer: the blocked work stays blocked. The inbox rows are untouched.
- **Page:** a Parked group below open items in Needs you: level chip, text, From, Blocks, parked-since, oldest first; not counted in the tab title; follows the choice (a goal view reads the goal and its scopes' files; squad-level items show under every choice); closed scopes' files are read from `_done/`. The page shows the command to copy, never writes the file.
- **AC1.** 3 open questions, 1 parked: Needs you lists 2 open and Parked (1), the tab count is 2, the parked row names what it blocks. **AC2.** After `unpark` the count is 3; after `resolve` the row leaves Parked. **AC3.** A parked question in S3 does not show when S1 is chosen; a squad-level one shows under both. **AC4.** A file with a broken entry shows "open-questions.md unreadable: <path>", other entries still show.

## 14. Saved UI state (iteration 1, PO item 9)
- **Why:** localStorage is per port; the PO wants layout and settings to last. The server saves `<squad folder>/board-ui.json` (UI preference, the only file the board writes), the browser keeps a copy. **Saved per squad:** panel position, size, hidden; table columns and order; **last choice and the 5 recent (feature 11)**; font size. Each save has `saved_at`; the newer of file and browser copy wins; last write wins between two browsers. **Reset:** "Reset layout" clears layout and columns; the choice has its own clear (the picker); font size its own.
- **AC1.** Layout and choice set, board opened on another port or browser: both come back. **AC2.** `board-ui.json` unwritable: the page works from the browser copy with "settings not shared"; neither works: defaults with "layout not saved". **AC3.** File unreadable or unknown version: defaults with "settings file unreadable"; the picker shows. A saved choice that is closed still opens (feature 11); one with no folder opens the picker.

## 15. Font size (iteration 1, PO item 10)
- A header control, three steps in words: Small / Normal / Extra large (no %), default normal, scales all text (tables, Work time labels, the picker). Saved as in feature 14. **AC1.** "Large" survives a reload and a new port; no text is cut off (a small panel scrolls).

## 16. New since I last looked (iteration 1, suggested; the PO decides)
- **Why:** the PO leaves the page and returns; he wants what changed without a feed. **Rules:** the browser stores the time the page was last visible per choice; on return, a task or picker row gets a dot and "N new" counting `messages.jsonl` events (HANDIN, FAIL, PASS, BLOCKED, DECISION) newer than that time. Opening the row's detail clears its dot. No text list. First visit: nothing is new.
- **AC1.** Given 2 PASS and 1 FAIL on task 03 since the last visit, then 03 shows "3 new" and the picker row of its scope shows "3 new". **AC2.** Given the PO opens 03, then its dot clears.

## Decisions (all closed)
- PO (E7): A `squad-start` prints the command only. B other repos by path only. C open a file from the page: yes. E feature 16: yes. F cuts and ignore list: accepted. D parked = `open-questions.md`. Architect I1-I7 as recommended (`architecture.md`).
- Manager: `tickets: <feature-slug>` line in `scope.md` (optional; Tasks falls back to guessing). New ADR in ticket 01 (dashboard replaces the board; `board-ui.json` write; `open-questions.md`; `tickets:` line).
- Business AC: agreed with QA blackbox, see `tasks/issues/` (record at the end of each ticket) and `tasks/business-ac-agreement.md`.

## Hand to promotion (PROMO-3a)
- No progress % exists; a task shows stage and facts. Task time is approx (message layer, roster layer, overhead).
- The board always shows one goal or one scope, never all; squad-wide: banner, tab count, squad-level parked questions.
- Ready for PO review = every checker PASS on the branch tip, not merged; the PO alone merges.
- All times show in the browser's zone, data stays UTC. Last active = newest commit, message or transcript time; unknown = "no activity recorded". Parking is not answering and does not unblock work.
- The board cuts (E7) are not rebuilt without a new PO decision. `squad-start` prints the board command; it does not open it.
- Term: **work time** = working, waiting, blocked or idle time of an agent, from transcripts (ADR 0014).
