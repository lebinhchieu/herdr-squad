# Evidence: 07 Upgrade a squad one rule at a time

## QA whitebox

### QA whitebox 07, 0a427c2 (round 1): FAIL

Ran `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadupgrade test_squadcompose test_process_history test_windows_safe test_squadruntime test_squadrules test_process_conversion` → 192 OK. Read all of `bin/squadupgrade.py`, the tests, the 13 fixtures, SKILL.md, changelog.md. Fixture per case-table cell, write guards (byte-snapshot of the squad tree plus backups), backup, log rows, scope.md pin, pin moved last, second apply no-op, bad-fixture CI proof, odd `installed_plugins.json`: all present and correct. `history/process-v7/` equals `templates/squad/process` at this sha (`diff -r` clean).

#### Findings
1. **skills/squad-process-update/changelog.md:156 + bin/squadprocess.py:187-191: the v7 block sits at the end (under v2) and `read_changelog` truncates at the first `## v7+` heading.** The file is newest-first (v6 at line 1). Reproduced: move the v7 block to the top, as the next release block would be, and `read_changelog` raises "no `## v<N>` heading found", so legacy `squad-process plan/apply` (kept for non-adopted squads until 09) breaks. Today's layout only works because v7 happens to be last, and v8 will go on top. Pass: put v7 first like every other version, and make `read_changelog` skip rule-format blocks (`## v7+` up to the next heading) instead of cutting everything after the first one; add a test with a v7+ block at the top and in the middle.

#### Notes (not blocking; Tech Lead to route)
- `--apply` without `--yes` exits 0 with "NOT APPLIED"; a caller must read the text. Consider exit 3 (SKILL.md step 3 relies on text only). No AC says either way.
- No test pins `history/process-v7/` to `templates/squad/process`; trim (22) will make them differ until INT re-copies. Suggest ticket 23 AC: `diff -r` clean at the final sha.
- v7 `added:` lines say "converted from P:206"; that is provenance, not a PO-readable why. Acceptable for the first rule-format release; later versions need a real why.
- Ticket AC 4 "one fixture is the live squad's overlay" waits for 09 (`overlays/` dir exists for it).
- `upgrade --check` on the live squad cannot be run until 09 adopts it (no `process.local.md`; it answers "not adopted").

#### Re-check at a9faac4 (diff 0a427c2..a9faac4) — PASS
- Finding 1 fixed: v7 block now at top of `changelog.md:1`; rest of file is the same lines (sorted diff identical). `squadprocess.read_changelog` skips each v7+ block instead of truncating (`bin/squadprocess.py:187-195`). Real file parses to the same 18 items as the base changelog (`b66036b`), `==` equal.
- Test `test_rule_format_blocks_skipped_anywhere` covers top, middle, two blocks.
- `_changelog_why` now reads only the target version's block (`squadupgrade.py:223`).
- TL ruling: `--apply` without `--yes`/`--resolve` exits 3 (`squadupgrade.py:468`), test asserts exit 3 and files byte-identical (`test_squadupgrade.py:123-131`), SKILL.md step 3 says so.
- Ran: test_squadprocess test_squadupgrade test_squadcompose test_process_history test_windows_safe test_squadruntime test_squadrules test_process_conversion → 222 OK; worktree clean after.

## QA blackbox

### QA blackbox: ticket 07 (upgrade by rule id), sha a9faac4

Verdict: **PASS**. Method: the branch's `bin/squad-process upgrade|upstream` against copies of `tests/fixtures/upgrade/<case>/{old,new,squad}` (used as inputs only), in /tmp scratch; outcomes judged against the ticket's case table and `tasks/business-ac.md`, not against `expect/`. CLI only, no screenshots. Scratch deleted after.

| AC | Did | Saw | Result |
|---|---|---|---|
| B07-1 cases table | `--check` on each cell | Add/no op, Change/no op, Remove/no op, Retarget/no op, retarget-op, retarget-own, semantic-clash, adopted: "nothing needs a decision", exit 0; counts printed (e.g. "1 unaffected"). Change+op: `REV-2 stale`, options keep/take/file:<path>, exit 3. Remove+op and Split+op: `removed` with `replaced_by` and why, options drop/retarget:<ID>/local, exit 3. Op on unknown ID: `unhandled`, exit 2. Add-clash and semantic-clash: listed under "review (not blocking)", exit 0 | pass |
| B07-1 never asks about unchanged rules | check outputs above | unaffected ops counted, not listed | pass |
| B07-2 nothing written | `--apply --yes` with no `--resolve`; `--resolve` without `--yes`; bad choice; resolve for a non-flagged ID | each: tree hash identical before/after; exit 3 ("NOT APPLIED"), 3, 2, 2 | pass |
| B07-3 apply | `--apply --yes --resolve …` for keep/take/file, drop/local/retarget (remove), retarget:COST-4 (split) | keep: op re-hashed, text kept; take: op dropped; file: new text from file; drop: op gone; local: becomes `add SQ-1` with roles/topic of the removed rule; retarget: op moves to the new ID, re-hashed. `plugin.pin` = new pin; `process-log.md` rows (upgrade row + one row per decision "the PO chose …"); every scope's `scope.md` pin unchanged | pass |
| B07-3 backup | after each apply | `backup: /tmp/squad-backups/<squad>-process.local-<date>.md` holds the old overlay; a second apply the same day writes `…-2.md`, nothing overwritten | pass |
| retarget cells | retarget-op / retarget-own | op rehashed to the new hash; own `roles:` line kept | pass |
| B07-4 upstream | `squad-process upstream` | lists each `upstream: proposed` op with why and body; local-only squad → "0 proposed"; an op the plugin now ships verbatim (adopted) is removed by `--apply` (overlay empty) | pass |
| B07-5 changelog | read `skills/squad-process-update/changelog.md`, ls | v7 block on top with `added:`/`changed:`/`removed:`/`retargeted:`; `changelog-v7.md` gone; `history/process-v7/` holds the rule folder | pass (note: v7 `added:` lines say "converted from P:206"; reasons are thin for a PO, acceptable for the conversion release) |
| B07-6 skill | read SKILL.md "Composed squads" | one inbox answer item with options per ID-and-choice; body explains rule, change and why, local text, consequences; `--resolve` passed back; apply without `--yes` first; upstream offered | pass |
| B07-8 legacy | `--check` and `--apply --yes` on a squad with only `process.md` | "not adopted: … run `squad-process adopt` first", exit 2, tree unchanged | pass |
| B07-9 semantic clash | see B07-1 | listed, not blocked | pass |
| B07-10 odd `installed_plugins.json` | 7 odd contents (`[]`, list entries, string entry, non-string path, `null`, invalid JSON) with HOME/CLAUDE_CONFIG_DIR pointed at them; ran `squad-start`, `squad-spawn --dry-run`, `squad-process compose`, `upgrade --check` | no traceback anywhere. Caveat: with the pin present none of these paths reads the installed file, so the specific read path is **not reachable black-box**; covered by the whitebox test | pass (limited) |
| Not covered here | AC 4 CI dry-run of template against all fixtures | QA whitebox | n/a |

Incident (mine, cleaned): one test run used the real `herdr` and opened a Manager tab `s-mgr-oddx`; I closed that tab (`herdr tab close`), `herdr agent list` shows none left. Rest of the run used a stub.
