# Warm cache: act before the 1h cache expires, never after

Status: ready-for-agent

## Problem Statement

Every squad session (Manager, Team Lead, Tech Lead, QAs, BA, Developers, Designer, Architect) has a 1h prompt cache. A session that sits idle for more than an hour loses it. Its next turn then rewrites the whole context at the 1h cache-write price, 2x the input price, instead of reading it at 0.1x. For a 150k context that is about twenty times the cost of keeping it warm.

Today the squad only reacts after the loss. The Stop hook fires on context size or a compaction, never on an expiry. The Manager gets a notice about an expiry only at its next `squad-spawn` or `squad-inbox add`. The rule for a long PO wait (COST-8b) makes the Manager respawn after the wait, when the cache is already cold. Respawning today also sends the notes prompt at once, so a respawned session that is never needed again still pays a cold cache write. The PO (Chieu) is not at the screen when this happens, so nobody interrupts it. The report counts the expiries only afterwards.

## Solution

The watchdog watches every agent in its home for the 1h cache. When an idle agent with a large context reaches 55 minutes since its last turn, the watchdog has it write its notes while the cache is still warm (one cheap turn), then restarts it as a lazy respawn: a fresh session that is started but not prompted. A lazy session makes no API call, so it writes no cache and costs nothing until a message arrives. The first message to it, from anyone, is preceded by an automatic "you were respawned: read your notes first" instruction, so senders do nothing different.

This applies to the whole team, the Manager and each Team Lead included, and it may interrupt them: an agent that has been idle for 55 minutes is not in a conversation. A small context (under 50k) is left to expire, because rewriting it costs little. An agent with nothing open is not respawned: the Team Lead retires it as COST-13b already says. The Manager and a Team Lead cannot be retired, so they get the lazy respawn.

```
last turn 55 min ago, agent idle, context over 50k, work open
        |
watchdog prompts: write roles/<name>.notes.md        (warm turn)
        |
watchdog sees fresh notes, runs squad-respawn --lazy (cold cache: none written)
        |
next message -> hook adds "read your notes first"    (one cold write, only when needed)
```

## User Stories

1. As the PO, I want an idle agent's cache never to expire unnoticed while it still holds a large context, so that I stop paying cold-cache writes for sessions nobody is talking to.
2. As the PO, I want the Manager covered by the same rule as every other role, so that a long wait for my answer does not leave it with a cold 150k context.
3. As the PO, I want the Manager to be prompted even though I might be in its pane, so that the cache is saved while I am away (I am normally not there when it is cold).
4. As the PO, I want a Team Lead covered too, so that the role that runs a pod is not the one that always expires.
5. As a Manager, I want the watchdog to prompt me to write my notes at 55 minutes idle, so that I do not have to watch the clock.
6. As a Manager, I want the respawn done for me once my notes are written, so that I cannot forget the second step.
7. As a Manager, I want my respawned session to read my notes on the next message, so that I continue where I left off.
8. As a Manager, I want a message from the PO to my lazy session to be answered as normal, so that the respawn is invisible to the PO.
9. As a Team Lead, I want an idle pod role with open work and a large context to be respawned before its cache expires, so that I do not pay a cold write when I next message it.
10. As a Team Lead, I want an idle pod role with nothing open to be left for me to retire, so that COST-13b stays the rule for finished roles.
11. As a Team Lead, I want to be told once per idle spell which roles have nothing open, so that I retire them instead of letting them idle.
12. As a Team Lead, I want a role with a small context (under 50k) left alone, so that the squad does not spend a notes turn to save a small write.
13. As a Developer, I want a lazy respawn to keep my worktree, branch and uncommitted work, so that nothing is lost.
14. As a Developer, I want my notes written before the restart, so that the new session knows my ticket state.
15. As a Developer, I want a watchdog-driven respawn to count with the mid-ticket respawn rule (COST-5), so that the Team Lead's split decision still sees it.
16. As a Tech Lead, QA, BA, Architect or Designer, I want the same behaviour as a Developer, so that no role is a special case.
17. As any role, I want to write notes exactly as NOTE-1 says, so that the watchdog restarts me from a file that has the state in it.
18. As any role, I want to be prompted at most twice per idle spell, so that a stuck session does not loop.
19. As the watchdog, I want to count a role whose pane is `blocked` as unavoidable, so that I never send text into a pane waiting on a prompt.
20. As the watchdog, I want to skip a role holding a background shell, so that a respawn does not kill the test suite it waits on.
21. As the watchdog, I want to skip a role that is `working`, so that a busy session (whose cache is being refreshed every request) is never touched.
22. As the watchdog, I want to measure idleness from the agent's last main-thread turn, so that subagent turns do not hide an idle main session.
23. As the watchdog, I want the context size from the same transcript readers `squad-usage` uses, so that the two never disagree.
24. As the watchdog, I want to verify that the notes file is newer than my prompt before I respawn, so that I never restart a role that did not write its notes.
25. As the watchdog, I want to log each decision (`cold-cache: prompted`, `respawned lazy`, `skipped: small context`, `unavoidable: blocked`, `unavoidable: background shell`, `gave up: notes not written`), so that the report and the PO can see what happened and why.
26. As the PO, I want a role that never wrote its notes after two prompts to be logged and left alone, so that nothing is restarted from stale notes.
27. As a role respawned lazily, I want my roster entry and my session id updated as for any respawn, so that the squad tools find my new session.
28. As a role respawned lazily, I want my model and effort overrides kept, so that I run on the same settings.
29. As a sender (any role or the PO), I want to message a lazy role the usual way, so that I need no knowledge of lazy sessions.
30. As a lazy role, I want the "read your notes first" instruction added to my first prompt by a hook, so that it applies to the first message whoever sends it.
31. As a lazy role, I want the instruction given once only, so that later prompts are not polluted.
32. As the squad, I want a leftover lazy marker harmless if the role is retired, so that a retired name never gets a stale instruction. (A retired name is never reused: COST-5.)
33. As the Manager, I want COST-8b rewritten to respawn before a long PO wait passes the hour, not after it, so that the rule matches the new behaviour.
34. As the PO, I want the Stop-hook and Manager-guard expiry notices to stay as a safety net, so that an expiry the watchdog could not avoid is still shown.
35. As the Token Coach, I want `cache_expiries` and their cost still in the report, so that I can check that the number falls.
36. As the PO, I want the watchdog's thresholds (55 minutes, 50k, 2 prompts) to be named constants with an environment override, so that I can tune them without a code change.
37. As the PO, I want this to work for a goal home and for a scope home, so that every role in every home is covered by the watchdog of its own home.
38. As an operator on native Windows or WSL, I want the lazy path to use the same helpers as the other tools (no new shell-only dependency), so that ADR 0011 still holds.

