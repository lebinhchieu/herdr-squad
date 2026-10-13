"""Seam A, BRD-15: the side panel, Jump to pane and the notes link, in headless Chromium.

Each test runs the real `bin/squad-board --replay` on a copy of the page fixture with a stub `herdr`
first on its PATH, opens the real page and reads the panel the way a person (or the blackbox QA) would:
through `#side-panel` and its hooks. Skipped, with the reason, where node, playwright-core or a Chromium
build is missing (the same rule as the page tests).
"""
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from board_fixture import Fixture
from test_board_page import (PAGE_FIXTURE, PIXELS_JS, colour_near, find_chrome, find_playwright)

DRIVER_JS = r"""
const readline = require('readline');
const { chromium } = require(process.env.PLAYWRIGHT_CORE);
let browser, context, page, events;
const ops = {
  async launch({ chrome }) { browser = await chromium.launch(chrome ? { executablePath: chrome } : {}); },
  async open({ url, width = 1280, height = 800 }) {
    if (context) await context.close();
    events = { dialogs: [], errors: [], responses: [] };
    context = await browser.newContext({ viewport: { width, height } });
    context.on('response', (r) => events.responses.push({ url: r.url(), status: r.status() }));
    page = await context.newPage();
    page.on('dialog', (d) => { events.dialogs.push(d.message()); d.dismiss(); });
    page.on('pageerror', (e) => events.errors.push(e.message));
    page.on('console', (m) => { if (m.type() === 'error') events.errors.push(m.text()); });
    await page.goto(url);
  },
  async eval({ js }) { return await page.evaluate(js); },
  async wait({ js, timeout = 8000 }) {
    const end = Date.now() + timeout;
    while (!(await page.evaluate(js))) {
      if (Date.now() > end) throw new Error('timed out waiting for ' + js);
      await page.waitForTimeout(50);
    }
  },
  async click({ x, y }) { await page.mouse.click(x, y); },
  async press({ key }) { await page.keyboard.press(key); },
  async clickSelector({ selector }) { await page.click(selector); },
  async popup({ selector }) {
    const [tab] = await Promise.all([context.waitForEvent('page'), page.click(selector)]);
    await tab.waitForLoadState();
    const out = { url: tab.url(), text: await tab.evaluate(() => document.body.innerText) };
    await tab.close();
    return out;
  },
  async sleep({ ms }) { await page.waitForTimeout(ms); },
  async events() { return events; },
  async close() { if (browser) await browser.close(); process.exit(0); },
};
readline.createInterface({ input: process.stdin }).on('line', async (line) => {
  const msg = JSON.parse(line);
  let reply;
  try {
    const value = await ops[msg.op](msg);
    reply = { value: value === undefined ? null : value };
  } catch (e) {
    reply = { error: String(e.message).slice(0, 500) };
  }
  process.stdout.write(JSON.stringify(reply) + '\n');
});
"""

STUB = """#!{python}
import sys, time
with open({calls!r}, "a") as f:
    f.write(" ".join(sys.argv[1:]) + "\\n")
if {mode!r} == "fail":
    sys.stderr.write("herdr: boom\\n")
    sys.exit(3)
if {mode!r} == "slow":
    time.sleep(1.5)
"""

PANEL_JS = """(() => {
  const p = document.getElementById('side-panel');
  return {hidden: p.hidden, agent: p.dataset.agent === undefined ? null : p.dataset.agent, text: p.textContent,
    field: Object.fromEntries([...p.querySelectorAll('[data-field]')].map((e) => [e.dataset.field, e.textContent])),
    messages: [...p.querySelectorAll('#panel-messages li')].map((li) => li.textContent),
    jump: {disabled: document.getElementById('jump-button').disabled,
           text: document.getElementById('jump-result').textContent,
           label: document.getElementById('jump-button').textContent},
    notes: {href: document.getElementById('notes-link').getAttribute('href'),
            target: document.getElementById('notes-link').target, rel: document.getElementById('notes-link').rel,
            text: document.getElementById('notes-link').textContent}};
})()"""
OPEN_JS = "(() => { const p = document.getElementById('side-panel'); return !!p && !p.hidden; })()"
CLOSED_JS = "(() => { const p = document.getElementById('side-panel'); return !!p && p.hidden; })()"

MANAGER = {"agent": "manager", "role": "Manager", "scope": "all"}


