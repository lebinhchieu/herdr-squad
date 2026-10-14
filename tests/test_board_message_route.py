"""BRD-32: rows carry at most 140 characters of text; GET /message/<msg_id>?token=... gives the whole text.

The route tests run the real `bin/squad-board --replay` on a temp squad folder (flat and per-scope)."""
import json
import unittest

from board_fixture import Fixture, make_scoped
from test_board_events import Stream
from test_board_http import NOW, request
from test_board_notes import STEP8

MANAGER = {"agent": "manager", "role": "Manager", "scope": "all"}
LONG = "".join(chr(97 + i % 26) for i in range(300))


class ClipCase(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.close)
        self.fx.roster([MANAGER, {"agent": "dev-a"}])

    def rows(self, **extra):
        srv = self.fx.start(now=NOW)
        self.addCleanup(srv.close)
        return srv, [r for r in srv.state()["rows"] if r["kind"] == "message"]


class ClipTest(ClipCase):
    def test_only_text_over_140_characters_is_cut_and_flagged(self):
        for n in (139, 140, 141):
            self.fx.message(**{"from": "manager", "to": "dev-a", "type": "ASK", "task": "T-1",
                               "text": LONG[:n], "msg_id": "m-%08d" % n})
        _, rows = self.rows()
        by_id = {r["msg_id"]: r for r in rows}
        self.assertNotIn("text_clipped", by_id["m-00000139"])
        self.assertNotIn("text_clipped", by_id["m-00000140"])
        self.assertEqual(by_id["m-00000140"]["text"], LONG[:140])
        self.assertTrue(by_id["m-00000141"]["text_clipped"])
        self.assertEqual(by_id["m-00000141"]["text"], LONG[:140])

    def test_a_multibyte_or_astral_character_is_never_split(self):
        self.fx.message(**{"from": "manager", "to": "dev-a", "text": "é" * 139 + "😀" + "x" * 10, "msg_id": "m-astral01"})
        self.fx.message(**{"from": "manager", "to": "dev-a", "text": "é" * 140 + "⛔", "msg_id": "m-three001"})
        _, rows = self.rows()
        self.assertEqual([r["text"] for r in rows], ["é" * 139 + "😀", "é" * 140])
        self.assertTrue(all(r["text_clipped"] for r in rows))

    def test_a_message_without_an_id_is_never_clipped(self):
        self.fx.message(**{"from": "manager", "to": "dev-a", "text": LONG, "msg_id": None})
        _, rows = self.rows()
        self.assertEqual(rows[0]["text"], LONG)
        self.assertNotIn("text_clipped", rows[0])

    def test_state_and_an_events_frame_carry_the_clip(self):
        self.fx.message(**{"from": "manager", "to": "dev-a", "type": "ASK", "task": "T-1", "text": LONG, "msg_id": "m-long0001"})
        srv, rows = self.rows()
        self.assertEqual(rows[0]["text"], LONG[:140])
        stream = Stream(srv)
        self.addCleanup(stream.close)
        pushed = [r for r in stream.state(10)["rows"] if r["kind"] == "message"]
        self.assertEqual((pushed[0]["text"], pushed[0]["text_clipped"]), (LONG[:140], True))

    def test_everything_but_row_text_is_the_same_as_with_short_texts(self):
        def build(text):
            fx = Fixture()
            self.addCleanup(fx.close)
            fx.roster([MANAGER, {"agent": "dev-a"}])
            for i in range(3):
                fx.message(**{"from": "manager", "to": "dev-a", "type": "ASK", "task": "T-%d" % i,
                              "text": text, "msg_id": "m-same%04d" % i})
            srv = fx.start(now=NOW)
            self.addCleanup(srv.close)
            state = srv.state()
            for r in state["rows"]:
                r.pop("text", None)
                r.pop("text_clipped", None)
            return state
        long_state, short_state = build(LONG), build(LONG[:100])
        for key in ("columns", "bars", "tasks", "needs_you", "rows"):
            self.assertEqual(long_state[key], short_state[key], key)


class RouteCase(unittest.TestCase):
    def setUp(self):
        self.fx = self.build()
        self.addCleanup(self.fx.close)
        self.fx.message(_home=self.home, **{"from": "manager", "to": "dev-a", "text": LONG, "msg_id": "m-route-001"})
        self.srv = self.fx.start(now=NOW)
        self.addCleanup(self.srv.close)

    home = ""

    def build(self):
        fx = Fixture()
        fx.roster([MANAGER, {"agent": "dev-a"}])
        return fx

    def get(self, msg_id="m-route-001", token="valid", **kw):
        query = "" if token is None else "?token=" + (self.srv.token if token == "valid" else token)
        return request(self.srv.port, "GET", "/message/" + msg_id + query, **kw)


class RouteTest(RouteCase):
    def test_the_full_text_with_the_text_headers(self):
        r = self.get()
        self.assertEqual((r.status, r.body), (200, LONG.encode()))
        for name, value in STEP8.items():
            self.assertEqual(r.headers.get(name), value, name)

    def test_a_missing_or_wrong_token_gets_the_same_403(self):
        a, b = self.get(token=None), self.get(token="wrong")
        self.assertEqual((a.status, b.status), (403, 403))
        self.assertEqual(a.body, b.body)
        self.assertEqual(self.get("nonexistent-id", token="wrong").body, a.body)  # id state never leaks

    def test_a_bad_id_is_400_and_an_unknown_id_404(self):
        for bad in ("short", "x" * 65, "..%2f..%2fetc", "a b c d e f g h"):
            self.assertEqual(self.get(bad).status, 400, bad)
        self.assertEqual(self.get("m-unknown-1").status, 404)

    def test_the_token_is_in_no_body(self):
        for r in (self.get(), self.get(token="wrong"), self.get("m-unknown-1"), self.get("bad")):
            self.assertNotIn(self.srv.token.encode(), r.body)

    def test_a_foreign_host_is_refused(self):
        self.assertEqual(self.get(host="evil.example:80").status, 403)

    def test_post_is_405(self):
        r = request(self.srv.port, "POST", "/message/m-route-001?token=" + self.srv.token)
        self.assertEqual(r.status, 405)


class ScopedRouteTest(RouteTest):
    home = "scopes/a"

    def build(self):
        fx = make_scoped()
        return fx


if __name__ == "__main__":
    unittest.main()
