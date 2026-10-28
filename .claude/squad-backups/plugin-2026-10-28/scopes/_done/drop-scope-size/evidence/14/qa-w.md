# QA whitebox 14 on cb9b925
FAIL (1 finding).

## F1 adopt drops any `Read(//…/**)` deny from every role, not only the retired QA blackbox code-path denies (regression, security)
- bin/squadadopt.py:266-267 (`settings_diff`) and :324-326 (`check_settings`): `_CODE_ENTRY = ^Read\(//+(.+)/\*\*\)$` is applied to the `permissions.deny` list of every role, with no role/placeholder guard. Base 90be196 only did this when the template carried the placeholder (qa-blackbox).
- Repro (own script /tmp/qaw14_t.py): dev template + old file with `Read(//home/u/.ssh/**)` in deny. 90be196: local overlay = `{'permissions': {'deny': ['Read(//home/u/.ssh/**)']}}`. cb9b925: local = `{}`, `check_settings` problems = `[]` (not even reported as "would be lost"). So `squad-process adopt` of a v6 squad silently removes a project's own Read denies on dev, qa-whitebox, tech-lead, etc. Also affects `.worktrees` code-path entries only by chance; the point is any `Read(//…/**)`.
- Why it matters: adopt promises "nothing lost / PO items for anything it cannot map"; a lost security deny with no report breaks it.
- What would pass: drop the pattern only for the qa-blackbox role (or only entries that the old qa-blackbox file generated from codePaths: absolute code-folder reads), keep it for every other role; a test with a `Read(//…/**)` deny in dev's old file that must reach `dev.local.json` (or be listed), and the same entry in qa-blackbox that is dropped.

## Checked OK
- Targeted tests from `git archive cb9b925`: test_squadsettings, test_squadadopt, test_model_effort_settings, test_templates, test_squad_spawn, test_squadrules, test_squad_start, test_sizes, test_dev_rules_size: 303 run, 1 failure `test_the_pinned_scope_md…` (archive is not a git checkout: "cannot pin the running plugin"); test_squad_spawn 87 OK in the real worktree. Lint exit 0 empty.
- qa-blackbox.json Read deny gone; `codePaths` in an old local file ignored, never fails; templates: 6 roles hold the 4 rm allows and 4 `/tmp/tmp.* *` asks, no other template has an rm allow; manager allows `squad-team:*`; SAFE-10/SAFE-11 text and changelog v9 `changed:` lines present; SAFE-11 smaller (-4 B).
- Dev worktree has uncommitted edits to templates/squad/settings/{dev,manager,qa-blackbox}.json after HANDIN: I tested the committed cb9b925 only.

## Re-check on 8d9e931
FAIL: F1 unchanged (diff cb9b925..8d9e931 touches only the 6 settings templates, test_squadsettings, evidence; squadadopt.py not changed). Repro on 8d9e931: dev old file with `Read(//home/u/.ssh/**)` -> local {} and check_settings []. Rest: test_squadsettings, test_squadadopt, test_model_effort_settings, test_templates 67 OK; lint 0; new ask entries (`..`, `$`, backtick, per rm command) present in all 6 templates and the test pins the set.

## Verdict on final b2ee4e5
PASS. Delta 8d9e931..b2ee4e5: squadadopt.py role-gated (settings_diff role arg, check_settings) + test_read_deny_is_dropped_for_qa_blackbox_only. Own repro: dev old file with a Read(//…) deny keeps it in the local overlay; qa-blackbox drops it; check_settings clean for both. test_squadsettings, test_squadadopt, test_model_effort_settings, test_templates, test_sizes, test_dev_rules_size: 111 OK (15 skip); lint 0. F1 closed.
