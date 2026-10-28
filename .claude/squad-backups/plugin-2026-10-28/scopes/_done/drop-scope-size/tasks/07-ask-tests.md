# 07 ASK: size-keyed tests outside my file list (Developer plugin-dev-dsz-07)

State: lifecycle.md, review.md, evidence.md retargeted to team keys (lint clean, branch has int1 merged). The 7-shape role-by-rule comparison old vs new matches except the intended moves (LC-7a/7c, LC-20, REV-14, REV-19, noqab-only losses).

Old size-keyed tests now fail because a `size:` home composed by the CLI has no team facts, so new-key rules match every role (missing = true):
- tests/test_dev_rules_size.py (dev 5 KiB sweep at S/M/L: 7 KB; owner task 09, rewritten over 128 sets)
- tests/test_sizes.py (size lines of `who`, absent-role sweeps, changelog check)
- tests/test_qab_optional.py, test_architect_handoff.py, test_pod_contact_routes.py, test_manager_m_l.py, test_instructions.py, test_process_conversion.py (size shapes via `who`/`composed(size)`)

QUESTION: do I (a) rewrite only my 4 listed test files plus add tests/test_rules_lifecycle_review_evidence.py (new, team language, 128-set text check, 7-shape golden) and leave the other 8 files red for 09/10, or (b) also edit the stale assertions in those 8 files? Default if no answer: (a), and I list each red test with its reason in evidence.md.
