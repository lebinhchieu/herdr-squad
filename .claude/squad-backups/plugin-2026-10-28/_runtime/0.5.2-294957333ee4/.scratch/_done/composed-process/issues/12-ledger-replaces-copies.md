Status: ready-for-agent
Type: task
Task ID: 12
Touches: `bin/squad-ledger` (new), `bin/squadledger.py` (new), `bin/squad-log-message` (task ID parse + 3-return notice), `templates/squad/process/messages.md`, `templates/squad/process/lifecycle.md`, `tests/test_squad_ledger.py` (new), `tests/test_squad_log_message.py`
Does not touch: `agents/*`, `hooks/hooks.json` (the existing PostToolUse SendMessage entry is reused)
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_ledger test_squad_log_message test_task_id_rule test_windows_safe`
Blocked by: 03, 06

# 12: A ledger instead of copies; the 3rd return raises itself

**Done when the Team Lead no longer receives copies of HANDIN, PASS and FAIL, can read every task's state with `squad-ledger`, and the 3rd FAIL on a task tells its sender to raise it.**

## Why
- Research (Claude Code costs doc): a message to an idle session starts a turn that resends its whole context. The Team Lead is copied on every HANDIN, PASS and FAIL, and `team-lead.md` itself says it "will cross 120k".
- Review finding 5: IV-03 reached 4 returns with nobody stepping in.

## What
- **`squad-ledger [--home <dir>] [--task NN] [--json]`** reads `messages.jsonl` and prints, per task:
  - last HANDIN sha and branch;
  - verdict per checker on that sha;
  - number of returns (FAIL messages);
  - open BLOCKED messages;
  - rounds on the current ASK thread.
- **Fix in `squad-log-message`:** the task ID is the bare ticket number after the type (`HANDIN 03:`), per the Task ID rule. Today the regex only catches `ABC-12` forms, so `task` is null for bare numbers. Keep the old form as a fallback.
- **3-return notice:** when a FAIL is the 3rd for its task, the hook returns a notice to the sender: "task NN has 3 returns: also send `BLOCKED NN: 3 returns` to <Team Lead; S: Manager> [LC-n]".
- **Rules:** HANDIN, PASS and FAIL go to the Developer and the checkers only. The Team Lead runs `squad-ledger` when it acts: on its own messages, on health checks and at iteration end. The iteration summary takes returns and passed shas from the ledger.

## Technical AC
1. Fixture `messages.jsonl` with two tasks, one with 3 FAILs, one with a re-HANDIN on a new sha: the ledger output matches the expected table and JSON.
2. `HANDIN 03:`, `HANDIN SET-13:` and `FAIL 3:` all parse to their task IDs. Text with no task gives null.
3. The notice fires exactly on the 3rd FAIL for a task, not the 2nd or the 4th.
4. The hook still always exits 0 (a logging problem never interrupts).
