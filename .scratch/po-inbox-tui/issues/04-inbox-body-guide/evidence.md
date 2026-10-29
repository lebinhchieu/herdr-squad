# Evidence: ticket 04, inbox body writing guide

## Behaviour

This ticket adds a document, not a pane change. The proof is that the guide's two examples are the 03 fixtures and parse with the real parser, and that the forms the guide names exist in the pane.

- Guide: `docs/inbox-body-guide.md` (code and guide at commit `3266b91`).
- Example 1 and Example 2 are the fixtures `guideE1` and `guideR1` (`hooks/po-inbox/fixtures/visual.ts`), byte for byte. `tests/test_inbox_body_guide.py` fails if they differ.
- `hooks/po-inbox/markup.test.ts` parses both with the real parser. E1 gives callout, table, `diagram` code fence, callout, paragraph, link paragraph. R1 gives callout, table with badges, callout, three bullets, paragraph, link paragraph. The same file checks the three callout tags, four badges and a link.
- The real-pane drawing of both examples (callouts, badge table, diagram, link) is in `.scratch/po-inbox-tui/issues/03-body-styles/evidence.md`; the guide adds no new drawing.

Test runs (this worktree):

```
python3 tests/test_inbox_body_guide.py          -> 2 tests OK
claude plugin test .                            -> 586 pass, 0 fail
python3 tests/test_po_inbox_mod.py              -> validate + plugin test, 586 pass, 0 fail
python3 tests/test_promotion_0_6_0.py           -> 8 tests OK (grep -rl hit)
```

The full suite was not run (PO rule: once, at the end, by QA whitebox).
