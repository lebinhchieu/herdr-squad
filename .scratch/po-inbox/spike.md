# PI-03 spikes S1, S2, S4 (Developer plugin-dev-po-inbox-2, 2026-10-15, claude 2.1.300)

**Result: all three pass. The mod is buildable as designed. `$.prompt.submit` is queued (never rejected, never interrupting), env reaches the module and the CLI, stat polling and stdin to the CLI work.** S3 is PI-04's.

Throwaway mod: `.scratch/po-inbox/spike-mod/` (copy it to `/tmp/po-spike/mod`; it logs to `/tmp/po-spike/log.txt`). Real session home, real auth (a throwaway `HOME` would lose the login); the mod only writes `/tmp/po-spike/`.

## Setup (replay)
```bash
mkdir -p /tmp/po-spike/scope && cp -r .scratch/po-inbox/spike-mod /tmp/po-spike/mod && touch /tmp/po-spike/watch.txt && rm -f /tmp/po-spike/log.txt
claude plugin validate /tmp/po-spike/mod        # passed; reads env GOAL_DIR SCOPE_DIR SQUAD_ROLE
herdr pane split --current --direction down --no-focus --cwd /tmp/po-spike --env SQUAD_ROLE=manager --env SCOPE_DIR=/tmp/po-spike/scope   # prints the pane id, P below
herdr pane run $P "SQUAD_INBOX_NOW=2026-01-01T00:00:00Z claude --plugin-dir /tmp/po-spike/mod --permission-mode default"
```

## S2: env readable in `session.start`
Mod line: `$.env.get('SQUAD_ROLE')`, `SCOPE_DIR`, `GOAL_DIR`, `$.plugin.root`. Log:
```
S2 env SQUAD_ROLE=manager SCOPE_DIR=/tmp/po-spike/scope GOAL_DIR=undefined plugin.root=/tmp/po-spike/mod
```
`$.env.get` of an unset name gives `undefined`. **PASS.**

### S2/S4 (M4): does `$.process.run` pass the env to the child?
`$.process.run(['printenv','SQUAD_ROLE','SCOPE_DIR','GOAL_DIR','SQUAD_INBOX_NOW'])` (exit 1 = GOAL_DIR unset):
```
S2 process.run printenv exit=1 out="manager\n/tmp/po-spike/scope\n"                              # session without SQUAD_INBOX_NOW
S2 process.run printenv exit=1 out="manager\n/tmp/po-spike/scope\n2026-01-01T00:00:00Z\n"        # started with SQUAD_INBOX_NOW=...
```
**The child inherits the host env, including `SQUAD_ROLE`, `SCOPE_DIR`, `SQUAD_INBOX_NOW`. The mod need not pass them.** (It may still pass `env` explicitly; harmless.)

### Env of a real Manager session
I did not read another process's `/proc/<pid>/environ` (blocked by the sandbox classifier as credential exploration; I did not work around it). Source evidence instead: `bin/squad-spawn` line 155-158 starts every agent, the Manager included (`squad-start` calls `squad-spawn manager`), with `--env SQUAD_ROLE=$role --env SCOPE_DIR=$scope_dir` (or `GOAL_DIR`), the same `herdr --env` mechanism the spike pane used. This Developer session, started by the same script, shows `echo $SQUAD_DIR $SCOPE_DIR $GOAL_DIR $SQUAD_NAME $SQUAD_SCOPE` = `.../plugin /.../scopes/po-inbox <empty> plugin-dev-po-inbox-2 po-inbox`. **Open: someone who owns a Manager pane should paste `printenv SQUAD_ROLE SCOPE_DIR GOAL_DIR` from it; a Manager the PO started by hand has no `SQUAD_ROLE` and the mod stays inert (T2).**

