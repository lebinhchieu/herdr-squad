# T3 `.gitattributes` keeps LF

Status: needs-triage (draft)
Type: task
Source: issue.md "Smaller things"
Touches: `.gitattributes` (new), maybe one test
Blocked by: 01, 02, 03, 06, 07

## What
Add `.gitattributes` with `* text=auto eol=lf` (Tech Lead may narrow to `bin/* text eol=lf` plus `*.py`, `*.ts`, `*.md`). The repo index is already LF (`git ls-files --eol bin` all `i/lf`), so no renormalise commit should be needed.

## Business AC (BA; spec.md story 11)
- B1. Given a clone with `core.autocrlf=true` (on any OS), When `git ls-files --eol` runs, Then every `bin/` script and every text file shows `w/lf`; binary files are not converted; no tracked text file may stay CRLF (none today: all 386 are `i/lf`). Today such a clone has 17 files with CR in `bin/`. (The index is already LF; only the checkout converts.)
- B2. On Linux the current tree needs no renormalise commit (`git add --renormalize .` changes nothing).
- **Proved on Linux, no simulation:** `git clone -c core.autocrlf=true` has 0 CR in `bin/`. The PO checklist step (W12) is a spot check.

## Technical AC (Tech Lead; design.md D11, guard test)
The guard test scans the result of 01, 02, 03, 06, 07.
1. `.gitattributes` has exactly `* text=auto eol=lf` and `bin/* text eol=lf`. `git check-attr eol text -- bin/squad-spawn bin/squadinbox.py` says `eol: lf`, `text: set`.
2. `git add --renormalize .` on the current tree changes nothing; `git ls-files --eol` shows no `i/crlf` or `w/crlf`.
3. New `tests/test_windows_safe.py`, a guard over every file in `bin/`: (a) no text-mode `open(`, `read_text(`, `write_text(` or `os.fdopen(..., "w")` without `encoding=`; (b) no write call without `newline="\n"`; (c) no `text=True` or `universal_newlines` subprocess call without `encoding=`; (d) no module-level `import fcntl`; (e) every Python CLI with a `main` calls `utf8_stdio`. Use `ast` for a-c so strings and comments never match; the test names the file and line on failure. Binary opens are exempt: `open(p, "rb"/"wb"/"ab")` and `os.fdopen(fd, "wb")` with a literal binary mode. A non-literal mode (`open(p, mode_var)`) is flagged unless the call has `encoding=` and `newline=`. `Path.write_text(..., newline=...)` is flagged (Python 3.10+).
4. The test passes on the integrated tree and fails (shown in the evidence) on one deliberately bad line.

## Comments
