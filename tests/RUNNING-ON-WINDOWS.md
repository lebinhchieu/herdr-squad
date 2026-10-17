# Running the tests on Windows

`tests/run_suite.py` imports `fcntl`, which Windows does not have, so it cannot run there. Run the `squad-inbox` test files with `unittest` instead:

```
cd tests
python -m unittest test_squadinbox test_squadinbox_win test_po_inbox_contract test_po_inbox_mod test_squadinbox_answer
```

Expected: 0 failures. Tests that cannot work on Windows are skipped with a reason (`python -m unittest -v` prints it). A failure outside the causes below is not a skip: report it, it may be a product bug.

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
