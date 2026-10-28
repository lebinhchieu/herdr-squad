# Evidence lives next to the ticket, screenshots are embedded

Status: accepted; folder name superseded 2026-10-22 (see Update)

Evidence for a ticket is one markdown file, `<ticket path minus .md>.evidence/evidence.md`, with its screenshots in `img/` beside it, embedded as `![alt](img/<file>)`. The PO reads that one file; nothing is mapped by hand.

- The folder is named `*.evidence`, not a sibling `.md`: readers that glob `issues/*.md` (`squad-report`) must not count evidence as a ticket.
- The Developer writes `## Behaviour` and commits it, images included, on its branch. Reviewers (Tech Lead, QAs) run in the project root, so they keep writing `qa-w.md`, `qa-b.md`, `tl-review.md` in `$SCOPE_DIR/evidence/<task>/`; after every checker passed, the Developer copies them into `evidence.md` with `squad-evidence add` and commits.
- That commit is the evidence sha: its diff to the passed sha touches only `*.evidence/` folders (`squad-evidence check --base`). The Manager merges the passed sha or the evidence sha after it.
- Suite receipts stay in `$SCOPE_DIR/evidence/`: a receipt names the sha it ran on and a later commit would change it.
- A project with no ticket files keeps evidence next to the `tasks/<id>.md` file.
- Existing evidence in open and closed scopes is not migrated.
- PNGs enter git history for good: at most 300 KB advised, 1 MB enforced by `squad-evidence check`.

## Update 2026-10-22

- The folder is now `<ticket path minus .md>/` (the `.evidence` suffix is dropped): it may hold more than evidence. A folder `10-x/` beside `10-x.md` is still not matched by a reader that globs `issues/*.md`, which was the reason for the suffix.
- `squad-evidence check --base` accepts a changed path only when it is `<stem>/evidence.md` or under `<stem>/img/` and `<stem>.md` exists, or it is under an old `*.evidence/` folder. Any other file in the folder is "outside an evidence folder".
- Old `*.evidence/` folders stay readable (and are written to while the new folder does not exist, never two folders) until ticket 09 adopts a squad. This repo's own folders were moved with `git mv`.