## Implementation Decisions

- **Who respawns whom: the watchdog respawns, for all roles.** The role writes its notes (only it knows its state); the watchdog then runs the lazy respawn itself. The restriction that a Team Lead may not respawn the Manager or another Team Lead stays for roles; the watchdog is infrastructure, not a role, and is not bound by it. This is a deliberate exception and needs a short ADR. Rejected alternative: each role runs `squad-respawn` itself on the watchdog's prompt (a second instruction a busy or confused session can drop; no way to verify it ran).
- **Idle:** a role is idle when its last main-thread turn (subagent turns excluded) is at least 55 minutes old and herdr does not report it `working`. Context is the last main-thread turn's input plus cache read plus cache write tokens, from the shared transcript readers.
- **Eligible:** idle, context over 50k, and work still open. "Open work" is: a ticket assigned to the role that is not passed or merged; for a Team Lead, any open ticket in its scope; for a Manager, any goal not done. A role with no open work is not respawned (see below).
- **Role with nothing open:** the watchdog does not retire. It tells the Team Lead once per idle spell (the Manager when the scope has no Team Lead), who retires it under COST-13b. The Manager and a Team Lead are never retire candidates: with a context over 50k they get the lazy respawn whether or not work is open; with a context under 50k they are left alone.
- **Small context:** at or under 50k nothing is done. The expiry is allowed, and logged as skipped.
- **Skips:** a pane that is `blocked` (the watchdog never sends into it), a role with a background shell token (a respawn would kill the shell), and a role that is `working`. Blocked and background-shell cases log `unavoidable` with the reason, once per spell.
- **Two prompts, then give up:** the watchdog sends the notes prompt, and on a later pass, if the notes file is still not newer than the prompt, sends it once more. After the second, it logs `gave up: notes not written` and does nothing more for that idle spell. Each prompt is one message per event, never repeated beyond two.
- **Notes check:** the watchdog respawns only when the notes file's modification time is later than the prompt it sent. It never respawns without notes (NOTE-1 still applies; no `--force`).
- **Prompt text** names the role, says the cache is about to expire, and asks only for the notes file to be written now (one turn, nothing else started). It follows the same wording rules as the other watchdog nudges.
- **Interrupting is allowed, including the Manager.** The Manager-pane rule "nothing is sent into a `blocked` pane" is kept; no other quiet-moment wait.
- **`squad-respawn` gains a lazy mode.** It does everything it does today (same name, role, scope, worktree, model and effort overrides, roster and session id, tab title, event log) but starts the new session without the notes prompt and writes a per-agent marker beside the notes. The event log records the respawn as lazy. Mid-task respawns (a Developer's COST-5 respawn, a role's own `fresh`) stay immediate: the default does not change.
- **`squad-spawn` must not wait for a first prompt in lazy mode.** It currently waits for the first prompt to start the agent, resends Enter once and then warns (merged watchdog-blind 01). A lazy spawn has no prompt, so that wait and warning are skipped for it.
- **A first-prompt hook reads the marker.** The existing UserPromptSubmit hook family gets a second hook (not folded into the away-mode hook): when the session belongs to a squad agent and its marker exists, it adds the "you were respawned: read your notes first" instruction to that prompt and deletes the marker. It acts once, in that agent's own sessions only. Anything else is silent and exits 0, as the other hooks do.
- **Rules.** COST-8b is rewritten: the Manager respawns before the PO wait passes the hour. One new COST rule (all roles, aware: manager) states the 55 min trigger, the 50k floor, the retire-versus-respawn split and that the watchdog does it. COST-3, COST-5 and COST-10b are unchanged. The rule change follows the existing process-update practice (process changelog, plugin version).
- **Tunables.** 55 minutes, 50k tokens and the 2-prompt cap are constants with environment overrides on the watchdog, next to the existing watchdog variables.
- **No change** to the Stop hook, the Manager guard, `squad-usage`, or the report's expiry counter. The guard's expiry notice stays as a safety net.
- **Verified in this session:** real transcripts show the writes land in the 1h bucket (the 5m bucket is 0), so the 1h assumption in the transcript readers holds for these sessions.

