# 02 Scratch rm under /tmp/tmp.*: remove the ask entries

Status: ready-for-agent
Feature: update-not-deny (draft here; commit it to `.scratch/update-not-deny/issues/02-tmp-no-ask.md`)
Repo: /home/chieule/workspace/squad. Base: the passed sha of ticket 01 (same files; run after 01). Touches: `templates/squad/settings/{dev,qa-whitebox,qa-blackbox,manager,tech-lead,team-lead}.json`, `templates/squad/process/safety.md` (SAFE-11), `tests/test_squadsettings.py`, `tests/test_team_lead_perms.py`.
Duties: no Tech Lead, BA or QA on the team. Developer owns design notes, technical AC, `promote.md` (nothing to promote unless a rule text moves into CONTEXT.md/ADR; then say so) and the full suite. Business AC = this ticket as written. Hand in to the Manager (`HANDIN NN: ...`), who confirms `evidence.md` + `## Review` (starts with an AC trace table, one line per AC: `AC<n> | test or capture file | how run`). A risk flag, user-visible change or business doubt: `BLOCKED NN`.

## Why
PO: agents always get asked before working with `/tmp`; he does not want that. Today 16 `ask` entries per role (`rm -rf|rm -r|rm|rmdir /tmp/tmp.*` with `* *`, `*..*`, `*$*`, `*`*` tails) override the `allow` entries and prompt.

## What
Remove those 16 `ask` entries from the 6 role templates. Keep the 4 `allow` entries. Update the SAFE-11 text in `safety.md`: drop the "no `$`, backtick or `..`" prompt warning and the "(PO prompt)" reason; keep `mktemp -d` only, `cd` out before `rm`, one path per `rm`. Update the tests that assert the ask entries: `test_scratch_rm_allowed_only_under_mktemp_dirs` and `test_safe11_rm_examples_match_allow_and_no_ask` in `tests/test_squadsettings.py`, and `tests/test_team_lead_perms.py` if it asserts them. Change them to assert: the 4 allow entries remain, and no `/tmp/tmp.` entry is in `ask`. Do not widen `allow` beyond the 4 entries. If the ask list is left empty, leave `"ask": []` or drop the key, whichever the tests and the merge accept.

## AC
- AC1: No `Bash(rm*/tmp/tmp.*)` or `Bash(rmdir /tmp/tmp.*)` entry is in `ask` in any template.
- AC2: The 4 `allow` entries stay in the 6 roles, and no other role has an `rm` allow.
- AC3: SAFE-11 matches; `squad-process lint` passes; every test found by `grep -rl 'SAFE-11\|tmp\.\*' tests/ templates/ bin/` passes.
- AC4: `test_safe11...` still proves that `rm -rf /tmp/tmp.A` is allowed and not asked.

## Evidence
Effective settings of one role (command + output) show no `/tmp/tmp.` entry in `ask`.

## Comments
