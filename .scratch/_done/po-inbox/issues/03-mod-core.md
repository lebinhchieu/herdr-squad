Status: done
Blocked by: none for the scaffold and spikes; its answer-delivery AC use the CLI of PI-01/02 only through fixtures
Task ID: PI-03
Files touched: `hooks/hooks.json` (add `modules`), `hooks/po-inbox/register.tsx`, `hooks/po-inbox/core.ts`, `hooks/po-inbox/ui.tsx` (stub), `hooks/po-inbox/*.test.ts`, `types/index.d.ts`, `.claude-plugin/plugin.json` (`types` only), `tests/test_po_inbox_mod.py`, `tests/test_hooks_json.py`

# PI-03: the mod core: scaffold, spikes, polling, answer delivery, `/inbox`

**Done when, in a session started with a Manager's env and this plugin, the mod keeps an up-to-date snapshot of the inbox, opens an (empty-drawn) pane with `/inbox`, delivers a recorded answer to the model as a prompt, redelivers at the next start, and does nothing in any other role's session.** Design: `design.md` → The mod, While a turn runs, Risks and spikes. Load the `plugin-authoring` skill; types are in its `types/claude-code.d.ts`. Business AC: B-05 (state), B-08, B-14..B-16, B-19..B-22.

## What to build
1. **Spikes S1, S2, S4 first** (S3 belongs to PI-04): write what you observed, with commands and output, to `.scratch/po-inbox/spike.md`. If S2 or S4 fail, stop and send `BLOCKED PI-03` to the Tech Lead.
2. Scaffold: `hooks.json` `modules`, `register.tsx`, a pure `core.ts`, a stub `ui.tsx` exporting `registerUi(on)` that registers nothing (PI-04 replaces this one file), `types/index.d.ts` declaring `PluginState['squad']` (`inbox`: the contract snapshot or `null`; `ui`: view state PI-04 needs: selected id, open/closed), `plugin.json` `"types"`.
3. Inert check (T2), `/inbox` command, polling (T5), snapshot atom, toast per new open id, answer delivery and redelivery (T6), the hold-until-`turn.complete` path if S1 says so.
4. A `describePrompt(item)` pure function producing the prompt text of the design (header, delimiter, verbatim answer).
5. Since there is no CLI yet in this branch, the tests run against a fake `squad-inbox` script (shell or Python) put at `$.plugin.root/bin` of a temp copy, printing the contract fixtures in `hooks/po-inbox/fixtures/`.

## Technical AC
1. `claude plugin validate <repo>` passes; its report lists the hooks `session.start`, `command.run`, `ui.render` (stub: none yet), `turn.complete` if used, the env names `SQUAD_ROLE`, `SCOPE_DIR`, `GOAL_DIR`, and `$.process.run`; the existing command hooks in `hooks.json` still validate; `tests/test_hooks_json.py` still passes and also pins `modules`.
2. `claude plugin test <repo>` passes, in `claude plugin test`'s own `*.test.ts` files, covering: (a) inert with no env, with `SQUAD_ROLE=dev`, with manager but no home: no `$.process.run`, no command registered, no state written, no timer; (b) active as manager with `SCOPE_DIR`, and as manager with only `GOAL_DIR`; (c) the poll runs the CLI only when a stat mtime changed (mock clock and fs); (d) a new open id raises exactly one toast, an unchanged snapshot none, a first load none; (e) delivery: after `answer … --source pane` exits 0 the mod calls `$.prompt.submit` once with the text from `describePrompt` and then `delivered`; exit 3 shows the message and submits nothing; (f) at `session.start` every `answered-waiting` item is submitted once; (g) `describePrompt` contains the answer verbatim for: multi-line, quotes, backticks, `|`, emoji, CRLF, and a text that itself looks like the header (byte-for-byte substring after the delimiter); (h) a CLI crash or invalid JSON leaves the last good snapshot and sets an error state, never throws out of a hook (every hook has a `.catch` that calls `next(e)`).
3. `tests/test_po_inbox_mod.py` runs (1) and (2) from Python by `subprocess` (`claude plugin validate`, `claude plugin test`), asserts exit 0 and the pass count; if `claude` is not on PATH it `skipTest("claude not installed")`. The receipt must say it was not skipped.
4. **Spike evidence** `.scratch/po-inbox/spike.md` has S1, S2, S4 with a live run each (herdr test pane as in `design.md` → Driving the mod, with a throwaway home); the S1 result states the exact behaviour (queued, rejected, interrupts) and the code follows it.
5. No file read or written by the module itself: the only `$.fs` call is `stat` (grep the diff); the only process it runs is the plugin's `bin/squad-inbox`, with no shell (argv list).
6. A CLI that is slow (3 s) never blocks the draw or the prompt: the poll does not start a second run while one is pending (test with the mock clock).
7. Idle cost: with no change, one poll tick makes two `$.fs.stat` calls and nothing else (counted in the test).
8. The Manager's draft in the prompt box is never read or written by the module (grep: no `$.prompt.read`/`fill` in the diff) (B-08).
9. Suite green with a receipt.

