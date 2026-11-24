# Evidence 09: saved UI state

## Behaviour
Server side only (page behaviour is tickets 10/11). Run: `cd tests && python3 -m unittest test_squadboard_ui`.

- AC1 `test_T09_AC1_...`: PUT a layout (order/span/hidden/max_height), choice, 5 recent, font; a fresh GET returns the same values. File has `version` 1, `saved_at`, LF, sorted keys, no `size` key.
- AC2/AC3 server side: unwritable folder gives GET `status: "unwritable"` and PUT 507 `{status:"unwritable"}`, no traceback.
- AC4: bad JSON, empty file, `[]`, version 99 give GET `status: "unreadable"` plus defaults; file bytes unchanged by the read.
- AC5: no token, Host `evil.example`, or non-JSON Content-Type is refused (403/403/415); file sha unchanged. Body over 64 KB is 413. A `path` or `squad` in the body is ignored; only `board-ui.json` is new in the squad tree.
- Atomic: patched `os.replace` failure keeps the old file byte-identical and no `*.tmp`; `PermissionError` is retried 3 times; 20 rounds of two writers always leave parseable JSON.

Touched: `bin/squadboard_ui.py` (new), `bin/squadboard.py` (put routes from `ROUTE["put"]`, tuple answers, opt-in `json_only`), `tests/test_squadboard_ui.py` (new).
Greps: `grep -rl 'squadboard\b|PUT_ROUTES|put_routes' tests/` hits `test_squadboard_server.py` (run, pass), `test_squadboard_ui.py`. Also run: test_windows_safe, test_no_bare_bash, test_old_language_inventory: pass (51 tests OK).

## Return 1 fixes
F1 position keys (x, y, row, size) are 400 at top level and in a panel. F2 NaN is 400 (parse_constant, allow_nan=False). F3 lone surrogate is 400 (encode check in validate). F4/QA-black AC2 PUT checks the same `_writable` as GET: read-only file gives 507 unwritable, file unchanged (real chmod test). F5 the file keeps its old mode (0644 if new). Tests: HardeningTest, 55 tests OK with server, windows_safe, no_bare_bash, old_language_inventory.

## QA whitebox

### QA whitebox 09: saved UI state. sha f8bae1d. Verdict: FAIL (first return)
Checked in a `git clone` at f8bae1d. Ran `cd tests && python3 -m unittest test_squadboard_ui test_squadboard_server`: 29 tests OK. Probe script: /tmp/qaw09_probe.py (live server, real `chmod`, euid 1000).
Checked OK: atomic write (mkstemp in same folder, fsync, os.replace, temp removed on error), 3 retries on PermissionError, token/Host/415/413 guards, `path`/`squad` body keys ignored, 507 JSON on unwritable folder, bad JSON/empty/version/`[]` give `unreadable` + defaults and the file is not rewritten, `saved_at` taken from the body, tree differs only by `board-ui.json`.

#### Findings (all in one return, REV-17)
- **F1 `bin/squadboard_ui.py:63` (validate), TA1 + TC.5.** `ui = {k: v for k, v in body.items() ...}` keeps every unknown top-level key. `PUT {"saved_at":..., "size":5,"x":10,"y":20,"row":3}` answers 200 and the file holds `size`, `x`, `y`, `row`. TA1: no pixel x/y, no row index, no key named `size`. Unknown keys may be kept, but these named ones must be refused (400) or dropped. Pass: a test that PUTs `size`/`x`/`y`/`row` (top level and inside a panel) and asserts 400 or absent from the file.
- **F2 `squadboard_ui.py:125` and `put` ~l.168, TA1 (wrong value is 400, nothing written).** `PUT ... "extra": NaN` (Python `json.loads` accepts NaN/Infinity) is stored and served as `NaN` with `status:"ok"`. The file and the GET body are not valid JSON; the page's `JSON.parse` fails on it. Pass: `json.loads(..., parse_constant=...)` raising, or `json.dumps(..., allow_nan=False)` caught as `ValueError` -> 400; file untouched; test it.
- **F3 `squadboard_ui.py:125` / `put` l.170-173, TA1 + TA4 (never a traceback).** A choice name with a lone surrogate (`"name":"\ud800"`) passes `validate`, then `fh.write` raises `UnicodeEncodeError` (a `ValueError`, not `OSError`). `put` catches only `OSError`, so the handler thread dies: client gets `RemoteDisconnected`, server prints a traceback. Pass: answer 400 JSON (reject lone surrogates in validate or catch `ValueError`/`UnicodeError` around `write_state`); test it. The temp file is already cleaned up (verified).
- **F4 `squadboard_ui.py:90` (`_writable`) vs `write_state`, TA4 (GET and PUT agree).** Read-only file (`chmod 444 board-ui.json`) in a writable folder: GET says `unwritable`, but PUT replaces the file (`os.replace` ignores the file mode) and answers 200 `status:"ok"`. The two answers contradict each other. Pass: PUT checks the same `_writable` and answers 507 `unwritable` (or GET stops reporting `unwritable` for a read-only file); one test with real `chmod` (skip on Windows with a stated reason) covers it. The ticket asked for a `chmod` test; the current tests only patch `os.access`/`mkstemp`.
- **F5 (small, same return) `squadboard_ui.py:121`.** `mkstemp` makes the temp file 0600, so `board-ui.json` ends up 0600 (observed `0o600`) and loses the mode it had. Other tools in the squad folder read and write with the user's umask. Pass: `os.chmod(tmp, 0o666 & ~umask)` or copy the old file's mode before `os.replace`. If you decide 0600 is intended, say so in the evidence.

