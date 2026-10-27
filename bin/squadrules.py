"""Rule files, overlay, hash, `when:` and lint. stdlib only; every problem is a `file:line: text` string.

Contract: .scratch/composed-process/spec.md (Contracts) and the goal's shared contract rules-and-compose.md.
"""
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import processlint as pl  # noqa: E402

FILE_ORDER = [
    ("CORE", "core"), ("FILE", "files"), ("START", "starting"), ("SIZE", "sizes"), ("TEAM", "teams"), ("GOAL", "goal"),
    ("PROMO", "promotion"), ("CLOSE", "closing"), ("MSG", "messages"), ("WHO", "who"),
    ("LC", "lifecycle"), ("REV", "review"), ("EVID", "evidence"), ("ITER", "iterations"),
    ("COST", "cost"), ("NOTE", "notes"), ("SAFE", "safety"), ("SUITE", "suites"),
    ("MRG", "merge"), ("SPAWN", "spawning"),
]
PREFIX_OF = {stem: prefix for prefix, stem in FILE_ORDER}
PREFIXES = {prefix for prefix, _ in FILE_ORDER}
REMOVED_FILE = "_removed.md"
OVERLAY_FILE = "process.local.md"
ROLES = ("manager", "ba", "team-lead", "tech-lead", "qa-whitebox", "qa-blackbox", "designer", "architect", "dev", "token-coach")
# Team model (drop-scope-size, architecture.md sections 2 and 3). `team:` tokens in scope.md; the `when:` presence
# key of a token is PRESENCE_KEY (designer -> design, architect -> architecture, the rest the same string).
TEAM_KEYS = ("ba", "team-lead", "tech-lead", "qa-white", "qa-black", "designer", "architect")
IMPLICIT_ROLES = ("manager", "dev", "token-coach")
ROLE_KEY = {"qa-whitebox": "qa-white", "qa-blackbox": "qa-black"}  # role name -> team token; other roles map to themselves
OLD_TEAM_TOKENS = {v: k for k, v in ROLE_KEY.items()}  # never a token: `qa-whitebox`, `qa-blackbox` are role names
PRESENCE_KEY = {"ba": "ba", "team-lead": "team-lead", "tech-lead": "tech-lead", "qa-white": "qa-white",
                "qa-black": "qa-black", "designer": "design", "architect": "architecture"}
# Duty facts: first present chain item owns the duty; every chain ends at manager, dev or ticket. `qas` stands for
# "qa-white or qa-black on the team" (the hand-in goes to the QAs).
DUTIES = {
    "plan-owner": ("team-lead", "manager"),
    "design-notes": ("tech-lead", "dev"),
    "tech-ac": ("tech-lead", "qa-white", "dev"),
    "business-ac": ("ba", "ticket"),
    "code-check": ("qa-white", "tech-lead", "manager"),
    "behaviour-check": ("qa-black", "qa-white", "manager"),
    "ui-check": ("qa-black", "manager"),
    "handin-target": ("qas", "team-lead", "manager"),
    "suite-owner": ("tech-lead", "qa-white", "dev"),
    "promote-owner": ("tech-lead", "qa-white", "dev"),
    "risk-owner": ("tech-lead", "manager"),
    "doubt-owner": ("ba", "manager"),
    "choice-owner": ("architect", "tech-lead", "manager"),
}
_DUTY_TERMINAL = ("manager", "dev", "ticket")
# `size` and `qa-b` stay until the cutover task (old rule files still use them); the new keys sit beside them.
WHEN_KEYS = {"size": ("S", "M", "L"), "design": ("yes", "no"), "architecture": ("yes", "no"), "qa": ("full", "light"),
             "goal": ("yes", "no"), "qa-b": ("yes", "no"),
             **{k: ("yes", "no") for k in ("ba", "team-lead", "tech-lead", "qa-white", "qa-black")},
             **{fact: chain for fact, chain in DUTIES.items()}}
