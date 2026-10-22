Status: ready-for-agent
Type: task
Task ID: 32
Touches: `templates/squad/process/review.md` (REV-22), `templates/squad/process/sizes.md` (SIZE-2 table cell, SIZE-22 duty row), `skills/squad-process-update/changelog.md` (v7 entry reasons), `tests/test_sizes.py`, `.scratch/composed-process/spec.md` (D9), `.scratch/composed-process/issues/17-sizes-s-m-l.md` (line 23), `.scratch/composed-process/issues/29-sizes-slice-2-review-evidence-suites.md` (Comments only)
Does not touch: `templates/squad/settings/*.json` and `tests/test_advisor_rules.py` (the advisor stays `advisorModel: opus`, D15), `skills/squad-process-update/history/process-v7/` (snapshot is re-copied at release, not here), `.scratch/composed-process/round1-sizes-advisor.html` (record of what the PO was asked), `bin/*`, `agents/*`
Harness: `bin/squad-process lint`; `bin/squad-process lint --hashes` before and after (the three IDs below change, no other); `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_sizes test_dev_rules_size test_pod_contact_routes test_squadrules test_squadcompose test_process_history test_process_writing`
Blocked by: none. Base: `squad/plugin/sizes-and-models/plugin-dev-sm-28` @ 853b0a4. Ticket 15 starts after this passes (same rule files)

# 32: The S review subagent runs on Sonnet at high effort, not Opus

**Done when the S Developer rule, the sizes tables, the v7 changelog, spec D9 and ticket 17 all say the fresh-context review subagent runs on Sonnet at high effort, nothing in them still says Opus for that subagent, and the tests pin the new wording.**

## PO decision (2026-10-22, E8 chat)
The one fresh-context review subagent an S Developer starts before `HANDIN` (spec D9, ticket 17, REV-22) runs on **Sonnet** at **high** effort, not Opus. Only the subagent changes: the built-in advisor stays Opus for every role (D15, D16). Rule hashes change by design: the process is unreleased (no pin carries the old text, D6 has nothing to keep).

## What
1. **REV-22** (`review.md`, roles dev, size S) becomes, keeping `roles:`, `when:`, `topic:` and the ID:
   > Before `HANDIN` start one fresh-context review subagent (Agent tool: `model: sonnet`, `effort: high`; a new agent, not a fork) that reads your diff; findings and fixes go under `## Review`; `squad-evidence check <folder>` must pass.
   Same facts as today plus the model and effort; no size clause in the text (a rule with `(S:` fails lint).
2. **SIZE-2** (`sizes.md`, S row, `Done =`): "one fresh-context Opus review subagent" → "one fresh-context Sonnet review subagent (high effort)".
3. **SIZE-22** (`sizes.md`, Code check row): "Developer + Opus review subagent" → "Developer + Sonnet review subagent".
4. **Changelog** (`changelog.md`, v7 entry above `## v6`): every reason that says "Opus review" for the S review (21 lines in `added:` and `retargeted:`, all the phrase "Developer + Opus review at S"; the other 44 lines that say Opus are advisor or model text and stay) says "Sonnet review (high effort)". REV-22 keeps its place in `added:` and its reason names the model and effort and the PO date. No ID is added or removed; SIZE-2 and SIZE-22 are already listed.
5. **Spec D9** and **ticket 17** (line 23): "one fresh-context Opus review subagent" → "one fresh-context Sonnet review subagent at high effort (PO 2026-10-22)". **Ticket 29** AC 8 keeps its text; add under its `## Comments`: "2026-10-22 ticket 32: the review subagent runs on Sonnet at high effort; AC 8 wording is superseded."
6. **Tests** in `tests/test_sizes.py`:
   - `S_DeveloperReview`: the REV-22 body contains `fresh-context review subagent`, `` `model: sonnet` ``, `` `effort: high` ``, `` `## Review` ``, `squad-evidence check`, and not `Opus`; it still reaches `composed("dev","S")` and not M or L; `acts("REV-22","S") == ("dev",)`, `acts("REV-22","M") == ()`.
   - Duty table: the row reads `Code check | Developer + Sonnet review subagent`.
   - New `test_no_opus_review_subagent_in_the_rule_files`: no file under `templates/squad/process/` and no line of the v7 changelog entry matches `Opus review|review subagent.{0,40}Opus|Opus.{0,20}review subagent`. No allow-list.

## Technical AC
1. `grep -rniE "opus review|review subagent.{0,40}opus|opus.{0,20}review subagent" templates skills/squad-process-update/changelog.md tests .scratch/composed-process/spec.md .scratch/composed-process/issues/17-*.md` prints nothing (output in the evidence). The `issues/29` and `round1-sizes-advisor.html` hits are expected and listed.
2. `squad-process lint` passes. `lint --hashes` before and after differ in exactly REV-22, SIZE-2 and SIZE-22 (both listings in the evidence). A pinned hash found elsewhere in `tests/` or `tests/fixtures/` for those IDs is regenerated, not skipped.
3. The composed Developer rules at S stay under 5120 B (`test_dev_rules_size`); the new REV-22 text is the only growth. Measured size before and after in the evidence.
4. `squad-process compose dev` at S shows REV-22 with the new text; at M and L it has no REV-22 (test).
5. `test_sizes.Changelog.test_every_changed_added_or_removed_rule_id_is_in_the_v7_entry` passes (base `2e81e5e`); the REV-22 reason is longer than 10 characters and names Sonnet.
6. Targeted tests in Harness pass, then the test files the diff touches; no full suite (the Tech Lead runs it once, ticket 15).
7. The diff touches only the files in Touches. `git diff --stat` in the evidence.

## Technical notes (Tech Lead)
- The Agent tool takes `model` and `effort`; `effort` is set only when instructions ask for it, and this rule is that instruction. `subagent_type: fork` would inherit the Developer's model, so the rule says "not a fork".
- Why Sonnet high is enough: the review is a fresh read of one diff against the ticket AC, run once per ticket; the Developer's own checks and the Manager's confirmation stay in front of it. If a QA run finds a miss a Sonnet review let through, that is a retro item, not a reason to revert now.
- Not in scope: telling the Manager anything new. The Manager still only confirms `## Review` exists (ticket 29 AC 8).
- This squad itself runs process v6 (S = Tech Lead review PASS), so this ticket is checked by the Tech Lead; the new S rule applies to squads that adopt v7.

## Comments
