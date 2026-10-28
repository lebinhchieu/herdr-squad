Status: done
Blocked by: none
Task ID: RB-02
Files touched: `bin/squad-start`, `bin/squadlabel.py`, `bin/squad-log-message` (comment), `skills/squad-start/SKILL.md`, `skills/squad-init/SKILL.md`, `README.md`, `hooks/po-inbox/ui.tsx`, `hooks/po-inbox/ui.test.ts`, `tests/test_squad_start.py`, `tests/test_squadlabel.py`, `tests/test_instructions.py`

# RB-02: Stop everything else from using the board

**Done when `squad-start`, the skills, the README and the PO inbox no longer start, mention or look for a board, while the board's own files are still in the tree.** Requirement: `spec.md` R-02, R-03, R-05..R-09. The board's own files (RB-03) are not touched here, so this runs beside RB-01.

## What to build
1. `bin/squad-start`: delete `open_board` and the `board` key of both JSON `print`s (resume path and new path). No other output change; stderr never says board.
2. `bin/squadlabel.py`: delete `BOARD_LABEL`, `LEGACY_BOARD_LABEL` (their only readers are the board and `tests/test_squadlabel.py::test_board_labels`). A tab titled `board` is an ordinary tab (R-06): confirm `squad-label` and `squad-spawn --title` have no special case (grep) and say so in `dev-evidence.md`.
3. `bin/squad-log-message` header comment: keep "append one record to messages.jsonl", drop "for squad-board" (say `squad-migrate` reads it). No code change.
4. `skills/squad-start/SKILL.md` step 7: drop the two board lines; the step ends after the tab and `process_update` lines. `skills/squad-init/SKILL.md:47`: "Only the board logs are ignored" becomes "Only the message logs are ignored"; the `*.jsonl` line stays. `tests/test_instructions.py::test_init_ignores_the_board_logs_when_everything_is_committed` is renamed `..._the_message_logs_...`, same assertion.
5. `README.md`: delete the "Squad board" section (lines about the tab, URL, token, recorder, guide), the "One board per herdr workspace" limit, and any board row of a file-layout table; keep `jq` in Requirements (the hook uses it). Do not add text.
6. `hooks/po-inbox/ui.tsx:264` and `ui.test.ts:457-460`: the notice becomes `Answer kept. escalations.md was not updated.` in both, test title too. `squad-inbox list --json` is untouched (R-07: byte-identical). Run the mod's own tests the way the repo does (`tests/test_po_inbox_mod.py`, and `contract.test.ts` if the repo runs it).
7. `tests/test_squad_start.py`: delete `BOARD_HERDR` and `BoardTest` (lines about 269-330); the existing tests keep their assertions. Their herdr stub already serves the non-board calls; the comment at line 94 ("only the board lookup runs") is reworded. `tests/test_squadlabel.py`: delete `test_board_labels`.

## Technical AC
1. No `open_board`, no `"board"` key, no `squad-board-start` string left in `bin/squad-start`; `git grep -n '"board"\|\.board\b' bin skills agents hooks` shows no remaining reader of the old JSON key.
2. `squad-start "<t>" --dry-run` and a real start in a scratch squad with a stub herdr/`claude` (use the existing `test_squad_start.py` harness): JSON keys equal `main`'s minus `board`; stdout+stderr contain no `board` (case-insensitive) — add this as an assertion in an existing start test, not a new class.
3. `tests/test_squad_start.py`, `test_squad_label.py`, `test_squadlabel.py`, `test_instructions.py`, `test_squad_log_message.py`, `test_po_inbox_mod.py`/hook tests green on their own; the 4 board suites that exist on this branch (`test_board_*`, `test_squad_board_start`) still pass (nothing they load was changed).
4. `git grep -inE 'board'` over the files of this ticket (README, the two SKILL.md, the six code/test files) lists no hit that says to use, open, restart or look for a board. A hit that is a different word is allowed and named in `dev-evidence.md`.
5. Diff touches only these files; every changed line is a deletion or the one-phrase rewording named above (CLAUDE.md surgical changes).
6. `--resume` JSON: a resume test asserts the printed JSON has no `board` key (the deleted BoardTest held the only `--resume` test; add `assertNotIn("board", json.loads(r.stdout))` to a resume test or add a small one).
- Receipt hygiene: run targeted tests with `PYTHONDONTWRITEBYTECODE=1`; `rm -rf bin/__pycache__` (gitignored, so `clean=yes` misses it; `test_no_pyc` fails on it) before the receipt run; `dev-evidence.md` quotes the receipt's real tail.

## Comments
