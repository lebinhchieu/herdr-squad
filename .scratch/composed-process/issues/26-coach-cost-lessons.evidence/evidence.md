# 26 Token Coach cost lessons: evidence

## Behaviour

Baseline = the pinned 4901cab runtime (`git archive 4901cab bin`, unpacked to `/tmp/p26/old`) against this branch. `probe.sh <runtime-root> <role> <rule> <outdir>` copies that runtime's `squad-usage-hook` beside a **stub `squad-usage`** that prints the rule (`fresh`), so the fresh-context event is fed without a real transcript. It runs the hook twice in one session (`session_id` s1) with `SQUAD_ROLE` set and `SCOPE_DIR`/`GOAL_DIR` unset, and records stderr and exit code of both runs.

**AC1, Developer fresh event** (4901cab, then now), exit 2 both times, text differs:
- old: `... then write roles/dev-1.notes.md, then run: squad-respawn dev-1`
- new: `... then write roles/dev-1.notes.md; if your ticket is handed in or passed, tell the Team Lead and stop ([COST-5], no squad-respawn); if you are mid-ticket, run once: squad-respawn dev-1`
- the logged `action` in `usage-events.jsonl` is the same new text (`test_squad_usage_hook.test_fixture_over_120k...`).

**AC2, other roles:** `tech-lead` and `manager` runs: stderr and exit code of run 1 and run 2 are byte-identical to 4901cab (`cmp`); tech-lead exit 2 with the old text, manager exit 0 (exempt); the second event in a session is exit 0 with 0 bytes for dev and tech-lead (also `test_tech_lead_text_is_unchanged`, `test_rule_fires_once_per_session`).

**AC3, who:**
- COST-3: manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer (no dev)
- COST-5: dev
- COST-13, COST-14: ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer; aware manager

**AC4, wording:** copied from `$SQUAD_DIR/process.md` Cost rules 2 (lines 248, 250, 251), all clauses kept. Differences, by design: COST-5 sentence "goes first to a live Developer under 80k, before any new spawn" (the identical sentence is in COST-6a and `lint` bans a 12-word duplicate); "Nothing left to do"/"Short life" lose their bullet label; pointers/owners "the Team Lead (S: the Manager)" kept as live.

## Checks
- `cd tests; python3 -m unittest test_squad_usage_hook test_squad_usage test_dev_rules_size test_pod_rules_process test_windows_safe`: 57 tests OK. `bin/squad-process lint`: clean.
- `test_dev_rules_size`: the duty pins moved (COST-3 `squad-respawn` no longer reaches dev; COST-5 pinned on "no `squad-respawn`"). Limit unchanged (5120).
- **Developer rules byte delta** (composed, design no/goal no for S/M; L is design yes/goal yes, the largest): S 4926 → 4932, M 4901 → 4907, L 5081 → 5087 (+6 each; limit 5120).

## Notes
- Probe slip: my first probe run inherited `SCOPE_DIR` and appended one record (`agent dev-1`, session s1, fresh, old text) to the live `scopes/process-fixes/usage-events.jsonl` (line 8). The fix was denied by the permission classifier; the line is a stray test record for the Tech Lead to drop. Later runs unset `SCOPE_DIR`.
