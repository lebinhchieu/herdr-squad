# 03 Evidence: docs, pending-work wake
sha: bc4e1e7
## Behaviour
sha: bc4e1e7
Docs only (`tools/claude-accounts/HANDOFF.md`, `README.md`, `skill/SKILL.md`). Each claim traced to 02's code (`bin/cwake`, `bin/cautoswitch`, `bin/cswitch`) or test.

| Doc claim | Source |
|---|---|
| silent move; `cswitch` never wakes; `--until idle --until done` | `cswitch` L46; `CswitchBlockedTest` |
| clause 1 cut-off/blocked, sampled before `/exit` | `cwake.clause1`, `sample`; `cswitch` L48; `WakeTest.test_cut_off_*`, `test_blocked_at_sample_time_*` |
| clause 2 failed send, 3 shapes, since batch start, no later success | `cwake.send_failed`, `clause2`; `cautoswitch.batch_start`, `wake_step` L196; `WakeTest.test_failed_send_*` |
| clause 3 unanswered message, folder order | `cwake.clause3`; `WakeTest.test_unanswered_message_*` |
| marker `epoch name reason`, 30 min expiry | `cwake.write_marker`; `cautoswitch.MARKER_MAX_AGE`, `wake_step`; `test_marker_older_*` |
| wake after batch, 15 min in-flight skip, oldest first, `CSWITCH_WAKE_GAP` 3 s | `wake_step` L183-202; `test_wakes_go_oldest_*`, `test_a_cswitch_still_in_its_15_*` |
| failed/still-running pane keeps marker, others woken | `wake_step` (`back`); `test_failed_move_*`, `test_a_move_still_running_*` |
| 60 s idle gate, `CWAKE_TIMEOUT_MS`, `WAKE SKIPPED`, log lines | `cwake.wake`; `CwakeTest.test_not_idle_*` |
| own pane / retired skipped | `cwake.wake` (`env is None or not name`); `CwakeTest.test_pane_without_squad_name_*`, `..._no_live_claude_*` |
| text, `(old -> new)` only when known, `CSWITCH_WAKE_TEXT` | `cwake.wake`, `OLD_ACCT`; `CwakeTest.test_default_text_*` |
| `CSWITCH_WAKE=off`; dry-run writes nothing | `cwake.main`, `tick` `wake_on`; `test_wake_off_*`, `test_dry_run_*` |
| fail direction | `cwake.sample`; `test_unreadable_*`, `test_herdr_failure_*` |
| restart `cautoswitch` after install | `cautoswitch` is a long-running loop (`main`); code loaded once |
| Unverified: bare `--resume` cost; clause 2 on live data; `blocked` row `.derived` | tasks/01 T5; 02 evidence (derived fixtures); no live probe run |

Test hits for changed docs (`grep -rl` of `cwake`, `HANDOFF.md` in tests/): `test_ca_install`, `test_ca_autoswitch`, `test_ca_launchers` run, OK.

## QA whitebox review

### QA whitebox 03 — sha 0a9790a: FAIL (2 doc findings)

Checked: diff 3ce1fba..0a9790a (HANDOFF, README, SKILL only) against bin/cwake, bin/cautoswitch, bin/cswitch at 0a9790a. All behaviour claims match the code (clauses 1-3, marker/30 min, wake gap, 15 min in-flight skip, 60 s gate, WAKE SKIPPED lines, own/retired pane skip, text, CSWITCH_WAKE=off, dry-run, install state list, .gitignore). Unverified items are stated as unverified. Style: ok.

#### F1 — checklist step 5 cannot be observed (HANDOFF.md:71)
Says the sender "should show `wake sent` with reason `failed-send` in its marker". After a wake, `cwake.wake` deletes the marker (`done()`, bin/cwake:252, log line :271) and the log line is `<ts> <pane> <name> wake sent` with no reason. So the PO can never see `failed-send` after the real tick; a `wake sent` could equally come from clause 1/3. The step is the one live sample of clause 2, so it must be doable.
Pass: give an observable route, e.g. before the tick finishes (or after the batch, before the wake) run `cwake --mark <sender> --clauses 2 --since <epoch of batch start>` and `cat ~/.claude-accounts/wake-pending/<sender>` -> `... failed-send`; or tell the PO to read the sender's transcript for the failed `SendMessage` and the wake prompt. Say which one proves clause 2.

#### F2 — checklist step 2 "and nothing else" is wrong (HANDOFF.md:68)
`cautoswitch --once --dry-run` also prints the tick status line `HH:MM:SS ok: <ws> -> cN 5h..` (cautoswitch tick, print before the pane loop) and, over threshold, a `[dry-run] would set ... default` line. Pass: "prints `[dry-run] would cswitch ...` for that pane, no `wake`/`WAKE` line in cswitch.log, wake-pending unchanged".

Suite: full run on 0a9790a started (receipt in evidence/ when done); docs-only fix will need a re-check of changed files and a suite run on the final sha.

