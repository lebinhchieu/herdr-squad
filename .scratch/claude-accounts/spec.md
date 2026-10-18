Status: ready-for-agent

# Spec: claude-accounts in the repo (scope ca-repo)

**One line:** the c / c1-c3 / cdefault / cswitch / cautoswitch launchers, the usage popup, the statusline recorder and the `claude-accounts` skill become source files in `tools/claude-accounts/`; an install script the PO runs links the live `~/.claude-accounts` and `~/.claude/skills/claude-accounts` to them and deletes the leftovers; after that every command behaves exactly as today. Source: goal `claude-accounts`, `shared/decisions.md` (binding), the live files read-only.

*Draft location until a Developer commits it as `.scratch/claude-accounts/spec.md`: `scopes/ca-repo/evidence/_scope/spec.md`. Technical AC live in the task files (`tasks/NN-*.md`).*

## Problem

As the PO I built the account launchers in `~/.claude-accounts` for working with squads, but they live in a loose directory with its own `.git`, a pile of `*.bak-*`, `*.new`, `*.orig` files and a `__pycache__`, and no tests. I want to maintain them in this repo, test them, and keep my daily setup (PATH, herdr popup, statusline) working without touching it.

## Glossary (business terms this scope adds)

- **Launcher:** one of `c`, `c1`, `c2`, `c3`, `cdefault`, `cswitch`, `cautoswitch` (bash/python scripts in `bin/`).
- **Live home:** `~/.claude-accounts`, where the PO's shell, herdr and statusline find everything. Scripts there are links after install.
- **State files:** `default`, `usage-1|2|3`, `cswitch.log`, `workspace-default/<id>`. Written by the launchers at run time; they stay real files in the live home, never in the repo.
- **Global default / workspace default:** the account `c` starts: the workspace one (herdr only) first, else the global one, else account 1.
- **Leftovers:** `*.bak-*`, `*.new`, `*.orig`, `HANDOFF.md.bak*`, `HANDOFF.md.new`, `__pycache__`, anywhere in the live home's script level, `bin/`, and the skill folder.
- **Main checkout:** `/home/chieule/workspace/squad` itself, not a git worktree of it.

## Business rules (binding for every task)

1. **Behaviour parity.** No launcher changes what it prints, returns, reads or writes. Bugs found while testing are listed in the iteration file, not fixed here (the PO asked to import, not to change).
2. **State stays in `$HOME/.claude-accounts`**, whatever the scripts' real path is. Nothing derives the state folder from the script's own location.
3. **The install script never edits** `.bashrc`, the herdr `config.toml`, the statusline script or any other file of `~/.claude`, beyond the one skill link. It never touches `~/.claude-accounts/.git`.
4. **Leftovers are deleted by pattern only**, and only at the script level of the live home, in its `bin/`, and in the skill folder. Never inside `workspace-default/` or `.git`, never a state file.
5. **The tool stays inert for the plugin:** nothing under `bin/`, `skills/`, `hooks/`, `agents/` refers to it, so it is not a plugin skill or command (goal decision E1).
6. **Squad and tests never touch the real live home.** Every check runs in a scratch `HOME` with a stub `herdr` and a stub `claude` on PATH, and never reaches the network.
7. **Windows is out of scope here** (scope ca-win). `tools/claude-accounts/windows/` is reserved for it.

## User stories and business AC

### Import (task 01)

1. **As the PO, I want the files in the repo exactly as they run today, with the junk left behind.**
   - **Given** the main checkout, **when** I list `tools/claude-accounts/`, **then** I see `bin/{c,c1,c2,c3,cdefault,cswitch,cautoswitch}`, `lib.sh`, `usage-popup.sh`, `record-usage.sh`, `HANDOFF.md`, `README.md` and `skill/SKILL.md`.
   - **Given** the repo, **when** I search `tools/` for the leftover patterns, `.git`, `__pycache__` and the state-file names, **then** nothing is found.
   - **Given** each imported script and the current live file, **when** I compare them byte for byte, **then** they are identical, and the executable bit of each script is kept. Any difference found at the final check goes to the Tech Lead as a finding, never silently reconciled (the live home may have been edited since the import). `HANDOFF.md` and `skill/SKILL.md` are the only files task 05 may change.
   - **Given** the plugin, **then** rule 5 holds and the plugin's shipped command and skill lists are unchanged.

### Install script (task 02)

Test scene: a scratch `HOME` that mimics the PO's: real scripts, a `default` file, `workspace-default/w23`, `usage-1`, `cswitch.log`, leftovers in the script level and `bin/`, a real skill folder with leftovers, an old `.git`, one extra file the PO made.

