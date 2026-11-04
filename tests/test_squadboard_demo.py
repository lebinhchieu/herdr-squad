"""Ticket 37: `squad-board --demo`. Names carry the business (T37.ACn) or technical (T37.TAn) AC they cover.
TA4 (the label, step 37b) is in class Label."""
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "bin"))
import squadboard  # noqa: E402
import squadboard_demo  # noqa: E402
from test_squadboard_page import CHROME, STUB, Server, run_page  # noqa: E402

PREFIX = "squad-board-demo-"
STAGES = ("todo", "in progress", "returned", "blocked", "checking", "ready for review", "sha changed after PASS", "merged", "done")
VIEWS = ("goal=alpha", "scope=checkout")


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def demo_dirs():
    return {p.name for p in Path(tempfile.gettempdir()).glob(PREFIX + "*")}


def tree_hash(root):
    h = hashlib.sha256()
    for p in sorted(Path(root).rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode() + p.read_bytes())
    return h.hexdigest()


def panel_routes():
    """The API route of every panel, read from the panel registry files (a fixed pattern; no panel found fails loudly)."""
    text = "".join(p.read_text(encoding="utf-8") for p in sorted((ROOT / "templates" / "board").glob("*.js")))
    routes = set(re.findall(r'route:\s*"(/api/\w+)"', text)) | set(re.findall(r'"(/api/worktime)\?"', text))
    if len(routes) < 6:
        raise AssertionError("panel registry: found only %s, expected 6 panel routes" % sorted(routes))
    return sorted(routes)


