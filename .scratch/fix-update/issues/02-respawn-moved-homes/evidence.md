# 02 `homes --apply --yes` respawns the moved homes' live agents: evidence

## Review
AC trace (run from `tests/`: `python3 -m unittest test_squadupgrade.Homes`):
- AC1 | `Homes.test_respawn_prompts_then_respawns_in_order_with_each_own_home_and_skips_the_caller` (prompt before respawn per agent, pod before coordinator, no call for caller, SQUAD_DIR + one of SCOPE_DIR/GOAL_DIR per agent's home) | unittest
- AC2 | same test: respawn path = `<target runtime>/bin/squad-respawn`, no `--force` | unittest
- AC3 | `Homes.test_a_prompt_without_done_leaves_the_agent_pending_exit_4_and_the_rest_respawn` | unittest
- AC4 | `Homes.test_no_herdr_call_without_yes_or_with_no_respawn_and_the_plan_is_listed` (empty `HERDR_LOG`) | unittest
- AC5 | first test: roster row `retired` never called; `DEAD` agent prints `not running s2-tech` | unittest
- AC6 | three whole-repo tests + `test_squad_respawn`, quoted below; subprocess calls are list argv with `sys.executable` | unittest
- AC7 | `## Behaviour`, "Not verified"
- AC8 | first test: last stdout line is the `caller mgr: ...` line; the pending test asserts no `caller` line without a caller row | unittest
- AC9 | pending test: `--timeout 50` in the prompt call; `prompt_ms()` falls back to 300000 on `x` | unittest
- AC10 | `Homes.test_a_home_refused_at_read_is_named_by_apply_and_exits_2` (stderr `refused scope solo`, exit 2, snapshot unchanged) | unittest
- AC11 | choice: the table is printed before the move (its `pin now` is the old pin); each `moved <home>: old -> new` line is the result | read `run()` in `bin/squadhomes.py`

## Behaviour
Tests (from `tests/`): `python3 -m unittest test_squad_respawn test_windows_safe test_utf8_helpers test_instructions test_squadupgrade`: 117 tests, OK. `test_squadupgrade.Homes test_squad_close` (hits of `grep -rl fake_herdr tests/`, squadtest.py gained a `FAIL_PROMPT` case): 88 tests, OK.

Design notes: a prompt that exits non-zero (herdr's `--wait` timeout) or does not return within timeout + 30 s is `pending`; the herdr stdout is not parsed for the word DONE (retire does the same). Test stub: B's `bin/squad-respawn` in the fixture plugin records argv and env to `HERDR_LOG`.
Exit codes: 0 all respawned / not running, 4 moved but one pending, 3 `--yes` missing (output lists `would respawn:` lines).

Not verified (stub only): a real agent mid-turn answering PIN-MOVE, the real `squad-respawn` run by this tool, and the new herdr tab. Chieu checks at merge: run `squad-process homes --apply --yes` in a real squad with one live agent and confirm its new tab opens from its notes.

## QA whitebox

### QA whitebox, ticket 02, sha 420e87c (re-check; first return on 4693c1e)

Verdict: PASS on 420e87c. Finding 1 fixed: `run` raises `refused <home>: <note>` exit 2 before any write for every offered refused home (respecting --only); the test covers mover + read-refused and `--only g1`. Re-ran 204 tests, OK.

Run by me: `test_squadupgrade test_squad_respawn test_windows_safe test_utf8_helpers test_instructions test_squad_close test_team_cli`, 204 tests OK. Read the diff 7238aab..4693c1e: AC1-AC9, AC11 hold by test and code reading (respawn path is the target runtime's `bin/squad-respawn`, no `--force`, list argv, caller skipped, pending -> exit 4).

#### Finding 1 (breaks AC10): a read-refused home next to a mover is still skipped with exit 0
- `bin/squadhomes.py` `run`, the `refused` raise sits only inside `if not chosen:`. When another offered home does move, a home refused at read time never reaches `chosen`/`bad`.
- Reproduced (scratch squad, goal g1 pinned old + scope s1 with `plugin: bad 0.10.1 <sha>`): `homes --apply --yes --no-respawn --home goals/g1` prints the s1 row `refused` with its note, moves g1, prints `moved goal g1`, and exits **0**; `scopes/s1/scope.md` unchanged. AC10: the home's note is printed and `--apply` exits 2.
- Why it matters: the skill (03) reads the exit code; exit 0 reads as "everything moved" while s1 stays on the old pin.
- What would pass: in `--apply`, a read-refused offered home (respecting `--only`) is handled like a compose-refused one: exit 2 with `refused <home>: <note> (deselect it with --only)`, nothing written. Add one case to the existing AC10 test (a mover plus a read-refused home, nothing changed).

#### Follow-ups (not blocking)
- `herdr agent prompt --wait` exit 0 is taken as DONE (herdr stdout not parsed), same as `bin/squad-retire`; the live check stays with Chieu at merge, as the evidence says.

## QA blackbox

### 02 QA blackbox: `homes --apply --yes` respawn, on 420e87c (first check 4693c1e: FAIL AC10; re-check below)
Method: live, scratch squad `s02` (goal g1 with live roster rows tl-g1, mgr-g1 (the caller), a retired row; scopes s1 with 6 live rows and s2 with tl, dev, one agent herdr cannot find, one retired row), all pinned at 0.10.1, target 0.10.2 (a clone of 4693c1e plus a version bump). Stub `herdr` on PATH logs argv; the target runtime's `bin/squad-respawn` was replaced by a wrapper logging its own path, argv and `SQUAD_DIR`/`SCOPE_DIR`/`GOAL_DIR`. No code read. A live agent mid-turn and the real new tab are not checked (stub only): Chieu checks at merge.

| AC | Mode | What I did | What I saw | Result |
|---|---|---|---|---|
| AC1 | live | `SQUAD_NAME=mgr-g1 homes --apply --yes --home goals/g1` | per agent `agent get`, then `agent prompt ... PIN-MOVE ... --wait --timeout 300000`, then `RESPAWN`; no call for mgr-g1; each respawn has `SQUAD_DIR` plus exactly one of `SCOPE_DIR` (s1, s2 agents) / `GOAL_DIR` (tl-g1); order inside each home: dev, qa-whitebox, qa-blackbox, tech-lead, team-lead | pass |
| AC2 | live | same log | path `$W/s02/_runtime/0.10.2-2a4892d7cc25/bin/squad-respawn` (the target runtime), no `--force` anywhere | pass |
| AC3 | live | stub: prompt exits 1 for s1-tl; `SQUAD_HOMES_PROMPT_TIMEOUT_MS=50`; another run where `squad-respawn` of s1-dev exits 1 | `pending s1-tl: prompt did not settle; run squad-respawn s1-tl after it saved its notes`, exit 4, others respawned, three `plugin:` lines moved; second run `pending s1-dev: squad-respawn exited 1: boom; run squad-respawn s1-dev ...` exit 4 | pass |
| AC4 | live | `--apply` without `--yes`; `--apply --yes --no-respawn` | `would respawn:` lines (no `would respawn` for the caller, a line says so); zero herdr lines both times; pins moved only in the second | pass |
| AC5 | live | rosters with `retired` rows; `herdr agent get s2-gone` fails | retired rows never in the log; `not running s2-gone` and no prompt for it | pass |
| AC6 | - | whitebox owns | - | n/a |
| AC7 | - | evidence says live agent and new tab not verified, and what Chieu checks (read) | present | pass |
| AC8 | live | caller in a moved roster; caller not in any moved roster | last line `caller mgr-g1: last step: report to Chieu, write your notes, then run squad-respawn mgr-g1` after every agent line (also with exit 4); with `SQUAD_NAME=outsider` no `caller` line | pass |
| AC9 | live | env 50, `x`, `-5`; a stub whose prompt hangs 60 s with env 100 | prompt call carries `--timeout 50`, `300000`, `300000`; the hang ends as `pending s2-tl` after 30.5 s (timeout + 30 s), exit 4 | pass |
| AC10 | live | one scope with `plugin: garbage`, `--check` / `--apply --yes` for that scope alone; then for the goal (g1, s1 fine, s2 malformed) | scope alone: exit 2, `refused scope s2: plugin: line 7: ...`, nothing written. **Goal: `--check` exit 2, `--apply` (no yes) exit 3, `--apply --yes` exit 0**, g1 and s1 moved, s2 only shown as `refused` in the table | **fail** (see below) |
| AC11 | live | read the output | table printed before the move (old pin, `moves`), each `moved ...` line is the result; evidence says so | pass |

#### Finding (breaks the written AC10 sentence)
AC10: "A home refused at read time ... is named on `--apply` too: its note is printed and `--apply` exits 2". With a goal whose scope s2 has a malformed `plugin:` line, `homes --apply --yes --home goals/g1` moves g1 and s1, prints s2 as `refused` inside the table, and exits 0. The same state gives exit 2 on `--check`, and the compose-refused case of 01 AC4 (one refused among the chosen exits 2, nothing written) behaves differently. The skill (03) will read exit 0 as a clean move. Expected: exit 2 and nothing written (Chieu deselects with `--only`), as the 01 AC4 compose gate does; or the ticket says that a read-refused home never blocks the rest, and `--apply --yes` exits a distinct code.

#### Follow-ups (not AC)
- Order: inside the goal-and-scopes batch, the goal's `tl-g1` is respawned first, before the scopes' agents. Design 1 says the coordinator restarts after the pod it routes to; that holds per home only. A scope's `manager` row sits after its `team-lead` and before nothing in Design 1's order list.
- Pending hang takes 30 s over the timeout; the output does not say that.

#### Re-check on 420e87c (AC10 only, LC-3b)
Fresh scratch squad `s03` from a clone of 420e87c: goal g1, s1 fine, s2 `plugin: garbage`.
- `homes --apply --yes --no-respawn --home goals/g1`: stderr `refused scope s2: plugin: line 7: ... (deselect it with --only)`, exit 2, md5 of every file outside `_runtime/` unchanged. **pass**
- `--only g1 s1`: `moved goal g1`, `moved scope s1`, exit 0; s2 still `plugin: garbage`. **pass**
AC10 now pass. Verdict on 420e87c: PASS.
