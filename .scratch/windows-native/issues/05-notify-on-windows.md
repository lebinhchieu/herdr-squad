# 05: `squad-notify` on Windows

Status: done
Type: task
Blocked by: none
Source: findings.md W4

**What:** desktop notifications ("an agent is waiting") never fire on Windows. `bin/squad-notify` finds the client tty through `/proc` (absent on Windows; it then exits 0 quietly) and reads `~/.config/herdr/config.toml` (`bin/squad-notify:97`), while herdr on Windows keeps its config in `%APPDATA%\herdr\config.toml` (present on the test machine). Nothing tells the PO the feature is off.

**Needs info:** how herdr 0.9.3 on Windows shows a toast (a CLI call? a config key?). The PO or the herdr author decides the mechanism; until then this ticket is a design question.

## Do (once the mechanism is known)
- Read the config from `%APPDATA%\herdr` first when `os.name == "nt"`.
- Implement the Windows notification path, or document in README that notifications are Linux-only and print one line the first time on Windows.

## AC
- [ ] On Windows the PO either gets the toast or the README says why not.
- [ ] Linux behaviour unchanged; `test_squad_notify` still passes there.

## Comments
- 14-final: done; merged at eac3d93 (squad-notify reads %APPDATA%\herdr on Windows). PO to look at the toast once after merge.
