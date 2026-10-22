"""squad-evidence: one evidence.md per ticket, screenshots embedded in place.

  squad-evidence path <ticket.md>
  squad-evidence add <ticket.md> --heading H --from review.md [--root DIR] [--sha SHA]
  squad-evidence check <evidence.md|folder> [--base SHA]

Layout: <ticket>.md -> <ticket minus .md>/evidence.md + <ticket minus .md>/img/<name>.
An old <ticket minus .md>.evidence/ folder is still read and written while the new folder does not exist.
Exit 0 ok, 1 problems found (one `file:line: problem` per line), 2 usage error or missing input.
"""
import argparse
import os
import re
import subprocess
import sys

IMG_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp")
MAX_BYTES = 1024 * 1024
EMBED = re.compile(r"""!\[([^\]]*)\]\(\s*(<[^>]*>|[^)\s]*)(?:\s+(?:"[^"]*"|'[^']*'))?\s*\)""")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
HEADING = re.compile(r"^(#{1,6})[ \t]+\S")
MENTION = re.compile(r"[\w./\\-]+\.(?:png|jpe?g|gif|webp)\b", re.IGNORECASE)
SCHEME = re.compile(r"^(?:[A-Za-z][A-Za-z0-9+.-]*:|//)")
DRIVE = re.compile(r"^[A-Za-z]:[\\/]")


class Usage(Exception):
    """A usage error or a missing input: exit 2."""


def read(path):
    try:
        with open(path, encoding="utf-8", newline="\n") as f:
            text = f.read()
    except OSError as e:
        raise Usage(f"cannot read {path}: {e.strerror}")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def evidence_folder(ticket):
    if not ticket.endswith(".md"):
        raise Usage(f"not a ticket file (must end .md): {ticket}")
    new = ticket[:-3]
    old = new + ".evidence"
    if os.path.isdir(old) and not os.path.isdir(new):
        return old
    return new


def scan(text):
    """(line number from 1, line, in_fence) per line; a fence line itself counts as in the fence."""
    opened = None
    for no, line in enumerate(text.split("\n"), 1):
        m = FENCE.match(line)
        if opened is None:
            if m:
                opened = (m.group(1)[0], len(m.group(1)))
            yield no, line, m is not None
        else:
            if m and m.group(1)[0] == opened[0] and len(m.group(1)) >= opened[1] and not m.group(2).strip():
                opened = None
            yield no, line, True


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "review"


def target_of(raw):
    return raw[1:-1].strip() if raw.startswith("<") else raw


def is_absolute(t):
    return t.startswith(("/", "\\")) or bool(DRIVE.match(t))


def is_url(t):
    return bool(SCHEME.match(t)) and not DRIVE.match(t)


def has_dotdot(t):
    return ".." in re.split(r"[\\/]", t)


def is_image(t):
    return t.lower().endswith(IMG_EXT)


# ---------------------------------------------------------------- path

def cmd_path(args):
    print(evidence_folder(args.ticket))
    return 0


# ---------------------------------------------------------------- add

def ticket_head(ticket_path, text):
    stem = os.path.basename(ticket_path)[:-3]
    m = re.match(r"(\d+)-", stem)
    nn = m.group(1) if m else stem
    title = ""
    for _no, line, in_fence in scan(text):
        if not in_fence and line.startswith("# "):
            title = line[2:].strip()
            break
    title = re.sub(r"^" + re.escape(nn) + r"\s*[:.\-]\s*", "", title)  # "# 01: x" would repeat the number
    return f"# Evidence: {nn} {title}".rstrip()


def split_sections(text):
    """(preamble, [[heading, chunk text], ...]); chunks keep their raw text, the file is their concatenation."""
    lines = text.split("\n")
    starts = []
    for no, line, in_fence in scan(text):
        if not in_fence and line.startswith("## "):
            starts.append((no - 1, line[3:].strip()))
    if not starts:
        return text, []
    pre = "\n".join(lines[:starts[0][0]])
    pre = pre + "\n" if pre else ""
    out = []
    for i, (at, head) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(lines)
        chunk = "\n".join(lines[at:end])
        chunk = chunk + "\n" if end < len(lines) else chunk
        out.append([head, chunk])
    return pre, out


def demote(lines_in_fence, shift):
    out = []
    for line, in_fence in lines_in_fence:
        m = None if in_fence else HEADING.match(line)
        if m and shift:
            level = min(6, len(m.group(1)) + shift)
            line = "#" * level + line[len(m.group(1)):]
        out.append(line)
    return out


