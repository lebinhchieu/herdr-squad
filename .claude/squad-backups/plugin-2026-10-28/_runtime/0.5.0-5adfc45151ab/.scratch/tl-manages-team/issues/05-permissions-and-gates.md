# T5 · Team Lead permissions and role gates
Status: ready-for-agent
Type: task
Blocked by: none
Repo: /home/chieule/workspace/squad (branch from main c1be501 unless the briefing names a base)
Spec: ../spec.md (B-ids) · Design: ../design.md (decision numbers) · Technical AC: `$SCOPE_DIR/evidence/qa-w-tech-ac.md` (AC ids)

## Files this task touches (and no others)
`templates/squad/settings/team-lead.json`, `bin/squad-spawn`, `bin/squad-retire`, `tests/test_team_lead_perms.py` (new).

## Do
- **Settings (decision 4).** Add to the allow list only: `Bash(squad-spawn dev:*)`, `Bash(squad-retire:*)`, `Bash(herdr agent list:*)`, `Bash(herdr agent get:*)`, `Bash(herdr agent read:*)`. Keep every deny. No `squad-start`, `squad-close`, `squad-usage`, `squad-label`, bare `squad-spawn:*`. Match the file's existing line style.
- **`squad-spawn`:** when `SQUAD_ROLE=team-lead` and the role is not `dev`: print `a Team Lead may only spawn dev` to stderr, exit 2, before any side effect. Other callers unchanged. **Exemption (QA-W A2):** a spawn whose `<name>` equals `$SQUAD_NAME` is allowed, because `bin/squad-respawn` runs `squad-spawn <role> <name>` in the caller's shell and a Team Lead respawning itself has role `team-lead`.
- **`squad-retire`:** when `SQUAD_ROLE=team-lead`, look the target up with `squad-usage --get <name>` (the caller's `SCOPE_DIR` roster); refuse with exit 2 and a message unless its role is `dev`. Other callers unchanged. A missing roster row is a refusal.
- Test as a new file; do not edit `test_squad_spawn.py`, `test_squad_retire.py`, `test_templates.py`. Cover: exact allow set for the Team Lead; the Team Lead cannot spawn `manager`, `tech-lead`, `team-lead`, `qa-whitebox`, `ba`; can `--dry-run` a `dev` with `--repo`, `--base`, `--title` and gets the role's model/effort unchanged; retire refuses a non-dev and a missing row, closes a dev; the Manager and Developer paths are unchanged; `squad-respawn <team-lead> --dry-run` works under the Team Lead env (name equals `$SQUAD_NAME`); `squad-spawn manager|tech-lead|team-lead <other-name>` under that env still exits 2.

## Technical AC
AC-3.2, AC-3.3 (run `squad-spawn --dry-run` with the Team Lead env and save the output in `dev-evidence.md`), AC-3.4 (two successive scripted roster edits on a copy, rows kept), "Always FAIL: a settings change broader than the role file justifies".

## Business AC
B4, B5 (permission side).
