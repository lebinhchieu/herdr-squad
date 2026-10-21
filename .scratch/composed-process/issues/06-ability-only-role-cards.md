Status: ready-for-agent
Type: task
Task ID: 06
Touches: `agents/*.md` (all 9), `tests/test_instructions.py`, `tests/test_pod_rules_process.py`, `tests/test_suite_rules_process.py`, `tests/test_task_id_rule.py`, `tests/test_team_lead_role.py`, `tests/test_manager_m_l.py`, `tests/test_designer_handoff.py`, `tests/test_pod_contact_routes.py`, `tests/test_process_citations.py`
Does not touch: `templates/squad/process/*.md` (a missing rule is an ASK to the Tech Lead, who re-issues 03's rule), `bin/`
Harness: `squad-process lint`; `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_instructions test_pod_rules_process test_suite_rules_process test_task_id_rule test_team_lead_role test_manager_m_l test_designer_handoff test_pod_contact_routes test_process_citations`
Blocked by: 03, 05

# 06: Role cards hold ability only

**Done when each `agents/*.md` holds only identity, stance and tools, nothing in it duplicates a rule, and every wording test has moved to rule IDs and targeting.**

## Card shape (at most 30 lines after frontmatter)
1. Frontmatter (unchanged keys).
2. `You are …`: what the role is for, in one paragraph.
3. Stance: how it judges. Examples: QA blackbox "stay blind to the code, don't talk yourself into passing"; Tech Lead "unverified = FAIL".
4. Tools it uses, as names only (`squad-evidence`, `squad-inbox`, …); how to use them is in rules.
5. One closing line: "Your process rules are attached after this card (`roles/<agent>.rules.md`). Follow them. When they don't cover a case, ASK the owner [CORE-<n>] names."

## What moves out
- Everything 03's `mapping.md` marked as moved: start-of-session steps, duties, routing, cost reactions, the roster recipe, inbox procedure.
- Delete each from the card and check its rule exists with `squad-process who <ID>` for that role.
- Fixes for finding 4: `manager.md` "label shape" and "(Retro)" sentences, and `tech-lead.md:29` (escalations.md) are gone with the moved text.
- The ready-tasks duty is now a Tech Lead rule from 03 (b).

## Technical AC
1. `squad-process lint` passes, including the duplication check between cards and rules.
2. Each card is at most 30 lines after frontmatter (test).
3. Every assertion of the listed tests becomes either (a) an assertion on rule targeting, such as `who("REV-3")` acting roles at M including `qa-whitebox`, or a phrase in the composed rules for a role and size; or (b) a deletion, with the reason given in the evidence's assertion map (old test name → new test name, or "deleted: …").
4. `test_process_citations.py` checks `[ID]` citations through the 02 lint instead of headings.
5. Probe: in a temp composed squad, each of the 9 roles is spawned with Haiku (05's harness) and answers YES to one rule marker of its own and NO to a marker in a rule not targeted at it. Record the commands and answers. Spend at most $0.20.
