"""apply2.py <stem>: cut rows of cuts2.tsv for tests/test_<stem>.py, drop empty classes, log removed.tsv rows."""
import ast, re, subprocess, sys
T = ".scratch/windows-native/issues/10-prune-tests"
stem = sys.argv[1]
rows = [l.rstrip("\n").split("|") for l in open(f"{T}/tools/cuts2.tsv", encoding="utf-8") if l.startswith(stem + "|")]
p = f"tests/test_{stem}.py"
subprocess.run([sys.executable, f"{T}/tools/del.py", p, *[r[1] for r in rows]], check=True)
subprocess.run([sys.executable, f"{T}/tools/clean.py", p], check=True)
src = open(p, encoding="utf-8", newline="").read()
tree = ast.parse(src)
lines = src.split("\n")
for c in reversed([n for n in tree.body if isinstance(n, ast.ClassDef)]):
    if not any(isinstance(n, ast.FunctionDef) for n in c.body):
        a = c.lineno - 1 - len(c.decorator_list); b = c.end_lineno
        print("drop empty class", c.name)
        del lines[a:b]
open(p, "w", encoding="utf-8", newline="").write("\n".join(lines))
subprocess.run([sys.executable, f"{T}/tools/clean.py", p], check=True)
ast.parse(open(p, encoding="utf-8").read())
with open(f"{T}/removed.tsv", "a", encoding="utf-8", newline="") as o:
    for f, t, r, w, c in rows:
        o.write(f"test_{f}::{t}\t{r}\t{w}\t{c}\n")
print(stem, "cut", len(rows))