def git_status():
    return subprocess.run(["git", "status", "--porcelain"], cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8").stdout


class RunningDemo(unittest.TestCase):
    """One demo run in this process; the real-looking sentinels around it must stay untouched (TA1, TA6)."""

    @classmethod
    def setUpClass(cls):
        cls.addClassCleanup(cls.cleanup)
        cls.real = "REALSQUAD-" + secrets.token_hex(4)
        cls.sentinel_dir = Path(tempfile.mkdtemp(prefix="demo-sentinel-"))
        (cls.sentinel_dir / "squad").mkdir()
        home = cls.sentinel_dir / "home"
        proj = home / ".claude" / "projects" / "-real"
        proj.mkdir(parents=True)
        (proj / (cls.real + ".jsonl")).write_text('{"type": "agent-name", "agentName": "%s"}\n' % cls.real, encoding="utf-8")
        cls.untracked = ROOT / cls.real  # an untracked file of the real checkout
        cls.untracked.write_text("x\n", encoding="utf-8")
        cls.before = (git_status(), tree_hash(HERE / "fixtures" / "board"), tree_hash(home))
        cls.home = home
        cls.env = {k: os.environ.get(k) for k in ("SQUAD_DIR", "HOME", "CLAUDE_CONFIG_DIR")}
        os.environ.update(SQUAD_DIR=str(cls.sentinel_dir / "squad"), HOME=str(home), CLAUDE_CONFIG_DIR=str(home / ".claude"))
        cls.calls, cls.mains, cls.cwd = [], [], os.getcwd()
        real_run, real_popen = subprocess.run, subprocess.Popen

        def spy_run(*a, **k):
            cls.calls.append((k.get("cwd"), (k.get("env") or os.environ).get("SQUAD_DIR"), os.getcwd()))
            return real_run(*a, **k)

        def spy_popen(*a, **k):
            cls.calls.append((k.get("cwd"), (k.get("env") or os.environ).get("SQUAD_DIR"), os.getcwd()))
            return real_popen(*a, **k)
        subprocess.run, subprocess.Popen = spy_run, spy_popen
        cls.restore = (real_run, real_popen)
        cls.stop = threading.Event()
        cls.port = free_port()

        def main(argv, stop=None, demo=False):
            cls.mains.append(list(argv))
            return squadboard.main(argv, stop=stop, open_browser=lambda u: None, demo=demo)
        cls.rc = []
        cls.thread = threading.Thread(target=lambda: cls.rc.append(squadboard_demo.run(
            ["--demo", "--port", str(cls.port), "--no-open"], main=main, stop=cls.stop)), daemon=True)
        cls.thread.start()
        for _ in range(100):
            try:
                cls.get("/api/squads")
                break
            except OSError:
                time.sleep(0.1)
        else:
            raise AssertionError("demo did not start")

    @classmethod
    def cleanup(cls):
        cls.stop.set()
        cls.thread.join(10)
        subprocess.run, subprocess.Popen = cls.restore
        for k, v in cls.env.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        cls.untracked.unlink(missing_ok=True)
        for p in sorted(cls.sentinel_dir.rglob("*"), reverse=True):
            p.rmdir() if p.is_dir() else p.unlink()
        cls.sentinel_dir.rmdir()

    @classmethod
    def get(cls, path):
        return json.load(urllib.request.urlopen("http://127.0.0.1:%d%s" % (cls.port, path), timeout=10))

    def api(self, route, view, extra=""):
        return self.get("%s?squad=fix&%s%s" % (route, view, extra))

    def test_T37_TA4_AC6_demo_flag_is_true_in_the_demo(self):
        self.assertIs(self.get("/api/squads")["data"].get("demo"), True)

    def test_T37_TA2_AC2_AC5_every_panel_has_content(self):
        routes = panel_routes()
        gap = {"night": False, "dst": False}
        dst = datetime(2026, 11, 1, 6, 0, tzinfo=timezone.utc).timestamp()
        for view in VIEWS:
            if view.startswith("scope"):
                routes_here = [r for r in routes if r != "/api/scopes"]
            else:
                routes_here = routes
            self.assertEqual(len(routes_here), 6 if view.startswith("goal") else 5, view)
            for r in routes_here:
                o = self.api(r, view)
                self.assertEqual(o["unknown"], [], (view, r))
                self.assertNotEqual(o["quality"], "unknown", (view, r))
                d = o["data"]
                n = {"/api/inbox": lambda: len(d["rows"]) + len((d["banner"] or {}).get("entries") or []),
                     "/api/tasks": lambda: len(d["rows"]), "/api/agents": lambda: len(d["agents"]),
                     "/api/files": lambda: len(d["rows"]), "/api/worktime": lambda: len(d["agents"]),
                     "/api/scopes": lambda: len(d["scopes"])}[r]()
                self.assertGreater(n, 0, (view, r))
            inbox = self.api("/api/inbox", view)["data"]
            self.assertTrue(inbox["rows"] and inbox["banner"]["entries"], view)  # an open question and a blocked agent
            statuses = {a["status"] for a in self.api("/api/agents", view)["data"]["agents"]}
            self.assertTrue({"working", "idle", "blocked"} <= statuses, (view, statuses))
            wt = self.api("/api/worktime", view)["data"]
            for a in wt["agents"]:
                for x in a["pieces"]:
                    gap["night"] |= x["end"] - x["start"] >= 11 * 3600
                    gap["dst"] |= x["start"] < dst < x["end"]
            self.assertGreaterEqual(wt["to"] - time.time(), -120, "window ends now")
        self.assertEqual(gap, {"night": True, "dst": True})
        stages = [t["stage"] for t in self.api("/api/tasks", "scope=checkout")["data"]["rows"]]
        for s in STAGES:
            self.assertTrue(any(x.startswith(s) for x in stages), (s, stages))
        self.assertGreaterEqual(len(self.api("/api/tasks", "goal=alpha")["data"]["rows"]), 3)

    def test_T37_TA3_AC11_ages_are_recent(self):
        rows = self.api("/api/tasks", "scope=checkout")["data"]["rows"]
        checking = [t["stage"] for t in rows if t["stage"].startswith("checking")][0]
        self.assertIn("40 min", checking)
        text = json.dumps([self.api(r, v) for r in ("/api/tasks", "/api/agents") for v in VIEWS])
        self.assertIsNone(re.search(r"\b\d+ (days?|years?)\b", text))

    def test_T37_TA1_AC7_AC8_nothing_real(self):
        everything = json.dumps([self.get("/api/squads"), self.get("/api/scopes?squad=fix&goal=alpha")] +
                                [self.api(r, v) for r in panel_routes() for v in VIEWS])
        self.assertNotIn(self.real, everything)
        copy = Path(self.mains[0][self.mains[0].index("--squad") + 1])
        self.assertEqual(self.mains[0].count("--squad"), 1)
        self.assertTrue(str(copy).startswith(tempfile.gettempdir()))
        for cwd, squad_dir, cwd_now in self.calls:  # every subprocess call runs inside the copy, with no real SQUAD_*
            here = str(cwd or cwd_now)
            self.assertTrue(here.startswith(str(copy.parents[3])), (cwd, cwd_now))
            self.assertIsNone(squad_dir)

    def test_T37_TA6_AC8_AC10_read_only_and_cleaned(self):
        squad = Path(self.mains[0][self.mains[0].index("--squad") + 1])
        copy = squad.parents[3]
        self.assertTrue(copy.is_dir())
        token = self.get("/api/session")["data"]["token"]  # the board's one write: PUT /api/ui lands in the copy
        req = urllib.request.Request("http://127.0.0.1:%d/api/ui?squad=fix" % self.port, method="PUT",
                                     data=json.dumps({"saved_at": "2026-11-04T10:00:00Z"}).encode(),
                                     headers={"X-Board-Token": token, "Content-Type": "application/json"})
        self.assertEqual(urllib.request.urlopen(req, timeout=10).status, 200)
        self.assertTrue((squad / "board-ui.json").is_file())
        self.stop.set()
        self.thread.join(10)
        self.assertFalse(copy.exists())
        self.assertEqual(self.rc, [0])
        self.assertEqual(os.getcwd(), self.cwd)
        self.assertEqual((git_status(), tree_hash(HERE / "fixtures" / "board"), tree_hash(self.home)), self.before)


class Flags(unittest.TestCase):
    def test_T37_TA5_AC1_exit_codes(self):
        before = demo_dirs()
        busy = socket.socket()
        busy.bind(("127.0.0.1", 0))
        busy.listen(1)
        self.addCleanup(busy.close)
        table = [(["--demo", "--squad", "x"], 2), (["--demo", "--goal", "alpha"], 2), (["--demo", "--scope", "checkout"], 2),
                 (["--demo", "--port", str(busy.getsockname()[1]), "--no-open"], 1)]
        for argv, code in table:
            self.assertEqual(squadboard_demo.run(argv), code, argv)
        self.assertEqual(demo_dirs(), before)  # no folder left after exit 1 or 2

    def test_T37_TA1_copy_removed_when_main_raises(self):
        before = demo_dirs()

        def boom(argv, stop=None, demo=False):
            raise RuntimeError("boom")
        with self.assertRaises(RuntimeError):
            squadboard_demo.run(["--demo", "--port", "0", "--no-open"], main=boom)
        self.assertEqual(demo_dirs(), before)

    def test_T37_TA5_help_documents_demo(self):
        self.assertIn("--demo", squadboard_demo.help_text())

    @unittest.skipIf(sys.platform == "win32", "SIGTERM child test is POSIX only")
    def test_T37_TA5_AC10_sigterm_removes_copy(self):
        p = subprocess.Popen([sys.executable, "-I", str(ROOT / "bin" / "squad-board"), "--demo", "--port", "0", "--no-open"],
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
        try:
            line = p.stdout.readline()
            m = re.match(r"demo: sample data in (.+)$", line.strip())
            self.assertTrue(m, line)
            path = Path(m.group(1))
            self.assertTrue(path.is_dir())
            p.stdout.readline()  # the URL line: the server is up
            p.send_signal(signal.SIGTERM)
            self.assertIn(p.wait(15), (0, 143))  # 0: the handler ended it cleanly
            self.assertFalse(path.exists())
        finally:
            if p.poll() is None:
                p.kill()
            p.stdout.close()


def css_token(name):
    """The value of a colour token of board.css, as the rgb() string a browser computes."""
    m = re.search(r"--%s:\s*#([0-9A-Fa-f]{6})" % name, (ROOT / "templates" / "board" / "board.css").read_text(encoding="utf-8"))
    assert m, "token --%s not found in board.css" % name
    h = m.group(1)
    return "rgb(%d, %d, %d)" % tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


PROBE = """
mkPanel('1','A',1,4,300);
BOARD.start({fetch:mkFetch({'1':1}),tz:'UTC',now:()=>Date.parse('2026-11-04T10:00:00Z'),setTimeout:fk.setTimeout,clearTimeout:fk.clearTimeout,storage:mem()});
await sleep(300);
const look=()=>{const e=document.querySelector('.demo');if(!e)return null;const c=getComputedStyle(e),r=e.getBoundingClientRect();
  return {text:e.textContent,shown:!e.hidden&&r.height>0,first:e.parentNode.firstChild===e,role:e.getAttribute('role'),kids:e.children.length,
  bg:c.backgroundColor,color:c.color,weight:c.fontWeight,ls:c.letterSpacing,fs:c.fontSize,bstyle:c.borderBottomStyle,bw:c.borderBottomWidth,bc:c.borderBottomColor,
  pos:c.position,top:r.top,h:r.height,headTop:document.querySelector('header.top').getBoundingClientRect().top}};
const o={first:look(),title1:document.title};
fakeTimers.splice(0).forEach(t=>t.f());await sleep(300);          // a poll
o.afterPoll=look();o.title2=document.title;
[...document.querySelectorAll('button.hb')].filter(b=>b.textContent==='Reset layout')[0].click();await sleep(200);  // a layout change
o.afterLayout=look();o.title3=document.title;
out(o);
"""


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser test skipped")
class Label(unittest.TestCase):
    """T37.TA4 (AC6, AC12): the demo flag in /api/squads and the light strip on the page."""

    def page(self, squads_json, session, ui, width=1440):
        return run_page(STUB + PROBE, {"session": session, "squads": squads_json, "ui": ui}, width=width)

    def test_T37_TA4_AC6_flag_only_in_demo_and_strip_is_light_and_stays(self):
        normal = Server()
        self.addCleanup(normal.close)
        normal.srv.routes = squadboard.load_routes()[0]  # the real routes: /api/squads is the picker route
        plain = json.loads(normal.get("/api/squads")[1])
        self.assertNotIn("demo", plain["data"])  # a normal run: no key
        demo = json.loads(json.dumps(plain))
        demo["data"]["demo"] = True  # what the demo server answers (checked on the running demo in RunningDemo)
        session = json.loads(normal.get("/api/session")[1])
        ui = json.loads(normal.get("/api/ui?squad=" + plain["data"]["squads"][0]["key"])[1])
        n = self.page(plain, session, ui)
        for width in (1000, 1440):
            self.look(self.page(demo, session, ui, width), n, width)

    def look(self, d, n, width):
        text = "DEMO · sample data, not your squads"
        panel, ink, muted = css_token("panel"), css_token("ink"), css_token("muted")
        for step in ("first", "afterPoll", "afterLayout"):
            s = d[step]
            self.assertEqual((s["text"], s["shown"], s["first"], s["role"], s["kids"]), (text, True, True, "note", 0), (step, width))
            self.assertEqual((s["bg"], s["color"], s["bstyle"], s["bw"], s["bc"]), (panel, ink, "dashed", "2px", muted), (step, width))
            self.assertEqual(s["weight"], "700", (step, width))
            self.assertAlmostEqual(float(s["ls"][:-2]), 0.05 * float(s["fs"][:-2]), delta=0.02, msg=(step, width))  # .05em
            self.assertEqual((s["pos"], s["top"]), ("sticky", 0), (step, width))
            self.assertAlmostEqual(s["headTop"], s["h"], delta=1, msg=(step, width))  # the top bar follows it in flow: nothing overlaps
        for t in ("title1", "title2", "title3"):
            self.assertTrue(d[t].startswith("[demo] "), d[t])
        self.assertFalse(n["first"]["shown"])  # a normal run: hidden, no prefix
        self.assertFalse(n["title1"].startswith("[demo]"))


PW_CORE = Path("/home/chieule/.nvm/versions/node/v24.15.0/lib/node_modules/@playwright/cli/node_modules/playwright-core")


def browser(mode, port, profile):
    env = {**os.environ, "PLAYWRIGHT_CORE": str(PW_CORE), "CHROME_BIN": CHROME}
    r = subprocess.run(["node", str(HERE / "demo_ac9_browser.js"), mode, "http://127.0.0.1:%d/" % port, str(profile)],
                       capture_output=True, text=True, encoding="utf-8", timeout=120, env=env)
    assert r.returncode == 0, r.stderr[-600:]
    return json.loads(r.stdout.strip().splitlines()[-1])


@unittest.skipUnless(PW_CORE.exists() and CHROME and shutil.which("node"), "needs node + playwright-core + Chrome")
class Browser(unittest.TestCase):
    """The demo seen by a real Chrome with a persistent profile (T37.AC9, T37.AC11)."""

    def start(self, port):
        p = subprocess.Popen([sys.executable, "-I", str(ROOT / "bin" / "squad-board"), "--demo", "--port", str(port), "--no-open"],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=tempfile.gettempdir())
        for _ in range(100):
            try:
                urllib.request.urlopen("http://127.0.0.1:%d/api/squads" % port, timeout=2)
                return p
            except OSError:
                time.sleep(0.2)
        p.kill()
        raise AssertionError("demo did not start")

    def stop(self, p):
        p.send_signal(signal.SIGINT)
        p.wait(15)

    def test_T37_AC9_hidden_panel_does_not_survive_a_demo_restart(self):
        profile = tempfile.mkdtemp(prefix="demo-profile-")
        self.addCleanup(shutil.rmtree, profile, True)
        port = free_port()
        p = self.start(port)
        try:
            first = browser("hide", port, profile)
        finally:
            self.stop(p)
        self.assertNotIn("files", first["panels"])  # the hide worked
        self.assertEqual(first["keys"], [])  # the demo writes no layout to browser storage
        p = self.start(port)
        try:
            second = browser("check", port, profile)
        finally:
            self.stop(p)
        self.assertEqual(sorted(second["panels"]), sorted(["inbox", "scopes", "tasks", "agents", "files", "worktime"]), second)
        self.assertEqual(second["keys"], [])

    def test_T37_AC11_no_age_in_days_in_the_rendered_demo(self):
        profile = tempfile.mkdtemp(prefix="demo-profile-")
        self.addCleanup(shutil.rmtree, profile, True)
        port = free_port()
        p = self.start(port)
        try:
            views = browser("ages", port, profile)
        finally:
            self.stop(p)
        age = re.compile(r"\b\d+\s*(d|day|days|y|year|years)\b\s*ago", re.I)
        self.assertGreaterEqual(len(views), 3, list(views))
        for label, text in views.items():
            self.assertTrue(text.strip(), label)  # not vacuous
            self.assertIsNone(age.search(text), (label, age.search(text) and age.search(text).group(0)))
        self.assertTrue(any(re.search(r"Pick the payment provider[\s\S]{0,200}\b\d+ min ago", t) for t in views.values()), "E1 reads minutes")


if __name__ == "__main__":
    unittest.main()
