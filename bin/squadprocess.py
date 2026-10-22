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
    sections: object  # "all" or list of full heading lines, `;`-separated in the file
    change: str
    why: str
    old_kind: str = "none"  # "text" (fenced, exact wording) | "snapshot" | "none" (`-`)
    old: str = ""
    new_kind: str = "none"
    new: str = ""
    manual: str = ""
    extra: dict = field(default_factory=dict)


FIRST_RULE_VERSION = 7
CHANGES = ("reword", "add", "remove", "rename", "rule")
_VERSION_HEAD = re.compile(r"## v([0-9]+)[ \t]+[—–-][ \t]+(\S.*)$")
_BULLET = re.compile(r"- ([a-z]+):[ \t]*(.*)$")


def read_changelog(path):
    """Items, newest version first as written. Anything it cannot parse raises ProcessError (never silent)."""
    lines = _read(path, "the changelog").splitlines()
    keep, skip = [], False  # from v7 a block lists rule IDs (read by squadupgrade), not sections: skip it
    for ln in lines:
        m = re.match(r"## v([0-9]+)\b", ln)
        if m:
            skip = int(m.group(1)) >= FIRST_RULE_VERSION
        if not skip:
            keep.append(ln)
    lines = keep
    items, ver, date, snap, cur, i = [], None, None, None, None, 0
    versions = []

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
                          "all" if sec == "all" else [s.strip() for s in sec.split(";") if s.strip()],
                          f["change"], f["why"], kinds["old"][0], kinds["old"][1],
                          kinds["new"][0], kinds["new"][1], f.get("manual", "")))

    def check_items():
        if ver is not None and not any(it.version == ver for it in items):
            raise ProcessError(f"changelog {path}: v{ver} has no items")

    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.startswith("# "):
            i += 1
            continue
        m = _VERSION_HEAD.match(line)
        if m:
            finish()
            check_items()
            cur, ver, date, snap = None, int(m.group(1)), m.group(2).strip(), None
            versions.append(ver)
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
    check_items()
    if not versions:
        raise ProcessError(f"changelog {path}: no `## v<N>` heading found")
    return items


# ---- plan / compose / apply (design §4-§6) ----------------------------------------------------

import datetime  # noqa: E402
import difflib  # noqa: E402
import shutil  # noqa: E402
import tempfile  # noqa: E402

SKILL_DIR = Path("skills", "squad-process-update")
LOG_HEADER = ("# Process log\n\n**Every change to `process.md`, newest first.**\n\n"
              "| Date | Change | Why |\n|---|---|---|\n")


def _snapshot(plugin_root, n):
    path = Path(plugin_root) / SKILL_DIR / "history" / f"process-v{n}.md"
    return _read(path, f"the snapshot of version {n}")


def _drop_version_lines(text):
    """The squad's own text without any process-version line (valid or malformed), fence-aware."""
    return "\n".join(ln for ln, fenced in _fence_flags(text.splitlines()) if fenced or not _LINE.match(ln))


def _udiff(a, b, la, lb):
    return "".join(difflib.unified_diff((a or "").splitlines(True), (b or "").splitlines(True), la, lb)) \
        or "(no difference)\n"


def plan(squad_dir, plugin_root=DEFAULT_PLUGIN_ROOT):
    """Read-only. Raises ProcessError when it must refuse (ahead, flat layout, no file, missing snapshot)."""
    squad_dir = Path(squad_dir)
    if not (squad_dir / "scopes").is_dir():
        raise ProcessError(f"{squad_dir} has no scopes/ folder (an older layout): run `squad-migrate` first")
    v, stamp = squad_version(squad_dir)
    p = plugin_version(plugin_root)
    if v > p:
        raise ProcessError(f"process.md is version {v}, newer than this plugin's {p}: update the plugin")
    if v == p:
        return {"squad": v, "plugin": p, "state": "current", "stamp": stamp, "items": [], "sections": []}
    changelog = Path(plugin_root) / SKILL_DIR / "changelog.md"
    items = sorted((i for i in read_changelog(changelog) if v < i.version <= p), key=lambda i: i.version)
    s_all = dict(sections(_drop_version_lines(_read(squad_dir / "process.md", "process.md"))))
    o_all = dict(sections(_snapshot(plugin_root, v)))
    n_list = sections(_snapshot(plugin_root, p))
    n_all = dict(n_list)
    heads = [h for h, _ in n_list]
    heads += [h for h in list(o_all) + list(s_all) if h not in heads]
    rows = []
    for h in dict.fromkeys(heads):
        s, o, n = s_all.get(h), o_all.get(h), n_all.get(h)
        if s == n:
            state = "already"
        elif o is None and n is None:
            state = "local-section"
        elif o == n and not (s is None and n is not None):  # a local deletion of a section N keeps is a conflict
            state = "local"
        elif o is None and s is None:
            state = "added"
        elif s == o:
            state = "removed" if n is None else "clean"
        else:
            state = "conflict"
        row = {"heading": h, "state": state, "squad": s, "old": o, "new": n}
        if state == "conflict":
            row["squad_vs_old"] = _udiff(o, s, "plugin v%d" % v, "squad")
            row["old_vs_new"] = _udiff(o, n, "plugin v%d" % v, "plugin v%d" % p)
        rows.append(row)
    return {"squad": v, "plugin": p, "state": "behind", "stamp": stamp,
            "items": [{"version": i.version, "title": i.title, "sections": i.sections, "change": i.change,
                       "why": i.why, **({"manual": i.manual} if i.manual else {})} for i in items],
            "sections": rows}


