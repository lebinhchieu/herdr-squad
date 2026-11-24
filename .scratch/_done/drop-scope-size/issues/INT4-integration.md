# INT4 Wave 5 integration

Status: ready-for-agent
Type: task

## What
Integration per GOAL-6b: merge 11 (d8b4738, code ca53ba7) then 14 (7c8af4a, code b2ee4e5) onto base 90be196 (INT3). Resolve changelog v9 append conflict (keep both).

## AC
- test_dev_rules_size, test_sizes, test_squadsettings, test_instructions, test_process_conversion green on the merged result.
- `squad-process lint` at baseline (exit 0).
- No code changes beyond conflict resolution / stale-test fixes (named in evidence).
- Suite owner (Tech Lead) runs `--if-changed 90be196` on the final sha.

## Comments
Written so `squad-evidence check` finds the evidence folder.
