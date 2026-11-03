"""squad board: the git calls. Stdlib only; `git` is found by name (ADR 0011).

Every function returns None (unknown) when git is missing, fails, times out or the repo is
not a repository. None means unknown; an empty list means "git answered: nothing". Never raises.
"""
import subprocess

TIMEOUT_S = 10


def _git(repo, *args):
    """-> stdout text, or None."""
    try:
        r = subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=TIMEOUT_S)
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


def branch_refs(repo, prefix="", merged_into=None):
    """for-each-ref refs/heads/<prefix>* -> [{branch, sha, ts}] (ts epoch float or None) or None.

    merged_into='main' keeps only branches already merged into that ref.
    """
    args = ["for-each-ref", "--format=%(refname:short)\t%(objectname)\t%(committerdate:unix)"]
    if merged_into:
        args.append("--merged=" + merged_into)
    args.append("refs/heads/" + prefix)
    out = _git(repo, *args)
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
