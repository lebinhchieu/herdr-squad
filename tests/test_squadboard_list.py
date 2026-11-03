"""Picker and goal/scope rows (ticket 04). Tests are named for the business (T04.ACn) or technical (T04.TAn) AC.

They call the reader in-process on a copy of the board fixture (ticket 02), plus one request through the server."""
import datetime
import hashlib
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
import unittest.mock
import urllib.error
import urllib.request
from pathlib import Path

from squadtest import BIN

sys.path.insert(0, str(BIN))
import board_fixtures  # noqa: E402
import squadboard  # noqa: E402
import squadboard_git  # noqa: E402
import squadboard_list as L  # noqa: E402

NOW = datetime.datetime(2026, 11, 4, 10, 0, tzinfo=datetime.timezone.utc)
SIX = {"needs_you", "stuck", "tasks_done", "tasks_total", "agents_working", "last_active", "new"}
ROW_KEYS = SIX | {"name", "kind", "goal", "goal_label", "brief", "status", "closed_at", "closed_approx", "read_only", "unknown"}


def snapshot(root):
    out = {}
    for p in sorted(Path(root).rglob("*")):
        if p.is_file():
            out[str(p)] = (p.stat().st_mtime_ns, hashlib.sha1(p.read_bytes()).hexdigest())
    return out


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fx = board_fixtures.copy_fixture(now=NOW)
        cls.squad = squadboard.Squad(cls.fx.squad, "fix")

    @classmethod
    def tearDownClass(cls):
        board_fixtures.cleanup(cls.fx)

    def sel(self, kind=None, name=None, **extra):
        s = {"squads": [self.squad], "squad": self.squad, "kind": kind, "name": name, "params": {},
             "home": self.squad.find(kind, name) if kind else None, "repo_root": self.squad.repo_root,
             "herdr_json": str(self.fx.herdr_json)}
        s.update(extra)
        return s

    def picker(self):
        r = L.read_picker(self.sel())
        return r["data"]["squads"][0]


class PickerTests(Base):
    def test_T04_AC1_rows_order_and_done_list(self):
        sq = self.picker()
        names = [r["name"] for r in sq["open"]]
        self.assertEqual(names[:2], ["questions", "checkout"])  # needs you 1, then stuck 2, then the rest
        for r in sq["open"] + sq["done"]:
            self.assertEqual(set(r) - {"scopes_count"}, ROW_KEYS, r["name"])  # six facts and no task, inbox or work-time data
        self.assertEqual(len(sq["done"]), 20)
        closed = [r["closed_at"] for r in sq["done"]]
        self.assertEqual(closed, sorted(closed, reverse=True))
        by = {r["name"]: r for r in sq["open"]}
        self.assertEqual((by["checkout"]["needs_you"], by["checkout"]["stuck"], by["checkout"]["agents_working"]), (0, 2, 2))
        self.assertEqual(by["checkout"]["tasks_total"], 9)
        self.assertEqual(by["checkout"]["last_active"], "2026-11-04T09:30:00Z")

    def test_T04_AC2_selection_required_and_only_the_choice(self):
        """Server: neither goal nor scope gives 'selection required'; a choice gives only its rows."""
        server = squadboard.BoardServer(0, [self.squad])
        server.initial = {}
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            base = "http://127.0.0.1:%d" % server.port
            with self.assertRaises(urllib.error.HTTPError) as cm:
                urllib.request.urlopen(base + "/api/scopes", timeout=10)
            self.assertEqual(cm.exception.code, 400)
            body = json.loads(urllib.request.urlopen(base + "/api/scopes?scope=checkout", timeout=10).read())
            self.assertEqual(body["data"]["scope"]["name"], "checkout")
            self.assertEqual(body["schema_version"], 1)
            self.assertEqual(json.loads(urllib.request.urlopen(base + "/api/squads", timeout=10).read())["data"]["squads"][0]["name"], "fix")
        finally:
            server.shutdown()
            server.server_close()

    def test_T04_AC3_goal_lists_open_and_done_scopes(self):
        home = self.squad.path / "scopes" / "alpha-qa"
        done = self.squad.path / "scopes" / "_done" / "alpha-qa"
        os.rename(home, done)
        try:
            d = L.read(self.sel("goal", "alpha"))["data"]
        finally:
            os.rename(done, home)
        status = {r["name"]: r["status"] for r in d["scopes"]}
        self.assertEqual(status, {"alpha-api": "open", "alpha-docs": "open", "alpha-ui": "open", "alpha-qa": "done"})

    def test_T04_AC4_no_goal_tag_and_empty_goal(self):
        r = L.read(self.sel("scope", "checkout"))["data"]["scope"]
        self.assertEqual((r["goal"], r["goal_label"]), (None, "no goal"))
        empty = self.squad.path / "goals" / "empty-g"
        empty.mkdir()
        (empty / "goal.md").write_text("# Goal: empty-g\n\n**Empty.**\n\n## Scopes\n\n| Scope | Depends on | Status |\n|---|---|---|\n", encoding="utf-8")
        try:
            d = L.read(self.sel("goal", "empty-g"))["data"]
        finally:
            shutil.rmtree(str(empty))
        self.assertEqual((d["scopes"], d["empty_text"]), ([], "No scopes in this goal"))

    def test_T04_AC5_closed_scope_is_approx_and_read_only(self):
        r = L.read(self.sel("scope", "done-02"))["data"]["scope"]
        self.assertEqual((r["status"], r["closed_approx"], r["read_only"]), ("done", True, True))
        self.assertEqual(r["closed_at"], "2026-11-02T10:00:00Z")
        self.assertEqual(L.read(self.sel("scope", "checkout"))["data"]["scope"]["read_only"], False)

    def test_T04_AC6_saved_choice_not_found(self):
        s = self.sel()
        self.assertTrue(L.check(s, "alpha")["exists"])
        self.assertEqual(L.check(s, "done-05")["where"], "done")
        gone = L.check(s, "no-such")
        self.assertEqual((gone["exists"], gone["message"]), (False, "saved choice no-such not found"))
        self.assertFalse(L.check(s, "../x")["exists"])


