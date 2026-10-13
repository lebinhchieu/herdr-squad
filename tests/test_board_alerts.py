"""BRD-16: the page's alerts (notification, chime, tab title, seen set) in headless Chromium.

Every browser API the page uses for alerts is replaced by a recorder from an init script, so a test
reads what the page asked for. Skipped, with the reason, where node, playwright-core or Chromium is missing.
"""
import json
import re
import shutil
import unittest
from unittest import mock

import test_board_page as page
from board_fixture import Fixture

# one tab, two extra driver ops (an init script before the page loads, a click); the shared driver stays as it is
DRIVER_JS = page.DRIVER_JS
for old, new in (
    ("async open({ url, width = 1280, height = 800, dpr = 1, failFirst = 0 }) {\n    await reset(width, height, dpr);",
     "async open({ url, width = 1280, height = 800, dpr = 1, failFirst = 0, init = null }) {\n"
     "    await reset(width, height, dpr);\n    if (init) await page.addInitScript(init);"),
    ("  async move({ x, y })", "  async click({ selector }) { await page.click(selector); },\n"
     "  async shot({ path }) { await page.screenshot({ path }); },\n  async move({ x, y })"),
):
    assert old in DRIVER_JS, old
    DRIVER_JS = DRIVER_JS.replace(old, new, 1)

SEEN_KEY_JS = "'squad-board.seen:' + location.origin"

# window.__rec holds plain data of everything the page asked of Notification and AudioContext
STUBS_JS = r"""
(() => {
  const cfg = %s;
  const rec = window.__rec = { notes: [], asks: 0, contexts: 0, osc: [], gains: [], resumes: 0, rejections: [] };
  window.addEventListener('unhandledrejection', (ev) => rec.rejections.push(String(ev.reason)));
  window.__install = (cfg) => {
    if (cfg.notification === false) {
      window.Notification = undefined;
    } else {
      window.Notification = class {
        constructor(title, opts) {
          if (cfg.ctor === 'throws') throw new Error('refused');
          rec.notes.push({ title: title, body: opts && opts.body, tag: opts && opts.tag });
        }
        static requestPermission() {
          rec.asks++;
          if (cfg.ask === 'reject') return Promise.reject(new Error('no'));
          if (cfg.ask === 'throws') throw new Error('no');
          if (cfg.ask === 'none') return undefined;
          return Promise.resolve(cfg.ask);
        }
      };
      window.Notification.permission = cfg.permission;
    }
    if (cfg.audio === 'missing') {
      window.AudioContext = undefined;
      return;
    }
    window.AudioContext = class {
      constructor() {
        if (cfg.audio === 'throws') throw new Error('no audio');
        rec.contexts++;
        this.state = cfg.audio === 'closed' ? 'closed'
          : cfg.audio.startsWith('suspended') || cfg.audio.startsWith('resume') ? 'suspended' : 'running';
        this.currentTime = 10;
        this.destination = {};
      }
      resume() {
        rec.resumes++;
        if (cfg.audio === 'resume-throws') throw new Error('no');
        if (cfg.audio === 'resume-rejects') return Promise.reject(new Error('no'));
        this.state = 'running';
        return Promise.resolve();
      }
      createOscillator() {
        const o = { type: '', hz: 0, start: null, stop: null };
        rec.osc.push(o);
        return { set type(v) { o.type = v; }, frequency: { set value(v) { o.hz = v; } }, connect() {},
                 start(t) { o.start = t; }, stop(t) { o.stop = t; } };
      }
      createGain() {
        const events = [];
        rec.gains.push(events);
        return { gain: { setValueAtTime(v, t) { events.push(['set', v, t]); },
                         linearRampToValueAtTime(v, t) { events.push(['ramp', v, t]); } }, connect() {} };
      }
    };
  };
  window.__install(cfg);
  if (cfg.seed !== undefined && !sessionStorage.getItem('__seeded')) {
    sessionStorage.setItem('__seeded', '1');
    localStorage.setItem(%s, cfg.seed);
  }
  if (cfg.storage === 'throws') {
    Storage.prototype.getItem = () => { throw new Error('no storage'); };
    Storage.prototype.setItem = () => { throw new Error('no storage'); };
  }
  if (cfg.storage === 'denied') {
    Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('denied', 'SecurityError'); } });
  }
})();
"""

