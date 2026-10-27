"""squad-report rollup page (ticket 18): headless-Chrome DOM checks of the real rollup per mock state.

Own harness (no shared file with the scope-report UI test). `build_states(outdir)` writes one index.html per state
(normal, mixed, files, single, empty, error) and is also used by hand for the screenshot evidence.
Skips (not fails) when no Chrome is installed.
"""
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "bin"))
import squadreport_rollup as ro  # noqa: E402
from test_squadreport_rollup import scope_json, write, PRICES_A, PRICES_B, PLANT  # noqa: E402

CHROME = next((c for c in map(shutil.which, ("google-chrome", "chromium", "chromium-browser", "chrome")) if c), None)
NOW = ro.parse_ts("2026-10-20T00:00:00Z")


def _scope(d, squad, name, **kw):
    kw.setdefault("start", "2026-09-28T09:00:00Z")
    kw.setdefault("end", "2026-10-02T09:00:00Z")
    return write(d, "%s/%s/data.json" % (squad, name), scope_json(squad, name, **kw))


def build_states(out):
    """-> {state: Path to index.html}. Real rollups built by the builder from scope data.json files."""
    out = Path(out)
    src = out / "src"
    big = _scope(src, "plugin", "win-compat", cost=1386.0, agent_s=212 * 3600, returns=12, passed=2, size="L", att=71.0)
    mid = _scope(src, "plugin", "per-scope-squads", cost=402.0, agent_s=70 * 3600, returns=0, passed=2, size="M", att=82.0, start="2026-10-01T09:00:00Z", end="2026-10-03T00:00:00Z")
    small = _scope(src, "plugin", "board-removal", cost=61.0, agent_s=14 * 3600, returns=0, size="S", att=90.0, start="2026-10-06T09:00:00Z", end="2026-10-06T18:00:00Z")
    run = _scope(src, "plugin", "squad-report", cost=318.0, agent_s=58 * 3600, status="running", returns=1, size="L", att=74.0, start="2026-10-12T09:00:00Z", end="2026-10-13T07:00:00Z")
    stale = _scope(src, "plugin", "inbox-mod", cost=88.0, agent_s=19 * 3600, returns=1, size="S", att=55.0, gen="2026-10-02T10:00:00Z", last="2026-10-04T13:00:00Z",
                   prices=PRICES_B, start="2026-10-08T09:00:00Z", end="2026-10-08T20:00:00Z")
    old = write(src, "teammate-a/old/data.json", None, raw=json.dumps({"schema_version": 0, "kind": "scope"}))
    junk = write(src, "teammate-b/junk/data.json", None, raw="not json")
    dup_old = _scope(src, "teammate-a", "dup", cost=5.0, agent_s=3600, gen="2026-10-01T00:00:00Z")
    dup_new = write(src, "teammate-a/dup2/data.json", scope_json("teammate-a", "dup", 6.0, 7200, gen="2026-10-03T00:00:00Z"))
    red = write(src, "teammate-b/red/data.json", scope_json("teammate-b", "redacted", 9.0, 7200, returns=2, redact=True, size="M"))
    teamed = _scope(src, "plugin", "team-scope", cost=50.0, agent_s=3600, size="", team="qa-white, qa-black", start="2026-10-07T09:00:00Z", end="2026-10-07T18:00:00Z")
    states = {
        "teams": ([big, teamed], "goal", "plugin-q4", []),
        "normal": ([big, mid, small], "goal", "plugin-q4", []),
        "mixed": ([big, mid, small, run, stale, old], "goal", "plugin-q4", [ro.entry(squad="plugin", name="token-coach-v2", command="squad-report token-coach-v2")]),
        "files": ([big, mid, run, stale, old, junk, dup_old, dup_new, red], "files", "Teammates' scopes", []),
        "single": ([run], "goal", "plugin-q4", []),
        "empty": ([], "goal", "plugin-q4", []),
    }
    paths = {}
    for st, (files, form, title, extra) in states.items():
        d = out / st
        entries = ro.file_entries(files) + extra
        data = ro.build_rollup(entries, title, form, d, NOW, goal_name=title if form == "goal" else None)
        (d).mkdir(parents=True, exist_ok=True)
        (d / "data.json").write_text(json.dumps(data), encoding="utf-8")
        ro.render(data, d)
        paths[st] = d / "index.html"
    bad = out / "error"
    bad.mkdir(parents=True, exist_ok=True)
    data = json.loads((out / "normal" / "data.json").read_text(encoding="utf-8"))
    data["kind"] = "scope"
    ro.render(data, bad)
    paths["error"] = bad / "index.html"
    return paths


