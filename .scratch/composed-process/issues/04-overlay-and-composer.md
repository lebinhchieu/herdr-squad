Status: ready-for-agent
Type: task
Task ID: 04
Touches: `bin/squadcompose.py` (new), `bin/squadrules_cli.py` (add `compose`, `rule`, `who`; `bin/squad-process` already delegates, 02), `tests/test_squadcompose.py` (new), `tests/fixtures/rules/compose/` (new)
Does not touch: `bin/squadrules.py` beyond imports (02 owns it; a needed parser change is an ASK to the Tech Lead), `templates/`, `agents/*`, `bin/squad-spawn`
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadcompose test_squadrules test_windows_safe`
Blocked by: 02

# 04: Overlay and composer

**Done when `squad-process compose`, `rule` and `who` behave as `spec.md` → Composed rules and CLI say, on fixtures.**

## What
- Scope facts come from the home's `scope.md`: `size:` (first S/M/L token), `design:`, `qa:`, `qa-b:`, and `goal:` (yes when a `goal:` line names a goal). A goal Manager's home (`goal.md`) has `goal: yes` and no size.
- The pin comes from `scope.md` `plugin:`. With no pin, use the plugin root of the running tool and print a warning; 05 makes the pin mandatory.
- Apply the overlay: `replace` and `remove` check the target's hash; `add` IDs must not exist in base.
- Filter by role in `roles`, `aware` or `all`, then by `when`. Core is always included. Order by file, then by position in the file.
- An aware-only rule is included with the tag `[aware]` after its title.
- Manager and Tech Lead also get `## Index of other rules`.
- `who <ID>` prints, for sizes S, M and L, the acting and aware roles.

## Technical AC
1. Stale `replace` (hash differs) exits 2 and prints `REV-3: overlay written for @7f3a9c21, plugin now @<new>`. Nothing is written.
2. `remove` of a missing ID, or `add` of an existing ID, exits 2 with the ID named.
3. Composition is byte-identical on repeat runs and on CRLF input; the `composed:` time is passed in by tests.
4. Fixture matrix (role × size × design × goal) gives the expected rule IDs. Includes: a `size = S` variant absent at M; a `design = yes` rule absent when design is no; a goal Manager getting both `-7a` and `-7b` (missing fact means true).
5. Source tags `[squad: replaced]` and `[squad: added]` appear exactly on overlay-touched rules.
6. `rule REV-3` prints the effective rule, overlay applied, with its source tag; an unknown ID exits 2.
