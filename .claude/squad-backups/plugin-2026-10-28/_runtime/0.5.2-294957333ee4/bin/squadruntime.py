"""Squad mode, plugin pin and pinned runtime (ticket 05). stdlib only.

  squad-process mode --squad-dir D                       prints composed | legacy | none
  squad-process runtime --squad-dir D --home H [--dry-run]
                                                         prints the pinned runtime folder (materialises it)
  squad-process prune --squad-dir D (--home H | --all) [--dry-run] [--protect PATH ...]
                                                         deletes the runtimes no open scope, goal or plugin.pin holds

Exit codes of `runtime`: 0 ok, 1 runtime missing and not buildable, 2 no pin or an unparseable pin.
`prune` exits 0 even when a delete fails (a close never stops on it); 2 only for a bad call.
Design: .scratch/composed-process/spike-runtime.md and runtime-compose design.md section 05.
"""
import argparse
import glob
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import squadio  # noqa: E402
import squadcompose as sc  # noqa: E402

DEFAULT_ROOT = sc.DEFAULT_ROOT
running_version = sc.running_version
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
VERSION_RE = re.compile(r"^[0-9A-Za-z.+-]+$")
RUNTIME_DIR = "_runtime"


class RuntimeError_(Exception):
    """A refusal: `code` is the exit code, `lines` what the CLI prints."""

    def __init__(self, code, *lines):
        super().__init__("\n".join(lines))
        self.code, self.lines = code, list(lines)


def mode(squad_dir):
    """composed: process.local.md exists; legacy: process.md only; none: neither."""
    if os.path.isfile(os.path.join(squad_dir, "process.local.md")):
        return "composed"
    if os.path.isfile(os.path.join(squad_dir, "process.md")):
        return "legacy"
    return "none"


def validate_pin(version, sha, where="the pin"):
    if not VERSION_RE.match(version or "") or version.startswith("-") or not SHA_RE.match(sha or ""):
        raise RuntimeError_(2, f"{where}: expected `plugin: <version> <sha>` (version [0-9A-Za-z.+-], sha 7-40 lower-case "
                               f"hex), got {version!r} {sha!r}")
    return version, sha


def parse_pin_line(text, where="plugin.pin"):
    """`<version> <sha>` (a leading `plugin:` is accepted) -> (version, sha); anything else exits 2."""
    parts = re.sub(r"^plugin:\s*", "", (text or "").strip()).split()
    if len(parts) != 2:
        raise RuntimeError_(2, f"{where}: expected one line `<version> <sha>`, got {text.strip()!r}")
    return validate_pin(parts[0], parts[1], where)


def read_pin_file(squad_dir):
    """$SQUAD_DIR/plugin.pin -> (version, sha) or None when absent."""
    path = os.path.join(squad_dir, "plugin.pin")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8-sig") as f:
        lines = [ln for ln in f.read().replace("\r\n", "\n").split("\n") if ln.strip()]
    if len(lines) != 1:
        raise RuntimeError_(2, f"{path}: expected one line `<version> <sha>`")
    return parse_pin_line(lines[0], path)


def home_pin(home):
    """The `plugin:` pin of a scope or goal home, validated; None when it has none."""
    try:
        pin = sc.read_home(home)["pin"]
    except sc.ComposeError as e:
        raise RuntimeError_(2, *e.lines)
    return validate_pin(*pin, where=f"{home}: plugin pin") if pin else None


def _git(root, *args):
    try:
        r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    except OSError:
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def is_repo_root(root):
    """True only when `root` is itself a git work tree root: a runtime lives inside the project's repo, and
    `git -C <runtime>` would otherwise find that enclosing repo."""
    top = _git(root, "rev-parse", "--show-toplevel")
    return bool(top) and os.path.realpath(top) == os.path.realpath(root)


def running_pin(plugin_root=DEFAULT_ROOT):
    """(version, sha, dirty): the running plugin's version and `git rev-parse HEAD`; raises when it is no repo."""
    version = sc.running_version(plugin_root)
    if not is_repo_root(plugin_root):
        raise RuntimeError_(1, f"cannot pin the running plugin ({plugin_root} is not a git checkout); write "
                               f"{{squad dir}}/plugin.pin as `<version> <sha>`")
    sha = _git(plugin_root, "rev-parse", "HEAD")
    if not sha or not SHA_RE.match(sha):
        raise RuntimeError_(1, f"cannot read HEAD of {plugin_root}")
    return version, sha, bool(_git(plugin_root, "status", "--porcelain"))


def vkey(version):
    """Sortable key: dotted numbers compare as ints (0.10 is newer than 0.9)."""
    return tuple(int(p) if p.isdigit() else 0 for p in re.split(r"[.+-]", version))


def runtime_path(squad_dir, version, sha):
    return os.path.join(os.path.realpath(squad_dir), RUNTIME_DIR, f"{version}-{sha[:12]}")


def _plugin_version(folder):
    try:
        with open(os.path.join(folder, ".claude-plugin", "plugin.json"), encoding="utf-8-sig") as f:
            return json.load(f).get("version")
    except (OSError, ValueError):
        return None


