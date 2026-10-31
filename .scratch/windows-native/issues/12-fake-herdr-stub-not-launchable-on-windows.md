Status: needs-triage

# 12 Tests' fake `herdr` is an extensionless bash script: nothing but bash can launch it on Windows

Cause: tests put a bash script named `herdr` first on PATH (or in `HERDR_BIN_PATH`). Python products (`squad-label`, `squad-notify`) call `subprocess.run(["herdr", ...])`. `CreateProcess` finds only `herdr.exe` and cannot run an extensionless script (`WinError 193`, or "not found"), so the stub is never called.
Seen (Windows, per-file `python -m unittest`, `PYTHONDONTWRITEBYTECODE=1`):
- `test_squad_label`: 6 failures (`test_blank_clears_title`, `test_goal_manager_finds_entry_in_a_scope_home`, `test_init_dry_run_prints_the_label_...`, `test_init_first_agent_has_no_number_and_no_tab_call`, `test_init_renames_newly_numbered_peer_...`, `test_self_relabel_renames_its_tab_...`): `calls()` is empty.
- `test_utf8_helpers` `LabelAndSpawnTest.test_label_reads_a_herdr_reply_with_emoji_on_the_calls_it_makes` (label `Dev`, not `Dev 2`: the peer list is empty).
- `test_utf8_helpers` `NotifyTest.test_a_missing_proc_...`: nt skip with this cause (`WinError 193`).
- `test_squad_start` `WorkspaceRenameTest` (5 tests) has the same cause: `calls()` is empty because the stub is never launched. Listed in ticket 13, group D.
Fix direction: the stub as a Python launcher `herdr.exe`/`herdr.cmd` the product can find (one shared helper in `tests/winlaunch.py` or `ca_stubs.py`), or the product resolves `herdr` with `shutil.which` (PATHEXT) and the stub is `herdr.cmd`. Related: ticket 05.

## Comments
