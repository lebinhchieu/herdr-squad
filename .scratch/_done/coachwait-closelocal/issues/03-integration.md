# 03 Integration: merge 01 and 02
Status: ready-for-agent
Type: task

Duties: cite [GOAL-6b] integration, [REV-13b] hand-in, [EVID-2d] evidence. Do no feature work. Commit this file as the ticket at `.scratch/coachwait-closelocal/issues/03-integration.md`.

Branch starts at 01's passed sha eb78476 (`--base`). Merge `squad/plugin/coachwait-closelocal/plugin-dev-cwcl-2` (passed sha e75a519) with `git merge --no-ff`. Resolve conflicts only if trivial and say which; any non-trivial conflict: `BLOCKED 03`. Run the targeted tests for the changed files (tests/test_squad_close.py, tests/test_squad_spawn.py and the rules tests task 02 touched). Do NOT run the full suite (QA whitebox does, with `--tz`, on your sha). Clean tree, no untracked files. `HANDIN 03: sha <sha>` to plugin-qaw-cwcl and plugin-mgr-coachwait-closelocal; no evidence beyond a short `evidence.md` with the merge command output and test receipts.
Business AC: the merged tree holds both changes unchanged (`git diff e75a519 HEAD -- <02's files>` and `git diff eb78476 HEAD -- <01's files>` empty).
