"""squad-board: CLI and local HTTP server of the dashboard (ADR 0020, architecture.md sections 1 and 6).

Read-only: the server reads squad files and writes nothing. (`board-ui.json` is written by ticket 09 through
`PUT_ROUTES`, the one hook this file keeps for it.) It listens on 127.0.0.1 only and refuses any other Host header.

Readers are discovered, not listed. Every `bin/squadboard_*.py` that defines `ROUTE` is loaded at start:

    ROUTE = {"name": "inbox", "path": "/api/inbox", "read": read, "selection": True}   # a dict, or a list of dicts

`read(sel) -> {"data": ..., "quality": ..., "unknown": [source, ...]}` and never raises (a raise or a run over
`READ_BUDGET_S` is answered as `unknown:<name>`; a missing `quality` or `unknown` is filled in). `sel` is a dict: `squads` (all `Squad`), `squad` (the chosen one
or None), `kind` ("goal" | "scope" | None), `name`, `home` (Path of that goal or scope folder), `repo_root`, `now` (epoch seconds from the server clock, fixed in tests),
`params` (the query as {key: first value}). `selection` defaults to True: the server answers
`400 selection required` unless `goal=` or `scope=` is given. A picker-style route sets it to False. A route whose
path equals a built-in one (`/api/squads`) replaces it. Every response carries `schema_version` (additive only).

Exit codes: 0 ok, 1 error (port busy), 2 refused (bad flags, unknown or ambiguous name, flat squad choice).
"""
import argparse
import importlib
import importlib.util
import json
import mimetypes
import os
import re
import secrets
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

BIN = Path(__file__).resolve().parent
if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))
import squadio  # noqa: E402

PLUGIN_ROOT = BIN.parent
STATIC_DIR = PLUGIN_ROOT / "templates" / "board"
SCHEMA_VERSION = 1
DEFAULT_PORT = 8765
HOSTS = ("127.0.0.1", "localhost")
READ_BUDGET_S = 3.0  # one constant for every reader; the page says "not updating" after 3 failed polls (architecture 1)
MAX_FILE = 5_000_000
OK, ERROR, REFUSED = 0, 1, 2
FLAT_MESSAGE = "flat squad: not supported"
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
CSP = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'"
PUT_ROUTES = {}  # path -> fn(server, params, body_bytes) -> dict. Ticket 09 registers `/api/ui` here.
FALLBACK_PAGE = ("<!doctype html><meta charset=utf-8><title>squad-board</title>"
                 "<p>squad-board is running. The page files (templates/board/index.html) are not installed yet.</p>")


class Refused(Exception):
    pass


class Squad:
    """One squad folder: `<repo>/.claude/squads/<name>`."""

    def __init__(self, path, key):
        self.path = Path(path).resolve()
        self.name = self.path.name
        self.key = key
        p = self.path.parents
        self.repo_root = p[2] if len(p) > 2 and p[0].name == "squads" and p[1].name == ".claude" else self.path.parent

    @property
    def flat(self):
        return not (self.path / "scopes").is_dir() or (self.path / "roster.md").exists()

    def names(self, kind):
        """Open names, then closed names (under `_done`), of "goals" or "scopes"."""
        def sub(d):
            try:
                return sorted(p.name for p in d.iterdir() if p.is_dir() and not p.name.startswith("_"))
            except OSError:
                return []
        return sub(self.path / kind), sub(self.path / kind / "_done")

    def find(self, kind, name):
        """Folder of the goal or scope `name` (open or closed), or None."""
        if not NAME_RE.match(name or ""):
            return None
        for rel in (kind + "s", kind + "s/_done"):
            d = self.path / rel / name
            if d.is_dir():
                return d
        return None


def _git_root():
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=10)
        top = r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        top = ""
    return Path(top or os.getcwd())


def _is_squad_dir(d):
    return d.is_dir() and any((d / n).exists() for n in ("process.md", "process.local.md", "scopes", "roster.md"))


def _squads_in(root):
    base = Path(root) / ".claude" / "squads"
    try:
        return sorted(p for p in base.iterdir() if _is_squad_dir(p))
    except OSError:
        return []


def _looks_like_path(arg):
    return "/" in arg or "\\" in arg or arg.startswith((".", "~")) or os.path.isabs(arg)


