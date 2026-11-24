# 10 Evidence-only commits must not show `sha changed after PASS`

Status: ready-for-agent
Blocked by: 04 (start from 04's passed branch; shared tests)

After a task passes, the Developer commits `evidence.md`, so the branch tip differs from the passed sha and the board shows `sha changed after PASS` for every task. Fix it on the read side. In `bin/squadboard_tasks.py`: when `tip != sha` and sha is an ancestor of tip, run `git diff --name-only sha tip`; if every path is in the ticket's evidence folder, the tip counts as matching. No new event; no change in `bin/squadtask.py` (store format frozen, design.md s2).

Also fix two stale `ready for review` docstrings (comment-only): bin/squadboard_inbox.py:12 and bin/squadtask.py:178.

Files: bin/squadboard_tasks.py, tests/test_squadboard_tasks.py, bin/squadboard_inbox.py, bin/squadtask.py (docstrings only)
Technical AC: T25, T26 (design.md s6.1). Read design.md s6.1 first.
Tests: targeted only (repo CLAUDE.md); one test per AC.
Tech Lead reviews it at HANDIN himself.
