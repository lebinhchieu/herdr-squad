"""Rule commands of `squad-process`: lint now; rule, who and compose <role> are added by ticket 04.

  squad-process lint [--squad-dir D] [--plugin-root R] [--cards error|warn] [--hashes]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import squadio  # noqa: E402
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


def main(argv=None):
    squadio.utf8_stdio()
    ap = argparse.ArgumentParser(prog="squad-process", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    lp = sub.add_parser("lint", help="check the rule files and the squad's overlay")
    lp.add_argument("--squad-dir", default=os.environ.get("SQUAD_DIR"))
    lp.add_argument("--plugin-root", default=DEFAULT_ROOT)
    lp.add_argument("--cards", choices=("error", "warn"), default="warn")
    lp.add_argument("--hashes", action="store_true", help="after any problems print `<ID> <hash>` per rule")
    for name in ("rule", "who", "compose"):
        p = sub.add_parser(name)
        p.add_argument("args", nargs="*")
    a = ap.parse_args(argv)
    if a.cmd == "lint":
        return cmd_lint(a)
    print(f"squad-process {a.cmd}: not available yet (ticket 04)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
