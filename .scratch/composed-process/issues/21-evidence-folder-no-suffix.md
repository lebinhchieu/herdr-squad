Status: ready-for-agent
Type: task
Task ID: 21
Touches: `bin/squadevidence.py` (folder rule, `--base` rule, docstring), `templates/squad/process/evidence.md` (EVID-1 only), `templates/squad/process/files.md` (FILE-9 only), `templates/squad/process/merge.md` (the `*.evidence/` mention), `templates/squad/project.md` (Evidence row), `CONTEXT.md` (Evidence term), `docs/adr/0015-evidence-next-to-the-ticket.md` (superseding note), `tests/test_squad_evidence.py`, `tests/test_process_conversion.py` (`MAPPING` path), `.scratch/composed-process/spec.md` (Global technical AC line) and every tracked doc that links an old path (grep `\.evidence/`; closed scopes' squad folders are left, listed in the evidence), `git mv` of every `*.evidence/` folder: `.scratch/composed-process/issues/{01..09,22}-*.evidence` and `.scratch/evidence-inline/issues/{01..05}-*.evidence` (22's folder has no `22-*.md` beside it: it moves too and stays an orphan folder; nothing writes to it again)
Does not touch: `skills/squad-process-update/history/**` (frozen archive), `templates/squad/process.md` (legacy v6 monolith; the tool is the source of truth for legacy squads), `bin/squad-spawn`, `bin/squad-log-message`, `bin/squad-close`, other blocks of `evidence.md`/`files.md` (tickets 10 and 14 add blocks to those files in parallel; edit only the lines named here)
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_evidence test_process_conversion test_process_citations test_templates test_windows_safe`; `python3 bin/squad-process lint`
Blocked by: none

# 21: Evidence folder is the ticket path minus `.md`, no `.evidence` suffix

**Done when `squad-evidence` writes `<ticket path minus .md>/evidence.md` (images in `img/`), still reads and checks an existing `*.evidence/` folder, no `*.evidence/` folder is left in this repo, and the rules, glossary and ADR 0015 say the new path.**

## Why
PO 2026-10-22 (goal decisions): the folder may hold more than evidence, so the `.evidence` suffix is wrong. A folder `10-x/` next to `10-x.md` is still not matched by a reader that globs `issues/*.md`, which was ADR 0015's reason for the suffix.

## What
- **`evidence_folder(ticket)`** returns `ticket[:-3]` (no suffix). Resolution:
  - nothing exists: the new folder;
  - only an old `<stem>.evidence/` exists: the old folder (an in-flight ticket of a squad that has not adopted keeps one folder; never two);
  - both exist: the new folder.
  `path` prints the resolved folder; `add` writes into it; `check <folder|evidence.md>` accepts either name.
- **`check --base SHA`** (BA ruling: folders already hold other files, e.g. `03-…/mapping.md`, so "inside a ticket folder" is not proof of evidence): a changed path is evidence only when it is `<stem>/evidence.md` or under `<stem>/img/` (any depth), and `<stem>.md` exists in the checked-out tree; or it is under an old `*.evidence/` folder (legacy form, same files). Anything else (`<stem>/notes.txt`, a path whose stem has no sibling `.md`, `src/a.py`) is reported "outside an evidence folder" naming the path; the message names both forms. The evidence commit after a pass must not alter the ticket's other deliverables.
- **Migration:** `git mv` each existing `*.evidence` folder to the new name (a pure rename commit, separate from the code commit, so history follows). Fix the one reader of an old path in the tests (`test_process_conversion.py` `MAPPING`) and update links in tracked docs by grep. A project with no ticket files: `tasks/<id>/evidence.md`.
- **Leftovers:** the Developers of 10, 12, 14 and 25/26 run the pinned (old) `squad-evidence`, so their evidence lands in `*.evidence/`. The integration task re-runs the `git mv` for any `*.evidence/` that appeared, re-runs `find`, and re-checks (AC 3 is final there). Ticket 21's own evidence is written by its branch's tool at the new path.
- **Ticket file:** this ticket lives in `$SCOPE_DIR/tasks/`; the Developer's first commit copies it to `.scratch/composed-process/issues/21-evidence-folder-no-suffix.md` so its evidence folder has a sibling.
- **Rules and docs:** EVID-1, FILE-9, the `merge.md` sentence, `templates/squad/project.md`, `CONTEXT.md` name the new path. ADR 0015 keeps its text, gains a `Status:` line and a final `## Update 2026-10-22` saying the folder is now `<ticket path minus .md>/` (suffix dropped, reason above), the `--base` rule, and that old folders stay readable until ticket 09 adopts a squad. Everything else in the ADR stays.
- Rule IDs stay; hashes change by design (unreleased; goal decision on ticket 22).

## Technical AC
1. `path`/`add`/`check` table: (nothing exists → new, `add` creates `<stem>/evidence.md` and `<stem>/img/`), (only old → old, `add` appends there and creates no second folder), (both → new), (`check` on an old and on a new folder → same result), (a ticket not ending `.md` → exit 2 as today).
2. `check --base` on a fixture repo: a diff touching only `<stem>/evidence.md` and `<stem>/img/a.png` exits 0 (`img/a/b.png` too); `<stem>/notes.txt`, `bin/x`, and a `docs/foo/evidence.md` with no `docs/foo.md` exit 1 with the path listed; an old-style `*.evidence/` diff exits 0.
3. Migration (final at integration): `find .scratch -name '*.evidence'` prints nothing and `git ls-files | grep '\.evidence/'` is empty; `git show --stat -M` of the migration commit lists only renames (100% similarity); `squad-evidence check` exits 0 on every moved `evidence.md`.
4. `grep -rn '\.evidence' templates/squad/process templates/squad/project.md CONTEXT.md bin tests` shows only the intentional legacy-read lines (code and its tests); the frozen `skills/.../history/**` is untouched.
5. `squad-report` on this repo gives the same ticket count per feature before and after (it counts `issues/*.md` only; a folder `NN-x/` beside `NN-x.md` is not counted). `squad-process lint` passes; `test_dev_rules_size` still passes (EVID-1/FILE-9 do not grow past their blocks).
6. ADR 0015: the original body is unchanged (diff adds lines only), the Update section is present.
7. The evidence of 10-14, 21, 25 and 26 sits at the new path `<ticket path minus .md>/evidence.md` once the integration task has run its mop-up (BA AC). The moved 22 folder has no `22-*.md`, so `check --base` on it fails by design; only `check` (exit 0) applies to it; say so in the evidence.
8. All file opens use `encoding="utf-8"` and `newline="\n"`; `test_windows_safe` passes.

## Notes (Tech Lead)
- Per-pin rule: an old folder stays in use only while it exists and the new one does not, so a squad never has two evidence files for one ticket. If the PO wants "always write new" instead, `add` must copy the old folder across first; not done here.
- Ticket 09 (done) adopts squads without touching evidence folders; no migration step for other repos' tickets is added here.
