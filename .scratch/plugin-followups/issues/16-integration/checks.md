| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `git merge-base --is-ancestor <sha> HEAD` exit 0 for 7 shas | - | - |
| AC2 | 443 tests OK (union + shared + SQ-10 trio); `squad-process lint` exit 0 | - | - |
| AC3 | plugin.json 0.11.1; changelog top `## v32` | - | - |
| AC4 | name-only diff vs `2b535f5` lists only 09-15 files | - | - |
