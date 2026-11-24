# 03 Inbox refuses bare IDs

Status: ready-for-agent

Spec: `.scratch/po-clarity/spec.md`
Duties: Design and technical AC: `$SCOPE_DIR/tasks/03-design-notes.md` (Tech Lead) with `$SCOPE_DIR/tasks/qaw-technical-ac.md` (QA whitebox, 03 and common lines). Build `bin/squadids.py`, the `cmd_add` refusal, the guide rule with its Why line; fix failing fixtures, never the check; run the test files the notes list plus the SQ-10 trio; write `evidence.md`; HANDIN to both QAs.
Files: `$SCOPE_DIR/tasks/03-design-notes.md`, `$SCOPE_DIR/tasks/03-idcheck-prototype.py`, `bin/squadinbox.py`, `bin/squadids.py`, `docs/inbox-body-guide.md`, `tests/test_squadinbox.py`, `tests/test_inbox_body_guide.py`
Duties: Design and technical AC: `$SCOPE_DIR/tasks/03-design-notes.md` (Tech Lead) with `$SCOPE_DIR/tasks/qaw-technical-ac.md` (QA whitebox, 03 and common lines). Build `bin/squadids.py`, the `cmd_add` refusal, the guide rule with its Why line; fix failing fixtures, never the check; run the test files the notes list plus the SQ-10 trio; write `evidence.md`; HANDIN to both QAs.
Files: `$SCOPE_DIR/tasks/03-design-notes.md`, `$SCOPE_DIR/tasks/03-idcheck-prototype.py`, `bin/squadinbox.py`, `bin/squadids.py`, `docs/inbox-body-guide.md`, `tests/test_squadinbox.py`, `tests/test_inbox_body_guide.py`

## Problem

Inbox bodies use codes Chieu has to look up. Example from E23 (guardian `clarify`):

> Decisions: D73 (amends D42/D44), D74 (closes O10/O11/O13/O15/O16 with your answers). Open: O17 ...

Chieu has to know what D42, D44, O10, O11, O13, O15 and O16 mean.

## Change

`squad-inbox add` checks the body (and the title) for **ID tokens**: a word of 1-4 capital letters, an optional `-`, and digits (`D73`, `O17`, `E22`, `LC-14`, `T5`, `AC3`). The **first** time each ID appears, a gloss must follow it within the same line, as `(…)` or ` = …`. If one is missing, the item is refused with exit 2, and the message lists the bare IDs.

Before and after:

```text
REFUSED (exit 2): bare IDs: D42, D44, O10, O11
  gloss each on first use, e.g. "D42 (EDI columns kept)"

ACCEPTED:
  D74 (config tables key by GuardianConfigID)
  closes O11 (engine takes workflowID) and
  O13 (no Activity join).
```

Not checked: text inside `` `code` ``, fences, and links. Shas and paths are not ID tokens anyway.

## AC

- AC1: the E23 body above is refused, and the message names every bare ID.
- AC2: the same body with a gloss after each first use is accepted. Later uses need no gloss.
- AC3: `LC-14` inside backticks is not checked.
- AC4: `docs/inbox-body-guide.md` gets one rule with a Why line. The guide/fixture sync test still passes.
- AC5: every existing test that calls `squad-inbox add` passes (`grep -rl 'squad-inbox' tests/`). Fix the fixtures that now fail, not the check.

## Comments
