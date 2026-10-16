Status: ready-for-agent
Blocked by: none (RB-03 6e1110e, RB-04 933adc2, RB-05 64fc206 passed)
Task ID: RB-06
Files touched: none of its own (merge commit and evidence only)

# RB-06: Integration branch and full suite

**Done when one branch holds RB-01..RB-05 and the full suite with `--tz` is green on its final sha.** Requirement: `spec.md` R-16, R-17, R-18. Process: `process.md` → Inside a goal (integration task).

1. Branch from main; `git merge` the passed RB-03 branch (it already contains RB-01 and RB-02), RB-04 and RB-05. Before each merge run `git merge-base --is-ancestor main <sha>` and `git log --oneline main..<sha>`, and paste the output in `dev-evidence.md`. A conflict means stop and `BLOCKED`.
2. Commit every fix before the run. Run `python3 tests/run_suite.py --receipt <evidence dir> --tz` in the background once on the final sha, never `pkill`.
3. Orphan search (R-17), output saved: `git grep -nIiw board -- README.md CONTEXT.md agents skills templates bin hooks docs/adr ':!skills/squad-process-update/history' ':!docs/adr/000[1-4]-*' ':!docs/adr/0009-*'` (and `tests/`). Each hit is a different word, a name in data (`dev-board-1` style scope names in fixtures), the changelog's v3 block (title, `why:`, `old:` text), or is explained in `dev-evidence.md`. Also `git grep -nIiE 'squad-board|open_board|BOARD_|test_board_|fixtures/board'` outside `.scratch`, `.claude`, history and ADRs 0001-0004, 0009 is empty outside RB-03's allow-list.
   **Allow-list (data, kept on purpose):** `tests/fixtures/squad-notify/{notification-permission_prompt,stop,subagent-stop}.json`, `hooks/po-inbox/fixtures/contract-home.ts`, `tests/test_squad_respawn.py` (a name string near line 145 and a comment near line 223), `tests/fixtures/inbox/home/escalations.md` (lines 19-20), `tests/fixtures/inbox/board-reader-golden.json` (its `_doc` line, line 2: provenance of the golden file, "captured from the board's reader at 39ab34a"; the rest of its hits are `dev-board-N` names and quoted escalation text, i.e. data), and `docs/adr/0007-inbox-sits-on-escalations.md` lines 7 and 11 ("the board's Needs-you", "`squad-board` stays the cross-home view"): ADR 0007 is not edited (BA R-11), ADR 0009's Consequences carries the correction. Any other hit means fix the file; never edit an allow-listed fixture to empty the grep. `dev-evidence.md` names every allow-listed hit.
4. Links (R-12): every relative link in README.md, CONTEXT.md, `docs/adr/*.md` and every `/squad:<skill>` name resolves; script output saved.
5. Smoke (R-02, R-03, R-05): in a scratch squad under a temp dir with stub `claude`/herdr (the `test_squad_start.py` harness is the model), run `squad-start --dry-run`, `squad-inbox add/list/answer`, `squad-process show manager`, `squad-migrate --dry-run` on a flat fixture holding `messages.jsonl` + `activity.jsonl`; save outputs; none says board.
6. audit-token (R-18): its integration (20d00b7) also edits `CONTEXT.md`, `README.md`, `bin/squad-spawn`, `bin/squad-respawn` and adds `docs/adr/0008`; our ADR is therefore 0009. If the PO has merged it into main first, merge main in, resolve README/CONTEXT conflicts keeping both sides' lines (never drop audit-token's), re-run steps 2-4. It takes no process version, so v3 stays ours. If a conflict is not a plain keep-both, `BLOCKED`.

## Technical AC
1. Receipt: first line `sha <final sha> clean=yes`, `OK` tail, `suite-tz.txt` present with its skip line (RB-01 AC7: "no time files") and no other skipped phase.
2. `git diff --stat main` = RB-01..RB-05's files only; deletions match RB-03's list.
3. `templates/squad/process.md` on the branch says `process-version: 3` and `skills/squad-process-update/history/process-v3.md` exists (ADR 0009 states it); output in `dev-evidence.md`.
4. Steps 3-5 outputs are in `dev-evidence.md`; the Tech Lead's `promote.md` items P1-P5 are all present on the branch (`git grep` for each).
- Receipt hygiene: run targeted tests with `PYTHONDONTWRITEBYTECODE=1`; `rm -rf bin/__pycache__` (gitignored, so `clean=yes` misses it; `test_no_pyc` fails on it) before the receipt run; `dev-evidence.md` quotes the receipt's real tail. The suite may recreate `bin/__pycache__` after a run: `ls bin/__pycache__` after it and clear it before any further run; say in `dev-evidence.md` whether it reappeared and which test imports caused it.

## Comments
