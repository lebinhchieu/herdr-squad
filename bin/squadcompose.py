"""Overlay and composer: facts, effective rules, composed rules file (ticket 04). stdlib only.

Contract: shared/contracts/rules-and-compose.md and spec.md (Composed rules). Every failure is a ComposeError
whose `lines` the CLI prints; compose builds the whole text before anything is written.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import squadrules as sr  # noqa: E402

_slurp = sr.read_text  # utf-8-sig, CRLF to LF

DEFAULT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
INDEX_ROLES = ("manager", "tech-lead")
_PIN = re.compile(r"^(\S+)\s+(\S+)\s*$")
_FACT_VALUES = {"design": ("yes", "no"), "architecture": ("yes", "no"), "qa": ("full", "light"), "qa-b": ("yes", "no")}
_FACT_DEFAULT = {"design": "no", "architecture": "no", "qa": "full", "qa-b": "yes"}


class ComposeError(Exception):
    def __init__(self, *lines):
        super().__init__("\n".join(lines))
        self.lines = list(lines)


class Eff:
    """One effective rule: plugin rule or added rule, overlay applied."""

    def __init__(self, id, title, roles, aware, when, topic, body, tag=""):
        self.id, self.title, self.roles, self.aware, self.when, self.topic, self.body, self.tag = (
            id, title, roles, aware, when, topic, body, tag)


def running_version(root=DEFAULT_ROOT):
    try:
        with open(os.path.join(root, ".claude-plugin", "plugin.json"), encoding="utf-8-sig") as f:
            return json.load(f).get("version", "unknown")
    except (OSError, ValueError):
        return "unknown"


def _kv(path):
    """`key: value` lines of a home file -> {key: (value, line number)}; first occurrence wins."""
    out = {}
    if not os.path.isfile(path):
        return out
    for n, line in enumerate(_slurp(path).split("\n"), 1):
        m = re.match(r"^([a-z][a-z-]*):[ \t]*(.*)$", line.rstrip())
        if m and m.group(1) not in out:
            out[m.group(1)] = (m.group(2).strip(), n)
    return out


_OLD_LINES = ("size", "design", "architecture", "qa-b")  # the old scope.md format (gone with the scaffold, task 10)
HEADER_TEAM_ROLES = ("manager", "team-lead", "tech-lead")  # D5: these headers print `team:` and `duties:`


def _qa_fact(kv):
    """`qa:` -> full | light. A first token `none` (`qa: none (PO ...)`: no QA roles, a hand-edited line) falls back to
    the default and the line stays untouched; any other value is an error naming the line."""
    value, n = kv.get("qa", (_FACT_DEFAULT["qa"], 0))
    tok = (value.split() or [_FACT_DEFAULT["qa"]])[0].lower()
    if tok == "none":
        return _FACT_DEFAULT["qa"]
    if tok not in _FACT_VALUES["qa"]:
        raise ComposeError(f"scope.md:{n}: qa must be {' | '.join(_FACT_VALUES['qa'])}, got {value!r}")
    return tok


def _size_facts(kv, facts):
    """The old size path, as it was before the team language (kept until task 10)."""
    if "size" in kv:
        m = re.search(r"\b[SML]\b", kv["size"][0])
        if m:
            facts["size"] = m.group(0)
    for key in ("design", "architecture", "qa-b"):
        value, n = kv.get(key, (_FACT_DEFAULT[key], 0))
        tok = (value.split() or [_FACT_DEFAULT[key]])[0].lower()
        if tok not in _FACT_VALUES[key]:
            raise ComposeError(f"scope.md:{n}: {key} must be {' | '.join(_FACT_VALUES[key])}, got {value!r}")
        facts[key] = tok
    if facts["qa-b"] == "no" and facts["design"] == "yes":
        raise ComposeError(f"scope.md: qa-b: no cannot be combined with design: yes (a design is checked on the "
                           "built UI by QA blackbox); set qa-b: yes or design: no")


def read_home(home, legacy_scaffold=False):
    """-> dict: facts (only the facts the home has), team (token list, [] for `none`, None when undecided or goal),
    team_source ("team" | "undecided" | "goal" | "size"), scope label, pin (version, sha) or None.

    A `team:` line decides the team and every presence and duty fact (never a missing one). A home without one but
    with any old line (`size:`, `design:`, `architecture:`, `qa-b:`) takes the old size path (source "size"); with
    `legacy_scaffold=True` (branch-internal, tests of the rule files only, deleted in task 10) its duty facts are
    filled from `squadrules.legacy_team`. A home with none of them is hand-made: undecided."""
    scope_md, goal_md = os.path.join(home, "scope.md"), os.path.join(home, "goal.md")
    is_goal_home = os.path.isfile(goal_md)
    kv = _kv(scope_md)
    gkv = _kv(goal_md) if is_goal_home else {}
    facts, team = {}, None
    if is_goal_home:
        facts["goal"] = "yes"
    else:
        value = kv.get("goal", ("", 0))[0].split()
        facts["goal"] = "yes" if value and value[0].lower() not in ("no", "none", "-", "n/a") else "no"
    facts["qa"] = _qa_fact(kv)
    if is_goal_home:  # a goal home takes the scope defaults; only the team facts are missing
        source = "goal"
        _size_facts({}, facts)
    elif "team" in kv:
        source = "team"
        try:
            team = sr.parse_team(kv["team"][0], f"scope.md:{kv['team'][1]}")
        except ValueError as ex:
            raise ComposeError(str(ex))
        if team is None:
            source = "undecided"
        else:
            facts.update(sr.team_facts(team))
            facts["qa-b"] = facts["qa-black"]  # old rule files still key on it until the cutover
    elif any(k in kv for k in _OLD_LINES):
        source = "size"
        _size_facts(kv, facts)
        if legacy_scaffold:
            try:
                team = sr.legacy_team(kv.get("size", ("", 0))[0], kv.get("qa-b", ("yes", 0))[0],
                                      kv.get("design", ("no", 0))[0], kv.get("architecture", ("no", 0))[0])
            except ValueError as ex:
                raise ComposeError(f"scope.md: {ex}")
            if team is not None:
                facts.update(sr.team_facts(team))
    else:
        source = "undecided"
    pin_line = (gkv if is_goal_home else kv).get("plugin") or kv.get("plugin") or gkv.get("plugin")
    pin = None
    if pin_line:
        m = _PIN.match(pin_line[0])
        if not m:
            raise ComposeError(f"plugin: line {pin_line[1]}: expected `plugin: <version> <sha>`, got {pin_line[0]!r}")
        pin = (m.group(1), m.group(2))
    name = os.path.basename(os.path.normpath(home))
    return {"facts": facts, "team": team, "team_source": source,
            "scope": f"goal {name}" if is_goal_home else name, "pin": pin}


def effective_rules(plugin_root, overlay_path):
    """-> (effective rules in compose order, number of overlay operations). Raises ComposeError (nothing written)."""
    pdir = sr.process_dir(plugin_root)
    if not os.path.isdir(pdir) or not [n for n in os.listdir(pdir) if n.endswith(".md")]:
        raise ComposeError(f"no rule files in {pdir}")
    rules, _tombs, problems = sr.load_rules(pdir, plugin_root)
    ops = []
    if overlay_path and os.path.isfile(overlay_path):
        ops = sr.parse_overlay(_slurp(overlay_path), sr.OVERLAY_FILE, problems)
    if problems:
        raise ComposeError(*problems)
    base = {r.id: r for r in rules}
    missing, seen = [], set()
    for o in ops:
        if o.id in seen:
            missing.append(f"{o.id}: second operation on the same ID in {sr.OVERLAY_FILE}:{o.line}")
        seen.add(o.id)
        if o.kind == "add" and o.id in base:
            missing.append(f"{o.id}: add of an ID the plugin already has ({sr.OVERLAY_FILE}:{o.line})")
        elif o.kind != "add" and o.id not in base:
            missing.append(f"{o.id}: {o.kind} of an ID the plugin does not have ({sr.OVERLAY_FILE}:{o.line})")
    if missing:
        raise ComposeError(*missing)
    stale = [f"{o.id}: overlay written for @{o.hash}, plugin now @{base[o.id].hash}"
             for o in ops if o.kind != "add" and o.hash != base[o.id].hash]
    if stale:
        raise ComposeError(*stale)

    eff = {r.id: Eff(r.id, r.title, list(r.roles), list(r.aware), r.when, r.topic, r.body) for r in rules}
    adds = []
    for o in ops:
        a = o.attrs
        if o.kind == "remove":
            del eff[o.id]
        elif o.kind == "replace":
            e = eff[o.id]
            if "roles" in a:
                e.roles = sr._roles(a["roles"])
            if "aware" in a:
                e.aware = sr._roles(a["aware"])
            if "when" in a:
                e.when = a["when"]
            if "topic" in a:
                e.topic = a["topic"]
            if o.title:
                e.title = o.title
            e.body, e.tag = o.body, "[squad: replaced]"
        else:
            adds.append(Eff(o.id, o.title, sr._roles(a.get("roles", "")), sr._roles(a.get("aware", "")),
                            a.get("when", ""), a.get("topic", ""), o.body, "[squad: added]"))
    out = [eff[r.id] for r in rules if r.id in eff] + adds
    for e in out:
        try:
            sr.matches(e.when, {})
        except ValueError as ex:
            raise ComposeError(f"{e.id}: {ex}")
    return out, len(ops)


def role_in(e, role):
    """'acts', 'aware' or '' for a role on an effective rule (the when: is checked by the caller)."""
    if "all" in e.roles or role in e.roles:
        return "acts"
    if "all" in e.aware or role in e.aware:
        return "aware"
    return ""


def heading(e, role=None, facts=None):
    tags = []
    if role is not None:
        if role_in(e, role) == "aware":
            tags.append("[aware]")
        if sr.missing_fact_keys(e.when, facts):
            tags.append(f"[if {e.when}]")
    if e.tag:
        tags.append(e.tag)
    return " ".join([f"## {e.id} {e.title}"] + tags)


def _fact(facts, key):
    return facts.get(key, "n/a")


def load_rules(plugin_root, overlay_path):
    """-> (effective rules, number of overlay operations). Once per run; `choose` is then pure (D4)."""
    return effective_rules(plugin_root, overlay_path)


def choose(rules, role, facts):
    """The rules a role gets for these facts, in compose order. Pure."""
    return [e for e in rules if role_in(e, role) and sr.matches(e.when, facts)]


def duties_line(info):
    """`duties:` header line: the owner of each duty for the home's team (`undecided` when there is none)."""
    if info["team"] is None:
        return "duties: undecided"
    owners = sr.resolve_duties(info["team"])
    return "duties: " + ", ".join(f"{d}={owners[d]}" for d in sr.DUTIES)


