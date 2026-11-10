"""squad-merge-check: the Manager's pre-merge checks, read-only. Task states come from squadtask (the event store),
the evidence-only rule is the one of `squad-evidence check --base`. Only git read commands run; args are a list."""
import os
import re
import subprocess
import sys

import squadtask

USAGE = "usage: squad-merge-check <branch-or-sha> [--base REF] [--scope DIR]"
OLD_EVIDENCE = re.compile(r"(^|/)[^/]+\.evidence/")


class Usage(Exception):
    pass


def git(*args):
    try:
        r = subprocess.run(["git", "--no-optional-locks", *args], capture_output=True, encoding="utf-8", timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        raise Usage("git failed: %s" % e)
    return r


def out(*args):
    r = git(*args)
    return r.stdout.splitlines() if r.returncode == 0 else []


def resolve(ref):
    if ref.startswith("-"):
        raise Usage("not a ref: %s" % ref)
    r = git("rev-parse", "--verify", "--quiet", ref + "^{commit}")
    if r.returncode != 0:
        raise Usage("unknown ref: %s" % ref)
    return r.stdout.strip()


def is_ancestor(a, b):
    return git("merge-base", "--is-ancestor", a, b).returncode == 0


def merge_base(a, b):
    r = git("merge-base", a, b)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def changed(a, b):
    return set(out("diff", "--name-only", a + ".." + b))


def test_hits(files, ref):
    """Test files under tests/ that mention a changed file (fixed string, base name): `grep -rl` semantics."""
    names = sorted({os.path.basename(f) for f in files if f and not f.startswith("tests/")})
    hits = set()
    for n in names:
        for line in out("grep", "-l", "-F", "-e", n, ref, "--", "tests/"):
            hits.add(line.split(":", 1)[1] if ":" in line else line)
    return hits


def is_evidence_path(ref, p):
    """Same rule as squadevidence.is_evidence_path, but the ticket `<stem>.md` is looked up in `ref`, not on disk."""
    if OLD_EVIDENCE.search(p):
        return True
    parts = p.split("/")
    for i in range(len(parts) - 1):
        rest = parts[i + 1:]
        if rest == ["evidence.md"] or (rest[0] == "img" and len(rest) > 1):
            return git("cat-file", "-e", "%s:%s.md" % (ref, "/".join(parts[:i + 1]))).returncode == 0
    return False


def evidence_only(old, new):
    """New is old plus commits that touch only a ticket's evidence.md / img (MRG-2)."""
    if not is_ancestor(old, new):
        return False
    return all(is_evidence_path(new, p) for p in changed(old, new))


def parse(argv):
    target = base = scope = None
    it = iter(argv)
    for a in it:
        if a in ("-h", "--help"):
            print(USAGE)
            raise SystemExit(0)
        if a in ("--base", "--scope"):
            v = next(it, None)
            if v is None:
                raise Usage("%s needs a value" % a)
            if a == "--base":
                base = v
            else:
                scope = v
        elif a.startswith("-"):
            raise Usage("unknown option: %s" % a)
        elif target is None:
            target = a
        else:
            raise Usage("one target only")
    if target is None:
        raise Usage(USAGE)
    return target, base or "HEAD", scope or os.environ.get("SCOPE_DIR")


def task_states(scope):
    if not scope or not os.path.isdir(scope):
        raise Usage("no scope home: pass --scope DIR or set $SCOPE_DIR")
    sd = squadtask.squad_dir_of(scope)
    return squadtask.fold(squadtask.read_events(sd, squadtask.slug_of(scope))), squadtask.checkers(scope)


def check(target, base_ref, scope):
    lines, reasons = [], []
    sha, base = resolve(target), resolve(base_ref)
    states, chk = task_states(scope)

    # GOAL-7: ancestor and log
    lines.append("ancestor: %s" % ("yes" if is_ancestor(base, sha) else "no"))
    log = out("log", "--oneline", base + ".." + sha)
    lines.append("log: %d commit(s)" % len(log))
    lines += ["  " + x for x in log]

    # MRG-2: both checkers passed this sha, or the evidence-only sha after it
    mine = []
    for st in states.values():
        br = st.get("branch")
        tip = resolve_quiet(br) if br else None
        if st.get("sha") and (br == target or tip == sha or squadtask._same_sha(st["sha"], sha)):
            mine.append(st)
    at_target = []
    for st in sorted(mine, key=lambda s: s["task"]):
        v = st["verdicts"]
        slots = squadtask.slots(chk)
        shown = ", ".join("%s=%s" % (s, v.get(s, "-")) for s in slots)
        if squadtask._same_sha(st["sha"], sha):
            m = "yes"
        elif resolve_quiet(st["sha"]) and evidence_only(st["sha"], sha):
            m = "yes (evidence-only after it)"
        elif resolve_quiet(st["sha"]) and is_ancestor(st["sha"], sha):
            m = "older"  # an earlier ticket of the same branch
        else:
            m = "no"
        ok = squadtask.is_passed(st, chk)
        lines.append("passed: ticket %s sha %s %s match=%s [%s]" % (st["task"], st["sha"][:9], "PASS" if ok else "not-passed", m, shown))
        if m.startswith("yes"):
            at_target.append((st, ok))
    if not mine:
        lines.append("passed: none (no task state for %s)" % target)
    if not any(ok for _, ok in at_target) or any(not ok for _, ok in at_target):
        reasons.append("sha not passed by every checker")

    # MRG-2 dirty root, MRG-5 untracked
    dirty, untracked = [], []
    for line in out("status", "--porcelain", "--untracked-files=all"):
        path = line[3:]
        if line.startswith("??"):
            if not path.startswith(".claude/squads/"):
                untracked.append(path)
        else:
            dirty.append(path)
    lines.append("dirty: %s" % (("yes (%s)" % ", ".join(dirty[:5])) if dirty else "no"))
    if dirty:
        reasons.append("project root has uncommitted changes")
    for p in untracked:
        lines.append("warning: untracked file outside .claude/squads/: " + p)

    # SQ-7: main moved
    if is_ancestor(base, sha):
        lines.append("main-moved: no")
    else:
        mb = merge_base(base, sha)
        if not mb:  # fail closed: unrelated histories are never "none related"
            lines.append("main-moved: yes, no merge base")
            reasons.append("no merge base with %s" % base_ref)
            lines.append("VERDICT: refuse: " + "; ".join(reasons))
            return lines, False
        on_base, on_sha = changed(mb, base), changed(mb, sha)
        shared = sorted(on_base & on_sha)
        hits = test_hits(on_base, base) & test_hits(on_sha, sha)
        lines.append("main-moved: yes, %d file(s) on base, %d on branch" % (len(on_base), len(on_sha)))
        if shared or hits:
            lines.append("main-related: shared files %s; shared test hits %s" % (shared or "none", sorted(hits) or "none"))
            reasons.append("main moved with related changes: a Developer merges main first (SQ-7b)")
        else:
            lines.append("main-related: main moved, %d files, none related" % len(on_base))

    # SQ-6: related passed siblings that are not ancestors
    mine_branches = {s.get("branch") for s in mine} | {target}
    my_files = changed(merge_base(base, sha) or base, sha)
    my_hits = test_hits(my_files, sha)
    related = []
    for st in states.values():
        br = st.get("branch")
        if not br or br in mine_branches or st.get("merged_ts") or not squadtask.is_passed(st, chk):
            continue
        tip = resolve_quiet(br)
        if not tip or is_ancestor(tip, sha) or is_ancestor(sha, tip):
            continue
        f = changed(merge_base(base, tip) or base, tip)
        if (f & my_files) or (test_hits(f, tip) & my_hits):
            if br not in related:
                related.append(br)
    lines.append("siblings: %s" % (("related " + ", ".join(related)) if related else "none related"))
    if related:
        reasons.append("related passed siblings not merged in: " + ", ".join(related))

    lines.append("VERDICT: " + ("ok" if not reasons else "refuse: " + "; ".join(reasons)))
    return lines, not reasons


def resolve_quiet(ref):
    if not ref or ref.startswith("-"):
        return None
    r = git("rev-parse", "--verify", "--quiet", ref + "^{commit}")
    return r.stdout.strip() if r.returncode == 0 else None


def run(argv):
    try:
        target, base, scope = parse(argv)
        lines, ok = check(target, base, scope)
    except Usage as e:
        print("squad-merge-check: %s" % e, file=sys.stderr)
        return 2
    print("\n".join(lines))
    return 0 if ok else 1
