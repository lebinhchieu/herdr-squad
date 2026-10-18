"""squad-report CLI and build (ticket 04): subprocess against a scratch squad from report_fixtures, field shape of the full build."""
import json
import os
import socket
import stat
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
import squadreport_digest as dg  # noqa: E402
from report_fixtures import Fixture, T0, asst, stamp, tasks_scope  # noqa: E402

CLI = str(ROOT / "bin" / "squad-report")
AGENT_ENV = ("SQUAD_DIR", "SCOPE_DIR", "GOAL_DIR", "SQUAD_NAME", "SQUAD_ROLE", "SQUAD_SCOPE")
TASK_KEYS = {"id", "aliases", "title", "dev", "status", "iteration", "window", "cycle_s", "buckets_s", "tokens", "cost_usd",
             "returns", "flag", "returns_list", "rework_s", "rework_cost_usd", "review_waits"}
RETURN_KEYS = {"fail_at", "fail_by", "handin_at", "reason"}
ITER_KEYS = {"n", "window", "agent_s", "cost_usd", "returns"}
MATRIX_KEYS = {"task", "agent", "time_s", "buckets_s", "tokens", "cost_usd"}
ROLE_KEYS = {"name", "role", "sessions", "respawns", "cache_expiries", "expiry_cost_usd", "transcript_found", "live",
             "buckets_s", "idle_s", "tokens", "cost_usd"}
AGENT_KEYS = {"name", "role", "transcript_found", "live", "segments", "events"}
DIGEST_KEYS = {"id", "kind", "weight", "text", "value", "unit", "target"}
WAIT_KEYS = {"handin_at", "verdict_at", "verdict", "wait_s"}


def run(fx, *args, extra=None, path=None):
    env = {k: v for k, v in os.environ.items() if k not in AGENT_ENV}
    env.update(fx.env())
    env["SQUAD_DIR"] = str(fx.squad)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if path:
        env["PATH"] = path + os.pathsep + env["PATH"]
    env.update(extra or {})
    return subprocess.run([sys.executable, "-B", CLI] + list(args), capture_output=True, env=env, timeout=60)


def out(r):
    return r.stdout.decode("utf-8")


class Base(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.close)
        tasks_scope(self.fx)
        self.data_path = self.fx.home / "report" / "data.json"


