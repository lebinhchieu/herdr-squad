# Task 05: Scratch dirs without a PO prompt (plugin level)

Status: ready (waits for 01's passed sha: both touch `skills/squad-process-update/changelog.md`; branch from it)
Duties: plan-owner=manager, design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=manager, choice-owner=tech-lead
Team: tech-lead, qa-white, qa-black. Suite: `python3 tests/run_suite.py --receipt <dir> --if-changed <base>` (CLAUDE.md Running tests); full suite by Tech Lead on final sha. Branch from repo HEAD (main) unless noted. Hand in to both QAs. A risk flag or user-visible change found: `BLOCKED <task>`.
Goal: scope brief `../scope.md`, plan `../iterations/1.md`.

## Problem (PO, 2026-10-28)
`rm` on a scratch dir in /tmp makes the PO accept each time. The PO wants it fixed in the plugin for every squad, not only this one.
Known cause to verify (Tech Lead): `templates/squad/settings/*.json` allow `rm ... /tmp/tmp.*` but ask on `*$*` (`test_squadsettings.test_scratch_rm_allowed_only_under_mktemp_dirs`), and SAFE-11 itself tells agents to write `rm -rf "${VAR:?}"`: the `$` matches the ask pattern, so the rule's own form prompts.

## Interim (Manager, already done for this squad only)
`process.local.md` replaces SAFE-11: scratch under `<project>/.worktrees/scratch` via `mktemp -d -p`, never /tmp. When this task passes, remove that overlay op (its `@hash` goes stale) and log it.

## Touches (Tech Lead confirms, LC-9)
`templates/squad/process/safety.md` (SAFE-11), `templates/squad/settings/*.json` allow/ask for `rm`/`rmdir`, `skills/squad-process-update/changelog.md` (one entry), tests `test_squadsettings`, `test_dev_rules_size`, `test_team_lead_role` (SAFE-11 hash row), and any allow-list/golden grep hits.

## AC
Tech Lead decides the design (scratch location + rm form + permission patterns that agree, no `$` conflict, no widening of `rm` beyond the scratch folder) and writes technical AC in Design notes. Business AC: an agent following SAFE-11 creates and removes its scratch dir with no PO prompt. QA blackbox verifies with a real settings check (`claude`-side permission match, or the matcher the plugin uses) on the exact command SAFE-11 prescribes. Plugin version stays 0.6.0.

## Design notes (Tech Lead, 2026-10-28)
**Cause re-checked live (not as suspected).** `claude -p --settings templates/squad/settings/dev.json`, default and `--permission-mode auto`, haiku, one command per run, `permission_denials` counted:
- No prompt: `D=/tmp/tmp.X; rm -rf "${D:?}"` (SAFE-11's own form: it starts with `D=`, so no `rm` ask pattern matches), `D=$(mktemp -d); ...; cd /; rm -rf "${D:?}"`, `rm -rf /tmp/tmp.X`, `rm -rf /tmp/tmp.X/s`, `rm -rf /tmp/tmp.X && echo "rc=$?"`, `rm -rf /tmp/tmp.X 2>&1`, `rm -rf /tmp/tmp.A && rm -rf /tmp/tmp.B` (ask patterns match per subcommand), `cd /tmp && rm -rf tmp.X`, `rm /tmp/file.py`.
- Prompt (ask pattern hit, target survives): `rm -rf /tmp/tmp.A /tmp/tmp.B` (two paths, `* *`), `rm -rf /tmp/tmp.X/"${f:?}"` (`$` after the prefix), `rm -rf /tmp/tmp.C <path outside /tmp>`.
So the prompt comes from an `rm` whose text starts `rm -rf /tmp/tmp.` and carries a 2nd path, `$`, backtick or `..`. The PO's exact prompted command is unseen: Manager asks the PO for one (or the pane text) before 05 closes; design below holds either way.

**Decision: keep /tmp, fix the rule text, pin it with a test. No settings change, no widening.** `.worktrees/scratch` rejected: the allow globs would need the absolute project path (templates are per plugin; squadsettings no longer takes a project dir since task 14), i.e. the codePaths machinery again, and an in-project `rm` has no allow entry (only the auto classifier let it through, unverified).

New SAFE-11 (roles dev, qa-whitebox, qa-blackbox; `topic: safety`), about 300 B:
`Scratch dirs: `mktemp -d` only. `cd` out before `rm` (Claude blocks the cwd or a parent). One literal path per `rm`: `rm -rf /tmp/tmp.AbC123`; several dirs: `rm -rf /tmp/tmp.A && rm -rf /tmp/tmp.B`. Never two paths, `$`, backtick or `..` in one `rm`: that prompts the PO. A variable is safe only as `rm -rf "${D:?}"` alone, after `D=...;`.`
(Developer may tighten wording; every example must pass the AC test.)

Touches (LC-9): `templates/squad/process/safety.md` SAFE-11; `skills/squad-process-update/changelog.md` one entry (check 01's final form first: branch from 01's passed sha 7c41807 + QA PASS); tests `test_squadsettings` (new), `test_dev_rules_size` and `test_team_lead_role` (SAFE-11 hash/size rows), grep hits. NOT touched: `templates/squad/settings/*.json`, `process.local.md` (Manager removes the SAFE-11 overlay op after PASS, logs it; plugin 0.6.0 stays).

Compat (LC-12): rule text only; squads with SAFE-11 pinned see a `changed` plan item via `squad-process upgrade --check`; no data, API or deploy-order change. Deploy: PO merges with the scope, nothing else.

## Technical AC
T1 SAFE-11 text as above: every backticked `rm ...` example in it is literal `/tmp/tmp.<name>`, one path, no `$`/backtick/`..`, except the one `"${D:?}"` form.
T2 New test in `test_squadsettings`: read SAFE-11 from `templates/squad/process/safety.md`, extract its backticked `rm` commands, split on `&&`/`;`, and for each of the six roles' settings (dev, qa-whitebox, qa-blackbox, manager, tech-lead, team-lead; only dev/qa-w/qa-b receive SAFE-11, but the same allow/ask set) assert: it matches an `allow` `Bash(...)` glob (`*` = anything) and no `ask` glob; `"${D:?}"` form (after `D=...;` prefix is stripped) matches no `ask` glob. Also a negative control: `rm -rf /tmp/tmp.A /tmp/tmp.B` matches an `ask`.
T3 `templates/squad/settings/*.json` byte-identical to 01's passed sha (`git diff --stat` empty for them); `test_scratch_rm_allowed_only_under_mktemp_dirs` unchanged and green.
T4 Size: composed dev rules stay within `test_dev_rules_size`; report SAFE-11 byte delta per role. Hash rows in `test_team_lead_role` updated.
T5 Changelog entry (next heading format, one `changed: SAFE-11` line + `why:`); `squad-process lint` empty rc 0; `upgrade --check` on a pin of the old SAFE-11 lists SAFE-11 as changed.
T6 Developer live check (like task 14, evidence.md): `claude -p --settings templates/squad/settings/dev.json`, default and `--permission-mode auto`, scratch dirs from `mktemp -d`, the exact SAFE-11 examples: 0 denials, dir gone; and 2-path, `$`-after-prefix, `..` forms: 1 denial, target survives.
T7 Tests: touched files + grep hits per CLAUDE.md; full `--tz` suite by Tech Lead on the final sha.
Business AC check (QA blackbox): repeat T6 independently on the exact command SAFE-11 prescribes, per role file.
