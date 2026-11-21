"""squad-process homes: list the open homes with their pins and move chosen ones to the squad's `plugin.pin`. stdlib only.

  squad-process homes --check | --apply [--yes] [--only NAME ...] [--squad-dir D] [--home H] [--plugin-root R]

`H` (default $SCOPE_DIR, else $GOAL_DIR) is offered, plus the open scopes of `H` when it is a goal home. The target
is the squad's `plugin.pin`. A home moves only when it composes for every role at the target runtime (the engine and
rules a spawn at the new pin will use). Exit 0 nothing to move, 3 a move is offered (`--check`) or needs `--yes`,
2 refused. Only the first `plugin:` line of a home's own file changes; one row per home goes to process-log.md.
"""
import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import squadio  # noqa: E402
import squadcompose as sc  # noqa: E402
import squadrules as sr  # noqa: E402
import squadruntime as rt  # noqa: E402
import squadupgrade as su  # noqa: E402

_PLUGIN_LINE = re.compile(r"^(plugin:[ \t]*)(\S+[ \t]+\S+)([ \t]*)$")
_TEAM_ROLE = {token: role for role, token in sr.ROLE_KEY.items()}  # qa-white -> qa-whitebox


class Refused(Exception):
    def __init__(self, *lines):
        super().__init__("\n".join(lines))
        self.lines = list(lines)


class Home:
    def __init__(self, kind, name, path):
        self.kind, self.name, self.path = kind, name, path
        self.pin, self.state, self.note, self.info = None, "", "", None

    @property
    def label(self):
        return f"{self.kind} {self.name}"

    @property
    def pin_file(self):
        return os.path.join(self.path, "goal.md" if self.kind == "goal" else "scope.md")


def _first_line(lines):
    return (lines[0] if lines else "").strip()


def _read(home):
    """Fill pin, state (no-pin | old-format | refused | at-target | moves) and note from the home's own files."""
    try:
        home.info = sc.read_home(home.path)
        if home.info["team_source"] == "old":
            raise sc.old_format_error(home.path)
        pin = home.info["pin"]
        home.pin = rt.validate_pin(*pin, where=f"{home.pin_file}: plugin pin") if pin else None
    except sc.ComposeError as e:
        old = sc.old_format_error(home.path)
        home.state = "old-format" if old and e.lines[:1] == old.lines[:1] else "refused"
        home.note = _first_line(e.lines)
    except rt.RuntimeError_ as e:
        home.state, home.note = "refused", _first_line(e.lines)
    else:
        home.state = "no-pin" if home.pin is None else None


def _goal_of(path):
    value = sc._kv(os.path.join(path, "scope.md")).get("goal", ("", 0))[0].split()
    return value[0] if value else None


def offered(squad, home_dir):
    """The home itself, plus the open scopes of a goal home."""
    home_dir = os.path.realpath(home_dir)
    homes = rt.iter_homes(squad)
    own = next((Home(k, n, p) for k, n, p in homes if os.path.realpath(p) == home_dir), None)
    if own is None:
        raise Refused(f"{home_dir} is not an open scope or goal home of {squad}")
    out = [own]
    if own.kind == "goal":
        out += [Home(k, n, p) for k, n, p in homes if k == "scope" and _goal_of(p) == own.name]
    return out, homes


def roles_of(home):
    """Every role a spawn in the home composes: manager (a goal home or a lone scope), team-lead, dev, team tokens."""
    roles = []
    if home.kind == "goal" or home.info["facts"].get("goal") == "no":
        roles.append("manager")
    roles += ["team-lead", "dev"]
    roles += [_TEAM_ROLE.get(t, t) for t in home.info["team"] or []]
    return roles


def compose_at(root, squad, home_path, role):
    """Run `compose <role>` of the runtime at `root` (stdout discarded, nothing written) -> first error line or ''."""
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    r = subprocess.run([sys.executable, os.path.join(root, "bin", "squad-process"), "compose", role, "--home", home_path,
                        "--squad-dir", squad, "--plugin-root", root], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env)
    if r.returncode == 0:
        return ""
    return _first_line((r.stderr or r.stdout).splitlines()) or f"compose {role} exited {r.returncode}"


def gate(home, root, squad):
    for role in roles_of(home):
        err = compose_at(root, squad, home.path, role)
        if err:
            home.state, home.note = "refused", f"{role}: {err}"
            return


def fmt_pin(pin):
    return f"{pin[0]} {pin[1]}" if pin else "-"


def table(homes, target):
    lines = [f"{'home':<28} {'pin now':<22} {'target':<22} state"]
    for h in homes:
        lines.append(f"{h.label:<28} {fmt_pin(h.pin):<22} {fmt_pin(target):<22} {h.state}")
        if h.note:
            lines.append(f"  {h.note}")
    return lines


