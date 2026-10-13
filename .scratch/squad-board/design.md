# squad-board: technical design (iteration 1, server in replay mode)

**Owner:** tech-board. **Every ticket in `issues/` links here; read it before building.** If a ticket and this file disagree, ask tech-board.

## Decisions

| # | Decision | Value |
|---|---|---|
| D1 | Server file | `bin/squad-board`, one Python file, stdlib only, executable, no `.py` suffix (like the other `bin/` commands). No syntax newer than Python 3.9 (no `match`, no `X \| None` at runtime). |
| D2 | Command line | `squad-board --replay DIR [--port N] [--now ISO]`. `--replay` is required in iteration 1 (no flag → exit 2, "live mode arrives in iteration 2"). |
| D3 | Replay = squad folder + `replay/` | `DIR` is read as the squad folder (D8 layout). Live mode later reads `$SQUAD_DIR` plus herdr and `~/.claude*` through the same functions. |
| D4 | Default port | **7420**. Busy → try 7421..7440. `--port 0` = OS picks (tests use this). All busy → exit 1. |
| D5 | Fold-gap threshold | **180 s**. A gap **longer than** 180 s between two consecutive visible rows becomes one `gap` row. Constant `FOLD_GAP_S`. |
| D6 | "now" in replay | `--now ISO` flag. Without it: the latest `ts` in either log, or the wall clock if both are empty. The same value is `state.now`. |
| D7 | Wake window | A `working` event for agent B that is followed, within **2 s**, by a message to B counts as woken by that message (the hook stamps after the receiver may already have started). Constant `WAKE_WINDOW_S`. Unverified against live data; re-check in the iteration 3 live run. |
| D8 | Fixture / squad folder layout | See below. |
| D9 | Test layout | One test file per concern (below) plus one shared helper `tests/board_fixture.py`. Seam A only: tests run the real command and read HTTP. |
| D10 | Task IDs for this scope | `BRD-01` … `BRD-08`, same number as the ticket file. Every BLOCKED / HANDIN / PASS / FAIL / STATUS message names one. |
| D11 | Iteration filter | See "Iteration filter". |
| D12 | Server startup line | First stdout line, flushed: `squad-board: http://127.0.0.1:<port>/` (from BRD-05 on: `…/?token=<token>`). |

## Layout of the server file

**One file, sections in this order, each behind a `# --- section: <name> ---` marker line.** Later tickets replace only the body of their own function, so parallel branches merge cleanly. BRD-01 writes every function below; the ones owned by later tickets are stubs with the final signature.

| Section | Function(s) | Owner ticket | Stub returns |
|---|---|---|---|
| squad reader | `read_squad(dir)` → roster, scopes, escalations, iterations | 01 | real |
| log reader | `read_logs(dir)` → `(messages, activity)`; skips bad lines, drops repeated `msg_id` | 01 | real |
| columns | `build_columns(squad, messages, activity)` | 01 | real (status from latest event; totals 0; tokens null) |
| timeline | `derive_timeline(messages, activity, columns, now, selected_iteration, lowest_iteration=None)` → `{"rows", "bars", "agents": {name: {"working_s","blocked_s","wakes"}}}` | 02 | `{"rows": [], "bars": [], "agents": {}}` |
| tasks | `derive_tasks(messages, activity, upto_iteration)` → list | 03 | `[]` |
| needs-you | `derive_needs_you(squad, columns, activity)` → list | 03 | `[]` |
| tokens | `read_tokens(columns, replay_root)` → `{agent: {"context_tokens","tokens_in","tokens_out","model"}}` | 04 | `{}` |
| state | `build_state(dir, now, selected_iteration)`: calls all of the above in a fixed order, merges the results into `columns` | 01 | real |
| http | `make_server(...)`, `handle_root`, `handle_state`, `handle_events`, `handle_jump`, `check_request` | 01 (root, state); 05 (`check_request`, `handle_jump`, port fallback); 06 (`handle_events`) | `handle_events` / `handle_jump` → 501 |

- **`build_state` is pure:** files in, dict out, no globals except the token cache of BRD-04 (behind a `threading.Lock`; the server is threaded).
- **The server is `ThreadingHTTPServer` with `daemon_threads = True` from BRD-01**, so SSE (BRD-06) needs no change to startup.
- **Unknown fields are ignored, missing fields tolerated** everywhere (logs are an append-only contract owned by the hook).

## Folder layout (D8)

