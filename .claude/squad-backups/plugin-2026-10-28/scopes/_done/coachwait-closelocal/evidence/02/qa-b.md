# QA blackbox 02 — sha e75a519 (clean `git archive` of the sha; scratch git repo, composed squad `sq` with pin; spawns via `squad-spawn ... --dry-run`, rules via `squad-process compose manager` / `lint`)

| AC | Did | Saw | Result |
|---|---|---|---|
| 1 spawn line carries --prompt | composed Manager rules, [ITER-6] | `squad-spawn token-coach <squad>-coach-<scope> --scope <scope> --prompt "<text>"` (`--goal` at goal close); prompt names scope+folder, size, exact output file `iterations/<n>.coach.md` or `coach/<goal>.coach.md`, "read `squad-usage`, `usage-events.jsonl`, earlier backlogs", "message the Manager with the file and the proposal count"; says without `--prompt` it starts idle | PASS |
| 2 wait, no polling | same rules, new [ITER-6c] right after ITER-6 | "do other work or end the turn and wait for the Coach's message; never loop, sleep or poll for the file. Run `herdr agent list` on its pane only when no message came after the 10-minute health-check idle window ([MSG-8a])" ; MSG-8a = 10 min no pane activity, matches | PASS |
| 3 warning | `squad-spawn <role> x --squad sq --scope s1 --dry-run` for dev, token-coach, qa-blackbox (no --prompt) / manager (no --prompt) / dev, token-coach with --prompt | no-prompt non-manager: exactly 1 stderr line `warning: <role> <name> spawned without --prompt; an unbriefed agent sits idle (pass --prompt with its first message)`, exit 0; manager and with-prompt: empty stderr, exit 0. Stdout of dev/token-coach/manager byte-identical to main (a0f7436) after path normalisation | PASS |
| 4 lint | `squad-process lint` (default and `--plugin-root <sha>`) | silent, exit 0; ITER-6 is one rule (ITER-6c is its own rule next to it, allowed by AC 2) | PASS |

Not observable here: real (non-dry) spawn actually sending the first message (needs herdr); dry-run only.
