# C Manager sends informational notes as read items

Status: ready-for-agent
Type: task
Source: `issue-po-inbox.md` section 2; PO E5 widened `touches` to `agents/`
Touches: `agents/manager.md`, `tests/test_manager_inbox_read.py` (new; do NOT edit `tests/test_instructions.py`)
Blocked by: none. Parallel with 09, 10, 12.

## What
In `agents/manager.md` (The PO, Inbox bullet): an informational note, one that needs no answer ("READ (not blocking)..."), goes through `squad-inbox add --kind read --title T` with a quoted-heredoc body, never a hand-written `escalations.md` row. Minimal edit: one sentence next to the existing bullet; no new section.

## Technical AC (Tech Lead)
1. The text names `--kind read`, says "never a hand-written row" for notes, and keeps every existing rule of the bullet.
2. New test greps `agents/manager.md` for those phrases; existing instruction tests (`test_instructions`, `test_manager_m_l`, `test_pod_*`, `test_process_*`) still pass.
3. Role-instruction change: Tech Lead lists it for the PO in `promote.md`/the summary. Clearing E5-E8 in scene-split is NOT ours.

## Comments

### Tech Lead amendment (2026-10-17) — binding
- **TC1** the Inbox bullet says: a note with nothing to decide ("READ, not blocking", a status, a resolved matter) goes through `squad-inbox add --kind read`, never a hand-written row in `escalations.md`; only `--kind answer` makes a row, and the command writes it.
- **TC2** delete the sentence "rows written by hand still work." (it licenses the habit). Add one clause: a resolved question is withdrawn (`squad-inbox withdraw E<n> --reason "<why>"`), not left open.
- **TC3** about two sentences net, no new bullet. Every string pinned by `ManagerInboxTest` in `tests/test_instructions.py` stays byte for byte (tokens, the heredoc sentence, M1-M3, "Never offer a merge, push or deploy as an item", `--blocks ""`), and `squad-inbox <word>` still only names CLI commands. The new test file also asserts the absence of "rows written by hand still work".
- **TC4** no other `agents/` or `templates/` file changes; run `test_instructions`, `test_manager_m_l`, `test_process_writing`, `test_pod_contact_routes`, `test_process_citations`.

- BA AC (spec.md story 16, F5): also REMOVE the sentence "rows written by hand still work" in `agents/manager.md` (line ~95), not only add the rule. No other file in `agents/` may change.
- **TC5 (QAW)** the phrase test anchors to the Inbox bullet and fails on the 59a8d1b text. Open item for the PO (not in touches, no FAIL): `templates/scope/escalations.md:3` and `templates/goal/escalations.md:3` say "The Manager writes each one before telling the PO"; with `squad-inbox add --kind answer` the command writes the row. I list it in the hand-in to the PO.