def _team_text(info):
    if info["team_source"] != "team" or info["team"] is None:
        return "undecided"
    return ", ".join(info["team"]) or "none"


def compose(role, home, plugin_root, overlay_path, agent, now, pinned=None, legacy_scaffold=False):
    """The composed rules text for one role. `pinned` is (version, sha) or None (unpinned: running version).
    `legacy_scaffold` is branch-internal (read_home); nothing in bin/ sets it."""
    info = read_home(home, legacy_scaffold)
    facts = info["facts"]
    rules, n_ops = load_rules(plugin_root, overlay_path)
    chosen = choose(rules, role, facts)
    if pinned:
        plugin_line = f"plugin: {pinned[0]} {pinned[1]}"
    else:
        plugin_line = f"plugin: {running_version()} unpinned"
    arch = "architecture yes, " if facts.get("architecture") == "yes" else ""  # shown only when on: header and 5 KiB budget unchanged otherwise
    team_head = ""
    if info["team_source"] != "size":  # the old header keeps `size X` for a size home (scaffold, until task 10)
        team_head = f" · team: {_team_text(info)}" if role in HEADER_TEAM_ROLES else ""
        head = (f"agent: {agent or role} · role: {role} · scope: {info['scope']}{team_head} (design {_fact(facts, 'design')}, "
                f"{arch}qa {_fact(facts, 'qa')}, goal {_fact(facts, 'goal')})")
    else:
        head = (f"agent: {agent or role} · role: {role} · scope: {info['scope']} (size {_fact(facts, 'size')}, "
                f"design {_fact(facts, 'design')}, {arch}qa {_fact(facts, 'qa')}, goal {_fact(facts, 'goal')})")
    out = [
        "# Your process rules",
        head,
        f"{plugin_line} · overlay: {n_ops} operations applied · composed: {now}",
    ]
    if role in HEADER_TEAM_ROLES and info["team_source"] != "size":
        out.append(duties_line(info))
    out.append("rules: " + " ".join(e.id for e in chosen))
    for e in chosen:
        out += ["", heading(e, role, facts), e.body]
    if role in INDEX_ROLES:
        got = {e.id for e in chosen}
        out += ["", "## Index of other rules"]
        on = facts.get("architecture") == "yes"  # architecture rules and the architect name stay out of a scope without it
        out += [f"- {e.id} {e.title} ({', '.join(r for r in e.roles if on or r != 'architect')})"
                for e in rules if e.id not in got and (on or "architecture" not in (e.when or ""))]
    return "\n".join(out) + "\n"


