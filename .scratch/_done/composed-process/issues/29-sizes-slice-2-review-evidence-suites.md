Status: ready-for-agent
Type: task
Task ID: 29
Touches: `templates/squad/process/starting.md` (START-6, START-10 wording), `templates/squad/process/cost.md` (COST-5 only), `templates/squad/process/messages.md` (MSG-11a only) (added 2026-10-22), `tests/test_instructions.py`, `tests/test_dev_rules_size.py`, `tests/fixtures/qab/golden.json` (regenerated), slice-2 classes of `tests/test_sizes.py` (added 2026-10-22), `templates/squad/process/{review,evidence,suites,promotion,lifecycle}.md`, `CLAUDE.md` (Running tests: the size's suite owner), the tests that pin them (`test_pod_contact_routes`, `test_suite_rules_process`, `test_qab_optional`, `test_retro_rules`, `test_process_conversion`, `test_team_lead_role`)
Does not touch: sizes/who/starting/spawning (17); cost/messages/files/iterations/notes/goal/closing/safety, `bin/*` (30); whole-template tests, changelog (31)
Harness: `squad-process lint`; `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest <each edited test file> test_sizes`
Blocked by: 17, 18 (base must contain passed 18: `lifecycle.md` is shared)

# 29: New sizes, slice 2: review, evidence, suites, promotion, lifecycle

**Done when every rule in these five files and CLAUDE.md Running tests names an owner present at its size, per `tasks/tech-ac.md` decisions 1-5.**

Spec: PO decisions D9-D14 in ticket 17; owner table = `scopes/sizes-and-models/tasks/tech-ac.md` decision 3. Never renumber: re-point `X-na`/`X-nb`, add a new letter for the actor that took the duty, `[ID]` pointers instead of repeated sentences (duplication lint), no `(S:` clauses.

## Technical AC
1. Hand-in goes to the Manager at S; to the QAs at M and L; "Done" tells the Manager (S, M) or the Team Lead (L). Code check: S = Developer's checks + one fresh-context Opus review subagent (`evidence.md` `## Review`), Manager confirms both exist; M, L = QA whitebox.
2. Suite owner: S Developer, M QA whitebox, L Tech Lead, once on the final sha. `CLAUDE.md` Running tests names it; a test greps it (17/29/30/31 AC6).
3. `promote.md`: S Developer, M QA whitebox, L Tech Lead.
4. `qa-b: no` keeps its meaning at M and L (decision 5); REV-19..21 re-pointed (no BA/Team Lead/Tech Lead at M).
5. No rule here has `when` matching S or M and acting on tech-lead, team-lead or ba, except move-up rules (list the IDs).
6. Pinned tests edited in the same commit; `squad-process lint` clean; `test_windows_safe` passes.
7. Every ID listed for 29 in `tech-ac.md` "Follow-up rule IDs" is retargeted or reasoned; the true orphans among them are fixed. The test lists any `who`-orphan left in these five files.
8. S Developer review duty: a rule in `review.md` says: before HANDIN, one fresh-context Opus review subagent reads the diff; findings and fixes go in `evidence.md` `## Review`; the Manager confirms by eye that `## Review` exists (no `squad-evidence` change; amended 2026-10-22). It reaches `composed("dev","S")` and not M or L (test); dev rules stay ≤ 5120 B.
9. REV-21 (`size in M, L and qa-b = no`) acts on BA, absent at M, and contradicts SIZE-5c: at M with `qa-b: no` QA whitebox checks `## Behaviour` (no BA); split by size (new letter for M), L keeps the BA wording. Test: `who REV-21` at M names no BA.

2026-10-22 ticket 32: the review subagent runs on Sonnet at high effort; AC 8 wording is superseded.
