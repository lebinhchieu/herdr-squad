# A lazily woken role misses messages sent while it was down

Status: needs-triage

Source: upstream-proposals retro (iterations/1.md, 1.summary.md Friction), 2026-11-24.

## Problem
Lazy check (evidence/lazy-check/qa-b.md): the Tech Lead's first reply came from its notes, but it did not know about a HANDIN logged seconds before the notes were written.

## Proposed fix
The read-notes hook also lists the `messages.jsonl` lines addressed to the agent since its notes' mtime.

## Comments
