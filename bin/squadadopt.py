"""squad-process adopt / scaffold (ticket 09): a squad with its own process.md and full settings becomes composed.

  squad-process scaffold --squad-dir D [--code-path P ...] [--plugin-root R] [--new-pin "<version> <sha>"]
      new squad: process.local.md (header only), plugin.pin, settings/<role>.local.json, project.md (if absent).
  squad-process adopt --squad-dir D [--dry-run] [--resolve L<n>=choice ...] [--yes] [--plugin-root R] [--new-pin ...]
      v6 squad: process.md -> overlay + plugin.pin, settings/<role>.json -> <role>.local.json, open scopes and goals
      pinned, old files archived. Writes nothing without --yes and an answer for every PO item (exit 3).

Choices for a PO item (never guessed): drop (the plugin rule stays) | add:<roles> (the new text becomes a squad rule
SQ-n for those roles, comma separated) | replace:<ID>:<file> (the text in <file> replaces that rule's body).
Exit: 0 done / nothing to do, 1 missing input, 2 refused, 3 PO action needed (a dry run with open items, or no --yes).
"""
import argparse
import datetime
import difflib
import json
import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import squadio  # noqa: E402
import squadprocess as sp  # noqa: E402
import squadrules as sr  # noqa: E402
import squadruntime as rt  # noqa: E402
import squadsettings as ss  # noqa: E402
import squadupgrade as su  # noqa: E402

DEFAULT_ROOT = su.DEFAULT_ROOT
ID_RE = re.compile(r"^[A-Z]+-\d+[a-z]?$")
HEADER = "# Local process\n"  # only a title may stand before the first operation
ROLE_FILES = ("manager", "ba", "team-lead", "tech-lead", "qa-whitebox", "qa-blackbox", "dev", "designer", "token-coach")
RETIRED = ("Bash(squad-process show:*)",)  # commands that no longer exist: not carried into the local file
_CODE_ENTRY = re.compile(r"^Read\(//+(.+)/\*\*\)$")


class AdoptError(Exception):
    def __init__(self, code, *lines):
        super().__init__("\n".join(lines))
        self.code, self.lines = code, lines


