"""The scratch repo of ticket 02 (squad-tree): built in code so every file time is fixed.

    build_repo(root) -> root      squads: `plugin` (goal g1: api, ui, docs[done]; lone fix; done goal g0 with old;
                                  done lone tiny) and `old-flat` (a flat squad)
    herdr_stub(bin_dir, up)       a `herdr` script for PATH: `agent list` answers api-dev working (up) or exits 1

Clock: every live file is 2026-11-12T09:30:00Z; closed homes carry their own close time.
"""
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

LIVE = datetime(2026, 11, 12, 9, 30, tzinfo=timezone.utc)
HEAD = "# Escalations\n\n| # | Date | Question | Options | Manager's recommendation | Blocks | Answer |\n|---|---|---|---|---|---|---|\n"


def _w(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _tickets(root, slug, done, total):
    for n in range(1, total + 1):
        _w(root / ".scratch" / slug / "issues" / ("%02d-t.md" % n),
           "# %02d: t\n\nStatus: %s\n" % (n, "done" if n <= done else "ready-for-agent"))


def _scope(home, brief, goal=None, tickets=None, open_q=None, agents=("x-dev",), messages=()):
    text = "# Scope: %s\n\n**%s**\n\n%s%s" % (home.name, brief, "goal: %s\n" % goal if goal else "goal:\n",
                                              "tickets: %s\n" % tickets if tickets else "")
    _w(home / "scope.md", text)
    if open_q is not None:
        _w(home / "escalations.md", HEAD + "".join("| %d | 2026-11-12 | Q%d? | a | a | none | |\n" % (i, i)
                                                  for i in range(1, open_q + 1)))
    _w(home / "roster.md", "# Roster\n| Agent | Role | Scope | Owns | Status | Session |\n| --- | --- | --- | --- | --- | --- |\n"
       + "".join("| %s | developer | %s | x | live | s |\n" % (a, home.name) for a in agents))
    _w(home / "messages.jsonl", "".join(json.dumps(m) + "\n" for m in messages))


def _stamp(root, when, close=None):
    """Every file and folder of the live tree at `when`; closed homes (`close`: {path: datetime}) at their time."""
    for dirpath, dirs, files in os.walk(str(root), topdown=False):
        for n in files + dirs:
            p = os.path.join(dirpath, n)
            if ".git" not in Path(p).parts:
                os.utime(p, (when.timestamp(),) * 2)
    for p, t in (close or {}).items():
        os.utime(str(p), (t.timestamp(),) * 2)


def build_repo(root):
    root = Path(root)
    sq = root / ".claude" / "squads" / "plugin"
    _w(sq / "process.md", "process\n")
    _w(sq / "goals" / "g1" / "goal.md", "# Goal: g1\n\n**Brief of g1**\n")
    _w(sq / "goals" / "_done" / "g0" / "goal.md", "# Goal: g0\n\n**Brief of g0**\n")
    _scope(sq / "scopes" / "api", "Brief of api", "g1", "api", 2, ("api-dev",))
    _scope(sq / "scopes" / "ui", "Brief of ui", "g1", "ui", 0, ("ui-dev",))
    _scope(sq / "scopes" / "_done" / "docs", "Brief of docs", "g1", "docs", 0)
    _scope(sq / "scopes" / "fix", "Brief of fix", None, "fix", 0, ("fix-dev",),
           [{"ts": "2026-11-12T09:00:00.000Z", "msg_id": "m1", "from": "plugin-dev-fix", "to": "plugin-mgr-fix",
             "type": "BLOCKED", "task": "02", "text": "BLOCKED 02: waiting", "iteration": 1}])
    _scope(sq / "scopes" / "_done" / "old", "Brief of old", "g0")
    _scope(sq / "scopes" / "_done" / "tiny", "Brief of tiny")
    _tickets(root, "api", 1, 3)
    _tickets(root, "ui", 0, 2)
    _tickets(root, "docs", 2, 2)
    _tickets(root, "fix", 1, 4)
    flat = root / ".claude" / "squads" / "old-flat"
    _w(flat / "roster.md", "# Roster\n")
    _w(root / "README.md", "scratch\n")
    for args in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-q", "-m", "base"]):
        subprocess.run(["git", *args], cwd=str(root), check=True, capture_output=True,
                       env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})
    done = lambda *a: datetime(*a, tzinfo=timezone.utc)  # noqa: E731
    _stamp(root, LIVE, {sq / "scopes" / "_done" / "docs": done(2026, 11, 11, 18), sq / "goals" / "_done" / "g0": done(2026, 11, 1, 12),
                        sq / "scopes" / "_done" / "old": done(2026, 11, 1, 12), sq / "scopes" / "_done" / "tiny": done(2026, 11, 5, 12)})
    return root


def herdr_stub(bin_dir, up):
    """Write `<bin_dir>/herdr` (a python script). Returns the directory to put first on PATH."""
    body = ('#!/usr/bin/env python3\nimport sys\n%s\n' % (
        'print(\'{"result": {"agents": [{"name": "api-dev", "agent_status": "working"}]}}\')' if up else "sys.exit(1)"))
    p = Path(bin_dir) / "herdr"
    p.write_text(body, encoding="utf-8", newline="\n")
    p.chmod(0o755)
    return str(bin_dir)
