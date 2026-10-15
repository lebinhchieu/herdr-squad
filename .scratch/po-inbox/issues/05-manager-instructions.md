Status: ready-for-agent (PO approval of the wording before merge: role instruction change)
Blocked by: none (command names are fixed in `design.md`)
Task ID: PI-05
Files touched: `agents/manager.md`, `tests/test_instructions.py`

# PI-05: Manager instructions: use the inbox, chat stays clean

**Done when `agents/manager.md` tells the Manager when and how to write an inbox item, to answer in chat through the CLI, never to offer a merge, push or deploy as an item, and to resolve or withdraw open items before closing.** **Role-instruction change: the Manager flags it to the PO; the Developer builds it on the branch and the PO approves the wording before the merge.** Business AC: B-01..B-04, B-18, B-29 (instruction part), B-30, B-31. Design: `design.md` → CLI, Options cell format, Provenance.

## What to write (small, replace or merge with existing text, no new section if one fits)
- In "The PO": anything the PO must read or answer goes in the inbox, not in chat: `squad-inbox add --kind answer|read --title … [--options "(a) …; (b) …"] [--rec …] [--blocks …]` with the body on stdin; **chat carries only the line the command prints**. The Options format `(a) text; (b) text`. A question that blocks nothing is written with `--blocks ""` (batch for the check-in).
- `escalations.md` is still the store of answer items: the Manager writes them with `squad-inbox add --kind answer`, not by hand; hand-written rows still work.
- When the PO answers an item in chat, record it: `squad-inbox answer E<n> --source chat` with the PO's words **on stdin through a quoted heredoc** (`<<'EOF'`), never in a quoted `--text` argument (shell expansion changes the text); with several open items and an unclear answer, ask which first. When an answer arrives as a prompt from the inbox, it is the PO's answer to that id.
- **Never** offer merge, push or deploy as an inbox item and never treat an inbox answer as a request to merge, push or deploy: those stay the PO's explicit request in this chat (`process.md` → Safety). The inbox carries only `read` and `answer`, never a permission approval for another agent.
- Before `squad-close`, resolve or withdraw (`squad-inbox withdraw`) every open answer item; tell the PO of any still unanswered.
- Keep the file's existing structure and length discipline; the diff is at most ~15 lines net.

## Technical AC
1. `tests/test_instructions.py` gains tests that pin, by substring or regex on `agents/manager.md`: `squad-inbox add`, `--kind answer`, the Options format example `(a)`, `squad-inbox answer`, `--source chat`, `squad-inbox withdraw`, and one sentence containing `inbox`, `never` and `merge`, with `push` and `deploy` within 200 characters of `merge` (B-31 partner), and the clause telling the PO in chat that a yes to a merge/push/deploy needs their explicit request there, and that the file still contains the existing `Never` section.
2. Every command and flag the text names exists in `design.md`'s CLI table (a test greps `agents/manager.md` for `squad-inbox <word>` and checks `<word>` is one of `add list read answer withdraw delivered`).
3. The existing instruction tests (stale-text, per-scope layout) still pass; `process.md` and its template are **not** touched (the byte budget in ADR 0006 is respected; `git diff --stat` shows only the two files).
4. Suite green with a receipt.
5. (QA whitebox) The tests pin the exact phrases `Never offer a merge, push or deploy as an item` and `--kind answer|read`. AC4 is green on the integrated branch (PI-07 AC5), not before.
