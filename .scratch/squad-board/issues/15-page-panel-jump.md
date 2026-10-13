Status: ready-for-agent
State: ready
Task ID: BRD-15
Blocked by: 12
Files touched: `bin/squad-board.html` (sections `panel` and its mirror part, plus `drawHeaderCard` in the `header` section for the selected-header mango outline: `view.selected`, 2.5 px stroke, as in round 6), `bin/squad-board` (`http` section only: new `handle_notes` and one route line in `do_GET`), `tests/test_board_notes.py` (new). Reviewer: qaw-board-2 (security).

# BRD-15: page side panel, Jump to pane, and the notes route

**Done when clicking an agent's header opens a side panel (round 6 look) with the agent's facts, last messages, a notes.md ↗ link that opens the notes file as text, and a Jump to pane button that focuses its herdr pane through the token-guarded endpoint.**

Read first: design-iteration-2.md (E14 and "Notes route", E24, E26), the side panel in the round 6 prototype, design.md "HTTP and security", spec stories 45 to 49. Replace only the `panel` section. The page never answers escalations or prompts agents (story 49): no such control exists.

## Technical AC (BRD-15)
1. **Content (round 6 panel):** name, role, pod, model, status; MONITOR: context tokens (raw), tokens in and out (raw, `—` if null), working and blocked totals (blocked red when non-zero), times woken (`wakes`); LAST MESSAGES: the last 3 sent or received by the agent in the viewed iteration (type in its colour, `→ peer` or `← peer`, task, text clipped); the **Jump to pane ↗** button (mango); the **notes.md ↗** link (E14). Selected header gets the mango outline.
2. **All text via `textContent`** (E18). A message text of 10,000 characters is shown clipped with a "show more" that expands it.
3. **Jump (E24):** `POST /jump/<agent>` with `X-Board-Token` from the page URL; shows `Jumped` on 200, otherwise the status and the error text; disabled while in flight and for retired agents; a missing token in the URL disables the button with an explanation.
4. **Open/close:** header click opens, second click, `Esc` or the close button closes; opening another agent replaces the content; the panel keeps working while state updates (no flicker, scroll position kept).
5. **Mirror:** `#side-panel`, `#notes-link` and the others as in the table.
6. **Notes route (server, E14 table "Notes route"):** Seam A tests in `tests/test_board_notes.py`, each against the real server on a temp fixture with `roles/<name>.notes.md` files:
   - success: 200, body equals the file, headers of step 8 exactly;
   - token: missing, wrong, repeated, empty, non-ASCII, 10 KB → 403 (never 500), no roster information leaks (a non-roster name with a bad token is 403, with a good token 404);
   - name: `../x`, `a/b`, `a%2fb`, `%2e%2e`, uppercase, over 32 chars, empty → 400 or 404 and no file read (a canary file outside `roles/` with a matching name is never returned);
   - symlink `roles/<name>.notes.md` → a file outside `roles/` → 404; a directory named `<name>.notes.md` → 404; missing file → 404; roster agent that is retired → 200;
   - size: a 2 MiB file returns exactly the first 1 MiB; invalid UTF-8 bytes do not raise;
   - Host/Origin: foreign Host 403; POST/HEAD/PUT → 405;
   - the token never appears in stderr or in any response body or header;
   - grep gate unchanged (`shell=True`, `eval`, etc. absent) and the file open uses a path built only from the validated name.
7. **Baseline AC 1 to 5, 7, 9, 10**; page technical AC 1 to 7.

## Behaviour AC (blackbox)
B1. **Header click opens the panel** for that agent; the panel shows role, model, token counts, working and blocked totals, woken count and the last messages, matching the data in the header and the log.
B2. **A different header** replaces the content; `Esc`, the close button or a second click on the same header closes it.
B3. **Notes link:** **notes.md ↗** opens a new tab showing the agent's notes file as plain text; the link works with the token already in the URL; a notes file that does not exist gives a plain 404 in the new tab and the page keeps working; editing the page URL's token to a wrong value makes the link answer 403.
B4. **Jump:** with a stub `herdr` on `PATH` that records its arguments, clicking **Jump to pane** records exactly `agent focus <name>` and the panel says it jumped; without the token in the URL the button is disabled; for a retired agent it is disabled.
B5. **A failing herdr** (stub exits non-zero) shows an error in the panel and the page keeps working.
B6. **No other action exists:** the page has no control to answer an escalation or prompt an agent.
B7. **Hostile message text** in the panel shows as plain text.

### QA whitebox additions (qaw-board)

(qaw-board adds points here.)

## Comments