class Cli(Base):
    def test_output_summary_and_data_json(self):
        r = run(self.fx, "sc", "--no-html")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = out(r).splitlines()
        self.assertEqual(len(lines), 6)
        self.assertEqual(lines[0], str(self.data_path))
        self.assertEqual([x.split(":")[0] for x in lines[1:]], ["elapsed", "agent-time", "est. cost", "returns", "attributed"])
        self.assertTrue(out(r).isascii())
        self.assertNotIn("\x1b", out(r))
        self.assertIn("returns: 1", lines)
        self.assertTrue(self.data_path.exists())

    def test_quiet_prints_nothing(self):
        r = run(self.fx, "sc", "--no-html", "--quiet")
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, b"", b""))

    def test_second_run_equal_bytes_except_generated_at(self):
        run(self.fx, "sc", "--no-html")
        a = json.loads(self.data_path.read_text(encoding="utf-8"))
        raw = self.data_path.read_bytes()
        run(self.fx, "sc", "--no-html")
        b = json.loads(self.data_path.read_text(encoding="utf-8"))
        a["scope"]["generated_at"] = b["scope"]["generated_at"] = None
        self.assertEqual(a, b)
        self.assertEqual(len(raw), len(self.data_path.read_bytes()))
        self.assertEqual(sorted(p.name for p in self.data_path.parent.iterdir()), ["data.json"])

    def test_done_scope_writes_only_its_report_folder(self):
        fx = Fixture(done=True)
        self.addCleanup(fx.close)
        tasks_scope(fx)
        before = fx.snapshot()
        r = run(fx, "sc", "--no-html", "--final")
        self.assertEqual(r.returncode, 0, r.stderr)
        after = fx.snapshot()
        new = set(after) - set(before)
        self.assertEqual(new, {str(fx.home / "report" / "data.json")})
        self.assertTrue(all(after[k] == before[k] for k in before))
        d = json.loads((fx.home / "report" / "data.json").read_text(encoding="utf-8"))
        self.assertFalse(d["scope"]["partial"])
        self.assertEqual(d["scope"]["status"], "done")

    def test_running_scope_is_partial_unless_final(self):
        run(self.fx, "sc", "--no-html")
        d = json.loads(self.data_path.read_text(encoding="utf-8"))
        self.assertIn("running", d["scope"]["partial_reasons"])
        run(self.fx, "sc", "--no-html", "--final")
        d = json.loads(self.data_path.read_text(encoding="utf-8"))
        self.assertNotIn("running", d["scope"]["partial_reasons"])

    def test_out_dir_and_redact(self):
        o = self.fx.root / "elsewhere"
        r = run(self.fx, "sc", "--no-html", "--out", str(o), "--redact")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.data_path.exists())
        d = json.loads((o / "data.json").read_text(encoding="utf-8"))
        for t in d["tasks"]:
            for x in t["returns_list"]:
                self.assertIsNone(x["reason"])
        for i in d["totals"]["po_wait"]["items"]:
            self.assertIsNone(i["title"])

    def test_no_claude_process_is_spawned(self):
        with tempfile.TemporaryDirectory() as d:
            marker = Path(d) / "called"
            stub = Path(d) / "claude"
            stub.write_text("#!/bin/sh\necho x > '%s'\nexit 99\n" % marker, encoding="utf-8")
            stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
            r = run(self.fx, "sc", "--no-html", path=d)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertFalse(marker.exists())

    def test_no_network(self):
        def boom(*a, **k):
            raise AssertionError("socket used")
        with mock.patch.dict(os.environ, self.fx.env()), mock.patch.object(socket, "socket", boom):
            d = bd.build(self.fx.home, self.fx.squad)
        self.assertEqual(d["schema_version"], 1)

    def test_html_renderer_missing_is_skipped(self):
        r = run(self.fx, "sc")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(out(r).splitlines()[0], str(self.data_path))


