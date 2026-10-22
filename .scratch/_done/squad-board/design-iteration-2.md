# squad-board: technical design, iteration 2 (live recorder, live mode, the page)

**Owner:** tech-board. **Read `design.md` first; this file adds to it and changes nothing there unless it says so.** Tickets BRD-10 to BRD-17 link here. Base for every ticket: BRD-09's passed sha (the merged iteration 1 server). BRD-08 (demo fixture) is stacked on BRD-09 too, so BRD-17 merges 08 as well; no iteration 2 ticket needs the demo fixture.

## Decisions

| # | Decision | Value |
|---|---|---|
| E1 | Live mode | `squad-board` with no `--replay`: squad folder = `$SQUAD_DIR`, else `<git toplevel>/squad`, else `./squad`. Replay mode stays exactly as is. |
| E2 | herdr socket | `$HERDR_SOCKET_PATH`, else `~/.config/herdr/herdr.sock`. Newline-delimited JSON, each request `{"id", "method", "params"}`. Snapshot: method `session.snapshot` (result `.snapshot.agents[]` has `name`, `pane_id`, `agent_status`, `agent_session.value` = session id). Subscribe: `events.subscribe` with `params.subscriptions` = one `{"type":"pane.agent_status_changed","pane_id":<id>}` per agent pane plus `{"type":"pane.created"}`. Event frames carry `event` and `data` (`pane_id`, `agent_status`, no name, no time). The Developer captures one real frame of each kind once (read-only, via the socket) and builds the fake from it. |
| E2a | Subscriptions (ruling 2026-10-13, BRD-10) | herdr refuses a status subscription without `pane_id` and resets a subscribed connection that sends another request. So: snapshots use their own short connection; the recorder re-subscribes on a new connection (old one closed) when the pane set changes. Replaces "one subscription" wording in E2. |
| E20a | Header name cut (ruling 2026-10-13) | Names ending `-<digits>` are cut in the middle and keep the suffix; others are cut at the end. Fixed in BRD-12 (B9), before 13..16 branch from it. No hover title on the canvas: the full name is in the mirror and in BRD-15's panel. The 7 px text floor of the blocked card stays as built. |
| E3 | Which agents the recorder writes | Only names found in `roster.md` (re-read when an unknown name appears, at most once per second). Known loss: events of an agent before the Manager adds its roster row. Re-check in the iteration 3 live run. |
| E4 | Initial sync | On start and after every reconnect: take a snapshot; for each rostered agent whose snapshot status differs from its last recorded status (or has none), append one activity record. Nothing else is back-filled. |
| E5 | Activity record | `{"ts": "YYYY-MM-DDTHH:MM:SS.mmmZ", "agent", "status", "iteration"}`; `ts` has exactly 3 fraction digits (Python 3.9 `fromisoformat`); iteration = highest numbered `iterations/<n>.md` at write time (null if none). One write per record, under `flock`, append mode. |
| E6 | Reconnect | herdr missing or dropped: the server keeps serving from files; the recorder retries after 1, 2, 4, … 30 s (cap), prints one stderr line per outage, re-syncs per E4. |
| E7 | Live `now` | In live mode `now` is the wall clock at each request (UTC, whole seconds). `--now` is replay-only (error in live mode). |
| E8 | Token refresh | Transcripts are read when a state is built. The SSE watcher (BRD-06) also rebuilds every `TOKEN_REFRESH_S = 30` while any agent is `working`, and whenever `activity.jsonl` grows (a bar end). |
| E9 | Page file | `bin/squad-board.html`, one file, one `<script>`, no framework, no external request (no CDN, no web font, no image URL). The server reads it on every `GET /` (no caching), from the directory of the resolved script path. |
| E10 | Page headers | `GET /` also sends `Content-Security-Policy: default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'`, `Referrer-Policy: no-referrer`. |
| E11 | State additions (allowed by design.md) | `live` (bool: true in live mode), needed for the "replay" banner. No path leaves the server. |
| E12 | Message colour for BLOCKED | The spec lists no colour for BLOCKED messages: use blocked red `#DB3B22`. An untyped message (type null) is muted `#857A68`, label `msg`. |
| E13 | Task column colours | blocked `#DB3B22`, building `#0C8A80`, checking `#9A40CF`, returned `#CE1D6C`, done `#368A1E`. `returns >= 2` adds a mango `#E8820E` "↺2" chip (the Manager steps in at 3). |
| E14 | Notes file (Manager's ruling 2026-10-12, overrules my first plan) | The side panel shows a link **notes.md ↗** to `GET /notes/<name>?token=<token>`, opened in a new tab (`target=_blank`, `rel="noopener noreferrer"`). The route is read-only and serves `<squad folder>/roles/<name>.notes.md` as text. Rules below ("Notes route"). This is the one exception to BRD-01 Q9 (no file serving): the path is built from a validated roster name, never from the request path. |
| E15 | Canvas size | The canvas is **viewport-sized**, never row-count sized (browsers cap canvas height). A spacer element gives the scroll height `rows * ROW_H`; the canvas is sticky and draws only rows in view. |
| E16 | Draw loop | `requestAnimationFrame` runs only while something animates (an arrow drawing in, a blocked pulse, an open-bar timer, a notification fade). Otherwise the page is idle (no CPU). |
| E17 | Text mirror | Alongside the canvas the page keeps an accessible, visually hidden DOM mirror of everything the canvas shows (hooks below). It makes the page testable without pixel reading and readable by screen readers. It is built with `textContent` only. |
| E18 | Untrusted text | Message text, agent names and task IDs are drawn with `fillText` or set with `textContent`. `innerHTML`, `outerHTML`, `document.write`, `eval`, `new Function` never appear in the page. |
| E19 | Time display | No time column (the Manager dropped it; it is not in the round 6 look). Durations on bars, end markers and the panel: `12s`, `4m 05s`, `1h 02m`. Header totals are compact like the prototype: `7m` (minimum `1m` once non-zero), `1h05`. Tokens: raw integer with thousands separators (`123,456`), `—` when null. Open-bar timers tick from `state.now` offset by the browser clock (offset = `Date.parse(state.now) - Date.now()` at receipt). |
| E20 | Layout numbers (from the round 6 prototype) | `ROW_H = 30`. Needs-you card at y 14, 46 px tall. Pod bands start at y 72 with the label at y 90. Header cards at y 100, 66 px tall. Rows start at y 180. Task column 230 px wide including its 16 px margin. Columns share the remaining width equally, minimum 84 px; at 1280 px wide, 12 live columns fit with no horizontal scroll. A retired agent with no row or bar in the selected iteration is a 24 px stub. Longer names are truncated with `…`; the full name is in the mirror and a `title`. |
| E21 | Following | Following = scrolled within 40 px of the bottom. New rows keep the bottom in view while following. A scroll up beyond 40 px pauses; the **↓ live** button shows the count of rows that arrived since; clicking it scrolls to the bottom and resumes. |
| E22 | Iteration picker | A `<select>` of `state.iterations`, default the current one. Choosing another iteration reloads `/state?iteration=N`, reconnects the stream with the same `N`, stops following, and shows a "Replay of iteration N" banner. Choosing the current one returns to live. |
| E23 | Notifications | A **Enable alerts** button asks for permission once (user gesture) and hides when granted or denied. A new needs-you `id` not in the seen set fires a `Notification` and a soft chime (WebAudio, two sine notes, gain ≤ 0.08) and sets the tab title to `(n) squad board`. Items present at page load count as seen. The seen set lives in `localStorage` key `squad-board.seen:<origin>` (ids only, pruned to ids still current plus the last 200). A closed audio context or denied permission is silent, never an error. |
| E24 | Jump from the page | `POST /jump/<agent>` with header `X-Board-Token` taken from `?token=` in the page URL; result shown in the panel (`Jumped`, or the HTTP status and error text). The button is disabled for retired agents. |
| E26 | The look | **Round 6 is the look** (`~/workspace/chat/squad-board-round6.html`, the PO-confirmed prototype). Developers open it in a browser and match it; the palette is the spec's. What changes from the prototype because the spec says so: header shows raw context tokens, not a percentage or meter; no model-window table anywhere; names are the real agent names (no abbreviation) truncated with `…`; task and message labels use real task IDs. Matched items: needs-you card with a mango left edge, pulsing dot, `N need you`, items separated by thin dividers, the iteration picker and `↓ live` at its right; translucent tinted pod bands (Manager's band mango without a label, other pods teal, blue, purple, pink, green, yellow in order) labelled `POD · SIZE` in small caps; header cards with status dot (pulsing ring while working or blocked), name, `⏱` left, `⛔` right, tokens right-aligned; dashed column rails; 14 px bars with teal tint and border, red hatch for blocked, pulsing end dot and a `⏱ time` pill on an open bar; a diamond marker with the status word (`idle · 4m 05s` at a bar end) on status rows; arrows 2.2 px with a filled head and a pill label `TYPE TASK-ID` at the midpoint; gap rows as a full-width pill `⋯ N min quiet ⋯`; task column as a card headed `TASKS`, grouped blocked, building, checking, returned, done, each group a coloured label with a rule and chips with a coloured left edge; side panel as a card with a mango border. |
| E25 | Page source layout | Sections with `<!-- section: name -->` / `// --- section: name ---` markers, stubs with final signatures (same method as the server): `state`, `layout`, `header`, `sequence`, `tasks`, `follow`, `picker`, `panel`, `alerts`, `mirror`. BRD-12 writes all; tickets 13 to 16 replace only their own section. |

