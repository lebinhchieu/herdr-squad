"""Seam A, BRD-13: the sequence diagram and the task column of the page.

Same method as test_board_page.py: the page runs in headless Chromium (node and playwright-core), the
text mirror is read for facts and the canvas for pixels. Two extra things on top of that driver: a
fillText/draw-call spy, and `openPatched`, which opens the page on a real replay server but hands the
page an edited copy of /state (and of the stream's state event), for shapes the server never makes
(5,000 rows, an agent that is in no column). Skipped where node, playwright-core or Chromium are missing.
"""
import json
import re
import time
import unittest
from unittest import mock

import test_board_page as page
from board_fixture import Fixture

EXTRA_OPS = r"""
  async openPatched({ url, patch, width = 1280, height = 800, dpr = 1 }) {
    await reset(width, height, dpr);
    const edit = new Function('state', patch);
    const origin = new URL(url).origin;
    // a handler that outlives its context must not throw: an unhandled rejection ends the driver
    await page.route('**/state', async (route) => {
      try {
        const res = await route.fetch();
        await route.fulfill({ response: res, json: edit(await res.json()) });
      } catch (e) { /* page closed */ }
    });
    await page.route('**/events*', async (route) => {
      try {
        const res = await context.request.get(origin + '/state');
        await route.fulfill({ status: 200, headers: { 'content-type': 'text/event-stream', 'cache-control': 'no-store' },
          body: 'event: state\ndata: ' + JSON.stringify(edit(await res.json())) + '\n\n' });
      } catch (e) { /* page closed */ }
    });
    await page.goto(url);
  },
  // the old page would otherwise go on retrying a dead server and report into the next test's events
  async quiesce() { if (context) { await context.close(); context = null; page = null; } },
"""
DRIVER_JS = page.DRIVER_JS.replace("const ops = {", "const ops = {" + EXTRA_OPS, 1)

ROW_H, ROWS_Y = 30, 180
PILL = re.compile("⏱ (\\d+h \\d\\dm|\\d+m \\d\\ds|\\d+s)")  # an open bar's timer; a header total has no seconds
TYPE_COLOURS = {"ASK": "2A6DC0", "ANSWER": "4A8FE0", "DECISION": "9E7A00", "HANDIN": "9A40CF", "PASS": "368A1E",
                "FAIL": "CE1D6C", "STATUS": "857A68", "BLOCKED": "DB3B22", None: "857A68"}
STATE_COLOURS = {"blocked": "DB3B22", "building": "0C8A80", "checking": "9A40CF", "returned": "CE1D6C", "done": "368A1E"}
STATE_ORDER = ["blocked", "building", "checking", "returned", "done"]

SEQ_MIRROR_JS = """(() => {
  const lis = (sel) => [...document.querySelectorAll(sel + ' li')].map((li) => ({
    text: li.textContent, data: Object.assign({}, li.dataset)}));
  return {rows: lis('#rows'), bars: lis('#bars'), tasks: lis('#tasks')};
})()"""

# patch the canvas context so that a NaN or Infinity coordinate is recorded; redraw; return what was seen
NAN_JS = """new Promise((done) => {
  window.__nan = window.__nan || [];
  if (!window.__nanPatched) {
    window.__nanPatched = true;
    const proto = CanvasRenderingContext2D.prototype;
    ['moveTo', 'lineTo', 'arc', 'fillRect', 'roundRect', 'fillText', 'translate', 'rect'].forEach((name) => {
      const original = proto[name];
      proto[name] = function (...args) {
        if (args.some((a) => typeof a === 'number' && !Number.isFinite(a))) window.__nan.push(name + ':' + args.join(','));
        return original.apply(this, args);
      };
    });
  }
  window.dispatchEvent(new Event('resize'));
  requestAnimationFrame(() => requestAnimationFrame(() => done(window.__nan)));
})"""

# fillText and path calls per frame, over about a second of frames
CALLS_JS = """new Promise((done) => {
  if (!window.__counted) {
    window.__counted = true; window.__calls = 0;
    const proto = CanvasRenderingContext2D.prototype;
    ['fillText', 'fill', 'stroke', 'fillRect'].forEach((name) => {
      const original = proto[name];
      proto[name] = function (...args) { window.__calls++; return original.apply(this, args); };
    });
  }
  window.dispatchEvent(new Event('resize'));
  // BRD-27: frames come at the ambient rate, so count the calls of one draw, not per frame
  requestAnimationFrame(() => requestAnimationFrame(() => {
    window.__calls = 0;
    window.dispatchEvent(new Event('resize'));
    requestAnimationFrame(() => done(window.__calls));
  }));
})"""


def lifted(*names):
    """Source of the page's own pure helpers, to run them in a page without touching the board."""
    source = page.page_text()
    return "".join(re.search(r"^function %s\(.*?^}\n" % fn, source, re.S | re.M).group(0) for fn in names)


def reddish(histogram):
    """Pixels that are plainly red-ish: the hatch is a tint of red over cream, never within a few steps of #DB3B22."""
    return sum(c for h, c in histogram.items()
               if int(h[0:2], 16) - int(h[2:4], 16) > 70 and int(h[0:2], 16) - int(h[4:6], 16) > 70)


def mirror_value(value):
    return str(value).lower() if isinstance(value, bool) else str(value)


def expected_gap(seconds):
    return "⋯ %d s quiet" % seconds if seconds < 60 else "⋯ %d min quiet" % max(1, int(seconds / 60 + 0.5))


def duration(seconds):
    h, m = divmod(seconds, 3600)[0], seconds % 3600 // 60
    if h:
        return "%dh %02dm" % (h, m)
    return "%dm %02ds" % (m, seconds % 60) if m else "%ds" % seconds


