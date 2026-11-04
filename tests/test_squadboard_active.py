"""squad-board last active (ticket 08, business AC T08.AC1-AC5 and technical TA6-TA10). Fixture: ticket 02."""
import hashlib
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "bin"))
import board_fixtures as bf  # noqa: E402
import squadboard  # noqa: E402
import squadboard_active as ac  # noqa: E402
from pathlib import Path  # noqa: E402

NOW = bf.REF.timestamp()


def snapshot(root):
    return sorted((str(p), p.stat().st_mtime, hashlib.sha1(p.read_bytes()).hexdigest())
                  for p in Path(root).rglob("*") if p.is_file() and ".git" not in p.parts)


class Active(unittest.TestCase):
    def setUp(self):
        self.fx = bf.copy_fixture(now=bf.REF)
        self.env = mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.fx.config_dir)})
        self.env.start()
        self.squad = squadboard.Squad(self.fx.squad, "fix")

    def tearDown(self):
        self.env.stop()
        bf.cleanup(self.fx)

    def sel(self, kind="scope", name="checkout"):
        return {"squad": self.squad, "kind": kind, "name": name, "home": self.squad.find(kind, name),
                "repo_root": self.squad.repo_root, "now": NOW}

    def touch(self, session, age_s):
        f = self.fx.config_dir / "projects" / "-fixture-repo" / (session + ".jsonl")
        os.utime(f, (NOW - age_s, NOW - age_s))

    def test_T08_AC1_working_owner_uses_transcript_time_approx(self):
        self.touch("s-dev02", 180)
        t = ac.read(self.sel())["data"]["tasks"]["02"]
        self.assertEqual((t["source"], t["approx"], t["ts"]), ("transcript", True, NOW - 180))

    def test_T08_AC1_done_task_has_no_transcript_time(self):
        self.touch("s-dev03", 10)  # owner retired: its transcript does not count
        t = ac.read(self.sel())["data"]["tasks"]["03"]
        self.assertNotEqual(t["source"], "transcript")
        self.assertFalse(t["approx"])
        self.assertIsNone(t["quiet_s"])

    def test_T08_AC2_nothing_recorded(self):
        with tempfile.TemporaryDirectory() as d:
            sq = Path(d) / ".claude" / "squads" / "t"
            (sq / "scopes" / "s").mkdir(parents=True)
            (sq / "process.md").write_text("x", encoding="utf-8")
            s = squadboard.Squad(sq, "t")
            sel = {"squad": s, "kind": "scope", "name": "s", "home": s.find("scope", "s"), "repo_root": s.repo_root, "now": NOW}
            with mock.patch.object(ac.squadboard_git, "branch_refs", return_value=[]):
                d = ac.read(sel)["data"]["scope"]
        self.assertEqual((d["ts"], d["source"]), (None, None))

    def test_T08_AC3_missing_transcript_is_partial(self):
        # fix-qab-checkout has a session id and no transcript file; the commits still give a time
        d = ac.read(self.sel())["data"]["scope"]
        self.assertIn("transcript", d["partial"])
        self.assertIsNotNone(d["ts"])
        self.assertEqual(ac.last_active(None, 100.0, None, ["transcript"])["source"], "git")

    def test_T08_AC4_goal_is_newest_scope_or_later(self):
        sel = self.sel("goal", "alpha")
        (self.squad.find("scope", "alpha-api") / "messages.jsonl").write_text(
            '{"ts": "2026-11-04T09:00:00.000Z", "from": "a", "to": "b", "task": "01", "text": "STATUS 01: x"}\n', encoding="utf-8")
        r = ac.read(sel)["data"]
        self.assertEqual(set(r["scopes"]), {"alpha-api", "alpha-ui", "alpha-docs", "alpha-qa"})
        self.assertEqual(r["goal"]["ts"], NOW - 3600)
        mgr = self.fx.config_dir / "projects" / "-fixture-repo" / "s-gm-alpha.jsonl"
        mgr.write_text("{}\n", encoding="utf-8")
        os.utime(mgr, (NOW + 50, NOW + 50))
        self.assertEqual(ac.read(sel)["data"]["goal"]["ts"], NOW + 50)

    def test_T08_AC5_quiet_boundary_and_90_min(self):
        self.assertIsNone(ac.last_active(NOW - 3599, None, None, now=NOW, in_progress=True)["quiet_s"])
        self.assertEqual(ac.last_active(NOW - 3600, None, None, now=NOW, in_progress=True)["quiet_s"], 3600)
        self.assertIsNone(ac.last_active(NOW - 9000, None, None, now=NOW, in_progress=False)["quiet_s"])
        self.touch("s-dev02", 5400)
        self.assertEqual(ac.read(self.sel())["data"]["tasks"]["02"]["quiet_s"], 5400)
        self.touch("s-dev02", 1800)
        self.assertIsNone(ac.read(self.sel())["data"]["tasks"]["02"]["quiet_s"])

    def test_T08_TA6_transcript_only_stat_and_subagents(self):
        sub = self.fx.config_dir / "projects" / "-fixture-repo" / "s-dev02" / "subagents"
        sub.mkdir(parents=True)
        (sub / "agent-x.jsonl").write_text("not json\n", encoding="utf-8")
        os.utime(sub / "agent-x.jsonl", (NOW - 7, NOW - 7))
        self.touch("s-dev02", 900)
        with mock.patch.object(ac.squadtranscript, "agent_name", side_effect=AssertionError("opened")), \
                mock.patch.object(ac.squadtranscript, "read_session", side_effect=AssertionError("parsed")):
            self.assertEqual(ac.transcript_mtime("s-dev02"), NOW - 7)

    def test_T08_TA10_read_only_and_never_raises(self):
        before = snapshot(self.fx.squad)
        ac.read(self.sel())
        ac.read(self.sel("goal", "alpha"))
        self.assertEqual(snapshot(self.fx.squad), before)
        self.assertEqual(ac.read({})["unknown"], ["active"])
        with mock.patch.object(ac.squadboard_git, "branch_refs", return_value=None):
            r = ac.read(self.sel())
        self.assertEqual(r["unknown"], ["git"])
        self.assertIn("git", r["data"]["scope"]["partial"])


if __name__ == "__main__":
    unittest.main()
