"""T02: the givens of the board fixture exist. One test per business AC id; no board is started."""
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import board_fixtures  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


class FixtureGivens(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fx = board_fixtures.copy_fixture()
        cls.addClassCleanup(board_fixtures.cleanup, cls.fx)

    def test_T02_AC1_picker_counts(self):
        sq = self.fx.squad
        self.assertEqual(sorted(p.name for p in (sq / "goals").iterdir()), ["alpha", "beta", "gamma"])
        goal_of = {}
        for p in (sq / "scopes").iterdir():
            if p.name == "_done":
                continue
            m = re.search(r"^goal:[ \t]*(\S*)", (p / "scope.md").read_text(encoding="utf-8"), re.M)
            goal_of[p.name] = m.group(1) if m else ""
        self.assertEqual(sum(1 for g in goal_of.values() if g == "alpha"), 4)
        self.assertEqual(sum(1 for g in goal_of.values() if g == ""), 6)
        self.assertEqual(len(list((sq / "scopes/_done").iterdir())), 20)
        self.assertTrue((self.fx.other_squad / "scopes").is_dir())

    def test_T02_AC2_every_stage_has_a_task(self):
        tickets = {p.name[:2] for p in (self.fx.repo / ".scratch/checkout-tasks/issues").glob("*.md")}
        self.assertEqual(tickets, {"0%d" % i for i in range(1, 10)})
        text = (self.fx.scope / "messages.jsonl").read_text(encoding="utf-8")
        recs = [json.loads(line) for line in text.splitlines()]
        by = lambda t, n: [r for r in recs if r["type"] == t and r["task"] == n]  # noqa: E731
        self.assertEqual(len({r["text"] for r in by("FAIL", "03")}), 3)         # returned, 3 FAIL
        self.assertTrue(by("BLOCKED", "04"))
        self.assertEqual(len(by("PASS", "05")), 1)                              # 1 of 2 PASS
        self.assertEqual(len(by("PASS", "06")), 2)
        self.assertFalse(list((self.fx.repo / ".scratch").glob("*/issues/*REV*")))  # REV-8: a token, no ticket
        self.assertTrue(by("HANDIN", "REV-8"))
        self.assertNotIn("{{sha:", text)
        branch = lambda n: "squad/fix/checkout/fix-dev-" + n  # noqa: E731
        tip = lambda n: subprocess.run(["git", "rev-parse", "--short=10", branch(n)], cwd=self.fx.repo, capture_output=True,
                                       text=True, encoding="utf-8").stdout.strip()
        merged = subprocess.run(["git", "branch", "--merged", "main"], cwd=self.fx.repo, capture_output=True, text=True,
                                encoding="utf-8").stdout
        self.assertIn(tip("06"), by("PASS", "06")[0]["text"])                   # ready for review: tip = passed sha
        self.assertNotIn(tip("07"), by("PASS", "07")[0]["text"])                # sha changed after PASS
        self.assertIn(branch("08"), merged)                                     # merged
        self.assertNotIn(branch("06"), merged)

    def test_T02_AC3_herdr_recordings(self):
        agents = json.loads(self.fx.herdr_json.read_text(encoding="utf-8"))["result"]["agents"]
        status = {a["name"]: a["agent_status"] for a in agents}
        self.assertEqual(status["fix-dev-02"], "blocked")
        self.assertIn("working", status.values())
        self.assertNotIn("fix-dev-03", status)                                  # retired in roster.md, not listed
        self.assertIn("| fix-dev-03 | dev | checkout | ticket 03 | retired |", (self.fx.scope / "roster.md").read_text(encoding="utf-8"))
        down = json.loads(self.fx.herdr_down.read_text(encoding="utf-8"))
        self.assertEqual(down["error"]["code"], "server_not_running")

    def test_T02_AC4_steps_name_commands_that_exist(self):
        steps = self.fx.steps.read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"^\d\. \*\*", steps, re.M)), 5)
        for word in ("chmod", "localStorage", "kill", "append-message", "squad-inbox"):
            self.assertIn(word, steps)
        for path in ("bin/squad-inbox", "tests/board_fixtures.py"):
            self.assertTrue((ROOT / path).exists(), path)
        base = ROOT / "tests/fixtures/board"
        self.assertTrue((base / "FIXTURE-STEPS.md").exists())
        # the CLI answer step works on the copy and nowhere else
        q = self.fx.squad / "scopes/questions"
        r = subprocess.run([sys.executable, str(ROOT / "bin/squad-inbox"), "--home", str(q), "answer", "E1", "--option", "a",
                            "--source", "chat"], capture_output=True, text=True, encoding="utf-8", input="", timeout=30,
                           env={**os.environ, "SQUAD_ROLE": "manager"})
        self.assertEqual(r.returncode, 0, r.stderr)
        orig = (base / "repo/dot-claude/squads/fix/scopes/questions/escalations.md").read_text(encoding="utf-8")
        self.assertNotEqual(orig, (q / "escalations.md").read_text(encoding="utf-8"))  # the copy changed, the fixture did not
        board_fixtures.append_message(self.fx.scope, "PASS", "03", "fix-qaw-checkout", "PASS 03: x")
        self.assertTrue((self.fx.scope / "messages.jsonl").read_text(encoding="utf-8").rstrip().endswith('"iteration": 1}'))


if __name__ == "__main__":
    unittest.main()
