"""Composed size per role and size (stand-in for `squad-process compose`): rules whose roles or aware match
and whose `when:` holds, body text plus heading lines. Usage: python3 -I size_table.py <plugin-root>"""
import os, sys
root = sys.argv[1]
sys.path.insert(0, os.path.join(root, "bin"))
import squadrules as sr

rules, _t, problems = sr.load_rules(sr.process_dir(root), root)
assert not problems, problems
ROLES = sr.ROLES
print("| Role | S bytes / rules | M bytes / rules | L bytes / rules |")
print("|---|---|---|---|")
for role in ROLES:
    cells = []
    for size in ("S", "M", "L"):
        facts = {"size": size, "design": "no", "qa": "full", "goal": "no", "qa-b": "yes"}
        if role == "designer":
            facts["design"] = "yes"
        n = b = 0
        for r in rules:
            if not (("all" in r.roles or role in r.roles or role in r.aware) and sr.matches(r.when, facts)):
                continue
            n += 1
            b += len(f"## {r.id} {r.title}\n\n{r.body}\n\n".encode("utf-8"))
        cells.append(f"{b} / {n}")
    print(f"| {role} | " + " | ".join(cells) + " |")
