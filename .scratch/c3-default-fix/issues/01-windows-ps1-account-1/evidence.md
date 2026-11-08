## Behaviour
Default account 1 now clears an inherited `CLAUDE_CONFIG_DIR` when the profile loads (`claude-accounts.ps1`, startup switch case `'1'`). It is silent if the variable is unset and never sets `~/.claude`.

Test `ps.startup_default_1_clears_an_inherited_config_dir` (ca_win_cases.ps1, run by `test_ca_win`):
- base sha 213652c: FAILED (`got ...\.claude-3 want $null`)
- fix: `test_ca_win` OK, 9 tests. `test_ca_install` skipped on Windows (nt skip, all 22).
Other copies of the block: none. `Get-ClaudeDefaultAccount` is used only in `claude-accounts.ps1`; `install.sh` byte-copies it.
