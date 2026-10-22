Status: ready-for-agent (last task; starts after TAB-07 passed)
Task ID: TAB-08
Blocked by: TAB-07
Files touched: `CONTEXT.md`, `README.md`, `templates/squad/process.md`, `tests/test_instructions.py` only if a stale-token check needs the new text. The Manager edits `$SQUAD_DIR/process.md` itself (it owns it).
Serves: spec story 5 (glossary, process rule); the Tech Lead's `promote.md`

# TAB-08: promote the lasting facts

**Done when every line of `$SCOPE_DIR/promote.md` is in its target file with the wording given there, and nothing else changes.**

Read first: `$SCOPE_DIR/promote.md` (exact wording and targets), `CONTEXT.md` (glossary style), `process.md` → Promotion if it exists.

## Build
- `CONTEXT.md`: terms display label, address name, task text, squad session; one-line rules for tab labels (`<emoji> <Role>[ n] · <task>`, cut at 32) and toasts.
- `README.md`: add `bin/squad-label` and `squad-spawn --title` to the command table; the board tab is `📋 Board` (README line about the `board` herdr tab); `squad-start` renames the workspace.
- `templates/squad/process.md`: a short "Tab labels and toasts" rule: the label shape, emoji per role, the 32-character cut, numbering, who relabels whom, and the toast rule. This is what TAB-06's role text points at. (The Manager adds the same text to `$SQUAD_DIR/process.md` and logs it in `process-log.md`.)

## Technical AC
1. Each `promote.md` line appears once in its target; `git diff` shows only those files.
2. `python3 -m unittest tests.test_instructions tests.test_templates` passes (the template must not mention removed things).
3. The rule text matches the code (role names, cut length, emoji) by checking `bin/squadlabel.py`.
4. Full suite once on the final sha.
