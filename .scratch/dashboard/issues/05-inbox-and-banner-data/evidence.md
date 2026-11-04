## Behaviour
No page yet (ticket 12 draws it). Checked on the ticket 02 fixture with the real `squad-inbox`; herdr from the recorded file.
- New reader `bin/squadboard_inbox.py`, route `GET /api/inbox` (found by ROUTE discovery). Output: `rows`, `count_choice`, `count_squad`, `others [{scope,n}]`, `banner {entries|None, reason}`, `parked`.
- AC1/AC3: rows oldest first (E1 26 h, unread item 1 h), fields id, title, age_s, blocks, options, kind, scope; option text unmodified, `recommended: true` on the recommended one. AC2: no rows, count 0.
- AC4: after `squad-inbox answer`, the row and count drop on the next read; a tree snapshot (sha + mtime) of the squad folder is equal after `read()` (no `inbox.jsonl` line, no lock file).
- Parked: an item parked whole (`From: E<n>`) is not a row and not counted; a parked point (`From: E<n> #<p>`) stays in.
- AC5/AC7: banner names agent, pane and scope (`fix-dev-02`, checkout) whatever the choice; herdr down gives `entries: null`, reason "herdr not running", `unknown: ["herdr"]`, never `[]`.
- AC6/AC8: choice `questions`, S3 `checkout` with a question, a ready branch and a prompt: `count_squad` 4, `others [{checkout, 3}]`, S3 rows absent from the choice rows; after S3's question is answered by CLI: 3 and 2.
- Cost (TA6): one `squad-inbox` call per open scope/goal/squad folder that has an inbox file (no transcripts, no git). Fixture, goal `alpha`: 0.15 s. One herdr call per `read()` (call counter test); the page-wide sharing with `/api/agents` is not built (two routes, two calls).
- **Open point (ticket 07 not merged):** ready-for-review counts come from `squadboard_tasks.ready_by_scope(sel)` -> `{scope: n}` if that exists, else `sel["ready_for_review"]` (used by the test); with neither, `unknown` lists `ready_for_review` and they count 0. Ticket 07 must export `ready_by_scope`, or the Manager names the function.
- Tests: `tests/test_squadboard_inbox.py` (10) pass. Also run: `test_board_fixtures`, `test_squadboard_agents`, `test_squadboard_list`, `test_windows_safe`, `test_no_bare_bash`, `test_old_language_inventory`. No `templates/` or printed text touched, so no grep of tests needed (TC.11).
- Real samples: `tests/fixtures/board/inbox/list-open.json`, `list-empty.json` (captures of `squad-inbox list --json --no-write`, version 1).