```
<DIR>/                       # the squad folder
  roster.md scopes.md escalations.md
  iterations/<n>.md          # TEMPLATE.md and non-numeric names ignored
  messages.jsonl activity.jsonl      # either may be missing
  roles/<agent>.notes.md     # optional
  replay/herdr.json          # {"agents": {"<name>": {"session_id": "<id>"}}}   (replay-only)
  replay/claude*/projects/<project>/<session_id>.jsonl      # transcripts (replay-only)
```

- **Committed fixtures** go in `tests/fixtures/board/<name>/` (BRD-08). **Test-specific fixtures** are built in a temp dir by `tests/board_fixture.py`.
- **Transcript roots** in replay: every `replay/claude*` folder. Live (later): every `~/.claude*`.
- **`replay/herdr.json`** is our own shape. Iteration 2's live adapter converts herdr's real snapshot into it.

## State JSON: fixed key list

**`GET /state?iteration=N` returns exactly these top-level keys. Additions are allowed, renames and removals need tech-board's DECISION.** Times are ISO strings as in the logs; durations are integer seconds.

| Key | Type | Notes |
|---|---|---|
| `now` | string | D6 |
| `iterations` | int[] | sorted, from `iterations/<n>.md` |
| `iteration` | int or null | current = highest; null when no iteration files |
| `selected_iteration` | int or null | `N` from the query, else `iteration`. An unknown or non-numeric `N` → 400 |
| `pods` | `[{name, size, agents[]}]` | pod order = column order |
| `columns` | list | see below |
| `rows` | list | see below; BRD-01 leaves `[]` |
| `bars` | list | see below; BRD-01 leaves `[]` |
| `tasks` | list | BRD-03 |
| `needs_you` | list | BRD-03 |

**`columns[]`:** `agent, role, pod, status, retired, notes_path, working_s, blocked_s, wakes, context_tokens, tokens_in, tokens_out, model`.

- `status` is `working`, `idle` or `blocked`. The latest activity event decides; `done` → `idle`; no events → `idle`.
- `retired` is true when the roster Status cell is not `live`.
- `notes_path` is `roles/<agent>.notes.md` when that file exists, else null.
- Token fields and `model` are null when unknown (the page prints "—").

**`rows[]`:** each has `id` (0-based index after folding), `kind` and `ts`.

| kind | extra keys |
|---|---|
| `message` | `from, to, type, task, text, msg_id` |
| `status` | `agent, status` (`working`/`idle`/`blocked`/`done`), `duration_s` (only on a row that ends a bar) |
| `gap` | `seconds, from_ts, to_ts` (`ts` = `from_ts`) |

**`bars[]`:** `agent, start_row, end_row (null if open), start_ts, end_ts (null if open), self_start (bool), open (bool), duration_s (to now if open), blocked: [{start_row, end_row, start_ts, end_ts, duration_s}]`.

**`tasks[]`:** `id, state (building|blocked|checking|returned|done), returns (int), last_ts, last_type`. Order = first appearance.

**`needs_you[]`:** `id` (stable string), `kind` (`blocked`|`escalation`|`manager_idle`), `text`, `agent` (null for escalations), `since` (ts or null).

## Parsing rules (BRD-01)

- **Markdown tables:** a table is the run of `|` lines under its header; skip the `---` separator row; split on unescaped `|`; strip `**` and backticks and whitespace from cells.
- **`scopes.md`:** only the first table (the second is the size-change log). `size` = Size cell as plain text.
- **Trailing parentheses (Q1 of BRD-01):** from the roster Scope cell and the scopes.md Scope and Size cells, strip `**` and then one trailing `(...)` group. Live rows: roster `board (S+QAW)` → pod `board`; scopes Size `**S + QA whitebox** (exception, …)` → `S + QA whitebox`. A test uses the live rows verbatim.
- **Pod of an agent** = roster Scope cell. Scope `all` (the Manager) is its own pod with `size` null. **Manager first:** the roster row whose Role is `Manager`. Then pods in order of first appearance, agents in roster order.
- **Agent in a log but not in the roster:** joins the end of the pod whose name equals one of its `-`-separated name parts (`dev-board-3` → pod `board`); no match → trailing pod `(unlisted)`, role null. The Manager's pod (`all`) is never a match target. A roster row with an empty Agent, Role or Scope cell (e.g. a short row `| only |`) is skipped. This is tech-board's reading of spec "join the end of their pod"; flag it if it looks wrong.
- **`msg_id` dedupe:** first record wins.
- **Timestamps:** replace a trailing `Z` with `+00:00`, then `datetime.fromisoformat` (the hook writes `…03.123Z`; 3 fractional digits parse on 3.9). A `ts` that is not a string, does not parse, or has no zone (naive) → the record is skipped like a bad line.
- **Wrong-typed records:** a valid JSON line that is not an object, or fields of the wrong type (`to`/`text`/`type` not strings, `iteration` not an int) → skipped, or the field treated as null. Never an exception.
- **Query `iteration`:** only `^[0-9]{1,6}$`; anything else, an empty value or a repeated parameter → 400.

