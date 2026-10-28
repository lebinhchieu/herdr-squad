"""`squad-team add|remove`: edit `team:` in scope.md, list who to respawn. stdlib only.

Reuses squadcompose (read_home, load_rules, choose, duties_line) and squadrules (parse_team, resolve_duties).
Every refusal is a ComposeError (exit 2) raised before scope.md is touched; the write is atomic.
"""
import argparse
import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import squadcompose as sc  # noqa: E402
import squadrules as sr  # noqa: E402

MIN_VERSION = (0, 6, 0)  # the first engine that reads `team:`
PO_ROLES = ("designer", "architect")  # an add waits for the PO's yes (--po-ok)
_TEAM_LINE = re.compile(r"^(team:[ \t]*)(.*?)([ \t]*\([^)]*\))?[ \t]*$")


def _version(text):
    """'0.6.1' or '0.6.0-rc1' -> (0, 6, 1); None when it does not start with numbers."""
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", text or "")
    return tuple(int(x) for x in m.groups()) if m else None


def _token(role):
    """Role name or team token -> team token. Implicit and unknown roles are refused."""
    if role in sr.IMPLICIT_ROLES:
        raise sc.ComposeError(f"squad-team: {role!r} is always on the team; nothing to add or remove")
    token = sr.ROLE_KEY.get(role, role)
    if token not in sr.TEAM_KEYS:
        raise sc.ComposeError(f"squad-team: unknown role {role!r} (one of {', '.join(sr.TEAM_KEYS)})")
    return token


def _edit(raw, tokens, scope_md):
    """scope.md text with the first `team:` line set to tokens (commentary, other lines and line endings kept)."""
    lines = raw.split("\n")
    for i, line in enumerate(lines):
        cr = "\r" if line.endswith("\r") else ""
        m = _TEAM_LINE.match(line[:-1] if cr else line)
        if m:
            value = ", ".join(tokens) if tokens else "none"
            lines[i] = f"{m.group(1)}{value}{m.group(3) or ''}{cr}"
            return "\n".join(lines)
    raise sc.ComposeError(f"{scope_md}: no `team:` line")


def _sig(rules, role, info):
    facts = info["facts"]
    sig = [(e.id, sc.heading(e, role, facts), e.body) for e in sc.choose(rules, role, facts)]
    if role in sc.HEADER_TEAM_ROLES:
        sig.append(("duties", sc.duties_line(info), ""))
    return sig


def _present(role, team):
    return role in sr.IMPLICIT_ROLES or sr.ROLE_KEY.get(role, role) in team