def find_squads(args, env=None):
    """-> [Squad]. Named squads (a NAME next to $SQUAD_DIR or in this repo, or a PATH), else $SQUAD_DIR, else every
    squad of this repo. Several and none named, or none at all, is Refused with the list. No other repo is scanned."""
    env = os.environ if env is None else env
    here = Path(env["SQUAD_DIR"]).resolve().parent if env.get("SQUAD_DIR") else _git_root() / ".claude" / "squads"
    known = [p.name for p in _squads_in(here.parent.parent)] if here.name == "squads" else []
    found = []
    for arg in args:
        cand = Path(arg).expanduser() if _looks_like_path(arg) else here / arg
        if not _is_squad_dir(cand):
            raise Refused("unknown squad: %s. Known squads: %s" % (arg, ", ".join(known) or "none"))
        found.append(cand.resolve())
    if not found:
        if env.get("SQUAD_DIR"):
            found = [Path(env["SQUAD_DIR"]).resolve()]
        else:
            found = [p.resolve() for p in _squads_in(_git_root())]
            if not found:
                raise Refused("no squad found in %s. Pass --squad NAME|PATH" % _git_root())
            if len(found) > 1:
                raise Refused("several squads here, name one with --squad (repeatable): %s" % ", ".join(p.name for p in found))
    out, seen = [], {}
    for p in dict.fromkeys(found):
        n = seen[p.name] = seen.get(p.name, 0) + 1
        out.append(Squad(p, p.name if n == 1 else "%s~%d" % (p.name, n)))
    return out


def initial_selection(squads, goal, scope):
    """-> {"squad": key, "goal"|"scope": name} or {}. Refused when the name is in no squad."""
    if goal and scope:
        raise Refused("--goal and --scope cannot be used together: pick one of --goal %s, --scope %s" % (goal, scope))
    kind, name = ("goal", goal) if goal else ("scope", scope) if scope else (None, None)
    if not kind:
        return {"squad": squads[0].key} if len(squads) == 1 else {}
    for s in squads:
        if not s.flat and s.find(kind, name):
            return {"squad": s.key, kind: name}
    known = []
    for s in squads:
        if not s.flat:
            o, c = s.names(kind + "s")
            known += ["%s/%s" % (s.key, n) for n in o + c]
    raise Refused("unknown %s: %s. Known %ss: %s" % (kind, name, kind, ", ".join(known) or "none"))


def _unknown_route(stem):
    """A reader that failed to load still answers: `unknown:<name>`, not a 404."""
    name = stem[len("squadboard_"):]
    return {"name": name, "path": "/api/" + name, "selection": False,
            "read": lambda sel: {"data": None, "quality": "unknown", "unknown": [name]}}


def load_routes(dirs=None):
    """-> (routes {path: route dict}, errors [module names]). Every `squadboard_*.py` with a `ROUTE` in `dirs`
    (default: this `bin/`). A module that does not import, or has a bad `ROUTE`, is skipped with one stderr line
    and its path answers `unknown:<name>`."""
    routes, errors = {}, []

    def skip(stem, why):
        errors.append(stem)
        print("squad-board: skipped reader %s (%s)" % (stem, why), file=sys.stderr)
        r = _unknown_route(stem)
        routes.setdefault(r["path"], r)

    for d in [BIN] if dirs is None else [Path(x) for x in dirs]:
        for f in sorted(d.glob("squadboard_*.py")):
            try:
                if d == BIN:
                    mod = importlib.import_module(f.stem)
                else:
                    spec = importlib.util.spec_from_file_location("squadboard_ext_" + f.stem, str(f))
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
            except Exception as e:  # a broken reader must not stop the board
                skip(f.stem, "%s: %s" % (type(e).__name__, e))
                continue
            raw = getattr(mod, "ROUTE", None)
            for r in (raw if isinstance(raw, list) else [raw] if raw else []):
                if isinstance(r, dict) and str(r.get("path", "")).startswith("/api/") and callable(r.get("read")):
                    routes[r["path"]] = r
                else:
                    skip(f.stem, "bad ROUTE")
    return routes, errors


class BoardServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = os.name != "nt"  # on Windows it would let a second process share a busy port

    def __init__(self, port, squads, initial=None, routes=None):
        super().__init__(("127.0.0.1", port), Handler)
        self.squads = squads
        self.initial = initial or {}
        self.token = secrets.token_urlsafe(24)
        self.routes, self.load_errors = (load_routes() if routes is None else (routes, []))
        self.put_routes = dict(PUT_ROUTES)
        self.clock = time.time

    @property
    def port(self):
        return self.server_address[1]

    def squad_by_key(self, key):
        for s in self.squads:
            if s.key == key or s.name == key:
                return s
        return None


