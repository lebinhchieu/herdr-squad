# Evidence 02

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
