# Task 12: Suite policy: targeted by default, ask Chieu before a full suite

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes later); full suite: QA whitebox, only after Chieu agrees (this scope's own rule; the Manager asks him). A risk flag, user-visible change or business doubt: `BLOCKED NN`. Run `grep -rl` over `tests/` for each changed string or path and run every hit (CLAUDE.md "Running tests"). `## Review` starts with an AC trace (SQ-2), one line per AC: `AC<n> | test or capture file | how run`.

Status: handed in
Source: Chieu E14: prefer targeted tests; the full suite only after asking the PO with an explanation; each project often redefines this, so `project.md` may set the default.
Files: templates/squad/process/suites.md, CLAUDE.md ("Running tests"), .claude-plugin/plugin.json (version), tests that quote the changed rules or pin the version (`tests/test_rules_contract.py`, `tests/test_rules_wording.py`, `tests/test_team_cli.py`, `tests/test_squadscaffold.py`, others by grep)
Ticket: commit this file's content as `.scratch/process-fixes/issues/12-suite-policy.md` in your first commit.
Base: your worktree after task 11. No merge.

## AC
- AC1 Every rule in suites.md that tells someone to run the full suite (SUITE-1, 1b, 2d, 3, 3b, 4, 4b) says: the default is targeted tests (touched files plus `grep -rl` hits); the full suite runs only after the owner has asked Chieu through the Manager and he said yes; `project.md` may redefine the default. Keep each rule short; do not copy the same sentence 7 times: put the whole statement once (SUITE-1 and 1b; the others point to it by [ID]).
- AC2 How to ask: the suite owner sends the Manager `ASK <task>: full suite? <why targeted tests are not enough>`; the Manager puts it in the inbox (ITER-4); nobody runs the full suite before the answer. Name this in one place only.
- AC3 What stays: the `templates/` and `bin/` text grep rule; `--tz` for the sha Chieu merges stays a full run (he is asked at the merge).
- AC4 `CLAUDE.md` "Running tests" matches AC1-AC3 (first bullet, runner bullet). Do not change the other bullets.
- AC5 Version 0.7.4 to 0.7.5 (SQ-5): `grep -rn '0\.7\.4' . --exclude-dir=.git --exclude-dir=.worktrees --exclude-dir=_runtime --exclude-dir=.claude` shows no remaining 0.7.4 outside history; tests that pin the version updated.
- AC6 Touched tests plus grep hits pass. Do NOT run the full suite: QA whitebox asks Chieu first.
