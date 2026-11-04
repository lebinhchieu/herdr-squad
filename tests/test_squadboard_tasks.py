"""squadboard_tasks: T07.AC1-AC11 on the board fixture (squad fix, scope checkout), TA4/TA5/TA7/TA10."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "bin"))
import board_fixtures  # noqa: E402
import squadboard  # noqa: E402
import squadboard_list
import squadtickets  # noqa: E402
import squadboard_tasks as bt  # noqa: E402

NOW = board_fixtures.REF.timestamp()
FIELDS = {"id", "title", "stage", "owner", "waits_on", "last_active", "returns", "last_fail_line", "branch", "tip",
          "new_count"}


def sel_for(fx, kind="scope", name="checkout", since=None, detail=None):
    squad = squadboard.Squad(fx.squad, "fix")
    params = {}
    if since is not None:
        params["since"] = str(since)
    if detail:
        params["detail"] = detail
    home = squad.find(kind, name)
    return {"squads": [squad], "squad": squad, "kind": kind, "name": name, "home": home,
            "repo_root": squad.repo_root, "now": NOW, "params": params}


class Tasks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fx = board_fixtures.copy_fixture()
        cls.res = bt.read(sel_for(cls.fx))
        cls.rows = {r["id"]: r for r in cls.res["data"]["rows"]}

    @classmethod
    def tearDownClass(cls):
        board_fixtures.cleanup(cls.fx)

    def test_T07_AC1_AC2_AC3_stage_per_task(self):
        want = {"01": "todo", "02": "in progress", "03": "returned", "04": "blocked", "06": "ready for review",
                "07": "sha changed after PASS", "08": "merged", "09": "done"}
        for k, v in want.items():
            self.assertEqual(self.rows[k]["stage"], v, k)
        for r in self.rows.values():
            self.assertTrue(FIELDS <= set(r), r)
            self.assertNotIn("scope", r)  # T07.AC9 scope choice
        self.assertEqual(self.rows["01"]["owner"], "unassigned")
        self.assertEqual(self.rows["03"]["returns"], 3)
        self.assertEqual(self.rows["03"]["last_fail_line"], "reason 3 first line (newest)")

    def test_T07_AC4_checking_words(self):
        self.assertEqual(self.rows["05"]["stage"], "checking, 1 of 2 PASS, waiting on QA blackbox, 40 min")
        self.assertEqual(self.rows["05"]["waits_on"], "QA blackbox")

    def test_T07_AC5_AC6_ready_list(self):
        rd = self.res["data"]["ready_for_review"]
        self.assertEqual([x["task"] for x in rd], ["06"])
        self.assertEqual(rd[0]["tip"], self.rows["06"]["tip"])

    def test_T07_AC7_AC8_no_row_for_rule_token_and_tickets_line(self):
        self.assertNotIn("REV-8", self.rows)
        self.assertEqual(len(self.rows), 9)  # the folder from `tickets:` is used
        scope_md = Path(self.fx.scope) / "scope.md"
        scope_md.write_text(scope_md.read_text(encoding="utf-8").replace("tickets: checkout-tasks", ""), encoding="utf-8")
        again = {r["id"] for r in bt.read(sel_for(self.fx))["data"]["rows"]}
        scope_md.write_text(scope_md.read_text(encoding="utf-8") + "tickets: checkout-tasks\n", encoding="utf-8")
        self.assertEqual(again, set())  # T19: no line and no .scratch/checkout/issues: no guess, no tasks

    def test_T07_AC9_goal_has_scope_column(self):
        data = bt.read(sel_for(self.fx, "goal", "alpha"))["data"]
        self.assertTrue(data["scope_column"])
        for r in data["rows"]:
            self.assertIn("scope", r)

    def test_T07_AC10_detail_time_order_no_free_text(self):
        d = bt.read(sel_for(self.fx, detail="03"))["data"]["rows"]
        self.assertEqual(len(d), 1)
        steps = d[0]["detail"]["steps"]
        self.assertEqual([s["ts"] for s in steps], sorted(s["ts"] for s in steps))
        self.assertTrue(all(s["iso"] for s in steps))
        self.assertNotIn("more detail", json.dumps(d))  # only the reason line, not the body

    def test_T07_AC11_new_counts(self):
        since = datetime(2026, 11, 4, 1, 0, tzinfo=timezone.utc).timestamp()
        rows = {r["id"]: r for r in bt.read(sel_for(self.fx, since=since))["data"]["rows"]}
        self.assertEqual(rows["03"]["new_count"], 4)  # HANDIN, FAIL, HANDIN, FAIL after 01:00
        self.assertEqual({r["new_count"] for r in self.rows.values()}, {0})  # no time: 0 new

    def test_ready_by_scope(self):
        for kind, name in (("scope", "checkout"), ("scope", "questions"), ("goal", "alpha")):
            got = bt.ready_by_scope(sel_for(self.fx, kind, name))  # squad-wide, whatever the choice
            self.assertEqual(got["checkout"], 1, (kind, name))
            self.assertIn("questions", got)

    def test_TA5_missing_tickets_folder_reports_unknown(self):
        scope_md = Path(self.fx.scope) / "scope.md"
        orig = scope_md.read_text(encoding="utf-8")
        try:
            scope_md.write_text(orig.replace("checkout-tasks", "nope"), encoding="utf-8")
            r = bt.read(sel_for(self.fx))
            self.assertIn("tickets", r["unknown"])
            self.assertEqual(r["data"]["rows"], [])  # T19: no fallback to a guess
        finally:
            scope_md.write_text(orig, encoding="utf-8")

    def test_T19_no_match_means_no_tasks(self):
        """A scope with no `tickets:` line and no .scratch/<scope>/issues shows no tasks, not another scope's."""
        for name in ("questions", "parked"):
            r = bt.read(sel_for(self.fx, "scope", name))
            self.assertEqual(r["data"]["rows"], [], name)
            self.assertIn("tickets", r["unknown"])
            self.assertEqual(r["quality"], "approx")
        r = bt.read(sel_for(self.fx, "scope", "alpha-ui"))
        self.assertEqual(r["data"]["rows"], [])
        self.assertIn("tickets", r["unknown"])

    def test_T19_same_folder_rule_as_list(self):
        """T28.TA1: reader and list both call squadtickets.scope_tasks, so they find the same ids over every fixture scope."""
        squad = squadboard.Squad(self.fx.squad, "fix")
        for kind_dir in ("scopes", "scopes/_done"):
            base = Path(squad.path) / kind_dir
            for home in sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith("_")) if base.is_dir() else []:
                text = (home / "scope.md").read_text(encoding="utf-8") if (home / "scope.md").exists() else ""
                want = squadboard_list._tickets(squad, home, text, None)
                r = squadtickets.scope_tasks(home, squad.repo_root, home.name)
                got = None if r["source"] is None else {t["id"] for t in r["tasks"]}
                self.assertEqual(None if want is None else set(want), got, home.name)

    def test_TA10_broken_sources_never_raise(self):
        fx = board_fixtures.copy_fixture(git=False)
        try:
            for victim in ("messages.jsonl", "roster.md"):
                (Path(fx.scope) / victim).unlink()
            r = bt.read(sel_for(fx))
            self.assertIn("git", r["unknown"])
            self.assertIn("messages", r["unknown"])
            self.assertIsInstance(r["data"]["rows"], list)
            shutil.rmtree(str(Path(fx.repo) / ".scratch"))
            self.assertEqual(bt.read(sel_for(fx))["data"]["rows"], [])
        finally:
            board_fixtures.cleanup(fx)

    def test_TA7_secret_text_not_in_payload(self):
        fx = board_fixtures.copy_fixture()
        try:
            board_fixtures.append_message(fx.scope, "STATUS", "03", "fix-dev-03", "STATUS 03: CANARY-SECRET")
            out = json.dumps(bt.read(sel_for(fx, detail="03")))
            self.assertNotIn("CANARY", out)
        finally:
            board_fixtures.cleanup(fx)


