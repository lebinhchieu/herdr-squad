# Evidence: 01 Contract: TS types and fixtures
sha: a6520db

## AC trace

| AC | Test or capture | How run |
|---|---|---|
| T0.1 types in `types/index.d.ts` as design-notes s2 (incl. `name_safe`, `changes: 'varies'`) | QA whitebox re-check, QA blackbox re-check | `git show a6520db:types/index.d.ts`; `claude plugin validate .` on a `git archive` of a6520db |
| T0.2 `tree.json` and `tree-empty.json` valid, version 1, required shapes | QA whitebox and blackbox scripts over every node and command | `python3 -c 'import json;json.load(open(...))'` on both files at a6520db |
| G1 no new dependency | no dependency file changed in the diff | `git diff --name-only <base> a6520db` |
| G2 UTF-8, no module `fcntl`; three SQ-10 files pass | no Python code in this ticket; the three files are run on the integration sha by the Tech Lead (T3.3) | `python3 tests/<file>.py` |
| G3 defect-class rule (LC-8) | process rule; QA returns on ab23706 (name_safe, Report, Report status, `varies`) were applied in a6520db | QA re-checks below |

## Review: QA whitebox

### QA whitebox: ticket 01 (contract), sha ab23706

Verdict: FAIL (return 1). Read-only: `git show ab23706:<file>`, a script that walks `tree.json` (every node, every command), the spec and design-notes tables.
Checked ok: tree.json and tree-empty.json are valid JSON, version 1; open goal g1 with 3 scopes (needs_you 2 = api, agents_working null = ui, one done = docs); lone open scope fix; done goal g0 with light scope old; lone done scope tiny; flat squad with `wait` New work + reason; every Command has exactly the 10 keys; no `run_ok`, `argv`, `--force`; every `wait` has a reason; inbox text is `squad-inbox --home <DIR> list --open --no-write`; retire text `squad-retire plugin-mgr-<name>`, only on lone done scope and done goal; Resume of scope api names the goal g1; spec.md in the commit equals `tasks/spec.md`; ticket files 01-06 present; no code touched (SQ-10 n/a).

#### Findings (all break a written AC)
1. **`name_safe` is missing from the types and the fixture.** design-notes s2 puts `"name_safe": bool` on Goal and Scope; T1.9a asserts it (`true`/`false`); T0.1 says the types are "exactly as design-notes section 2". `ScopeNode` and `GoalNode` in `types/index.d.ts` (lines 92-120) have no `name_safe`, no node of `tree.json` has it. Would pass: `name_safe: boolean` on both types, and `"name_safe": true` on every node of the fixture (add one unsafe node only if a mod test needs it; T1.9a covers it in Python).
2. **Fixture: open scopes have no Report.** Spec Commands table: Report applies to "any goal or scope"; AC3.1: an open lone scope shows "Resume, Board, Report, Inbox list, Close scope, Watchdog status, Sleep". Scopes `api`, `ui`, `fix` in `tree.json` have report-status but no `report` (goal g1 has it). Would pass: a `report` command on each open scope.
3. **Fixture: done scopes have no Report status.** Spec AC3.3: "a closed scope also shows Report status"; closed scope of an open goal: "Board, Report and Report status". Scopes `docs` (done, open goal), `old` (scope of done goal) and `tiny` (lone done) have only board/report (+ retire on tiny). Would pass: `report-status` on all three. (`g0`, a goal, correctly has none.)
4. **`changes: "varies"` is not in the type.** `SquadCommand.changes` is `'read'|'writes'|'destructive'|'starts'` (index.d.ts:83) but the team-group commands (`squad-spawn`, `squad-team`) carry `"varies"` in the fixture. design-notes s2 lists four values and s3 table says "varies": the two Tech Lead texts disagree. The type and the fixture must agree, or T2.3's parseTree test on this fixture cannot be written. Would pass: add `'varies'` to the union (my suggestion; the Tech Lead may rule the other way and change the fixture instead).