def duration(seconds):
    """E19: 12s, 4m 05s, 1h 02m."""
    if seconds >= 3600:
        return "%dh %02dm" % (seconds // 3600, seconds % 3600 // 60)
    return "%dm %02ds" % (seconds // 60, seconds % 60) if seconds >= 60 else "%ds" % seconds


class Driver:
    def __init__(self, core, chrome):
        self.script = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False)
        self.script.write(DRIVER_JS)
        self.script.close()
        self.proc = subprocess.Popen(["node", self.script.name], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     universal_newlines=True, env=dict(os.environ, PLAYWRIGHT_CORE=core),
                                     cwd=tempfile.gettempdir())
        self.call("launch", chrome=chrome)

    def call(self, op, **args):
        self.proc.stdin.write(json.dumps(dict(args, op=op)) + "\n")
        self.proc.stdin.flush()
        reply = json.loads(self.proc.stdout.readline())
        if "error" in reply:
            raise AssertionError("%s: %s" % (op, reply["error"]))
        return reply["value"]

    def eval(self, js):
        return self.call("eval", js=js)

    def wait(self, js, timeout=8000):
        self.call("wait", js=js, timeout=timeout)

    def close(self):
        try:
            self.proc.stdin.write(json.dumps({"op": "close"}) + "\n")
            self.proc.stdin.flush()
            self.proc.wait(10)
        except (OSError, subprocess.TimeoutExpired):
            self.proc.kill()
        os.unlink(self.script.name)


class PanelCase(unittest.TestCase):
    driver = None

    @classmethod
    def setUpClass(cls):
        core, chrome = find_playwright(), find_chrome()
        if not (core and chrome and shutil.which("node")):
            raise unittest.SkipTest("browser tests need node, playwright-core (PLAYWRIGHT_CORE) and a Chromium "
                                    "build (CHROME_PATH); found node=%s core=%s chrome=%s"
                                    % (shutil.which("node"), core, chrome))
        cls.driver = Driver(core, chrome)

    @classmethod
    def tearDownClass(cls):
        if cls.driver:
            cls.driver.close()

    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.close)
        shutil.copytree(str(PAGE_FIXTURE), str(self.fx.root), dirs_exist_ok=True)
        self.now = (PAGE_FIXTURE / "now.txt").read_text().strip()
        self.tmp = Path(tempfile.mkdtemp(prefix="board-panel-"))
        self.addCleanup(shutil.rmtree, str(self.tmp), True)
        self.calls = self.tmp / "calls"
        self.srv = None

    def start(self, mode="ok", fx=None):
        """The server with a stub herdr (mode ok, fail or slow) as the only thing on PATH."""
        bindir = self.tmp / "bin"
        bindir.mkdir(exist_ok=True)
        stub = bindir / "herdr"
        stub.write_text(STUB.format(python=sys.executable, calls=str(self.calls), mode=mode))
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
        self.srv = (fx or self.fx).start(now=self.now, env={"PATH": str(bindir)})
        return self.srv

    def open(self, token=True, **kw):
        self.driver.call("open", url=self.srv.base + "/" + ("?token=" + self.srv.token if token else ""), **kw)
        self.driver.wait("document.querySelector('#connection-state').dataset.state === 'live'")
        self.driver.wait("document.querySelectorAll('#columns li').length > 0")

    def herdr_calls(self):
        return self.calls.read_text().splitlines() if self.calls.exists() else []

    def card_xy(self, agent, width=1280):
        """Page position of an agent's header card (E20 layout rules)."""
        cols = self.driver.eval("[...document.querySelectorAll('#columns li')].map((li) => "
                                "({agent: li.dataset.agent, stub: li.dataset.collapsed === 'true'}))")
        stubs = sum(1 for c in cols if c["stub"])
        col_w = max(84, (width - 230 - 16 - 24 * stubs) / (len(cols) - stubs))
        x = 16
        for c in cols:
            w = 24 if c["stub"] else col_w
            if c["agent"] == agent:
                return x + w / 2, 133
            x += w
        raise AssertionError(agent)

    def click_header(self, agent, width=1280):
        x, y = self.card_xy(agent, width)
        self.driver.call("click", x=x, y=y)

    def panel(self):
        return self.driver.eval(PANEL_JS)

    def column(self, agent):
        return next(c for c in self.srv.state()["columns"] if c["agent"] == agent)

    def messages_of(self, agent, n=3):
        rows = [r for r in self.srv.state()["rows"]
                if r["kind"] == "message" and agent in (r["from"], r["to"])]
        return rows[-n:]


