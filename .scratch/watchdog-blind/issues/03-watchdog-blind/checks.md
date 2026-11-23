| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | test_squad_watchdog manager tests, Ran 104 OK | cd tests; python3 -m unittest -q test_squad_watchdog test_squad_log_message test_squad_start test_squad_spawn test_squadtask test_windows_safe test_utf8_helpers test_instructions (5773a20, detached worktree) -> Ran 347 OK; read decide() diff: team_working excludes role manager and its bg_busy; working kept for all_blocked/stop | |
| AC2 | test_squad_watchdog blind tests | same run; read tick() blind branch and decide() blind_logged flag | |
| AC3 | test_squad_watchdog wsl test | same run; ls -l /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe exists; read suspend_cmd/suspend diff | |
| AC4 | git diff ADR 0028 + docstring | git diff da9c43a 5773a20 -- docs/adr/0028-watchdog-follows-goals-file.md bin/squad-watchdog (docstring) | |
| AC5 | grep 0.10.8 in plugin.json, tests: none | grep -rn 0\.10\.8 .claude-plugin tests -> none (only changelog history and .scratch hit) | |