def _restore_hint(version, sha, target, plugin_root):
    return (f"pin: plugin {version} {sha}; restore it with: mkdir -p {target} && git -C <plugin checkout> archive {sha} | "
            f"tar -x -C {target}   (the checkout must contain commit {sha}), or write a pin you have in "
            f"plugin.pin / scope.md")


def _installed_cache(version, sha, plugin_json_paths=None):
    """The installed cache folder of a `squad@*` plugin whose gitCommitSha matches the pin and whose
    plugin.json version equals it; else None. Fixture override: env SQUAD_INSTALLED_PLUGINS (a file path)."""
    env = os.environ.get("SQUAD_INSTALLED_PLUGINS")
    paths = [env] if env else (plugin_json_paths or sorted(
        glob.glob(os.path.join(os.path.expanduser("~"), ".claude*", "plugins", "installed_plugins.json"))))
    for p in paths:
        try:
            with open(p, encoding="utf-8-sig") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        plugins = data.get("plugins") if isinstance(data, dict) else None
        for key, entries in (plugins.items() if isinstance(plugins, dict) else ()):
            if not key.startswith("squad@") or not isinstance(entries, list):
                continue
            for e in entries:
                if not isinstance(e, dict):
                    continue
                have = str(e.get("gitCommitSha") or "")
                path = e.get("installPath")
                if have and path and (have.startswith(sha) or sha.startswith(have)) and os.path.isdir(path) \
                        and _plugin_version(path) == version:
                    return path
    return None


def _extract(plugin_root, sha, dest):
    """git archive <sha> into dest through tarfile (no `tar` binary, exec bits kept, no links outside dest)."""
    proc = subprocess.Popen(["git", "-C", plugin_root, "archive", "--format=tar", sha],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ok = True
    try:
        with tarfile.open(fileobj=proc.stdout, mode="r|", encoding="utf-8") as tf:
            if hasattr(tarfile, "data_filter"):
                tf.extractall(dest, filter="data")
            else:  # Python before 3.12: refuse links and absolute or parent paths by hand
                for m in tf:
                    if m.issym() or m.islnk() or m.name.startswith("/") or ".." in m.name.split("/"):
                        raise tarfile.TarError(f"refusing {m.name}")
                    tf.extract(m, dest)
    except tarfile.TarError:
        ok = False
    finally:
        proc.stdout.close()
        err = proc.stderr.read()
        proc.stderr.close()
        code = proc.wait()
    return ok and code == 0 and not err.strip().startswith(b"fatal")


def materialise(squad_dir, version, sha, plugin_root=DEFAULT_ROOT, dry_run=False):
    """The runtime folder for a pin, built from `git archive <sha>` when absent. Raises RuntimeError_."""
    validate_pin(version, sha)
    target = runtime_path(squad_dir, version, sha)
    if dry_run:
        return target
    if os.path.isdir(target):
        held = _plugin_version(target)
        if held != version:
            shutil.rmtree(target, ignore_errors=True)
            raise RuntimeError_(1, f"runtime {target} holds plugin {held}, not {version}; removed it.",
                                _restore_hint(version, sha, target, plugin_root))
        return target
    base = os.path.dirname(target)
    os.makedirs(base, exist_ok=True)
    tmp = tempfile.mkdtemp(dir=base, prefix=f".tmp-{os.getpid()}-")
    try:
        built = is_repo_root(plugin_root) and _extract(plugin_root, sha, tmp)
        if not built:
            cache = _installed_cache(version, sha)
            if cache:
                return cache
            raise RuntimeError_(1, f"runtime missing: {target} does not exist and commit {sha} is not in {plugin_root}.",
                                _restore_hint(version, sha, target, plugin_root))
        if _plugin_version(tmp) != version:
            raise RuntimeError_(1, f"pin says plugin {version}, but commit {sha} holds plugin {_plugin_version(tmp)}.",
                                _restore_hint(version, sha, target, plugin_root))
        try:
            os.rename(tmp, target)
            tmp = None
        except OSError:
            if not os.path.isdir(target):
                raise
        return target
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


RUNTIME_NAME_RE = re.compile(r"^[0-9A-Za-z.+-]+-[0-9a-f]{12}$")


def _mb(n):
    return f"{n / 1048576:.1f} MB"


def _tree_size(path):
    total = 0
    for dp, _dn, fns in os.walk(path):  # followlinks stays False
        for fn in fns:
            try:
                total += os.lstat(os.path.join(dp, fn)).st_size
            except OSError:
                pass
    return total


def _clear_readonly(func, path, _exc):
    """rmtree error handler: a read-only file (git archive keeps modes; Windows refuses to delete it) loses the
    bit, then the failed call is retried once."""
    os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
    func(path)


def _rmtree(path):
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_clear_readonly)
    else:
        shutil.rmtree(path, onerror=_clear_readonly)


def _under(root, path):
    """True when realpath(path) is directly inside realpath(root)."""
    return os.path.dirname(os.path.realpath(path)) == os.path.realpath(root)


