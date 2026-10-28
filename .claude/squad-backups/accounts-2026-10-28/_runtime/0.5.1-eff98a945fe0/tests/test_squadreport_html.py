import copy
import json
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "bin"))
import report_fixtures as rf  # noqa: E402
import squadreport_build as build  # noqa: E402
import squadreport_embed as emb  # noqa: E402
import squadreport_html as html  # noqa: E402

PLANT = ['</script><img src=x onerror=alert(1)>', '"><svg onload=1>']
DATA_RE = re.compile(r'<script type="application/json" id="report-data">(.*?)</script>', re.S)


def real_data():
    fx = rf.Fixture()
    try:
        rf.tasks_scope(fx)
        old = os.environ.get("CLAUDE_CONFIG_DIR")
        os.environ["CLAUDE_CONFIG_DIR"] = str(fx.claude)
        try:
            return build.build(fx.home, fx.squad, plugin_root=rf.PLUGIN_ROOT)
        finally:
            if old is None:
                os.environ.pop("CLAUDE_CONFIG_DIR")
            else:
                os.environ["CLAUDE_CONFIG_DIR"] = old
    finally:
        fx.close()


def embedded(text):
    m = DATA_RE.findall(text)
    assert len(m) == 1
    return json.loads(m[0])


class Structure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = real_data()
        cls.text = html.render(cls.data)

    def test_single_file_no_external_url(self):
        t = self.text
        self.assertNotRegex(t, r"https?://")
        self.assertNotRegex(t, r'(?:src|href)\s*=\s*["\'](?!#)')
        self.assertNotIn("__CSS__", t)
        self.assertNotIn("__JS__", t)
        self.assertNotIn("__DATA__", t)

    def test_js_never_uses_innerhtml(self):
        js = open(os.path.join(HERE, "..", "templates", "report", "report.js"), encoding="utf-8").read()
        self.assertNotIn("innerHTML", js)
        self.assertNotIn("</script", js.lower())

    def test_embedded_json_equals_data(self):
        self.assertEqual(embedded(self.text), json.loads(emb.dumps(self.data)))

    def test_render_scope_writes_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = html.render_scope(self.data, d)
            self.assertEqual(open(p, encoding="utf-8").read(), self.text)
            self.assertEqual(os.listdir(d), ["report.html"])

    def test_xss_plant_closes_script_once(self):
        d = copy.deepcopy(self.data)
        d["tasks"][0]["title"] = PLANT[0]
        d["tasks"][0]["returns_list"][0]["reason"] = PLANT[1]
        d["roles"][0]["role"] = PLANT[0]
        d["totals"]["po_wait"]["items"][0]["title"] = PLANT[1]
        t = html.render(d)
        self.assertEqual(len(re.findall(r"</script", t, re.I)), 2)  # data block and js block
        self.assertNotIn("<img src=x", t)
        self.assertEqual(embedded(t)["tasks"][0]["title"], PLANT[0])

    def test_real_build_fields_the_page_reads(self):
        d = self.data
        for t in d["tasks"]:
            for k in ("id", "status", "buckets_s", "tokens", "cost_usd", "returns", "returns_list", "review_waits", "flag"):
                self.assertIn(k, t)
        for a in d["agents"]:
            for g in a["segments"]:
                self.assertEqual(len(g), 5)
        for k in ("wall_s", "agent_s", "buckets_s", "tokens", "cost_usd", "po_wait", "attributed", "idle_s"):
            self.assertIn(k, d["totals"])

    def test_no_drawn_block_longer_than_agent_bucket_total(self):
        names = {"w": "working", "a": "waiting", "b": "blocking", "i": "idle"}
        roles = {r["name"]: r for r in self.data["roles"]}
        for a in self.data["agents"]:
            tot = roles[a["name"]]["buckets_s"]
            for s, e, b, _t, _on in a["segments"]:
                self.assertLessEqual(e - s, tot[names[b]], a["name"])

    def test_redacted_data_has_no_text(self):
        d = copy.deepcopy(self.data)
        for t in d["tasks"]:
            t["title"] = None
            for r in t["returns_list"]:
                r["reason"] = None
        t = html.render(d)
        self.assertNotIn("one blocking finding", t)
        self.assertIn("not shared", open(os.path.join(HERE, "..", "templates", "report", "report.js"), encoding="utf-8").read())

    def test_schema_mismatch_still_renders_a_file(self):
        d = {"schema_version": 3}
        self.assertEqual(embedded(html.render(d)), d)


if __name__ == "__main__":
    unittest.main()
