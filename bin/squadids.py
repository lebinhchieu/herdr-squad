"""ID tokens (D73, O17, LC-14) that a reader cannot look up: the one check `squad-inbox add` and the Aim check share."""
import re

TOKEN_RE = re.compile(r"(?<![\w`])[A-Z]{1,4}-?\d+(?!\w)")
FENCE_RE = re.compile(r"```.*?(?:```|\Z)", re.S)
CODE_RE = re.compile(r"`[^`\n]*`")
LINK_RE = re.compile(r"\[[^\]\n]*\]\([^)\n]*\)")
GLOSS_RE = re.compile(r"\s*\([^)]+\)|\s=\s\S")


def _blank(match):
    return re.sub(r"[^\n]", " ", match.group(0))


def bare_ids(text):
    """The ID tokens in `text` whose first use has no gloss `(...)` or ` = ...` on the same line, in order.

    Fences, `code` and [links](url) are blanked first (same length), so they are never checked and cannot fake a gloss.
    """
    for pattern in (FENCE_RE, CODE_RE, LINK_RE):
        text = pattern.sub(_blank, text)
    seen, bare = set(), []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        for m in TOKEN_RE.finditer(line):
            if m.group(0) in seen:
                continue
            seen.add(m.group(0))
            if not GLOSS_RE.match(line, m.end()):
                bare.append(m.group(0))
    return bare
