# 26 Token Coach cost lessons: evidence
sha: 57335d5
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

## QA whitebox review

### QA whitebox 26 (Coach cost lessons): PASS @ 57335d5

Ran (detached worktree): `test_squad_usage_hook test_squad_usage test_dev_rules_size test_pod_rules_process test_windows_safe test_instructions test_processlint` = 116 OK; `squad-process lint` ok (rc 0). Reviewed 0e0a362..57335d5: `cost.md`, `bin/squad-usage-hook`, `test_squad_usage_hook`, `test_dev_rules_size`.

#### AC check
1. Hook: ran the real script from a temp squad (stub `squad-usage` printing `fresh`, `env -u SCOPE_DIR -u GOAL_DIR`, temp `SQUAD_DIR`, live logs untouched): `dev` run 1 exit 2 with the retire text, run 2 exit 0 silent; logged `action` carries the same text and `role dev`. `tech-lead` text pinned byte-for-byte in `test_tech_lead_text_is_unchanged`; Manager exemption and once-per-session tests still pass. (A different role in the same session after a dev event is silent: once per session, as the AC says.)
2. `who`: COST-3 no dev; COST-5 dev only; COST-13/14 act the six roles, aware manager, same in S/M/L. Dev rules +6 B, limit 5120 unchanged; the `test_dev_rules_size` duty pins moved with the text (COST-5 pinned on "no `squad-respawn`"), not weakened.
3. Wording: compared with live `process.md` lines 248, 250, 251, all clauses kept; only the stated differences (COST-5 sentence reworded because lint bans a 12-word duplicate with COST-6a; bullet labels become headings).
4. Lint ok: IDs unique, no renames, no dup.

#### Notes (not blocking)
1. Stray dev-1/s1 record at line 8 of the live scope `usage-events.jsonl` (Dev's probe slip, disclosed in evidence): Tech Lead to drop. Not in the diff.
2. Evidence is old-form `26-….evidence/`; integration re-runs `git mv`.

## QA blackbox review

### QA-b 26 (commit 57335d5, branch squad/plugin/process-fixes/plugin-dev-pf-8)
Method: `bin/squad-usage-hook` from `git archive 57335d5` and from the pinned baseline `git archive 4901cab`, each run twice per role with a stub `squad-usage` printing `fresh` (SQUAD_DIR scratch, SCOPE_DIR/GOAL_DIR unset); `squad-process who` and `compose` on the branch worktree. No code read.

| AC | What I did | Saw | Result |
| --- | --- | --- | --- |
| 1 | Developer fresh event, baseline vs branch | Baseline: `...then run: squad-respawn x-1`. Branch: `write roles/x-1.notes.md; if your ticket is handed in or passed, tell the Team Lead and stop ([COST-5], no squad-respawn); if you are mid-ticket, run once: squad-respawn x-1`. Same text in `usage-events.jsonl` `action`. Exit 2 | pass |
| 2 | tech-lead, team-lead, ba, qa-whitebox, qa-blackbox, designer, manager: stderr baseline vs branch; second event | six roles byte-identical (exit 2); manager exit 0 (exempt), no stderr; second event exit 0 and 0 bytes for every role | pass |
| 3 | `squad-process who COST-3/5/13/14` | COST-3: no dev; COST-5: dev only; COST-13 and COST-14: ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, designer, manager aware, at S, M and L | pass |
| 4 | Composed dev and tech-lead rules vs the live `process.md` Cost rules 2 | COST-5 keeps all clauses (120k merged-ready, or no open ticket touches its files; mid-ticket respawn once then split; at most 2 files to a live Developer under 80k first; retired name never reused). COST-13 and COST-14 match the live bullets word for word | pass |
| size | Composed Developer rules | 4832 bytes (under 5 KiB) | pass |

Verdict: PASS 26 on 57335d5.
