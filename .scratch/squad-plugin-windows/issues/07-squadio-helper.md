# T0 `bin/squadio.py`: the shared UTF-8 stdio setup

Status: needs-triage (draft)
Type: task
Source: design.md D1
Touches: `bin/squadio.py` (new), `tests/test_squadio.py` (new)
Blocked by: none. Blocks T1, T2a, T2b, T2c. Tiny: do it first, hand in, then the same Developer may take T2c.

## What
One function `utf8_stdio()`. Sibling modules are imported the way `squadlabel` is: `sys.path.insert(0, dirname(realpath(__file__)))`.
```
def utf8_stdio():
    for s in (sys.stdin, sys.stdout, sys.stderr): reconfigure UTF-8, errors="replace"
    stdout and stderr also newline="\n"
```
Skip a stream that is `None` or has no `reconfigure` (a test replaces it with a StringIO).

## Technical AC (Tech Lead)
1. Test, simulated Windows stdout: `sys.stdout = TextIOWrapper(BytesIO(), encoding="cp1252", newline="\r\n")`; after `utf8_stdio()`, `print("→ 🦀 é")` leaves the exact UTF-8 bytes with `\n` only. Same for stderr; stdin: bytes `→ 🦀` in a cp1252 wrapper read back as the text.
2. A stream that is `None` or a `StringIO` does not raise.
3. Idempotent: two calls change nothing.
4. No other change in `bin/`; the callers are added by T1, T2a, T2b, T2c.

## Comments
