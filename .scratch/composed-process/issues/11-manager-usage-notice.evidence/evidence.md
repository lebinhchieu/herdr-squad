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

## QA whitebox review

### QA whitebox 11 (manager notice): FAIL @ fcff3a2

Ran (detached worktree): `test_squad_manager_guard test_hooks_json test_squad_usage test_windows_safe test_dev_rules_size test_processlint` = 97 OK; `squad-process lint` ok. Reviewed 2f2e5a7..fcff3a2: guard decision table, exit-0 forced failures, no-jq, hooks.json, COST-8 and ITER-12 edits, dev rules +0 B all read fine. Delivery probe (PreToolUse `additionalContext`, Haiku, $<0.10): command and answer are in evidence.md; I could not re-run it (nested `claude -p` refused in my session); accepted from the recorded command + answer + the `usage-events.jsonl` line.

#### Findings
1. **"At most once per session per crossing" fails under parallel calls.** `bin/squad-manager-guard` `decide`: `seen_keys(log)` is read, then `fresh` lines are appended, with no lock between. A Manager issuing two `squad-spawn` calls in one turn (normal when spawning a pod) runs two guard processes at once; both read an empty log and both notify. Repro: fixture transcript with last ctx 144k, same payload, two `bin/squad-manager-guard` processes started together under `SQUAD_ROLE=manager` with `SCOPE_DIR` set (env -u GOAL_DIR), fresh log each round: 3 of 15 rounds printed two notices (and two identical log lines when the race is wider). No test covers it. Would pass: claim the event atomically (lock the log for the read+append, e.g. `fcntl.flock` / `msvcrt.locking` with a guarded import so it degrades silently, or an `O_CREAT|O_EXCL` marker per event key), and a test that runs 2-4 guard processes at once and asserts one notice and one log line per key.

#### Notes (not blocking)
1. `ctx` is one key per session: after a compaction drops the context under 100k and it rises over 100k again, no second `ctx` notice (the compaction has its own event). Spec says "per threshold crossing"; accepted unless the Tech Lead wants re-arming.
2. A command that does not start with `squad-spawn` (e.g. `cd x && squad-spawn …`, `VAR=1 squad-spawn …`) gets no notice; matches the ticket's "starts with".
3. Evidence is old-form (`11-…evidence/`); integration re-runs the `git mv`.

---
### Re-check @ 3be9c32: PASS

Re-checked only the guard + concurrency test (diff fcff3a2..3be9c32 = `bin/squad-manager-guard`, `tests/test_squad_manager_guard.py`, evidence.md). Detached worktree: `test_squad_manager_guard` 24 OK x3; new `test_parallel_calls_give_one_notice_and_one_log_line` (4 procs x 8 rounds) 15 consecutive runs OK (=480 rounds, 0 double notices; before: 3/15 rounds); `test_hooks_json test_windows_safe test_processlint test_dev_rules_size` OK. F1 fixed: check+append are inside one `claim_lock` (atomic `mkdir`, portable, no msvcrt/fcntl); lock removed in `finally`; lock busy >5s or OSError -> silent (exit 0), stale (>10s) taken over.

#### Notes (not blocking)
1. Stale takeover is itself racy: two waiters both see a >10s lock, A `rmdir`+`mkdir`s, B's pending `rmdir` can then remove A's fresh lock. Only after a killed process holds the lock and two spawns hit it in the same ~ms; worst case one duplicate notice. Accept.
2. Earlier notes (ctx one key per session, "starts with" match, old-form evidence folder for integration `git mv`) unchanged.

## QA blackbox review

### QA-b 11 (sha 3be9c32; first HANDIN fcff3a2, branch squad/plugin/process-fixes/plugin-dev-pf-5)
Method: real `bin/squad-manager-guard` fed PreToolUse JSON (session_id, transcript_path, tool_input.command; env SQUAD_ROLE/SQUAD_NAME/SCOPE_DIR) with fixture transcripts in the real Claude Code JSONL shape (assistant turns with usage, `compact_boundary` lines, old timestamps). Composed rules via `squad-process compose`. One live Haiku probe ($ well under the 0.10 cap). No code read.

| AC | What I did | Saw | Result |
| --- | --- | --- | --- |
| 1 | Manager, session at 150k, `squad-spawn plugin-dev-9 dev`; a new session at 160k running `squad-inbox add foo` | `{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"context 150k (over 100k): after this step write your notes and run squad-respawn mgr [COST-8]"}}`, exit 0; new session notices again | pass |
| 2 | second `squad-spawn` and `squad-inbox add` in the same session | empty output | pass |
| 3 | Manager at 60k/fresh cache; the 8 other roles at 150k; `ls`, `git status`, `squad-inbox list`, `echo squad-spawn`, `squad-respawn mgr` | empty output, exit 0 | pass |
| 4 | Turn at 62k, then `compact_boundary` + 30k turn; later a second compaction; separate session whose last turn is 2 h old at 40k; a 2-minute-old 40k turn | compaction: `context 62k (after a compaction)` once, then silent; 2nd compaction: notice again; 2 h gap: `context 40k (cache expired)` once; fresh cache: silent | pass |
| 5 | no `jq` on PATH; `squad-usage` removed from bin; junk stdin; missing transcript | exit 0; no jq needed (notice still given); others silent, stderr empty | pass |
| 6 | as AC 3; hook output for non-matching commands | empty (identical to no hook); never any `permissionDecision` | pass |
| 7 | live: `claude -p --model haiku --settings <hook> --max-budget-usd 0.10`, "Run exactly this bash command: squad-spawn probe-9 ..." (stub `squad-spawn` on PATH, hook pointed at the 150k fixture) | Answer: `YES. Hook context: "context 150k (over 100k): after this step write your notes and run squad-respawn mgr [COST-8]"` | pass |
| 3be9c32 | 12 parallel `squad-spawn` in one session; 12 parallel `squad-inbox add` over 3 sessions | exactly 1 notice and 1 log line for the session; 3 notices for 3 sessions | pass |
| rules | composed manager | COST-8 points at the notice ("a hook adds one `context <n>k` notice ... act on it then"); ITER-12 keeps only the reset after a check-in, "never nudges you" sentence gone; dev composed rules byte-identical to 4901cab; `who COST-8` manager at S/M/L | pass |

Non-blocking observations:
- The hook fires only when the command starts with `squad-spawn` / `squad-inbox add` (also after `;` or in a pipe line). `cd dir && squad-spawn x`, `/abs/path/squad-spawn x` and `VAR=1 squad-spawn x` get no notice.
- With a compaction the size in the notice is the last turn's size before the boundary (62k in my fixture), not the size after it.

Verdict: PASS 11 on 3be9c32.
