# Evidence lives next to the ticket, screenshots are embedded

Evidence for a ticket is one markdown file, `<ticket path minus .md>.evidence/evidence.md`, with its screenshots in `img/` beside it, embedded as `![alt](img/<file>)`. The PO reads that one file; nothing is mapped by hand.

- The folder is named `*.evidence`, not a sibling `.md`: readers that glob `issues/*.md` (`squad-report`) must not count evidence as a ticket.
- The Developer writes `## Behaviour` and commits it, images included, on its branch. Reviewers (Tech Lead, QAs) run in the project root, so they keep writing `qa-w.md`, `qa-b.md`, `tl-review.md` in `$SCOPE_DIR/evidence/<task>/`; after every checker passed, the Developer copies them into `evidence.md` with `squad-evidence add` and commits.
- That commit is the evidence sha: its diff to the passed sha touches only `*.evidence/` folders (`squad-evidence check --base`). The Manager merges the passed sha or the evidence sha after it.
- Suite receipts stay in `$SCOPE_DIR/evidence/`: a receipt names the sha it ran on and a later commit would change it.
- A project with no ticket files keeps evidence next to the `tasks/<id>.md` file.
- Existing evidence in open and closed scopes is not migrated.
- PNGs enter git history for good: at most 300 KB advised, 1 MB enforced by `squad-evidence check`.
