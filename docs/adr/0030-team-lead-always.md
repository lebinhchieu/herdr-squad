# 0030: The Team Lead is always on the team; the Manager owns the plan

Status: accepted (tl-always; Chieu answered E1 on 2026-11-21)

**Overrides:** ADR 0010 (Team Lead only in M and L scopes; "the Manager plans" at S), ADR 0016 (Team Lead at size L only, already amended by 0018), ADR 0018 (the `team:` token list includes `team-lead`; "every subset of the seven roles is a valid team" becomes six optional roles), ADR 0022 and ADR 0028 (the watchdog nudge and the blocked-pane wake go to the Manager).

## Context
The Team Lead was optional, so every rule that named the plan owner needed variants: one for a Team Lead, one for the Manager (31 Manager-twin rules). The `plan-owner` duty and the `team-lead` presence key existed only to pick between them. A scope with no Team Lead made the Manager plan, assign, spawn and track at once, and the plan owner could also reorder the plan.

## Decision
- The Team Lead is always on the team. `plan-owner` is no longer a duty or a `when:` key, and `team-lead` is no longer a presence key.
- The Manager owns the plan (which tasks, their order, the iteration goal) and settles disputes.
- The Team Lead coordinates: it spawns and retires Developers, assigns per the plan, tracks STATUS messages and the ledger, runs health checks, escalates to the Manager only on fixed triggers, and never reorders the plan.
- `team:` may still list `team-lead`: the engine accepts the token and ignores it (the Tech Lead's choice, reversible). `squad-team add|remove team-lead` refuses.
- Watchdog (Chieu E1, option a): a scope's watchdog wakes its own Team Lead, and falls back to the Manager while no Team Lead is up or when it is blocked. A scope inside a goal gets its own watchdog. The goal's watchdog wakes the goal Manager only on `goals.md` events.
- Defaults: Manager `opus medium`, Team Lead `sonnet low` (settings JSON; where defaults live stays as in 0010). Subagents the Manager spawns default to `sonnet high`; the Manager picks model and effort per task (gather and explore stay `sonnet high`, a judgment call may use `opus` or a higher effort); forks are allowed and run on the Manager's model.

## Consequences
- Plugin 0.10.0, breaking for rule retargets: the 31 Manager-twin rules get tombstones; overlay ops on them go stale and `squad-process upgrade --check` lists them, as in 0018.
- `squad-process upgrade --check` lists old-key `when:` lines with their translation; `lint` names `file:line`.
- Live roles re-compose at their next respawn. Pinned scopes (`plugin: <v> <sha>`) keep their runtime.
- Known limit (watchdog): the watchdog treats the Team Lead as absent only when it is missing from `herdr agent list`. A Team Lead the roster marks retired whose pane is still open would still get the nudges. `squad-retire` closes the pane, so the case needs a hand-edited roster; the Manager's fallback does not cover it.

## Alternatives rejected
The goal-watchdog options Chieu did not pick (`iterations/1.md`, `escalations.md` E1):
- (b) the goal's watchdog wakes the goal Manager, who routes to each scope's Team Lead: one more relay, and the Manager is woken for pod matters.
- (c) change the proposed rows: not asked for.
