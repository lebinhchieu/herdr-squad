# The PO inbox sits on top of escalations.md

Status: accepted (po-inbox)

**Decision:** an answer item is a row of `escalations.md` (unchanged table); read items are the inbox's own append-only `inbox.jsonl` in the Manager's home; one CLI, `squad-inbox`, is the only reader and writer of both, and the mod talks only to the CLI (the `list --json` version-1 contract is the seam).

**Why:** one place for the PO; the board's Needs-you, the check-in rule and `process.md` keep working untouched; replacing the file would touch `process.md`, `manager.md`, `project.md` and the board for no visible gain.

**Consequences:**
- The PO's answer is written into the row's Answer cell (`|` escaped, newline as `<br>`) and kept verbatim in the log; a deleted row stays listable from a snapshot; the Options cell format `(a) text; (b) text` gives choices.
- An inbox answer is never a merge, push or deploy request; per-home only, `squad-board` stays the cross-home view.
- The pane hides a Manager's `squad-inbox add` body only for a quoted heredoc `<<'WORD'` / `<<"WORD"` (allow-list); any other form shows its full row in chat. Manager instructions say "body in a quoted heredoc".
- A hand-written `escalations.md` row shorter than the header is a valid item; answering pads it to header width. When the Answer cell cannot be written the answer is still kept and the item carries flag `cell-not-written`.
- Known limits: an answer recorded by an outside process with `--source pane` is delivered at the next session start; `squad-close` refuses for `--scope`/`--goal` only (not whole-squad or legacy flat).
- The engine's permission dialog shows the full `squad-inbox add` command, body included, unless `squad-inbox add *` is pre-allowed in the Manager's settings (the PO's choice, not set by the plugin).
- The mod reads and writes no file itself; the CLI cannot prove who ran `answer`, so the merge/push/deploy rule is an instruction, not a lock.

**Alternatives rejected:** replace `escalations.md` (cross-cutting change); two separate lists (the PO looks in two places).
