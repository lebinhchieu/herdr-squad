# QA whitebox: technical AC review (REV-7), tasks/tech-design.md rev 2

Verdict: **not yet agreed.** 9 changes (C1 to C9) + 4 smaller (S1 to S4). With them: agreed.
Checked against: architecture.md (final, E4), tasks/spec.md AC numbers, base code at main 2949573 (bin/squadcompose.py, squadrules.py, squad-spawn, squad-log-message, squadreport*), real `scope.md` files in `.claude/squads/plugin-bk261023/` and `enhanced-markdown-vscode/.claude/squads/blueprint/`.

## Changes needed

**C1 AC 11 (task 11) and AC 25 grep cannot pass as written.**
`git grep -n -iw size -- templates/squad/process` = 288 hits today; 58 are `SIZE-n` IDs that survive by D2 (`sizes.md`, `[SIZE-n]` citations): `-w` treats `SIZE-22` as the word `SIZE`.
Pass = `git grep -nP '(?i)\bsize\b(?!-\d)' -- templates/squad/process` returns only `_removed.md`, changelog text, plus an explicit allow-list in the ticket (file:line, reason) for non-scope uses. Same grep over `README.md`, `CONTEXT.md` (Size entry gone, Team/Duty owner/Checker present), `agents/`, `skills/` outside `history/`, `bin/` (only converter/migrate/report-display hits), `hooks/`. `git grep 'qa-b\b'` ok as written (does not match `qa-black`).

**C2 Tasks 02 and 03 conflict with the D1 scaffold.**
02 AC: engine error for an old-format home "names file and line and `squad-process adopt`". 03 AC: an unpinned `size:` scope is refused, never composed. But D1 says until task 10 `read_home` fills duty facts from `size:` for such a home, so `team --home` and the spawn gate would accept it.
Needed: the scaffold is reachable only through the compose path used by rule-file tests (explicit parameter), never by `squad-process team` or the spawn gate; the old-format error text is one shared function, tested directly in 02/03; the end-to-end compose exit 2 is task 10's. Task 03 test must run a `size:`-only home through `squad-process team` and `squad-spawn` and see the refusal while the same home still composes in the scaffold path.

**C3 Pin hand-off (task 03, AC 20) under-specified.** Add, each a test:
- boundary table: pin `0.5.2` -> hand-off; `0.6.0` -> new gate, no hand-off; no pin line -> unpinned path; malformed `plugin:` line (`read_home` raises) -> refuse naming the line.
- Hand-off happens once (a pinned 0.5.x runtime has no hand-off; no exec loop; guard stated).
- Runtime missing `bin/squad-spawn`: exit non-zero, warning, **nothing created** (worktree, label, herdr call: assert on a stub that records calls).
- AC 20 "byte-identical": fixture `scope.md` unchanged by `squad-spawn`, `squad-respawn`, the converter (dry run and apply) and `squad-team`; the composed text of the pinned fixture equals a golden **generated from base sha 2949573**, not hand-written.
- Both entry points: `squad-spawn` and `squad-respawn`, from the PO shell and from an agent session.
I will also run a live respawn on a copy of this squad (pinned 0.5.2, `size: L`) after task 03 (REV-5b).

**C4 Real samples (REV-4) for 01/02 are incomplete.** Repo files hold prose and values the AC does not list; add verbatim as fixtures (cite the source file):
- `size: M, custom pod (PO 2026-10-14): Tech Lead, BA, QA whitebox, Devs; no QA blackbox. ...` (plugin-bk261023 `_done/refine-process`)
- `size: M (PO confirmed 2026-10-17, no QA roles) - signals: ...` with `qa: none (PO 2026-10-17): ...` (`_done/extractor-role`)
- `size: L — confirmed by PO (E1 a). Signals: ...` (blueprint `_done/svgdraw`), `size: M — signals: ...`
- `size: M` + `qa-b: yes` + `design: yes` (blueprint `grillui`); a `design: yes` + `qa-b: no` shape.
Required behaviour: converter takes the first token (arch §7); base `read_home` takes `\b[SML]\b` anywhere (squadcompose.py:70), a different rule, so test a line where they differ. When commentary contradicts the mapping (custom pod, no QA roles), the dry run prints the commentary beside the proposed team and flags it "check"; it is never silently dropped. `qa: none` is not in `_FACT_VALUES` today: converter keeps the `qa:` line untouched and does not crash on it. `design: yes` + `qa-b: no` today's refusal is dropped only under I8(a): AC reads "valid team if PO answers (a); converter refuses with reason if (b)".

**C5 Migration rollback (REV-2b) missing in 02.** Add: restoring the converter's backup gives a byte-identical `scope.md` and the 0.5.2 pinned fixture composes it; apply on a home with both `size:` and `team:` is defined (error naming both, nothing written); second apply no-op and no second backup churn; CRLF `scope.md` keeps CRLF; atomic write (kill between backup and write leaves the original); the converter writes only inside the squad folder (a symlinked scope is refused or not followed). Run the dry run and apply on a **copy** of `plugin-bk261023` and on the blueprint squad copy (live data, REV-5b); I will re-run.

