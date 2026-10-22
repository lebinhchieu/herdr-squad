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