class Status(Base):
    def test_missing_fresh_stale(self):
        r = run(self.fx, "status", "sc")
        self.assertEqual((r.returncode, out(r).strip()), (4, "missing"))
        run(self.fx, "sc", "--no-html")
        r = run(self.fx, "status", "sc")
        self.assertEqual((r.returncode, out(r).strip()), (0, "fresh"))
        with open(self.fx.home / "messages.jsonl", "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"ts": stamp(9000), "from": "tl", "to": "dev", "text": "STATUS? x"}) + "\n")
        r = run(self.fx, "status", "sc")
        self.assertEqual((r.returncode, out(r).strip()), (3, "stale"))

    def test_stale_on_escalation_and_roster(self):
        run(self.fx, "sc", "--no-html")
        with open(self.fx.home / "inbox.jsonl", "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"ev": "answer", "id": "E2", "ts": stamp(9000), "text": "ok"}) + "\n")
        self.assertEqual(run(self.fx, "status", "sc").returncode, 3)
        run(self.fx, "sc", "--no-html")
        self.assertEqual(run(self.fx, "status", "sc").returncode, 0)
        with open(self.fx.home / "roster.md", "a", encoding="utf-8", newline="\n") as f:
            f.write("| new | dev | sc |  | live | s |\n")
        self.assertEqual(run(self.fx, "status", "sc").returncode, 3)


class Refusals(Base):
    def test_unknown_name(self):
        r = run(self.fx, "nope", "--no-html")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(len(r.stderr.decode().strip().splitlines()), 1)

    def test_flat_squad(self):
        flat = self.fx.root / "flat"
        flat.mkdir()
        (flat / "roster.md").write_text("x\n", encoding="utf-8")
        r = run(self.fx, "sc", "--squad", str(flat))
        self.assertEqual(r.returncode, 2)

    def test_transcripts_gone_leaves_old_report(self):
        run(self.fx, "sc", "--no-html")
        raw = self.data_path.read_bytes()
        for p in self.fx.proj.glob("*.jsonl"):
            p.unlink()
        r = run(self.fx, "sc", "--no-html")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(self.data_path.read_bytes(), raw)

    def test_deadline_exits_5_and_leaves_old_report(self):
        run(self.fx, "sc", "--no-html")
        raw = self.data_path.read_bytes()
        r = run(self.fx, "sc", "--no-html", "--deadline", "-1")
        self.assertEqual(r.returncode, 5)
        self.assertEqual(self.data_path.read_bytes(), raw)


class Goal(Base):
    def test_goal_name_goes_to_rollup_stub(self):
        for rel in ("goals/g1", "goals/_done/g2"):
            (self.fx.squad / rel).mkdir(parents=True)
        for g in ("g1", "g2"):
            r = run(self.fx, g)
            self.assertEqual(r.returncode, 2)
            self.assertIn("not built", r.stderr.decode())
        self.assertEqual(run(self.fx, "g3").returncode, 2)
        self.assertNotIn("not built", run(self.fx, "g3").stderr.decode())

    def test_subcommand_stubs(self):
        for sub in ("rollup", "query"):
            r = run(self.fx, sub, "sc")
            self.assertEqual(r.returncode, 2)
            self.assertIn("not built", r.stderr.decode())


class FieldShape(Base):
    def build(self):
        with mock.patch.dict(os.environ, self.fx.env()):
            return bd.build(self.fx.home, self.fx.squad, final=True)

    def test_every_row_has_exactly_the_spec_fields(self):
        d = self.build()
        self.assertTrue(d["tasks"] and d["matrix"] and d["roles"] and d["agents"] and d["iterations"])
        for t in d["tasks"]:
            self.assertEqual(set(t), TASK_KEYS)
            for r in t["returns_list"]:
                self.assertEqual(set(r), RETURN_KEYS)
                self.assertIsNotNone(r["fail_at"])
            for w in t["review_waits"]:
                self.assertEqual(set(w), WAIT_KEYS)
                if w["verdict"] != "none":
                    self.assertIsNotNone(w["verdict_at"])
            self.assertEqual(set(t["window"]), {"start", "end"})
        self.assertEqual(sum(len(t["returns_list"]) for t in d["tasks"]), d["totals"]["returns"])
        for x in d["iterations"]:
            self.assertEqual(set(x), ITER_KEYS)
            self.assertTrue(x["window"]["start"] and x["window"]["end"])
        for x in d["matrix"]:
            self.assertEqual(set(x), MATRIX_KEYS)
        for x in d["roles"]:
            self.assertEqual(set(x), ROLE_KEYS)
        for a in d["agents"]:
            self.assertEqual(set(a), AGENT_KEYS)
            for s in a["segments"]:
                self.assertEqual(len(s), 5)
                self.assertLessEqual(s[0], s[1])
                self.assertIn(s[2], "wabi")
                self.assertEqual(len(s[2]), 1)
            for e in a["events"]:
                self.assertEqual(len(e), 3)
        self.assertTrue(d["digest"])
        for x in d["digest"]:
            self.assertEqual(set(x), DIGEST_KEYS)
        self.assertLessEqual(len(d["digest"]), 8)
        items = d["totals"]["po_wait"]["items"]
        self.assertEqual({i["id"] for i in items}, {"E1", "E2"})
        for i in items:
            if i["answered_at"] is not None:
                self.assertGreaterEqual(i["wait_s"], 0)
        self.assertEqual(sum(d["totals"]["buckets_s"].values()), d["totals"]["agent_s"])

    def test_one_agent_no_messages_constant_case(self):
        fx = Fixture(scope="solo")
        self.addCleanup(fx.close)
        fx.session("dev", [[asst(0), asst(100), asst(250)]])
        with mock.patch.dict(os.environ, fx.env()):
            d = bd.build(fx.home, fx.squad)
        self.assertEqual(d["totals"]["agent_s"], 250)
        self.assertEqual(d["totals"]["returns"], 0)
        self.assertEqual(d["tasks"], [])
        self.assertEqual(d["totals"]["attributed"]["time_pct"], 0.0)
        for x in d["digest"]:
            self.assertEqual(set(x), DIGEST_KEYS)

    def test_summary_helper(self):
        self.assertEqual(dg.fmt_dur(3725), "1h02m")
        self.assertEqual(dg.fmt_dur(125), "2m05s")
        self.assertEqual(dg.fmt_dur(9), "9s")


if __name__ == "__main__":
    unittest.main()
