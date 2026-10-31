# Evidence: 03 Windows launch helper for the tests

## Behaviour

03a, Windows 11, Git Bash, Python 3.14 (Linux not run here; Tech Lead's Debian run covers it).

- `cd tests && python -m unittest -q test_winlaunch test_no_bare_bash`: 14 tests OK (nt: shebang bash/sh -> Git bash by absolute path, never System32; python -> sys.executable; POSIX argv/env identity; real script run).
- `test_squad_spawn.SpawnRuntimePathEnvTest` (now through `winlaunch.run_script`, hand-rolled Git bash lookup removed): 3 OK.
- `test_run_suite`: 23/24 OK; the 1 failure runs `test_squad_usage`, an unconverted script launch (WinError 193, ticket 03b). run_suite imports on Windows; lock via msvcrt, temp-folder path on nt; Linux keeps fcntl and /tmp/squad-suite.lock.
- Guard: `test_no_bare_bash` now scans `tests/` for argv lists starting with bare "bash"/"sh"; `TESTS_TO_CONVERT` (5 files) is a ratchet 03b empties; planted-line tests prove it fails.
- `bin/squad-process lint` exit 0.
