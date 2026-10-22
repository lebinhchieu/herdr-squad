# Evidence: 12 a ledger instead of copies; the 3rd return raises itself

**`squad-ledger` prints every task's state from `messages.jsonl`; HANDIN/PASS/FAIL no longer copy the Team Lead; the hook tells the sender of the first FAIL on a task's 3rd failing sha to send `BLOCKED NN: 3 returns`. Harness green.**

Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_ledger test_squad_log_message test_task_id_rule test_windows_safe test_dev_rules_size test_pod_contact_routes test_instructions test_processlint test_process_conversion` → OK.

## Behaviour

- **AC1 ledger** `LedgerTest.test_json_matches_expected`: task 03 (HANDIN A, FAIL x2 on A, HANDIN B, PASS x2) → sha B, both PASS, 1 return, 2 FAIL messages; task 04 (3 shas, FAIL on each) → 3 returns, the open BLOCKED, 2 ASK rounds. `--task 4` matches `04`; table test pins the columns. A DECISION closes BLOCKED and resets rounds; an ANSWER does not close a BLOCKED.
- **Row shape** every row has `task, sha, branch, handin_from, verdicts, returns, fail_messages, blocked, ask_rounds`; `null` when empty. A FAIL before any HANDIN is one return on an anonymous sha; shas compare by prefix; `3` and `03` are one row. Run read-only on this scope's live log: `ledger-live.txt`.
- **AC2 task IDs** `test_bare_number_ids_after_the_type`: `HANDIN 03:`→03, `HANDIN SET-13:`→SET-13, `FAIL 3:`→3, `STATUS: building SET-01`→SET-01, text with no ID→null.
- **AC3 notice** `NoticeTest`: fires once, on the first FAIL of the 3rd failing sha; not on the 2nd checker's FAIL on that sha, not on the 1st/2nd sha, not on a 4th; PASS never resets; an earlier sha failed again is not new; S names the Manager ([LC-7a]), M/L the Team Lead ([LC-7b]); two FAILs sent together on the 3rd sha → one notice (computed under the log's flock, from the log including the new record).
- **AC4 exit 0** forced failures: no `jq` on PATH, bad payload, log path unreadable (a directory) → exit 0, empty stdout.
- **Delivery path, live.** Headless `claude -p` with a PostToolUse hook on matcher `SendMessage` printing `{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"CANARY-9902 ..."}}`: (probe: [probe/run.md](probe/run.md), hook `probe/hook.sh`, settings `probe/settings.json`) the model quotes it back ("PostToolUse:SendMessage hook additional context: CANARY-9902..."). Same for `Bash`. So the notice reaches the sender through `additionalContext`; the hook still exits 0.
- **Rules.** `grep -rn "copy the Team Lead" templates agents` → none. Edited: REV-12, REV-13b, LC-7a, LC-7b, LC-17, MSG-19, NOTE-3, ITER-3 (returns, passed shas from `squad-ledger`). MSG-3 unchanged (MSG-2 already says the ID follows the type; dev cap).
- **Developer rules size**: max over size x design x goal = 5106 B before and after (cap 5120). REV-13b shrinks M/L by 24 B; MSG-3 untouched.
- Hash note: rules REV-12, REV-13b, LC-7a, LC-7b, LC-17, MSG-19, NOTE-3, ITER-3 have new hashes (unreleased, by design).

- **Return 1 fixes.** Hook reads the log with `jq -R 'fromjson?'` so garbage lines don't stop the notice; an `evidence sha` HANDIN no longer replaces the ledger's current sha/verdicts (ledger and hook); tests: `test_garbage_lines_in_log_do_not_stop_notice`, `test_evidence_handin_*`; `test_live_log_read_only` asserts mtime unchanged.

## QA whitebox

### QA whitebox 12 (ledger): FAIL @ 8d54ebd

Ran (detached worktree): `test_squad_ledger test_squad_log_message test_task_id_rule test_squadreport_tasks test_windows_safe test_dev_rules_size test_pod_contact_routes` = 69 OK. jq 1.7 here. Diff 4901cab..8d54ebd reviewed. Rules edits (REV-12, REV-13b, LC-7a/7b, LC-17, MSG-19, NOTE-3, ITER-3) match the ticket; no "copy the Team Lead" left outside `history/`. Task-ID regex, key normalisation (3 = 03), prefix shas, anonymous FAIL, near-simultaneous FAILs, exit-0 forced failures: tests exist and I read them.

#### Findings
1. **Notice dies on any malformed line in `messages.jsonl`.** `bin/squad-log-message` `third_return`: `jq -rn --slurpfile all "$log"` fails on the first non-JSON line, `|| notice=` swallows it, so no notice ever fires. Not hypothetical: this scope's live `messages.jsonl` has 14 non-JSON lines (lines 1-14, tool-output text) and `squad-ledger` skips them while the hook does not. Repro: `printf 'garbage line\n\n' > $SQUAD_DIR/messages.jsonl`, then send HANDIN 05 / FAIL 05 for three shas: the same sequence on a clean log prints the notice, on the garbage log prints nothing (both rc 0). Would pass: read the log as `jq -R 'fromjson? | select(type=="object")'` (slurped) so the hook and the ledger agree; test with a garbage line AND a valid non-object line (`3`) in the log; the notice still fires on the 3rd failing sha.
2. **An evidence HANDIN erases the passed sha from the ledger.** `squadledger.py:build` takes every HANDIN with a sha as the new current sha and gives it empty verdicts. EVID-2b has the Developer send `HANDIN <task>: evidence sha <sha>` after both QAs passed, so the row then reads `sha=<evidence sha> verdicts=null`. ITER-3 now says the Team Lead takes "each task's final passed sha and the checkers that passed it" from `squad-ledger`: it gets the wrong sha and no checkers. Repro: HANDIN 05 commit aaaaaaa1; PASS qaw; PASS qab; HANDIN 05 "evidence sha bbbbbbb2" → `squad-ledger` prints `05 bbbbbbb2 - ...`. Would pass: an `evidence sha` HANDIN (to the Tech Lead) does not replace the current sha / verdicts (and does not move the hook's current sha either), or the row also carries `passed_sha` + its checkers; add the test.
3. **Delivery path not reproducible from the evidence.** `evidence.md` says a headless `claude -p` probe showed `additionalContext` reaches the model, but neither the probe command nor its output is in the evidence folder, and I could not re-run it (a nested `claude -p` is refused in my session). Would pass: save the probe (hook script, settings, command, model's quoted reply) under `12-…evidence/` and link it from `## Behaviour`; I read it, no re-run needed.
4. (minor, fold in) `test_live_log_read_only` captures `before` mtime and never asserts it; assert unchanged.