def _atomic(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=os.path.basename(path) + ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _slurp(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def new_pin(plugin_root, given=None):
    try:
        if given:
            return rt.parse_pin_line(given, "--new-pin")
        version, sha, _dirty = rt.running_pin(plugin_root)
        return version, sha
    except rt.RuntimeError_ as e:
        raise AdoptError(e.code, *e.lines)


def _template_roles(plugin_root):
    d = os.path.join(plugin_root, "templates", "squad", "settings")
    if not os.path.isdir(d):
        raise AdoptError(1, f"no settings templates at {d}")
    return sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json"))


# ---- scaffold ------------------------------------------------------------------------------------------

def scaffold(squad_dir, plugin_root, pin, code_paths=()):
    """Create what a composed squad needs and does not have yet; returns (created paths, notes). Never overwrites."""
    created, notes = [], []
    os.makedirs(squad_dir, exist_ok=True)

    def put(rel, text):
        path = os.path.join(squad_dir, rel)
        if not os.path.exists(path):
            _atomic(path, text)
            created.append(rel)

    put(sr.OVERLAY_FILE, HEADER)
    put("plugin.pin", f"{pin[0]} {pin[1]}\n")
    for role in _template_roles(plugin_root):
        local = {"codePaths": list(code_paths)} if role == "qa-blackbox" and code_paths else {}
        put(f"settings/{role}.local.json", json.dumps(local, indent=2) + "\n")
        if role == "qa-blackbox" and not code_paths and any("settings/qa-blackbox.local" in c for c in created):
            notes.append("settings/qa-blackbox.local.json has no codePaths: set them before spawning QA blackbox "
                         "(spawn refuses without them)")
    tpl = os.path.join(plugin_root, "templates", "squad")
    for name in ("project.md", "process-log.md"):
        if os.path.isfile(os.path.join(tpl, name)):
            put(name, _slurp(os.path.join(tpl, name)))
    for d in ("scopes", "goals"):
        os.makedirs(os.path.join(squad_dir, d), exist_ok=True)
    return created, notes


# ---- the v6 map and the process.md diff ----------------------------------------------------------------

def load_map(plugin_root, n):
    path = os.path.join(plugin_root, "skills", "squad-process-update", "history", f"process-v{n}.map.md")
    if not os.path.isfile(path):
        raise AdoptError(2, f"cannot adopt a version {n} process.md: no line map at {path}",
                         "adopt knows version 6; bring the squad to 6 first (squad-process plan / apply --legacy)")
    out = {}
    for line in _slurp(path).split("\n"):
        m = re.match(r"^\| (\d+) \| (.+) \|$", line)
        if m:
            out[int(m.group(1))] = [t.strip() for t in m.group(2).split(",")]
    return out


def norm(s):
    return " ".join(s.split())


def _ids(targets):
    return [t for t in targets if ID_RE.match(t)]


class Item:
    """A change in the squad's process.md the tool will not decide: the PO answers it."""
    def __init__(self, key, old, new, candidates, reason):
        self.key, self.old, self.new, self.candidates, self.reason = key, old, new, candidates, reason
        self.choice = None


def _body_pattern(old_lines):
    toks = " ".join(old_lines).split()
    return re.compile(r"\s+".join(re.escape(t) for t in toks))


def _make_op(rule, old_lines, new_lines, line_ref):
    """The replace/remove op for one rule when the old text occurs once in its body, else None."""
    pat = _body_pattern(old_lines)
    found = pat.findall(rule.body)
    if len(found) != 1:
        return None
    new_text = "\n".join(new_lines).strip()
    body = pat.sub(lambda _m: new_text, rule.body, count=1)
    body = re.sub(r"\n{3,}", "\n\n", body).strip("\n")
    why = f"adopted from the squad's process.md (v6 line {line_ref})"
    if not body.strip():
        return sr.Op("remove", rule.id, rule.hash, "", {"why": why, "upstream": "proposed"}, "", 0)
    return sr.Op("replace", rule.id, rule.hash, "", {"why": why, "upstream": "proposed"}, body, 0)


def diff_process(old_text, new_text, mapping, rules):
    """-> (ops, items, upstream notes): each changed hunk is handled, answered upstream already, or left to the PO."""
    a, b = old_text.split("\n"), new_text.split("\n")
    ops, items, notes = [], [], []
    all_bodies = norm(" ".join(r.body for r in rules.values()))
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        old = [x for x in a[i1:i2] if x.strip()]
        new = [x for x in b[j1:j2] if x.strip()]
        if not old and not new:
            continue
        if old and old[0].startswith("process-version:"):
            continue
        key = f"L{i1 + 1}" if old else f"L{i1}+"
        span = range(i1 + 1, i2 + 1) if old else range(max(i1, 1), i1 + 2)
        targets = []
        for n in span:
            targets += _ids(mapping.get(n, []))
        cands = [i for i in dict.fromkeys(targets) if i in rules]
        cand_bodies = norm(" ".join(rules[i].body for i in cands))
        label = f"v6 line {i1 + 1}" if old else f"after v6 line {i1}"
        if new and all(norm(x) in all_bodies or norm(re.sub(r"^\s*[-*] ", "", x)) in all_bodies for x in new):
            notes.append(f"{label}: the new wording is already in the plugin's rules ({', '.join(cands) or 'any rule'})")
            continue
        if old and cands:
            hits = [rules[i] for i in cands if len(_body_pattern(old).findall(rules[i].body)) == 1]
            if len(hits) == 1:
                op = _make_op(hits[0], old, new, i1 + 1)
                if op is not None:
                    errs = sr._lint_ops([op], rules)
                    if not errs:
                        ops.append(op)
                        continue
                    items.append(Item(key, old, new, cands, "the exact edit does not lint: " + errs[0].split(": ", 1)[-1]))
                    continue
        reason = ("added text with no old text" if not old else
                  "no rule maps the old text" if not cands else "the old text is not found once in a mapped rule")
        items.append(Item(key, old, new, cands, reason))
    merged, seen = [], {}
    for o in ops:  # two edits to one rule: the second would overwrite the first; leave the pair to the PO
        if o.id in seen:
            first = seen[o.id]
            if first in merged:
                merged.remove(first)
            items.append(Item(f"R{o.id}", [], [], [o.id], f"two edits to {o.id} in the squad's process.md"))
        else:
            seen[o.id] = o
            merged.append(o)
    return merged, items, notes


def apply_choices(items, resolves, rules, ops):
    """Turn each answered item into an op; -> (ops, unanswered items). A bad choice raises AdoptError(2)."""
    known = {i.key: i for i in items}
    for k in resolves:
        if k not in known:
            raise AdoptError(2, f"--resolve {k}: no such item; open items: {', '.join(known) or 'none'}")
    out, open_items = list(ops), []
    taken = {o.id for o in out}
    sq = [int(m.group(1)) for o in out for m in [re.fullmatch(r"SQ-(\d+)", o.id)] if m]
    for it in items:
        choice = resolves.get(it.key)
        if choice is None:
            open_items.append(it)
            continue
        text = "\n".join(it.new).strip()
        why = f"adopted from the squad's process.md ({it.key}), PO choice {choice.split(':')[0]}"
        if choice == "drop":
            continue
        if choice.startswith("add:"):
            roles = [r.strip() for r in choice[4:].split(",") if r.strip()]
            if not roles or not text:
                raise AdoptError(2, f"--resolve {it.key}={choice}: add needs roles and new text")
            n = max(sq or [0]) + 1
            sq.append(n)
            title = re.sub(r"[`*|#]", "", text.split("\n")[0]).strip()[:48] or f"Squad rule {n}"
            attrs = {"roles": ", ".join(roles), "topic": "squad", "why": why, "upstream": "local-only"}
            out.append(sr.Op("add", f"SQ-{n}", "", title, attrs, text, 0))
        elif choice.startswith("replace:"):
            _, rid, path = (choice.split(":", 2) + ["", ""])[:3]
            if rid not in rules or not os.path.isfile(path):
                raise AdoptError(2, f"--resolve {it.key}={choice}: needs replace:<existing ID>:<readable file>")
            if rid in taken:
                raise AdoptError(2, f"--resolve {it.key}: {rid} already has an operation")
            taken.add(rid)
            out.append(sr.Op("replace", rid, rules[rid].hash, "", {"why": why, "upstream": "proposed"},
                             _slurp(path).strip("\n"), 0))
        else:
            raise AdoptError(2, f"--resolve {it.key}={choice}: choose drop | add:<roles> | replace:<ID>:<file>")
    errs = sr._lint_ops(out, rules)
    if errs:
        raise AdoptError(2, "the resulting overlay does not lint:", *errs)
    return out, open_items


# ---- settings ------------------------------------------------------------------------------------------

def settings_diff(template, old):
    """-> (local overlay dict, codePaths, regained entries, gained scalar keys): old = merge(template, local) + codePaths."""
    local, regained, gains = {}, [], []
    code = []
    has_placeholder = any(isinstance(e, str) and ss.PLACEHOLDER in e
                          for e in template.get("permissions", {}).get("deny", []))

    def walk(t, o, path, out):
        for k, v in o.items():
            here = path + (k,)
            if here in ss.UNION_KEYS and isinstance(v, list) and isinstance(t.get(k, []), list):
                extra = [e for e in v if e not in t.get(k, []) and e not in RETIRED]
                if here == ("permissions", "deny") and has_placeholder:
                    keep = []
                    for e in extra:
                        m = _CODE_ENTRY.match(e) if isinstance(e, str) else None
                        if m and not m.group(1).endswith("/.worktrees"):
                            code.append("/" + m.group(1).strip("/"))
                        elif m:
                            continue  # the project's .worktrees entry: regenerated from the placeholder
                        else:
                            keep.append(e)
                    extra = keep
                regained.extend(e for e in t.get(k, []) if e not in v and e not in RETIRED
                                and not (isinstance(e, str) and ss.PLACEHOLDER in e))
                if extra:
                    out[k] = extra
            elif isinstance(v, dict) and isinstance(t.get(k), dict):
                sub = {}
                walk(t[k], v, here, sub)
                if sub:
                    out[k] = sub
            elif t.get(k) != v:
                out[k] = v
        for k in t:
            if k not in o:
                tv = t[k]
                if path + (k,) in ss.UNION_KEYS and isinstance(tv, list):
                    regained.extend(e for e in tv if not (isinstance(e, str) and ss.PLACEHOLDER in e))
                elif not isinstance(tv, (dict, list)):
                    gains.append(".".join(path + (k,)) + f"={tv}")
                elif isinstance(tv, dict):
                    pass
    walk(template, old, (), local)
    # regained entries of nested unions that the old file lacked entirely (e.g. no permissions.allow at all)
    for key in ("allow", "deny", "ask"):
        if key not in old.get("permissions", {}) and key in template.get("permissions", {}):
            regained.extend(e for e in template["permissions"][key] if not (isinstance(e, str) and ss.PLACEHOLDER in e))
    if code:
        local["codePaths"] = list(dict.fromkeys(code))
    return local, regained, gains


def plan_settings(squad_dir, plugin_root):
    """-> list of dicts per role with a full settings file and no local file."""
    out = []
    sdir = os.path.join(squad_dir, "settings")
    if not os.path.isdir(sdir):
        return out
    for role in _template_roles(plugin_root):
        full, loc = os.path.join(sdir, f"{role}.json"), os.path.join(sdir, f"{role}.local.json")
        if not os.path.isfile(full) or os.path.isfile(loc):
            continue
        try:
            tpl = ss._load(os.path.join(plugin_root, "templates", "squad", "settings", f"{role}.json"), 1, "template")
            old = ss._load(full, 2, "settings file")
        except ss.SettingsError as e:
            raise AdoptError(e.code, str(e))
        local, regained, gains = settings_diff(tpl, old)
        out.append({"role": role, "local": local, "regained": regained, "gains": gains,
                    "template": tpl, "old": old})
    return out


def check_settings(planned):
    """The effective file must hold every entry the old file had (adopt never narrows a permission silently)."""
    problems = []
    for p in planned:
        eff = ss.merge(p["template"], {k: v for k, v in p["local"].items() if k != "codePaths"})
        code = {c.strip("/") for c in p["local"].get("codePaths", [])}
        for key in ("allow", "deny"):
            have = eff.get("permissions", {}).get(key, [])
            for e in p["old"].get("permissions", {}).get(key, []):
                m = _CODE_ENTRY.match(e) if isinstance(e, str) else None
                if e in have or e in RETIRED or (key == "deny" and m and (m.group(1).strip("/") in code
                                                          or m.group(1).endswith("/.worktrees"))):
                    continue
                problems.append(f"{p['role']}: {key} entry {e!r} would be lost")
    return problems


# ---- open scopes and goals -------------------------------------------------------------------------------

_PIN_LINE = re.compile(r"(?m)^plugin:[ \t]*\S")


def open_homes(squad_dir):
    out = []
    for kind, fname in (("scopes", "scope.md"), ("goals", "goal.md")):
        base = os.path.join(squad_dir, kind)
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            f = os.path.join(base, name, fname)
            if not name.startswith("_") and os.path.isfile(f):
                out.append((f"{kind}/{name}", f))
    return out


def unpinned_homes(squad_dir):
    return [(rel, f) for rel, f in open_homes(squad_dir) if not _PIN_LINE.search(_slurp(f))]


def pin_home_file(path, pin):
    text = _slurp(path)
    line = f"plugin: {pin[0]} {pin[1]}\n\n"
    i = text.find("\n## ")
    text = text[:i + 1] + line + text[i + 1:] if i >= 0 else text.rstrip("\n") + "\n\n" + line
    _atomic(path, text)


# ---- adopt -----------------------------------------------------------------------------------------------

class Plan:
    pass


def build_plan(squad_dir, plugin_root, pin, resolves):
    if not os.path.isdir(squad_dir):
        raise AdoptError(1, f"no squad folder at {squad_dir}")
    p = Plan()
    p.squad_dir, p.pin, p.plugin_root = squad_dir, pin, plugin_root
    p.process_md = os.path.join(squad_dir, "process.md")
    p.composed = rt.mode(squad_dir) == "composed"
    p.leftovers = p.composed and (os.path.isfile(p.process_md) or any(
        os.path.isfile(os.path.join(squad_dir, "settings", f"{r}.json")) for r in ROLE_FILES))
    p.unpinned = unpinned_homes(squad_dir) if p.composed or os.path.isfile(p.process_md) else []
    p.ops, p.items, p.notes, p.settings, p.version = [], [], [], [], None
    if p.composed:
        if p.leftovers:  # a crashed run: the rest is finished
            p.version = sp.squad_version(squad_dir)[0] if os.path.isfile(p.process_md) else None
        return p
    if not os.path.isfile(p.process_md):
        raise AdoptError(1, f"{squad_dir} has no process.md and no {sr.OVERLAY_FILE}: nothing to adopt "
                            "(a new squad starts with `squad-process scaffold`)")
    n, status = sp.squad_version(squad_dir)
    p.version = n
    hist = os.path.join(plugin_root, "skills", "squad-process-update", "history", f"process-v{n}.md")
    if not os.path.isfile(hist):
        raise AdoptError(1, f"no archived process version {n} at {hist}: cannot tell the squad's own edits")
    mapping = load_map(plugin_root, n)
    rules, _t = su.load_plugin(plugin_root)
    ops, items, p.notes = diff_process(_slurp(hist), _slurp(p.process_md), mapping, rules)
    p.rules = rules
    p.ops, p.items = apply_choices(items, resolves, rules, ops)
    p.open_items = [i for i in items if i.key not in resolves]
    p.settings = plan_settings(squad_dir, plugin_root)
    problems = check_settings(p.settings)
    if problems:
        raise AdoptError(2, "adopt would narrow the squad's permissions:", *problems)
    return p


def fmt_item(it):
    out = [f"  {it.key}  {it.reason}", f"     candidate rules: {', '.join(it.candidates) or 'none'}"]
    out += [f"     - old: {x.strip()}" for x in it.old] or ["     - old: (nothing)"]
    out += [f"     + new: {x.strip()}" for x in it.new] or ["     + new: (deleted)"]
    return "\n".join(out)


def format_plan(p, dry_run):
    out = [("adopt (dry run, nothing written)" if dry_run else "adopt") + f": {p.squad_dir}", ""]
    if p.composed and not p.leftovers:
        return "\n".join(out + ["already adopted: process.local.md exists and no old process.md or full settings remain; nothing to do."])
    if p.composed:
        out.append("an earlier run was cut short: finishing the pins and archives only.")
    if not p.composed:
        out.append(f"process.md (version {p.version}) -> overlay with {len(p.ops)} operation(s):")
        for o in p.ops:
            out.append(f"  {o.kind} {o.id} @{o.hash}  upstream: {o.upstream}")
        if not p.ops:
            out.append("  (none: the plugin's rules already cover the squad's wording)")
        if p.notes:
            out.append("")
            out.append("changes already in the plugin's rules (no operation needed):")
            out += [f"  {n}" for n in p.notes]
        out.append("")
        out.append(f"PO items ({len(p.open_items)} open of {len(p.items)}): the tool will not guess these")
        out += [fmt_item(i) for i in p.open_items] or ["  (none)"]
        if p.open_items:
            out.append("  answer each with --resolve <key>=drop | add:<roles> | replace:<ID>:<file>")
        out.append("")
        out.append(f"plugin.pin -> {p.pin[0]} {p.pin[1]}")
        for s in p.settings:
            loc = s["local"]
            n_allow = len(loc.get("permissions", {}).get("allow", []))
            n_deny = len(loc.get("permissions", {}).get("deny", []))
            out.append(f"settings/{s['role']}.json -> {s['role']}.local.json: +{n_allow} allow, +{n_deny} deny"
                       + (f", codePaths {loc['codePaths']}" if loc.get("codePaths") else ""))
        regained = [(s["role"], e) for s in p.settings for e in s["regained"]]
        out.append("")
        out.append("permissions regained from the template (the effective file will contain them):")
        out += [f"  {r}: {e}" for r, e in regained] or ["  (none)"]
        gains = [(s["role"], g) for s in p.settings for g in s["gains"]]
        if gains:
            out.append("keys the template sets that the old file lacked:")
            out += [f"  {r}: {g}" for r, g in gains]
    out.append("")
    out.append("open scopes and goals without a plugin: line that would be pinned to the new pin:")
    out += [f"  would pin {rel}" for rel, _f in p.unpinned] or ["  (none)"]
    if not p.composed:
        out.append("")
        out.append(f"archive: process.md -> process.v{p.version}-archived.md; "
                   "settings/<role>.json -> <role>.v%s-archived.json" % p.version)
    return "\n".join(out)


def execute(p, today):
    """The writes, in the order that keeps a half-done run valid: overlay first, archives last."""
    sd = p.squad_dir
    if not p.composed:
        _atomic(os.path.join(sd, sr.OVERLAY_FILE), su.emit_overlay(HEADER.rstrip("\n"), p.ops))
        for s in p.settings:
            _atomic(os.path.join(sd, "settings", f"{s['role']}.local.json"), json.dumps(s["local"], indent=2) + "\n")
        pin_path = os.path.join(sd, "plugin.pin")
        if not os.path.isfile(pin_path):
            _atomic(pin_path, f"{p.pin[0]} {p.pin[1]}\n")
        rows = [(f"adopt: process.md v{p.version} -> process.local.md ({len(p.ops)} operation(s)), plugin.pin "
                 f"{p.pin[0]} {p.pin[1]}, {len(p.settings)} settings file(s) -> .local.json",
                 "composed process (ticket 09); old files archived as *-archived.*")]
        su._write_log(sd, rows, today)
    pin = rt.read_pin_file(sd) or p.pin
    for rel, f in unpinned_homes(sd):
        pin_home_file(f, pin)
    n = p.version
    if os.path.isfile(os.path.join(sd, "process.md")) and n is not None:
        os.replace(os.path.join(sd, "process.md"), os.path.join(sd, f"process.v{n}-archived.md"))
    for role in ROLE_FILES:
        full = os.path.join(sd, "settings", f"{role}.json")
        if os.path.isfile(full) and os.path.isfile(os.path.join(sd, "settings", f"{role}.local.json")) and n is not None:
            os.replace(full, os.path.join(sd, "settings", f"{role}.v{n}-archived.json"))


def cmd_adopt(a):
    squad_dir = a.squad_dir
    resolves = {}
    for r in a.resolve:
        k, sep, v = r.partition("=")
        if not sep or not k:
            raise AdoptError(2, f"--resolve {r!r}: expected <key>=<choice>")
        resolves[k] = v
    pin = new_pin(a.plugin_root, a.new_pin)
    p = build_plan(squad_dir, a.plugin_root, pin, resolves)
    print(format_plan(p, a.dry_run))
    if p.composed and not p.leftovers and not p.unpinned:
        return 0
    open_items = getattr(p, "open_items", [])
    if a.dry_run:
        return 3 if open_items else 0
    if open_items:
        print(f"\nNOT APPLIED: {len(open_items)} PO item(s) unanswered; nothing was written.")
        return 3
    if not a.yes:
        print("\nNOT APPLIED: nothing was written; run again with --yes after the PO confirms.")
        return 3
    execute(p, a.today or str(datetime.date.today()))
    print("\nAPPLIED: process.local.md, plugin.pin and local settings written; old files archived.")
    return 0


def cmd_scaffold(a):
    pin = new_pin(a.plugin_root, a.new_pin)
    if rt.mode(a.squad_dir) == "legacy":
        raise AdoptError(2, f"{a.squad_dir} has a process.md: run `squad-process adopt` instead")
    created, notes = scaffold(a.squad_dir, a.plugin_root, pin, a.code_path)
    for c in created:
        print(f"created {c}")
    if not created:
        print("nothing to create: the squad already has every file")
    for n in notes:
        print(f"note: {n}")
    return 0


def main(argv=None):
    squadio.utf8_stdio()
    ap = argparse.ArgumentParser(prog="squad-process")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("adopt", "scaffold"):
        p = sub.add_parser(name)
        p.add_argument("--squad-dir", default=os.environ.get("SQUAD_DIR"))
        p.add_argument("--plugin-root", default=str(DEFAULT_ROOT))
        p.add_argument("--new-pin", help="test hook: `<version> <sha>` instead of the running plugin's")
        if name == "adopt":
            p.add_argument("--dry-run", action="store_true")
            p.add_argument("--resolve", action="append", default=[], metavar="KEY=CHOICE")
            p.add_argument("--yes", action="store_true")
            p.add_argument("--today", help=argparse.SUPPRESS)
        else:
            p.add_argument("--code-path", action="append", default=[])
    a = ap.parse_args(argv)
    if not a.squad_dir:
        print("squad-process: no --squad-dir and $SQUAD_DIR is not set", file=sys.stderr)
        return 2
    try:
        return cmd_adopt(a) if a.cmd == "adopt" else cmd_scaffold(a)
    except AdoptError as e:
        for line in e.lines:
            print(f"squad-process: {line}", file=sys.stderr)
        return e.code
    except (su.UpgradeError, sp.ProcessError) as e:
        print(f"squad-process: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