def _squads_payload(server):
    rows = []
    for s in server.squads:
        row = {"name": s.name, "key": s.key, "path": str(s.path), "flat": s.flat}
        if s.flat:
            row["message"] = FLAT_MESSAGE
        else:
            row["goals"], row["closed_goals"] = s.names("goals")
            row["scopes"], row["closed_scopes"] = s.names("scopes")
        rows.append(row)
    return {"data": {"squads": rows, "multiple": len(rows) > 1, "initial": server.initial, "read_only": True},
            "quality": "exact", "unknown": []}


def _error(code, msg):
    return code, {"schema_version": SCHEMA_VERSION, "error": msg}


def resolve_selection(server, params):
    """-> (sel, None) or (None, (code, payload))."""
    key = params.get("squad")
    if key:
        squad = server.squad_by_key(key)
        if squad is None:
            return None, _error(404, "unknown squad: %s. Known: %s" % (key, ", ".join(s.key for s in server.squads)))
    else:
        squad = server.squads[0] if len(server.squads) == 1 else None
    sel = {"squads": server.squads, "squad": squad, "kind": None, "name": None, "home": None,
           "repo_root": squad.repo_root if squad else None, "now": server.clock(), "params": params}
    goal, scope = params.get("goal"), params.get("scope")
    if goal and scope:
        return None, _error(400, "give goal or scope, not both")
    kind, name = ("goal", goal) if goal else ("scope", scope) if scope else (None, None)
    if kind:
        if squad is None:
            return None, _error(400, "squad required")
        if squad.flat:
            return None, _error(400, FLAT_MESSAGE)
        home = squad.find(kind, name)
        if home is None:
            o, c = squad.names(kind + "s")
            return None, _error(404, "unknown %s: %s. Known %ss: %s" % (kind, name, kind, ", ".join(o + c) or "none"))
        sel.update(kind=kind, name=name, home=home)
    return sel, None


def call_reader(route, sel):
    """Run a reader with a time budget; never raises. -> the response dict (without schema_version)."""
    box = {}

    def run():
        try:
            box["r"] = route["read"](sel)
        except Exception:
            pass
    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(READ_BUDGET_S)
    r = box.get("r")
    if not isinstance(r, dict):
        return {"data": None, "quality": "unknown", "unknown": [route.get("name", route["path"])]}
    return {"data": None, "quality": "unknown", "unknown": [], **r}


def _under(path, roots):
    for r in roots:
        try:
            path.relative_to(r)
            return True
        except ValueError:
            pass
    return False


class Handler(BaseHTTPRequestHandler):
    server_version = "squad-board"
    protocol_version = "HTTP/1.0"

    def log_message(self, *a):
        pass

    # --- plumbing ---
    def _send(self, code, body, ctype, csp=CSP):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Security-Policy", csp)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, payload):
        payload = {"schema_version": SCHEMA_VERSION, **payload}
        self._send(code, json.dumps(payload).encode("utf-8"), "application/json; charset=utf-8")

    def _host_ok(self):
        host = self.headers.get("Host", "")
        name, _, port = host.rpartition(":") if ":" in host else (host, "", "")
        if name not in HOSTS or (port and port != str(self.server.port)):
            self._json(403, {"error": "host not allowed"})
            return False
        return True

    # --- verbs ---
    def do_GET(self):
        if not self._host_ok():
            return
        u = urlsplit(self.path)
        params = {k: v[0] for k, v in parse_qs(u.query).items()}
        path = u.path
        if path == "/" or path.startswith("/static/"):
            return self._static("index.html" if path == "/" else path[len("/static/"):])
        if path == "/api/session":
            return self._json(200, {"data": {"token": self.server.token, "port": self.server.port}, "quality": "exact", "unknown": []})
        if path == "/api/file":
            return self._file(params)
        route = self.server.routes.get(path)
        if route is None and path == "/api/squads":
            return self._json(200, _squads_payload(self.server))
        if route is None:
            return self._json(404, {"error": "not found"})
        if route.get("selection", True) and not (params.get("goal") or params.get("scope")):
            return self._json(400, {"error": "selection required"})
        sel, err = resolve_selection(self.server, params)
        if err:
            return self._json(*err)
        self._json(200, call_reader(route, sel))

    def _mutating(self):
        if not self._host_ok():
            return
        u = urlsplit(self.path)
        fn = self.server.put_routes.get(u.path) if self.command == "PUT" else None
        if fn is None:
            return self._json(405, {"error": "read-only: no write route"})
        if not secrets.compare_digest(self.headers.get("X-Board-Token", ""), self.server.token):
            return self._json(403, {"error": "token required"})
        try:
            n = min(int(self.headers.get("Content-Length", "0")), 1_000_000)
        except ValueError:
            n = 0
        params = {k: v[0] for k, v in parse_qs(u.query).items()}
        self._json(200, fn(self.server, params, self.rfile.read(n)))

    do_PUT = do_POST = do_DELETE = do_PATCH = _mutating

    # --- static and files ---
    def _static(self, name):
        f = STATIC_DIR / name if NAME_RE.match(name) else None
        if f is None or not f.is_file():
            if name == "index.html":
                return self._send(200, FALLBACK_PAGE.encode("utf-8"), "text/html; charset=utf-8")
            return self._json(404, {"error": "not found"})
        ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        self._send(200, f.read_bytes(), ctype)

    def _file(self, params):
        sel, err = resolve_selection(self.server, {"squad": params.get("squad")} if params.get("squad") else {})
        if err:
            return self._json(*err)
        squad = sel["squad"]
        if squad is None:
            return self._json(400, {"error": "squad required"})
        raw = params.get("path", "")
        if not raw or "\x00" in raw:
            return self._json(400, {"error": "path required"})
        p = Path(raw)
        try:
            real = (p if p.is_absolute() else squad.path / p).resolve(strict=True)
        except (OSError, RuntimeError, ValueError):
            return self._json(404, {"error": "not found"})
        if not _under(real, [squad.path, (squad.repo_root / ".scratch").resolve()]):
            return self._json(403, {"error": "path not allowed"})
        if not real.is_file():
            return self._json(404, {"error": "not found"})
        try:
            if real.stat().st_size > MAX_FILE:
                return self._json(413, {"error": "file too large"})
            body = real.read_bytes()
        except OSError:
            return self._json(404, {"error": "not found"})
        ext = real.suffix.lower()
        if ext in (".html", ".htm", ".svg", ".xhtml"):
            return self._send(200, body, "text/html; charset=utf-8", csp="sandbox")  # agent HTML: no script, own origin
        if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
            return self._send(200, body, mimetypes.guess_type(real.name)[0], csp="sandbox")
        self._send(200, body, "text/plain; charset=utf-8", csp="sandbox")


