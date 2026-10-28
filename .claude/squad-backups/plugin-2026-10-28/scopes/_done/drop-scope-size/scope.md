# Scope: drop-scope-size

**I would like to have an update about the scope size. Now I want to remove the scope size, the Manager has to work base on scopes to suggest team to fit that scope. The suggestion now include architecture, designer as well -> all roles now are suggested base on scope, not base on PO request**

goal: 
touches: /home/chieule/workspace/squad
size: L
qa-b: yes
qa: full
design: no
architecture: yes
<!-- Team models: one line per changed role, `model <role>: <model> <effort>`, e.g. `model dev: sonnet medium`. Unlisted roles use their defaults. -->
model manager: sonnet high

plugin: 0.5.2 294957333ee4b2953e1db26e96e297637ed2343c

## Constraints
- **Developer cap:** 3 (the default in `process.md`)
- **Budget:** one iteration; check in with the PO when every task passed or after 3 returns on one task
- **Done means:** the size's checks passed (`process.md` → Sizes), evidence saved, branches ready for PO review

## Notes from the PO
