## Behaviour

`squad-review-pack NN [--sha S] [--base REF] [--scope DIR] [--max-lines N]` (new `bin/squad-review-pack` + `bin/squadreviewpack.py`). Writes only `$SCOPE_DIR/evidence/NN/pack.md` and `pack-blackbox.md`, after both texts are built. Reuses `squadtickets.scope_tasks` (committed tickets); a draft in `$SCOPE_DIR/tasks/` is the fallback (a `*notes*` file is skipped). Blackbox pack: Business AC, commands that start `squad-`, evidence path; no diff. Output has no timestamps.

## AC trace

| AC | Test | How run |
|---|---|---|
| AC1 pack sections | `test_pack_has_every_section_and_writes_only_two_files` | `cd tests && PYTHONPATH=. python3 -m unittest test_squad_review_pack` |
| AC2 blind pack, T4 | `test_blackbox_pack_is_blind` (markers in Technical AC and diff, changed path, no diff lines) | same |
| AC3, T1, T2 errors, only two files | `test_errors_exit_2_and_leave_nothing` (missing ticket, `../x`, `1/../..`, `-x`, unknown sha/base, no scope) and file-list check in the first test | same |
| T3 cap, T7 deterministic | `test_hunk_cap_note_and_deterministic` | same |
| T5 fallback | `test_draft_in_scope_tasks_is_the_fallback` (with a `07-design-notes.md` next to it) | same |
| T6 real sample | tickets 01, 04, 07 copied from `$SCOPE_DIR/tasks` to a mktemp scope: AC and commands sane; 07 has Technical AC, `test_ticket_without_technical_ac` covers "(none yet)". Found and fixed: `NN-design-notes.md` sorts before the ticket | manual |
| T8 | with `test_squad_merge_check test_no_bare_bash test_hooks_json` | 24 tests OK |

Also in this commit: `squad-merge-check` fails closed when `merge-base` fails (QAW follow-up of 04, commit 8e58856, `test_no_merge_base_refuses`).