class SequenceCase(page.BrowserTestCase):
    @classmethod
    def setUpClass(cls):
        with mock.patch.object(page, "DRIVER_JS", DRIVER_JS):
            super().setUpClass()

    def tearDown(self):
        self.browser.call("quiesce")
        super().tearDown()

    def seq(self):
        return self.browser.eval(SEQ_MIRROR_JS)

    def drawn(self):
        return self.browser.eval("Array.from(window.__drawn)")

    def cx(self, agent):
        left, width = self.card(agent)
        return left + width / 2

    def stay_at_top(self):
        """A live page follows the bottom (BRD-14) and pins it again on every resize. These tests sample
        or scroll the page themselves, so a wheel and a scroll to the top pause the follow first."""
        self.browser.eval("window.dispatchEvent(new Event('wheel')); window.scrollTo(0, 0)")
        self.browser.call("sleep", ms=500)  # past the page's 400 ms "this is the user" window
        self.browser.eval("new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)))")

    def scroll_to_bottom(self):
        self.scroll_to(self.browser.eval("document.documentElement.scrollHeight - innerHeight"))

    def scroll_to(self, y):
        self.browser.eval("window.scrollTo(0, %s)" % y)
        self.browser.wait("window.scrollY === %s" % y if y >= 0 else "true")
        self.browser.eval("new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)))")

    def scene(self, extra=None, close=True):
        """Three agents; one message of every type; both agents idle at the end, so nothing animates."""
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"}, {"agent": "dev-a"}, {"agent": "qaw-a"}])
        fx.iteration(1, page.QUIET_CHECKIN)
        for sender, receiver, kind, task in [
                ("manager", "dev-a", "ASK", "T-1"), ("dev-a", "manager", "ANSWER", "T-1"),
                ("manager", "dev-a", "DECISION", "T-1"), ("dev-a", "qaw-a", "HANDIN", "T-1"),
                ("qaw-a", "dev-a", "FAIL", "T-1"), ("dev-a", "qaw-a", "HANDIN", "T-1"),
                ("qaw-a", "dev-a", "PASS", "T-1"), ("dev-a", "manager", "STATUS", "T-2"),
                ("dev-a", "manager", "BLOCKED", "T-2"), ("manager", "dev-a", None, None)]:
            fx.message(**{"from": sender, "to": receiver, "type": kind, "task": task})
        if extra:
            extra(fx)
        if close:
            for agent in ("manager", "dev-a", "qaw-a"):
                fx.activity(agent=agent, status="idle")
        return fx

    def arrow_y(self, index, scroll=0):
        return ROWS_Y + index * ROW_H + ROW_H // 2 - scroll

    def line_colour_count(self, index, sender, receiver, colour, scroll=0):
        """Pixels of `colour` on the arrow's line, a few px out from the sender's bar (clear of its label)."""
        x1, x2 = self.cx(sender), self.cx(receiver)
        direction = 1 if x2 > x1 else -1
        a, b = sorted((x1 + direction * 14, x1 + direction * 26))
        y = self.arrow_y(index, scroll)
        return page.colour_near(self.pixels(a, y - 1, b, y + 1), colour, 6)


class MirrorTest(SequenceCase):
    def test_rows_mirror_state_in_order_with_their_hooks_and_texts(self):
        self.browser.open(self.url())
        state = self.srv.state()
        shown = self.seq()["rows"]
        self.assertEqual(len(shown), len(state["rows"]))
        self.assertGreater(len(shown), 250)
        for mirrored, row in zip(shown, state["rows"]):
            data = mirrored["data"]
            self.assertEqual((data["rowId"], data["kind"]), (str(row["id"]), row["kind"]))
            if row["kind"] == "message":
                label = (row["type"] or "msg") + (" " + row["task"] if row["task"] else "")
                self.assertEqual(mirrored["text"], "%s %s → %s" % (label, row["from"], row["to"]))
                self.assertEqual((data["type"], data["task"], data["from"], data["to"]),
                                 (row["type"] or "", row["task"] or "", row["from"], row["to"]))
            elif row["kind"] == "status":
                tail = " · " + duration(row["duration_s"]) if "duration_s" in row else ""
                self.assertEqual(mirrored["text"], row["status"] + tail)
                self.assertEqual(data["agent"], row["agent"])
            else:
                self.assertEqual(mirrored["text"], expected_gap(row["seconds"]))
                self.assertEqual(data["seconds"], str(row["seconds"]))

    def test_there_are_gap_rows_and_they_read_n_min_quiet(self):
        self.browser.open(self.url())
        gaps = [r for r in self.seq()["rows"] if r["data"]["kind"] == "gap"]
        self.assertEqual(len(gaps), 5)
        self.assertTrue(all(re.fullmatch("⋯ \\d+ min quiet", g["text"]) for g in gaps), gaps)
        self.assertIn("⋯ 7 min quiet", [g["text"] for g in gaps])  # 395 s, rounded

    def test_bars_mirror_state_in_order_with_their_hooks_and_texts(self):
        self.browser.open(self.url())
        state = self.srv.state()
        shown = self.seq()["bars"]
        self.assertEqual(len(shown), len(state["bars"]))
        for mirrored, bar in zip(shown, state["bars"]):
            self.assertEqual(mirrored["data"], {
                "agent": bar["agent"], "startRow": str(bar["start_row"]),
                "endRow": "" if bar["end_row"] is None else str(bar["end_row"]),
                "selfStart": mirror_value(bar["self_start"]), "open": mirror_value(bar["open"]),
                "blockedSegments": str(len(bar["blocked"]))})
            text = ("⏱ " if bar["open"] else "") + duration(bar["duration_s"])
            self.assertEqual(mirrored["text"], ("⟲ " if bar["self_start"] else "") + text)
        self.assertTrue([b for b in shown if b["text"].startswith("⟲")])
        self.assertTrue([b for b in shown if b["data"]["open"] == "true"])
        self.assertTrue([b for b in shown if b["data"]["blockedSegments"] != "0"])

    def test_tasks_mirror_is_grouped_by_state_and_keeps_first_appearance_inside_a_group(self):
        self.browser.open(self.url())
        state = self.srv.state()
        expected = [t for s in STATE_ORDER for t in state["tasks"] if t["state"] == s]
        shown = self.seq()["tasks"]
        self.assertEqual([t["data"]["taskId"] for t in shown], [t["id"] for t in expected])
        for mirrored, task in zip(shown, expected):
            self.assertEqual(mirrored["text"], "%s %s ↺%d" % (task["id"], task["state"], task["returns"]))
            self.assertEqual((mirrored["data"]["state"], mirrored["data"]["returns"]), (task["state"], str(task["returns"])))
        self.assertEqual([t["data"]["state"] for t in shown].count("building"), 2)

    def test_mirror_follows_a_change_of_the_squad_files(self):
        fx = self.scene()
        srv = fx.start()
        self.browser.open(self.url(srv))
        before = len(self.seq()["rows"])
        fx.message(**{"from": "dev-a", "to": "manager", "type": "ASK", "task": "T-9", "text": "one more"})
        self.browser.wait("document.querySelectorAll('#rows li').length > %d" % before)
        self.assertIn("T-9", [t["data"]["taskId"] for t in self.seq()["tasks"]])


