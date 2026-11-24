# Evidence: 10
sha: ecea181

## Behaviour

Code sha ecea181 (base 46d2f4b). Files: `bin/squad-usage`, `tests/test_squad_usage.py`. `bin/squadtranscript.py` needed no change.

- AC1 (fixture): `test_a_roster_session_without_transcript_falls_back_to_the_newest_spawn_session_with_one`: roster session has no transcript; spawn events of `ux` (two with transcripts, a newer one without, and a newer one of another agent with a transcript) → the row is 2 sessions, peak 50k, no "could not be told" footer, and `--sessions ux` lists both. `test_no_spawn_event_with_a_transcript_keeps_no_transcript_and_the_footer` keeps the base behaviour when no anchor exists. Red on base 46d2f4b (new test file against the base tree): 9 failures, including these two; green now.
- AC2 (fixture): `test_peak_ctx_is_the_newest_session_and_max_peak_the_largest`: sessions 331k then 61k → `peak ctx` 61k, `max peak` 331k.
- AC3: `python3 bin/squad-usage --help | grep -c 'max peak'` and `grep -c '1st act'` print (base 0, 0):
```
1
1
```
  `test_help_says_what_the_peak_and_first_action_columns_count` keeps it.
- AC4 (real data, this scope, plugin-ux-po-clarity: base "no transcript", footer "roster session not found"): `SCOPE_DIR=<po-clarity scope> python3 bin/squad-usage --sessions plugin-ux-po-clarity`:
```
session  peak ctx  turns  last turn
1        134k      30     2026-11-24 15:09
```
  Table rows from the same scope (cut to 110 columns):
```
agent                     model/effort              turns  peak ctx  max peak  last ctx  1st act  line  out   
```
- AC5: followups 08 is already `Status: wontfix` at base (46d2f4b); nothing to edit here.
- Optional `squad-respawn` change: not done. The respawn event is written before the new session exists, and `squad-spawn` logs no `spawn` event on a respawn (`SQUAD_RESPAWN=1`), so a second lazy respawn is still not covered; the Tech Lead may want a follow-up.
- Columns: `max peak` is inserted after `peak ctx`; nothing parses the table (reviewer grep of the repo without worktrees: only `tests/test_squad_usage.py` reads column indexes, updated).
- Tests (foreground, one file at a time, all OK): test_squad_usage 34, test_squadtranscript 3, test_squad_usage_hook 13, test_squad_manager_guard 25, test_session_lookup 16, test_squadboard_active 9, test_squad_respawn 34, test_squadruntime 74, test_crlf_squad_files 6, test_templates 8; SQ-10 trio: test_windows_safe 14, test_utf8_helpers 14, test_instructions 16.

## Review

Fresh sonnet/high subagent on `46d2f4b..17d70e8`; checks are in `## Checks`.
- Standards: no column-index reader of the table outside `tests/test_squad_usage.py` (grep without worktrees). One finding: the "other agent's events" case was not really tested (its session had no transcript, so it was skipped anyway). Fixed in the next commit: the other agent's spawn event is newest and has a transcript, so the agent filter matters.
- Spec: AC1 to AC4 met; design followed (spawn events only, newest with a transcript, footer only when no anchor). Optional `squad-respawn` change skipped, a second lazy respawn is not covered (see Behaviour).
- Bugs: none found (corrupt/missing/non-dict log line skipped, unreadable log gives none, an anchor without an `agent-name` record is still added). Note: after the fallback `peak ctx`/`last ctx` come from the older anchored session, as designed.

## Checks

| AC | Dev: test or capture | QA whitebox | QA blackbox |
|---|---|---|---|
| AC1 | `python3 -m unittest -q test_squad_usage` (34 OK); red on base: 9 failures | - | - |
| AC2 | `test_peak_ctx_is_the_newest_session_and_max_peak_the_largest` OK: 61k / 331k | - | - |
| AC3 | `squad-usage --help` piped to `grep -c 'max peak'` 1, to `grep -c '1st act'` 1 | - | - |
| AC4 | `SCOPE_DIR=<po-clarity> python3 bin/squad-usage --sessions plugin-ux-po-clarity` prints `1  134k  30  2026-11-24 15:09` | - | - |
| AC5 | `head -5 .scratch/plugin-followups/issues/08-usage-last-session.md`: `Status: wontfix` at base | - | - |

## Changelog line

squad-usage: an agent whose roster session has no transcript (after a lazy respawn) is found again through its newest `spawn` event, and the table shows `max peak`; why: the designer row read "no transcript" and `peak ctx` hid a 331k session behind a 61k one.
