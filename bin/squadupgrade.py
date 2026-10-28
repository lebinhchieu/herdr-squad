"""Upgrade a composed squad one rule at a time (ticket 07). stdlib only.

  squad-process upgrade --check [--squad-dir D] [--plugin-root NEW] [--old-root OLD] [--new-pin "<ver> <sha>"]
  squad-process upgrade --apply [--resolve ID=choice ...] [--yes] [--today DATE] (same options)
  squad-process upstream [--squad-dir D]

The plugin's change per rule ID is read from the rule files of the squad's pinned (old) plugin and of the new
one; each overlay operation is then handled by the table in .scratch/composed-process/issues/07:

  op is current ........ nothing         op body = new plugin text .. dropped (adopted upstream)
  only targeting moved .. op re-hashed   body changed ............... flagged "stale": keep | take | file:<path>
  rule removed .......... flagged "removed": drop | retarget:<ID> | local

Exit: 0 nothing to decide (or applied), 2 a refusal, 3 something needs a decision. Nothing is written unless
every flagged item has a --resolve and --yes is given.
"""
import argparse
import datetime
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import squadio  # noqa: E402
import squadcompose as sc  # noqa: E402
import squadprocess as sp  # noqa: E402
import squadrules as sr  # noqa: E402
import squadruntime as rt  # noqa: E402

DEFAULT_ROOT = sc.DEFAULT_ROOT
_slurp = sr.read_text
STALE_CHOICES = "keep | take | file:<path>"
REMOVED_CHOICES = "drop | retarget:<ID> | local"


class UpgradeError(Exception):
    def __init__(self, *lines, code=2):
        super().__init__("\n".join(lines))
        self.lines, self.code = list(lines), code


class Item:
    """One overlay operation and what the upgrade does with it.

    kind: current | retarget | adopted | auto-drop | stale | removed | unhandled | add
    """

    def __init__(self, kind, op, new=None, old=None, tomb=None, why=""):
        self.kind, self.op, self.new, self.old, self.tomb, self.why = kind, op, new, old, tomb, why

    @property
    def flagged(self):
        return self.kind in ("stale", "removed")


# Old `when:` conditions and what to write now (AC 21). The size ones are the nearest team-language reading, a hint:
# the PO decides, the upgrade never rewrites a `when:` by itself.
_OLD_COND = re.compile(r"(size|qa-b|qa-whitebox) (=|in) (\S+(?:, ?\S+)*)")
_TRANSLATE = {("size", "S"): "qa-white = no", ("size", "M"): "qa-white = yes", ("size", "L"): "ba = yes",
              ("qa-b", "yes"): "qa-black = yes", ("qa-b", "no"): "qa-black = no",
              ("qa-whitebox", "yes"): "qa-white = yes", ("qa-whitebox", "no"): "qa-white = no"}


def old_when_conditions(when):
    """-> [(old condition text, suggested translation or '')] for each `size`, `qa-b`, `qa-whitebox` condition."""
    out = []
    for part in (when or "").split(" and "):
        m = _OLD_COND.fullmatch(part.strip())
        if not m:
            continue
        key, _op, vals = m.groups()
        vals = [v.strip() for v in vals.split(",")]
        new = [_TRANSLATE.get((key, v)) for v in vals]
        if None in new:
            text = ""
        elif len(set(new)) == 1:
            text = new[0]
        else:
            k = {n.split(" = ")[0] for n in new}
            text = (f"{k.pop()} in {', '.join(n.split(' = ')[1] for n in new)}" if len(k) == 1
                    else "no single key (write one rule per case)")
        out.append((part.strip(), text))
    return out


def _other_l_role(op):
    """True when the op's `roles:` names an L role other than the BA (a rule about the Team Lead or Tech Lead): the
    L-only `ba = yes` is then not the only reading, `team-lead = yes` and `tech-lead = yes` are listed too (AC 21)."""
    roles = {r.strip() for r in (op.attrs.get("roles") or "").split(",")}
    return bool(roles & {"team-lead", "tech-lead"})


class Plan:
    def __init__(self):
        self.items, self.review, self.counts, self.old_known = [], [], {}, False
        self.old_when = []  # [(op, [(old condition, translation)])]

    @property
    def flagged(self):
        return [i for i in self.items if i.flagged]

    @property
    def unhandled(self):
        return [i for i in self.items if i.kind == "unhandled"]


# ---- reading ---------------------------------------------------------------------------------------

