# Evidence: 21 Evidence folder is the ticket path minus `.md`, no `.evidence` suffix

## Behaviour

### AC 1 path/add/check table
`tests/test_squad_evidence.py` `FolderResolutionTest`: nothing exists → new `<stem>/evidence.md` (no `img/` without an embedded image, no `.evidence`); only old → old, `add` appends, no second folder; both → new; `check` accepts old and new folder; non-`.md` ticket → exit 2 (`PathTest`).

### AC 2 `check --base`
`CheckBaseTest`: `<stem>/evidence.md` + `img/ nested png` exit 0; `<stem>/notes.txt`, `bin/x`, `docs/foo/evidence.md` (no `docs/foo.md`) exit 1 and listed; ticket `.md` deleted in the same diff → exit 1; old `*.evidence/` diff (any file, per BA ruling) → exit 0.

### AC 3 migration
`find .scratch -name '*.evidence'` empty; `git ls-files | grep '\.evidence/'` empty; `git show -M --summary HEAD~2` (migration commit): 27 renames, all `(100%)`; `squad-evidence check` exits 0 on every moved `evidence.md`.

### AC 4 leftovers of `.evidence` (grep over agents hooks skills README bin tests templates CONTEXT.md docs, minus `history/`)
Intentional: `bin/squadevidence.py` (legacy read/write, docstring, message), `tests/test_squad_evidence.py` (legacy tests), `templates/squad/process/evidence.md` and `CONTEXT.md` (say old folders stay readable), `docs/adr/0015` (original body + Update), `templates/squad/process.md` (legacy v6 monolith, left on purpose), `skills/squad-init/SKILL.md:48` (`*.jsonl`-style gitignore text, unrelated). Frozen `skills/squad-process-update/history/**` untouched. Closed `.scratch/evidence-inline/**` records and earlier evidence files keep old paths in the commands they quote (history). Live link fixed: `.scratch/composed-process/spec.md:177`.

### AC 5 lint and size
`python3 bin/squad-process lint` passes; `test_dev_rules_size` OK. Composed Developer rules (M/design no/goal no): 4901 B at base 4901cab and 4901 B now, delta 0 (EVID-1, FILE-9 and MRG-2 are not Developer rules).

### AC 6 ADR 0015
`git diff` adds lines only (a `Status:` line and `## Update 2026-10-22`).

### AC 7 encoding
All opens `encoding="utf-8", newline="\n"`; `test_windows_safe` OK.

### Readers of `issues/`
Only `bin/squadreport_tasks.py:68` globs `issues/*.md` (non-recursive, requires `^\d+-`), so a `NN-x/` folder is never a ticket. Ticket count in `.scratch/*/issues/*.md` by `git ls-tree`: 25 at 4901cab, 26 now; the extra one is this ticket's own file (21), the folder moves change nothing.

## QA blackbox

### QA-b 21 (sha 7b1d84e, branch squad/plugin/process-fixes/plugin-dev-pf-3)
Tool run from the worktree `bin/` in a temp git repo (issues/05-x.md etc.); no code read.

| AC | What I did | Saw | Result |
|---|---|---|---|
| 1 new | `squad-evidence add issues/05-x.md` (no folder) | `issues/05-x/evidence.md`; no `.evidence`. `img/` appears only when an image is embedded (second add with a png: `img/ a png`, embed rewritten to `img/ a png`) | pass (BA FINAL: img/ only when an image is embedded) |
| 1 old only | `add` on ticket with only `06-y.evidence/` | appended there, no second folder | pass |
| 2 | `path` with none / old / both; `add` with both | none → `05-x`; old → `.evidence`; both → new folder, old untouched | pass |
| 3 | `check --base` on commits: evidence.md+img; `img/ nested png` embedded; `notes.txt` in ticket folder; `src/a.py`; folder `issues/orphan/` with no `orphan.md`; `other/evidence.md` | 0; 0; 1 naming `issues/05-x/notes.txt`; 1 naming `src/a.py`; 1; 1 | pass |
| 3 legacy | extra file `n.txt` in old `06-y.evidence/`, `check --base` | exit 0 (accepted) | pass (BA FINAL: legacy folders keep old rule) |
| 4 | `git ls-files \| grep '\.evidence/'` = 0; `find -name '*.evidence'` empty; HEAD~1 = 27 pure renames; `git log --follow` on a moved file shows pre-move history; `squad-evidence check` on all 27 moved evidence.md ok | as stated | pass |
| 5 | `squad-report runtime-compose --no-html` with 4901cab bin vs new bin: data.json identical (except timestamp); `git ls-tree` count of `.scratch/*/issues/*.md` per feature identical before/after (13 features) | identical | pass |
| 6 | `squad-process rule EVID-1`, `FILE-9`; `git diff 4901cab HEAD -- docs/adr/0015*` | both name `<ticket path minus .md>/evidence.md`; ADR: +8 lines (Status line + `## Update 2026-10-22`), body untouched; spec line changed | pass |
| 7 | evidence of tickets 10-14, 21, 25, 26 at new path | not testable yet: this scope's `evidence.md` files do not exist on the branch | open, check at later tickets |