## S4: CLI by `$.process.run` with stdin; stat shows a change
Fake CLI `spike-mod/bin/squad-inbox` echoes argv and stdin. Mod runs `[$.plugin.root + '/bin/squad-inbox','answer','E1','--source','pane']` with `stdin: 'line1\nq"uo`te|é😀\r\nx'`:
```
S4 run exit=0 out="ARGV=['answer', 'E1', '--source', 'pane'] STDIN='line1\\nq\"uo`te|é😀\\r\\nx'\n"
```
stdin arrives byte for byte (newline, quote, backtick, pipe, emoji, CRLF). `$.fs.stat` gives `{"kind":"file","size":0,"mtimeMs":1792077568688.6406,"isLink":false}`. A 1 s `$.clock.every` tick, then `echo x >> /tmp/po-spike/watch.txt`: the next ticks read `mtimeMs=1792077597188.6726` (changed). **PASS.**
Validator rule met on the way: `$` may be passed only to a top-level `function` declaration (a `const log = ...` arrow is refused); a `$` helper must be a declared function.

## S1: `$.prompt.submit` idle / mid-turn / draft
The mod's `/spike` registers `$.clock.after(1000, submit)`, `/spikeb` the same after 6000 ms. (`sub` logs resolve/reject and elapsed time.)

**Idle** (`/spike` then wait):
```
15:20:57.511 S1 command run; scheduling submit in 1s
15:20:58.579 turn.start
15:20:58.585 S1 A resolved {"text":"S1-A: reply with exactly the word ALPHA","origin":{"kind":"plugin","name":"spike"}} after 54ms
15:21:00.332 turn.complete
```
The model saw: `The spike plugin sent a message: S1-A: ... This is how Claude Code surfaces a prompt a plugin submits between turns — it starts this turn in the user's place. Address the message above.` (the default frame; `asUser: true` would drop it, see Open points.)

**Mid-turn** (`/spikeb`, then at once "Write a 900-word story about a lighthouse, no tools."; submit fires 6 s into the story turn):
```
15:21:24.307 S1b command run; scheduling submit in 6s (during a turn)
15:21:25.369 turn.start                       (the story)
15:22:17.320 turn.complete                    (story done, 52 s)
15:22:17.374 S1 B resolved {...BRAVO...} after 47049ms    (submit resolved 47 s later, right after the turn)
15:22:17.386 turn.start                       (the BRAVO turn)
```
**Queued behind the running turn, not rejected, not interrupting.** The promise stays pending until the turn ends. So no hold-until-`turn.complete` code is needed; but `delivered` must be written only after the promise resolves, and "in flight" lasts the length of a turn (no second submit while pending).

**Draft in the prompt box** (`/spike`, then typed `MY DRAFT line one` without Enter, within 0.5 s; submit 1 s later): the turn ran with only the plugin text, and after it the box still read `❯ MY DRAFT line one`. **The draft is kept, untouched, and not sent with the answer.** Not tested: a draft present while the submit is queued mid-turn (the box is the same single editor; expected the same).

**`session.start` redelivery** (`SPIKE_REDELIVER=void`: `void sub(...)` unawaited in the hook): `S1 R-void resolved ... after 73ms` and the ROMEO turn ran at once after start. The very first spike awaited `$.prompt.submit` inside the `command.run` hook itself: never ran, no `turn.start`, no error, for 60+ s. **Rule: never await `$.prompt.submit` inside a hook; call it unawaited (`void`) or from a timer/handler.** A draft at `session.start` cannot be staged in time to test (the box is empty at start); the mechanism is the same box, so the idle result applies.

## Open points for the Tech Lead
- **Prompt text is framed by default.** `{ text }` reads "The <plugin> plugin sent a message: ..." plus a trailing sentence; `asUser: true` reads bare as the person's words. I use the default (framed): it keeps provenance honest (T7/B-31: an inbox answer is not a chat message of the PO). Say if you want `asUser`.
- Hot reload: `/reload-plugins` in the pane picked up edited module code (not automatic for `--plugin-dir` here).
