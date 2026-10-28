# QA whitebox 11 on cb8888a
FAIL (1 finding). Everything else checks out.

## F1 REV-5a and EVID-5 re-roled dev -> manager: the Manager is told to do Developer work (correctness)
- templates/squad/process/review.md:55-57 (REV-5a `roles: dev` -> `manager`), templates/squad/process/evidence.md:~65 (EVID-5 `roles: dev` -> `manager`).
- Composed from cb8888a (qaw script, `compose_team`): Manager with team tech-lead gets "REV-5a Run code that parses another tool's output once, read-only, on live data."; Manager with tech-lead,designer also gets "EVID-5 Save one screenshot per screen and state in `img/`". `squad-process who REV-5a` = `qa-white = no: acts: manager`; `who EVID-5` = `ui-check = manager: acts: manager`. Base 90be196 and 6389642: `acts: dev`. The Developer now gets only a pointer ("[REV-5a]" in REV-22, "shots [EVID-5]" in LC-19), no body.
- Why it matters: the Manager does not write or run the changed code or take the screenshots; the instruction now lands on the wrong role and the Developer duty is only a citation. It changes who acts, which a "wording/trim" ticket (AC 09: "every duty a Developer acts on still present", on-demand reachable by `squad-process rule <ID>`) does not allow. Lesson 07: Manager composition must be compared over every shape.
- Also: LC-19's `[EVID-5]` pointer fires under `design-notes = tech-lead and design = yes` incl. `ui-check = qa-black`, where EVID-5 does not apply.
- What would pass: keep the actor the Developer. Options (Tech Lead to choose): (a) keep `roles: dev` and win the bytes elsewhere / with more wording trims; (b) make the Developer the one who reaches the body on demand without naming the Manager as actor (e.g. an `aware:`-only form if the parser allows it; today attribute order is roles, aware, when, topic, and roles is required), with `who` still showing dev; (c) the Tech Lead rules that the Manager acts and amends AC 09 + `squad-process rule` text so the Manager rule says what the Manager does. Then re-run the 128-team Manager invariant (nothing lost, nothing new for the Manager) and add a test that REV-5a/EVID-5 are not composed for the Manager unless ruled.

## Checked OK
- Tests from `git archive cb8888a`: test_dev_rules_size, test_sizes, test_architect_handoff, test_instructions, test_manager_m_l, test_pod_contact_routes, test_pod_rules_process, test_squadruntime, test_team_lead_role, test_advisor_rules, test_process_conversion, test_suite_rules_process: 225 OK (1 skip, the changelog base-not-in-clone one). test_squadrules 58 OK. Lint exit 0 empty (= baseline).
- `grep -rn "ticket 11" tests/*.py`: no hits; the 4 skips are gone; PINNED deleted.
- AC 09 branch "pinned by team set, <= 5443": CAP 5443, worst 5423 B; the sweep test asserts the over-5120 sets equal EXCEPTIONS (32 sets, all with designer or architect and at most one QA, second test asserts that). Not "no exceptions": Dev's note says remaining bytes sit in safety.md (ticket 14), squadcompose header, text pinned by other tests.
- Changelog v9 `changed:` lists every touched ID (CORE-2, CORE-3, REV-5a, EVID-5, REV-22, LC-19, REV-22a, EVID-2b, MSG-4a, MSG-4b, MSG-11b, COST-5a); wording-only edits keep the duty (CORE-3 drops "size": G4 ok).

# Return 1 verdict on f86b26b (supersedes the cb8888a FAIL above; F1 there is fixed)
FAIL (2 findings; all style/content findings of this sha in this one return).

Fixed since cb8888a: REV-5a and EVID-5 are `roles:` empty (on demand, no actor). Own 128-team x goal x qa sweep (9 roles, 4608 composes per tree, base 90be196 vs 5da365a code): the Manager and every other role gain and lose no rule ID; only the Developer loses REV-5a (256 composes, qa-white = no) and EVID-5 (128), cited from REV-22 / LC-19 / LC-19b (f86b26b adds the LC-19b pointer, new test). Dev worst 5110 B, none > 5120 (AC 24 / 09 met, EXCEPTIONS/CAP gone). Tests (from git archive f86b26b): 286 OK (1 skip), lint exit 0, `grep "ticket 11" tests/` none.

## F1 changelog v9 misses four changed rules (G5)
- IDs whose title or body differs from the scope base 6389642 and have no `- ID:` line in v9 (`skills/squad-process-update/changelog.md`, lines 1-135): LC-18 ("Developer work" -> "Dev work", body merges "test new behaviour" into the implement bullet), MSG-3 (drops "Name it after the type;"), START-6 (goal-line wording), START-10 ("Developer start" -> "Dev start", the 3-step list becomes one sentence, drops the `git status` step). Why it matters: G5 / ticket AC: "changelog v9 lists every changed ID with a reason (>10 chars)".
- What passes: add `- LC-18: ...`, `- MSG-3: ...`, `- START-6: ...`, `- START-10: ...` lines to v9 `changed:` with a reason each (wording only, same duty). Script to recheck: parse `## ID` blocks base vs branch under templates/squad/process and compare to v9 lines.

## F2 REV-22a lost the instruction to check conformance (duty weakened)
- templates/squad/process/review.md (REV-22a): base "Give the review subagent architecture.md too: it checks that the diff conforms to it." (d2e8d06/f86b26b) "Also give the review subagent `$SCOPE_DIR/architecture.md`." The subagent is handed the file but never told to check the diff against it; SIZE-23d / the technical AC need the check. Changelog says "same duty".
- What passes: restore the clause in few bytes, e.g. "Also give the review subagent `$SCOPE_DIR/architecture.md` to check the diff against." Headroom: worst Dev set is 5110 B, so re-measure (<= 5120 for all 512) and keep the sweep test green.

## Re-check on final ca53ba7 (Tech DECISION 11) — PASS
- F1: all 207 rules changed since base 6389642 have a `- ID:` row in v9 (parsed `## ID` blocks base vs ca53ba7; missing: []). LC-18, MSG-3, START-6, START-10, COST-5, EVID-2a, EVID-4 rows match the diff.
- F2: REV-22a (review.md:229) "Give the review subagent `$SCOPE_DIR/architecture.md` to check the diff conforms." restores SIZE-23d clause.
- Delta f86b26b..ca53ba7 touches no `roles:`/`when:`/`topic:` line → no rule moves between roles. 512 Dev composes: worst 5117, 0 over 5120; only dev output changed vs f86b26b.
- Lint exit 0; 13 targeted test modules: 286 OK, 1 skip (archive of ca53ba7).