QUIET_AGENTS = ["dev-a-1", "dev-b-2", "dev-c-3"]


def stubs(**cfg):
    full = {"permission": "granted", "ask": "granted", "audio": "ok", "ctor": "ok"}
    full.update(cfg)
    return STUBS_JS % (json.dumps(full), SEEN_KEY_JS)


class AlertsCase(unittest.TestCase):
    browser = None

    @classmethod
    def setUpClass(cls):
        core, chrome = page.find_playwright(), page.find_chrome()
        if not (core and chrome and shutil.which("node")):
            raise unittest.SkipTest("browser tests need node, playwright-core (PLAYWRIGHT_CORE) and a Chromium build")
        with mock.patch.object(page, "DRIVER_JS", DRIVER_JS):
            cls.browser = page.Browser(core, chrome)

    @classmethod
    def tearDownClass(cls):
        if cls.browser:
            cls.browser.close()

    def setUp(self):
        """Manager and three developers, all idle, check-in filled in: nothing waits on the PO."""
        self.fx = Fixture()
        self.addCleanup(self.fx.close)
        self.fx.roster([{"agent": "manager", "role": "Manager", "scope": "all"}] + [{"agent": a} for a in QUIET_AGENTS])
        self.fx.iteration(1, page.QUIET_CHECKIN)
        for agent in ["manager"] + QUIET_AGENTS:
            self.fx.activity(agent=agent, status="idle")

    # --- helpers --------------------------------------------------------------------------------

    def start(self, **cfg):
        """Start the server (no --now: it follows the log) and open the page with the recorders."""
        self.srv = self.fx.start()
        self.browser.open(self.srv.base + "/", init=stubs(**cfg))
        return self.srv

    def rec(self):
        return self.browser.eval("window.__rec")

    def count(self):
        return int(self.browser.eval("document.querySelector('#needs-you').dataset.count"))

    def wait_count(self, n):
        self.browser.wait("document.querySelector('#needs-you').dataset.count === '%d'" % n)

    def title(self):
        return self.browser.eval("document.title")

    def block(self, agent):
        self.fx.activity(agent=agent, status="blocked")

    def resolve(self, agent):
        self.fx.activity(agent=agent, status="working")

    def seen_stored(self):
        return self.browser.eval("JSON.parse(localStorage.getItem(%s))" % SEEN_KEY_JS)

    def errors(self):
        return self.browser.call("events")["errors"] + self.rec()["rejections"]

    def chimes(self, rec=None):
        """The recorded oscillators split in chimes of two notes."""
        osc = (rec or self.rec())["osc"]
        self.assertEqual(len(osc) % 2, 0)
        return len(osc) // 2

    def button_hidden(self):
        return self.browser.eval("document.querySelector('#alerts-button').hidden")


