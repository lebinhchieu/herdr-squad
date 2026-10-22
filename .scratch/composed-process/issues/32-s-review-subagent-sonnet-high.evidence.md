# Evidence 32

## Behaviour

### AC1 grep (nothing expected but the new test's own regex line)
```
tests/test_sizes.py:451:        pat = re.compile(r"Opus review|review subagent.{0,40}Opus|Opus.{0,20}review subagent")
```
Only hit: the regex literal in `test_no_opus_review_subagent_in_the_rule_files` (tests/test_sizes.py). Expected issues/29 (AC 8 text, superseded by Comment) and round1-sizes-advisor.html hits untouched.

### AC2 lint --hashes diff (before/after)
```
/tmp/h32-before.txt → /tmp/h32-after.txt
   +3 added, -3 removed, ~0 modified

-  44 SIZE-2 fa17858e
+  44 SIZE-2 03737ca9
-  78 SIZE-22 74b5ce69
+  78 SIZE-22 22a279df
- 222 REV-22 b82dab67
+ 222 REV-22 99eb849f
```
`squad-process lint`: ok. No pinned hashes for these IDs in tests/ or tests/fixtures/ (grep of old hashes: none).

### AC3 composed dev rules at S (bytes, before -> after; limit 5120)
- design yes goal yes: 5086 -> 5119; design yes goal no: 5085 -> 5118; design no: 4795/4794 -> 4828/4827
REV-22 text had to be tightened to fit: `start a fresh-context review subagent (model: sonnet, effort: high, no fork) on your diff; findings and fixes: ## Review;` (ticket wording was 79 B growth, 5165 B at S, 45 B over the limit).

### AC4/5/6 tests
```
Ran 159 tests in 37.368s

OK
```
REV-22 at S: `squad-process compose dev` shows new text; M/L have none (S_DeveloperReview test).

### AC7 diff stat
```
.scratch/composed-process/issues/17-sizes-s-m-l.md |  2 +-
 .../29-sizes-slice-2-review-evidence-suites.md     |  2 ++
 .scratch/composed-process/spec.md                  |  2 +-
 skills/squad-process-update/changelog.md           | 42 +++++++++++-----------
 templates/squad/process/review.md                  |  2 +-
 templates/squad/process/sizes.md                   |  4 +--
 tests/test_sizes.py                                | 17 +++++++--
 7 files changed, 42 insertions(+), 29 deletions(-)
```