#### Not findings
- `?squad=K` picks a squad from the server's list (`squad_by_key`, unknown key gives 400); no path from the request. Accepted for TA6.
- TA7: ticket 03's `snap()` is inline in a test, not reusable; the local copy is fine.

#### Recheck sha 94da561: PASS
Changed files only (LC-3b): bin/squadboard_ui.py, tests/test_squadboard_ui.py. test_squadboard_ui + test_squadboard_server + test_windows_safe + test_old_language_inventory: 49 OK. Live probe (same script as before, real chmod): F1 x/y/row/size gives 400 and no file; F2 NaN gives 400; F3 lone surrogate gives 400 JSON, no temp left; F4 read-only file gives GET `unwritable` and PUT 507, file unchanged; F5 file keeps its mode (0o644 observed). Each fix has a test in HardeningTest (chmod tests skip on Windows/root with a stated reason).

## QA blackbox

### QA blackbox, ticket 09 at f8bae1d: FAIL (T09.AC2, read-only file)
Method: `bin`+`templates` extracted from f8bae1d, temp repo with squad `sq1`, board on 18721 (+18722 for "other port"). No page exists yet (tickets 10/11), so I used the HTTP API only: `GET /api/ui`, `PUT /api/ui` with the page token from `/api/session` (header `X-Board-Token`). Servers stopped by PID; scratch left in /tmp/qb09.*.

| AC | What I did | What I saw | Result |
|---|---|---|---|
| T09.AC1 | Saved font xl, choice scope s1, 2 recent, 2 panels (one hidden, order/span/max_height) with a token; read it from a second board on another port | File `board-ui.json` written; the second board returned identical font, choice, recent, panels, hidden flag. A PUT with an older `saved_at` is stored as sent (newer-wins is the page's job, not testable yet) | PASS for the data; "comes back" on screen at T10/T11 |
| T09.AC2 | (a) `chmod 444 board-ui.json`, then PUT. (b) folder `chmod 555`, PUT. (c) `board-ui.json` made a folder, PUT | (a) **200 ok: the read-only file was replaced and the new content saved.** (b) 507 "settings file not writable: Permission denied". (c) 507 "not writable: Is a directory" | **FAIL for (a)**; (b), (c) PASS |
| T09.AC3 | Needs the page and blocked storage | Not testable before T10/T11 | open |
| T09.AC4 | File with unknown version 99, bad JSON, empty, chmod 000, a folder; then PUT over a bad file | GET answers defaults with `status: "unreadable"` each time (page text "settings file unreadable" and picker are page parts). PUT over a bad file recovers it (valid file, no leftover temp file) | PASS for the data; page text at T10/T11 |
| T09.AC5 | PUT with no token, wrong token, token of the other board, wrong Host; compared md5 of the file | All 403; `/api/session` with a wrong Host also 403; file unchanged | PASS |

Finding (T09.AC2): a PO who marks `board-ui.json` read-only (the way FIXTURE-STEPS step 1 of ticket 02 says to make it unwritable) still gets the file overwritten, so "unwritable" is never reached and the page never shows "settings not shared". Fix either way: respect a read-only file (answer 507) or tell me the AC means only an unwritable folder. If the folder is the intended case, ticket 02's step 1 must say `chmod 555` on the squad folder.

#### Re-check at 94da561: PASS on the data (AC1, AC2, AC4, AC5)
Same method as above (extract, token from `/api/session`, header `X-Board-Token`, port 18761).
- AC2 (was the FAIL): `chmod 444 board-ui.json` with a writable folder: PUT now answers 507 `unwritable`, file unchanged, GET still serves the old content. Folder `chmod 555`: 507. `board-ui.json` as a folder: 507. After undo, PUT 200. PASS
- AC1: save of font xl, choice, recent, hidden panel: 200 and the same data back. PASS
- AC4: version 99, bad JSON, empty, chmod 000: `status: unreadable`, defaults. PASS
- AC5: no token, wrong token, wrong Host: 403, file unchanged; valid PUT 200; no leftover temp file. PASS
Still open for T10/T11: AC3 and the page texts ("settings not shared", "layout not saved", "settings file unreadable"). Ticket 02 FIXTURE-STEPS step 1 (chmod 444) now reaches the unwritable state.
