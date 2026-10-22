Status: ready-for-agent
Task ID: TAB-03
Blocked by: none (file-disjoint from TAB-01, TAB-02, TAB-04)
Files touched: `bin/squad-start`, `tests/test_squad_start.py`
Serves: spec story 9 (D6, B6)

# TAB-03: `squad-start` names the herdr workspace

**Done when `squad-start` renames the caller's herdr workspace to the goal name (goal) or scope name (lone scope), and every failure or non-herdr case leaves the start untouched.**

Read first: spec story 9, B6, `bin/squad-start`, `tests/test_squad_start.py`.

## Build
- After the Manager started successfully (so a failed start does not rename), and also at the end of `resume()`: if `HERDR_ENV == "1"` and `HERDR_WORKSPACE_ID` is set, run `herdr workspace rename "$HERDR_WORKSPACE_ID" <name>` where `<name>` is the goal or scope name (`name`, or the resumed name).
- Not for `--in-goal` (no Manager of its own: the goal name stays), not for `--dry-run`.
- Failure (herdr exits non-zero, missing binary, timeout 10 s): a one-line warning on stderr; exit code and the printed JSON line stay as they are. Outside herdr: do nothing and say nothing.
- Pass the name as a list argument (it is already validated by `NAME_RE`).

## Technical AC
1. With the fake `herdr` of `test_squad_start.py` logging calls: lone scope -> `workspace rename wK <scope>`; `goal:` text -> goal name; `--in-goal` -> no rename call; `--resume NAME` (goal or scope) -> rename to NAME; `--dry-run` -> none; `HERDR_ENV` unset -> none and no warning; `HERDR_WORKSPACE_ID` unset -> none.
2. A fake `herdr workspace rename` that exits 1: `squad-start` exit code 0, the same stdout JSON, one warning line on stderr, scope folder and Manager exist.
3. A failed Manager start (spawn exits non-zero) does not call rename.
4. Two starts in a row each rename (last start wins).
5. **Live check only in the throwaway workspace `squad-tabs-test`** (never the PO's workspace): one real `herdr workspace rename` call on it, saved in `evidence/TAB-03/`; no real `squad-start` live run (it would spawn a Manager).
6. Targeted tests pass; full suite once on the final sha.
