"""The one place that knows a squad's process version: parse, compare, check, split into sections.

The version is one line `process-version: <N>` (N a positive integer) in process.md. A squad without
it is version 1 (BASELINE); a malformed line also counts as 1, with a different message.
"""
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

BASELINE = 1
DEFAULT_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path("templates", "squad", "process.md")

_LINE = re.compile(r"process-version:")
_OK = re.compile(r"process-version:[ \t]*([1-9][0-9]*)[ \t]*$")
_HEADING = re.compile(r"#{1,3} +\S")


class ProcessError(ValueError):
    """A process file or changelog the tool cannot read; the message is for the PO."""


def _fence_flags(lines):
    """Yield (line, inside_fence); a fence marker line itself counts as inside."""
    inside = False
    for line in lines:
        if line.lstrip().startswith(("```", "~~~")):
            inside = not inside
            yield line, True
        else:
            yield line, inside


def parse_version(text):
    """(int|None, "ok"|"missing"|"malformed"): the first process-version line outside code fences."""
    hits = [ln.rstrip("\r") for ln, fenced in _fence_flags(text.splitlines())
            if not fenced and _LINE.match(ln)]
    if not hits:
        return None, "missing"
    m = _OK.match(hits[0])
    if len(hits) > 1 or not m:
        return None, "malformed"
    return int(m.group(1)), "ok"


def _read(path, what):
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as e:
        raise ProcessError(f"cannot read {what} {path}: {e.strerror or e}") from e


def squad_version(squad_dir):
    """(int, "stamped"|"unstamped"|"malformed"); unstamped and malformed count as BASELINE."""
    n, status = parse_version(_read(Path(squad_dir) / "process.md", "the squad's process.md"))
    if status == "ok":
        return n, "stamped"
    return BASELINE, "unstamped" if status == "missing" else "malformed"


def plugin_version(plugin_root=DEFAULT_PLUGIN_ROOT):
    """The version in the plugin's template; raises ProcessError when the file or the line is missing/bad."""
    path = Path(plugin_root) / TEMPLATE
    n, status = parse_version(_read(path, "the plugin template"))
    if status != "ok":
        raise ProcessError(f"the plugin template {path} has no valid `process-version: <N>` line ({status})")
    return n


def check(squad_dir, plugin_root=DEFAULT_PLUGIN_ROOT):
    s, stamp = squad_version(squad_dir)
    p = plugin_version(plugin_root)
    state = "current" if s == p else "behind" if s < p else "ahead"
    note = {"stamped": "", "unstamped": " (no process-version line: treated as version 1)",
            "malformed": " (malformed process-version line: treated as version 1)"}[stamp]
    if state == "ahead":
        msg = (f"process.md is version {s}{note}, newer than this plugin's {p}: update the plugin; "
               "the migration will not run.")
    elif state == "behind":
        msg = (f"process.md is version {s}{note}, this plugin's is {p}: say `migrate the process` "
               "(`/squad:squad-process-update`) to update; nothing changes until you confirm.")
    else:
        msg = "" if stamp == "stamped" else (
            f"process.md has {'no' if stamp == 'unstamped' else 'a malformed'} process-version line; "
            f"treated as version {s}, the plugin's is {p}.")
    return {"squad": s, "plugin": p, "state": state, "stamp": stamp, "message": msg}


def sections(text):
    """[(heading line, body)]: flat split at #, ##, ### lines outside code fences.

    The heading is the full line (`## Safety`) so a section can be written back. The version line is
    dropped; trailing blank lines are stripped from bodies; text before the first heading is the
    section "". A duplicate heading raises ProcessError."""
    out, head, body = [], "", []

    def close():
        text_ = "\n".join(body).strip("\n")
        if head or text_:
            if any(h == head for h, _ in out):
                raise ProcessError(f"duplicate heading in process text: {head!r}")
            out.append((head, text_.rstrip()))

    for line, fenced in _fence_flags(text.splitlines()):
        if not fenced and _LINE.match(line) and parse_version(line)[1] == "ok":
            continue
        if not fenced and _HEADING.match(line):
            close()
            head, body = line.rstrip(), []
        else:
            body.append(line)
    close()
    return out