## Text mirror hooks (the contract blackbox tests read)

**The mirror is a `<div id="board-text">` kept in the DOM (visually hidden with the clip pattern, never `display:none`). Hooks use `data-*` attributes and ids; text is what the canvas shows.**

| Element | Attributes | Text |
|---|---|---|
| `#needs-you` | `data-count="N"` | heading text "Needs you" plus count |
| `#needs-you li` | `data-kind`, `data-id` | the item text |
| `#iteration-picker` | the `<select>` itself | options `Iteration N` |
| `#replay-banner` | present only when viewing a non-current iteration | "Replay of iteration N" |
| `#pods li` | `data-pod`, `data-size` | pod name and size |
| `#columns li` | `data-agent`, `data-status`, `data-retired`, `data-collapsed` | name, role, status word, `⏱ 4m 05s`, `⛔ 1m 10s` only when non-zero, tokens text |
| `#rows li` | `data-row-id`, `data-kind`, `data-type`, `data-task`, `data-from`, `data-to` | for a message `TYPE TASK-ID from → to`; for a status row the status; for a gap `⋯ N min quiet` |
| `#bars li` | `data-agent`, `data-start-row`, `data-end-row`, `data-self-start`, `data-open`, `data-blocked-segments` | duration text; self-start marked `⟲` |
| `#tasks li` | `data-task-id`, `data-state`, `data-returns` | `BRD-01 checking ↺1`; order = the drawn order: grouped blocked, building, checking, returned, done, inside a group by first appearance |
| `#live-state` | `data-following="true\|false"` | "Live" or "Paused" |
| `#live-button` | hidden unless paused; `data-new-rows="N"` | `↓ live` plus count |
| `#side-panel` | `data-agent` when open | role, pod, model, status, context tokens, tokens in/out, working, blocked, woken count, last messages |
| `#notes-link` | `href` = `/notes/<name>?token=...` | `notes.md ↗` |
| `#jump-button`, `#jump-result` | | button label / result text |
| `#alerts-button` | | `Enable alerts`; hidden once decided |
| `#clock-offset` | | not required |