#### Live data
`squad-ledger --json` on this scope's live log (read-only): 4 rows, all 9 keys on every row, `null` for empty. Only old-form IDs (FILE-11, SIZE-19, SIZE-20, SIZE-2) show: 44 of 61 records predate the hook change and carry `task: null` (bare numbers). Accepted: no back-fill is asked.

#### Incident (mine)
My shell had `SCOPE_DIR` set; probing the hook with `SQUAD_DIR=/tmp/...` wrote 24 fake records (`HANDIN 05` / `FAIL 05`, from `dev`/`qaw`, "commit aaaaaaa/bbbbbbb/ccccccc") onto lines 76-99 (the end) of the live `scopes/process-fixes/messages.jsonl`. Removing them was refused by the auto-mode classifier; they are all `"task":"05"` and need deleting by the Manager (or PO). They would show as a task `05` with 3 returns in `squad-ledger`.

#### Re-check 8d54ebd..054bf37: PASS
F1: hook reads the log with `jq -R fromjson? | select(type=="object")`; my repro (garbage, `3`, `[1]`, truncated line) now gives the notice once on the 3rd failing sha. F2: `evidence sha` HANDIN skipped in ledger and hook; repro row keeps aaaaaaa1 with qab/qaw PASS. F3: probe hook/settings/run.md in the evidence folder (matcher `Bash`, same `additionalContext` mechanism the SendMessage hook uses; accepted). F4: mtime asserted. 72 tests OK (7 files). Accepted: probe ran on a Bash matcher, not SendMessage.
Still open from the earlier incident: my 24 fake task-05 records in the live log (Manager/PO to delete lines 76-99).