class NewItemTest(AlertsCase):
    def test_a_blocked_agent_fires_one_notification_and_one_chime(self):
        srv = self.start()
        self.assertEqual((self.rec()["notes"], self.count(), self.title()), ([], 0, "squad board"))
        self.block("dev-a-1")
        self.wait_count(1)
        rec = self.rec()
        item = srv.state()["needs_you"][0]
        self.assertEqual(rec["notes"], [{"title": "Squad needs you", "body": "dev-a-1 is blocked", "tag": item["id"]}])
        self.assertEqual(self.chimes(rec), 1)
        self.assertEqual(self.title(), "(1) squad board")
        self.assertEqual(self.errors(), [])

    def test_the_chime_is_two_soft_sine_notes_shorter_than_600_ms(self):
        self.start()
        self.block("dev-a-1")
        self.wait_count(1)
        rec = self.rec()
        self.assertEqual([o["type"] for o in rec["osc"]], ["sine", "sine"])
        self.assertEqual(len(set(o["hz"] for o in rec["osc"])), 2)
        peaks = [e[1] for events in rec["gains"] for e in events]
        self.assertGreater(max(peaks), 0.02)  # audible
        self.assertLessEqual(max(peaks), 0.08)
        starts, stops = [o["start"] for o in rec["osc"]], [o["stop"] for o in rec["osc"]]
        self.assertGreaterEqual(min(starts), 10)  # scheduled from the context's clock, never in the past
        self.assertLess(max(stops) - min(starts), 0.6)
        self.assertLess(starts[0], starts[1])
        for o in rec["osc"]:
            self.assertGreater(o["stop"], o["start"])
        for o, events in zip(rec["osc"], rec["gains"]):  # each note fades in from silence, peaks, and fades out
            self.assertEqual((events[0][:2], events[-1][:2]), (["set", 0], ["ramp", 0]))
            self.assertTrue(o["start"] < events[1][2] < o["stop"], events)
            self.assertEqual((events[0][2], events[-1][2]), (o["start"], o["stop"]))

    def test_the_title_follows_the_count_and_a_resolved_item_is_silent(self):
        self.start()
        self.block("dev-a-1")
        self.wait_count(1)
        self.block("dev-b-2")
        self.wait_count(2)
        self.assertEqual(self.title(), "(2) squad board")
        self.resolve("dev-a-1")
        self.wait_count(1)
        self.assertEqual(self.title(), "(1) squad board")
        self.resolve("dev-b-2")
        self.wait_count(0)
        self.assertEqual(self.title(), "squad board")
        rec = self.rec()
        self.assertEqual((len(rec["notes"]), self.chimes(rec)), (2, 2))

    def test_resolved_then_a_different_new_item_notifies_only_the_new_one(self):
        self.start()
        self.block("dev-a-1")
        self.wait_count(1)
        self.resolve("dev-a-1")
        self.wait_count(0)
        self.block("dev-b-2")
        self.wait_count(1)
        rec = self.rec()
        self.assertEqual([n["body"] for n in rec["notes"]], ["dev-a-1 is blocked", "dev-b-2 is blocked"])
        self.assertEqual(self.chimes(rec), 2)

    def test_the_same_id_coming_back_does_not_notify_again_and_a_new_one_does(self):
        self.fx.escalations([{"question": "Ship it?"}])
        self.start()
        self.assertEqual((self.count(), self.rec()["notes"]), (1, []))  # present at load: seen
        self.fx.escalations([{"question": "Ship it?", "answer": "yes"}])
        self.wait_count(0)
        self.fx.escalations([{"question": "Ship it?"}])  # the same escalation:1 is open again
        self.wait_count(1)
        self.assertEqual(self.rec()["notes"], [])
        self.fx.escalations([{"question": "Ship it?"}, {"question": "And then?"}])
        self.wait_count(2)
        rec = self.rec()
        self.assertEqual([(n["body"], n["tag"]) for n in rec["notes"]], [("And then?", "escalation:2")])
        self.assertEqual(self.chimes(rec), 1)

    def test_two_new_items_in_one_update_are_two_notifications_and_one_chime(self):
        self.start()
        self.fx.escalations([{"question": "First?"}, {"question": "Second?"}])
        self.wait_count(2)
        rec = self.rec()
        self.assertEqual([n["body"] for n in rec["notes"]], ["First?", "Second?"])
        self.assertEqual([n["tag"] for n in rec["notes"]], ["escalation:1", "escalation:2"])
        self.assertEqual(self.chimes(rec), 1)

    def test_a_blocked_message_between_agents_is_not_an_item_and_fires_nothing(self):
        self.start()
        self.fx.message(**{"from": "dev-a-1", "to": "dev-b-2", "type": "BLOCKED", "task": "BRD-01", "text": "stuck"})
        self.fx.activity(agent="dev-c-3", status="working")
        self.browser.wait("document.querySelector('#columns li[data-agent=dev-c-3]').dataset.status === 'working'")
        rec = self.rec()
        self.assertEqual((rec["notes"], rec["osc"], self.count(), self.title()), ([], [], 0, "squad board"))

    def test_hostile_item_text_arrives_as_the_same_plain_string(self):
        hostile = "<img src=x onerror=alert(1)>"
        self.start()
        self.fx.escalations([{"question": hostile}])
        self.wait_count(1)
        self.browser.call("sleep", ms=300)
        self.assertEqual([n["body"] for n in self.rec()["notes"]], [hostile])
        self.assertEqual(self.browser.call("events")["dialogs"], [])
        self.assertEqual(self.browser.eval("document.querySelectorAll('img').length"), 0)

    def test_the_page_reads_notification_and_audio_context_when_it_fires_not_when_it_loads(self):
        self.start(permission="denied", audio="throws")  # what the page found at load: nothing usable
        self.browser.eval("window.__install({permission: 'granted', ask: 'granted', audio: 'ok'}); 1")
        self.block("dev-a-1")
        self.wait_count(1)
        rec = self.rec()
        self.assertEqual([n["body"] for n in rec["notes"]], ["dev-a-1 is blocked"])
        self.assertEqual(self.chimes(rec), 1)

    def test_no_request_leaves_the_server_and_none_is_for_sound(self):
        self.start()
        self.block("dev-a-1")
        self.wait_count(1)
        urls = [u.replace(self.srv.base, "") for u in self.browser.call("events")["requests"]]
        self.assertEqual([u for u in urls if not re.match(r"^/(\?|$|state|events)", u)], [])