2. **As the PO, I want to run one script after the merge and have my live home use the repo's files.**
   - **Given** the scene, **when** I run the install script from the main checkout, **then** each script in `~/.claude-accounts` (`bin/c`, `c1`-`c3`, `cdefault`, `cswitch`, `cautoswitch`, `lib.sh`, `usage-popup.sh`, `record-usage.sh`) is a symlink with an absolute target to the checkout's file and runs; `~/.claude-accounts/bin` stays a real folder; `~/.claude/skills/claude-accounts` is a symlink to `tools/claude-accounts/skill`; every path the docs and the skill name after install exists (`HANDOFF.md` linked, or the reference repointed).
   - **Given** the same run, **then** `default`, `usage-*`, `cswitch.log` and `workspace-default/*` are byte-identical to before, and all leftovers (rule 4) are gone.
   - **Given** the run, **then** it prints what it did (links made, files deleted, files kept) and ends with a line saying `.git` was left alone and can be retired by hand (rule 3). It touches nothing outside `$HOME/.claude-accounts` and `$HOME/.claude/skills/claude-accounts`.
   - **Given** a file in the live home that is neither a script of the tool, a state file nor a leftover, **then** it is kept and named in the output as kept.
3. **As the PO, I want a second run to be harmless and a first run on a clean machine to work.**
   - **Given** the install already ran, **when** I run it again, **then** nothing changes and it exits 0.
   - **Given** a `HOME` with no `~/.claude-accounts` and no skill link, **then** it creates the folders and links, creates no state file, and exits 0.
4. **As the PO, I do not want to lose edits I made in the live home.** (BA amends QA proposal I6)
   - **Given** a live script or the skill's `SKILL.md` that is a real file whose content differs from the repo's, **when** I run the install script, **then** nothing is changed (checked for every file before the first change), it names each differing file with a `diff` command, and exits non-zero.
   - **Given** the same state and `--force`, **then** the file is replaced by the link. **Given** a real file identical to the repo's, **then** it is replaced by the link without `--force`. **Given** a link that points elsewhere, **then** it is repointed (a link holds no content).
   - **Given** `--dry-run`, **then** it prints the same plan, changes nothing, and exits non-zero when a real run would refuse.
