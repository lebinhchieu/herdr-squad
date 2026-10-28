Status: ready-for-agent
Type: task
Task ID: 01
Touches: `bin/squadtranscript.py` (new), `bin/squad-usage`, `tests/test_squadtranscript.py` (new), `tests/test_squad_respawn.py` (file list ~line 162), `tests/test_squad_spawn.py` (file list ~line 543)
Does not touch: `tests/test_squad_usage.py` and every other test (must pass unchanged), any `squadreport*` file
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_usage test_squad_usage_hook test_squadtranscript test_squad_respawn test_squad_spawn`. Fixtures: the existing `turn()` helper pattern of `test_squad_usage.py`; transcripts built in a temp `CLAUDE_CONFIG_DIR`.
Blocked by: none

# 01: Extract `squadtranscript.py` from `bin/squad-usage` (behaviour-neutral)

**Done when `squad-usage` imports its transcript readers from one shared module and nothing it prints or logs has changed.** Spec: `.scratch/squad-report/spec.md` → Technical → "Reuse of `bin/squad-usage`". `squad-usage` is a Stop-hook hot path: keep imports cheap.

## What
1. Move, do not copy: `config_dir`, `projects_glob`, `find_transcript`, `agent_name`, `agent_sessions`, `read_lines`, `read_session`, `parse_ts`, `is_expiry`, `TOKEN_FIELDS` into `bin/squadtranscript.py` (pure functions, stdlib only, `encoding="utf-8"`, no `fcntl`; ADR 0011). `bin/squad-usage` imports them (same `sys.path` trick the other `bin/*.py` modules use).
2. Add `iter_records(path)`: one generator over a session file **and** its subagent files, yielding one plain dict per record that has a timestamp: `ts` (int epoch s, floored; `parse_ts`), `kind` (the record `type`: assistant|user|system|other), `side` (`isSidechain`), `origin` (the record's `origin` dict or None), `msg_id` (assistant `message.id` or None), `model`, `usage` (dict or None), `cmds` (list of `Bash` tool_use command strings in an assistant record, else `[]`), `cost_state` (the `cost-state` record's dict or None). Unknown or malformed lines are skipped, never raised. Rebuild `read_session` on it so its output is byte-identical.
3. Update the two file lists in `test_squad_respawn.py` and `test_squad_spawn.py` that copy bin files into a stub plugin dir: add `squadtranscript.py`.

## Technical AC
1. `git diff` of `bin/squad-usage` shows only removed definitions plus the import; no other logic line changes.
2. `test_squad_usage.py`, `test_squad_usage_hook.py` unchanged and green (quote `Ran N ... OK`, same N as before the ticket).
3. `test_squadtranscript.py`: `iter_records` on a synthetic session with a peer message (`origin.kind=peer`), a human message, a task-notification, a tool result, a duplicated assistant `message.id`, a subagent file, a `cost-state` record and a malformed line yields the dict shape above; `ts` is floored; the malformed line is skipped.
4. The two stub-plugin tests pass (they fail without the new list entry: say so in the hand-in).
5. Primary behaviour only (qa: light): no new CLI, no new output.
