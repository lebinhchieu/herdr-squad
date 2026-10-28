# Drop scope size: the Manager suggests a team per scope

Status: final (BA, 2026-10-27, after PO answer E4 and the Architect's amended `architecture.md`). Business AC pending agreement with QA blackbox (REV-8). Commit target: `.scratch/drop-scope-size/spec.md` (first Developer task).

## In one paragraph
A scope no longer has a size (S/M/L). The Manager reads the scope's signals and suggests a **team**: which of BA, Tech Lead, Team Lead, QA whitebox, QA blackbox, Designer, Architect (and the Token Coach) join the always-present Manager and Developers. Every role is suggested the same way; the PO's only job is to confirm or change the team. Duties never vanish: each duty has an ordered fallback of owners, so any team has exactly one owner per duty. Open scopes finish on the plugin version they are pinned to; every other existing squad **must migrate** with the converter, and the new plugin does not read `size:` or the old keys at all (no shim, no dual support; PO, E4).

## Answers to open questions a–g
| Q | Answer | Who settles |
|---|---|---|
| a. What replaces `size` in `when:` | **Requirement:** a role's rules depend only on the team (plus `goal`, `qa`), never on a size label. A team equal to today's S, M or L gets exactly today's duty owners (rule 3, AC 9). *How* rules are keyed (role-presence facts, derived duty facts such as the Tech Lead's `plan-owner = ...`, presets) is the Architect's call; the BA has no preference except: a missing fact is an error, never "matches" (AC 11). Key names are fixed by the PO (rule 1). | Architect |
| b. Duty owner when its default role is absent | Ordered fallback per duty, ending at Manager or Developer (table in rule 3). **All team shapes are valid**; the Manager's suggestion rules (rule 2) keep odd shapes rare. Open for PO only as P2. | BA (done) |
| c. What Done means | Done = every checker on the team passed the task; a duty with no checker falls back to the Developer's evidence, confirmed by the next owner (rule 4). | BA (done) |
| d. PO confirms the team | Yes. Recorded as decided: the PO's brief and the Manager's briefing say so. | decided |
| e. Role change mid-scope | Generalise moving up/down (rule 5). Adding is the Manager's call and reported at check-in, except Designer and Architect which wait for the PO (P1). Removing only at an iteration boundary with the PO's OK. | BA; P1 → PO |
| f. Migration | Open pinned scopes untouched. Every other existing squad migrates with the converter; the new plugin has **no shim** and rejects `size:` and the old keys with a pointer to the converter (PO, E4). `team:` replaces `size:`, `design:`, `architecture:`, `qa-b:`. Size→team mapping lives in the converter, `squad-migrate` and overlay translation hints; closed scopes show their recorded size in the report (rule 6). | BA (done); PO decided |
| g. Developer rules 5 KiB cap | Business line only: Developer rules stay within the cap for every allowed team. Mechanism (all-set sweep, trimming, pinned exceptions) is the Tech Lead's / Architect's. | Tech Lead |

## Rules

### 1. The team
- Always present: Manager, Developers (cap unchanged: 3).
- Optional, each independently: BA, Tech Lead, Team Lead, QA whitebox, QA blackbox, Designer, Architect. Token Coach is not on `team:`; the Manager spawns it at the close by the rule 2 condition.
- **Key names (PO, E4).** The `team:` tokens are `ba`, `tech-lead`, `team-lead`, `qa-white`, `qa-black`, `designer`, `architect`. The `when:` presence keys are `ba`, `tech-lead`, `team-lead`, `qa-white`, `qa-black`, `design`, `architecture` (`design`/`architecture` keep their old names, now derived from the team; `designer`/`architect` stay the `team:` tokens). `qa-white` and `qa-black` are new key names; `qa-b` (the old `when:` key and `scope.md` line) is gone and nothing aliases it. Role and agent names do **not** change: `squad-spawn`, `roster.md`, agent files and messages still say `qa-whitebox` and `qa-blackbox`. The term stays **QA** (PO unsure; not renamed to QC).
- `scope.md` records the confirmed team on one `team:` line using those keys. It replaces `size:`, `design:`, `architecture:`, `qa-b:`. `qa: full|light`, `goal:`, `touches:`, `model <role>:` lines stay.
- `squad-spawn <role>` refuses a role not on the team and says so; the Manager and Team Lead spawn only team roles.
- A role can be *retired* (session ended, e.g. Designer once its design is final) and still be *on the team*. Removing a role from the team is rule 5.

