# squad-report: spec

Status: Phase A proposal, draft 1 (2026-10-19). Input: `decisions.md` (rounds 1-2). Sections are owned: Business = BA, Design = Designer, Technical = Tech Lead. Edit only your own.

## Business

**Owner:** plugin-ba-squad-report. **PO answered round 3 (Q14-Q25, 2026-10-18):** all yes except Q19 (no backfill; build on demand for a chosen scope), Q22 (rollup over a list of `data.json` files teammates send), Q23 (open to a process change if cheap), Q25 (rollup inputs come from teammates' own squads). New PO question: "do we have data on why a task was returned?" is answered in S4 (AC4.3-4.5). Round 4 not needed unless the Tech Lead's Q23 estimate or Q27 below need a PO call.

### Goal in one line
After a scope or goal, the PO (and a later analyst skill) can see in one page where the time and money went, which tasks and roles drove it, what was blocked or waited on, and how many returns it cost, with zero LLM tokens spent to produce it.

### Who reads it, when
| Reader | Moment | Wants |
|---|---|---|
| PO | scope/goal close, check-in, "why was this slow/expensive?"; also when teammates (own squads, maybe other machines) send their `data.json` | the headline numbers, the 3 things to look at, why tasks were returned, a rollup across scopes and squads |
| Manager | retro (before the check-in) | where the pod lost time: blocks, returns, PO wait |
| analyze skill | on demand | the `digest` only; drills into `data.json` when a finding needs it |
| Token Coach | unchanged (reads `squad-usage`) | n/a in v1 |

### Terms (to promote to `CONTEXT.md` by the Tech Lead's promotion task)
- **Elapsed**: wall clock from the scope's first event to its last. **Agent-time**: the sum over agents of their time in the four buckets. **Parallelism** = agent-time / elapsed. A report never shows a bare "time": it says which.
- **Buckets** (agent-time, derived): working (model or tool running), waiting (long tool call or background job), blocking (BLOCKED/ASK sent, reply not yet in; or an escalation to the PO open), idle (waiting for work from a peer, or for the PO's typed chat reply). A gap is classified by what ends it, not by its length; 5 min is only a stall guard. They add up to agent-time exactly.
- **PO wait**: an escalation open (`inbox.jsonl` `seen` to `answer`). Reported as elapsed intervals (count, total, longest), never as agent cost; any agent's time inside it is bucketed blocking with reason `po`. Agents sitting between the PO's typed chat messages with no escalation open are **idle, reason "waiting for your chat reply"**, shown as a sub-line under idle (Q16; win-compat: 11.2 of 29.3 agent-h). Same bucket in the data, own colour in the timeline legend and a KPI line (Designer Q-D4).
- **Review wait**: a task's HANDIN to its PASS/FAIL verdict.
- **Return**: one FAIL message (label "returns (FAIL messages)": the Manager's own count can differ by one when a return came in another wording). **Rework**: FAIL to the task's next HANDIN (time and cost). **Returned reason**: the headline of the FAIL message (first line, cut to 200 characters), who returned it, and the pointer to the task's QA evidence file where the full findings are. Not classified (no LLM).
- **`data.json`**: the one shareable file of a scope. A teammate can send it; the PO's rollup reads only such files (no scope folder, no transcripts). A scope is identified by squad name + scope name.
- **Task**: a ticket id seen in messages/roster (e.g. `16`); **scope overhead**: agent-time and cost not attributable to any task; **% attributed** (attributed non-idle seconds / non-idle seconds, i.e. working+waiting+blocking; cost share shown beside it) always shown; banner when under 60% (Q17). The real non-idle figure is unmeasured until the QA real-data run (88%/87% in the prototype was working-time only).
- **Derived**: every time figure; **estimated, list price**: every dollar figure. Labelled on the page.

### User stories and business AC
Format Given/When/Then, all observable by running the CLI and opening the output; QA blackbox needs no code. "Fixture scope" = a scope folder with roster, messages.jsonl, inbox.jsonl, usage-events.jsonl and transcripts (the QA fixture is Tech Lead's to name).

**S1. See where time and money went (scope report).**
- AC1.1 Given a closed fixture scope, when `squad-report <scope>` runs, then it prints the report path and a 5-line summary (elapsed, agent-time, est. cost, returns, % attributed) and exits 0.
- AC1.2 Given that run, then `<scope home>/report/data.json` and `report.html` exist; `report.html` opens from `file://` offline with no network request and no server.
- AC1.7 Given a scope whose transcripts carry Claude Code's own cost figure, then a small line "Claude Code reported $X (estimate off by Y%)" sits beside the headline cost; absent otherwise (Q24).
- AC1.3 Given the report, the header shows: elapsed, agent-time, parallelism, tokens by kind (input, cache read, cache write, output), est. cost, returns, % attributed, PO wait total. Each time figure carries "derived", each dollar figure "estimated, list price".
- AC1.4 Given the report, bucket times of every agent, task and role add up to its agent-time (to the second).
- AC1.5 Given the same inputs, a second run yields identical `data.json` except `generated_at` (idempotent, no duplicate rows).
- AC1.6 Given a generation run, no LLM is called and no token is spent (verifiable: no `claude` process spawned, no network).

**S2. See which tasks and roles drove it.**
- AC2.1 Given the fixture, the task table has one row per task with time by bucket, tokens, est. cost, returns, rework time/cost, cycle time (first mention to PASS), sortable and filterable in-page.
- AC2.2 Given the fixture, the role table has the same columns scope-wide; respawned agents of one role roll up under the role and the table shows agent count and respawn count.
- AC2.6 Given long overnight gaps, then the timeline compresses gaps over 1 hour to a marker by default, with a toggle to true scale (Q21).
- AC2.3 Given a task x role drill-down and an agent timeline coloured by bucket, then hovering/selecting a cell or bar shows the same numbers as the tables (no second source of truth).
- AC2.7 Given one ticket named differently across roles (`T0`, `07`, `07-squadio-helper`), then it is one task row when a single message names both aliases; leftovers show as separate rows and lower % attributed (Q23).
- AC2.4 Given work that matches no task, then it is listed as "scope overhead" with its cost and time, and % attributed = attributed non-idle seconds / non-idle seconds (attributed cost share shown beside it); under 60% a banner says the task table is weak.
- AC2.5 Given an iteration number on messages (e.g. win-compat 1..5), then the report can show time and cost per iteration.

**S3. See what was blocked or waited on.**
- AC3.1 Given BLOCKED/ASK messages with replies, then blocking time per task and per role is shown, with the longest 3 blocks naming who waited on whom and for which task.
- AC3.2 Given escalations in `inbox.jsonl`, then PO wait is shown as count, total, longest and % of elapsed; the PO is never shown as an agent with cost.
- AC3.3 Given HANDIN then PASS/FAIL, then review wait per task is shown (median and longest in the digest).
- AC3.5 Given gaps ended by a typed human message with no escalation open, then they are idle with reason "waiting for your chat reply" and are shown as a sub-line under idle, never counted as PO wait.
- AC3.4 Given a long tool call whose command matches a pattern in the config file (e.g. `run_suite.py`), then that time is "waiting", not "working" or "idle". Changing the pattern or the 5-minute threshold in the config file changes the result with no code change.

**S4. See the returns.**
- AC4.1 Given FAIL messages (copies of one message sent to several roles counted once), then each FAIL counts as one return, labelled "returns (FAIL messages)", on its task; a task with 3 or more returns is flagged in the table and in the digest.
- AC4.2 Given a returned task, then rework time and cost run from the FAIL to its next HANDIN.
- AC4.3 Given a FAIL message, then the task's return row shows when, who returned it (role, e.g. QA whitebox), at which sha if the headline names one, and the returned reason (the FAIL text without its `FAIL <task>` prefix, whitespace collapsed, cut at 200 characters). Win-compat check: all 12 FAIL messages (6 after dedupe) carry a one-line headline such as "One blocking finding, tests only" and a findings list; this is enough to answer "what failed".
- AC4.4 Given a returned task whose evidence folder holds `qa-w.md` or `qa-b.md`, then the local report may name that file (relative to the scope folder) as "full findings"; the report never copies or reads its content (free-form, not portable). Optional for v1 (Tech Lead's call); the reason headline of AC4.3 is the required part.
- AC4.5 Given the digest, then the "tasks by returns" finding lists the reason headline of each return of the top task, so the PO sees why, not only how many.
- AC4.6 Given `squad-report <scope> --redact`, then `data.json` and `report.html` contain no return reasons and no ticket or escalation titles (ids, counts, roles, times only): the form to send to someone else.

**S5. Roll up a list of scopes, from `data.json` files (Q22, Q25).**
The PO's teammates run their own squads and send `data.json`; the PO rolls them up. A goal in the PO's own squad is the same case with local files.
- AC5.1 Given a list of `data.json` files (paths on the command line, or a folder of them), when `squad-report rollup <files>` runs, then it shows a scopes table, totals, role totals, cost share and time share per scope, built from those files only: no transcript, no scope folder, no network.
- AC5.4 Given files from other squads or machines, then each row is labelled squad name + scope name; two files with the same squad + scope keep the one with the newest `generated_at` and list the other as skipped.
- AC5.5 Given a file that is not a `data.json`, is unreadable, or has another `schema_version` or `kind` (shown as `schema_mismatch`), then the rollup still builds from the rest, lists that file as "skipped: <reason>", and marks the totals "partial".
- AC5.3 Given a rollup row, then it links by relative path to a `report.html` sitting next to that `data.json` when one exists (Designer Q-D6); with none (teammate sent only `data.json`), the row shows a disabled "no report" state.
- AC5.6 Given `squad-report <goal>` in a squad that has the goal, then it is the same rollup over the goal's scopes' `data.json` files (convenience; a scope without one is listed "missing" with the command to create it, totals "partial").
- AC5.7 Given a `data.json` made with `--redact`, then the rollup works and the reason/title columns show "not shared".
- AC5.8 Given files with different price tables, then the rollup sums each file's own cost and shows a "mixed price tables" note. The 60% attribution banner applies per file/row.

**S6. Report at close, on demand, without risk.**
- AC6.1 Given `squad-close --scope S` (not `--dry-run`), then the report is generated first, before any agent is retired or the folder moved; the report ends up in `scopes/_done/S/report/`.
- AC6.2 Given `squad-close --goal G`, then the goal rollup is built from its scopes' `data.json`.
- AC6.3 Given the report step fails, then close prints a one-line warning and completes; the exit code and effects equal a close without the feature.
- AC6.4 Given `--dry-run`, then no report is written.
- AC6.5 Given `/squad:squad-report <scope|goal|file list>`, then it runs the same command as AC1.1 or S5 and relays its summary.

**S7. Honest about what it knows.**
- AC7.1 Given a scope still running, then the report carries a "partial" banner and `data.json` says `partial: true`.
- AC7.2 Given an agent whose transcript is missing, then the agent is listed "no transcript", all other figures still compute, and totals are marked partial.
- AC7.3 Given a scope folder with no messages, or no tasks, then the report builds with empty tables and an explicit "nothing to show" state, not an error.
- AC7.4 Given a legacy flat squad, then the command refuses with a one-line "unsupported" message.
- AC7.5 Given the report or `data.json`, it contains ids, titles, names, numbers and the return reasons of AC4.3 only: no other message text, no prompt or transcript content. Given `--redact`, it contains neither titles nor reasons (AC4.6). The HTML shows free text as text only.

**S8. Analyze skill.**
- AC8.1 Given `data.json` fresher than the last message, then the analyze skill reads only the `digest` and answers in chat with findings, each citing its digest signal, and a proposal each.
- AC8.2 Given missing or stale data, then it runs collect first.
- AC8.3 Given any run, it writes no file and never edits `process.md`.
- AC8.4 Given a finding that needs detail (e.g. which task cost most in which role), then it uses the query command for just that slice, not the whole `data.json`.

**S9. A chosen older scope, on demand (Q19: no backfill).**
- AC9.1 Given an existing scope, live or in `_done`, whose transcripts still exist, when `squad-report <scope>` runs, then its `data.json` and `report.html` are built in that scope's folder (`report/`), whatever its state; no other scope is touched. There is no `--all`.
- AC9.2 Given a closed scope whose transcripts are gone, then it builds with the agents listed "no transcript" and totals marked partial (AC7.2), not an error; a scope that has no messages at all is AC7.3.
- AC9.3 Given an existing `data.json`, then a new run replaces it with the identical result of the same inputs (AC1.5), so the PO can rebuild any time.

**S10. Process help for the report (Q23, optional).**
The PO accepts a process change that makes the report better if it is cheap in effort and tokens.
- AC10.1 Given the Tech Lead's price (spec Technical, Round-3 follow-ups: one `process.md` line in Messages "task id = ticket number NN, alone, first after the type" + "Owns: ticket NN" in the roster template; about 40 tokens read once per role per session, no extra calls), then the Manager asks the PO to approve it as a role-instruction change (Manager edits `process.md`, logged); once in, alias merging (AC2.7) is a fallback for old scopes only. The report works either way and no report ticket depends on it.
- BA view of cost: the rule is already followed in 100% of HANDIN/PASS/FAIL (spec Technical F6), so the change is mostly naming the ticket number consistently (`07`, not `T0`/`07-squadio-helper`); one line read by every role at start.

### Do the digest signals and views answer the PO's questions?
Yes with additions. Matrix of what the PO asks against what answers it (new rows marked +):

| PO question | View | Digest signal (top 3 each, ranked) |
|---|---|---|
| Where did the time go? | header, bucket split, per-iteration, timeline | idle share of agent-time; **+ parallelism** (was the Developer cap used?) |
| Where did the money go? | header, task table, role table | top cost tasks; role cost share; scope-overhead share; **+ cost per PASSed task**; **+ respawns and cache-expiry cost** (re-reading context) |
| Which tasks? | task table, drill-down | top cost tasks; slowest cycle time |
| Which roles? | role table, drill-down | role cost share; coordination share (non-Developer roles) |
| Blocked / waited? | blocking and waiting columns, timeline | longest blocks (who on whom); **+ PO wait** (count, total, longest); **+ review wait** (HANDIN to verdict) |
| Returns? Why returned? | returns column, flag at 3, returns table with reason headline, who, evidence pointer | tasks with most returns (with each reason headline); rework time and cost |
| Is the data trustworthy? | % attributed, partial banner | **+ attribution under threshold** (warn) |
| Was this scope unusual? | rollup | vs other scopes: **deferred** (needs a baseline, see v1 cut) |

Gaps found vs `decisions.md`: PO wait (win-compat escalation E6 alone waited 84 min, longer than most tasks), review wait, iteration dimension, parallelism, cost per PASSed task, respawns. No new data source needed for any (Tech Lead verified on real data): `inbox.jsonl`, `messages.jsonl` (`iteration`, `type`) and transcripts (respawns = sessions of an agent minus 1). Corrections taken from the Tech Lead's facts: no price table existed in `bin/squad-usage` (new `config.json`); gaps are classified by what ends them, not by a 5-minute rule; task id is read from the message subject, not the `task` field.

### v1 cut (BA proposal; PO accepted, Q18, 2026-10-18; Q19 backfill removed)
| Tier | Content |
|---|---|
| Must | collect + `data.json` (+ `digest`), scope `report.html` (header, task table, role table, honesty labels, partial/empty/missing states), `squad-report <scope>` command and `/squad:squad-report`, config file for threshold and patterns, tests |
| Should | `squad-close` hook, rollup over a list of `data.json` files (also from other squads/machines), analyze skill + query command, PO wait / review wait / iteration columns, returned reasons table and `--redact` |
| Could (drop first) | task x role drill-down, per-agent timeline |
| Deferred | `--all` backfill (PO: no, Q19), digest "vs other scopes" (needs a baseline; the PO can build it by running chosen scopes), Token Coach reading the digest, CSV export, legacy flat squads, classifying return reasons |
Size stays L: ~8-9 tickets, order collect, render, rollup, query/analyze, close hook, promotion (backfill dropped).

### Lasting rules to promote (one line each; Tech Lead puts them in `promote.md`)
- Reports never show a bare "time": elapsed or agent-time, labelled derived; dollars labelled estimated at list price.
- PO wait is elapsed time, never agent cost.
- A report contains no transcript or prompt content; the only message text is the returned-reason headline (200 characters), removable with `--redact` (which also removes titles).
- `data.json` is the unit teammates share; a rollup needs nothing else (squad name + scope name identify a scope).
- A report failure never blocks a close.

### PO questions
Round 3 answered 2026-10-18 (verbatim in `decisions.md`). Q14-Q18, Q20, Q21, Q24 yes. Changed by the PO: Q19 (no backfill), Q22 (rollup over teammates' `data.json` list), Q23 (process change welcome if cheap; Tech Lead to price it), Q25 (inputs come from teammates' squads). Open for Tech Lead (not for the PO): price of the Q23 rule; whether data.json needs a field for squad identity beyond `scope.squad`; `schema_version` policy for files from older/newer plugin versions (AC5.5 skips, never guesses).

## Design

**Owner:** plugin-ux-squad-report. **Status:** draft 1, ready for BA review (2026-10-19). Files in `$SCOPE_DIR/ui-design/` (`.claude/squads/plugin/scopes/squad-report/ui-design/`):
- `scope-report.md` + `scope-report.html`: scope report. Sections Overview (6 KPI cards, digest, longest blocks, by iteration), Tasks, Roles, Task × role grid, Timeline (lane per agent + PO-wait lane). Drawer for every drill-down.
- `rollup.md` + `rollup.html`: goal / file-list rollup. KPIs, scopes table (totals footer, report links), share bars, role × scope grid, calendar strip.
- Mocks open from disk; the dark toolbar switches state (`?state=`): scope `done|running|flag|lowattr|missing|empty|error`; rollup `normal|mixed|all|single|empty|error`. Palette: Mango Parrot light only. Fake data, not shipped code.
- Design choices that follow the PO's open questions (Q15-Q17, Q20-Q22 in `round3.html`): elapsed big with agent-time and parallelism under it; PO wait own card and own timeline colour/lane; attribution banner under 60%; cost as default grid metric; idle gaps > 1 h compressed by default; rollup rows link to each scope's `report.html`.
- v1 tiers (BA's cut): Must = header, KPIs, task table, role table, honesty labels, banners and empty/partial/missing states. Should = rollup, PO wait / review wait / iteration columns. Could (drop first) = Task × role grid, timeline, rollup "When" strip.
- Data asks to the Tech Lead are in the last section of each `.md`.

### PO questions
Already in `round3.html` (BA folded them): Q-D1 → Q15 elapsed vs agent-time; Q-D4 → Q16 PO-wait display; Q-D5 → Q17 attribution threshold; Q-D2 → Q20 grid metric; Q-D3 → Q21 idle compression; Q-D6 → Q22 rollup links. Nothing new.

## Technical

**Owner:** plugin-tech-squad-report. Draft 1, 2026-10-19. Verified on real data (see "Verified facts"); prototypes in my scratch dir only, nothing built. Schema agreed in principle with the Designer (their draft of 2026-10-19, differences below).

### Verified facts (real data: `_done/win-compat` 429 msgs / 22 roster rows / 29 agent-h; `_done/remove-board`; 480 transcripts under `~/.claude/projects/-home-chieule-workspace-squad*`)
| # | Fact | Consequence for the design |
|---|---|---|
| F1 | `bin/squad-usage` has **no price table** (decisions.md says it does). It parses tokens only. | A price table is new work: `templates/report/config.json`. |
| F2 | Transcripts carry a `cost-state` record (`totalCostUSD`, per-model tokens and `costUSD`) in 473 of 480 files, written at session end (several per file when resumed, 7 files none). Fitting list-price ratios (output 5x, cache read 0.1x, cache write 2x input) to it: median error per session 7-10%, p90 19-28%. | Compute cost per turn from tokens x config prices (needed to split by task and time). Cross-check with `cost-state` where present: `cost_reported_usd` + `cost_delta_pct` in data.json. Not a primary source (cannot split by task). |
| F3 | A turn gap is **not** "working if <= 5 min". 186 of 270 min of gaps in the 30 s-5 min band end in a peer message: the agent was waiting, not working. | Classify a gap by **what ends it** (rule below). 5 min stays only as a "stalled" guard for gaps ending in a model/tool record. |
| F4 | Every user record has `origin.kind`: `peer` (message from an agent; carries `msg_id`, `name`, `body`), `human` (typed), `plugin` (PO inbox answer), `task-notification` (background shell/Monitor finished), none (tool result). `msg_id` of a peer receipt matches `messages.jsonl` 262 of 262 (win-compat); send ts vs receipt ts differ < 6 s (median 25 ms). | `messages.jsonl` alone times a message; no need to read receipts for time. Receipts only classify the gap end. Old harness versions without `origin` degrade to "idle" (flag in `sources`). |
| F5 | `system/turn_duration` exists but only 2-12 per session (not every turn). | Not used. |
| F6 | Task id is the first token after the message type in 100% of HANDIN/PASS/FAIL (200/200 win-compat, 60/60 remove-board). The hook's `task` field is a regex over the whole text and is wrong or null (`UTF-8`, `null`). The same task appears as `T0`, `07`, `07-squadio-helper (T0)`. | Parse the subject token from `text`, ignore the `task` field. Merge aliases when one subject names both (`07-squadio-helper (T0)`, `04 (T3)`). Tickets: `.scratch/<feature>/issues/NN-slug.md` give titles. |
| F7 | One HANDIN/FAIL is logged 2-4 times (original + copies to TL, Tech, other QA). | Dedupe by (from, type, task, ts within 120 s). |
| F8 | FAIL dedup gives 6 returns in win-compat; the Manager's summary says 7 (one return came through a message that does not start with FAIL). | The PO's rule stands (FAIL = a return). The report labels it "returns (FAIL messages)". |
| F9 | Respawns: 5 sessions for the Manager, 9 for Tech in win-compat; `usage-events.jsonl` holds the *advice* ("fresh") not the act. | Respawn count = sessions of the agent - 1 (found by `agent-name`, as `squad-usage` does). Cache expiry from `squad-usage`'s own `is_expiry`. |
| F10 | `inbox.jsonl` events: `seen` (escalation raised, id `Ex`), `answer`, `delivered`; win-compat escalation intervals 0.02-1.4 h. | PO wait = `seen` to `answer`. |
| F11 | Of 29.3 agent-h in win-compat, 11.2 h are gaps ended by a **typed human message** with no escalation open (agents sitting in panes between PO chat turns, overnight). Only 0.8 h of agent-time overlaps an open escalation. | See PO question T1. Default: `idle`, reason `human_input`. |
| F12 | Collecting win-compat (22 roster rows, agent-name scan of 313 + worktree dirs, full parse) takes ~1 s. The main project dir holds 637 MB, but only the head of each file is read to find the agent. | No cache layer, no incremental mode in v1. A scope with a missing `~/.claude/projects` (other machine) reports "no transcript". |
| F13 | Prototype on win-compat and remove-board: working time attributed to a task by the sticky rule = 88% and 87%. | The 60% banner threshold is safe for real scopes. |
| F14 | `.claude/squads` is git-ignored. | Reports are local files; fixtures for tests must be synthetic under `tests/`. |

### Time model (the rules `collect` implements)
Per agent: all transcript records with a `timestamp` and `isSidechain` false, from every session of that agent, sorted. Timestamps floored to whole seconds on ingest, so every duration is an integer and **bucket sums equal agent-time exactly** (AC1.4). Gaps are taken within one session only; the gap between two sessions of an agent is not agent-time (agent did not exist); it is counted as `respawn_gap_s` (not a bucket).

Each gap between two consecutive records is classified by the record that **ends** it (`b`) and the state at its start (`a`):
| Gap ends with | Bucket | Note |
|---|---|---|
| assistant, tool result, system, hook (model or tool running), length <= `stall_s` (300) | **working** | |
| the same, length > `stall_s` | **working**, flagged `stalled` in the segment | a permission prompt or a very long call; not blocking (cannot tell). Counted separately in totals (`stalled_s`, inside working) |
| a `task-notification`, or a long tool call whose command matches `wait_patterns` | **waiting** | background shell, Monitor, `run_suite.py` |
| a `peer` message, and this agent has an unanswered ASK/BLOCKED sent before the gap start (no message from its addressee since) | **blocking**, reason `peer`, `on` = addressee, `task` | ends at the first message from the addressee |
| a `peer` message, otherwise | **idle**, reason `peer` | waiting for work |
| a `human` or `plugin` message while an escalation is open (`seen` <= gap start < `answer`) | **blocking**, reason `po` | any agent |
| a `human` or `plugin` message, no escalation open | **idle**, reason `human_input` | F11 |
| end of file (session ended) | none | no gap |
Open points the AC must pin: a gap straddling an escalation boundary is split at the boundary; HANDIN sent and no verdict yet is **not** blocking (it is review wait, a separate measure over elapsed time, not an agent bucket).
My first prototype wrongly counted every gap after an old ASK as blocking (6.8 h of 29 h); the unanswered-ASK condition above fixes that and is the first AC.

Cost: per assistant message (max usage per `message.id`, as `squad-usage` does; subagent turns included, priced at their own model) tokens x `prices[model]`. A turn's cost goes to the bucket of the gap it sits in (always working) and to the agent's task context at that second. 1h and 5m cache writes are priced separately when `usage.cache_creation` splits them. An unknown model uses `prices["default"]`, listed in `sources.unpriced_models`.

Task context (attribution), first match wins, layer recorded per second so `% attributed` is exact. **Denominator = non-idle agent seconds (working+waiting+blocking); idle is excluded** (BA/Designer, agreed). The 88%/87% prototype figure was working-time only; the non-idle figure is measured in the real-data check:
1. **message**: the agent's current task = the subject token of the last message it sent or received that carries one (sticky until another task appears).
2. **branch**: a Developer's worktree branch / roster `Owns` text when it names a ticket token.
3. otherwise **overhead** (task `null`).
Tokens resolve to a canonical task: aliases merged (`X (Y)`), `NN-slug` and bare `NN` map to ticket `NN` when `.scratch/*/issues/NN-*.md` exists (the feature dir is the one whose slugs match most subject tokens; none found = no titles, still works). Tokens `STATUS`, `squad-*` and agent names are not tasks.
Returns, rework, review wait: from deduped messages. Return = FAIL, task = its subject. Rework = FAIL to the task's next HANDIN. Review wait = HANDIN to the last PASS/FAIL before the next HANDIN of the task.

### File layout (all new unless marked)
```
bin/squad-report            CLI, python3, thin (like squad-inbox): scope|goal|all, query, status
bin/squadtranscript.py      EXTRACTED from bin/squad-usage: config_dir, projects_glob, find_transcript, agent_name,
                            agent_sessions, read_lines/read_session, parse_ts, is_expiry (no behaviour change)
bin/squad-usage             (edit) imports squadtranscript instead of defining them
bin/squadreport.py          collect: timeline, buckets, cost, attribution, returns, waits, digest, rollup data, query
bin/squadreport_html.py     render: inline css/js/data into one file; rollup page
templates/report/config.json       defaults: stall_s, wait_patterns, min_segment_s, prices, unknown_model price
templates/report/template.html     one page; placeholders __CSS__ __JS__ __DATA__
templates/report/report.css        Mango Parrot light palette only
templates/report/report.js         sort, filter, tab, timeline; reads the embedded data; textContent only
skills/squad-report/SKILL.md           /squad:squad-report (run, relay the 5-line summary)
skills/squad-report-analyze/SKILL.md   analyze (reads digest, uses `squad-report query`)
tests/test_squadtranscript.py, test_squadreport_collect.py, _tasks.py, _digest.py, _html.py, _rollup.py,
tests/test_squad_report_cli.py, tests/report_fixtures.py (builder of synthetic transcripts)
bin/squad-close (edit)      report step; tests/test_squad_close.py (edit)
docs/adr/0012-squad-report-derives-from-transcripts.md, CONTEXT.md, README.md (promotion ticket)
```
Output (per scope home, git-ignored): `<home>/report/data.json`, `<home>/report/report.html`. Goal: `goals/<g>/report/`. `rollup <files>`: `--out DIR` (default `./squad-rollup/`) gets `index.html` + `data.json`. A per-squad override of `config.json` is read from `<squad>/settings/report.json` when present (shallow merge by key; JSON, not TOML: the Python floor has no `tomllib`). Config is echoed into `data.json`, so a report always says which numbers it used.
Names: command `squad-report`, skill `squad-report`, analyze skill `squad-report-analyze` (matches `squad-start`, `squad-process-update`), plugin command `/squad:squad-report`. Why not `squad-usage --report`: usage is a hot-path Stop hook; keep it small.
Assets are read from the plugin dir (`dirname(realpath(__file__))/../templates/report`), never from the squad.

### CLI
```
squad-report [<scope>|<goal>] [--squad S] [--out DIR] [--no-html] [--quiet]   collect + render; prints the path + 5-line summary; exit 0
squad-report <scope> --final            same, not partial (squad-close passes it)
squad-report rollup <data.json>... [--out DIR]   rollup of scope data.json files from anywhere (teammates' squads, other machines); writes index.html + data.json (kind rollup)
squad-report ... --redact               drop free text (ticket/escalation titles, return reasons) from data.json, for sharing
squad-report status <scope>             fresh | stale | missing  (exit 0 | 3 | 4); stale = a message/escalation/roster row newer than data.json's sources
squad-report query <scope> <what> [--task X] [--role R] [--top N] [--refresh]   compact lines/JSON from data.json only
   what: digest | totals | tasks | roles | task | role | matrix | blocks | returns | iterations
```
A bare name is resolved against `scopes/`, `scopes/_done/`, `goals/`, `goals/_done/` of `$SQUAD_DIR` (or `--squad`). Exit 2 refusal (flat squad, unknown name, mixed), 1 error. A scope whose transcripts are gone is refused by `squad-report <scope>` (exit 2, existing `data.json` untouched). Output text is ASCII-safe, no ANSI.

### data.json (schema_version 1)
Rules: UTF-8, `sort_keys`, `separators=(",",":")`, integers for seconds/tokens, USD rounded to 4 decimals, timestamps `YYYY-MM-DDTHH:MM:SSZ`. Only `generated_at` varies between runs on equal input (AC1.5). **Contains ids, names, numbers and ticket/escalation titles (cut at 120 chars); no message, prompt or transcript text (AC7.5).** Additive fields never bump the version; rename/removal does; the renderer and rollup refuse any other `schema_version` (`schema_mismatch`).
```
{ "schema_version": 1, "kind": "scope",
  "scope": {"name","squad","size","status":"running|done","partial":bool,"partial_reasons":["running","no_transcript:<agent>",...],
            "generated_at","window":{"start","end"},"last_message_at","iterations":[1..n]},
  "config": {"stall_s","wait_patterns","min_segment_s","prices":{...}},
  "sources": {"agents_total","agents_with_transcript","transcripts":n,"messages":n,"escalations":n,"unpriced_models":[],
              "ticket_dir":"<relative or null>","harness_origin":bool},
  "totals": {"wall_s","agent_s","parallelism",   // wall_s = elapsed wall clock; same name in the rollup scopes[].totals
             "buckets_s":{"working","waiting","blocking","idle"},          // sum == agent_s
             "stalled_s","respawn_gap_s",
             "blocking_s":{"peer","po"}, "idle_s":{"peer","human_input"},
             "tokens":{"input","cache_read","cache_write","output"},
             "cost_usd","cost_reported_usd","cost_delta_pct",
             "returns","tasks_passed","cost_per_passed_task_usd",
             "attributed":{"time_pct","cost_pct","layers":{"message","branch","overhead"}},   // time_pct = attributed non-idle s / non-idle s; layers = non-idle seconds
             "po_wait":{"count","total_s","longest_s","pct_of_elapsed","items":[{"id","title","raised_at","answered_at","wait_s"}]}},
  "iterations": [{"n","window","agent_s","cost_usd","returns"}],
  "tasks": [{"id","aliases":[],"title","dev","status":"open|passed","iteration",
             "window":{"start","end"},"cycle_s","buckets_s":{...},"tokens":{...},"cost_usd",
             "returns","flag":bool,                                  // flag: returns >= 3
             "returns_list":[{"fail_at","fail_by","handin_at","reason"}],"rework_s","rework_cost_usd",
             "review_waits":[{"handin_at","verdict_at","verdict":"PASS|FAIL|none","wait_s"}]}],
  "roles": [{"name","role","sessions","respawns","cache_expiries","expiry_cost_usd","transcript_found","live",
             "buckets_s","idle_s":{"peer","human_input"},"tokens","cost_usd"}],  // one row per agent; idle_s sums to buckets_s.idle; role rollup = group by role in the UI
  "matrix": [{"task"|null,"agent","time_s","buckets_s","tokens","cost_usd"}],   // sparse, only non-zero cells
  "agents": [{"name","role","transcript_found","live","segments":[[start_s,end_s,"w|a|b|i","task|null","on"]],      // offsets from window.start; 5th element `on` = agent name or "PO" for b segments, else null; merged, < min_segment_s absorbed (display only)
              "events":[[t_s,"BLOCKED|ASK|ANSWER|FAIL|HANDIN|PASS|DECISION","task|null"]]}],
  "digest": [{"id","kind","weight","text","value","unit","target":{"view","id"}}] }
rollup: { "schema_version":1,"kind":"rollup","goal":{"name","scopes":[..]}, "totals":{same as scope totals},
          "scopes":[{"name","status":"running|done|no_data|stale|schema_mismatch|skipped","size","report_href","window":{"start","end"},"generated_at","last_message_at",
                     "totals":{"wall_s","agent_s","buckets_s","tokens":{4 kinds},"cost_usd","tasks","passed","flagged_tasks","returns","po_wait_s","attributed_time_pct"},
                     "roles":[{"role","agent_s","cost_usd","tokens"}]}],
          "roles":[{"role","agent_s","cost_usd","tokens"}], "digest":[..] }
```
**Differences from the Designer's draft (their field in parentheses):** `buckets_s` names fixed `working|waiting|blocking|idle` (as theirs); `agents[].segments` use `[start_s,end_s,bucket,task]` with offsets, not ISO strings (size: a 3-day scope stays under ~2,000 segments per agent after merging; display-only, totals come from the raw seconds, so segments do not sum exactly); added: `blocking_s` split `peer|po`, `idle_s` split `peer|human_input`, `stalled_s`, `respawn_gap_s`, `cost_reported_usd`, `cost_delta_pct`, `tasks[].aliases`, `tasks[].iteration`, `tasks[].review_waits`, `iterations[]`, `cost_per_passed_task_usd`, `po_wait.items`. `roles[]` is per agent (the role grouping is a UI group-by, so data stays one table); `matrix[].task null` = overhead as they asked. `digest[].weight` is the rank key (a share 0-1 of its own total) and `text` is built from numbers by a template, never from transcript text. Designer round 2 (accepted): blocking segments carry `on` (adjacent b segments merge only when `on` is equal); `live` = scope running and the roster row says live (an input, so the run stays deterministic); rollup `scopes[].totals.wall_s` = the scope's `totals.wall_s` (the scope file uses `wall_s`, not `elapsed_s`), `status` adds `skipped` (duplicate (squad,scope) key, older copy). Their `status` in the rollup is kept; `report_href` is computed at render time (scopes move to `_done/` at close). I accept their `goal{name,scopes[]}` shape.

### Round-3 follow-ups (PO answers E2, 2026-10-19)
- **Portable `data.json`.** A teammate's scope `data.json` is the only input of `squad-report rollup <files>`: totals, roles[], tasks, digest and `scope.{name,squad,size,status,window,generated_at,last_message_at}` are all in it; the rollup never opens a transcript, a squad folder or a path. `data.json` holds no absolute path (`sources.ticket_dir` is relative and unused by rollup). Rollup rows are keyed `(squad, scope)`; a duplicate key keeps the newest `generated_at` and lists the other as skipped. `report_href` = a relative link to a `report.html` sitting beside that file, else null (no link). Files with another `schema_version` or `kind` show as `schema_mismatch` and never fail the run. Prices differ per squad config: the rollup sums each file's own `cost_usd` and shows a "mixed price tables" note when `config.prices` differ. Goal rollups keep working from the squad folder and use the same code on the scopes' `data.json`.
- **Return reasons.** Yes, we have them: the text of the FAIL message (`returns_list[].reason`: `FAIL <task>` prefix removed, whitespace collapsed, cut at 200 chars; `fail_by` already names the checker). It is the QA's own summary and usually names the finding (win-compat: 12 FAIL messages, each names file and defect). The longer finding list lives in `evidence/<task>/qa-*.md`, a free-form file: not read, not portable. This is free text from messages, so **AC7.5 changes** (BA to rewrite): `data.json` carries titles and return reasons, no other message text; `--redact` removes both. Risk: a reason can name a path or a secret an agent typed; the HTML shows it via `textContent` only. No classification of reasons (keyword guesses would mislead).
- **Q23, cheap naming rule (process.md, PO approves).** Add to Messages: "Task id = the ticket number (`NN`), alone, first after the type; never an alias or slug; `squad-start` scope names unchanged." Effort: one line in `process.md` (Manager edit, PO approval as a role-instruction change) plus one sentence in `roster.md` template "Owns: ticket NN" for Developers. Token cost: about 40 tokens read once per role per session (~10 agents), no extra tool calls. Effect: alias merging becomes a fallback for old scopes only, and attribution rises because branch/roster layer also finds the ticket. Recommend yes.

### Digest (max 8, ranked by `weight` desc, ties by the kind order below; thresholds only 3 returns and 60% attributed)
`top_cost_task` (share of cost), `top_cost_role`, `scope_overhead` (share of cost), `idle_share` (of agent_s), `longest_block` (share of agent_s, names who waited on whom), `po_wait` (pct of elapsed), `review_wait` (median, share of elapsed), `most_returns` (flag at 3), `rework_cost`, `respawns` (cache-expiry cost share), `parallelism`, `attribution_low` (only when < 60%, weight 1). Same input, same digest (deterministic).

### Reuse of `bin/squad-usage`
Extract, do not copy: `squadtranscript.py` takes `config_dir`, `projects_glob`, `find_transcript`, `agent_name`, `agent_sessions`, `read_lines`/`read_session` (turn dedupe by message id, subagent files), `parse_ts`, `is_expiry`, `TOKEN_FIELDS`; `squad-usage` keeps its CLI and tables and imports them. Two existing tests copy a fixed file list into a stub plugin dir and must add `squadtranscript.py`: `tests/test_squad_respawn.py` (line 162) and `tests/test_squad_spawn.py` (line 543). The collect needs more than `read_session` returns (it drops the record kind and `origin`), so `squadtranscript` gains `iter_records(path)` (one generator over main + subagent files) and `read_session` is rebuilt on it. `squad-usage` tests are the safety net and must pass unchanged.

### squad-close hook
In `bin/squad-close`, `--scope` and `--goal` only, not `--dry-run`, before the `== agents` retire step and before the folder move:
`python3 "$bin/squad-report" "$name" --final --quiet || echo "warning: report not generated (squad-report exited $?)" >&2` then continue; the script's own exit code, output order and effects are otherwise unchanged. A goal close runs the rollup from the scopes' `data.json`; a scope in `_done/` without one is `no_data`. A `--deadline 60` argument makes `squad-report` stop itself (exit 5) instead of using shell `timeout` (not guaranteed on Git Bash). The report folder travels with the scope into `_done/`. Windows (ADR 0011): `python3`, `encoding="utf-8"`, `newline="\n"`, `squadio.utf8_stdio()`, no `fcntl`; write `data.json` to a temp name in the same folder then `os.replace`.

### Security and data rules
- `report.html` embeds data inside `<script type="application/json">`: escape `<`, `>`, `&`, U+2028/9 (`<`) so a title cannot close the tag; the JS builds DOM with `textContent` and `setAttribute` only, never `innerHTML`. No external URL, font, script or request (AC1.2). A test plants `</script><img src=x onerror=...>` as an escalation title and a ticket title.
- No absolute home path in output; transcript sessions appear as ids only. A planted canary string in a prompt/message body must not appear in `data.json` or `report.html`.
- Read-only on transcripts, roster, messages, inbox. Writes only `report/` and the rollup folder. Pure python: no child process, no network.

### Test approach
No real transcripts in the repo (F14, they hold prompts). `tests/report_fixtures.py` builds a **synthetic scope**: roster, messages.jsonl, inbox.jsonl, usage-events.jsonl, tickets, and transcripts in a temp `CLAUDE_CONFIG_DIR` with known timestamps, so every bucket, task and cost has a hand-computed expected value (the pattern of `test_squad_usage.py`'s `turn()` helper). Must-have cases: each row of the time-model table; unanswered ASK vs answered; stalled gap; gap across two sessions; straddling an escalation; copies of one HANDIN counted once; alias merge; cost with 1h/5m cache split and an unknown model; `cost-state` delta; running scope = partial; missing transcript; no messages; flat squad refused; determinism (two runs equal except `generated_at`); invariants on every fixture (buckets sum, task cost + overhead = total, matrix sums = totals, every closed item has its end, every task row has the fields the consumer reads: field-shape check per process.md); no canary text; HTML structure (single file, no external URL, embedded JSON == data.json, escaped); rollup with ok/missing/stale/mismatch rows; close hook (report first, close still completes when the report fails, `--dry-run` writes nothing). The suite stays Python-only: no node, no browser dependency (CI-friendly, Windows-safe).
Behaviour of `report.js` and the built UI vs the design: QA blackbox opens the generated `report.html` over `file://` with `playwright-cli` and screenshots each screen and state (needs a row in `project.md` → Running app: "squad-report: open the generated report.html with playwright-cli"). **Real-data checks (process.md → verify against the real thing)** are a QA whitebox read-only live run, not CI: `squad-report` on `_done/win-compat` and `_done/remove-board`, asserting the invariants above, returns = FAIL dedup count (6 / 1), PO wait items = 8 / the escalations, field shape of every row, and a report of the % attributed; plus the constant/idle case and the `cost_delta_pct` figure. The two real scopes are the acceptance reference; the constant/idle case is a scope with one agent and no messages.

### Touched files and order (future tickets; the Team Lead owns the plan)
| # | Ticket | Touches | After |
|---|---|---|---|
| T1 | Extract `squadtranscript.py` + `iter_records` | `bin/squadtranscript.py`, `bin/squad-usage`, `tests/test_squad_respawn.py`, `tests/test_squad_spawn.py`, new `tests/test_squadtranscript.py`; `test_squad_usage.py` unchanged | - |
| T2 | Collect core: timeline, buckets, tokens, cost, config, partial/missing states | `bin/squadreport.py` (core), `templates/report/config.json`, `tests/report_fixtures.py`, `tests/test_squadreport_collect.py` | T1 |
| T3 | Tasks: aliases, attribution layers, returns, rework, review wait, PO wait, iterations, respawns | `bin/squadreport.py` (tasks section) , `tests/test_squadreport_tasks.py` | T2 (interface: T2 returns `Timeline` = per-agent `[(start,end,bucket,reason,on)]` + per-turn `(ts,tokens,cost)`; T3 consumes it, so the two can start together once T2 pins the type) |
| T4 | Digest + `data.json` writer + CLI `squad-report <scope>` + `status` | `bin/squad-report`, `bin/squadreport.py` (digest, write), `tests/test_squadreport_digest.py`, `tests/test_squad_report_cli.py` | T3 |
| T5 | Scope report HTML (UI ticket; `Design:` line, waits for design final) | `bin/squadreport_html.py`, `templates/report/{template.html,report.css,report.js}`, `tests/test_squadreport_html.py` | T4 schema frozen; Designer final |
| T6 | Rollup (goal / file list) data + page | `bin/squadreport.py` (rollup), `bin/squadreport_html.py`, `tests/test_squadreport_rollup.py` | T4, T5 |
| T7 | `query` + analyze skill + `/squad:squad-report` skill | `bin/squadreport.py` (query), `bin/squad-report`, `skills/squad-report/SKILL.md`, `skills/squad-report-analyze/SKILL.md`, `tests/test_squad_report_query.py` | T4 |
| T8 | `squad-close` hook | `bin/squad-close`, `tests/test_squad_close.py` | T4 (T6 for goals) |
| T9 | dropped (Q19: no backfill; `squad-report <scope>` builds any existing scope) | - | - |
| T10 | Integration: merge passed branches, targeted tests; Tech Lead runs the full suite `--tz` | - | all |
| T11 | Promotion (last): `promote.md` to `CONTEXT.md`, ADR 0012, README | `CONTEXT.md`, `docs/adr/0012-*.md`, `README.md` | T10 |
Parallel: T2 and T3 in step with a pinned interface; T7 and T8 after T4; T5 runs beside T3 once the Designer is final. Files two tickets share: `bin/squadreport.py` (T2, T3, T4, T6, T7 are sections of one file: **split it** into `squadreport.py` (collect), `squadreport_tasks.py` (T3), `squadreport_digest.py` (T4), `squadreport_rollup.py` (T6), `squadreport_query.py` (T7) so parallel Developers touch different files; I will fix the interface in the plan handover). `bin/squad-report` is shared by T4, T6, T7: T4 creates all subcommand stubs.
If the PO cuts "Could" (drill-down, timeline): `matrix` and `agents[].segments` stay in the schema but T5 drops the views; collect cost for them is small.

### Risks
- **Attribution quality** depends on agents writing the task id after the type. Measured 100% on HANDIN/PASS/FAIL; unmeasured on a scope where agents ignore it. Mitigation: `% attributed` + banner + overhead row.
- **Cost accuracy**: list-price estimate vs `cost-state` is 7-10% median per session on this machine; model prices change. Prices live in config; the report shows the delta. I cannot verify current list prices offline: the PO or the ticket author supplies them (T2 AC: fixture-defined; T2 default table from `cost-state` calibration, labelled).
- **Transcripts of another Claude account** (`c1`/`c2`, `CLAUDE_CONFIG_DIR`) are invisible: marked "no transcript", partial. `config.json` may list extra `claude_config_dirs`.
- **`squad-usage` refactor** touches the Stop-hook hot path: T1 is behaviour-neutral and gated by its existing tests.
- **Old transcripts without `origin`** (pre-peer harness): all gaps ending in a message classify as idle; `sources.harness_origin=false`, banner.
- **Process drift**: if a future `process.md` changes message types the digest lists (ASK, BLOCKED, HANDIN, PASS, FAIL), `squadreport` must follow; a test pins the list against `hooks`' `squad-log-message` regex.

### Migrations, compatibility, deploy
Additive only: new files, one extracted module, two edits (`squad-usage` import swap, `squad-close` report step). No stored data changes; `report/` is new and disposable (rebuild any time). `schema_version` policy above. Deploy order: plugin release only (PO deploys); nothing to run on shared data; rollback = remove the `squad-close` step (a warning-only step cannot corrupt a close). Running `squad-report <scope>` on a `_done` scope writes only a new `report/` folder there.

### PO questions
1. **T1 · Gaps ended by your typed reply.** In win-compat 11.2 of 29.3 agent-hours (38%) were agents sitting between your chat messages (overnight, between rounds) with no inbox escalation open. Only 0.8 h overlapped an open escalation. Counting all of it "blocking on PO" would make you look like the bottleneck for time you were away; counting it as plain idle hides your chat latency. Recommendation: **escalation open = blocking on PO; otherwise idle, with reason "waiting for your chat reply" shown as a sub-line under idle.** Why it matters: it sets the headline blocking and idle numbers.
2. **T2 · Task ids differ across roles.** The same ticket is called `T0`, `07` and `07-squadio-helper` in one scope. Recommendation: **merge only when one message names both** (`07-squadio-helper (T0)`), show the leftover separately, and show % attributed; no `process.md` change. Why: otherwise a task splits into several rows and its returns and cost with it. (If you would rather fix the cause, a one-line `process.md` rule "task id = ticket number" removes the problem for future scopes.)
3. **T3 · Show Claude Code's own cost figure beside the estimate?** Transcripts hold the harness's reported cost for 473 of 480 sessions; our list-price estimate differs by a median 7-10% per session. Recommendation: **yes, one small line "Claude Code reported $X (estimate off by Y%)" next to the headline cost, hidden when absent.** Why: it tells you how far to trust the estimate for free; the cost is one extra number on the page.
4. **T4 · Reports stay local.** `report/` lives inside the scope folder, which is git-ignored, and moves to `_done/` with it. Recommendation: **keep it local and disposable (rebuild any time, never committed), and `squad-report <scope>` can build a `_done` scope's `report/` on demand.** Why: only the promoted facts belong in the repo; say if you want `data.json` of closed scopes committed as history.