def plan(mode, role, home, squad_dir, plugin_root, po_ok=False, at_boundary=False):
    """-> (new scope.md bytes, report lines). Raises ComposeError; touches nothing."""
    token = _token(role)
    if mode == "add" and token in PO_ROLES and not po_ok:
        raise sc.ComposeError(f"squad-team: adding {role} waits for the PO's yes; ask the PO, then add --po-ok")
    if mode == "remove" and not at_boundary:
        raise sc.ComposeError("squad-team: remove only at an iteration boundary with the PO's OK; "
                              "then add --at-boundary")
    if not os.path.isdir(home):
        raise sc.ComposeError(f"squad-team: --home {home!r} is not a directory")
    if os.path.isfile(os.path.join(home, "goal.md")):
        raise sc.ComposeError(f"squad-team: {home} is a goal home; a goal has no team, change a scope's team")
    scope_md = os.path.join(home, "scope.md")
    if not os.path.isfile(scope_md):
        raise sc.ComposeError(f"squad-team: {scope_md} not found")
    before = sc.read_home(home)
    if before["pin"] is not None:
        v = _version(before["pin"][0])
        if v is None or v < MIN_VERSION:
            raise sc.ComposeError(f"squad-team: {home} is pinned to plugin {before['pin'][0]}, which reads `size:`; "
                                  "change its team by hand under that version's rules (this tool needs 0.6.0 or later)")
        if plugin_root is None and before["pin"][0] != sc.running_version():
            raise sc.ComposeError(f"squad-team: pin is plugin {before['pin'][0]} but the running plugin is "
                                  f"{sc.running_version()}; pass --plugin-root <that version's plugin folder>")
    if before["team_source"] == "old":
        raise sc.ComposeError(f"{scope_md}: old `size:` format; replace the old lines by one `team:` line by hand first")
    if before["team"] is None:
        raise sc.ComposeError(f"{scope_md}: the team is undecided; the Manager writes the first `team:` after the PO's "
                              "reply, then use squad-team")
    team = list(before["team"])
    if mode == "add" and token in team:
        raise sc.ComposeError(f"squad-team: {role} is already on the team ({', '.join(team) or 'none'})")
    if mode == "remove" and token not in team:
        raise sc.ComposeError(f"squad-team: {role} is not on the team ({', '.join(team) or 'none'})")
    new_team = [t for t in sr.TEAM_KEYS if (t in team) != (t == token)]
    with open(scope_md, "rb") as f:
        data = f.read()
    bom = b"\xef\xbb\xbf" if data.startswith(b"\xef\xbb\xbf") else b""
    new_text = _edit(data[len(bom):].decode("utf-8"), new_team, scope_md)
    # After-state: the same scope.md text in a scratch folder of the same name (read_home takes the scope label from it).
    root = plugin_root or sc.DEFAULT_ROOT
    overlay = os.path.join(squad_dir, sr.OVERLAY_FILE) if squad_dir else None
    scratch = tempfile.mkdtemp(prefix="squad-team-")
    try:
        tmp_home = os.path.join(scratch, os.path.basename(os.path.normpath(home)))
        os.mkdir(tmp_home)
        with open(os.path.join(tmp_home, "scope.md"), "wb") as f:
            f.write(new_text.encode("utf-8"))
        after = sc.read_home(tmp_home)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    rules, _n = sc.load_rules(root, overlay)
    out = []
    owners_b, owners_a = sr.resolve_duties(frozenset(team)), sr.resolve_duties(frozenset(new_team))
    roles_b = [r for r in sr.ROLES if _present(r, team)]
    roles_a = [r for r in sr.ROLES if _present(r, new_team)]
    respawn = [r for r in roles_a if r in roles_b and _sig(rules, r, before) != _sig(rules, r, after)]
    out.append(f"team: {', '.join(new_team) or 'none'}")
    for d in sr.DUTIES:
        if owners_b[d] != owners_a[d]:
            out.append(f"duty {d}: {owners_b[d]} -> {owners_a[d]}")
    for r in roles_a:
        if r not in roles_b:
            out.append(f"spawn: {r}")
    for r in roles_b:
        if r not in roles_a:
            out.append(f"retire: {r}")
    out.append("respawn: " + (", ".join(respawn) or "none"))
    return bom + new_text.encode("utf-8"), out


def _atomic_write(path, data):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", prefix=os.path.basename(path) + ".")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def run(argv):
    p = argparse.ArgumentParser(prog="squad-team", description="Add a role to or remove one from a scope's team.")
    p.add_argument("mode", choices=("add", "remove"))
    p.add_argument("role")
    p.add_argument("--home", default=os.environ.get("SCOPE_DIR"), help="scope folder (default $SCOPE_DIR)")
    p.add_argument("--squad-dir", default=os.environ.get("SQUAD_DIR"), help="squad folder, for process.local.md")
    p.add_argument("--plugin-root", default=None)
    p.add_argument("--po-ok", action="store_true", help="the PO said yes to adding a designer or architect")
    p.add_argument("--at-boundary", action="store_true", help="iteration boundary and the PO's OK, to remove a role")
    p.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    try:
        a = p.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        if not a.home:
            raise sc.ComposeError("squad-team: no --home and $SCOPE_DIR is not set")
        data, lines = plan(a.mode, a.role, a.home, a.squad_dir, a.plugin_root, a.po_ok, a.at_boundary)
        if not a.dry_run:
            _atomic_write(os.path.join(a.home, "scope.md"), data)
    except sc.ComposeError as e:
        for line in e.lines:
            print(line, file=sys.stderr)
        return 2
    except OSError as e:
        print(f"squad-team: scope.md not changed: {e}", file=sys.stderr)
        return 2
    if a.dry_run:
        print("dry run: scope.md not changed")
    for line in lines:
        print(line)
    return 0
