# Evidence 02 Scratch rm under /tmp/tmp.*: remove the ask entries

## Behaviour
Command: `python3 bin/squadsettings.py effective --role dev --squad-dir $T/sq --template-root . --out $T/o.json` (empty `dev.local.json`), rc=0. Read back:
- `/tmp/tmp.` entries in `permissions.ask`: `[]` (ask has only the 18 Atlassian entries from 01).
- `/tmp/tmp.` entries in `allow`: `Bash(rm -rf /tmp/tmp.*)`, `Bash(rm -r /tmp/tmp.*)`, `Bash(rm /tmp/tmp.*)`, `Bash(rmdir /tmp/tmp.*)`.
- 16 entries removed from each of dev, qa-whitebox, qa-blackbox, manager, tech-lead, team-lead; other roles never had them or an rm allow.
- SAFE-11 now: "Scratch dirs: `mktemp -d` only. `cd` out before `rm`. One path per `rm`: `rm -rf /tmp/tmp.X`; repeat per dir."
- `test_safe11_rm_examples_match_allow_and_no_ask` still proves `rm -rf /tmp/tmp.A` matches allow and not ask (negative control that asserted the two-path ask match was removed with the entries).

## Tests
Run: test_squadsettings 25, test_team_lead_perms, test_squadrules, test_sizes, test_dev_rules_size: OK. `bin/squad-process lint` rc=0. `test_team_lead_perms` needed no change (asserts only allow).

## test_ca_launchers error (asked by the Manager)
`test_scripts_are_syntactically_valid_bash` passes on a `git archive main` copy and fails in this worktree with `IsADirectoryError ... tools/claude-accounts/bin/__pycache__`. Cause: running the file imports `caproc.py`, which writes an ignored `__pycache__` dir; the test globs `bin/` and reads it. Not from this diff (no `tools/` change); it appears on any tree after the first test run that imports caproc.
