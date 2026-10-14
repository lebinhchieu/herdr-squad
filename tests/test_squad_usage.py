"""squad-usage: fixture transcripts in, table / --check rule / roster edit out."""
import json
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "squad-usage"
T0 = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)
NOW = datetime.now(timezone.utc)


def turn(minutes, msg_id, ctx=(2, 1000, 0), out=100, model="claude-sonnet-5-5", effort="medium", base=T0, **extra):
    inp, read, write = ctx
    return {"type": "assistant", "timestamp": (base + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z"),
            "effort": effort, "sessionId": "s",
            "message": {"id": msg_id, "model": model,
                        "usage": {"input_tokens": inp, "cache_read_input_tokens": read,
                                  "cache_creation_input_tokens": write, "output_tokens": out}}, **extra}


class UsageHomeTest(unittest.TestCase):
    def test_get_reads_the_roster_of_scope_dir_before_squad_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            squad, scope = Path(tmp) / "squad", Path(tmp) / "squad" / "scopes" / "sc1"
            scope.mkdir(parents=True)
            head = "| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"
            (squad / "roster.md").write_text(head + "| dev-1 | dev | flat | x | live | s-flat |\n")
            (scope / "roster.md").write_text(head + "| dev-1 | dev | sc1 | x | live | s-scope |\n")
            env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
            env.update(SQUAD_DIR=str(squad), SCOPE_DIR=str(scope))
            r = subprocess.run([str(SCRIPT), "--get", "dev-1"], env=env, text=True, capture_output=True, timeout=10)
            self.assertEqual(r.stdout.split("\t")[2].strip(), "s-scope", r.stderr)
            env.pop("SCOPE_DIR")
            env["GOAL_DIR"] = str(scope)
            r = subprocess.run([str(SCRIPT), "--get", "dev-1"], env=env, text=True, capture_output=True, timeout=10)
            self.assertEqual(r.stdout.split("\t")[2].strip(), "s-scope", r.stderr)


class UsageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.cfg = root / "cfg"
        self.proj = self.cfg / "projects" / "-some-cwd"
        self.proj.mkdir(parents=True)
        self.squad = root / "squad"
        self.squad.mkdir()
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR", "CLAUDE_CONFIG_DIR"))}
        self.env["CLAUDE_CONFIG_DIR"] = str(self.cfg)

    def tearDown(self):
        self.tmp.cleanup()

    def transcript(self, sid, lines):
        (self.proj / f"{sid}.jsonl").write_text("".join(json.dumps(l) + "\n" for l in lines))

    def run_cli(self, *args):
        return subprocess.run([str(SCRIPT), *args], env=self.env, text=True, capture_output=True, timeout=10)

    def test_table_totals(self):
        self.transcript("sid-1", [
            {"type": "user", "timestamp": "2026-10-01T09:00:00Z"},
            turn(0, "m1", ctx=(2, 0, 20_000), out=50),
            turn(1, "m1", ctx=(2, 0, 20_000), out=80),  # same message, later line: counts once, final usage
            turn(2, "m2", ctx=(2, 20_000, 40_000), out=100),
            turn(3, "m3", ctx=(2, 60_000, 10_000), out=70),
            turn(4, "side", isSidechain=True),
            turn(5, "syn", model="<synthetic>"),
        ])
        (self.squad / "roster.md").write_text(
            "| Agent | Role | Scope | Owns | Status | Session |\n|---|---|---|---|---|---|\n"
            "| manager | Manager | all | x | live | |\n| dev-1 | Dev | s | y | live | sid-1 |\n")
        r = self.run_cli("--squad-dir", str(self.squad))
        self.assertEqual(r.returncode, 0, r.stderr)
        row = next(l for l in r.stdout.splitlines() if l.startswith("dev-1")).split()
        # turns=3, peak=70002 -> 70k, last=70002, out=80+100+70=250 -> 0k, 0 expiries, 0 compactions
        self.assertEqual(row[1], "claude-sonnet-5-5/medium")
        self.assertEqual(row[2], "3")
        self.assertEqual(row[3:5], ["70k", "70k"])
        self.assertEqual(row[5:], ["0k", "0", "0"])
        self.assertNotIn("manager", r.stdout)

    def test_cache_expiry_needs_gap_and_big_write(self):
        self.transcript("sid-1", [
            turn(0, "a", ctx=(2, 0, 50_000)),
            turn(30, "b", ctx=(2, 50_000, 1_000)),               # 30 min gap, small write
            turn(30 + 61, "c", ctx=(2, 0, 52_000)),              # >1h gap, big write -> expiry
            turn(30 + 61 + 90, "d", ctx=(2, 52_000, 500)),       # >1h gap but cache survived -> not an expiry
        ])
        self.env["SQUAD_DIR"] = str(self.squad)
        (self.squad / "roster.md").write_text("| Agent | Session |\n|---|---|\n| dev-1 | sid-1 |\n")
        r = self.run_cli()
        self.assertEqual(r.stdout.splitlines()[1].split()[-2:], ["1", "0"])

    def test_compaction_counted_once_per_compaction(self):
        self.transcript("sid-1", [turn(0, "a"), {"type": "system", "subtype": "compact_boundary"},
                                  {"type": "user", "isCompactSummary": True}, turn(1, "b")])
        self.assertEqual(self.run_cli("--check", "sid-1").stdout.strip(), "fresh")
        (self.squad / "roster.md").write_text("| Agent | Session |\n|---|---|\n| dev-1 | sid-1 |\n")
        self.assertEqual(self.run_cli("--squad-dir", str(self.squad)).stdout.splitlines()[1].split()[-1], "1")

    def test_check_fresh_over_120k(self):
        self.transcript("hot", [turn(0, "a", ctx=(2, 100_000, 21_000), base=NOW)])    # 121k
        self.transcript("ok", [turn(0, "a", ctx=(2, 100_000, 19_000), base=NOW)])     # 119k
        self.assertEqual(self.run_cli("--check", "hot").stdout.strip(), "fresh")
        self.assertEqual(self.run_cli("--check", "ok").stdout, "")

    def test_check_idle_needs_gap_and_big_context(self):
        old = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat().replace("+00:00", "Z")
        big, small = turn(0, "a", ctx=(2, 110_000, 0)), turn(0, "a", ctx=(2, 90_000, 0))
        big["timestamp"] = small["timestamp"] = old
        self.transcript("big", [big])
        self.transcript("small", [small])
        self.assertEqual(self.run_cli("--check", "big").stdout.strip(), "idle")
        self.assertEqual(self.run_cli("--check", "small").stdout, "")

    def test_check_idle_after_a_gap_that_expired_the_cache(self):
        # what the Stop hook sees: the turn that just ended came after a >1h gap and re-wrote the cache
        self.transcript("big", [turn(0, "a", ctx=(2, 100_000, 0), base=NOW - timedelta(hours=3)),
                                turn(0, "b", ctx=(2, 0, 110_000), base=NOW)])
        self.transcript("small", [turn(0, "a", ctx=(2, 40_000, 0), base=NOW - timedelta(hours=3)),
                                  turn(0, "b", ctx=(2, 0, 50_000), base=NOW)])
        self.transcript("survived", [turn(0, "a", ctx=(2, 100_000, 0), base=NOW - timedelta(hours=3)),
                                     turn(0, "b", ctx=(2, 110_000, 500), base=NOW)])
        self.assertEqual(self.run_cli("--check", "big").stdout.strip(), "idle")
        self.assertEqual(self.run_cli("--check", "small").stdout, "")
        self.assertEqual(self.run_cli("--check", "survived").stdout, "")

    def test_check_unknown_session_prints_nothing(self):
        r = self.run_cli("--check", "nope")
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_the_limit_is_the_same_on_a_1m_model(self):
        self.transcript("big", [turn(0, "a", ctx=(2, 130_000, 0), model="claude-opus-5-5[1m]", base=NOW)])
        self.assertEqual(self.run_cli("--check", "big").stdout.strip(), "fresh")

    def test_check_with_explicit_transcript(self):
        p = Path(self.tmp.name) / "elsewhere.jsonl"
        p.write_text(json.dumps(turn(0, "a", ctx=(2, 150_000, 0))) + "\n")
        self.assertEqual(self.run_cli("--check", "x", "--transcript", str(p)).stdout.strip(), "fresh")

    def test_set_session_updates_row_adds_column_and_appends(self):
        roster = self.squad / "roster.md"
        roster.write_text("# Roster\n\n| Agent | Role | Scope | Owns | Status |\n|---|---|---|---|---|\n"
                          "| manager | Manager | all | x | live |\n")
        self.env["SQUAD_DIR"] = str(self.squad)
        self.run_cli("--set-session", "manager", "sid-m")
        self.run_cli("--set-session", "dev-1", "sid-d", "--role", "Dev", "--scope", "s")
        self.run_cli("--set-session", "dev-1", "sid-d2")
        lines = roster.read_text().splitlines()
        self.assertEqual(lines[0], "# Roster")
        self.assertEqual(lines[2], "| Agent | Role | Scope | Owns | Status | Session |")
        self.assertEqual(lines[4], "| manager | Manager | all | x | live | sid-m |")
        self.assertEqual(lines[5], "| dev-1 | Dev | s |  | live | sid-d2 |")
        self.assertEqual(len(lines), 6)


if __name__ == "__main__":
    unittest.main()