def load_plugin(root):
    """-> (rules by id in file order, tombstones by id). Raises UpgradeError on a rule file problem."""
    pdir = sr.process_dir(root)
    if not os.path.isdir(pdir):
        raise UpgradeError(f"no rule files in {pdir}")
    rules, tombs, problems = sr.load_rules(pdir, root)
    if problems:
        raise UpgradeError(*problems)
    return {r.id: r for r in rules}, {t.id: t for t in tombs}


def read_overlay(squad_dir):
    """-> (preamble text, [Op]); the file must lint clean as an overlay."""
    path = os.path.join(squad_dir, sr.OVERLAY_FILE)
    text = _slurp(path)
    problems = []
    ops = sr.parse_overlay(text, sr.OVERLAY_FILE, problems)
    if problems:
        raise UpgradeError(*problems)
    pre = []
    for line in text.split("\n"):
        if line.startswith("## "):
            break
        pre.append(line)
    return "\n".join(pre).rstrip(), ops


def read_pin(squad_dir):
    """The squad's plugin.pin -> (version, sha) or None."""
    path = os.path.join(squad_dir, "plugin.pin")
    if not os.path.isfile(path):
        return None
    parts = _slurp(path).split()
    if len(parts) != 2:
        raise UpgradeError(f"plugin.pin: expected `<version> <sha>`, got {' '.join(parts)!r}")
    return parts[0], parts[1]


def parse_pin(text, where):
    parts = (text or "").split()
    if len(parts) == 2 and parts[0].lower() == "plugin:":
        parts = parts[1:]
    if len(parts) != 2:
        raise UpgradeError(f"{where}: expected `<version> <sha>`, got {text!r}")
    return parts[0], parts[1]


def _new_pin(a):
    if a.new_pin:
        return parse_pin(a.new_pin, "--new-pin")
    try:
        version, sha, _dirty = rt.running_pin(a.plugin_root)
    except rt.RuntimeError_ as e:
        raise UpgradeError(*e.lines)
    return version, sha


def find_old_root(a, squad_dir, pin):
    """--old-root, else the squad's pinned runtime folder when it exists, else None."""
    if a.old_root:
        return a.old_root
    if not pin:
        raise UpgradeError("no plugin.pin in the squad folder: the old rule files cannot be found; "
                           "pass --old-root <old plugin folder>", code=1)
    path = rt.runtime_path(squad_dir, pin[0], pin[1])
    if not os.path.isdir(sr.process_dir(path)):
        raise UpgradeError(f"the pinned runtime is missing: {path} (build it with "
                           f"`squad-process runtime --squad-dir {squad_dir} --home <home>`, or pass --old-root)", code=1)
    return path


def _same(a, b):
    return sr.rule_hash("", a or "") == sr.rule_hash("", b or "")


# ---- classification --------------------------------------------------------------------------------

def plugin_counts(old, new):
    """Per-rule plugin change: added, changed (body), removed, retargeted (only roles/aware/when/topic)."""
    c = {"added": [], "changed": [], "removed": [], "retargeted": []}
    for rid, r in new.items():
        o = old.get(rid)
        if o is None:
            c["added"].append(rid)
        elif o.hash != r.hash:
            c["retargeted" if _same(o.body, r.body) else "changed"].append(rid)
    c["removed"] = [rid for rid in old if rid not in new]
    return c


