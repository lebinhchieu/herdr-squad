"""Builder of synthetic squad-report scopes: roster, messages, inbox and transcripts under a temp CLAUDE_CONFIG_DIR.

Every later squad-report test builds its scope with Fixture; times are epoch seconds (T0 + offset) so expected values are hand-computed.
"""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

T0 = 1_800_000_000
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
PRICES = {  # USD per million tokens; clean numbers on purpose
    "model-a": {"input": 1, "cache_read": 0.5, "cache_write_5m": 2, "cache_write": 4, "output": 8},
    "default": {"input": 2, "cache_read": 0, "cache_write_5m": 0, "cache_write": 0, "output": 0},
}


def stamp(t):
    return datetime.fromtimestamp(T0 + t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def asst(t, id=None, model="model-a", usage=None, cmd=None, text=""):
    content = [{"type": "text", "text": text}]
    if cmd:
        content.append({"type": "tool_use", "name": "Bash", "input": {"command": cmd}})
    return {"type": "assistant", "timestamp": stamp(t), "uuid": "u%d" % t,
            "message": {"id": id or "m%d" % t, "model": model, "content": content, "usage": usage or {}}}


def user(t, kind=None, text="", **origin):
    o = {"type": "user", "timestamp": stamp(t), "uuid": "u%d" % t, "message": {"role": "user", "content": text}}
    if kind:
        o["origin"] = {"kind": kind, **origin}
    return o


def tool_result(t):
    return user(t)


def peer(t, text=""):
    return user(t, "peer", text, name="x")


def human(t):
    return user(t, "human")


def notif(t):
    return user(t, "task-notification")


def system(t):
    return {"type": "system", "timestamp": stamp(t), "uuid": "s%d" % t}


def cost_state(session, total):
    return {"type": "cost-state", "sessionId": session, "totalCostUSD": total, "modelUsage": {}}


class Fixture:
    """A temp squad: <root>/squad/{settings,scopes/<scope>} and <root>/claude (CLAUDE_CONFIG_DIR)."""

    def __init__(self, scope="sc", done=False, prices=None, settings=None):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.squad = self.root / "squad"
        self.home = self.squad / "scopes" / ("_done" if done else "") / scope
        self.home.mkdir(parents=True)
        self.claude = self.root / "claude"
        self.proj = self.claude / "projects" / "-proj"
        self.proj.mkdir(parents=True)
        (self.squad / "settings").mkdir()
        self.settings = {"prices": prices or PRICES, **(settings or {})}
        self.rows, self.n = [], 0
        (self.home / "scope.md").write_text("# Scope: %s\n\nsize: M\n" % scope, encoding="utf-8")
        self.write_settings()

    def write_settings(self):
        (self.squad / "settings" / "report.json").write_text(json.dumps(self.settings), encoding="utf-8")

    def close(self):
        self._tmp.cleanup()

    def env(self):
        return {"CLAUDE_CONFIG_DIR": str(self.claude)}

    def session(self, agent, sessions, role="dev", status="retired", transcript=True, subagent=None):
        """sessions: list of record lists, one per session of the agent. The roster row names the last one."""
        sid = None
        for recs in sessions:
            self.n += 1
            sid = "00000000-0000-0000-0000-%012d" % self.n
            lines = [{"type": "agent-name", "agentName": agent}] + list(recs)
            if transcript:
                self._write(self.proj / (sid + ".jsonl"), lines)
        if subagent and transcript:
            d = self.proj / sid / "subagents"
            d.mkdir(parents=True)
            self._write(d / "agent-1.jsonl", subagent)
        self.rows.append((agent, role, status, sid or ""))
        self.write_roster()
        return sid

    def _write(self, path, lines):
        path.write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")

    def write_roster(self):
        out = ["# Roster", "", "| Agent | Role | Scope | Owns | Status | Session |", "| --- | --- | --- | --- | --- | --- |"]
        out += ["| %s | %s | sc |  | %s | %s |" % r for r in self.rows]
        (self.home / "roster.md").write_text("\n".join(out) + "\n", encoding="utf-8")

    def messages(self, rows):
        """rows: (t, from, to, text)."""
        self._write(self.home / "messages.jsonl", [
            {"ts": stamp(t), "msg_id": "g%d" % i, "from": f, "to": to, "type": None, "task": None, "text": text}
            for i, (t, f, to, text) in enumerate(rows)])

    def inbox(self, escalations):
        """escalations: (id, title, raised_t, answered_t|None)."""
        ev = []
        for i, title, a, b in escalations:
            ev.append({"ev": "seen", "id": i, "ts": stamp(a), "title": title})
            if b is not None:
                ev.append({"ev": "answer", "id": i, "ts": stamp(b), "text": "ok"})
        self._write(self.home / "inbox.jsonl", ev)

    def snapshot(self):
        """Bytes of every file in the scope home and the claude dir, to prove a run is read-only."""
        return {str(p): p.read_bytes() for d in (self.home, self.claude) for p in sorted(d.rglob("*")) if p.is_file()}


# ---- ticket 03: tasks scope (appended block) ----
def tasks_scope(fx):
    """dev and qa on tickets 07 (2 FAILs, one copied to a 3rd role) and 08; an overhead turn; one unanswered escalation."""
    fx.session("dev", [[asst(0, usage={"input_tokens": 1000}), tool_result(100), asst(200), peer(1000, "x"),
                        asst(1100), asst(1700), peer(2100, "x"), asst(2200)]], role="developer")
    fx.session("qa", [[asst(0), peer(900, "x"), asst(1000), peer(1900, "x"), asst(2000)]], role="qa-whitebox")
    fx.messages([
        (50, "tl", "dev", "ASSIGN 07 go"),
        (900, "dev", "qa", "HANDIN 07 branch a"),
        (1500, "qa", "dev", "FAIL 07: one   blocking\n finding"),
        (1503, "qa", "tl", "FAIL 07: one   blocking\n finding"),
        (1800, "dev", "qa", "HANDIN 07 again"),
        (2000, "qa", "dev", "PASS 07"),
    ])
    fx.inbox([("E1", "Which way", 300, 600), ("E2", "Open one", 2000, None)])
