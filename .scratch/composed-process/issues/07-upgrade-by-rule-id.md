Status: ready-for-agent
Type: task
Task ID: 07
Touches: `bin/squadupgrade.py` (new), `bin/squad-process` (add `upgrade`), `skills/squad-process-update/SKILL.md`, `skills/squad-process-update/changelog.md` (format from v7 on), `tests/test_squadupgrade.py` (new), `tests/fixtures/upgrade/` (new)
Does not touch: `bin/squadprocess.py` `apply` (kept for not-yet-migrated squads, retired in 09), `bin/squad-spawn`, `agents/*`
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadupgrade test_squadcompose test_process_history test_windows_safe`
Blocked by: 03, 04

# 07: Upgrade a squad one rule at a time

**Done when `squad-process upgrade --check` and `--apply` handle every case in the table below, write nothing until each flagged operation is resolved, and the plugin's CI dry-runs every release against fixture overlays.**

## Cases
| Plugin change | No overlay operation on the rule | Overlay operation on it |
|---|---|---|
| Add | applied | local rule with same `topic:` listed for review |
| Change (hash) | applied | stale: PO picks `keep` (re-hash local text), `take` (drop op) or `file:<path>` |
| Remove (tombstone) | applied | flagged: `drop`, `retarget:<new ID>` or `local` (becomes an `add SQ-n`) |
| Retarget only | applied | op keeps its body and takes new targeting unless it sets its own |
| Split/rename (tombstone + `replaced_by`) | applied | as Remove |

## What
- **Changelog:** from v7, each version lists `added:`, `changed:`, `removed:` and `retargeted:` IDs, with the why per item. `history/process-v<N>/` holds a copy of that version's rule folder.
- **`--check`:** prints counts and the list that needs a decision. Exit 0 when nothing needs one, 3 when something does.
- **`--apply`:** with `--resolve <ID>=<choice>` for each flagged item, it:
  - backs up the overlay;
  - rewrites the overlay with new hashes;
  - moves `$SQUAD_DIR/plugin.pin` to the new version;
  - adds rows to `process-log.md`.

  Running scopes keep their `scope.md` pin. `--yes` is required to write.
- **Upstream report:** `squad-process upstream` lists `upstream: proposed` operations, with why and body, ready to paste into a plugin ticket. An operation whose ID the plugin now ships with the same text is removed by `--apply`.
- **Skill:** `squad-process-update` turns flagged items into one inbox answer item with options. The PO's answer is passed back as `--resolve`.

## Technical AC
1. One fixture per case cell above, each with the expected `--check` output and post-`--apply` overlay.
2. A semantic-clash fixture: a local `add` in `topic: review` plus a changed plugin `review` rule. It is listed for review, not blocked.
3. Nothing is written when a flagged item has no `--resolve`, or without `--yes`. The backup exists after a write.
4. A CI test dry-runs the template against every overlay in `tests/fixtures/upgrade/` and fails on an unhandled operation. One fixture is the live squad's overlay as 09's dry run produced it, copied in by 09.
5. A running scope's `scope.md` pin is unchanged by `--apply` (test).
