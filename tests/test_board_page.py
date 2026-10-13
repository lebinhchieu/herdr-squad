"""Seam A, BRD-12: GET / serves the real page, and what the page needs from the server.

The last class opens the page in headless Chromium (through node and playwright-core) and checks
what a person would see: the text mirror, pixels of the canvas, scrolling, reconnecting. It is
skipped, with the reason, where node, playwright-core or a Chromium build is missing.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

import board_fixture
from board_fixture import BIN, Fixture

PAGE_FILE = BIN.parent / "squad-board.html"
PAGE_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "board" / "page"

CSP = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; "
       "img-src data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
TOP_KEYS = {"now", "iterations", "iteration", "selected_iteration", "pods", "columns", "rows",
            "bars", "tasks", "needs_you", "live"}

# Spec "Palette" plus what tech-board allowed for the round 6 look: card, rules, dark mango, white on mango.
PALETTE = {"FCF8F1", "F4ECDD", "E7DBC8", "3E372E", "857A68", "E8820E", "0C8A80", "DB3B22", "A99C86",
           "2A6DC0", "4A8FE0", "9E7A00", "9A40CF", "368A1E", "CE1D6C", "FFFDF9", "D6CCBC", "CE7000", "FFFFFF"}

# design-iteration-2 E18, plus the one sibling of innerHTML that would be the same hole
FORBIDDEN = ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function")

SECTIONS = ["state", "layout", "header", "sequence", "tasks", "follow", "picker", "panel", "alerts", "mirror"]
# Final signatures: the page tickets 13 to 16 fill these in without renaming them.
SIGNATURES = ["loadState()", "connectStream(iteration)", "applyState(next)", "computeLayout(current, width, height)",
              "drawNeedsYou(ctx, view)", "drawPods(ctx, view)", "drawHeaders(ctx, view)",
              "drawSequence(ctx, view)", "drawTasks(ctx, view)", "updateFollow(previous, next)",
              "setupPicker(current)", "drawPanel(ctx, view)", "onHeaderClick(agent)", "checkAlerts(current)",
              "renderMirror(current)"]


def page_text():
    return PAGE_FILE.read_text(encoding="utf-8")


def rgb_triples(hex_set):
    return {tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for h in hex_set}


class PageFixtureCase(unittest.TestCase):
    """The committed page fixture, copied to a temp dir so that nothing can change it."""

    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.close)
        shutil.copytree(str(PAGE_FIXTURE), str(self.fx.root), dirs_exist_ok=True)
        self.now = (PAGE_FIXTURE / "now.txt").read_text().strip()
        self.srv = self.fx.start(now=self.now)


class RootTest(PageFixtureCase):
    def test_root_serves_the_page_file_with_its_headers(self):
        status, headers, body = self.srv.get("/")
        self.assertEqual(status, 200)
        self.assertEqual(body, PAGE_FILE.read_bytes())
        self.assertEqual(headers["content-type"], "text/html; charset=utf-8")
        self.assertEqual(headers["cache-control"], "no-store")
        self.assertEqual(headers["content-security-policy"], CSP)
        self.assertEqual(headers["referrer-policy"], "no-referrer")

    def test_other_routes_do_not_carry_the_page_policy(self):
        _, headers, _ = self.srv.get("/state")
        self.assertNotIn("content-security-policy", headers)
        self.assertNotIn("referrer-policy", headers)

    def test_token_in_the_url_does_not_change_the_page(self):
        status, _, body = self.srv.get("/?token=" + self.srv.token)
        self.assertEqual((status, body), (200, PAGE_FILE.read_bytes()))


class PageSourceTest(unittest.TestCase):
    def test_no_external_request(self):
        text = page_text()
        self.assertEqual(re.findall(r"https?://[^\s\"')]*", text), [])
        self.assertEqual(re.findall(r"(?:src|href|action)\s*=", text), [])
        self.assertNotIn("@import", text)
        self.assertNotIn("url(", text)

    def test_no_forbidden_construct(self):
        text = page_text()
        for token in FORBIDDEN:
            self.assertNotIn(token, text)

    def test_every_colour_is_in_the_palette(self):
        text = page_text()
        found = re.findall(r"#[0-9A-Fa-f]{3,8}\b", text)
        self.assertGreater(len(found), 10)  # the regexp still sees the palette
        for literal in found:
            self.assertIn(len(literal), (7, 9), literal)  # 6 digits, or 6 plus an alpha pair
            self.assertIn(literal[1:7].upper(), PALETTE, literal)
        triples = rgb_triples(PALETTE)
        # tints built at run time (tint(P.x, a)) start from the P table; this sees written-out ones
        for rgba in re.findall(r"rgba?\(\s*(\d+\s*,\s*\d+\s*,\s*\d+)", text):
            self.assertIn(tuple(int(p) for p in rgba.split(",")), triples, rgba)

    def test_sections_exist_in_order(self):
        text = page_text()
        positions = [text.find("// --- section: %s ---" % name) for name in SECTIONS]
        self.assertNotIn(-1, positions)
        self.assertEqual(positions, sorted(positions))
        self.assertIn("<!-- section: mirror -->", text)

    def test_stubs_keep_their_final_signatures(self):
        text = page_text()
        for signature in SIGNATURES:
            self.assertIn("function " + signature, text)

    def test_one_script_and_no_framework(self):
        text = page_text()
        self.assertEqual(text.count("<script"), 1)
        self.assertEqual(text.count("</script>"), 1)


class MissingPageTest(unittest.TestCase):
    """The server looks for the page next to its own (resolved) script path, on every request."""

    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.close)
        self.fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"}])
        self.bindir = Path(tempfile.mkdtemp(prefix="board-bin-"))
        self.addCleanup(shutil.rmtree, str(self.bindir), True)
        self.script = self.bindir / "squad-board"
        shutil.copy(str(BIN), str(self.script))
        self.script.chmod(0o755)

    def start(self, script):
        with mock.patch.object(board_fixture, "BIN", script):
            return self.fx.start()

    def test_missing_page_file_is_a_500_json_and_the_server_lives_on(self):
        srv = self.start(self.script)
        status, headers, body = srv.get("/")
        self.assertEqual(status, 500)
        self.assertEqual(headers["content-type"], "application/json; charset=utf-8")
        self.assertIn("error", json.loads(body))
        self.assertNotIn("content-security-policy", headers)
        self.assertNotIn(str(self.bindir), body.decode())
        self.assertEqual(srv.get("/state")[0], 200)
        self.assertEqual(srv.stderr(), "")

    def test_page_is_read_on_every_request(self):
        (self.bindir / "squad-board.html").write_text("<p>one</p>")
        srv = self.start(self.script)
        self.assertEqual(srv.get("/")[2], b"<p>one</p>")
        (self.bindir / "squad-board.html").write_text("<p>two</p>")
        self.assertEqual(srv.get("/")[2], b"<p>two</p>")
        (self.bindir / "squad-board.html").unlink()
        self.assertEqual(srv.get("/")[0], 500)

    def test_a_symlinked_script_finds_the_page_next_to_the_real_file(self):
        link_dir = Path(tempfile.mkdtemp(prefix="board-link-"))
        self.addCleanup(shutil.rmtree, str(link_dir), True)
        (link_dir / "squad-board").symlink_to(BIN)
        srv = self.start(link_dir / "squad-board")
        self.assertEqual(srv.get("/")[2], PAGE_FILE.read_bytes())

    def test_a_page_that_is_a_directory_is_a_500_json(self):
        (self.bindir / "squad-board.html").mkdir()
        srv = self.start(self.script)
        status, headers, _ = srv.get("/")
        self.assertEqual((status, headers["content-type"]), (500, "application/json; charset=utf-8"))
        self.assertEqual(srv.get("/state")[0], 200)


class StateForThePageTest(PageFixtureCase):
    def test_live_is_false_in_replay_and_the_other_keys_are_unchanged(self):
        st = self.srv.state()
        self.assertIs(st["live"], False)
        self.assertEqual(set(st), TOP_KEYS)

    def test_no_absolute_path_leaves_the_server(self):
        def strings(value):
            if isinstance(value, str):
                yield value
            elif isinstance(value, dict):
                for k, v in value.items():
                    yield k
                    yield from strings(v)
            elif isinstance(value, list):
                for v in value:
                    yield from strings(v)

        st = self.srv.state()
        for s in strings(st):
            self.assertFalse(s.startswith("/"), s)
        self.assertNotIn(str(self.fx.root), json.dumps(st))
        self.assertNotIn(os.path.expanduser("~"), json.dumps(st))


class PageFixtureTest(PageFixtureCase):
    """The committed fixture has everything the BRD-12 ticket lists."""

    def test_now_file_is_utc_and_later_than_every_record(self):
        self.assertRegex(self.now, r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        for name in ("messages.jsonl", "activity.jsonl"):
            for line in (self.fx.root / name).read_text().splitlines():
                self.assertLess(json.loads(line)["ts"], self.now)
        self.assertEqual(self.srv.state()["now"], self.now)

    def test_twelve_live_agents_in_three_pods_manager_first(self):
        st = self.srv.state()
        live = [c for c in st["columns"] if not c["retired"]]
        self.assertEqual(len(live), 12)
        self.assertEqual(live[0]["agent"], "manager")
        self.assertEqual(len(st["pods"]), 3)
        self.assertEqual(st["pods"][0]["agents"], ["manager"])

    def test_one_retired_agent_without_events(self):
        st = self.srv.state()
        retired = [c for c in st["columns"] if c["retired"]]
        self.assertEqual(len(retired), 1)
        name = retired[0]["agent"]
        for row in st["rows"]:
            self.assertNotIn(name, (row.get("agent"), row.get("from"), row.get("to")))
        self.assertEqual([b for b in st["bars"] if b["agent"] == name], [])

    def test_needs_you_has_a_blocked_agent_an_escalation_and_the_idle_manager(self):
        st = self.srv.state()
        self.assertEqual(sorted(n["kind"] for n in st["needs_you"]), ["blocked", "escalation", "manager_idle"])
        self.assertEqual([c["status"] for c in st["columns"]].count("blocked"), 1)
        manager = next(c for c in st["columns"] if c["agent"] == "manager")
        self.assertEqual(manager["status"], "idle")

    def test_a_blocked_message_between_agents_exists_but_is_not_needs_you(self):
        st = self.srv.state()
        self.assertTrue([r for r in st["rows"] if r.get("type") == "BLOCKED"])
        self.assertNotIn("BLOCKED", " ".join(n["text"] for n in st["needs_you"] if n["kind"] == "escalation"))

    def test_a_task_at_two_returns_and_the_other_states(self):
        st = self.srv.state()
        # exactly 2 once BRD-18 (one return per FAIL fan-out) is merged; this branch is based before it
        self.assertTrue(max(t["returns"] for t in st["tasks"]) >= 2)
        self.assertEqual({t["state"] for t in st["tasks"]}, {"blocked", "building", "checking", "returned", "done"})

    def test_each_fail_of_the_returned_task_goes_to_three_recipients_within_a_second(self):
        fails = [json.loads(line) for line in (self.fx.root / "messages.jsonl").read_text().splitlines()]
        fails = [m for m in fails if m["type"] == "FAIL" and m["task"] == "CART-02"]
        self.assertEqual(len(fails), 6)
        for first in (0, 3):
            batch = fails[first:first + 3]
            self.assertEqual(sorted(m["to"] for m in batch), ["dev-shop-2", "manager", "tech-shop"])
            self.assertLess((self.stamp(batch[-1]) - self.stamp(batch[0])), 1.0)

    def test_a_passed_task_is_followed_by_status_and_decision_messages_naming_the_pass(self):
        msgs = [json.loads(line) for line in (self.fx.root / "messages.jsonl").read_text().splitlines()]
        kinds = [m["type"] for m in msgs if m["task"] == "AUTH-01"]
        after_pass = kinds[kinds.index("PASS") + 1:]
        self.assertEqual(after_pass[:2], ["STATUS", "DECISION"])
        about = [m for m in msgs if m["task"] == "AUTH-01"]
        first_pass = [m["type"] for m in about].index("PASS")
        self.assertTrue(all("PASS" in m["text"] for m in about[first_pass + 1:first_pass + 3]))

    @staticmethod
    def stamp(message):
        return datetime.strptime(message["ts"], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()

    def test_three_iterations_and_about_three_hundred_rows(self):
        st = self.srv.state()
        self.assertEqual(st["iterations"], [1, 2, 3])
        self.assertTrue(250 <= len(st["rows"]) <= 350, len(st["rows"]))

    def test_gaps_open_bar_self_start_bar_and_blocked_segment(self):
        st = self.srv.state()
        gaps = [r for r in st["rows"] if r["kind"] == "gap"]
        self.assertTrue(gaps)
        self.assertTrue(all(g["seconds"] > 180 for g in gaps))
        self.assertTrue([b for b in st["bars"] if b["open"]])
        self.assertTrue([b for b in st["bars"] if b["self_start"]])
        self.assertTrue([b for b in st["bars"] if b["blocked"]])

    def test_hostile_message_text_and_an_agent_with_null_tokens(self):
        st = self.srv.state()
        texts = [r["text"] for r in st["rows"] if r["kind"] == "message"]
        self.assertIn("<img src=x onerror=alert(1)>", texts)
        nulls = [c["agent"] for c in st["columns"] if c["context_tokens"] is None and not c["retired"]]
        self.assertEqual(nulls, ["dev-auth-1"])
        self.assertTrue(all(c["context_tokens"] > 0 for c in st["columns"]
                            if not c["retired"] and c["agent"] != "dev-auth-1"))


DRIVER_JS = r"""
const readline = require('readline');
const { chromium } = require(process.env.PLAYWRIGHT_CORE);
let browser, context, page, events;
function reset(width, height, dpr) {
  events = { dialogs: [], errors: [], requests: [], times: [] };
  return browser.newContext({ viewport: { width, height }, deviceScaleFactor: dpr }).then(async (c) => {
    if (context) await context.close();
    context = c;
    page = await context.newPage();
    page.on('dialog', (d) => { events.dialogs.push(d.message()); d.dismiss(); });
    page.on('pageerror', (e) => events.errors.push(e.message));
    page.on('console', (m) => { if (m.type() === 'error') events.errors.push(m.text()); });
    page.on('request', (r) => { events.requests.push(r.url()); events.times.push(Date.now()); });
    await page.addInitScript(() => {
      window.__raf = 0;
      const original = window.requestAnimationFrame.bind(window);
      window.requestAnimationFrame = (cb) => { window.__raf++; return original(cb); };
    });
  });
}
const ops = {
  async launch({ chrome }) { browser = await chromium.launch(chrome ? { executablePath: chrome } : {}); },
  async open({ url, width = 1280, height = 800, dpr = 1, failFirst = 0 }) {
    await reset(width, height, dpr);
    let left = failFirst;  // abort the first requests for /state: a server that is not answering yet
    await page.route('**/state', (route) => (left-- > 0 ? route.abort() : route.continue()));
    await page.goto(url);
  },
  async reload() { await page.reload(); },
  async eval({ js }) { return await page.evaluate(js); },
  // polled here, not with waitForFunction: that one evaluates a string in the page, which the page's CSP forbids
  async wait({ js, timeout = 8000 }) {
    const end = Date.now() + timeout;
    while (!(await page.evaluate(js))) {
      if (Date.now() > end) throw new Error('timed out waiting for ' + js);
      await page.waitForTimeout(50);
    }
  },
  async move({ x, y }) { await page.mouse.move(x, y); },
  async viewport({ width, height }) { await page.setViewportSize({ width, height }); },
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


def find_playwright():
    for var in ("PLAYWRIGHT_CORE",):
        if os.environ.get(var):
            return os.environ[var]
    node = shutil.which("node")
    if not node:
        return None
    root = subprocess.run([node, "-e", "console.log(require('child_process').execSync('npm root -g').toString().trim())"],
                          capture_output=True, text=True).stdout.strip()
    for sub in ("@playwright/cli/node_modules/playwright-core", "playwright-core", "playwright/node_modules/playwright-core"):
        if root and (Path(root) / sub).is_dir():
            return str(Path(root) / sub)
    return None


def find_chrome():
    if os.environ.get("CHROME_PATH"):
        return os.environ["CHROME_PATH"]
    found = sorted(glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome")))
    return found[-1] if found else None


class Browser:
    """One headless Chromium, driven line by line through DRIVER_JS."""

    def __init__(self, core, chrome):
        env = dict(os.environ, PLAYWRIGHT_CORE=core)
        self.script = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False)
        self.script.write(DRIVER_JS)
        self.script.close()
        self.proc = subprocess.Popen(["node", self.script.name], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     universal_newlines=True, env=env, cwd=tempfile.gettempdir())
        self.call("launch", chrome=chrome)

    def call(self, op, **args):
        self.proc.stdin.write(json.dumps(dict(args, op=op)) + "\n")
        self.proc.stdin.flush()
        reply = json.loads(self.proc.stdout.readline())
        if "error" in reply:
            raise AssertionError("%s: %s" % (op, reply["error"]))
        return reply["value"]

    def open(self, url, **kw):
        self.call("open", url=url, **kw)
        self.wait(LIVE_JS)
        # the state is in the mirror one frame before it is on the canvas
        self.eval("new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)))")

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


LIVE_JS = "document.querySelector('#connection-state').dataset.state === 'live'"
RECONNECTING_JS = "document.querySelector('#connection-state').dataset.state === 'reconnecting'"
QUIET_CHECKIN = ("# Iteration 1\n\n## PO check-in\n- **Done (with evidence):** x\n- **Next:** y\n"
                 "- **Decisions from the PO:**\n")
CANVAS_SIZE_JS = ("(() => { const c = document.getElementById('board'); "
                  "return [c.width, c.height, c.clientWidth, c.clientHeight, innerHeight]; })()")

MIRROR_JS = """(() => {
  const lis = (sel) => [...document.querySelectorAll(sel + ' li')].map((li) => ({
    text: li.textContent, data: Object.assign({}, li.dataset)}));
  return {needs: lis('#needs-you'), count: document.querySelector('#needs-you').dataset.count,
          heading: document.querySelector('#needs-you h2').textContent,
          empty: document.querySelector('#needs-you p').textContent,
          pods: lis('#pods'), columns: lis('#columns')};
})()"""

# colour histogram {hex: pixel count} of a rectangle of the canvas, in CSS pixels
PIXELS_JS = """((x0, y0, x1, y1) => {
  const c = document.getElementById('board'), ctx = c.getContext('2d'), r = c.width / c.clientWidth;
  const d = ctx.getImageData(Math.round(x0 * r), Math.round(y0 * r), Math.round((x1 - x0) * r), Math.round((y1 - y0) * r)).data;
  const seen = {};
  for (let i = 0; i < d.length; i += 4) {
    const hex = [d[i], d[i + 1], d[i + 2]].map((v) => v.toString(16).padStart(2, '0')).join('').toUpperCase();
    seen[hex] = (seen[hex] || 0) + 1;
  }
  return seen;
})(%s)"""


def colour_near(histogram, wanted, tolerance):
    """Pixels of {hex: count} within `tolerance` per channel of the colour `wanted`."""
    target = [int(wanted[i:i + 2], 16) for i in (0, 2, 4)]
    return sum(count for hex_, count in histogram.items()
               if all(abs(int(hex_[i:i + 2], 16) - t) <= tolerance for i, t in zip((0, 2, 4), target)))


# leftmost and rightmost x (CSS px) of the pixels within `tolerance` of a colour in a rectangle, or None
EXTENT_JS = """((x0, y0, x1, y1, hex, tol) => {
  const c = document.getElementById('board'), ctx = c.getContext('2d'), r = c.width / c.clientWidth;
  const w = Math.round((x1 - x0) * r), h = Math.round((y1 - y0) * r);
  const d = ctx.getImageData(Math.round(x0 * r), Math.round(y0 * r), w, h).data;
  const want = [0, 2, 4].map((i) => parseInt(hex.slice(i, i + 2), 16));
  let lo = null, hi = null;
  for (let px = 0; px < w; px++) for (let py = 0; py < h; py++) {
    const i = (py * w + px) * 4;
    if ([0, 1, 2].every((k) => Math.abs(d[i + k] - want[k]) <= tol)) { if (lo === null) lo = px; hi = px; }
  }
  return lo === null ? null : [x0 + lo / r, x0 + (hi + 1) / r];
})(%s)"""
TEXT_WIDTH_JS = """(() => { const c = document.createElement('canvas').getContext('2d');
  c.font = %s; return c.measureText(%s).width; })()"""
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


class BrowserTestCase(PageFixtureCase):
    browser = None

    @classmethod
    def setUpClass(cls):
        core, chrome = find_playwright(), find_chrome()
        if not (core and chrome and shutil.which("node")):
            raise unittest.SkipTest("browser tests need node, playwright-core (PLAYWRIGHT_CORE) and a Chromium "
                                    "build (CHROME_PATH); found node=%s core=%s chrome=%s"
                                    % (shutil.which("node"), core, chrome))
        cls.browser = Browser(core, chrome)

    @classmethod
    def tearDownClass(cls):
        if cls.browser:
            cls.browser.close()

    def url(self, srv=None):
        return (srv or self.srv).base + "/"

    def mirror(self):
        return self.browser.eval(MIRROR_JS)

    def pixels(self, x0, y0, x1, y1):
        return self.browser.eval(PIXELS_JS % ", ".join(str(v) for v in (x0, y0, x1, y1)))

    def extent(self, x0, y0, x1, y1, colour, tolerance):
        return self.browser.eval(EXTENT_JS % ", ".join([str(x0), str(y0), str(x1), str(y1),
                                                         json.dumps(colour), str(tolerance)]))

    def text_width(self, font, text):
        return self.browser.eval(TEXT_WIDTH_JS % (json.dumps(font), json.dumps(text)))

    def small_server(self, developer_status="idle", waiting=False):
        """Two agents. By default nothing is working, blocked or waiting, so nothing animates."""
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"}, {"agent": "dev-shop-1"}])
        fx.iteration(1, QUIET_CHECKIN)
        fx.activity(agent="manager", status="idle")
        fx.activity(agent="dev-shop-1", status=developer_status)
        if waiting:
            fx.escalations([{"question": "Ship it?"}])
        return fx.start(now=self.now)

    def quiet_server(self):
        return self.small_server()

    def card(self, agent):
        """(left, width) of an agent's header card at 1280 px, from the layout rules of E20."""
        cols = self.mirror()["columns"]
        stubs = sum(1 for c in cols if c["data"]["collapsed"] == "true")
        col_w = max(84, (1280 - 230 - 16 - 24 * stubs) / (len(cols) - stubs))
        x = 16
        for c in cols:
            w = 24 if c["data"]["collapsed"] == "true" else col_w
            if c["data"]["agent"] == agent:
                return x + 4, w - 8
            x += w
        raise AssertionError(agent)


class PageTest(BrowserTestCase):
    def test_page_loads_without_errors_or_dialogs(self):
        self.browser.open(self.url())
        events = self.browser.call("events")
        self.assertEqual(events["errors"], [])
        self.assertEqual(events["dialogs"], [])

    def test_state_is_fetched_once_and_the_stream_follows_the_selected_iteration(self):
        self.browser.open(self.url())
        deadline = time.monotonic() + 5
        while True:  # the stream request follows the state response by a moment
            urls = [u.replace(self.srv.base, "") for u in self.browser.call("events")["requests"]]
            if any(u.startswith("/events") for u in urls) or time.monotonic() > deadline:
                break
            time.sleep(0.05)
        self.assertEqual([u for u in urls if u.startswith("/state")], ["/state"])
        self.assertEqual([u for u in urls if u.startswith("/events")], ["/events?iteration=3"])

    def test_the_page_follows_the_stream_when_the_squad_files_change(self):
        self.browser.open(self.url())
        self.assertEqual(self.mirror()["count"], "3")
        self.fx.escalations([{"question": "Ship it?", "answer": "A"}, {"question": "Cut coupons?"},
                             {"question": "Rename the shop?"}])
        self.browser.wait("document.querySelector('#needs-you').dataset.count === '4'")
        urls = [u.replace(self.srv.base, "") for u in self.browser.call("events")["requests"]]
        self.assertEqual([u for u in urls if u.startswith("/state")], ["/state"])

    def test_mirror_matches_state(self):
        self.browser.open(self.url())
        st = self.srv.state()
        m = self.mirror()
        self.assertEqual([n["data"]["id"] for n in m["needs"]], [n["id"] for n in st["needs_you"]])
        self.assertEqual([n["data"]["kind"] for n in m["needs"]], [n["kind"] for n in st["needs_you"]])
        self.assertEqual([n["text"] for n in m["needs"]], [n["text"] for n in st["needs_you"]])
        self.assertEqual((m["count"], m["heading"]), ("3", "Needs you · 3"))
        self.assertEqual([p["data"]["pod"] for p in m["pods"]], [p["name"] for p in st["pods"]])
        self.assertEqual([p["data"]["size"] for p in m["pods"]], [p["size"] or "" for p in st["pods"]])
        self.assertEqual([c["data"]["agent"] for c in m["columns"]], [c["agent"] for c in st["columns"]])
        for mirrored, col in zip(m["columns"], st["columns"]):
            self.assertEqual(mirrored["data"]["status"], col["status"])
            self.assertEqual(mirrored["data"]["retired"], "true" if col["retired"] else "false")
            for word in (col["agent"], col["role"], col["status"]):
                self.assertIn(word, mirrored["text"])
            tokens = "{:,}".format(col["context_tokens"]) if col["context_tokens"] is not None else "—"
            self.assertTrue(mirrored["text"].endswith(tokens), mirrored["text"])
            self.assertEqual("⛔" in mirrored["text"], col["blocked_s"] > 0)
            self.assertIn("⏱ ", mirrored["text"])

    def test_a_squad_with_nothing_waiting_says_so(self):
        self.browser.open(self.url(self.quiet_server()))
        m = self.mirror()
        self.assertEqual((m["count"], m["needs"], m["empty"]), ("0", [], "Nothing is waiting on you"))

    def test_a_blocked_message_between_agents_is_not_a_needs_you_item(self):
        self.browser.open(self.url())
        kinds = [n["data"]["kind"] for n in self.mirror()["needs"]]
        self.assertEqual(sorted(kinds), ["blocked", "escalation", "manager_idle"])
        tasks = {t["id"]: t["state"] for t in self.srv.state()["tasks"]}
        self.assertEqual(tasks["CART-03"], "blocked")  # the BLOCKED message is a task state only

    def test_manager_first_pods_in_roster_order_and_the_same_after_reload(self):
        self.browser.open(self.url())
        first = [c["data"]["agent"] for c in self.mirror()["columns"]]
        self.assertEqual(first[0], "manager")
        self.assertEqual([p["data"]["pod"] for p in self.mirror()["pods"]], ["all", "shop", "auth"])
        self.browser.call("reload")
        self.browser.wait(LIVE_JS)
        self.assertEqual([c["data"]["agent"] for c in self.mirror()["columns"]], first)

    def test_only_the_retired_agent_without_events_is_collapsed(self):
        self.browser.open(self.url())
        flags = {c["data"]["agent"]: (c["data"]["retired"], c["data"]["collapsed"]) for c in self.mirror()["columns"]}
        self.assertEqual(flags["dev-shop-0"], ("true", "true"))
        self.assertEqual([a for a, f in flags.items() if f[1] == "true"], ["dev-shop-0"])

    def test_a_retired_agent_with_events_keeps_its_full_column(self):
        self.fx.message(**{"from": "dev-shop-0", "to": "tech-shop", "ts": "2026-10-12T10:59:00.000Z",
                           "iteration": 3, "msg_id": "late-1"})
        self.fx.activity(agent="dev-shop-0", status="idle", ts="2026-10-12T10:59:01.000Z", iteration=3)
        srv = self.fx.start(now=self.now)
        self.browser.open(self.url(srv))
        flags = {c["data"]["agent"]: c["data"]["collapsed"] for c in self.mirror()["columns"]}
        self.assertEqual(flags["dev-shop-0"], "false")

    def test_twelve_columns_fit_at_1280_without_a_horizontal_scrollbar(self):
        self.browser.open(self.url(), width=1280)
        self.assertEqual(self.browser.eval("document.documentElement.scrollWidth - document.documentElement.clientWidth"), 0)

    def test_narrower_than_the_minimum_column_width_scrolls_sideways(self):
        self.browser.open(self.url(), width=900)
        self.assertGreater(self.browser.eval("document.documentElement.scrollWidth - document.documentElement.clientWidth"), 100)

    def test_canvas_is_viewport_sized_dpr_aware_and_follows_resizes(self):
        self.browser.open(self.url(), width=1280, height=800, dpr=2)
        self.assertEqual(self.browser.eval(CANVAS_SIZE_JS), [2560, 1600, 1280, 800, 800])
        self.browser.call("viewport", width=1000, height=600)
        self.browser.wait("document.getElementById('board').clientHeight === 600")
        self.assertEqual(self.browser.eval(CANVAS_SIZE_JS), [2000, 1200, 1000, 600, 600])
        self.browser.call("viewport", width=1100, height=600)  # a change of width alone
        self.browser.wait("document.getElementById('board').clientWidth === 1100")
        self.assertEqual(self.browser.eval(CANVAS_SIZE_JS), [2200, 1200, 1100, 600, 600])
        self.browser.call("viewport", width=1100, height=700)  # and of height alone
        self.browser.wait("document.getElementById('board').clientHeight === 700")
        self.assertEqual(self.browser.eval(CANVAS_SIZE_JS), [2200, 1400, 1100, 700, 700])

    def test_canvas_is_never_taller_than_the_viewport_however_many_rows(self):
        self.browser.open(self.url(), height=500)
        self.assertEqual(self.browser.eval("document.getElementById('board').clientHeight"), 500)
        self.assertGreater(self.browser.eval("document.documentElement.scrollHeight"), 500 * 5)

    def test_a_squad_without_iterations_follows_the_stream_without_a_parameter(self):
        empty = Fixture()
        self.addCleanup(empty.close)
        srv = empty.start(now=self.now)
        self.browser.open(self.url(srv))
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            urls = [u.replace(srv.base, "") for u in self.browser.call("events")["requests"]]
            if "/events" in urls:
                break
            time.sleep(0.05)
        self.assertIn("/events", urls)
        self.assertEqual(self.mirror()["columns"], [])

    def test_header_totals_are_compact_with_a_one_minute_floor_and_hours_as_h_mm(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        durations = {"dev-shop-1": 1, "dev-shop-2": 59 * 60 + 59, "dev-shop-3": 3600, "dev-shop-4": 7260,
                     "dev-shop-5": 0}
        fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"}] + [{"agent": a} for a in durations])
        fx.iteration(1, QUIET_CHECKIN)
        for i, (agent, seconds) in enumerate(durations.items()):
            if seconds:
                fx.activity(agent=agent, status="working", ts="2026-10-12T08:00:00.000Z")
                end = 8 * 3600 + seconds
                fx.activity(agent=agent, status="idle", ts="2026-10-12T%02d:%02d:%02d.000Z" % (end // 3600, end % 3600 // 60, end % 60))
        self.browser.open(self.url(fx.start(now=self.now)))
        shown = {c["data"]["agent"]: c["text"].split(" \u00b7 ")[3] for c in self.mirror()["columns"]}
        self.assertEqual(shown["dev-shop-1"], "\u23f1 1m")
        self.assertEqual(shown["dev-shop-2"], "\u23f1 59m")
        self.assertEqual(shown["dev-shop-3"], "\u23f1 1h00")
        self.assertEqual(shown["dev-shop-4"], "\u23f1 2h01")
        self.assertEqual(shown["dev-shop-5"], "\u23f1 0m")

    def test_blocked_total_is_shown_only_when_non_zero(self):
        self.browser.open(self.url())
        texts = {c["data"]["agent"]: c["text"] for c in self.mirror()["columns"]}
        col = next(c for c in self.srv.state()["columns"] if c["agent"] == "dev-shop-3")
        self.assertIn("\u26d4 %dm" % (col["blocked_s"] // 60), texts["dev-shop-3"])
        self.assertIn("\u23f1 %dh%02d" % (col["working_s"] // 3600, col["working_s"] % 3600 // 60), texts["dev-shop-3"])
        self.assertNotIn("\u26d4", texts["tech-shop"])

    def test_hovering_between_cards_or_beside_the_header_strip_names_nobody(self):
        self.browser.open(self.url())
        left, width = self.card("tech-shop")
        for x, y in ((left - 2, 133), (left + width + 2, 133), (left + width / 2, 96), (left + width / 2, 170)):
            self.browser.call("move", x=x, y=y)
            self.browser.call("sleep", ms=60)
            self.assertEqual(self.browser.eval("document.getElementById('board').title"), "", (x, y))
        self.browser.call("move", x=left + width - 3, y=133)
        self.browser.wait("document.getElementById('board').title === 'tech-shop \u00b7 Tech Lead \u00b7 idle'")

    def test_a_collapsed_stub_has_no_header_to_hover(self):
        self.browser.open(self.url())
        left, width = self.card("dev-shop-0")
        self.browser.call("move", x=left + width / 2, y=133)
        self.browser.call("sleep", ms=100)
        self.assertEqual(self.browser.eval("document.getElementById('board').title"), "")

    def test_scrolling_sideways_moves_the_columns_but_not_the_bar_and_header_hits_follow(self):
        self.browser.open(self.url(), width=900)
        self.browser.eval("window.scrollTo(200, 0)")
        self.browser.wait("window.scrollX === 200")
        # at 900 px every column is 84 wide: page x 308 is the fourth column, qab-shop
        self.browser.call("move", x=108, y=133)
        self.browser.wait("document.getElementById('board').title === 'qab-shop \u00b7 QA blackbox \u00b7 working'")
        self.assertEqual(self.browser.eval("document.getElementById('board').style.cursor"), "pointer")
        self.assertGreater(colour_near(self.pixels(17, 20, 23, 54), "E8820E", 3), 150)  # the bar stays put
        # the Manager's mango band has scrolled out of view: the strip below the first screen x is teal now
        self.assertEqual(colour_near(self.pixels(50, 700, 54, 704), "F8F1E3", 6), 0)
        self.browser.call("move", x=640, y=400)
        self.browser.wait("document.getElementById('board').style.cursor === 'default'")

    def test_hovering_a_header_names_the_agent_role_and_status(self):
        self.browser.open(self.url())
        self.browser.call("move", x=58, y=133)
        self.browser.wait("document.getElementById('board').title === 'manager \\u00b7 Manager \\u00b7 idle'")
        self.browser.call("move", x=640, y=400)
        self.browser.wait("document.getElementById('board').title === ''")


class IdleLoopTest(BrowserTestCase):
    def frames_over(self, seconds):
        self.browser.call("sleep", ms=500)
        before = self.browser.eval("window.__raf")
        self.browser.call("sleep", ms=int(seconds * 1000))
        return self.browser.eval("window.__raf") - before

    def test_loop_runs_while_something_pulses(self):
        self.browser.open(self.url())
        self.assertGreater(self.frames_over(1), 20)

    def test_loop_runs_for_a_working_agent_alone(self):
        self.browser.open(self.url(self.small_server(developer_status="working")))
        self.assertEqual(self.mirror()["count"], "0")
        self.assertGreater(self.frames_over(1), 20)

    def test_loop_runs_for_a_waiting_item_alone(self):
        self.browser.open(self.url(self.small_server(waiting=True)))
        self.assertEqual(self.mirror()["count"], "1")
        self.assertGreater(self.frames_over(1), 20)

    def test_loop_is_idle_on_a_quiet_squad(self):
        self.browser.open(self.url(self.quiet_server()))
        self.assertEqual(self.mirror()["count"], "0")
        self.assertEqual(self.frames_over(2), 0)


class LookTest(BrowserTestCase):
    """What the canvas paints, sampled from its pixels. The strip y 100..168 holds the header cards."""

    def test_background_is_the_light_cream(self):
        self.browser.open(self.url())
        self.assertEqual(colour_near(self.pixels(2, 700, 12, 790), "FCF8F1", 2), 10 * 90)

    def test_needs_you_bar_has_a_mango_left_edge_when_something_waits(self):
        self.browser.open(self.url())
        self.assertGreater(colour_near(self.pixels(17, 20, 23, 54), "E8820E", 3), 0.9 * 6 * 34)

    def test_blocked_header_is_outlined_in_red_and_idle_ones_are_not(self):
        self.browser.open(self.url())
        self.assertGreater(colour_near(self.pixels(0, 100, 1000, 168), "DB3B22", 8), 150)
        self.browser.open(self.url(self.quiet_server()))
        self.assertEqual(colour_near(self.pixels(0, 100, 1000, 168), "DB3B22", 8), 0)
        # nothing waits: the bar's edge is the idle grey, not mango
        self.assertGreater(colour_near(self.pixels(17, 20, 23, 54), "A99C86", 3), 150)

    def test_working_header_has_a_teal_dot(self):
        self.browser.open(self.url())
        self.assertGreater(colour_near(self.pixels(0, 100, 1000, 168), "0C8A80", 8), 100)

    def test_all_three_needs_you_items_are_painted_in_the_bar_at_1280(self):
        self.browser.open(self.url())
        for x0, x1 in ((225, 400), (437, 620), (660, 870)):
            self.assertGreater(colour_near(self.pixels(x0, 22, x1, 50), "3E372E", 40), 100, (x0, x1))

    def test_the_needs_you_items_are_separated_by_thin_rules(self):
        self.browser.open(self.url())
        for x0, x1, rule in ((419, 428, True), (641, 650, True), (210, 220, False)):
            found = colour_near(self.pixels(x0, 26, x1, 48), "D6CCBC", 12)
            self.assertEqual(found > 20, rule, (x0, found))

    def test_a_narrow_bar_gives_up_on_the_items_and_counts_them(self):
        self.browser.open(self.url(), width=900)
        self.assertEqual(colour_near(self.pixels(225, 22, 520, 50), "3E372E", 40), 0)
        self.assertGreater(colour_near(self.pixels(225, 22, 520, 50), "857A68", 20), 20)

    def test_status_dots_are_grey_idle_teal_working_and_red_blocked(self):
        self.browser.open(self.url())
        for agent, colour in (("tech-shop", "A99C86"), ("qab-shop", "0C8A80"), ("dev-shop-3", "DB3B22")):
            left, _ = self.card(agent)
            self.assertEqual(colour_near(self.pixels(left + 12, 115, left + 14, 117), colour, 6), 4, agent)

    def test_a_blocked_total_paints_red_inside_the_card_and_other_cards_do_not(self):
        self.browser.open(self.url())
        left, width = self.card("dev-shop-3")
        # the digits at the right end, clear of the emoji, which brings its own colour
        self.assertGreater(colour_near(self.pixels(left + width - 20, 128, left + width - 6, 143), "DB3B22", 25), 5)
        left, width = self.card("tech-shop")
        self.assertEqual(colour_near(self.pixels(left + width - 20, 128, left + width - 6, 143), "DB3B22", 25), 0)

    def test_working_and_blocked_cards_pulse_a_ring_and_idle_cards_have_none(self):
        self.browser.open(self.url())

        def ring_is_painted(agent):
            left, _ = self.card(agent)
            hist = self.pixels(left + 13 + 8, 100 + 16 - 1, left + 13 + 11, 100 + 16 + 1)
            return sum(c for h, c in hist.items() if colour_near({h: c}, "FFFDF9", 12) == 0)

        self.assertGreater(ring_is_painted("qab-shop"), 0)
        self.assertGreater(ring_is_painted("dev-shop-3"), 0)
        self.assertEqual(ring_is_painted("tech-shop"), 0)

    def test_pod_bands_are_tinted_in_the_pod_colours_and_labelled_except_the_managers(self):
        self.browser.open(self.url())

        def band(x, colour):
            hist = self.pixels(x, 700, x + 4, 704)
            blend = [round(0xFC * 0.93 + int(colour[0:2], 16) * 0.07), round(0xF8 * 0.93 + int(colour[2:4], 16) * 0.07),
                     round(0xF1 * 0.93 + int(colour[4:6], 16) * 0.07)]
            return colour_near(hist, "%02X%02X%02X" % tuple(blend), 2)

        self.assertEqual(band(50, "E8820E"), 16)   # the Manager's band is mango
        self.assertEqual(band(300, "0C8A80"), 16)  # the first other pod is teal
        self.assertEqual(band(800, "2A6DC0"), 16)  # the second is blue
        self.assertGreater(colour_near(self.pixels(112, 82, 180, 96), "0C8A80", 20), 20)   # SHOP \u00b7 M
        self.assertGreater(colour_near(self.pixels(724, 82, 790, 96), "2A6DC0", 20), 20)   # AUTH \u00b7 S
        self.assertEqual(colour_near(self.pixels(20, 82, 95, 96), "E8820E", 20), 0)         # no label

    def test_task_card_and_rails_are_drawn_and_a_stub_has_a_rule_but_no_rail(self):
        self.browser.open(self.url())
        self.assertEqual(colour_near(self.pixels(1100, 600, 1110, 610), "FFFDF9", 2), 100)
        left, width = self.card("tech-shop")
        centre = left + width / 2
        self.assertGreater(colour_near(self.pixels(centre - 1, 300, centre + 1, 500), "D6CCBC", 20), 20)
        left, width = self.card("dev-shop-0")
        centre = left + width / 2
        self.assertEqual(colour_near(self.pixels(centre - 1, 300, centre + 1, 500), "D6CCBC", 20), 0)
        self.assertGreater(colour_near(self.pixels(centre - 1, 100, centre + 1, 166), "D6CCBC", 20), 20)

    def test_a_working_header_total_is_teal_and_a_missing_token_count_is_grey(self):
        self.browser.open(self.url())
        left, width = self.card("tech-shop")
        self.assertGreater(colour_near(self.pixels(left + 6, 128, left + 40, 143), "0C8A80", 40), 20)
        left, width = self.card("dev-auth-1")
        self.assertGreater(colour_near(self.pixels(left + width - 20, 148, left + width - 4, 160), "A99C86", 12), 3)
        self.assertEqual(colour_near(self.pixels(left + width - 20, 148, left + width - 4, 160), "857A68", 12), 0)
        left, width = self.card("tech-shop")  # a known count is the darker muted ink, not the idle grey
        self.assertGreater(colour_near(self.pixels(left + width - 30, 148, left + width - 4, 160), "857A68", 12), 3)

    def test_the_page_is_not_dark(self):
        self.browser.open(self.url())
        histogram = self.pixels(0, 600, 1000, 700)
        dark = sum(c for hex_, c in histogram.items() if sum(int(hex_[i:i + 2], 16) for i in (0, 2, 4)) < 3 * 128)
        self.assertEqual(dark, 0)


class CanvasDetailTest(BrowserTestCase):
    """The rules behind the layout and the paint that no other test pins down."""

    def test_a_retired_agent_is_a_stub_only_when_no_row_or_bar_involves_it(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"}, {"agent": "live-quiet"},
                   {"agent": "gone-status", "status": "retired 2026-10-11"},
                   {"agent": "gone-sender", "status": "retired 2026-10-11"},
                   {"agent": "gone-receiver", "status": "retired 2026-10-11"},
                   {"agent": "gone-nothing", "status": "retired 2026-10-11"}])
        fx.iteration(1, QUIET_CHECKIN)
        fx.activity(agent="manager", status="idle")
        fx.activity(agent="gone-status", status="working")
        fx.activity(agent="gone-status", status="idle")
        fx.message(**{"from": "gone-sender", "to": "manager"})
        fx.message(**{"from": "manager", "to": "gone-receiver"})
        self.browser.open(self.url(fx.start(now=self.now)))
        flags = {c["data"]["agent"]: c["data"]["collapsed"] for c in self.mirror()["columns"]}
        self.assertEqual(flags, {"manager": "false", "live-quiet": "false", "gone-status": "false",
                                 "gone-sender": "false", "gone-receiver": "false", "gone-nothing": "true"})

    def test_pod_bands_meet_at_the_column_edge(self):
        self.browser.open(self.url())
        pods = self.srv.state()["pods"]
        for index, colour in ((1, "0C8A80"), (2, "2A6DC0")):
            x = self.card(pods[index]["agents"][0])[0] - 4 + 10  # ten px into the pod, past the previous band
            blend = [round(base * 0.93 + int(colour[i:i + 2], 16) * 0.07)
                     for base, i in ((0xFC, 0), (0xF8, 2), (0xF1, 4))]
            hist = self.pixels(x, 700, x + 2, 702)
            self.assertEqual(colour_near(hist, "%02X%02X%02X" % tuple(blend), 2), 4, index)

    def test_the_mirror_lists_every_pod_with_its_size(self):
        self.browser.open(self.url())
        expected = [(p["name"] + (" \u00b7 " + p["size"] if p["size"] else ""), p["name"], p["size"] or "")
                    for p in self.srv.state()["pods"]]
        shown = [(n["text"], n["data"]["pod"], n["data"]["size"]) for n in self.mirror()["pods"]]
        self.assertEqual(shown, expected)

    def test_a_pod_label_is_upper_case_and_carries_the_size(self):
        self.browser.open(self.url())
        pod = self.srv.state()["pods"][1]
        left = self.card(pod["agents"][0])[0] - 4 + 14
        label = pod["name"].upper() + " \u00b7 " + pod["size"].upper()
        wanted = self.text_width('800 11.5px ' + FONT, label)
        found = self.extent(left - 2, 82, left + 200, 96, "0C8A80", 40)
        self.assertAlmostEqual(found[1] - left, wanted, delta=3)

    def test_the_tasks_card_is_titled(self):
        self.browser.open(self.url())
        self.assertGreater(colour_near(self.pixels(1066, 80, 1110, 100), "A99C86", 30), 20)

    def test_a_rail_is_dashed(self):
        self.browser.open(self.url())
        left, width = self.card("tech-shop")
        centre = left + width / 2
        painted = colour_near(self.pixels(centre - 1, 300, centre + 1, 500), "D6CCBC", 20)
        self.assertTrue(30 < painted < 150, painted)  # of 400 pixels: dashes, not a solid line

    def test_the_mirror_is_in_the_page_flow_not_removed_from_it(self):
        self.browser.open(self.url())
        box = self.browser.eval("(() => { const m = document.getElementById('board-text');"
                                " return [getComputedStyle(m).display, m.offsetWidth, m.offsetHeight]; })()")
        self.assertEqual(box, ["block", 1, 1])

    def test_a_waiting_item_pulses_a_halo_that_changes_over_time(self):
        self.browser.open(self.url())
        seen = set()
        for _ in range(8):
            seen.add(tuple(sorted(self.pixels(54, 36, 56, 38).items())))
            self.browser.call("sleep", ms=250)
        self.assertGreater(len(seen), 1)
        self.assertEqual(colour_near(self.pixels(54, 36, 56, 38), "FFFDF9", 12), 0)
        self.browser.open(self.url(self.quiet_server()))
        self.assertEqual(colour_near(self.pixels(54, 36, 56, 38), "FFFDF9", 2), 4)

    def test_many_changes_in_one_frame_ask_for_one_frame(self):
        self.browser.open(self.url(self.quiet_server()))
        self.browser.call("sleep", ms=500)
        before = self.browser.eval("window.__raf")
        self.browser.eval("for (let i = 0; i < 50; i++) window.dispatchEvent(new Event('resize'))")
        self.browser.call("sleep", ms=300)
        self.assertLessEqual(self.browser.eval("window.__raf") - before, 2)

    def test_scrolling_sideways_redraws_a_quiet_page(self):
        self.browser.open(self.url(self.quiet_server()), width=300)
        # the first card's dot; the second column hides under the task card at this width
        self.assertEqual(colour_near(self.pixels(32, 115, 34, 117), "A99C86", 6), 4)
        self.browser.eval("window.scrollTo(50, 0)")
        self.browser.wait("window.scrollX === 50")
        self.browser.call("sleep", ms=200)
        self.assertEqual(colour_near(self.pixels(32, 115, 34, 117), "A99C86", 6), 0)

    def test_before_the_first_state_the_bar_says_loading_and_afterwards_what_is_waiting(self):
        self.browser.call("open", url=self.url(), failFirst=2)
        self.browser.wait(RECONNECTING_JS)
        self.browser.call("sleep", ms=200)
        loading = self.text_width('800 17px ' + FONT, "Loading\u2026")
        found = self.extent(60, 22, 420, 50, "857A68", 40)
        self.assertAlmostEqual(found[1] - 66, loading, delta=3)
        self.browser.wait(LIVE_JS, timeout=15000)
        self.browser.open(self.url(self.quiet_server()))
        nothing = self.text_width('800 17px ' + FONT, "Nothing is waiting on you")
        found = self.extent(60, 22, 420, 50, "857A68", 40)
        self.assertAlmostEqual(found[1] - 66, nothing, delta=3)

    def test_a_long_name_is_cut_inside_its_card(self):
        self.browser.open(self.url())
        for entry in self.mirror()["columns"]:
            agent = entry["data"]["agent"]
            if entry["data"]["collapsed"] == "true":
                continue
            left, width = self.card(agent)
            gap = self.pixels(left + width + 1, 106, left + width + 4, 126)
            self.assertEqual(colour_near(gap, "3E372E", 80), 0, agent)

    def test_a_narrow_card_shrinks_both_totals_so_they_do_not_overlap(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"}, {"agent": "dev-shop-1"}])
        fx.iteration(1, QUIET_CHECKIN)
        fx.activity(agent="manager", status="idle", ts="2026-10-10T00:00:00.000Z")
        for status, ts in (("working", "2026-10-10T00:00:00.000Z"), ("blocked", "2026-10-10T01:00:00.000Z"),
                           ("idle", "2026-10-10T02:05:00.000Z")):
            fx.activity(agent="dev-shop-1", status=status, ts=ts)
        # 420 px: the second column is as narrow as it gets and still clear of the task card
        self.browser.open(self.url(fx.start(now=self.now)), width=420)
        text = self.mirror()["columns"][1]["text"]
        self.assertIn("\u23f1 2h05", text)  # working counts the blocked hour too
        self.assertIn("\u26d4 1h05", text)
        left, width = 16 + 87 + 4, 87 - 8
        teal = self.extent(left, 128, left + width, 143, "0C8A80", 40)
        red = self.extent(left, 128, left + width, 143, "DB3B22", 40)
        self.assertLess(teal[1], red[0])


class SafetyTest(BrowserTestCase):
    def test_hostile_text_is_never_executed_or_turned_into_markup(self):
        hostile = "<img src=x onerror=alert(1)>"
        self.fx.escalations([{"question": hostile}])
        self.fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"},
                        {"agent": hostile, "role": "<b>Dev</b>", "scope": "<i>shop</i>"}])
        srv = self.fx.start(now=self.now)
        self.browser.open(self.url(srv))
        self.browser.call("sleep", ms=500)
        self.assertEqual(self.browser.call("events")["dialogs"], [])
        self.assertEqual(self.browser.eval("document.querySelectorAll('img, b, i').length"), 0)
        m = self.mirror()
        self.assertIn(hostile, [n["text"] for n in m["needs"]])
        self.assertIn(hostile, [c["data"]["agent"] for c in m["columns"]])

    def test_the_fixture_message_with_markup_does_not_run_or_appear(self):
        self.browser.open(self.url())
        self.browser.call("sleep", ms=500)
        self.assertEqual(self.browser.call("events")["dialogs"], [])
        self.assertEqual(self.browser.eval("document.querySelectorAll('img').length"), 0)


class ReconnectTest(BrowserTestCase):
    def painted_reconnecting(self):
        return colour_near(self.pixels(1090, 20, 1250, 54), "CE7000", 30)

    def test_the_bar_paints_reconnecting_only_while_the_server_is_away(self):
        self.browser.open(self.url())
        self.assertEqual(self.painted_reconnecting(), 0)
        port = self.srv.port
        self.srv.stop()
        self.browser.wait(RECONNECTING_JS)
        self.browser.call("sleep", ms=200)
        self.assertGreater(self.painted_reconnecting(), 50)
        self.fx.start(now=self.now, port=port)
        self.browser.wait(LIVE_JS, timeout=15000)
        self.browser.call("sleep", ms=200)
        self.assertEqual(self.painted_reconnecting(), 0)

    def test_retries_back_off_one_second_then_two(self):
        self.browser.call("open", url=self.url(), failFirst=3)
        self.browser.wait(LIVE_JS, timeout=15000)
        events = self.browser.call("events")
        times = [t for u, t in zip(events["requests"], events["times"]) if u.endswith("/state")]
        self.assertEqual(len(times), 4)
        gaps = [(b - a) / 1000.0 for a, b in zip(times, times[1:])]
        self.assertTrue(0.9 <= gaps[0] < 1.8 and 1.9 <= gaps[1] < 3.0 and 3.9 <= gaps[2], gaps)

    def test_a_second_outage_starts_the_backoff_again_at_one_second(self):
        self.browser.open(self.url())
        port = self.srv.port
        self.srv.stop()
        self.browser.wait(RECONNECTING_JS)
        self.browser.call("sleep", ms=3500)  # two failed attempts: the next wait would be 4 s
        self.fx.start(now=self.now, port=port)
        self.browser.wait(LIVE_JS, timeout=15000)
        self.srv.stop()  # already stopped; the restarted server is the last one in the fixture
        self.fx._servers[-1].stop()
        self.browser.wait(RECONNECTING_JS)
        self.fx.start(now=self.now, port=port)
        self.browser.wait(LIVE_JS, timeout=2500)

    def test_a_stopped_server_shows_reconnecting_and_the_page_recovers_on_its_own(self):
        self.browser.open(self.url())
        port = self.srv.port
        self.srv.stop()
        self.browser.wait(RECONNECTING_JS)
        self.assertEqual(self.browser.eval("document.querySelector('#connection-state').textContent"), "Reconnecting…")
        self.fx.start(now=self.now, port=port)
        self.browser.wait(LIVE_JS, timeout=15000)
        self.assertEqual(self.mirror()["count"], "3")

    def test_a_failed_stream_is_closed_so_the_browser_does_not_retry_on_its_own(self):
        self.browser.open(self.url())
        port = self.srv.port
        before = len(self.browser.call("events")["requests"])
        self.srv.stop()
        self.browser.wait(RECONNECTING_JS)
        self.browser.call("sleep", ms=5500)  # our attempts: +1 s and +3 s; the browser's own would be +3 s each
        urls = [u.replace(self.srv.base, "") for u in self.browser.call("events")["requests"][before:]]
        self.assertEqual(len([u for u in urls if u.startswith("/events")]), 2, urls)
        self.fx.start(now=self.now, port=port)
        self.browser.wait(LIVE_JS, timeout=15000)

    def test_a_state_request_that_fails_at_load_is_retried(self):
        self.browser.call("open", url=self.url(), failFirst=2)
        self.browser.wait(RECONNECTING_JS)
        self.browser.wait(LIVE_JS, timeout=15000)
        self.assertEqual(self.mirror()["count"], "3")


if __name__ == "__main__":
    unittest.main()