class ArrowTest(SequenceCase):
    def test_every_message_type_has_its_own_colour_on_the_line_and_untyped_is_muted(self):
        srv = self.scene().start(now="2026-10-12T11:00:00Z")
        self.browser.open(self.url(srv))
        rows = [r for r in srv.state()["rows"] if r["kind"] == "message"]
        self.assertEqual([r["type"] for r in rows], ["ASK", "ANSWER", "DECISION", "HANDIN", "FAIL", "HANDIN", "PASS",
                                                      "STATUS", "BLOCKED", None])
        for row in rows:
            found = self.line_colour_count(row["id"], row["from"], row["to"], TYPE_COLOURS[row["type"]])
            self.assertGreater(found, 6, row)
            others = [c for t, c in TYPE_COLOURS.items() if c != TYPE_COLOURS[row["type"]]]
            for colour in others:
                self.assertEqual(self.line_colour_count(row["id"], row["from"], row["to"], colour), 0, (row, colour))

    def test_a_handin_fail_handin_pass_loop_is_four_arrows_in_three_colours(self):
        srv = self.scene().start(now="2026-10-12T11:00:00Z")
        self.browser.open(self.url(srv))
        loop = [r for r in srv.state()["rows"] if r["kind"] == "message" and r["type"] in ("HANDIN", "FAIL", "PASS")]
        self.assertEqual([r["type"] for r in loop], ["HANDIN", "FAIL", "HANDIN", "PASS"])
        colours = [next(c for c in TYPE_COLOURS.values() if self.line_colour_count(r["id"], r["from"], r["to"], c) > 6)
                   for r in loop]
        self.assertEqual(len(colours), 4)
        self.assertEqual(colours[0], colours[2])
        self.assertEqual(len(set(colours)), 3)

    def test_the_head_is_at_the_receiver_in_both_directions(self):
        srv = self.scene().start(now="2026-10-12T11:00:00Z")
        self.browser.open(self.url(srv))
        for row_id, sender, receiver, colour in ((0, "manager", "dev-a", "2A6DC0"), (1, "dev-a", "manager", "4A8FE0")):
            x1, x2 = self.cx(sender), self.cx(receiver)
            direction = 1 if x2 > x1 else -1
            y = self.arrow_y(row_id)
            tip = sorted((x2 - direction * 17, x2 - direction * 9))
            tail = sorted((x1 + direction * 9, x1 + direction * 17))
            at_tip = page.colour_near(self.pixels(tip[0], y - 6, tip[1], y + 6), colour, 8)
            at_tail = page.colour_near(self.pixels(tail[0], y - 6, tail[1], y + 6), colour, 8)
            self.assertGreater(at_tip, at_tail * 2, (row_id, at_tip, at_tail))
            self.assertGreater(at_tip, 30)

    def test_labels_are_type_and_task_or_type_or_msg(self):
        srv = self.scene().start(now="2026-10-12T11:00:00Z")
        self.browser.open(self.url(srv))
        drawn = self.drawn()
        for label in ("ASK T-1", "ANSWER T-1", "HANDIN T-1", "FAIL T-1", "PASS T-1", "STATUS T-2", "BLOCKED T-2", "msg"):
            self.assertIn(label, drawn)
        fx = self.scene(lambda f: f.message(**{"from": "manager", "to": "dev-a", "type": "STATUS", "task": None}))
        self.browser.open(self.url(fx.start(now="2026-10-12T11:00:00Z")))
        self.assertIn("STATUS", self.drawn())

    def test_a_label_stays_inside_the_left_board_edge(self):
        self.browser.open(self.url())
        y = self.arrow_y(0)
        self.assertEqual(page.colour_near(self.pixels(0, y - 17, 15, y - 3), "9E7A00", 30), 0)
        self.assertGreater(page.colour_near(self.pixels(16, y - 17, 140, y - 3), "9E7A00", 30), 10)

    def test_a_message_to_an_agent_who_left_still_draws_to_its_full_column(self):
        def extra(fx):
            fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"}, {"agent": "dev-a"}, {"agent": "qaw-a"},
                       {"agent": "gone-1", "status": "retired 2026-10-11"}])
            fx.message(**{"from": "manager", "to": "gone-1", "type": "ASK", "task": "T-3"})
        srv = self.scene(extra).start(now="2026-10-12T11:00:00Z")
        self.browser.open(self.url(srv))
        flags = {c["data"]["agent"]: c["data"]["collapsed"] for c in self.mirror()["columns"]}
        self.assertEqual(flags["gone-1"], "false")
        row = [r for r in srv.state()["rows"] if r.get("task") == "T-3"][0]
        self.assertGreater(self.line_colour_count(row["id"], "manager", "gone-1", "2A6DC0"), 6)

    def test_a_self_message_draws_a_short_arrow_and_does_not_fail(self):
        fx = self.scene(lambda f: f.message(**{"from": "dev-a", "to": "dev-a", "type": "ASK", "task": "T-4"}))
        srv = fx.start(now="2026-10-12T11:00:00Z")
        self.browser.open(self.url(srv))
        self.assertEqual(self.browser.call("events")["errors"], [])
        row = [r for r in srv.state()["rows"] if r.get("task") == "T-4"][0]
        x = self.cx("dev-a")
        y = self.arrow_y(row["id"])
        self.assertGreater(page.colour_near(self.pixels(x + 14, y - 1, x + 40, y + 1), "2A6DC0", 6), 20)


class ScrolledSidewaysTest(SequenceCase):
    def test_a_status_word_has_room_by_the_scroll_and_not_by_the_page(self):
        self.browser.open(self.url(), width=700)
        scroll_x = 300
        state = self.srv.state()
        rows = [r for r in state["rows"] if r["kind"] == "status" and "duration_s" in r
                and scroll_x + 60 <= self.cx(r["agent"]) <= scroll_x + 300]
        self.assertTrue(rows)
        row = rows[0]
        scroll_y = ROWS_Y + ROW_H * row["id"] - 300
        self.browser.eval("window.scrollTo(%d, %d)" % (scroll_x, scroll_y))
        self.browser.wait("window.scrollX === %d && window.scrollY === %d" % (scroll_x, scroll_y))
        self.browser.eval("new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)))")
        x, y = self.cx(row["agent"]) - scroll_x, self.arrow_y(row["id"], scroll_y)
        muted = "857A68"
        self.assertGreater(page.colour_near(self.pixels(x + 26, y - 6, x + 80, y + 6), muted, 30), 10)
        self.assertEqual(page.colour_near(self.pixels(x - 80, y - 6, x - 26, y + 6), muted, 30), 0)


