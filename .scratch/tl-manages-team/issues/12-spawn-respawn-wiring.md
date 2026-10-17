# T12 · squad-spawn and squad-respawn use the combined settings
Status: ready-for-agent
Type: task
Blocked by: T10 and T11 passed (QA whitebox). Branch from T10's passed sha and merge T11's.
Repo: /home/chieule/workspace/squad
Spec: PO E3/E4 · Design: ../design.md decisions 16-18, 20 (where it runs), 22, 23 · Technical AC: AC-13 below (QA-W to confirm)

## Files this task touches (and no others)
`bin/squad-spawn`, `bin/squad-respawn` (header comment only), `tests/test_squad_spawn.py`, `tests/test_squad_respawn.py`, `tests/test_settings_live_claude.py` (new). **Keep every `bin/squad-spawn` hunk small and separate** (another scope may edit the role list; do not touch the `case $role` line or the Team Lead gate).

## Do
1. **Settings block (lines ~123-125 and `key_of`).** Replace the `settings=` choice by: build the effective file with `"$plugin_root/bin/squad-settings" build "$role" --squad-dir "$squad_dir" --out "$home/roles/$name.settings.json"` (`--check` instead of `--out` under `--dry-run`), stderr passed through (the warnings), a non-zero exit ends the spawn with exit 2 and no fallback to the raw file. Pass that path to `--settings`. `key_of` reads `model` and `effortLevel` from the generated file only (same `jq` and regex, same "no key" warning; precedence and results identical to today: flag, squad file, template).
2. **`squad-spawn <role> --show-settings [--squad NAME]`**: prints what `squad-settings show` prints for the squad and exits 0 before any herdr check or agent name; `squad-spawn` with only `<role>` and that flag is valid (adjust the argument-count check). Update `--help`.
3. **Manager spawn:** the existing `squad-process check --quiet` notice block becomes `squad-process auto --source squad-spawn --quiet`; its output (when not empty) goes into the Manager's prompt as `Process update: <message> <rule>` where the rule text is the one in `agents/manager.md` (T11): applied: "Tell the PO in your first message and tell running roles to re-read the changed sections."; blocked: "Put it in the PO inbox." No other role's spawn calls it (design decision 20).
4. **`bin/squad-respawn`:** no logic change (it calls `squad-spawn`, so it rebuilds the file); fix the header comment to say the settings are rebuilt from the template and the squad file at each respawn.
5. **Tests.** `test_squad_spawn.py` (the existing fake `herdr`, dry-run): the `--settings` argument is `<home>/roles/<name>.settings.json` and in a real (non-dry) run holds the combined JSON with no `remove` and no stamp; a layered squad file adding an allow and removing a template deny gives exactly that; a full copy is passed through unchanged with the warning; an invalid squad file exits 2 and starts nothing (fake herdr log empty); `--dry-run` writes no file; `--show-settings` works with `HERDR_ENV` unset and no name; the T9 tests (flag beats squad beats template, no-key warning, bad value) still pass unchanged; Manager prompt carries the applied and blocked notices from a temp squad, a Developer spawn does not call `auto` (process.md hash unchanged). `test_squad_respawn.py`: a respawn dry-run shows the generated path, and after changing the template (a copy in a temp plugin root) a real respawn run rebuilds the file with the change.
6. **`tests/test_settings_live_claude.py`**: the real Claude Code accepts the generated file. Skipped unless `SQUAD_LIVE_CLAUDE=1` and `claude` is on PATH (the full suite does not run it; it costs one tiny call per case). For each of the 9 roles: build the file with `squad-settings build` from a layered temp squad, run `claude -p --settings <file> --model haiku --max-budget-usd 0.05 "reply with the single word ok" </dev/null`, assert exit 0, `ok` in the output and **no** "did not load". Negative control: a file with `"allow": "x"` must print "did not load" (proves the detector). One more: a `squad-spawn <role> --show-settings` output is itself accepted (it is the same JSON).
7. **Run only the test files you touched**; never the full suite. `PYTHONDONTWRITEBYTECODE=1`. Run the live test once (`SQUAD_LIVE_CLAUDE=1`) and save its output in `dev-evidence.md`.

## Technical AC (AC-13)
- AC-13.1 Effective `--model/--effort` per role unchanged versus main 507f86e (table in `dev-evidence.md`, from `--dry-run` on both).
- AC-13.2 For each of the 9 roles the generated file's `permissions` equals the template's when the squad has no file, and equals the full copy's when the squad file is a full copy (the compatibility promise, tested on the real live squad's files copied to a temp squad).
- AC-13.3 A broken squad file or a missing `python3` never reaches `claude`: no agent starts, exit 2, stderr names the file.
- AC-13.4 `bash -n bin/squad-spawn bin/squad-respawn`; no `eval`; `git diff main -- bin/squad-spawn` shows only the three hunks (settings block, `--show-settings` and the argument check, the Manager notice).
- AC-13.5 Live test output saved: 9 roles pass, the negative control shows "did not load".
- AC-13.6 The merge sha of T12 goes to the Manager at once (`extractor-role` rebases on it).

## Business AC
PO E3: a plugin change to a role's allow or deny rules reaches every layered squad at the next spawn or respawn, with no hand edit; Claude never sees `remove`; the PO can see the final result with `--show-settings`.

## Amendments (Tech Lead, 2026-10-17, from QA-W v6)
- **A11 `key_of` in dry-run:** `squad-settings show` output is captured once into a shell variable (not a file) and `key_of` reads `model` and `effortLevel` from it, in both modes; under `--dry-run` the build step is `squad-settings build --check` (writes nothing) and the printed `--settings` value is the path it would write. AC-13.1 compares `--dry-run` output on main and on the branch.
- **A13 Manager notice (changes item 3):** `squad-spawn manager` uses `$SQUAD_PROCESS_NOTICE` when it is set (squad-start passes it, T11) and runs `squad-process auto --source squad-spawn --quiet` only when it is unset. The output starts with `applied:` or `blocked:`; that word picks the rule text. Test both: variable set (prompt carries it, `auto` not run) and unset (spawn applies on a v3 temp squad).
- **A12** Test (fake herdr): an invalid squad settings file makes `squad-respawn` exit non-zero (1 is fine), keep the old agent name and pane, and start nothing.
- **A8 live test:** the detector matches "did not load", "were skipped" and "can't apply"; negative controls for both messages (see T10 A8); 9 valid role files print neither. Skipped (not failed) without `SQUAD_LIVE_CLAUDE=1`; the receipt shows it as skipped.
