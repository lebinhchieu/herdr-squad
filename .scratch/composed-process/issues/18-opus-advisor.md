Status: ready-for-agent
Type: task
Task ID: 18
Touches: `templates/squad/process/cost.md` (replaces the model step-up), `templates/squad/process/lifecycle.md` (required triggers), `bin/squad-log-message` (3-return notice text, shared with 12), `tests/test_advisor_rules.py` (new), `tests/test_model_effort_settings.py`
Does not touch: `agents/*`
Harness: `squad-process lint`; `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_advisor_rules test_model_effort_settings test_squad_log_message`
Blocked by: 03, 12

# 18: Rules for the Opus advisor

**Done when the rules say when an advisor call is required, and the 3rd-FAIL notice tells the Developer to consult it before handing in again.** The settings part is done (spec D15): `advisorModel: opus` is in every role template and the live squad's settings, and `tests/test_model_effort_settings.py` pins it.

## Facts (2026-10-21)
- Claude Code has a built-in advisor (https://code.claude.com/docs/en/advisor), turned on with `"advisorModel": "opus"` in settings or `--advisor opus`. A probe on 2.1.306 with Haiku as the main model and `--advisor opus` reported the `advisor` tool present. The flag is not in `--help`.
- The model decides when to call it; no setting forces or caps calls. It is experimental and needs the Anthropic API (not Bedrock or Vertex). Toggling it does not break the main cache. On a subscription, calls count against plan limits.

## PO decisions (round 1, 2026-10-22): spec D15, D16
Required calls:
- the Developer, on a task's 3rd FAIL, before handing in again;
- any role, after 2 failed attempts at the same error, or a BLOCKED unanswered for 2 rounds;
- the Tech Lead or Manager, before an irreversible design choice.

Each required call leaves a 3-line note in the task file: question, advice, what was done. Outside these, the model decides.

## Technical AC
1. Settings are already in place (D15). With ticket 08, a squad's `.local.json` can turn the advisor off per role; test that.
2. Cost rule 4 ("step up one notch of model") is replaced: effort may step up, and a model change happens only by respawn; the advisor comes first.
3. The 3-return notice from 12 adds: "consult the advisor before the next HANDIN; note it in the task file [LC-n]".
4. Each required trigger is one rule with an ID; `who` shows the acting roles.
5. A probe with a spawned Haiku Developer in a temp squad reports the `advisor` tool present (command and answer in the evidence).
