# QA whitebox 05 — PASS on 9ffa44f (code 6d33099)
Checked in worktree plugin-dev-dsz-5 (read-only).
- Tests (cd tests; unittest): test_sizes 34, test_manager_m_l 9, test_qab_optional 11 (2 skipped, ticket 07), test_architect_handoff, test_pod_rules_process, test_instructions, test_team_duties, test_squadcompose, test_squadadopt, test_process_history, test_processlint, test_team_lead_role, test_squadprocess, test_squadupgrade, test_windows_safe, test_crlf_squad_files: all OK.
- Lint: exit 0, empty (= base). G4: `\bsize\b(?!-\d)` in sizes.md/teams.md: none. G5: 10 tombstones with why:/replaced_by:, changelog v9 per ID with reasons; kept IDs justified by live citations (D2).
- Live compose (REV-5b-style, real engine) for teams full / qa-white / none / qa-black / team-lead+tech-lead: rule sets per role match the duties line (e.g. qa-white only: TEAM-1, TEAM-4, SIZE-5a/6a/6c; none: TEAM-3, SIZE-7a/8a; full: SIZE-2, 5b, 6b absent from Manager). No rule acts for an absent role (TEAM-1..3 broadcast, accepted).
- R9: 5 `qa-b` `when:` lines in sizes.md retargeted; 18 remain in review/evidence/lifecycle/spawning, owned by 07/08 (their tickets carry R9). Not a finding here.
- Fixture edits outside file list (test_squadadopt, test_architect_handoff, test_pod_rules_process): forced by retargets, TL accepted.
Forward notes: 07 re-enable 2 skipped test_qab_optional tests; 10 owns the `squad-team` pointer (SIZE-13/TEAM-7); SIZE-18 now `plan-owner = team-lead` (was size L).
