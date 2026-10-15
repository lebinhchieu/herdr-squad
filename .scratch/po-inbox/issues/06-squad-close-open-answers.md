Status: done
Blocked by: 01 (it reads `squad-inbox list --json --no-write`)
Task ID: PI-06
Files touched: `bin/squad-close`, `tests/test_squad_close.py`

# PI-06: `squad-close` refuses while answer items are open

**Done when `squad-close <squad> --scope S` and `--goal G` stop, naming each open or answered-but-undelivered answer item, unless `--force`.** Business AC: B-29 (deterministic). Design: `design.md` → CLI (`list`, home). Precedent: the `--goal` refusal without `promoted:` in `bin/squad-close` (same message style, same `--force`).

## What to build
- Before retiring anything: for the scope's folder (and for `--goal`, the goal folder and each of its open scopes? **No: only the home being closed**), run `squad-inbox list --json --no-write --home <folder>`; blocking = `kind: answer` and `state` open or answered-waiting. Read items do not block closing. If any: print `scope S has N open answer items: E3 <title>, … (answer or withdraw them first, or --force)` to stderr, exit 1, change nothing.
- If `squad-inbox` is missing or its output is not JSON, do not block (print a warning once); a broken inbox must never trap a close.

## Technical AC
1. Open `E` item → exit 1, message names ids and titles, nothing retired, folder not moved (assert no herdr call in the fake `herdr` log and the folder still in `scopes/`).
2. **`answered-waiting` blocks too** (K1: closing ends the Manager session that would receive the answer): message names it as `E3 <title> (answered, not yet read by the Manager)`. Answered (delivered), withdrawn and read items do not block.
3. `--force` closes despite open items; `--dry-run` reports the refusal without acting.
4. Goal: `--goal G` checks `$GOAL_DIR` only and still refuses on `promoted:` first (existing test unchanged and green).
5. A missing CLI or output that is not JSON warns and does not block. A malformed row (`errors` in the JSON) warns naming the file and row, since it may be an open question (K2).
6. Existing `tests/test_squad_close.py` tests unchanged and green; suite green with a receipt.