### Round 2 — sha bc4e1e7: PASS
Diff 0a9790a..bc4e1e7 = HANDOFF.md lines 68/71 only. F2 fixed (status line + `would cswitch` named, no wake line, wake-pending unchanged). F1 fixed: route (a) checked against bin/cwake: `--mark --clauses 2 --since` works after the wake (transcript survives, mark() writes marker, rm needed else next tick wakes: cautoswitch wake_step); route (b) sound. Non-blocking nit: nested backticks in item 5 render oddly.
Early suite on 0a9790a: 1449 tests OK (browser skipped by --if-changed). Final-sha run on bc4e1e7: see evidence/suite-default.txt.

## QA blackbox review

### 03 QA blackbox — sha bc4e1e7 (docs; round 2 after 0a9790a)

Verdict: **PASS**. Docs only (HANDOFF.md, README.md, skill/SKILL.md under tools/claude-accounts/). CLI/doc task: no screenshots. Code is unchanged since 3ce1fba (my 02 PASS); 0a9790a..bc4e1e7 changes only HANDOFF.md checklist steps 2 and 5. Read via `git show`/`git diff` (exported to /tmp/qab-03-8bmj).
Vehicle: claims compared with what I saw in 02 on the stub harness (evidence/02/qa-b.md); plus a rerun of Dev's tests/test_ca_autoswitch.py on the stub export (52 tests, OK) for claims I did not drive myself.

| Doc claim (HANDOFF unless noted) | Checked against | Result |
|---|---|---|
| Every off-default squad pane moves silently; bare resume sends no prompt | 02: both panes `/exit` + resume, no prompt to idle pane | PASS |
| Only pending-work pane woken once, after the workspace batch | 02: one prompt, to cut-off pane; `done` lines precede `wake sent` | PASS |
| Pending = cut-off/`blocked`, failed send, unanswered message | 02: cut-off, unanswered message, failed send (`toolUseResult.success=false`) each woke the right pane | PASS |
| `blocked` pane waited on, `/exit` only after idle | 02: `agent wait --until idle --until done` | PASS |
| Marker `wake-pending/<pane>`, deleted unsent after 30 min with a log line | 02: 1900 s marker deleted, log "older than 30 min; deleted unsent" | PASS |
| `CSWITCH_WAKE=off` = old behaviour, no marker, no prompt | 02: both cut-off panes moved, no prompt, no `wake-pending/` | PASS |
| `CSWITCH_WAKE_TEXT` replaces text; default text wording | 02: override used; default text matches the quoted one | PASS |
| `--dry-run` sends no prompt, writes no marker | 02: only `would cswitch`, old marker untouched | PASS |
| Unreadable file = not pending, one log line, never wakes everyone | 02: missing `messages.jsonl` -> `not pending` per pane, no prompt | PASS |
| Second run does not re-wake | 02 | PASS |
| Not-idle 60 s: no prompt, `WAKE SKIPPED ... state=`, `wake skipped`, marker deleted, no retry | Dev test `test_pane_not_idle_in_the_gate_...` (rerun, OK); not driven by me | PASS (Dev test) |
| Pane without `SQUAD_NAME` neither moved nor woken | Dev test (rerun, OK); same as 02 note | PASS (Dev test) |
| Command `cwake <pane>` / `cwake --mark <pane>` in HANDOFF table, README table, SKILL table | read all three; names consistent, `cwake` present in README file list and command line | PASS |
| `cwake --mark <pane> --clauses 13\|2 --since EPOCH` (step 5a) | ran `cwake --mark p1 --clauses 2 --since 1` (accepted, rc 0); `--bogus` -> usage, rc 2; usage line shows those flags | PASS |
| README: `wake-pending/` in state list; wake rule line; "restart `cautoswitch` after install" | read | PASS |
| SKILL: agent may be woken; resend failed messages; idle gets nothing; own pane never woken; unverified items named; defers to HANDOFF; consistent with HANDOFF | read | PASS |
| Unverified stated plainly: bare `--resume` cost, clause 2 on live batch, whole chain on live panes (+ `blocked` row `.derived`) | HANDOFF "Unverified until a live sample" and SKILL gotcha | PASS |
| Live-probe checklist present: throwaway pane, `cautoswitch --once --dry-run`, `squad-usage` before/after on one idle pane, log grep, clause 2 sample, rollback | HANDOFF steps 1-6. Round-2 step 5 now truthfully says the marker is deleted at wake and gives two proofs (marker via `cwake --mark --clauses 2` then `rm`, or transcript + no-other-clause) | PASS |

Notes (not failures):
- Step 2 now says the dry-run prints a status line and `[dry-run] would cswitch ...` on screen. In 02 I saw the `would cswitch` log line and no prompt/marker; I did not re-capture the exact stdout format here (stub only). Low risk: the PO runs this step by eye on the live probe.
- Doc says the clause 2 failure shape came from a real 2026-10-16 transcript; I cannot confirm that (blind to it); it is labelled unverified for live use, which is the honest reading.

#### Untested live
Real herdr/claude panes, bare `--resume` token cost, clause 2 on live data: all left to the PO checklist, and the docs say so.
