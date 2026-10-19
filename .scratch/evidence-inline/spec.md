# evidence-inline: evidence next to the ticket, screenshots inline

Status: ready-for-agent
Scope: `.claude/squads/plugin/scopes/evidence-inline` (size S, PO chose S 2026-10-19)

**Outcome:** the PO opens one markdown file per ticket and sees what was checked, the verdicts and every screenshot rendered in place. No hunting in `$SCOPE_DIR/evidence/`, no image that is only named.

## Layout contract (every ticket builds on this; change it only by re-issuing the tickets)

| Item | Rule |
|---|---|
| Ticket | `<dir>/<NN>-<slug>.md` (`.scratch/<feature>/issues/`), or `$SCOPE_DIR/tasks/<id>.md` when the project has no ticket files |
| Evidence folder | the ticket path with `.md` replaced by `.evidence/`, e.g. `.scratch/f/issues/03-x.evidence/` (a **folder**, so `issues/*.md` readers never see it as a ticket: `bin/squadreport_tasks.py:67` globs `issues/*.md` by `^\d+-`) |
| The one file | `<evidence folder>/evidence.md` |
| Images | `<evidence folder>/img/<name>.<png\|jpg\|jpeg\|gif\|webp>`, embedded only as `![alt](img/<name>)`: relative, non-empty alt, no `..`, no absolute path, no URL |
| Where it is committed | tickets in `.scratch/` (committed): evidence goes in the **Developer's branch**, with the code, images included. Tickets in `tasks/` (squad folder, normally untracked): evidence sits next to the task file, local, not committed |
| Working files | `$SCOPE_DIR/evidence/<task>/` stays for the reviewers' own files (`qa-w.md`, `qa-b.md`, `tl-review.md`), suite receipts and copied report deliverables. The PO never needs to open it |

`evidence.md` shape:

```
# Evidence: <NN> <ticket title>
sha: <40-hex sha the checks ran on>

## Behaviour            <- Developer: per AC: the AC, what was run, what was seen, screenshot(s)
## Tech Lead review     <- S: tl-review.md, verbatim
## QA whitebox          <- M, L: qa-w.md, verbatim
## QA blackbox          <- M, L: qa-b.md, verbatim
```

## Decisions (the open points of `iterations/1.md`)

1. **Path:** the contract above. One rule for tickets of any home, so there is no separate fallback branch for tickets without a `.scratch` file: "next to the ticket" means next to wherever the ticket file is.
2. **Images are committed with the ticket on the Developer's branch.** Size: at most 300 KB advised (viewport shots, png), `squad-evidence check` fails over 1 MB. PNG history is permanent: asked to the PO (ASK 1).
3. **Reviewers' content reaches the one file** by assembly, not by reviewers writing into the repo: TL, QAs and the Manager run in the project root (the PO's tree). Anything they write under `.scratch/` would dirty it (the Manager refuses to merge on a dirty root) and can collide with the Dev branch at merge. So reviewers write where they do now. After every checker passed, the **Developer** runs `squad-evidence add <ticket> --heading "<Heading>" --from <review file>` for each, which copies the review verbatim, copies the screenshots it references into `img/`, rewrites the links, and replaces the section if it exists. The Developer commits.
4. **That commit is the "evidence sha".** Its diff to the sha the checkers passed touches only `*.evidence/` folders; the Tech Lead proves it with `squad-evidence check <folder> --base <passed sha>`. Checkers are not asked again. The Manager's merge rule accepts the passed sha or the evidence sha after it, and no other. Changes the Safety merge rule: asked to the PO (ASK 2).
5. **Suite receipts stay in `$SCOPE_DIR/evidence/`:** the receipt names the sha it ran on and a later commit would change it. The check-in quotes sha and OK line.
6. **Existing evidence is left alone:** no migration of `_done` or open scopes, no change to `evidence/` folders already written. A squad whose `process.md` is below v6 keeps the old rule until the PO runs `squad-process update`.
7. **No change** to `bin/squad-close` (archives `scopes/<s>/` as before; ticket evidence lives in the repo), `bin/squad-migrate` (flat → per-scope only), `bin/squad-start` (still makes `evidence/` for the working files), `tests/run_suite.py` (its dirty check keeps ignoring only `evidence/`; evidence must be committed before a suite run).
8. **Squad's own `.claude/squads/plugin/process.md`, `project.md`, `settings/` are git-ignored (`.gitignore:3`), so no ticket can change them on a Dev branch.** The templates change in the repo; after the PO merges, the Manager brings the squad copy up with `squad-process update`, edits its own `project.md` Evidence row and adds the `squad-evidence` allow rules to its `settings/dev.json` and `settings/tech-lead.json` if they exist (a squad's settings override the plugin's).
9. **Process version:** `templates/squad/process.md` → `process-version: 6`, `skills/squad-process-update/history/process-v6.md` (equal to the template), changelog block `## v6`. `tests/test_process_history.py` guards all of it.

