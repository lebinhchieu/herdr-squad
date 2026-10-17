"""Shared harness for the claude-accounts tests (tasks 03, 04): a temp HOME with the scripts linked in per
file, and stub `herdr`, `claude` and `pgrep` first on a minimal PATH. Never the real ~/.claude-accounts,
never the PO's real herdr/claude, never the network. See scopes/ca-repo/design.md "Test harness".

Fixtures in tests/fixtures/ca/: *.real.json are real herdr captures; pane-get-nosession.derived.json is the
real pane JSON minus `agent` and `agent_session` (no real no-session capture exists). Lists with several
workspaces are built from workspace-list.real.json by editing values (Env.set_workspaces)."""
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "tools" / "claude-accounts"
FIX = Path(__file__).resolve().parent / "fixtures" / "ca"
PANE = "w26:p7"  # the pane of the real pane-get / agent-list captures

requires_linux = unittest.skipUnless(
    sys.platform.startswith("linux") and shutil.which("bash") and shutil.which("jq") and os.path.isdir("/proc"),
    "the launchers need Linux with bash, jq and /proc (ADR 0011: Windows is not a target)")

_COMMON = f'''import json, os, sys
S = os.environ["CA_STUB"]
def append(name, text):
    with open(S + "/" + name, "a", encoding="utf-8") as f:
        f.write(text)
'''

HERDR_STUB = "#!" + sys.executable + "\n" + _COMMON + '''
import signal, subprocess
argv = sys.argv[1:]
append("herdr.log", json.dumps({"argv": argv}) + "\\n")

def live_claude(pane):
    """Pids of live stub claudes of a pane (not zombies, not `claude daemon run`)."""
    try:
        pids = [int(x) for x in open(S + "/pids", encoding="utf-8").read().split()]
    except OSError:
        return []
    out = []
    for p in pids:
        try:
            stat = open("/proc/%d/stat" % p, encoding="utf-8").read()
            cmd = open("/proc/%d/cmdline" % p, "rb").read().split(b"\\0")
            env = open("/proc/%d/environ" % p, "rb").read().split(b"\\0")
        except OSError:
            continue
        if stat.rsplit(")", 1)[1].split()[0] == "Z" or (len(cmd) > 1 and cmd[1] == b"daemon"):
            continue
        if ("HERDR_PANE_ID=" + pane).encode() in env:
            out.append(p)
    return out

def serve(name):
    try:
        data = open(S + "/" + name, "rb").read()
    except OSError:
        sys.exit(1)
    sys.stdout.flush(); sys.stdout.buffer.write(data); sys.stdout.buffer.flush()

if argv[:2] == ["workspace", "list"]:
    if os.path.exists(S + "/workspaces.fail"):
        sys.exit(1)
    serve("workspaces.bad" if os.path.exists(S + "/workspaces.bad") else "workspaces.json")
elif argv[:2] == ["workspace", "report-metadata"]:
    if os.path.exists(S + "/report.hang"):
        import time; time.sleep(10)
elif argv[:2] == ["pane", "get"]:
    pane = argv[2]
    try:
        data = json.load(open(S + "/panes/" + pane + ".json", encoding="utf-8"))
    except OSError:
        sys.exit(1)
    if not live_claude(pane):  # the agent is gone: real herdr drops both keys
        data["result"]["pane"].pop("agent", None)
        data["result"]["pane"].pop("agent_session", None)
    print(json.dumps(data, separators=(",", ":")))
elif argv[:2] == ["agent", "list"]:
    serve("agents.json")
elif argv[:2] == ["agent", "prompt"] and argv[3:4] == ["/exit"]:
    for p in live_claude(argv[2]):
        os.kill(p, signal.SIGTERM)
elif argv[:2] == ["pane", "run"]:
    pane, cmd = argv[2], argv[3]
    try:
        ws = json.load(open(S + "/panes/" + pane + ".json", encoding="utf-8"))["result"]["pane"]["workspace_id"]
    except (OSError, KeyError):
        ws = "w26"
    env = dict(os.environ, HERDR_ENV="1", HERDR_PANE_ID=pane, HERDR_WORKSPACE_ID=ws)
    subprocess.Popen(["bash", "-c", cmd], env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)
'''

