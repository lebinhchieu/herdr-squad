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
