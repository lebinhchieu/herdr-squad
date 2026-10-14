Status: resolved
State: done (PASS; in the iteration-2 line merged at 7f0b436)
Task ID: BRD-11
Blocked by: 10, 06 (06 is in BRD-08's base, so this is already satisfied; listed because the watcher it extends is BRD-06's)
Files touched: `bin/squad-board` (the `tokens` section's source lookup, the `http` section's watcher trigger, `main` live branch only where it passes the snapshot map), `tests/test_board_live.py` (new)

# BRD-11: live data sources: session ids from herdr, `~/.claude*` roots, token refresh

**Done when, in live mode, each column's tokens and model come from the transcript of the session herdr reports for that agent, found under any `~/.claude*` folder, and refresh on the E8 schedule.**

Read first: design-iteration-2.md (E2, E7, E8), design.md "Tokens", spec "Transcript token reader". Replay mode keeps reading `replay/herdr.json` and `replay/claude*`; live mode must share all the reading code (same function, different source of the two inputs).

## Technical AC (BRD-11)
1. **Session map from the snapshot:** the recorder's snapshot (BRD-10) is the source of `{name: session_id}`; it refreshes on each re-snapshot. Test with the fake herdr: agent `a` has session `S1` → a transcript under `<HOME>/.claude/projects/p/S1.jsonl` gives its tokens.
2. **Roots:** every `$HOME/.claude*` directory (tests set `HOME` to a temp dir; never the real one); the same file reachable through two roots counts once (symlink in the test).
3. **Session id validation** and containment as in iteration 1 (regex; realpath must stay under the root).
4. **Refresh (E8):** with a fake transcript growing while the agent is `working`, `/state` reflects the new totals within `TOKEN_REFRESH_S` (constant overridable by `SQUAD_BOARD_TOKEN_REFRESH_S` for tests) and at once after a bar ends. No refresh timer runs while nobody is working.
5. **Missing herdr, unknown agent, no transcript** → four nulls, `/state` 200, no stderr.
6. **SSE interplay:** the watcher rebuilds on the token timer only, not on every poll (a second client does not add rebuilds); an unchanged state sends nothing.
7. **Jump in live mode** uses the real `herdr` on `PATH` exactly as in replay (stub in the test); the roster check is unchanged.
8. **No new global state** besides the token cache and the session map, both behind locks.
9. **Live `now` in streamed state (BRD-06 N2):** the SSE cache keeps the `now` of its build, so in live mode every sent event and every `/state` carries a fresh wall-clock `now` (re-stamp the cached state; do not rebuild just for `now`). Test: two events/requests 1 s apart differ in `now`; a state with no changes still sends nothing. **`live` on streamed states (tech-board ruling 2026-10-13, qaw-board-2 N2):** the streamed state also carries `live: true` in live mode. Add one helper `stamp_live(state)` (sets wall-clock `now` and `live: true`) and call it from both `handle_state` (replacing BRD-10's inline lines) and the SSE sender. Test: the first `/events` frame in live mode has `live` true and a wall-clock `now`; in replay it has neither a wall-clock `now` nor `live: true` (BRD-12 adds `false`).
10. **Watched sources (BRD-06 N1):** in live mode the watcher signature also covers the transcript files of known sessions; a changed transcript triggers a rebuild at most once per `TOKEN_REFRESH_S`. Replay mode keeps its fixed file list.
9. **Baseline AC 1 to 5, 7, 9, 10** from design.md.

### QA whitebox additions (qaw-board)

(qaw-board adds points here.)

## Comments
