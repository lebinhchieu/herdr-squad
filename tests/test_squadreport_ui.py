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
JS = open(os.path.join(HERE, "..", "templates", "report", "report.js"), encoding="utf-8").read()
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

    def test_chips_in_table_cells_keep_a_gap(self):
        self.assertIn("margin-left:6px", rule(".chip"))

    def test_narrow_padding(self):
        self.assertIn("@media(max-width:760px){main,header.page{padding-left:12px;padding-right:12px}", CSS)


class OverviewCss(unittest.TestCase):
    def test_grids(self):
        self.assertIn("minmax(min(360px,100%),1fr)", rule(".kpis"))
        self.assertIn("minmax(min(250px,100%),1fr)", rule(".digest"))
        self.assertIn("minmax(min(340px,100%),1fr)", rule(".two"))
        self.assertIn("flex-wrap:wrap", rule(".legend"))

    def test_matrix_row_label_one_background_each(self):
        line = [l for l in CSS.splitlines() if ".mx td.rl,.mx th.rl{" in l][0]
        self.assertEqual(line.count("background:"), 2)
        self.assertEqual(len(re.findall(r"\.mx th\.rl\{[^}]*background", line)), 1)
        self.assertEqual(len(re.findall(r"\.mx td\.rl\{[^}]*background", line)), 1)
        self.assertIn(".mx td.rl{background:#fff}", line)  # mock colour
        self.assertIn(".mx th.rl{background:var(--panel)}", line)

    def test_section_h2_16px(self):
        self.assertIn("section h2{margin:8px 0;font-size:16px}", CSS)

    def test_digest_card_rules_merged(self):
        self.assertEqual(len(re.findall(r"\.digest button,\.digest>li>div\{", CSS)), 1)
        self.assertIn("display:flex", rule(".digest button,.digest>li>div"))

    def test_escalation_singular_in_js(self):
        self.assertIn('" escalation" + (po.count === 1 ? "" : "s")', JS)


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

    def test_digest_sub_lines_not_raw_targets(self):
        d = fxs.base()
        kinds = [("top_cost_task", "tasks", "07"), ("idle_share", "timeline", "idle"), ("top_cost_role", "roles", "dev"),
                 ("scope_overhead", "matrix", "overhead"), ("po_wait", "waits", "po"), ("attribution_low", "matrix", "overhead")]
        d["digest"] = [{"id": k, "kind": k, "weight": 1, "text": "T " + k, "value": 1, "unit": "x", "target": {"view": v, "id": i}}
                       for k, v, i in kinds]
        dom = dump_dom(d)
        dg = dom[dom.index('class="digest"'):dom.index('class="two"')]
        for raw in ("timeline idle", "roles dev", "tasks 07", "waits po", "matrix overhead"):
            self.assertNotIn(">" + raw + "<", dg)
        self.assertEqual(len(re.findall(r"<small>", dg)), 6)

    def test_returns_card_opens_task_drawer(self):
        self.assertIn('target.view === "returns") && target.id && taskById(target.id)) { scrollTo("tasks"); openTask', JS)

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


def banners(dom):
    dom = re.sub(r"<noscript>.*?</noscript>", "", dom, flags=re.S)
    return re.findall(r'<div class="banner (\w+)"[^>]*>(.*?)</div></div>', dom, flags=re.S)


def text(frag):
    return re.sub(r"<[^>]+>", "", frag).lstrip("!i")


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser DOM test skipped")
class BannersDom(unittest.TestCase):
    def test_f_a_closed_retired_agent_no_banner(self):
        d, exp = fxs.f_a_retired_with_transcript()
        dom = dump_dom(d)
        self.assertEqual(banners(dom), [])
        for t in exp["absent_text"]:
            self.assertNotIn(t, dom)
        self.assertIn("dev-x", dom)
        self.assertNotIn('class="chip run"', dom[dom.index('id="roles"'):dom.index('id="grid"')])

    def test_f_b_only_missing_banner(self):
        d, _ = fxs.f_b_retired_no_transcript()
        bs = banners(dump_dom(d))
        self.assertEqual([k for k, _ in bs], ["warn"])
        self.assertIn("dev-y", text(bs[0][1]))
        self.assertNotIn("still running", text(bs[0][1]))

    def test_f_c_flag_banner_numbers_from_data(self):
        d, exp = fxs.f_c_eight_returns()
        dom = dump_dom(d)
        bs = banners(dom)
        self.assertEqual([k for k, _ in bs], ["bad"])
        self.assertTrue(text(bs[0][1]).startswith(exp["banner_text_start"]), text(bs[0][1]))
        self.assertIn(">Task 04</a>", bs[0][1])
        self.assertIn("8 \u2691", dom)

    def test_flag_banner_plural_and_order_independent(self):
        d, _ = fxs.f_c_eight_returns()
        d["tasks"].append(fxs._task("05", 4))
        d["totals"]["returns"] = 12
        t = text(banners(dump_dom(d))[0][1])
        self.assertTrue(t.startswith("2 tasks reached 3 or more returns (Task 04: 3, Task 05: 4) of 12 in all."), t)

    def test_f_d_running_partial_and_live(self):
        d, _ = fxs.f_d_running_live()
        dom = dump_dom(d)
        self.assertEqual([k for k, _ in banners(dom)], ["info"])
        self.assertIn("still running", dom)

    def test_banner_order_missing_then_flag(self):
        d, _ = fxs.f_c_eight_returns()
        d["roles"][0]["transcript_found"] = False
        self.assertEqual([k for k, _ in banners(dump_dom(d))], ["warn", "bad"])

    def test_closed_scope_with_other_partial_reason_not_running(self):
        d, _ = fxs.f_b_retired_no_transcript()
        self.assertNotIn("Partial:", dump_dom(d))


