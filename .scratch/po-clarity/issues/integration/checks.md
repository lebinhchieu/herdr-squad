| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| Merges | `git merge-base --is-ancestor` of every passed sha (01 `932173b` `4629bb8`, 02 `e2b05c8`, 03 `5f0288f`, 04 `34191f3`, 05 `e0ab63b`, 06 `6bab9f1`, 07 `eaab72e`, `main` `9b74b02`) against HEAD: all true; 03's `evidence.md` has `## Review` | - | - |
| plugin.json 0.11.0 | `grep version .claude-plugin/plugin.json` = 0.11.0 = changelog top heading v31; v30 below it, v29 untouched | - | - |
| Changelog v31 | bullets for 01, 03, 04, 07, 05, 02 and LC-9c; Deploy names 0.11.0 and the `squad-inbox add` refusal; no conflict markers | - | - |
| ADR 0034 kept | `ls docs/adr/0034-handin-evidence-gate-blocks.md` | - | - |
| Shared tests | see `## Behaviour`: all OK | - | - |
