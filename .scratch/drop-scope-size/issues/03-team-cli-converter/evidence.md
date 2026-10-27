# Evidence: 03 `squad-process team` CLI and converter
sha: 64871b4

## Behaviour
- `squad-process team --home D`: prints `ba, qa-white` style list, `none` or `undecided`; only `TEAM_KEYS` tokens ever reach stdout (hostile `team:` values `qa-white; touch X`, `$(...)`, backticks exit 2, nothing runs, stdout empty). `--has ROLE` (role names via `ROLE_KEY`) prints nothing, exit 0 on team / 1 not / 2 unknown role or bad home; manager, dev, token-coach always on; an undecided team has only the Manager. No `--from-size`.
- Old-format home (any of `size:`, `design:`, `architecture:`, `qa-b:`, no `team:`) through `team` exits 2 with `scope.md:<line>: old format \`<key>:\`; run \`squad-process adopt\` ...` per line; one shared function `squadcompose.old_format_error(home)` (Tech Lead approved the addition to squadcompose.py; not wired into `read_home`, task 12 does that). The same home still composes via `read_home(legacy_scaffold=True)`.
- Converter = `squad-process adopt` (dry run is the default: without `--yes` exit 3, nothing written). Lists each open scope's `scope.md`: `would convert ... -> team: ...`, `skip` for a pinned scope (byte-identical after dry run and apply), `error` for both `team:` and an old line (names both lines), a symlinked scope/file, or an old line below the header. Mapping = `legacy_team` (D3); blank size -> blank `team:`; `design: yes` + `qa-b: no` -> valid team (I8 a, confirmed by Tech Lead).
- Commentary: any value with more than the first token is printed beside the proposed team; `check:` is added for `qa: none`, a non-S/M/L size, a blank size with flags, and words like custom/pod/no QA/only. The original values are kept in the file as `<!-- converted from ... -->` under the `team:` line; `qa:` line is untouched.
- Apply: backup `scope.md.pre-team.bak` beside the file (byte-identical original; restoring it gives the old file, which the 0.5.2 engine shape composes), then atomic write; second run is a no-op with no second backup; CRLF kept (also by the pin step, which used to normalise to LF); an injected failure between backup and write leaves the original. Only goals-free `scopes/<name>/scope.md` (not `_done`) is touched.
- `squad-migrate` fills the template's `team:` line from the `scopes.md` size row (S none, M qa-white qa-black, L + ba/team-lead/tech-lead; no row or unreadable size = blank `team:`); a template with no `team:` line is a loud error with nothing written. Migrate tests use a fixture template (the tree's template changes in ticket 09).
- Live data (copy, REV-5b): `plugin-bk261023` `_done` scopes (21) copied into `scopes/` of a scratch squad: dry run lists all 23 (flags `check` on refine-process, extractor-role, process-fixes, board-flakes, ask-timeline), apply converts, every role composes with exit 0 and owners per duty equal the old size's (`LiveCopyTest`, skipped when the folder is absent). Blueprint squad copy: dry run skips its 2 open scopes as pinned (grillui, mermaidlazy), converts nothing, files unchanged.
- Existing test change: `test_squadadopt` pin test had a `size: M` fixture line; it now converts too, so the fixture uses `qa: full` (the pin-only contract is unchanged).
- Lint baseline (G2b), `python3 bin/squad-process lint`: base 6ec3a75 empty, exit 0; branch empty, exit 0.
- Tests run green: test_team_cli (35), test_squad_migrate, test_squadadopt, and the grep hits for `squadadopt|squad-migrate|squadrules_cli|squad-process|squadcompose|pin_home_file` (31 files).
- Changelog v9: no rule ID changed in this ticket.
- Files beyond the ticket list: `bin/squadcompose.py` (additive `old_format_lines`, `old_format_error`; Tech Lead OK).
- Blank `size:` or any `check` entry: the `<!-- converted from ... -->` comment lists every dropped old line verbatim (`design: yes`, `qa-b: no`, ...); `--` still escaped. Test `test_blank_size_with_flags_keeps_dropped_lines_in_file`.
- `plan_scopes` skips `scopes/_done/*` (names starting with `_`) by design; real-sample dry runs use copies placed directly in `scopes/`.
- `team --home <missing dir or file>` exits 2 with a message, stdout empty; an existing home without scope.md stays `undecided` (exit 0). Test `test_missing_or_file_home_exits_2_but_home_without_scope_md_is_undecided`.
- AC 21 (`upgrade --check` retarget lines) moved from this ticket to ticket 12 by the Tech Lead; no code here.

## QA whitebox

### QA whitebox 03 (code sha 13ed665, evidence b7a512e, base 6ec3a75, branch squad/plugin/drop-scope-size/plugin-dev-dsz-3)

