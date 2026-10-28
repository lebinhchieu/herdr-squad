# plugin-dev-dsz-11 notes (ticket 11)
- DONE: both QAs PASS at ca53ba7 (evidence d8b4738), Tech accepted; TL told. Retired, no respawn.
- Result: all 512 Dev combos <= 5120 B (worst 5117); EXCEPTIONS/CAP deleted; REV-5a/EVID-5 empty `roles:` (on demand; lint allows empty value, missing line errors); LC-19b cites [EVID-5]; REV-22a keeps the "diff conforms" clause; START-10 drops `git status` (Tech OK); v9 changelog row for every changed rule ID.
- Untouched: safety.md (ticket 14), compose header.
- If 14 merges before 11: `git merge` inside branch (no rebase), re-run test_sizes changelog test.
- Evidence: .scratch/drop-scope-size/issues/11-dev-cap-sweep-and-trim/evidence.md; LC-25 note in tasks/11-worst-set-breakdown.md.
