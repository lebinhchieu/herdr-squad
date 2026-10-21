# Evidence 04: overlay and composer

## Behaviour

Run at the handed-in sha from the repo root with `PYTHONDONTWRITEBYTECODE=1`; `F=tests/fixtures/rules/compose`, `--plugin-root $F --squad-dir $F/squad`, `SQUAD_DIR` unset. Homes are temp `scope.md` (size M, design yes, pin `0.4.1 abc1234`) and a `goal.md` home.

- **04-1 stale replace.** Overlay with `replace REV-3 @7f3a9c21`, `compose dev --out out.md`: exit 2, stderr `REV-3: overlay written for @7f3a9c21, plugin now @203fa130`, `out.md` absent (test also keeps an existing `--out` file's bytes).
- **04-2 missing remove / existing add.** `remove REV-99` and `add REV-3` each exit 2 naming the ID (`OverlayFailTest`).
- **04-3 determinism.** Two runs and an all-CRLF copy (rules, overlay, scope.md) give identical bytes with `--now` fixed (`DeterminismTest`).
- **04-4 matrix.** `FactsMatrixTest.test_matrix_role_size_design` pins the rule IDs for 13 role×size×design cells. `dev` M design yes: `CORE-1 REV-3 REV-8 SQ-1`; `tech-lead` and `manager` get `## Index of other rules`, the others none. Aware-only REV-3 for `dev` reads `## REV-3 One verdict per final sha [aware] [squad: replaced]`.
- **04-5 tags and `rule`.** `[squad: replaced]` only on REV-3, `[squad: added]` only on SQ-1. `rule REV-3` prints `## REV-3 One verdict per final sha [squad: replaced]` and the overlay body; `rule NOPE-1` prints `NOPE-1: no such rule`, exit 2.
- **04-6 `who REV-3`.** `S: acts: -; aware: -` / `M: acts: qa-whitebox, qa-blackbox; aware: dev, team-lead` / `L:` same as M.
- **04-7 goal Manager.** Titles: `## MSG-2a … [if size = S]`, `## MSG-2b … [if size in M, L]`; `MSG-1` (no `when`) and the known-fact rules carry no `[if]`. Header `scope: goal g1 (size n/a, design n/a, qa n/a, goal yes)`.
- **Golden files.** `tests/fixtures/rules/compose/golden/dev-M-design.rules.md` (replaced, added, aware) and `manager-goal.rules.md` (`[if]`, index) are compared byte for byte (`GoldenTest`).
- **Pin.** No pin: stderr warning, header `plugin: 0.4.1 unpinned`. Pin of another version and no `--plugin-root`: exit 2 naming `--plugin-root`. Unparseable pin: exit 2.
- **Decisions.** One space before every tag; goal name is the home folder's basename (Tech Lead ANSWER 04; contract updated).
- **Tests.** `cd tests; python3 -m unittest test_squadcompose test_squadrules test_squadprocess test_squadprocess_apply test_squadprocess_show test_windows_safe test_processlint`: 212 tests OK. The fixture lints clean (`lint` exit 0).
