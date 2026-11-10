"""squad-review-pack: builds pack.md (AC, diff stat, capped hunks, commands, evidence path) and pack-blackbox.md
(Business AC, invocation commands, evidence path; no code, SAFE-10). Read-only git, args as a list; the two files are
written only after both texts are built, so an error leaves nothing behind."""
import os
import re
import subprocess
import sys
from pathlib import Path

import squadtickets

USAGE = "usage: squad-review-pack NN [--sha S] [--base REF] [--scope DIR] [--max-lines N]"
CMD = re.compile(r"`((?:python3 |cd tests|squad-|bin/squad-|tests/)[^`\n]*)`")


class Usage(Exception):
    pass


def git(*args, cwd=None):
    try:
        return subprocess.run(["git", "--no-optional-locks", *args], capture_output=True, encoding="utf-8", cwd=cwd, timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        raise Usage("git failed: %s" % e)


def resolve(ref, what):
    if not ref or ref.startswith("-"):
        raise Usage("not a ref (%s): %s" % (what, ref))
    r = git("rev-parse", "--verify", "--quiet", ref + "^{commit}")
    if r.returncode != 0:
        raise Usage("unknown %s: %s" % (what, ref))
    return r.stdout.strip()


def parse(argv):
    nn = sha = base = scope = None
    maxl = 400
    it = iter(argv)
    for a in it:
        if a in ("-h", "--help"):
            print(USAGE)
            raise SystemExit(0)
        if a in ("--sha", "--base", "--scope", "--max-lines"):
            v = next(it, None)
            if v is None:
                raise Usage("%s needs a value" % a)
            if a == "--sha":
                sha = v
            elif a == "--base":
                base = v
            elif a == "--scope":
                scope = v
            else:
                if not v.isdigit() or int(v) < 1:
                    raise Usage("--max-lines needs a positive number")
                maxl = int(v)
        elif a.startswith("-"):
            raise Usage("unknown option: %s" % a)
        elif nn is None:
            nn = a
        else:
            raise Usage("one task number only")
    if nn is None or not re.fullmatch(r"\d+", nn):
        raise Usage(USAGE if nn is None else "NN must be digits: %s" % nn)
    scope = scope or os.environ.get("SCOPE_DIR")
    if not scope or not os.path.isdir(scope):
        raise Usage("no scope home: pass --scope DIR or set $SCOPE_DIR")
    return nn, sha or "HEAD", base, scope, maxl


def find_ticket(scope, nn, top):
    """-> (path, repo-relative evidence folder or None). Committed tickets come from squadtickets; a draft in
    `$SCOPE_DIR/tasks/` is the fallback (notes files next to a ticket, like NN-design-notes.md, are not the ticket)."""
    for row in squadtickets.scope_tasks(scope, repo_root=top)["tasks"]:
        if int(row["id"]) == int(nn) and row["source"] in ("declared", "scratch"):
            p = Path(row.get("abs") or (Path(top) / row["where"]))
            if p.is_file():
                return p, row["where"][:-3] if row["where"].endswith(".md") else row["where"]
    drafts = []
    for p in sorted((Path(scope) / "tasks").glob("*.md")):
        m = re.match(r"^(\d+)(?:-.*)?\.md$", p.name)
        if m and int(m.group(1)) == int(nn) and "notes" not in p.name:
            drafts.append(p)
    drafts.sort(key=lambda p: "## Business AC" not in p.read_text(encoding="utf-8", errors="replace"))
    if drafts:
        return drafts[0], None
    raise Usage("no ticket file for task %s in %s" % (nn, scope))


def section(text, prefix):
    out, on = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            on = line[3:].strip().lower().startswith(prefix.lower())
            if on:
                continue
        elif on:
            out.append(line)
    return "\n".join(out).strip()


def commands(text, blind):
    seen = []
    for m in CMD.finditer(text):
        c = m.group(1).strip()
        if c.startswith("tests/") and " " not in c:
            continue  # a file path, not a command
        if blind:
            if not c.startswith(("squad-", "bin/squad-")):
                continue
            c = c[4:] if c.startswith("bin/") else c
        if c not in seen:
            seen.append(c)
    return seen


def build(nn, sha, base, scope, maxl):
    top = git("rev-parse", "--show-toplevel").stdout.strip()
    if not top:
        raise Usage("not in a git repo")
    full = resolve(sha, "sha")
    if base:
        bfull = resolve(base, "base")
    else:
        r = git("merge-base", "main", full)
        if r.returncode != 0 or not r.stdout.strip():
            raise Usage("no base: pass --base REF")
        bfull = r.stdout.strip()
    ticket, folder = find_ticket(scope, nn, top)
    text = ticket.read_text(encoding="utf-8", errors="replace")
    biz, tech = section(text, "Business AC"), section(text, "Technical AC")
    ev = "%s/evidence.md" % folder if folder else "(ticket not committed yet: %s)" % ticket
    copy = "%s/evidence/%s/" % (scope, nn)
    head = "# Review pack, task %s\n\nsha: %s\nbase: %s\n" % (nn, full, bfull)

    stat = git("diff", "--no-color", "--no-ext-diff", "--stat", bfull + ".." + full).stdout.rstrip()
    diff = git("diff", "--no-color", "--no-ext-diff", "-U3", bfull + ".." + full).stdout.splitlines()
    shown = diff[:maxl]
    note = "\ncapped: showing %d of %d lines\n" % (maxl, len(diff)) if len(diff) > maxl else ""
    cmds = commands(text, False)
    full_md = "\n".join([
        head, "## Acceptance criteria", "", "### Business AC", "", biz or "(none)", "", "### Technical AC", "",
        tech or "(none yet)", "", "## Diff stat", "", "```", stat, "```", "", "## Hunks", "",
        "````diff", "\n".join(shown), "````", note, "## Test commands", "",
        "\n".join("- `%s`" % c for c in cmds) or "(none found)", "", "## Evidence path", "",
        "- ticket evidence: `%s`" % ev, "- review copy: `%s`" % copy, ""])
    bcmds = commands(biz, True)
    blind = "\n".join([
        "# Review pack (blackbox), task %s\n\nsha: %s\n" % (nn, full), "## Acceptance criteria", "", biz or "(none)", "",
        "## Behaviour commands", "", "\n".join("- `%s`" % c for c in bcmds) or "(none found)", "",
        "## Evidence path", "", "- review copy: `%s`" % copy, ""])
    return full_md, blind


def run(argv):
    try:
        nn, sha, base, scope, maxl = parse(argv)
        full_md, blind = build(nn, sha, base, scope, maxl)
        d = Path(scope) / "evidence" / nn
        d.mkdir(parents=True, exist_ok=True)
        (d / "pack.md").write_text(full_md, encoding="utf-8", newline="\n")
        (d / "pack-blackbox.md").write_text(blind, encoding="utf-8", newline="\n")
    except Usage as e:
        print("squad-review-pack: %s" % e, file=sys.stderr)
        return 2
    print("wrote %s and %s" % (d / "pack.md", d / "pack-blackbox.md"))
    return 0
