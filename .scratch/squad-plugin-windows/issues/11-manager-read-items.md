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
