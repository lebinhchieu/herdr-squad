"""TAB-04: the board shows the display label (`columns[i].label`), the address name stays `agent`."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
import squadlabel as sl  # noqa: E402

from board_fixture import Fixture, make_scoped
from test_board_events import Stream

NOW = "2026-10-12T12:00:00Z"
MGR = {"agent": "manager", "role": "Manager", "scope": "all"}


def labels(state):
    return {c["agent"]: c["label"] for c in state["columns"]}


class Base(unittest.TestCase):
    def setUp(self):
        self.fx = None

    def tearDown(self):
        if self.fx:
            self.fx.close()

    def flat(self, rows):
        self.fx = Fixture()
        self.fx.roster([MGR] + rows)
        return self.fx

    def state(self, **kw):
        return self.fx.start(now=NOW, **kw).state()


class StoredLabelTest(Base):
    def test_label_is_built_from_the_store_and_agent_is_the_address(self):
        fx = self.flat([{"agent": "d1", "role": "Dev", "scope": "s"}, {"agent": "d2", "role": "Dev", "scope": "s"}])
        sl.write_entry(fx.root, "manager", "manager", None, "")
        sl.write_entry(fx.root, "d1", "dev", 1, "TAB-04")
        sl.write_entry(fx.root, "d2", "dev", 2, "<img src=x onerror=alert(1)> \"q\"")
        st = self.state()
        self.assertEqual(labels(st)["manager"], "🦀 Manager")
        self.assertEqual(labels(st)["d1"], sl.build_label("dev", 1, "TAB-04"))
        self.assertEqual(labels(st)["d2"], sl.build_label("dev", 2, "<img src=x onerror=alert(1)> \"q\""))
        self.assertEqual([c["agent"] for c in st["columns"]], ["manager", "d1", "d2"])

    def test_needs_you_text_uses_the_label_and_keeps_address_and_id(self):
        fx = self.flat([{"agent": "d2", "role": "Dev", "scope": "s"}])
        sl.write_entry(fx.root, "d2", "dev", 2, "TAB-04")
        fx.activity(agent="d2", status="blocked")
        item = next(i for i in self.state()["needs_you"] if i["kind"] == "blocked")
        self.assertEqual((item["text"], item["agent"]), ("🤖 Dev 2 · TAB-04 is blocked", "d2"))
        self.assertTrue(item["id"].startswith("blocked:d2:"))

    def test_bad_json_in_the_store_falls_back(self):
        fx = self.flat([{"agent": "d1", "role": "Dev", "scope": "s"}])
        fx.write("labels/d1.json", "{nope")
        self.assertEqual(labels(self.state())["d1"], "🤖 Dev")


class FallbackTest(Base):
    def test_roster_role_and_numbers_only_for_two_in_a_pod(self):
        self.flat([{"agent": "d1", "role": "Dev", "scope": "s"}, {"agent": "d2", "role": "Dev", "scope": "s"},
                   {"agent": "q", "role": "QA whitebox", "scope": "s"}, {"agent": "lone", "role": "Dev", "scope": "t"},
                   {"agent": "old", "role": "Tech Lead", "scope": "s", "status": "retired"}])
        self.fx.activity(agent="ghost-s-1", status="working")  # seen only in a log: no role
        got = labels(self.state())
        self.assertEqual(got["manager"], "🦀 Manager")
        self.assertEqual((got["d1"], got["d2"]), ("🤖 Dev 1", "🤖 Dev 2"))
        self.assertEqual((got["q"], got["lone"], got["old"]), ("🤖 QA Whitebox", "🤖 Dev", "🤖 Tech Lead"))
        self.assertEqual(got["ghost-s-1"], "ghost-s-1")
        self.assertTrue(all(got.values()))


class ScopedTest(Base):
    def test_per_scope_layout_reads_each_home_and_ignores_strangers_and_done(self):
        self.fx = fx = make_scoped()
        sl.write_entry(fx.root / "scopes" / "a", "x-dev-a", "dev", None, "TAB-9")
        sl.write_entry(fx.root / "scopes" / "a", "not-on-roster", "dev", 3, "ghost")
        sl.write_entry(fx.root / "scopes" / "b", "x-dev-a", "dev", 7, "other home")  # not b's agent
        sl.write_entry(fx.root / "scopes" / "_done" / "x", "gone-dev", "dev", None, "x")
        st = self.state()
        got = labels(st)
        self.assertEqual(got["x-dev-a"], "🤖 Dev · TAB-9")
        self.assertEqual(got["g-mgr"], "🦀 Manager")
        self.assertEqual(got["x-qaw-a"], "🤖 QA Whitebox")
        self.assertNotIn("not-on-roster", got)
        self.assertNotIn("gone-dev", got)


class RefreshTest(Base):
    def test_rewriting_a_label_file_sends_a_new_state(self):
        fx = self.flat([{"agent": "d1", "role": "Dev", "scope": "s"}])
        sl.write_entry(fx.root, "d1", "dev", None, "old")
        server = fx.start(now=NOW)
        s = Stream(server)
        self.addCleanup(s.close)
        first = s.state(5)
        self.assertEqual(labels(first)["d1"], "🤖 Dev · old")
        sl.write_entry(fx.root, "d1", "dev", None, "new")
        later = s.state_where(lambda st: labels(st)["d1"] == "🤖 Dev · new")
        self.assertIsNotNone(later, "the new label never arrived")
        sl.write_entry(fx.root, "d1", "dev", None, "")
        self.assertIsNotNone(s.state_where(lambda st: labels(st)["d1"] == "🤖 Dev"))


try:
    from test_board_panel import PanelCase
except ImportError:  # pragma: no cover
    PanelCase = None

HOSTILE = '<img src=x onerror=alert(1)> "q" \'x\' <script>alert(2)</script>'


@unittest.skipIf(PanelCase is None, "page helpers unavailable")
class PageTest(PanelCase if PanelCase else object):
    def test_header_and_panel_show_the_label_and_keep_the_address(self):
        sl.write_entry(self.fx.root, "dev-shop-3", "dev", 2, HOSTILE)
        sl.write_entry(self.fx.root, "manager", "manager", None, "")
        self.start()
        want = sl.build_label("dev", 2, HOSTILE)
        self.open()
        self.driver.wait("[...document.querySelectorAll('#columns li')].some((li) => li.textContent.includes(%s))"
                         % json.dumps(want[:20]))
        item = self.driver.eval("(() => { const li = document.querySelector('#columns li[data-agent=dev-shop-3]');"
                                " return li.textContent; })()")
        self.assertTrue(item.startswith(want), item)
        self.click_header("dev-shop-3")
        self.driver.wait("!document.getElementById('side-panel').hidden")
        got = self.driver.eval("({name: document.getElementById('panel-name').textContent,"
                               " addr: document.getElementById('panel-address').textContent,"
                               " agent: document.getElementById('side-panel').dataset.agent,"
                               " href: document.getElementById('notes-link').getAttribute('href'),"
                               " injected: document.querySelectorAll('img, script[src]').length})")
        self.assertEqual((got["name"], got["addr"], got["agent"]), (want, "dev-shop-3", "dev-shop-3"))
        self.assertIn("/notes/dev-shop-3", got["href"])
        self.assertEqual(got["injected"], 0)
        events = self.driver.call("events")
        self.assertEqual((events["dialogs"], events["errors"]), ([], []))

    def test_needs_you_row_reads_the_label(self):
        sl.write_entry(self.fx.root, "dev-shop-3", "dev", 2, "TAB-04")  # dev-shop-3 is blocked in the fixture
        self.start()
        self.open()
        text = self.driver.eval("[...document.querySelectorAll('#needs-you li')].map((li) => li.textContent)")
        self.assertTrue(any("🤖 Dev 2 · TAB-04 is blocked" in t for t in text), text)


class SymlinkTest(unittest.TestCase):
    def test_board_runs_from_a_symlink_in_another_cwd(self):
        import os, subprocess, tempfile
        with tempfile.TemporaryDirectory() as d:
            link = Path(d) / "board-link"
            link.symlink_to(Path(__file__).resolve().parent.parent / "bin" / "squad-board")
            r = subprocess.run([sys.executable, str(link), "--help"], cwd=d, capture_output=True, text=True, timeout=20)
            self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