# CLAUDE_STUB_MODE=exit (default): record and exit 0. sleep: also register the pid, then wait for SIGTERM
# (bounded to 2 minutes, a safety net so a failed test cannot leave it running).
CLAUDE_STUB = "#!" + sys.executable + "\n" + _COMMON + '''
import signal, time
e = os.environ.get
append("claude.jsonl", json.dumps({"argv": sys.argv[1:], "CLAUDE_CONFIG_DIR": e("CLAUDE_CONFIG_DIR"),
    "HERDR_PANE_ID": e("HERDR_PANE_ID"), "HERDR_ENV": e("HERDR_ENV"),
    "HERDR_WORKSPACE_ID": e("HERDR_WORKSPACE_ID"), "SQUAD_NAME": e("SQUAD_NAME")}) + "\\n")
if e("CLAUDE_STUB_MODE") == "sleep":
    append("pids", "%d\\n" % os.getpid())
    signal.signal(signal.SIGTERM, lambda *a: sys.exit(0))
    for _ in range(1200):
        time.sleep(0.1)
'''

# Lists only the pids in $CA_STUB/pids that are alive: the real pgrep would see the PO's live agents.
PGREP_STUB = """#!/usr/bin/env bash
for p in $(cat "$CA_STUB/pids" 2>/dev/null); do
  s=$(cat "/proc/$p/stat" 2>/dev/null) || continue
  case "${s##*) }" in Z*) continue ;; esac
  echo "$p"
done
"""

_TOOLS = ("bash", "jq", "python3", "timeout", "cat", "mktemp", "date", "sleep", "grep", "sed", "seq", "tr", "cut",
          "mv", "rm", "mkdir", "ln", "id", "env", "nohup", "dirname", "basename")


def _tool_dirs():
    dirs = []
    for t in _TOOLS:
        w = shutil.which(t)
        if w and os.path.dirname(w) not in dirs:
            dirs.append(os.path.dirname(w))
    return dirs


def live(pid):
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except OSError:
        return False
    return stat.rsplit(")", 1)[1].split()[0] != "Z"


