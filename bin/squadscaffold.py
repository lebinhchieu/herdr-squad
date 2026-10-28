"""squad-process scaffold: a new composed squad.

  squad-process scaffold --squad-dir D [--plugin-root R] [--new-pin "<version> <sha>"]
      process.local.md (header only), plugin.pin, settings/<role>.local.json, project.md (if absent).
Exit: 0 done / nothing to create, 1 missing input, 2 refused.
"""
import argparse
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import squadio  # noqa: E402
import squadrules as sr  # noqa: E402
import squadruntime as rt  # noqa: E402
import squadupgrade as su  # noqa: E402

DEFAULT_ROOT = su.DEFAULT_ROOT
HEADER = "# Local process\n"  # only a title may stand before the first operation


class ScaffoldError(Exception):
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
        raise ScaffoldError(e.code, *e.lines)


def _template_roles(plugin_root):
    d = os.path.join(plugin_root, "templates", "squad", "settings")
    if not os.path.isdir(d):
        raise ScaffoldError(1, f"no settings templates at {d}")
    return sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json"))


# ---- scaffold ------------------------------------------------------------------------------------------

def scaffold(squad_dir, plugin_root, pin):
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
        put(f"settings/{role}.local.json", "{}\n")
    tpl = os.path.join(plugin_root, "templates", "squad")
    for name in ("project.md", "process-log.md"):
        if os.path.isfile(os.path.join(tpl, name)):
            put(name, _slurp(os.path.join(tpl, name)))
    for d in ("scopes", "goals"):
        os.makedirs(os.path.join(squad_dir, d), exist_ok=True)
    return created, notes


def cmd_scaffold(a):
    pin = new_pin(a.plugin_root, a.new_pin)
    if rt.mode(a.squad_dir) == "legacy":
        raise ScaffoldError(2, f"{a.squad_dir} has a process.md (a legacy squad): scaffold only makes a new composed squad")
    created, notes = scaffold(a.squad_dir, a.plugin_root, pin)
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
    p = sub.add_parser("scaffold")
    p.add_argument("--squad-dir", default=os.environ.get("SQUAD_DIR"))
    p.add_argument("--plugin-root", default=str(DEFAULT_ROOT))
    p.add_argument("--new-pin", help="test hook: `<version> <sha>` instead of the running plugin's")
    a = ap.parse_args(argv)
    if not a.squad_dir:
        print("squad-process: no --squad-dir and $SQUAD_DIR is not set", file=sys.stderr)
        return 2
    try:
        return cmd_scaffold(a)
    except ScaffoldError as e:
        for line in e.lines:
            print(f"squad-process: {line}", file=sys.stderr)
        return e.code
    except su.UpgradeError as e:
        print(f"squad-process: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
