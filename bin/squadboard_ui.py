"""Saved UI state of the dashboard (ticket 09, architecture.md sections 1 and 1a).

The one file the board writes: `<squad folder>/board-ui.json`. The path comes from the server's squad choice, never
from a request. Layout is stored as order, column span, hidden and an optional max height per panel: no pixel
position and no row index (a saved layout then survives a font change or a window resize).

    {"version": 1, "saved_at": "2026-11-04T10:00:00Z", "font": "normal",
     "choice": {"kind": "scope", "name": "dashboard"} | null, "recent": [<choice>, ...5],
     "panels": {"<panel id>": {"order": 0, "span": 2, "hidden": false, "max_height": 300}}}

`GET /api/ui?squad=K` -> data {"ui": {...}, "status": "ok" | "unwritable" | "unreadable"}; it never raises and never
writes. `PUT /api/ui?squad=K` (token and Host are checked by the server before this runs) -> the saved ui, or a JSON
error. Two writers: temp file in the same folder, fsync, `os.replace`; the last one wins, the file is never half.
"""
import json
import os
import re
import tempfile
import time
from pathlib import Path

FILE = "board-ui.json"
VERSION = 1
MAX_BODY = 64 * 1024
RECENT_MAX = 5
FONTS = ("small", "normal", "xl")
SAVED_AT_RE = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?Z$")
REPLACE_TRIES = 3
NO_POSITION_KEYS = ("x", "y", "row", "".join(("si", "ze")))  # layout is order and span only (architecture 1a)


def _no_constant(name):
    raise ValueError("%s is not valid JSON" % name)


def defaults():
    return {"version": VERSION, "saved_at": None, "font": "normal", "choice": None, "recent": [], "panels": {}}


def _int(v, lo=0):
    return isinstance(v, int) and not isinstance(v, bool) and v >= lo


def _choice(c):
    if c is None:
        return None
    if not (isinstance(c, dict) and c.get("kind") in ("goal", "scope") and isinstance(c.get("name"), str) and c["name"]):
        raise ValueError("choice must be null or {kind: goal|scope, name}")
    return {"kind": c["kind"], "name": c["name"]}


def validate(body):
    """-> the ui dict to store. Raises ValueError (message for the 400) on a wrong type; unknown top-level keys are kept."""
    if not isinstance(body, dict):
        raise ValueError("body must be a JSON object")
    bad = [k for k in NO_POSITION_KEYS if k in body]
    if bad:
        raise ValueError("no position keys in the layout: %s" % ", ".join(bad))
    ui = {k: v for k, v in body.items() if k not in ("path", "squad")}  # never taken from the request
    ui["version"] = VERSION
    saved_at = body.get("saved_at")
    if not (isinstance(saved_at, str) and SAVED_AT_RE.match(saved_at)):
        raise ValueError("saved_at must be a UTC ISO string ending in Z")
    ui["font"] = body.get("font", "normal")
    if ui["font"] not in FONTS:
        raise ValueError("font must be one of %s" % ", ".join(FONTS))
    ui["choice"] = _choice(body.get("choice"))
    recent = body.get("recent", [])
    if not isinstance(recent, list):
        raise ValueError("recent must be a list")
    seen, out = set(), []
    for c in recent:
        c = _choice(c)
        if c is None:
            raise ValueError("recent holds choices, not null")
        key = (c["kind"], c["name"])
        if key not in seen:
            seen.add(key)
            out.append(c)
    ui["recent"] = out[:RECENT_MAX]
    panels = body.get("panels", {})
    if not isinstance(panels, dict):
        raise ValueError("panels must be an object")
    clean = {}
    for pid, p in panels.items():
        if isinstance(p, dict) and any(k in p for k in NO_POSITION_KEYS):
            raise ValueError("panel %s: no position keys, use order and span" % pid)
        if not (isinstance(p, dict) and _int(p.get("order")) and _int(p.get("span"), 1)
                and isinstance(p.get("hidden", False), bool)
                and (p.get("max_height") is None or _int(p.get("max_height"), 1))):
            raise ValueError("panel %s: order and span are integers, hidden a boolean, max_height optional" % pid)
        row = {"order": p["order"], "span": p["span"], "hidden": p.get("hidden", False)}
        if p.get("max_height") is not None:
            row["max_height"] = p["max_height"]
        clean[str(pid)] = row
    ui["panels"] = clean
    try:
        json.dumps(ui, ensure_ascii=False, allow_nan=False).encode("utf-8")  # NaN, lone surrogates
    except (ValueError, UnicodeError) as e:
        raise ValueError("not storable: %s" % e)
    return ui


def _writable(folder):
    f = Path(folder) / FILE
    try:
        if f.exists():
            return os.access(f, os.W_OK) and os.access(folder, os.W_OK)
        return os.access(folder, os.W_OK)
    except OSError:
        return False


def read_state(folder):
    """-> (ui, status). Never raises, never writes."""
    f = Path(folder) / FILE
    status = "ok"
    ui = defaults()
    try:
        if f.exists():
            raw = json.loads(f.read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or raw.get("version") != VERSION:
                raise ValueError("unknown version")
            ui = {**defaults(), **raw}
    except (OSError, ValueError, UnicodeError, RecursionError):
        return defaults(), "unreadable"
    if not _writable(folder):
        status = "unwritable"
    return ui, status


def write_state(folder, ui):
    """Atomic write of `ui`. Raises OSError when the folder or file cannot be written; the old file stays whole."""
    folder = Path(folder)
    text = json.dumps(ui, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    try:
        mode = (folder / FILE).stat().st_mode & 0o777
    except OSError:
        mode = 0o644
    fd, tmp = tempfile.mkstemp(dir=str(folder), prefix=FILE + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, mode)  # mkstemp is 0600; keep the file's own mode
        for i in range(REPLACE_TRIES):
            try:
                os.replace(tmp, str(folder / FILE))
                return
            except PermissionError:  # Windows: the file is open elsewhere (ADR 0011)
                if i == REPLACE_TRIES - 1:
                    raise
                time.sleep(0.05)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _squad(server, params):
    key = params.get("squad")
    if key:
        return server.squad_by_key(key)
    return server.squads[0] if len(server.squads) == 1 else None


def read(sel):
    squad = sel.get("squad")
    if squad is None:
        return {"data": None, "quality": "unknown", "unknown": ["ui"]}
    ui, status = read_state(squad.path)
    return {"data": {"ui": ui, "status": status}, "quality": "exact", "unknown": []}


def put(server, params, body):
    """PUT /api/ui. Returns (code, payload)."""
    if len(body) > MAX_BODY:
        return 413, {"error": "body too large", "status": "refused"}
    squad = _squad(server, params)
    if squad is None:
        return 400, {"error": "squad required", "status": "refused"}
    try:
        ui = validate(json.loads(body.decode("utf-8"), parse_constant=_no_constant))
    except (ValueError, UnicodeError, RecursionError) as e:
        return 400, {"error": "bad body: %s" % e, "status": "refused"}
    if not _writable(squad.path):
        return 507, {"error": "settings file not writable", "status": "unwritable"}
    try:
        write_state(squad.path, ui)
    except OSError as e:
        return 507, {"error": "settings file not writable: %s" % (e.strerror or type(e).__name__), "status": "unwritable"}
    return 200, {"data": {"ui": ui, "status": "ok"}, "quality": "exact", "unknown": []}


put.json_only = True  # the server answers 415 to any other Content-Type
ROUTE = {"name": "ui", "path": "/api/ui", "read": read, "selection": False, "put": put}
