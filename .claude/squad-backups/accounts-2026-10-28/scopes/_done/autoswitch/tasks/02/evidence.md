# 02 Evidence: pending-work wake
sha: 3ce1fba
## Behaviour
Branch `squad/accounts/autoswitch/accounts-dev-autoswitch-2`. All on the stub harness (no live pane).

| AC | Behaviour | Test |
|---|---|---|
| T1/T4 rule | cut-off pane (transcript ends `tool_use` / user after last `end_turn`) marked and woken once; idle pane moved, no `agent prompt` | `WakeTest.test_cut_off_pane_is_woken_once_...`, `CwakeTest.test_mark_clause1_...` |
| T1 clause 2 | failed `SendMessage` (real shape: `toolUseResult.success:false`, no `is_error`) since batch start, no later success: sender woken after the last pane is back; older failure / later success: not | `WakeTest.test_failed_send_*`, `CwakeTest.test_mark_clause2_*` |
| T1 clause 3 | `messages.jsonl` row `to==name` newer than last `end_turn` | `WakeTest.test_unanswered_message_*`, `CwakeTest.test_mark_clause3_*` |
| blocked | herdr `blocked` at sample time marks | `WakeTest.test_blocked_at_sample_time_*`, `CwakeTest.test_mark_blocked_*` (derived row) |
| T7 gate | not idle in gate: no prompt, `WAKE SKIPPED <pane> state=<s>`, marker removed, no retry | `WakeTest.test_pane_not_idle_*`, `CwakeTest.test_not_idle_*` |
| T7 skips | pane without `SQUAD_NAME` / no live claude: skipped | `CwakeTest.test_pane_without_squad_name_*`, `..._no_live_claude_*` |
| T8 text | default text, `--text`, `CSWITCH_WAKE_TEXT`, no path/token | `CwakeTest.test_idle_pane_gets_*`, `test_text_flag_*`, `test_default_text_*` |
| T9 | `CSWITCH_WAKE=off`: all moved, no marker, no prompt | `WakeTest.test_wake_off_*`, `CwakeTest.test_wake_off_*` |
| T10 | marker >30 min deleted unsent + log; second tick no re-wake; oldest first; dry-run writes nothing | `WakeTest.test_marker_older_*`, `test_dry_run_*`, `test_wakes_go_oldest_*` |
| F2/D2 | C FAILED: A+B woken, C marker kept; retry FAILED: no wake; retry done: C woken, A+B not again; deadline-hit: others woken; pane in its 15 min delays the wake | `WakeTest.test_failed_move_*`, `test_a_move_still_running_*`, `test_a_cswitch_still_in_its_15_*` |
| fail direction | unreadable transcript / messages.jsonl / herdr: not pending + one log line | `WakeTest.test_unreadable_*`, `test_herdr_failure_*` |
| cswitch fix | `agent wait --until idle --until done`; blocked pane gets no `/exit` until done | `CswitchBlockedTest`, `CswitchTest.test_happy_path_*` |
| install | `bin/cwake` linked; `wake-pending/` kept as state | `test_ca_install` |
| chain | real cswitch + cwake + cautoswitch: mark before `/exit`, one wake after `done` | `WakeTest.test_full_chain_real_cswitch_*` |

Fixtures: `.derived`: `transcript-tail-sendmessage-{error,ok}.derived.jsonl` (hand-added SendMessage items, real nesting), `agent-list-blocked.derived.json` (no real `blocked` row existed: a live list had none).

Open: none. Clause 2 verified against the real failed-SendMessage record shape (QA-w F1). Design deviation: `cwake --mark` is called from `cswitch`'s detached block (T1 D1 sample point), so `cswitch` has one more line than "only the `--until` fix".

## PO checklist after merge (first live batch)
- `squad-usage` before/after on one idle pane: confirm a bare `--resume` costs nothing.
- After the batch: `grep wake ~/.claude-accounts/cswitch.log`; only panes with pending work show `wake sent`.

