# Evidence 02: rule file parser and `squad-process lint`

## Behaviour

Run from the repo root at the handed-in sha, with `PYTHONDONTWRITEBYTECODE=1`. `E=tests/fixtures/rules/errors`, `C=tests/fixtures/rules/clean`.

- **02-1 errors fixture.** `python3 bin/squad-process lint --cards error --plugin-root $E --squad-dir $E/squad` exits 1 and prints 21 `file:line: problem` lines, one per error class (first: `templates/squad/process/core.md:1: core.md has 47 lines, over 40`). Same command with `$C` exits 0 and prints nothing.
- **02-2 no rule files.** `lint --plugin-root <empty tmp dir>` prints `no rule files`, exit 0; plain `python3 bin/squad-process lint` in the repo prints the same, exit 0.
- **02-3 bare ids.** The errors output has `bin/tool.py:1: [REV-8] cites a rule that does not exist` and no line for the bare `SEC-04` / `UTF-8` in the cited files.
- **02-4 `when`.** Clean fixture REV-4 reads `when: qa-b = no and size = S` and lints clean; the truth table is pinned in `tests/test_squadrules.py`.
- **02-5 hash.** `lint --hashes` over LF and CRLF copies of `safety.md` gives identical output (same md5); one word edit changes the line; clean REV-3 is `203fa130`.
- **Design AC 6a (delegation).** `compose --out F` and `compose --out F --resolve "…"` still reach the v6 merge; `compose dev --home D` reaches the composer; a token after `compose` starting with `-` is not delegated. Pinned by stub tests in `tests/test_squadrules.py` (`test_compose_by_role_is_refused_until_04` and the delegation tests).
- **Design AC 6b (`--hashes`).** After any problems, one `<ID> <hash>` line per rule in file order, exit code unchanged by the flag: `test_hashes_after_problems_do_not_change_exit`.
- **Suite.** `$SCOPE_DIR/evidence/02/suite-default.txt`: 1012 tests, OK, clean=yes at 4230349.