# --- CLI ---
def make_parser():
    p = argparse.ArgumentParser(
        prog="squad-board",
        description="Open the read-only dashboard of a squad on 127.0.0.1. Shows one goal or one scope at a time.")
    p.add_argument("--squad", action="append", default=[], metavar="NAME|PATH",
                   help="a squad name (next to $SQUAD_DIR or in this repo) or the path of a squad folder, even in another "
                        "repo; repeat it to open several. Needed when this repo has more than one squad")
    p.add_argument("--goal", metavar="G", help="open on this goal (not with --scope)")
    p.add_argument("--scope", metavar="S", help="open on this scope (not with --goal)")
    p.add_argument("--port", type=int, default=DEFAULT_PORT, metavar="N",
                   help="port on 127.0.0.1 (default %d; 0 picks a free one)" % DEFAULT_PORT)
    p.add_argument("--no-open", action="store_true", help="print the URL and do not start a browser")
    return p


def _url(server):
    q = "&".join("%s=%s" % kv for kv in server.initial.items())
    return "http://127.0.0.1:%d/%s" % (server.port, "?" + q if q else "")


def main(argv=None, open_browser=webbrowser.open, stop=None):
    """Run until Ctrl-C. `stop` (a threading.Event) lets a test end it; `open_browser` is replaceable."""
    squadio.utf8_stdio()
    args = make_parser().parse_args(sys.argv[1:] if argv is None else argv)
    if not 0 <= args.port <= 65535:
        print("squad-board: --port must be 0..65535", file=sys.stderr)
        return REFUSED
    try:
        squads = find_squads(args.squad)
        initial = initial_selection(squads, args.goal, args.scope)
    except Refused as e:
        print("squad-board: %s" % e, file=sys.stderr)
        return REFUSED
    try:
        server = BoardServer(args.port, squads, initial)
    except OSError as e:
        print("squad-board: port %d is busy or not allowed (%s). Pick another with --port N" % (args.port, e.strerror or e),
              file=sys.stderr)
        return ERROR
    url = _url(server)
    for s in squads:
        if s.flat:
            print("%s: %s" % (s.name, FLAT_MESSAGE))
    print("squad-board: %s (read-only, 127.0.0.1 only; Ctrl-C to stop)" % url, flush=True)
    if stop is not None:
        threading.Thread(target=lambda: (stop.wait(), server.shutdown()), daemon=True).start()
    if not args.no_open:
        try:
            open_browser(url)
        except Exception:
            print("squad-board: could not start a browser; open the URL above", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return OK