def classify(old, new, tombs, ops):
    """-> Plan. `old` is {id: Rule} or None (old plugin not available)."""
    plan = Plan()
    plan.old_known = old is not None
    if old is not None:
        plan.counts = plugin_counts(old, new)
    for o in ops:
        conds = old_when_conditions(o.attrs.get("when"))
        if conds:
            plan.old_when.append((o, conds))
        if o.kind == "add":
            if not re.fullmatch(r"SQ-\d+[a-z]?", o.id):
                plan.items.append(Item("unhandled", o, why=f"add needs an SQ-<n> ID, got {o.id}"))
            elif o.upstream == "proposed" and any(_same(r.body, o.body) for r in new.values()):
                plan.items.append(Item("adopted", o, why="the plugin now ships this text"))
            else:
                plan.items.append(Item("add", o))
            continue
        r = new.get(o.id)
        was = (old or {}).get(o.id)
        if r is not None:
            if o.hash == r.hash:
                plan.items.append(Item("current", o, new=r, old=was))
            elif o.kind == "replace" and o.upstream == "proposed" and _same(o.body, r.body):
                plan.items.append(Item("adopted", o, new=r, old=was, why="the plugin now ships this text"))
            elif was is not None and was.hash == o.hash and _same(was.body, r.body):
                plan.items.append(Item("retarget", o, new=r, old=was, why="only roles/aware/when/topic moved"))
            else:
                plan.items.append(Item("stale", o, new=r, old=was, why="the plugin changed this rule"))
        elif o.id in tombs:
            if o.kind == "remove":
                plan.items.append(Item("auto-drop", o, tomb=tombs[o.id], old=was, why="the plugin removed it too"))
            else:
                plan.items.append(Item("removed", o, tomb=tombs[o.id], old=was, why="the plugin removed this rule"))
        else:
            plan.items.append(Item("unhandled", o, why=f"{o.kind} of {o.id}: the plugin has neither the rule nor "
                                                       "a tombstone for it"))
    kept = [i.op for i in plan.items if i.kind == "add"]
    for o in kept:
        topic = o.attrs.get("topic", "")
        for rid, r in new.items():
            if r.topic != topic:
                continue
            was = (old or {}).get(rid)
            if old is not None and was is None:
                plan.review.append(f"{o.id} (topic {topic}): the plugin added {rid} {r.title}")
            elif old is not None and was.hash != r.hash and not _same(was.body, r.body):
                plan.review.append(f"{o.id} (topic {topic}): the plugin changed {rid} {r.title}")
    return plan


# ---- output ----------------------------------------------------------------------------------------

def _changelog_why(root, version):
    """{ID: why} of the plugin changelog's block for `version` (rule-ID format from v7), or {}."""
    path = os.path.join(root, "skills", "squad-process-update", "changelog.md")
    out = {}
    if not os.path.isfile(path):
        return out
    cur = None
    for line in _slurp(path).split("\n"):
        m = re.match(r"^## v(\d+)\b", line)
        if m:
            cur = int(m.group(1))
            continue
        m = re.match(rf"^- ({sr._ID}): (.+)$", line)
        if m and cur is not None and cur >= 7 and str(cur) == str(version):
            out[m.group(1)] = m.group(2)
    return out


def format_check(plan, old_pin, new_pin, why_of=None):
    why_of = why_of or {}
    n = lambda k: sum(1 for i in plan.items if i.kind == k)  # noqa: E731
    lines = [f"upgrade: plugin {' '.join(old_pin) if old_pin else '(no pin)'} -> {' '.join(new_pin)}"]
    if plan.old_known:
        c = plan.counts
        lines.append("plugin changes: " + ", ".join(f"{k} {len(c[k])}" for k in ("added", "changed", "removed", "retargeted")))
    else:
        lines.append("plugin changes: unknown (the old plugin's rule files are not available; "
                     "every changed rule counts as changed; pass --old-root)")
    lines.append(f"overlay: {len(plan.items)} operations: {n('current') + n('add')} unaffected, "
                 f"{n('retarget')} re-targeted, {n('adopted') + n('auto-drop')} dropped, "
                 f"{len(plan.flagged)} need a decision")
    for i in plan.unhandled:
        lines.append(f"unhandled: {i.op.id}: {i.why}")
    if plan.flagged:
        lines.append("decide:")
    for i in plan.flagged:
        o = i.op
        extra = f" ({why_of[o.id]})" if o.id in why_of else ""
        if i.kind == "stale":
            lines.append(f"  {o.id} stale: the plugin changed the rule your `{o.kind}` was written for "
                         f"(@{o.hash} -> @{i.new.hash}){extra}")
            lines.append(f"    --resolve {o.id}=<{STALE_CHOICES}>")
        else:
            rb = ", ".join(i.tomb.replaced_by) or "none"
            lines.append(f"  {o.id} removed: the plugin removed the rule your `{o.kind}` was written for "
                         f"(replaced_by: {rb}; why: {i.tomb.why}){extra}")
            lines.append(f"    --resolve {o.id}=<{REMOVED_CHOICES}>")
    if plan.old_when:
        lines.append("old `when:` language (the engine rejects it; edit these operations by hand, nothing was written):")
        for o, conds in plan.old_when:
            for old, new in conds:
                lines.append(f"  {o.id} (line {o.line}): {old} -> {new or 'no direct translation: pick a duty or role key'}")
                if new == "ba = yes" and _other_l_role(o):
                    lines += [f"  {o.id} (line {o.line}): alternative: team-lead = yes",
                              f"  {o.id} (line {o.line}): alternative: tech-lead = yes"]
    if plan.review:
        lines.append("review (not blocking):")
        lines += [f"  {r}" for r in plan.review]
    if not plan.flagged and not plan.old_when:
        lines.append("nothing needs a decision.")
    return "\n".join(lines) + "\n"


