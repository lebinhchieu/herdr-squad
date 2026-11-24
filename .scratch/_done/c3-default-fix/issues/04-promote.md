# 04 Promote the lasting facts of c3-default-fix

Status: ready-for-agent
Slug: promote
Duties: design notes = Developer (in this file); technical AC = QA whitebox with the Developer; business AC = the ticket as written; code check = QA whitebox; behaviour check = QA blackbox; hand in to both QAs; full suite and promote.md = QA whitebox (full suite only after Chieu's yes via the Manager). A risk flag, user-visible change or business doubt found while building: BLOCKED to the Manager.
Promotion task (cite PROMO-5, PROMO-4): commit `$SCOPE_DIR/promote.md` into the project docs on your branch, based on 53c479d.

AC
1. `tools/claude-accounts/README.md` (Windows section) gets the one sentence of promote.md "Business rule".
2. `docs/adr/0013-claude-accounts-windows.md` gets a short dated addendum with the promote.md "ADR candidate" decision. It must not contradict the ADR's earlier text; if it does, say so in the addendum and in evidence.md.
3. No other file changes except `.scratch/c3-default-fix/issues/04-promote.md` (this file, `Status:` line) and its evidence.md. Docs only: no test run beyond `python3 bin/processlint.py` if it reads these files.
4. The "For the PO" bullets and the glossary gap stay out of the docs (they go to the PO check-in).
Ticket path: `.scratch/c3-default-fix/issues/04-promote.md`.
