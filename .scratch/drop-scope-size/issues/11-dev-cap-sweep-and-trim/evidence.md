# Evidence: 11 Developer 5 KiB sweep and trim
sha: pending

## Behaviour
- Sweep: 128 team sets x goal x qa (full, light), `dev` composed from a `team:` home (live-length names, no scaffold). Base 90be196: worst 5674 B, 140 of 256 (set x goal) over 5120. Now: worst 5423 B (<= 5443); 32 team sets over 5120, all with designer or architect and at most one QA, pinned by set in `EXCEPTIONS` (`tests/test_dev_rules_size.py`); the test asserts the over-5120 sets equal that table exactly, so it cannot grow or silently shrink. The old stale PINNED size table is deleted.
- Trims (IDs kept, bodies changed -> changelog v9 `changed:`): REV-5a and EVID-5 now act for the Manager and are cited from REV-22 / LC-19 (`squad-process rule REV-5a|EVID-5` reaches them; test added to the lost-rules list and a citation test); wording only: CORE-2, CORE-3 (no `size` word), MSG-4a, MSG-4b, MSG-11b, COST-5a, REV-22a, EVID-2b.
- Un-skipped: `test_dev_rules_size` x3 (replaced by `test_every_team_set_fits_5_kib_or_is_a_pinned_exception` and `test_pinned_exceptions_all_carry_designer_or_architect_and_at_most_one_qa`) and `test_sizes.test_dev_rules_stay_within_5_kib`. `grep -rn "ticket 11" tests/*.py` returns nothing.
- Blocker for "all sets <= 5120" (no exceptions): the remaining bytes are in rules outside this ticket: `safety.md` (ticket 14), the fixed header/`rules:` line in `squadcompose.py`, and text pinned by other tests (LC-19c, REV-14a, REV-22a acts). Needs Tech/TL ruling; the AC's pinned-exceptions branch (<= 5443) is what is met.
- Lint baseline (G2b): `squad-process lint` on 90be196 empty, exit 0; branch empty, exit 0.
- Tests green (touched/grep hits): dev_rules_size, sizes, architect_handoff, instructions, manager_m_l, pod_contact_routes, pod_rules_process, squadruntime, team_lead_role, advisor_rules, windows_safe, crlf_squad_files.
