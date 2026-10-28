# INT4 QA whitebox (964c443, merge 11 ca53ba7 + 14 b2ee4e5 on 90be196)
- Merge fidelity: every non-.scratch file changed by only 11 or only 14 equals that branch's version at 964c443; only `skills/squad-process-update/changelog.md` is touched by both; every line of both changelogs is in the merge, none extra, one v9 block.
- Lint exit 0. 16 targeted test modules (dev_rules_size, sizes, squadsettings, instructions, process_conversion, squadadopt, squadrules, advisor_rules, architect_handoff, model_effort_settings, manager_m_l, pod_contact_routes, pod_rules_process, team_lead_role, suite_rules_process, squadruntime): 344 OK, 11 skips (base shas not in the `git archive` clone: test_sizes v7 base, model_effort c1be501).
- 512 Dev composes worst 5113 (<=5120). Composed output differs vs ca53ba7 only for dev, qa-blackbox, qa-whitebox (14's SAFE-11 text), no rule moves.
- Verdict: pending Tech Lead's final sha (REV-3).

## Delta 964c443..2175bd2 (test-only)
- tests/test_team_lead_perms.py +1 line: TL_ALLOW gains the 4 `rm`/`rmdir /tmp/tmp.*` entries, equal to team-lead.json allow (line 8). No code change. test_team_lead_perms, squadsettings, dev_rules_size, sizes: 78 OK.
- Verdict pending Tech's final sha.
