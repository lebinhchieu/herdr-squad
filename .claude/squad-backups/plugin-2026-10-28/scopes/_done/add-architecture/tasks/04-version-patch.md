# 04 Plugin version patch bump
Status: ready-for-agent
Type: task
Blocked by: 03

PO decision (chat): patch bump is enough. Change `.claude-plugin/plugin.json` version 0.6.0 -> 0.5.2 (one line). No other file changes expected; `tests/test_squadadopt.py:312` uses 0.6.0 as a fixture string and stays. Historic 03 evidence mentions 0.6.0; leave it. Check with `git grep -n "0\.6\.0"` and `git grep -n "0\.5\.1"` that nothing else keys off the version (changelog `## v8` is a process-snapshot number, not the plugin version).
Duties: [REV-13b] hand-in to QA whitebox (QA blackbox is not spawned: no observable behaviour changes, PO informed), [EVID-2d] evidence (`.scratch/add-architecture/issues/04-version-patch/evidence.md`, commit this file as the ticket `.../04-version-patch.md`), [SUITE-2c] run the tests whose files grep hits. Base: 8e10686. Defect class: none.
## Business AC
1. `.claude-plugin/plugin.json` reads 0.5.2; no other source of the version disagrees.
## Technical AC
T1. Diff is plugin.json plus ticket/evidence only. T2. Tests that grep hits pass.
