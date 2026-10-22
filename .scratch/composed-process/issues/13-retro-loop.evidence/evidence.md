# Evidence 13: the retro keeps what it learns

Branch `squad/plugin/process-fixes/plugin-dev-pf-6`, base 2f2e5a7. Old-form folder (ticket 21 is not in this branch; moved at integration).

## Technical AC
1. **Empty retro refuses.** `tests/test_squad_close.py::RetroCloseTest`: each of `Went well`, `Friction`, `Process changes made` empty → exit 1, stderr names it (`scope sc1 has an empty retro in its last iteration file: Friction (…or --force)`), nothing retired or moved. `--force` → exit 0, stdout `WARNING: closing with an empty retro (--force): Friction`, and the archived iteration file gets `- <date> squad-close --force: empty retro (Friction)` under `## Log` (tested with `## Log` present and absent). `--force` on a filled retro and `--dry-run --force` write nothing.
2. **`who`.** `tests/test_retro_rules.py`: ITER-13, ITER-14 act = `token-coach`; ITER-15, ITER-16 act = `manager` at S, M, L. Rule text asserts: backlog read, 2+ scopes cite both, overlay + `upstream: proposed`, `## Plugin proposals`, `tasks/` drafts, tracker, `--force`.
3. **Coach dry run** (Haiku, temp squad, `--max-budget-usd 0.10`): two earlier coach files (`scopes/_done/alpha/iterations/1.coach.md`, `goals/_done/g1/coach/g1.coach.md`) share the backlog item "Dev idles at 120k context…". Cost **$0.0118**. Output `coach-dry-run.md` cites both paths under one proposal (ITER-13), writes the change as `upstream: proposed`, and lists a `## Plugin proposals` item. (The overlay block it wrote is loose pseudo-syntax; the rule asks for `process.local.md` syntax and Haiku had no example.)

## Rulings applied (TL amendments over BA text where they differ)
- Retro fields are bold bullets; accepted: `**Label:**`/`**Label**:`, or a `### Label` heading. Continuation lines and sub-bullets count as text. A `<…>` that is the whole text is empty; `none`, `-`, `n/a` are text. Section = any heading starting `Retro` (`## Retro / Coach` works). Missing label = empty.
- Last iteration = highest numeric `n` among `<n>.md` (`10` after `9`; `.log/.summary/.coach` ignored).
- **Conflict:** BA says "no iteration file counts as empty"; TL amendment says no refusal for none, or a legacy flat squad. I followed the TL (existing close tests and legacy squads have none). BA to confirm.
- `--goal` untouched. `--force` + `--dry-run` writes nothing.
- ITER-7 and ITER-9 got a minimal edit (they said "read only usage" and "propose only rule changes"); the ITER-7 edit follows BA additions. New blocks ITER-13..16. Card: one stance line. The "Plugin proposals become `$SCOPE_DIR/tasks/` drafts" BA ruling is ITER-15. The template has no "Plugin follow-ups" bullet (not in Touches); ITER-15 names it as the ticket does.

## Developer-rules byte delta
Composed `dev` rules at M/design no/goal no: 4901 B before (2f2e5a7) and after: **+0 B** (new blocks target manager and token-coach only; limit 5120).

## Commands
`cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_close test_retro_rules test_windows_safe test_manager_inbox_read test_dev_rules_size test_process_conversion test_squadrules` → 156 tests OK. `squad-process lint` rc 0.