def stranded(squad, all_homes, shown, plugin_root):
    """Warnings for open homes that are not offered and will refuse spawn and respawn (composed at their own pin)."""
    skip = {os.path.realpath(h.path) for h in shown}
    out = []
    for kind, name, path in all_homes:
        if os.path.realpath(path) in skip:
            continue
        other = Home(kind, name, path)
        _read(other)
        if other.state is not None or other.pin is None:
            continue
        root = rt.runtime_path(squad, *other.pin)
        if not os.path.isdir(root):
            out.append(f"not checked: {other.label}: runtime {root} is not built")
            continue
        err = compose_at(root, squad, path, "manager")
        if err:
            out.append(f"will refuse spawn and respawn: {other.label}: {err}")
    return out


def _edit_pin(home, new):
    """Text of the home's file with the first `plugin:` line's value replaced (line ends and the rest kept)."""
    with open(home.pin_file, encoding="utf-8", newline="") as f:
        text = f.read()
    parts = text.split("\n")
    for i, line in enumerate(parts):
        cr = "\r" if line.endswith("\r") else ""
        m = _PLUGIN_LINE.match(line[:-1] if cr else line)
        if m:
            parts[i] = f"{m.group(1)}{new[0]} {new[1]}{m.group(3)}{cr}"
            return "\n".join(parts)
        if re.match(r"^plugin:", line):
            break
    raise Refused(f"{home.pin_file}: cannot find the `plugin: <version> <sha>` line")


def run(a):
    squad = os.path.realpath(a.squad_dir) if a.squad_dir else None
    if not squad or not os.path.isdir(squad):
        raise Refused("homes: no squad dir: pass --squad-dir or run inside a squad session")
    home_dir = a.home or os.environ.get("SCOPE_DIR") or os.environ.get("GOAL_DIR")
    if not home_dir:
        raise Refused("no home: run inside a scope or goal session or pass --home")
    target = rt.read_pin_file(squad)
    if target is None:
        raise Refused(f"{os.path.join(squad, 'plugin.pin')}: missing; no target pin (run upgrade --apply --yes first)")
    shown, all_homes = offered(squad, home_dir)
    for h in shown:
        _read(h)
        if h.state is None:
            h.state = "at-target" if h.pin == target else "moves"
    names = {h.name for h in shown}
    only = set(a.only or [])
    if only - names:
        raise Refused(*(f"--only {n}: not an offered home (offered: {', '.join(sorted(names))})"
                        for n in sorted(only - names)))
    try:
        root = rt.materialise(squad, *target, plugin_root=a.plugin_root)
    except rt.RuntimeError_ as e:
        raise Refused(*e.lines)
    movers = [h for h in shown if h.state == "moves"]
    for h in movers:
        gate(h, root, squad)
    print("\n".join(table(shown, target)))
    if a.check:
        for line in stranded(squad, all_homes, shown, a.plugin_root):
            print(line)
        if any(h.state == "refused" for h in shown):
            return 2
        return 3 if movers else 0
    chosen = [h for h in movers if not only or h.name in only]
    if not chosen:
        print("nothing to move")
        return 0
    bad = [h for h in chosen if h.state == "refused"]
    if bad:
        raise Refused(*(f"refused {h.label}: {h.note} (deselect it with --only)" for h in bad))
    if not a.yes:
        print("NOT APPLIED (add --yes after Chieu confirms)")
        return 3
    new = {h.path: _edit_pin(h, target) for h in chosen}  # every edit succeeds before the first write
    for h in chosen:
        su._atomic_write(Path(h.pin_file), new[h.path])
    today = a.today or datetime.date.today().isoformat()
    rows = [f"| {today} | Home {h.label} plugin {fmt_pin(h.pin)} -> {fmt_pin(target)} | squad-process homes --apply |"
            for h in chosen]
    log = Path(squad) / "process-log.md"
    old = log.read_text(encoding="utf-8", newline="").replace("\r\n", "\n") if log.is_file() else ""
    su._atomic_write(log, su._insert_log(old, rows))
    for h in chosen:
        print(f"moved {h.label}: {fmt_pin(h.pin)} -> {fmt_pin(target)}")
    return 0


def main(argv=None):
    squadio.utf8_stdio()
    ap = argparse.ArgumentParser(prog="squad-process homes")
    ap.add_argument("homes")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--only", nargs="+", metavar="NAME")
    ap.add_argument("--squad-dir", default=os.environ.get("SQUAD_DIR"))
    ap.add_argument("--home")
    ap.add_argument("--plugin-root", default=sc.DEFAULT_ROOT)
    ap.add_argument("--today")
    a = ap.parse_args(argv)
    try:
        return run(a)
    except Refused as e:
        print("\n".join(e.lines), file=sys.stderr)
        return 2
    except (rt.RuntimeError_, sc.ComposeError) as e:
        print("\n".join(e.lines), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