class TabsCss(unittest.TestCase):
    def test_mock_values(self):
        self.assertIn("border-radius:10px", rule(".frame"))
        self.assertIn("background:#fff", rule(".frame"))
        self.assertIn("text-transform:uppercase", rule("th"))
        self.assertIn("min-width:22px", rule(".pill"))
        self.assertIn("width:min(460px,100vw)", rule(".drawer"))
        self.assertIn("translateX(105%)", rule(".drawer"))
        self.assertIn("border-radius:10px", rule(".tl"))
        self.assertIn("position:sticky", rule(".mx td.rl,.mx th.rl"))
        self.assertIn("th[aria-sort=descending]::after", CSS)

    def test_no_dark_background(self):
        self.assertNotRegex(CSS, r"background:#[0-3][0-9A-Fa-f]{5}\b")

    def test_timeline_svg_no_url_in_js(self):
        self.assertNotRegex(JS, r"https?://")


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser DOM test skipped")
class TabsDom(unittest.TestCase):
    def test_tasks_table_columns_sort_and_overhead_last(self):
        dom = dump_dom(fxs.f_c_eight_returns()[0])
        sec = dom[dom.index('id="tasks"'):dom.index('id="roles"')]
        heads = re.findall(r"<th[^>]*>([^<]*)</th>", sec)
        self.assertEqual(heads, ["Task", "Title", "Iter", "Dev", "Status", "Returns (FAIL)", "Time by bucket", "Cycle",
                                 "Review wait", "Tokens", "Cost", "Rework"])
        self.assertIn('aria-sort="descending"', sec)
        self.assertEqual(len(re.findall(r'<span class="pill', sec)), 5)
        self.assertIn('<span class="pill r" title="3 or more returns: flagged">3 \u2691</span>', sec)
        self.assertIn('<tr class="flag"', sec)
        self.assertLess(sec.rindex("<tr "), sec.index("Scope overhead"))
        self.assertIn('aria-pressed="false"', sec)

    def test_roles_grid_timeline_render(self):
        dom = dump_dom(fxs.f_c_eight_returns()[0])
        self.assertIn('<table class="mx">', dom)
        self.assertIn('id="mx"', dom)
        self.assertIn("<svg", dom[dom.index('id="timeline"'):])
        self.assertIn("PO wait", dom)
        self.assertIn("blocking, waiting on the PO", dom)
        self.assertIn('<aside class="drawer"', dom)

    def test_missing_role_row_chip(self):
        d, _ = fxs.f_b_retired_no_transcript()
        sec = dump_dom(d)
        sec = sec[sec.index('id="roles"'):sec.index('id="grid"')]
        self.assertIn('<span class="chip warn">no transcript</span>', sec)

    def test_empty_states(self):
        d = fxs.base()
        d["sources"]["transcripts"] = 0
        d["totals"].update(agent_s=0, wall_s=0)
        d.update(tasks=[], agents=[], matrix=[], digest=[], iterations=[], roles=[])
        dom = dump_dom(d)
        for t in ("No tasks yet.", "No roles.", "Nothing to cross yet.", "No timeline."):
            self.assertIn(t, dom)

    def test_error_state_single_card(self):
        d = fxs.base()
        d["schema_version"] = 3
        dom = dump_dom(d)
        self.assertIn("The report data could not be read", dom)
        self.assertIn("schema_version 3 not supported.", dom)
        self.assertIn("squad-report &lt;scope&gt;", dom)
        self.assertNotIn('id="tasks"', dom)

    def test_drawer_open_and_close(self):
        self.assertIn('if (e.key === "Escape") closeDrawer()', JS)
        self.assertIn('drawerEl.classList.remove("open")', JS)
        self.assertIn('querySelectorAll("tr.sel,td.sel")', JS)


class ReturnOneFixes(unittest.TestCase):
    """qa-b F1-F5 of ticket 17."""

    def test_space_and_enter_open_rows_and_cells(self):
        self.assertEqual(JS.count('e.key === "Enter" || e.key === " "'), 3)  # task/role rows, grid cell, list rows
        self.assertIn("r.onclick(); } }", JS)

    def test_lane_labels_use_role(self):
        self.assertIn("function shortLane(name, mc)", JS)
        self.assertIn("roleOf(name)", JS)
        self.assertIn("name.length > mc ? shortLane(name, mc) : name", JS)

    def test_empty_kpis(self):
        d = fxs.base()
        d["sources"]["transcripts"] = 0
        d["totals"].update(agent_s=0, wall_s=0)
        d.update(tasks=[], agents=[], matrix=[], digest=[], iterations=[])
        for r in d["roles"]:
            r["transcript_found"] = False
        dom = dump_dom(d)
        self.assertIn("none yet", dom)
        self.assertIn("agents \u00b7 bars are shares of agent-time", dom)
        self.assertRegex(dom, r"Attributed to tasks.*?class=\"bar")

    def test_banner_bold_wraps(self):
        r = rule(".banner b")
        self.assertIn("overflow-wrap:anywhere", r)
        self.assertNotIn("nowrap", r)

    def test_dev_label_short_with_title(self):
        self.assertIn('t.dev.replace(/^[^-]+-/, "")', JS)
        self.assertIn("{ title: t.dev }", JS)

    def test_tasks_table_width_budget(self):
        self.assertIn("width:90px", rule("td .bar") or re.search(r"td \.bar\{[^}]*\}", CSS).group(0))
        self.assertIn("white-space:normal", rule("#tasks th"))
        self.assertIn("padding:6px 8px", rule("th,td"))


if __name__ == "__main__":
    unittest.main()
