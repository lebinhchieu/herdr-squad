# 05 Fix the `bin/squad-usage` undercount

Status: done
Blocked by: none (AT-01 passed, ad3b4c7)
Files: `bin/squad-usage`, `tests/test_squad_usage.py`. Not `squad-spawn`, `squad-respawn` (ticket 06).
Parallel with: 06 (disjoint files).

AT-01 found the live table (`squad-usage` with no flags) undercounts: it skips subagent lines, reads only the latest roster session of an agent, and counts the `~/.claude-2/projects` symlink twice when both config dirs are searched. The trial (below) reads this table, so it must be right first.

## Business AC
The Manager and the PO can see each agent's real token use in the table, including its subagents and every session it has had (after respawns).

## Technical AC
- **U1 Real samples first.** Before coding, read one real transcript of a respawned agent and one real `<session>/subagents/*.jsonl` (e.g. `~/.claude/projects/-home-chieule-workspace-squad/`). `dev-evidence.md` states the line types and the fields used: `type:"agent-name"` with `agentName`, `isSidechain`, `message.id`, `message.usage`. Counts and field names only, no text.
- **U2 Subagents, table only.** Sidechain lines and the session's `subagents/*.jsonl` files are folded in for the **table's** `out` and a new `subagents` column (their output tokens, rightmost) and nowhere else: `peak ctx`, `last ctx`, `expiries`, `just_expired`, compactions, `model` and `effort` come from main-thread lines only, because `summarize` is shared with `--check` and a subagent's context must not trigger a respawn or hide an idle gap. Deduped by `message.id` (max per token field, as AT-01 D1). `turns` counts main-thread turns only, `out` includes the subagents; the header says so. Test: a session whose subagent line has a huge ctx and a later timestamp gives the same `--check` result as without it.
- **U3 Every session of an agent.** An agent's sessions are the transcripts whose first `type:"agent-name"` line has `agentName` **exactly** equal to its name, plus its roster session. `turns`, `out` and `expiries` sum over them; `peak ctx`, `last ctx` and `model/effort` come from the newest. **Bounded scan:** only the project dirs of the roster session and of the agent's worktree (`.worktrees/...`), (reading each file only up to its first `agent-name` line is optional: the unbounded table ran in 0.24 s on ~1.1 GB, so speed is not the reason for the bound; the cross-squad sum is). **`--check SESSION` never takes the scan path** (it runs on every Stop) and judges one session only; its output does not change. If two squads share a bare name (`dev-1`), the roster's squad decides: only transcripts whose cwd matches that squad's project dir count, and the report says when it could not tell.
- **U4 Symlink.** Transcript paths are resolved with `os.path.realpath` and deduped, so a config dir that links to another (`~/.claude-2/projects` -> `~/.claude/projects`) never counts a session twice. `find_transcript` keeps working for a bare session id; when two paths share an id the realpath-sorted first wins, so the result is deterministic (test).
- **U5 Tests** in `tests/test_squad_usage.py`, fixtures only: (a) subagent file adds to the agent's totals and its duplicated lines are not double-counted; (b) two sessions with the same `agent-name` sum, a third agent's session is not included; (c) a symlinked projects dir gives the same numbers as the real one; (d) the constant case: an agent with no subagents and one session gives exactly today's numbers (regression); (e) `--check` output unchanged for the existing cases. Existing tests stay green.
- **U6 Real-data check.** Run the table in the real squad (`SCOPE_DIR` of `plugin/audit-token`) and compare turns and output for `plugin-tech-audit-token` with a hand count over the same transcripts (one `python3 -I` one-liner, in `dev-evidence.md`), and compare the table's per-agent totals for the whole scope with `scripts/audit.py`'s per-role numbers for the same scope and `--until` (an independent method; `audit.py` is on the AT-01 branch, base for this task ad3b4c7 is not needed, read it by path). Compare turns, output, `last ctx` and `expiries` with the hand count, not only turns and output. State the difference per role and explain any over 1%. Compatibility: the columns that exist keep their names and order; new columns go to the right; `squad-usage-hook` and `squad-respawn` (which call `--check` and `--get`) work unchanged.
- **U7 Suite** per CLAUDE.md "Running tests": run once on the final sha, receipt saved. Not an integration task, so `--if-changed` is allowed.
- **U8 Merge overlap (remove-board).** The remove-board scope also edits `agents/`, `bin/`, `skills/`, `templates/`. `dev-evidence.md` lists the files this branch changed (`git diff --stat <base>`); the integration task (04) resolves conflicts, and a conflict in `bin/squad-usage` goes to the Tech Lead.
- **U9 Process rule.** The "Long suites: run once, read the receipt" rule is already in `templates/squad/process.md` (v2). Do not edit it; `dev-evidence.md` quotes the line number as proof.

## Out of scope
$ prices and shares (that is `audit.py`); changing `--check` thresholds.

## Comments
- 2026-10-16 Tech Lead, after QAW FAIL 1: U2 stands as written (`turns` main-thread only, `subagents` = subagent output tokens, header says what `turns` and `out` include). U3: the project-dir restriction and same-name check stand; only the read-up-to-first-line optimisation is relaxed. U4 test and the full U6 comparison stand.

- 2026-10-16 Dev AT-04: merged into the integration branch; passed both QAs.