Notes:
- N1: AC1 says `img/` is created by `add`; it is created only when an image is embedded. Behaviour is sensible; BA to confirm AC wording.
- N2: BA AC3 "legacy `*.evidence/` accepted for the same files" — extra file in a legacy folder is accepted. BA to rule.
- Prose in two moved evidence.md (01, 02) and in old tickets still names `*.evidence/` paths: historical text, not a link; not a defect.

#### Verdict
PASS on 7b1d84e. N1, N2 ruled by BA (FINAL). AC7 re-checked when the later tickets land their evidence.

## QA whitebox

### QA whitebox: ticket 21 @ 7b1d84e (base 4901cab)

Verdict: **FAIL** (2 must-fix, 2 notes)

Ran: `test_squad_evidence test_process_conversion test_process_citations test_templates test_windows_safe test_dev_rules_size` = 90 OK; `squad-process lint` exit 0. Migration commit bbcf832: 27 renames, all 100%; `find .scratch -name '*.evidence'` empty; `git ls-files | grep '\.evidence/'` empty. Rule/doc edits (EVID-1, FILE-9, MRG-2 clause, project.md, CONTEXT, ADR 0015 additive, spec line) match the ticket.

#### Must fix
1. `bin/squadevidence.py` `is_evidence_path` (first `if`, regex `(^|/)[^/]+\.evidence/`): any file under an old `*.evidence/` folder is accepted. The agreed AC (`ticket-amendments.md` "Technical AC agreed", 21) says the old form accepts only `evidence.md` and `img/**`. Repro (fixture repo, ticket `i/05-z.md`, commit `i/05-z.evidence/notes.txt` + `evidence.md`): `squad-evidence check i/05-z.evidence --base <B>` → `ok`, rc 0. Pass: `notes.txt` under an old folder is reported "outside an evidence folder"; test added in `CheckBaseTest` (current "old form" test only commits `evidence.md`). ADR 0015 Update text says the same strict set for the old form only by implication; keep it consistent.
2. Missing test for the agreed AC: ticket `<stem>.md` deleted in the same diff (sibling must exist in the checked-out tree, so evidence of a deleted ticket is reported). Behaviour of the code is probably right; no test pins it.

#### Notes (not blocking alone)
3. Ticket file `21-evidence-folder-no-suffix.md` is not in `.scratch/composed-process/issues/` (amendments: first commit copies it so the evidence folder has a sibling). Needed before `squad-evidence add` / `check --base` can pass for 21's own evidence; add it with the fix.
4. Remaining `.evidence` mentions in tracked files are historical records (closed ticket/evidence texts under `.scratch/evidence-inline/**`, `01-/02-` evidence, `03` mapping.md, ADR 0015 body, `templates/squad/process.md` legacy monolith). Acceptable if the Developer lists them in `evidence.md` as intentional; `skills/squad-init/SKILL.md:48` has no old path (false hit).
Not yet seen: the AC 5 `squad-report` ticket-count before/after and the grep of every `issues/` reader (belongs in `evidence.md`, checked at the evidence commit).

#### Re-check @ 27df79d (diff 7b1d84e..27df79d: tests only)
Verdict: **PASS** (code and tests).
- Finding 1 withdrawn: `business-ac.md` §21 AC3 (BA ruling on QAB ASK 21, agreed by BA and QAB) keeps the old any-file rule for legacy `*.evidence/`; business behaviour wins over the amendment. Now pinned by `test_old_form_folder_keeps_the_any_file_rule`. ADR 0015 Update text matches.
- Findings 2, 3 done: `test_ticket_deleted_in_the_same_diff_fails`, `test_add_creates_no_img_folder_without_images`, ticket copied to `.scratch/composed-process/issues/21-evidence-folder-no-suffix.md`.
- Re-ran the harness: 93 tests OK; `squad-process lint` exit 0.
- Open for the evidence commit (not code): the AC 4/5 greps and the intentional-leftover list, `squad-report` count before/after, byte delta of the Developer rules.
