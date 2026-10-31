import subprocess, sys
D = sys.argv[1]
NL = bytes([10])
rows = []
for l in open(D + "/baseline-before.txt", encoding="utf-8"):
    n, t, ran, res = [x.strip() for x in l.split("|")][:4]
    f = f"tests/test_{n}.py"
    log = subprocess.run(["git", "log", "--format=%H %s", "--", f], capture_output=True, text=True).stdout.splitlines()
    mine = [x.split()[0] for x in log if x.split(" ", 1)[1].startswith("10:")]
    ref = (mine[-1] + "^") if mine else "HEAD"
    b = subprocess.run(["git", "show", f"{ref}:{f}"], capture_output=True).stdout.count(NL)
    a = open(f, "rb").read().count(NL)
    rows.append((n, b, a, t, ran))
rows.sort(key=lambda r: -r[1])
print("| file | lines before | lines after | time before | tests before |\n|---|---|---|---|---|")
for n, b, a, t, ran in rows:
    print(f"| test_{n} | {b} | {a} | {t} | {ran[4:]} |")
