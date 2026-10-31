# Running the tests on Windows

Needs Git for Windows (its `bash.exe`) and Python 3 on PATH.

## Commands

One file (always works): `cd tests && python -m unittest -q <test_file_stem>`

For per-file `python -m unittest` runs set `PYTHONDONTWRITEBYTECODE=1`, else `bin/__pycache__` fails `test_squadinbox.test_no_pyc` (`run_suite.py` sets it for you).

Whole suite, one subprocess per file, in parallel, same as Linux (the browser lock is a file in the temp folder, taken with `msvcrt`):

```
python tests/run_suite.py --receipt <dir> --if-changed <task base>
```

Without the runner: `cd tests && python -m unittest discover -p "test_*.py"`.

The `squad-inbox` files, as a short check:

```
cd tests
python -m unittest test_squadinbox test_squadinbox_win test_po_inbox_contract test_po_inbox_mod test_squadinbox_answer
```

## Launching scripts from a test

Never `subprocess.run([".../bin/squad-spawn", ...])` or `["bash", script]` in a test. Windows cannot exec an extensionless script, and a bare `bash` is `C:\Windows\System32\bash.exe` (the WSL launcher). Use `tests/winlaunch.py`:

```
import winlaunch
r = winlaunch.run_script(SCRIPT, ["arg"], env=env, capture_output=True, text=True)   # one runner; utf8=True gives POSIX UTF-8 bytes argv/env; winlaunch.command is its argv
```

On Linux it runs `[path, *args]` with env untouched (bytes stay bytes). On Windows it reads the shebang (a binary, a bare name or a file without `#!` is passed through unchanged, so a bare `bash` is not caught here): `bash`/`sh` become Git's bash by absolute path (`squadio.pick_bash`), `python`/`python3` become `sys.executable`; paths become forward-slash `str`. `test_no_bare_bash` fails on a bare `"bash"`/`"sh"` argv in `bin/`, `hooks/`, `tools/` and `tests/`; `TESTS_TO_CONVERT` in that file lists the test files not yet converted (ticket 03b empties it).

Expected: 0 failures for these files. For the whole suite 0 failures holds only after tickets 03b and 03c; until then the files that still fail are the ones that launch `bin/` scripts directly (`WinError 193`) or hit the causes below. Tests that cannot work on Windows are skipped with a reason (`python -m unittest -v` prints it). A failure outside the causes below is not a skip: report it, it may be a product bug.

## What is skipped on Windows, and why

| Test | Cause |
|---|---|
| `test_squadinbox` `test_symlink_refused`, `test_squadinbox_answer` `test_unwritable_cases_warn_and_record` (symlink case) | creating a symlink needs a privilege (`WinError 1314`); skipped only when `os.symlink` fails |
| `test_squadinbox` `test_stdin_never_hangs`, `test_squadinbox_answer` `test_never_hangs` (the `pty` part only) | `pty` needs `termios`, which Windows lacks; skipped when `import pty` fails |
| `test_mode_kept`, `test_no_temp_left_and_mode_kept` (the mode assertion only) | Windows file modes differ from POSIX (`438 != 416`) |
| `test_unwritable_home_is_one_clean_line` | `os.geteuid` and directory modes do not exist on Windows |
| `test_concurrent_adds_on_a_barrier` | `os.execv` on Windows returns early instead of replacing the process |
| `test_squadinbox_win` `NoFcntl` (3 tests) | they fake Windows on top of a real `fcntl`; they keep running on Linux |
| `test_po_inbox_contract` `test_fixture_files_are_the_cli_output_byte_for_byte` | the fixtures hold POSIX `/tmp/home` paths; a Windows temp home is `C:\...` |

`test_po_inbox_mod` skips itself when `claude` is not installed.

On Linux nothing is skipped by these changes.