class NoRepeatTest(AlertsCase):
    def test_items_present_at_load_notify_nothing_now_or_after_a_reload(self):
        self.block("dev-a-1")
        self.fx.escalations([{"question": "Ship it?"}])
        srv = self.start()
        ids = [n["id"] for n in srv.state()["needs_you"]]
        self.assertEqual(len(ids), 2)
        self.assertEqual((self.count(), self.rec()["notes"], self.rec()["osc"]), (2, [], []))
        self.assertEqual(self.title(), "(2) squad board")
        self.assertEqual(self.seen_stored(), ids)
        self.browser.call("reload")
        self.browser.wait(page.LIVE_JS)
        self.assertEqual((self.count(), self.rec()["notes"], self.rec()["osc"]), (2, [], []))

    def test_the_stored_set_is_ids_only_under_the_origin_key(self):
        self.fx.escalations([{"question": "Ship it?"}])
        self.start()
        self.assertEqual(self.browser.eval("Object.keys(localStorage)"), ["squad-board.seen:" + self.srv.base])
        self.assertEqual(self.seen_stored(), ["escalation:1"])

    def test_a_new_item_after_a_reload_notifies_once_and_a_reload_does_not_repeat_it(self):
        self.start()
        self.block("dev-a-1")
        self.wait_count(1)
        self.browser.call("reload")
        self.browser.wait(page.LIVE_JS)
        self.assertEqual(self.count(), 1)
        self.assertEqual(self.rec()["notes"], [])  # the new page, the same id: nothing again
        self.block("dev-b-2")
        self.wait_count(2)
        self.assertEqual([n["body"] for n in self.rec()["notes"]], ["dev-b-2 is blocked"])

    def test_unrelated_events_and_a_stream_reconnect_do_not_fire_again(self):
        self.start()
        self.block("dev-a-1")
        self.wait_count(1)
        port = self.srv.port
        self.srv.stop()
        self.browser.wait(page.RECONNECTING_JS)
        self.fx.start(port=port)
        self.browser.wait(page.LIVE_JS, timeout=15000)
        self.fx.activity(agent="dev-c-3", status="working")
        self.fx.message(**{"from": "manager", "to": "dev-c-3", "type": "ASK", "text": "go"})
        self.browser.wait("document.querySelector('#columns li[data-agent=dev-c-3]').dataset.status === 'working'")
        rec = self.rec()
        self.assertEqual(([n["body"] for n in rec["notes"]], self.chimes(rec)), (["dev-a-1 is blocked"], 1))

    def test_an_item_that_appeared_while_the_server_was_away_notifies_once_on_return(self):
        self.start()
        port = self.srv.port
        self.srv.stop()
        self.browser.wait(page.RECONNECTING_JS)
        self.block("dev-a-1")
        self.fx.start(port=port)
        self.wait_count(1)
        self.assertEqual([n["body"] for n in self.rec()["notes"]], ["dev-a-1 is blocked"])

    def test_the_set_is_pruned_to_the_current_ids_plus_the_last_200_in_order(self):
        self.fx.escalations([{"question": "Ship it?"}])
        old = ["escalation:1"] + ["old-%d" % i for i in range(1, 250)]
        self.start(seed=json.dumps(old))
        self.assertEqual(self.count(), 1)
        self.assertEqual(self.seen_stored(), ["escalation:1"] + old[-200:])
        self.assertEqual(self.rec()["notes"], [])

    def test_a_long_resolved_id_pushed_out_of_the_last_200_is_gone(self):
        self.start(seed=json.dumps(["old-%d" % i for i in range(250)]))
        self.block("dev-a-1")
        self.wait_count(1)
        stored = self.seen_stored()
        self.assertEqual(len(stored), 200)
        self.assertEqual((stored[0], stored[-2], stored[-1].startswith("blocked:dev-a-1:")), ("old-51", "old-249", True))

    def test_a_set_within_the_limit_is_kept_untouched(self):
        self.start(seed=json.dumps(["a", "b"]))
        self.assertEqual(self.seen_stored(), ["a", "b"])

    def test_a_fresh_id_is_added_even_when_nothing_is_pushed_out(self):
        self.start(seed=json.dumps(["a", "b"]))
        self.block("dev-a-1")
        self.wait_count(1)
        self.assertEqual(self.seen_stored()[:2], ["a", "b"])
        self.assertEqual(len(self.seen_stored()), 3)


