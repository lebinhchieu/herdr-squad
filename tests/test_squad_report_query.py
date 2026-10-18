"""squad-report query (ticket 07): real build output of the 02/03 fixture scope, no transcripts needed after the build; skills text."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "bin"))
import squadreport_build as bd  # noqa: E402
import squadreport_query as q  # noqa: E402
from report_fixtures import Fixture, tasks_scope  # noqa: E402

CLI = str(ROOT / "bin" / "squad-report")
AGENT_ENV = ("SQUAD_DIR", "SCOPE_DIR", "GOAL_DIR", "SQUAD_NAME", "SQUAD_ROLE", "SQUAD_SCOPE")


class Base(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.close)
        tasks_scope(self.fx)
        old = dict(os.environ)
        os.environ.update(self.fx.env())
        self.addCleanup(lambda: (os.environ.clear(), os.environ.update(old)))
        self.data = bd.build(self.fx.home, self.fx.squad)  # the real build, not a hand-written data.json
        self.out = self.fx.home / "report"
        self.out.mkdir()
        bd.write_data(self.data, self.out)

    def cli(self, *args, squad=True):
        env = {k: v for k, v in os.environ.items() if k not in AGENT_ENV}
        if squad:
            env["SQUAD_DIR"] = str(self.fx.squad)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        r = subprocess.run([sys.executable, "-B", CLI, "query"] + list(args), capture_output=True, env=env, timeout=60)
        return r.returncode, r.stdout.decode(), r.stderr.decode()


class Query(Base):
    def test_digest_order_matches_data(self):
        rc, out, _ = self.cli("sc", "digest")
        self.assertEqual(rc, 0)
        ids = [l.split()[0] for l in out.splitlines()]
        self.assertEqual(ids, [d["id"] for d in self.data["digest"]][:5])
        self.assertEqual(ids[0], "top_cost_role")

    def test_top_bounds(self):
        rc, out, _ = self.cli("sc", "digest", "--top", "2")
        self.assertEqual(len(out.splitlines()), 2)
        self.assertLessEqual(len(self.cli("sc", "matrix", "--top", "1")[1].splitlines()), 1)

    def test_task_row(self):
        rc, out, _ = self.cli("sc", "task", "--task", "07")
        self.assertEqual(rc, 0)
        self.assertIn("07 passed", out.splitlines()[0])
        self.assertIn("returns 1", out)
        self.assertIn("one blocking finding", out)

    def test_returns_headline_of_top_task(self):
        rc, out, _ = self.cli("sc", "returns")
        self.assertEqual(rc, 0)
        self.assertIn("07 return 1", out)
        self.assertIn("by qa: one blocking finding", out)

    def test_tasks_roles_matrix_iterations_totals(self):
        for what, needle in (("tasks", "07 passed"), ("roles", "dev (developer)"), ("matrix", "07 x dev"),
                             ("iterations", "iteration 1"), ("totals", "elapsed")):
            rc, out, _ = self.cli("sc", what)
            self.assertEqual(rc, 0, what)
            self.assertIn(needle, out, what)
        self.assertIn("message window only", self.cli("sc", "iterations")[1])
        self.assertIn("dev (developer)", self.cli("sc", "role", "--role", "dev")[1])

    def test_json(self):
        rc, out, _ = self.cli("sc", "tasks", "--json")
        obj = json.loads(out)
        self.assertEqual([t["id"] for t in obj["data"]], ["07"])
        self.assertFalse(obj["stale"])

    def test_ascii_no_ansi(self):
        for what in q.WHAT:
            _, out, _ = self.cli("sc", what, "--task", "07", "--role", "dev")
            self.assertTrue(out.isascii() and "\x1b" not in out, what)

    def test_refusals_exit_2_one_line(self):
        for args in (("sc", "bogus"), ("nope", "digest"), ("sc", "task"), ("sc", "task", "--task", "ZZ")):
            rc, out, err = self.cli(*args)
            self.assertEqual(rc, 2, args)
            self.assertEqual(len(err.strip().splitlines()), 1, args)
        shutil.rmtree(self.out)
        rc, _, err = self.cli("sc", "digest")
        self.assertEqual(rc, 2)
        self.assertIn("no data.json", err)

    def test_stale_first_line_and_refresh(self):
        with open(self.fx.home / "messages.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": "2027-01-15T09:00:00Z", "msg_id": "gx", "from": "dev", "to": "qa", "type": None,
                                "task": None, "text": "hi"}) + "\n")
        rc, out, _ = self.cli("sc", "digest")
        self.assertEqual(rc, 0)
        self.assertEqual(out.splitlines()[0], "stale")
        rc, out, _ = self.cli("sc", "digest", "--refresh")
        self.assertEqual(rc, 0)
        self.assertNotEqual(out.splitlines()[0], "stale")

    def test_reads_data_json_only(self):
        keep = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, keep, True)
        shutil.copy(self.out / "data.json", keep / "data.json")
        shutil.rmtree(self.fx.claude)
        shutil.rmtree(self.fx.squad)
        rc, out, err = self.cli(str(keep / "data.json"), "digest", squad=False)
        self.assertEqual(rc, 0, err)
        self.assertIn("top_cost_role", out)


class Blocks(Base):
    def fake(self):
        d = json.loads(json.dumps(self.data))
        for a in d["agents"]:
            if a["name"] == "dev":
                a["segments"] += [[2200, 2500, "b", "07", "qa"], [2600, 2700, "b", None, "PO"]]
        for r in d["roles"]:
            if r["name"] == "dev":
                r["buckets_s"]["blocking"] = 250
        for t in d["tasks"]:
            t["buckets_s"]["blocking"] = 250
        return d

    def test_blocks_longest_first_who_on_whom_and_capped(self):
        d = self.fake()
        b = q.blocks(d)
        self.assertEqual([(x["agent"], x["on"]) for x in b], [("dev", "qa"), ("dev", "PO")])
        self.assertEqual(b[0]["s"], 250)  # 300 s segment capped at the 250 s bucket
        self.assertTrue(all(x["s"] <= 250 for x in b))

    def test_real_build_blocks_never_exceed_bucket(self):
        caps = {r["name"]: r["buckets_s"]["blocking"] for r in self.data["roles"]}
        for b in q.blocks(self.data):
            self.assertLessEqual(b["s"], caps[b["agent"]])
        _, lines = q.answer(self.data, "blocks", type("A", (), {"top": 5, "top_given": None, "task": None, "role": None})())
        self.assertEqual(lines, [])


class Skills(unittest.TestCase):
    def read(self, name):
        return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")

    def test_frontmatter_name_is_folder(self):
        for name in ("squad-report", "squad-report-analyze"):
            m = re.match(r"---\nname: (.+)\ndescription: .+\n(disable-model-invocation: true\n)?---\n", self.read(name))
            self.assertIsNotNone(m, name)
            self.assertEqual(m.group(1), name)
        self.assertIn("disable-model-invocation: true", self.read("squad-report"))

    def test_referenced_commands_exist(self):
        sub = {"status", "query", "rollup"}
        for name in ("squad-report", "squad-report-analyze"):
            text = self.read(name)
            self.assertTrue((ROOT / "bin" / "squad-report").exists())
            for w in re.findall(r"squad-report (query|status|rollup)\b", text):
                self.assertIn(w, sub)
            for w in re.findall(r"query <scope> (\w+)", text):
                self.assertIn(w, q.WHAT)

    def test_analyze_has_no_write_step(self):
        text = self.read("squad-report-analyze")
        for bad in (r"\bWrite\b", r"\bEdit\b", r"process\.md", r"\bwrite[s]? (a|the) file"):
            self.assertIsNone(re.search(bad, text), bad)


if __name__ == "__main__":
    unittest.main()
