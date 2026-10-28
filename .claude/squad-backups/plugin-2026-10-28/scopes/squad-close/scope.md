# Scope: squad-close

**squad-close should not close manager session**

goal: 
touches: bin/squad-close, templates/squad/process/closing.md, templates/squad/process.md, tests
size: M (confirmed by PO 2026-10-23)
qa: full
qa-b: no  (task 03 only changes tests/fixtures; nothing a person using the product observes; PO confirmed 2026-10-23)
design: no
<!-- Team models: one line per changed role, `model <role>: <model> <effort>`, e.g. `model dev: sonnet medium`. Unlisted roles use their defaults. -->

plugin: 0.5.0 5adfc45151ab8611abc76c11cc4939cc5fc2db90

## Constraints
- **Developer cap:** 3 (the default in `process.md`)
- **Budget:** one iteration; check in with the PO when every task passed or after 3 returns on one task
- **Done means:** the size's checks passed (`process.md` → Sizes), evidence saved, branches ready for PO review

## Notes from the PO
Design: `.scratch/squad-close-keeps-manager/grill.md` (round 1; decisions in iterations/1.md).