class StorageTest(AlertsCase):
    def check_survives(self, **cfg):
        self.fx.activity(agent="dev-a-1", status="idle")  # a subtest repeats on the same squad: nobody blocked
        self.fx.escalations([{"question": "Ship it?"}])
        self.start(**cfg)
        self.assertEqual((self.count(), self.rec()["notes"], self.rec()["osc"]), (1, [], []))  # no mass notification
        self.assertEqual(self.title(), "(1) squad board")
        self.block("dev-a-1")
        self.wait_count(2)
        self.assertEqual([n["body"] for n in self.rec()["notes"]], ["dev-a-1 is blocked"])
        self.assertEqual(self.errors(), [])

    def test_corrupt_json_counts_as_empty(self):
        self.check_survives(seed="{not json")
        self.assertEqual(self.seen_stored()[0], "escalation:1")  # and is replaced by a good set

    def test_a_value_that_is_not_an_array_counts_as_empty(self):
        for value in ('{"a": 1}', '"escalation:1"', "null", "7"):
            with self.subTest(value=value):
                self.check_survives(seed=value)

    def test_storage_that_throws_on_read_and_write_keeps_the_set_in_memory(self):
        self.check_survives(storage="throws")
        self.block("dev-b-2")
        self.wait_count(3)
        self.resolve("dev-a-1")
        self.wait_count(2)
        self.block("dev-a-1")  # a new blocked event is a new id, but the set still has no repeats
        self.wait_count(3)
        self.assertEqual(len(self.rec()["notes"]), 3)

    def test_a_storage_that_cannot_even_be_reached_is_the_same(self):
        self.check_survives(storage="denied")

    def test_a_full_storage_does_not_stop_the_alerts(self):
        self.fx.escalations([{"question": "Ship it?"}])
        self.start(storage="throws")
        # the same escalation coming back after it resolved is still not announced, from memory
        self.fx.escalations([{"question": "Ship it?", "answer": "ok"}])
        self.wait_count(0)
        self.fx.escalations([{"question": "Ship it?"}])
        self.wait_count(1)
        self.assertEqual(self.rec()["notes"], [])


