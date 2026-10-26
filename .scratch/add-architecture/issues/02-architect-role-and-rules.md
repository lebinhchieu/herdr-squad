# 02 Architect role card, settings and process rules
Status: ready-for-agent
Type: task
Blocked by: 01

Duties: put design notes in this file; technical AC are QA whitebox's (agree with it); business AC are the ticket as written; risk flag or business doubt: `BLOCKED NN` (SIZE-14). Cite [REV-13b] hand-in, [EVID-2d] evidence, [SUITE-2c] suites, [LC-19b] design. Run only the test files you touch; before HANDIN run `grep -rl '<touched path or changed string>' tests/` and run every hit (goldens included). QA whitebox runs the full suite once on the final sha. Commit this task file as the ticket at `.scratch/add-architecture/issues/NN-<slug>.md`, evidence at `.../NN-<slug>/evidence.md`. Brief: `$SCOPE_DIR/scope.md`, design `$SCOPE_DIR/tasks/architect-design.md` (the spec; PO confirmed it as written), plan `$SCOPE_DIR/iterations/1.md`. Defect class: none yet. Base: the passed sha of 01 (`--base`).

Touched files: new `agents/architect.md`, new `templates/squad/settings/architect.json`; rule files `templates/squad/process/{core,sizes,starting,spawning,lifecycle,who,review,...}.md` as needed (grep first); `templates/squad/process.md` only if it is still a live source (check); tests `tests/test_templates.py`, `tests/test_instructions.py`, `tests/test_model_effort_settings.py`, `tests/test_sizes.py`, `tests/test_squad_spawn.py`, plus a new `tests/test_architect_handoff.py` modelled on `tests/test_designer_handoff.py`, and any golden/fixture a grep of the changed rule text shows. Rule composition goldens live under `tests/fixtures/rules/`.

## Business AC (spec: `tasks/architect-design.md`)
1. Card `agents/architect.md` like `agents/designer.md`: identity, stance (writes `architecture.md` and ADR drafts only, never code, never edits project files, checks no built code), tools. Settings `architect.json` modelled on `designer.json`, writing only `$SCOPE_DIR/architecture.md` and `$SCOPE_DIR/tasks/`; default sonnet high, advisor on.
2. Rules (each with `roles:`/`when:` headers, ID style as the neighbours): flag rule next to SIZE-3 (`architecture:` line, PO only, any size, Manager never proposes, logged in the iteration file); role rule next to SIZE-9 (Architect delivers `architecture.md` with the listed contents, `Status: draft|final`, in a scope with the flag on); spawn rule next to SPAWN-4 plus SPAWN-2a/b/c mention (after the goal check, before the plan, retire when final, respawn for a question); plan gate like LC-2/LC-2b/LC-11/LC-11b (the plan or task split waits for `Status: final`); START-4 role-short `arch`; START-5 lifetime row; feedback rule (team `ASK`s the Architect, 2 rounds then Manager, CORE-4).
3. Above the Tech Lead: at L the Architect owns the architecture and the Tech Lead keeps per-task design, quality, security inside it; at S/M it sits above the Developer's design notes. Update CORE-3, WHO-2/WHO-2d tables and the SIZE-22 duty table accordingly. Irreversible tech choices: Architect lists and recommends, the PO decides (Manager escalates); rows "Irreversible design choice" and any "Always goes to PO" cell say so.
4. Conformance to `architecture.md` joins the technical AC and is checked by the existing checker (S Developer's review subagent, M QA whitebox, L Tech Lead + QA whitebox); the Architect checks no code.
5. A composed rules file for a scope with `architecture: no` is byte-identical to today's for every role (no leakage); with `yes` the Manager, Architect and affected roles carry the new rules.

## Technical AC (QA whitebox; agreed unless the Developer counters here)
T1. `squad-process lint` passes before and after; composition tests for yes and no, per role.
T2. Each new rule is one block, stated once, no history or dates ([FILE-style rules in the process writing rule]); pointers elsewhere.
T3. Existing tests in touched files pass whole; every grep hit run; goldens updated only where the text legitimately changed.
T4. Diff lists only the files above plus ticket/evidence files.

## Design notes
(Developer fills in.)
