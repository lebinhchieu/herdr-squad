"""squad tickets: ONE rule for the tasks of a scope. The report, the board panel and the scope picker all call it.

scope_tasks(scope_home, repo_root=None, name=None, git=True) -> {"tasks": [row], "source": ..., "dir": ..., "tried": [...]}
Sources, in this order (SOURCES); the first one with at least one task wins; never another scope's folder.
Inside a ticket folder (declared, scratch) the copies of a ticket merge by number: the scope's own Dev branch `...-NN`
(not merged into main, differing from main), else the newest such scope branch, else main's file, else the draft
`tasks/NN-ticket.md`. Rows of the folder carry origin (main|branch|draft), origin_ref (branch or ""), on_main.
git=False skips the branch reads (the watchdog, reviewpack). Git is read-only: for-each-ref, ls-tree, show; 2 s budget.
  declared  `tickets: <slug>` line of scope.md -> .scratch/<slug>/issues/NN-*.md
  scratch   .scratch/<scope name>/issues/NN-*.md
  scope     <scope home>/tasks/NN.md | NN-*.md, and tasks/issues/NN-*.md (drafts)
  plan      a plan table (plan.md, tasks/plan.md): id = first cell, title = second cell
A row: id, title, status (first word, lowercase), where (repo-relative posix path), abs (only inside the roots), source.
find_tickets(c, raw_tokens) stays as a thin adapter ({NN: title}, dir). Never raises; reads at most 12 lines for a status.
"""
import hashlib
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import squadboard_git  # noqa: E402

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
    """`Status:` value in the first 12 lines (else the `State:` value), lowercase, first word only."""
    lines = (text or "").splitlines()[:12]
    for key in ("Status", "State"):
        for line in lines:
            m = re.match(r"^" + key + r":[ \t]*(.*)$", line)
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


def _row_text(nn, stem, text, where, source, f=None, roots=()):
    """One row from ticket text. `f` is the file on disk (or None); `abs` is set only when it lies inside the roots."""
    row = {"id": nn, "title": title_of(text, nn, stem), "status": status_of(text), "where": where, "source": source}
    if not any(x.startswith("# ") for x in (text or "").splitlines()):
        row["untitled"] = True   # the title is the file name (the panel shows it in italics)
    if f is not None:
        try:
            real = f.resolve()
            if any(real == r or r in real.parents for r in roots):
                row["abs"] = str(real)
        except OSError:
            pass
    return row


def _row(f, root, roots, source):
    nn = NUM_FILE.match(f.name).group(1)
    rel = _rel(f, root) if root else None
    return _row_text(nn, f.stem, _text(f), rel or f.as_posix(), source, f, roots)


# ---- merge by number (ticket 01): main, unmerged scope branches, drafts. Read-only git; see _branch_copies.
GIT_BUDGET_S = 2.0   # below the board reader's READ_BUDGET_S (3 s): a slow git must leave time for the non-git rows
MAX_BRANCHES = 40
HEADS_TTL_S = 2.0
_TREES, _BLOBS, _BASES, _HEADS = {}, {}, {}, {}   # (tip sha, path) -> {name: blob}; blob sha -> text; (main sha, tip) -> merge-base. Shas are immutable, so no expiry.


def _remember(cache, key, val):
    if len(cache) > 2000:
        cache.clear()
    cache[key] = val
    return val


def _squad_of(home):
    h = Path(str(home))
    return h.parent.parent.name if h.parent.name == "scopes" else None


def _blob_sha(path):
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _heads(root, squad, left):
    """-> (main sha list, [refs of squad/<squad>/*]) or None. One for-each-ref shared by every scope of the squad for 2 s,
    so a picker of 30 scopes asks git once."""
    key = (str(root), squad)
    hit = _HEADS.get(key)
    if hit and time.monotonic() - hit[0] < HEADS_TTL_S:
        return hit[1]
    refs = squadboard_git.heads(root, "squad/%s/" % squad, "main", timeout=left())
    if refs is None:
        return None
    main = [r for r in refs if r["branch"] == "main"]
    val = ([r["sha"] for r in main if r["branch"] == "main"], refs)
    _HEADS[key] = (time.monotonic(), val)
    return val


