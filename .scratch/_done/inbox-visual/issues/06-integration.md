Status: ready
Blocked by: 01, 02, 03, 04, 05 if built
Task ID: IV-06
Files touched: merges only; `.claude-plugin/plugin.json` (`version` bump), `.scratch/inbox-visual/` (committed as the scope's design files)

# IV-06: integration: merge the passed branches, run the full suite

**Done when one branch holds IV-01..IV-05 (as built), the full suite (`--tz`, nothing skipped) is green, and the live drive shows the new look in a real pane.** `process.md` → Inside a goal (Stacked branches, integration task): branch from the scope's base, merge each passed branch with `git merge --no-ff`, quote `git log --oneline <base>..HEAD`. Expected conflict (checked with `git merge-tree` on ffef7f1 + 0a33014): ONE hunk in `ui.tsx` around the list row (`row-${it.id}` / `withAge`). Resolve to IV-04's side (0a33014): it already draws the id through `line(it.id)`, which is IV-03's hostile-id fix, so nothing is lost. `ui.test.ts` auto-merges. After the merge, run the hostile-id list test of item.test.ts and the IV-04 list tests.

## Technical AC
1. `claude plugin validate <repo>` and `claude plugin test <repo>` pass; mod calls unchanged (`validate` lists `$.process.run`, `$.fs.stat` only).
2. `python3 tests/run_suite.py --receipt <dir> --tz` green, receipt first line `sha <rev> clean=yes`.
3. `plugin.json` version bumped minor.
4. **Live drive** (`evidence/IV-06/live.md`, for QA blackbox): in a herdr pane with the stand-in Manager env of `.scratch/po-inbox/design.md` → Driving the mod, over a copy of the fixture home: add E1/E2-shaped items and a 12+9 set; read the pane as text and ANSI at 80x24 and 40x24; answer an option item; the Manager prompt text arrives byte for byte. Stop every process by PID.
5. **Business AC V-29:** no regression of po-inbox B-05..B-36 (`.scratch/po-inbox/`): the full suite covers the automated ones; the live drive (4) also walks the list, item, answer, withdraw and read paths so QA blackbox can repeat B-05..B-36 by hand on the integration sha; `live.md` names which B-nn each step covers. Business AC of this ticket: V-29.
6. `.scratch/inbox-visual/` (spec, design, plan, issues) committed on the branch as `IV-06: scope design files`, as they are on the day of the last merge.

## QA whitebox additions (agreed 2026-10-16; each is a pass condition; a line with the same number replaces the ticket line above)
Source: `evidence/qa-w-ac.md` in the scope folder.

- **6.6 (new)** `claude plugin validate` output is captured at the base and at the merge and the two are diffed in `evidence/IV-06/`: only the version line may differ.
- **6.7 (new)** The receipt is on the merge sha, `clean=yes`, `--tz`, nothing skipped; the live drive records `bodyRows` seen at 80x24 and 40x24 and compares it with IV-03's evidence.
- **6.8 (new, Manager FINAL 2026-10-16) Answered-waiting group live.** The mod has no hold-delivery hook. QA blackbox tries once in a scratch squad with no deliverer to see the Answered-waiting list group on IV-04. If that fails, QAB waives the group on dev-4's unit test, and the IV-06 live drive must show that group in a real pane (an answered item whose delivery is still pending; the Developer builds the state in a sandbox squad with no deliverer, or by the file state the group reads) and save the pane text and ansi (V-15 amber waiting) in `dev-evidence.md`.
- **6.9 (new)** The live ansi capture of an item with a long body shows `+N more` dim (the Button has a `Text dimColor` child; IV-03 could only unit-test it). Save the ansi bytes in `evidence/IV-06/`.