## The tool: `bin/squad-evidence` (python wrapper + `bin/squadevidence.py`, like `squad-report`)

- `squad-evidence path <ticket file>` prints the evidence folder.
- `squad-evidence add <ticket file> --heading <H> --from <review.md> [--root DIR]`: creates `evidence.md` (title from the ticket's first `# ` line, `sha:` line left as given by `--sha`, default none) if absent; adds or replaces `## <H>`; reviewer headings demoted to start at `###`; local image refs (`![](p)` relative to the review file's folder, or absolute) copied to `img/` (name clash → prefix `<slug of H>-`), links rewritten to `img/<name>`. A referenced image that does not exist → exit 2, nothing written. Idempotent on a second run.
- `squad-evidence check <evidence.md or folder> [--base SHA]`: exit 0 clean, 1 with one `file:line: problem` per line. Problems: an embed that is absolute, a URL, has `..`, an empty alt, a missing target or a non-image extension; an image in `img/` that no embed uses; an image path or image file name mentioned outside an embed (a bare, linked or backticked screenshot is not evidence); an image over 1 MB; with `--base`, any path in `git diff --name-only <SHA> HEAD` outside a `*.evidence/` folder.
- Exit 2 on usage errors. UTF-8, LF, every file read/written with `encoding="utf-8"`, `newline="\n"` (`tests/test_windows_safe.py` enforces).
- Allow rules: `Bash(squad-evidence:*)` in `templates/squad/settings/dev.json`; `Bash(squad-evidence check:*)` and `Bash(squad-evidence path:*)` in `tech-lead.json`.

## Tickets and order

| # | Ticket | Files | Parallel |
|---|---|---|---|
| 01 | `squad-evidence` tool + tests + allow rules | `bin/squad-evidence`, `bin/squadevidence.py`, `tests/test_squad_evidence.py`, `templates/squad/settings/dev.json`, `templates/squad/settings/tech-lead.json` | yes |
| 02 | process v6: rule text, project.md row, squad-init, snapshot, changelog | `templates/squad/process.md`, `templates/squad/project.md`, `skills/squad-init/SKILL.md`, `skills/squad-process-update/history/process-v6.md`, `skills/squad-process-update/changelog.md` | yes |
| 03 | role files | `agents/dev.md`, `agents/tech-lead.md`, `agents/qa-whitebox.md`, `agents/qa-blackbox.md`, `agents/manager.md`, `agents/team-lead.md`, `tests/test_instructions.py` | yes |
| 04 | integration + live check | merge of 01–03 into one branch; no new files except the evidence of 01–03 | after 01–03 passed |
| 05 | promotion | `docs/adr/0015-evidence-next-to-the-ticket.md`, `CONTEXT.md` | after 04 |

01, 02 and 03 share no file and can run in parallel (3 Developers). 02 and 03 quote the wording in this spec and the `squad-evidence` command line; neither reads the other's branch.

## Global technical AC (every ticket)

- Existing tests touched pass; new behaviour has a test; no full suite (only the Tech Lead runs it).
- `python3 bin/processlint.py templates/squad/process.md` passes where `process.md` changes.
- No file under `bin/` breaks `tests/test_windows_safe.py`.
- The Developer writes this ticket's own evidence in the new layout: `.scratch/evidence-inline/issues/<NN>-<slug>.evidence/evidence.md` with a `## Behaviour` section, screenshots embedded, committed on its branch. Where the ticket has no screenshot, it has the command output as a fenced block. (A first live use of the layout; the old role files still say `dev-evidence.md` and the Developer follows this ticket.)
- One commit per fix round; the final sha is named in `HANDIN`.

## Rollback and compatibility

Additive: a squad on process v5 keeps working (its roles never call the tool). Reverting is reverting the merge; evidence folders already written are plain markdown and stay readable. Deploy order: PO merges → Manager runs `squad-process update` and edits the squad's own `project.md`/settings (decision 8) → live roles re-read `process.md`.
