# 06 ADR 0019 slips

## Behaviour
Doc-only; `docs/adr/0019-...md` lines 12 and 19 changed (`git diff 3d29f4e`: 2 lines).

| AC | Check | Result |
|---|---|---|
| 1 pointers | Line 19 now names `.scratch/squad-plugin-windows/` (ADR 0011) and `.scratch/composed-process/` (bin comments), says they moved to `_done` and were pruned, and points at live `docs/adr/0011-plugin-runs-on-native-windows.md` and `docs/adr/0016-process-composed-per-role.md` (both exist: `ls docs/adr/0011* docs/adr/0016*`). | PASS |
| 2 size | `git ls-tree -r -l main` summed over `process-v[0-9]`, `history/`, `templates/squad/process.md`: 71 files, 474,005 B = **474 KB** (462.9 KiB). Not 580. The QA figure of 476 KB / 75 files could not be reproduced exactly (set definition differs); 474 KB is what this method measures. | PASS (474 KB) |
| 3 no other change | `git diff --stat`: 1 file, 2 lines. `grep -rn _done docs/adr/0019*`: line 10 (list of what was removed) and line 19 (says they were pruned); neither points a reader to a deleted path. | PASS |
| tests | `grep -rl 'adr/0019\|0019-' tests/`: no hits, nothing to run. | PASS |
