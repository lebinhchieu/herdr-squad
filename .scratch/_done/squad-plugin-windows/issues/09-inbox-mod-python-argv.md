# A The inbox mod runs `squad-inbox` through `python3`

Status: ready-for-agent
Type: task
Source: `.scratch/squad-plugin-windows/issue-po-inbox.md` section 1; ADR 0011 D6
Touches: `hooks/po-inbox/actions.ts`, `hooks/po-inbox/mod.test.ts`
Blocked by: none. Parallel with 10, 11, 12.

## What
The 3 `$.process.run` argv builds (`delivered`, `answer`, and the third at the `list` call) become `['python3', `${$.plugin.root}/bin/squad-inbox`, ...]`. A script with no extension cannot be spawned by argv on Windows (`ENOENT`).

## Technical AC (Tech Lead)
1. Every `$.process.run` argv in `actions.ts` starts `python3`, then the script path, then the subcommand and flags unchanged.
2. `mod.test.ts` line ~128 (`argv[0].endsWith('/bin/squad-inbox')`) is updated, and a test asserts the argv of all 3 calls (`list`, `answer`, `delivered`) as exact arrays.
3. No other file in `hooks/po-inbox/` changes; `bun`/`claude plugin test` as `tests/test_po_inbox_mod.py` runs it still passes.
4. Linux unchanged: `python3` is on PATH.

## Comments

### Tech Lead amendment (2026-10-17) — binding, replaces AC 1-3 where they differ
- **There are 4 `$.process.run` calls, not 3:** `list` (refresh), `delivered` (sendAndMark), `answer` (answerItem), `read` (markRead). All four change. Use one local helper `cliArgv(root, ...args)` returning `['python3', `${root}/bin/squad-inbox`, ...args]`.
- **TA1** `grep -n "process.run" hooks/po-inbox/*.ts` (non-test) shows only `cliArgv` callers; stdin, timeout, error text unchanged.
- **TA2** a new test asserts the raw argv of all four verbs as exact arrays (`list --json`; `delivered <id> --session <s>`; `answer <id> [--option k] --source pane`; `read <id>`). It fails on 59a8d1b.
- **TA3** other harnesses record argv with the same shape, so touches widens to the three harnesses that index `argv[1]`/`slice(1)`: `hooks/po-inbox/testkit.ts`, `ui.test.ts`, `item.test.ts` (plus `mod.test.ts`). In each harness drop the leading `python3` when recording/passing argv, so the ~70 existing assertions stay unchanged. Do not rewrite them. Nothing else in `hooks/po-inbox/` changes.
- **TA4** `claude plugin validate` clean; `tests/test_po_inbox_mod.py` and `test_po_inbox_contract.py` pass (do not edit them: ticket 12 owns them).
- **TA5** `$.plugin.root` with backslashes is not normalised (Python accepts a mixed path). Evidence states: the host's `$.process.run` resolving `python3` on Windows is not provable here; the PO's pane check (issue section 1) stays.
- **TA6 (QAW)** the fakes strip 2 argv items (`python3` and the script); no test may pass only because the verb stopped matching: the new test asserts verbs are reached (each verb's handler ran).
- **TA7 (QAW)** the harness code that drops or skips the leading `python3` throws if `argv[0] !== 'python3'`, so reverting one site to the bare script path fails every test that goes through it, not only the new argv test.
