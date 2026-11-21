# 04 Promotion: ADR 0031 (amends 0016) and the CONTEXT.md terms
Duties: Developer builds and writes design notes; technical AC are in this file (Tech Lead, agreed with QA whitebox); business AC = this ticket as written; QA whitebox check of the docs against the code on 03's sha; QA blackbox check that the docs say what the CLI does; hand in to both QAs. Run `/domain-modeling` for the edits (project.md rule for lasting docs, PROMO-4).
Files: docs/adr/0031-home-upgrade-mid-scope.md (new), docs/adr/0016-process-composed-per-role.md (header line only), docs/adr/0030-team-lead-always.md (one line), CONTEXT.md
Evidence: .scratch/fix-update/issues/04-promotion/evidence.md
Status: ready
After: 03 (build on 03's branch; the passed sha of 03 is `--base`)

Ticket path: `.scratch/fix-update/issues/04-promotion.md`. The text to commit is `$SCOPE_DIR/promote.md` (exact wording, per target). Touched files are an estimate (LC-9b).
Harness: none (docs). Run `python3 tests/test_instructions.py`-style hits: `grep -rl 'between scopes only\|keep their runtime\|Plugin pin\|Process update' tests/` and run every hit; plus `tests/test_old_language_inventory.py` and `tests/test_process_writing.py` if the grep names them.

## AC
- AC1 `docs/adr/0031-home-upgrade-mid-scope.md` exists in the house shape (`# 0031: ...`, `Status: accepted (fix-update; Chieu answered Q1-Q3 on 2026-11-21)`, `Amends 0016 ...`, Decision, Why, Consequences, Alternatives rejected) with the text of `promote.md` section 1.
- AC2 ADR 0016 changes only in its header block: a line `Amended by 0031 (home upgrade): the sentence "an upgrade applies between scopes only" now has the exception of a PO-confirmed home move.` The Decision text is not rewritten (house pattern, as 0018).
- AC3 ADR 0030 line `Pinned scopes ... keep their runtime.` gets `, until Chieu moves one (ADR 0031)`; nothing else in 0030 changes.
- AC4 `CONTEXT.md` **Plugin pin** (line ~124) and **Process update** (line ~144) are rewritten per `promote.md` section 2 (no "between scopes only"); one new term **Pin move** is added with `_Avoid_: scope upgrade`; the glossary term **Home** is reused, not redefined.
- AC5 Every claim in the ADR and glossary is true of `bin/squadhomes.py` on 03's sha: QA whitebox checks each of these against the code: target is `plugin.pin`; compose gate; one-line edit; respawn of live agents at once except the caller; pending agents are listed and exit 4; other open homes are warned about, never offered.
- AC6 `grep -rn 'between scopes only' CONTEXT.md docs/adr/0016* skills/` prints only ADR 0016's Decision line (kept, with the header exception above).
- AC7 No code or test change; no file deleted or moved.

## SQ-1 (deletes and moves)
Deletes or moves no file. The two glossary lines and the ADR sentence are edited in place; their readers are docs only (`grep -rn 'between scopes only'` run above).

## Comments
