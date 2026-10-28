# Audit token usage and study Haiku

Status: ready-for-agent

**Phase A measures where the squad's tokens go and whether Haiku can do part of the work. It changes no product code.** Two reports, each backed by a re-runnable script, let the PO pick what to build in Phase B.

## Tickets

| # | Ticket | Output | Depends on |
|---|---|---|---|
| 01 | Token audit | `.scratch/audit-token/audit.md` + `scripts/` | none |
| 02 | Haiku study | `.scratch/audit-token/haiku.md` + `fixtures/` | none (its share column reads 01's script, see ticket) |

Phase B tasks (AT-03..) are set after the PO's pick. Not in this spec.

## The bar: a real saving

Measured, net saving >= 2% of total squad spend, no QA-AC loss (business definition: `scopes/audit-token/business-ac.md`, RS-1..RS-3). Anything else is "minor" or "unproven".

## Technical design (both tickets)

**Data sources (PO decision E1, read-only):**

| Source | Path | Notes |
|---|---|---|
| Session transcripts | `~/.claude/projects/-home-chieule-workspace-squad*/<session>.jsonl` and `<session>/subagents/*.jsonl` | `~/.claude-2/projects` is a symlink to the same folder: resolve with `realpath`, or every session is counted twice. Worktree sessions live in `...squad--worktrees-*` dirs |
| Rosters | `.claude/squads/*/scopes/{*,_done/*}/roster.md` | holds only the **latest** session of a respawned agent |
| Cost-rule events | `.../usage-events.jsonl` | one line per rule firing, has `session` |
| Message log | `.../messages.jsonl` | optional, for phase timing |

**Facts verified 2026-10-16 (two samples: this Tech Lead session, `_done/board-flakes` roster):**
- A transcript has `type: assistant` lines with `message.id`, `message.model`, `message.usage` (`input_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`, `cache_creation.{ephemeral_5m,ephemeral_1h}_input_tokens`, `output_tokens`, `output_tokens_details.thinking_tokens`, `speed`, `service_tier`). One message id spans several lines (this session: 15 lines, 8 ids; QA whitebox saw 98 of 135 ids on 2-3 lines).
- Every squad transcript starts with an `agent-name` record (`agentName: plugin-tech-audit-token`) and `agent-setting` (`squad:tech-lead`). 126 of 153 sessions in the squad project folder have one. This, not the roster, attributes sessions that were respawned.
- `bin/squad-usage` skips sidechain lines and reads only roster rows, so its table undercounts: a copy of it is not an audit.
- Subagent transcripts exist (`<session>/subagents/`, 3 under the squad project today).

**Decisions:**
1. Stdlib Python 3, run as `python3 -I`, read-only, scripts committed under `.scratch/audit-token/scripts/`. No code in `bin/`, `hooks/`, `agents/`, `skills/`, `templates/`.
2. Unit = **cost-weighted dollars at list price**, plus raw tokens per type. Price table is printed in the report with its source and date. Models with no price are listed, not guessed.
3. Dedupe by `message.id`. Each token field is the **max** over the lines of an id (streaming partials only grow); the script states and tests this.
4. Role = from the `agent-name` pattern `<squad>-<role-short>-<scope>[-n]`, checked against roster and `usage-events.jsonl`. Phase = from role (ba/tech/team-lead/designer: plan; dev: build; qaw/qab: QA; coach: retro; mgr: coordination). The role-to-phase table is printed. Phase is therefore approximate: say so.
5. Deterministic re-run: scripts take `--until <ISO timestamp>`; reports state it. Live sessions keep growing, so a re-run without the cutoff differs by design.
6. Reports hold ids, counts, paths and numbers only. No transcript text.
7. Safe to commit: `.claude/squads` is gitignored, `.scratch/` is committed, so nothing from squad files is copied beyond ids and numbers.

**No migration, no contract change, no deploy.** Nothing here is a backward-compatibility risk.

## Out of scope

Building any saving; editing `agents/*.md` model defaults (PO approval first); other projects' squads (`wpw-squad`), because E1 covers this repo's `scopes/_done/` only.

## Closing task AC (integration or promotion task, Phase B)

- `.scratch/audit-token/spec.md` and `issues/*.md` (untracked in the project root while Phase A runs) are committed on that task's branch, with each ticket's `Status:` and `## Comments` brought up to date.
- `git status --short .scratch/audit-token` is clean afterwards; the Developers' Phase A files (`audit.md`, `haiku.md`, `scripts/`, `fixtures/`) are merged in and do not collide with these.
- `promote.md` rows that the PO's pick confirmed are committed to their target files.
- AT-01 follow-ups from QAW (droppable): make the `audit-tables.md` file-count line cutoff-aware or say it is not; fix the `audit.py` docstring (`audit.json` should be `audit-tables.json`); note in `audit.md` that the Opus price rests on the vendor page alone (within 6% of cost-state).

## RS-3 history result (AT-03 dropped)

- driver 5: unproven, history too small (n=1 scope / 50 HANDINs on Sonnet; Opus arm 3 scopes / 64 HANDINs; the 41% scope has 3 HANDINs and is mixed). The only Sonnet scope, `po-inbox`, is also the largest-FAIL scope (30 FAIL / 50 HANDIN), and it differs in size and date: one scope cannot separate the model from those.
- driver 2: no history contrast (tech-lead, qa-whitebox, qa-blackbox, ba ran `high` on every message, audit.md [D5]).
- Consequence: the PO's pick is whether to run a controlled trial, not about history.
