# QA blackbox, task 14 (final b2ee4e5; handed in cb9b925, 8d9e931, b2ee4e5)

Method: (1) `squadsettings.effective()` per role on a scratch squad with `settings/<role>.local.json` overlays; (2) live `claude -p --settings templates/squad/settings/qa-blackbox.json` (haiku, default permission mode), one Bash command per run, count of `permission_denials` and whether the target survived; (3) `compose` + `lint`.

| Check | Saw | Result |
|---|---|---|
| Effective qa-blackbox settings: no Read deny | `Read deny: []` with empty overlay | PASS |
| Old overlay `codePaths` (list / bad string) | ignored, never fails, no code key in result; other overlay allows kept; an overlay's own Read deny still merged | PASS |
| rm allow entries in dev, qa-white, qa-black, manager, tech-lead, team-lead | 4 each (`rm -rf`, `rm -r`, `rm`, `rmdir` on `/tmp/tmp.*`); token-coach/ba/designer/architect none; token-coach keeps its own Read denies | PASS |
| `Bash(squad-team:*)` in manager.json | present | PASS |
| Live: `rm -rf <mktemp -d>` | 0 denials, dir gone | PASS |
| Live: `rmdir <mktemp -d>` | 0 denials, dir gone | PASS |
| Live: `rm -rf /tmp/tmp.X/../other/zz`, `rm -rf /tmp/other`, `rm -rf /tmp/tmp.X /tmp/other/zz`, `rm -rf /tmp/tmp.$(...)`, `rm /tmp/file`, `A ; touch B` | each 1 denial, target survived, nothing ran | PASS |
| SAFE-10 text | "no setting enforces this"; rule kept | PASS |
| SAFE-11 text | "Scratch dirs: `mktemp -d` only." one line | PASS |
| `lint` | empty | PASS |

Findings: none. Not tested: a full qa-blackbox session reading `$SCOPE_DIR` files (the Manager removes the interim local overlay after merge; my own session still runs the old deny).
