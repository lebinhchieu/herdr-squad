"""squad board M6: agents now and the permission-banner entries (ticket 08).

herdr lists every agent of the machine. Rows are kept only when the name is in the roster of the choice (the banner: of any
scope or goal of this squad). `herdr agent list` is called by name with a timeout; `sel["herdr_json"]` (`--herdr-json FILE`)
replaces the call with a recorded file. If herdr does not answer, `status` is "unknown" with a `reason` and the roster rows
keep their role (T08.AC7). Never raises, writes nothing.

    read(sel) -> data {status: "ok"|"unknown", reason, agents: [live rows], retired: [rows], retired_count}
    row = {name, role, task, status (working|idle|blocked|unknown), state (live|retired), last_activity, pane_id, scope}
    banner(sel) -> {"entries": [{agent, pane_id, scope}] | None (unknown), "reason"}   (ticket 05 imports this)
"""
import json
import subprocess
import sys
from pathlib import Path

BIN = Path(__file__).resolve().parent
if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))
import squadboard_active as active  # noqa: E402
import squadreport  # noqa: E402

TIMEOUT_S = 5
NOT_RUNNING = "herdr not running"
STATUSES = ("working", "idle", "blocked")


def parse_herdr(text):
    """herdr `agent list` JSON text -> ({name: {status, pane_id, cwd}}, None) or (None, reason). Pure."""
    try:
        o = json.loads(text)
        if not isinstance(o, dict):
            raise ValueError
    except ValueError:
        return None, "herdr answered badly"
    if o.get("error"):
        err = o["error"] if isinstance(o["error"], dict) else {}
        return None, NOT_RUNNING if err.get("code") == "server_not_running" else "herdr error"
    agents = (o.get("result") or {}).get("agents")
    if not isinstance(agents, list):
        return None, "herdr answered badly"
    out = {}
    for a in agents:
        if isinstance(a, dict) and a.get("name"):
            st = a.get("agent_status")
            out[str(a["name"])] = {"status": st if st in STATUSES else "unknown", "pane_id": a.get("pane_id"),
                                   "cwd": a.get("cwd")}
    return out, None


def fetch(sel):
    """-> ({name: info}, None) or (None, reason)."""
    f = sel.get("herdr_json")
    try:
        if f:
            return parse_herdr(Path(f).read_text(encoding="utf-8", errors="replace"))
        r = subprocess.run(["herdr", "agent", "list"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=TIMEOUT_S)
    except FileNotFoundError:
        return None, NOT_RUNNING if f is None else "herdr file missing"
    except (OSError, ValueError, subprocess.SubprocessError):
        return None, NOT_RUNNING if f is None else "herdr file unreadable"
    got, why = parse_herdr(r.stdout)
    if got is None and r.returncode != 0 and why == "herdr answered badly":
        why = NOT_RUNNING
    return got, why


def _homes(sel):
    """-> [(scope label, folder)] of the choice: a scope; a goal with its scopes."""
    home, squad = Path(sel["home"]), sel["squad"]
    out = [(sel["name"], home)]
    if sel["kind"] == "goal":
        for s in squad.names("scopes")[0] + squad.names("scopes")[1]:
            sh = squad.find("scope", s)
            if sh is not None and squadreport._scope_field(sh / "scope.md", "goal") == sel["name"]:
                out.append((s, sh))
    return out


def _all_homes(squad):
    out = []
    for kind in ("scope", "goal"):
        for n in squad.names(kind + "s")[0]:
            h = squad.find(kind, n)
            if h is not None:
                out.append((n, h))
    return out


def read(sel):
    try:
        got, why = fetch(sel)
        agents, retired = [], []
        for scope, home in _homes(sel):
            for r in active.roster_rows(home):
                info = (got or {}).get(r["name"], {})
                live = r["status"] == "live"
                row = {"name": r["name"], "role": r["role"], "task": r["owns"],
                       "status": info.get("status", "unknown") if live else "unknown",
                       "state": "live" if live else "retired", "pane_id": info.get("pane_id") if live else None,
                       "scope": scope, "last_activity": active.transcript_mtime(r["session"])}
                (agents if live else retired).append(row)
        ok = got is not None
        data = {"status": "ok" if ok else "unknown", "reason": why, "agents": agents, "retired": retired,
                "retired_count": len(retired)}
        return {"data": data, "quality": "exact" if ok else "unknown", "unknown": [] if ok else ["herdr"]}
    except Exception:
        return {"data": None, "quality": "unknown", "unknown": ["agents"]}


def banner(sel):
    """Blocked agents of every scope and goal of this squad (not the machine). entries None = herdr did not answer."""
    try:
        got, why = fetch(sel)
        if got is None:
            return {"entries": None, "reason": why}
        entries = []
        for scope, home in _all_homes(sel["squad"]):
            for r in active.roster_rows(home):
                info = got.get(r["name"])
                if r["status"] == "live" and info and info["status"] == "blocked":
                    entries.append({"agent": r["name"], "pane_id": info["pane_id"], "scope": scope})
        return {"entries": entries, "reason": None}
    except Exception:
        return {"entries": None, "reason": "banner failed"}


ROUTE = {"name": "agents", "path": "/api/agents", "read": read, "selection": True}