class BarTest(SequenceCase):
    def test_bar_columns_line_up_with_header_cards_at_three_widths_and_at_dpr_2(self):
        for width, dpr in ((1280, 1), (1600, 1), (1920, 1), (1280, 2)):
            srv = self.scene().start(now="2026-10-12T11:00:00Z")
            self.browser.open(self.url(srv), width=width, dpr=dpr)
            cols = self.mirror()["columns"]
            stubs = sum(1 for c in cols if c["data"]["collapsed"] == "true")
            col_w = max(84, (width - 230 - 16 - 24 * stubs) / (len(cols) - stubs))
            for agent in ("manager", "dev-a", "qaw-a"):
                index = [c["data"]["agent"] for c in cols].index(agent)
                centre = 16 + col_w * index + col_w / 2
                # rows 0..9 are messages; the first bar of each agent covers them
                # a line between two arrows, so only the bar's own border is on it
                y = self.arrow_y(5) + 10
                found = self.extent(centre - 12, y, centre + 12, y + 2, "0C8A80", 40)
                self.assertIsNotNone(found, (width, agent))
                self.assertAlmostEqual((found[0] + found[1]) / 2, centre, delta=1.5)
                self.assertAlmostEqual(found[1] - found[0], 14 + 1.6, delta=2.5)

    def test_the_bar_starts_on_the_message_that_woke_the_agent_and_a_self_start_has_the_mark(self):
        srv = self.scene().start(now="2026-10-12T11:00:00Z")
        self.browser.open(self.url(srv))
        bars = {b["data"]["agent"]: b for b in self.seq()["bars"]}
        self.assertEqual(bars["manager"]["data"]["selfStart"], "true")   # sent the first message
        self.assertEqual(bars["dev-a"]["data"]["selfStart"], "false")    # woken by it
        self.assertEqual(bars["dev-a"]["data"]["startRow"], "0")
        self.assertIn("⟲", self.drawn())
        x_manager, x_dev = self.cx("manager"), self.cx("dev-a")
        top = self.arrow_y(0) - 4
        # the mark sits left of a self-start bar's top; the woken agent's bar has none
        self.assertGreater(page.colour_near(self.pixels(x_manager - 20, top, x_manager - 8, top + 16), "0C8A80", 60), 5)
        self.assertEqual(page.colour_near(self.pixels(x_dev - 20, top, x_dev - 8, top + 16), "0C8A80", 60), 0)

    def test_the_end_marker_says_idle_and_the_duration(self):
        srv = self.scene().start(now="2026-10-12T11:00:00Z")
        self.browser.open(self.url(srv))
        ends = [r for r in srv.state()["rows"] if r["kind"] == "status"]
        self.assertEqual(len(ends), 3)
        for row in ends:
            self.assertIn("idle · %s" % duration(row["duration_s"]), self.drawn())

    def test_a_blocked_stretch_is_hatched_red_and_the_rest_of_the_bar_is_not(self):
        self.browser.open(self.url())
        state = self.srv.state()
        bar = [b for b in state["bars"] if b["blocked"]][0]
        seg = bar["blocked"][0]
        x = self.cx(bar["agent"])
        self.scroll_to(self.browser.eval("document.documentElement.scrollHeight - innerHeight"))
        scroll = self.browser.eval("window.scrollY")
        inside = self.arrow_y(seg["start_row"] + 1, scroll)
        before = self.arrow_y(bar["start_row"] + 1, scroll)  # row 283: working, before the block
        self.assertLess(before, inside)
        striped = self.pixels(x - 6, inside - 6, x + 6, inside + 6)
        self.assertGreater(reddish(striped), 20)
        self.assertEqual(reddish(self.pixels(x - 6, before - 6, x + 6, before + 6)), 0)
        self.assertGreater(len([h for h, c in striped.items() if c > 3]), 2)  # stripes: more than one tone

    def test_a_closed_bar_has_no_open_end_pill(self):
        srv = self.scene().start(now="2026-10-12T11:00:00Z")
        self.browser.open(self.url(srv))
        self.assertEqual([b["data"]["open"] for b in self.seq()["bars"]], ["false"] * 3)
        self.assertEqual([t for t in self.drawn() if PILL.fullmatch(t)], [])

    def test_a_bar_that_starts_and_ends_on_one_row_is_still_drawn(self):
        patch = """
          state.bars.push({agent: 'tech-shop', start_row: 5, end_row: 5, start_ts: state.now, end_ts: state.now,
                           self_start: false, open: false, duration_s: 0, blocked: []});
          return state;"""
        self.browser.call("openPatched", url=self.url(), patch=patch)
        self.browser.wait(page.LIVE_JS)
        self.browser.eval("new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)))")
        self.stay_at_top()
        x = self.cx("tech-shop")
        y = self.arrow_y(5)
        found = self.pixels(x - 8, y - 8, x + 8, y + 8)
        self.assertGreater(page.colour_near(found, "0C8A80", 40), 15)
        self.assertEqual(self.browser.eval(NAN_JS), [])


class OpenBarTest(SequenceCase):
    def test_the_timer_ticks_without_asking_for_state_again_and_is_never_negative_or_nan(self):
        self.browser.open(self.url())
        self.scroll_to_bottom()
        requests_before = len([u for u in self.browser.call("events")["requests"] if u.endswith("/state")])
        self.browser.call("sleep", ms=3200)
        # the pills; a header total is "⏱ 14m", with no seconds
        stamps = sorted({t for t in self.drawn() if re.fullmatch("⏱ (\\d+h \\d\\dm|\\d+m \\d\\ds|\\d+s)", t)})
        self.assertGreaterEqual(len(stamps), 4, stamps)
        self.assertFalse([t for t in self.drawn() if t.startswith("⏱ ") and ("NaN" in t or "-" in t)])
        requests_after = len([u for u in self.browser.call("events")["requests"] if u.endswith("/state")])
        self.assertEqual(requests_after, requests_before)

    def test_the_timer_starts_from_the_servers_figure_for_the_bar(self):
        self.browser.open(self.url())
        self.scroll_to_bottom()
        opens = [b for b in self.srv.state()["bars"] if b["open"]]
        self.assertEqual(len(opens), 3)
        seconds = {b["duration_s"] for b in opens}
        shown = {t for t in self.drawn() if t.startswith("⏱ ")}
        for value in seconds:
            self.assertIn("⏱ " + duration(value), shown)

    def test_an_open_bar_ends_in_a_dot_and_a_pill_that_stay_inside_the_columns(self):
        self.browser.open(self.url())
        self.scroll_to(self.browser.eval("document.documentElement.scrollHeight - innerHeight"))
        bar = [b for b in self.srv.state()["bars"] if b["open"] and b["blocked"]][0]
        x = self.cx(bar["agent"])
        y = 180 + 30 * (len(self.srv.state()["rows"]) - 1) + 15 + 15 + 2 - self.browser.eval("window.scrollY")
        self.assertGreater(page.colour_near(self.pixels(x - 5, y - 5, x + 5, y + 5), "DB3B22", 60), 5)  # blocked: red dot

    def test_the_pill_sits_right_of_the_rail_and_flips_left_only_where_the_tasks_card_is_in_the_way(self):
        self.browser.open(self.url())
        self.scroll_to_bottom()
        state = self.srv.state()
        y = ROWS_Y + ROW_H * (len(state["rows"]) - 1) + 15 + 15 + 2 - self.browser.eval("window.scrollY")
        xs = sorted(self.cx(b["agent"]) for b in state["bars"] if b["open"])
        self.assertEqual(len(xs), 3)

        def teal(left, right):
            return page.colour_near(self.pixels(left, y - 12, right, y - 3), "0C8A80", 60)
        for x in xs[:-1]:
            self.assertGreater(teal(x + 10, x + 75), 5, x)
            self.assertEqual(teal(x - 75, x - 10), 0, x)
        self.assertGreater(teal(xs[-1] - 75, xs[-1] - 10), 5)
        self.assertEqual(teal(xs[-1] + 10, xs[-1] + 75), 0)

    def test_the_loop_idles_once_nothing_is_open_and_nothing_draws_in(self):
        srv = self.scene().start(now="2026-10-12T11:00:00Z")
        self.browser.open(self.url(srv))
        self.browser.call("sleep", ms=500)
        before = self.browser.eval("window.__raf")
        self.browser.call("sleep", ms=2000)
        self.assertEqual(self.browser.eval("window.__raf") - before, 0)

    def test_the_loop_runs_while_a_bar_is_open(self):
        srv = self.scene(close=False).start(now="2026-10-12T11:00:00Z")
        self.browser.open(self.url(srv))
        self.browser.call("sleep", ms=500)
        before = self.browser.eval("window.__raf")
        self.browser.call("sleep", ms=1000)
        frames = self.browser.eval("window.__raf") - before
        self.assertGreater(frames, 2)  # BRD-27: an open bar's timer redraws about 5 times a second
        self.assertLessEqual(frames, 14)


