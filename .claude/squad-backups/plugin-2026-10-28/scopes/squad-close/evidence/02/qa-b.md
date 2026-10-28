# QA blackbox 02 — commit 6ebcfbd (rule text, read against the behaviour seen in 01)
| AC | Saw | Result |
|---|---|---|
| 1 CLOSE-1 | "runs squad-close ... as its last action. The Manager stays; its $SCOPE_DIR moves, so it says everything first and is chat-only after. The PO ends it with `squad-retire <manager>`." Matches 01 (kept line, no pane close). | PASS |
| 2 CLOSE-2 | "retires the scope's agents except the Manager"; "closes the Manager's pane" and "Manager last" gone; "never the one it runs from or the closing scope's own pin, which the next close prunes". Matches 01 (pin kept, pruned by the later scope close). Does not say "while its Manager lives" literally; meaning is covered. | PASS |
| 3 CLOSE-4 | "moves the folder to goals/_done/ and keeps the goal Manager, chat-only until the PO runs squad-retire <manager>". Matches 01 goal run. | PASS |
| 4 CLOSE-5 | Behaviour statement true (01: all agents, Managers last, all runtimes pruned). Text was edited to add "retires every agent, the Managers last"; the AC says "unchanged" — wording added, no behaviour change. | PASS, flagged |
| 5 process.md | Closing lines 156-160 and lifetime row (Manager "Lives with the scope; stays, chat-only, after the close until the PO retires it") match 01. CLOSE-3b still true (goal Manager runs scope close, then respawns). `squad-process lint` exit 0, no output. Lint/rule-count tests not run by me (whitebox). | PASS |
Verdict: PASS.
