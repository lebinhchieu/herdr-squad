Status: ready
Blocked by: 06
Task ID: IV-07
Files touched: `CONTEXT.md`, `docs/adr/` only if `promote.md` names one

# IV-07: promotion

**Done when `$SCOPE_DIR/promote.md` is committed to the project docs on the integration branch.** `process.md` → Promotion; `CONTEXT.md` and ADR edits through `/domain-modeling` (`project.md` → Rules for lasting docs). Technical AC: every entry of `promote.md` appears at its named target with its exact wording; `CONTEXT.md` glossary terms use the same style as the PO inbox section; nothing else changes.

## QA whitebox additions (agreed 2026-10-16; each is a pass condition; a line with the same number replaces the ticket line above)
Source: `evidence/qa-w-ac.md` in the scope folder.

- **7.1** The glossary terms are the three of the spec's last section; the three rules match `promote.md` and add nothing the scope did not decide; ADR only if `promote.md` names one.

Not demanded: lint (none configured), a benchmark, a library audit (none added).
