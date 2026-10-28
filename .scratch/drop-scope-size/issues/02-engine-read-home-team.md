# 02 Engine vocabulary: squadcompose

Status: ready-for-agent
Type: task
Blocked by: 01
Design task: tech 01b in `$SCOPE_DIR/tasks/tech-design.md` (read its Decisions D1-D8 and the section for this task)

## What
Engine vocabulary: squadcompose, inside `architecture.md` (Status: final; E4: keys `qa-white`/`qa-black`, no shim). One Developer session; commit to your branch, hand in to QA whitebox and QA blackbox.

## Files you touch (nobody else touches these in parallel)
`bin/squadcompose.py` (`read_home` team parse and validity, D1 scaffold for `size:` homes, `load_rules`/`choose` split, header `team:`/`duties:`, `who_lines` adds duty lines, keeps size lines until 12); `tests/rulesview.py` (`composed(..., team=)`, `who` accepts both); `tests/test_squadcompose.py`

## AC
Amended (REV-7) AC govern where they differ from older text. Source: `$SCOPE_DIR/tasks/tech-design.md` rev 3 (design id in the line). Business AC: `$SCOPE_DIR/tasks/spec.md`.
Your part: `squadcompose.py` side (team: parse and errors, scaffold D1, load/choose, header, who_lines, `qa: none` tolerance, CRLF). Ticket 01 is merged.

### Global
G1 Tests for every behaviour the task changes exist and pass; the task's `grep -rl '<touched path or string>' tests/` hits all run green (CLAUDE.md).
G2 `squad-process lint` clean (no new warnings) on the task branch.
G3 Conforms to `architecture.md` (SIZE-23d): sections named in the ticket; any difference is a finding.
G4 No `size` word added to rule text; no rule block acts on a role absent for any valid team (from 04a on, enforced by the 128-set test).
G5 Rule retargets keep their ID unless the body changed; tombstones carry `why:` and `replaced_by:`; changelog v9 lists every changed ID with a reason (>10 chars).
G2b Baseline: the ticket records `squad-process lint` output on its base sha; the branch output is diffed against it, no new line (S1).
G6 Python stdlib only; no new dependency; files stay UTF-8, LF in writes, CRLF-tolerant reads (`squadio`), no shell-only path logic that breaks on Windows (tests `test_windows_safe.py`, `test_crlf_squad_files.py` pass).
G7 Security and robustness (C9): `squad-process team` prints only tokens from the fixed set (`TEAM_KEYS`, `none`, `undecided`); `--has` is validated against `ROLES` (unknown role exits 2); bash callers quote the value and never `eval` or word-split it (`read -r`/`case`, test with a hostile `team:` value such as `qa-white; touch X` and `$(...)`, asserting nothing runs); no value read from `scope.md` reaches a shell unvalidated. Test in 02 (CLI) and 03 (bash callers).

### Specific (design 01)
01: `resolve_duties` gives, for each of today's S, M, L, `qa-b: no`, `design`, `architecture` shapes (mapped through `legacy_team`), exactly the owners of SIZE-22/22a (hard-coded expected table in the test, AC 9); for all 128 sets every duty has exactly one owner that is present or Manager/Developer/ticket (AC 10); `legacy_team` real-sample tests from this repo: `size: M (confirmed by PO 2026-10-23)`, `size: L`, blank `size:`, `qa-b: no  (task 03 only changes tests/fixtures; ...)` (REV-4: real samples including the blank/idle case); `choose` result equals old `compose` body for the same facts (refactor proof); an unknown role, duplicate role or implicit role in `team:` fails with the line number; `qa-whitebox`/`qa-blackbox` as a `team:` token is rejected naming `qa-white`/`qa-black`; `ROLE_KEY` maps both and no other role; a decided-team home never has a missing fact; `who_lines` unchanged lines for size and new duty lines. **Amended (REV-7):** (S2) the expected-owner table for today's S/M/L is copied from the base SIZE-22/22a text (ticket cites file:lines), not derived from `DUTIES`; `team:` edge cases tested: blank, `none`, no `team:` line (hand-made = undecided), trailing `(note)`, duplicate, `manager` token, CRLF file. (C4) Real-sample fixtures, verbatim with the source file cited: `size: M, custom pod (PO 2026-10-14): Tech Lead, BA, QA whitebox, Devs; no QA blackbox. ...` (plugin-bk261023 `_done/refine-process`), `size: M (PO confirmed 2026-10-17, no QA roles) - signals: ...` with `qa: none (PO 2026-10-17): ...` (`_done/extractor-role`), `size: L — confirmed by PO (E1 a). Signals: ...` and `size: M — signals: ...` (blueprint `_done/svgdraw`), `size: M` + `qa-b: yes` + `design: yes` (blueprint `grillui`), a `design: yes` + `qa-b: no` shape. `legacy_team` takes the first token (arch §7) while base `read_home` takes `\b[SML]\b` anywhere (squadcompose.py:70): one test line where they differ asserts each rule. `qa: none` is not in `_FACT_VALUES`: `read_home` and the converter leave the `qa:` line untouched and do not crash. (C6) Lint lands here for every `when:` that uses a new key: value in the key's set (`DUTIES`/`WHEN_KEYS`); at most one key from `DUTIES` ∪ {`ba`,`team-lead`,`tech-lead`,`qa-white`}; extras only `goal`, `qa`, `design`, `architecture`, `qa-black`. Tests: `business-ac = ba and qa-black = yes` passes; `business-ac = ba and code-check = qa-white` fails naming the rule. Task 10 only adds the old-key rejections. No golden of byte-identical legacy text is required (nothing ships dual).

Before HANDIN: `squad-process lint` (record the base-sha baseline in this ticket, G2b); `grep -rl '<touched path or changed string>' tests/` and run every hit (CLAUDE.md). Tech Lead names the final sha; QAs verdict on it.
Changelog v9: append your changed rule IDs (D8).

### Spec AC added (BA, 1-31 agreed)
AC 30: `team:` line with unknown or duplicate role makes `squad-process compose` fail non-zero naming line and token.

## Comments