# ---- resolving and rewriting -----------------------------------------------------------------------

def parse_resolves(args, plan):
    out = {}
    flagged = {i.op.id: i for i in plan.flagged}
    for arg in args:
        rid, sep, choice = arg.partition("=")
        if not sep or not choice:
            raise UpgradeError(f"--resolve {arg!r}: expected <ID>=<choice>")
        if rid not in flagged:
            raise UpgradeError(f"--resolve {arg!r}: {rid} is not a flagged item "
                               f"(flagged: {', '.join(flagged) or 'none'})")
        if rid in out:
            raise UpgradeError(f"--resolve: {rid} given twice")
        item = flagged[rid]
        ok = ("keep", "take") if item.kind == "stale" else ("drop", "local")
        if not (choice in ok or choice.startswith("file:") and item.kind == "stale"
                or choice.startswith("retarget:") and item.kind == "removed"):
            raise UpgradeError(f"--resolve {arg!r}: choose {STALE_CHOICES if item.kind == 'stale' else REMOVED_CHOICES}")
        out[rid] = choice
    return out


def _read_file_choice(path):
    """A `file:<path>` answer: optional roles/aware/when/topic lines, then the body -> (attrs, body)."""
    try:
        text = _slurp(path)
    except (OSError, UnicodeDecodeError) as e:
        raise UpgradeError(f"file:{path}: cannot read: {e}")
    lines, attrs = text.split("\n"), {}
    while lines:
        m = re.match(r"^([a-z]+):[ \t]*(.*)$", lines[0].rstrip())
        if not m or m.group(1) not in sr.PLUGIN_ATTRS:
            break
        attrs[m.group(1)] = m.group(2).strip()
        lines.pop(0)
    body = "\n".join(ln.rstrip(" \t") for ln in lines).strip("\n")
    if not body:
        raise UpgradeError(f"file:{path}: no body")
    return attrs, body


def _next_sq(ops):
    nums = [int(re.match(r"SQ-(\d+)", o.id).group(1)) for o in ops if o.id.startswith("SQ-")]
    return max(nums, default=0) + 1


def rewrite(plan, resolves, new_rules, old_rules):
    """-> (new ops list, log rows [(change, why)]). Raises UpgradeError before anything is written."""
    out, rows, ops_all = [], [], [i.op for i in plan.items]
    for i in plan.items:
        o = i.op
        if i.kind in ("current", "add"):
            out.append(o)
        elif i.kind == "retarget":
            o.hash = i.new.hash
            out.append(o)
            rows.append((f"overlay {o.kind} {o.id}: re-hashed to @{o.hash}", "the plugin moved only the targeting"))
        elif i.kind == "adopted":
            rows.append((f"overlay {o.kind} {o.id} dropped", "the plugin now ships the same text"))
        elif i.kind == "auto-drop":
            rows.append((f"overlay remove {o.id} dropped", "the plugin removed the rule too"))
        elif i.kind == "stale":
            choice = resolves[o.id]
            if choice == "take":
                rows.append((f"overlay {o.kind} {o.id} dropped: plugin text taken", "the PO chose take"))
                continue
            if choice == "keep":
                o.hash = i.new.hash
                rows.append((f"overlay {o.kind} {o.id}: local text kept, re-hashed to @{o.hash}", "the PO chose keep"))
            else:
                if o.kind != "replace":
                    raise UpgradeError(f"{o.id}: file:<path> needs a `replace` operation, this is `{o.kind}`")
                attrs, body = _read_file_choice(choice[5:])
                kept = {k: v for k, v in o.attrs.items() if k not in sr.PLUGIN_ATTRS}
                o.attrs = {**{k: attrs[k] for k in sr.PLUGIN_ATTRS if k in attrs}, **kept}
                o.body, o.hash = body, i.new.hash
                rows.append((f"overlay replace {o.id}: text from {choice[5:]}, re-hashed to @{o.hash}", "the PO chose a file"))
            out.append(o)
        elif i.kind == "removed":
            choice = resolves[o.id]
            if choice == "drop" or (choice == "local" and o.kind == "remove"):
                rows.append((f"overlay {o.kind} {o.id} dropped: the plugin removed the rule", f"the PO chose {choice}"))
            elif choice.startswith("retarget:"):
                target = choice[9:]
                if target not in new_rules:
                    raise UpgradeError(f"--resolve {o.id}={choice}: the new plugin has no rule {target}")
                o.id, o.hash = target, new_rules[target].hash
                out.append(o)
                rows.append((f"overlay {o.kind} moved to {target}, re-hashed to @{o.hash}", "the PO chose retarget"))
            else:  # local: a replace becomes `add SQ-n`
                was = i.old
                title = o.title or (was.title if was else "")
                attrs = {}
                for k in sr.PLUGIN_ATTRS:
                    v = o.attrs.get(k) or (getattr(was, k, None) and
                                           (", ".join(getattr(was, k)) if isinstance(getattr(was, k), list)
                                            else getattr(was, k)))
                    if v:
                        attrs[k] = v
                if not title or "roles" not in attrs or "topic" not in attrs:
                    raise UpgradeError(f"--resolve {o.id}=local: the old rule's title, roles and topic are needed "
                                       "(pass --old-root, or give them on the operation)")
                n = _next_sq(ops_all + out)
                kept = {k: v for k, v in o.attrs.items() if k not in sr.PLUGIN_ATTRS}
                new_op = sr.Op("add", f"SQ-{n}", "", title, {**attrs, **kept}, o.body, o.line, o.body_line)
                out.append(new_op)
                rows.append((f"overlay replace {o.id} became add SQ-{n}", "the PO chose local"))
    return out, rows


