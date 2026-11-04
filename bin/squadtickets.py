"""squad tickets: find the ticket folder of a scope. Moved out of squadreport_tasks (behaviour unchanged).

find_tickets(c, raw_tokens) -> ({NN: title}, relative feature dir or None). Never raises:
no `.scratch`, no ticket folder or an unreadable file gives ({}, None) or the file-name title.
`c` needs `.scope_home` and `.name`.
"""
import re
from pathlib import Path


def find_tickets(c, raw_tokens):
    """-> ({NN: title}, relative feature dir or None)."""
    root = None
    p = Path(str(c.scope_home)).resolve()
    for _ in range(10):
        if (p / ".scratch").is_dir():
            root = p
            break
        if p.parent == p:
            break
        p = p.parent
    if root is None:
        return {}, None
    declared = declared_folder(c.scope_home)
    if declared and (root / ".scratch" / declared / "issues").is_dir():
        files = [f for f in sorted((root / ".scratch" / declared / "issues").glob("*.md")) if re.match(r"^\d+-", f.name)]
        if files:
            return _titles(files), ".scratch/" + declared
    best = None
    for fdir in sorted((root / ".scratch").glob("*")):
        files = sorted((fdir / "issues").glob("*.md")) if (fdir / "issues").is_dir() else []
        files = [f for f in files if re.match(r"^\d+-", f.name)]
        if not files:
            continue
        stems = {f.stem for f in files}
        nns = {f.name.split("-", 1)[0] for f in files}
        slug = sum(1 for t in raw_tokens if t in stems)
        cover = sum(1 for t in raw_tokens if t in nns)
        score = (slug, 1 if fdir.name == c.name else 0, cover)
        if best is None or score > best[0]:
            best = (score, fdir, files)
    if best is None:
        return {}, None
    _, fdir, files = best
    return _titles(files), str(fdir.relative_to(root)).replace("\\", "/")


def declared_folder(scope_home):
    """The `tickets: <feature-slug>` line of scope.md (key case ignored, CRLF ok), or None."""
    try:
        text = (Path(str(scope_home)) / "scope.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        m = re.match(r"^\s*tickets\s*:\s*(\S+)\s*$", line, re.I)
        if m and re.match(r"^[\w.-]+$", m.group(1)):
            return m.group(1)
    return None


def _titles(files):
    out = {}
    for f in files:
        nn = f.name.split("-", 1)[0]
        title = f.stem.split("-", 1)[1] if "-" in f.stem else f.stem
        try:
            for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith("# "):
                    title = re.sub(r"^\d+\s*[:.-]\s*", "", line[2:].strip())
                    break
        except OSError:
            pass
        out[nn] = title
    return out
