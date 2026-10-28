# Dev notes (plugin-dev-squad-close-1)
- 01: PASS both QAs at 3ffabe7 (bin/squad-close keeps Manager on scope/goal; pin protected).
- 02: handed in at 6ebcfbd to QAW+QAB; waiting on PASS/FAIL. On FAIL: fix, re-verify, same branch.
- Extra files 02 touched (test-forced): skills/squad-process-update/changelog.md (v7 retargeted), history/process-v6.md re-copy, process/starting.md.
- Run process tests from tests/ (rulesview import). Use `rtk proxy bin/squad-process lint` (rtk garbles output).
- After both PASS on 02: `squad-evidence` is Manager's at M? EVID-2d: add review files from $SCOPE_DIR/evidence/<task>/ per ticket, `squad-evidence check`, commit, HANDIN evidence sha to Manager. REV-14c diff check for later commits.
- Do not forget the double "kept" pin line (known, accepted).
- RETIRED: 01 and 02 PASS both QAs (02 at 6ebcfbd). Evidence committed edf5d87, HANDIN sent to Manager. Nothing open. Later commits need REV-14c diff check. 2 suite files fail on base 5adfc45 (QAW raised with Manager).
