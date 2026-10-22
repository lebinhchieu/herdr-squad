Status: ready-for-agent
Type: task
Task ID: 26
Touches: `templates/squad/process/cost.md` (COST-3 roles, COST-5, two new rules, COST-8 unchanged), `bin/squad-usage-hook` (the `action` text for a Developer), `tests/test_squad_usage_hook.py`, `tests/test_dev_rules_size.py` (only if the Developer size limit breaks), `tests/test_suite_rules_process.py` only if it pins cost text
Ticket file: lives in `$SCOPE_DIR/tasks/`; the Developer's first commit copies it to `.scratch/composed-process/issues/26-coach-cost-lessons.md`.
Does not touch: `bin/squad-usage` (it computes the rule, it prints no action), `templates/squad/process/iterations.md`, `agents/*`, `hooks/hooks.json`
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_usage_hook test_squad_usage test_dev_rules_size test_pod_rules_process test_windows_safe`; `python3 bin/squad-process lint`
Blocked by: 11 (11 edits `cost.md` for the Manager notice; branch from the merged 11)

# 26: The Token Coach's three cost lessons reach the plugin rules and the hook

**Done when a Developer's fresh event says "retire" (not "respawn"), and `cost.md` carries the three Coach rules that the live squad already runs.**

## Why
Coach role-cards-upgrade it.1 (`scopes/_done/role-cards-upgrade/iterations/1.coach.md`, #1-#3): 14 respawns cost about 450k of cold start. The Manager accepted them into the live squad on 2026-10-22 (`$SQUAD_DIR/process-log.md`, last row; wording in `$SQUAD_DIR/process.md` → Cost rules 2). Without this ticket the plugin template loses them and `bin/squad-usage-hook` still prints `squad-respawn` to every Developer, against COST-5.

## What
- **`cost.md`:** copy the live wording, no new decision:
  - COST-5 Developer: at 120k, or when no open ticket touches its files, a Developer whose ticket is merged-ready retires (no `squad-respawn`); mid-ticket it respawns once, then the Tech Lead splits the rest; a ticket touching at most 2 files goes to a live Developer under 80k before a new spawn; a retired name is never reused (all clauses of the live wording kept; if the Developer size test breaks, shorten words, not clauses). Remove `dev` from COST-3's `roles:` so only COST-5 speaks to Developers (COST-3's other roles unchanged).
  - New `COST-13 Nothing left to do` (roles: ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer; aware: manager): the live "Nothing left to do" bullet.
  - New `COST-14 Short life` (same roles): the live "Short life" bullet.
  - Plan-owner wording stays "the Team Lead (S: the Manager)" as in COST-6; ticket 17 (sizes) rewrites owners later.
  - Each new rule ID is unused; none is renamed; `_removed.md` is not needed.
- **`bin/squad-usage-hook`:** for `SQUAD_ROLE=dev` the printed action and the logged `action` read: write `roles/<name>.notes.md`; if your ticket is handed in or passed, tell the Team Lead and stop (`[COST-5]`, no `squad-respawn`); if you are mid-ticket, `squad-respawn <name>` once. Other roles unchanged. The hook stays exit 2 + stderr, once per session and rule.

## Technical AC
1. `test_squad_usage_hook`: a `dev` fresh event prints and logs the retire text and not `squad-respawn` as the only action; a `tech-lead` event is byte-identical to before; the Manager stays exempt; the second event in a session is silent.
2. `squad-process who COST-5` lists dev; `who COST-3` no longer lists dev; `who COST-13`/`COST-14` list the six roles; Developer composed rules stay within the 5 KiB test (`test_dev_rules_size`); if COST-5 grows, shorten, do not raise the limit.
3. The new text matches the live squad's wording (diff shown in the evidence).
4. `lint` passes: IDs unique, no 12-word sentence duplicated between rules, pointers (`[COST-5]`) resolve.
