# 04 Promotion: ADR 0031 and CONTEXT.md terms: evidence
sha: b2fc5f8
## Review
AC trace:
- AC1 | `head -8 docs/adr/0031-home-upgrade-mid-scope.md` (title, Status, Amends, Decision) | read
- AC2 | `git diff e728bb8..722b549 -- docs/adr/0016*` adds only the header line and a blank line | git diff
- AC3 | `git diff e728bb8..722b549 -- docs/adr/0030*` one line, ", until Chieu moves one (ADR 0031)" | git diff
- AC4 | `grep -n 'Pin move\|Plugin pin\|Process update' CONTEXT.md` (lines 123, 143, 151) | grep
- AC5 | claims match `bin/squadhomes.py`; QA whitebox checks each | read
- AC6 | `grep -rn 'between scopes only' CONTEXT.md docs/adr/0016* skills/` | grep
- AC7 | `git diff --stat e728bb8..722b549`: CONTEXT.md, two ADRs, one new ADR, 03's evidence; no code or test | git diff

## Behaviour
AC6 output: only `docs/adr/0016-...md:7` (the header exception, which quotes the sentence) and `:11` (the Decision line, kept).
`grep -rl 'between scopes only\|keep their runtime\|Plugin pin\|Process update' tests/` prints nothing, so no test reads the edited text.
`git diff --stat e728bb8..722b549`: CONTEXT.md 8, 0016 2, 0030 2, 0031 new 23 lines, plus 03's evidence.md.
Tests on the final tree (docs unchanged since; run with 06): `cd tests; python3 -m unittest test_windows_safe test_utf8_helpers test_instructions test_squadupgrade test_promotion_0_6_0 test_squad_spawn`: 200 tests, OK.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `head -8 docs/adr/0031-home-upgrade-mid-scope.md` | read docs/adr/0031 against promote.md section 1: same text |read ADR 0031: house shape ok |
| AC2 | `git diff e728bb8..722b549 -- docs/adr/0016*`: header lines only | git diff e728bb8 722b549 on ADR 0016: header lines only, Decision untouched |read: header line only |
| AC3 | `git diff e728bb8..722b549 -- docs/adr/0030*`: one line | git diff on ADR 0030: one line |read: one line |
| AC4 | grep of CONTEXT.md for the three terms: lines 123, 143, 151 | git diff on CONTEXT.md: Plugin pin, Process update, Pin move (Avoid: scope upgrade) match promote.md section 2 |read CONTEXT.md terms |
| AC5 | claims vs bin/squadhomes.py: for QA whitebox | read bin/squadhomes.py run(), gate, respawn, stranded, _edit_pin: each ADR claim holds (see qa-w.md) |FAIL: ADR 0031 Consequences bullet 1 says the skill still needs the new plugin; false since 05 (qa-b.md) |
| AC6 | grep `between scopes only`: only ADR 0016 lines 7, 11 | grep 'between scopes only' CONTEXT.md docs/adr/0016* skills/: ADR 0016 lines 7 and 11 only |n/a: QA whitebox |
| AC7 | `git diff --stat e728bb8..722b549`: docs only | git diff --stat e728bb8 722b549: docs only, no delete or move |n/a: QA whitebox |

## QA blackbox

### 04 QA blackbox on 722b549 (docs vs what the CLI does)
I read ADR 0031, the 0016 and 0030 header edits and the CONTEXT.md terms (Plugin pin, Process update, Pin move) and compared each claim with what I saw the CLI do in tickets 01, 02, 03, 05 and 06 (scratch squads, CLI output).