## Receipts
See test output in the HANDIN.

## QA whitebox review

### QA whitebox, task 02 (sha 0f80fe5)

#### Run
Clean `git clone` at 0f80fe5: `python3 -m unittest tests/test_ca_autoswitch.py tests/test_ca_launchers.py tests/test_ca_install.py` = 154 tests OK (1 skipped). (A first run failed 4 tests because my own live probe wrote `bin/__pycache__` into the clone meanwhile: my error, not a defect.) `test_cache_younger_than_900s_is_used` did not fail for me.

#### Live check (REV-5b, read-only, pure functions of `bin/cwake` on the current herdr panes)
Idle/done panes (7): `clause1` False, last assistant `end_turn`. Working panes (4): `clause1` True (never sampled while working; sample is after `agent wait`). Clause 1/3 parsing holds on live transcripts.

#### FAIL findings

F1 (blocker). `tools/claude-accounts/bin/cwake:clause2` (~line 139) treats a failed send as `tool_result` with `is_error is True`. Real failed SendMessage results do NOT carry `is_error`. Real sample (transcript be3e1bf7-9b0e-485c-b78a-3ae359ab3e95.jsonl, 2026-10-16T04:53:41.550Z, under `~/.claude-2/projects/`): user record, `message.content[]` item `{"tool_use_id":"toolu_015m...","type":"tool_result","content":[{"type":"text","text":"{\"success\":false,\"message\":\"No agent named 'guardian-tl-guardian-rebuild' is reachable.\\nUse ListAgents ...\"}"}]}` with no `is_error` key, and the record has top-level `toolUseResult: {"success": false, "message": "...", "display": "Not sent — no agent named '...' is reachable."}`. I scanned all `~/.claude*/projects` transcripts: 267 `toolUseResult.success == false` records, 0 have `is_error`. Success results (120 in the squad project) also have no `is_error`; their `toolUseResult` has `success:true`. Why it matters: clause 2 (failed send by the sender, the real loss of the 2026-10-22 batch and the reason for the post-batch sample) can never fire on live data; every test passes because the `.derived` fixture `transcript-tail-sendmessage-error.derived.jsonl` encodes the guessed `is_error:true` shape. The design note's own open point 1 said this; the sample was on disk after all (the 01 grep looked for "not reachable" in `~/.claude-2` only under one pattern).
What would pass: `clause2` detects failure by (a) record-level `toolUseResult.success is False` on the user record whose `message.content[]` has the matching `tool_use_id`, or (b) the tool_result `content[].text` parsing as JSON with `success:false`; keep `is_error is True` as an extra accepted signal. Rebuild `transcript-tail-sendmessage-error.derived.jsonl` from the real record shape above (real nesting incl. `toolUseResult`; mark `.derived` or add the trimmed real record as `.real.jsonl`), and add a test where the record has no `is_error`. Drop "UNVERIFIED" comments in `bin/cwake` and `cautoswitch.wake_step` once verified; the evidence "Open" line changes accordingly.

F2 (minor, same return). Failed-send recipient match: calls keyed `input.to or input.recipient`; real `input` keys are `to, summary, message` (success result also shows `recipient`). Fine, but add the real input shape to the fixture so the pairing by `tool_use_id` is tested on real nesting.

Not findings (noted): marker expiry 30 min is measured from first write, a 7-pane serial batch with 10-min idle waits could expire pane 1's marker unsent (rare; the design accepted 30 min); `clause3` uses `last_t=0` if the 200-line tail holds no `end_turn` (any message to the agent counts); evidence line "only the --until fix" deviation (extra `cwake --mark` line in `cswitch`) is the agreed D1 sample point: accepted.

Re-check after fix (LC-3b): `bin/cwake` clause2, the fixture, new test, evidence Open line. I also run the full suite once on the scope's final sha (SUITE-3b).

