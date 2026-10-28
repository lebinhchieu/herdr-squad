# 05 Promote the glossary term

Status: ready-for-agent
Blocked by: 04
Task ID: UXD-05

**`CONTEXT.md` has the UI/UX Designer term and the `design:` flag.** The scope's last task (`process.md` → Promotion). Build it on UXD-04's passed branch (`--base`).

## What to do

Apply the entries of `$SCOPE_DIR/promote.md` to `CONTEXT.md` with the `/domain-modeling` skill's rules (the repo's `CLAUDE.md` names it as the way to edit it): a **UI/UX Designer** entry under People (after QA blackbox) and a `design:` flag entry, in the file's existing format, with an `_Avoid_:` line where the Tech Lead's wording gives one.

## AC

1. Only `CONTEXT.md` changes, and only by the entries in `promote.md`, worded as there.
2. Suite green (`tests/` has no test on `CONTEXT.md`: run it anyway), receipt in `$SCOPE_DIR/evidence/UXD-05/`.