#### Follow-ups (not AC)
- TS names are `SquadFacts` and `SquadCommand`; T0.1 names `Facts` and `Command`. No clash exists in the file, so the AC wording should follow the code: Tech Lead to confirm, no change needed from the Developer.
- Ticket files keep the draft `Touches:` line (Developer's note); scope-wide `--touches` was just removed: Team Lead's call.

### Re-check, sha a6520db (return 1 fixed)
Verdict: PASS. Changed files only (tree.json, types/index.d.ts); script over every node and command.
- name_safe: in ScopeNode and GoalNode (types), `true` on all 8 nodes of tree.json.
- report on all 8 nodes; report-status on all 5 scopes (open and done); goal nodes have none.
- 'varies' in the union; changes values in fixture = read, writes, starts, destructive, varies (all in the type).
- Every Command still has exactly 10 keys; no run_ok/argv/--force; every wait has a reason.
- `claude plugin validate .` on a `git archive` of a6520db: passed (warnings only). tree-empty.json valid.
Follow-ups: none new.

## Review: QA blackbox

### QA blackbox: ticket 01 (contract and fixtures), sha ab23706

No running app. I read the fixture as data (what the pane will be told to draw) and compared it with the business AC in spec.md. Ticket AC = tech-ac T0.1, T0.2 (whitebox owns T0.1 types and `claude plugin validate`).

| Check | shot/live | What I did | What I saw | Result |
|---|---|---|---|---|
| T0.2 `tree-empty.json` valid, `squads: []` | live | parsed with python json | version 1, squads [] | pass |
| T0.2 `tree.json` valid v1, shapes listed | live | parsed, printed the tree | squad `plugin`: goal g1 (scopes api needs 2, ui agents null + unknown herdr, docs done), lone open `fix`, done goal g0 (+ light scope old), lone done `tiny`; flat squad `old-flat` | pass |
| a `wait` command with a reason | live | read commands | Resume "agents are working now", Close scope "tasks open", Close goal "scope api is open", New work (flat) "flat layout: squad-start refuses it" | pass |
| `.scratch/squads-mod/spec.md` = final spec; issues 01-06 present | live | `diff` with tasks/spec.md; `git ls-tree` | same; 6 issue files | pass |
| Numbers add up (goal g1 = sum of its scopes, done scope counted) | live | summed facts | tasks 3/7, agents 1, needs 2; squad needs_you 2 | pass |
| AC3.2 Resume of a scope in a goal uses the goal's name | live | read text | `squad-start --resume g1 --squad plugin` | pass |
| AC3.3 retire text | live | read text | `squad-retire plugin-mgr-g0`, `plugin-mgr-tiny`; none on a scope of a goal | pass |

#### Follow-ups (not ticket-01 AC; they become FAILs on 02/03 because the 02 golden equals this fixture)
1. AC3.1: an open scope has no plain `Report` command (`squad-report <name> --squad S`), only `Report status`. Goal g1 has Report. AC3.1 lists Report for an open scope.
2. AC3.3: closed scopes `docs`, `old`, `tiny` have Board and Report only. Report status is missing on each (a closed scope also shows Report status).
3. AC3.7: Board `when` is "Open the board."; it must say "keeps running: stop with Ctrl-C".
4. AC1.7: Close squad `when` is "Close the whole squad."; it needs the warning.
5. Commands table: goal g1 has no Watchdog status and no Sleep when idle (table: open scope or goal).
6. AC3.6 words: reasons are "agents are working now" and "nothing to answer"; spec says "agents are working" and "no open questions".

#### Re-check: sha a6520db (changed files only: tree.json, types/index.d.ts)
Re-parsed tree.json and printed every command. Follow-ups 1-6 all applied: open scopes have Report; closed scopes docs, old, tiny have Report status; every Board `when` ends "Keeps running: stop with Ctrl-C."; Close squad `when` has "Warning: retires every agent and archives the squad."; goal g1 has Watchdog status and Sleep when idle; reasons are "agents are working" and "no open questions". New: `name_safe` on goal and scope rows (all true). Resume of scope in goal still `--resume g1`; Retire only on g0 and tiny. Result: pass.
Not checked by me: that the Close squad warning words are true (whitebox/02 shows the real CLI).
