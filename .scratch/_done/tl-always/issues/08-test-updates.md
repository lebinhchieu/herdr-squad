# 08 Update two test files to match tasks 02 and 03 (returns on 03 and 02)
Status: handed-in
Duties: plan-owner=team-lead, design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=manager, choice-owner=tech-lead
Files: tests/test_squad_ledger.py, tests/test_squad_spawn.py
Evidence: .scratch/tl-always/issues/08-test-updates/evidence.md
Branch: squad/plugin/tl-always/plugin-dev-tl-always-07 (worktree reused, base 6b604e4). Commit on top.
Source: evidence/suite-triage.md, section "New on 6b604e4", items 1 and 2.

## Change (test-only, no bin/ or templates/ edits)
1. tests/test_squad_ledger.py NoticeTest: expect `to Team Lead [LC-7b]` (bin/squad-log-message, task 03, 60b2987), not `to Manager [LC-7c]`.
2. tests/test_squad_spawn.py: SpawnTaskPromptTest test_a_no_qa_team_hands_in_to_the_team_lead_else_the_manager and SpawnTeamGateTest test_a_role_not_on_the_team... subcase role=team-lead. The Team Lead is always on the team now (task 02, 4dda3e0): rewrite the expectations to the passed behaviour (team-lead spawn is accepted; no-team-lead rosters exit 2 "roster.md has no team-lead row"). Keep the other subcases (tech-lead, qa-blackbox, designer, architect); they failed only from leftover files.
Different files, no overlap. Do not touch the known base failures.

## Verify
Run only: tests/test_squad_ledger.py, tests/test_squad_spawn.py (touched), plus `grep -rl` hits for changed strings over tests/. No full suite. `rm -rf bin/__pycache__` if test_squadinbox no_pyc flakes.
Evidence: .scratch/tl-always/issues/08-test-updates/evidence.md in the worktree; run `squad-evidence check --base 6b604e4` and quote the exit code.
HANDIN to plugin-qaw-tl-always and plugin-qab-tl-always (both QAs, respawned by the Team Lead): sha. Do not run the full suite.