def format_plan(pl):
    if pl["state"] == "current":
        return "process.md is up to date."
    out = [f"process.md is version {pl['squad']}; the plugin's is {pl['plugin']}. Nothing is written until you confirm.",
           "", "Changelog items:"]
    for i in pl["items"]:
        secs = i["sections"] if i["sections"] == "all" else "; ".join(i["sections"])
        out.append(f"- v{i['version']} {i['title']} [{secs}] {i['change']}: {i['why']}"
                   + (f" (MANUAL: {i['manual']})" if "manual" in i else ""))
    out += ["", "Sections:"]
    for r in pl["sections"]:
        out.append(f"  {r['state']:13} {r['heading'] or '(preamble)'}")
        if r["state"] == "conflict":
            if r["squad"] is None and r["new"] is not None:
                out.append("    the squad deleted this section: `ours` is not offered, choose theirs or file:<path>")
            out += ["    what the squad changed (squad vs old):", _indent(r["squad_vs_old"]),
                    "    what the plugin changed (old vs new):", _indent(r["old_vs_new"])]
    return "\n".join(out)


def _indent(text):
    return "\n".join("      " + ln for ln in text.rstrip("\n").splitlines())


def _decide(row, resolve):
    """(body|None, how). A conflict without a resolution raises."""
    st = row["state"]
    if st != "conflict":
        return (row["squad"] if st in ("already", "local", "local-section") else
                row["new"] if st in ("clean", "added") else None), st
    how = resolve.get(row["heading"])
    if how is None:
        raise ProcessError(f"conflict in {row['heading']!r}: say --resolve \"{row['heading']}=ours|theirs|file:<path>\"")
    if how == "ours":
        if row["squad"] is None and row["new"] is not None:
            raise ProcessError(f"{row['heading']!r}: the squad deleted this section, so `ours` would drop a "
                               "heading the new version needs: choose `theirs` or `file:<path>`")
        return row["squad"], "ours"
    if how == "theirs":
        return row["new"], "theirs"
    if how.startswith("file:"):
        return _own_wording(row["heading"], _read(how[5:], "the replacement wording")), "own wording"
    raise ProcessError(f"cannot resolve {row['heading']!r} with {how!r}: use ours, theirs or file:<path>")


def _own_wording(heading, text):
    """The body only: a first line equal to the section's heading is dropped; any other heading is refused."""
    lines = text.strip("\n").splitlines()
    if lines and lines[0].rstrip() == heading:
        lines = lines[1:]
    if any(not fenced and _HEADING.match(ln) for ln, fenced in _fence_flags(lines)):
        raise ProcessError(f"the wording for {heading!r} holds a heading line: give the body only")
    return "\n".join(lines).strip("\n")


def _render(blocks, version):
    parts = []
    for i, (h, body) in enumerate(blocks):
        lines = [h] if h else []
        if i == 0 and h.startswith("# "):
            lines += ["", f"process-version: {version}"]
        if body:
            lines += ["", body] if lines else [body]
        parts.append("\n".join(lines))
    return "\n\n".join(parts) + "\n"


def compose(squad_dir, plugin_root, out, resolve=None):
    """Write the combined file to `out` (not inside the squad folder); return its text."""
    squad_dir, out = Path(squad_dir).resolve(), Path(out).resolve()
    if out == squad_dir or squad_dir in out.parents:
        raise ProcessError(f"--out {out} is inside the squad folder: pick a path outside it")
    pl = plan(squad_dir, plugin_root)
    if pl["state"] == "current":
        raise ProcessError("process.md is up to date: nothing to compose")
    resolve = dict(resolve or {})
    unknown = set(resolve) - {r["heading"] for r in pl["sections"] if r["state"] == "conflict"}
    if unknown:
        raise ProcessError(f"--resolve names a heading that is not a conflict: {', '.join(sorted(unknown))}")
    rows = {r["heading"]: r for r in pl["sections"]}
    decided = {h: _decide(r, resolve) for h, r in rows.items()}
    s_order = [h for h, _ in sections(_drop_version_lines(_read(squad_dir / "process.md", "process.md")))]
    n_order = [h for h, _ in sections(_snapshot(plugin_root, pl["plugin"]))]
    blocks = [[h, decided[h][0]] for h in s_order if decided[h][0] is not None]
    for k, h in enumerate(n_order):
        if h in s_order or decided[h][0] is None:
            continue
        at = 0
        for prev in reversed(n_order[:k]):
            idx = next((j for j, b in enumerate(blocks) if b[0] == prev), None)
            if idx is not None:
                at = idx + 1
                break
        blocks.insert(at, [h, decided[h][0]])
    text = _render(blocks, pl["plugin"])
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return text


