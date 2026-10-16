# The Team Lead runs the pod in M and L scopes

Status: accepted (tl-manages-team)

**Decision:** in M and L the Team Lead runs the pod and is its single point of contact; S is unchanged.

**Why:** every routine message reached the Manager, whose Opus context should hold the PO's conversation and decisions.

**Consequences:**
- The Manager spawns the Team Lead, Tech Lead, BA, QAs and Designer; the Team Lead spawns and retires Developers only, enforced by its settings (`squad-spawn dev` prefix) and by `squad-spawn` and `squad-retire` refusing other targets when `SQUAD_ROLE=team-lead` (a squad's own `settings/` copy overrides the template).
- The Manager hears four kinds from a pod (the *Manager traffic* term): an escalation to the PO, a size-change signal, a dispute the pod could not settle, and the iteration summary; plus one line at 3 returns on a task. Everything else goes to the Team Lead.
- The Developer cap holds across a goal by shares: the goal Manager divides it among running scopes in each Team Lead's briefing. When a scope ends, its share goes to the scopes still running, at their next briefing or respawn.
- The Team Lead settles plan, order and assignment disputes; every other dispute goes straight to the Manager. A Team Lead ruling starts with `FINAL:` and is not re-opened.
- Nobody relays a blocked pane or a permission prompt; each agent's own toast tells the PO.
- The Team Lead writes `iterations/<n>.summary.md` (at most 40 lines) for the Manager's retro and check-in; at 3 returns on one task it sends one budget line, so the PO's Budget rule holds.
- The PO removed the `process.md` byte budget ("Remove the budget completely"): the `processlint` size check and the Manager file's budget bullet are gone, and ADR 0006's budget bullets are history (ADR 0006 gets a one-line amendment note). Version 4 (ADR 0005); L stays a size label with the same roles as M.
- Suites (PO note): Developers and QAs run only the test files they touch and never the full suite or two suite runs at once; the Tech Lead decides when the full suite runs (once for a batch, or at the end of the scope or iteration) and runs it; a failing run returns the named task. The rule is `process.md` → Safety → Suites; `CLAUDE.md` keeps the runner command.
- A role's default `model` and `effortLevel` live in its settings JSON (`settings/<role>.json`, the template as fallback), not in `agents/*.md`; `squad-spawn` reads them with `jq` and still passes `--model`/`--effort`. A flag beats the file, and recorded overrides (ADR 0008) stay flag-only. Reason: an `--agent` frontmatter `model` beats a `--settings` `model`, so relying on Claude to read the key is fragile.
- The roster has two writers on disjoint rows (Team Lead: its Developers; Manager: the rest).

**Alternatives rejected:** the Manager keeps spawning and routing (the cost the PO named); the Team Lead relays blocked panes (the PO goes to the pane himself); a cap counter in `squad-spawn` (the cap is overridable per brief and lives in prose); dropping L (a later scope).
