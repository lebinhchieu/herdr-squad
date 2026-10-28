# Mapping: every source line to its rule

Source = `templates/squad/process.md` (v6), `agents/<role>.md` or `log row <N>` (line N of the live squad's `process-log.md`, rows 33-49 are the Coach and Manager changes of 2026-10-16 to 2026-10-19 that are not `v<N>` migration rows). Target = rule ID(s), `dropped: duplicate of <ID>`, `dropped: structure`, `dropped: replaced by compose`, `dropped: fix <a-e>`, or `stays in card`. Several IDs are comma separated: the line was split across those rules. Header rows, separator rows and `#` headings are not listed.

| Source | Target | Source text (first 60 chars) |
|---|---|---|
| templates/squad/process.md:3 | dropped: structure | process-version: 6 |
| templates/squad/process.md:5 | WHO-6 | Every role reads the sections its row names, at start and wh |
| templates/squad/process.md:9 | dropped: replaced by compose | / Developer, QA whitebox, QA blackbox / its task and AC (QA: |
| templates/squad/process.md:10 | dropped: replaced by compose | / UI/UX Designer / the UI tasks and AC, the UI conventions r |
| templates/squad/process.md:11 | dropped: replaced by compose | / Token Coach / what the Manager's briefing names / |
| templates/squad/process.md:12 | dropped: replaced by compose | / BA, Team Lead, Tech Lead, Manager / everything / |
| templates/squad/process.md:16 | FILE-1 | A **request** from the PO is one of: |
| templates/squad/process.md:17 | FILE-1 | - **A lone task: one scope.** Own Manager and pod, isolated, |
| templates/squad/process.md:18 | FILE-1 | - **A goal: several scopes.** One goal Manager lives across  |
| templates/squad/process.md:20 | FILE-1 | A **pod** is the role sessions that deliver one scope. |
| templates/squad/process.md:24 | FILE-1 | / Project / the repo / for good / Domain and goal knowledge  |
| templates/squad/process.md:25 | FILE-1 | / Squad / `.claude/squads/<squad>/` / for good / This file,  |
| templates/squad/process.md:26 | FILE-1 | / Goal / `goals/<goal>/` / until the goal closes / What its  |
| templates/squad/process.md:27 | FILE-1 | / Scope / `scopes/<scope>/` / until the scope closes / One p |
| templates/squad/process.md:31 | FILE-2 | / `SQUAD_DIR` / every agent / Squad folder / |
| templates/squad/process.md:32 | FILE-2 | / `SCOPE_DIR` / agents of a scope / Scope folder / |
| templates/squad/process.md:33 | FILE-2 | / `GOAL_DIR` / goal Manager, agents of a scope in a goal / G |
| templates/squad/process.md:34 | FILE-2 | / `SQUAD_NAME`, `SQUAD_ROLE`, `SQUAD_SCOPE` / every agent /  |
| templates/squad/process.md:36 | FILE-2 | Your folder is `$SCOPE_DIR` (`$GOAL_DIR` for the goal Manage |
| templates/squad/process.md:40 | CORE-5 | - Write a durable thing to a file first, then send a message |
| templates/squad/process.md:41 | FILE-3 | - `project.md` says where things live (requirements, AC, dec |
| templates/squad/process.md:42 | FILE-4 | - Edit structured files (`roster.md`, notes, tables) with a  |
| templates/squad/process.md:43 | FILE-3 | - Scope files live in `scopes/<scope>/`. The goal folder hol |
| templates/squad/process.md:47 | FILE-6 | / `project.md` / PO, Managers / Source map / |
| templates/squad/process.md:48 | FILE-6 | / `process.md`, `process-log.md` / Managers / This file; eac |
| templates/squad/process.md:49 | FILE-6 | / `scope.md` / Manager / PO's brief, `goal:`, `touches:`, `s |
| templates/squad/process.md:50 | FILE-6 | / `roster.md` / Manager; Team Lead for its Developers / Each |
| templates/squad/process.md:51 | FILE-6 | / `escalations.md` / Manager / Waiting on the PO / |
| templates/squad/process.md:52 | FILE-8 | / `iterations/<n>.summary.md` / Team Lead (M, L) / Pod summa |
| templates/squad/process.md:53 | FILE-7 | / `iterations/<n>.md`, `iterations/<n>.log.md` / Manager / G |
| templates/squad/process.md:54 | FILE-7 | / `tasks/<id>.md` / Plan owner (Team Lead; Tech Lead in S) / |
| templates/squad/process.md:55 | FILE-9 | / `<ticket path minus .md>.evidence/` / Developer / `evidenc |
| templates/squad/process.md:56 | FILE-9 | / `evidence/<task>/` / QAs, Tech Lead / Reviewers' working f |
| templates/squad/process.md:57 | FILE-9 | / `ui-design/<task>.md` / Designer / One UI task's design (` |
| templates/squad/process.md:58 | FILE-6 | / `promote.md` / Tech Lead / For the project docs / |
| templates/squad/process.md:59 | NOTE-1 | / `roles/<agent>.notes.md` / each agent / Under 80 lines / |
| templates/squad/process.md:60 | FILE-6 | / `messages.jsonl`, `usage-events.jsonl` / hooks / Message l |
| templates/squad/process.md:61 | FILE-10 | / `goal.md` / goal Manager / Brief, ordered scopes with depe |
| templates/squad/process.md:62 | FILE-10 | / `shared/decisions.md`, `shared/summaries/<scope>.md` / Tec |
| templates/squad/process.md:63 | FILE-10 | / `shared/contracts/<name>.md` / Tech Leads of both scopes / |
| templates/squad/process.md:67 | START-1 | Every scope and goal starts with these; its brief may overri |
| templates/squad/process.md:69 | START-2a, START-2b | - **Developer cap:** 3 at once. The Team Lead (S: the Manage |
| templates/squad/process.md:70 | START-1 | - **Budget:** the Manager checks in with the PO at each iter |
| templates/squad/process.md:71 | START-1 | - **Done means:** the size's Done rule (Sizes), evidence sav |
| templates/squad/process.md:75 | START-3 | 1. The PO runs `/squad:squad-start "<text>"`; it makes the f |
| templates/squad/process.md:76 | START-4 | 2. **Names.** A scope or goal is named after its ticket id ( |
| templates/squad/process.md:77 | START-4 | 3. An agent is `<squad>-<role-short>-<scope>[-n]`, at most 3 |
| templates/squad/process.md:78 | START-3 | 4. **Overlap.** `touches:` lists the repos or paths the work |
| templates/squad/process.md:79 | START-3, START-2b | 5. The Manager reads the brief, sizes the scope (Sizes), pro |
| templates/squad/process.md:85 | START-5 | / Manager / Lives and ends with the scope / The goal Manager |
| templates/squad/process.md:86 | START-5 | / BA, Team Lead, Tech Lead, QA whitebox, QA blackbox / One s |
| templates/squad/process.md:87 | START-5 | / Designer / One session per scope; retired once every desig |
| templates/squad/process.md:88 | START-5 | / Developer / One session per task / Same / |
| templates/squad/process.md:89 | START-5 | / Token Coach / At the close (Iterations) / Same / |
| templates/squad/process.md:91 | START-5 | A lone scope sees nothing of other scopes; a scope in a goal |
| templates/squad/process.md:95 | SIZE-1 | The Manager proposes each scope's size with its signals, the |
| templates/squad/process.md:99 | SIZE-2 | / **S** Quick fix / Manager, Tech Lead, Developers / 1–2 tas |
| templates/squad/process.md:100 | SIZE-2 | / **M** Feature / + BA, QA whitebox, QA blackbox, Team Lead  |
| templates/squad/process.md:101 | SIZE-2 | / **L** Full pod / As M / Unclear requirements or open quest |
| templates/squad/process.md:103 | SIZE-3 | Work bigger than one L scope is a goal. A `design:` line in  |
| templates/squad/process.md:105 | SIZE-4 | - **Signals:** tasks, repos touched, user-visible change, op |
| templates/squad/process.md:106 | SIZE-4 | - **Risk flags force at least M:** DB migration or data chan |
| templates/squad/process.md:107 | SIZE-4 | - When unsure, size up. |
| templates/squad/process.md:113 | SIZE-5a, SIZE-5b | / Business AC / Ticket as written; business doubt moves it t |
| templates/squad/process.md:114 | SIZE-6a, SIZE-6b | / Plan, order, assignment / Tech Lead / Team Lead / Team Lea |
| templates/squad/process.md:115 | SIZE-7a, SIZE-7b | / Code and test check / Tech Lead reads the diff, runs tests |
| templates/squad/process.md:116 | SIZE-8a, SIZE-8b | / Behaviour check / Developer saves Playwright/API evidence  |
| templates/squad/process.md:117 | SIZE-9 | / UI/UX design (only when `design: yes`) / Designer / Design |
| templates/squad/process.md:118 | SIZE-10a, SIZE-10b | / Built UI vs the design / Developer screenshots each screen |
| templates/squad/process.md:119 | SIZE-11a, SIZE-11b | / Outside questions (open-points place in `project.md`) / Te |
| templates/squad/process.md:121 | SIZE-6b | The plan file has the same format in every size; only its ow |
| templates/squad/process.md:125 | SIZE-13, SIZE-14 | - **Up:** the Manager moves a scope up on its own when a bus |
| templates/squad/process.md:126 | SIZE-15 | - **Down:** only at an iteration boundary, with the PO's OK; |
| templates/squad/process.md:127 | SIZE-16 | - **Handover on moving up:** the Tech Lead writes a `## Hand |
| templates/squad/process.md:128 | SIZE-16 | - The Manager logs every size change in `scope.md` and the i |
| templates/squad/process.md:132 | GOAL-1 | - `goal.md` orders the scopes with their dependencies. The g |
| templates/squad/process.md:133 | GOAL-1 | - Independent scopes may run at once (cap: Defaults). |
| templates/squad/process.md:134 | GOAL-2 | - **Shared, and nothing more:** `shared/decisions.md`: one ` |
| templates/squad/process.md:135 | GOAL-2 | - `shared/summaries/<scope>.md`: one page per closed scope:  |
| templates/squad/process.md:136 | GOAL-2, GOAL-3a, GOAL-3b | - `shared/contracts/<name>.md`: both Tech Leads agree it bef |
| templates/squad/process.md:137 | GOAL-5 | - **Stacked branches.** Nothing merges until the PO asks, so |
| templates/squad/process.md:138 | GOAL-5 |   - A task that needs unmerged work is spawned with `--base  |
| templates/squad/process.md:139 | GOAL-6a, GOAL-6c |   - Each scope ends with one integration task: a Developer b |
| templates/squad/process.md:140 | GOAL-6a |   - A one-task scope has no integration task: its passed bra |
| templates/squad/process.md:141 | GOAL-7 |   - **Check a merge target before naming it:** the Manager r |
| templates/squad/process.md:142 | GOAL-4 | - A lone scope builds on the project as the PO left it. |
| templates/squad/process.md:146 | PROMO-1 | A task, reviewed and merged like any other, writes what must |
| templates/squad/process.md:148 | PROMO-2, PROMO-3a, PROMO-3b | - **Lone scope:** the Tech Lead keeps `promote.md` while wor |
| templates/squad/process.md:149 | PROMO-4 | - The scope's last task: a Developer commits `promote.md` to |
| templates/squad/process.md:150 | PROMO-6 | - **Goal:** scopes do not promote at their own close; lastin |
| templates/squad/process.md:151 | PROMO-6 | - When it passes, the goal Manager adds `promoted: <date> <c |
| templates/squad/process.md:152 | PROMO-7 | - An abandoned goal keeps its knowledge in `goals/_done/<goa |
| templates/squad/process.md:156 | CLOSE-1 | - **Scope:** the PO confirms the close at a check-in; the Ma |
| templates/squad/process.md:157 | CLOSE-2 | - `squad-close` retires the scope's agents (its Manager last |
| templates/squad/process.md:158 | CLOSE-3a, CLOSE-3b | - **In a goal,** the Tech Lead writes the scope's summary an |
| templates/squad/process.md:159 | CLOSE-4 | - **Goal:** closes once every scope is closed and the promot |
| templates/squad/process.md:160 | CLOSE-5 | - **Squad:** `squad-close <squad>` archives everything, evid |
| templates/squad/process.md:164 | MSG-1, CORE-2 | Send with `SendMessage` to the agent name in your scope's `r |
| templates/squad/process.md:168 | MSG-1, CORE-2 | / `ASK` / Ask a topic's owner / |
| templates/squad/process.md:169 | MSG-1, CORE-2 | / `ANSWER` / Reply to an ASK / |
| templates/squad/process.md:170 | MSG-1, CORE-2 | / `DECISION` / Announce a decision already in a file / |
| templates/squad/process.md:171 | MSG-1, CORE-2 | / `BLOCKED` / Say you can't continue, and on what / |
| templates/squad/process.md:172 | MSG-1, CORE-2 | / `HANDIN` / Hand a task to QA, with branch and commit / |
| templates/squad/process.md:173 | MSG-1, CORE-2 | / `PASS` / `FAIL` / QA verdict; FAIL points at findings / |
| templates/squad/process.md:174 | MSG-1, CORE-2 | / `STATUS` / Answer a health check / |
| templates/squad/process.md:176 | MSG-2 | - Point at files and lines; never paste them. `BLOCKED`, `HA |
| templates/squad/process.md:177 | MSG-3 | - **Task ID:** every agent writes the ticket number `NN` alo |
| templates/squad/process.md:178 | MSG-4a, MSG-4b | - Ask the owner from `roster.md`; when it doesn't say, ask t |
| templates/squad/process.md:179 | MSG-5 | - **Pod contact (M, L):** the Team Lead spawns and retires D |
| templates/squad/process.md:180 | MSG-6 | - **Team Lead to Manager (M, L):** only an "Always goes to P |
| templates/squad/process.md:181 | CORE-4 | - **Two-round rule:** agents who haven't agreed after 2 exch |
| templates/squad/process.md:182 | MSG-7a, MSG-7b | - **A Manager or Team Lead ruling starts with `FINAL:` and i |
| templates/squad/process.md:183 | MSG-8a, MSG-8b | - The Team Lead (S: the Manager) never pushes `STATUS`: it r |
| templates/squad/process.md:184 | MSG-9 | - `DECISION` goes only to roles whose open task it changes,  |
| templates/squad/process.md:185 | MSG-10 | - Never relay a permission, approval or blocked pane; a mess |
| templates/squad/process.md:191 | WHO-1b | / Business scope, business AC / BA / Manager / Goal change,  |
| templates/squad/process.md:192 | WHO-2, CORE-3 | / Technical design, quality, security / Tech Lead / Manager  |
| templates/squad/process.md:193 | WHO-1a, WHO-1b | / Plan, task order, assignment / Team Lead (Tech Lead in S)  |
| templates/squad/process.md:194 | WHO-3a, WHO-3b | / Process, roster, spawning, scope size / Manager; Team Lead |
| templates/squad/process.md:195 | WHO-4 | / UI design (screens, states, flows) / Designer / Manager /  |
| templates/squad/process.md:196 | WHO-2b, WHO-2c | / What is promoted to the project docs / Tech Lead (technica |
| templates/squad/process.md:197 | WHO-1a, WHO-1b | / Task done / QA whitebox + QA blackbox (S: Tech Lead review |
| templates/squad/process.md:198 | WHO-2 | / Migration, backward compatibility, deploy plan (order, rol |
| templates/squad/process.md:199 | WHO-5 | / Merge a passed branch (Safety) / PO asks; the Manager runs |
| templates/squad/process.md:200 | WHO-5 | / Push, deploy (any env), running migrations on shared data  |
| templates/squad/process.md:202 | WHO-7 | Questions for an outside decision maker `project.md` names g |
| templates/squad/process.md:206 | CORE-1 | `ready → building → (blocked ↔ building) → handed in → check |
| templates/squad/process.md:208 | LC-1 | - A Developer's own checks are required but never enough for |
| templates/squad/process.md:209 | LC-2 | - A UI ticket with a `Design:` line stays `ready` until its  |
| templates/squad/process.md:210 | LC-3a, LC-3b | - A returned task stays with its Developer and task file. |
| templates/squad/process.md:211 | LC-4 | - QA never pre-writes test points before the Developer start |
| templates/squad/process.md:212 | LC-5 | - The next ticket starts on the last sha that passed QA whit |
| templates/squad/process.md:213 | LC-6 | - A Developer with queued tickets in its area takes the next |
| templates/squad/process.md:214 | REV-4, REV-5a, REV-5b | - **Verify against the real thing:** code that parses anothe |
| templates/squad/process.md:215 | REV-6 | - A ticket that changes a payload is checked on its field sh |
| templates/squad/process.md:216 | LC-21 | - **QA mode** (`qa:` in `scope.md`): `full` (default) or `li |
| templates/squad/process.md:217 | LC-22a, LC-22b | - In `light`, test-strength gaps go in `qa-w.md` as "follow- |
| templates/squad/process.md:218 | LC-7a, LC-7b | - After 3 returns on one task the Team Lead (S: the Manager) |
| templates/squad/process.md:219 | EVID-1 | - Evidence lives next to the ticket in `evidence.md`: folder |
| templates/squad/process.md:220 | EVID-2a, EVID-2b, EVID-2c | - The Developer writes `## Behaviour` and commits it with it |
| templates/squad/process.md:221 | EVID-3a, EVID-3b | - `qa-b.md` exists in M and L, `tl-review.md` in S. |
| templates/squad/process.md:225 | ITER-1 | Each iteration has `iterations/<n>.md`. |
| templates/squad/process.md:227 | ITER-1 | 1. **Goal check:** the Manager and PO agree the goal in the  |
| templates/squad/process.md:228 | ITER-1 | 2. **Plan:** the roles (by size) talk freely; requirements,  |
| templates/squad/process.md:229 | ITER-1 | 3. **Build and verify:** event-driven; Developers build, QA  |
| templates/squad/process.md:230 | ITER-1 | 4. **Retro:** the Manager writes the friction (loops, blocke |
| templates/squad/process.md:231 | ITER-1 | 5. **Check-in:** the Manager shows the PO what is done, open |
| templates/squad/process.md:233 | dropped: structure | **Token Coach:** |
| templates/squad/process.md:234 | ITER-6, ITER-6a, ITER-6b | - The Manager spawns it at the close of every M or L scope a |
| templates/squad/process.md:235 | ITER-7 | - It reads only `squad-usage` and `usage-events.jsonl` of th |
| templates/squad/process.md:236 | ITER-10 | - The Manager accepts at most the top 3 proposals into this  |
| templates/squad/process.md:237 | ITER-9 | - The Coach proposes only `process.md` changes, never `agent |
| templates/squad/process.md:241 | COST-1 | A Stop hook (`squad-usage --check`) tells you when rule 2 or |
| templates/squad/process.md:243 | COST-2 | 1. **Reuse** a session while it stays on the same task and c |
| templates/squad/process.md:244 | COST-3, COST-5 | 2. **Fresh** when context is over 120k, after a compaction,  |
| templates/squad/process.md:245 | COST-8 |    - **The Manager is not exempt:** after every DONE, every  |
| templates/squad/process.md:246 | COST-9 | 3. **Idle** over 1h with context over 100k: start fresh from |
| templates/squad/process.md:247 | COST-11 | 4. **Step-up** one notch of model or effort only on failure  |
| templates/squad/process.md:248 | COST-12 | 5. **Messages point at files.** The Manager reads summaries, |
| templates/squad/process.md:252 | NOTE-1 | `roles/<agent>.notes.md` is a snapshot of now, not a log; a  |
| templates/squad/process.md:254 | NOTE-1 | - Rewrite it on every save, never append; hard cap about 80  |
| templates/squad/process.md:255 | NOTE-1 | - Fixed sections: `Now`, `Open threads`, `Decisions that bin |
| templates/squad/process.md:256 | NOTE-1 | - History lives in `iterations/<n>.md`, `process-log.md` and |
| templates/squad/process.md:257 | NOTE-2 | - A closed scope's notes go with it to `_done/`; a goal Mana |
| templates/squad/process.md:258 | NOTE-2 | - `squad-respawn` warns when notes pass 100 lines; trim befo |
| templates/squad/process.md:262 | SAFE-1a | - **No push or deploy.** Developers commit to their own `squ |
| templates/squad/process.md:263 | MRG-1 | - **Merge only on the PO's request.** Only the Manager merge |
| templates/squad/process.md:264 | MRG-1 |   - **Which merge:** only what the PO names, into the branch |
| templates/squad/process.md:265 | MRG-2 |   - **Before:** check the target as in Stacked branches and  |
| templates/squad/process.md:266 | MRG-3 |   - **Conflict or failure:** `git merge --abort`, then tell  |
| templates/squad/process.md:267 | MRG-4 |   - **After:** quote `git log --oneline -1` and the result t |
| templates/squad/process.md:268 | SAFE-2 | - **No writes to Jira or Confluence.** Read only. |
| templates/squad/process.md:269 | SUITE-1 | - **Suites: only the Tech Lead runs the full suite.** `proje |
| templates/squad/process.md:270 | SUITE-2a, SUITE-2b |   - Developers and QAs run only the test files their diff to |
| templates/squad/process.md:271 | SUITE-3 |   - The Tech Lead decides when it runs: once for a batch of  |
| templates/squad/process.md:272 | SUITE-4 |   - Run it in the background and wait for its completion not |
| templates/squad/process.md:273 | SUITE-5 |   - On a failing run the Tech Lead names the task whose file |
| templates/squad/process.md:274 | SUITE-6 |   - QA reads the receipt when it covers the sha (same sha, c |
| templates/squad/process.md:275 | SAFE-3 | - **Close what you open.** Before you report, end every brow |
| templates/squad/process.md:276 | SAFE-4 | - **Stay in your lane:** edit only the files your role owns, |
| agents/manager.md:1 | stays in card | --- |
| agents/manager.md:2 | stays in card | name: manager |
| agents/manager.md:3 | stays in card | description: Squad Manager role for a top-level session star |
| agents/manager.md:4 | stays in card | --- |
| agents/manager.md:6 | stays in card | You are the **Manager** of a squad of Claude Code sessions.  |
| agents/manager.md:10 | START-18 | 1. `echo $SQUAD_DIR $SCOPE_DIR $GOAL_DIR $SQUAD_NAME`. **`SC |
| agents/manager.md:11 | START-18 | 2. Read `process.md` and `project.md`, then your folder, in  |
| agents/manager.md:12 | START-18 |    - **Scope Manager:** `$SCOPE_DIR/scope.md` (the PO's brie |
| agents/manager.md:13 | START-18 |    - **Goal Manager:** `$GOAL_DIR/goal.md`, `shared/decision |
| agents/manager.md:14 | SAFE-7 |    - Never read a `_done/` folder. |
| agents/manager.md:15 | START-18 | 3. Check live agents with `herdr agent list` and reconcile ` |
| agents/manager.md:16 | START-18 | 4. Tell the PO in 3–5 lines: where the work stands, what you |
| agents/manager.md:20 | START-19 | - **Scope Manager:** read the brief, size the scope (`proces |
| agents/manager.md:21 | START-19 | - **Goal Manager:** split the brief into scopes. Write them  |
| agents/manager.md:25 | SIZE-13, SIZE-15, SIZE-16 | - **Sizing and changing size.** Move a scope **up** yourself |
| agents/manager.md:26 | SIZE-18 | - **Extra hands.** Add a second BA, Tech Lead or QA when a s |
| agents/manager.md:27 | START-2a, START-2c | - **Developers (S only): one per ready task, up to the cap.* |
| agents/manager.md:28 | FILE-4, FILE-5a, FILE-5b | - **The roster.** Edit `roster.md`, notes and other structur |
| agents/manager.md:29 | MSG-18 | - **Routing (S only).** In S, when an agent asks you who own |
| agents/manager.md:30 | WHO-6 | - **Process.** `process.md` is shared by every scope. Re-rea |
| agents/manager.md:31 | MRG-1 | - **Merging.** Only when the PO asks you to, in your session |
| agents/manager.md:32 | WHO-8, WHO-8a, WHO-8b, MSG-7a, MSG-7b, GOAL-7 | - **Disputes between owners** (see the table in `process.md` |
| agents/manager.md:34 | stays in card | **Writing rule for `process.md`.** Every agent reads it, so: |
| agents/manager.md:35 | stays in card | - **Decide a rule's level first.** A rule a teammate without |
| agents/manager.md:36 | stays in card | - One rule per bullet, stated once in the section that owns  |
| agents/manager.md:37 | stays in card | - Each rule names who acts, when, and the limit or outcome,  |
| agents/manager.md:38 | stays in card | - No history, dates or incidents. A reason only as one short |
| agents/manager.md:39 | stays in card | - At most 60 words per bullet, paragraph or table cell, and  |
| agents/manager.md:40 | stays in card | - Before an edit, run `python3 <plugin>/bin/processlint.py < |
| agents/manager.md:44 | SPAWN-1 | Spawn with the `squad-spawn` command (on your PATH from this |
| agents/manager.md:46 | SPAWN-1 | ```bash |
| agents/manager.md:47 | SPAWN-1 | squad-spawn <role> <agent-name> --scope <scope> [--repo DIR  |
| agents/manager.md:48 | SPAWN-1 | ``` |
| agents/manager.md:50 | SPAWN-2a, SPAWN-2b | - Roles you spawn: `ba`, `team-lead` (M, L), `tech-lead`, `q |
| agents/manager.md:51 | SPAWN-3 | - **Tell every agent its scope's size in the first prompt**, |
| agents/manager.md:52 | START-2c | - **Tell each Team Lead its Developer share of the cap in it |
| agents/manager.md:53 | dropped: duplicate of START-4 | - Names: `<squad>-<role-short>-<scope>[-n]` (`ba`, `tl`, `te |
| agents/manager.md:54 | SPAWN-4 | - **Designer: only when `scope.md` has `design: yes`, and ne |
| agents/manager.md:55 | SPAWN-5a, GOAL-5 | - **Developers (S only) always get `--repo <code repo>`** so |
| agents/manager.md:56 | SPAWN-6 | - **The first prompt is the agent's only briefing.** Include |
| agents/manager.md:57 | SPAWN-7 | - **Pass `--title` when the agent has a specific task:** a D |
| agents/manager.md:58 | SPAWN-8a, SPAWN-8b | - Retire with `squad-retire <agent-name>`: it asks the agent |
| agents/manager.md:62 | GOAL-1 | - **Start a scope:** `squad-start "<text>" --in-goal <goal>  |
| agents/manager.md:63 | GOAL-1 | - **Order and parallelism:** start a scope when everything i |
| agents/manager.md:64 | dropped: duplicate of GOAL-6a | - **Stacking and integration:** follow `process.md` → Inside |
| agents/manager.md:65 | dropped: duplicate of CLOSE-3a | - **When a scope's work is passed**, before its pod is retir |
| agents/manager.md:66 | CLOSE-3b | - **Close the scope:** with the PO's confirmation at an iter |
| agents/manager.md:67 | PROMO-6 | - **Last scope:** add the promotion task (`process.md` → Pro |
| agents/manager.md:68 | CLOSE-4 | - **Close the goal:** run the Token Coach (Retro), tell the  |
| agents/manager.md:72 | CLOSE-1, CLOSE-2 | When both checkers have passed every task and the PO confirm |
| agents/manager.md:76 | SPAWN-11 | Check every time you get a message and at least between iter |
| agents/manager.md:78 | SPAWN-10b | **M and L: watch the Team Lead only.** The Team Lead runs th |
| agents/manager.md:80 | SPAWN-10b | - `herdr agent list`: is the Team Lead alive. Dead or stuck  |
| agents/manager.md:81 | SPAWN-10b | - **Context filling** (the Team Lead confused or repeating i |
| agents/manager.md:82 | SPAWN-10b | - Read `iterations/<n>.summary.md` (the Team Lead's) for the |
| agents/manager.md:84 | SPAWN-10a | **S: you run the pod's health checks.** |
| agents/manager.md:86 | SPAWN-10a | - `herdr agent list`: who is `working`, `idle`, `blocked`, o |
| agents/manager.md:87 | SPAWN-10a | - **Idle with work assigned** → send `ASK <name>: STATUS?`. |
| agents/manager.md:88 | SPAWN-10a | - **Looping** (the same two agents exchanging messages on on |
| agents/manager.md:89 | SPAWN-10a | - **Context filling** (long-running agent getting confused o |
| agents/manager.md:90 | LC-7a, LC-7b | - **3 returns on one task** → read the QA findings and decid |
| agents/manager.md:94 | ITER-2 | - **Escalate only** what `process.md` says always goes to th |
| agents/manager.md:95 | ITER-4 | - **Inbox.** Anything the PO must read or answer goes in the |
| agents/manager.md:96 | ITER-5 | - **A PO answer in chat** to an open item: record it with `s |
| agents/manager.md:97 | ITER-5 | - **The inbox carries only `read` and `answer` items.** Neve |
| agents/manager.md:98 | ITER-11 | - **Batch.** Unless it blocks the squad now, bring it to the |
| agents/manager.md:99 | ITER-11 | - **Check-in** at the end of each iteration, sent as ONE `sq |
| agents/manager.md:100 | ITER-12 | - **Reset after each check-in** (when the scope goes on). Th |
| agents/manager.md:104 | SAFE-1b | - Never push, deploy, or write to Jira/Confluence. Merge onl |
| agents/manager.md:105 | SAFE-6 | - Never do a role's work yourself (writing requirements, cod |
| agents/manager.md:106 | SAFE-7 | - Never read or write another scope's folder, or a `_done/`  |
| agents/manager.md:107 | dropped: duplicate of WHO-7 | - Never contact anyone outside the squad. Questions for outs |
| agents/manager.md:111 | NOTE-2 | Keep `roles/$SQUAD_NAME.notes.md` in your folder current und |
| agents/team-lead.md:1 | stays in card | --- |
| agents/team-lead.md:2 | stays in card | name: team-lead |
| agents/team-lead.md:3 | stays in card | description: Squad Team Lead role for a top-level session st |
| agents/team-lead.md:4 | stays in card | --- |
| agents/team-lead.md:6 | SIZE-17b | You are the **Team Lead** in a squad of Claude Code sessions |
| agents/team-lead.md:8 | stays in card | You own the **plan** and run the **pod**: the right tasks, i |
| agents/team-lead.md:12 | START-6, START-7 | 1. `echo $SQUAD_DIR $SCOPE_DIR $GOAL_DIR $SQUAD_NAME`. Read  |
| agents/team-lead.md:13 | START-9 | 2. Read the Manager's briefing: your scope and peers. |
| agents/team-lead.md:14 | START-15 | 3. Read the scope's tickets or requirements, the decisions f |
| agents/team-lead.md:15 | COST-1 | 4. **Cost rules** (`process.md`): if a Stop-hook message say |
| agents/team-lead.md:19 | stays in card | - **Understand the product end to end** for your scope: what |
| agents/team-lead.md:20 | MSG-13 | - **Raise gaps:** business and backend facts to the BA; tech |
| agents/team-lead.md:21 | LC-15, LC-16 | - **Shape the plan with the Tech Lead.** Each task fits one  |
| agents/team-lead.md:22 | LC-15, LC-16 | - **Write the plan** where `project.md` says (or `$SCOPE_DIR |
| agents/team-lead.md:23 | SPAWN-5b, SPAWN-8b | - **Spawn and retire Developers, only Developers.** `squad-s |
| agents/team-lead.md:24 | START-2b | - **Developer cap:** spawn within your share from the Manage |
| agents/team-lead.md:25 | LC-17 | - **Track delivery:** move task state as HANDIN / PASS / FAI |
| agents/team-lead.md:26 | MSG-8b, LC-7b | - **Health checks:** `herdr agent list` and `herdr agent rea |
| agents/team-lead.md:27 | MSG-19 | - **Routing:** answer "who owns X" from `roster.md`. |
| agents/team-lead.md:28 | FILE-4, FILE-5c | - **Roster:** you edit only the rows of the Developers you s |
| agents/team-lead.md:29 | WHO-8c | - **Disputes:** settle plan, order and assignment ones. Writ |
| agents/team-lead.md:33 | SPAWN-9 | - Spawn or retire any role but `dev`: no second Team Lead, n |
| agents/team-lead.md:34 | dropped: duplicate of MSG-10 | - Relay a blocked pane or a permission prompt; each agent's  |
| agents/team-lead.md:35 | MSG-6 | - Message the Manager for a routine matter. |
| agents/team-lead.md:39 | MSG-6 | Each as one line pointing at a file: |
| agents/team-lead.md:41 | MSG-6 | - an "Always goes to PO" item; |
| agents/team-lead.md:42 | MSG-6 | - a size-change signal; |
| agents/team-lead.md:43 | MSG-6 | - a dispute outside plan and assignment that two rounds did  |
| agents/team-lead.md:44 | MSG-6 | - 3 returns on one task (one budget line); |
| agents/team-lead.md:45 | MSG-6, ITER-3 | - `iterations/<n>.summary.md` at iteration end: tasks done w |
| agents/team-lead.md:49 | dropped: duplicate of WHO-1b | - **Own:** plan, task order, assignment, Developer spawn and |
| agents/team-lead.md:50 | dropped: duplicate of WHO-1b | - **Don't own:** business AC (BA), technical design (Tech Le |
| agents/team-lead.md:54 | LC-17, NOTE-3 | You carry every HANDIN / PASS / FAIL copy and will cross 120 |
| agents/team-lead.md:58 | dropped: duplicate of NOTE-1 | Keep `$SCOPE_DIR/roles/$SQUAD_NAME.notes.md` current (`proce |
| agents/tech-lead.md:1 | stays in card | --- |
| agents/tech-lead.md:2 | stays in card | name: tech-lead |
| agents/tech-lead.md:3 | stays in card | description: Squad Tech Lead role for a top-level session st |
| agents/tech-lead.md:4 | stays in card | --- |
| agents/tech-lead.md:6 | stays in card | You are the **Tech Lead** in a squad of Claude Code sessions |
| agents/tech-lead.md:10 | START-6, START-7 | 1. `echo $SQUAD_DIR $SCOPE_DIR $GOAL_DIR $SQUAD_NAME`. Read  |
| agents/tech-lead.md:11 | START-16 | 2. **Read the existing design decisions** (ADRs, decisions f |
| agents/tech-lead.md:12 | START-9 | 3. Read the Manager's briefing: your scope and peers. |
| agents/tech-lead.md:13 | COST-1 | 4. **Cost rules** (`process.md`): if a Stop-hook message say |
| agents/tech-lead.md:17 | LC-10 | - **Design** each task before it is built: which files, whic |
| agents/tech-lead.md:18 | SIZE-6a, SIZE-16, LC-14 | - **In S you also own the plan** (the Team Lead's duty in M  |
| agents/tech-lead.md:19 | REV-1, EVID-2c, SIZE-14, SIZE-11a | - **In S you are also the checker.** On `HANDIN`: read the d |
| agents/tech-lead.md:20 | SIZE-16 | - **When the scope moves up a size,** write a `## Handover`  |
| agents/tech-lead.md:21 | GOAL-3a | - **Contracts with other scopes of your goal:** agree each s |
| agents/tech-lead.md:22 | PROMO-2 | - **Keep `promote.md`** in your scope folder while the work  |
| agents/tech-lead.md:23 | CLOSE-3a | - **When your scope is passed, inside a goal:** write `$GOAL |
| agents/tech-lead.md:24 | GOAL-6a | - **Plan the integration task** at the end of the scope (`pr |
| agents/tech-lead.md:25 | SUITE-3, SUITE-4, SUITE-5 | - **Run the full suite.** You decide when it runs (once for  |
| agents/tech-lead.md:26 | LC-14 | - **Help the Team Lead plan** (M, L): split work so parallel |
| agents/tech-lead.md:27 | REV-4, REV-5a, REV-5b, REV-6 | - **Design against the real thing.** For code that parses an |
| agents/tech-lead.md:28 | REV-7 | - **Agree technical AC with QA whitebox:** tests required, l |
| agents/tech-lead.md:29 | LC-11, REV-1 | - **When `scope.md` has `design: yes`:** plan the UI tasks t |
| agents/tech-lead.md:30 | MSG-14 | - **Answer Developers' technical gaps** fast. A decision tha |
| agents/tech-lead.md:31 | LC-12 | - **Own migrations and backward compatibility.** For any cha |
| agents/tech-lead.md:32 | LC-13 | - **Write the deploy plan, never run it.** Order, migration  |
| agents/tech-lead.md:33 | MSG-15 | - **Raise technical facts to the BA** when they change what  |
| agents/tech-lead.md:37 | dropped: duplicate of WHO-2 | - **Own:** technical design, quality, security. |
| agents/tech-lead.md:38 | dropped: duplicate of WHO-2 | - **Don't own:** business AC (BA), plan (Team Lead in M, L), |
| agents/tech-lead.md:39 | dropped: duplicate of WHO-2 | - **Escalate via the Manager:** irreversible choices (data m |
| agents/tech-lead.md:43 | dropped: duplicate of NOTE-1 | Keep `$SCOPE_DIR/roles/$SQUAD_NAME.notes.md` current (`proce |
| agents/ba.md:1 | stays in card | --- |
| agents/ba.md:2 | stays in card | name: ba |
| agents/ba.md:3 | stays in card | description: Squad BA role for a top-level session started b |
| agents/ba.md:4 | stays in card | --- |
| agents/ba.md:6 | stays in card | You are a **BA** in a squad of Claude Code sessions. You own |
| agents/ba.md:10 | START-6, START-7 | 1. `echo $SQUAD_DIR $SCOPE_DIR $GOAL_DIR $SQUAD_NAME`. Read  |
| agents/ba.md:11 | START-9 | 2. Read the first message from the Manager: your scope and y |
| agents/ba.md:12 | START-11 | 3. Read the scope's requirements where `project.md` says the |
| agents/ba.md:13 | COST-1 | 4. **Cost rules** (`process.md`): if a Stop-hook message say |
| agents/ba.md:17 | stays in card | - **Understand the goal** behind each requirement. Ask "what |
| agents/ba.md:18 | stays in card | - **Find requirement issues:** gaps, contradictions, missing |
| agents/ba.md:19 | REV-8 | - **Agree business AC with QA blackbox** (Given/When/Then, o |
| agents/ba.md:20 | MSG-12 | - **Take gaps** from the Team Lead and Developers. Settle wh |
| agents/ba.md:21 | SIZE-17a | - **Joining a scope that moved up from S:** start from the p |
| agents/ba.md:22 | PROMO-3a | - **Hand the Tech Lead the lasting business rules and glossa |
| agents/ba.md:23 | SIZE-11b | - **Questions only an outside decision maker can answer** (s |
| agents/ba.md:27 | dropped: duplicate of WHO-1b | - **Own:** business scope and business AC for your scope. Yo |
| agents/ba.md:28 | dropped: duplicate of CORE-3 | - **Don't own:** technical design (Tech Lead), plan and orde |
| agents/ba.md:29 | dropped: duplicate of WHO-1b | - **Always escalate via the Manager:** goal change, scope cu |
| agents/ba.md:33 | dropped: duplicate of NOTE-1 | Keep `$SCOPE_DIR/roles/$SQUAD_NAME.notes.md` current (`proce |
| agents/qa-whitebox.md:1 | stays in card | --- |
| agents/qa-whitebox.md:2 | stays in card | name: qa-whitebox |
| agents/qa-whitebox.md:3 | stays in card | description: Squad QA whitebox role for a top-level session  |
| agents/qa-whitebox.md:4 | stays in card | --- |
| agents/qa-whitebox.md:6 | stays in card | You are **QA whitebox** in a squad of Claude Code sessions.  |
| agents/qa-whitebox.md:10 | START-6, START-7 | 1. `echo $SQUAD_DIR $SCOPE_DIR $GOAL_DIR $SQUAD_NAME`. Run ` |
| agents/qa-whitebox.md:11 | START-9, START-14 | 2. Read the Manager's briefing, the repo conventions and the |
| agents/qa-whitebox.md:12 | COST-1 | 3. **Cost rules** (`process.md`): if a Stop-hook message say |
| agents/qa-whitebox.md:16 | REV-7 | - **Agree technical AC with the Tech Lead** before work star |
| agents/qa-whitebox.md:17 | REV-2 | - **On `HANDIN`:** check out the Developer's branch (read-on |
| agents/qa-whitebox.md:18 | REV-2 |   1. Review the diff against the technical AC and the repo's |
| agents/qa-whitebox.md:19 | REV-2 |   2. Run the tests and linters `project.md` lists, on the ch |
| agents/qa-whitebox.md:20 | REV-2 |   3. Check that each new behaviour has a test and each new e |
| agents/qa-whitebox.md:21 | REV-2 |   4. When the task changes a schema, data, API or contract:  |
| agents/qa-whitebox.md:22 | REV-4, REV-5b, REV-6 | - **Check the real thing, and its shape.** Code that parses  |
| agents/qa-whitebox.md:23 | GOAL-3b | - **Contracts between scopes of a goal:** before either scop |
| agents/qa-whitebox.md:24 | PROMO-8 | - **Promotion task:** check the project-doc edits like any o |
| agents/qa-whitebox.md:25 | SIZE-17c | - **Joining a scope that moved up:** work already built goes |
| agents/qa-whitebox.md:26 | REV-10 | - **Write findings** to `$SCOPE_DIR/evidence/<task>/qa-w.md` |
| agents/qa-whitebox.md:27 | REV-12 | - **Send `PASS` or `FAIL`** to the Developer, copy the Team  |
| agents/qa-whitebox.md:31 | stays in card | You are the check the Developer can't be for itself. **Don't |
| agents/qa-whitebox.md:35 | SAFE-9 | Never edit the Developer's code. Never pass on the Developer |
| agents/qa-blackbox.md:1 | stays in card | --- |
| agents/qa-blackbox.md:2 | stays in card | name: qa-blackbox |
| agents/qa-blackbox.md:3 | stays in card | description: Squad QA blackbox role for a top-level session  |
| agents/qa-blackbox.md:4 | stays in card | --- |
| agents/qa-blackbox.md:6 | stays in card | You are **QA blackbox** in a squad of Claude Code sessions.  |
| agents/qa-blackbox.md:10 | START-6, START-8 | 1. `echo $SQUAD_DIR $SCOPE_DIR $GOAL_DIR $SQUAD_NAME`. Run ` |
| agents/qa-blackbox.md:11 | START-13 | 2. Read the Manager's briefing and the scope's requirements, |
| agents/qa-blackbox.md:12 | COST-1 | 3. **Cost rules** (`process.md`): if a Stop-hook message say |
| agents/qa-blackbox.md:16 | SAFE-10 | **Don't read source code, diffs or the Developer's explanati |
| agents/qa-blackbox.md:20 | REV-8 | - **Agree business AC with the BA** before work starts: Give |
| agents/qa-blackbox.md:21 | REV-9 | - **On `HANDIN`:** test the running app the way `project.md` |
| agents/qa-blackbox.md:22 | SIZE-17d | - **Joining a scope that moved up from S:** test everything  |
| agents/qa-blackbox.md:23 | REV-11 | - **Write evidence** to `$SCOPE_DIR/evidence/<task>/qa-b.md` |
| agents/qa-blackbox.md:24 | REV-12 | - **Send `PASS` or `FAIL`** to the Developer, copy the Team  |
| agents/qa-blackbox.md:28 | stays in card | **Don't talk yourself into passing.** If what you saw differ |
| agents/designer.md:1 | stays in card | --- |
| agents/designer.md:2 | stays in card | name: designer |
| agents/designer.md:3 | stays in card | description: Squad UI/UX Designer role for a top-level sessi |
| agents/designer.md:4 | stays in card | --- |
| agents/designer.md:6 | stays in card | You are the **UI/UX Designer** in a squad of Claude Code ses |
| agents/designer.md:10 | START-6, START-7 | 1. `echo $SQUAD_DIR $SCOPE_DIR $GOAL_DIR $SQUAD_NAME`. Run ` |
| agents/designer.md:11 | START-9 | 2. Read the Manager's briefing: the UI tasks and their AC. |
| agents/designer.md:12 | START-12 | 3. **Read the existing UI conventions** that `project.md` li |
| agents/designer.md:13 | COST-1 | 4. **Cost rules** (`process.md`): if a Stop-hook message say |
| agents/designer.md:17 | LC-23 | - **Write `$SCOPE_DIR/ui-design/<task>.md` for each UI task* |
| agents/designer.md:18 | LC-23 | - **Optional `ui-design/<task>.html`:** one self-contained f |
| agents/designer.md:19 | MSG-17 | - **When a design is final,** send `DECISION <task>: design  |
| agents/designer.md:20 | MSG-16a, MSG-16b | - **Doubts:** business → `ASK` the BA (M, L) or the Tech Lea |
| agents/designer.md:24 | dropped: duplicate of FILE-9 | - **Own:** the design files in `$SCOPE_DIR/ui-design/`. |
| agents/designer.md:25 | SAFE-8 | - **Never:** edit project code, `scope.md`, `process.md`, ti |
| agents/designer.md:29 | dropped: duplicate of NOTE-1 | Keep `$SCOPE_DIR/roles/$SQUAD_NAME.notes.md` current (`proce |
| agents/dev.md:1 | stays in card | --- |
| agents/dev.md:2 | stays in card | name: dev |
| agents/dev.md:3 | stays in card | description: Squad Developer role for a top-level session st |
| agents/dev.md:4 | stays in card | --- |
| agents/dev.md:6 | stays in card | You are a **Developer** in a squad of Claude Code sessions.  |
| agents/dev.md:10 | START-6, START-7 | 1. `echo $SQUAD_DIR $SCOPE_DIR $GOAL_DIR $SQUAD_NAME $SQUAD_ |
| agents/dev.md:11 | START-10 | 2. Read your briefing: the task, its AC, the Tech Lead's des |
| agents/dev.md:12 | START-10 | 3. `git status` and `git branch --show-current`: you are on  |
| agents/dev.md:13 | START-10 | 4. Read the repo's CLAUDE.md and the conventions `project.md |
| agents/dev.md:14 | COST-1 | 5. **Cost rules** (`process.md`): if a Stop-hook message say |
| agents/dev.md:18 | LC-18 | - **Label your tab:** when you take a ticket run `squad-labe |
| agents/dev.md:19 | LC-18 | - **Implement the task as designed.** Reuse what exists; fol |
| agents/dev.md:20 | LC-19, EVID-5, SIZE-10a | - **Design.** If the ticket has a `Design:` line, read `$SCO |
| agents/dev.md:21 | MSG-11a, MSG-11b | - **Gaps:** don't guess. Technical → `ASK` the Tech Lead. Bu |
| agents/dev.md:22 | LC-18 | - **Verify before handing in:** the tests, linters and check |
| agents/dev.md:23 | SUITE-2a | - **Suites.** Run only the test files you touched. Never run |
| agents/dev.md:24 | EVID-4, SIZE-8a, REV-13a | - **In an S-size scope there is no QA blackbox:** write `##  |
| agents/dev.md:25 | SAFE-1a | - **Commit** to your branch with clear messages. **Never pus |
| agents/dev.md:26 | REV-13a, REV-13b | - **Hand in:** `HANDIN <task>: branch squad/<squad>/$SQUAD_S |
| agents/dev.md:27 | REV-15 | - **Copy a report.** A report or doc deliverable is also cop |
| agents/dev.md:28 | REV-14a, REV-14b | - **After a `PASS`.** A later commit goes to both QAs as `HA |
| agents/dev.md:29 | EVID-2b | - **Assemble the evidence.** Once every checker passed, run  |
| agents/dev.md:30 | GOAL-6b, PROMO-5 | - **Special tasks.** An **integration task** merges the scop |
| agents/dev.md:31 | LC-3a | - **On `FAIL`:** fix every finding, re-verify, hand in again |
| agents/dev.md:35 | LC-20a, LC-20b | Your task is done when the size's checkers sent `PASS` (M, L |
| agents/token-coach.md:1 | stays in card | --- |
| agents/token-coach.md:2 | stays in card | name: token-coach |
| agents/token-coach.md:3 | stays in card | description: Squad Token Coach role for a top-level session  |
| agents/token-coach.md:4 | stays in card | --- |
| agents/token-coach.md:6 | stays in card | You are the **Token Coach** of a squad of Claude Code sessio |
| agents/token-coach.md:10 | START-17 | 1. `echo $SQUAD_DIR $SCOPE_DIR $GOAL_DIR $SQUAD_NAME`. Your  |
| agents/token-coach.md:11 | START-17 | 2. Run `squad-usage` for the per-agent table. Read your fold |
| agents/token-coach.md:15 | ITER-8 | - **Find waste in the table:** cache expiries, peak context  |
| agents/token-coach.md:16 | ITER-7, ITER-8 | - **Write the proposals file:** `$SCOPE_DIR/iterations/<n>.c |
| agents/token-coach.md:17 | ITER-8 | - **Tune the rule values** (120k / 1h / 100k) if the evidenc |
| agents/token-coach.md:18 | ITER-7 | - **Tell the Manager** with one short message that points at |
| agents/token-coach.md:22 | ITER-9 | - **Never read raw transcripts.** The table and the events a |
| agents/token-coach.md:23 | ITER-9 | - **Never propose without an evidence row.** No evidence, no |
| agents/token-coach.md:24 | ITER-9 | - **Never edit any file except your proposals file.** Not `p |
| log row 33 | COST-8 |  |
| log row 34 | COST-4b |  |
| log row 35 | LC-3b |  |
| log row 36 | START-5 |  |
| log row 37 | COST-4a |  |
| log row 38 | REV-3 |  |
| log row 39 | LC-8 |  |
| log row 40 | COST-5, COST-6a, COST-6b |  |
| log row 41 | COST-8 |  |
| log row 42 | LC-9 |  |
| log row 43 | SAFE-5 |  |
| log row 44 | COST-7 |  |
| log row 45 | COST-10a, COST-10b |  |
| log row 46 | MSG-3 |  |
| log row 47 | COST-6a, COST-6b |  |
| log row 48 | REV-16, REV-17 |  |
| log row 49 | REV-18a, REV-18b |  |

## Rules with no source row of their own

- `SIZE-12`: the heading of v6 line 109 ("duties move, never dropped"); headings are not rows.
- `START-2d`: fix (b), the Tech Lead tells the Manager which tasks are ready in parallel (S).
- Fix (a) is `REV-13a` / `REV-13b` / `REV-14a` / `REV-14b`; fix (c) is `MSG-16a` / `MSG-16b` (BA decision BD6); fix (d) drops "The label shape is in process.md" (`manager.md:57`, mapped to `SPAWN-7`, which does not repeat it); fix (e) puts the Token Coach rules in `ITER-6` to `ITER-10` and nothing cites a Retro section.
