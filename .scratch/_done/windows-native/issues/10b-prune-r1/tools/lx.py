"""lx.py stem...: per-file Linux run (WSL Debian, python3 -m unittest -q), prints stem | secs | Ran N | last line."""
import re, subprocess, sys, time
R = "/mnt/c/Users/84084/workspace/squad/.worktrees/plugin/solve-windows/plugin-dev-solve-windows-11/tests"
for f in sys.argv[1:]:
    t = time.time()
    p = subprocess.run(["wsl", "-d", "Debian", "--", "bash", "-c",
        f"cd {R} && env -u SQUAD_DIR -u SCOPE_DIR -u SQUAD_NAME -u SQUAD_SCOPE -u GOAL_DIR PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -q test_{f} 2>&1"],
        capture_output=True)
    o = p.stdout.decode("utf-8", "replace").replace("\0", "")
    m = re.search(r"Ran (\d+) tests? in", o)
    last = o.strip().splitlines()[-1] if o.strip() else ""
    print(f"{f} | {time.time()-t:.1f}s | ran {m.group(1) if m else '?'} | {last}", flush=True)
    for l in re.findall(r"^(?:FAIL|ERROR): .*$", o, re.M)[:5]:
        print("   ", l, flush=True)
