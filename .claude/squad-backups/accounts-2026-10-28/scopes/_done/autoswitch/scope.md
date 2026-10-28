# Scope: autoswitch

**Context: /home/chieule/workspace/squad/.claude/squads/plugin-bk261023/scopes/_done/integrate-promote/tasks/auto-switch-wake-plan.md (earlier plan: wake every agent after an account switch). The PO says auto switch works not well. Goal: find the best way to switch accounts and save tokens. The PO does not want to resume with the new account and trigger a prompt/wake for ALL agents; only agents with pending work should wake.**

goal: 
touches: /home/chieule/.claude-accounts (installed copies; edits happen in tools/claude-accounts/ of the squad repo, ADR 0012)
size: M
qa: full
design: no
<!-- Team models: one line per changed role, `model <role>: <model> <effort>`, e.g. `model dev: sonnet medium`. Unlisted roles use their defaults. -->

plugin: 0.5.1 eff98a945fe0a0eb578da5552cf2ab594e31943a

## Constraints
- **Developer cap:** 3 (the default in `process.md`)
- **Budget:** one iteration; check in with the PO when every task passed or after 3 returns on one task
- **Done means:** the size's checks passed (`process.md` → Sizes), evidence saved, branches ready for PO review

## Notes from the PO
