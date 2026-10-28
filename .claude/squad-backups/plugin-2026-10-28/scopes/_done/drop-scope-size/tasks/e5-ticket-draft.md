# Draft ticket: remove QA blackbox Read deny; stop `rm /tmp` prompts

PO decision E5 (2026-10-27): remove the code-path Read deny from the plugin; the deny blocked QA blackbox from its own scope files. Also get rid of the repeated permission prompt on `rm /tmp/...`.

## Part 1: Read deny
- `templates/squad/settings/qa-blackbox.json`: drop the `Read(//CODE_PATHS_SET_BY_SQUAD_INIT/**)` entry.
- `bin/squadsettings.py`: drop PLACEHOLDER, `expand_code_paths`, the `codePaths` key and its fail-closed error; `squad-init` stops asking for code paths.
- Tests `tests/test_squadsettings.py`, `tests/test_squadadopt.py`; `SETTINGS-NOTES.md` text; squad `*.local.json` with `codePaths` (ignore or strip, never fail).
- SAFE-10 (QA blackbox stays blind to code) stays a rule, no longer enforced by a deny: say so in the rule's text.
- Interim (done by the Manager): this squad's `qa-blackbox.local.json` `codePaths` points at a nonexistent path so respawn stays valid; remove once this lands.

## Part 2: `rm /tmp/...` prompts
- Cause to confirm: the agents' allow lists have no `rm` entry, and /tmp is outside the repo, so Claude asks every time. SAFE-11 says use `mktemp -d`, `cd` out, then `rm`.
- Fix: in the dev, qa-whitebox and qa-blackbox (and manager, tech-lead, team-lead if they ever use scratch dirs) templates allow removing mktemp scratch dirs only: `Bash(rm -rf /tmp/tmp.*)`, `Bash(rm -r /tmp/tmp.*)`, `Bash(rm /tmp/tmp.*)`, `Bash(rmdir /tmp/tmp.*)` (Developer checks the exact matcher syntax against Claude Code docs and tests it live: `rm` of a `mktemp -d` dir must not prompt, `rm -rf /tmp/other` still must).
- SAFE-11 text: scratch dirs come from `mktemp -d` only, so the allow rule covers them; one line, no history.
- Test: template settings parse; the allow entries exist for the listed roles; no entry allows `rm` outside `/tmp/tmp.*`.

## Done when
Both parts merged with the full suite green; a live QA blackbox session reads `$SCOPE_DIR` files without a prompt.
