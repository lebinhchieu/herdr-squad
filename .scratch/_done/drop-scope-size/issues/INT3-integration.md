# INT3 Wave 4 integration

Status: ready-for-agent
Type: task

## What
Integration per GOAL-6b: merge 07 (0067a5d, code 0f1dc44) then 08 (evidence e08bb66, code f041603) onto base fed0c95 (INT2). Resolve changelog v9 append conflicts (keep all).

## AC
- test_squad_migrate, test_instructions, test_sizes, test_dev_rules_size, test_process_conversion green on the merged result.
- `squad-process lint` at baseline (exit 0, empty).
- No code changes beyond conflict resolution / stale-test fixes (named in evidence).
- Suite owner (Tech Lead) runs `--if-changed fed0c95` on the final sha.

## Comments
Written so `squad-evidence check` finds the evidence folder.
