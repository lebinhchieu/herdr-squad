# QA whitebox 01 (engine vocabulary) on d5a4b9c (evidence d2c2d00, no code change)

Verdict: FAIL, one finding (test-only). Everything else passes.

## Finding
1. **tests/test_team_duties.py:~150-170 (SAMPLES / LegacyTeam), C4 fixture missing.** Amended AC 01 (REV-7 C4) requires verbatim fixtures including `size: M — signals: ...`. The line exists: `.claude/squads/plugin-bk261023/scopes/_done/report-ui-fix/scope.md:7` (`size: M — signals: user-visible UI change, ~5 tasks, one repo, no risk flag, PO req...`). The test header says it "does not exist in any scope.md on this machine": wrong (my C4 text cited the wrong squad; the Tech Lead's note carried it). Pass = add the full line verbatim as a SAMPLES entry, source path cited, assert `legacy_team(...) == ["qa-white", "qa-black"]`; drop the "does not exist" comment.

## Checked and fine
- Diff vs architecture.md §2, §3, §6 c.5: TEAM_KEYS, ROLE_KEY, PRESENCE_KEY, 13 DUTIES chains equal the §3 table line by line; `qas` pseudo-item; terminals manager/dev/ticket; legacy_team mapping equals §7 / D3 (S none; M qa-white, qa-black unless qa-b no; L +ba, team-lead, tech-lead; flags add theirs; first token).
- C6 lint in 01: one primary key (duties + ba, team-lead, tech-lead, qa-white) plus extras goal, qa, design, architecture, qa-black; value sets; overlay ops linted with rule ID; old-only whens still pass (scaffold). Error names rule ID.
- S2: owner table hand-copied from base `sizes.md` SIZE-22 (269-281), SIZE-22a (291-295), SIZE-20; I re-read the base text, every cell matches. 128-set sweep, 13 duties, purity, CRLF, hostile values all tested.
- I ran: test_team_duties 39 OK, test_squadrules 58 OK, test_sizes 36 OK, test_qab_optional 13 OK; `bin/squad-process lint` empty, exit 0 (equals the recorded base baseline, G2b). The `grep -rl` hits for WHEN_KEYS/FILE_ORDER/squadrules/changelog.md also in evidence list (pod_rules_process, process_conversion, process_history, squadadopt, squadupgrade, squadprocess*, windows_safe, crlf) are the Dev's runs; targeted by me: the four above.
- Python stdlib only; no `size` text added to rules.

## Forward to 02/03 (not findings of 01)
- `legacy_team` returns None for a blank AND for an unreadable non-blank size (`XL`, `(not decided)`): the converter (03) must test `raw.strip() and result is None` and flag it, not write a blank `team:` silently.
- `read_home` still raises ComposeError on `qa: none` (extractor-role sample): ticket 02.

## Re-check (LC-3b) on 991cab6 (evidence-only 67dee82 on top)
- Finding closed: `tests/test_team_duties.py` SAMPLES has `M-signals` = value of `report-ui-fix/scope.md:7` (verbatim, checked by sed), asserted via `legacy_team` -> `["qa-white","qa-black"]`; wrong "does not exist" comment gone.
- Diff d5a4b9c..991cab6 touches only that test + evidence. `test_team_duties` 39 OK; `squad-process lint` empty, exit 0 (= base).
- Verdict: PASS.