# A `when:` that uses a key of the team language holds at most one PRIMARY key; the rest are EXTRA (orthogonal).
PRIMARY_KEYS = frozenset(DUTIES) | {"ba", "team-lead", "tech-lead", "qa-white"}
EXTRA_KEYS = frozenset({"goal", "qa", "design", "architecture", "qa-black"})
PLUGIN_ATTRS = ("roles", "aware", "when", "topic")
OVERLAY_ATTRS = PLUGIN_ATTRS + ("why", "upstream")
UPSTREAM = ("proposed", "local-only", "rejected")
CORE_MAX_LINES = 40
MIN_DUP_WORDS = 12

_ID = r"[A-Z]+-\d+[a-z]?"
_HEAD_RULE = re.compile(rf"^## ({_ID}) (.+)$")
_HEAD_TOMB = re.compile(rf"^## ({_ID}) \(removed in (\S+)\)\s*$")
_HEAD_OP = re.compile(r"^## (replace|remove|add) (\S+)( @[0-9a-f]{8})?( .+)?$")
_ATTR = re.compile(r"^([a-z][a-z_-]*):[ \t]*(.*)$")
_TOPIC = re.compile(r"^[a-z][a-z0-9-]*$")
_CITE = re.compile(rf"\[({_ID})\]")


class Rule:
    def __init__(self, id, title, roles, aware, when, topic, body, file, line, attr_text, body_line=0):
        self.id, self.title, self.roles, self.aware, self.when, self.topic = id, title, roles, aware, when, topic
        self.body, self.file, self.line, self.attr_text, self.body_line = body, file, line, attr_text, body_line

    @property
    def hash(self):
        return rule_hash(self.attr_text, self.body)


class Op:
    def __init__(self, kind, id, hash, title, attrs, body, line, body_line=0):
        self.kind, self.id, self.hash, self.title, self.attrs, self.body = kind, id, hash, title, attrs, body
        self.line, self.body_line = line, body_line

    @property
    def why(self):
        return self.attrs.get("why")

    @property
    def upstream(self):
        return self.attrs.get("upstream")


class Tombstone:
    def __init__(self, id, version, why, replaced_by, line, file=""):
        self.id, self.version, self.why, self.replaced_by, self.line, self.file = id, version, why, replaced_by, line, file


# ---- text and hash -------------------------------------------------------------------------------

def normalize(text):
    """BOM dropped, CRLF and lone CR become LF."""
    if text.startswith("﻿"):
        text = text[1:]
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read_text(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return normalize(f.read())


def rule_hash(attr_text, body):
    """First 8 hex digits of the sha256 of the attribute lines, one blank line, the body (contract: Rule hash)."""
    def lines(t):
        return [ln.rstrip(" \t") for ln in normalize(t).split("\n")]
    body_lines = lines(body)
    while body_lines and not body_lines[0]:
        body_lines.pop(0)
    while body_lines and not body_lines[-1]:
        body_lines.pop()
    attr_lines = [ln for ln in lines(attr_text) if ln]
    data = "\n".join(attr_lines) + "\n\n" + "\n".join(body_lines)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:8]


# ---- when ----------------------------------------------------------------------------------------

def _conditions(when):
    for part in when.split(" and "):
        part = part.strip()
        m = re.fullmatch(r"([a-z][a-z-]*) = (\S+)", part)
        if m:
            key, values = m.group(1), [m.group(2)]
        else:
            m = re.fullmatch(r"([a-z][a-z-]*) in (\S+(?:, ?\S+)*)", part)
            if not m:
                raise ValueError(f"cannot read condition {part!r}")
            key, values = m.group(1), [v.strip() for v in m.group(2).split(",")]
        if key not in WHEN_KEYS:
            raise ValueError(f"unknown when key {key!r}")
        for v in values:
            if v not in WHEN_KEYS[key]:
                raise ValueError(f"unknown value {v!r} for when key {key!r}")
        yield key, values