class PermissionTest(AlertsCase):
    def test_the_button_asks_once_and_then_disappears(self):
        self.start(permission="default", ask="granted")
        self.assertEqual((self.rec()["asks"], self.button_hidden()), (0, False))
        self.assertEqual(self.browser.eval("document.querySelector('#alerts-button').textContent"), "Enable alerts")
        self.browser.call("click", selector="#alerts-button")
        self.browser.wait("document.querySelector('#alerts-button').hidden")
        self.assertEqual(self.rec()["asks"], 1)

    def test_permission_is_never_requested_on_load_or_for_a_new_item(self):
        self.start(permission="default")
        self.block("dev-a-1")
        self.wait_count(1)
        self.browser.call("reload")
        self.browser.wait(page.LIVE_JS)
        self.assertEqual(self.rec()["asks"], 0)

    def test_the_button_is_hidden_when_the_browser_already_decided_or_cannot_ask(self):
        for cfg in ({"permission": "granted"}, {"permission": "denied"}, {"notification": False}):
            with self.subTest(cfg=cfg):
                self.start(**cfg)
                self.assertTrue(self.button_hidden())
                self.assertEqual(self.rec()["asks"], 0)

    def test_a_denied_answer_hides_the_button_and_silences_everything_but_the_page(self):
        self.start(permission="default", ask="denied")  # the stub keeps saying "default": the answer is what counts
        self.browser.call("click", selector="#alerts-button")
        self.browser.wait("document.querySelector('#alerts-button').hidden")
        self.block("dev-a-1")
        self.wait_count(1)
        rec = self.rec()
        self.assertEqual((rec["notes"], rec["osc"], self.title()), ([], [], "(1) squad board"))
        self.assertEqual(self.errors(), [])

    def test_a_browser_that_says_denied_at_load_is_silent_and_the_page_still_updates(self):
        self.start(permission="denied")
        self.block("dev-a-1")
        self.wait_count(1)
        rec = self.rec()
        self.assertEqual((rec["notes"], rec["osc"], rec["contexts"], self.title()), ([], [], 0, "(1) squad board"))
        self.assertEqual(self.errors(), [])

    def test_a_granted_answer_lets_the_alerts_through(self):
        self.start(permission="default", ask="granted")
        self.browser.call("click", selector="#alerts-button")
        self.browser.wait("document.querySelector('#alerts-button').hidden")
        self.block("dev-a-1")
        self.wait_count(1)
        self.assertEqual(len(self.rec()["notes"]), 1)

    def test_answers_that_are_no_decision_still_hide_the_button_except_a_dismissed_prompt(self):
        for ask, hidden in (("reject", True), ("throws", True), ("none", True), ("default", False)):
            with self.subTest(ask=ask):
                self.start(permission="default", ask=ask)
                self.browser.call("click", selector="#alerts-button")
                self.browser.call("sleep", ms=150)
                self.assertEqual(self.button_hidden(), hidden)
                self.assertEqual(self.rec()["asks"], 1)
                self.assertEqual(self.errors(), [])

    def test_a_dismissed_prompt_can_be_asked_again(self):
        self.start(permission="default", ask="default")
        self.browser.call("click", selector="#alerts-button")
        self.browser.call("click", selector="#alerts-button")
        self.assertEqual(self.rec()["asks"], 2)

    def test_notification_missing_is_silent_for_it_and_the_chime_and_page_go_on(self):
        self.start(notification=False)
        self.block("dev-a-1")
        self.wait_count(1)
        self.assertEqual((self.title(), self.chimes(), self.errors()), ("(1) squad board", 1, []))

    def test_a_constructor_that_throws_does_not_stop_the_rest(self):
        self.start(ctor="throws")
        self.fx.escalations([{"question": "First?"}, {"question": "Second?"}])
        self.wait_count(2)
        self.assertEqual((self.title(), self.rec()["notes"], self.chimes(), self.errors()),
                         ("(2) squad board", [], 1, []))

    def test_the_alerts_button_sits_left_of_the_bar_controls_at_every_width(self):
        self.srv = self.fx.start()
        for width in (1280, 1600, 1920):
            self.browser.open(self.srv.base + "/", init=stubs(permission="default"), width=width)
            boxes = self.browser.eval(  # the ↓ live button only shows while paused: force it, it is the widest case
                "(() => { document.querySelector('#live-button').hidden = false;"
                "const r = (s) => { const b = document.querySelector(s).getBoundingClientRect();"
                "return [b.left, b.top, b.right, b.bottom]; };"
                "return {alerts: r('#alerts-button'), controls: r('#bar-controls')}; })()")
            alerts, controls = boxes["alerts"], boxes["controls"]
            self.assertLess(alerts[2], controls[0], (width, boxes))
            self.assertLessEqual(controls[2], width - 16, (width, boxes))

    def test_the_button_is_on_the_bar_and_not_in_the_hidden_text_mirror(self):
        self.start(permission="default")
        box = self.browser.eval("(() => { const r = document.querySelector('#alerts-button').getBoundingClientRect();"
                                "return [r.left, r.top, r.right, r.bottom, !!document.querySelector('#board-text #alerts-button')]; })()")
        self.assertFalse(box[4])
        self.assertTrue(box[0] >= 1280 - 16 - 440 and box[2] <= 1280 - 16 and 14 <= box[1] and box[3] <= 14 + 46, box)
        self.assertTrue(self.browser.eval(  # the button, not the canvas, is what a click at its middle reaches
            "(() => { const r = document.querySelector('#alerts-button').getBoundingClientRect();"
            "return document.elementFromPoint((r.left + r.right) / 2, (r.top + r.bottom) / 2).id === 'alerts-button'; })()"))