5. **As the PO, I do not want links into a folder that will be deleted.**
   - **Given** the script is started from a git worktree (a squad Developer branch), **then** it refuses, says why, and changes nothing; an explicit flag (name: the Tech Lead's) lets tests and QA run it from a worktree, with a warning in the output. **Given** the main checkout, **then** no flag is needed.

### Behaviour through the links (tasks 03, 04)

Same scene after install, `PATH` starting with `$HOME/.claude-accounts/bin`, stub `claude` printing its arguments and `CLAUDE_CONFIG_DIR`, stub `herdr` answering `workspace list`, `pane get`, `agent list`, `report-metadata` and logging calls.

6. **`c1`, `c2`, `c3`.** **Given** inside herdr (`HERDR_ENV=1`, `HERDR_WORKSPACE_ID=w23`), **when** I run `c2 --resume X`, **then** the stub claude gets `--resume X` with `CLAUDE_CONFIG_DIR=$HOME/.claude-2`, `workspace-default/w23` holds `2`, and the stub herdr received `workspace report-metadata w23 --source claude-accounts --token account=c2`. `c1` runs with `CLAUDE_CONFIG_DIR` unset; `c3` uses `~/.claude-3`. For 2 and 3 the shared items are linked into the account's folder. **Given** outside herdr, **then** no workspace file is written. **Given** `ACCT_NO_WS_DEFAULT=1`, **then** none is written either. **Given** the workspace write fails, **then** claude still starts.
7. **`c`.** **Given** a workspace file `3` for `w23`, **then** `c` starts account 3 in `w23`; **given** no workspace file, an invalid one, or outside herdr, **then** `c` starts the global default (`1`, `2` or `3` in `default`, else account 1). `c` writes no default.
8. **`cdefault`.** With no argument it prints the effective default. `cdefault 2` writes the global file and prints `default account: 2`; any other value prints `use 1, 2 or 3` and exits 2. `cdefault --ws 3` sets the current workspace (outside herdr: `usage: not inside herdr: give a workspace`, exit 2). `cdefault --ws <ref> N` resolves the ref by id, then panel number, then label (first tier with a hit wins); two equal labels print `ambiguous: <ref> matches` with the candidates and exit 2; an unknown, non-id-shaped ref prints `no workspace matches <ref>` and exits 2; an id-shaped unknown ref is taken as a raw id. A workspace write also drops files of workspaces herdr no longer lists, but not when the list is empty or fails.
9. **`.bashrc` line.** **Given** the PO's line (`export PATH=...; d=$(cdefault); case ... CLAUDE_CONFIG_DIR ...`) run in the scene, **then** PATH finds `c`; default 2 or 3 exports `CLAUDE_CONFIG_DIR=$HOME/.claude-N`; default 1 unsets it.
10. **`cswitch`.** `cswitch 2 [pane]` against the stub herdr waits for idle, sends `/exit`, then runs the launcher with the original arguments minus any earlier `--resume`, `--continue` and `--session-id`, plus `--resume <session>`, restores the herdr agent name, and appends a `-> account 2` line and a `done` line to `cswitch.log`. Errors: bad account prints `usage: cswitch 1|2|3 [pane]` (exit 2); outside herdr `not inside Herdr` (exit 1); no Claude session in the pane `no Claude session found in pane <p>` (exit 1). A claude that never exits gives a `FAILED` line.
11. **`cautoswitch`.** `--once --dry-run` against stub usage (workspace default at 5h >= threshold, another account lower on both 5h and 7d) prints and logs the move it would make, writes no default file and sends no key; without `--dry-run` it sets only the workspace default, never the global file; a lower account that is not lower on both is not chosen; outside herdr it exits with `not inside Herdr`; an expired token's refresh never makes a workspace default (`ACCT_NO_WS_DEFAULT`). No test reaches the network.
12. **Usage popup.** **Given** the usage cache `usage-1|2|3` and no usable login, **then** `usage-popup.sh` prints three accounts with their 5h and 7d bars and reset times, the default one tagged, and notes `cached Nm ago`; it never refreshes a token. **Given** an expired or missing token, **then** it says so, falls back to the cache, and still exits cleanly after a key press.
13. **Statusline recorder.** `record-usage.sh S 41 1730000000 12 1730500000` under no `CLAUDE_CONFIG_DIR` writes `usage-1` as `41 1730000000 12 1730500000 <epoch>`; under `CLAUDE_CONFIG_DIR=~/.claude-2` it writes `usage-2`; with an empty second argument it writes nothing. It runs when the statusline test is `-x` on the link.
14. **Real-home parity (final check, read-only).** The statusline's `[ -x ~/.claude-accounts/record-usage.sh ]` and herdr's `command = "~/.claude-accounts/usage-popup.sh"` keep working because the links keep their names and the files are executable; asserted on the scratch home by running exactly those two paths.

### Skill and docs (task 05)

15. **As an agent, I want the skill to load and be true.** **Given** the skill link, **then** `~/.claude/skills/claude-accounts/SKILL.md` loads, keeps the same commands table (c1-c3, c, cdefault incl. `--ws`, cswitch, cautoswitch), and no sentence names a file that no longer exists: `bin/cswitch.orig` and the `install-wsl.sh` setup line are corrected, and "where things live" says the source is `tools/claude-accounts/` and the install script links it.
16. **As the PO, I want a README that I can follow.** It says what the tool is, how to run the install script (after the merge, from the main checkout, `--dry-run` first), what stays in `~/.claude-accounts`, how to run the tests, and ends with a short **post-install check for the PO** (below). `HANDOFF.md` keeps its design records and hazards; only its install line changes.

### Tests (tasks 03, 04, 02)

17. The tool's tests run through `python3 tests/run_suite.py` (or by file), pass in a clean scratch `HOME`, and obey rule 6.

## PO post-install check (the README carries it; the squad cannot run it on the live home)

1. `ls -l ~/.claude-accounts ~/.claude-accounts/bin` shows links into `/home/chieule/workspace/squad/tools/claude-accounts/`, state files still real, no `*.bak-*`.
2. New shell: `type c1`, `cdefault` prints your account.
3. In herdr: `prefix+u` shows the popup; `cdefault --ws 2` then `cdefault` prints `2`; `cautoswitch --once --dry-run` prints a tick line.
4. Run `c1`, check it starts, then `/exit`; the statusline updates `~/.claude-accounts/usage-1`'s timestamp.
5. Retire `~/.claude-accounts/.git` when satisfied.

## Decisions (BA)

- **B1.** The install script never deletes `.git` (decision says "retired at cutover"; the script says so and the PO retires it). Reason: irreversible and not in the leftover list.
- **B2.** A real live file that differs from the repo stops the install unless `--force` (story 4). Reason: the live home was being edited when this scope started.
- **B3.** The install refuses to run from a worktree (story 5). Reason: squad close removes worktrees; every launcher would break.
- **B4.** Unlisted extra files stay and are named (QA I6).
- **B5.** Parity is checked by byte comparison of the scripts plus the behaviours above, not by re-running the live scripts on the PO's home.

## Open points

None for the PO. Known limit carried from `HANDOFF.md`: a herdr restart may reuse a workspace id and hand its old default to a new workspace; unchanged by this scope.