**C6 Single-key lint arrives too late (task 10).** Retarget tasks 04a to 06 run in parallel and are checked by G2, but lint of "two role/duty keys" and of duty value sets lands only in 10, so combination `when:` lines from 04 to 06 surface late. Move to task 01: lint checks every `when:` that uses a new key (value in the key's set from `DUTIES`/`WHEN_KEYS`; at most one key from `DUTIES ∪ {ba, team-lead, tech-lead, qa-white}`; extras only `goal, qa, design, architecture, qa-black`). Task 10 only adds the old-key rejections. Test: `business-ac = ba and qa-black = yes` passes; `business-ac = ba and code-check = qa-white` fails naming the rule.

**C7 Business AC 12, 13, 14 have no runnable check.** 04a "no composed text names an absent role" does not prove Done/hand-in per shape. Add to 04a/05: one table-driven test from `DUTIES` that, per duty fact and value, `who <rule>` lists exactly the acting roles; plus four named shapes (both QAs, qa-white only, qa-black only, no QA) asserting: hand-in target (AC 12), who checks `## Behaviour` (AC 13), a task with qa-white PASS and no qa-black PASS is not Done in the both-QAs text (AC 14), no-QA shape: Manager confirms `evidence.md` and `## Review`.

**C8 Report payload shape (REV-6, task 07).** Beyond "renders without error": every rollup scope row and every report `scope` object has both `team` and `size` keys (string, `""` allowed) for old, new, hand-made (no team line), undecided and error rows (rollup error rows set `"size": None` at squadreport_rollup.py:200,206: `team` must match). Browser test asserts the chip text for old (recorded size) and new (team) rows.

**C9 Tasks 08 and G-level security/robustness.**
- 08: refuses on a pinned scope below 0.6.0, on a goal home, on an undecided team for `remove`; rejects unknown role, add of present role, remove of absent role; keeps commentary, other lines and CRLF; atomic write; `--po-ok` / `--at-boundary` gates tested for the refusal and the pass.
- New G7: `squad-process team` prints only tokens from the fixed set; `--has` validated against `ROLES`; bash callers quote and never `eval` or word-split the list; no value read from `scope.md` reaches a shell unvalidated.

## Smaller

- **S1 G2:** "no new warnings" needs a baseline: record `squad-process lint` output on the task's base sha in the ticket and diff.
- **S2 Task 01:** the expected-owner table for today's S/M/L (AC 9) must be copied from the base SIZE-22/22a text (cite lines), not derived from `DUTIES`; cases: `team:` blank, `team: none`, no `team:` line (hand-made = undecided), trailing `(note)`, duplicate, `manager` token, CRLF.
- **S3 Task 11:** add PROMO-8: edits match `promote.md` and nothing undecided; version `0.6.0` identical in `plugin.json`, `process-version`, changelog header, README; ADR 0018 states where it overrides 0016/0017 (CLAUDE.md domain rule).
- **S4 Reader inventory:** besides the files in tasks 03/07 the base reads `size`/`qa-b` in `bin/squad-spawn:111-118` (design/architecture greps), `bin/squad-log-message:43`, `bin/squadrules_cli.py:109` (help text), `bin/squad-start:367`, `bin/squadcompose.py:190,219-227`. Add one grep AC in 10: `git grep -nE "size:|'size'|\"size\"|qa-b\b" -- bin hooks agents skills ':!skills/*/history'` returns only the allow-list (converter mapping, migrate input, report display).

## Business AC coverage (cited by the Tech Lead)

| AC | Covered by | Status |
|---|---|---|
| 1, 15 | 04a (row per role, no "size"), 01/03 header and undecided refusal | ok; C7 adds shapes |
| 6 | 03 gate, 07 template | ok; Manager-side `team:` write is blackbox's |
| 9, 10 | 01 | ok with S2 |
| 11 | 10 | ok with C6 |
| 12 | 03 hook, 04 handin-target | needs C7 |
| 20 | 03 | needs C3 |
| 21 | 10 | ok (writes nothing) |
| 23 | 07 | needs C8 |
| 25 | 11 | needs C1 |
| 22, 26, 27, 28 | 02, 03, 10 | 22/28 need C4, C5; 26 needs C2 |

## Points the Tech Lead asked about
- D1 scaffold: acceptable if C2 (scope of the scaffold) and the permanent task 10 test stay; the test must grep `squadcompose.py` and run a `size:` home through `compose` expecting exit 2.
- Pin hand-off refusal: agreed with C3.
- Key rename: test every `when:` in plugin rules and overlays for `qa-b`/`qa-whitebox` (task 10) and the `team:` token rejection (01); also `who`/`lint` help text names the new key.
- Converter real samples: C4, C5.
