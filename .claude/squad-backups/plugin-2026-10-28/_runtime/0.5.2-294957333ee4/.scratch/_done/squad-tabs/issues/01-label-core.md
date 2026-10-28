Status: ready-for-agent
Task ID: TAB-01
Blocked by: none
Files touched: new `bin/squadlabel.py`, new `bin/squad-label`, new `tests/test_squadlabel.py`, new `tests/test_squad_label.py`
Serves: spec stories 1 (shape, cut, numbers), 3, 4 (relabel, blank clears, who may relabel)

# TAB-01: label builder, label store and `squad-label`

**Done when the label rule exists in exactly one place (`bin/squadlabel.py`), every agent's label inputs are stored as a file, and `squad-label` relabels a tab from them.** Nothing else in the repo is changed here; TAB-02 and TAB-04 build on this contract.

Read first: `.scratch/squad-tabs/decisions.md` D1-D4, spec stories 1, 3, 4 and B1-B3, `bin/squad-respawn` (how it finds the home folder), `tests/test_squad_respawn.py` (the FAKE_HERDR pattern).

## Contract (binding for TAB-02 and TAB-04)
- **Store:** one file per agent, `<home>/labels/<agent>.json` = `{"role": "dev", "number": 2 | null, "title": "TAB-02 tab labels"}`. `<home>` = `$SCOPE_DIR`, else `$GOAL_DIR`, else `$SQUAD_DIR` (the rule `squad-respawn` already uses). The label itself is never stored; it is built from these three fields, so a rule change cannot leave stale labels. One file per agent means no lock: only the agent itself or the Manager writes it. Write with a temp file and `os.replace`. The agent name is checked against `^[a-z][a-z0-9_-]{0,31}$` before it becomes a file name.
- **`bin/squadlabel.py`** (importable: a plain module next to the scripts; scripts add their own `bin` dir to `sys.path`). Pure functions, stdlib only:
  - `ROLE_NAMES` (B1): manager `Manager`, ba `BA`, team-lead `Team Lead`, tech-lead `Tech Lead`, qa-whitebox `QA Whitebox`, qa-blackbox `QA Blackbox`, dev `Dev`, designer `Designer`, token-coach `Token Coach`. Unknown role: title-case the role id.
  - `build_label(role, number=None, title="")` -> `<emoji> <Role>[ n][ · <title>]`; emoji `🦀` for manager, `🤖` otherwise; no trailing space or ` · ` when the title is blank; title is stripped, control characters removed, runs of whitespace (newlines too) collapsed to one space; the whole label is cut to 32 characters (code points, emoji = 1) as 31 + `…`; a label of 32 or less is untouched (D3).
  - `BOARD_LABEL = "📋 Board"`, `LEGACY_BOARD_LABEL = "board"`.
  - `read_entry(home, agent)` -> dict or None (missing or bad JSON gives None, never raises); `write_entry(home, agent, role, number, title)`.
  - `assign_number(home, agent, role, live_names)` (B2, B4): `peers` = stored entries in `<home>/labels/` of the same role whose name is in `live_names`, excluding `agent`. No peers: number None. Otherwise a peer without a number gets the next free number (so the first Dev becomes `Dev 1`), and `agent` gets `max + 1`. If `agent` already has a stored number it keeps it (a respawn). Returns `(number, [(peer, new_number), ...])`. Numbers never move: Dev 1 retiring leaves Dev 2 as it is.
