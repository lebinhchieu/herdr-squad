"""Saved UI state (ticket 09). Tests are named for the business AC (T09.ACn) or technical risk they cover."""
import hashlib
import json
import os
import sys
import tempfile
import threading
import unittest
import unittest.mock
import urllib.error
import urllib.request
from pathlib import Path

from squadtest import BIN, clean_env

sys.path.insert(0, str(BIN))
import squadboard  # noqa: E402
import squadboard_ui as ui  # noqa: E402
from test_squadboard_server import make_squad  # noqa: E402

GOOD = {"saved_at": "2026-11-04T10:00:00Z", "font": "xl", "choice": {"kind": "scope", "name": "alpha"},
        "recent": [{"kind": "scope", "name": "alpha"}, {"kind": "goal", "name": "g1"}, {"kind": "scope", "name": "alpha"}],
        "panels": {"inbox": {"order": 1, "tracks": 2, "hidden": True, "max_height": 300}}}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.squad = make_squad(Path(self.tmp.name))
        self.file = self.squad / ui.FILE
        self.addCleanup(self.tmp.cleanup)
        squads = squadboard.find_squads([], env=clean_env(SQUAD_DIR=str(self.squad)))
        routes, _ = squadboard.load_routes()
        self.srv = squadboard.BoardServer(0, squads, None, routes)
        t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        t.start()
        self.addCleanup(lambda: (self.srv.shutdown(), self.srv.server_close(), t.join(5)))
        self.base = "http://127.0.0.1:%d" % self.srv.port

    def put(self, body, token=True, host=None, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        h = {"Content-Type": ctype}
        if token:
            h["X-Board-Token"] = self.srv.token
        if host:
            h["Host"] = host
        req = urllib.request.Request(self.base + "/api/ui", data=data, method="PUT", headers=h)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def get(self):
        with urllib.request.urlopen(self.base + "/api/ui", timeout=10) as r:
            return json.loads(r.read())["data"]

    def sha(self):
        return hashlib.sha256(self.file.read_bytes()).hexdigest() if self.file.exists() else None


class SaveTest(Base):
    def test_T09_AC1_saved_state_comes_back_and_matches_format(self):
        code, r = self.put(GOOD)
        self.assertEqual(code, 200)
        d = self.get()
        self.assertEqual(d["status"], "ok")
        u = d["ui"]
        self.assertEqual((u["font"], u["choice"], u["saved_at"], u["version"]), ("xl", GOOD["choice"], GOOD["saved_at"], 1))
        self.assertEqual(u["panels"], GOOD["panels"])
        self.assertEqual(len(u["recent"]), 2)  # no duplicates
        raw = self.file.read_bytes()
        self.assertNotIn(b"\r", raw)
        self.assertNotIn(b'"size"', raw)

    def test_T09_bad_type_is_400_and_writes_nothing(self):
        bad = dict(GOOD, panels={"p": {"order": "1", "span": 1}})
        self.assertEqual(self.put(bad)[0], 400)
        self.assertEqual(self.put(dict(GOOD, font="huge"))[0], 400)
        self.assertEqual(self.put(b"not json")[0], 400)
        self.assertFalse(self.file.exists())

    def test_T09_two_writers_leave_a_whole_file(self):
        a, b = dict(GOOD, font="small"), dict(GOOD, font="xl")
        for _ in range(20):
            ts = [threading.Thread(target=self.put, args=(x,)) for x in (a, b)]
            [t.start() for t in ts]
            [t.join() for t in ts]
            self.assertIn(json.loads(self.file.read_text(encoding="utf-8"))["font"], ("small", "xl"))
        self.assertEqual([p.name for p in self.squad.glob("*.tmp")], [])

    def test_T09_failed_replace_keeps_old_file_and_leaves_no_temp(self):
        self.put(GOOD)
        before = self.sha()
        with unittest.mock.patch("os.replace", side_effect=OSError("boom")):
            code, r = self.put(dict(GOOD, font="small"))
        self.assertEqual((code, r["status"]), (507, "unwritable"))
        self.assertNotIn("Traceback", json.dumps(r))
        self.assertEqual(self.sha(), before)
        self.assertEqual(list(self.squad.glob("*.tmp")), [])

    def test_T09_replace_permission_error_is_retried_3_times(self):
        with unittest.mock.patch("os.replace", side_effect=PermissionError("busy")) as m, \
                unittest.mock.patch("time.sleep"):
            self.assertEqual(self.put(GOOD)[0], 507)
        self.assertEqual(m.call_count, 3)


class HardeningTest(Base):
    def test_T36_TA4_tracks_bounds_and_old_keys(self):
        row = {"order": 1, "hidden": False}
        for ok in (1, 12):
            code, r = self.put(dict(GOOD, panels={"a": dict(row, tracks=ok)}))
            self.assertEqual((code, r["data"]["ui"]["panels"]["a"]["tracks"]), (200, ok))
        for bad in (0, 13, "2", 2.5, True):
            code, r = self.put(dict(GOOD, panels={"a": dict(row, tracks=bad)}))
            self.assertEqual(code, 400, bad)
            self.assertIn("tracks 1..12", r["error"])   # same error shape as a bad order
        self.assertEqual(self.put(dict(GOOD, panels={"a": dict(row, order="x")}))[0], 400)
        # an old body (no tracks, with col or span) is accepted; neither is stored; "auto" is retired
        code, r = self.put(dict(GOOD, auto=True, panels={"a": dict(row, col=2, span=2)}))
        self.assertEqual(code, 200)
        self.assertEqual(r["data"]["ui"]["panels"]["a"], row)
        self.assertNotIn("auto", r["data"]["ui"])
        self.assertEqual(self.put(dict(GOOD, panels={"a": dict(row, row=3)}))[0], 400)    # position keys still refused

    def test_T09_position_keys_are_refused(self):
        for extra in ({"x": 1}, {"y": 2}, {"row": 3}, {"size": 5}):
            self.assertEqual(self.put(dict(GOOD, **extra))[0], 400, extra)
            p = {"order": 0, "span": 1, "hidden": False, **extra}
            self.assertEqual(self.put(dict(GOOD, panels={"a": p}))[0], 400, extra)
        self.assertFalse(self.file.exists())

    def test_T09_nan_and_lone_surrogate_are_400_not_a_dropped_connection(self):
        self.assertEqual(self.put(b'{"saved_at":"2026-11-04T10:00:00Z","extra":NaN}')[0], 400)
        raw = b'{"saved_at":"2026-11-04T10:00:00Z","choice":{"kind":"scope","name":"\\ud800"}}'
        self.assertEqual(self.put(raw.replace(b"\\\\", b"\\"))[0], 400)
        self.assertFalse(self.file.exists())

    @unittest.skipIf(os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
                     "chmod 444 does not stop writes on Windows or for root")
    def test_T09_AC2_read_only_file_is_507_on_put_and_unwritable_on_get(self):
        self.put(GOOD)
        self.file.chmod(0o444)
        before = self.sha()
        self.assertEqual(self.get()["status"], "unwritable")
        code, r = self.put(dict(GOOD, font="small"))
        self.assertEqual((code, r["status"]), (507, "unwritable"))
        self.assertEqual(self.sha(), before)

    @unittest.skipIf(os.name == "nt", "POSIX file modes")
    def test_T09_file_keeps_its_mode(self):
        self.put(GOOD)
        self.file.chmod(0o664)
        self.put(dict(GOOD, font="small"))
        self.assertEqual(self.file.stat().st_mode & 0o777, 0o664)


class ReadTest(Base):
    def test_T09_AC2_AC3_unwritable_status_on_get_and_put(self):
        with unittest.mock.patch("os.access", return_value=False):
            self.assertEqual(self.get()["status"], "unwritable")
        with unittest.mock.patch("tempfile.mkstemp", side_effect=PermissionError("ro")):
            code, r = self.put(GOOD)
        self.assertEqual((code, r["status"]), (507, "unwritable"))

    def test_T09_AC4_bad_json_empty_or_unknown_version_gives_defaults_and_is_not_overwritten(self):
        for text in ("{bad", "", '{"version": 99}', "[]"):
            self.file.write_text(text, encoding="utf-8")
            d = self.get()
            self.assertEqual((d["status"], d["ui"]), ("unreadable", ui.defaults()), text)
            self.assertEqual(self.file.read_text(encoding="utf-8"), text)

    def test_T09_missing_file_is_defaults_and_ok(self):
        d = self.get()
        self.assertEqual((d["status"], d["ui"]), ("ok", ui.defaults()))
        self.assertFalse(self.file.exists())


class ColumnsTest(Base):
    COLS = {"tasks": ["owner", "task", "last_active"], "files": ["file", "scope"], "future_panel": ["x_y"]}

    def test_T20_TA1_columns_saved_read_back_one_entry_for_every_choice(self):
        self.assertEqual(self.put(dict(GOOD, columns=self.COLS))[0], 200)
        a = self.get()["ui"]
        self.assertEqual((a["columns"], a["version"]), (self.COLS, 1))  # unknown panel kept
        self.assertEqual(self.put(dict(GOOD, choice={"kind": "goal", "name": "g1"}, columns=self.COLS))[0], 200)
        self.assertEqual(self.get()["ui"]["columns"], a["columns"])
        raw = self.file.read_text(encoding="utf-8")
        self.assertNotIn("alpha\": [", raw)

    def test_T20_TA2_bad_columns_is_400_and_file_unchanged(self):
        self.put(dict(GOOD, columns=self.COLS))
        before = self.sha()
        for bad in ([], {"tasks": "owner"}, {"tasks": [1]}, {"tasks": ["Bad Id"]}, {"tasks": ["a"] * 31},
                    {("p%d" % i): [] for i in range(21)}):
            self.assertEqual(self.put(dict(GOOD, font="small", columns=bad))[0], 400, bad)
        self.assertEqual(self.sha(), before)

    def test_T20_TA2_hand_edited_bad_columns_drops_to_empty_and_keeps_the_rest(self):
        self.file.write_text(json.dumps(dict(GOOD, version=1, columns={"tasks": "x"})), encoding="utf-8")
        d = self.get()
        self.assertEqual((d["status"], d["ui"]["columns"], d["ui"]["font"]), ("ok", {}, "xl"))
        self.assertEqual(d["ui"]["panels"], GOOD["panels"])

    def test_T20_TA3_old_file_without_columns_reads_as_defaults_and_is_not_rewritten(self):
        text = json.dumps(dict(GOOD, version=1))
        self.file.write_text(text, encoding="utf-8")
        d = self.get()
        self.assertEqual((d["status"], d["ui"]["columns"]), ("ok", {}))
        self.assertEqual(self.file.read_text(encoding="utf-8"), text)


class GuardTest(Base):
    def test_T09_AC5_no_token_wrong_host_or_content_type_leaves_file_unchanged(self):
        self.put(GOOD)
        before = self.sha()
        other = dict(GOOD, font="small")
        self.assertEqual(self.put(other, token=False)[0], 403)
        self.assertEqual(self.put(other, host="evil.example")[0], 403)
        self.assertEqual(self.put(other, ctype="text/plain")[0], 415)
        self.assertEqual(self.sha(), before)

    def test_T09_body_over_64k_is_413(self):
        self.assertEqual(self.put(dict(GOOD, pad="x" * 70000))[0], 413)
        self.assertFalse(self.file.exists())

    def test_T09_path_in_body_is_ignored_and_only_board_ui_json_changes(self):
        def snap():
            return {str(p): p.read_bytes() for p in self.squad.rglob("*") if p.is_file()}
        before = snap()
        outside = Path(self.tmp.name) / "x"
        self.assertEqual(self.put(dict(GOOD, path=str(outside), squad="other"))[0], 200)
        self.assertFalse(outside.exists())
        after = snap()
        self.assertEqual(set(after) - set(before), {str(self.file)})
        self.assertEqual({k: v for k, v in after.items() if k in before}, before)
        self.assertNotIn("path", json.loads(self.file.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
