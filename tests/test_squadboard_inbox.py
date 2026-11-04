"""Inbox and banner data (ticket 05). Tests are named for the business (T05.ACn) or technical (T05.TAn) AC.

The real `squad-inbox` runs on a copy of the board fixture (ticket 02); the herdr file is the recorded one."""
import datetime
import hashlib
import json
import subprocess
import sys
import unittest
import unittest.mock
from pathlib import Path

from squadtest import BIN

sys.path.insert(0, str(BIN))
import board_fixtures  # noqa: E402
import squadboard  # noqa: E402
import squadboard_inbox as I  # noqa: E402

NOW = datetime.datetime(2026, 11, 4, 10, 0, tzinfo=datetime.timezone.utc)
SAMPLES = Path(__file__).resolve().parent / "fixtures" / "board" / "inbox"
ROW_KEYS = {"id", "title", "age_s", "blocks", "options", "kind", "scope"}


def append(path, text):
    with open(str(path), "a", encoding="utf-8", newline="\n") as f:
        f.write(text)


def tree(root):
    return {str(p): (p.stat().st_mtime_ns, hashlib.sha1(p.read_bytes()).hexdigest())
            for p in sorted(Path(root).rglob("*")) if p.is_file()}


class Base(unittest.TestCase):
    def setUp(self):
        self.fx = board_fixtures.copy_fixture(now=NOW)
        self.addCleanup(board_fixtures.cleanup, self.fx)
        self.squad = squadboard.Squad(self.fx.squad, "fix")

    def sel(self, kind, name, herdr=None, **extra):
        s = {"squads": [self.squad], "squad": self.squad, "kind": kind, "name": name, "params": {},
             "home": self.squad.find(kind, name), "repo_root": self.squad.repo_root, "now": NOW.timestamp(),
             "herdr_json": str(herdr or self.fx.herdr_json)}
        s.update(extra)
        return s

    def read(self, name, **extra):
        r = I.read(self.sel("scope", name, **extra))
        self.assertIsNotNone(r["data"], r)
        return r

    def home(self, name):
        return self.squad.path / "scopes" / name


class Rows(Base):
    def test_T05_AC1_AC3_rows_oldest_first_with_options(self):
        # 1 open question (E1, seen 26 h ago) + 1 unread item (1 h old) in the choice
        append(self.home("questions") / "inbox.jsonl", json.dumps(
            {"ev": "add", "id": "R1", "ts": "2026-11-04T09:00:00Z", "title": "Read the report", "body": "b",
             "blocks": "nothing"}) + "\n")
        d = self.read("questions")["data"]
        self.assertEqual([r["id"] for r in d["rows"]], ["E1", "R1"])
        for r in d["rows"]:
            self.assertEqual(set(r), ROW_KEYS)
        e1, r1 = d["rows"]
        self.assertEqual((e1["title"], e1["blocks"], e1["age_s"], e1["kind"]), ("Pick the payment provider", "ticket 04", 26 * 3600, "open"))
        self.assertEqual((r1["age_s"], r1["kind"]), (3600, "answer"))
        # AC3: option text passed through, the recommended one is data
        self.assertEqual(e1["options"], [{"key": "a", "text": "Stripe", "recommended": True},
                                         {"key": "b", "text": "Adyen", "recommended": False}])
        self.assertEqual(d["count_choice"], 2)

    def test_T05_AC2_nothing_open(self):
        d = self.read("search")["data"]
        self.assertEqual((d["rows"], d["count_choice"]), ([], 0))

    def test_T05_AC4_answer_by_cli_drops_row_and_count_and_page_writes_nothing(self):
        before = tree(self.squad.path)
        self.assertEqual(self.read("questions")["data"]["count_choice"], 1)
        self.assertEqual(tree(self.squad.path), before)  # TA2: no file, no lock, no mtime touched
        subprocess.run([sys.executable, str(BIN / "squad-inbox"), "--home", str(self.home("questions")), "answer", "E1",
                        "--option", "a", "--source", "chat"], check=True, capture_output=True,
                       env={**__import__("os").environ, "SQUAD_ROLE": "manager"})
        d = self.read("questions")["data"]
        self.assertEqual((d["rows"], d["count_choice"]), ([], 0))

    def test_T05_parked_whole_item_is_not_counted_a_parked_point_is(self):
        p = self.home("parked")
        (p / "escalations.md").write_text(
            "# Escalations\n\n| # | Date | Question | Options | Manager's recommendation | Blocks | Answer |\n|---|---|---|---|---|---|---|\n"
            "| 1 | 2026-11-04 | First<br>x | (a) y; (b) n | (a) | nothing |  |\n"
            "| 2 | 2026-11-04 | Second<br>x | (a) y; (b) n | (b) | nothing |  |\n", encoding="utf-8")
        (p / "open-questions.md").write_text("## Q1\nStatus: parked\nParked: 2026-11-03T09:00:00Z\nt\nFrom: E1\n\n"
                                             "## Q2\nStatus: parked\nParked: 2026-11-03T09:00:00Z\nt\nFrom: E2 #2\n", encoding="utf-8")
        d = self.read("parked")["data"]
        self.assertEqual([r["id"] for r in d["rows"]], ["E2"])
        self.assertEqual((d["count_choice"], d["parked"]), (1, 1))


