# promotion: promote.md committed into the project docs

## Behaviour

Base `a654749` (integration passed). Code commit `7ffbddb` touches only `CONTEXT.md` (+20) and `docs/adr/0035-routine-gates-go-ahead.md` (new, +18). No UI, so no screenshots.
- 5 terms in `CONTEXT.md` `## Work`, directly after **Check table**, before **Phase rule**: Origin tag, Plan fields, Plan line, Bare ID, Routine gate. Same form as the neighbours (bold term, one definition, `_Avoid_`); text taken from `promote.md` unchanged.
- ADR 0035: `git ls-tree` over `main` and every branch (`git branch -a`) for `docs/adr/0035*` found nothing before the commit; main's last ADR is 0034. Text is the fenced block of `promote.md`.
- Check only, all true and untouched by the diff: ITER-19 (`iterations.md:151`), LC-9c (`lifecycle.md:106`), START-19c (`starting.md:195`); ADR 0020 line 22 (main beats a draft, merged branch ignored, `origin`) and line 32 (07 amendment, `/api/file`, `img=1&base=`); `docs/inbox-body-guide.md:61` bare-ID refusal; `skills/squad-process-update/changelog.md` top heading v31; `.claude-plugin/plugin.json` 0.11.0.
- Every rule ID the new text cites (ITER-4, ITER-5, ITER-17, ITER-19, START-19c) exists in `templates/squad/process/`.

Tests (SQUAD_* unset, `PYTHONDONTWRITEBYTECODE=1`, from `tests/`, foreground), all OK:
- SQ-10 trio: `test_windows_safe` (14), `test_utf8_helpers` (14), `test_instructions` (16).
- Also: `test_rules_wording` (31), `test_processlint` (31). `grep -rl 'Origin tag\|Plan fields\|Routine gate\|routine-gates\|0035' tests bin`: no hit, so no other test file to run. `squad-process lint` exit 0.
- Full suite: not run (task says no full suite).

## Review

`/mattpocock-skills:code-review` since `a654749`, two sub-agents (sonnet high).

### Standards
No hard violation. Both files follow the existing form (terms: bold, one definition, `_Avoid_`; ADR: title, Status, Context, Decision, Consequences, `Rejected:` as in 0033/0034); no CRLF, `git diff --check` clean. Judgement calls, all left as is because the task says to commit the `promote.md` text:
- Terms cite rules as `([ITER-19])`; older terms use prose ("Rule ITER-17."). No rule asks for either.
- **Plan line** carries API detail (`plan_line_parts`, contract version 1); **Plan fields** repeats START-19c. Both kept from `promote.md`.
- ADR 0035 has no "Plugin 0.x; changelog vN" last line (0033/0034 have one) and the Context date "22-23 Oct" has no year. Plugin 0.11.0 and v31 belong to the scope, not this ADR; the text is as drafted.

### Spec
No finding. Missing or partial: none. Not asked for: none (two docs files only). Wrong: none; ADR text `diff`s equal to the `promote.md` block, the terms match it, ADR number free on all 362 refs, every "already in docs" item true.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| 5 terms in `## Work` | `git diff a654749 HEAD -- CONTEXT.md`: +20 lines after **Check table**, five blocks as in `promote.md` | - | - |
| ADR 0035 | `git ls-tree` over all branches: no other 0035; file = `promote.md` block | - | - |
| Already in docs | grep of ITER-19, LC-9c, START-19c, ADR 0020 lines 22 and 32, guide line 61, changelog v31, plugin 0.11.0: all present | - | - |
| Tests | SQ-10 trio, `test_rules_wording`, `test_processlint`: OK; `squad-process lint` exit 0 | - | - |
