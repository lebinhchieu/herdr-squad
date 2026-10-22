Status: ready-for-agent
Task ID: TAB-02
Blocked by: TAB-01 (branch from TAB-01's passed sha; it imports nothing but calls `bin/squad-label --init`)
Files touched: `bin/squad-spawn`, `bin/squad-respawn`, `bin/squad-board-start`, `bin/squad-label` (only the new `--init --dry-run` flag), `tests/test_squad_label.py` (only its test), `tests/test_squad_spawn.py`, `tests/test_squad_respawn.py`, `tests/test_squad_board_start.py`
Serves: spec stories 1, 2, 4 (`--title`), 6, 7

# TAB-02: tabs get their label at spawn, respawn and board start

**Done when every tab `squad-spawn` opens is labelled `<emoji> <Role>[ n][ · <task>]`, a respawn brings the same label back, and the board tab is `📋 Board` and found by that label.**

Read first: TAB-01 (the contract), spec stories 1, 2, 6, 7 and B4, B5, the three scripts and their tests.

## Build
1. **`squad-spawn --title "<text>"`** (default blank; added to usage). Before `herdr tab create` it runs `squad-label --init --home "$home" --agent <name> --role <role> --title <text>` and passes its stdout as `--label`. `$home` is the `home` the script already computes (scope dir for a scope agent, goal dir for a goal Manager, `$SQUAD_DIR` in the legacy layout) and is passed as a flag: **never rely on the caller's inherited `SCOPE_DIR`/`GOAL_DIR`**. `--dry-run` runs the same call with `squad-label --init --dry-run`, **which this ticket adds to `bin/squad-label`** (not in TAB-01 as passed: it prints the label exactly as `--init` would, writes no store file and renames no tab; no other change to that file) and prints that label; no second label code path in `squad-spawn`. If `squad-label --init` fails, fall back to `--label <name>` with a warning: a label must never stop an agent from starting.
2. **`squad-respawn`** reads the stored title with `squad-label --get-title --home "$home" --agent <name>` (its own `home` rule) and passes `--title` to `squad-spawn` when it is not blank. The number is kept by TAB-01's rule (stored number is reused). Manager and every other role alike (B4). No stored entry (an agent spawned before this change): spawn assigns normally and the title is blank.
3. **`squad-board-start`**: the new tab is created with `--label "📋 Board"`. The lookup accepts `📋 Board` **or** the legacy `board`; a legacy tab that is reused is renamed to `📋 Board` (`herdr tab rename`), so no second board opens (B5). `--restart` closes whichever it finds. Legacy flat layout squads behave the same (D5).
4. **Short temporary name in `squad-respawn`** (found by the Manager 2026-10-14): the old agent is renamed to `<name>-prev` first, which is invalid when the name is over 27 characters (herdr allows 32, `^[a-z][a-z0-9_-]{0,31}$`), so every `squad-board-dev-<scope>-N` respawn fails. Rename it to `prev-$$` instead (always fits, unique per running respawn) and rename it back to `$name` by the same variable if the spawn fails; update the `--dry-run` output. No other change to the respawn flow.
5. The usage text and the header comments of the three scripts describe the label.

## Technical AC
1. Spawn: with the FAKE_HERDR of `test_squad_spawn.py`, `--title "plan"` on `tech-lead` gives `tab create ... --label 🤖 Tech Lead · plan --no-focus` and the env still carries the unchanged address name; manager gives `🦀 Manager`; no title gives no ` · `; a second live `dev` in the same scope renames the first tab to `🤖 Dev 1` and opens `🤖 Dev 2`; the label never contains the squad or scope name. `--home` equals the agent's own home for a scope agent, a goal Manager (`--goal G`: entry under `<squad>/goals/G/labels/`) and the legacy layout (`$SQUAD_DIR/labels/`), even when the test's caller env has a different `SCOPE_DIR`; `--dry-run` writes no `labels/` file; a test in `tests/test_squad_label.py` proves `--init --dry-run` prints the same label as `--init`, leaves the store without the entry, and makes no `herdr tab rename`. The `--label` argument is passed as one argument (a title with spaces, quotes or `$(...)` is data).
2. Respawn: after a spawn with a title, `squad-respawn` creates a tab with the same label (title and number kept); a Manager respawn gives `🦀 Manager`; an agent with no stored entry respawns as before plus a label without title; works in the per-scope layout and the legacy flat layout (both are in `test_squad_respawn.py`).
3. Board start: a new tab is labelled `📋 Board`; an existing `📋 Board` tab is reused and printed (no `tab create`); an existing `board` tab is reused, renamed once, no second tab; two labels present (`board` and `📋 Board`) reuse the new one; `--restart` closes the matching tab.
4c. **A refused spawn changes nothing** (QA blackbox F1, BA-confirmed, story 6): in `squad-spawn` the "an agent named X is already live" check runs **before** `squad-label --init` (outside `--dry-run`, which still writes nothing and does not refuse), so a refused spawn leaves the live agent's stored title and number untouched and renumbers no peer tab. Test: spawn with `--title plan`, spawn the same name with `--title OTHER` (refused, exit 1) and with no title (refused): the entry still has `plan`, no `herdr tab rename` was logged for the refused call, and `squad-respawn` then gives `... · plan`.
4b. Respawn with a 32-character agent name works: the fake herdr log shows the old agent renamed to a name that matches the herdr rule (at most 32 characters), then the spawn, then the old pane closed; a failing spawn renames the old agent back to its real name; existing assertions on `-prev` are updated deliberately.
4. `squad-label --init` failing (exit 1 from a stub) still starts the agent with the address name as label and a warning.
5. All existing assertions about the old `--label <name>` are updated deliberately (they change because the behaviour changes); no other behaviour of the three scripts changes (diff reviewed for that).
6. **No live spawn spam:** unit tests stub herdr. A live check is allowed only in the throwaway workspace `squad-tabs-test` (created for the check, closed after) and spawns at most one real agent (`token-coach`, no worktree) plus a `squad-board-start`; save the `herdr tab list` output in `evidence/TAB-02/`.
7. Targeted tests pass; full suite once on the final sha (`process.md` → Safety).

## Notes
- Do not change what `squad-spawn` does for names, env, worktrees or `herdr agent start`.
- `squad-start` needs no change here: it calls `squad-spawn`, so the Manager gets `🦀 Manager` through it (TAB-03 edits `squad-start` for the workspace only).
