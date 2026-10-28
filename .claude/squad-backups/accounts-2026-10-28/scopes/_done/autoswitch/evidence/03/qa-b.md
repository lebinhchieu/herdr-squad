# 03 QA blackbox — sha bc4e1e7 (docs; round 2 after 0a9790a)

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

## Untested live
Real herdr/claude panes, bare `--resume` token cost, clause 2 on live data: all left to the PO checklist, and the docs say so.