class ChimeTest(AlertsCase):
    def test_the_context_is_not_made_at_load_but_on_the_first_gesture_or_chime(self):
        self.start()
        self.assertEqual(self.rec()["contexts"], 0)
        self.browser.call("click", selector="#board")
        self.assertEqual(self.rec()["contexts"], 1)
        self.block("dev-a-1")
        self.wait_count(1)
        self.assertEqual((self.rec()["contexts"], self.chimes()), (1, 1))  # one context, reused

    def test_a_key_press_is_a_gesture_too(self):
        self.start()
        self.browser.eval("window.dispatchEvent(new KeyboardEvent('keydown', {key: 'a'})); 1")
        self.assertEqual(self.rec()["contexts"], 1)

    def test_the_enable_click_makes_the_context(self):
        self.start(permission="default")
        self.browser.call("click", selector="#alerts-button")
        self.assertEqual(self.rec()["contexts"], 1)

    def test_a_suspended_context_is_silent_until_a_gesture_wakes_it(self):
        self.start(audio="suspended")
        self.block("dev-a-1")
        self.wait_count(1)
        rec = self.rec()
        self.assertEqual((len(rec["notes"]), rec["osc"], rec["resumes"]), (1, [], 0))  # no gesture: not even a resume
        self.browser.call("click", selector="#board")
        self.assertEqual(self.rec()["resumes"], 1)
        self.block("dev-b-2")
        self.wait_count(2)
        self.assertEqual((len(self.rec()["notes"]), self.chimes()), (2, 1))

    def test_a_running_context_is_not_resumed(self):
        self.start()
        self.browser.call("click", selector="#board")
        self.assertEqual(self.rec()["resumes"], 0)

    def test_a_context_that_cannot_resume_is_silent_and_not_an_error(self):
        for mode in ("resume-rejects", "resume-throws"):
            with self.subTest(mode=mode):
                self.start(audio=mode)
                self.browser.call("click", selector="#board")
                self.browser.call("sleep", ms=100)
                self.block("dev-a-1")
                self.wait_count(1)
                self.assertEqual((self.rec()["osc"], self.errors()), ([], []))
                self.assertEqual(self.rec()["resumes"], 1)
                self.resolve("dev-a-1")
                self.wait_count(0)

    def test_a_closed_context_is_silent(self):
        self.start(audio="closed")
        self.block("dev-a-1")
        self.wait_count(1)
        self.assertEqual((len(self.rec()["notes"]), self.rec()["osc"], self.errors()), (1, [], []))

    def test_a_context_that_throws_or_is_missing_is_silent_and_the_rest_goes_on(self):
        for mode in ("throws", "missing"):
            with self.subTest(mode=mode):
                self.start(audio=mode)
                self.browser.call("click", selector="#board")
                self.fx.escalations([{"question": "Q-%s?" % mode}])
                self.wait_count(1)
                self.assertEqual((len(self.rec()["notes"]), self.rec()["osc"], self.title(), self.errors()),
                                 (1, [], "(1) squad board", []))
                self.fx.escalations([])
                self.wait_count(0)

    def test_the_chime_is_made_with_the_audio_context_only(self):
        text = page.page_text()
        for forbidden in ("new Audio(", ".src", "<audio", "decodeAudioData", "createBufferSource"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