def check_when_combination(when):
    """ValueError when a `when:` of the team language breaks one-primary-key (constraint 5). Old-key-only whens pass."""
    if not when or not when.strip():
        return
    keys = [k for k, _ in _conditions(when)]
    if not any(k in PRIMARY_KEYS or k == "qa-black" for k in keys):
        return
    primary = [k for k in keys if k in PRIMARY_KEYS]
    if len(primary) > 1:
        raise ValueError(f"when uses {len(primary)} duty/role keys ({', '.join(primary)}); at most one of them is allowed")
    bad = [k for k in keys if k not in PRIMARY_KEYS and k not in EXTRA_KEYS]
    if bad:
        raise ValueError(f"when mixes the team keys with {', '.join(bad)}; only goal, qa, design, architecture, qa-black may join one")


def matches(when, facts):
    """True when every condition holds; a fact missing from facts counts as true. ValueError on a bad key or value."""
    if not when or not when.strip():
        return True
    conds = list(_conditions(when))
    return all(key not in facts or facts[key] in values for key, values in conds)


def missing_fact_keys(when, facts):
    """Keys of `when` whose fact the home lacks (04 tags a title with them)."""
    if not when or not when.strip():
        return []
    return [key for key, _ in _conditions(when) if key not in facts]


# ---- team ----------------------------------------------------------------------------------------

def role_key(role):
    """Team token of a role name (`qa-whitebox` -> `qa-white`); ValueError for a name that is not a role."""
    if role not in ROLES:
        raise ValueError(f"unknown role {role!r}")
    return ROLE_KEY.get(role, role)


def parse_team(value, where="scope.md"):
    """Value of a `team:` line -> list of tokens (None when blank = undecided; [] for `none`). ValueError names `where`.

    A trailing `(note)` is commentary. Unknown, duplicate or implicit tokens are errors; `qa-whitebox` and
    `qa-blackbox` are role names, not tokens, and the error names the token to use."""
    text = re.sub(r"\s*\([^)]*\)\s*$", "", (value or "").replace("\r", "")).strip()
    if not text:
        return None
    if text.lower() == "none":
        return []
    tokens, seen = [], set()
    for raw in text.split(","):
        tok = raw.strip()
        if tok in ROLE_KEY:
            raise ValueError(f"{where}: team token {tok!r} is a role name; write {ROLE_KEY[tok]!r}")
        if tok in IMPLICIT_ROLES:
            raise ValueError(f"{where}: {tok!r} is always on the team; do not list it in team:")
        if tok not in TEAM_KEYS:
            raise ValueError(f"{where}: unknown team token {tok!r} (allowed: {', '.join(TEAM_KEYS)}, or none)")
        if tok in seen:
            raise ValueError(f"{where}: team token {tok!r} listed twice")
        seen.add(tok)
        tokens.append(tok)
    return [t for t in TEAM_KEYS if t in seen]


def resolve_duties(team):
    """team (tokens) -> {duty: owner}. Pure; the first present chain item owns the duty."""
    team = frozenset(team)
    out = {}
    for fact, chain in DUTIES.items():
        for item in chain:
            if item == "qas":
                if "qa-white" in team or "qa-black" in team:
                    out[fact] = "qas"
                    break
            elif item in _DUTY_TERMINAL or item in team:
                out[fact] = item
                break
    return out


def team_facts(team):
    """team (tokens) -> every presence and duty fact for a `when:` (a decided team never has a missing fact)."""
    team = frozenset(team)
    facts = {PRESENCE_KEY[t]: "yes" if t in team else "no" for t in TEAM_KEYS}
    facts.update(resolve_duties(team))
    return facts


def _first_token(value):
    toks = (value or "").split()
    return toks[0] if toks else ""


