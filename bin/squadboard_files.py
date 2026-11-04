"""squad board M8: the Files panel list (ticket 14; architecture.md sections 1 and 6).

Route `GET /api/files` (goal= or scope=). Everything the squad made for the PO, in one list. Read-only; it never opens a
file, it only lists names and mtimes. Opening a file is the existing `/api/file` route (ticket 03), which answers agent HTML
with `Content-Security-Policy: sandbox`. This module adds no route for that.

    data = {rows, report, report_expected, closed, truncated, files_seen}
    row  = {name, kind, what, scope, path, mtime}      mtime = UTC epoch seconds (the page formats the local time)
    kind in KINDS; report = the report.html row of a closed scope, or None ("no report yet (made at close)").

What is listed (the Rules of ticket 14): scope `tasks/*.md`, `ui-design/` (.md and .html), `promote.md`, `report/report.html`
and `report/data.json`, `evidence/`, the ticket `evidence.md` under `<repo>/.scratch/<scope>/issues/*/`, `escalations.md`
(the answered questions); goal `shared/*.md` (`decisions.md` is kind `decision`). ADRs, `messages.jsonl`, `inbox.jsonl`,
`roles/`, locks and `_runtime` are not listed. A path is listed only when its resolved path lies under the squad folder or
`<repo>/.scratch` (the same check as the file route: `squadboard._under`). Symlinked folders are not followed. A folder
walk stops at DEPTH and at MAX_ROWS (`truncated: true`). Never raises.
"""
import os
import sys
from pathlib import Path

BIN = Path(__file__).resolve().parent
if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))
import squadboard  # noqa: E402  (the allow-list helper `_under` and nothing else)

KINDS = ("ticket", "design", "prototype", "promote", "report", "data", "evidence", "decision", "answer", "other")
WHAT = {"ticket": "ticket plan", "design": "design", "prototype": "prototype", "promote": "promotion", "report": "scope report",
        "data": "report data", "evidence": "evidence", "decision": "decisions", "answer": "questions and answers", "other": "document"}
DEPTH = 3
MAX_ROWS = 500


def _scandir(d):
    try:
        with os.scandir(d) as it:
            return sorted(it, key=lambda e: e.name)
    except OSError:
        return []


class _Walk:
    def __init__(self, squad, home, roots):
        self.squad, self.home, self.roots = squad, home, roots
        self.rows, self.truncated, self.seen = [], False, 0

    def add(self, p, kind):
        """List file `p` (a Path) when it is a regular file inside the allow-list."""
        self.seen += 1
        if len(self.rows) >= MAX_ROWS:
            self.truncated = True
            return
        try:
            real = p.resolve(strict=True)
            if not real.is_file() or not squadboard._under(real, self.roots):
                return
            mtime = int(real.stat().st_mtime)
        except (OSError, RuntimeError, ValueError):
            return
        path, name = str(real), p.name
        for base in (self.squad.path, self.squad.repo_root):  # /api/file takes a path relative to the squad folder
            try:
                rel = p.relative_to(base).as_posix()
            except ValueError:
                continue
            name = rel
            if base == self.squad.path:
                path = rel
            break
        try:
            name = p.relative_to(self.home).as_posix()
        except ValueError:
            pass
        self.rows.append({"name": name, "kind": kind, "what": WHAT[kind], "scope": self.home.name, "path": path, "mtime": mtime})

    def files(self, d, exts, kind_of, depth=1):
        """Files of folder `d` with an extension in `exts`; recurse into real (not symlinked) subfolders up to DEPTH."""
        for e in _scandir(d):
            if len(self.rows) >= MAX_ROWS:
                self.truncated = True
                return
            try:
                if e.is_symlink():  # a file link is listed only if its target is allowed (add checks); a folder link is not followed
                    if e.is_file() and Path(e.name).suffix.lower() in exts:
                        self.add(Path(e.path), kind_of(e.name))
                elif e.is_dir(follow_symlinks=False):
                    if depth < DEPTH:
                        self.files(Path(e.path), exts, kind_of, depth + 1)
                    else:
                        self.truncated = True
                elif e.is_file(follow_symlinks=False) and Path(e.name).suffix.lower() in exts:
                    self.add(Path(e.path), kind_of(e.name))
            except OSError:
                continue


def _closed(home):
    return home.parent.name == "_done"


def list_files(squad, kind, name, home):
    """-> data dict. Pure listing of the folders named in the module docstring."""
    roots = [squad.path, (squad.repo_root / ".scratch").resolve()]
    w = _Walk(squad, Path(home), roots)
    home = Path(home)
    if kind == "scope":
        w.files(home / "tasks", {".md"}, lambda n: "ticket" if n[:1].isdigit() else "other", DEPTH)
        w.files(home / "ui-design", {".md", ".html"}, lambda n: "prototype" if n.endswith(".html") else "design")
        if (home / "promote.md").is_file():
            w.add(home / "promote.md", "promote")
        for n, k in (("report.html", "report"), ("data.json", "data")):
            if (home / "report" / n).is_file():
                w.add(home / "report" / n, k)
        w.files(home / "evidence", {".md"}, lambda n: "evidence")
        for t in _scandir(squad.repo_root / ".scratch" / name / "issues"):
            try:
                if t.is_dir(follow_symlinks=False) and (Path(t.path) / "evidence.md").is_file():
                    w.add(Path(t.path) / "evidence.md", "evidence")
            except OSError:
                continue
    else:
        w.files(home / "shared", {".md"}, lambda n: "decision" if n == "decisions.md" else "other", DEPTH)
    if (home / "escalations.md").is_file():
        w.add(home / "escalations.md", "answer")
    rows = sorted(w.rows, key=lambda r: (-r["mtime"], r["name"]))
    report = next((r for r in rows if r["kind"] == "report"), None)
    return {"rows": rows, "report": report, "report_expected": kind == "scope", "closed": kind == "scope" and _closed(home),
            "truncated": w.truncated, "files_seen": w.seen}


def read(sel):
    """-> {data, quality, unknown}. A missing folder gives `unknown:files`; never raises."""
    try:
        squad, home = sel.get("squad"), sel.get("home")
        if squad is None or home is None or not Path(home).is_dir():
            return {"data": None, "quality": "unknown", "unknown": ["files"]}
        return {"data": list_files(squad, sel.get("kind"), sel.get("name"), home), "quality": "exact", "unknown": []}
    except Exception:
        return {"data": None, "quality": "unknown", "unknown": ["files"]}


ROUTE = {"name": "files", "path": "/api/files", "read": read, "selection": True}
