"""Show one file in VS Code (ticket 34, decision D7/D9, `issues-tech/34.md`).

`open_file(abs_path)` runs `code --goto <abs path>` (file only: VS Code picks the window) and answers
`{"ok": bool, "how": "path" | "socket" | None, "why": None | "no-vscode" | "timeout" | "refused"}`. It never raises.
`post(server, params, body)` is the `POST /api/open` handler; the server (`squadboard.py`) has already checked the
Host, the page token and the Content-Type. This module only runs one local program; it writes no file.

The VS Code CLI exits 0 even when it refuses, so success is the exit code AND no refusal text in the output.
"""
import glob
import json
import os
import shutil
import socket
import subprocess
import threading
from pathlib import Path

TIMEOUT_S = 5
REFUSAL = "Command is only available in WSL or inside a Visual Studio Code terminal."
_BUSY = threading.Lock()  # one call at a time; a busy call is answered 429, no queue


def _live(sock_path):
    """True when something listens on this unix socket file. Dead socket files are left behind by closed windows."""
    af = getattr(socket, "AF_UNIX", None)
    if af is None:
        return False
    s = socket.socket(af, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect(sock_path)
        return True
    except OSError:
        return False
    finally:
        s.close()


def _sockets(env):
    runtime = env.get("XDG_RUNTIME_DIR") or "/run/user/%d" % os.getuid()
    out = []
    for d in (runtime, "/tmp"):
        out += sorted(glob.glob(os.path.join(d, "vscode-ipc-*.sock")), key=_mtime, reverse=True)
    return out


def _mtime(p):
    try:
        return os.path.getmtime(p)
    except OSError:
        return 0


def _remote_cli(env):
    home = env.get("HOME") or str(Path.home())
    found = glob.glob(os.path.join(home, ".vscode-server", "bin", "*", "bin", "remote-cli", "code"))
    found.sort(key=_mtime, reverse=True)  # newest server first
    return found[0] if found else None


def _pick(env):
    """-> (argv head, extra env, how) or None."""
    on_path = shutil.which("code", path=env.get("PATH"))
    if on_path:
        return [on_path], {}, "path"
    if env.get("WSL_DISTRO_NAME"):
        cli = _remote_cli(env)
        if cli:
            hook = env.get("VSCODE_IPC_HOOK_CLI")
            socks = ([hook] if hook else []) + _sockets(env)
            for s in socks:
                if _live(s):
                    return [cli], {"VSCODE_IPC_HOOK_CLI": s}, "socket"
    return None


def open_file(abs_path, env=None):
    env = dict(os.environ if env is None else env)
    p = str(abs_path)
    assert os.path.isabs(p) and not p.startswith("-"), "absolute path only"
    if os.name == "nt" and any(c in p for c in '&|<>^%"!'):
        return {"ok": False, "how": None, "why": "refused"}   # `code.cmd` runs through cmd.exe: these would be injection
    pick = _pick(env)
    if pick is None:
        return {"ok": False, "how": None, "why": "no-vscode"}
    head, extra, how = pick
    env.update(extra)
    try:
        r = subprocess.run(head + ["--goto", p], env=env, timeout=TIMEOUT_S, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return {"ok": False, "how": how, "why": "timeout"}
    except (OSError, ValueError):
        return {"ok": False, "how": how, "why": "refused"}
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0 or REFUSAL in out:
        return {"ok": False, "how": how, "why": "refused"}
    return {"ok": True, "how": how, "why": None}


def post(server, params, body):
    """POST /api/open?squad=<key>, body {"path": "<abs>"} -> (code, payload)."""
    if getattr(server, "demo", False):   # ticket 39 (D12): the demo never opens a file
        return 403, {"error": "disabled in the demo"}
    key = params.get("squad")
    squad = server.squad_by_key(key) if key else (server.squads[0] if len(server.squads) == 1 else None)
    if key and squad is None:   # the same answer as /api/file
        return 404, {"error": "unknown squad: %s. Known: %s" % (key, ", ".join(s.key for s in server.squads))}
    if squad is None or squad.flat:
        return 400, {"error": "squad required"}
    try:
        raw = json.loads(body.decode("utf-8")).get("path")
    except (ValueError, UnicodeError, AttributeError, RecursionError):
        return 400, {"error": "bad body"}
    if not isinstance(raw, str) or not raw or "\x00" in raw or raw.startswith("-") or ".." in Path(raw).parts:
        return 400, {"error": "bad path"}
    if not os.path.isabs(raw):
        return 400, {"error": "absolute path required"}
    try:
        real = Path(raw).resolve(strict=True)
    except (OSError, RuntimeError, ValueError):
        return 404, {"error": "not found"}
    if not any(real == r or r in real.parents for r in (squad.path, (squad.repo_root / ".scratch").resolve())):  # the rule of /api/file
        return 403, {"error": "path not allowed"}
    if not (real.is_file() or real.is_dir()):
        return 404, {"error": "not found"}
    if not _BUSY.acquire(blocking=False):
        return 429, {"error": "busy"}
    try:
        res = open_file(str(real))
    finally:
        _BUSY.release()
    return 200, {"data": res, "quality": "exact", "unknown": []}
post.json_only = True