class ContentTest(PanelCase):
    def test_a_header_click_opens_the_panel_with_the_agents_facts(self):
        self.start()
        self.open()
        self.assertEqual(self.driver.eval(CLOSED_JS), True)
        self.assertIsNone(self.panel()["agent"])
        self.click_header("dev-shop-3")  # blocked, so the red total shows
        self.driver.wait(OPEN_JS)
        col, panel = self.column("dev-shop-3"), self.panel()
        self.assertEqual(panel["agent"], "dev-shop-3")
        for word in (col["agent"], col["role"], col["pod"], col["model"], "status: blocked"):
            self.assertIn(word, panel["text"])
        self.assertEqual(panel["field"]["context"], "{:,}".format(col["context_tokens"]))
        self.assertEqual(panel["field"]["tokens-in"], "{:,}".format(col["tokens_in"]))
        self.assertEqual(panel["field"]["tokens-out"], "{:,}".format(col["tokens_out"]))
        self.assertEqual(panel["field"]["wakes"], str(col["wakes"]))
        self.assertEqual(panel["field"]["working"], duration(col["working_s"]))
        self.assertEqual(panel["field"]["blocked"], duration(col["blocked_s"]))
        self.assertEqual(self.driver.eval("getComputedStyle(document.querySelector('[data-field=blocked]')).color"),
                         "rgb(219, 59, 34)")

    def test_the_status_line_takes_the_status_colour(self):
        self.start()
        self.open()
        for agent, rgb in (("dev-shop-3", "rgb(219, 59, 34)"), ("qab-shop", "rgb(12, 138, 128)"),
                           ("tech-shop", "rgb(169, 156, 134)")):
            self.click_header(agent)
            self.driver.wait("document.getElementById('side-panel').dataset.agent === %s" % json.dumps(agent))
            self.assertEqual(self.driver.eval("getComputedStyle(document.getElementById('panel-status')).color"), rgb)

    def test_the_card_sits_under_the_headers_and_left_of_the_task_card(self):
        self.start()
        self.open(width=1600)
        self.click_header("tech-shop", 1600)
        self.driver.wait(OPEN_JS)
        rect = self.driver.eval("(() => { const r = document.getElementById('side-panel').getBoundingClientRect();"
                                " return [r.top, r.width, innerWidth - r.right]; })()")
        self.assertEqual(rect, [176, 360, 230])

    def test_durations_read_as_seconds_minutes_and_hours(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([MANAGER, {"agent": "dev-a"}, {"agent": "dev-b"}, {"agent": "dev-c"}])
        fx.iteration(1)
        for agent, seconds in (("dev-a", 12), ("dev-b", 65), ("dev-c", 3725)):
            fx.activity(agent=agent, status="working", ts="2026-10-12T10:00:00.000Z")
            fx.activity(agent=agent, status="idle", ts="2026-10-12T%02d:%02d:%02d.000Z" % (
                10 + seconds // 3600, seconds % 3600 // 60, seconds % 60))
        fx.activity(agent="manager", status="idle", ts="2026-10-12T10:00:00.000Z")
        self.start(fx=fx)
        self.open()
        for agent, wanted in (("dev-a", "12s"), ("dev-b", "1m 05s"), ("dev-c", "1h 02m")):
            self.click_header(agent)
            self.driver.wait("document.getElementById('side-panel').dataset.agent === %s" % json.dumps(agent))
            self.assertEqual(self.panel()["field"]["working"], wanted)

    def test_the_type_label_takes_the_message_type_colour(self):
        colours = {"ASK": "rgb(42, 109, 192)", "ANSWER": "rgb(74, 143, 224)", "BLOCKED": "rgb(219, 59, 34)",
                   "DECISION": "rgb(158, 122, 0)", "HANDIN": "rgb(154, 64, 207)", "PASS": "rgb(54, 138, 30)",
                   "FAIL": "rgb(206, 29, 108)", "STATUS": "rgb(133, 122, 104)", None: "rgb(133, 122, 104)",
                   "constructor": "rgb(133, 122, 104)"}
        fx = Fixture()
        self.addCleanup(fx.close)
        agents = ["dev-%d" % i for i in range(len(colours))]
        fx.roster([MANAGER] + [{"agent": a} for a in agents])
        fx.iteration(1)
        fx.activity(agent="manager", status="idle")
        for agent, type_ in zip(agents, colours):
            fx.activity(agent=agent, status="idle")
            fx.message(**{"from": "manager", "to": agent, "type": type_, "task": "T-1", "text": "x", "iteration": 1})
        self.start(fx=fx)
        self.open()
        for agent, (type_, rgb) in zip(agents, colours.items()):
            self.click_header(agent)
            self.driver.wait("document.getElementById('side-panel').dataset.agent === %s" % json.dumps(agent))
            self.assertEqual(self.driver.eval("(() => { const s = document.querySelector('#panel-messages .panel-type');"
                                              " return [s.textContent, getComputedStyle(s).color]; })()"),
                             [type_ or "msg", rgb], type_)

    def test_the_last_three_messages_match_the_log(self):
        self.start()
        self.open()
        self.click_header("tech-shop")
        self.driver.wait(OPEN_JS)
        shown = self.panel()["messages"]
        wanted = self.messages_of("tech-shop")
        self.assertEqual(len(shown), 3)
        for text, row in zip(shown, wanted):
            arrow = "→ " + row["to"] if row["from"] == "tech-shop" else "← " + row["from"]
            self.assertIn(row["type"] or "msg", text)
            self.assertIn(arrow, text)
            self.assertIn(row["task"] or "", text)
            self.assertIn(row["text"], text)

    def test_context_tokens_in_and_out_are_three_different_figures(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([MANAGER, {"agent": "dev-t"}])
        fx.iteration(1)
        fx.activity(agent="manager", status="idle")
        fx.activity(agent="dev-t", status="idle")
        fx.herdr({"dev-t": "11111111-2222-3333-4444-555555555555"})
        usage = lambda mid, tin, tout: {"type": "assistant", "message": {"id": mid, "model": "m", "role": "assistant", "usage": {
            "input_tokens": tin, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": tout}}}
        fx.transcript("claude", "p", "11111111-2222-3333-4444-555555555555",
                      [usage("a", 1000, 70), usage("b", 3000, 50)])
        self.start(fx=fx)
        self.open()
        self.click_header("dev-t")
        self.driver.wait(OPEN_JS)
        self.assertEqual([self.panel()["field"][k] for k in ("context", "tokens-in", "tokens-out")],
                         ["3,000", "4,000", "120"])

    def test_null_tokens_and_no_blocked_time_read_plainly(self):
        self.start()
        self.open()
        self.click_header("dev-auth-1")
        self.driver.wait(OPEN_JS)
        panel = self.panel()
        self.assertEqual([panel["field"][k] for k in ("context", "tokens-in", "tokens-out")], ["—", "—", "—"])
        self.assertEqual(panel["field"]["blocked"], "0s")
        self.assertEqual(self.driver.eval("document.querySelector('[data-field=blocked]').style.color"), "")
        self.assertIn("pod auth · —", panel["text"])  # no model known

    def test_an_agent_with_no_messages_shows_an_empty_list(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([MANAGER, {"agent": "dev-shop-1"}])
        fx.iteration(1)
        fx.activity(agent="manager", status="idle")
        fx.activity(agent="dev-shop-1", status="idle")
        self.start(fx=fx)
        self.open()
        self.click_header("dev-shop-1")
        self.driver.wait(OPEN_JS)
        self.assertEqual(self.panel()["messages"], [])

    def test_the_selected_header_has_the_mango_outline(self):
        self.start()
        self.open()
        x, _ = self.card_xy("tech-shop")
        edge = (x - 30, 99, x + 30, 103)  # the top edge of the card (HEADER_Y = 100)
        before = colour_near(self.driver.eval(PIXELS_JS % ", ".join(str(v) for v in edge)), "E8820E", 12)
        self.click_header("tech-shop")
        self.driver.wait(OPEN_JS)
        self.driver.call("sleep", ms=150)
        after = colour_near(self.driver.eval(PIXELS_JS % ", ".join(str(v) for v in edge)), "E8820E", 12)
        self.assertEqual(before, 0)
        self.assertGreater(after, 40)
        self.click_header("tech-shop")
        self.driver.call("sleep", ms=150)
        self.assertEqual(colour_near(self.driver.eval(PIXELS_JS % ", ".join(str(v) for v in edge)), "E8820E", 12), 0)


class OpenCloseTest(PanelCase):
    def test_another_header_replaces_the_content(self):
        self.start()
        self.open()
        self.click_header("tech-shop")
        self.driver.wait(OPEN_JS)
        self.click_header("qaw-shop")
        self.driver.wait("document.getElementById('side-panel').dataset.agent === 'qaw-shop'")
        panel = self.panel()
        self.assertIn("QA whitebox", panel["text"])
        self.assertNotIn("tech-shop ", panel["text"].split("LAST MESSAGES")[0])

    def test_escape_the_close_button_and_a_second_click_each_close_it(self):
        self.start()
        self.open()
        for close in (lambda: self.driver.call("press", key="Escape"),
                      lambda: self.driver.call("clickSelector", selector="#panel-close"),
                      lambda: self.click_header("tech-shop")):
            self.click_header("tech-shop")
            self.driver.wait(OPEN_JS)
            close()
            self.driver.wait(CLOSED_JS)
            self.assertIsNone(self.panel()["agent"])

    def test_escape_with_nothing_open_does_nothing_and_a_click_beside_the_cards_opens_nothing(self):
        self.start()
        self.open()
        self.driver.call("press", key="Escape")
        self.driver.call("click", x=5, y=133)
        self.driver.call("click", x=600, y=400)
        self.driver.call("sleep", ms=100)
        self.assertEqual(self.driver.eval(CLOSED_JS), True)
        self.assertEqual(self.driver.call("events")["errors"], [])

    def test_a_retired_stub_cannot_be_opened(self):
        self.start()
        self.open()
        self.click_header("dev-shop-0")
        self.driver.call("sleep", ms=100)
        self.assertEqual(self.driver.eval(CLOSED_JS), True)

    def test_the_panel_closes_when_its_agent_leaves_the_state(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([MANAGER, {"agent": "dev-shop-1"}])
        fx.iteration(1)
        fx.activity(agent="manager", status="idle")
        fx.activity(agent="dev-shop-1", status="idle")
        self.start(fx=fx)
        self.open()
        self.click_header("dev-shop-1")
        self.driver.wait(OPEN_JS)
        fx.roster([MANAGER])
        (fx.root / "activity.jsonl").write_text(
            '{"ts": "2026-10-12T10:00:01.000Z", "agent": "manager", "status": "idle", "iteration": 1}\n')
        self.driver.wait(CLOSED_JS)
        self.assertEqual(self.driver.call("events")["errors"], [])
        fx.roster([MANAGER, {"agent": "dev-shop-1"}])
        fx.activity(agent="dev-shop-1", status="idle", ts="2026-10-12T10:00:02.000Z")
        self.driver.wait("document.querySelectorAll('#columns li').length === 2")
        self.driver.call("sleep", ms=300)
        self.assertEqual(self.driver.eval(CLOSED_JS), True)  # it does not reopen by itself
        self.click_header("manager")
        self.driver.wait(OPEN_JS)
        self.assertEqual(self.panel()["agent"], "manager")

    def test_updates_keep_the_panel_in_place_without_rebuilding_what_did_not_change(self):
        self.start()
        self.open(height=420)  # short window: the panel scrolls
        self.click_header("tech-shop")
        self.driver.wait(OPEN_JS)
        self.driver.eval("""(() => {
          const p = document.getElementById('side-panel');
          window.__kept = { value: p.querySelector('[data-field=context]'), item: p.querySelector('#panel-messages li'),
            text: p.querySelector('[data-field=context]').firstChild };
          p.scrollTop = 40;
          window.__scrolled = p.scrollTop;
        })()""")
        scrolled = self.driver.eval("window.__scrolled")
        self.assertGreater(scrolled, 0)
        # a message between two other agents: the state changes, this agent's panel does not
        self.fx.message(**{"from": "dev-auth-1", "to": "tech-auth", "type": "ASK", "task": "AUTH-09",
                           "text": "unrelated", "iteration": 3})
        self.driver.wait("document.querySelectorAll('#columns li').length > 0 && "
                         "document.getElementById('side-panel').dataset.agent === 'tech-shop'")
        self.driver.call("sleep", ms=1500)
        self.assertEqual(self.driver.eval("""(() => {
          const p = document.getElementById('side-panel');
          return [p.scrollTop, window.__kept.value === p.querySelector('[data-field=context]'),
                  window.__kept.item === p.querySelector('#panel-messages li'),
                  window.__kept.text === p.querySelector('[data-field=context]').firstChild];
        })()"""), [scrolled, True, True, True])
        # a message to this agent: the list follows
        self.fx.message(**{"from": "manager", "to": "tech-shop", "type": "DECISION", "task": "CART-77",
                           "text": "brand new", "iteration": 3, "ts": "2026-10-12T11:16:45.000Z"})
        self.driver.wait("document.getElementById('side-panel').textContent.includes('brand new')")
        self.assertEqual(self.driver.eval("document.getElementById('side-panel').dataset.agent"), "tech-shop")
        self.assertEqual(len(self.panel()["messages"]), 3)


class NotesLinkTest(PanelCase):
    def setUp(self):
        super().setUp()
        self.fx.write("roles/tech-shop.notes.md", "# notes of tech-shop\n<img src=x onerror=alert(1)>\n")

    def test_the_link_opens_the_notes_file_as_text_in_a_new_tab(self):
        self.start()
        self.open()
        self.click_header("tech-shop")
        self.driver.wait(OPEN_JS)
        notes = self.panel()["notes"]
        self.assertEqual(notes["href"], "/notes/tech-shop?token=" + self.srv.token)
        self.assertEqual((notes["target"], notes["rel"], notes["text"]),
                         ("_blank", "noopener noreferrer", "notes.md ↗"))
        tab = self.driver.call("popup", selector="#notes-link")
        self.assertEqual(tab["url"], self.srv.base + notes["href"])
        self.assertEqual(tab["text"].strip(), "# notes of tech-shop\n<img src=x onerror=alert(1)>")
        self.assertEqual(self.driver.call("events")["dialogs"], [])
        self.assertEqual(self.panel()["agent"], "tech-shop")  # the page is untouched

    def test_an_agent_without_a_notes_file_gets_a_plain_404_and_the_page_keeps_working(self):
        self.start()
        self.open()
        self.click_header("qaw-shop")
        self.driver.wait(OPEN_JS)
        tab = self.driver.call("popup", selector="#notes-link")
        self.assertEqual(tab["text"], "not found")
        statuses = [r["status"] for r in self.driver.call("events")["responses"] if "/notes/" in r["url"]]
        self.assertEqual(statuses, [404])
        self.click_header("tech-shop")
        self.driver.wait("document.getElementById('side-panel').dataset.agent === 'tech-shop'")

    def test_a_page_opened_without_the_token_links_to_a_refused_notes_request(self):
        self.start()
        self.open(token=False)
        self.click_header("tech-shop")
        self.driver.wait(OPEN_JS)
        self.assertEqual(self.panel()["notes"]["href"], "/notes/tech-shop")
        tab = self.driver.call("popup", selector="#notes-link")
        self.assertEqual(tab["text"], "forbidden")
        statuses = [r["status"] for r in self.driver.call("events")["responses"] if "/notes/" in r["url"]]
        self.assertEqual(statuses, [403])

    def test_the_link_token_is_encoded_into_the_query(self):
        self.start()
        self.driver.call("open", url=self.srv.base + "/?token=a%26b%3Dc%20d")
        self.driver.wait("document.querySelectorAll('#columns li').length > 0")
        self.click_header("tech-shop")
        self.driver.wait(OPEN_JS)
        self.assertEqual(self.panel()["notes"]["href"], "/notes/tech-shop?token=a%26b%3Dc%20d")


class JumpTest(PanelCase):
    def jump(self, agent="dev-shop-1"):
        self.click_header(agent)
        self.driver.wait(OPEN_JS)
        self.driver.call("clickSelector", selector="#jump-button")

    def test_jump_runs_exactly_agent_focus_name_and_says_jumped(self):
        self.start()
        self.open()
        self.jump()
        self.driver.wait("document.getElementById('jump-result').textContent === 'Jumped'")
        self.assertEqual(self.herdr_calls(), ["agent focus dev-shop-1"])
        self.assertEqual(self.driver.call("events")["errors"], [])
        # the result belongs to that agent: another panel starts clean
        self.click_header("dev-shop-2")
        self.driver.wait("document.getElementById('side-panel').dataset.agent === 'dev-shop-2'")
        self.assertEqual(self.panel()["jump"]["text"], "")
        self.assertEqual(self.herdr_calls(), ["agent focus dev-shop-1"])

    def test_the_button_is_disabled_while_the_request_is_in_flight(self):
        self.start(mode="slow")
        self.open()
        self.jump()
        self.driver.wait("document.getElementById('jump-button').disabled")
        self.assertEqual(self.panel()["jump"]["text"], "Jumping…")
        self.driver.wait("document.getElementById('jump-result').textContent === 'Jumped'")
        self.assertEqual(self.panel()["jump"]["disabled"], False)
        self.assertEqual(len(self.herdr_calls()), 1)

    def test_a_failing_herdr_shows_the_status_and_error_and_the_page_keeps_working(self):
        self.start(mode="fail")
        self.open()
        self.jump()
        self.driver.wait("document.getElementById('jump-result').textContent.startsWith('502')")
        self.assertEqual(self.panel()["jump"]["text"], "502 herdr exited with status 3")
        self.assertEqual(self.panel()["jump"]["disabled"], False)
        self.assertEqual(self.driver.eval("getComputedStyle(document.getElementById('jump-result')).color"),
                         "rgb(219, 59, 34)")
        self.click_header("tech-shop")  # still alive
        self.driver.wait("document.getElementById('side-panel').dataset.agent === 'tech-shop'")
        self.driver.call("press", key="Escape")
        self.driver.wait(CLOSED_JS)

    def test_a_wrong_token_in_the_url_shows_403(self):
        self.start()
        self.driver.call("open", url=self.srv.base + "/?token=wrong")
        self.driver.wait("document.querySelectorAll('#columns li').length > 0")
        self.jump("tech-shop")
        self.driver.wait("document.getElementById('jump-result').textContent.startsWith('403')")
        self.assertEqual(self.herdr_calls(), [])

    def test_a_server_that_is_gone_says_so(self):
        self.start()
        self.open()
        self.click_header("tech-shop")
        self.driver.wait(OPEN_JS)
        self.srv.stop()
        self.driver.call("clickSelector", selector="#jump-button")
        self.driver.wait("document.getElementById('jump-result').textContent.startsWith('Jump failed')")
        self.assertEqual(self.panel()["jump"]["disabled"], False)

    def test_without_a_token_in_the_url_the_button_is_disabled_with_an_explanation(self):
        self.start()
        self.open(token=False)
        self.click_header("tech-shop")
        self.driver.wait(OPEN_JS)
        jump = self.panel()["jump"]
        self.assertEqual(jump["disabled"], True)
        self.assertIn("token", jump["text"])
        self.driver.call("eval", js="document.getElementById('jump-button').click()")
        self.driver.call("sleep", ms=300)
        self.assertEqual(self.herdr_calls(), [])

    def test_an_empty_token_counts_as_none(self):
        self.start()
        self.driver.call("open", url=self.srv.base + "/?token=")
        self.driver.wait("document.querySelectorAll('#columns li').length > 0")
        self.click_header("tech-shop")
        self.driver.wait(OPEN_JS)
        self.assertEqual(self.panel()["jump"]["disabled"], True)

    def test_for_a_retired_agent_the_button_is_disabled_with_an_explanation(self):
        # one event in the viewed iteration gives the retired agent a full column, so it can be opened
        self.fx.activity(agent="dev-shop-0", status="working", iteration=3, ts="2026-10-12T11:17:00.000Z")
        self.start()
        self.open()
        self.click_header("dev-shop-0")
        self.driver.wait(OPEN_JS)
        panel = self.panel()
        self.assertEqual(panel["jump"]["disabled"], True)
        self.assertIn("retired", panel["jump"]["text"])
        self.assertIn("· retired", panel["text"])
        self.driver.call("eval", js="document.getElementById('jump-button').click()")
        self.driver.call("sleep", ms=300)
        self.assertEqual(self.herdr_calls(), [])
        self.click_header("dev-shop-1")  # a live one beside it is enabled
        self.driver.wait("document.getElementById('side-panel').dataset.agent === 'dev-shop-1'")
        self.assertEqual(self.panel()["jump"]["disabled"], False)
        self.assertEqual(self.panel()["jump"]["text"], "")


class UntrustedTextTest(PanelCase):
    def long_message(self):
        self.fx.message(**{"from": "dev-shop-4", "to": "qaw-shop", "type": "HANDIN", "task": "CART-99",
                           "text": "A" * 5000 + "B" * 5000, "iteration": 3, "msg_id": "long-1",
                           "ts": "2026-10-12T11:16:00.000Z"})

    def test_a_10000_character_message_is_clipped_and_show_more_expands_it(self):
        self.long_message()
        self.start()
        self.open()
        self.click_header("qaw-shop")
        self.driver.wait(OPEN_JS)
        shown = self.panel()["messages"][-1]
        self.assertLess(len(shown), 250)
        self.assertIn("show more", shown)
        self.assertIn("…", shown)
        self.driver.call("clickSelector", selector="#panel-messages li:last-child .panel-more")
        self.driver.wait("document.querySelector('#panel-messages li:last-child').textContent.length > 10000")
        expanded = self.panel()["messages"][-1]
        self.assertIn("A" * 5000 + "B" * 5000, expanded)
        self.assertIn("show less", expanded)
        self.driver.call("clickSelector", selector="#panel-messages li:last-child .panel-more")
        self.driver.wait("document.querySelector('#panel-messages li:last-child').textContent.length < 250")

    def test_an_expanded_message_stays_expanded_across_updates(self):
        self.long_message()
        self.start()
        self.open()
        self.click_header("qaw-shop")
        self.driver.wait(OPEN_JS)
        self.driver.call("clickSelector", selector="#panel-messages li:last-child .panel-more")
        self.driver.wait("document.querySelector('#panel-messages li:last-child').textContent.length > 10000")
        self.fx.message(**{"from": "dev-auth-1", "to": "tech-auth", "type": "ASK", "task": "AUTH-09",
                           "text": "unrelated", "iteration": 3})
        self.driver.call("sleep", ms=1500)
        self.assertGreater(len(self.panel()["messages"][-1]), 10000)

    def test_the_clip_edge_is_140_characters(self):
        for i, (length, clipped) in enumerate(((140, False), (141, True))):
            self.fx.message(**{"from": "dev-shop-4", "to": "qaw-shop", "type": "HANDIN", "task": "CART-9%d" % i,
                               "text": "z" * length, "iteration": 3, "msg_id": "edge-%d" % i,
                               "ts": "2026-10-12T11:16:0%d.000Z" % i})
        self.start()
        self.open()
        self.click_header("qaw-shop")
        self.driver.wait(OPEN_JS)
        edge, over = self.panel()["messages"][-2:]
        self.assertIn("z" * 140, edge)
        self.assertNotIn("…", edge)
        self.assertNotIn("show more", edge)
        self.assertIn("…", over)
        self.assertIn("show more", over)
        self.assertNotIn("z" * 141, over)

    def test_the_clip_never_cuts_a_surrogate_pair(self):
        self.fx.message(**{"from": "dev-shop-4", "to": "qaw-shop", "type": "HANDIN", "task": "CART-98",
                           "text": "a" * 139 + "\U0001F600" + "b" * 30, "iteration": 3, "msg_id": "emoji-1",
                           "ts": "2026-10-12T11:16:00.000Z"})
        self.start()
        self.open()
        self.click_header("qaw-shop")
        self.driver.wait(OPEN_JS)
        self.assertIn("show more", self.panel()["messages"][-1])
        self.assertEqual(self.driver.eval(
            "/[\\ud800-\\udbff](?![\\udc00-\\udfff])|(?<![\\ud800-\\udbff])[\\udc00-\\udfff]/"
            ".test(document.querySelector('#panel-messages li:last-child').textContent)"), False)

    def test_short_messages_have_no_show_more(self):
        self.start()
        self.open()
        self.click_header("tech-shop")
        self.driver.wait(OPEN_JS)
        self.assertEqual(self.driver.eval("document.querySelectorAll('.panel-more').length"), 0)

    def test_hostile_text_shows_as_plain_text(self):
        self.start()
        self.open()
        hostile = "<img src=x onerror=alert(1)>"
        row = next(r for r in self.srv.state()["rows"] if r["kind"] == "message" and r["text"] == hostile)
        self.click_header(row["from"])
        self.driver.wait(OPEN_JS)
        # it may not be among the last three of the sender: write it as a fresh last message then
        self.fx.message(**{"from": row["from"], "to": row["to"], "type": "ASK", "task": "AUTH-98",
                           "text": hostile, "iteration": 3, "ts": "2026-10-12T11:16:30.000Z"})
        self.driver.wait("document.getElementById('side-panel').textContent.includes('onerror=alert(1)')")
        self.assertEqual(self.driver.eval("document.querySelectorAll('#side-panel img, #side-panel script').length"), 0)
        self.assertEqual(self.driver.eval("document.querySelectorAll('img').length"), 0)
        self.driver.call("sleep", ms=200)
        self.assertEqual(self.driver.call("events")["dialogs"], [])

    def test_hostile_agent_task_and_type_are_text_too(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([MANAGER, {"agent": "dev-shop-1"}])
        fx.iteration(1)
        fx.activity(agent="manager", status="idle")
        fx.activity(agent="dev-shop-1", status="idle")
        fx.message(**{"from": "manager", "to": "dev-shop-1", "type": "<b>X</b>", "task": "<i>T-1</i>",
                      "text": "<svg onload=alert(1)>", "iteration": 1})
        fx.message(**{"from": "dev-shop-1", "to": "manager", "type": "constructor", "task": None,
                      "text": "__proto__", "iteration": 1})
        self.start(fx=fx)
        self.open()
        self.click_header("dev-shop-1")
        self.driver.wait(OPEN_JS)
        self.assertEqual(self.driver.eval("document.querySelectorAll('#side-panel b, #side-panel i, #side-panel svg').length"), 0)
        shown = self.panel()["messages"]
        self.assertIn("<b>X</b> ← manager <i>T-1</i> <svg onload=alert(1)>", shown[0])
        self.assertIn("constructor → manager __proto__", shown[1])
        self.assertEqual(self.driver.call("events")["dialogs"], [])

    def test_the_panel_has_no_control_that_answers_or_prompts(self):
        self.start()
        self.open()
        self.click_header("tech-shop")
        self.driver.wait(OPEN_JS)
        controls = self.driver.eval("""[...document.querySelectorAll('button, a, input, textarea, select, form, [contenteditable]')]
          .filter((e) => document.getElementById('side-panel').contains(e)).map((e) => e.id || e.className)""")
        self.assertEqual(controls, ["panel-close", "jump-button", "notes-link"])
        self.assertEqual(self.driver.eval("document.querySelectorAll('input, textarea, form, [contenteditable]').length"), 0)


if __name__ == "__main__":
    unittest.main()
