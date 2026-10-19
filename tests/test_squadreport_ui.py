"""Browser DOM checks of the squad-report page (headless Chrome --dump-dom). Skips with a message when Chrome is missing.

Layout numbers are CSS-string asserts here; pixel/screenshot checks are done by QA with playwright-cli.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "bin"))
import report_ui_fixtures as fxs  # noqa: E402
import squadreport_html as html  # noqa: E402

CHROME = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
CSS = open(os.path.join(HERE, "..", "templates", "report", "report.css"), encoding="utf-8").read()


def dump_dom(data, width=1440, height=900):
    """DOM text of the rendered page (a Chrome headless run on a temp file)."""
    with tempfile.TemporaryDirectory() as d:
        path = html.render_scope(data, d)
        r = subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=3000",
                            "--window-size=%d,%d" % (width, height), "--dump-dom", "file://" + path],
                           capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr[-500:]
    body = r.stdout[r.stdout.index("<body"):]
    return re.sub(r"<script.*?</script>", "", body, flags=re.S)


def rule(sel):
    m = re.search(r"(?:^|\})\s*%s\{([^}]*)\}" % re.escape(sel), CSS)
    return m.group(1) if m else ""


class ShellCss(unittest.TestCase):
    def test_centred_column(self):
        r = rule("main")
        self.assertIn("max-width:1280px", r)
        self.assertIn("margin:auto", r)
        self.assertIn("padding:14px 24px 60px", r)

    def test_pill_nav_sticky(self):
        self.assertIn("position:sticky", rule("nav.sections"))
        self.assertIn("flex-wrap:wrap", rule("nav.sections"))
        self.assertIn("border-radius:14px", rule("nav.sections a"))
        self.assertIn("#E8820E25", CSS)

    def test_chip_colours_as_mock(self):
        self.assertIn("background:var(--bg);color:var(--muted)", rule(".chip"))
        self.assertIn(".chip.done{background:#368A1E18;border-color:var(--work);color:var(--work)}", CSS)
        self.assertIn(".chip.run{background:#E8820E22;border-color:var(--mango)", CSS)

    def test_narrow_padding(self):
        self.assertIn("@media(max-width:760px){main,header.page{padding-left:12px;padding-right:12px}", CSS)


class OverviewCss(unittest.TestCase):
    def test_grids(self):
        self.assertIn("minmax(min(360px,100%),1fr)", rule(".kpis"))
        self.assertIn("minmax(min(250px,100%),1fr)", rule(".digest"))
        self.assertIn("minmax(min(340px,100%),1fr)", rule(".two"))
        self.assertIn("flex-wrap:wrap", rule(".legend"))


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser DOM test skipped")
class OverviewDom(unittest.TestCase):
    def test_kpis_digest_blocks_no_banner(self):
        d = fxs.base()
        d["digest"] = [{"id": "k%d" % i, "kind": "k", "weight": 1, "text": "Item %d" % i, "value": 1, "unit": "x",
                        "target": {"view": "tasks", "id": "07"} if i % 2 else None} for i in range(8)]
        dom = dump_dom(d)
        sec = dom[dom.index('id="overview"'):]
        self.assertEqual(len(re.findall(r'<div class="card[ "]', sec[:sec.index('class="digest"')])), 6)
        self.assertEqual(len(re.findall(r"<li>", sec[sec.index('class="digest"'):sec.index('class="two"')])), 8)
        self.assertIn('class="two"', dom)
        self.assertIn("Longest blocks", dom)
        self.assertIn("By iteration", dom)

    def test_longest_blocks_table_po_chip(self):
        d = fxs.base()
        d["agents"][0]["segments"] = [[0, 600, "b", None, "PO"], [700, 900, "b", None, "qa"]]
        dom = dump_dom(d)
        blk = dom[dom.index("Longest blocks"):dom.index("By iteration")]
        self.assertEqual(re.findall(r"<th[^>]*>([^<]*)</th>", blk), ["Who", "Waited on", "Task", "For"])
        self.assertIn('<span class="chip po">PO</span>', blk)
        self.assertEqual(blk.count("<tr>"), 3)

    def test_reason_sub_line(self):
        d = fxs.base()
        d["digest"] = [{"id": "m", "kind": "most_returns", "weight": 1, "text": 'Task 07 came back 3 times (3 returns in all): "tests missing"',
                        "value": 3, "unit": "count", "target": {"view": "returns", "id": "07"}}]
        dom = dump_dom(d)
        self.assertIn("<small>\"tests missing\"</small>", dom)


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser DOM test skipped")
class ShellDom(unittest.TestCase):
    def test_header_pills_and_rollup_link(self):
        dom = dump_dom(fxs.f_e_goal_link()[0])
        self.assertIn('<header class="page">', dom)
        self.assertIn("Generated ", dom)
        self.assertIn("Derived from transcripts, gaps classified by what ends them", dom)
        self.assertIn("Scope report · ", dom)
        self.assertEqual(len(re.findall(r'<nav class="sections"[^>]*>(?:<a [^>]*>[^<]*</a>){5}</nav>', dom)), 1)
        self.assertIn("<main>", dom)
        links = re.findall(r'<a href="([^"#][^"]*)"', dom)
        self.assertEqual(links, ["../../../goals/g1/report/report.html"])
        self.assertIn("Rollup: g1 goal →", dom)
        self.assertNotRegex(links[0], r"^[a-z]+:")

    def test_no_link_without_rollup_href(self):
        dom = dump_dom(fxs.f_e_goal_no_rollup()[0])
        self.assertNotIn("Rollup:", dom)
        self.assertEqual(re.findall(r'<a href="([^"#][^"]*)"', dom), [])

    def test_unsafe_href_not_linked(self):
        d, _ = fxs.f_e_goal_link()
        d["scope"]["rollup_href"] = "javascript:alert(1)"
        self.assertNotIn("Rollup:", dump_dom(d))
        d["scope"]["rollup_href"] = "https://evil/x.html"
        self.assertNotIn("Rollup:", dump_dom(d))


if __name__ == "__main__":
    unittest.main()
