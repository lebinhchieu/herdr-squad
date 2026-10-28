# Trial protocol: Manager on Sonnet, QA/BA/TL effort medium

**Run the two drivers in the PO's next scopes through spawn overrides, one driver per scope, and call a driver "real" only after 3 of its scopes and 10 HANDINs summed over them, no escaped defect inside the escape window, returns not above the agreed tolerance and a net saving of 2% or more.** The PO signs off the tolerance and the denominator below before the first trial scope. **One escape makes the driver "not real" at once, at any n; over-limit returns do so only after 10 HANDINs.** No `agents/*.md` change is made by the trial; the PO changes defaults only after a "real" verdict.

## Overrides (no file edits)

| Driver | Override | Where it is set |
|---|---|---|
| D5 Manager Opus -> Sonnet | `squad-start "<text>" --model sonnet` (effort stays `medium`) | the PO starts the scope |
| D2 QA-side effort `high` -> `medium` | `squad-spawn <role> <name> --scope <s> --effort medium` for tech-lead, qa-whitebox, qa-blackbox, ba | the Manager spawns them |

- **One driver per scope, alternating** (scope A: D5, scope B: D2, ...). Both at once gives a verdict on the pair only, because the effect of each cannot be separated. If the PO wants both at once, the report says so and the verdict is for the pair.
- **Respawns keep the override only after ticket 06 is merged.** Until then run neither D2 nor D5: a cost-rule respawn silently returns the role (the Manager included) to its default. Ticket 06 covers `squad-start --model` too.
- **`squad-start --resume <name>` forgets the Manager's override unless the flags are repeated** (QAB's caveat on 06): a trial resumes with `--model sonnet` again, and the check below is repeated at every check-in.
- **Check the override took:** after spawning and at each check-in, `squad-usage` (ticket 05) shows `model/effort` per agent; the Manager writes the line into the iteration file. A scope whose roles do not show the override is not a trial scope.

## Baseline (AT-01, `audit.md` at ad3b4c7, total spend $297.17)

| What | Value |
|---|---|
| Manager on Opus | 856 messages, $40.54 (13.6%); at Sonnet $20.27, ceiling saving $20.27 (6.8%) |
| QA/BA/TL on `high` | output $26.25; at medium's 521/997 output ratio, ceiling $12.5 (4.2%) |
| Opus-manager scopes, FAIL / HANDIN (`type` field, deduped by `msg_id`) | board-flakes 2/16, refine-process 4/19, squad-tabs 13/29 = **19/64 = 0.30** |
| Sonnet-manager history | po-inbox 30/50 (one scope, not a baseline; AT-03 dropped) |

Both the share and the returns are re-measured on the trial scope with the same script (`scripts/audit.py`, same price table, `--until` set to the scope's close), never with a new method.

## What is measured, per trial scope

1. **Spend:** the scope's total $ and the driver's role $ (Manager, or tech-lead + qa-whitebox + qa-blackbox + ba), from `audit.py`, including subagents.
2. **Net saving** = (role $ the same tokens would cost at the baseline setting) - (role $ measured) - (extra-return cost). "Would cost" uses AT-01's price table and, for D2, the 521/997 output ratio. **Extra-return cost** = max(0, trial returns per HANDIN - 0.30) x trial HANDINs x mean $ per HANDIN cycle, where mean $ per HANDIN cycle = (dev + QA role $ of the trial scope) / its HANDINs. Both are models, not a measurement of a twin scope (causality is not measurable); the report says so.
   **Denominator (BA ruling, business-ac.md "Trial scopes (AT-05)" 1): the projection decides.** r = net saving / what the driver's role(s) would have cost at the baseline setting in the trial scopes (summed over the driver's scopes). Projected saving = r x the driver's share of AT-01's total ($297.17): D5 13.6%, D2 8.8%, fixed, not re-measured. "Real" needs projected >= 2%. Both r and the projected % are printed. Net saving <= 0 in the trial scopes' own terms is "not real" whatever the projection says.
3. **QA returns per HANDIN:** FAIL lines per HANDIN line, the same combined count as the 0.30 baseline (whitebox and blackbox FAILs added; also shown separately), deduped by `msg_id`, a resent HANDIN counted as a new one. Computed cumulatively over a driver's trial scopes.
4. **Escapes:** a defect found after a QA PASS against an AC or spec line that existed at the PASS (a new PO requirement or changed mind is not one; the trial scope's BA classifies a doubtful case, the Manager records it, the PO decides a dispute), found in the trial scope, from the PO's check-in answers and fix commits on a passed task. **Window:** from the PASS until the trial scope closes plus the next scope's first check-in. **The Manager of the trial scope records escapes** in the iteration file (`Escapes:` line, task ids) at close and again at that check-in. A "real" verdict cannot be issued before the window of the driver's last scope has ended. For D2 this is the quality measure; returns per HANDIN alone is not (a weaker QA returns fewer).
5. **Cost side of D5:** manager messages per task and respawns per scope.

## Stop rule and verdict

- **Tolerance: the BA accepts 0.45 as a stop limit only; the PO signs off, and 0.30 is the PO's stricter option.** Returns between 0.30 and 0.45 are already priced by the extra-return cost. Baseline returns per HANDIN by scope: 0.125 (board-flakes), 0.21 (refine-process), 0.45 (squad-tabs); pooled 0.30. The limit is **0.45** (1.5 x pooled, the top of the spread). At n=10 HANDINs returns cannot tell 0.30 from 0.45, so they are weak evidence: they can only stop a trial, never prove a driver on their own. A stricter limit (0.30, RS-3 "not higher") is the PO's option; it will stop most trials by noise.
- **not real (stop and revert, takes precedence over unproven):** one escape in the window (any n); or cumulative returns per HANDIN above the signed-off limit after at least 10 HANDINs of that driver (below 10 it is noise); or net saving <= 0 in the trial scopes' own terms. The PO decides the revert; no further trial scope for that driver.
- **Keep going** while neither fires, until the driver has **3 trial scopes and at least 10 HANDINs summed over them**.
- **real:** that n reached, the escape window of the last scope ended with zero escapes, returns at or under the limit, projected saving at or above 2%, and the PO accepts the tolerance. The PO then edits `agents/*.md` (role-instruction change).
- **minor:** same n, no stop, projected saving below 2%.
- **unproven:** fewer than 3 scopes or 10 HANDINs and no stop, or the override did not take. Never stretch the rule to get a verdict.
- The rule is fixed before the first trial scope; a change is a new commit with its reason.

The baseline is three Opus scopes of different sizes, not a twin of the trial scope; every verdict says so.

## Not in the trial
Haiku (AT-02: no go verdict), role-instruction edits, any other model or effort change.

## Open for the PO
Which scopes are trial scopes is the PO's call; the Manager of each says in the iteration file which driver it carries.
