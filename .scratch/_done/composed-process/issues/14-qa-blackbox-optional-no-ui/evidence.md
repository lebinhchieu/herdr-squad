# Evidence 14: `qa-b: no`

## Behaviour
Harness: `squad-process lint`; `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_qab_optional test_squadcompose` (58 tests OK); `test_dev_rules_size test_processlint test_manager_m_l` (46 OK).

- **AC1** M, `qa-b: no`: Manager gets SIZE-21 (spawn list without QA blackbox, flip-back steps), SPAWN-2b absent; dev gets REV-19 + EVID-6 and no REV-13b/14b/LC-20b; QA whitebox gets REV-20 + EVID-7; BA gets REV-21 and no REV-8/SIZE-5b; SIZE-20 ("Done = QA whitebox PASS"). Tests: `QabNo.*`, and a per-rule test that a base block and its variant never compose together.
- **AC2** no `qa-b` line: golden sha256 per role x size x design (`tests/fixtures/qab/golden.json`) taken from the pinned 4901cab runtime (`git archive`); new code matches after removing the 8 new rules (their sections, `rules:` tokens, index lines). The new rules cannot be byte-invisible: the Manager needs the proposal rule SIZE-19 at the default, and the Index of other rules lists every unchosen rule. Raised to Tech Lead/BA.
- **AC3** `qa-b: no` + `design: yes`: `compose` exits 2 and `lint --home D` exits 1, both naming `qa-b` and `design`. `qa-b: no` at S composes identical to no line (test, all roles).
- **AC6** `squad-process lint` clean; `who REV-9` etc. print `M qa-b no: acts: -; aware: -`.
- `qa: light` combines (test).

## Notes
- Rule hashes of edited rules change (only `when:` lines), by design.
- Edited `when:` to add `and qa-b = yes`: REV-8, 9, 11, 13b, 14b, SIZE-5b, SIZE-8b, EVID-3b, LC-20b, SPAWN-2b. SIZE-10b/17d, LC-3b, REV-3/12/17/18b left (QA blackbox-only with design yes, or still right for QA whitebox).
- New IDs: REV-19..21, EVID-6..7, SIZE-19..21 (peers 12/21 may also take REV/EVID numbers: lint at integration).
- `bin/`: `squadcompose.py` (error, `who` qa-b lines), `squadrules_cli.py` (`lint --home`).

## Developer-rules byte delta
Composed dev rules (M, design no, goal no): `qa-b` absent or yes: +0 B (4827 B). `qa-b: no`: +94 B (4921 B). S: +0. All under the 5 KiB limit.

## QA whitebox

### QA whitebox: ticket 14 @ 5af0a26 (base 4901cab)

Verdict: **PASS**

