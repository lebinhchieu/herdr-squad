# Evidence: 11 the Manager hears its own context size

**`squad-manager-guard` (PreToolUse, Bash) adds one `context <n>k` notice to the result of a Manager's `squad-spawn` / `squad-inbox add`; COST-8 says what to do; the Stop-hook exemption stays. Delivery path verified live: `hookSpecificOutput.additionalContext` reaches a Haiku Manager. Developer rules byte delta 0.**

Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_manager_guard test_hooks_json test_squad_usage test_windows_safe` OK. Also (146 OK together): test_dev_rules_size, test_process_conversion, test_processlint, test_pod_rules_process, test_process_citations, test_task_id_rule, test_suite_rules_process, test_templates. `squad-process lint` clean (COST-8 is 59 words, limit 60).
sha: see the HANDIN. Old-form evidence folder (ticket 21 is not in this branch); integration moves it.

## Behaviour

**Delivery path (ticket "not verified")**: `hookSpecificOutput.additionalContext` on stdout, exit 0, **works**; `systemMessage` not needed. Live probe (Haiku, cap $0.10, `--max-budget-usd 0.10`), temp squad with a stub `squad-usage` (summarize → last ctx 150000) and a stub `squad-spawn` on PATH, hook wired by `--settings`:
`SQUAD_ROLE=manager SQUAD_NAME=mgr SQUAD_DIR=… SCOPE_DIR=… PATH=<tmp>/bin:$PATH claude -p --model haiku --settings <tmp>/settings.json --permission-mode bypassPermissions --max-budget-usd 0.10 "Run exactly this bash command: squad-spawn probe-1. Then answer in one line: did the tool result or any hook context mention a context size and a squad-respawn? Quote the notice text exactly if so, else say NONE."`
Answer: `YES. Hook context: "context 150k (over 100k): after this step write your notes and run squad-respawn mgr [COST-8]". I did not run squad-respawn.`
The scope's `usage-events.jsonl` got `{"agent":"mgr","role":"manager","session":"a3e9…","rule":"manager-ctx","action":"write roles/mgr.notes.md, then run: squad-respawn mgr"}`. (Tech AC3)

**Tech AC1 / BA AC1-3, 6** `test_squad_manager_guard.DecisionTable` (+ `CliTest`):
- over 100k → one notice naming size, `squad-respawn <name>`, `[COST-8]`; a second call in the same session (either command) → none; a new session → notice again.
- under 100k with a fresh cache → none; the 8 non-manager roles and no role → none; `ls`, `squad-inbox list`, `squad-spawner`, `echo squad-spawn`, `squad-respawn`, empty → none. For these the output is empty and exit 0 (`test_no_notice_means_empty_output`): identical to no hook.
- The call is never blocked: output has no `permissionDecision`, exit 0, stderr empty.

**BA AC4 (compaction, cache expiry)**: simulated with fixture transcripts (no stub needed; the guard reads the same transcript summary `squad-usage` uses): a `compact_boundary` line → notice "after a compaction", once; a second compaction → a new event; a 195 min gap plus a big cache write → "cache expired" once under 100k; a last turn 2 h ago (cache gone, no new turn yet) → once. Each event key is logged (`manager-ctx`, `manager-compaction-N`, `manager-expiry-N`) in `usage-events.jsonl` of `$SCOPE_DIR`, else `$GOAL_DIR` (goal Manager tested), else `$SQUAD_DIR`.

**Tech AC2 / BA AC5** forced failures, all exit 0 and silent: missing `squad-usage` (guard copied to a bin without it), unparsable/empty/`[1]`/`null` payload, unreadable transcript, missing transcript, no session id, no `SQUAD_NAME`, missing home, unwritable log (a directory in its place; stays silent rather than nag), junk lines in the log. **No `jq` dependency** (Python): with `PATH=/nonexistent` the notice still works; the test also greps the source.

**Return 1 (QAW: parallel spawns gave two notices)**: the check and the append now run under a cross-process lock (`<log>.lock` directory, atomic `mkdir`, stale after 10 s, released in `finally`; a busy lock after 5 s stays silent). `CliTest.test_parallel_calls_give_one_notice_and_one_log_line`: 8 rounds × 4 concurrent guard processes → exactly one notice and one log line per round, no lock left; `test_a_stale_lock_is_taken_over`.

**Hook wiring** `test_hooks_json`: one `PreToolUse` entry with matcher `Bash` → `squad-manager-guard`, beside the path guard; `squad-usage-hook` still exempts the Manager (`test_stop_hook_still_exempts_the_manager`, `test_usage_hook_still_exempts_the_manager`).

**Rules**: COST-8 (`cost.md`) gains the reaction (notice in the next `squad-spawn`/`squad-inbox add` result → finish the step, write notes, `squad-respawn`). ITER-12 (`iterations.md`, only that block) loses "The cost hook never nudges you…" and keeps the reset after a check-in. The optional effort-before-model step-up rule is out of scope (BA ruling).
- **Developer rules byte delta 0** (both rules are manager-only; dev composed at M/design no/goal no = 4901 B before and after; cap 5120; `test_dev_rules_size` green).
- Limits: a Manager that only chats with the PO and never spawns or writes to the inbox hears nothing (by design); a cache expiry alone (no big context) also triggers, as COST-8 and BA ruling 1 say.
