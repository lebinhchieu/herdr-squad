# Evidence: 07 QA blackbox checks from committed shots first

## Behaviour

No screen: a text change to two rules in `templates/squad/process/review.md`.

| AC | What I ran | What I saw |
|---|---|---|
| AC1 | `git diff -U0 templates/squad/process/review.md` | REV-9 now: check each business AC first from the Developer's committed shots and text in `evidence.md` `## Behaviour` ([EVID-2a]); run the app only for an AC whose shot is missing, unclear or shows the wrong state, and for the obvious unhappy paths no shot covers ("obvious" restored by task 10). |
| AC2 | same diff, REV-11 | `qa-b.md` line per AC: `AC → shot or live → what you did (live only) → what you saw → pass/fail` ("what you did (live only)" added by task 10); `shot` = checked from a committed shot, `live` = by a live run. |
| AC3 | `grep -c 'EVID-2a' templates/squad/process/review.md`; `squad-process lint` | the shot rule is stated once (REV-9); REV-11 only names the two words. Only pointer is `[EVID-2a]`, an existing ID. Lint prints nothing, exit 0. (First try failed `length: 70 words > 60`; REV-9 is now under 60.) |
| AC4 | `cd tests && python3 -m unittest test_qab_optional test_squadrules test_sizes test_squadupgrade test_squadcompose`; `grep -rl 'REV-9\|REV-11' tests/` (8 hits: 5 test files above, plus 3 fixtures they load) | `Ran 133 tests ... OK`, nothing skipped. No golden quotes the old REV-9 or REV-11 text (`grep -rl` of the old phrases in `tests/`: none). |
| AC5 | below | below |

### AC5: exact rule text, for Chieu to approve

(The REV-11 tail about embedding screenshots is unchanged and cut here only because `squad-evidence check` reads the image-embed syntax in quotes as a real embed.)

**REV-9 QA blackbox check**

Before:
> On `HANDIN`, test the running app the way `project.md` says (for example Playwright against the dev server, with the Developer's branch deployed or served locally). Walk every business AC, plus the obvious unhappy paths a real user would hit.

After:
> On `HANDIN`, check each business AC first from the Developer's committed shots and text in `evidence.md` `## Behaviour` ([EVID-2a]). Run the app the way `project.md` says only for an AC whose shot is missing, unclear or shows the wrong state, and for the obvious unhappy paths no shot covers.

**REV-11 QA blackbox evidence**

Before:
> Write evidence to `$SCOPE_DIR/evidence/<task>/qa-b.md`: each AC → what you did → what you saw → pass/fail, with each screenshot embedded (…rest of the rule unchanged).

After:
> Write evidence to `$SCOPE_DIR/evidence/<task>/qa-b.md`: each AC → `shot` or `live` (checked from a committed shot, or by a live run) → what you did (live only) → what you saw → pass/fail, with each screenshot embedded (…rest of the rule unchanged).

Dropped from REV-9: the Playwright example sentence and "Walk every business AC" (replaced by shot-first). "obvious" is kept; "a real user would hit" is dropped. Final text is as of task 10 (reopen of 07; changes from d3118ab below).

### Task 10 (reopen): change from d3118ab

- REV-9, only this phrase: `and for unhappy paths no shot covers` → `and for the obvious unhappy paths no shot covers`.
- REV-11, only this phrase: `→ `shot` or `live` (checked from a committed shot, or by a live run) → what you saw → pass/fail` → `→ `shot` or `live` (checked from a committed shot, or by a live run) → what you did (live only) → what you saw → pass/fail`.
- Check: `git diff -U0 d3118ab -- templates/squad/process/review.md` shows exactly these two lines changed; front-matter and rule IDs untouched. `bin/squad-process lint` exit 0 (REV-9 still under 60 words). `grep -rn` of both old phrases in `tests/`: no quote to fix. `cd tests && python3 -m unittest test_qab_optional test_squadrules test_sizes test_squadupgrade test_squadcompose test_processlint test_rules_wording test_rules_contract` → `Ran 194 tests ... OK`, nothing skipped.

## Review

| AC | Test or capture file | How run |
|---|---|---|
| AC1 | `templates/squad/process/review.md` REV-9 (diff in Behaviour) | `git diff -U0 templates/squad/process/review.md` |
| AC2 | `templates/squad/process/review.md` REV-11 | same diff |
| AC3 | `squad-process lint` (rule length max 60 words, duplicate sentences, unknown IDs) | `bin/squad-process lint` → exit 0, no output |
| AC4 | `tests/test_qab_optional.py`, `test_squadrules.py`, `test_sizes.py`, `test_squadupgrade.py`, `test_squadcompose.py` | `cd tests && python3 -m unittest test_qab_optional test_squadrules test_sizes test_squadupgrade test_squadcompose` → 133 OK |
| T10 AC1-AC5 | `templates/squad/process/review.md` REV-9, REV-11; the Task 10 section above | `git diff -U0 d3118ab -- templates/squad/process/review.md`; lint; the 8 test files above (194 OK) |
| AC5 | `## Behaviour` → AC5 section above | read |
