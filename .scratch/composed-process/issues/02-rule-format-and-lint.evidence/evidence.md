# Evidence 02: rule file parser and `squad-process lint`
sha: 8b65410
## Behaviour

Run from the repo root at the handed-in sha, with `PYTHONDONTWRITEBYTECODE=1`. `E=tests/fixtures/rules/errors`, `C=tests/fixtures/rules/clean`.

- **02-1 errors fixture.** `python3 bin/squad-process lint --cards error --plugin-root $E --squad-dir $E/squad` exits 1 and prints 21 `file:line: problem` lines, one per error class (first: `templates/squad/process/core.md:1: core.md has 47 lines, over 40`). Same command with `$C` exits 0 and prints nothing.
- **02-2 no rule files.** `lint --plugin-root <empty tmp dir>` prints `no rule files`, exit 0; plain `python3 bin/squad-process lint` in the repo prints the same, exit 0.
- **02-3 bare ids.** The errors output has `bin/tool.py:1: [REV-8] cites a rule that does not exist` and no line for the bare `SEC-04` / `UTF-8` in the cited files.
- **02-4 `when`.** Clean fixture REV-4 reads `when: qa-b = no and size = S` and lints clean; the truth table is pinned in `tests/test_squadrules.py`.
- **02-5 hash.** `lint --hashes` over LF and CRLF copies of `safety.md` gives identical output (same md5); one word edit changes the line; clean REV-3 is `203fa130`.
- **Design AC 6a (delegation).** `compose --out F` and `compose --out F --resolve "…"` still reach the v6 merge; `compose dev --home D` reaches the composer; a token after `compose` starting with `-` is not delegated. Pinned by stub tests in `tests/test_squadrules.py` (`test_compose_by_role_is_refused_until_04` and the delegation tests).
- **Design AC 6b (`--hashes`).** After any problems, one `<ID> <hash>` line per rule in file order, exit code unchanged by the flag: `test_hashes_after_problems_do_not_change_exit`.
- **Suite.** `$SCOPE_DIR/evidence/02/suite-default.txt`: 1012 tests, OK, clean=yes at 4230349.
- **Design AC 7 (rule-body pointers).** `[REV-99]` in a `core.md` body gives `templates/squad/process/core.md:<n>: unknown pointer [REV-99]`; an existing `[REV-3]` and `[SEC-04]` (ignored by the prefix filter) give none (`test_pointer_in_rule_body_must_name_a_base_rule`). Clean fixture still lints clean (exit 0); errors fixture still 21 lines.

## QA whitebox

### QA whitebox: ticket 02, sha 4230349

**FAIL on one finding: the Developer's `evidence.md` (`## Behaviour`) is not committed. Code, tests and every 02 AC pass.**

#### Finding (blocks)
1. No `.scratch/composed-process/issues/02-rule-format-and-lint.evidence/evidence.md` in `4230349` (`git diff-tree -r --name-only 6050951 4230349 | grep evidence` is empty). Global technical AC (spec) and Task lifecycle: the Developer commits `## Behaviour` with its code. The HANDIN message holds the claims, the repo does not. What would pass: that file, committed, with `## Behaviour` for 02-1 to 02-5 (and design AC 6a, 6b), using the commands in the HANDIN. Evidence-only change: re-hand-in on the new sha; I re-check only that file.

#### Passes (no change needed)
- Ran from a clean `git archive 4230349` (probes) and in the Developer worktree (tests, `git status` clean after): `python3 -m unittest test_squadrules test_processlint test_windows_safe test_squadprocess test_squadprocess_apply test_squadprocess_show` with `PYTHONDONTWRITEBYTECODE=1`: 166 tests OK in the worktree.
- `lint --cards error` on `errors` fixture: exit 1, 21 `file:line: problem` lines, one per class; `clean`: exit 0, no output. No rule folder or nonexistent `--plugin-root`: `no rule files`, exit 0 (AC6).
- `--hashes` on `clean`: `REV-3 203fa130` = my own `sha256sum`. A CRLF rule file parses; ID/prefix mismatch is reported.
- Delegation: `compose --out F --resolve "…"` reaches the v6 merge; `rule` reaches the stub (exit 2, "ticket 04"). `processlint.py` untouched.
- Each class has its own `LintClassTest` using `only(...)` (exactly one error): "triggers it and only it" holds.
- Receipt `evidence/02/suite-default.txt`: sha 4230349, clean=yes, OK.

#### Contract `shared/contracts/rules-and-compose.md` (02's side)
- Hash form and golden `203fa130`: ok. `FILE_ORDER` table, unknown stem error: ok. `SQ-<n>` valid only in overlay `add`: ok (`add needs an SQ-<n> ID`; a rule file with SQ ID fails prefix). Pointer prefix filter (`SEC-04` ignored, `[REV-8]` flagged): ok. `skills/**/changelog.md` skipped: ok. `--cards` default `warn`: ok. Compose side (04) not yet built.