DRAW_IN_JS = """new Promise((done) => {
  // the longest run of the arrow colour on one canvas row, per frame, until it stops growing
  const c = document.getElementById('board'), ctx = c.getContext('2d'), r = c.width / c.clientWidth;
  const [x0, x1, y, want] = %s;
  const wanted = [0, 2, 4].map((i) => parseInt(want.slice(i, i + 2), 16));
  const lengths = [];
  const probe = () => {
    const d = ctx.getImageData(Math.round(x0 * r), Math.round(y * r), Math.round((x1 - x0) * r), 1).data;
    let n = 0;
    for (let i = 0; i < d.length; i += 4) if ([0, 1, 2].every((k) => Math.abs(d[i + k] - wanted[k]) <= 10)) n++;
    lengths.push(n);
  };
  const start = performance.now();
  const step = () => { probe(); if (performance.now() - start < %d) requestAnimationFrame(step); else done(lengths); };
  requestAnimationFrame(step);
})"""


DRAW_TIMES_JS = DRAW_IN_JS.replace("lengths.push(n);", "lengths.push([Math.round(performance.now() - start), n]);")


class AnimationTest(SequenceCase):
    def appended(self):
        fx = self.scene()
        srv = fx.start()
        return fx, srv

    def append_arrow(self, fx):
        # all three records at once and the agents idle again, so only the arrow is animating
        rows = len(self.seq()["rows"])
        fx.message(**{"from": "manager", "to": "dev-a", "type": "ASK", "task": "T-7"})
        fx.activity(agent="manager", status="idle")
        fx.activity(agent="dev-a", status="idle")
        return rows

    def test_a_new_arrow_draws_itself_in_and_a_reload_shows_it_drawn_already(self):
        fx, srv = self.appended()
        self.browser.open(self.url(srv))
        rows = self.append_arrow(fx)
        index = rows  # the new message is the next row
        x1, x2 = self.cx("manager"), self.cx("dev-a")
        y = self.arrow_y(index)
        seen = self.browser.eval(DRAW_IN_JS % (json.dumps([x1 + 10, x2 + 10, y, "2A6DC0"]), 2500))
        self.assertGreater(max(seen), 0.8 * (x2 - x1 - 20))
        self.browser.call("reload")
        self.browser.wait(page.LIVE_JS)
        self.browser.eval("new Promise((done) => requestAnimationFrame(done))")
        after_reload = self.browser.eval(DRAW_IN_JS % (json.dumps([x1 + 10, x2 + 10, y, "2A6DC0"]), 200))
        self.assertGreater(min(after_reload), 0.8 * (x2 - x1 - 20))

    def test_the_arrow_grows_over_about_400_ms_from_nothing(self):
        fx, srv = self.appended()
        self.browser.open(self.url(srv))
        rows = self.append_arrow(fx)
        x1, x2 = self.cx("manager"), self.cx("dev-a")
        y = self.arrow_y(rows)
        # sample from before the row exists, so the first frames of the draw-in are caught
        seen = self.browser.eval(DRAW_IN_JS % (json.dumps([x1 + 10, x2 + 10, y, "2A6DC0"]), 2500))
        grown = [n for n in seen if n > 0]
        self.assertTrue(grown, seen)
        self.assertLess(grown[0], 0.6 * max(grown), seen)
        self.assertEqual(seen[-1], max(seen))

    def test_the_draw_in_takes_about_400_ms(self):
        fx, srv = self.appended()
        self.browser.open(self.url(srv))
        rows = self.append_arrow(fx)
        x1, x2 = self.cx("manager"), self.cx("dev-a")
        seen = self.browser.eval(DRAW_TIMES_JS % (json.dumps([x1 + 10, x2 + 10, self.arrow_y(rows), "2A6DC0"]), 2500))
        top = max(n for _, n in seen)
        started = next(t for t, n in seen if n > 0)
        done = next(t for t, n in seen if n >= 0.97 * top)
        self.assertTrue(250 <= done - started <= 900, (started, done, seen))

    def test_an_arrow_that_arrives_off_screen_does_not_keep_the_loop_running(self):
        fx = self.scene()
        for _ in range(60):
            fx.message(**{"from": "manager", "to": "dev-a", "type": "ASK", "task": "T-7"})
        fx.activity(agent="manager", status="idle")
        fx.activity(agent="dev-a", status="idle")
        srv = fx.start()
        self.browser.open(self.url(srv))
        self.browser.eval("window.scrollTo(0, 0)")
        rows = self.append_arrow(fx)
        self.browser.wait("document.querySelectorAll('#rows li').length >= %d" % (rows + 3), timeout=8000)
        self.browser.call("sleep", ms=1500)
        before = self.browser.eval("window.__raf")
        self.browser.call("sleep", ms=2500)
        self.assertEqual(self.browser.eval("window.__raf") - before, 0)

    def test_the_loop_stops_after_the_draw_in(self):
        fx, srv = self.appended()
        self.browser.open(self.url(srv))
        rows = self.append_arrow(fx)
        self.browser.wait("document.querySelectorAll('#rows li').length >= %d" % (rows + 3), timeout=8000)
        self.browser.call("sleep", ms=1500)
        before = self.browser.eval("window.__raf")
        self.browser.call("sleep", ms=2500)
        self.assertEqual(self.browser.eval("window.__raf") - before, 0)

    def test_nothing_draws_in_at_the_first_render(self):
        srv = self.scene().start(now="2026-10-12T11:00:00Z")
        self.browser.open(self.url(srv))
        self.assertEqual(self.browser.call("events")["errors"], [])
        x1, x2 = self.cx("manager"), self.cx("dev-a")
        first = self.browser.eval(DRAW_IN_JS % (json.dumps([x1 + 10, x2 + 10, self.arrow_y(0), "2A6DC0"]), 100))
        self.assertGreater(min(first), 0.8 * (x2 - x1 - 20))

    def test_the_first_message_into_an_empty_board_draws_in_too(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"}, {"agent": "dev-a"}])
        fx.iteration(1, page.QUIET_CHECKIN)
        srv = fx.start()
        self.browser.open(self.url(srv))
        self.assertEqual(self.seq()["rows"], [])
        fx.message(**{"from": "manager", "to": "dev-a", "type": "ASK", "task": "T-1"})
        fx.activity(agent="manager", status="idle")
        fx.activity(agent="dev-a", status="idle")
        x1, x2 = self.cx("manager"), self.cx("dev-a")
        seen = self.browser.eval(DRAW_IN_JS % (json.dumps([x1 + 10, x2 + 10, self.arrow_y(0), "2A6DC0"]), 2500))
        grown = [n for n in seen if n > 0]
        self.assertTrue(grown, seen)
        self.assertLess(grown[0], 0.6 * max(grown), seen)

    def first_arrow_is_drawn_already(self):
        x1, x2 = self.cx("manager"), self.cx("tech-shop")
        seen = self.browser.eval(DRAW_IN_JS % (json.dumps([x1 + 10, x2 + 10, self.arrow_y(0), "9E7A00"]), 150))
        self.assertGreater(min(seen), 0.8 * (x2 - x1 - 20), seen)

    def test_a_board_with_no_iteration_does_not_draw_its_first_state_in(self):
        self.browser.call("openPatched", url=self.url(), patch="state.selected_iteration = null; return state;")
        self.browser.wait(page.LIVE_JS)
        self.browser.wait("document.querySelectorAll('#rows li').length > 100")
        self.first_arrow_is_drawn_already()

    def test_a_switch_to_another_iteration_shows_its_messages_drawn_already(self):
        patch = """
          if (Date.now() > %d) {
            state.selected_iteration = 99;
            state.bars = [];
            state.rows = [{id: 0, kind: 'message', ts: state.now, from: 'manager', to: 'tech-shop', type: 'DECISION',
                           task: 'T-S', text: 'x', msg_id: 'switch-1'}];
          }
          return state;""" % (int(time.time() * 1000) + 2500)
        self.browser.call("openPatched", url=self.url(), patch=patch)
        self.browser.wait(page.LIVE_JS)
        self.browser.wait("document.querySelectorAll('#rows li').length === 1", timeout=15000)
        self.first_arrow_is_drawn_already()

    def test_a_redraw_of_the_same_state_does_not_animate_again(self):
        fx, srv = self.appended()
        self.browser.open(self.url(srv))
        rows = self.append_arrow(fx)
        self.browser.wait("document.querySelectorAll('#rows li').length >= %d" % (rows + 3), timeout=8000)
        self.browser.call("sleep", ms=1500)
        x1, x2 = self.cx("manager"), self.cx("dev-a")
        self.browser.eval("window.dispatchEvent(new Event('resize'))")
        seen = self.browser.eval(DRAW_IN_JS % (json.dumps([x1 + 10, x2 + 10, self.arrow_y(rows), "2A6DC0"]), 200))
        self.assertGreater(min(seen), 0.8 * (x2 - x1 - 20))


class TaskColumnTest(SequenceCase):
    CHIP = 26

    def chip_tops(self, tasks):
        """y of each chip, in the drawn order, from the card's rules: groups of a label and a rule, then chips."""
        tops, y = [], 112
        for state in STATE_ORDER:
            members = [t for t in tasks if t["state"] == state]
            if not members:
                continue
            y += 28
            for t in members:
                tops.append((t, y))
                y += self.CHIP + 6
            y += 6
        return tops

    def test_groups_are_drawn_in_order_with_empty_ones_left_out(self):
        self.browser.open(self.url())
        drawn = self.drawn()
        order = [w for w in drawn if w in STATE_ORDER]
        self.assertEqual(sorted(order), sorted(STATE_ORDER))
        self.assertIn("TASKS", drawn)
        quiet = self.scene().start(now="2026-10-12T11:00:00Z")
        self.browser.open(self.url(quiet))
        drawn = self.drawn()
        self.assertEqual(sorted(w for w in drawn if w in STATE_ORDER), ["blocked", "done"])

    def test_every_chip_has_a_left_edge_in_its_state_colour(self):
        self.browser.open(self.url())
        for task, top in self.chip_tops(self.srv.state()["tasks"]):
            found = self.pixels(1068, top + 8, 1070, top + 18)
            self.assertEqual(page.colour_near(found, STATE_COLOURS[task["state"]], 6), 20, (task["id"], found))

    def test_two_returns_get_the_mango_chip_and_one_does_not(self):
        self.browser.open(self.url())
        tops = dict((t["id"], y) for t, y in self.chip_tops(self.srv.state()["tasks"]))
        hot = self.pixels(1180, tops["CART-02"] + 1, 1250, tops["CART-02"] + self.CHIP)
        warm = self.pixels(1180, tops["CART-01"] + 1, 1250, tops["CART-01"] + self.CHIP)
        self.assertGreater(page.colour_near(hot, "E8820E", 6), 60)
        self.assertEqual(page.colour_near(warm, "E8820E", 6), 0)
        self.assertIn("↺2", self.drawn())
        self.assertIn("↺1", self.drawn())
        self.assertNotIn("↺0", self.drawn())

    def test_the_threshold_is_two_not_three_and_not_one(self):
        def extra(fx):
            for _ in range(2):
                fx.message(**{"from": "dev-a", "to": "qaw-a", "type": "HANDIN", "task": "T-5"})
                fx.message(**{"from": "qaw-a", "to": "dev-a", "type": "FAIL", "task": "T-5"})
        srv = self.scene(extra).start(now="2026-10-12T11:00:00Z")
        self.browser.open(self.url(srv))
        tasks = {t["id"]: t["returns"] for t in srv.state()["tasks"]}
        self.assertEqual((tasks["T-1"], tasks["T-5"]), (1, 2))
        tops = dict((t["id"], y) for t, y in self.chip_tops(srv.state()["tasks"]))
        card_left = 1280 - 230 + 16
        self.assertEqual(page.colour_near(self.pixels(card_left + 100, tops["T-1"] + 1, card_left + 182, tops["T-1"] + 25),
                                          "E8820E", 6), 0)
        self.assertGreater(page.colour_near(self.pixels(card_left + 100, tops["T-5"] + 1, card_left + 182, tops["T-5"] + 25),
                                            "E8820E", 6), 60)

    def test_long_ids_are_cut_inside_the_chip(self):
        long_id = "VERYLONG-" + "X" * 80
        srv = self.scene(lambda f: f.message(**{"from": "dev-a", "to": "manager", "type": "ASK", "task": long_id})
                         ).start(now="2026-10-12T11:00:00Z")
        self.browser.open(self.url(srv))
        cut = [t for t in self.drawn() if t.startswith("VERYLONG-") and t.endswith("…")]
        self.assertTrue(cut, self.drawn())
        font = "700 12.5px " + page.FONT
        self.assertLessEqual(max(self.text_width(font, t) for t in cut if len(t) < 60), 182 - 12 - 8)
        arrows = [t for t in self.drawn() if t.startswith("ASK VERYLONG-")]
        self.assertTrue(arrows)
        self.assertLessEqual(self.text_width("700 11px " + page.FONT, arrows[0]), 3 * 344)

    def test_more_tasks_than_fit_say_how_many_are_not_shown(self):
        def extra(fx):
            for n in range(30):
                fx.message(**{"from": "manager", "to": "dev-a", "type": "DECISION", "task": "MANY-%02d" % n})
        srv = self.scene(extra).start(now="2026-10-12T11:00:00Z")
        self.browser.open(self.url(srv), height=700)
        more = [t for t in self.drawn() if re.fullmatch(r"\+\d+ more", t)]
        shown = [t for t in self.drawn() if t.startswith("MANY-")]
        self.assertEqual(len(more), 1, self.drawn())
        self.assertEqual(more[0], "+%d more" % (32 - len(shown) - len([t for t in self.drawn() if t in ("T-1", "T-2")])))
        self.assertEqual(self.browser.call("events")["errors"], [])


class WindowTest(SequenceCase):
    PATCH = """
      const rows = [];
      for (let i = 0; i < %d; i++) {
        const even = i %% 2 === 0;
        rows.push({id: i, kind: 'message', ts: '2026-10-12T10:00:00.000Z', from: even ? 'manager' : 'tech-shop',
                   to: even ? 'tech-shop' : 'manager', type: 'ASK', task: 'T-' + i, text: 'x', msg_id: 'p' + i});
      }
      state.rows = rows;
      state.bars = [];
      for (let i = 10; i < %d - 8; i += 10) {
        state.bars.push({agent: 'tech-shop', start_row: i, end_row: i + 4, start_ts: '2026-10-12T10:00:00.000Z',
                         end_ts: '2026-10-12T10:00:01.000Z', self_start: false, open: false, duration_s: 4, blocked: []});
      }
      state.bars.push({agent: 'manager', start_row: 0, end_row: null, start_ts: '2026-10-12T10:00:00.000Z', end_ts: null,
                     self_start: true, open: true, duration_s: 10, blocked: [{start_row: 3, end_row: null,
                     start_ts: '2026-10-12T10:00:00.000Z', end_ts: null, duration_s: 5}]});
      return state;"""

    def open_rows(self, count, **kw):
        self.browser.call("openPatched", url=self.url(), patch=self.PATCH % (count, count), **kw)
        self.browser.wait(page.LIVE_JS)
        self.browser.wait("document.querySelectorAll('#rows li').length === %d" % count)
        self.browser.eval("new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)))")
        self.stay_at_top()

    def calls(self):
        return self.browser.eval(CALLS_JS)

    def test_what_is_drawn_per_frame_does_not_grow_with_the_number_of_rows(self):
        self.open_rows(300)
        small = [self.calls()]
        self.scroll_to(3000)
        small.append(self.calls())
        self.open_rows(5000)
        big = [self.calls()]
        self.scroll_to(60000)
        big.append(self.calls())
        self.scroll_to(149000)
        big.append(self.calls())
        self.assertLess(max(big), max(small) * 1.3 + 20, (small, big))
        self.assertGreater(min(big), 50)  # and it did draw something at each place

    def test_only_the_rows_in_view_are_painted_and_the_first_and_last_are_not_off_by_one(self):
        self.open_rows(5000, height=800)
        for scroll in (0, 29, 30, 31, 4321, 60000, 149000, None):
            self.scroll_to_bottom() if scroll is None else self.scroll_to(scroll)
            actual = self.browser.eval("window.scrollY")
            self.browser.eval("window.__drawn.clear(); window.dispatchEvent(new Event('resize'));"
                              " new Promise((d) => requestAnimationFrame(() => requestAnimationFrame(d)))")
            drawn = {int(t.split("-")[1]) for t in self.drawn() if re.fullmatch(r"ASK T-\d+", t)}
            whole = [i for i in range(5000) if 196 <= ROWS_Y + i * ROW_H + 15 - actual <= 800 - 16 - 10]
            self.assertTrue(whole)
            self.assertTrue(set(whole) <= drawn, (scroll, sorted(set(whole) - drawn)[:5]))
            self.assertLess(len(drawn), len(whole) + 9, (scroll, len(drawn)))
            self.assertFalse([i for i in drawn if ROWS_Y + i * ROW_H + 15 - actual < 100 or ROWS_Y + i * ROW_H + 15 - actual > 900])

    def test_a_bar_across_five_thousand_rows_is_clamped_and_draws_no_nan(self):
        self.open_rows(5000)
        for scroll in (0, 70000, 149000):
            self.scroll_to(scroll)
            self.assertEqual(self.browser.eval(NAN_JS), [], scroll)
        self.assertEqual(self.browser.call("events")["errors"], [])
        x = self.cx("manager")
        self.scroll_to(70000)
        found = self.pixels(x - 6, 400, x + 6, 440)  # the bar is blocked from row 3 to the end: striped
        self.assertGreater(reddish(found), 50)

    def hatch_strip(self, x, y):
        """Which pixels of a 12 x 4 patch are stripe (not tint): the edges anti-alias a little differently."""
        return self.browser.eval("""(() => {
          const c = document.getElementById('board'), r = c.width / c.clientWidth;
          const d = c.getContext('2d').getImageData(Math.round(%d * r), Math.round(%d * r), Math.round(12 * r),
                                                    Math.round(4 * r)).data;
          let out = '';
          for (let i = 0; i < d.length; i += 4) out += d[i] - d[i + 1] > 55 ? '1' : '0';
          return out;
        })()""" % (x - 6, y))

    def test_the_hatch_stripes_move_with_their_rows_while_scrolling(self):
        self.open_rows(300)
        x = self.cx("manager")
        self.scroll_to(1500)
        before = self.hatch_strip(x, 600)
        self.scroll_to(1504)  # four pixels: the same page rows are now four pixels higher
        self.assertEqual(self.hatch_strip(x, 596), before)
        self.assertIn("1", before)
        self.assertGreater(reddish(self.pixels(x - 6, 596, x + 6, 600)), 10)

    def test_rows_run_up_to_the_clip_edge_just_below_the_headers(self):
        self.open_rows(300)
        self.scroll_to(1500)
        x = self.cx("manager")
        self.assertGreater(reddish(self.pixels(x - 6, 175, x + 6, 179)), 10)

    def test_the_sequence_stays_under_the_headers_while_scrolling(self):
        self.open_rows(300)
        self.scroll_to(1500)
        top = self.pixels(100, 100, 400, 166)
        self.assertGreater(page.colour_near(top, "FFFDF9", 2), 800)  # header cards still painted over the rows
        self.assertEqual(page.colour_near(self.pixels(60, 168, 400, 172), "2A6DC0", 30), 0)  # nothing between header and rows


class EdgeTest(SequenceCase):
    def test_an_empty_squad_one_row_and_a_lone_open_bar_draw_without_errors(self):
        empty = Fixture()
        self.addCleanup(empty.close)
        self.browser.open(self.url(empty.start(now=self.now)))
        self.assertEqual(self.browser.eval(NAN_JS), [])
        self.assertEqual(self.seq(), {"rows": [], "bars": [], "tasks": []})
        one = Fixture()
        self.addCleanup(one.close)
        one.roster([{"agent": "manager", "role": "Manager", "scope": "all"}, {"agent": "dev-a"}])
        one.iteration(1, page.QUIET_CHECKIN)
        one.message(**{"from": "manager", "to": "dev-a", "type": "ASK", "task": "T-1"})
        self.browser.open(self.url(one.start(now="2026-10-12T11:00:00Z")))
        self.assertEqual(len(self.seq()["rows"]), 1)
        self.assertEqual(self.browser.eval(NAN_JS), [])
        self.assertEqual(self.browser.call("events")["errors"], [])

    def test_blocked_first_blocked_last_and_a_single_row_bar(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"}, {"agent": "dev-a"}, {"agent": "dev-b"}])
        fx.iteration(1, page.QUIET_CHECKIN)
        fx.activity(agent="dev-a", status="blocked")      # a blocked segment on the very first row
        fx.activity(agent="dev-b", status="working")
        fx.activity(agent="dev-b", status="idle")         # a bar on one row
        fx.activity(agent="manager", status="blocked")    # and the last
        srv = fx.start(now="2026-10-12T11:00:00Z")
        self.browser.open(self.url(srv))
        state = srv.state()
        self.assertEqual(state["rows"][0]["status"], "blocked")
        self.assertEqual(state["rows"][-1]["status"], "blocked")
        self.assertEqual(self.browser.eval(NAN_JS), [])
        self.assertEqual(self.browser.call("events")["errors"], [])
        x = self.cx("dev-a")
        self.assertGreater(page.colour_near(self.pixels(x - 6, 186, x + 6, 200), "DB3B22", 45), 5)

    def test_a_row_naming_an_agent_that_has_no_column_is_skipped_quietly(self):
        patch = """
          const ghost = {id: state.rows.length, kind: 'message', ts: state.now, from: 'ghost', to: 'manager', type: 'ASK',
                         task: 'T-G', text: 'x', msg_id: 'ghost-1'};
          state.rows.push(ghost, {id: ghost.id + 1, kind: 'status', ts: state.now, agent: 'ghost', status: 'working'});
          state.bars.push({agent: 'ghost', start_row: 0, end_row: null, start_ts: state.now, end_ts: null,
                           self_start: true, open: true, duration_s: 1, blocked: []});
          return state;"""
        self.browser.call("openPatched", url=self.url(), patch=patch)
        self.browser.wait(page.LIVE_JS)
        self.assertEqual(self.browser.eval(NAN_JS), [])
        self.assertEqual(self.browser.call("events")["errors"], [])
        self.assertEqual(len(self.seq()["rows"]), len(self.srv.state()["rows"]) + 2)

    def test_bar_rows_outside_the_row_list_are_clamped(self):
        patch = """
          state.bars.push({agent: 'manager', start_row: -4, end_row: 99999, start_ts: state.now, end_ts: state.now,
                           self_start: false, open: false, duration_s: 3, blocked: [{start_row: 99998, end_row: 99999,
                           start_ts: state.now, end_ts: state.now, duration_s: 1}]});
          return state;"""
        self.browser.call("openPatched", url=self.url(), patch=patch)
        self.browser.wait(page.LIVE_JS)
        self.assertEqual(self.browser.eval(NAN_JS), [])
        self.assertEqual(self.browser.call("events")["errors"], [])

    def test_a_hostile_label_name_and_task_id_stay_text(self):
        hostile = "<img src=x onerror=alert(1)>"
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"}, {"agent": hostile}])
        fx.iteration(1, page.QUIET_CHECKIN)
        fx.message(**{"from": "manager", "to": hostile, "type": "ASK", "task": "<b>x</b>"})
        fx.message(**{"from": hostile, "to": "manager", "type": hostile, "task": hostile})
        fx.activity(agent="manager", status="idle")
        fx.activity(agent=hostile, status="idle")
        self.browser.open(self.url(fx.start(now="2026-10-12T11:00:00Z")))
        self.browser.call("sleep", ms=300)
        self.assertEqual(self.browser.call("events")["dialogs"], [])
        self.assertEqual(self.browser.eval("document.querySelectorAll('img, b').length"), 0)
        drawn = self.drawn()
        self.assertIn("ASK <b>x</b>", drawn)
        self.assertTrue([t for t in drawn if t.startswith("<img src=x onerror")])
        texts = [r["text"] for r in self.seq()["rows"]]
        self.assertIn("ASK <b>x</b> manager → " + hostile, texts)
        self.assertIn(hostile + " " + hostile + " " + hostile + " → manager", texts)
        self.assertIn("<b>x</b>", [t["data"]["taskId"] for t in self.seq()["tasks"]])
        self.assertEqual(self.browser.eval(NAN_JS), [])


class LiftedHelperTest(SequenceCase):
    def run_js(self, call):
        source = lifted("fmtDuration", "gapText", "messageLabel", "statusText")
        return self.browser.eval("(() => { %s return %s; })()" % (source, call))

    def test_durations_are_seconds_minutes_and_hours(self):
        self.browser.open(self.url(self.quiet_server()))
        for seconds in (0, 1, 12, 59, 60, 61, 245, 3599, 3600, 3720, 7260, 90000):
            self.assertEqual(self.run_js("fmtDuration(%d)" % seconds), duration(seconds), seconds)
        self.assertEqual(self.run_js("fmtDuration(-5)"), "0s")
        self.assertEqual(self.run_js("fmtDuration(4.6)"), "5s")

    def test_gaps_read_minutes_and_under_a_minute_seconds(self):
        self.browser.open(self.url(self.quiet_server()))
        for seconds, text in ((45, "⋯ 45 s quiet"), (0, "⋯ 0 s quiet"), (60, "⋯ 1 min quiet"),
                              (181, "⋯ 3 min quiet"), (395, "⋯ 7 min quiet"), (840, "⋯ 14 min quiet"),
                              (20, "⋯ 20 s quiet")):
            self.assertEqual(self.run_js("gapText(%d)" % seconds), text)

    def test_labels_and_status_texts(self):
        self.browser.open(self.url(self.quiet_server()))
        self.assertEqual(self.run_js("messageLabel({type: 'ASK', task: 'T-1'})"), "ASK T-1")
        self.assertEqual(self.run_js("messageLabel({type: 'ASK', task: null})"), "ASK")
        self.assertEqual(self.run_js("messageLabel({type: null, task: null})"), "msg")
        self.assertEqual(self.run_js("statusText({status: 'idle', duration_s: 245})"), "idle · 4m 05s")
        self.assertEqual(self.run_js("statusText({status: 'working'})"), "working")


if __name__ == "__main__":
    unittest.main()