## QA blackbox

### QA-b 12 (sha 8d54ebd, branch squad/plugin/process-fixes/plugin-dev-pf-2)
Method: scratch scope; real `bin/squad-log-message` fed PostToolUse JSON per message; `bin/squad-ledger` run on the resulting `messages.jsonl`; `squad-process compose` for 9 roles × S/M/L vs `git archive 4901cab`. No code read.

| AC | What I did | Saw | Result |
| --- | --- | --- | --- |
| 1 | Task 03: HANDIN aaa1111, FAIL from qaw+qab, HANDIN bbb2222, PASS both. Task 04: HANDIN+FAIL on 3 shas, BLOCKED | `03 bbb2222 b qab PASS, qaw PASS returns 1 blocked 0`; `04 c000003 - qaw FAIL returns 3 blocked 1` | pass |
| 2 | `--task 04 --json` | keys task, sha, branch, handin_from, verdicts, returns (3), fail_messages (3), blocked (list), ask_rounds. Same facts | pass |
| 3 | 3rd failing sha, 1st FAIL: tool result `task 04 has 3 returns: also send BLOCKED 04: 3 returns to Team Lead [LC-7b]`. Then: 2nd checker FAIL on same sha, PASS after, 4th sha FAIL, 1st/2nd sha FAILs: no notice. Task 07 (fail, pass+fail, 3rd sha): one notice only. S scope: notice says Manager [LC-7a]. Task with 2 failing shas: none | | pass |
| 4 | Two FAILs on one sha (task 03, 08) | returns 1 / 2, no notice | pass |
| 5 | `HANDIN 03:`, `HANDIN SET-13:`, `FAIL 3:`, text with no ID | task 03 / SET-13 / 3 / null; hook rc 0 on every call, also with invalid JSON, `{}`, empty stdin, no env; ledger on empty home: "no tasks", rc 0 | pass |
| 6 | Compose dev, qa-whitebox, qa-blackbox, team-lead, M, vs 4901cab | Dev HANDIN: "copy the Team Lead" removed; QA: "PASS or FAIL to the Developer only" (was "copy the Team Lead"); Team Lead: "go to the Developer and the checkers only; you are not copied. Run squad-ledger ... at health checks and at iteration end", plus the move-state and respawn lines. No "copy the Team Lead" left in any role at S/M/L | pass (wording is "Developer only" in QA rules, not the literal "and the checkers only"; same meaning) |
| 7 | Team Lead summary rule | "task's final passed sha, the checkers that passed it and the returns per task (all three from `squad-ledger`)"; 3-returns rule says a return is a handed-in sha with a FAIL | pass |
| extra | ASK rounds | q1/a1,q2/a2,q3 → 3; after DECISION → 0; q4/a4 with tl (q5 to another agent unanswered) → 1 | pass |

Non-blocking: the ruling says the ledger "also lists the FAIL messages"; the table and JSON give only a count (`fail_messages: 3`), not the texts.

Verdict: PASS 12 on 8d54ebd.

#### Re-check 054bf37 (diff check 8d54ebd..054bf37)
Scratch scope, real hook + ledger.
| Check | Saw | Result |
| --- | --- | --- |
| `HANDIN 03: evidence sha bbb2222` after both PASS on aaa1111 | ledger keeps sha aaa1111, `qab PASS, qaw PASS`, returns 0 | pass |
| non-JSON and broken lines appended to `messages.jsonl` | ledger still prints the same table, rc 0 | pass |
| 3 failing shas with garbage lines present, then evidence HANDIN | notice `task 04 has 3 returns: also send BLOCKED 04: 3 returns to Team Lead [LC-7b]` once; ledger sha c000003, returns 3 | pass |
| real `diff check aaa1111..eee5555` HANDIN | ledger moves to eee5555, verdicts cleared | pass |

Verdict: PASS 12 on 054bf37.
