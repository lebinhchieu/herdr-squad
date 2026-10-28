# QA blackbox, task 03 (final code sha 13ed665, evidence b7a512e; branch squad/plugin/drop-scope-size/plugin-dev-dsz-3)

Scratch squad: temp dir with `scopes/<name>/scope.md` for ten shapes plus a pinned and a `_done` scope, and the stock `process.md`. CLI only, no screenshots.

| AC / check | What I did | What I saw | Result |
|---|---|---|---|
| AC 22(a) dry run | `squad-process adopt --squad-dir D --dry-run` | one line per scope: `would convert scopes/m_no/scope.md -> team: qa-white`; nothing written (`diff -r` before/after empty) | PASS |
| AC 22 variants | S; M+qa-b no; M+qa-b yes; L+design; M+architecture; L+qa-b no; M+design+qa-b no; blank | `none`; `qa-white`; `qa-white, qa-black`; `ba, team-lead, tech-lead, qa-white, qa-black, designer`; `qa-white, qa-black, architect`; `ba, team-lead, tech-lead, qa-white`; `qa-white, designer`; blank `team:` (undecided) | PASS |
| AC 22 `--yes` | `adopt --yes` | each scope has `team:` and none of the four old lines; `scope.md.pre-team.bak` equals the original byte for byte | PASS |
| Commentary kept | `size: M (confirmed by PO ...)` + `qa-b: no  (task only changes tests)` | dry run prints the commentary beside the proposal with `check: commentary may contradict the mapping`; file keeps `<!-- converted from size: M (...); qa-b: no (...) -->`; blank `size:` also kept in a comment | PASS |
| Second run | `adopt --yes` again | exit 0, tree identical to after the first run | PASS |
| AC 20 pinned scope | scope with a `plugin:` line | skipped, says "pinned ... runs its own runtime", file byte-identical | PASS |
| `_done` scope | scope under `scopes/_done/` | untouched | PASS |
| Both old and new lines | `size: M` + `team: ba` in one scope | exit 2 naming both lines, nothing written for any scope | PASS |
| CRLF | CRLF `scope.md` | converted with CRLF kept | PASS |
| `squad-process team --home` | team, `none`, blank | prints the list, `none`, `undecided` | PASS |
| `--has` | `qa-black`, `designer`, `wizard`, `qa-whitebox` | role names only: unknown role (incl. `qa-black`) exit 2 with the list; `designer` not on team exit 1; `qa-whitebox` on team exit 0 | PASS |
| Old-format scope | `size: M` + `qa-b: no` | exit 2: `scope.md:3: old format size:; run squad-process adopt (dry run first) ...` for each old line | PASS |
| Hostile `team:` value | `qa-white; touch /tmp/PWN3` | exit 2 unknown token; no file created | PASS |
| AC 28 after migration | `compose manager|dev|qa-whitebox` on six migrated shapes | all exit 0; `duties:` owners equal AC 9 for each shape (S, M, L, L no QA blackbox, M+design, M+architecture) | PASS |

Not tested here: AC 21. `squad-process upgrade --check` on a 0.5.2-pinned squad with overlay `replace SIZE-2` and local rules `when: size = L` / `when: qa-b = no` prints no `size = L -> ba = yes` or `qa-b = no -> qa-black = no` lines (it reports `plugin changes: added 0, changed 0` and one stale SIZE-2 decision) and left every file byte-identical. The rule retargets come with tickets 04-08 and 12, so I do not count this against 03; the Team Lead should confirm AC 21 belongs to ticket 12.

## Re-check on 64871b4 (changed: `squad-process team --home` validation)
Scratch dir with: missing path, a plain file, empty dir, dir with `team: ba, qa-white`.

| Case | Saw | Result |
|---|---|---|
| `--home` missing dir | exit 2, stdout empty, stderr `team: --home '...' is not a directory` | PASS |
| `--home` a file | exit 2, same message | PASS |
| existing dir, no scope.md | exit 0, `undecided` | PASS |
| dir with `team: ba, qa-white` | exit 0, `ba, qa-white`; `--has ba` exit 0 | PASS |
| `--has wizard` | exit 2, unknown role | PASS |

AC 21 moved to ticket 12 (Tech Lead's call); not tested here.
