# QA whitebox 03 (code sha 13ed665, evidence b7a512e, base 6ec3a75, branch squad/plugin/drop-scope-size/plugin-dev-dsz-3)

## Passed (run by me)
- Diff 6ec3a75..13ed665 read vs ticket AC (design 02, C2, C4, C5, C9) and architecture.md.
- Tests OK: test_team_cli 36, test_squad_migrate 20 (the 2 reds from 09 are green here), test_squadadopt 29, test_squadcompose 85, test_team_duties 39, test_squadrules 58, test_crlf_squad_files 8, test_windows_safe 11, test_squadupgrade 19. `squad-process lint` empty, exit 0 (= base).
- G7 live: hostile `team:` values (`qa-white; touch X`, `$(touch X)`, backticks, note with `$(x)`) exit 2, nothing ran, stdout empty. `--has wizard` exits 2. `--has qa-whitebox` maps via ROLE_KEY.
- REV-5b live on copies (read-only on the real folders): the 21 `plugin-bk261023/scopes/_done` scope.md files placed in a scratch squad (process.local.md as fixture): dry run lists all 21, flags `check` on extractor-role (`qa: none`), refine-process (custom pod), process-fixes, board-flakes, ask-timeline; tree unchanged. Apply: every `scope.md.pre-team.bak` byte-identical to the original; `team:` lines as D3 (refine-process `qa-white, qa-black`, process-fixes L = `ba, team-lead, tech-lead, qa-white, qa-black`); second run identical tree, no second backup; 21 scopes x 10 roles = 210 composes, 0 failures; `squad-process team` prints the list. Blueprint copy (grillui, mermaidlazy): dry run skips both as pinned, apply leaves both byte-identical.
- Note: on the real plugin-bk261023 `process.md` apply stops at "8 PO item(s) unanswered" (existing adopt coupling: scope conversion rides the same --yes); not a finding.

## Findings (one return, REV-17)
- F1 `bin/squadrules_cli.py:94-115` (`cmd_team`): `squad-process team --home <nonexistent dir>` prints `undecided`, exit 0 (live: `--home /tmp/x/nope`, `--home` of a missing folder). The docstring and evidence.md say exit 2 on an unreadable/bad home; no test covers it (`tests/test_team_cli.py` has none). A typo in `--home` is then indistinguishable from an undecided scope, and `--has ROLE` exits 1 silently; the 04 spawn/hook callers will read that as a decided "not on the team". Pass: exit 2 with a message when `--home` is not a directory (an existing home without `scope.md` stays `undecided`, as for compose), plus a test for both.
- F2 spec AC 21 not implemented: ticket 03 lists "AC 21/22 variants ... `squad-process upgrade --check|--apply --yes`" and spec.md:170 requires `squad-process upgrade --check` to print the exact lines `qa-b = no -> qa-black = no` and `size = L -> ba = yes` for an overlay rule with `when: size = L` / `when: qa-b = no`, and `--apply --yes` as the only writer. Branch has no such text (`git grep -n "qa-b = no -> "` empty), no `squadupgrade.py` change, no test, and evidence.md does not mention AC 21. Pass: implement and test AC 21, or the Team Lead states in the ticket which later ticket owns AC 21 and removes it from 03 (then this finding closes, no code).

## Forward notes
- 04: `squad-process team --has` is the hook caller's contract; F1 matters there.
- 12: engine error for `team:` + old line says "delete the old line by hand" (no adopt pointer; the converter refuses that home, so correct); AC text of 03 says "with or without team:" names `adopt`; keep wording consistent when 12 wires `old_format_error` into read_home.

## Re-check on 64871b4 (evidence a0ec659), LC-3b
F1 closed: `cmd_team` exits 2 on missing/file --home (live: rc=2, stderr names dir); existing home without scope.md -> `undecided` rc=0; test added (tests/test_team_cli.py). F2 closed: AC 21 moved to ticket 12 (Tech Lead DECISION 03). Ran test_team_cli (37), test_squad_migrate, test_squadadopt, test_squadcompose, test_squadrules: OK. Lint exit 0, empty. PASS.
