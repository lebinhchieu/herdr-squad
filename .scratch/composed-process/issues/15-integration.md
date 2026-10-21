Status: ready-for-agent
Type: task
Task ID: 15
Touches: the integration branch only (merges)
Blocked by: 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 17, 18, 19, 20

# 15: Integration

**Done when one Developer branch from the effort's base has every passed branch merged, targeted tests pass, and the Tech Lead's full suite passes on that sha (`--tz`).**

## Technical AC
1. Merge order follows the Blocked-by graph. A conflict is resolved only in the integration branch and is listed in the evidence with each side's ticket.
2. `squad-process lint` passes on the template.
3. The full suite passes (`python3 tests/run_suite.py --receipt <dir> --tz`), run by the Tech Lead; the receipt is in the scope's `evidence/`.
4. A live end-to-end probe in a temp squad: `squad-start` → spawn Developer and QA whitebox at M → each answers YES to a marker in its own composed rules and NO to the other's. Commands and answers are in the evidence.
