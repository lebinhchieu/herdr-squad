# 01 Guards: the Team Lead spawns, respawns and retires every pod role
Status: ready-for-agent
Duties: design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=manager, choice-owner=tech-lead
Files: bin/squad-spawn (line 92 and its header), bin/squad-retire (lines 12-14), bin/squad-respawn (before the usage-event log), templates/squad/settings/team-lead.json, tests/test_team_lead_perms.py, tests/test_squadsettings.py (line 94); also commits all four tickets from `$SCOPE_DIR/tasks/NN.md` to `.scratch/tl-spawns-pod/issues/NN-<slug>.md` (FILE-11)
Depends: none. Base: main at 8d74fcb. Parallel-safe with 02. Plan: `$SCOPE_DIR/iterations/1.md`. Design notes: `$SCOPE_DIR/tasks/design.md` (D1-D5, D7).
Evidence: .scratch/tl-spawns-pod/issues/01-team-lead-guards/evidence.md

## What and why
Today `squad-spawn` (line 92) lets a Team Lead spawn only `dev`, `squad-retire` lets it retire only `dev`, and `squad-respawn` fails for a QA because it calls `squad-spawn`. So COST-10b ("the Team Lead respawns the roles the next iteration needs") cannot work. Chieu's brief: with a Team Lead on the team, the Team Lead spawns, respawns and retires every pod role on `team:` and the Developers; it never touches `manager`, `token-coach` or another `team-lead`.

## Design (copied from design.md)
- D1 deny-list: a caller with `SQUAD_ROLE=team-lead` may spawn any known role except `manager`, `token-coach` and a `team-lead` under a name other than `$SQUAD_NAME`. The `team:` gate further down stays the only check for "on the team".
- D2 name vs row: for a Team Lead caller, a name that already has a row in `$SCOPE_DIR/roster.md` must carry the role asked for; a name with no row passes. The row role is normalised first as in D3 (`QA Whitebox` is `qa-whitebox`), as `squad-respawn` does.
- D3 `squad-retire` for a Team Lead: role from `squad-usage --get`, lowercased, spaces to `-`; refuse `manager`, `token-coach`, every `team-lead` row (its own too) and a name with no row; allow every other role.
- D4 `squad-respawn` for a Team Lead: refuse a `manager`, `token-coach` or other `team-lead` row with exit 2 before the `respawn` usage event and before `herdr agent rename`.
- D5 settings: one `Bash(squad-spawn <role>:*)` entry per allowed role; nothing for the three never-roles; no `Bash(squad-spawn:*)`.
- Reuse the one role list; do not copy the three names into three scripts differently (a small shared function or the same literal pattern in each, your choice, kept next to the existing line).
- Out of scope: a second live copy of a role under a fresh name is not guarded (cost, not security).
- Compatibility (LC-12): additive; Manager, Developer and Team-Lead-self-respawn calls behave as before.