def legacy_team(size, qa_b="yes", design="no", architecture="no"):
    """Old `size:`, `qa-b:`, `design:`, `architecture:` values (raw text, commentary allowed) -> team tokens.

    For the converter and the branch-internal scaffold only (D1/D3). Uses the FIRST token of each value, so
    `size: M (confirmed ...)` is M and `size: confirmed M` is not (read_home's `\\b[SML]\\b` finds it anywhere). A blank
    or unreadable size gives None (undecided, a blank `team:`). A bad qa-b/design/architecture token is a ValueError."""
    sz = _first_token(size).rstrip(",;:.")
    if sz not in ("S", "M", "L"):
        return None
    flags = {}
    for name, value in (("qa-b", qa_b), ("design", design), ("architecture", architecture)):
        tok = _first_token(value).lower() or ("yes" if name == "qa-b" else "no")
        if tok not in ("yes", "no"):
            raise ValueError(f"{name} must be yes | no, got {value!r}")
        flags[name] = tok
    team = set()
    if sz in ("M", "L"):
        team |= {"qa-white"} | ({"qa-black"} if flags["qa-b"] == "yes" else set())
    if sz == "L":
        team |= {"ba", "team-lead", "tech-lead"}
    if flags["design"] == "yes":
        team.add("designer")
    if flags["architecture"] == "yes":
        team.add("architect")
    return [t for t in TEAM_KEYS if t in team]


# ---- parsing -------------------------------------------------------------------------------------

