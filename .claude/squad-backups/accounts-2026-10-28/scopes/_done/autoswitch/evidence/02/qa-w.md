# QA whitebox, task 02 (sha 0f80fe5)

## Run
Clean `git clone` at 0f80fe5: `python3 -m unittest tests/test_ca_autoswitch.py tests/test_ca_launchers.py tests/test_ca_install.py` = 154 tests OK (1 skipped). (A first run failed 4 tests because my own live probe wrote `bin/__pycache__` into the clone meanwhile: my error, not a defect.) `test_cache_younger_than_900s_is_used` did not fail for me.

## Live check (REV-5b, read-only, pure functions of `bin/cwake` on the current herdr panes)
Idle/done panes (7): `clause1` False, last assistant `end_turn`. Working panes (4): `clause1` True (never sampled while working; sample is after `agent wait`). Clause 1/3 parsing holds on live transcripts.

## FAIL findings

F1 (blocker). `tools/claude-accounts/bin/cwake:clause2` (~line 139) treats a failed send as `tool_result` with `is_error is True`. Real failed SendMessage results do NOT carry `is_error`. Real sample (transcript be3e1bf7-9b0e-485c-b78a-3ae359ab3e95.jsonl, 2026-10-16T04:53:41.550Z, under `~/.claude-2/projects/`): user record, `message.content[]` item `{"tool_use_id":"toolu_015m...","type":"tool_result","content":[{"type":"text","text":"{\"success\":false,\"message\":\"No agent named 'guardian-tl-guardian-rebuild' is reachable.\\nUse ListAgents ...\"}"}]}` with no `is_error` key, and the record has top-level `toolUseResult: {"success": false, "message": "...", "display": "Not sent — no agent named '...' is reachable."}`. I scanned all `~/.claude*/projects` transcripts: 267 `toolUseResult.success == false` records, 0 have `is_error`. Success results (120 in the squad project) also have no `is_error`; their `toolUseResult` has `success:true`. Why it matters: clause 2 (failed send by the sender, the real loss of the 2026-10-22 batch and the reason for the post-batch sample) can never fire on live data; every test passes because the `.derived` fixture `transcript-tail-sendmessage-error.derived.jsonl` encodes the guessed `is_error:true` shape. The design note's own open point 1 said this; the sample was on disk after all (the 01 grep looked for "not reachable" in `~/.claude-2` only under one pattern).
What would pass: `clause2` detects failure by (a) record-level `toolUseResult.success is False` on the user record whose `message.content[]` has the matching `tool_use_id`, or (b) the tool_result `content[].text` parsing as JSON with `success:false`; keep `is_error is True` as an extra accepted signal. Rebuild `transcript-tail-sendmessage-error.derived.jsonl` from the real record shape above (real nesting incl. `toolUseResult`; mark `.derived` or add the trimmed real record as `.real.jsonl`), and add a test where the record has no `is_error`. Drop "UNVERIFIED" comments in `bin/cwake` and `cautoswitch.wake_step` once verified; the evidence "Open" line changes accordingly.

F2 (minor, same return). Failed-send recipient match: calls keyed `input.to or input.recipient`; real `input` keys are `to, summary, message` (success result also shows `recipient`). Fine, but add the real input shape to the fixture so the pairing by `tool_use_id` is tested on real nesting.

Not findings (noted): marker expiry 30 min is measured from first write, a 7-pane serial batch with 10-min idle waits could expire pane 1's marker unsent (rare; the design accepted 30 min); `clause3` uses `last_t=0` if the 200-line tail holds no `end_turn` (any message to the agent counts); evidence line "only the --until fix" deviation (extra `cwake --mark` line in `cswitch`) is the agreed D1 sample point: accepted.

Re-check after fix (LC-3b): `bin/cwake` clause2, the fixture, new test, evidence Open line. I also run the full suite once on the scope's final sha (SUITE-3b).

## Verdict on HANDIN 02 @ 3ce1fba (round 2): PASS
F1: `send_failed()` accepts `toolUseResult.success is False`, content-JSON `success:false`, or `is_error`; UNVERIFIED notes dropped; fixtures rebuilt in the real shape (input to/summary/message, `toolUseResult`, no `is_error`); new test for content JSON alone. F2 done. Clean clone at 3ce1fba: 155 tests OK (1 skipped) for test_ca_autoswitch/launchers/install. Diff vs 0f80fe5: cwake, one comment line in cautoswitch, fixtures, 2 test files.
Full suite: once on the scope's final sha after 03 passes (SUITE-3b).
