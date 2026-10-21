"""Effective agent settings: pinned template plus the squad's overlay (ticket 08). stdlib only.

  squadsettings.py effective --role R --squad-dir D --template-root P [--out FILE]

Layouts of <squad>/settings/:
  <role>.local.json  overlay: merged over <P>/templates/squad/settings/<role>.json; prints the effective JSON
  <role>.json        old full file: no overlay, exit 3 tells the caller to use the file as-is
Merge, per key: scalars - the local value wins; permissions.allow / deny / ask - union (template order,
then new local entries, duplicates dropped); other arrays - local replaces; objects - recursive. `codePaths` (a list
in the local file) replaces the placeholder deny entry by one Read deny per path, plus the project's .worktrees;
the placeholder with no codePaths is a refusal (exit 2, fail closed). `codePaths` is never written to the result.
Exit: 0 ok, 1 template missing, 2 unreadable or bad JSON, 3 no overlay (old layout or none).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import squadio  # noqa: E402

PLACEHOLDER = "CODE_PATHS_SET_BY_SQUAD_INIT"
UNION_KEYS = {("permissions", "allow"), ("permissions", "deny"), ("permissions", "ask")}


class SettingsError(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code


def _union(a, b):
    out = []
    for x in list(a) + list(b):
        if x not in out:
            out.append(x)
    return out


def merge(template, local, path=()):
    """Template merged with local, per the rules above. Neither argument is changed."""
    out = dict(template)
    for k, v in local.items():
        here = path + (k,)
        if here in UNION_KEYS and isinstance(v, list) and isinstance(out.get(k, []), list):
            out[k] = _union(out.get(k, []), v)
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v, here)
        else:
            out[k] = v
    return out


def expand_code_paths(settings, code_paths, project_dir=None, where="the local file"):
    """Replace the placeholder deny entry by one Read deny per code path (plus <project>/.worktrees).

    Fails closed: the placeholder present and no code path is a refusal, never a silent drop."""
    deny = settings.get("permissions", {}).get("deny")
    if not isinstance(deny, list):
        return settings
    paths = list(code_paths)
    if project_dir:
        paths.append(project_dir.rstrip("/") + "/.worktrees")
    entries = []
    for e in deny:
        if isinstance(e, str) and PLACEHOLDER in e:
            if not code_paths:
                raise SettingsError(2, f"{where} needs a non-empty codePaths list: the template denies reading "
                                       f"code paths ({PLACEHOLDER}) and none are given")
            entries += [e.replace(PLACEHOLDER, p.strip("/")) for p in paths]
        else:
            entries.append(e)
    settings["permissions"]["deny"] = _union(entries, [])
    return settings


def _load(path, code, what):
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except OSError as e:
        raise SettingsError(code, f"cannot read {what} {path}: {e.strerror}")
    except ValueError as e:
        raise SettingsError(2, f"cannot read {what} {path}: {e}")
    if not isinstance(d, dict):
        raise SettingsError(2, f"cannot read {what} {path}: not a JSON object")
    return d


def effective(role, squad_dir, template_root, project_dir=None):
    """The merged settings dict, or None when the squad has no overlay for the role."""
    local_path = os.path.join(squad_dir, "settings", f"{role}.local.json")
    if not os.path.isfile(local_path):
        return None
    tpl_path = os.path.join(template_root, "templates", "squad", "settings", f"{role}.json")
    if not os.path.isfile(tpl_path):
        raise SettingsError(1, f"no settings template for {role} at {tpl_path}")
    template, local = _load(tpl_path, 1, "template"), _load(local_path, 2, "overlay")
    code_paths = local.pop("codePaths", [])
    if not isinstance(code_paths, list) or not all(isinstance(p, str) and p.startswith("/") for p in code_paths):
        raise SettingsError(2, f"codePaths in {local_path} must be a list of absolute paths")
    return expand_code_paths(merge(template, local), code_paths, project_dir, local_path)


def main(argv=None):
    squadio.utf8_stdio()
    ap = argparse.ArgumentParser(prog="squadsettings")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("effective")
    p.add_argument("--role", required=True)
    p.add_argument("--squad-dir", required=True)
    p.add_argument("--template-root", required=True)
    p.add_argument("--project-dir")
    p.add_argument("--out")
    a = ap.parse_args(argv)
    try:
        eff = effective(a.role, a.squad_dir, a.template_root, a.project_dir)
    except SettingsError as e:
        print(str(e), file=sys.stderr)
        return e.code
    if eff is None:
        return 3
    text = json.dumps(eff, indent=2) + "\n"
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        tmp = a.out + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, a.out)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
