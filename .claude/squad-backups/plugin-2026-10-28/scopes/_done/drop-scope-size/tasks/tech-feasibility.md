# Tech Lead: feasibility facts for architecture.md (drop-scope-size)

Read from code at main 2949573 (0.5.2). Verified by reading, not run. Pointers are file:line.

## Where `size` is read
| Place | Use | Effect of dropping |
|---|---|---|
| `bin/squadrules.py:25` `WHEN_KEYS["size"]` | valid `when:` key; unknown key/value raises `ValueError` | every rule with `when: size...` fails lint and compose until rewritten: hard cutover, no half-state |
| `templates/squad/process/*.md` | 201 `when:` lines with `size` in 17 of 20 files, 342 rules total | one mechanical rewrite pass plus a judgment pass for variant IDs (S/M/L twins) |
| `bin/squadcompose.py:69` `read_home` | `size` fact from `scope.md` (`\b[SML]\b`); missing is allowed | add role-set facts here; header line 190 prints `size X` |
| `bin/squadcompose.py:219-230` `who_lines` | prints acts/aware per S, M, L (and M/L x qa-b) | must print per team preset or per fact value |
| `bin/squadrules.py:matches` | **a fact missing from the home counts as true** | a scope with no `size:` line would match every size rule (all roles' text in one file). Safe only because the unknown-key error fires first; the new key set must make a missing team fact an error, not "true", for the new keys |
| `bin/squad-spawn` | does NOT read size. Gates only `designer`/`architect` on `design: yes` / `architecture: yes` (`:111-118`) and accepts all roles | the Manager suggests the team, PO confirms: these two gates ("only the PO turns it on") change meaning (ADR 0017 / SIZE-3). Gate becomes "role is in the confirmed team" |
| `bin/squad-start:367` | first Manager prompt says "size the scope" | text only |
| `bin/squad-log-message:43-69` | hook reads `size:` to route the 3-returns notice (S/M to Manager, L to Team Lead; S adds a budget line) | needs a role-presence test (`team-lead` in team) |
| `bin/squadreport.py:81,423,483`, `squadreport_rollup.py:88`, `templates/report/report.js:97`, `rollup.js:103,151,178` | read `size` from `scope.md`, tolerant of empty (`or ""`, `"?"`, `"–"`) | old scopes keep their size line; new ones show a team. Report change is display-only; the rollup size filter (`fSize`) needs a replacement or removal |
| `bin/squad-migrate:77-190` | writes `size:` from `scopes.md` | folder-layout migration of legacy squads; keep or stop writing it |
| `templates/scope/scope.md` | `size:` line, "Done means: the size's checks" | template text |
| `bin/squadupgrade.py`, `squadadopt.py` | compare overlay hashes; `adopt` stamps a `plugin:` pin | retargeted/removed IDs flow through existing tombstone + stale-op listing; no engine change needed |
| `process.md` legacy template, `skills/squad-process-update/history/process-v*` | frozen history | untouched |

## Pins protect running scopes
A role launches with `PATH=<runtime>/bin` from the pinned `git archive`, so a scope pinned to 0.5.1/0.5.2 runs its own `squadcompose`/`squadrules`. A new engine that drops `size` never reads an old scope's file. Only the upgrade path (`squad-process upgrade/adopt`, between scopes) meets old `scope.md` and old overlays. Open scope `squad-close` (touches `templates/squad/process/`) will conflict in the rule files.

## Tests that bind size (all rewritten or retargeted)
`test_sizes.py` (467 lines, the table/duty/orphan checks), `test_dev_rules_size.py` (5 KiB cap, `COMBOS = product("SML", design, goal)` plus pinned S+architecture exception), `test_squadcompose.py`, `test_squadrules.py`, `test_qab_optional.py`, `test_process_conversion.py`, `test_team_models.py`, `test_team_lead_perms.py`, `test_advisor_rules.py`, `test_retro_rules.py`, `test_architect_handoff.py`, `test_squadreport_*`, `test_squad_migrate.py`, `test_squadruntime.py`, `test_squadadopt.py`, `test_squad_ledger.py`; fixtures `tests/rulesview.py`, `tests/report_fixtures.py`.

## Feasibility judgments (for the Architect's questions a-g)
1. **Role-presence facts are feasible in the engine**: `WHEN_KEYS` gains boolean keys per optional role (`ba`, `team-lead`, `tech-lead`, `qa-whitebox`, `qa-blackbox`, `designer`, `architect`; the existing `design`, `architecture`, `qa-b` fold into them). `read_home` derives them from a `team:` line in `scope.md`. About 30 lines in `squadcompose.py`/`squadrules.py`.
2. **Do not target rules by role combination.** 2^7 sets make per-combination variant IDs (today's `-b`, `-c` twins) unbounded. Feasible and bounded: **derived duty facts**. The engine maps the team to one fact per duty by a fallback chain kept in one place (plan owner: team-lead, else manager; tech AC: tech-lead + qa-whitebox, else qa-whitebox + dev, else dev; business AC: ba, else ticket; code check; behaviour check; full-suite owner; promote.md owner; hand-in target; 3-returns owner). Rules say `when: plan-owner = manager`. Fact values are few (2-3 per duty), so the ADR 0016 duty table becomes the chain table and stays the single source. Test every team set (128, in-process compose, fast) for: each duty has exactly one owner present, no rule acts on an absent role.
3. **Minimum viable team**: the Manager is always present; Developers always present. Every other role optional. Chain ends at Manager or Developer, so no duty is orphaned for any set.
4. **5 KiB Developer cap (`test_dev_rules_size.py`)**: the Dev text varies only with duty facts a Developer acts on (hand-in target, design-notes owner, review owner, suite owner, done check), roughly 5 facts of 2-3 values each. Test all role sets in-process and assert max <= 5120. Cap keeps; the pinned S+architecture exception is gone only if the new Dev text is trimmed. Today's worst case is 5443 B (S, design, goal, architecture); the cap can hold with dedicated trimming (rules on demand via `squad-process rule`), and "worst-case set" replaces the per-size loop.
5. **Hard-cutover migration is mechanical for plugin rules, manual for overlays.** `squad-process upgrade` already lists stale operations (hash change), operations on removed IDs and same-topic local rules. Old overlay ops that target size twin IDs (`SIZE-*`, `*-b/-c`) land in the removed-ID list; the PO sees them. A converter for `scope.md`: `size: S|M|L` + `design` + `architecture` + `qa-b` map to a `team:` line deterministically (S = manager+dev; M = + qa-whitebox, qa-blackbox unless qa-b no; L = all but designer/architect; design/architecture add theirs). Feasible in `squadadopt.py` (it already stamps `plugin:` into open `scope.md`).
6. **Mid-scope role change**: today "moving up/down" re-composes after a Handover (SIZE-13, 15, 16). With `team:` in `scope.md`, adding/removing a role is an edit plus `squad-respawn` of roles whose composed text changes; a tool can list those roles by diffing composed output before/after. Feasible, small.
7. **Report**: display only; scope `size` becomes `team` string; keep reading old `size` for old scopes.

## Risks
- Two rules whose `when` mixes `size` and `goal` (e.g. 3+3+1 lines) need both facts: fine.
- Rewriting 201 `when:` lines changes ~hundreds of rule hashes: every `process.local.md` overlay op in any squad goes stale. Expected; listed by `upgrade`.
- Rule count may drop (twin IDs collapse) or rise; `_removed.md` needs a tombstone per collapsed ID (`why`, `replaced_by`), plus changelog block and a rule snapshot (ADR 0016).
- Scope too big for one iteration? Judgment: engine + tools + rule rewrite + migration + tests is 4-6 tasks of 100-250 changed lines, except the rule rewrite (201 lines in 17 files + tests) which can split by file group. One iteration is feasible with 3 Developers if the fact vocabulary is fixed first. No goal split needed unless the Architect keeps per-combination variants.
