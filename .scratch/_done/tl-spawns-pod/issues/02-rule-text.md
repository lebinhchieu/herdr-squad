# 02 Rule text: the Team Lead spawns, respawns and retires the pod
Status: ready-for-agent
Duties: design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=manager, choice-owner=tech-lead
Files: templates/squad/process/spawning.md, templates/squad/process/cost.md, templates/squad/process/starting.md, templates/squad/process/sizes.md, templates/squad/process/files.md, templates/squad/process/messages.md, templates/squad/process/who.md, templates/squad/process/goal.md, skills/squad-process-update/changelog.md, tests/test_rules_contract.py (and each pinned test the edit breaks, listed in the AC)
Depends: none. Base: main at 8d74fcb. Parallel-safe with 01. Plan: `$SCOPE_DIR/iterations/1.md`. Design notes: `$SCOPE_DIR/tasks/design.md` (D1, D6, D7, D8).
Evidence: .scratch/tl-spawns-pod/issues/02-rule-text/evidence.md

## What and why
The rules still say the Manager spawns every pod role and the Team Lead only Developers (SPAWN-2b, 2c, 8b, 9), yet COST-10b already tells the Team Lead to respawn the roles the next iteration needs. Rewrite the rule text so the Team Lead spawns, respawns and retires every pod role on `team:` and the Developers; the Manager spawns only the Team Lead and, at the close, the Token Coach. 01 makes the scripts allow it.

## Design (copied from design.md)
- D6 no rule ID is removed or renamed: `_removed.md` is not touched. SPAWN-9 keeps its ID, new title "Team Lead spawns and retires the pod". `roles:` follows the actor: add `team-lead` to SPAWN-3, SPAWN-4, SPAWN-4a and START-4a (the Team Lead now acts on them); add `aware: team-lead` to SIZE-13 and SIZE-21a if they stay `roles: manager`.
- One phrase everywhere it applies: **"spawns, respawns and retires"** (SPAWN-9, START-2c, START-5, MSG-5).
- SPAWN-9 body, in this order: the Team Lead spawns, respawns and retires every role on `team:` and the Developers, with `squad-spawn`, `squad-respawn`, `squad-retire`; it never spawns, respawns or retires `manager`, `token-coach` or another `team-lead` (the Manager spawns the Token Coach at the close, [ITER-6b]); a role not on `team:` is refused by `squad-spawn` and a late role comes through the Manager (`squad-team add`, the `## Handover`, [SIZE-13]), after which the Team Lead spawns the joiner from the Handover and respawns the roles `squad-team` lists; Designer and Architect join only after the PO's yes.
- D7 the PO's yes for Designer and Architect stays; D8 the Architect: the Team Lead spawns and retires it; before the plan, when no Team Lead is up, the Manager spawns the Team Lead first. No text may let the Manager spawn a pod role other than the Team Lead and the Token Coach.
- FILE-5b/5c: `squad-spawn` adds the row; whoever spawned an agent fills its Owns and Status; the Manager keeps its own row and the Team Lead's. FILE-5c (Team Lead) edits the rows of the agents it spawned, not only Developers.
- No behaviour change to the Manager's own spawn path (`squad-spawn` for the Team Lead and the Token Coach).

## Business AC
- AC1 `grep -rn "spawns and retires Developers\|retire only Developers\|spawns Developers; you do not" templates/squad/process/` has no hit (base: 5 hits in `spawning.md`, `starting.md`, `sizes.md`, `messages.md`).
- AC2 SPAWN-2b says the Manager spawns `team-lead` and `token-coach` only and that the Team Lead spawns every other role on `team:`; it no longer contains "every other role on" in the Manager's list. SPAWN-2c says the Team Lead spawns Developers and the pod roles, the Manager neither.
- AC3 SPAWN-9: title has no "only"; body satisfies the SPAWN-9 line of the Design section, names `manager`, `token-coach` and another Team Lead as never, and contains "spawns, respawns and retires". SPAWN-8b says the Team Lead retires any pod role with `squad-retire` once its work is accepted (not only a Developer).
- AC4 COST-10b: the Team Lead retires every pod role over 60k before a PO wait and respawns the roles the next iteration needs; the sentence "the Manager retires every pod role" is gone (base: present).
- AC5 START-2c, START-5 and MSG-5 contain "spawns, respawns and retires" (START-5 as one line after its table: the Manager spawns the Team Lead and the Token Coach, the Team Lead every other row). MSG-6's "add a role" bullet says the Manager adds it and the Team Lead spawns it.
- AC6 SIZE-13 second bullet: the Manager runs `squad-team add` and writes the `## Handover`; the Team Lead spawns the joiner and respawns the listed roles. SIZE-21a: the Manager spawns the Team Lead and the Token Coach, the Team Lead the rest of `team:` and the Developers.
- AC7 FILE-5b and FILE-5c as in the Design section (FILE-5c no longer says "the Developers you spawned"; base: present). `goal.md` line 8: the goal Manager spawns each scope's Team Lead and the Team Lead spawns the rest of the pod. `who.md` line 104 reads "Manager; Team Lead for the pod roles and Developers" in the spawning row.
- AC8 SPAWN-10b: "Developers keep running" becomes "the pod keeps running" (base: present).