def emit_overlay(preamble, ops):
    blocks = []
    for o in ops:
        head = f"## {o.kind} {o.id}" + (f" @{o.hash}" if o.hash else "") + (f" {o.title}" if o.title else "")
        lines = [head] + [f"{k}: {v}" for k, v in o.attrs.items()]
        if o.body:
            lines.append(o.body)
        blocks.append("\n".join(lines))
    parts = ([preamble] if preamble else []) + blocks
    return "\n\n".join(parts) + "\n"


def _check_result(new_root, ops):
    """Lint the result as an overlay against the new rules; ComposeError-free means compose will work."""
    rules, _t = load_plugin(new_root)
    errs = sr._lint_ops(ops, rules)
    if errs:
        raise UpgradeError("the rewritten overlay does not lint:", *errs)


def _backup(squad_dir, today):
    sq = os.path.realpath(squad_dir)
    folder = os.path.join(os.path.dirname(os.path.dirname(sq)), "squad-backups")
    os.makedirs(folder, exist_ok=True)
    base, n = os.path.join(folder, f"{os.path.basename(sq)}-process.local-{today}"), 1
    path = base + ".md"
    while os.path.exists(path):
        n += 1
        path = f"{base}-{n}.md"
    shutil.copy2(os.path.join(squad_dir, sr.OVERLAY_FILE), path)
    return path


def _write_log(squad_dir, rows, today):
    log = os.path.join(squad_dir, "process-log.md")
    old = open(log, encoding="utf-8", newline="").read().replace("\r\n", "\n") if os.path.isfile(log) else ""
    table = [f"| {today} | {c} | {w} |" for c, w in rows]
    sp._atomic_write(Path(log), sp._insert_log(old, table))
    return table


# ---- commands --------------------------------------------------------------------------------------

def prepare(a):
    if not a.squad_dir:
        raise UpgradeError("squad-process: no --squad-dir and $SQUAD_DIR is not set")
    squad_dir = a.squad_dir
    if rt.mode(squad_dir) != "composed":
        raise UpgradeError(f"not composed: {squad_dir} has no {sr.OVERLAY_FILE}; "
                           "a v6 squad moves with `squad-process plan` / `apply`")
    old_pin, new_pin = read_pin(squad_dir), _new_pin(a)
    new_rules, tombs = load_plugin(a.plugin_root)
    old_root = find_old_root(a, squad_dir, old_pin)
    old_rules = load_plugin(old_root)[0] if old_root else None
    pre, ops = read_overlay(squad_dir)
    plan = classify(old_rules, new_rules, tombs, ops)
    return squad_dir, old_pin, new_pin, new_rules, old_rules, pre, ops, plan


def cmd_check(a):
    _sd, old_pin, new_pin, _nr, _or, _pre, _ops, plan = prepare(a)
    if plan.unhandled:
        sys.stdout.write(format_check(plan, old_pin, new_pin))
        return 2
    sys.stdout.write(format_check(plan, old_pin, new_pin, _changelog_why(a.plugin_root, new_pin[0])))
    return 3 if plan.flagged or plan.old_when else 0


