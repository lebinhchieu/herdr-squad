# Evidence: 01 `squad-evidence` tool

## Behaviour

No UI: no screenshots. One real run of the tool, in a throwaway `git init` (`$T` = `bin/squad-evidence` of this branch), plus the test run.

### AC 1, 2, 3: `path`, `add`, `check` end to end

Ran: `path`, then `add` with a review file holding a relative image and a `# ` / `## ` heading, then `check`, then `check --base` after an evidence-only commit and after a code commit.
Saw: folder printed, review headings demoted to `###`/`####`, image copied into `img/` and the link rewritten to `img/<name>` (shown in the `find` and `cat` output), `check` exit 0, `--base` exit 0 on the evidence-only diff and exit 1 naming `code.py` after a code commit.

```
$ squad-evidence path .scratch/f/issues/03-x.md
.scratch/f/issues/03-x.evidence

$ squad-evidence add .scratch/f/issues/03-x.md --heading "Tech Lead review" --from work/tl-review.md --sha 0123456789abcdef0123456789abcdef01234567
.scratch/f/issues/03-x.evidence/evidence.md
[exit 0]

$ find .scratch -type f | sort
.scratch/f/issues/03-x.evidence/evidence.md
.scratch/f/issues/03-x.evidence/img/home.png
.scratch/f/issues/03-x.md

$ cat .scratch/f/issues/03-x.evidence/evidence.md
# Evidence: 03 The thing
sha: 0123456789abcdef0123456789abcdef01234567

## Tech Lead review

### Review

Verdict: PASS

#### AC 1

![home page](img/home.png)

$ squad-evidence check .scratch/f/issues/03-x.evidence
ok: .scratch/f/issues/03-x.evidence/evidence.md
[exit 0]

$ squad-evidence check .scratch/f/issues/03-x.evidence --base <base sha>   # evidence-only commit
ok: .scratch/f/issues/03-x.evidence/evidence.md
[exit 0]

$ squad-evidence check ... --base <base sha>   # after a code commit
code.py:1: changed since 8ac17f69f1e100c3b9690e322ba152f8538ed6fe but outside a *.evidence/ folder
[exit 1]
```

### AC 4: every `check` problem class

Ran `python3 -m unittest test_squad_evidence` (40 tests): absolute embed (POSIX and `C:\`), URL, `..`, empty alt, missing target, non-image extension, orphan in `img/`, backticked name, linked name, bare name, image over 1 MB (exactly 1 MB passes), `--base` with a path outside `*.evidence/`, clean folder and evidence-only `--base` diff. Each failing class asserts exit 1 and the `file:line: problem` shape.

### AC 5: fenced blocks

`test_fence_may_name_an_image_but_text_after_it_may_not`, `test_tilde_fence_and_longer_fence`, `test_fenced_block_is_not_demoted_or_rewritten`.

### AC 2, 3: add idempotent, clash, missing image, Behaviour kept

`test_second_run_is_byte_identical`, `test_name_clash_between_reviews_prefixes_the_second` (second gets the heading slug as prefix, re-add stable), `test_missing_image_exits_2_and_writes_nothing` and `..._leaves_an_existing_file_unchanged`, `test_creates_title_from_ticket`, `test_title_without_a_title_line`, `test_developers_behaviour_section_is_never_touched_or_reordered`.

### AC 6, 7: encoding and settings

`test_crlf_review_is_written_back_as_lf`, `test_utf8_survives`; `test_windows_safe`, `test_squad_respawn`, `test_squad_spawn`, `test_templates`, `test_model_effort_settings` pass (138 tests together). Both settings files load as JSON; the diff adds only the three allow rules.

```
$ cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_evidence test_windows_safe test_squad_respawn test_squad_spawn test_templates test_model_effort_settings
Ran 138 tests ... OK
```

### Decisions to confirm

- `# Evidence: <NN> <title>` drops a leading `<NN>:` from the ticket title (`# 01: x` gives `# Evidence: 01 x`, not `01 01: x`).
- `--root DIR` resolves a relative ticket path against DIR; `--sha` sets the `sha:` line.
- `add` removes an `img/` file only when the replaced section used it and no remaining embed does.
