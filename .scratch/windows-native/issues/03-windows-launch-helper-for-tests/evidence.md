# Evidence: 03 Windows launch helper for the tests

## Behaviour

03a, Windows 11, Git Bash, Python 3.14 (Linux not run here; Tech Lead's Debian run covers it).

- `cd tests && python -m unittest -q test_winlaunch test_no_bare_bash`: 14 tests OK, also with SystemRoot empty as on Linux; nt tests pass system_root explicitly (nt: shebang bash/sh -> Git bash by absolute path, never System32; python -> sys.executable; POSIX argv/env identity; real script run).
- `test_squad_spawn.SpawnRuntimePathEnvTest` (now through `winlaunch.run_script`, hand-rolled Git bash lookup removed): 3 OK.
- `test_run_suite`: 23/24 OK; the 1 failure runs `test_squad_usage`, an unconverted script launch (WinError 193, ticket 03b). run_suite imports on Windows; lock via msvcrt, temp-folder path on nt; Linux keeps fcntl and /tmp/squad-suite.lock.
- Guard: `test_no_bare_bash` now scans `tests/` for argv lists starting with bare "bash"/"sh"; `TESTS_TO_CONVERT` (5 files) is a ratchet 03b empties; planted-line tests prove it fails.
- `bin/squad-process lint` exit 0.

- Return 1 (QA-w FAIL, run_suite.py print on a cp1252 pipe): `run_suite.main()` now calls `squadio.utf8_stdio()`. New test `test_a_redirected_stdout_in_a_legacy_codepage_still_gets_the_summary_and_the_receipt` (stdout to a file, PYTHONIOENCODING=cp1252, U+FFFD in the summary): passes; with the call commented out it fails with UnicodeEncodeError. `Expected: 0 failures` in RUNNING-ON-WINDOWS.md now says whole-suite zero holds after 03b/03c.

## 03b-1 conversion

03b-1 (spawn/start/close family), Windows 11, per-file `cd tests && python -m unittest -q <stem>`, before (40d64af) -> after:

| File | before | after |
|---|---|---|
| test_squad_spawn | errors=143 | failures=44-45, errors=2-4 (0 x WinError 193; 2 x WinError 1314 symlink privilege) |
| test_squad_close | errors=82 | failures=4 (0 launch errors) |
| test_squad_start | errors=42 | failures=14 (0 launch/bytes errors) |
| test_utf8_helpers | errors=27 | failures=1, errors=3 (2 x WinError 1314 symlink in JqTest; 1 x WinError 193 inside squad-notify's own herdr launch, in-process, 03c/ticket 05) |
| test_crlf_squad_files | failures=3 | failures=3 (path-form asserts, not launches) |

Remaining failures are no launch errors: backslash vs forward-slash paths in expected output, a `mv` Permission denied, `Dev` label, symlink privilege. They are 03c triage input. Zero `WinError 193` in the four files that launch scripts.

Added to `tests/winlaunch.py`: `bash()`, `python()`, `child_argv()`, `run_child()` (POSIX keeps UTF-8 bytes argv/env, as before; nt str). `test_squad_start.run_child` and `test_utf8_helpers.run` delegate to it. 30+12+1 `subprocess.run([str(x), ...])` sites became `winlaunch.run_script(x, [...])`. `TESTS_TO_CONVERT` lost `test_utf8_helpers.py`. test_winlaunch 18 + guard OK; `bin/squad-process lint` 0. Linux not run here.

## 03b2 (tests converted to winlaunch, commit 6b476d0)

Windows `python -m unittest <stem>` (cd tests), launch errors (WinError 193 / bytes env) before -> after; remaining are non-launch (03c):
- test_squad_log_message E27->0 OK; test_team_lead_perms E26->0 OK; test_squad_usage_hook E10->0 OK; test_squad_retire E3->0 OK; test_squad_manager_guard E1->0 OK; test_old_language_inventory E1->0 OK
- test_team_models E25->F1 (path format in override check); test_squadruntime E30->F2,E1 (symlink privilege WinError 1314, path format); test_squad_respawn E22->F7,E1 (herdr log shows `/` paths vs `\` expected; symlink priv); test_squad_usage E20->E1 (symlink priv); test_squad_label E17->F6 (PATH stub herdr built with `:`); test_squadsettings E10->F5 (path format); test_squad_ledger E10->F1,E1 (symlink of bash, PATH stub)
- test_run_suite F1 unchanged (nested test_squad_usage symlink error; no script launches to convert)
- test_ca_install F17,E1 -> F11,E1 (no launch error left; symlink priv/path); test_ca_autoswitch/launchers: skipped on nt (requires_linux, ADR 0011), bare bash -> ca_stubs.bash_argv
- TESTS_TO_CONVERT: only test_utf8_helpers.py left (03b-1's). test_no_bare_bash, test_winlaunch, test_processlint OK.
- Linux not runnable here; POSIX path of winlaunch is identity ([path,*args], env untouched), no skips added.
- Linux (Debian, Tech Lead run at 6b476d0): 19 owned files incl. test_ca_* and test_run_suite, same counts as 40d64af, all OK.

## 03c triage (Windows, `cd tests && python -m unittest <stem>`)

- Fixed (test bugs): `test_templates` (`relative_to` -> `as_posix`), `test_squad_evidence` orphan regex accepts `\`, `test_squad_path_guard` (ROOT substituted into JSON unescaped), `test_squadinbox_answer.test_stdin_meaning` (stdin+`--note/--text` refusal asserted only off nt: `squadinbox.stdin_text` skips select() on Windows by design).
- nt-only skips, cause named: `test_squad_notify` DeliveryTest/RunTest (ADR 0011, os.openpty, /proc fds), `test_ca_install` InstallTest (install.sh uses ln -s and MSYS paths; ADR 0011), `test_inbox_guide_cmd` symlink test (WinError 1314), `test_squadreport_ui.test_empty_kpis` (needs Chrome like its sibling classes; no-op where Chrome exists).
- Already OK after 03b: `test_old_language_inventory`, `test_po_inbox_mod`, `test_promotion_0_6_0`, `test_windows_safe`.
- New tickets: 09 (`test_ca_win` POSIX/WSL guard), 10 (`winlaunch` import writes `bin/__pycache__`, breaks `test_squadinbox.test_no_pyc` after other tests; Tech Lead owns winlaunch). `squadinbox` D3 known-not-fixed (ADR 0011).
- Linux: no skips added where the condition is Linux (all `os.name == "nt"`; the Chrome skip only where Chrome is missing).

## 03d (Windows, `PYTHONDONTWRITEBYTECODE=1 python -m unittest <stem>` in tests/)

Result per file (pass / skip / ticket). Every skip is `os.name == "nt"` with a cause; Linux code paths are unchanged (expected strings use `Path(..).as_posix()`, which equals `str` on POSIX; `pathsep` is `:` there). Linux not runnable here.
- test_team_models: OK. Fix: the `.overrides` fixture is written as LF bytes (`write_text` made CRLF, respawn refused the value).
- test_squadruntime: OK, 1 skip (symlink WinError 1314) + 1 existing skip. Fix: path asserts via `as_posix`; PATH check on nt matches bash's own `/tmp/..` form.
- test_squad_respawn: OK, 1 skip (symlink WinError 1314). Fix: `as_posix` in the herdr-log asserts.
- test_squad_usage: OK, 1 skip (symlink WinError 1314).
- test_squadsettings: OK (25). Fix: `settings_arg` helper accepts `C:/x` and `/c/x` forms on nt; exact path elsewhere.
- test_squad_ledger: 1 skip (symlink of bash, WinError 1314); 1 failure left, ticket 06 (no `flock`, `test_simultaneous_fails_on_third_sha_give_one_notice`).
- test_run_suite: OK (the nested test_squad_usage now skips).
- test_ca_install: OK, 23 skipped (ADR 0011, from 03c). Nothing left.
- test_squad_label: PATH built with `os.pathsep`; 6 failures left, ticket 12 (fake `herdr` is an extensionless bash script `CreateProcess` cannot run).
- test_utf8_helpers: OK except 1 failure, ticket 12 (`test_label_reads_a_herdr_reply...`); 3 skips (JqTest x2 symlink WinError 1314; NotifyTest herdr stub, ticket 12). Fix: `run()` launches through `winlaunch.run_script` (was `TypeError` on bytes argv, 27 errors), PATH with `os.pathsep`. `TESTS_TO_CONVERT` unchanged. One run of the spawn-simulation test failed once for `team-lead --dry-run` (exit 1) while another ran in parallel; it passed on 2 later runs, not ticketed.
- test_ca_win: 3 failures + 1 setUpClass error, ticket 11 (was 09).
- test_po_inbox_mod, test_squad_report_cli: OK on Windows with `PYTHONDONTWRITEBYTECODE=1`; nothing changed.
- test_no_bare_bash, test_processlint, test_squad_notify, test_squadinbox: OK. `python bin/squad-process lint` exit 0.
- Housekeeping: ticket 09-ca-win... renamed to 11; ticket 10 (pycache) deleted; one line added to RUNNING-ON-WINDOWS.md.
- Failing on Windows without a skip, all with a ticket: test_squad_ledger (06), test_squad_label x6 + test_utf8_helpers x1 (12), test_ca_win x4 (11).
