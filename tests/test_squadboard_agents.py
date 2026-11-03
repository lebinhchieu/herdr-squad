"""squad-board agents now and banner entries (ticket 08, business AC T08.AC6-AC7 and technical TA1-TA5). Fixture: ticket 02."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "bin"))
import board_fixtures as bf  # noqa: E402
import squadboard  # noqa: E402
import squadboard_agents as ag  # noqa: E402

NOW = bf.REF.timestamp()
FIELDS = {"name", "role", "task", "status", "state", "last_activity", "pane_id", "scope"}
EMPTY = '{"id": "cli:agent:list", "result": {"agents": []}}'


class Agents(unittest.TestCase):
    def setUp(self):
        self.fx = bf.copy_fixture(now=bf.REF)
        self.env = mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.fx.config_dir)})
        self.env.start()
        self.squad = squadboard.Squad(self.fx.squad, "fix")

    def tearDown(self):
        self.env.stop()
        bf.cleanup(self.fx)

    def sel(self, herdr, kind="scope", name="checkout"):
        return {"squad": self.squad, "kind": kind, "name": name, "home": self.squad.find(kind, name),
                "repo_root": self.squad.repo_root, "now": NOW, "herdr_json": str(herdr) if herdr else None}

    def test_T08_TA1_two_recorded_samples(self):
        got, why = ag.parse_herdr(self.fx.herdr_json.read_text(encoding="utf-8"))
        self.assertIsNone(why)
        self.assertEqual({v["status"] for v in got.values()}, {"working", "idle", "blocked"})
        self.assertEqual(got["fix-dev-02"], {"status": "blocked", "pane_id": "w1:p2", "cwd": "/fixture/repo"})
        self.assertEqual(ag.parse_herdr(EMPTY), ({}, None))
        self.assertEqual(ag.parse_herdr(self.fx.herdr_down.read_text(encoding="utf-8")), (None, ag.NOT_RUNNING))

    def test_T08_TA4_done_status_is_idle_new_word_unknown(self):
        # shape copied from a live `herdr agent list` (agent_status "done"), name changed; "paused" stands for a future word
        a = '{"agent": "claude", "agent_status": "%s", "cwd": "/fixture/repo", "name": "fix-dev-02", "pane_id": "w1:p2"}'
        for word, want in (("done", "idle"), ("paused", "unknown")):
            got, _ = ag.parse_herdr('{"id": "cli:agent:list", "result": {"agents": [%s]}}' % (a % word))
            self.assertEqual(got["fix-dev-02"]["status"], want)

    def test_T08_AC6_five_live_one_retired_other_squad_hidden(self):
        d = ag.read(self.sel(self.fx.herdr_json))["data"]
        self.assertEqual(d["status"], "ok")
        self.assertEqual(len(d["agents"]), 5)
        self.assertEqual((d["retired_count"], [r["name"] for r in d["retired"]]), (1, ["fix-dev-03"]))
        for r in d["agents"] + d["retired"]:
            self.assertEqual(set(r), FIELDS)
        by = {r["name"]: r for r in d["agents"]}
        self.assertNotIn("other-dev-1", by)
        self.assertEqual((by["fix-dev-02"]["status"], by["fix-dev-02"]["pane_id"], by["fix-dev-02"]["role"],
                          by["fix-dev-02"]["task"]), ("blocked", "w1:p2", "dev", "ticket 02"))
        self.assertIsNotNone(by["fix-dev-02"]["last_activity"])
        self.assertEqual(by["fix-qab-checkout"]["status"], "unknown")  # live in the roster, not listed by herdr

    def test_T08_AC7_herdr_down_roles_still_listed(self):
        bad = Path(tempfile.mkdtemp(prefix="agents-bad-")) / "x.json"
        bad.write_text("garbage", encoding="utf-8")
        for src in (self.fx.herdr_down, bad, bad.parent / "missing.json"):
            r = ag.read(self.sel(src))
            self.assertEqual(r["unknown"], ["herdr"])
            self.assertEqual(r["data"]["status"], "unknown")
            self.assertEqual(len(r["data"]["agents"]), 5)
            self.assertEqual({a["status"] for a in r["data"]["agents"]}, {"unknown"})
        self.assertEqual(ag.read(self.sel(self.fx.herdr_down))["data"]["reason"], "herdr not running")

    def test_T08_TA2_no_herdr_on_path_is_unknown_without_shell(self):
        with mock.patch.dict(os.environ, {"PATH": ""}):
            r = ag.read(self.sel(None))
        self.assertEqual((r["data"]["status"], r["data"]["reason"]), ("unknown", ag.NOT_RUNNING))
        with mock.patch.object(ag.subprocess, "run", return_value=mock.Mock(stdout=EMPTY, returncode=0)) as run:
            ag.read(self.sel(None))
        self.assertEqual(run.call_args[0][0], ["herdr", "agent", "list"])
        self.assertEqual(run.call_args[1]["timeout"], 5)
        self.assertFalse(run.call_args[1].get("shell"))

    def test_T08_TA5_banner_entries(self):
        self.assertEqual(ag.banner(self.sel(self.fx.herdr_json)),
                         {"entries": [{"agent": "fix-dev-02", "pane_id": "w1:p2", "scope": "checkout"}], "reason": None})
        self.assertEqual(ag.banner(self.sel(self.fx.herdr_down))["entries"], None)
        f = self.fx.root / "empty.json"
        f.write_text(EMPTY, encoding="utf-8")
        self.assertEqual(ag.banner(self.sel(f))["entries"], [])

    def test_T08_herdr_json_flag_reaches_the_selection(self):
        self.assertEqual(squadboard.make_parser().parse_args(["--herdr-json", "f.json"]).herdr_json, "f.json")
        srv = mock.Mock(squads=[self.squad], clock=lambda: NOW, herdr_json="f.json")
        srv.squad_by_key = self.squad and (lambda k: self.squad)
        sel, err = squadboard.resolve_selection(srv, {"scope": "checkout"})
        self.assertIsNone(err)
        self.assertEqual(sel["herdr_json"], "f.json")

    def test_T08_TA10_never_raises(self):
        self.assertEqual(ag.read({})["unknown"], ["agents"])


class Routes(unittest.TestCase):
    def test_routes_are_discovered(self):
        routes, errors = squadboard.load_routes()
        self.assertEqual(errors, [])
        self.assertIn("/api/agents", routes)
        self.assertIn("/api/active", routes)


if __name__ == "__main__":
    unittest.main()