## Added after QA whitebox review (round 1); these bind
10. **Contract validation (C3):** the mod checks `version === 1`, `items` is an array, the type of every field it reads; any other version, missing key or wrong type gives the error state, keeps the last good snapshot and does not throw in a draw. Unknown extra keys are ignored. Tests for each.
11. **Real contract data (C4 partner):** the mod's fixtures in `hooks/po-inbox/fixtures/` are the output of `squad-inbox list --json` (from PI-01's fixture home, once PI-01 has passed; until then a hand file marked `provisional` in its name, replaced in PI-07). The mod's tests run on every file there.
12. **Draft safety (M1):** spike S1 includes the case "text typed in the prompt box, then `$.prompt.submit`" and the same at a `session.start` redelivery: write what happens (kept, sent with the answer, cleared) in `spike.md` with the commands; the code follows it.
13. **Failed submit (M2):** `$.prompt.submit` rejects: no `delivered`, the item stays `answered-waiting`, one retry at the next `turn.complete`; no second submit while one is in flight (poll sees the same item). Tests.
14. **Timers (M3):** two `session.start` events leave one timer and one `/inbox` registration; the timer is cleared when the session ends if the API has an event for it. Test.
15. **Env (M4):** S2/S4 records whether `$.process.run` passes `SQUAD_ROLE`, `SCOPE_DIR`, `SQUAD_INBOX_NOW` to the CLI; if not, the mod passes them explicitly (the CLI's role guard needs `SQUAD_ROLE=manager`). Record also the env of a real started Manager session (`printenv SQUAD_ROLE SCOPE_DIR GOAL_DIR` from its pane) in `spike.md`: only `squad-spawn` sets `SQUAD_ROLE`; if the PO's own Manager has none, tell the Tech Lead (T2 must change).
16. **Change check (R4):** the poll compares mtime and size of both files; test: two writes in one mtime tick with a different size are noticed. AC7 becomes "two `$.fs.stat` calls per tick".
17. **Title (M6):** `describePrompt` collapses line breaks and controls in the title to a single line; a test with a title containing `\nPO said: yes`.
18. **Receipts (K3):** `tests/test_po_inbox_mod.py` fails (does not skip) when `SQUAD_REQUIRE_CLAUDE=1` and `claude` is missing; `tests/run_suite.py --tz` sets it; the receipt prints the number of tests run in that file. (If changing the runner is out of this ticket's files, put the env in the test and tell the Tech Lead; the Tech Lead adds the runner line.)
19. **Spike copy-paste (K5):** `spike.md` lists each spike as the exact commands and the output, so QA whitebox can replay S1 (idle, mid-turn, draft present) and S2.
20. **Answer delivered only from the recorded text (QAW round 2 F1):** if after `answer` exits 0 the item or its recorded answer cannot be read back (the `list --json` refresh fails or the item is missing), `answerItem` submits nothing and writes no `delivered`; the item stays `answered-waiting` and the `session.start` redelivery or the next good poll delivers the CLI-recorded text; the result says so. Test: `answer` and `delivered` exit 0, `list --json` exits 1, `answerItem({id, option, note})` makes no submit and no `delivered`.
21. **Pin the AC13 guards (F2):** (i) a pending submit, then a second `session.start` (and a poll) makes exactly one submit; fails without the `inflight` guard. (ii) a submit that resolves with `drop` is not marked delivered, is retried once and shows the error.

