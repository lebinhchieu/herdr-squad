"""squad-report rollup (ticket 06): files + goal form, statuses, partial totals, relative links, XSS structure, real build input."""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "bin"))
import squadreport_build as bd  # noqa: E402
import squadreport_rollup as ro  # noqa: E402
from report_fixtures import Fixture, T0, tasks_scope  # noqa: E402

CLI = str(ROOT / "bin" / "squad-report")
PRICES_A = {"m": {"input": 1}}
PRICES_B = {"m": {"input": 2}}
PLANT = '</script><img src=x onerror=alert(1)>"><svg onload=1>'


def scope_json(squad, name, cost, agent_s, gen="2026-10-02T10:00:00Z", last="2026-10-02T09:00:00Z", prices=PRICES_A,
               returns=0, passed=2, status="done", redact=False, title="T", size="M", att=80.0, start="2026-10-01T00:00:00Z",
               end="2026-10-02T00:00:00Z", reason="needs work"):
    return {"schema_version": 1, "kind": "scope",
            "scope": {"name": name, "squad": squad, "size": size, "status": status, "generated_at": gen, "last_message_at": last,
                      "window": {"start": start, "end": end}},
            "config": {"prices": prices},
            "totals": {"wall_s": 86400, "agent_s": agent_s, "buckets_s": {"working": agent_s // 2, "waiting": 0, "blocking": 0, "idle": agent_s - agent_s // 2},
                       "tokens": {"input": 10, "cache_read": 20, "cache_write": 30, "output": 40}, "cost_usd": cost, "returns": returns,
                       "tasks_passed": passed, "attributed": {"time_pct": att}, "po_wait": {"total_s": 600}},
            "tasks": [{"id": "01", "title": None if redact else title, "flag": returns >= 3,
                       "returns_list": [{"reason": None if redact else reason}] * returns},
                      {"id": "02", "title": None if redact else title, "flag": False, "returns_list": []}],
            "roles": [{"role": "developer", "buckets_s": {"working": agent_s}, "tokens": {"output": 100}, "cost_usd": cost}]}


def write(d, rel, obj, raw=None):
    p = Path(d) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(raw if raw is not None else json.dumps(obj), encoding="utf-8")
    return str(p)


def rollup(files, out, cwd=None, extra=()):
    env = {k: v for k, v in os.environ.items() if k not in ("SQUAD_DIR", "SCOPE_DIR", "GOAL_DIR")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run([sys.executable, "-B", CLI, "rollup"] + list(files) + ["--out", out] + list(extra), capture_output=True,
                          env=env, cwd=cwd, timeout=60)


class FilesForm(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        a = write(self.d, "a/data.json", scope_json("alpha", "s1", 10.0, 1000, returns=1))
        b = write(self.d, "b/data.json", scope_json("beta", "s1", 5.5, 500, prices=PRICES_B))
        old = write(self.d, "c/data.json", scope_json("alpha", "s1", 99.0, 9999, gen="2026-10-01T10:00:00Z"))
        kind = write(self.d, "d/data.json", {**scope_json("x", "k", 1, 1), "kind": "rollup"})
        junk = write(self.d, "e/data.json", None, raw="{not json")
        red = write(self.d, "f/data.json", scope_json("gamma", "s9", 2.0, 200, redact=True, returns=2))
        (self.d / "a" / "report.html").write_text("<html></html>", encoding="utf-8")
        self.files = [a, b, old, kind, junk, red]
        self.out = str(self.d / "roll")
        self.r = rollup(self.files, self.out, cwd=str(self.d))
        self.data = json.loads((Path(self.out) / "data.json").read_text(encoding="utf-8"))

    def tearDown(self):
        self.tmp.cleanup()

    def by(self, status):
        return [s for s in self.data["scopes"] if s["status"] == status]

    def test_rows_and_statuses(self):
        self.assertEqual(self.r.returncode, 0, self.r.stderr)
        self.assertEqual(len(self.data["scopes"]), 6)
        self.assertEqual(sorted((s["squad"], s["name"]) for s in self.data["scopes"] if s["status"] == "done"),
                         [("alpha", "s1"), ("beta", "s1"), ("gamma", "s9")])
        sk = self.by("skipped")[0]
        self.assertIn("Older copy", sk["reason"])
        self.assertIsNone(sk["totals"])
        self.assertIn("kind", self.by("schema_mismatch")[0]["reason"])
        self.assertIn("not JSON", self.by("unreadable")[0]["reason"])
        self.assertIn("skipped:", self.r.stderr.decode())

    def test_totals_partial_sum_ok_only(self):
        t = self.data["totals"]
        self.assertEqual((t["included"], t["listed"]), (3, 6))
        self.assertTrue(t["partial"])
        self.assertEqual(t["cost_usd"], 17.5)
        self.assertEqual(t["agent_s"], 1700)
        self.assertEqual(t["returns"], 3)
        self.assertEqual(t["tokens"]["output"], 120)
        self.assertEqual(t["po_wait_s"], 1800)
        self.assertEqual(t["passed"], 6)
        self.assertEqual(sum(r["cost_usd"] for r in self.data["roles"]), 17.5)

    def test_mixed_prices_and_redact(self):
        self.assertTrue(self.data["totals"]["mixed_prices"])
        red = [s for s in self.data["scopes"] if s["name"] == "s9"][0]
        self.assertTrue(red["redacted"])
        self.assertIsNone(red["top_reason"])
        top = [d for d in self.data["digest"] if d["kind"] == "most_returns_scope"][0]
        self.assertIn("reasons not shared", top["text"])

    def test_report_href_relative_or_null(self):
        a = [s for s in self.data["scopes"] if s["squad"] == "alpha" and s["status"] == "done"][0]
        self.assertEqual(a["report_href"], "../a/report.html")
        self.assertIsNone([s for s in self.data["scopes"] if s["squad"] == "beta"][0]["report_href"])

    def test_href_survives_move(self):
        import shutil
        dst = self.d / "moved"
        for sub in ("a", "roll"):
            shutil.copytree(self.d / sub, dst / sub)
        d2 = json.loads(ro.emb.dumps({}))  # noqa: F841
        r = rollup([str(dst / "a" / "data.json")], str(dst / "roll2"))
        out = json.loads((dst / "roll2" / "data.json").read_text(encoding="utf-8"))
        self.assertEqual(out["scopes"][0]["report_href"], "../a/report.html")

    def test_no_absolute_path_in_output(self):
        for f in ("index.html", "data.json"):
            text = (Path(self.out) / f).read_text(encoding="utf-8")
            self.assertNotIn(str(self.d), text)
            self.assertNotIn(self.tmp.name, text)
        self.assertNotIn(self.tmp.name, self.r.stderr.decode())

    def test_stale_and_running(self):
        p = write(self.d, "g/data.json", scope_json("alpha", "late", 1.0, 100, gen="2026-10-02T10:00:00Z", last="2026-10-05T00:00:00Z"))
        q = write(self.d, "h/data.json", scope_json("alpha", "live", 1.0, 100, status="running"))
        rollup([p, q], str(self.d / "r2"))
        rows = {s["name"]: s for s in json.loads((self.d / "r2" / "data.json").read_text(encoding="utf-8"))["scopes"]}
        self.assertEqual((rows["late"]["status"], rows["live"]["status"]), ("stale", "running"))

    def test_html_structure(self):
        html = (Path(self.out) / "index.html").read_text(encoding="utf-8")
        self.assertNotRegex(html, r"https?://")
        self.assertNotRegex(html, r"\b(src|href)=[\"'](?!#)")
        self.assertNotIn("__DATA__", html)
        self.assertNotIn("__JS__", html)
        self.assertNotIn("innerHTML", html)
        m = re.search(r'<script type="application/json" id="data">(.*?)</script>', html, re.S)
        got = json.loads(m.group(1))
        self.assertEqual(got, self.data)

    def test_all_unusable_exit_2_still_writes(self):
        r = rollup([self.files[4]], str(self.d / "r3"))
        self.assertEqual(r.returncode, 2)
        self.assertTrue((self.d / "r3" / "index.html").exists())

    def test_bad_input_never_raises(self):
        r = rollup([str(self.d / "nope.json"), self.files[0]], str(self.d / "r4"))
        self.assertEqual(r.returncode, 0)


class Xss(unittest.TestCase):
    def test_plant_in_names_and_titles(self):
        with tempfile.TemporaryDirectory() as t:
            f = write(t, "x/data.json", scope_json(PLANT, PLANT, 1.0, 100, title=PLANT, returns=1, reason=PLANT))
            g = write(t, "y/data.json", scope_json("sq", "ok", 1.0, 100))
            rollup([f, g], str(Path(t) / "o"))
            html = (Path(t) / "o" / "index.html").read_text(encoding="utf-8")
            self.assertEqual(html.count("</script>"), 2)
            self.assertNotIn("<img src=x", html)
            self.assertNotIn("<svg onload", html)
            m = re.search(r'id="data">(.*?)</script>', html, re.S)
            self.assertIn(PLANT, json.loads(m.group(1))["scopes"][1]["name"] + json.loads(m.group(1))["scopes"][0]["name"])


class GoalForm(unittest.TestCase):
    def test_goal_scopes_and_no_data(self):
        with tempfile.TemporaryDirectory() as t:
            sq = Path(t) / "squad"
            for n in ("s1", "s2", "s3"):
                (sq / "scopes" / n).mkdir(parents=True)
                (sq / "scopes" / n / "scope.md").write_text("# Scope\ngoal: G\n", encoding="utf-8")
            (sq / "scopes" / "other").mkdir()
            (sq / "scopes" / "other" / "scope.md").write_text("goal: H\n", encoding="utf-8")
            (sq / "goals" / "G").mkdir(parents=True)
            write(sq, "scopes/s1/report/data.json", scope_json("squad", "s1", 4.0, 400))
            write(sq, "scopes/s2/report/data.json", scope_json("squad", "s2", 6.0, 600))
            env = {k: v for k, v in os.environ.items() if k not in ("SQUAD_DIR", "SCOPE_DIR", "GOAL_DIR")}
            r = subprocess.run([sys.executable, "-B", CLI, "G", "--squad", str(sq)], capture_output=True, env=env, timeout=60)
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads((sq / "goals" / "G" / "report" / "data.json").read_text(encoding="utf-8"))
            self.assertEqual(data["kind"], "rollup")
            self.assertEqual(data["totals"]["cost_usd"], 10.0)
            self.assertTrue(data["totals"]["partial"])
            nd = [s for s in data["scopes"] if s["status"] == "no_data"]
            self.assertEqual([s["name"] for s in nd], ["s3"])
            self.assertEqual(nd[0]["command"], "squad-report s3")
            self.assertEqual(len(data["scopes"]), 3)
            self.assertTrue((sq / "goals" / "G" / "report" / "index.html").exists())


class RealOutput(unittest.TestCase):
    def test_rollup_of_real_build(self):
        fx = Fixture()
        self.addCleanup(fx.close)
        tasks_scope(fx)
        with mock.patch.dict(os.environ, fx.env()):
            data = bd.build(fx.home, fx.squad, now=T0 + 5000)
        with tempfile.TemporaryDirectory() as t:
            f = write(t, "r/data.json", data)
            r = rollup([f], str(Path(t) / "o"))
            self.assertEqual(r.returncode, 0, r.stderr)
            out = json.loads((Path(t) / "o" / "data.json").read_text(encoding="utf-8"))
            row = out["scopes"][0]
            self.assertIn(row["status"], ("done", "running", "stale"))
            self.assertEqual(row["totals"]["cost_usd"], data["totals"]["cost_usd"])
            self.assertEqual(row["totals"]["returns"], data["totals"]["returns"])
            self.assertEqual(row["totals"]["agent_s"], data["totals"]["agent_s"])
            self.assertEqual(row["totals"]["passed"], data["totals"]["tasks_passed"])
            self.assertEqual(row["totals"]["po_wait_s"], data["totals"]["po_wait"]["total_s"])
            self.assertEqual(sum(row["totals"]["tokens"].values()), sum(data["totals"]["tokens"].values()))
            self.assertEqual(sum(x["cost_usd"] for x in row["roles"]), sum(x["cost_usd"] for x in data["roles"]))
            self.assertEqual(out["totals"]["attributed_time_pct"], data["totals"]["attributed"]["time_pct"])


if __name__ == "__main__":
    unittest.main()
