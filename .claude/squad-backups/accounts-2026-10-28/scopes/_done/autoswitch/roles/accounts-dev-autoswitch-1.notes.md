# Notes: accounts-dev-autoswitch-1 (retired 2026-10-23)
- Task 01 done: design note in tasks/01.md ## Design (copy evidence/01/design.md); QA-w PASS at dac0c50 on branch squad/accounts/autoswitch/accounts-dev-autoswitch-1. Fixtures in tests/fixtures/ca/ (agent-list-status.real.json, messages.real.jsonl, transcript-tail-*.derived.jsonl).
- Task/evidence files live under $SCOPE_DIR in the main checkout (git-ignored), not in the worktree.
- Rule: pending = transcript tail (cut off / failed send by sender / unanswered msg) + herdr blocked. Clauses 1/3 sampled in cswitch after `agent wait`, before /exit; clause 2 in cautoswitch after batch. Wake after batch via new cwake; CSWITCH_WAKE=off rollback; marker wake-pending/<pane>, 30 min expiry.
- Carried to 02/03: SendMessage tool_use/tool_result fixtures, real blocked row, `agent wait --until idle --until done` fix + stub test, clause 2 unverified in HANDOFF until real failed-send sample, squad-usage compare on first live batch, bash -n / py_compile gates. windows/*.ps1 out of scope.
- No QA blackbox PASS seen for 01; asked Manager.
