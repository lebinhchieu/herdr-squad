# T4 Integration, Windows checklist, promote

Status: needs-triage (draft)
Type: task
Source: scope win-compat
Touches: `$SCOPE_DIR/promote.md`, `$SCOPE_DIR/evidence/`, `.scratch/squad-plugin-windows/windows-checklist.md`; no code except merge fixes
Blocked by: 01, 02, 03, 04, 06, 07

## What
Merge T1-T3 on one branch, run the suite with `--tz` (nothing skipped), run the helpers once more under `PYTHONUTF8=0 LC_ALL=C`, write the short Windows checklist for the PO, `promote.md` (ADR candidate: "the plugin must run on native Windows"; domain glossary note if any).

## Business AC (BA; spec.md stories 12, 13)
- B1. The PO gets `windows-checklist.md`, at most 12 numbered steps (the 0a-0c prerequisite checks are a "before you start" list and do not count; QA blackbox drafts `evidence/windows-checklist.md`; CR counts are merged into the steps that write the files; one two-window inbox step; one `core.autocrlf=true` clone spot check) for a plain Git Bash prompt, each with the command and the one thing to see: `squad-start` new, `--resume`, spawn each role with a space-and-emoji path, Manager spawning the pod with no env vars, `squad-inbox list` and the mod, answer an item with emoji, a fresh clone with `core.autocrlf=true` shows LF, a rewritten `scope.md` has no CRLF. Plus one line saying what the squad proved on Linux and what only Windows proves. (story 12)
- B2. The Linux suite is green on the final branch with `--tz`, and **every test file the tickets touch** (listed in the receipt) also passes under `PYTHONUTF8=0 LC_ALL=C`. Under a UTF-8 locale, read-only command output and written files are byte-identical to 0.3.2 (QA blackbox diffs a `git archive`). (story 13)
- B2a. The checklist says plainly what only Windows proves (real tabs, `\n` not becoming `\r\n`, the real Windows file lock, how Claude Code starts `squad-inbox`) and that hooks firing on real Windows is not verified. (story 12)
- B3. Business rule for `promote.md` (BA, one line each): "the plugin runs on native Windows (Git Bash + Python) without env vars; WSL/PowerShell are not targets; `bash` is a prerequisite" - ADR candidate. Glossary: none new.

## Technical AC (Tech Lead; process.md Inside a goal, Promotion)
1. One Developer merges the passed branches of T0, T1, T2a, T2b, T2c, T3 into its own branch, runs the touched test files and hands in; no code beyond merge fixes.
2. I run the full suite on that sha: `python3 tests/run_suite.py --receipt <evidence>/T4 --tz`; receipt first line `sha <sha> clean=yes`, OK line at the tail. Then the changed test files again under `PYTHONUTF8=0 LC_ALL=C PYTHONIOENCODING=cp1252`.
3. `windows-checklist.md` has steps 0a `python3 --version`, 0b `jq --version`, 0c `bash --version` is Git's (not `C:\Windows\System32\bash.exe`), then the BA steps; plus the open items from design.md (the `/c/...` path forms; `os.replace` race while the inbox mod is open).
4. `promote.md`: ADR candidate "the plugin runs on native Windows (Git Bash + Python 3.10+, `bash`, `python3`, `jq` prerequisites; WSL and PowerShell not targets)" plus the D1-D8 decisions in two lines each, target `docs/adr/NNNN-<slug>.md` via `/domain-modeling`; one glossary line only if the BA names a term.

## Comments