def cmd_apply(a):
    squad_dir, old_pin, new_pin, new_rules, old_rules, pre, ops, plan = prepare(a)
    if plan.unhandled:
        sys.stdout.write(format_check(plan, old_pin, new_pin))
        return 2
    if plan.old_when:
        sys.stdout.write(format_check(plan, old_pin, new_pin))
        print(f"NOT APPLIED: {len(plan.old_when)} operation(s) use the old `when:` language; nothing was written.")
        return 3
    resolves = parse_resolves(a.resolve, plan)
    missing = [i for i in plan.flagged if i.op.id not in resolves]
    if missing:
        sys.stdout.write(format_check(plan, old_pin, new_pin, _changelog_why(a.plugin_root, new_pin[0])))
        print(f"NOT APPLIED: {len(missing)} flagged item(s) have no --resolve; nothing was written.")
        return 3
    new_ops, rows = rewrite(plan, resolves, new_rules, old_rules)
    _check_result(a.plugin_root, new_ops)
    text = emit_overlay(pre, new_ops)
    if old_pin == new_pin and not rows:
        print(f"already on plugin {' '.join(new_pin)}; nothing to do.")
        return 0
    if not a.yes:
        print(format_check(plan, old_pin, new_pin).rstrip("\n"))
        print(f"\noverlay after: {len(new_ops)} operations; pin moves to {' '.join(new_pin)}")
        print("NOT APPLIED (add --yes after the PO confirms).")
        return 3
    today = a.today or str(datetime.date.today())
    backup = _backup(squad_dir, today)
    sp._atomic_write(Path(squad_dir) / sr.OVERLAY_FILE, text)
    rows = [(f"Upgraded plugin {' '.join(old_pin) if old_pin else '(no pin)'} -> {' '.join(new_pin)}; running "
             "scopes keep their scope.md pin", "squad-process upgrade --apply")] + rows
    table = _write_log(squad_dir, rows, today)
    sp._atomic_write(Path(squad_dir) / "plugin.pin", f"{new_pin[0]} {new_pin[1]}\n")  # last: a crash re-runs safely
    print(f"backup: {backup}")
    print("log rows:\n" + "\n".join(table))
    print(f"applied: overlay {len(new_ops)} operations; plugin.pin = {new_pin[0]} {new_pin[1]}")
    return 0


def cmd_upstream(a):
    if not a.squad_dir:
        raise UpgradeError("squad-process: no --squad-dir and $SQUAD_DIR is not set")
    if rt.mode(a.squad_dir) != "composed":
        raise UpgradeError(f"not composed: {a.squad_dir} has no {sr.OVERLAY_FILE}")
    _pre, ops = read_overlay(a.squad_dir)
    chosen = [o for o in ops if o.upstream == "proposed"]
    print(f"upstream: {len(chosen)} proposed operation(s)")
    for o in chosen:
        print(f"\n### {o.kind} {o.id}" + (f" @{o.hash}" if o.hash else "") + (f" {o.title}" if o.title else ""))
        print(f"Why: {o.why}")
        for k in sr.PLUGIN_ATTRS:
            if k in o.attrs:
                print(f"{k}: {o.attrs[k]}")
        if o.body:
            print("\n```\n" + o.body + "\n```")
    return 0


def main(argv=None):
    squadio.utf8_stdio()
    ap = argparse.ArgumentParser(prog="squad-process")
    sub = ap.add_subparsers(dest="cmd", required=True)
    up = sub.add_parser("upgrade")
    mode_ = up.add_mutually_exclusive_group(required=True)
    mode_.add_argument("--check", action="store_true")
    mode_.add_argument("--apply", action="store_true")
    up.add_argument("--resolve", action="append", default=[], metavar="ID=CHOICE")
    up.add_argument("--yes", action="store_true")
    up.add_argument("--today")
    up.add_argument("--plugin-root", default=DEFAULT_ROOT)
    up.add_argument("--old-root")
    up.add_argument("--new-pin")
    us = sub.add_parser("upstream")
    for p in (up, us):
        p.add_argument("--squad-dir", default=os.environ.get("SQUAD_DIR"))
    a = ap.parse_args(argv)
    try:
        if a.cmd == "upstream":
            return cmd_upstream(a)
        return cmd_check(a) if a.check else cmd_apply(a)
    except (UpgradeError, sc.ComposeError) as e:
        for line in e.lines:
            print(line, file=sys.stderr)
        return getattr(e, "code", 2)


if __name__ == "__main__":
    sys.exit(main())
