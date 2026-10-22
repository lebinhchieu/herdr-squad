# 04 Integration

Status: ready-for-agent
Blocked by: 01, 02, 03
Task ID: UXD-04

**One branch holds tickets 01-03 and the full suite passes on it.** This is the branch the PO merges and the next ticket builds on (`process.md` → Inside a goal, Stacked branches).

## What to do

- Branch from the scope's base (main at `a9a52ca`), merge the passed branches of UXD-01, UXD-02, UXD-03 into your own branch (`git merge`, inside your own branch only). The tickets touch disjoint files; resolve any conflict that shows up and say what it was.
- Run the full suite: `python3 tests/run_suite.py --receipt <evidence dir> --tz`.
- Run the check after deploy from the spec once, read-only: `squad-spawn designer x --scope add-ui-ux-design --dry-run` must refuse (scope has `design: no`/no line), and succeed against a throwaway scope folder with `design: yes`. Do not leave the throwaway folder behind.

## AC

1. `git log --oneline <base>..HEAD` shows the three passed branches' commits; `git merge-base --is-ancestor <base> HEAD` succeeds. Quote both in `dev-evidence.md`.
2. Full suite green, receipt saved in `$SCOPE_DIR/evidence/UXD-04/`.
3. The two dry-run results are quoted in `dev-evidence.md`.
4. No change beyond the merges unless a merge conflict forced one.

## Notes

Hand in `HANDIN UXD-04: ...` to the Tech Lead. Needs the passed branches named by the Manager in the briefing.
