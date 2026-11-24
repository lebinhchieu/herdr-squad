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

## QA whitebox

### QA whitebox 14 on cb9b925
FAIL (1 finding).

#### F1 adopt drops any `Read(//…/**)` deny from every role, not only the retired QA blackbox code-path denies (regression, security)
- bin/squadadopt.py:266-267 (`settings_diff`) and :324-326 (`check_settings`): `_CODE_ENTRY = ^Read\(//+(.+)/\*\*\)$` is applied to the `permissions.deny` list of every role, with no role/placeholder guard. Base 90be196 only did this when the template carried the placeholder (qa-blackbox).
- Repro (own script /tmp/qaw14_t.py): dev template + old file with `Read(//home/u/.ssh/**)` in deny. 90be196: local overlay = `{'permissions': {'deny': ['Read(//home/u/.ssh/**)']}}`. cb9b925: local = `{}`, `check_settings` problems = `[]` (not even reported as "would be lost"). So `squad-process adopt` of a v6 squad silently removes a project's own Read denies on dev, qa-whitebox, tech-lead, etc. Also affects `.worktrees` code-path entries only by chance; the point is any `Read(//…/**)`.
- Why it matters: adopt promises "nothing lost / PO items for anything it cannot map"; a lost security deny with no report breaks it.
- What would pass: drop the pattern only for the qa-blackbox role (or only entries that the old qa-blackbox file generated from codePaths: absolute code-folder reads), keep it for every other role; a test with a `Read(//…/**)` deny in dev's old file that must reach `dev.local.json` (or be listed), and the same entry in qa-blackbox that is dropped.

#### Checked OK
- Targeted tests from `git archive cb9b925`: test_squadsettings, test_squadadopt, test_model_effort_settings, test_templates, test_squad_spawn, test_squadrules, test_squad_start, test_sizes, test_dev_rules_size: 303 run, 1 failure `test_the_pinned_scope_md…` (archive is not a git checkout: "cannot pin the running plugin"); test_squad_spawn 87 OK in the real worktree. Lint exit 0 empty.
- qa-blackbox.json Read deny gone; `codePaths` in an old local file ignored, never fails; templates: 6 roles hold the 4 rm allows and 4 `/tmp/tmp.* *` asks, no other template has an rm allow; manager allows `squad-team:*`; SAFE-10/SAFE-11 text and changelog v9 `changed:` lines present; SAFE-11 smaller (-4 B).
- Dev worktree has uncommitted edits to templates/squad/settings/{dev,manager,qa-blackbox}.json after HANDIN: I tested the committed cb9b925 only.

#### Re-check on 8d9e931
FAIL: F1 unchanged (diff cb9b925..8d9e931 touches only the 6 settings templates, test_squadsettings, evidence; squadadopt.py not changed). Repro on 8d9e931: dev old file with `Read(//home/u/.ssh/**)` -> local {} and check_settings []. Rest: test_squadsettings, test_squadadopt, test_model_effort_settings, test_templates 67 OK; lint 0; new ask entries (`..`, `$`, backtick, per rm command) present in all 6 templates and the test pins the set.

#### Verdict on final b2ee4e5
PASS. Delta 8d9e931..b2ee4e5: squadadopt.py role-gated (settings_diff role arg, check_settings) + test_read_deny_is_dropped_for_qa_blackbox_only. Own repro: dev old file with a Read(//…) deny keeps it in the local overlay; qa-blackbox drops it; check_settings clean for both. test_squadsettings, test_squadadopt, test_model_effort_settings, test_templates, test_sizes, test_dev_rules_size: 111 OK (15 skip); lint 0. F1 closed.

## QA blackbox

### QA blackbox, task 14 (final b2ee4e5; handed in cb9b925, 8d9e931, b2ee4e5)

Method: (1) `squadsettings.effective()` per role on a scratch squad with `settings/<role>.local.json` overlays; (2) live `claude -p --settings templates/squad/settings/qa-blackbox.json` (haiku, default permission mode), one Bash command per run, count of `permission_denials` and whether the target survived; (3) `compose` + `lint`.

| Check | Saw | Result |
|---|---|---|
| Effective qa-blackbox settings: no Read deny | `Read deny: []` with empty overlay | PASS |
| Old overlay `codePaths` (list / bad string) | ignored, never fails, no code key in result; other overlay allows kept; an overlay's own Read deny still merged | PASS |
| rm allow entries in dev, qa-white, qa-black, manager, tech-lead, team-lead | 4 each (`rm -rf`, `rm -r`, `rm`, `rmdir` on `/tmp/tmp.*`); token-coach/ba/designer/architect none; token-coach keeps its own Read denies | PASS |
| `Bash(squad-team:*)` in manager.json | present | PASS |
| Live: `rm -rf <mktemp -d>` | 0 denials, dir gone | PASS |
| Live: `rmdir <mktemp -d>` | 0 denials, dir gone | PASS |
| Live: `rm -rf /tmp/tmp.X/../other/zz`, `rm -rf /tmp/other`, `rm -rf /tmp/tmp.X /tmp/other/zz`, `rm -rf /tmp/tmp.$(...)`, `rm /tmp/file`, `A ; touch B` | each 1 denial, target survived, nothing ran | PASS |
| SAFE-10 text | "no setting enforces this"; rule kept | PASS |
| SAFE-11 text | "Scratch dirs: `mktemp -d` only." one line | PASS |
| `lint` | empty | PASS |

Findings: none. Not tested: a full qa-blackbox session reading `$SCOPE_DIR` files (the Manager removes the interim local overlay after merge; my own session still runs the old deny).