#### Verdict on HANDIN 02 @ 3ce1fba (round 2): PASS
F1: `send_failed()` accepts `toolUseResult.success is False`, content-JSON `success:false`, or `is_error`; UNVERIFIED notes dropped; fixtures rebuilt in the real shape (input to/summary/message, `toolUseResult`, no `is_error`); new test for content JSON alone. F2 done. Clean clone at 3ce1fba: 155 tests OK (1 skipped) for test_ca_autoswitch/launchers/install. Diff vs 0f80fe5: cwake, one comment line in cautoswitch, fixtures, 2 test files.
Full suite: once on the scope's final sha after 03 passes (SUITE-3b).

## QA blackbox review

### 02 QA blackbox — sha 3ce1fba (PO rule E1)

Verdict: **PASS** (stub harness only; live items listed under "Untested live").
Vehicle (Manager FINAL 02): Dev stub harness, exported to /tmp/qab-02. Scenarios are my own (`/tmp/qab-02-extra/qab_scenarios.py`, `qab2.py`): real `cautoswitch` + `cswitch` + `cwake` against stub herdr/claude, two panes in one workspace (account 1 -> 2). CLI task: no screenshots; evidence = harness log/herdr call lines. Dev's own tests are context only, not my evidence.

| AC (E1 / ticket) | What I did | What I saw | Result |
|---|---|---|---|
| Every off-default squad pane moves, silently | cut-off pane + idle pane, run `cautoswitch --once` | `/exit` + resume for both; `workspace-default` stays 2 | PASS |
| Only pane with pending work gets one wake prompt | same run | exactly one non-`/exit` prompt, to the cut-off pane only; log `wake sent` for it, nothing for the idle one | PASS |
| Wake comes after the whole batch | same run, read `cswitch.log` order | `done` lines of both panes precede `wake sent` | PASS |
| Idle no-work panes get no prompt | two idle panes | both moved, zero wake prompts, no `wake sent/skipped` line | PASS |
| Wake text | read prompt | "Your Claude account changed (1 -> 2) ... Resend what failed ... answer with one line."; no paths/tokens | PASS |
| `CSWITCH_WAKE_TEXT` override | env set, pane with an unanswered message | prompt text is the override | PASS |
| Unanswered message -> pending | `messages.jsonl` row to dev-b newer than last turn | dev-b woken, nobody else | PASS |
| Failed SendMessage (new real shape `toolUseResult.success=false`) -> sender woken | dev-a transcript has failed send to dev-b after batch start | dev-a woken once, after both panes back | PASS |
| Blocked pane | pane `blocked`, goes idle after 3 s | `agent wait --until idle --until done`, `/exit` only after idle, no cut-off | PASS |
| `CSWITCH_WAKE=off` = old behaviour | two cut-off panes | both moved, no prompt, no `wake-pending/` dir | PASS |
| Second run does not re-wake | rerun after batch | no new prompts, marker gone | PASS |
| Marker >30 min deleted unsent | marker 1900 s old, idle pane | deleted, log "older than 30 min; deleted unsent", no prompt | PASS |
| `--dry-run` | cut-off pane + old marker | only `would cswitch` log line (as before), no prompt, marker untouched | PASS |
| Failed read never wakes everyone | missing `messages.jsonl` | one `not pending` log line per pane, no prompt | PASS |

Observations (not failures): the log carries a `wake: <pane> <name> messages.jsonl unreadable ...; not pending` line per pane when a scope has no `messages.jsonl` (expected by design). A pane without `SQUAD_NAME` is neither moved nor woken (Dev's test; not re-driven by me).

#### Untested live (stub only)
- Real herdr/claude panes; bare `--resume` token cost (PO checklist: `squad-usage` before/after on the first live batch).
- A real failed-SendMessage on a live session (the shape comes from the Dev's fixture).
- Pane without `SQUAD_NAME` and a pane not idle for 60 s: covered by Dev's tests only, not by my scenarios.
