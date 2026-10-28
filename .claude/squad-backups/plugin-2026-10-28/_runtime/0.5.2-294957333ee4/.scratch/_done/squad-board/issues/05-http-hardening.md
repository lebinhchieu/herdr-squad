Status: resolved
State: done
Task ID: BRD-05
Blocked by: 01
Files touched: `bin/squad-board` (only the `http` section: `check_request`, `handle_jump`, port selection, startup line), `tests/test_board_http.py` (new), `tests/board_fixture.py` only to fill `Server.token` from the startup URL (the one allowed edit); `tests/test_board_state.py` only the three BRD-01 tests that BRD-05 makes obsolete (startup line regex and token, the jump half of the 501 test, the busy-port exit test replaced by BRD-05's all-busy test), approved 2026-10-12

# BRD-05: HTTP hardening: token, Host check, jump refusals, port fallback

**Done when the security rules in design.md "HTTP and security" hold and are proven by tests, with a stub `herdr` on `PATH` showing that refused jumps run nothing.**

Read first: design.md "HTTP and security", spec stories 59–61. Security-flagged ticket: qaw-board reviews it hardest (greps for `shell=True`, `0.0.0.0`, `==` on the token).

## Technical AC (BRD-05)

1. **Bind (baseline 6):** the server listens on `127.0.0.1` only. Test: connecting to the host's non-loopback address is refused (`skipTest` if the host has none); code has `("127.0.0.1", …)` literally.
2. **Startup line (D12):** `squad-board: http://127.0.0.1:<port>/?token=<token>`; token from `secrets.token_urlsafe(16)`, different on every run (test two runs); `/state` and `/` never contain the token.
3. **Port (D4):** with `--port P` busy, the server picks a port in P+1..P+20 and prints it; `--port 0` takes an OS port; all of P..P+20 busy → exit 1 with a message on stderr. Tests occupy ports with sockets they open themselves.
4. **Host check:** a request with `Host: evil.example` or the wrong port → 403 on `/`, `/state`, `/events`, `/jump/*`. `Host: localhost:<port>` is accepted.
5. **Jump success:** `POST /jump/<roster name>` with the right `X-Board-Token` → 200 `{"ok": true}`; the stub `herdr` records exactly one call whose argv is `["agent", "focus", "<name>"]`.
6. **Jump refusals** (stub `herdr` records **no call** in every one): `GET /jump/x` 405; missing token 403; wrong token 403 (same length and different length); bad `Origin` 403; name `a b`, `../x`, `x;rm`, over 32 chars or empty → 400; valid-looking name not in roster → 404. Check order: method, Host/Origin, token, name regex, roster (a refused token never reveals roster membership: a non-roster name with a bad token is 403, not 404).
7. **Argv safety:** a roster name containing shell metacharacters cannot occur (regex), and the call is a list with no shell; QA greps for `shell=True`, `os.system`, `0.0.0.0`, and `==`/`!=` on the token (must be `hmac.compare_digest`).
8. **herdr failure:** stub exits non-zero → 502; `herdr` not on `PATH` → 502; both with a JSON body, no traceback to the client; timeout 5 s.
9. **Headers:** `Cache-Control: no-store` on all responses; `X-Content-Type-Options: nosniff` on JSON; no `Access-Control-*` header anywhere; `OPTIONS /jump/x` → 405 or 501, not 2xx.
10. **Tests never use a fixed port** except the port-fallback test, which picks a free port at runtime first.
11. **Baseline AC 1 to 5, 7, 9, 10** from design.md "Technical AC".

### QA whitebox additions (qaw-board)
Q1. **Token compare on bytes:** `X-Board-Token` with non-ASCII (`é`), empty, or 10 KB long → 403, never 500 (`hmac.compare_digest` raises `TypeError` on non-ASCII `str`; compare `.encode()` bytes). Duplicate `X-Board-Token` headers → 403 unless both equal.
Q2. **Host edge cases (each 403):** missing `Host` (HTTP/1.0), `127.0.0.1.evil.com:<port>`, `localhost.evil.com:<port>`, `127.0.0.1` without port, `localhost:<other port>`, empty Host; `LOCALHOST:<port>` accepted (case-insensitive). `Origin: null`, `Origin: http://127.0.0.1` (no port) → 403.
Q3. **Order of refusals proved:** wrong method with bad Host → 405 or 403 (state which, test the chosen order); bad Origin plus good token → 403; bad token plus non-roster name → 403 (already in AC 6).
Q4. **Token never leaks:** after a full test session, neither stderr nor any response body, header (`Location`, `Set-Cookie`, `Referer`-like) contains the token; stdout contains it only on the startup line; `log_message` is silenced (see BRD-01 Q7).
Q5. **Request body:** `POST /jump/<name>` with a large `Content-Length` and no body, or a huge body, does not hang or crash the thread; the body is ignored.
Q6. **Stub design:** the stub `herdr` records argv one per line to a file and the test asserts the file is absent/empty for refusals and has exactly `agent`, `focus`, `<name>` for success. The stub is created in a temp dir put first on `PATH` via the helper's `env`; no real `herdr` is ever run (QA checks `which herdr` is not reached: a PATH containing only the stub dir plus Python's).
Q7. **Roster source:** the roster used for the check is parsed per request (or on change) from `roster.md`; a name present only in logs (unlisted agent) → 404. A retired roster agent: state the rule (proposal: 404) and test it.
Q8. **Timeout:** a stub that sleeps 30 s → 502 after about 5 s and the child is killed (no leaked process; test checks the stub's pid is gone).
Q9. **Port fallback:** the chosen port is the one printed and the one actually bound; a busy port taken by a socket in `LISTEN` state and one taken by a bound-not-listening socket both count as busy; `SO_REUSEADDR` must not let the server share a live port (check `allow_reuse_address` / SO_REUSEPORT is not set).
Q10. **grep gate (QA runs):** `shell=True`, `os.system`, `0.0.0.0`, `""` as bind host, `==`/`!=`/`in` on token, `Access-Control`, `eval(`, `exec(`, `pickle`: all absent from `bin/squad-board`.

## Comments
- 2026-10-12 tech-board: PASS by qaw-board-2 at 9d30599 (squad/dev-board-6) after FAIL at 76b1b99 (tests only). Rulings in design.md row 10; handler socket timeout moved to BRD-06 AC 10.