class Env:
    """One test's world. Call cleanup() in tearDown (or addCleanup): it kills every process started by pid."""

    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ca-test-"))
        self.home = self.tmp / "home"
        self.stub = self.tmp / "stub"
        (self.stub / "bin").mkdir(parents=True)
        (self.stub / "panes").mkdir()
        (self.home / ".claude" / "skills").mkdir(parents=True)
        (self.home / ".claude" / "CLAUDE.md").write_text("# test\n", encoding="utf-8")
        (self.home / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
        acct = self.acct = self.home / ".claude-accounts"
        (acct / "bin").mkdir(parents=True)
        for f in SRC.iterdir():
            if f.is_file() and f.suffix == ".sh":
                (acct / f.name).symlink_to(f)
        for f in (SRC / "bin").iterdir():
            (acct / "bin" / f.name).symlink_to(f)
        for name, body in (("herdr", HERDR_STUB), ("claude", CLAUDE_STUB), ("pgrep", PGREP_STUB)):
            p = self.stub / "bin" / name
            p.write_text(body, encoding="utf-8")
            p.chmod(0o755)
        self.env = {
            "HOME": str(self.home),
            "PATH": os.pathsep.join([str(self.stub / "bin")] + _tool_dirs()),
            "CA_STUB": str(self.stub),
            "HTTPS_PROXY": "http://127.0.0.1:9", "HTTP_PROXY": "http://127.0.0.1:9",
            "ALL_PROXY": "http://127.0.0.1:9",
            "LC_ALL": "C.UTF-8",
        }
        self.procs = []
        self.groups = []

    # -- processes ---------------------------------------------------------------------------------------
    def popen(self, argv, env=None, session=False, **kw):
        for k in ("stdin", "stdout", "stderr"):  # never hold the test runner's pipes open
            kw.setdefault(k, subprocess.DEVNULL)
        p = subprocess.Popen(argv, env=dict(self.env, **(env or {})), start_new_session=session, **kw)
        self.procs.append(p)
        if session:
            self.groups.append(p.pid)
        return p

    def spawn_claude(self, pane, args=(), extra_env=None):
        """A stub claude (sleep mode) that carries HERDR_PANE_ID, as a running agent does. Returns the Popen."""
        env = {"CLAUDE_STUB_MODE": "sleep", "HERDR_PANE_ID": pane, "HERDR_ENV": "1", **(extra_env or {})}
        p = self.popen([str(self.stub / "bin" / "claude"), *args], env=env)
        self.wait_for(lambda: p.pid in self.pids(), "stub claude never registered")
        return p

    def spawn_decoy(self, pane):
        """A `claude daemon run` look-alike of the same pane; cswitch must skip it. Registered first in pids."""
        d = self.tmp / "decoy"
        d.mkdir()
        # a bash builtin wait (no child process that could outlive the kill and hold a pipe)
        (d / "daemon").write_text('mkfifo f; exec 3<>f; read -t 100 -u 3\n', encoding="utf-8")
        p = self.popen(["bash", "daemon", "run"], env={"HERDR_PANE_ID": pane}, cwd=d)
        with open(self.stub / "pids", "a", encoding="utf-8") as f:
            f.write(f"{p.pid}\n")
        return p

    def pids(self):
        try:
            return [int(x) for x in (self.stub / "pids").read_text(encoding="utf-8").split()]
        except OSError:
            return []

    def cleanup(self):
        """Kill by pid only (no pkill, no pgrep -f), then assert nothing registered is left alive."""
        for g in self.groups:
            try:
                os.killpg(g, signal.SIGKILL)
            except OSError:
                pass
        everyone = set(self.pids()) | {p.pid for p in self.procs}
        for pid in everyone:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        for p in self.procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        deadline = time.time() + 3
        left = [p for p in everyone if live(p)]
        while left and time.time() < deadline:
            time.sleep(0.05)
            left = [p for p in everyone if live(p)]
        shutil.rmtree(self.tmp, ignore_errors=True)
        if left:
            raise AssertionError(f"processes left alive: {left}")

    # -- running scripts ---------------------------------------------------------------------------------
    def run(self, cmd, *args, env=None, timeout=30):
        """A launcher by name (bin/<cmd>). Returns CompletedProcess (text)."""
        return subprocess.run([str(self.acct / "bin" / cmd), *args], env=dict(self.env, **(env or {})),
                              capture_output=True, text=True, encoding="utf-8", timeout=timeout)

    def sh(self, script, *args, env=None, timeout=30):
        """Source lib.sh and run a bash snippet; args are $1.. of the snippet."""
        return subprocess.run(["bash", "-c", '. "$HOME/.claude-accounts/lib.sh"; ' + script, "bash", *args],
                              env=dict(self.env, **(env or {})), capture_output=True, text=True,
                              encoding="utf-8", timeout=timeout)

    def wait_for(self, cond, msg, timeout=40):
        """Wait for a state that stays; the failure message names what was missing."""
        end = time.time() + timeout
        while time.time() < end:
            if cond():
                return
            time.sleep(0.05)
        raise AssertionError(msg)

    # -- stub herdr state --------------------------------------------------------------------------------
    def set_workspaces(self, *rows):
        """rows: (workspace_id, number, label), built by editing the real capture's one entry."""
        real = json.loads((FIX / "workspace-list.real.json").read_text(encoding="utf-8"))
        tmpl = real["result"]["workspaces"][0]
        real["result"]["workspaces"] = [dict(tmpl, workspace_id=i, number=n, label=l) for i, n, l in rows]
        (self.stub / "workspaces.json").write_text(json.dumps(real, separators=(",", ":")), encoding="utf-8")

    def set_workspaces_real(self):
        shutil.copy(FIX / "workspace-list.real.json", self.stub / "workspaces.json")

    def set_pane(self, fixture="pane-get-claude.real.json", pane=PANE):
        shutil.copy(FIX / fixture, self.stub / "panes" / f"{pane}.json")

    def set_agents(self):
        shutil.copy(FIX / "agent-list.real.json", self.stub / "agents.json")

    def herdr_calls(self):
        """Every herdr call as an argv list (JSON log: a label with a space survives)."""
        try:
            lines = (self.stub / "herdr.log").read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        return [json.loads(l)["argv"] for l in lines]

    def claude_calls(self):
        try:
            lines = (self.stub / "claude.jsonl").read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        return [json.loads(l) for l in lines]

    # -- state files -------------------------------------------------------------------------------------
    def default_file(self, value):
        (self.acct / "default").write_text(value, encoding="utf-8")

    def ws_file(self, ws_id):
        p = self.acct / "workspace-default" / ws_id
        return p.read_text(encoding="utf-8") if p.exists() else None
