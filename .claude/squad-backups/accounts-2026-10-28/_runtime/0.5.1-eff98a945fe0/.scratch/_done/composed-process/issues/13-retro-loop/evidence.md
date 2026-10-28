# Evidence 13: the retro keeps what it learns

Branch `squad/plugin/process-fixes/plugin-dev-pf-6`, base 2f2e5a7. Old-form folder (ticket 21 is not in this branch; moved at integration).
sha: 297cd22
## Technical AC
1. **Empty retro refuses.** `tests/test_squad_close.py::RetroCloseTest`: each of `Went well`, `Friction`, `Process changes made` empty → exit 1, stderr names it (`scope sc1 has an empty retro in its last iteration file: Friction (…or --force)`), nothing retired or moved. `--force` → exit 0, stdout `WARNING: closing with an empty retro (--force): Friction`, and the archived iteration file gets `- <date> squad-close --force: empty retro (Friction)` under `## Log` (tested with `## Log` present and absent). `--force` on a filled retro and `--dry-run --force` write nothing.
2. **`who`.** `tests/test_retro_rules.py`: ITER-13, ITER-14 act = `token-coach`; ITER-15, ITER-16 act = `manager` at S, M, L. Rule text asserts: backlog read, 2+ scopes cite both, overlay + `upstream: proposed`, `## Plugin proposals`, `tasks/` drafts, tracker, `--force`.
3. **Coach dry run** (Haiku, temp squad, `--max-budget-usd 0.10`): two earlier coach files (`scopes/_done/alpha/iterations/1.coach.md`, `goals/_done/g1/coach/g1.coach.md`) share the backlog item "Dev idles at 120k context…". Cost **$0.0118**. Output `coach-dry-run.md` cites both paths under one proposal (ITER-13), writes the change as `upstream: proposed`, and lists a `## Plugin proposals` item. (The overlay block it wrote is loose pseudo-syntax; the rule asks for `process.local.md` syntax and Haiku had no example.)

## Rulings applied (TL amendments over BA text where they differ)
- Retro fields are bold bullets; accepted: `**Label:**`/`**Label**:`, or a `### Label` heading. Continuation lines and sub-bullets count as text. A `<…>` that is the whole text is empty; `none`, `-`, `n/a` are text. Section = any heading starting `Retro` (`## Retro / Coach` works). Missing label = empty.
- Last iteration = highest numeric `n` among `<n>.md` (`10` after `9`; `.log/.summary/.coach` ignored).
- No iteration file (or a legacy flat squad): no refusal. BA aligned `business-ac.md` §13 to the TL amendment (2026-10-22); no conflict left.
- `--goal` untouched. `--force` + `--dry-run` writes nothing.
- ITER-7 and ITER-9 got a minimal edit (they said "read only usage" and "propose only rule changes"); the ITER-7 edit follows BA additions. New blocks ITER-13..16. Card: one stance line. The "Plugin proposals become `$SCOPE_DIR/tasks/` drafts" BA ruling is ITER-15. The template has no "Plugin follow-ups" bullet (not in Touches); ITER-15 names it as the ticket does.

## Developer-rules byte delta
Composed `dev` rules at M/design no/goal no: 4901 B before (2f2e5a7) and after: **+0 B** (new blocks target manager and token-coach only; limit 5120).

## Commands
`cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_close test_retro_rules test_windows_safe test_manager_inbox_read test_dev_rules_size test_process_conversion test_squadrules` → 156 tests OK. `squad-process lint` rc 0.

## QA whitebox review

### QA whitebox 13 (retro loop): PASS @ a6e06f0 (297cd22 = evidence only)

