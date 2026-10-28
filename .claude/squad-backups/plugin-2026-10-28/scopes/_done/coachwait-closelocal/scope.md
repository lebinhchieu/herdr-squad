# Scope: coachwait-closelocal

**Two issues when using squad 0.5.0 (seen in /home/chieule/workspace/enhanced-markdown-vscode/.claude/squads/blueprint):

1. Token coach verify takes a long time. The Manager ran: Bash(cd $SCOPE_DIR; ls roles tasks iterations; herdr agent list | grep -o '"name":"blueprint-coach[^}]*agent_status[^,]*' | head), then Bash(cd $SCOPE_DIR; for i in $(seq 1 55); do ls | grep -qi proposal && break; sleep 10; done; ls) and a second find -iname '*proposal*' loop, both with (timeout 10m), i.e. up to ~9 min of polling for the coach's proposal file. Scope folder had roles/blueprint-coach-grillui.rules.md etc. Find why the coach takes so long to produce proposals / why the Manager polls like this, and make it faster or event-driven.

2. squad-close refuses to run: exits with 'no squad folder' because it requires .claude/squads/<squad>/process.md. That squad only has process.local.md (the plugin squad in this repo is in the same state: plugin.pin + process.local.md, no process.md). Bug in the plugin's squad-close, not the user's repo. Note: open scope squad-close also touches bin/squad-close; coordinate at merge.**

goal: 
touches: bin/squad-close, agents, skills/squad-start, templates/squad
size: M (confirmed by PO 2026-10-23)
qa: full
design: no
<!-- Team models: one line per changed role, `model <role>: <model> <effort>`, e.g. `model dev: sonnet medium`. Unlisted roles use their defaults. -->

plugin: 0.5.0 5adfc45151ab8611abc76c11cc4939cc5fc2db90

## Constraints
- **Developer cap:** 3 (the default in `process.md`)
- **Budget:** one iteration; check in with the PO when every task passed or after 3 returns on one task
- **Done means:** the size's checks passed (`process.md` → Sizes), evidence saved, branches ready for PO review

## Notes from the PO