Row, bar and needs-you order equals the order in `/state`; tasks follow the drawn order above.

## Notes route (BRD-15)

**`GET /notes/<name>?token=<token>` returns an agent's notes file as plain text. A browser link cannot send a header, so this one route takes the token in the query. Everything else about it is as strict as jump.**

| Step | Rule |
|---|---|
| 1 | Host and Origin check first (`check_request`), every method. |
| 2 | Method must be `GET`; other methods 405. |
| 3 | Token: the `token` query parameter, exactly one, compared with `hmac.compare_digest` on UTF-8 bytes; missing, wrong or repeated → 403. A refused token never reveals roster membership. |
| 4 | Name must match `^[a-z][a-z0-9_-]{0,31}$` → else 400. |
| 5 | Name must be a roster agent (live or retired, since notes outlive an agent), read from `roster.md` per request → else 404. |
| 6 | Path is built as `<squad folder>/roles/<name>.notes.md` from the validated name only. `realpath` must stay inside `<squad folder>/roles` and be a regular file (symlinks leading out are refused, 404). Missing file 404. |
| 7 | Reads at most 1 MiB; invalid UTF-8 replaced. |
| 8 | Headers: `Content-Type: text/plain; charset=utf-8`, `X-Content-Type-Options: nosniff`, `Content-Security-Policy: sandbox; default-src 'none'`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store`, `Content-Disposition: inline`. |
| 9 | The token in the URL never appears in stderr (access log stays silenced), responses or `/state`. |

## Page layout

```
┌ needs-you bar (mango) : "Needs you · 2"  [item] [item]            iteration picker · ↓ live · 🔔 ┐
├ pod band : [ Manager ] [ BOARD · S + QA WHITEBOX ........ ] [ OTHER POD ........ ] ─────────────┤ task
├ headers : ● manager   ● tech-board  ● qaw-board  ● dev-board-7  ...                            ┤ column
│           ⏱ 12m  ⛔ 1m  123,456                                                                  ┤
├ sequence : ─── ASK BRD-01 ───▶   | bars | arrows | ⋯ 7 min quiet ⋯                                ┤
```

Side panel: slides over the sequence from the right (width 360 px) when a header is clicked; click the header again, the close button or `Esc` closes it.

## Technical AC for the page tickets (add to the baseline, which still applies)

1. **No external request:** the page text contains no `http://` or `https://` URL and no `src=`/`href=` to another origin. A Seam A test reads `GET /` for this.
2. **E18 forbidden list** absent from the page (Seam A grep test on `GET /`).
3. **CSP and Referrer-Policy headers** of E10 on `GET /` (and on no other route needs them).
4. **Palette:** every colour in the page is in the allowed set: the spec's palette values, plus three more from the same Mango Parrot light theme file that the PO-confirmed round 6 look uses (`#FFFDF9` card, `#D6CCBC` dashed lines and dividers, `#CE7000` mango-dark text) and `#FFFFFF` for text on the mango button. Tints are allowed as `rgba(...)` of those colours or as 8-digit hex whose first six digits are in the set. A Seam A test greps every hex literal in the page against this set and fails on any other.
5. **Python 3.9-safe server code**, same as iteration 1.
6. **Developer evidence:** Playwright screenshots in replay mode at 1280, 1600 and 1920 px wide for the ticket's behaviours, in `$SQUAD_DIR/evidence/BRD-NN/`; use the `playwright-cli` skill. Screenshots are reviewed by eye, not asserted.
7. **Stubs/dead code:** none left in the ticket's own section.

## Risks

- **One HTML file, five Developers:** the section-marker method kept the server mergeable; the page gets the same. BRD-17 resolves conflicts.
- **Fake herdr drifts from the real socket:** mitigated by capturing real frames once (E2) and by the iteration 3 live run.
- **E3 roster filter can lose the first events of a new agent:** accepted, see E3.
- **Canvas text is not testable by pixels:** that is what the mirror (E17) is for. Pixel look is checked by eye on screenshots.