## Business AC
- AC1 A Team Lead (`SQUAD_ROLE=team-lead`) runs `squad-spawn <role> x --scope s --dry-run` with the role on `team:`: exit 0 for each of `dev`, `ba`, `tech-lead`, `qa-whitebox`, `qa-blackbox`, `designer`, `architect`.
- AC2 The same caller for `manager`, `token-coach`, and `team-lead` under a name other than its own: exit 2, empty stdout, stderr names the refused role and says a Team Lead may not spawn it (the old text "may only spawn dev" is gone); no `labels/` folder and no herdr call is made. `team-lead` under its own `SQUAD_NAME` still exits 0.
- AC3 Name vs row: that caller spawning `qa-whitebox` under a name whose roster row says `manager` exits 2 and the stderr names both roles, with no `labels/` folder and no herdr call (01-A); spawning `qa-whitebox` under a name whose row says `qa-whitebox` (the respawn case) or under a name whose row says `QA Whitebox` (written with capitals and a space), or under a name with no row exits 0.
- AC4 A role not on `team:` is still refused by the team gate for a Team Lead caller: `squad-spawn ba x --scope s --dry-run` on a `scope.md` with no `ba` exits non-zero, stderr says the role is not on the team, no side effect.
- AC5 `squad-retire <name> --no-notes` as a Team Lead: closes the pane (exit 0) for rows `dev`, `ba`, `tech-lead`, `qa-whitebox`, `qa-blackbox`, `designer`, `architect`; exit 2 with the pane still alive for rows `manager`, `token-coach`, `team-lead` (the caller's own row too) and for a name with no row. A row role written `QA Whitebox` counts as `qa-whitebox`.
- AC6 `squad-respawn <qa-name> --dry-run` as a Team Lead exits 0 and prints `squad-spawn qa-whitebox <qa-name>`. For a `manager`, `token-coach` or other-`team-lead` row it exits 2; a real (non-dry) run leaves `usage-events.jsonl` without a new `respawn` line and the herdr log without a `rename`. The Team Lead respawning itself still exits 0.
- AC7 Callers `manager`, `dev` and none spawn and retire exactly as before.

## Technical AC
- AC8 `grep -rn "only spawn dev\|only retire dev" bin tests` has no hit (base: 4 hits: `bin/squad-spawn:92`, `bin/squad-retire:14`, `tests/test_team_lead_perms.py:74` and `:115`).
- AC9 `grep -o 'Bash(squad-spawn [a-z-]*:\*)' templates/squad/settings/team-lead.json | sort` prints exactly the seven allowed roles (base: only `dev`); `grep -c 'squad-spawn:\*' templates/squad/settings/team-lead.json` is `0`; `ask` and `deny` are unchanged. `TL_ALLOW` in `tests/test_team_lead_perms.py` and the entries at `tests/test_squadsettings.py:94` match the new set.
- AC10 In `tests/test_team_lead_perms.py` the dev-only tests are replaced, never skipped: the three-role refusal (AC2), name vs row (AC3), retire allowed and refused rows (AC5), respawn refusal leaving no event and no rename (AC6). Extend the existing file and its `ROSTER`; no new test file. One test per risk.
- AC11 The header text of `bin/squad-spawn` and the comment above `bin/squad-retire`'s check describe the new rule (no stale "dev only" wording).
- AC12 Run and quote in `## Behaviour`: `tests/test_team_lead_perms.py`, `tests/test_squadsettings.py`, `tests/test_squad_spawn.py`, `tests/test_squad_retire.py`, `tests/test_squad_respawn.py`, and every hit of `grep -rl "squad-respawn\|squad-retire\|team-lead.json\|squad-spawn" tests/` that you did not edit.
- AC13 SQ-10: `bin/` is edited, so also run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py` and quote the result.
- AC14 Security read (QA whitebox): no path lets a `team-lead` caller reach `manager`, `token-coach` or a second `team-lead`: not by role, not by name-vs-row, not through `squad-respawn`, not through `SQUAD_RESPAWN=1`.
- AC15 Live check (QA blackbox, scratch home): the guard runs from the home's pinned runtime, which leads each agent's `PATH` (`bin/squad-spawn` lines 252-268), so it works only where the home is pinned at this branch's plugin. In a scratch squad composed and pinned to the branch, with a stub herdr, a pane with `SQUAD_ROLE=team-lead` shows AC1, AC2, AC5 and AC6 end to end; the same pane under a 0.10.3 pin still refuses with the old text (the expected limit, quoted in the evidence). A composed fixture in `tests/` is out of scope (the fixtures use `process.md`, legacy mode, and the running script).

- QA whitebox (agreed, REV-7; details in `$SCOPE_DIR/evidence/tech-ac/qa-w.md`):
  - 01-A Order: the name-vs-row refusal (D2) comes before the `team:` gate and before any `labels/` folder, worktree or herdr call. `$scope_dir` is known only after line ~128 of `bin/squad-spawn`, so move the scope resolution up or do the check where it is known but before those effects. Test: a refused D2 case leaves the scratch scope without `labels/` and the herdr log empty.
  - 01-B Fail closed: for a Team Lead caller a name missing from a readable roster passes; a missing or unreadable `$scope_dir/roster.md` refuses with exit 2. One test: `roster.md` absent, `squad-spawn qa-whitebox x` exits 2. Name `$scope_dir/roster.md` in the code comment.
  - 01-C (makes AC14 checkable) (a) the guard does not read `SQUAD_RESPAWN`: `grep -n SQUAD_RESPAWN bin/squad-spawn` shows only the event-log line (about 539-540). (b) The guard keys on `SQUAD_ROLE` only; a caller that sets `SQUAD_ROLE=manager` on the command line misses the allow entries and prompts the PO. `evidence.md` states this limit: the guard stops mistakes, not a Team Lead rewriting its own environment.
  - 01-D The `squad-respawn` refusal test uses a row written with capitals or a space (`Manager`, `QA Whitebox`) at least once each, so the D2b/D3 normalisation is pinned.

## Base dry-run (SQ-15, Tech Lead, main 8d74fcb)
- Run from `tests/`: `test_team_lead_perms` 9 ok, `test_squadsettings` 25 ok, `test_squad_spawn` 108 ok, `test_squad_retire` 4 ok, `test_squad_respawn` 33 ok, `test_windows_safe` 14 ok, `test_utf8_helpers` 14 ok, `test_instructions` 16 ok. All pass on base. The other 11 hits of AC12's grep (25 files in all) also pass on base: `test_squadupgrade` 45, `test_squad_close` 79, `test_architect_handoff` 11, `test_team_models` 19, `test_squad_usage_hook` 13, `test_crlf_squad_files` 6, `test_squad_start` 49, `test_winlaunch` 9, `test_squad_usage` 30, `test_squadcommands` 8, `test_squad_manager_guard` 25.
- AC8 on base: 4 hits (expected before the change). AC9 on base: only `Bash(squad-spawn dev:*)`, `squad-spawn:*` count 0.
- AC1 to AC7 are new behaviour; on base AC1 (roles other than `dev`), AC3, AC5 (non-dev rows) and AC6 fail as intended, AC4 refuses with the old text, AC7 passes.
- Known failing on base: none.

## Evidence
`evidence.md` next to the committed ticket; QA cells assembled before the Developer is retired. Run `squad-evidence check <evidence folder>` (no `--base`) before HANDIN and quote the exit code (SQ-18).
