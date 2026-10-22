# Token Coach: token-efficient squad

Status: ready-for-agent

**The squad spends tokens well without anyone watching live.** Defaults are written into code, agents fix their own sessions by rule through a hook, and a Sonnet Token Coach reviews spend at each retro. The Manager stays decision-only: it reads at most 3 ranked proposals per retro.

## Layer 1: defaults in code

- Each `agents/<role>.md` sets `model:` and `effort:`:

  | Role | Model | Effort |
  |---|---|---|
  | Manager | opus | medium |
  | Tech Lead | sonnet | high |
  | BA | sonnet | high |
  | Team Lead | sonnet | medium |
  | Dev | sonnet | medium |
  | QA whitebox | sonnet | high |
  | QA blackbox | sonnet | high |
  | Token Coach | sonnet | medium |

- A step-up (one notch of model or effort) happens only on failure or escalation, and lasts for that task only.
- `squad-spawn` records each agent's session id in `roster.md`.

## Layer 2: rules applied by each agent, checked by a hook

- A Stop hook in the squad settings file (the one `squad-spawn` passes with `--settings`) runs `squad-usage --check <own session>` after every turn. It costs no LLM tokens.
- Rules (starting values; the Coach tunes them):
  1. **Reuse** a session while it stays on the same scope and context is under 50%.
  2. **Fresh** when context is over 60%, after a compaction, or on a new scope.
  3. **Idle**: idle over 1h (the cache lifetime) and context over ~100k → fresh from notes.
  4. **Step-up** as in layer 1.
  5. Messages point at files. The Manager reads summaries, never transcripts.
- When a rule fires, the hook tells the agent. The agent writes `roles/<agent>.notes.md` and calls `squad-respawn <self>`. The event is appended to `usage-events.jsonl`.

## Layer 3: Token Coach at retro

- The Manager spawns the Coach at the retro step (`templates/squad/process.md:112`).
- The Coach reads the `squad-usage` table and `usage-events.jsonl`. It does not read raw transcripts.
- It writes `iterations/<n>.coach.md`: every proposal, ranked by expected saving. Each one gives the evidence row, the `process.md` change, and the saving.
- The Manager decides the top 3. The rest go to a backlog section in the same file. Accepted changes are logged in `process-log.md`.
- The Coach may only propose changes to `process.md`, never to `agents/` or skills.

## Evidence

- **Verified:** transcript JSONL lines carry `message.model`, `effort`, `timestamp`, `sessionId`, and `message.usage` with input, cache read, cache write (`ephemeral_1h` / `5m`) and output tokens.
- **Verified:** today only `agents/manager.md` sets a model, so other roles inherit the Manager's model (`bin/squad-spawn:19`, `:84`).
- **Not verified:** which hook event fits best (Stop is assumed), and how `squad-spawn` learns the session id (passing `--session-id <uuid>` is assumed).

## Tickets

01 squad-usage → 02 role defaults → 03 session id in roster → 04 check hook → 05 squad-respawn → 06 process rules → 07 Token Coach role
