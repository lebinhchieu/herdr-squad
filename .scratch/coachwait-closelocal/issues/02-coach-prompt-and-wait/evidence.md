# Evidence 02
sha: e75a519
## Behaviour
`squad-spawn` (stub herdr, `--dry-run`; the "composed mode needs a pin" line is the scratch squad lacking a pin, unrelated):

```
== token-coach, no --prompt
warning: token-coach c1 spawned without --prompt; an unbriefed agent sits idle (pass --prompt with its first message)
== token-coach --prompt hello      -> no warning
== manager, no --prompt            -> no warning
== real (non-dry) run, no --prompt -> same one warning, spawn continues
```
Rules: composed Manager rules contain ITER-6 (`--prompt "<text>"`, output paths, inputs, message back) and ITER-6c (never loop, sleep or poll; `herdr agent list` only after the idle window). `squad-process lint` passes. Tests: test_squad_spawn, test_retro_rules, test_sizes, test_process_citations, test_instructions OK.

## QA whitebox review

### 02 QA whitebox, sha e75a519 — PASS
- T1 ITER-6 one rule with --prompt, both output paths, inputs, message-back; ITER-6c (roles: manager) has no-loop/sleep/poll + herdr agent list after idle window ([MSG-8a] exists). lint=0; citations test OK.
- T2 ITER-7 unchanged, same file name/message; test asserts it.
- T3 bin/squad-spawn:66 one stderr line, role != manager && no prompt; exit/stdout unchanged; squad-respawn passes --prompt so no warning there. Tests cover dev/token-coach/qa-whitebox warn, manager/--prompt silent.
- T4 wording asserted in test_retro_rules; no golden diff needed (none changed); changelog entries added.
- T5 bash -n ok; diff = iterations.md, squad-spawn, 2 tests, changelog, ticket, evidence; squad-close untouched.
- T6 real stderr sample in evidence.md.
- I ran: test_squad_spawn test_retro_rules test_sizes test_process_citations test_processlint test_squadcompose = 192 OK.

## QA blackbox review

### QA blackbox 02 — sha e75a519 (clean `git archive` of the sha; scratch git repo, composed squad `sq` with pin; spawns via `squad-spawn ... --dry-run`, rules via `squad-process compose manager` / `lint`)

| AC | Did | Saw | Result |
|---|---|---|---|
| 1 spawn line carries --prompt | composed Manager rules, [ITER-6] | `squad-spawn token-coach <squad>-coach-<scope> --scope <scope> --prompt "<text>"` (`--goal` at goal close); prompt names scope+folder, size, exact output file `iterations/<n>.coach.md` or `coach/<goal>.coach.md`, "read `squad-usage`, `usage-events.jsonl`, earlier backlogs", "message the Manager with the file and the proposal count"; says without `--prompt` it starts idle | PASS |
| 2 wait, no polling | same rules, new [ITER-6c] right after ITER-6 | "do other work or end the turn and wait for the Coach's message; never loop, sleep or poll for the file. Run `herdr agent list` on its pane only when no message came after the 10-minute health-check idle window ([MSG-8a])" ; MSG-8a = 10 min no pane activity, matches | PASS |
| 3 warning | `squad-spawn <role> x --squad sq --scope s1 --dry-run` for dev, token-coach, qa-blackbox (no --prompt) / manager (no --prompt) / dev, token-coach with --prompt | no-prompt non-manager: exactly 1 stderr line `warning: <role> <name> spawned without --prompt; an unbriefed agent sits idle (pass --prompt with its first message)`, exit 0; manager and with-prompt: empty stderr, exit 0. Stdout of dev/token-coach/manager byte-identical to main (a0f7436) after path normalisation | PASS |
| 4 lint | `squad-process lint` (default and `--plugin-root <sha>`) | silent, exit 0; ITER-6 is one rule (ITER-6c is its own rule next to it, allowed by AC 2) | PASS |

Not observable here: real (non-dry) spawn actually sending the first message (needs herdr); dry-run only.
