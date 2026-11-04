"""squad tickets: ONE rule for the tasks of a scope. The report, the board panel and the scope picker all call it.

scope_tasks(scope_home, repo_root=None, name=None) -> {"tasks": [row], "source": ..., "dir": ..., "tried": [...]}
Sources, in this order (SOURCES); the first one with at least one task wins. No merging, no scoring, never another scope's folder:
  declared  `tickets: <slug>` line of scope.md -> .scratch/<slug>/issues/NN-*.md
  scratch   .scratch/<scope name>/issues/NN-*.md
  scope     <scope home>/tasks/NN.md | NN-*.md, and tasks/issues/NN-*.md (drafts)
  plan      a plan table (plan.md, tasks/plan.md): id = first cell, title = second cell
A row: id, title, status (first word, lowercase), where (repo-relative posix path), abs (only inside the roots), source.
find_tickets(c, raw_tokens) stays as a thin adapter ({NN: title}, dir). Never raises; reads at most 12 lines for a status.
"""
import re
from pathlib import Path

SOURCES = ("declared", "scratch", "scope", "plan")
NUM_FILE = re.compile(r"^(\d+)(?:-.*)?\.md$")
NOT_TASK = re.compile(r"\.(coach|summary)\.md$", re.I)   # notes next to a task, never a task
TEXT_MAX = 256 * 1024   # read at most this many bytes of any ticket or plan file


def _text(path):
    try:
        with open(path, "rb") as fh:
            return fh.read(TEXT_MAX).decode("utf-8", errors="replace")
    except OSError:
        return None


def _repo_of(scope_home):
    p = Path(str(scope_home)).resolve()
    for a in [p] + list(p.parents):
        if (a / ".scratch").is_dir():
            return a
    for a in p.parents:
        if a.name == ".claude":
            return a.parent
    return None


def declared_folder(scope_home):
    """The `tickets: <feature-slug>` line of scope.md (key case ignored, CRLF ok), or None."""
    text = _text(Path(str(scope_home)) / "scope.md")
    for line in (text or "").splitlines():
        m = re.match(r"^\s*tickets\s*:\s*(\S+)\s*$", line, re.I)
        if m and re.match(r"^[\w.-]+$", m.group(1)):
            return m.group(1)
    return None


def title_of(text, nn, stem=""):
    """First `# ` heading; a leading number is cut only when it equals nn (separator `:` `.` `-` or space optional)."""
    for line in (text or "").splitlines():
        if line.startswith("# "):
            h = line[2:].strip()
            m = re.match(r"^0*(\d+)\s*[:.-]?\s*(.*)$", h)
            if m and int(m.group(1)) == int(nn) and m.group(2):
                return m.group(2)
            return h
    return re.sub(r"^\d+-?", "", stem) or stem


def status_of(text):
    """`Status:` value in the first 12 lines, lowercase, first word only."""
    for line in (text or "").splitlines()[:12]:
        m = re.match(r"^Status:[ \t]*(.*)$", line)
        if m:
            v = m.group(1).strip().lower()
            for phrase in ("handed in", "in progress"):
                if v.startswith(phrase):
                    return phrase
            w = re.match(r"[^\s,;:(]*", v)
            return w.group(0)
    return ""


def _files(folder):
    try:
        fs = [f for f in sorted(Path(folder).iterdir()) if f.is_file() and NUM_FILE.match(f.name) and not NOT_TASK.search(f.name)]
    except OSError:
        return []
    return fs


def _rel(path, root):
    try:
        return Path(path).resolve().relative_to(root).as_posix()
    except (ValueError, OSError):
        return None


def _row(f, root, roots, source):
    nn = NUM_FILE.match(f.name).group(1)
    text = _text(f)
    rel = _rel(f, root) if root else None
    row = {"id": nn, "title": title_of(text, nn, f.stem), "status": status_of(text), "where": rel or f.as_posix(),
           "source": source}
    try:
        real = f.resolve()
        if any(real == r or r in real.parents for r in roots):
            row["abs"] = str(real)
    except OSError:
        pass
    return row


def _plan_files(home):
    """Plan candidates in order: plan.md, tasks/plan.md, then iterations/*.md (newest number first)."""
    out = [home / "plan.md", home / "tasks" / "plan.md"]
    try:
        its = [f for f in (home / "iterations").glob("*.md") if f.is_file() and not NOT_TASK.search(f.name) and f.stem.isdigit()]
    except OSError:
        its = []
    return out + sorted(its, key=lambda f: -int(f.stem))


def _plan_rows(scope_home, root):
    for f in _plan_files(Path(str(scope_home))):
        text = _text(f)
        if text is None:
            continue
        rows = []
        for line in text.splitlines():
            if not line.strip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            m = re.match(r"^`?#?(\d+)`?$", cells[0]) if cells else None
            if m and len(cells) > 1:
                rows.append({"id": m.group(1).zfill(2), "title": cells[1], "status": "",
                             "where": "plan table, " + f.name, "source": "plan"})
        if rows:
            return rows
    return []


def scope_tasks(scope_home, repo_root=None, name=None):
    try:
        return _scope_tasks(scope_home, repo_root, name)
    except Exception:  # a reader never raises
        return {"tasks": [], "source": None, "dir": None, "tried": [], "looked": []}


def _scope_tasks(scope_home, repo_root, name):
    home = Path(str(scope_home))
    root = Path(repo_root).resolve() if repo_root else _repo_of(home)
    name = name or home.name
    roots = [r for r in (home.resolve().parent.parent if home.parent.name == "scopes" else home.resolve(),
                         root / ".scratch" if root else None) if r]
    tried, found = [], (None, [], None)
    for src in SOURCES:
        if src in ("declared", "scratch"):
            slug = declared_folder(home) if src == "declared" else name
            if not slug or root is None:
                continue
            d = root / ".scratch" / slug / "issues"
            tried.append(".scratch/%s/issues" % slug)
            files = [f for f in _files(d) if re.match(r"^\d+-", f.name)]
            rows = [_row(f, root, roots, src) for f in files]
            dirr = ".scratch/" + slug
        elif src == "scope":
            tried.append(_rel(home / "tasks", root) or (home / "tasks").as_posix())
            seen, rows = set(), []
            for d in (home / "tasks", home / "tasks" / "issues"):
                for f in _files(d):
                    r = _row(f, root, roots, src)
                    if r["id"] not in seen:
                        seen.add(r["id"])
                        rows.append(r)
            dirr = _rel(home / "tasks", root) or "tasks"
        else:
            rows = _plan_rows(home, root)
            tried.append("plan.md, tasks/plan.md, iterations/")
            dirr = None
        if rows:
            rows.sort(key=lambda r: (len(r["id"]), r["id"]))
            found = (src, rows, dirr)
            break
    src, rows, dirr = found
    return {"tasks": rows, "source": src, "dir": dirr, "tried": tried, "looked": tried}


def find_tickets(c, raw_tokens):
    """Adapter kept for the report: -> ({NN: title}, relative folder or None). `raw_tokens` is unused (no guessing)."""
    r = scope_tasks(c.scope_home, None, getattr(c, "name", None))
    return {t["id"]: t["title"] for t in r["tasks"]}, r["dir"]
