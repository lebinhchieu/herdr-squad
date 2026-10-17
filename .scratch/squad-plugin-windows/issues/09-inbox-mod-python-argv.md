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
