# 01: `PATH=` env sent to `herdr tab create` is mangled on Windows

Status: ready-for-agent
Type: task
Blocked by: none
Source: findings.md W1 (blocker)

**What:** `squad-start` and every `squad-spawn` in a composed squad fail on Windows with `tab_create_failed … The system cannot find the file specified`, so no Manager (or any role) can start.

**Cause:** `bin/squad-spawn:199` builds `--env "PATH=$runtime/bin:$PATH"` (sent at `:329`). `$runtime` is the output of `squad-process runtime`, a Windows path (`C:\…\squad\0.6.1`, or `C:/…`). Mixed with the POSIX colon list in `$PATH`, Git Bash's argument conversion leaves the value alone, so herdr (a native exe) gives the new `pwsh` an unusable PATH. Presetting `runtime=` in the environment cannot work around it: line 101 resets `runtime=""`.

**Proof:** `--env "PATH=/c/…/bin:$PATH"` creates a tab; `--env "PATH=C:/…/bin:$PATH"` fails every time (see spec.md, reproduction).

## Do
- In `bin/squad-spawn`, turn `$runtime` into a POSIX path before building `runtime_env` (`cygpath -u`, falling back to the value unchanged where `cygpath` does not exist, e.g. Linux). Check the other `--env` values (`SQUAD_DIR`, `SCOPE_DIR`, `SQUAD_PLUGIN_DIR`) for the same list-vs-single-path trap; single paths are fine.
- Check `bin/squad-respawn` and any other script that builds a PATH override the same way (`grep -n 'PATH=' bin/`).

## AC
- [ ] With a shim `herdr` that logs argv, `squad-start` on Windows passes a `PATH=` value containing no `C:\` or `C:/` segment and ending in the caller's PATH.
- [ ] A test pins that (shim-based, runs on Linux too with a fake `cygpath` or a Windows-form `runtime`).
- [ ] On the Windows machine, `squad-start` opens a Manager tab and the Manager can run `squad-spawn` from its own tab. (Needs a herdr pane; the PO or Manager does the live check.)
- [ ] Linux output unchanged.

## Comments
