Status: resolved
State: done
Task ID: BRD-01
Blocked by: none
Files touched: `bin/squad-board` (new), `tests/board_fixture.py` (new), `tests/test_board_state.py` (new)

# BRD-01: server skeleton, squad reader, columns, `GET /state`

**Done when `bin/squad-board --replay <fixture> --port 0` serves a correct `GET /state` with pods, columns and iterations, and every later ticket can fill its stub without touching another ticket's lines.**

Read first: `.scratch/squad-board/design.md` (all of it), spec sections "Modules", "Data contracts", "Testing Decisions".

## Build

- **`bin/squad-board`** with every section and function in design.md "Layout of the server file", in that order, each behind a `# --- section: <name> ---` marker. Sections owned by later tickets are stubs with the final signature and the stub return value from the table.
- **Command line:** D2, D4 (default port constant; no fallback yet, that is BRD-05), D6 (`--now`), D12 (startup line, flushed).
- **Server:** `ThreadingHTTPServer`, `daemon_threads = True`, bound to `127.0.0.1`.
- **Routes:** `GET /` returns a minimal placeholder HTML page (200). `GET /state[?iteration=N]` returns the JSON of design.md "State JSON". `GET /events` and `POST /jump/<name>` return 501 for now. Any other path 404.
- **Readers and columns:** parsing rules in design.md "Parsing rules".
- **`tests/board_fixture.py`:** the shared helper every later test file imports. API:
  - `Fixture()`: temp dir, cleaned up with `addCleanup`/`close()`.
  - File writers: `write(relpath, text)`, `append_jsonl(relpath, obj)`; conveniences `roster(rows)`, `scopes(rows)`, `escalations(rows)`, `iteration(n, text=None)`, `message(**fields)`, `activity(**fields)`, `herdr(agents)`, `transcript(root, project, session_id, lines)`. Defaults make a valid minimal record; a test overrides only what it checks.
  - `fx.start(now=None, port=0, env=None)` → `Server`: runs the real command, reads the startup line, exposes `.base`, `.token` (None until BRD-05), `.state(iteration=None)` (GET + `json.loads`), `.get(path, headers=None)` → `(status, headers, body)`, `.post(path, headers=None)`, `.stop()`. Wait for the startup line with a deadline (10 s), kill the process in cleanup, capture stderr.
  - Later tickets must not need to edit this file; if one does, it asks tech-board.

## Technical AC (BRD-01)

1. **Key list:** `/state` has exactly the top-level keys of design.md (`now, iterations, iteration, selected_iteration, pods, columns, rows, bars, tasks, needs_you`); each column has exactly the column keys. A test asserts both lists.
2. **Reader:** roster, scopes (first table only), escalations and iterations parsed from a fixture. Test with the bold-marked Size cell (`**S + QA whitebox**` → `S + QA whitebox`), a cell containing `\|`, and `TEMPLATE.md` in `iterations/`.
3. **Order and pods:** Manager first; pods by first appearance; roster order inside a pod; `pods[].size` from `scopes.md`, null for the Manager's pod.
4. **Unknown agent:** an agent only in a log joins the end of its pod (name-part match), else the `(unlisted)` pod. Both tested.
5. **Status:** from the latest activity event; `done` → `idle`; no events → `idle`; `retired` from the roster Status cell; `notes_path` only when the file exists.
6. **Iterations:** `iterations`, `iteration` (highest), `selected_iteration` from `?iteration=N`; `?iteration=abc` and an unknown N → 400; no iteration files → `iteration` null and no error.
7. **Robustness (baseline 7):** bad JSON line, missing `messages.jsonl`/`activity.jsonl`, record with a bad `ts`, repeated `msg_id`, empty fixture folder (no roster) → 200 and an empty but well-formed state, empty stderr.
8. **Host check is BRD-05's.** Not required here, but every request handler calls a `check_request(handler)` that returns True for now, so BRD-05 and BRD-06 share one entry point.
9. **Placeholder and stubs:** the stub sections exist with the final signatures (QA reads the file). `/` returns 200 HTML.
10. **Suite:** `python3 -m unittest discover -s tests` green, 14 Seam B tests untouched.

### QA whitebox additions (qaw-board)
Q1. **Real-data shape.** The live `squad/roster.md` has Scope cell `board (S+QAW)` while `scopes.md` has Scope `board` and a Size cell `**S + QA whitebox** (exception, see process.md → Sizes; escalation #1)`. A test uses these two rows verbatim. Pod name, `pods[].size` and the name-part match for `dev-board-3` must work on them. **Needs a tech-board DECISION** (see message: proposal = pod name is the Scope cell with a trailing `(...)` stripped; size = Size cell with bold markers removed and a trailing `(...)` stripped).
Q2. **Wrong-typed records:** a JSON line that is valid but not an object (`[1]`, `3`, `"x"`, `null`), `ts` as a number, `to`/`text`/`type` as non-strings, `iteration` as `"1"`, `"abc"` or `1.5` → skipped or tolerated, 200, empty stderr. Timestamps in the hook's real form `2026-10-12T00:27:03.123Z` parse; a naive `ts` (no zone) must not raise `TypeError` when compared (skip it or treat as UTC, state which).
Q3. **Query parsing:** `?iteration=` accepts only `^[0-9]{1,6}$`; `+1`, `1_0`, ` 1`, `-1`, `1.0`, empty, and repeated `iteration=1&iteration=2` → 400 (or first wins, stated); never 500.
Q4. **Command line:** no `--replay` → exit 2 and a message on stderr; `--replay` pointing at a missing dir → non-zero exit with a one-line error, no traceback.
Q5. **`notes_path` and agent names from logs are untrusted:** a log agent named `../x` or `a/b` gets `notes_path` null and never touches the filesystem outside `roles/`.
Q6. **Unknown-agent pod match** is deterministic when two name parts match different pods (first matching part in name order); one test.
Q7. **Server logging:** `BaseHTTPRequestHandler.log_message` is silenced (otherwise every request writes to stderr and the "empty stderr" checks fail or leak). The helper drains stdout and stderr continuously (threads or temp files) so a chatty server cannot block on a full pipe.
Q8. **Content-Type** `application/json; charset=utf-8` on `/state`, `text/html; charset=utf-8` on `/`; JSON with non-ASCII and `</script>` in a message `text` round-trips.
Q9. **No file serving:** `/` is a constant page; no route reads a file named by the request path (`/../x`, `/%2e%2e/x` → 404).
Q10. **Mode and shebang:** `bin/squad-board` is committed executable (`git ls-files -s` mode 100755), shebang `#!/usr/bin/env python3`. QA reads the file for Python 3.9-safe syntax (no `match`, no runtime `X | None`, no `str.removeprefix`, no parenthesised `with`), since only 3.13 is available here.
Q11. **Diff hygiene:** `git diff --stat` shows only the three listed files; no `__pycache__`, no `.pyc`.

## Comments
- 2026-10-12 tech-board: PASS by qaw-board at 084b6a4 on squad/dev-board-1 (round 2; round 1 FAIL 83706ff for two test gaps). N1 (Manager pod excluded from name match) and N2 (skip roster rows lacking Agent, Role or Scope) added by decision. Base sha for BRD-02..05: 084b6a4.
