# Tech Lead ANSWER to T1 (architecture.md section 9)

**Verdict: feasible, with 4 changes (A to D) and 2 additions (E, F).** Checked by reading code and timing `effective_rules`; nothing built.

## Per item
| # | Verdict | Notes |
|---|---|---|
| 1 duty-fact table | OK | 13 rows (not 12). Pure data in `squadrules.DUTIES` plus `read_home`. `team_from_size` and the chain resolver are ~60 lines. Keep `qa` (full/light) in `scope.md`; the table does not replace it (say so in section 2, the template keeps `qa:`) |
| 2 lint | OK | Define it exactly: at most one key from `DUTIES` + `{ba, team-lead, tech-lead, qa-whitebox}`; any of `goal, qa, design, architecture, qa-b` extra (these three are presence keys derived from the team, so they count as orthogonal). Existing `size in S, M and design = yes` shape maps cleanly. ~15 lines in `_conditions`/lint |
| 3 `squad-process team` | OK | Subcommand in `squadrules_cli.py`. Python start ~60 ms per call; fine in `squad-spawn` (once per spawn). In `squad-log-message` call it only inside `third_return` (FAIL records only), and on any error fall back to "Manager" (the hook already means "any problem: no notice"). Output: `--has ROLE` exits 0/1; plain `team` prints the comma list or `none`/`undecided`. The shim lives in this one function |
| 4 `squad-team` | OK with change A | Before/after compose per roster role with fixed `--now`/`--agent`, compare. Composing needs `effective_rules` once per call (about 3 ms measured), so about 10 roles = under 100 ms |
| 5 128-set sweeps | OK with change B | Measured `effective_rules` at about 3 ms for 342 rules. Dev sweep 128 x goal x qa = 512 composes, a few seconds; the no-orphan sweep over all roles filters preloaded rules with facts only, under a second. Replace `test_dev_rules_size`'s subprocess-per-combo with in-process compose |
| 6 legacy shim + converter | OK with change C | Shim and converter share `team_from_size`; first token of `size:`, `qa-b:`, `design:`, `architecture:` as `squad-close` already does. Blank `size:` maps to `undecided`, as an empty size does today |

## Changes
**A. Respawn diff must ignore the header.** The header prints `team:` and a `composed:` stamp, so any team change would differ in every role and `squad-team` would list all of them. Compare the `rules:` ID line, the rule bodies and (only for the three index roles) the `duties:` line; drop `team:`, `composed:`, `agent:`. Also keep `team:` out of the Developer header: it saves bytes under 5 KiB and avoids a stale team line in a Dev that rightly does not respawn.

**B. Make the sweeps cheap by design.** Split `compose()` into load (once) and `choose(rules, role, facts)` (pure). The 128-set tests and `squad-team` call the pure part. No other change to `compose`.

**C. Pin integrity: the running engine must not meet old rule files.** `squad-spawn:159` runs the *running* plugin's `squad-process compose` with `--plugin-root "$runtime"` (pinned rule files, current engine). Inside a pinned scope, roles have `PATH=<runtime>/bin`, so they use the pinned engine; but a spawn or respawn from the PO's own shell, `squad-close`, `squad-report` and `squad-process upgrade` use the new engine against 0.5.x rule files that still say `when: size`. After the cutover the new engine rejects those files (compose exit 2) in any open pinned scope. Fix: in composed mode `squad-spawn` and `squad-respawn` call `$runtime/bin/squad-process compose` (the pin's own engine) after building the runtime. One line each, plus a test with a pinned fixture runtime. Without it, "pinned scopes are untouched" in section 7 is false for PO-shell spawns. The `squad-log-message` hook and report read `scope.md` of pinned scopes with the new code, so they keep the `size:` shim (shim removal is later, as planned).

**D. Keep every task green: transitional engine.** The architecture's constraint 1 (vocabulary first, then rule files) breaks the suite if T1 removes `size` while 201 rule lines still use it. Order instead: T1 adds presence and duty keys while `WHEN_KEYS` still accepts `size`; tasks 2 to n retarget rule files by group (disjoint files, parallel Developers); the last engine task removes `size` from `WHEN_KEYS`, adds the lint, deletes the transitional path. Nothing ships between tasks, so there is no released half-state (I6 holds). Add this to section 6.

## Additions
**E. Dev cap and the worst set.** "No optional role" is the likely worst set for the Developer text (it carries every duty). Today's worst is 5443 B (S + design + goal + architecture). Expect a trimming task: move 2 to 3 Dev rules to `aware:`/on demand. Plan for it in the Dev-rules task; the cap does not move.

**F. Task shape I will design inside (for the Team Lead).** T1 engine and `DUTIES` (transitional); T2 `squad-process team`, shim, `team_from_size`, converter in `squadadopt`; T3 `squad-spawn`/`squad-respawn` pin engine, spawn gate, `squad-start`, `squad-log-message`; T4 to T6 rule files by group (sizes/who/starting/promotion; lifecycle/review/evidence/suites; the rest) plus rewritten tests; T7 report and rollup; T8 `squad-team`; T9 remove `size`, lint, Dev-cap sweep; T10 promotion (ADR 0018, glossary, README, changelog, `_removed.md`, snapshot, 0.6.0). Files do not overlap across T4 to T6. `squad-close` conflicts land in T4 to T6: rebase first.

Not an irreversible choice of mine; the PO items I1 to I8 stay as you list them. I agree with the recommendations.