def dump_dom(path, width=1440):
    r = subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--virtual-time-budget=3000", "--window-size=%d,900" % width,
                        "--dump-dom", Path(path).as_uri()], capture_output=True, timeout=90)
    return r.stdout.decode("utf-8", "replace")


def body(dom):
    return re.sub(r"<(script|style|noscript)\b.*?</\1>", "", dom, flags=re.S)


def text(dom):
    dom = re.sub(r"<(script|style)\b.*?</\1>", " ", dom, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", dom))


@unittest.skipUnless(CHROME, "no Chrome installed")
class RollupUi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.paths = build_states(cls.tmp.name)
        cls.dom = {k: dump_dom(v) for k, v in cls.paths.items()}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def n(self, st, cls):
        return self.dom[st].count('class="%s"' % cls)

    def test_no_script_error_and_rendered(self):
        for st, dom in self.dom.items():
            self.assertFalse("Uncaught" in dom, st)
            self.assertTrue('id="app"' in dom, st)
            self.assertTrue(('<header class="page">' in dom) or st == "error", st)

    def test_normal_header_nav_kpis_no_banners(self):
        d, t = self.dom["normal"], text(self.dom["normal"])
        d = body(d)
        self.assertIn("goal rollup", t)
        self.assertIn("complete", t)
        self.assertIn("3 scopes · 3 done", t)
        self.assertIn("Generated", t)
        self.assertFalse('class="banner' in d, "banner in a clean goal")
        self.assertEqual(d.count('class="card kpi'), 6)
        for w in ("Overview", "Scopes", "Share", "Roles", "When"):
            self.assertIn(">%s</a>" % w, d)
        self.assertIn("Worth a look", t)
        self.assertEqual(d.count('<button class="dg"'), 4)
        self.assertIn("Total · 3 of 3", t)

    def test_scopes_table_columns_and_default_sort(self):
        d = self.dom["normal"]
        for c in ("Scope", "Status", "Elapsed", "Agent-time by bucket", "Cost · share", "Tokens", "Tasks passed", "Returns (FAIL)", "PO wait", "Attributed", "Report"):
            self.assertIn(">%s</th>" % c, d)
        self.assertIn('aria-sort="descending">Cost · share', d)
        self.assertLess(d.index("win-compat"), d.index("per-scope-squads"))
        self.assertIn("flag", d)  # flagged row edge
        self.assertIn("no report", d)  # built from files: no report.html beside them

    def test_mixed_partial_banners_and_rows(self):
        d, t = self.dom["mixed"], text(self.dom["mixed"])
        self.assertIn("partial", t)
        self.assertIn("Totals are partial.", t)
        self.assertIn("Mixed price tables.", t)
        self.assertIn("Still running:", t)
        self.assertIn("Stale data:", t)
        self.assertIn("running · partial", t)
        self.assertIn("No data.json yet.", t)
        self.assertIn("old schema", t)
        self.assertIn("Total · 5 of 7", t)
        self.assertIn("2d 3h old", t)

    def test_files_form(self):
        t = text(self.dom["files"])
        self.assertIn("Teammates' scopes", t)
        self.assertIn("from files", t)
        self.assertIn("skipped", t)
        self.assertIn("unreadable", t)
        self.assertIn("This file could not be read (not JSON).", t)
        self.assertIn("Older copy of the same squad and scope", t)

    def test_single_hides_worth_a_look_and_share_has_one_segment(self):
        d, t = self.dom["single"], text(self.dom["single"])
        self.assertNotIn("Worth a look", t)
        self.assertEqual(d.count("<h2>Share by scope</h2>"), 1)

    def test_empty_state(self):
        d, t = self.dom["empty"], text(self.dom["empty"])
        self.assertIn("No scopes to roll up.", t)
        self.assertEqual(d.count('class="card kpi'), 6)
        self.assertIn("No share to show.", t)
        self.assertIn("Nothing to cross yet.", t)
        self.assertIn("No scopes.", t)
        self.assertNotIn("complete", t)
        self.assertNotIn("Worth a look", t)

    def test_error_state(self):
        t = text(self.dom["error"])
        self.assertIn("The rollup data could not be read", t)
        self.assertIn('kind "rollup" expected.', t)
        self.assertIn("squad-report plugin-q4", t)
        self.assertNotIn('class="sections"', self.dom["error"])

    def test_no_innerhtml_and_self_contained(self):
        html = self.paths["normal"].read_text(encoding="utf-8")
        self.assertNotIn("innerHTML", html)
        self.assertNotRegex(html, r"https?://")
        self.assertNotRegex(html, r"\b(src|href)=[\"'](?!#)")

    def test_xss_plant_is_text(self):
        with tempfile.TemporaryDirectory() as t:
            a = write(t, "x/data.json", scope_json(PLANT, PLANT, 1.0, 100, title=PLANT, returns=1, reason=PLANT))
            b = write(t, "y/data.json", scope_json("sq", "ok", 1.0, 100))
            o = Path(t) / "o"
            data = ro.build_rollup(ro.file_entries([a, b]), PLANT, "files", o, NOW)
            o.mkdir(parents=True, exist_ok=True)
            ro.render(data, o)
            dom = dump_dom(o / "index.html")
            self.assertNotIn("<img src=x", dom)
            self.assertNotIn("<svg onload", dom)
            self.assertIn("&lt;/script&gt;", dom)


@unittest.skipUnless(CHROME, "no Chrome installed")
class RollupTeamChip(unittest.TestCase):
    """Ticket 09 (AC 23): an old row shows its recorded size, a team row its team; the folder is served over http, server stopped by PID."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.paths = build_states(cls.tmp.name)
        cls.port = _free_port()
        cls.srv = subprocess.Popen([sys.executable, "-m", "http.server", str(cls.port), "--bind", "127.0.0.1", "--directory", cls.tmp.name],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cls.pid = cls.srv.pid
        cls.addClassCleanup(cls._stop)
        _wait_port(cls.port)
        r = subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--virtual-time-budget=3000", "--window-size=1440,900",
                            "--dump-dom", "http://127.0.0.1:%d/teams/index.html" % cls.port], capture_output=True, timeout=90)
        cls.dom = r.stdout.decode("utf-8", "replace")

    @classmethod
    def _stop(cls):
        os.kill(cls.pid, signal.SIGTERM)
        cls.srv.wait(timeout=10)

    def test_rows_show_size_or_team(self):
        self.assertFalse("Uncaught" in self.dom)
        t = text(self.dom)
        self.assertRegex(t, r"win-compat · plugin L done")
        self.assertRegex(t, r"team-scope · plugin qa-white, qa-black done")
        self.assertNotRegex(t, r"win-compat · plugin qa-")
        self.assertNotRegex(t, r"team-scope · plugin [SML] done")
        self.assertFalse("size ?" in t)


def _free_port():
    import socket
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_port(port, tries=100):
    import socket
    import time
    for _ in range(tries):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("server did not start")


if __name__ == "__main__":
    unittest.main()