def _branch_copies(root, squad, scope, folder, left):
    """-> {int(number): [{branch, ts, blob, name}]}, or None (no git, a failed call, budget spent).

    Only branches `squad/<squad>/<scope>/*`, the 40 newest, and only the tickets a branch changed since its merge-base
    with main (an untouched ticket is main's old copy; a branch merged into main changes nothing, so it drops out). Calls: for-each-ref, then merge-base and
    ls-tree per branch, cached by sha. One budget for the phase.
    """
    if left() <= 0:
        return None
    got = _heads(root, squad, left)
    if got is None:
        return None
    mains, refs = got
    refs = sorted((r for r in refs if r["branch"].startswith("squad/%s/%s/" % (squad, scope)) and r["sha"]),
                  key=lambda r: -(r["ts"] or 0))[:MAX_BRANCHES]
    if not refs:
        return {}
    if not mains:
        return None
    path = ".scratch/%s/issues" % folder

    def tree(sha):
        key = (sha, path)
        if key not in _TREES:
            names = squadboard_git.ls_tree_blobs(root, sha, path, timeout=max(left(), 0.1)) if left() > 0 else None
            if names is None:
                return None
            _remember(_TREES, key, names)
        return _TREES[key]

    def numbered(names):
        out = {}
        for name in sorted(names):
            m = NUM_FILE.match(name)
            if m and re.match(r"^\d+-", name) and not NOT_TASK.search(name):
                out.setdefault(int(m.group(1)), (name, names[name], m.group(1)))
        return out

    out = {}
    for r in refs:
        mkey = (mains[0], r["sha"])
        if mkey not in _BASES:
            if left() <= 0:
                return None
            base = squadboard_git.merge_base(root, mains[0], r["sha"], timeout=left())
            if base is None:
                return None
            _remember(_BASES, mkey, base)
        names, bnames = tree(r["sha"]), tree(_BASES[mkey])
        if names is None or bnames is None:
            return None
        was = numbered(bnames)
        for n, (name, blob, nn) in numbered(names).items():
            if n in was and was[n][1] == blob:
                continue   # the branch did not change this ticket: its copy is just the old main one
            out.setdefault(n, []).append({"branch": r["branch"], "ts": r["ts"] or 0, "blob": blob, "name": name, "id": nn})
    return out


def _blob_text(root, blob, left):
    if blob not in _BLOBS:
        if left() <= 0:
            return None
        t = squadboard_git.show_blob(root, blob, timeout=max(left(), 0.1))
        if t is None:
            return None
        _remember(_BLOBS, blob, t[:TEXT_MAX])
    return _BLOBS[blob]


def _drafts(home):
    """Drafts of a ticket not committed yet: tasks/NN-ticket.md and tasks/issues/NN-*.md (tasks/NN.md is task state)."""
    out = {}
    for d, pat in ((home / "tasks", r"^\d+-ticket\.md$"), (home / "tasks" / "issues", r"^\d+-")):
        for f in _files(d):
            if re.match(pat, f.name):
                out.setdefault(int(NUM_FILE.match(f.name).group(1)), f)
    return out


def _folder_rows(home, root, roots, folder, src, name, git):
    """Rows of one ticket folder, all sources merged by number; [] when no source has a ticket."""
    main = {}
    for f in _files(root / ".scratch" / folder / "issues"):
        if re.match(r"^\d+-", f.name):
            main.setdefault(int(NUM_FILE.match(f.name).group(1)), f)
    squad = _squad_of(home)
    deadline = time.monotonic() + GIT_BUDGET_S   # one budget for every git call of this folder read

    def left():
        return deadline - time.monotonic()

    copies = (_branch_copies(root, squad, name, folder, left) if git and squad else None) or {}
    if not main and not copies:
        return []   # a draft alone does not make a folder: the scope's own tasks/ source reads it
    drafts = _drafts(home)
    rows = []
    for n in sorted(set(main) | set(copies) | set(drafts)):
        mf = main.get(n)
        mblob = _blob_sha(mf) if mf else None
        diff = sorted((c for c in copies.get(n, []) if c["blob"] != mblob), key=lambda c: -c["ts"])
        own = [c for c in diff if re.search(r"-0*%d$" % n, c["branch"])]
        row = None
        for c in own + [c for c in diff if c not in own]:
            text = _blob_text(root, c["blob"], left)
            if text is not None:
                where = ".scratch/%s/issues/%s" % (folder, c["name"])
                row = _row_text(c["id"], Path(c["name"]).stem, text, where, src, mf, roots)
                row.update(origin="branch", origin_ref=c["branch"])
                break
        if row is None and mf:
            row = _row(mf, root, roots, src)
            row.update(origin="main", origin_ref="")
        if row is None and n in drafts:
            row = _row(drafts[n], root, roots, src)
            row.update(origin="draft", origin_ref="")
        if row is None:
            continue
        row["on_main"] = mf is not None
        rows.append(row)
    return rows


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


def scope_tasks(scope_home, repo_root=None, name=None, git=True):
    try:
        return _scope_tasks(scope_home, repo_root, name, git)
    except Exception:  # a reader never raises
        return {"tasks": [], "source": None, "dir": None, "tried": [], "looked": []}


def _scope_tasks(scope_home, repo_root, name, git=True):
    home = Path(str(scope_home))
    root = Path(repo_root).resolve() if repo_root else _repo_of(home)
    name = name or home.name
    roots = [r for r in (home.resolve().parent.parent if home.parent.name == "scopes" else home.resolve(),
                         root / ".scratch" if root else None) if r]
    tried, found = ["scope.md (tickets: line)"], (None, [], None)
    for src in SOURCES:
        if src in ("declared", "scratch"):
            slug = declared_folder(home) if src == "declared" else name
            if not slug or root is None:
                continue
            d = root / ".scratch" / slug / "issues"
            tried.append(".scratch/%s/issues" % slug)
            rows = _folder_rows(home, root, roots, slug, src, name, git)
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
