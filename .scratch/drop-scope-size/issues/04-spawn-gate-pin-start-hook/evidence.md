# Evidence: 04 spawn gate, pinned hand-off, start, hook
sha: c97299a

## Behaviour
- `squad-spawn` team gate (via `squad-process team --has`): role not on team exits 1 naming role and `scope.md`, nothing created; `qa-whitebox`/`qa-blackbox` gated on `qa-white`/`qa-black`; undecided team refuses all but Manager; `size:`-only or bad `team:` line exits 2 with the converter pointer / line+token; hostile `team:` values run nothing. Goal Manager has no gate.
- Pinned scope below 0.6.0: `squad-spawn` and `squad-respawn` `exec` the pin's own script with the same args (PO shell and agent session; `--dry-run` prints "would hand off"). Pin 0.6.0 -> new gate, no hand-off; no pin line -> unpinned path; malformed `plugin:` line -> refused naming the line; runtime without the script -> warning, exit 1, nothing created/renamed. One hop (runtime == this script is not re-entered). Pinned `scope.md` byte-identical after spawn and converter.
- `squad-log-message`: 3-returns notice to Team Lead iff `team-lead` on team, else Manager (also on `none`, undecided, error, `size:`); text has no size word.
- Where the 3-returns notice shows (AC 12): stdout of the hook, one JSON line `{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"task N has 3 returns: ..."}}`; no file, socket or pane. Trigger: HANDIN (with `commit <sha>`) + FAIL on three distinct shas; only the 3rd FAIL prints; three FAILs on one sha count as one. Test: `test_the_notice_is_stdout_json_on_the_third_failing_sha_only`.
- Dry run with a pinned runtime lacking the script now warns and exits 1 like a real run (`test_a_dry_run_without_the_pins_*`, both scripts).
- A composed scope with `size:` and no `plugin:` line is refused with `scope.md:N: old format \`size:\`` + `squad-process adopt` (fix in `squadruntime.py` `cmd_runtime`); scopes with neither keep the pin text. Tests `test_a_composed_scope_with_size_and_no_pin_*`, both scripts.
- Pin-version / <0.6 / exec-guard block is duplicated in `squad-spawn` and `squad-respawn` on purpose: a shared sourced helper would live in the running engine and be missing from, or differ in, a pinned runtime; each script is standalone, and the two differ in the home variable, args and message.
- `squad-start:367`: Manager prompt says "propose the team".
- Lint baseline (G2b): `squad-process lint` on base 6389642 empty; branch empty; diff identical.
- Tests green: test_squad_spawn (85), test_squad_respawn (21), test_squad_log_message (22), test_squadruntime (64), test_squad_start (48), plus grep hits: crlf_squad_files, squad_ledger, squadsettings, team_lead_perms, team_models, utf8_helpers, windows_safe, team_lead_role, squad_usage_hook, squad_manager_guard, templates, instructions, architect_handoff, dev_rules_size, hooks_json, squadreport_digest.
- Changelog v9: no rule ID changed in this ticket.
