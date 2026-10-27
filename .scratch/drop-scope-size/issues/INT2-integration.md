# INT2 Wave 3 integration

Status: ready-for-agent
Type: task

## What
Integration per GOAL-6b: merge 04 (b2dcc52, evidence 14847ad), 10 (d792d78, evidence f8af869), 06 (bd361cf, evidence 9620c7e) onto base 6389642. 07 is NOT merged (Tech DECISION INT2: goes to INT3 with 08). Resolve changelog v9 append conflicts (keep all).

## AC
- test_squad_migrate, test_instructions, test_squad_team, test_squad_spawn green on the merged result.
- `squad-process lint` at baseline (exit 0, empty).
- No code changes beyond conflict resolution / stale-test fixes.
- Suite owner (Tech Lead) runs `--if-changed 6389642` on the final sha.

## Comments
Written so `squad-evidence check` finds the evidence folder.
