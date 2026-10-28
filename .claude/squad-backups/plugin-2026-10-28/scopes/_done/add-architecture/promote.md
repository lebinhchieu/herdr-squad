# Promote: add-architecture

What the scope decided that belongs in the project docs (applied in ticket 03, commit on branch squad/plugin/add-architecture/plugin-dev-add-architecture-2).

## CONTEXT.md
- New term **Architect**: optional role, designs architecture before the plan, writes `architecture.md` and ADR drafts, never code, checks no built code; above the Tech Lead (L) and the Developer's design notes (S, M); proposes irreversible choices, the PO decides.
- New term **architecture flag**: `architecture: yes|no` in `scope.md`, default `no`, PO only, any size.
- **Tech Lead**: removed `_Avoid_: architect`; added that its per-task design stays inside `architecture.md` when the flag is on.

## docs/adr/0017-architect-role.md (new)
Decision, boundary versus the Tech Lead, irreversible-choice ownership (amends the owner rows of ADR 0016), enforcement through conformance in the technical AC, no change for flag-off scopes, dev-rules size exception for S + flag.

## README.md
Roles list and the Designer paragraph mention the Architect and `architecture:` next to the Designer and `design:`.

## Not promoted
Ticket mechanics, test names, the evidence, the changelog (shipped with the plugin as v8).