#### Route to the Tech Lead (not a FAIL reason)
- Pointers inside rule bodies are not linted (probe: `[REV-99]` in a `core.md` body gave no error). Spec lists agents, skills and bin only, and none of them cites a rule today, so as built the pointer check checks nothing real until 06, and 03 AC1 will not catch a broken pointer in a rule. Decide: add the check to this return (one fix) or make it a 03 AC.
- `lint --plugin-root <typo>` prints `no rule files`, exit 0. Matches AC6; cosmetic.

#### Re-check at 8b65410 (final candidate; supersedes b036cb4 check)
**PASS.** Diff vs b036cb4: `bin/squadrules.py` (+5, pointer check in the lint loop), `tests/test_squadrules.py` (+8), evidence.md (+1). Design AC 7 matches: prefix table plus `SQ`, base rules only, `file:line: unknown pointer [ID]`.
- Probe (clean-fixture copy plus a rule with `[REV-3]`, `[SEC-04]`, `[REV-99]`, `[SQ-3]`, `[CORE-77]` on body line 15): exactly three errors, all `core.md:15`; `[REV-3]` and `[SEC-04]` silent; line number matches the file. Clean fixture exit 0 silent; errors fixture still 21 lines.
- Tests: worktree 8b65410, `test_squadrules test_processlint test_windows_safe test_squadprocess test_squadprocess_apply test_squadprocess_show`: 167 OK, `git status` clean after. (Archive run: only the 2 GitAttributes tests fail, no `.git` there.)
- evidence.md earlier claims (02-1..02-5, 6a, 6b) reverified on b036cb4; AC 7 line added and true. Nit: it calls `[SEC-04]` "bare-style"; it is bracketed but ignored by the prefix filter. Suite receipt in it is at 4230349; the TL's full run covers the final sha.

## QA blackbox

### QA blackbox 02: rule format + lint

**PASS** on 4230349 (branch squad/plugin/runtime-compose/plugin-dev-runtime-compose-2). Own fixtures built from spec.md → Contracts in a temp dir (not the Developer's); tool run by absolute path from the worktree `bin/`. `squad-process lint --help` showed `--squad-dir --plugin-root --cards --hashes`. Plugin-root layout: `templates/squad/process/*.md`, `agents/`, `skills/*/SKILL.md`, `bin/`.

| AC | What I did | What I saw | Result |
|---|---|---|---|
| 02-1 clean | clean fixture (core, review w/ REV-3 + REV-4, safety, agent/skill/bin citing `[REV-3]`/`[CORE-1]`) | no output, exit 0 | pass |
| 02-1 errors | 17 fixtures, one error class each: dup ID, no roles, no topic, unknown role, unknown when key, unknown when value, prefix vs file, 70-word bullet, same 12-word sentence rule/rule, rule/agent file, cited `[REV-99]` missing, tombstone still a rule, overlay remove of missing ID, two ops one ID, op w/o why, op w/o upstream | each printed exactly one `file:line: problem` line naming the class (e.g. `templates/squad/process/safety.md:7: duplicate ID SAFE-1 (first at …:1)`, `agents/x.md:1: sentence repeats SAFE-2 (…:11)`), exit 1 | pass |
| 02-2 | `--plugin-root <empty dir>`; plain `lint` in the worktree (template has no rules) | `no rule files`, exit 0 both | pass |
| 02-3 | agent file with `SEC-04`, `UTF-8`, `[REV-9]`, `[SEC-04]` | only `agents/x.md:1: [REV-9] cites a rule that does not exist`; no SEC-04/UTF-8 line. Note `[SEC-04]` bracketed also gave no line on that file because line 1 reports once; per-line reporting is the tool's choice | pass |
| 02-4 | REV-4 with `when: qa-b = no and size = S` in clean fixture | clean, exit 0 | pass |
| 02-5 | `--hashes`: LF vs CRLF copy vs trailing-spaces copy vs one word edited vs one attribute (`aware:`) edited | LF=CRLF=trailing-spaces `REV-3 203fa130`; word edit `fa6c81bb`; attr edit `64d50ce0`; other rules unchanged. Independent sha256 of (attr lines + body, LF, stripped) gives 203fa130 | pass |

#### Observation (not a FAIL)
- Overlay errors print `process.local.md:N` without the squad dir; rule-file errors print a path relative to plugin root. Still `file:line`.

#### Re-check 4230349..8b65410 (changed: bin/squadrules.py, tests, evidence): PASS
New rule-body pointer lint, own fixtures (temp dir, deleted after):
- clean fixture: exit 0, no output.
- `See [REV-99].` in core.md body → `templates/squad/process/core.md:7: unknown pointer [REV-99]`, exit 1; same in review.md (`:15`).
- Body with `[REV-3]`, `[SEC-04]`, `[UTF-8]`, bare `SEC-04` → silent, exit 0. `[CORE-1]` → silent.
- Cited tombstone ID `[REV-1]` → reported as unknown pointer (it is no longer a rule): acceptable.
Earlier 02-1..02-5 results unaffected (changed files are additive: 5 lines in squadrules.py).