## Testing Decisions

- A good test checks behaviour from outside: what the watchdog logs and sends, what files `squad-respawn` writes and what it runs, what the hook prints. It does not test private helpers.
- **Seam 1, the watchdog pass** (extend the existing watchdog tests, which already drive a pass with a snapshot and fake herdr output): transcript fixtures with a last turn before and after 55 min, contexts under and over 50k, and one case each for: eligible role, nothing-open role (Team Lead told, no respawn), Manager and Team Lead, blocked pane, background shell, and the 2-prompt cap with notes never written. One test per risk; no matrix.
- **Seam 2, `squad-respawn --lazy`** (extend the existing respawn tests, which fake herdr): the new session is started without a prompt, the marker is written, overrides and refusals still apply, and the default respawn still sends its prompt.
- **Seam 3, the first-prompt hook** (same style as the existing away-mode hook tests): marker present gives the instruction and removes the marker; marker absent gives nothing; a second prompt gives nothing.
- Prior art: the existing watchdog, respawn, away-hook and manager-guard tests. Tests for `squad-spawn` skip the first-prompt wait in lazy mode belong in the existing spawn tests.
- Run only the touched files plus the `grep -rl` hits, as `CLAUDE.md` says. The full suite once on the final sha, after asking Chieu through the Manager.
- Existing tests must keep passing and none may be newly skipped.

## Out of Scope

- Keep-alive pings of any kind.
- Running `/compact` in a session: a compaction stays a failure signal, not a tool.
- Retiring roles automatically: the Team Lead keeps that (COST-13b).
- Verifying the 1h lifetime against Claude docs beyond the transcript check above.
- Cache handling when the PC suspends (Sleep-when-idle): a suspended PC loses the cache regardless.
- Per-role thresholds, and changes to the respawn line (`first action + 50k, at most 180k`).
- Any change to the Developer rule for retiring (COST-5).

## Further Notes

- Cost model, for the report: a read costs 0.1x input, a 1h write 2x, so keeping a 150k context warm for an hour costs about 15k input-equivalent tokens and an expiry about 300k. A lazy respawn costs one warm notes turn and then nothing until used.
- Order of action matters: a respawn or compact has to start before the hour, because after the expiry the notes turn itself would pay the cold write. The 55 min trigger and the 60 s watchdog pass leave 5 minutes.
- Open for the Plan phase: whether sleep-when-idle (the PC about to suspend) should first run the same pass, since a suspended PC always loses the cache. Not required by this spec.
- Glossary gap for `/domain-modeling`: "lazy respawn" and "cold cache" are new terms, and "idle" is used by the watchdog with a different meaning (nobody working in the home) than here (one agent's last turn).
