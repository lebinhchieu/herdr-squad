"""Find a squad agent by session id in roster.md, for a hook run in a session that has no SQUAD_* variables
(herdr restores a pane with `claude --resume <id>`, which loses the variables squad-spawn set).

resolve(env, payload) returns a dict of SQUAD_NAME, SQUAD_ROLE, SQUAD_SCOPE, SQUAD_DIR and, when they apply,
SCOPE_DIR and GOAL_DIR, or None. The environment always wins: with SQUAD_NAME and SQUAD_DIR set it returns None.
Never raises, never prints. fill(env, payload) is the copy of env with the missing keys set from resolve."""
import os
import re
import subprocess
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9-]+$")
KEYS = ("SQUAD_NAME", "SQUAD_ROLE", "SQUAD_SCOPE", "SQUAD_DIR", "SCOPE_DIR", "GOAL_DIR")


def _roots(env, payload):
    """Project roots (folders holding .claude/squads) for the candidate working folders, in order."""
    cands = []
    for c in (env.get("CLAUDE_PROJECT_DIR"), payload.get("cwd") if isinstance(payload.get("cwd"), str) else None, os.getcwd()):
        if c and c not in cands:
            cands.append(c)
    roots = []

    def add(p):
        p = Path(p)
        if (p / ".claude" / "squads").is_dir() and p not in roots:
            roots.append(p)

    for c in cands:
        found = False
        for p in [Path(c), *Path(c).parents]:
            if (p / ".claude" / "squads").is_dir():
                add(p)
                found = True
                break
        if not found:  # a worktree outside the project: its main checkout, through git
            try:
                r = subprocess.run(["git", "-C", c, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5)
                if r.returncode == 0 and r.stdout.strip():
                    add(Path(r.stdout.strip()).parent)
            except (OSError, subprocess.SubprocessError):
                pass
    return roots


def _rosters(root):
    """roster.md paths of live scopes, goals and a flat squad; never a folder starting with `_` (_done, _runtime)."""
    base = root / ".claude" / "squads"
    out = []
    try:
        for squad in sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith("_")):
            for kind in ("scopes", "goals"):
                try:
                    out += sorted(r for r in (d / "roster.md" for d in (squad / kind).iterdir()
                                              if d.is_dir() and not d.name.startswith("_")) if r.is_file())
                except OSError:
                    pass
            if (squad / "roster.md").is_file():
                out.append(squad / "roster.md")
    except OSError:
        pass
    return out


def _row(roster, sid):
    """(name, role, scope) of the first row whose Session cell is exactly sid, else None."""
    try:
        text = roster.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    col = 5
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] == "Agent":
            col = cells.index("Session") if "Session" in cells else col
        elif len(cells) > col and cells[col] == sid and len(cells) >= 3:
            return cells[0], cells[1], cells[2]
    return None


def _goal_of(scope_dir):
    try:
        for line in (scope_dir / "scope.md").read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^goal:[ \t]*(\S*)", line)
            if m:
                return m.group(1)
    except OSError:
        pass
    return ""


def resolve(env, payload):
    try:
        if env.get("SQUAD_NAME") and env.get("SQUAD_DIR"):
            return None
        sid = payload.get("session_id") if isinstance(payload, dict) else None
        if not isinstance(sid, str) or not sid.strip():
            return None
        sid = sid.strip()
        for root in _roots(env, payload):
            for roster in _rosters(root):
                row = _row(roster, sid)
                if row is None:
                    continue
                name, role, scope = row
                squad_dir, home = roster.parents[2] if roster.parent.parent.name in ("scopes", "goals") else roster.parent, roster.parent
                out = {"SQUAD_NAME": name, "SQUAD_ROLE": role, "SQUAD_DIR": str(squad_dir)}
                if scope:
                    out["SQUAD_SCOPE"] = scope
                if roster.parent.parent.name == "scopes":
                    out["SCOPE_DIR"] = str(home)
                    goal = _goal_of(home)
                    if goal:
                        out["GOAL_DIR"] = str(squad_dir / "goals" / goal)
                elif roster.parent.parent.name == "goals":
                    out["GOAL_DIR"] = str(home)
                ok = NAME_RE.match(name) and NAME_RE.match(role) and (not scope or NAME_RE.match(scope))
                ok = ok and all(os.path.isdir(out[k]) for k in ("SQUAD_DIR", "SCOPE_DIR", "GOAL_DIR") if k in out)
                return out if ok else None
    except Exception:
        return None
    return None


def fill(env, payload):
    """A copy of env with every empty key of KEYS set from resolve (never overriding a set one)."""
    env = dict(env)
    found = resolve(env, payload)
    for k, v in (found or {}).items():
        if not env.get(k):
            env[k] = v
    return env