### 2. Signals → roles (the Manager's suggestion)
The Manager proposes **every** role (picks and non-picks) in one table in one inbox item: role | pick | signal | model/effort, plus advisor on/off (today's team-models step, START-3b). It states the signal for each row. Signals disagree → task count loses. Unsure → add the role (replaces "size up"). Nothing is spawned before the PO confirms. A goal Manager does this for each scope.

| Role | Brought in by (any one) | If signals are silent |
|---|---|---|
| BA | open business question; requirement unclear or contradicting a decision/spec; an outside decision maker's answer needed; no testable AC in the ticket; output other teams see | out (the ticket is the AC) |
| Tech Lead | any risk flag below; cross-repo; per-task design choices several Developers depend on | out (Developer's design notes) |
| Team Lead | 4 or more tasks; order or dependencies matter; 2 or more Developers in parallel | out (Manager plans) |
| QA whitebox | any task changes code or tests | in. Out only when all hold: ≤2 tasks, one repo, no user-visible change, no risk flag, existing tests cover it |
| QA blackbox | a task changes what a person observes (screen, CLI or hook output, exit code, generated file or report, message to the PO); a Designer is on the team | out (state "no observable change") |
| Designer | UI screens, states or flows are built or changed | out |
| Architect | an irreversible choice is likely (data model, new dependency, vendor); boundaries or contracts across 2 or more components must be set before the plan; a cross-cutting redesign | out |
| Token Coach | team has QA whitebox or QA blackbox (today's M and L); otherwise only when the PO asks (today's S) | PO's ask |

Risk flags keep forcing roles (they used to force L). The suggestion must include them; the PO may confirm without, and the Manager logs that override in the iteration file:
- DB migration or data change, breaking API or contract change, security or permissions → Tech Lead + QA whitebox.
- Anything another team will see → Tech Lead + QA whitebox + BA.
- Business doubt, or a question for an outside decision maker (written by the BA, SIZE-11b) → BA.

**Goal instead of scope.** Work that cannot finish in one iteration under the Developer cap, or that needs two separate teams (separate repos or contracts), is a goal; each scope of a goal gets its own team. (Replaces "bigger than one L scope"; threshold is guidance, the PO's cut stands.)

**The brief.** A PO request for a role in the brief (`design: yes`, "add an Architect") is taken as a confirmed pick but still appears in the table. A brief that still says `size: S|M|L` gets no special treatment: the Manager ignores the label and proposes from the scope's signals (no size hint, no mapping).

### 3. Duty owners (first present role wins; replaces SIZE-22 / SIZE-22a)
| Duty | Owner chain |
|---|---|
| Plan, Developer spawning | Team Lead → Manager |
| Pod's contact for routine questions; 3 returns on a task | Team Lead → Manager |
| Architecture (`architecture.md`) | Architect → none (no `architecture.md`) |
| Design notes | Tech Lead → Developer (inside `architecture.md` when an Architect is on the team) |
| Technical AC | Tech Lead with QA whitebox → QA whitebox with the Developer → Developer |
| Business AC | BA with QA blackbox → BA (QA whitebox checks `## Behaviour`) when no QA blackbox → ticket as written |
| Code check | QA whitebox → Developer's `## Review` (one Sonnet review subagent), confirmed by Tech Lead, else Manager |
| Behaviour check | QA blackbox → Developer's `evidence.md` `## Behaviour`, checked by QA whitebox, else confirmed by Manager |
| Built-UI check (with a Designer) | QA blackbox → Developer's screenshots in `evidence.md`, confirmed by Manager |
| Hand in to / done told to | the QAs on the team, none → Manager / Team Lead → Manager |
| Full suite | Tech Lead → QA whitebox → Developer |
| `promote.md`, technical part | Tech Lead → QA whitebox → Developer |
| `promote.md`, business part | BA → the technical owner above |
| Migration, contract change, risk flag | Tech Lead → Manager adds Tech Lead (rule 5) |
| Business doubt, outside question | BA → Manager adds BA (rule 5) |
| Irreversible design choice | Architect proposes → Tech Lead proposes → Manager proposes (after an advisor call); **the PO decides in every case** |
| Disputes | Manager; plan, order and assignment ones: Team Lead when present |

**Equivalence (must hold):** S = Manager + Developers; M = + QA whitebox, QA blackbox; L = + BA, Team Lead, Tech Lead, QA whitebox, QA blackbox; today's `qa-b: no` = no QA blackbox; `design`/`architecture: yes` add Designer/Architect. For each, the chains above give exactly the owners in today's SIZE-22 / SIZE-22a column.

### 4. Done
A task is done when its **code check** and its **behaviour check** (and **built-UI check** with a Designer) have passed, each owned per rule 3.
- Both QAs on the team: both PASS (today's M and L).
- QA whitebox only: QA whitebox PASS, checking the Developer's `## Behaviour` against the business AC (today's SIZE-20).
- QA blackbox only: QA blackbox PASS + the Developer's `## Review` confirmed.
- Neither QA: the Developer's checks, `evidence.md` and `## Review` exist and the Manager (or Tech Lead for the review) confirms (today's S).
- Every rule that says "both QAs" or "PASS + PASS" reads "every checker on the team". `Done means` in the brief defaults changes from "the size's checks" to "every checker on the team passed".

### 5. Changing the team mid-scope (replaces SIZE-13 to 17)
- **Late signal → role to add:** business doubt → BA; risk flag or migration → Tech Lead (+ QA whitebox if absent); user-visible change → QA blackbox; 4+ tasks or order matters → Team Lead; UI work appears → Designer; irreversible choice appears → Architect.
- **Add:** Manager edits `team:`, writes `## Handover` (decided, built, open) in the plan, spawns the joiner with a briefing that points at it, respawns the roles whose composed rules change, logs it in the iteration file, tells the PO at the check-in. **Designer and Architect: the PO confirms first** (P1).
- **Joiner starts from the Handover.** BA checks the AC so far (they were the ticket as written). Team Lead takes the plan from the Manager. QA whitebox / QA blackbox / Tech Lead check everything already built before it counts as done. Designer/Architect: tasks not started wait for `final`; built tasks are checked against the design/architecture, a difference is a finding.
- **Remove:** only at an iteration boundary with the PO's OK. Its duties move along the chain; its open threads go to the fallback owner, named in the Handover. Tasks already PASSed stay PASSed; unfinished tasks use the new Done.
- The Manager reports a team change as a "team-change signal" (replaces "size-change signal" in Manager traffic).

### 6. Migration
- **No shim, no dual support (PO, E4).** The new plugin does not derive a team from `size:`. A squad whose `scope.md` still has `size:`, `design:`, `architecture:` or `qa-b:` lines, or whose overlay still uses `when: size` or `qa-b`, is **rejected** with a message that names the file or rule and points at the converter. Nothing "kind of works".
- **Who must migrate:** every existing squad that composes with the new plugin: unpinned legacy squads (composed from the running plugin on respawn) and any scope or overlay the PO moves to it. Migration is the PO's yes on the converter's dry run.
- **Open pinned scopes** (pinned below 0.6.0) keep their pin and their `size:`; their roles keep composing with the pin's own engine to the end of the scope (ADR 0016), so no byte of their composed rules changes and nothing forces them to migrate. The new plugin's other tools (report, hooks) must not break on them (Architect's call how; BA's only line: no shim for compose).
- **Size → team** mapping (same duties as today, rule 3), used only by the converter, `squad-migrate` (folder layout): S = {}; M = {qa-white, qa-black}; L = {ba, team-lead, tech-lead, qa-white, qa-black}; `qa-b: no` removes qa-black; `design`/`architecture: yes` add `designer`/`architect`. Shown to the PO before anything is written.
- **Overlays** (`process.local.md`): `squad-process upgrade` lists operations whose target ID was removed or retargeted, and local rules with `when: size ...` or `qa-b ...`, each with a suggested translation (`qa-b = no` → `qa-black = no`). Nothing is written without the PO's yes; compose fails loudly on a leftover old key, naming the rule and pointing at the converter.
- **Closed scopes** and the report: old `size:` shown as recorded (display only, no compose); new scopes show their team; the rollup handles both and its size filter is replaced or dropped. No crash on a mix.
- **Shipping:** breaking contract → version bump with changelog block, `_removed.md` tombstone (`why`, `replaced_by`) for every removed or merged ID, rule snapshot, README, CONTEXT.md glossary, superseding ADR (below).

### 7. Cost guardrail
Composed Developer rules stay ≤ 5 KiB for every allowed team (with `goal`, `design` variants as today). No new pinned exception; the existing pinned S+architecture overshoot should disappear or stay no worse.

## Business AC (Given/When/Then, observable in a scratch squad)
**Agreed by QA blackbox 2026-10-27 (REV-8), on condition of edits E1-E6, applied here (AC 1-31).** QA verifies mechanics in a scratch squad; AC 1-6, 16 and 31 (Manager inbox flow) on a live Manager run with three briefs (open question + risk flag; new screen; one-line fix); AC 10, 24, 25 and the exact owners of 9 and 28 from the suite receipt (QA does not run the suite). "Scratch squad" = temp dir with stub `claude` and herdr (`tests/test_squad_start.py`). Numbers are stable (tickets cite them): 24-25 and 26-28 sit out of order on purpose; 29-31 are new.

**Reference used by the AC**
- Commands: `squad-process compose <role> --home D` (composed rules, header, and for Manager/Team Lead/Tech Lead a `duties:` line with the owner of each duty for the team); `squad-process who <ID>`; `squad-process team --home D`; `squad-process lint`; converter = `squad-process adopt --squad-dir D` (dry run by default, `--yes` writes); `squad-process upgrade` (overlay report on stdout); `squad-report rollup <data.json>...`; `squad-team add|remove <role>` (`--po-ok` for designer/architect adds, `--at-boundary` for removes; prints the roles to respawn).
- Duties (rule 3), 13 of them: plan-owner, design-notes, tech-ac, business-ac, code-check, behaviour-check, ui-check, handin-target, suite-owner, promote-owner, risk-owner, doubt-owner, choice-owner.
- Today's sizes as teams (the same mapping the converter uses):

| Today | Team (`team:` tokens) |
|---|---|
| S | `none` |
| M | `qa-white, qa-black` |
| L | `ba, team-lead, tech-lead, qa-white, qa-black` |
| `qa-b: no` | the same team without `qa-black` (`qa-b: yes` is the default and changes nothing) |
| `design: yes` | adds `designer` |
| `architecture: yes` | adds `architect` |

- "Today's owners" = SIZE-22 / SIZE-22a of the 0.5.2 plugin (`git show 2949573:templates/squad/process/sizes.md`), copied here. QA whitebox asserts exact equality; QA blackbox checks that each of the six shapes prints a `duties:` line with a plausible owner per duty.

| Duty | S | M | L |
|---|---|---|---|
| Plan, Developer spawning | Manager | Manager | Team Lead |
| Design notes | Developer | Developer | Tech Lead |
| Technical AC | Developer | QA whitebox with the Developer | Tech Lead with QA whitebox |
| Business AC | ticket as written | ticket as written | BA with QA blackbox |
| Code check | Developer + Sonnet review subagent | QA whitebox | QA whitebox |
| Behaviour check | Developer's `evidence.md` | QA blackbox | QA blackbox |
| Hand in to / done told to | Manager / Manager | QAs / Manager | QAs / Team Lead |
| Full suite | Developer | QA whitebox | Tech Lead |
| `promote.md` | Developer | QA whitebox | Tech Lead, BA |
| Migration, contract change, risk flag, business doubt | (was: Manager moves to L) | (was: Manager moves to L) | Tech Lead, BA |
| Irreversible design choice | Manager | Manager | Tech Lead |
| 3 returns | Manager | Manager | Team Lead |
| With an Architect (SIZE-22a), all sizes: Architecture | Architect | Architect | Architect |
| With an Architect: Design notes | Developer, inside it | Developer, inside it | Tech Lead, inside it |
| With an Architect: Irreversible choice | Architect proposes, PO decides | same | same |

  Differences by design, not defects: the "moves to L" row now follows the chain (Manager adds the role, rule 5); the irreversible-choice row for S/M changes from "Manager" to "Manager proposes after an advisor call, PO decides" (rule 3).
- **How `team:` is written.** The Manager edits the `team:` line of `scope.md` after the PO's inbox reply; no command writes the first `team:` (a blank `team:` is *undecided*; `team: none` is the confirmed minimal team, Manager + Developers). Later changes use `squad-team add|remove`.

**Suggestion and confirmation** (Manager proposal; observed in the inbox item and `scope.md`)
1. Given a brief with an open business question, a breaking-contract risk flag and no UI, when the Manager proposes the team, then one inbox item shows a table with a row for every role (BA, Tech Lead, Team Lead, QA whitebox, QA blackbox, Designer, Architect), each with pick and signal, plus models and advisor; the word "size" is absent from the item; nothing is spawned yet.
2. Given a brief that builds a new screen but never says `design: yes`, when proposed, then Designer is *yes* and its signal text contains the word "screen" (example: "new screen: report filter").
3. Given a brief with a data-model or new-dependency choice, when proposed, then Architect is *yes* with that signal.
4. Given a one-line fix with existing tests, one repo, no risk flag, when proposed, then BA, Tech Lead, Team Lead, QA blackbox, Designer and Architect are *no*, each with a reason (QA blackbox: "no observable change"), and QA whitebox is *no* only because all five "out" conditions hold (at most 2 tasks, one repo, no user-visible change, no risk flag, existing tests cover it).
5. Given a risk flag, when proposed, then Tech Lead and QA whitebox are *yes*. Given the PO answers the inbox item with a reply that removes Tech Lead (for example "drop tech-lead"), then, after the Manager edits `scope.md` (no command writes the first `team:`), `team:` has no `tech-lead` and the iteration file's `## Log` has a line containing "override", the role and the flag (for example "Team override: PO removed tech-lead despite breaking-contract flag").
6. Given the PO confirms with the Architect removed, when the Manager has written the confirmed team to `scope.md`, then `scope.md` `team:` lists exactly the confirmed roles and has no `size:`, `design:`, `architecture:` or `qa-b:` line, its tokens are `qa-white`, `qa-black` etc. (never `qa-whitebox` or `qa-b`), and `squad-spawn architect` exits non-zero saying the role is not on the team, while `squad-spawn qa-whitebox` succeeds.
7. Given a goal with two scopes, then each scope has its own table and its own `team:` line.
8. Given a brief containing `size: M`, then the table is built from the scope's signals only, no team is derived from the size, and the item does not mention a size mapping.
31. Given the PO edits the proposal (adds some roles, removes others) in the inbox reply, when the Manager records it, then `team:` in `scope.md` equals the final list exactly (no extra or missing role, no duplicates).

**Duties and Done (any team)**
9. Given each of the six shapes in the reference table (S, M, L, L without QA blackbox, M plus `designer`, M plus `architect`), when `squad-process compose manager --home D` runs, then the `duties:` line gives, for each duty, the owner that today's SIZE-22 / SIZE-22a names for that size and flag (Plan, Design notes, Technical AC, Business AC, Code check, Behaviour check, Hand in to / done told to, plus Architecture and Irreversible choice with an Architect).
10. Given every one of the 128 teams (any subset of the seven optional roles), when composed by the suite test that sweeps them (run with `python3 tests/run_suite.py`; it prints pass/fail), then each of the 13 duties has exactly one owner, that owner is on the team or is Manager, Developer or the ticket, and no composed rule names an absent role as the one who acts, receives a hand-in or is waited on. QA accepts the suite test's pass as the observation.
11. (a) Given a rule or overlay whose `when:` has an unknown key or value (including `size` and `qa-b`), when `squad-process lint` or compose runs, then it exits non-zero naming the rule ID. (b) Given a scope with a decided `team:`, then its composed rules for every role contain no `[if ` tag; only goal homes and a Manager whose team is still blank (undecided) show `[if ...]` tags.
12. Given a team without Team Lead, then `squad-process compose dev --home D` names the QAs on the team as the HANDIN recipient (and, when there is no QA on the team, the Manager) and the composed Manager rules send the 3-returns notice to the Manager; given a team with Team Lead, the Team Lead.
13. Given a team without QA blackbox, then the composed QA whitebox rules say it checks the Developer's `## Behaviour` against the business AC; given a team with no QA at all, then the composed Manager rules say it confirms that `evidence.md` and `## Review` exist and that the task is Done without a QA PASS.
14. Given a team with both QAs, then the composed Manager and Team Lead rules state that a task is Done only when both QA whitebox and QA blackbox have passed it (and with a Designer also the built-UI check); the text for this team never says one PASS is enough.
15. Given a composed header or `squad-process who`, then it shows `team: <list|none|undecided>`, not a size. While the team is undecided, `squad-spawn` refuses every role except the Manager (non-zero, message says the team is undecided).

**Changing the team** (Manager behaviour, observed in files after a scripted scenario; `squad-team` is the Manager's tool)
16. Given a team without BA, when a Developer sends the Manager a business doubt, then (a) `scope.md` `team:` includes `ba`; (b) the plan (`iterations/N.md`) has a `## Handover` with decided, built and open; (c) the briefing sent to the BA (in `messages.jsonl`) points at the Handover; (d) `squad-team add ba` printed the roles whose composed rules changed and those roles were respawned; (e) the iteration file `## Log` has a line for the change; (f) the PO is told at the next check-in (the check-in inbox item mentions it).
17. Given the Manager adds `designer` or `architect`, then `squad-team add` without `--po-ok` exits non-zero and `team:` is unchanged; with `--po-ok` (after the PO's yes) it succeeds.
18. Given a QA added mid-scope, then before the scope closes every task built before that QA joined has a review file from that QA in `$SCOPE_DIR/evidence/<task>/`.
19. Given a request to remove a role, then `squad-team remove <role>` without `--at-boundary` exits non-zero and `team:` is unchanged; with it (iteration boundary and the PO's OK) `team:` drops the role and the Handover names the new owner of each duty the role held.

**Migration** (no shim)
20. Given a scope pinned to 0.5.x with `size: L`, when the new plugin is installed, then its `scope.md` and its composed rules are byte-identical to before, `squad-process adopt` skips it and says so, and its next respawn from the PO shell still works.
21. Given an overlay with `replace SIZE-2` and a local rule `when: size = L` or `when: qa-b = no`, when `squad-process upgrade` runs, then `squad-process upgrade --check` stdout lists each with its suggested replacement, with the exact lines `qa-b = no -> qa-black = no` and `size = L -> ba = yes` (L is the only size with a BA; for a rule about another L role the report also lists `team-lead = yes` and `tech-lead = yes` as alternatives), and every file is byte-identical afterwards. The PO's "yes" is a second run, `squad-process upgrade --apply --yes`, the only step that writes; a PO "no" is not running it, or running `--apply` without `--yes` (decisions listed, exit 3, nothing written).
22. (a) Given an open unpinned scope with `size: M` and `qa-b: no`, when `squad-process adopt --squad-dir D` runs (dry run), then it prints the proposed `team: qa-white` and writes nothing; after `--yes` the file has `team:` and none of the four old lines. Variants: `size: M` + `qa-b: yes` → `qa-white, qa-black`; `size: L` + `design: yes` → adds `designer`; `size: M` + `architecture: yes` → adds `architect`; `size: L` + `qa-b: no` → `ba, team-lead, tech-lead, qa-white`; `size: S` → `team: none` (confirmed minimal team); a blank `size:` → blank `team:` (undecided, as AC 15). (b) Given a legacy-layout squad, `squad-migrate` writes the same `team:` line for the same input.
23. Given `squad-report rollup a.json b.json` where a.json is a closed scope with `size: S` and b.json a new scope with a `team:`, then both render, the command exits 0, and each shows its own size or team.

**Migration, no shim, continued**
26. Given an unpinned legacy squad whose `scope.md` has `size: M` and no `team:`, when any role including the Manager is spawned or respawned with the new plugin, then it exits non-zero, the message names the file and the `size:` line and points at `squad-process adopt`, and no session starts with a guessed team.
27. Given an overlay rule with `when: qa-b = no`, then compose fails naming the rule and pointing at `squad-process upgrade`/the converter, while `qa-black = no` in the same place composes (this refines AC 11 with the pointer); given a `team:` line using `qa-whitebox` or `qa-b`, compose and `squad-spawn` reject it naming the line.
28. Given a squad migrated by `squad-process adopt --yes` from each shape of AC 9, when `squad-process compose manager --home D` runs, then it composes with no error and its `duties:` owners equal those of AC 9 for that shape.

**Output and team validity**
29. Given the PO-visible output of `squad-start`, `squad-spawn`, `squad-process who`, the Manager's proposal and a new `scope.md`, then none contains the whole word "size" (case-insensitive, `grep -iw size`), except the legacy-squad error (AC 26), the converter's output (AC 22) and the overlay report (AC 21), which must say "size" to name the old key. No other hit is allowed (a phrase like "file size" in these outputs is a finding to reword).
30. Given a `team:` line with an unknown role or a duplicate role, then `squad-process compose` and `squad-spawn` fail (non-zero) naming the line and the bad token.

**Cost and ship**
24. Given every one of the 128 teams, each `goal` value (yes/no) and `qa` value (full/light), then `squad-process compose dev --home D --out F` gives a file F of at most 5120 bytes (`wc -c F`). `design` is no longer a scope flag, so the sweep varies the team, not a `design:` line.
25. After the promotion task: (a) `CONTEXT.md` has no `**Size**` glossary entry and has `**Team**`, `**Duty owner**` and `**Checker**`; (b) a superseding ADR (`docs/adr/0018-...md`) exists; (c) `_removed.md` has a tombstone with `replaced_by` for every ID listed under `removed:` in the changelog v9 block; (d) the changelog v9 block exists; (e) the plugin version is 0.6.0 (`.claude-plugin/plugin.json`).

## Not in scope
Changing roles' stances, the Developer cap, models, `qa: full|light`, goal mechanics other than the goal trigger, or open scopes in flight.

## Hand-over to promotion (PROMO-3a), one line each
- Team replaces size, with no shim: existing squads migrate with the converter, the engine rejects old keys (PO, E4). Keys `qa-white`, `qa-black` in `team:`/`when:`; role names `qa-whitebox`/`qa-blackbox` and the term QA unchanged.
- Team replaces size; PO confirms the Manager's per-role suggestion (supersedes ADR 0016 Sizes and ADR 0017 "Manager never proposes Designer/Architect").
- Every duty has an owner chain ending at Manager or Developer; the PO always decides irreversible choices.
- Done = every checker on the team passed; with no QA, the Developer's evidence confirmed by the Manager.
- Risk flags force Tech Lead + QA whitebox (+ BA when another team sees it); business doubt forces BA; the PO may override, logged.
- Adding a role is the Manager's call (Designer/Architect: PO first); removing needs an iteration boundary and the PO's OK.
- Glossary: add **Team**, **Duty owner chain**, **Checker**; rewrite Size (remove), Risk flag, Handover, Manager traffic, Pod, Done, Single point of contact, and every "present in L scopes" line.

## For the PO (via the Manager's escalations)
- **P1.** May the Manager add the Designer or Architect mid-scope on its own? Proposed: no, the PO confirms first (they hold up the plan and can reopen built work), as only the PO could turn them on before.
- **P2.** Allow any team shape (Team Lead without Tech Lead, QA blackbox without QA whitebox, ...)? Proposed: yes, because duty chains cover every shape and every shape is tested; the Manager's rules keep odd shapes rare. The alternative adds a few "X requires Y" dependency rules.