class TechnicalTests(Base):
    def test_T04_TA2_cheap_two_git_calls_no_transcript_no_write(self):
        before = snapshot(self.fx.root)
        opened = []
        real_open = open

        def spy(path, *a, **k):
            opened.append(str(path))
            return real_open(path, *a, **k)
        with unittest.mock.patch.object(squadboard_git, "_git", wraps=squadboard_git._git) as g, \
                unittest.mock.patch("builtins.open", spy):
            L.read_picker(self.sel())
        self.assertLessEqual(g.call_count, 2)
        self.assertFalse([p for p in opened if p.endswith(".jsonl") and "claude-config" in p])
        self.assertEqual(snapshot(self.fx.root), before)  # TC.2: nothing written

    def test_T04_TA3_speed_25_scopes(self):
        n = len(self.picker()["open"]) + len(self.picker()["done"])
        self.assertGreaterEqual(n, 25)
        t = time.time()
        L.read_picker(self.sel())
        took = time.time() - t
        print("picker for %d rows: %.3f s" % (n, took))
        self.assertLess(took, 1.5)

    def test_T04_TA4_traversal_is_refused(self):
        r = L.read(self.sel("scope", "../x", home=None))
        self.assertIsNone(r["data"])
        self.assertEqual(squadboard.Squad.find(self.squad, "scope", "../x"), None)

    def test_T04_TA6_goal_table_as_written(self):
        d = L.read(self.sel("goal", "alpha"))["data"]
        self.assertEqual(d["scopes_table"]["columns"], ["Scope", "Depends on", "Status"])
        self.assertEqual(d["scopes_table"]["rows"][0], ["alpha-api", "-", "open"])
        self.assertEqual(L.goal_scopes_table("## Scopes\r\n\r\n| A | B |\r\n|---|---|\r\n| x | y |\r\n")["rows"], [["x", "y"]])

    def test_T04_TA7_missing_sources_give_unknown(self):
        tmp = tempfile.mkdtemp()
        try:
            sq = Path(tmp) / ".claude" / "squads" / "t"
            (sq / "scopes" / "bare").mkdir(parents=True)
            (sq / "process.md").write_text("x", encoding="utf-8")
            squad = squadboard.Squad(sq, "t")
            s = {"squads": [squad], "squad": squad, "kind": "scope", "name": "bare", "params": {},
                 "home": sq / "scopes" / "bare", "herdr_json": str(Path(tmp) / "none.json")}
            r = L.read(s)
            row = r["data"]["scope"]
            self.assertEqual(set(row), ROW_KEYS)
            self.assertEqual(row["brief"], "")
            for src in ("scope.md", "roster.md", "messages.jsonl", "inbox", "herdr"):
                self.assertIn(src, row["unknown"])
            self.assertEqual(L.read_picker({**s, "kind": None})["data"]["squads"][0]["open"][0]["name"], "bare")
        finally:
            shutil.rmtree(tmp)

    def test_T04_TA7_crlf_scope_md(self):
        r = L.read(self.sel("scope", "done-02"))["data"]["scope"]  # the fixture makes done-02/scope.md CRLF
        self.assertEqual((r["brief"], r["goal"]), ("Closed fixture scope 2.", None))


if __name__ == "__main__":
    unittest.main()
