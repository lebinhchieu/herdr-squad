"""Lint a process.md against the writing rule (design §9). stdlib only.

lint(text, budget, exceptions) -> ["line N: <check>: <detail>", ...]; line 0 = whole file.
CLI: python3 bin/processlint.py FILE  (exit 1 on any problem).
"""
import re
import sys

MAX_WORDS = 60
MAX_BOLD_WORDS = 15
MIN_DUP_WORDS = 8

_BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_HEDGE = re.compile(
    r"(?<!\w)(?:try to|ideally|preferably|where possible|as appropriate|as needed|usually|generally"
    r"|properly|carefully|etc\.|and so on|should)(?!\w)", re.I)
_HISTORY = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b|\b(?:19|20)\d\d\b"
    r"|(?<!\w)(?:changelog|formerly|previously|used to|no longer|was added|was changed|was renamed)(?!\w)", re.I)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _blocks(lines):
    """Yield (kind, first line number, text, first line) outside code fences.

    kind: bullet | para | heading | cell. A bullet or paragraph includes its wrapped continuation
    lines; a table row yields one block per cell.
    """
    fenced = False
    cur = None  # [kind, number, [lines]]
    out = []

    def flush():
        nonlocal cur
        if cur:
            out.append((cur[0], cur[1], " ".join(cur[2]), cur[2][0]))
        cur = None

    for n, raw in enumerate(lines, 1):
        s = raw.strip()
        if s.startswith("```"):
            flush()
            fenced = not fenced
            continue
        if fenced:
            continue
        if not s:
            flush()
        elif s.startswith("#"):
            flush()
            out.append(("heading", n, s, s))
        elif s.startswith("|"):
            flush()
            if not re.fullmatch(r"[|\s:-]+", s):
                for cell in s.strip("|").split("|"):
                    if cell.strip():
                        out.append(("cell", n, cell.strip(), s))
        elif _BULLET.match(raw):
            flush()
            cur = ["bullet", n, [_BULLET.sub("", raw, 1).strip()]]
        elif cur:
            cur[2].append(s)
        else:
            cur = ["para", n, [s]]
    flush()
    return out


def _norm(text):
    return " ".join(re.sub(r"[*`_|]", "", text).lower().split())


def _problems(text, budget):
    lines = text.splitlines()
    found = []  # (line, check, detail, line text for exception matching)

    def add(n, check, detail, shown=""):
        found.append((n, check, detail, shown.strip()))

    size = len(text.encode("utf-8"))
    if size > budget:
        add(0, "size", f"{size} bytes > {budget}")

    fenced = False
    rule_lines, first_h2 = [], None
    for n, raw in enumerate(lines, 1):
        if raw.strip().startswith("```"):
            fenced = not fenced
        elif not fenced:
            if raw.startswith("**Writing rule.**"):
                rule_lines.append(n)
            if first_h2 is None and raw.startswith("## "):
                first_h2 = n
            for pat, check in ((_HEDGE, "hedge"), (_HISTORY, "history")):
                for m in pat.finditer(raw):
                    add(n, check, f"'{m.group(0)}'", raw)
    if len(rule_lines) != 1:
        add(0, "writing-rule", f"{len(rule_lines)} lines start with '**Writing rule.**', need exactly one")
    elif first_h2 is not None and rule_lines[0] > first_h2:
        add(rule_lines[0], "writing-rule", f"comes after the first '##' (line {first_h2})", lines[rule_lines[0] - 1])

    seen = {}
    for kind, n, body, first in _blocks(lines):
        if kind == "heading":
            continue
        words = len(body.split())
        if words > MAX_WORDS:
            add(n, "length", f"{words} words > {MAX_WORDS}", first)
        spans = _BOLD.findall(body)
        if kind == "bullet" and len(spans) > 1:
            add(n, "bold", f"{len(spans)} bold spans in one bullet", first)
        for span in spans:
            if len(span.split()) > MAX_BOLD_WORDS:
                add(n, "bold", f"bold span of {len(span.split())} words > {MAX_BOLD_WORDS}", first)
        if kind == "cell":
            continue  # a table row is compared whole, below
        for sentence in _SENTENCE_SPLIT.split(body):
            key = _norm(sentence)
            if len(key.split()) < MIN_DUP_WORDS:
                continue
            if key in seen:
                add(n, "duplicate", f"repeats line {seen[key]}", first)
            else:
                seen[key] = n
    rows = {}
    fenced = False
    for n, raw in enumerate(lines, 1):
        s = raw.strip()
        if s.startswith("```"):
            fenced = not fenced
        elif not fenced and s.startswith("|") and not re.fullmatch(r"[|\s:-]+", s):
            key = _norm(s)
            if key in rows:
                add(n, "duplicate", f"table row repeats line {rows[key]}", s)
            else:
                rows[key] = n
    return sorted(found, key=lambda p: p[0])


def lint(text, budget=15000, exceptions=()):
    """exceptions: (check, line-text prefix, reason). No reason raises; one matching nothing is stale."""
    for exc in exceptions:
        if len(exc) != 3 or not str(exc[2]).strip():
            raise ValueError(f"exception {exc!r} needs a reason: (check, line-text prefix, reason)")
    problems = _problems(text, budget)
    used = set()
    kept = []
    for n, check, detail, shown in problems:
        hit = [i for i, (c, prefix, _) in enumerate(exceptions) if c == check and shown.startswith(prefix)]
        used.update(hit)
        if not hit:
            kept.append(f"line {n}: {check}: {detail}")
    for i, (check, prefix, _) in enumerate(exceptions):
        if i not in used:
            kept.append(f"line 0: stale-exception: ({check}, {prefix!r}) matches no problem")
    return kept


def main(argv):
    if len(argv) != 2:
        print("usage: processlint.py FILE", file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as f:
        out = lint(f.read())
    for line in out:
        print(line)
    return 1 if out else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
