## Behaviour
The stub `pgrep` prints a line with one 0x90 byte. Test: `test_ca_autoswitch.AutoswitchTest.test_bad_byte_in_child_output_is_replaced_not_a_traceback` (run in WSL Debian, the tests need Linux).

- Base: `autoswitch: error: 'utf-8' codec can't decode byte 0x90 in position 0: invalid start byte`; test FAILED.
- Fixed: the byte becomes U+FFFD, no traceback, stdout has `ok: w1 -> c1 5h 50% 7d 20%` as with clean output; test OK.
- `test_ca_autoswitch`: 51 tests OK. `test_ca_launchers`+`test_ca_install`: 1 failure, `test_gitignore_names_the_state_files` (`git check-ignore` exit 128 inside WSL on a /mnt/c worktree; not related to the change).

## Review
(QA files in the scope evidence folder.)