## Timeline rules (BRD-02)

**Order:** all records sorted by `ts`; ties: message before status, then file order.

**Bar logic** (spec prototype, made precise):

| Event | Effect |
|---|---|
| message a→b | if a has no open bar: start a's bar here (`self_start` true). If b has no open bar: start b's bar here (`self_start` false). Starting is a no-op when a bar is open. |
| `working` for X | open bar with an open blocked segment → close the segment, row emitted. Open bar, no open segment → nothing, **no row**. No open bar → start a bar (`self_start` true) here, unless D7 applies: then the following message starts it (`self_start` false) and this event emits no row. |
| `blocked` for X | no open bar → start one first (`self_start` true). Open a blocked segment. Row emitted. A `blocked` while a segment is already open: no row, no new segment. |
| `idle` or `done` for X | open bar → close it (closes an open blocked segment too), row emitted with `duration_s`. No open bar → ignored, no row. |
| `unknown` | ignored |

- **`wakes`** = number of bars with `self_start` false.
- **Totals:** `working_s` = sum of bar durations including blocked time; `blocked_s` = sum of blocked segments. An open bar runs to `now`.
- **Fold:** after building the visible rows, insert one `gap` row between two consecutive rows more than `FOLD_GAP_S` apart. Then assign `id`s. No gap row before the first or after the last.

## Iteration filter (D11)

| Part of the state | Source |
|---|---|
| `rows`, `bars` | records tagged `selected_iteration` only (a bar belongs to the iteration of its start row). Derivation still runs over **all** records in time order, so a bar open across a boundary stays correct. |
| `tasks` | messages tagged ≤ `selected_iteration` (state as of the end of that iteration) |
| column `working_s`, `blocked_s`, `wakes`, `status`, tokens, and `needs_you` | **whole run, always live** (not filtered) |
| record with `iteration: null` | counts as the lowest iteration number; with no iteration files, nothing is filtered |

## Needs-you and tasks (BRD-03)