def _blocks(text, relpath, heading_ok, problems):
    """Split into (match, heading line, [(n, text)...]) blocks; outside fences a `## ` line starts one."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    blocks, cur, fenced = [], None, False
    for n, raw in enumerate(lines, 1):
        s = raw.strip()
        if s.startswith("```"):
            fenced = not fenced
        elif not fenced and raw.startswith("## "):
            m = heading_ok(raw)
            if m is None:
                problems.append(f"{relpath}:{n}: heading not in the rule format: {raw.strip()!r}")
            cur = [m, n, []]
            blocks.append(cur)
            continue
        if cur is None:
            if s and not raw.startswith("# ") and not fenced:
                problems.append(f"{relpath}:{n}: text outside a rule (before the first `## ` heading)")
        else:
            cur[2].append((n, raw))
    return blocks, lines


def _split_attrs(body_lines, allowed, relpath, problems, blank_required):
    """Leading `key: value` lines -> ([(n, key, value, raw)], body lines after them)."""
    attrs, i = [], 0
    while i < len(body_lines):
        n, raw = body_lines[i]
        m = _ATTR.match(raw.rstrip())
        if not m or (allowed is not None and m.group(1) not in allowed):
            break
        attrs.append((n, m.group(1), m.group(2).strip(), raw.rstrip(" \t")))
        i += 1
    rest = body_lines[i:]
    if blank_required and rest and rest[0][1].strip():
        problems.append(f"{relpath}:{rest[0][0]}: attribute lines must end with a blank line")
    return attrs, rest


def _body(rest):
    rest = list(rest)
    while rest and not rest[0][1].strip():
        rest.pop(0)
    while rest and not rest[-1][1].strip():
        rest.pop()
    first = rest[0][0] if rest else 0
    return "\n".join(r[1].rstrip(" \t") for r in rest), first


def _roles(value):
    return [r.strip() for r in value.split(",") if r.strip()]


def parse_rule_file(text, relpath, problems):
    """-> [Rule]; problems get `relpath:line: text` strings."""
    text = normalize(text)

    def head(raw):
        return _HEAD_RULE.match(raw)
    blocks, _ = _blocks(text, relpath, head, problems)
    rules = []
    for m, n, body_lines in blocks:
        if m is None:
            continue
        attrs, rest = _split_attrs(body_lines, None, relpath, problems, True)
        body, body_line = _body(rest)
        vals, seen, order = {}, set(), []
        for an, key, value, _raw in attrs:
            if key not in PLUGIN_ATTRS:
                problems.append(f"{relpath}:{an}: unknown attribute {key!r}")
            elif key in seen:
                problems.append(f"{relpath}:{an}: attribute {key!r} given twice")
            else:
                seen.add(key)
                order.append(key)
                vals[key] = value
        if order != [k for k in PLUGIN_ATTRS if k in seen]:
            problems.append(f"{relpath}:{n}: attribute lines out of order (expected roles, aware, when, topic)")
        rules.append(Rule(m.group(1), m.group(2).strip(), _roles(vals.get("roles", "")), _roles(vals.get("aware", "")),
                          vals.get("when", ""), vals.get("topic", ""), body, relpath, n,
                          "\n".join(a[3] for a in attrs), body_line))
    return rules


def parse_removed(text, relpath, problems):
    text = normalize(text)
    blocks, _ = _blocks(text, relpath, lambda raw: _HEAD_TOMB.match(raw), problems)
    out = []
    for m, n, body_lines in blocks:
        if m is None:
            continue
        attrs, _rest = _split_attrs(body_lines, None, relpath, problems, False)
        vals = {k: v for _n, k, v, _r in attrs}
        for key in ("why", "replaced_by"):
            if not vals.get(key):
                problems.append(f"{relpath}:{n}: tombstone {m.group(1)} has no {key}:")
        rb = [x for x in _roles(vals.get("replaced_by", "")) if x != "none"]
        out.append(Tombstone(m.group(1), m.group(2), vals.get("why", ""), rb, n, relpath))
    return out


def parse_overlay(text, relpath, problems):
    text = normalize(text)

    def head(raw):
        return _HEAD_OP.match(raw)
    blocks, _ = _blocks(text, relpath, head, problems)
    ops = []
    for m, n, body_lines in blocks:
        if m is None:
            continue
        attrs, rest = _split_attrs(body_lines, OVERLAY_ATTRS, relpath, problems, False)
        d = {}
        for an, key, value, _raw in attrs:
            if key in d:
                problems.append(f"{relpath}:{an}: attribute {key!r} given twice")
            d[key] = value
        body, body_line = _body(rest)
        title = (m.group(4) or "").strip()
        ops.append(Op(m.group(1), m.group(2), (m.group(3) or "").strip()[1:], title, d, body, n, body_line))
    return ops


def _file_rank(stem):
    for i, (_p, s) in enumerate(FILE_ORDER):
        if s == stem:
            return i, stem
    return len(FILE_ORDER), stem


def process_dir(plugin_root):
    return os.path.join(plugin_root, "templates", "squad", "process")


def load_rules(pdir, rel_root=None):
    """(rules in FILE_ORDER, tombstones, problems) for a process folder. Never raises on content."""
    rel_root = rel_root or pdir
    problems, rules, tombs = [], [], []
    names = sorted((n for n in os.listdir(pdir) if n.endswith(".md")), key=lambda n: _file_rank(n[:-3]))
    for name in names:
        rel = os.path.relpath(os.path.join(pdir, name), rel_root).replace(os.sep, "/")
        try:
            text = read_text(os.path.join(pdir, name))
        except (OSError, UnicodeDecodeError) as e:
            problems.append(f"{rel}:1: cannot read: {e}")
            continue
        if name == REMOVED_FILE:
            tombs.extend(parse_removed(text, rel, problems))
            continue
        stem = name[:-3]
        found = parse_rule_file(text, rel, problems)
        if stem not in PREFIX_OF:
            problems.append(f"{rel}:1: unknown file stem {stem!r} (not in FILE_ORDER)")
        else:
            for r in found:
                if r.id.split("-")[0] != PREFIX_OF[stem]:
                    problems.append(f"{rel}:{r.line}: ID {r.id} does not match the file prefix {PREFIX_OF[stem]}")
            if stem == "core":
                n_lines = len(text.rstrip("\n").split("\n"))
                if n_lines > CORE_MAX_LINES:
                    problems.append(f"{rel}:1: core.md has {n_lines} lines, over {CORE_MAX_LINES}")
                for r in found:
                    if r.roles != ["all"]:
                        problems.append(f"{rel}:{r.line}: core rule {r.id} needs `roles: all`")
        rules.extend(found)
    _structure(rules, tombs, problems)
    return rules, tombs, problems


# ---- lint ----------------------------------------------------------------------------------------

def _check_roles(value, key, rel, n, out):
    for r in value:
        if r != "all" and r not in ROLES:
            out.append(f"{rel}:{n}: unknown role {r!r} in {key}:")


def _check_attrs(vals, rel, n, out, need, rid=None):
    """Shared checks of a rule or an overlay op: roles, aware, when, topic. vals: key -> raw string."""
    for key in need:
        if not vals.get(key, "").strip():
            out.append(f"{rel}:{n}: missing {key}:")
    for key in ("roles", "aware"):
        if key in vals:
            _check_roles(_roles(vals[key]), key, rel, n, out)
    if vals.get("when", "").strip():
        try:
            matches(vals["when"], {})
        except ValueError as e:
            out.append(f"{rel}:{n}: {e}")
        else:
            try:
                check_when_combination(vals["when"])
            except ValueError as e:
                out.append(f"{rel}:{n}: {rid + ': ' if rid else ''}{e}")
    if vals.get("topic") and not _TOPIC.match(vals["topic"]):
        out.append(f"{rel}:{n}: topic {vals['topic']!r} is not [a-z][a-z0-9-]*")


def _structure(rules, tombs, out):
    """Checks compose depends on: unique IDs, tombstones, attributes of each rule."""
    first = {}
    for r in rules:
        if r.id in first:
            out.append(f"{r.file}:{r.line}: duplicate ID {r.id} (first at {first[r.id].file}:{first[r.id].line})")
        else:
            first[r.id] = r
    for t in tombs:
        if t.id in first:
            out.append(f"{t.file}:{t.line}: removed ID {t.id} is still a rule ({first[t.id].file}:{first[t.id].line})")
        for rb in t.replaced_by:
            if rb not in first:
                out.append(f"{t.file}:{t.line}: replaced_by names missing ID {rb}")
    for r in rules:
        raw = {k: v for k, v in (("roles", ", ".join(r.roles)), ("aware", ", ".join(r.aware)),
                                 ("when", r.when), ("topic", r.topic)) if v}
        _check_attrs(raw, r.file, r.line, out, ("roles", "topic"), r.id)


def _writing(body, body_line, rel, out):
    if not body:
        return
    for n, check, detail, _shown in pl._problems(body):
        if check != "duplicate":
            out.append(f"{rel}:{body_line + n - 1}: {check}: {detail}")


def _sentences(text, first_line):
    """(line, normalised sentence) of every sentence with MIN_DUP_WORDS or more words; table rows excluded."""
    found = []
    for kind, n, body, _first in pl._blocks(text.split("\n")):
        if kind in ("heading", "cell"):
            continue
        for s in pl._SENTENCE_SPLIT.split(body):
            key = pl._norm(s)
            if len(key.split()) >= MIN_DUP_WORDS:
                found.append((first_line + n - 1, key))
    return found


def _pointer_files(plugin_root):
    for sub in ("agents", "skills", "bin"):
        base = os.path.join(plugin_root, sub)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
            for f in sorted(filenames):
                if f.endswith(".pyc") or (sub == "skills" and f == "changelog.md"):
                    continue
                yield os.path.join(dirpath, f)


def lint(plugin_root, squad_dir=None, cards="warn"):
    """-> (errors, warnings, has_rule_files). `warnings` are the card duplicates when cards == "warn"."""
    pdir = process_dir(plugin_root)
    if not os.path.isdir(pdir) or not [n for n in os.listdir(pdir) if n.endswith(".md")]:
        return [], [], False
    rules, tombs, errs = load_rules(pdir, plugin_root)
    warns = []

    first = {r.id: r for r in reversed(rules)}
    for r in rules:
        _writing(r.body, r.body_line, r.file, errs)
        for i, line in enumerate((r.body or "").split("\n")):
            for m in _CITE.finditer(line):
                rid = m.group(1)
                if rid.split("-")[0] in PREFIXES | {"SQ"} and rid not in first:
                    errs.append(f"{r.file}:{r.body_line + i}: unknown pointer [{rid}]")

    # cross-rule duplicates: a sentence of 12 or more words in two rules
    seen = {}
    for r in rules:
        for ln, key in _sentences(r.body, r.body_line):
            prev = seen.get(key)
            if prev is None:
                seen[key] = (r, ln)
            elif prev[0] is not r:
                errs.append(f"{r.file}:{ln}: sentence repeats {prev[0].id} ({prev[0].file}:{prev[1]})")

    # rule vs agents/*.md
    agents = os.path.join(plugin_root, "agents")
    if os.path.isdir(agents):
        for name in sorted(os.listdir(agents)):
            if not name.endswith(".md"):
                continue
            rel = f"agents/{name}"
            try:
                text = read_text(os.path.join(agents, name))
            except (OSError, UnicodeDecodeError):
                continue
            for ln, key in _sentences(text, 1):
                if key in seen:
                    msg = f"{rel}:{ln}: sentence repeats {seen[key][0].id} ({seen[key][0].file}:{seen[key][1]})"
                    (errs if cards == "error" else warns).append(msg)

    # overlay
    ops = []
    if squad_dir and os.path.isfile(os.path.join(squad_dir, OVERLAY_FILE)):
        try:
            ops = parse_overlay(read_text(os.path.join(squad_dir, OVERLAY_FILE)), OVERLAY_FILE, errs)
        except (OSError, UnicodeDecodeError) as e:
            errs.append(f"{OVERLAY_FILE}:1: cannot read: {e}")
    errs.extend(_lint_ops(ops, first))

    # pointers
    sq_added = {o.id for o in ops if o.kind == "add"}
    for path in _pointer_files(plugin_root):
        rel = os.path.relpath(path, plugin_root).replace(os.sep, "/")
        try:
            with open(path, encoding="utf-8", errors="replace", newline="") as f:
                lines = normalize(f.read()).split("\n")
        except OSError:
            continue
        for n, line in enumerate(lines, 1):
            for m in _CITE.finditer(line):
                rid = m.group(1)
                prefix = rid.split("-")[0]
                if prefix not in PREFIXES and prefix != "SQ":
                    continue
                if rid not in first and rid not in sq_added:
                    errs.append(f"{rel}:{n}: [{rid}] cites a rule that does not exist")
    return errs, warns, True


def _lint_ops(ops, rules_by_id):
    errs, seen = [], {}
    for o in ops:
        rel = OVERLAY_FILE
        if o.id in seen:
            errs.append(f"{rel}:{o.line}: second operation on {o.id} (first at line {seen[o.id]})")
        else:
            seen[o.id] = o.line
        if o.kind == "add":
            if not re.fullmatch(r"SQ-\d+[a-z]?", o.id):
                errs.append(f"{rel}:{o.line}: add needs an SQ-<n> ID, got {o.id}")
            if o.id in rules_by_id:
                errs.append(f"{rel}:{o.line}: add of {o.id}, which already exists")
            if o.hash:
                errs.append(f"{rel}:{o.line}: add takes no hash")
            if not o.title:
                errs.append(f"{rel}:{o.line}: add {o.id} has no title")
            if not o.body:
                errs.append(f"{rel}:{o.line}: add {o.id} has no body")
            _check_attrs(o.attrs, rel, o.line, errs, ("roles", "topic"), o.id)
        else:
            if o.id not in rules_by_id:
                errs.append(f"{rel}:{o.line}: {o.kind} of {o.id}, which does not exist")
            if not o.hash:
                errs.append(f"{rel}:{o.line}: {o.kind} {o.id} needs its hash (@<8 hex>)")
            if o.kind == "remove":
                extra = [k for k in o.attrs if k not in ("why", "upstream")]
                if extra:
                    errs.append(f"{rel}:{o.line}: remove takes only why: and upstream:, got {', '.join(extra)}")
            else:
                _check_attrs(o.attrs, rel, o.line, errs, (), o.id)
        if not (o.why or "").strip():
            errs.append(f"{rel}:{o.line}: {o.kind} {o.id} has no why:")
        if not (o.upstream or "").strip():
            errs.append(f"{rel}:{o.line}: {o.kind} {o.id} has no upstream:")
        elif o.upstream not in UPSTREAM:
            errs.append(f"{rel}:{o.line}: upstream must be {' | '.join(UPSTREAM)}, got {o.upstream!r}")
        if o.kind != "remove":
            _writing(o.body, o.body_line, rel, errs)
    return errs
