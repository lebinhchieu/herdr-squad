Status: ready-for-agent
Type: task
Task ID: 01
Touches: `bin/squad-evidence` (new, python wrapper like `bin/squad-report`), `bin/squadevidence.py` (new), `tests/test_squad_evidence.py` (new), `templates/squad/settings/dev.json`, `templates/squad/settings/tech-lead.json`
Does not touch: `templates/squad/process.md`, `agents/*`, `bin/squad-close`, `bin/squad-migrate`, `bin/squad-start`, `tests/run_suite.py`
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_evidence test_windows_safe test_squad_respawn test_squad_spawn` (a temp dir with a throwaway `git init` for `--base`; PNGs are 1x1 bytes written by the test)
Blocked by: none

# 01: `squad-evidence` tool

**Done when `path`, `add` and `check` behave as `spec.md` → "The tool" says, with tests.** The tool is how the Developer assembles reviewers' files into the ticket's one `evidence.md` and how the Tech Lead proves the file has no unembedded screenshot and the evidence commit is evidence-only.

## What
Implement the three subcommands exactly as specified in `spec.md` (layout contract + "The tool"). Reuse `squadio.utf8_stdio()`, follow the `bin/squad-report` wrapper pattern (executable, `sys.dont_write_bytecode`). Stdlib only. Add the allow rules (dev: `Bash(squad-evidence:*)`; tech-lead: `Bash(squad-evidence check:*)`, `Bash(squad-evidence path:*)`).

## Technical AC
1. `path`: `.scratch/f/issues/03-x.md` → `.scratch/f/issues/03-x.evidence`; a `tasks/T1.md` path → `tasks/T1.evidence`; a path not ending `.md` → exit 2.
2. `add` on a review file with a relative image and an absolute image: both copied into `img/`, links in `evidence.md` are `img/<name>`, review headings start at `###`, the section sits under `## <heading>`. Second run with the same input → byte-identical `evidence.md` and `img/`. Name clash between two reviews → second prefixed with the heading slug. Missing image → exit 2, no file written or changed.
3. `add` creates `evidence.md` with `# Evidence: <NN> <title>` from the ticket's first `# ` line (test with and without a title line); an existing `## Behaviour` section written by the Developer is never touched or reordered.
4. `check` fails (exit 1, one `file:line: problem` per line, each class tested): absolute embed; URL embed; `..`; empty alt; missing target; non-image extension; orphan file in `img/`; a screenshot named in backticks or linked with `[text](img/x.png)` instead of embedded; image over 1 MB; `--base` with a changed path outside a `*.evidence/` folder. Passes (exit 0) on a clean folder, including `--base` with an evidence-only diff.
5. Text outside fenced code blocks only is scanned for mentions; a fenced block may name an image file.
6. Every file open uses `encoding="utf-8"` and `newline="\n"`; `tests/test_windows_safe.py` passes. CRLF input in a review file is accepted and written back as LF.
7. The two settings files stay valid JSON and every other allow rule is unchanged (tests that load `templates/squad/settings/*.json` pass).
8. Evidence: `evidence.md` in this ticket's evidence folder (layout contract) shows one real `add` + `check` run as fenced output; Developer runs `squad-evidence check` on its own file.