class Squadwide(Base):
    def test_T05_AC5_AC7_banner_entries_and_herdr_down(self):
        r = self.read("questions")
        ents = r["data"]["banner"]["entries"]
        self.assertEqual([(e["agent"], e["pane_id"]) for e in ents], [("fix-dev-02", ents[0]["pane_id"])])
        self.assertTrue(ents[0]["pane_id"])
        self.assertEqual(ents[0]["scope"], "checkout")  # not in the choice, still named
        down = self.read("questions", herdr_json=str(self.fx.herdr_down))
        self.assertIsNone(down["data"]["banner"]["entries"])
        self.assertIn("herdr not running", down["data"]["banner"]["reason"])
        self.assertIn("herdr", down["unknown"])

    def test_T05_AC6_AC8_others_and_ready_for_review(self):
        append(self.home("checkout") / "escalations.md",
               "| 1 | 2026-11-04 | Other scope question<br>x | (a) y; (b) n | (a) | nothing |  |\n")
        ready = {"checkout": 1}
        d = self.read("questions", ready_for_review=lambda sel: ready)["data"]
        # choice: E1. squad: E1 + S3 question + S3 ready branch + S3 permission prompt
        self.assertEqual((d["count_choice"], d["count_squad"]), (1, 4))
        self.assertEqual(d["others"], [{"scope": "checkout", "n": 3}])
        self.assertEqual({r["scope"] for r in d["rows"]}, {"questions"})  # S3's rows do not show under the choice
        # answer S3's question by CLI: the line and the count drop on the next read
        subprocess.run([sys.executable, str(BIN / "squad-inbox"), "--home", str(self.home("checkout")), "answer", "E1",
                        "--option", "a", "--source", "chat"], check=True, capture_output=True,
                       env={**__import__("os").environ, "SQUAD_ROLE": "manager"})
        d = self.read("questions", ready_for_review=lambda sel: ready)["data"]
        self.assertEqual((d["count_squad"], d["others"]), (3, [{"scope": "checkout", "n": 2}]))

    def test_T05_TA7_one_herdr_fetch_per_read(self):
        with unittest.mock.patch.object(I.squadboard_agents, "fetch", wraps=I.squadboard_agents.fetch) as f:
            self.read("questions")
        self.assertEqual(f.call_count, 1)


class Cli(Base):
    def test_T05_TA1_argv_is_read_only(self):
        a = I.argv("/h")
        self.assertEqual(a[1:], [str(BIN / "squad-inbox"), "--home", "/h", "list", "--json", "--no-write"])
        self.assertTrue(set(a).isdisjoint({"answer", "delivered", "read", "park"}))

    def test_T05_TA3_real_samples_and_version(self):
        full = json.loads((SAMPLES / "list-open.json").read_text(encoding="utf-8"))
        rows, _ = I.rows_of("/nowhere", "q", full, NOW.timestamp())
        self.assertEqual([r["id"] for r in rows], ["E1"])  # E2 is done in the sample
        empty = json.loads((SAMPLES / "list-empty.json").read_text(encoding="utf-8"))
        self.assertEqual(I.rows_of("/nowhere", "q", empty, 0)[0], [])
        run = subprocess.CompletedProcess([], 0, stdout=json.dumps({"version": 2, "items": []}), stderr="")
        with unittest.mock.patch.object(I.subprocess, "run", return_value=run):
            snap, why = I.call("/h")
        self.assertIsNone(snap)
        self.assertIn("version", why)

    def test_T05_TA1_broken_cli_gives_unknown_inbox(self):
        bad = subprocess.CompletedProcess([], 2, stdout="", stderr="boom")
        with unittest.mock.patch.object(I.subprocess, "run", return_value=bad):
            r = I.read(self.sel("scope", "questions"))
        self.assertIn("inbox", r["unknown"])
        self.assertNotEqual(r["data"]["rows"], None)


if __name__ == "__main__":
    unittest.main()