def find_rule(plugin_root, overlay_path, rule_id):
    for e in effective_rules(plugin_root, overlay_path)[0]:
        if e.id == rule_id:
            return e
    raise ComposeError(f"{rule_id}: no such rule")


def rule_text(e):
    return "\n".join([heading(e), e.body]) + "\n"


_NEW_WHO_KEYS = frozenset(sr.DUTIES) | {"ba", "team-lead", "tech-lead", "qa-white", "qa-black"}


def _acts_aware(e, facts):
    ok = sr.matches(e.when, facts)
    return (", ".join(e.roles) if ok and e.roles else "-"), (", ".join(e.aware) if ok and e.aware else "-")


def who_lines(e):
    lines = []
    for size in sr.WHEN_KEYS["size"]:
        acts, aware = _acts_aware(e, {"size": size})
        lines.append(f"{size}: acts: {acts}; aware: {aware}")
    if re.search(r"\bqa-b\b", e.when or ""):  # a rule the QA-blackbox switch changes: show both settings
        for size in ("M", "L"):
            for qab in sr.WHEN_KEYS["qa-b"]:
                acts, aware = _acts_aware(e, {"size": size, "qa-b": qab})
                lines.append(f"{size} qa-b {qab}: acts: {acts}; aware: {aware}")
    keys = []  # one line per value of each duty or presence key the rule's `when:` names (the team language)
    for key, _values in (sr._conditions(e.when) if e.when and e.when.strip() else ()):
        if key in _NEW_WHO_KEYS and key not in keys:
            keys.append(key)
    for key in keys:
        for value in sr.WHEN_KEYS[key]:
            acts, aware = _acts_aware(e, {key: value})
            lines.append(f"{key} = {value}: acts: {acts}; aware: {aware}")
    return lines
