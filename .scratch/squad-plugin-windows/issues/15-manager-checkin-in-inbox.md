# H Manager check-in and PO steps go to the inbox, never to chat

Status: ready-for-agent
Type: task
Source: iteration 4, PO request in chat 2026-10-17 ("Why don't this kind of info is not put into PO inbox?")
Touches: `agents/manager.md` (lines 95, 97, 99 only), `tests/test_manager_inbox_read.py`
Blocked by: none. Base `d4aed31`. One Developer (`plugin-dev-win-compat-10`); its passed branch is the integration branch. No version bump (0.3.4 stays).

## What
`agents/manager.md:95` already says "anything the PO must read or answer goes in the inbox, never in chat". The Manager broke it at the iteration 3 check-in, because :99 ("Check-in") names no channel and :97 keeps the merge in chat, so the whole check-in followed the merge into chat. Three wording edits, no new section:

1. **:99 Check-in bullet.** Say the check-in is sent as ONE `squad-inbox add` item (`--kind read`; `--kind answer` when it asks the PO to choose), not as a chat report. The item lists every step the PO must take (clean-up, checklist, close confirmation, open choices) next to the existing contents (done with evidence links, next, the Team Lead's 3-returns line, open escalations, proposed role-instruction changes). Keep the closing "Then copy each answered escalation's outcome ... delete its row from `escalations.md`."
2. **:97 "The inbox carries only..." bullet.** Add: the check-in item may name the passed sha with the words "to merge, ask in chat"; it never offers the merge, push or deploy as an option. Keep every existing sentence of the bullet, including "that stays the PO's explicit request in this chat" and "needs their explicit request here".
3. **:95 Inbox bullet.** Add one sentence: a chat reply to the PO never lists steps for the PO; the steps go in the inbox item and the reply is the printed line (or one line pointing at it). Keep all existing sentences, in order.

Write each addition in the bullet's own voice, short, must/never. Plain ASCII in the added text. No change to `templates/`, `process.md`, other agents.

## Technical AC (Tech Lead)
1. Test class in `tests/test_manager_inbox_read.py` (that file already reads `manager.md` as UTF-8 and selects the Inbox bullet; add selectors for the Check-in and "The inbox carries only" bullets the same way, by their leading `- **...` label). Assertions, each a substring or regex on the right bullet:
   - Check-in bullet contains `squad-inbox add`, `--kind read`, and a phrase saying it lists each step the PO must take; it does not contain a "report" or "tell the PO in chat" instruction for the check-in itself.
   - "carries only" bullet contains `to merge, ask in chat` and still contains `Never offer a merge, push or deploy as an item` and `needs their explicit request here`.
   - Inbox bullet contains a sentence that a chat reply never lists steps for the PO; and still contains the three existing wording rules (`One \`squad-inbox add\` per Bash call, never two.`, `your reply is the printed line and nothing else`, `never answer from memory of what is open.`).
2. Each new assertion fails on `d4aed31` and passes on the tip (show the failing run of the new tests in `dev-evidence.md`).
3. Existing tests unchanged and green: `test_manager_inbox_read`, `test_instructions`, `test_manager_m_l`, `test_process_writing`, `test_po_inbox_contract`, `test_templates`. The count rises by the new tests only.
4. `git diff --stat d4aed31 HEAD` lists only `agents/manager.md` (three bullets; show `git diff -U0` in the hand-in), `tests/test_manager_inbox_read.py`, and this ticket file at `.scratch/squad-plugin-windows/issues/15-manager-checkin-in-inbox.md`. No other line of `manager.md` changes (the Writing-rule block, `## Never`, the S/M/L text stay byte-identical).
5. `git merge-base --is-ancestor d4aed31 HEAD` printed in the hand-in. Fresh branch name, `--base d4aed31`.
6. Run test files from inside `tests/` with `PYTHONDONTWRITEBYTECODE=1`, in a UTF-8 locale. Under `PYTHONUTF8=0 LC_ALL=C PYTHONIOENCODING=cp1252` only `test_manager_inbox_read` is required: `test_instructions` and `test_manager_m_l` read `manager.md` without an encoding and fail at import there already at `d4aed31` (known follow-up, not this ticket). The Developer does not run the full suite; the Tech Lead runs `--tz` on the final sha into `evidence/T-int4`.
7. Role-instruction change: the PO asked for it in chat (iteration 4); QA blackbox may read the three bullets against the "What" above, no live run is possible (prompt text only).

## Comments