#### Passed (run by me)
- Diff 6ec3a75..13ed665 read vs ticket AC (design 02, C2, C4, C5, C9) and architecture.md.
- Tests OK: test_team_cli 36, test_squad_migrate 20 (the 2 reds from 09 are green here), test_squadadopt 29, test_squadcompose 85, test_team_duties 39, test_squadrules 58, test_crlf_squad_files 8, test_windows_safe 11, test_squadupgrade 19. `squad-process lint` empty, exit 0 (= base).
- G7 live: hostile `team:` values (`qa-white; touch X`, `$(touch X)`, backticks, note with `$(x)`) exit 2, nothing ran, stdout empty. `--has wizard` exits 2. `--has qa-whitebox` maps via ROLE_KEY.
- REV-5b live on copies (read-only on the real folders): the 21 `plugin-bk261023/scopes/_done` scope.md files placed in a scratch squad (process.local.md as fixture): dry run lists all 21, flags `check` on extractor-role (`qa: none`), refine-process (custom pod), process-fixes, board-flakes, ask-timeline; tree unchanged. Apply: every `scope.md.pre-team.bak` byte-identical to the original; `team:` lines as D3 (refine-process `qa-white, qa-black`, process-fixes L = `ba, team-lead, tech-lead, qa-white, qa-black`); second run identical tree, no second backup; 21 scopes x 10 roles = 210 composes, 0 failures; `squad-process team` prints the list. Blueprint copy (grillui, mermaidlazy): dry run skips both as pinned, apply leaves both byte-identical.
- Note: on the real plugin-bk261023 `process.md` apply stops at "8 PO item(s) unanswered" (existing adopt coupling: scope conversion rides the same --yes); not a finding.

#### Findings (one return, REV-17)
- F1 `bin/squadrules_cli.py:94-115` (`cmd_team`): `squad-process team --home <nonexistent dir>` prints `undecided`, exit 0 (live: `--home /tmp/x/nope`, `--home` of a missing folder). The docstring and evidence.md say exit 2 on an unreadable/bad home; no test covers it (`tests/test_team_cli.py` has none). A typo in `--home` is then indistinguishable from an undecided scope, and `--has ROLE` exits 1 silently; the 04 spawn/hook callers will read that as a decided "not on the team". Pass: exit 2 with a message when `--home` is not a directory (an existing home without `scope.md` stays `undecided`, as for compose), plus a test for both.
- F2 spec AC 21 not implemented: ticket 03 lists "AC 21/22 variants ... `squad-process upgrade --check|--apply --yes`" and spec.md:170 requires `squad-process upgrade --check` to print the exact lines `qa-b = no -> qa-black = no` and `size = L -> ba = yes` for an overlay rule with `when: size = L` / `when: qa-b = no`, and `--apply --yes` as the only writer. Branch has no such text (`git grep -n "qa-b = no -> "` empty), no `squadupgrade.py` change, no test, and evidence.md does not mention AC 21. Pass: implement and test AC 21, or the Team Lead states in the ticket which later ticket owns AC 21 and removes it from 03 (then this finding closes, no code).

#### Forward notes
- 04: `squad-process team --has` is the hook caller's contract; F1 matters there.
- 12: engine error for `team:` + old line says "delete the old line by hand" (no adopt pointer; the converter refuses that home, so correct); AC text of 03 says "with or without team:" names `adopt`; keep wording consistent when 12 wires `old_format_error` into read_home.

#### Re-check on 64871b4 (evidence a0ec659), LC-3b
F1 closed: `cmd_team` exits 2 on missing/file --home (live: rc=2, stderr names dir); existing home without scope.md -> `undecided` rc=0; test added (tests/test_team_cli.py). F2 closed: AC 21 moved to ticket 12 (Tech Lead DECISION 03). Ran test_team_cli (37), test_squad_migrate, test_squadadopt, test_squadcompose, test_squadrules: OK. Lint exit 0, empty. PASS.

## QA blackbox

### QA blackbox, task 03 (final code sha 13ed665, evidence b7a512e; branch squad/plugin/drop-scope-size/plugin-dev-dsz-3)

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

#### Re-check on 64871b4 (changed: `squad-process team --home` validation)
Scratch dir with: missing path, a plain file, empty dir, dir with `team: ba, qa-white`.

| Case | Saw | Result |
|---|---|---|
| `--home` missing dir | exit 2, stdout empty, stderr `team: --home '...' is not a directory` | PASS |
| `--home` a file | exit 2, same message | PASS |
| existing dir, no scope.md | exit 0, `undecided` | PASS |
| dir with `team: ba, qa-white` | exit 0, `ba, qa-white`; `--has ba` exit 0 | PASS |
| `--has wizard` | exit 2, unknown role | PASS |

AC 21 moved to ticket 12 (Tech Lead's call); not tested here.

## Tech Lead review

### TL review 03 (code sha 61fff86, branch squad/plugin/drop-scope-size/plugin-dev-dsz-3, base 6ec3a75)
- Bin diff read. Run: test_team_cli, test_squad_migrate, test_squadadopt, test_squadcompose, test_squadrules, test_crlf_squad_files, test_windows_safe OK; lint exit 0.
- Dry run on copy of plugin-bk261023 with 3 _done scopes copied into scopes/: S -> none (commentary kept), M -> qa-white, qa-black. plan_scopes skips scopes/_done/* by design.
- F1 (FAIL): blank size + design/architecture yes or qa-b no: lines dropped, no trace in file (check only printed). Fix: comment lists every dropped old line when check non-empty or team blank; test.
- Also 09: F1 template lost `qa: full` (arch.md:48); returned to dsz-9, 09 final sha moves again.
- Re-check 13ed665 (evidence b7a512e, check --base 13ed665 exit 0): F1 closed (comment lists every dropped old line when team blank or check non-empty; test added); 4 test files OK. Final sha: 13ed665 code / b7a512e evidence.
- 03 re-check 64871b4 (evidence a0ec659, check exit 0): F1 closed, tests OK, live missing home rc 2, empty home undecided. Final sha named: 64871b4 / a0ec659.
