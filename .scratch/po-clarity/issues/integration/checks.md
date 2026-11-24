| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| Merges | `git merge-base --is-ancestor` of the 02 branch, the 07 branch and `main` against HEAD: all three true | - | - |
| plugin.json 0.11.0 | `grep version .claude-plugin/plugin.json` = 0.11.0 = changelog top heading v31; v30 below it, v29 untouched | - | - |
| Changelog v31 | bullets for 01, 03, 04, 07, 05, 02 and LC-9c; Deploy names 0.11.0 and the `squad-inbox add` refusal; no conflict markers | - | - |
| ADR 0034 kept | `ls docs/adr/0034-handin-evidence-gate-blocks.md` | - | - |
| Shared tests | see `## Behaviour`: all OK | - | - |
