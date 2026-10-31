# Evidence: 01 `PATH=` env sent to `herdr tab create` is mangled on Windows

## Behaviour

`bin/squad-spawn:199-200` (main, PO diff, unchanged): `rt_posix=$(cygpath -u "$runtime" 2>/dev/null || printf '%s' "$runtime")`, `--env "PATH=$rt_posix/bin:$PATH"`.

New `SpawnRuntimePathEnvTest` in `tests/test_squad_spawn.py`: runs a copy of `bin/` (stub `squad-process` returns the runtime) with a shim `herdr` that logs the `tab create` argv and the caller PATH.

- Windows-form runtime `C:\Users\me\sq\_runtime\0.6.3-aaaaaaaaaaaa` + fake `cygpath` -> `PATH=/c/Users/me/sq/_runtime/0.6.3-aaaaaaaaaaaa/bin:<caller PATH>`, no drive-letter segment.
- POSIX runtime, real or no `cygpath` -> unchanged.
- `cygpath` exits 1 -> unchanged.
- Mutation check: with `rt_posix=$runtime` the Windows-form test fails.
- `grep -n 'PATH=' bin hooks tools`: only this line. `squad-respawn` calls `squad-spawn` (line 83), no PATH of its own. Other `--env` values are single paths.

Run: `cd tests && python -m unittest test_squad_spawn.SpawnRuntimePathEnvTest` (3 OK on Windows). No Linux run here (Tech Lead runs Debian WSL). Live Windows herdr check: Manager/PO.
