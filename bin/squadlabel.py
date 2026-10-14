"""The squad tab label rule and the label store. The only place either lives.

A label is never stored. <home>/labels/<agent>.json holds {"role", "number", "title"} and the label
is built from it, so a rule change cannot leave a stale label behind. One file per agent: only that
agent or the Manager writes it, so there is no lock; writes go through a temp file and os.replace.
"""
import json
import os
import re
import unicodedata
from pathlib import Path

ROLE_NAMES = {
    "manager": "Manager", "ba": "BA", "team-lead": "Team Lead", "tech-lead": "Tech Lead",
    "qa-whitebox": "QA Whitebox", "qa-blackbox": "QA Blackbox", "dev": "Dev",
    "designer": "Designer", "token-coach": "Token Coach",
}
BOARD_LABEL = "📋 Board"
LEGACY_BOARD_LABEL = "board"
MAX_LEN = 32
NAME_RE = re.compile(r"[a-z][a-z0-9_-]{0,31}")


def role_name(role):
    return ROLE_NAMES.get(role) or str(role).replace("-", " ").replace("_", " ").title()


def clean_title(title):
    t = "".join(" " if c.isspace() else c for c in str(title or "") if c.isspace() or unicodedata.category(c) != "Cc")
    return " ".join(t.split())


def build_label(role, number=None, title=""):
    label = ("🦀" if role == "manager" else "🤖") + " " + role_name(role)
    if number is not None:
        label += f" {number}"
    title = clean_title(title)
    if title:
        label += f" · {title}"
    return label if len(label) <= MAX_LEN else label[:MAX_LEN - 1] + "…"


def _path(home, agent):
    if not isinstance(agent, str) or not NAME_RE.fullmatch(agent):
        raise ValueError(f"bad agent name: {agent!r}")
    return Path(home) / "labels" / f"{agent}.json"


def read_entry(home, agent):
    try:
        d = json.loads(_path(home, agent).read_text())
    except (OSError, ValueError):
        return None
    if not isinstance(d, dict) or not isinstance(d.get("role"), str):
        return None
    n = d.get("number")
    return {"role": d["role"], "number": n if isinstance(n, int) and not isinstance(n, bool) else None,
            "title": d["title"] if isinstance(d.get("title"), str) else ""}


def write_entry(home, agent, role, number, title):
    p = _path(home, agent)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f".{p.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(json.dumps({"role": role, "number": number, "title": title}, ensure_ascii=False))
        os.replace(tmp, p)
    finally:
        tmp.unlink(missing_ok=True)


def assign_number(home, agent, role, live_names):
    """Number for `agent` among live peers of its role; also numbers an unnumbered peer (first Dev -> Dev 1).
    Returns (number, [(peer, new_number), ...]); the peers' new numbers are already stored."""
    peers = {}
    d = Path(home) / "labels"
    for f in sorted(d.glob("*.json")) if d.is_dir() else []:
        name = f.stem
        if name == agent or name not in live_names or not NAME_RE.fullmatch(name):
            continue
        e = read_entry(home, name)
        if e and e["role"] == role:
            peers[name] = e
    if not peers:
        return None, []
    used = {e["number"] for e in peers.values() if e["number"] is not None}
    changed = []
    for name, e in peers.items():
        if e["number"] is None:
            n = next(i for i in range(1, len(peers) + 2) if i not in used)
            used.add(n)
            write_entry(home, name, role, n, e["title"])
            changed.append((name, n))
    mine = read_entry(home, agent)
    if mine and mine["number"] is not None:
        return mine["number"], changed
    return max(used) + 1, changed