- **CLI `squad-label`** (python3, executable):
  - `squad-label "<text>"`: relabel the caller (`$SQUAD_NAME`, `$SQUAD_ROLE`, home from env). Updates the stored title (blank `""` clears it, B3), then `herdr tab rename <tab_id> <label>`; the tab id comes from `herdr agent get <name>` (`.result.agent.tab_id`). Prints the new label.
  - `squad-label --agent NAME "<text>"`: relabel another agent. Allowed only when `$SQUAD_ROLE` is `manager` or `NAME` is the caller; otherwise exit 2 with `only the Manager may relabel another agent`. The target's entry is looked up in `$SCOPE_DIR`, `$GOAL_DIR`, then each open `$SQUAD_DIR/scopes/*` (not `_done`); no entry or more than one: exit 1 with the reason.
  - `squad-label --init --home DIR --agent NAME --role R [--title T]` (used by `squad-spawn`): **`--home` is required and is the only home used; the env (`SCOPE_DIR`/`GOAL_DIR`) of the calling process is ignored**, because the caller is a Manager spawning an agent of another scope or goal. `squad-spawn` passes its computed `home` (scope dir for a scope agent, goal dir for a goal Manager, `$SQUAD_DIR` in the legacy layout), which is exactly the home the agent itself derives later from its own env (`SCOPE_DIR`, else `GOAL_DIR`, else `SQUAD_DIR`). Runs `assign_number` with the live names from `herdr agent list`, writes the entry, renames the tab of every newly numbered peer (`herdr tab rename`), prints only the new agent's label on stdout. Does not touch herdr for the agent's own tab (it does not exist yet).
  - `squad-label --get-title --home DIR --agent NAME` (used by `squad-respawn`): prints the stored title, empty and exit 0 when there is no entry. Same explicit-home rule.
  - Outside herdr (`HERDR_ENV` != 1): the store is updated, the tab rename is skipped, exit 0.
  - A herdr call that fails after the store was written: warn on stderr, exit 0 (the label store is the truth; a stale tab fixes itself on the next relabel).

## Technical AC
1. `build_label`: table test over every role in `ROLE_NAMES` with and without number and title; blank, whitespace-only and multi-line titles; exactly 32 characters untouched, 33 cut to 31 + `…`; the spec's example `🤖 QA Blackbox · TAB-05 integration live check` -> `🤖 QA Blackbox · TAB-05 integrat…`; an emoji counts as 1.
2. `assign_number`: no peer -> None; one live peer -> peer 1 and new 2; three agents -> 1, 2, 3; peer 1 not in `live_names` -> new agent gets None when no live peer remains, and `max+1` when Dev 2 is still live; respawn of Dev 2 keeps 2; a retired peer's stored file is never rewritten.
3. Store: round trip; bad JSON and missing file give None; a name that fails the regex (`../x`, `A b`) is refused before any path is built; no `.tmp` file is left behind; two homes do not see each other's files.
4. CLI with a fake `herdr` on PATH (log of calls): self relabel renames the right tab id; blank text clears the title and the label has no ` · `; `--agent` by a non-Manager targeting someone else exits 2 and writes nothing; `--agent` by the Manager finds an entry in a scope home from a goal Manager env (`GOAL_DIR` set, `SCOPE_DIR` unset); `--init` renames a newly numbered peer and prints only the new label; `--init --home <goal dir>` run with a different `SCOPE_DIR` in the env writes the entry under the goal dir only (and a goal Manager with only `GOAL_DIR` then self-relabels and keeps its number); `--init` without `--home` exits 2; `--get-title` prints the stored title and empty for no entry; `HERDR_ENV` unset updates the store and calls no herdr; a failing `herdr tab rename` exits 0 with a warning.
5. Unit tests stub herdr. **No live herdr is needed for this ticket.** A short live check is allowed only in a throwaway workspace named `squad-tabs-test` (`herdr workspace create --label squad-tabs-test`, closed at the end): `herdr tab create`, then `squad-label --init` and a rename on a plain shell tab, with the real `herdr agent list` shape saved in `evidence/TAB-01/` (the fake's shape must match it).
6. Security: titles are untrusted text from other agents; nothing is passed to a shell (list args to `subprocess`), and the title is only ever data.
7. `python3 -m unittest tests.test_squadlabel tests.test_squad_label` passes; the full suite once on the final sha (`process.md` → Safety).

## Notes
- Python, like `bin/squad-usage` and `bin/squad-start`. Follow their style (docstring with usage at the top).
- Do not edit `squad-spawn`, `squad-respawn`, `squad-board-start` (TAB-02) or the board (TAB-04).