class ScopeFilesShape(unittest.TestCase):
    """T28.TA3/TA4/TA6: the accounts/cswitch-bg shape (flat tasks/NN.md) through the board reader and the list."""

    def test_T28_cswitch_shape_rows_stage_and_list(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            (root / ".scratch").mkdir()
            home = root / ".claude" / "squads" / "accounts" / "scopes" / "cswitch-bg"
            (home / "tasks").mkdir(parents=True)
            (home / "tasks" / "01.md").write_text(
                "# 01 Repro: what cswitch meets on a pane with background work\nStatus: done (Manager-confirmed; QA at the end)\n", encoding="utf-8")
            (home / "tasks" / "02.md").write_text("# 02 Second\nStatus: handed in e8a7c5f, Manager-confirmed\n", encoding="utf-8")
            (home / "tasks" / "notes.md").write_text("# n\n", encoding="utf-8")
            rows, unknown, _ = bt.read_scope("accounts", "cswitch-bg", home, root, None, NOW, git=([], []))
            self.assertNotIn("tickets", unknown)
            self.assertEqual([r["id"] for r in rows], ["01", "02"])
            self.assertEqual((rows[0]["title"], rows[0]["stage"], rows[0]["ticket_status"]),
                             ("Repro: what cswitch meets on a pane with background work", "done", "done"))
            self.assertEqual(rows[1]["stage"], "in progress")
            for k in ("id", "title", "stage", "owner", "where", "ticket_status", "abs"):
                self.assertIn(k, rows[0])
            self.assertEqual(rows[0]["where"], ".claude/squads/accounts/scopes/cswitch-bg/tasks/01.md")
            squad = SimpleNamespace(repo_root=root)
            self.assertEqual(squadboard_list._tickets(squad, home, "", None), {"01": "done", "02": "handed in"})


if __name__ == "__main__":
    unittest.main()
