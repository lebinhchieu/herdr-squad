"""Builds mapping.md from spec.txt (ranges -> targets), one row per non-blank, non-heading, non-table-separator source line.
Usage: python3 -I make_mapping.py <plugin-root> <spec.txt> <out mapping.md>; prints uncovered lines and exits 1 on gaps."""
import os, re, sys
root, spec_path, out = sys.argv[1:4]
SRC = {"P": "templates/squad/process.md"}
for n in ("manager", "team-lead", "tech-lead", "ba", "qa-whitebox", "qa-blackbox", "designer", "dev", "token-coach"):
    SRC[n] = f"agents/{n}.md"
spec = {}
for raw in open(spec_path, encoding="utf-8"):
    raw = raw.strip()
    if not raw or raw.startswith("#"):
        continue
    key, rng, target = raw.split(" ", 2)
    a, b = map(int, rng.split("-"))
    for n in range(a, b + 1):
        spec.setdefault((key, n), target)

def source_lines(key):
    if key == "log":
        return []
    with open(os.path.join(root, SRC[key]), encoding="utf-8") as f:
        lines = f.read().split("\n")
    skip, fenced = set(), False
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if s.startswith("```"):
            fenced = not fenced
        elif not fenced and ln.startswith("#"):
            skip.add(i)
        if not s:
            skip.add(i)
        if re.fullmatch(r"[|\s:-]+", s) and s.startswith("|"):
            skip.add(i)
            if i > 1:
                skip.add(i - 1)  # header row
    return [(i, lines[i - 1]) for i in range(1, len(lines) + 1) if i not in skip]

rows, gaps = [], []
for key in ("P", "manager", "team-lead", "tech-lead", "ba", "qa-whitebox", "qa-blackbox", "designer", "dev", "token-coach"):
    label = SRC[key]
    for i, text in source_lines(key):
        t = spec.get((key, i))
        if t is None:
            gaps.append(f"{label}:{i}: {text[:70]}")
            continue
        rows.append((f"{label}:{i}", t, text))
for n in range(33, 50):
    t = spec.get(("log", n))
    if t is None:
        gaps.append(f"log row {n}")
    else:
        rows.append((f"log row {n}", t, ""))
if gaps:
    print("\n".join(gaps))
    sys.exit(1)
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write("# Mapping: every source line to its rule\n\n"
            "Source = `templates/squad/process.md` (v6), `agents/<role>.md` or `log row <N>` (line N of the live squad's "
            "`process-log.md`, rows 33-49 are the Coach and Manager changes of 2026-10-16 to 2026-10-19 that are not `v<N>` migration rows). "
            "Target = rule ID(s), `dropped: duplicate of <ID>`, `dropped: structure`, `dropped: replaced by compose`, `dropped: fix <a-e>`, "
            "or `stays in card`. Several IDs are comma separated: the line was split across those rules. Header rows, separator rows "
            "and `#` headings are not listed.\n\n| Source | Target | Source text (first 60 chars) |\n|---|---|---|\n")
    for src, t, text in rows:
        f.write(f"| {src} | {t} | {text[:60].replace('|', '/')} |\n")
    f.write("\n## Rules with no source row of their own\n\n"
            "- `SIZE-12`: the heading of v6 line 109 (\"duties move, never dropped\"); headings are not rows.\n"
            "- `START-2d`: fix (b), the Tech Lead tells the Manager which tasks are ready in parallel (S).\n"
            "- Fix (a) is `REV-13a` / `REV-13b` / `REV-14a` / `REV-14b`; fix (c) is `MSG-16a` / `MSG-16b` (BA decision BD6); "
            "fix (d) drops \"The label shape is in process.md\" (`manager.md:57`, mapped to `SPAWN-7`, which does not repeat it); "
            "fix (e) puts the Token Coach rules in `ITER-6` to `ITER-10` and nothing cites a Retro section.\n")
print(len(rows), "rows")
