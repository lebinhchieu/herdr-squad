# Evidence 21 stale token save

## Behaviour
Change: `put()` in `templates/board/board.js`. A save answered `403` with JSON `{"error":"token required"}` gets a new token from `GET /api/session` (stored in `S.token`) and ONE re-send of the same snapshot (same body string). Any other answer ends the save at once: `403 host not allowed`, 400/413/415/507/5xx, network error, or a second refusal. The notes area is not touched until the final answer, so the PO sees no message while the retry runs. `bin/squadboard.py` is not in the diff. The only write call is still `PUT /api/ui`; the session fetch is a GET; no new storage key.

Test: `tests/test_squadboard_page.py` `StaleToken` (headless Chrome, stub fetch). Run: `python3 -m unittest tests.test_squadboard_page` (22 ok); `tests.test_squadboard_panels` and `tests.test_squadboard_ui` also ok (they reference board.js / the token guard).

| Case | Calls seen | Result | AC |
|---|---|---|---|
| PUT 403 `token required`, session, PUT 200 | PUT, GET, PUT; 2nd PUT has `new` token, body equal to 1st; notes hidden at both PUTs | `ok`, no note | T21.AC1, TA2, TA6 |
| PUT 403 `host not allowed` | PUT | `failed` | TA1 |
| PUT 403 token twice | PUT, GET, PUT (no 3rd) | `failed`; next save again PUT, GET, PUT | TA3 |
| PUT 403 token, retry 507 | PUT, GET, PUT | `unwritable`, note starts "Settings not shared. " + the T09 explanation | T21.AC4, TA4 |

- T21.AC3 / TA7: server unchanged. Existing `test_T09_AC5_no_token_wrong_host_or_content_type_leaves_file_unchanged` in `tests/test_squadboard_ui.py` (made-up/missing token -> 403, file unchanged) passes.
- TA5: each `put` call retries at most once on its own; the code has no shared counter, so two parallel stale saves each make at most 2 PUTs. Not a separate test (no matrix).
- T21.AC2 (header returns to "updated") is the existing poller, not touched.

TA8 steps (real restart, for QA whitebox): start `squad-board` on a fixed port, open the page, stop and restart it on the same port, click a font size, wait 1 s, read `board-ui.json` in the squad folder: the font is saved and no "could not be saved" note showed.

Return fix (QA blackbox FAIL on T21.AC4, Manager FINAL): the unwritable note now starts with "Settings not shared. " followed by the old text ("The settings file in the squad folder cannot be written. Settings are kept in this browser only."). This also settles the older T09.AC2 wording. Tests grepped for the old text: only `tests/test_squadboard_page.py` (updated); `test_squadboard_page`, `test_squadboard_panels`, `test_squadboard_ui` re-run.