- **Blocked:** an agent whose latest activity event is `blocked`. `id` = `blocked:<agent>:<event ts>`.
- **Escalation:** each row of `escalations.md` whose Answer cell is empty. `id` = `escalation:<#>`.
- **Manager idle:** the Manager's latest event is `idle` or `done` (at least one event exists) **and** the current iteration's `## PO check-in` section has an empty **Done** bullet and an empty **Next** bullet. `id` = `manager_idle:<iteration>`. "Decisions from the PO" is ignored: the PO fills it during the iteration, so it can't mean "check-in not held". This is tech-board's reading of spec "PO check-in section still empty"; reported to the Manager.
- **A BLOCKED message is never a needs-you item.** It is a row and a task state only.
- **Return count (BRD-18, BINDING, Manager 2026-10-12):** a FAIL counts a return only if a HANDIN came after the last counted FAIL, or none was counted yet; `returns` = the number of HANDIN→FAIL rounds. Copies of one FAIL sent to several recipients, two QAs failing one HANDIN, and a STATUS, DECISION or BLOCKED landing between copies all count once. No time window. State after any FAIL is `returned`. Real data: qaw-board sends one FAIL to the Developer, the Manager and the Tech Lead within 0.5 s (once 2.2 s apart).
- **Done is sticky (BRD-18, FINAL; Manager's last word 2026-10-12):** once `done`, STATUS, DECISION, ASK and ANSWER naming the task do not change its state (for example `STATUS BRD-01: PASS from qaw-board`). HANDIN (→ `checking`), FAIL (→ `returned`, counted) and BLOCKED (→ `blocked`) reopen it. `last_ts` and `last_type` always follow the latest message.
- **STATUS and DECISION on a task that is not done** keep the spec table: they set `building`, from `blocked` and `returned` too (a Developer's `STATUS BRD-xx: fixing` after a FAIL is the normal way a returned task goes back to building). Known and accepted: another agent's STATUS also clears `blocked`. A test pins both.
- **Task state table:** as in the spec. `blocked` returns to `building` at the BLOCKED sender's next `working` event, unless a later message already moved the state. Last write wins. `returns` counts FAILs.
- **Known limitation, per spec story 44:** an ASK that merely mentions `BR-014` makes a task `BR-014`. Accepted for now.

## Tokens (BRD-04)

- **Session lookup:** `replay/herdr.json` gives `session_id`; accept only `^[A-Za-z0-9_-]{1,64}$`. Find `replay/claude*/projects/*/<session_id>.jsonl`; dedupe roots and files by real path.
- **Per assistant reply with `message.usage`:** in = `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`; out = `output_tokens`. **Several lines can share one `message.id`: count each id once (last line wins).**
- **Fields:** `context_tokens` = in of the last reply; `tokens_in` = sum of in; `tokens_out` = sum of out; `model` = last reply's `message.model`. **Replies with model `<synthetic>` are ignored entirely** (checked 2026-10-12 against real transcripts: they carry zero usage, so counting one as the last reply would show context 0).
- **Incremental:** keep a byte offset per file, read only appended bytes, never consume a last line without its newline.
- **Missing or unreadable transcript, or no usage lines:** all four values null.
- Before writing fixtures, look at one real transcript in `~/.claude/projects/` to confirm the field names. Read it only; never copy it into the repo.

## HTTP and security (BRD-01, 05, 06)

| Item | Rule |
|---|---|
| Bind | `127.0.0.1` literally, never `""` or `0.0.0.0`. |
| Token | `secrets.token_urlsafe(16)`, new each run, printed in the startup URL, never in `/state`. |
| Host check | Every request: `Host` must be `127.0.0.1:<port>` or `localhost:<port>`, else 403 (DNS rebinding). |
| Read endpoints | `GET /`, `/state`, `/events`: no token (Host check applies). Responses carry `Cache-Control: no-store`; JSON also `X-Content-Type-Options: nosniff`. No CORS headers. |
| Jump | `POST /jump/<name>` with header `X-Board-Token`. Order of checks: Host/Origin (every route) → method → token (`hmac.compare_digest` on UTF-8 **bytes**, so a non-ASCII header gives 403, not 500; repeated header with different values → 403) → name regex `^[a-z][a-z0-9_-]{0,31}$` → name in parsed roster. Then run `["herdr", "agent", "focus", name]` (argv list, no shell, 5 s timeout). |
| Jump codes | bad Host or Origin 403; wrong method 405; missing or wrong token 403; bad name 400; not in roster 404; success 200 `{"ok": true}`; herdr failed or missing 502. |
| Origin | If an `Origin` header is present it must be `http://127.0.0.1:<port>` or `http://localhost:<port>`, else 403. |
| Replay and jump | Replay mode runs the real `herdr` found on `PATH`; tests put a stub `herdr` there that records its argv. |
| Notes route (iteration 2) | `GET /notes/<name>?token=…` is added by BRD-15 under the rules in `design-iteration-2.md` "Notes route"; the only route that takes the token in the query and the only one that reads a file for a request. |
| Untrusted text | Message `text` is untrusted. The server only emits JSON; the page (iteration 2) must draw it with `fillText`/`textContent`, never `innerHTML`. |

## Decisions on qaw-board's additions (2026-10-12)

Each ticket's `### QA whitebox additions` stands as written; these are the points that needed a decision.

| # | Ticket | Decision |
|---|---|---|
| 1 | 01 | Strip trailing `(...)` from Scope and Size cells (see Parsing rules). Unknown-agent pod match: first matching name part in name order. `log_message` is silenced in `BaseHTTPRequestHandler`; the test helper drains stdout and stderr continuously. |
| 2 | 02 | A bar or blocked segment whose closing row is not in the filtered `rows` → `end_row` null, `end_ts` real, `open` false. Gap rows are computed after filtering, so a gap across an iteration boundary is shown in neither view. Durations are floored to whole seconds per bar and per blocked segment; totals sum those integers; never negative (clock skew → 0). |
| 3 | 05, 01 | Token compared as bytes. Host/Origin is checked before the method (a foreign Host gets 403 whatever the method). A retired roster agent → 404 on jump. |
| 4 | 06 | `POLL_S` and `KEEPALIVE_S` may be overridden by env `SQUAD_BOARD_POLL_S` and `SQUAD_BOARD_KEEPALIVE_S`, read once at startup, documented in a comment. One shared watcher thread with a `(size, mtime_ns)` signature per watched file; state is rebuilt only when the signature changes. |
| 5 | 03 | `unknown` events are ignored everywhere (status, blocked, timeline). Retired agents are skipped in `needs_you`. Only an **empty** Answer cell is unanswered; `—` or `-` counts as answered. A row with fewer cells than the header is unanswered. |
| 6 | 04 | A usage field that is not a non-negative int (string, float, null, bool, negative) counts as 0 for that field; the reply is still counted. A shrunk or replaced file is re-read from the start. |
| 8 | 05 | `allow_reuse_address` stays on (Python's default), `SO_REUSEPORT` never. With reuse off, a restart within ~60 s cannot rebind the default port (TIME_WAIT), which breaks the fixed default port. A test restarts the server on the same port. |
| 9 | 03 | An escalation row counts only if it has a `#` cell or a Question with text; fully blank rows are skipped. A heading line inside `## PO check-in` ends the previous bullet's continuation text. |
| 10 | 05 | F2: a Seam A test with a listening occupant that sets SO_REUSEADDR and SO_REUSEPORT; the server must pick another port. No grep-gate addition. F3: a query string on `/jump/<name>` is ignored (same as every route); a test pins 200 and the argv. Exotic verbs (`BREW`, `TRACE`, `CONNECT`) may answer 501 before the Host check: no data or action behind it, so row 3 holds for the verbs the handler defines. No Sec-Fetch-Site check: the token plus the absent CORS headers cover it. A handler socket timeout is decided in BRD-06 (it touches the same code as the slow-client point). |
| 7 | 07 | Q1 and Q2 are superseded by the widened AC1 (rule line plus the one STATUS example line). Already PASSed. |

## Notes for iteration 2

- **Recorder timestamps:** the live activity recorder must stamp `YYYY-MM-DDTHH:MM:SS.mmmZ` (3 fraction digits), because `fromisoformat` on Python 3.9/3.10 accepts only 3 or 6 digits.

## Technical AC

**Baseline for every ticket** (qaw-board's 12 points, amended by tech-board; qaw-board adds per-ticket points under each ticket's own `## Technical AC`):

1. **Seam A only.** Tests start the real `bin/squad-board --replay <tmp fixture> --port 0` and assert on HTTP. No imports of the server's internals.
2. **Red, then green.** Dev-evidence shows each behaviour's failing test first (commit order or pasted red output).
3. **Fixtures only.** Never the real `~/.claude*`, herdr or squad dir.
4. **Stdlib, one file, Python 3.9-safe.** `python3 -m unittest discover -s tests` green, including the 14 Seam B tests. Run with `PYTHONDONTWRITEBYTECODE=1`.
5. **Deterministic.** `--now` in tests; port 0; no sleeps for correctness (poll with a deadline); the helper kills the server in `tearDown`.
6. **Security rules** of the table above (BRD-05 tests them).
7. **Robust.** Bad JSONL line, missing log, missing or bad transcript, empty fixture folder → `/state` 200, no traceback on stderr.
8. **State contract:** the key list above.
9. **CLAUDE.md:** surgical, no dead code, comments say why. Touch only the files the ticket lists.
10. **Evidence:** `$SQUAD_DIR/evidence/BRD-NN/dev-evidence.md` with test output, a `curl` of `/state`, the commit id. Not committed (the squad folder is untracked).
11. **Needs-you:** BLOCKED message is not a needs-you item (BRD-03, explicit test).
12. **Process ticket (BRD-07):** diff limited to the one rule.

**Answers to qaw-board's two questions:** (1) yes, the fixed key list above is part of BRD-01's AC. (2) `now` comes from the `--now` flag (D6), not from the fixture.

## Migration, compatibility, deploy

- **None.** All new files; no schema, API or data of another team changes. The logs are written by the already-merged hook; the reader tolerates unknown and missing fields.
- **Deploy plan:** nothing to run. The PO merges branches `squad/dev-board-N` into `squad-board-spec`; BRD-01 first (everything else builds on it).

## Why

- **One file, stubbed sections:** the spec demands one file; stubs with final signatures let three Developers fill three functions without touching each other's lines.
- **No token on read endpoints:** the Host check plus missing CORS stops other web pages; a token on every read adds friction and no real protection against a local process, which can read the squad files anyway.
- **Real `herdr` on PATH in replay:** lets tests prove that refused jumps run nothing and accepted ones pass one argv element, without a dry-run branch in the server.
