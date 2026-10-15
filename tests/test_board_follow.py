"""BRD-14: the page follows new rows, pauses on a user scroll, and replays another iteration.

Browser tests (headless Chromium through node and playwright-core, like test_board_page.py) read
the text mirror hooks `#live-state`, `#live-button`, `#iteration-picker` and `#replay-banner`, and
the page's own scroll position. Skipped, with the reason, where the browser is missing.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import test_board_page as page
from board_fixture import Fixture

ROW_H = 30  # the page grows by this much for every row (E20)

# The page tests' driver plus what these tests need: real wheel, key and scrollbar input, scrollbars
# that really exist, a slow /state answer, a script that runs before the page, and screenshots.
FOLLOW_DRIVER = page.DRIVER_JS.replace(
    "browser = await chromium.launch(chrome ? { executablePath: chrome } : {});",
    "browser = await chromium.launch(Object.assign({ ignoreDefaultArgs: ['--hide-scrollbars'] },"
    " chrome ? { executablePath: chrome } : {}));").replace(
    "  async sleep(", """  async wheel({ dy }) { await page.mouse.move(400, 400); await page.mouse.wheel(0, dy); },
  async press({ key }) { await page.keyboard.press(key); },
  async focus({ selector }) { await page.focus(selector); },
  async select({ selector, value }) { await page.selectOption(selector, value); },
  async click({ selector }) { await page.click(selector); },
  async drag({ x, y1, y2 }) {
    await page.mouse.move(x, y1); await page.mouse.down(); await page.mouse.move(x, y2, { steps: 5 });
  },
  async mouseUp() { await page.mouse.up(); },
  async shot({ path }) { await page.screenshot({ path }); },
  async delay({ regex, ms }) {
    await page.route(new RegExp(regex), async (route) => {
      await new Promise((done) => setTimeout(done, ms));
      await route.continue();
    });
  },
  async fail({ regex, ms = 0, times = 1 }) {
    let left = times;
    await page.route(new RegExp(regex), async (route) => {
      if (left-- <= 0) return route.continue();
      await new Promise((done) => setTimeout(done, ms));
      await route.fulfill({ status: 500, contentType: 'application/json', body: '{"error": "boom"}' });
    });
  },
  async init({ js }) { extraInit = js; },
  async sleep(""", 1).replace(
    "let browser, context, page, events;", "let browser, context, page, events, extraInit = null;", 1).replace(
    "    await page.goto(url);",
    "    if (extraInit) await page.addInitScript({ content: extraInit });\n    await page.goto(url);", 1)

# every EventSource the page opens, and every scroll listener it adds to the window
SPY_JS = """
window.__streams = [];
const ES = window.EventSource;
window.EventSource = class extends ES {
  constructor(url, options) { super(url, options); window.__streams.push(this); }
};
window.__scrollListeners = 0;
const add = window.addEventListener.bind(window);
window.addEventListener = (type, ...rest) => { if (type === 'scroll') window.__scrollListeners++; return add(type, ...rest); };
"""
OPEN_STREAMS_JS = "window.__streams.filter((s) => s.readyState !== 2).map((s) => new URL(s.url).search)"

STATUS_JS = """(() => {
  const button = document.querySelector('#live-button');
  const banner = document.querySelector('#replay-banner');
  return {
    following: document.querySelector('#live-state').dataset.following,
    text: document.querySelector('#live-state').textContent,
    buttonShown: !button.hidden, newRows: button.dataset.newRows, buttonText: button.textContent,
    banner: banner ? banner.textContent : null,
    picker: document.querySelector('#iteration-picker').value,
    options: [...document.querySelectorAll('#iteration-picker option')].map((o) => [o.value, o.textContent]),
  };
})()"""
METRICS_JS = """(() => {
  const root = document.documentElement;
  return { y: window.scrollY, height: root.scrollHeight, view: root.clientHeight,
           left: root.scrollHeight - root.clientHeight - window.scrollY };
})()"""
# a real wheel event arms the page's "this is the user" window; the scroll that follows is ours to place
USER_SCROLL_TO_JS = """((distance) => {
  window.dispatchEvent(new WheelEvent('wheel', { deltaY: -1 }));
  const root = document.documentElement;
  window.scrollTo(0, root.scrollHeight - root.clientHeight - distance);
})(%d)"""
PROGRAMMATIC_SCROLL_TO_JS = "window.scrollTo(0, %d)"


class FollowBrowser(page.Browser):
    at_top = False  # the follow tests start where a live page starts: at the bottom

    def __init__(self, core, chrome):
        env = dict(os.environ, PLAYWRIGHT_CORE=core)
        self.script = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False)
        self.script.write(FOLLOW_DRIVER)
        self.script.close()
        self.proc = subprocess.Popen(["node", self.script.name], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     universal_newlines=True, env=env, cwd=tempfile.gettempdir())
        self.call("launch", chrome=chrome)


class FollowCase(page.PageFixtureCase):
    browser = None

    @classmethod
    def setUpClass(cls):
        core, chrome = page.find_playwright(), page.find_chrome()
        if not (core and chrome and shutil.which("node")):
            raise unittest.SkipTest("browser tests need node, playwright-core (PLAYWRIGHT_CORE) and a Chromium "
                                    "build (CHROME_PATH)")
        cls.browser = FollowBrowser(core, chrome)

    @classmethod
    def tearDownClass(cls):
        if cls.browser:
            cls.browser.close()

    def setUp(self):
        super().setUp()
        self.browser.call("init", js=SPY_JS)
        self.next_second = 0

    def open(self, srv=None, **kw):
        self.browser.open((srv or self.srv).base + "/", **kw)
        self.browser.call("sleep", ms=100)

    def status(self):
        return self.browser.eval(STATUS_JS)

    def metrics(self):
        return self.browser.eval(METRICS_JS)

    def sleep(self, ms=250):
        self.browser.call("sleep", ms=ms)

    def to_bottom(self):
        self.browser.eval("window.scrollTo(0, document.documentElement.scrollHeight)")
        self.sleep(100)

    def wheel_up(self, pixels=300):
        self.browser.call("wheel", dy=-pixels)
        self.sleep(500)  # longer than the page's 400 ms "this is the user" window

    def pause(self):
        """Scroll up with the wheel until paused; the page must say so."""
        self.wheel_up()
        for _ in range(10):  # a loaded machine can take longer than the 500 ms to deliver the wheel
            if self.status()["following"] == "false":
                break
            self.sleep(300)
        self.assertEqual(self.status()["following"], "false")

    def message(self, fx=None, **fields):
        """Append one row-making message to iteration 3 of the fixture, 1 s after the last one."""
        self.next_second += 1
        sec = 11 * 3600 + 10 * 60 + 47 + self.next_second
        ts = "2026-10-12T%02d:%02d:%02d.000Z" % (sec // 3600, sec % 3600 // 60, sec % 60)
        rec = {"ts": ts, "msg_id": "fl-%d" % self.next_second, "from": "tech-shop", "to": "dev-shop-1",
               "type": None, "task": None, "text": "new row %d" % self.next_second, "iteration": 3}
        rec.update(fields)
        (fx or self.fx).append_jsonl("messages.jsonl", rec)

    def wait_height(self, grew_by_rows, before):
        """Wait until the page is `grew_by_rows` rows taller than `before` (the stream delivered them)."""
        self.browser.wait("document.documentElement.scrollHeight >= %d" % (before + grew_by_rows * ROW_H))
        self.sleep(100)

    def row_count(self, iteration=3):
        return len(self.srv.state(iteration)["rows"])

    def open_streams(self):
        return self.browser.eval(OPEN_STREAMS_JS)

    def requests(self):
        return [u.replace(self.srv.base, "") for u in self.browser.call("events")["requests"]]

    def choose(self, value):
        self.browser.call("select", selector="#iteration-picker", value=str(value))


class FollowTest(FollowCase):
    def test_the_page_opens_at_the_bottom_following(self):
        self.open()
        m = self.metrics()
        self.assertGreater(m["height"], m["view"] * 3)  # the fixture is long enough to scroll
        self.assertLessEqual(m["left"], 40)
        s = self.status()
        self.assertEqual((s["following"], s["text"], s["buttonShown"]), ("true", "Live", False))
        self.assertEqual(s["newRows"], "0")

    def test_a_new_row_keeps_the_bottom_in_view_without_any_scrolling(self):
        self.open()
        before = self.metrics()["height"]
        self.message()
        self.wait_height(1, before)
        self.assertLessEqual(self.metrics()["left"], 40)
        self.assertEqual((self.status()["text"], self.status()["newRows"]), ("Live", "0"))  # nothing is "new" while following
        self.assertEqual(self.browser.call("events")["errors"], [])

    def test_a_wheel_up_pauses_and_the_view_does_not_move_for_new_rows(self):
        self.open()
        self.pause()
        s = self.status()
        self.assertEqual((s["text"], s["buttonShown"], s["newRows"]), ("Paused", True, "0"))
        before = self.metrics()
        self.message()
        self.message()
        self.wait_height(2, before["height"])
        after = self.metrics()
        self.assertEqual(after["y"], before["y"])
        self.assertEqual(self.status()["newRows"], "2")
        self.assertEqual(self.status()["buttonText"], "↓ live · 2")

    def test_every_scroll_key_is_the_user(self):
        for key in ("PageUp", "PageDown", "Home", "ArrowUp", "ArrowDown", " "):
            with self.subTest(key=key):
                self.open()
                self.browser.eval(PROGRAMMATIC_SCROLL_TO_JS % 3000)  # the middle: far from both ends
                self.sleep(100)
                self.assertEqual(self.status()["following"], "true")  # the page's own scroll changed nothing
                self.browser.call("press", key=key)
                self.sleep(500)
                self.assertEqual(self.status()["following"], "false")

    def test_a_scrollbar_drag_pauses(self):
        self.open()
        width = self.browser.eval("document.documentElement.clientWidth")
        self.browser.call("drag", x=width + 6, y1=700, y2=100)
        self.sleep(300)
        self.assertEqual(self.status()["following"], "false")
        self.browser.call("mouseUp")

    def test_after_a_drag_a_scroll_of_the_pages_own_is_not_the_user(self):
        self.open()
        width = self.browser.eval("document.documentElement.clientWidth")
        self.browser.call("drag", x=width + 6, y1=700, y2=100)
        self.browser.call("mouseUp")
        self.assertEqual(self.status()["following"], "false")
        self.browser.call("move", x=300, y=300)  # the drag is over
        self.to_bottom()  # our own scroll: it must not be taken for a drag that went on
        self.assertEqual(self.status()["following"], "false")

    def test_a_scroll_the_page_makes_itself_never_flips_following(self):
        self.open()
        self.browser.eval(PROGRAMMATIC_SCROLL_TO_JS % 0)
        self.sleep(300)
        self.assertEqual(self.status()["following"], "true")  # scrolled to the top, still "Live"
        self.to_bottom()
        self.pause()
        self.to_bottom()
        self.sleep(300)
        self.assertEqual(self.status()["following"], "false")  # scrolled to the bottom, still "Paused"

    def test_a_key_on_the_picker_is_not_a_scroll_by_the_user(self):
        self.open()
        self.browser.call("focus", selector="#iteration-picker")
        self.browser.call("press", key="ArrowDown")  # the last option: nothing changes
        self.browser.eval(PROGRAMMATIC_SCROLL_TO_JS % 0)
        self.sleep(300)
        self.assertEqual(self.status()["following"], "true")

    def test_an_unrelated_key_is_not_a_scroll_by_the_user(self):
        self.open()
        self.browser.call("press", key="a")
        self.browser.eval(PROGRAMMATIC_SCROLL_TO_JS % 0)
        self.sleep(300)
        self.assertEqual(self.status()["following"], "true")

    def test_exactly_40_px_from_the_bottom_follows_and_41_pauses(self):
        self.open()
        for distance, expected in ((40, "true"), (41, "false"), (40, "true"), (0, "true"), (300, "false")):
            with self.subTest(distance=distance):
                self.browser.eval(USER_SCROLL_TO_JS % distance)
                self.sleep(150)
                self.assertEqual(self.status()["following"], expected)
                self.assertEqual(round(self.metrics()["left"]), distance)

    def test_a_page_shorter_than_the_window_is_following(self):
        srv = self.small_server()
        self.open(srv)
        m = self.metrics()
        self.assertLessEqual(m["height"], m["view"])
        self.browser.eval("window.dispatchEvent(new WheelEvent('wheel', { deltaY: -1 })); "
                          "window.dispatchEvent(new Event('scroll'))")
        self.sleep(100)
        self.assertEqual(self.status()["following"], "true")

    def small_server(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"}, {"agent": "dev-shop-1"}])
        fx.iteration(1, page.QUIET_CHECKIN)
        fx.activity(agent="manager", status="idle")
        fx.activity(agent="dev-shop-1", status="idle")
        return fx.start(now=self.now)

    def test_with_a_single_iteration_the_picker_works_and_there_is_no_banner(self):
        srv = self.small_server()
        self.open(srv)
        s = self.status()
        self.assertEqual(s["options"], [["1", "Iteration 1"]])
        self.assertEqual((s["picker"], s["banner"]), ("1", None))
        self.choose(1)
        self.sleep(300)
        self.assertEqual(self.status()["banner"], None)
        self.assertEqual(self.open_streams(), ["?iteration=1"])

    def test_scrolling_back_to_the_bottom_by_hand_follows_again_and_clears_the_count(self):
        self.open()
        self.pause()
        before = self.metrics()["height"]
        self.message()
        self.wait_height(1, before)
        self.assertEqual(self.status()["newRows"], "1")
        self.browser.call("press", key="End")
        self.sleep(500)
        s = self.status()
        self.assertEqual((s["following"], s["newRows"], s["buttonShown"]), ("true", "0", False))

    def test_the_count_is_exact_across_updates_and_resets_after_live(self):
        self.open()
        self.pause()
        expected = 0
        for batch in (1, 2, 5):
            before = self.metrics()["height"]
            rows_before = self.row_count()
            for _ in range(batch):
                self.message()
            self.browser.wait("document.documentElement.scrollHeight > %d" % before)
            self.sleep(400)  # the batch may arrive as several state updates
            expected += self.row_count() - rows_before
            self.assertEqual(self.status()["newRows"], str(expected))
        self.assertEqual(expected, 8)
        self.browser.call("click", selector="#live-button")
        self.sleep(200)
        s = self.status()
        self.assertEqual((s["newRows"], s["buttonShown"], s["following"]), ("0", False, "true"))
        self.pause()
        self.assertEqual(self.status()["newRows"], "0")

    def test_a_gap_row_counts_as_a_row(self):
        self.open()
        self.pause()
        before = self.metrics()["height"]
        rows_before = self.row_count()
        self.message(ts="2026-10-12T11:15:00.000Z")  # 4 min after the last row: a gap row, then the message
        self.wait_height(1, before)
        self.sleep(300)
        self.assertEqual(self.row_count() - rows_before, 2)
        self.assertEqual(self.status()["newRows"], "2")

    def test_the_live_button_jumps_to_the_bottom_and_goes_away(self):
        self.open()
        self.pause()
        before = self.metrics()["height"]
        self.message()
        self.wait_height(1, before)
        self.browser.call("click", selector="#live-button")
        self.sleep(300)
        s = self.status()
        self.assertEqual((s["text"], s["buttonShown"], s["following"]), ("Live", False, "true"))
        self.assertLessEqual(self.metrics()["left"], 40)

    def test_resize_never_flips_following(self):
        self.open()
        self.browser.call("viewport", width=1100, height=500)
        self.sleep(300)
        self.assertEqual(self.status()["following"], "true")
        self.assertLessEqual(self.metrics()["left"], 40)  # a following page keeps the bottom in view
        self.to_bottom()
        self.pause()
        y = self.metrics()["y"]
        self.browser.call("viewport", width=1280, height=800)
        self.sleep(300)
        self.assertEqual(self.status()["following"], "false")
        self.assertEqual(self.status()["newRows"], "0")
        self.assertEqual(self.metrics()["y"], y)  # a paused view stays where the reader left it

    def test_the_mirror_has_no_nan_and_the_console_is_clean(self):
        self.open()
        self.assertNotIn("NaN", self.browser.eval("document.querySelector('#board-text').textContent"))
        self.assertEqual(self.status()["buttonText"], "↓ live")
        self.assertEqual(self.browser.call("events")["errors"], [])

    def test_rows_that_vanish_are_not_counted_as_new(self):
        self.open()
        self.pause()
        path = self.fx.root / "messages.jsonl"
        lines = path.read_text().splitlines(True)
        path.write_text("".join(lines[:-3]))
        self.browser.wait("document.documentElement.scrollHeight < %d" % self.metrics()["height"])
        self.sleep(300)
        self.assertEqual(self.status()["newRows"], "0")

    def test_a_dropped_stream_while_paused_keeps_paused_and_the_count(self):
        self.open()
        self.pause()
        before = self.metrics()
        self.message()
        self.wait_height(1, before["height"])
        port = self.srv.port
        count = self.status()["newRows"]
        y = self.metrics()["y"]
        self.srv.stop()
        self.browser.wait(page.RECONNECTING_JS)
        self.fx.start(now=self.now, port=port)
        self.browser.wait(page.LIVE_JS, timeout=15000)
        self.sleep(300)
        s = self.status()
        self.assertEqual((s["following"], s["newRows"]), ("false", count))
        self.assertEqual(self.metrics()["y"], y)


class PickerTest(FollowCase):
    def test_the_options_are_the_iterations_of_the_state_and_the_current_one_is_selected(self):
        self.open()
        s = self.status()
        self.assertEqual(s["options"], [[str(n), "Iteration %d" % n] for n in self.srv.state()["iterations"]])
        self.assertEqual((s["picker"], s["banner"]), ("3", None))

    def test_an_iteration_that_is_not_offered_is_not_requested(self):
        self.open()
        self.browser.eval("""(() => {
          const option = document.createElement('option'); option.value = '99'; option.textContent = 'x';
          const picker = document.querySelector('#iteration-picker');
          picker.append(option); picker.value = '99'; picker.dispatchEvent(new Event('change'));
        })()""")
        self.sleep(300)
        self.assertFalse([u for u in self.requests() if "iteration=99" in u])
        self.assertEqual(self.status()["picker"], "3")
        self.assertEqual(self.open_streams(), ["?iteration=3"])

    def test_choosing_an_old_iteration_replays_it_and_stops_following(self):
        self.open()
        self.choose(1)
        self.browser.wait("document.querySelector('#replay-banner') !== null")
        self.sleep(300)
        s = self.status()
        self.assertEqual(s["banner"], "Replay of iteration 1")
        self.assertEqual((s["picker"], s["text"], s["following"], s["buttonShown"]), ("1", "Paused", "false", True))
        self.assertEqual(self.open_streams(), ["?iteration=1"])
        urls = self.requests()
        self.assertIn("/state?iteration=1", urls)
        self.assertIn("/events?iteration=1", urls)
        self.assertEqual(self.browser.call("events")["errors"], [])

    def test_a_choice_clears_the_count_of_the_view_it_leaves(self):
        self.open()
        self.pause()
        before = self.metrics()["height"]
        self.message()
        self.wait_height(1, before)
        self.assertEqual(self.status()["newRows"], "1")
        self.choose(1)
        self.browser.wait("document.querySelector('#replay-banner') !== null")
        self.sleep(300)
        self.assertEqual(self.status()["newRows"], "0")

    def test_the_options_are_not_rebuilt_by_a_state_update_that_leaves_the_list_alone(self):
        self.open()
        self.browser.eval("document.querySelector('#iteration-picker option').mark = 1")
        before = self.metrics()["height"]
        self.message()
        self.wait_height(1, before)
        self.assertEqual(self.browser.eval("document.querySelector('#iteration-picker option').mark"), 1)

    def test_one_banner_however_many_updates_arrive_in_a_replay(self):
        self.open()
        self.choose(1)
        self.browser.wait("document.querySelector('#replay-banner') !== null")
        self.fx.iteration(1, (self.fx.root / "iterations" / "1.md").read_text() + "\nmore\n")
        self.sleep(800)
        self.assertEqual(self.browser.eval("document.querySelectorAll('#replay-banner').length"), 1)

    def test_the_picker_shows_the_choice_at_once_and_the_old_stream_is_closed_while_the_answer_is_awaited(self):
        self.open()
        self.choose(1)
        self.browser.wait("document.querySelector('#replay-banner') !== null")
        self.browser.call("delay", regex=r"/state\?iteration=3$", ms=1500)
        self.browser.call("click", selector="#live-button")  # back to 3, slowly
        self.sleep(200)
        self.assertEqual(self.status()["picker"], "3")
        self.assertEqual(self.open_streams(), [])
        self.browser.wait("document.querySelector('#replay-banner') === null", timeout=5000)
        self.assertEqual(self.open_streams(), ["?iteration=3"])

    def test_an_error_answer_is_not_taken_for_a_state_and_the_choice_is_retried(self):
        self.open()
        self.browser.call("fail", regex=r"/state\?iteration=1$", times=1)
        self.choose(1)
        self.browser.wait(page.RECONNECTING_JS)
        self.browser.wait("document.querySelector('#replay-banner') !== null", timeout=8000)
        self.browser.wait(page.LIVE_JS, timeout=8000)
        self.assertEqual(len(self.browser.call("events")["errors"]), 1)  # only the browser's own note of the 500
        self.assertEqual(self.open_streams(), ["?iteration=1"])

    def test_an_older_choice_that_fails_late_does_not_start_a_retry(self):
        self.open()
        self.browser.call("fail", regex=r"/state\?iteration=2$", ms=700, times=1)
        self.choose(2)
        self.sleep(100)
        self.choose(1)
        self.browser.wait("document.querySelector('#replay-banner') !== null")
        self.sleep(1200)  # the failure of 2 has come by now
        self.assertEqual(self.browser.eval("document.querySelector('#connection-state').dataset.state"), "live")
        self.assertEqual(self.status()["banner"], "Replay of iteration 1")
        self.assertEqual(self.open_streams(), ["?iteration=1"])

    def test_the_replay_has_the_rows_of_that_iteration(self):
        self.open()
        full = self.metrics()["height"]
        self.choose(1)
        self.browser.wait("document.querySelector('#replay-banner') !== null")
        self.sleep(300)
        rows = len(self.srv.state(1)["rows"])
        self.assertLess(rows, self.row_count())
        self.assertLess(self.metrics()["height"], full)
        self.assertEqual(self.metrics()["height"] - (180 + 24), rows * ROW_H)

    def test_header_totals_stay_whole_run_in_a_replay(self):
        self.open()
        shown = self.mirror_columns()
        self.assertEqual([c["working_s"] for c in self.srv.state(1)["columns"]],
                         [c["working_s"] for c in self.srv.state(3)["columns"]])
        self.choose(1)
        self.browser.wait("document.querySelector('#replay-banner') !== null")
        self.sleep(300)
        self.assertEqual(self.mirror_columns(), shown)

    def mirror_columns(self):
        return self.browser.eval("[...document.querySelectorAll('#columns li')].map((li) => li.textContent)")

    def test_choosing_the_current_iteration_again_removes_the_banner_and_follows(self):
        self.open()
        self.choose(1)
        self.browser.wait("document.querySelector('#replay-banner') !== null")
        self.choose(3)
        self.browser.wait("document.querySelector('#replay-banner') === null")
        self.sleep(300)
        s = self.status()
        self.assertEqual((s["picker"], s["text"], s["following"], s["buttonShown"]), ("3", "Live", "true", False))
        self.assertLessEqual(self.metrics()["left"], 40)
        self.assertEqual(self.open_streams(), ["?iteration=3"])

    def test_the_live_button_in_a_replay_returns_to_the_current_iteration(self):
        self.open()
        self.choose(2)
        self.browser.wait("document.querySelector('#replay-banner') !== null")
        self.browser.call("click", selector="#live-button")
        self.browser.wait("document.querySelector('#replay-banner') === null")
        self.sleep(300)
        s = self.status()
        self.assertEqual((s["picker"], s["following"]), ("3", "true"))
        self.assertEqual(self.open_streams(), ["?iteration=3"])

    def test_scrolling_to_the_bottom_of_a_replay_does_not_make_it_live(self):
        self.open()
        self.choose(1)
        self.browser.wait("document.querySelector('#replay-banner') !== null")
        self.sleep(300)
        self.browser.call("press", key="End")
        self.sleep(500)
        self.assertEqual(self.status()["following"], "false")
        self.assertEqual(self.status()["banner"], "Replay of iteration 1")

    def test_three_quick_choices_leave_one_stream_and_the_last_choice(self):
        self.open()
        self.browser.eval("""(() => {
          const picker = document.querySelector('#iteration-picker');
          for (const value of ['1', '2', '1']) { picker.value = value; picker.dispatchEvent(new Event('change')); }
        })()""")
        self.sleep(800)
        s = self.status()
        self.assertEqual((s["picker"], s["banner"]), ("1", "Replay of iteration 1"))
        self.assertEqual(self.open_streams(), ["?iteration=1"])
        self.assertEqual(len([u for u in self.requests() if u.startswith("/events")]), 2)  # 3 at load, 1 now

    def test_a_late_answer_to_an_older_choice_is_ignored(self):
        self.open()
        self.browser.call("delay", regex=r"/state\?iteration=2$", ms=1200)
        self.choose(2)
        self.sleep(100)
        self.choose(1)
        self.browser.wait("document.querySelector('#replay-banner') !== null")
        self.sleep(1700)  # the answer for 2 has arrived by now
        s = self.status()
        self.assertEqual((s["picker"], s["banner"]), ("1", "Replay of iteration 1"))
        self.assertEqual(self.open_streams(), ["?iteration=1"])
        self.assertFalse([u for u in self.requests() if u == "/events?iteration=2"])

    def test_no_stream_or_listener_is_left_behind_by_ten_choices(self):
        self.open()
        listeners = self.browser.eval("window.__scrollListeners")
        for i in range(10):
            self.choose(1 + i % 2)
            self.sleep(120)
        self.sleep(500)
        self.assertEqual(self.browser.eval("window.__scrollListeners"), listeners)
        self.assertEqual(len(self.open_streams()), 1)
        self.assertEqual(self.browser.eval("window.__streams.filter((s) => s.readyState === 1).length"), 1)

    def test_a_retry_of_an_older_stream_does_nothing_after_another_choice(self):
        self.open()
        port = self.srv.port
        self.srv.stop()
        self.browser.wait(page.RECONNECTING_JS)
        self.sleep(1400)  # the first retry failed; the next one is 2 s later
        self.fx.start(now=self.now, port=port)
        self.choose(1)
        self.browser.wait("document.querySelector('#replay-banner') !== null", timeout=5000)
        before = len(self.requests())
        self.sleep(3000)  # the old retry fires in here
        self.assertEqual(self.open_streams(), ["?iteration=1"])
        self.assertFalse([u for u in self.requests()[before:] if u == "/events?iteration=3"])
        self.assertEqual(self.status()["banner"], "Replay of iteration 1")

    def test_a_failed_state_request_for_a_choice_is_retried(self):
        self.open()
        port = self.srv.port
        self.srv.stop()
        self.choose(1)
        self.browser.wait(page.RECONNECTING_JS)
        self.fx.start(now=self.now, port=port)
        self.browser.wait("document.querySelector('#replay-banner') !== null", timeout=15000)
        self.browser.wait(page.LIVE_JS, timeout=15000)
        self.assertEqual(self.open_streams(), ["?iteration=1"])

    def test_a_newer_iteration_appears_while_viewing_the_one_before(self):
        self.open()
        self.fx.iteration(4)
        self.browser.wait("document.querySelector('#replay-banner') !== null")
        self.sleep(300)
        s = self.status()
        self.assertEqual(s["banner"], "Replay of iteration 3")
        self.assertEqual((s["picker"], s["following"], s["buttonShown"]), ("3", "false", True))
        self.assertEqual(s["options"][-1], ["4", "Iteration 4"])
        self.browser.call("click", selector="#live-button")
        self.browser.wait("document.querySelector('#replay-banner') === null")
        self.sleep(300)
        s = self.status()
        self.assertEqual((s["picker"], s["following"]), ("4", "true"))
        self.assertEqual(self.open_streams(), ["?iteration=4"])

    def test_a_reload_on_a_replay_returns_to_the_current_iteration(self):
        self.open()
        self.choose(1)
        self.browser.wait("document.querySelector('#replay-banner') !== null")
        self.browser.call("reload")
        self.browser.wait(page.LIVE_JS)
        self.sleep(300)
        s = self.status()
        self.assertEqual((s["picker"], s["banner"]), ("3", None))
        # the picked iteration is not stored; the alerts' list of seen items (BRD-16) is the one key allowed
        self.assertEqual(self.browser.eval("[Object.keys(localStorage).map((k) => k.split(':')[0]), sessionStorage.length]"),
                         [["squad-board.seen"], 0])

    def test_history_survives_closing_and_reopening_the_page(self):
        self.open()
        first = self.mirror_columns()
        height = self.metrics()["height"]
        self.open()
        self.assertEqual(self.mirror_columns(), first)
        self.assertEqual(self.metrics()["height"], height)


# A state update for the page's own EventSource: `prepare(extra)` fetches the current state with `extra` more
# rows (cloned from the last one), `deliver(data)` hands it to the stream synchronously, so a test can place the
# update exactly between a gesture and its scroll event.
STATE_JS = """
const prepare = async (extra) => {
  const next = await (await fetch('/state', { cache: 'no-store' })).json();
  const last = next.rows[next.rows.length - 1];
  for (let i = 0; i < extra; i++) next.rows.push(JSON.parse(JSON.stringify(last)));
  return JSON.stringify(next);
};
const deliver = (data) => window.__streams.filter((s) => s.readyState !== 2).pop()
  .dispatchEvent(new MessageEvent('state', { data }));
"""
FRAMES_JS = "new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)))"


class RaceTest(FollowCase):
    """A state update or a resize that lands after the user's gesture but before its scroll event (one task,
    so no timing is involved) must not pin the bottom again. The scroll event is delivered with the next
    frame, after microtasks, which is exactly the gap."""

    def race(self, gesture, update):
        """The gesture scrolls to the top, then `update` runs, all in one task; then two frames pass."""
        self.open()
        m = self.metrics()
        self.assertGreater(m["height"], m["view"] * 3)
        self.assertEqual(self.status()["following"], "true")
        self.browser.eval("""(async () => {
          %s
          const data = await prepare(1);
          %s
          window.scrollTo(0, 0);
          %s
          await %s;
        })()""" % (STATE_JS, gesture, update, FRAMES_JS))
        self.sleep(100)
        self.assertEqual(self.status()["following"], "false")
        self.assertEqual(self.status()["buttonShown"], True)
        self.assertEqual(self.metrics()["y"], 0)

    WHEEL = "window.dispatchEvent(new Event('wheel'));"
    STATE = "deliver(data);"
    RESIZE = "window.dispatchEvent(new Event('resize'));"

    def test_a_state_update_between_a_wheel_and_its_scroll_does_not_pin_the_bottom(self):
        self.race(self.WHEEL, self.STATE)

    def test_a_resize_between_a_wheel_and_its_scroll_does_not_pin_the_bottom(self):
        self.race(self.WHEEL, self.RESIZE)

    def test_a_state_update_right_after_a_scroll_key_does_not_pin_the_bottom(self):
        self.race("window.dispatchEvent(new KeyboardEvent('keydown', { key: 'PageUp' }));", self.STATE)

    def test_a_state_update_during_a_scrollbar_drag_does_not_pin_the_bottom(self):
        self.race("window.dispatchEvent(new MouseEvent('mousedown', "
                  "{ clientX: document.documentElement.clientWidth + 6 }));", self.STATE)
        self.browser.eval("window.dispatchEvent(new MouseEvent('mouseup'))")

    def test_a_state_update_while_a_real_scrollbar_drag_is_down_does_not_pin_the_bottom(self):
        self.open()
        width = self.browser.eval("document.documentElement.clientWidth")
        self.browser.call("drag", x=width + 6, y1=700, y2=100)  # the button stays down
        self.browser.eval("(async () => { %s deliver(await prepare(1)); })()" % STATE_JS)
        self.sleep(300)
        self.browser.call("mouseUp")
        self.sleep(300)
        self.assertEqual(self.status()["following"], "false")
        self.assertGreater(self.metrics()["left"], 40)

    def test_a_state_update_while_the_scrollbar_is_held_does_not_pin_even_after_the_window(self):
        self.open()
        self.browser.eval("window.dispatchEvent(new MouseEvent('mousedown', "
                          "{ clientX: document.documentElement.clientWidth + 6 })); window.scrollTo(0, 0)")
        self.sleep(600)  # past the 400 ms window: only the drag keeps the gesture alive
        self.browser.eval("(async () => { %s deliver(await prepare(1)); })()" % STATE_JS)
        self.sleep(600)
        self.assertEqual((self.status()["following"], self.metrics()["y"]), ("false", 0))
        self.browser.eval("window.dispatchEvent(new MouseEvent('mouseup'))")

    def test_a_wheel_that_moves_nothing_does_not_leave_the_page_short_of_the_new_rows(self):
        self.open()
        self.assertLessEqual(self.metrics()["left"], 1)
        before = self.metrics()["height"]
        self.browser.eval("""(async () => {
          %s
          const data = await prepare(3);
          window.dispatchEvent(new Event('wheel'));  // a wheel down at the bottom: no scroll event follows
          deliver(data);
          await %s;
        })()""" % (STATE_JS, FRAMES_JS))
        self.browser.wait("document.documentElement.scrollHeight >= %d" % (before + 3 * ROW_H))
        # the trailing pin comes when the 400 ms window ends
        self.browser.wait("document.documentElement.scrollHeight - document.documentElement.clientHeight"
                          " - window.scrollY <= 1", timeout=1500)
        self.assertEqual((self.status()["following"], self.status()["buttonShown"]), ("true", False))

    def test_the_trailing_pin_waits_for_a_second_gesture_and_is_not_taken_for_the_user(self):
        self.open()
        self.browser.eval("""(async () => {
          %s
          const data = await prepare(3);
          window.dispatchEvent(new Event('wheel'));
          deliver(data);
          await new Promise((done) => setTimeout(done, 300));
          window.dispatchEvent(new Event('wheel'));  // the window starts over; the first timer must not pin
          window.scrollTo(0, 0);
        })()""" % STATE_JS)
        self.sleep(200)  # the first window would have ended by now
        self.assertEqual(self.metrics()["y"], 0)
        self.sleep(600)
        self.assertEqual((self.status()["following"], self.metrics()["y"]), ("false", 0))


class FollowSourceTest(unittest.TestCase):
    def sections(self):
        text = page.page_text()
        a = text.index("// --- section: follow ---")
        b = text.index("// --- section: picker ---")
        c = text.index("// --- section: panel ---")
        return text[a:b], text[b:c]

    def test_neither_section_is_a_stub(self):
        follow, picker = self.sections()
        self.assertRegex(follow, r"function updateFollow\(previous, next\) \{\n  const")
        self.assertRegex(picker, r"function setupPicker\(current\) \{\n  const")

    def test_the_choice_is_not_kept_anywhere(self):
        follow, picker = self.sections()
        for text in (follow, picker):
            self.assertNotRegex(text, r"localStorage|sessionStorage|location\.|history\.|document\.cookie")

    def test_the_controls_are_built_with_textcontent_and_palette_colours(self):
        follow, picker = self.sections()
        for text in (follow, picker):
            for token in page.FORBIDDEN:
                self.assertNotIn(token, text)
        self.assertEqual({h.upper() for h in re.findall(r"#[0-9A-Fa-f]{3,8}\b", follow + picker)} - {"#FFFFFF"}, set())


if __name__ == "__main__":
    unittest.main()