def img_names(text):
    """Names embedded as img/<name> outside fences."""
    names = set()
    for _no, line, in_fence in scan(text):
        if in_fence:
            continue
        for m in EMBED.finditer(line):
            t = target_of(m.group(2))
            if t.startswith("img/"):
                names.add(t[4:])
    return names


def cmd_add(args):
    ticket = args.ticket if not args.root or os.path.isabs(args.ticket) else os.path.join(args.root, args.ticket)
    folder = evidence_folder(ticket)
    ticket_text = read(ticket)
    review_path = args.review
    review = read(review_path)
    review_dir = os.path.dirname(os.path.abspath(review_path))
    heading = args.heading.strip()
    if not heading:
        raise Usage("--heading is empty")
    img_dir = os.path.join(folder, "img")
    ev_path = os.path.join(folder, "evidence.md")
    existing = read(ev_path) if os.path.exists(ev_path) else None

    if existing is None:
        pre, sections = ticket_head(ticket, ticket_text) + "\n", []
    else:
        pre, sections = split_sections(existing)
    old = next((s for s in sections if s[0] == heading), None)
    owned = img_names(old[1]) if old else set()
    present = set(os.listdir(img_dir)) if os.path.isdir(img_dir) else set()

    classified = list(scan(review))
    levels = [len(HEADING.match(line).group(1)) for _no, line, f in classified if not f and HEADING.match(line)]
    shift = max(0, 3 - min(levels)) if levels else 0

    claimed, copies, missing = {}, {}, []
    sl = slug(heading)

    def pick(name, src):
        cands = [name, f"{sl}-{name}"] + [f"{sl}-{i}-{name}" for i in range(2, 1000)]
        for c in cands:
            if c in claimed:
                if claimed[c] == src:
                    return c
                continue
            if c in present and c not in owned:
                continue
            claimed[c] = src
            return c
        raise Usage(f"no free image name for {name}")

    def rewrite(m):
        alt, t = m.group(1), target_of(m.group(2))
        if not t or is_url(t) or not is_image(t):
            return m.group(0)
        src = os.path.normpath(t if is_absolute(t) else os.path.join(review_dir, t))
        if not os.path.isfile(src):
            missing.append(t)
            return m.group(0)
        name = pick(re.sub(r"[^A-Za-z0-9._-]", "-", os.path.basename(src)), src)
        copies[name] = src
        return f"![{alt}](img/{name})"

    body_lines = []
    for (_no, line, in_fence) in classified:
        body_lines.append(line if in_fence else EMBED.sub(rewrite, line))
    if missing:
        raise Usage("image not found: " + ", ".join(missing) + f" (referenced from {review_path})")
    body_lines = demote(list(zip(body_lines, [f for _n, _l, f in classified])), shift)
    body = "\n".join(body_lines).strip("\n")
    section = f"## {heading}\n\n{body}\n"

    if args.sha:
        sha_line = f"sha: {args.sha}"
        if re.search(r"(?m)^sha:.*$", pre):
            pre = re.sub(r"(?m)^sha:.*$", lambda _m: sha_line, pre, count=1)
        else:
            pre = pre.rstrip("\n") + "\n" + sha_line + "\n"

    if old:
        old[1] = section + ("\n" if sections[-1] is not old else "")
    else:
        if sections and not sections[-1][1].endswith("\n\n"):
            sections[-1][1] += "\n\n" if not sections[-1][1].endswith("\n") else "\n"
        elif not sections and not pre.endswith("\n\n"):
            pre += "\n" if pre.endswith("\n") else "\n\n"
        sections.append([heading, section])
    text = pre + "".join(c for _h, c in sections)
    if old and sections[-1] is old:
        text = text.rstrip("\n") + "\n"

    # everything validated: write
    for name, src in copies.items():
        with open(src, "rb") as f:
            data = f.read()
        dest = os.path.join(img_dir, name)
        if os.path.isfile(dest):
            with open(dest, "rb") as f:
                if f.read() == data:
                    continue
        os.makedirs(img_dir, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
    if existing != text:
        write(ev_path, text)
    for name in owned - img_names(text):  # images only the replaced section used
        p = os.path.join(img_dir, name)
        if os.path.isfile(p):
            os.remove(p)
    print(ev_path)
    return 0


# ---------------------------------------------------------------- check

def is_evidence_path(top, p):
    """A changed path (relative to the repo top) that may appear in an evidence commit."""
    if re.search(r"(^|/)[^/]+\.evidence/", p):
        return True
    parts = p.split("/")
    for i in range(len(parts) - 1):
        rest = parts[i + 1:]
        if rest == ["evidence.md"] or (rest[0] == "img" and len(rest) > 1):
            stem = "/".join(parts[:i + 1])
            return os.path.isfile(os.path.join(top, stem + ".md"))
    return False


def cmd_check(args):
    target = args.target
    if os.path.isdir(target):
        folder, ev_path = target, os.path.join(target, "evidence.md")
    else:
        folder, ev_path = os.path.dirname(target) or ".", target
    if not os.path.isfile(ev_path):
        raise Usage(f"no evidence.md: {ev_path}")
    text = read(ev_path)
    problems = []
    used = set()

    def bad(where, no, msg):
        line = f"{where}:{no}: {msg}"
        if line not in problems:
            problems.append(line)

    for no, line, in_fence in scan(text):
        if in_fence:
            continue
        for m in EMBED.finditer(line):
            alt, t = m.group(1), target_of(m.group(2))
            if is_url(t):
                bad(ev_path, no, f"embed is a URL: {t}")
                continue
            if is_absolute(t):
                bad(ev_path, no, f"embed path is absolute: {t}")
                continue
            if has_dotdot(t):
                bad(ev_path, no, f"embed path has '..': {t}")
                continue
            if not alt.strip():
                bad(ev_path, no, f"embed has empty alt text: {t}")
            if not is_image(t):
                bad(ev_path, no, f"embed is not an image file: {t}")
                continue
            full = os.path.normpath(os.path.join(folder, t))
            if not os.path.isfile(full):
                bad(ev_path, no, f"embed target is missing: {t}")
            else:
                used.add(full)
        rest = EMBED.sub(" ", line)
        for mm in MENTION.finditer(rest):
            bad(ev_path, no, f"image named but not embedded (use ![alt](img/name)): {mm.group(0)}")

    img_dir = os.path.join(folder, "img")
    if os.path.isdir(img_dir):
        for root, _dirs, files in os.walk(img_dir):
            for name in sorted(files):
                full = os.path.normpath(os.path.join(root, name))
                shown = os.path.join(root, name)
                if full not in used:
                    bad(shown, 1, "orphan image: no embed in evidence.md uses it")
                if os.path.getsize(full) > MAX_BYTES:
                    bad(shown, 1, f"image over 1 MB ({os.path.getsize(full)} bytes)")

    if args.base:
        try:
            r = subprocess.run(["git", "-C", folder, "diff", "--name-only", args.base, "HEAD"],
                               capture_output=True, encoding="utf-8")
        except OSError as e:
            raise Usage(f"git failed: {e.strerror}")
        if r.returncode != 0:
            raise Usage(f"git diff --name-only {args.base} HEAD failed: {r.stderr.strip()}")
        top = subprocess.run(["git", "-C", folder, "rev-parse", "--show-toplevel"],
                             capture_output=True, encoding="utf-8").stdout.strip() or "."
        for p in r.stdout.split("\n"):
            p = p.strip()
            if p and not is_evidence_path(top, p):
                bad(p, 1, f"changed since {args.base} but outside an evidence folder "
                          "(<stem>/evidence.md or <stem>/img/ beside <stem>.md, or an old *.evidence/ folder)")

    for line in problems:
        print(line)
    if not problems:
        print(f"ok: {ev_path}")
    return 1 if problems else 0


# ---------------------------------------------------------------- cli

class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Usage(f"{message}\n{self.format_usage().strip()}")


def build():
    p = Parser(prog="squad-evidence", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True, parser_class=Parser)
    a = sub.add_parser("path", help="print the evidence folder of a ticket file")
    a.add_argument("ticket")
    a = sub.add_parser("add", help="add or replace one review section in evidence.md")
    a.add_argument("ticket")
    a.add_argument("--heading", required=True)
    a.add_argument("--from", dest="review", required=True)
    a.add_argument("--root", default=None, help="folder a relative ticket path is resolved against")
    a.add_argument("--sha", default=None, help="value of the sha: line")
    a = sub.add_parser("check", help="verify evidence.md (and, with --base, that the diff is evidence-only)")
    a.add_argument("target")
    a.add_argument("--base", default=None)
    return p


def run(argv):
    try:
        args = build().parse_args(argv)
        return {"path": cmd_path, "add": cmd_add, "check": cmd_check}[args.cmd](args)
    except Usage as e:
        print(f"squad-evidence: {e}", file=sys.stderr)
        return 2
    except SystemExit as e:  # --help
        return e.code if isinstance(e.code, int) else 0
