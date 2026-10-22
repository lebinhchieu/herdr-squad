# 02 evidence

## Behaviour
Rule text now matches 01: scope/goal close keep the Manager (chat-only after, PO ends it with `squad-retire <manager>`); squad close retires all, Managers last.
Changed: `closing.md` CLOSE-1/2/4/5; `process.md` Closing section + lifetime row (also `process/starting.md` row, same table); `bin/squad-migrate` comment; changelog v7 `retargeted` (CLOSE-1/2/4/5, START-5; required by test_sizes); `history/process-v6.md` re-copied from the template (test_process_history: snapshot == template). CLOSE-3a/3b/3c untouched and still true (goal Manager respawns itself after `--scope`).

## Lint
`bin/squad-process lint`: before: rc 0, silent. After: rc 0, silent (word-limit failures at 61/73/67 words fixed on the way).

## Stale-wording grep (templates README CONTEXT docs skills agents hooks bin)
Fixed: closing.md, process.md, process/starting.md, bin/squad-migrate. Left alone: `skills/squad-process-update/history/process-v1..v5.md` (frozen snapshots); README:46 and docs/adr/0005 (no claim about the Manager ending); `starting.md`/`process.md` "Manager is gone" in `--resume` (a Manager that died, unrelated).

## Tests
test_process_history, test_process_writing, test_process_citations, test_pod_rules_process, test_sizes, test_processlint, test_templates, test_dev_rules_size, test_suite_rules_process, test_squadprocess, test_squadrules, test_squadcompose: 251 OK. Run from `tests/` (`rulesview` import). `promote.md`: none.

## QA whitebox

### QA whitebox 02 — PASS on 6ebcfbd (final sha of the scope)
Checked: diff 3ffabe7..6ebcfbd vs tasks/02.md T1-T6. closing.md CLOSE-1/2/4/5, process.md Closing + lifetime row, starting.md START-5 row, bin/squad-migrate comment (my carry-over), changelog v7 + history/process-v6.md (both forced by test_sizes / test_process_history; accepted). Wording matches 01 (scope/goal keep Manager, chat-only after, `squad-retire <manager>`; squad close retires all, Managers last). CLOSE-3a/b/c untouched, still true. Grep for stale wording in templates/README/CONTEXT/docs/skills/agents/hooks/bin: only frozen history v1-v5 and unrelated `--resume` "Manager is gone" remain. `bin/squad-process lint` rc 0. promote.md: none needed (no lasting business rule or glossary term; behaviour is in the process rules themselves).

### Full suite (SUITE-1b/3b) on 6ebcfbd, clean=yes: FAILED, receipt evidence/suite/suite-default.txt
Two files fail: test_qab_optional (54 subtests, `test_every_role_matches_the_4901cab_golden`) and test_squadinbox (`test_no_pyc`).
Both fail identically on the scope base 5adfc45 (run from tests/: 68 tests, failures=55 = 54 golden + 1 pyc). Not caused by this scope; no task is returned (SUITE-5b needs the failing files to be the task's).

## QA blackbox

### QA blackbox 02 — commit 6ebcfbd (rule text, read against the behaviour seen in 01)
| AC | Saw | Result |
|---|---|---|
| 1 CLOSE-1 | "runs squad-close ... as its last action. The Manager stays; its $SCOPE_DIR moves, so it says everything first and is chat-only after. The PO ends it with `squad-retire <manager>`." Matches 01 (kept line, no pane close). | PASS |
| 2 CLOSE-2 | "retires the scope's agents except the Manager"; "closes the Manager's pane" and "Manager last" gone; "never the one it runs from or the closing scope's own pin, which the next close prunes". Matches 01 (pin kept, pruned by the later scope close). Does not say "while its Manager lives" literally; meaning is covered. | PASS |
| 3 CLOSE-4 | "moves the folder to goals/_done/ and keeps the goal Manager, chat-only until the PO runs squad-retire <manager>". Matches 01 goal run. | PASS |
| 4 CLOSE-5 | Behaviour statement true (01: all agents, Managers last, all runtimes pruned). Text was edited to add "retires every agent, the Managers last"; the AC says "unchanged" — wording added, no behaviour change. | PASS, flagged |
| 5 process.md | Closing lines 156-160 and lifetime row (Manager "Lives with the scope; stays, chat-only, after the close until the PO retires it") match 01. CLOSE-3b still true (goal Manager runs scope close, then respawns). `squad-process lint` exit 0, no output. Lint/rule-count tests not run by me (whitebox). | PASS |
Verdict: PASS.
