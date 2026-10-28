# plugin-dev-dsz-int3 notes
- INT3 done at 90be196 (07 @0067a5d + 08 @e08bb66 onto fed0c95); both QAs and Tech passed. Branch squad/plugin/drop-scope-size/plugin-dev-dsz-int3.
- Evidence: .scratch/drop-scope-size/issues/INT3-integration/evidence.md. QA review files not assembled (Tech: no more commits).
- Gotchas: run tests from tests/ dir (rulesview import). make_plugin() in test_squadruntime adds REV-14a/REV-19b stubs; don't put them in the shared compose fixture (breaks goldens).
- Forward note (qa-w.md): ticket 11 should un-skip the 4 "5 KiB trim" tests and re-pin PINNED in test_dev_rules_size.