| Claim | Seen on the CLI | Result |
|---|---|---|
| `homes --check | --apply [--yes]` lists homes with pins; on yes rewrites only the `plugin:` line of each chosen home | diff of scope.md before/after: only the `plugin:` line (also goal.md) | pass |
| composes every role at the new pin, refuses (exit 2, nothing written) a home that does not compose | refused homes: exit 2, `refused <home> ... (deselect it with --only)`, squad listing unchanged (read refusal here, compose refusal in 01/02) | pass |
| asks each live agent to save notes, respawns it at once, the caller is told to respawn itself last | stub run: `PIN-MOVE` prompt per live agent, `caller mgr-g1: last step: ...` line | pass |
| an agent that does not settle is `pending` (exit 4), never killed | `pending tl-g1: ... notes.md is missing`, exit 4 | pass |
| other open homes are not offered; `homes --check` warns when one would no longer compose | lone scope not listed from a goal home; `will refuse spawn and respawn: scope solo: ...` line (ticket 01) | pass |
| moved home: one process-log row per home with the old pin | `Home goal g1 plugin <old> -> <new>` rows | pass |
| Consequences: "The target is plugin.pin, never the running plugin, so the tool works from a pinned runtime; **the skill still needs a session whose plugin is the new one for the squad upgrade itself**" | false since ticket 05: from a pinned 0.10.2 runtime `upgrade --check/--apply` print `using plugin 0.10.3 from <root> (known marketplace ...)` and run the newer plugin; the dialog worked end to end (03 and 05 evidence). The sentence also says nothing about the discovery or that only sessions pinned before 0.10.2 need a hand move | FAIL on 722b549, fixed in b2fc5f8 |
| ADR 0016 header, ADR 0030 line, CONTEXT.md Plugin pin / Process update / Pin move (`_Avoid_: scope upgrade`) | read: consistent with the CLI | pass |

Finding (breaks AC5 "every claim is true"): ADR 0031 Consequences, first bullet, second clause. Fix: replace it with the 05 behaviour, e.g. "From a Manager session pinned at 0.10.2 or later, `upgrade` and `homes` find the newest plugin (known marketplace checkout, else installed cache) and run it; sessions pinned before 0.10.2 move to 0.10.2 by hand (ticket 05)." If `promote.md` carries the same sentence, change it there too.

#### Re-check on b2fc5f8 (LC-3b)
`git diff 722b549..b2fc5f8 -- docs CONTEXT.md`: one line of ADR 0031 Consequences bullet 1, now "from a Manager session pinned at 0.10.2 or later, `upgrade` and `homes` find the newest plugin (known marketplace checkout, else installed cache) and run it; sessions pinned before 0.10.2 move to 0.10.2 by hand (ticket 05)". Matches what I saw in the 03 and 05 runs. Nothing else in the docs changed. Result: pass.

## QA whitebox

### QA whitebox 04 (docs 722b549): PASS

PROMO-8: edits match promote.md and contain nothing the scope did not decide.
- AC1-AC4, AC6, AC7: ADR 0031 and the CONTEXT.md Plugin pin, Process update and Pin move text match promote.md; ADR 0016 changes in the header only; ADR 0030 changes one line; `grep 'between scopes only'` hits only ADR 0016 lines 7 and 11; the diff is docs only.
- AC5, each claim vs bin/squadhomes.py: target is `plugin.pin` (run(): read_pin_file, materialise); compose gate over manager/team-lead/dev/team roles, exit 2 and nothing written when refused (gate, `bad`); only the first `plugin:` line is edited, all edits built before the first write (_edit_pin); respawn at once, the caller left out and told to respawn last (respawn_plan, respawn); a pending agent is listed, exit 4, never killed (respawn_one); other open homes are warned about in --check and never offered (stranded); one log row per home holds the old pin.
- test_old_language_inventory and test_process_writing: OK.

Follow-ups (not FAIL):
- ADR 0016 header wording follows the ticket's AC2 ("home move"), not promote.md section 3 ("pin move"). Same meaning.
- ADR 0031 Consequences says the skill "still needs a session whose plugin is the new one for the squad upgrade itself". Ticket 05 changed that: from a 0.10.2 session `upgrade` finds the newer plugin itself. Worth one line at the next doc touch.

#### Re-check b2fc5f8
PASS: one ADR 0031 line, matches ticket 05; follow-up 2 resolved.
