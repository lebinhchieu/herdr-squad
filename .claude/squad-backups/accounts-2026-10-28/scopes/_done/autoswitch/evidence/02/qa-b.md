# 02 QA blackbox — sha 3ce1fba (PO rule E1)

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

## Untested live (stub only)
- Real herdr/claude panes; bare `--resume` token cost (PO checklist: `squad-usage` before/after on the first live batch).
- A real failed-SendMessage on a live session (the shape comes from the Dev's fixture).
- Pane without `SQUAD_NAME` and a pane not idle for 60 s: covered by Dev's tests only, not by my scenarios.
