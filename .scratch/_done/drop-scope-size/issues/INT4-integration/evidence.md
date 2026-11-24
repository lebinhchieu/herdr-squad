# Evidence: INT4 integration of 11 + 14
base 90be196 (INT3); merged in order: 11 (d8b4738, code ca53ba7), 14 (7c8af4a, code b2ee4e5).

## Behaviour
- 11: merged clean (no conflicts).
- 14: one conflict, `skills/squad-process-update/changelog.md` (v9 appends): kept both sides (11's rows, then 14's SAFE-10, SAFE-11 rows). No other conflicts.
- Stale-test fix (e265fd7, after Tech FAIL): `tests/test_team_lead_perms.py` TL_ALLOW gains 14's 4 entries (`Bash(rm /tmp/tmp.*)`, `rm -r`, `rm -rf`, `rmdir`) because team-lead.json carries them. Only edit beyond conflict resolution. Re-run: that file 9 OK, plus every `templates/squad/settings` grep hit (squadsettings, team_lead_role, instructions, architect_handoff, model_effort_settings, squad_respawn, squadadopt, squad_spawn) OK, and test_templates, ca_launchers, squad_start, team_models, squad_log_message OK.
- Tests on merged result: test_dev_rules_size 11 OK; test_sizes 34 OK; test_squadsettings 24 OK; test_instructions 30 OK; test_process_conversion 14 OK; also test_squadadopt 30, test_model_effort_settings 4 (1 skip), test_squadrules 59, test_squadcompose 85, test_squadruntime 64, test_pod_contact_routes 7, test_qab_optional 11 OK. `squad-process lint`: exit 0, empty.
- Full suite not run by me (Tech Lead owns it, `--if-changed 90be196`).

## QA whitebox

### INT4 QA whitebox (964c443, merge 11 ca53ba7 + 14 b2ee4e5 on 90be196)
- Merge fidelity: every non-.scratch file changed by only 11 or only 14 equals that branch's version at 964c443; only `skills/squad-process-update/changelog.md` is touched by both; every line of both changelogs is in the merge, none extra, one v9 block.
- Lint exit 0. 16 targeted test modules (dev_rules_size, sizes, squadsettings, instructions, process_conversion, squadadopt, squadrules, advisor_rules, architect_handoff, model_effort_settings, manager_m_l, pod_contact_routes, pod_rules_process, team_lead_role, suite_rules_process, squadruntime): 344 OK, 11 skips (base shas not in the `git archive` clone: test_sizes v7 base, model_effort c1be501).
- 512 Dev composes worst 5113 (<=5120). Composed output differs vs ca53ba7 only for dev, qa-blackbox, qa-whitebox (14's SAFE-11 text), no rule moves.
- Verdict: pending Tech Lead's final sha (REV-3).

#### Delta 964c443..2175bd2 (test-only)
- tests/test_team_lead_perms.py +1 line: TL_ALLOW gains the 4 `rm`/`rmdir /tmp/tmp.*` entries, equal to team-lead.json allow (line 8). No code change. test_team_lead_perms, squadsettings, dev_rules_size, sizes: 78 OK.
- Verdict pending Tech's final sha.

## QA blackbox

### QA blackbox, INT4 (HANDIN 964c443, branch squad/plugin/drop-scope-size/plugin-dev-dsz-int4: 11 + 14 on 90be196)

Method: CLI only. `git archive 964c443` to scratch; scratch homes (`scope.md` with `plugin: 0.6.0 abc1234`, `team:`); `squad-process compose` for 9 roles; `lint`; 512-compose Developer sweep; composed text diffed against 90be196 and ca53ba7 (11 final).

| Check | Saw | Result |
|---|---|---|
| Compose 9 roles x 12 team shapes (as INT3) | 0 compose failures | PASS |
| `lint` per shape | empty | PASS |
| AC 24 sweep, 128 teams x goal x qa | 512/512 OK, max Developer file 5034 B, 0 over 5120 | PASS |
| 11 content kept | REV-22a "Give the review subagent ... to check the diff conforms."; EVID-2b "After all `PASS`:"; changelog rows for both | PASS |
| 14 content kept | SAFE-10 "no setting enforces this", SAFE-11 "Scratch dirs: `mktemp -d` only" in qa-blackbox/dev files; changelog rows for SAFE-10, SAFE-11 | PASS |
| INT4 vs ca53ba7 composed text | only the SAFE-10 / SAFE-11 lines differ (14's change) on 3 shapes | PASS |
| Changelog v9 merge | rows of 11 and 14 both present, no conflict markers | PASS |

Findings: none. Verdict waits for the Tech Lead's final sha (REV-3).

#### Re-check, 2175bd2 (delta from 964c443)
Diff: tests/test_team_lead_perms.py (+1) and the ticket evidence.md only. Compose of 9 roles on 3 shapes (none, tech-lead+qa-white, full 7-role team): bodies byte-identical to 964c443 (header scope name and timestamp excluded); lint empty. Saved composes: /tmp/qab-int4-composes/. Findings: none. Verdict waits for the Tech Lead's final sha.
