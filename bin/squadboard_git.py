"""squad board: the git calls. Stdlib only; `git` is found by name (ADR 0011).

Every function returns None (unknown) when git is missing, fails, times out or the repo is
not a repository. None means unknown; an empty list means "git answered: nothing". Never raises.
"""
import re
import subprocess

TIMEOUT_S = 10
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def _git(repo, *args, timeout=None):
    """-> stdout text, or None."""
    try:
        r = subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout or TIMEOUT_S)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def worktrees(repo):
    """git worktree list --porcelain -> [{path, head, branch}] (branch '' when detached) or None."""
    out = _git(repo, "worktree", "list", "--porcelain")
    return None if out is None else parse_worktrees(out)


def parse_worktrees(text):
    rows, cur = [], None
    for line in text.splitlines():
        if line.startswith("worktree "):
            cur = {"path": line[9:], "head": "", "branch": ""}
            rows.append(cur)
        elif cur is not None and line.startswith("HEAD "):
            cur["head"] = line[5:]
        elif cur is not None and line.startswith("branch "):
            ref = line[7:]
            cur["branch"] = ref[len("refs/heads/"):] if ref.startswith("refs/heads/") else ref
    return rows


def branch_refs(repo, prefix="", merged_into=None, timeout=None):
    """for-each-ref refs/heads/<prefix>* -> [{branch, sha, ts}] (ts epoch float or None) or None.

    merged_into='main' keeps only branches already merged into that ref.
    """
    args = ["for-each-ref", "--format=%(refname:short)\t%(objectname)\t%(committerdate:unix)"]
    if merged_into:
        args.append("--merged=" + merged_into)
    args.append("refs/heads/" + prefix)
    out = _git(repo, *args, timeout=timeout)
    return None if out is None else parse_refs(out)


def heads(repo, *prefixes, timeout=None):
    """One for-each-ref over several refs/heads/<prefix>* patterns -> [{branch, sha, ts}] or None."""
    out = _git(repo, "for-each-ref", "--format=%(refname:short)\t%(objectname)\t%(committerdate:unix)",
               *["refs/heads/" + p for p in prefixes], timeout=timeout)
    return None if out is None else parse_refs(out)


def parse_refs(text):
    rows = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        try:
            ts = float(parts[2])
        except ValueError:
            ts = None
        rows.append({"branch": parts[0], "sha": parts[1], "ts": ts})
    return rows


def last_commit_time(repo, ref="HEAD"):
    """Committer time of ref as epoch float, or None."""
    out = _git(repo, "log", "-1", "--format=%ct", ref, "--")
    try:
        return float(out.strip()) if out and out.strip() else None
    except ValueError:
        return None


def ls_tree_blobs(repo, sha, path, timeout=None):
    """git ls-tree -z <commit sha> -- <path> -> {file name: blob sha} (files directly in path) or None.

    Read-only. `sha` must be 40 hex (never a ref name, so it cannot become an option): anything else gives None.
    """
    if not isinstance(sha, str) or not HEX40.match(sha):
        return None
    out = _git(repo, "ls-tree", "-z", sha, "--", path.rstrip("/") + "/", timeout=timeout)
    if out is None:
        return None
    rows = {}
    for ent in out.split("\0"):
        meta, _, name = ent.partition("\t")
        parts = meta.split()
        if len(parts) == 3 and parts[1] == "blob" and HEX40.match(parts[2]):
            rows[name.rsplit("/", 1)[-1]] = parts[2]
    return rows


def show_blob(repo, blob, timeout=None):
    """git show <blob sha> -> text, or None. Only a 40-hex sha is accepted."""
    if not isinstance(blob, str) or not HEX40.match(blob):
        return None
    return _git(repo, "show", blob, timeout=timeout)


def merge_base(repo, main_sha, tip, timeout=None):
    """git merge-base <main sha> <tip sha> -> 40-hex sha or None. Both must be 40 hex."""
    if not all(isinstance(x, str) and HEX40.match(x) for x in (main_sha, tip)):
        return None
    out = _git(repo, "merge-base", main_sha, tip, timeout=timeout)
    out = (out or "").strip()
    return out if HEX40.match(out) else None