def _validate(file_text, pl, items_removed):
    if not file_text.strip():
        raise ProcessError("FILE is empty")
    n, status = parse_version(file_text)
    if status != "ok":
        raise ProcessError(f"FILE needs exactly one `process-version: {pl['plugin']}` line ({status})")
    if n != pl["plugin"]:
        raise ProcessError(f"FILE says version {n}; the plugin's is {pl['plugin']}")
    have = {h for h, _ in sections(file_text)}
    missing = [r["heading"] for r in pl["sections"]
               if r["new"] is not None and r["heading"] not in have and r["heading"] not in items_removed]
    if missing:
        raise ProcessError("FILE lacks headings of the new version: " + ", ".join(repr(m) for m in missing))


def _backup_path(squad_dir, today):
    backups = squad_dir.parent.parent / "squad-backups"
    path, n = backups / f"{squad_dir.name}-process-{today}.md", 1
    while path.exists():
        n += 1
        path = backups / f"{squad_dir.name}-process-{today}-{n}.md"
    return path


def _atomic_write(path, text):
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        if path.exists():
            shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _log_rows(pl, chosen, today):
    rows = [f"| {today} | v{pl['plugin']} conflict {h}: kept {how} | the PO chose |" for h, how in chosen]
    for i in sorted(pl["items"], key=lambda i: -i["version"]):
        secs = i["sections"] if i["sections"] == "all" else "; ".join(i["sections"])
        rows.append(f"| {today} | v{i['version']} {i['title']}: {secs} | {i['why']} |")
    return rows


def _insert_log(old, rows):
    lines = (old or LOG_HEADER).splitlines()
    at = next((k + 1 for k, ln in enumerate(lines) if re.fullmatch(r"\|[ \-|:]+\|", ln.strip())), None)
    if at is None:
        lines += ["", *LOG_HEADER.splitlines()[-2:]]
        at = len(lines)
    return "\n".join(lines[:at] + rows + lines[at:]) + "\n"


def apply(squad_dir, plugin_root, file, yes=False, today=None):
    """Validate FILE; without `yes` return the diff and write nothing. Returns a dict for the CLI to print."""
    from processlint import lint
    squad_dir, today = Path(squad_dir).resolve(), str(today or datetime.date.today())
    pl = plan(squad_dir, plugin_root)
    if pl["state"] == "current":
        return {"applied": False, "message": "process.md is up to date: nothing to do."}
    text = _read(file, "FILE")
    removed = {s for i in pl["items"] if i["change"] == "remove" and i["sections"] != "all" for s in i["sections"]}
    _validate(text, pl, removed)
    current = _read(squad_dir / "process.md", "process.md")
    new_s = dict(sections(text))
    chosen = []
    for r in pl["sections"]:
        if r["state"] == "conflict":
            got = new_s.get(r["heading"])
            chosen.append((r["heading"], "ours" if got == r["squad"] else "theirs" if got == r["new"]
                           else "own wording"))
    changed = [h for h, b in new_s.items() if b != dict(sections(_drop_version_lines(current))).get(h)]
    changed += [r["heading"] for r in pl["sections"] if r["squad"] is not None and r["heading"] not in new_s]
    res = {"applied": False, "changed": changed, "warnings": [f"WARNING lint: {w}" for w in lint(text)],
           "diff": _udiff(current, text, "process.md (now)", "process.md (proposed)")}
    if not yes:
        res["message"] = "NOT APPLIED (add --yes after the PO confirms)."
        return res
    backup = _backup_path(squad_dir, today)
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(squad_dir / "process.md", backup)
    _atomic_write(squad_dir / "process.md", text)
    log = squad_dir / "process-log.md"
    rows = _log_rows(pl, chosen, today)
    _atomic_write(log, _insert_log(log.read_text(encoding="utf-8") if log.exists() else "", rows))
    r = check(squad_dir, plugin_root)
    res.update(applied=True, backup=str(backup), log_rows=rows, message=r["message"] or "process.md is current.")
    return res