## Technical AC
- AC9 `roles:` lines: for each of SPAWN-3, SPAWN-4, SPAWN-4a the `roles:` line contains `team-lead`; START-4a likewise. Check: `for id in SPAWN-3 SPAWN-4 SPAWN-4a; do awk -v id="$id" '$0 ~ "^## " id " "{f=1;next} f&&/^roles:/{print id": "$0;exit}' templates/squad/process/spawning.md; done` (base: `roles: manager` for all three).
- AC10 `git diff main --stat -- templates/squad/process/_removed.md` is empty, and every rule ID present on main is still present in the process folder (`diff <(git show main:templates/squad/process/spawning.md | grep -o '^## [A-Z]*-[0-9a-z]*' ) <(grep -o '^## [A-Z]*-[0-9a-z]*' templates/squad/process/spawning.md)` empty, same for each edited file).
- AC11 Changelog: a new top entry `## v23 — 2026-11-22` in `skills/squad-process-update/changelog.md` in the existing format (changed list with `why:`, `Deploy (Chieu):` and `Rollback:` lines per design.md: merge, `claude plugin update` to 0.10.4, then `/squad:squad-process-update` so the squad upgrade and `squad-process homes --apply --yes` move each open home's pin and respawn its agents (a home pinned at 0.10.3 or older keeps the old Team Lead guard in its agents' `PATH`; a bare respawn changes nothing); rollback is revert, plugin back to 0.10.3 and the pins moved back by the same step). It says "Plugin 0.10.4"; 03 bumps `plugin.json` to match (`tests/test_promotion_0_6_0.py` keeps passing).
- AC12 Tests: update `tests/test_rules_contract.py` (lines 32, 154-160, 164-169: rename `test_team_lead_spawns_and_retires_dev_only`, replace the `"no" in SPAWN-9` assertion with the new SPAWN-9 content, keep the ID checks) and every other pinned test the edit breaks (`grep -rl "SPAWN-\|COST-10b\|START-2c\|START-5\|SIZE-13\|SIZE-21a\|FILE-5b\|MSG-5\|MSG-6" tests/` hits: expect `tests/test_small_files_equivalence.py`, `tests/test_sizes.py`, `tests/test_qab_optional.py`, `tests/test_rules_wording.py`, `tests/test_dev_rules_size.py`). Update, never skip; no new test file; one assertion per new risk (SPAWN-9 content, `roles:` retarget, no ID removed).
- AC13 Run and quote in `## Behaviour`: `tests/test_rules_contract.py`, the hits above, `tests/test_processlint.py` (rule text lint, no dates or "formerly"), `tests/test_old_language_inventory.py`.
- AC14 SQ-10: this diff edits text attached to roles, so run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py` and quote the result.
- AC15 Rule text follows the existing style: no dates, no "formerly", no size words (`tests/test_rules_contract.py` `test_spawning_cost_and_safety_files_have_no_size_word`).

## Base dry-run (SQ-15, Tech Lead, main 8d74fcb)
- From `tests/`: `test_rules_contract` 17 ok, `test_rules_wording` 30 ok, `test_dev_rules_size` 9 ok, `test_sizes` 8 ok, `test_small_files_equivalence` 2 ok, `test_qab_optional` 11 ok, `test_old_language_inventory` 2 ok, `test_windows_safe` 14 ok, `test_utf8_helpers` 14 ok, `test_instructions` 16 ok. All pass on base.
- AC1 on base: 5 hits. AC9 on base: `roles: manager` x3. AC4, AC7, AC8 phrases are present on base (each AC names the base text it removes).
- Known failing on base: none.

## Evidence
`evidence.md` next to the committed ticket (01's Developer commits the ticket files; this Developer writes its evidence at that same path in its own branch and does not rebase onto 01). Run `squad-evidence check <evidence folder>` (no `--base`) before HANDIN and quote the exit code (SQ-18).
