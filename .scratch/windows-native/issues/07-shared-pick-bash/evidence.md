# Evidence: 07 One `pick_bash` for every bash launch

## Behaviour

Move: `pick_bash` and `need_bash` went from `bin/squad-start` to `bin/squadio.py` unchanged, except `need_bash` prints the same message to stderr and `sys.exit(1)` where it called `die` (same output and exit code). `squad-start` does `from squadio import need_bash, pick_bash`, so `mod.pick_bash` in the existing tests still resolves; `import ntpath/posixpath` dropped from `squad-start`.

Guard: new `tests/test_no_bare_bash.py` (AST scan of `*.py` and python-shebang scripts under `bin/ hooks/ tools/`: `subprocess.run/Popen/call/check_call/check_output` with an argv list/tuple starting with `"bash"` or `"sh"`). Three tests: scanner flags planted bad lines, scanner passes `need_bash()`/`git`, tree is clean (green now).

Windows runs (`cd tests && python -m unittest ...`): `test_no_bare_bash`, `test_squad_start.PickBashTest` (5, untouched), `test_squadio`, `test_windows_safe`: 23 OK. `test_squad_start` whole file: 42 errors before and after the move (same count, launch problem, ticket 03). Linux run: Tech Lead.