Ran (detached worktree): `test_squad_close test_retro_rules test_windows_safe test_dev_rules_size test_processlint test_squadrules` = 160 OK; `squad-process lint` ok. Reviewed 2f2e5a7..a6e06f0 (squad-close, ITER-7/8/13-16, token-coach card one line, tests).
Independent probe: the `retro_check` heredoc run directly on 10 fixtures: full retro rc 0; `<placeholder>` + continuation-line + `none`; `10.md` after `9.md` wins; `--force` inserts the dated `## Log` bullet (log section present and absent); `n/a` and `-` count as text; a label under a later non-Retro section does not count; CRLF file read right; the template's own empty `Went well` / `<…>` placeholders are empty (a fresh scope refuses until filled). Aux files (`.log/.summary/.coach`) ignored. Mode `scope` only: goal and legacy flat squads unchanged.
Delta of dev rules +0 B (ITER-13..16 target token-coach/manager).
Coach dry run (AC 3): coach-dry-run.md cites both backlog files, `upstream: proposed`, a `## Plugin proposals` item; $0.0118. Overlay block is loose pseudo-syntax (Haiku had no example): accepted.

#### Notes (not blocking)
1. `retro\b` means `## Retrospective` is not a Retro section (refuses, fail-safe); the AC says "starts with Retro". Live files use `## Retro / Coach`.
2. A forced close rewrites the iteration file with LF endings (CRLF normalised); repo rule is LF.
3. An empty label followed by an unlabeled free paragraph counts the paragraph as its text (agreed continuation rule).
4. Evidence is old-form (`13-retro-loop.evidence/`); integration re-runs the `git mv`.

## QA blackbox review

### QA-b 13 (code a6e06f0, evidence sha 297cd22, branch squad/plugin/process-fixes/plugin-dev-pf-6)
Method: temp git project with `.claude/squads/t` (project.md, process.md, scopes); real `bin/squad-close t --scope S [--dry-run|--force]`; `squad-process compose/who`; one live Haiku Coach run (cap $0.10). No code read.

| AC | What I did | Saw | Result |
| --- | --- | --- | --- |
| 1 | Last iteration file with Friction empty / Friction = `<loops, blocked panes, ...>` placeholder / Went well empty / Process changes made empty / all three blank (real run, not dry) | exit 1 each, `scope X has an empty retro in its last iteration file: <label(s)> (fill Went well, Friction and Process changes made, or --force)`; all-blank names all three; scope folder not moved | pass |
| 2 | labels filled with text, "none", "nothing", sub-bullet text under Went well | proceeds (dry-run goes on to agents/branches/folder) | pass |
| 3 | `--force` on blank retro | closes (archived to `_done`), warns `closing with an empty retro (--force): ...`; iteration file gains `- 2026-10-22 squad-close --force: empty retro (Went well, Friction, Process changes made)` under `## Log`; works with `## Retro / Coach` free heading too | pass |
| 4 | `1.md` filled + `1.log.md`, `1.coach.md`, `1.summary.md` with blank labels | proceeds; highest-n rule: `2.md` filled and `10.md` blank → refuses on 10 | pass |
| 5 | Composed token-coach (M) | ITER-7 reads earlier backlogs; ITER-13 promotes an item in 2+ scopes and cites both coach files; ITER-14 proposals as overlay ops with `upstream: proposed`, tool/role-card findings under `## Plugin proposals` | pass |
| 6 | Live Haiku Coach run on my fixture (alpha and beta coach files share one backlog item, beta has a second item) | `--max-budget-usd 0.10`; file cites `scopes/_done/alpha/iterations/1.coach.md` and `scopes/_done/beta/iterations/1.coach.md`; the one-scope item not promoted; empty `## Backlog`. Developer's own run also in `.scratch/composed-process/issues/13-retro-loop.evidence/coach-dry-run.md` ($0.0118) | pass |
| 7 | `squad-process who ITER-13/14/15/16` | 13, 14: token-coach acts at S/M/L; 15, 16: manager acts at S/M/L | pass |
| 8 | Composed manager (M) | ITER-15: each Coach `## Plugin proposals` item becomes one draft in `$SCOPE_DIR/tasks/` ([FILE-11], never the project root), or the plugin tracker named in `project.md`; draft paths listed in the check-in item. ITER-16 blank-retro rule present | pass |
| extra | no iteration file | no refusal (BA FINAL ANSWER 13: amendment stands; business-ac.md corrected) | pass |

Verdict: PASS 13 on 297cd22.