def _holders(squad, exclude_home):
    """{runtime name: [holder label]} from plugin.pin and the pins of scopes/* and goals/* (never a recursive
    glob; `_done` folders are not matched). `exclude_home` (the home being closed) holds nothing."""
    held = {}

    def add(pin, label):
        if pin:
            held.setdefault(f"{pin[0]}-{pin[1][:12]}", []).append(label)

    add(read_pin_file(squad), "plugin.pin")
    skip = os.path.realpath(exclude_home) if exclude_home else None
    for kind, group, marker in (("scope", "scopes", "scope.md"), ("goal", "goals", "goal.md")):
        for home in sorted(glob.glob(os.path.join(glob.escape(squad), group, "*"))):
            name = os.path.basename(home)
            if name == "_done" or not os.path.isfile(os.path.join(home, marker)):
                continue
            if skip and os.path.realpath(home) == skip:
                continue
            add(home_pin(home), f"{kind} {name}")
    return held


def prune(squad_dir, home=None, dry_run=False, protect=(), all_=False, out=print):
    """Delete the `_runtime/<version>-<sha12>/` folders nothing holds; print one line per child and a total.
    Never raises on a failed delete. Returns 0."""
    squad = os.path.realpath(squad_dir)
    root = os.path.join(squad, RUNTIME_DIR)
    if not os.path.isdir(root):
        return 0
    try:
        held = {} if all_ else _holders(squad, home)
    except RuntimeError_ as e:
        out(f"warning: {e.lines[0]}; no runtime removed")
        return 0
    protected = [os.path.realpath(p) for p in protect or ()]
    verb, done = ("would remove", "would free") if dry_run else ("removed", "freed")
    freed = count = 0
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        real = os.path.realpath(path)
        if not RUNTIME_NAME_RE.match(name):
            out(f"kept {name} (not a runtime)")
            continue
        if any(p == real or p.startswith(real + os.sep) for p in protected):
            out(f"kept {name} (running)")
            continue
        if held.get(name):
            out(f"kept {name} (held by {', '.join(held[name])})")
            continue
        if os.path.islink(path):
            if not dry_run:
                try:
                    os.unlink(path)
                except OSError as e:
                    out(f"could not remove {name} ({e.strerror or e})")
                    continue
            out(f"{verb} {name} (link only, target kept)")
            count += 1
            continue
        if not _under(root, path):
            out(f"refused {name} (resolves outside {RUNTIME_DIR}/)")
            continue
        size = _tree_size(path)
        if not dry_run:
            try:
                _rmtree(path)
            except OSError as e:
                out(f"could not remove {name} ({e.strerror or e})")
                continue
            if os.path.lexists(path):
                out(f"could not remove {name}")
                continue
        out(f"{verb} {name} ({_mb(size)})")
        freed += size
        count += 1
    if all_ and not dry_run:
        try:
            os.rmdir(root)
        except OSError:
            pass
    if count:
        out(f"{done} {_mb(freed)} in {count} runtime{'s' if count != 1 else ''}")
    return 0


def cmd_prune(a):
    if bool(a.home) == bool(a.all):
        print("prune: pass --home H or --all", file=sys.stderr)
        return 2
    return prune(a.squad_dir, a.home, a.dry_run, a.protect, a.all)


def cmd_mode(a):
    print(mode(os.path.realpath(a.squad_dir)))
    return 0


def cmd_runtime(a):
    squad = os.path.realpath(a.squad_dir)
    try:
        pin = home_pin(a.home)
        if pin is None:
            raise RuntimeError_(2, f"{a.home}: composed mode needs a pin; add the line `plugin: <version> <sha>` to its "
                                   f"scope.md (or goal.md); squad-start writes it for a new scope")
        print(materialise(squad, pin[0], pin[1], a.plugin_root, a.dry_run))
    except RuntimeError_ as e:
        for line in e.lines:
            print(line, file=sys.stderr)
        return e.code
    return 0


def main(argv=None):
    squadio.utf8_stdio()
    ap = argparse.ArgumentParser(prog="squad-process", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    mp = sub.add_parser("mode", help="composed | legacy | none")
    rp = sub.add_parser("runtime", help="materialise and print the pinned runtime of a scope or goal home")
    pp = sub.add_parser("prune", help="delete the pinned runtimes no open scope, goal or plugin.pin holds")
    for p in (mp, rp, pp):
        p.add_argument("--squad-dir", default=os.environ.get("SQUAD_DIR"), required=not os.environ.get("SQUAD_DIR"))
    rp.add_argument("--home", required=True)
    rp.add_argument("--plugin-root", default=DEFAULT_ROOT)
    rp.add_argument("--dry-run", action="store_true")
    pp.add_argument("--home", help="the scope or goal being closed (its own pin holds nothing)")
    pp.add_argument("--all", action="store_true", help="whole-squad close: ignore holders")
    pp.add_argument("--protect", action="append", default=[], metavar="PATH",
                    help="a path inside a runtime that must stay (the running script); repeatable")
    pp.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    return {"mode": cmd_mode, "runtime": cmd_runtime, "prune": cmd_prune}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
