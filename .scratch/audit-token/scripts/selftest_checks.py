"""Self-test of every fixture's checks.py: good.txt must give no defects, bad.txt at least one."""
import importlib.util, os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fixtures")
ok = True
for name in sorted(os.listdir(ROOT)):
    d = os.path.join(ROOT, name)
    spec = importlib.util.spec_from_file_location("c_" + name, os.path.join(d, "checks.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    g = mod.check(open(os.path.join(d, "selftest", "good.txt")).read())
    b = mod.check(open(os.path.join(d, "selftest", "bad.txt")).read())
    res = (g == [] and b != [])
    ok &= res
    print(f"{name}: good->{g} bad->{b} {'OK' if res else 'FAIL'}")
sys.exit(0 if ok else 1)
