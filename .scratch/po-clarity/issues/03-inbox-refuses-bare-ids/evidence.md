## Behaviour

`squad-inbox add` now refuses a title or body with a bare ID token (`bin/squadids.py::bare_ids`, called in `cmd_add` before the lock). Exit 2, stderr:

```
squad-inbox: bare IDs: D42, D44, O10, O11, O13, O15, O16, O17
  gloss each on first use, e.g. "D42 (what it is)", or put a non-ID in `backticks`
```

- AC1/AC2/AC3, fence, link, CRLF, title, nothing written (T03-2): `tests/test_squadinbox.py::BareIdTest` (4 tests, kinds read and answer).
- AC4: rule plus `  - Why:` line in `docs/inbox-body-guide.md`; the two examples are untouched (T03-8).
- AC5: every `grep -rl 'squad-inbox' tests/` hit passes with SQUAD_* unset, PYTHONDONTWRITEBYTECODE=1: test_windows_safe, test_squadinbox_park, test_rules_wording, test_squadinbox_win, test_po_inbox_contract, test_squadinbox_answer, test_squadruntime, test_squadboard_inbox, test_board_fixtures, test_instructions, test_squadboard_panels, test_squad_close, test_squad_manager_guard, test_squad_usage, test_inbox_guide_cmd, test_squadcommands, test_squadinbox (59, incl. test_no_pyc). Also test_inbox_body_guide, test_squadinbox_body_crlf, test_utf8_helpers. No fixture needed a change.
- SQ-10 trio: test_windows_safe 14 OK, test_utf8_helpers 14 OK, test_instructions 16 OK.
- T03-4 sweep (read-only, all `inbox.jsonl` under the squad dir): 12 of 36 items would be refused. A report, not a FAIL.
- T03-6 callers: `grep -n "squad-inbox\|squadinbox"` over `bin/` shows no caller of `add` besides the Manager's command; `squad-manager-guard` only reads the command text; `squad-close`, `squad-usage`, `squadcommands` use `list`.
- No escape-hatch flag, no version bump.
