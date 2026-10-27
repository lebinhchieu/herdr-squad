# 14 Remove QA blackbox Read deny; stop `rm /tmp` prompts

## Behaviour
- Part 1: `qa-blackbox.json` has no `Read(//CODE_PATHS…)` deny. `squadsettings.py` lost PLACEHOLDER, `expand_code_paths`, the fail-closed error; a `codePaths` key in an old `*.local.json` is ignored (test: `{}`, `[]`, absolute, relative all resolve, no Read deny). `squad-process scaffold` and `squadadopt` no longer take `--code-path`; adopt drops old `Read(//…/**)` denies (retired). `squad-init` no longer asks. `--project-dir` still accepted by `squadsettings.py` (squad-spawn passes it), unused.
- SAFE-10 text: "no setting enforces this". SAFE-11: "Scratch dirs: `mktemp -d` only." Bytes (rule block incl. header): SAFE-10 313 -> 249 (-64, qa-blackbox only), SAFE-11 231 -> 227 (-4, dev/qa-white/qa-black). A Developer file frees 4 B from 14.
- Part 2: dev, qa-whitebox, qa-blackbox, manager, tech-lead, team-lead allow `Bash(rm -rf|rm -r|rm|rmdir /tmp/tmp.*)`. Live test (`claude -p`, `--settings`, default permission mode):
  - `rm -rf /tmp/tmp.t14a`: ran, no prompt.
  - `rm -rf /tmp/other-t14`: prompt (not run).
  - `rm -rf /tmp/tmp.t14b /tmp/other-t14` with allow only: RAN, deleted `/tmp/other-t14` (the glob `*` matches spaces). Hole found.
  - Fix: also `ask` `Bash(<cmd> /tmp/tmp.* *)` for the four commands. Re-test: same command prompts, `rm -rf /tmp/tmp.t14c /tmp/other-t14` prompts, `rm -rf /tmp/tmp.t14a` still silent. `/tmp/tmp.x/../y` is blocked by Claude itself ("path contains `..`").
  - Tech FAIL (cb9b925): `*` also matches `..`, `$(…)`, backticks. Added asks per command: `/tmp/tmp.*..*`, `*$*`, `` *`* `` (ask beats allow). Live, dev.json as `--settings`, victim dir `/tmp/zz-victim-t14` (empty, made for the test), all kept it:
    - `rm -rf /tmp/tmp.t14x/../zz-victim-t14`: prompt (not run).
    - `rm -rf /tmp/tmp.t14x; rm -rf /tmp/zz-victim-t14`: blocked on the 2nd part, nothing deleted.
    - `rm -rf /tmp/tmp.$(echo ../zz-victim-t14)`: prompt. `` rm -rf /tmp/tmp.`echo` ``: prompt.
    - `rm -rf "$(mktemp -d)"`: prompt (not run).
    - `rm -rf /tmp/tmp.t14abc`: ran, no prompt.
    - Globs: `rm -rf /tmp/tmp.t14*`, `/tmp/tmp.t14?`, `/tmp/tmp.t1[4]x` are refused by Claude itself ("Glob patterns are not allowed in write operations") with no ask entry of mine, so no glob asks added (a literal-`*` pattern is not needed). Known gap: this rests on Claude's own guard, not on our settings.
  - Test `test_scratch_rm_allowed_only_under_mktemp_dirs`: the six roles hold exactly the four allows, and each allow has the four paired asks (space, `..`, `$`, backtick); no other template has an `rm` allow; every rm allow contains ` /tmp/tmp.`.
- manager.json allows `Bash(squad-team:*)` (test `test_manager_allows_squad_team`).
- Changelog v9: SAFE-10, SAFE-11 appended to `changed:`.
- Ran green (grep -rl hits): advisor_rules, architect_handoff, dev_rules_size, model_effort_settings (retired Read deny allowed in the base-permissions check), sizes, squad_respawn, squadrules, squad_spawn, squad_start, team_cli, team_lead_role, templates, squadsettings, squadadopt. `squad-process lint`: empty, rc 0.
- QAW F1: adopt dropped `Read(//…/**)` denies of every role; now only qa-blackbox's (`settings_diff(..., role)`, `check_settings`). Test `test_read_deny_is_dropped_for_qa_blackbox_only`: dev keeps `Read(//home/u/.ssh/**)`, qa-blackbox drops its Read denies. test_squadadopt 30 OK.