Ran: `test_qab_optional test_squadcompose` = 58 OK; `squad-process lint` exit 0.
Independent AC 2 check (not the Developer's golden): `git archive 4901cab` vs the branch, `compose <role>` over 9 roles x size S/M/L x design no/yes with no `qa-b` line. After removing the 8 new rules (their sections, `rules:` tokens, index lines) all outputs are byte-identical; 0 differences. The raw outputs differ only by those new rules (SIZE-19 for the Manager, index lines for the unchosen ones): inherent to adding rules, accepted.
AC 3: `qa-b: no` + `design: yes` → `compose` rc 2 and `lint --home D` rc 1, both naming `qa-b` and `design`. Base blocks carry `and qa-b = yes`; variants carry `qa-b = no`; per-rule never-both test exists. Dev rules byte delta +0 (default), +94 B at qa-b no (4921 of 5120).

#### Notes / follow-ups (not blocking)
1. Under `qa-b: no` M, a few composed rules still name QA blackbox as a done-owner or spawn: `WHO-1b` ("Task done | QA whitebox + QA blackbox"), `SIZE-2` M/L rows (SIZE-20 overrides in words), `START-5`. They are outside the BA's list for 14; SIZE-20 states Done = QA whitebox PASS. Suggest one follow-up item for the integration task or the droppable last ticket.
2. `qa-b: no` at size S with `design: yes` errors (composes fine at design no); the ticket says S composes as no line. Edge case, harmless: S with design yes and no QA blackbox has no meaning to override. Tech Lead may accept.
3. Evidence is at the old `14-…evidence/` path (old tool): integration re-runs the `git mv` (Tech Lead's amendment).

#### Re-check 5af0a26..99796ce (2026-10-22): PASS
Diff = SIZE-20 text only (`sizes.md`): adds the "read QA whitebox alone" clause for "both checkers/QAs" wording; closes note 1 in words. `test_squadcompose test_dev_rules_size` 53 OK; `squad-process lint` ok.

## QA blackbox

### QA-b 14 (re-check sha 99796ce; first check 5af0a26, branch squad/plugin/process-fixes/plugin-dev-pf-4)
Method: `squad-process compose <role> --home <fixture scope> --squad-dir … --plugin-root <runtime> --now <fixed>` for all 9 roles on fixtures (M/L/S × no key / `qa-b: yes` / `qa-b: no` / `qa-b: no`+`design: yes` / `qa-b: maybe`), baseline = `git archive 4901cab`, then `/usr/bin/diff`. `squad-process who`, `lint`. No code read.

| AC | What I did | Saw | Result |
|---|---|---|---|
| 1 | M `qa-b: no`, all roles | Manager: SIZE-19/20/21 (no QA blackbox in spawn list: "spawn ba, team-lead, tech-lead, qa-whitebox, token-coach, not QA blackbox"; flip back to yes with steps). Dev: REV-19 (HANDIN to QA whitebox only; Done = QA whitebox PASS), EVID-6 (Behaviour per AC: command + output). QA whitebox: REV-20 (check Behaviour per AC, own PASS is Done), EVID-7. BA: REV-21 (writes AC alone). `who REV-11` = qa-blackbox absent at `qa-b: no`. Dev rules mention no QA blackbox | pass |
| 1b | same, Manager rules | Still says "QA whitebox PASS + QA blackbox PASS" (M/L rows), "once both checkers have passed" (iteration check-in), "that both checkers passed the sha" (merge check), table "Task done: QA whitebox + QA blackbox". Only SIZE-20 says the SIZE-2 rows "read" Done = QA whitebox PASS; the merge gate and check-in rule are not varied | **FAIL**: Manager merge/check-in gate still demands a QA blackbox verdict that does not exist |
| 2 | no `qa-b` line (M, S) and `qa-b: yes` (M), 4901cab vs new | dev, ba, team-lead, qa-whitebox, qa-blackbox, designer, token-coach: byte-identical. Manager +11/-1 lines (SIZE-19 rule + rule index lines); Tech Lead +8 (index lines of SIZE-20/21, REV-19..21, EVID-6/7). No existing rule text changed | pass (BA FINAL: reading agreed) |
| 3 | M `qa-b: no` + `design: yes`, every role | all 9: exit 2, `scope.md: qa-b: no cannot be combined with design: yes (…) set qa-b: yes or design: no`. S `qa-b: no` vs no key: all 9 roles byte-identical. `qa-b: maybe`: exit 2 `qa-b must be yes \| no` | pass |
| 4 | SIZE-21 | flip-back steps present (set yes, respawn Developers and QA whitebox, spawn QA blackbox with briefing, note in iteration file) | pass |
| 5 | Dev rules at `qa-b: no` | no HANDIN to QA blackbox | pass |
| 6 | `squad-process lint` (plugin) rc 0; `who SIZE-20/21, REV-19/20/21, EVID-6/7` show acts only for `qa-b no` variants | | pass |

#### Re-check 99796ce (fix for 1b)
Method as above (compose M/L/S × no key / yes / no, baseline `git archive 4901cab`, header lines 1-4 excluded).

| AC | What I did | Saw | Result |
| --- | --- | --- | --- |
| 1b | Manager, Team Lead, Tech Lead, BA at M/L/S `qa-b: no` | SIZE-20 now reads: wherever a rule says "both checkers", "both QAs", "QA whitebox + QA blackbox" or "PASS + QA blackbox PASS" (SIZE-2, task-done owner table, merge and check-in rules), read QA whitebox alone. Present in all four roles' rules; the stale rows remain but are explicitly overridden | pass |
| 2 | no `qa-b` line, M/L/S, all 9 roles vs 4901cab | dev, ba, team-lead, qa-whitebox, qa-blackbox, designer, token-coach: 0 body lines changed; Manager +10 (SIZE-19 + index lines), Tech Lead +8 (index lines); no existing text removed or changed | pass |
| 3 | `qa-b: no` + `design: yes`, manager and dev | exit 2, same message as before | pass |
| 6 | `squad-process check` | process.md is current | pass |

Verdict: PASS 14 on 99796ce.