@dataclass
class Item:
    version: int
    date: str
    snapshot: str
    title: str
    sections: object  # "all" or list of exact headings
    change: str
    why: str
    old_kind: str = "none"  # "text" (fenced, exact wording) | "snapshot" | "none" (`-`)
    old: str = ""
    new_kind: str = "none"
    new: str = ""
    manual: str = ""
    extra: dict = field(default_factory=dict)


CHANGES = ("reword", "add", "remove", "rename", "rule")
_VERSION_HEAD = re.compile(r"## v([0-9]+)[ \t]+[—–-][ \t]+(\S.*)$")
_BULLET = re.compile(r"- ([a-z]+):[ \t]*(.*)$")


def read_changelog(path):
    """Items, newest version first as written. Anything it cannot parse raises ProcessError (never silent)."""
    lines = _read(path, "the changelog").splitlines()
    items, ver, date, snap, cur, i = [], None, None, None, None, 0

    def bad(msg):
        raise ProcessError(f"changelog {path} line {i + 1}: {msg}")

    def finish():
        if cur is None:
            return
        f = cur["f"]
        for k in ("sections", "change", "why") + (() if "manual" in f else ("old", "new")):
            if k not in f:
                bad(f"item {cur['title']!r} of v{cur['version']} has no `{k}:`")
        if f["change"] not in CHANGES:
            bad(f"item {cur['title']!r}: change must be one of {', '.join(CHANGES)}")
        kinds = {}
        for k in ("old", "new"):
            v = f.get(k, "-")
            kinds[k] = ("none", "") if v == "-" else ("snapshot", "") if v == "snapshot" else ("text", v)
        sec = f["sections"].strip()
        extra = {k: v for k, v in f.items() if k not in
                 ("sections", "change", "why", "old", "new", "manual")}
        if extra:
            bad(f"item {cur['title']!r}: unknown field(s) {', '.join(sorted(extra))}")
        items.append(Item(cur["version"], cur["date"], cur["snapshot"], cur["title"],
                          "all" if sec == "all" else [s.strip() for s in sec.split(",") if s.strip()],
                          f["change"], f["why"], kinds["old"][0], kinds["old"][1],
                          kinds["new"][0], kinds["new"][1], f.get("manual", "")))

    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.startswith("# "):
            i += 1
            continue
        m = _VERSION_HEAD.match(line)
        if m:
            finish()
            cur, ver, date, snap = None, int(m.group(1)), m.group(2).strip(), None
            i += 1
            continue
        if line.startswith("### "):
            if ver is None:
                bad("item before any `## v<N>` heading")
            finish()
            if snap is None:
                bad(f"v{ver} has no `- snapshot:` line before its items")
            cur = {"version": ver, "date": date, "snapshot": snap, "title": line[4:].strip(), "f": {}}
            i += 1
            continue
        m = _BULLET.match(line)
        if not m or ver is None:
            bad(f"cannot parse {line!r}")
        key, val = m.groups()
        i += 1
        if not val.strip():  # fenced block under the key
            if i >= len(lines) or not lines[i].lstrip().startswith("```"):
                bad(f"`{key}:` has no value and no fenced block")
            i += 1
            block = []
            while i < len(lines) and not lines[i].lstrip().startswith("```"):
                block.append(lines[i])
                i += 1
            if i >= len(lines):
                bad(f"unclosed fenced block under `{key}:`")
            i += 1
            val = "\n".join(block)
        if cur is None:
            if key != "snapshot":
                bad(f"unknown version-level field `{key}:`")
            snap = val.strip()
        else:
            if key in cur["f"]:
                bad(f"duplicate `{key}:` in item {cur['title']!r}")
            cur["f"][key] = val if "\n" in val else val.strip()
    finish()
    return items
