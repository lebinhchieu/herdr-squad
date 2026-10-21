"""Rule commands of `squad-process`: lint, rule, who, compose <role>.

  squad-process lint [--squad-dir D] [--plugin-root R] [--cards error|warn] [--hashes]
  squad-process compose <role> --home D [--agent A] [--out F] [--plugin-root R] [--squad-dir D] [--now ISO]
  squad-process rule <ID> [--squad-dir D] [--plugin-root R]
  squad-process who <ID> [--squad-dir D] [--plugin-root R]
"""
import argparse
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import squadio  # noqa: E402
import squadcompose as sc  # noqa: E402
import squadrules as sr  # noqa: E402

DEFAULT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def cmd_lint(a):
    root = a.plugin_root
    errors, warnings, has_rules = sr.lint(root, a.squad_dir, a.cards)
    if not has_rules:
        print("no rule files")
        return 0
    for line in errors:
        print(line)
    for line in warnings:
        print(f"warning: {line}")
    if a.hashes:
        rules, _tombs, _problems = sr.load_rules(sr.process_dir(root), root)
        for r in rules:
            print(f"{r.id} {r.hash}")
    return 1 if errors else 0


def _overlay(a):
    return os.path.join(a.squad_dir, sr.OVERLAY_FILE) if a.squad_dir else None


def _fail(e):
    for line in e.lines:
        print(line, file=sys.stderr)
    return 2


def cmd_compose(a):
    try:
        if a.role not in sr.ROLES:
            raise sc.ComposeError(f"compose: unknown role {a.role!r} (one of {', '.join(sr.ROLES)})")
        info = sc.read_home(a.home)
        root, pin = a.plugin_root, info["pin"]
        if pin is None:
            root = root or sc.DEFAULT_ROOT
            print("squad-process: no `plugin:` pin in the home; composing from the running plugin", file=sys.stderr)
        else:
            if root is None:
                if pin[0] != sc.running_version():
                    raise sc.ComposeError(
                        f"compose: pin is plugin {pin[0]} but the running plugin is {sc.running_version()}; "
                        "pass --plugin-root <that version's plugin folder>")
                root = sc.DEFAULT_ROOT
        now = a.now or os.environ.get("SQUAD_COMPOSE_NOW") or \
            datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        text = sc.compose(a.role, a.home, root, _overlay(a), a.agent, now, pin)
    except sc.ComposeError as e:
        return _fail(e)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    else:
        sys.stdout.write(text)
    return 0


def cmd_rule(a):
    try:
        print(sc.rule_text(sc.find_rule(a.plugin_root or sc.DEFAULT_ROOT, _overlay(a), a.id)), end="")
    except sc.ComposeError as e:
        return _fail(e)
    return 0


def cmd_who(a):
    try:
        e = sc.find_rule(a.plugin_root or sc.DEFAULT_ROOT, _overlay(a), a.id)
    except sc.ComposeError as ex:
        return _fail(ex)
    print("\n".join(sc.who_lines(e)))
    return 0


def main(argv=None):
    squadio.utf8_stdio()
    ap = argparse.ArgumentParser(prog="squad-process", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    lp = sub.add_parser("lint", help="check the rule files and the squad's overlay")
    lp.add_argument("--squad-dir", default=os.environ.get("SQUAD_DIR"))
    lp.add_argument("--plugin-root", default=DEFAULT_ROOT)
    lp.add_argument("--cards", choices=("error", "warn"), default="error")
    lp.add_argument("--hashes", action="store_true", help="after any problems print `<ID> <hash>` per rule")
    cp = sub.add_parser("compose", help="composed rules for one role")
    cp.add_argument("role")
    cp.add_argument("--home", required=True)
    cp.add_argument("--agent")
    cp.add_argument("--out")
    cp.add_argument("--now")
    for name in ("rule", "who"):
        p = sub.add_parser(name)
        p.add_argument("id")
    for p in (cp, sub.choices["rule"], sub.choices["who"]):
        p.add_argument("--squad-dir", default=os.environ.get("SQUAD_DIR"))
        p.add_argument("--plugin-root", default=None)
    a = ap.parse_args(argv)
    return {"lint": cmd_lint, "compose": cmd_compose, "rule": cmd_rule, "who": cmd_who}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
