Status: needs-triage

# 09 test_ca_win: guard and finder tests assume POSIX/WSL on native Windows

Cause: `tests/test_ca_win.py` is written for a WSL host driving `pwsh.exe`. On native Windows (Git Bash, Python 3.14): `unsafe_home` compares against `/mnt`, `/` and the real `~`, and the temp dir is always under `C:\Users\<me>`, so `GuardTest.test_accepts_a_wsl_temp_dir` and `WindowsPortTest.setUpClass` refuse ("the real home or under it"); `FinderTest.test_finds_pwsh_on_path_before_the_alias` writes an extensionless `pwsh` that `shutil.which` ignores on nt; `test_refuses_empty_mnt_and_the_real_home` expects `"/"` refused (realpath gives `C:\`).
Fix direction: on nt, refuse only `~\.claude-accounts` / `~\.claude` (USERPROFILE is redirected in the run), build the fake pwsh as `pwsh.exe`/`.cmd`; keep the WSL branch unchanged. 3 failures + 1 setUpClass error today (`python -m unittest test_ca_win` from tests/).

## Comments
