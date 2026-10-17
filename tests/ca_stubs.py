"""Shared fixtures for the claude-accounts launcher tests: a temp HOME with the launchers
linked in, and stub `claude`, `herdr` and `nohup` on PATH. Never touches the real ~/.claude-accounts."""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "tools" / "claude-accounts"

CLAUDE_STUB = """#!/usr/bin/env bash
{ echo "CLAUDE_CONFIG_DIR=${CLAUDE_CONFIG_DIR-<unset>}"; for a in "$@"; do echo "ARG=$a"; done; } > "$STUB_LOG_DIR/claude.out"
"""

# herdr: `workspace list` prints $STUB_WS_LIST (a file); `pane get` prints $STUB_PANE_GET; `agent list` prints
# $STUB_AGENT_LIST; every call is logged one per line to herdr.calls.
HERDR_STUB = """#!/usr/bin/env bash
echo "$*" >> "$STUB_LOG_DIR/herdr.calls"
case "$1 $2" in
  "workspace list") [ -f "$STUB_LOG_DIR/ws-list.json" ] && cat "$STUB_LOG_DIR/ws-list.json" || exit 1 ;;
  "pane get") [ -f "$STUB_LOG_DIR/pane-get.json" ] && cat "$STUB_LOG_DIR/pane-get.json" || exit 1 ;;
  "agent list") [ -f "$STUB_LOG_DIR/agent-list.json" ] && cat "$STUB_LOG_DIR/agent-list.json" ;;
esac
exit 0
"""

# nohup stub: record the detached cswitch job instead of running it.
NOHUP_STUB = """#!/usr/bin/env bash
printf '%s\\0' "$@" > "$STUB_LOG_DIR/nohup.argv"
"""


class Env:
    """A temp HOME with ~/.claude-accounts (symlinks into the checkout) and stubs first on PATH."""

    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ca-test-"))
        self.home = self.tmp / "home"
        self.log = self.tmp / "log"
        stubs = self.tmp / "stubs"
        for d in (self.home / ".claude", self.log, stubs):
            d.mkdir(parents=True)
        acct = self.acct = self.home / ".claude-accounts"
        (acct / "bin").mkdir(parents=True)
        (acct / "lib.sh").symlink_to(SRC / "lib.sh")
        for f in (SRC / "bin").iterdir():
            (acct / "bin" / f.name).symlink_to(f)
        for name, body in (("claude", CLAUDE_STUB), ("herdr", HERDR_STUB), ("nohup", NOHUP_STUB)):
            p = stubs / name
            p.write_text(body)
            p.chmod(0o755)
        self.env = {
            "HOME": str(self.home),
            "PATH": f"{stubs}:{os.environ['PATH']}",
            "STUB_LOG_DIR": str(self.log),
        }

    def cleanup(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run(self, cmd, *args, env=None, stdin=None):
        """Run a launcher by name (bin/<cmd>) with an extra env; herdr vars are absent unless given."""
        e = dict(self.env, **(env or {}))
        return subprocess.run([str(self.acct / "bin" / cmd), *args], env=e, capture_output=True,
                              text=True, input=stdin, timeout=30)

    def sh(self, script, env=None):
        """Source lib.sh and run a bash snippet."""
        e = dict(self.env, **(env or {}))
        return subprocess.run(["bash", "-c", f'. "$HOME/.claude-accounts/lib.sh"; {script}'], env=e,
                              capture_output=True, text=True, timeout=30)

    def herdr_workspaces(self, *rows):
        """rows: (workspace_id, number, label)."""
        ws = [{"workspace_id": i, "number": n, "label": l} for i, n, l in rows]
        (self.log / "ws-list.json").write_text(json.dumps({"result": {"workspaces": ws}}))

    def herdr_calls(self):
        p = self.log / "herdr.calls"
        return p.read_text().splitlines() if p.exists() else []

    def claude_out(self):
        p = self.log / "claude.out"
        return p.read_text().splitlines() if p.exists() else None

    def default_file(self, value):
        (self.acct / "default").write_text(value)

    def ws_file(self, ws_id):
        p = self.acct / "workspace-default" / ws_id
        return p.read_text().strip() if p.exists() else None
