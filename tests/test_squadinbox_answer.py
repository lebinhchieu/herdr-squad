"""PI-02: squad-inbox answer, withdraw, delivered, the Answer-cell writer, options_raw."""
import json
import os
import pty
import stat
import subprocess
import sys
import threading
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock

from test_squadinbox import Base, CLI, ROOT, env, listing, by_id, load_board, run, digest

sys.path.insert(0, str(ROOT / "bin"))
import squadinbox  # noqa: E402

BREAKS = ["\r\n", "\n", "\r", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", " ", " "]


def events(home, ev=None):
    p = Path(home) / "inbox.jsonl"
    out = [json.loads(l) for l in p.read_text().split("\n") if l.strip()] if p.exists() else []
    return [e for e in out if ev is None or e["ev"] == ev]


def table(home):
    return [(len(r), tuple(r)) for r in load_board().read_first_table(Path(home) / "escalations.md")]


def lines_except(home, marker=None):
    return (Path(home) / "escalations.md").read_bytes().split(b"\n")


class AnswerTest(Base):
    def test_option_and_note(self):  # AC1
        r = run(self.home, "answer", "E8", "--option", "b", "--note", "x", "--source", "pane")
        self.assertEqual(r.returncode, 0, r.stderr)
        ev = events(self.home, "answer")[-1]
        self.assertEqual((ev["id"], ev["option"], ev["note"], ev["text"], ev["source"]), ("E8", "b", "x", "(b) no\nx", "pane"))
        it = by_id(listing(self.home))["E8"]
        self.assertEqual((it["state"], it["answer"]["text"]), ("answered-waiting", "(b) no\nx"))
        row = [r for r in load_board().read_first_table(self.home / "escalations.md") if r.get("question", "").startswith("Ship")][0]
        self.assertEqual(row["answer"], "(b) no<br>x")

    def test_option_without_note(self):
        run(self.home, "answer", "E8", "--option", "a", "--source", "pane")
        ev = events(self.home, "answer")[-1]
        self.assertEqual((ev["text"], ev["note"]), ("(a) yes", None))

    def test_free_text_and_bad_option(self):  # AC2
        r = run(self.home, "answer", "E18", "--text", "just do it", "--source", "pane")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(by_id(listing(self.home))["E18"]["answer"]["text"], "just do it")
        before = digest(self.home)
        for args in (("E19", "--option", "a"), ("E8", "--option", "z"), ("E8", "--option", "")):
            r = run(self.home, "answer", *args, "--note", "n", "--source", "pane")
            self.assertEqual(r.returncode, 2, (args, r.stderr))
        self.assertEqual(digest(self.home), before)

    def test_empty_answers(self):  # AC3
        before = digest(self.home)
        for extra in (["--text", ""], ["--text", "  \n\t "], []):
            r = run(self.home, "answer", "E8", *extra, "--source", "pane")
            self.assertEqual(r.returncode, 2, (extra, r.stderr))
        r = run(self.home, "answer", "E8", "--source", "pane", stdin="  \n")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(digest(self.home), before)
        self.assertEqual(by_id(listing(self.home))["E8"]["state"], "open")

    def test_round_trip(self):  # AC4, AC15, AC16
        texts = ["line one\nline two\r\nthree", "a | b \\| c", "`code` **bold** \"q\" 'q'\ttab", "<br> and <br/>",
                 "emoji 🎉 ünï 日本語", "ends with \\", "ends with \\\\", "ends with \\|", "ends with |", "a|"] + ["x%sy" % b for b in BREAKS]
        for i, t in enumerate(texts):
            h = self.home / ("h%d" % i)
            os.mkdir(h)
            for n in ("escalations.md", "inbox.jsonl"):
                (h / n).write_bytes((self.home / n).read_bytes())
            before = (h / "escalations.md").read_bytes()
            r = run(h, "answer", "E18", "--source", "pane", stdin=t)
            self.assertEqual(r.returncode, 0, (t, r.stderr))
            self.assertEqual(events(h, "answer")[-1]["text"], t)
            self.assertEqual(by_id(listing(h))["E18"]["answer"]["text"], t)
            after = (h / "escalations.md").read_bytes()
            old, new = before.split(b"\n"), after.split(b"\n")
            self.assertEqual(len(old), len(new), repr(t))
            self.assertEqual([i for i, (a, b) in enumerate(zip(old, new)) if a != b].__len__(), 1, repr(t))
            rows = load_board().read_first_table(h / "escalations.md")
            self.assertTrue(all(len(r) == 7 for r in rows if r.get("question")), repr(t))

    def test_second_answer_and_withdraw_race_losers(self):  # AC5
        self.base_answers = len(events(self.home, "answer"))
        run(self.home, "answer", "E8", "--option", "a", "--source", "pane")
        r = run(self.home, "answer", "E8", "--option", "b", "--source", "pane")
        self.assertEqual(r.returncode, 3)
        self.assertIn("answered at", r.stderr)
        self.assertEqual(len(events(self.home, "answer")), self.base_answers + 1)
        r = run(self.home, "withdraw", "E8", "--reason", "late")
        self.assertEqual(r.returncode, 3)
        run(self.home, "withdraw", "E18", "--reason", "gone")
        r = run(self.home, "answer", "E18", "--text", "x", "--source", "pane")
        self.assertEqual((r.returncode, "withdrawn" in r.stderr), (3, True))
        self.assertEqual(by_id(listing(self.home))["E8"]["answer"]["text"], "(a) yes")

    def test_hand_answer_and_removed(self):  # AC18
        r = run(self.home, "answer", "E7", "--option", "a", "--source", "pane")
        self.assertEqual(r.returncode, 3)
        self.assertIn("in the file", r.stderr)
        r = run(self.home, "answer", "E16", "--option", "a", "--source", "pane")  # row gone while open
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("not written", r.stderr)
        self.assertEqual(by_id(listing(self.home))["E16"]["state"], "answered-waiting")

    def test_chat_source(self):  # AC10
        r = run(self.home, "answer", "E8", "--option", "b", "--source", "chat")
        self.assertEqual(r.returncode, 0, r.stderr)
        it = by_id(listing(self.home))["E8"]
        self.assertEqual((it["state"], it["done"]["kind"], it["answer"]["source"], it["answer"]["delivered_ts"] is not None),
                         ("done", "answered", "chat", True))
        self.assertEqual(run(self.home, "answer", "E8", "--option", "a", "--source", "chat").returncode, 3)

    def test_ids_and_roles(self):  # AC11 guard, AC13
        before = digest(self.home)
        for cmd in (["answer", "E8", "--option", "a", "--source", "pane"], ["withdraw", "E8", "--reason", "r"],
                    ["delivered", "E11", "--session", "s"]):
            self.assertEqual(run(self.home, *cmd, role=None).returncode, 2, cmd)
            self.assertEqual(run(self.home, *cmd, role="dev").returncode, 2, cmd)
        self.assertEqual(digest(self.home), before)
        self.assertEqual(run(self.home, "answer", "R1", "--text", "x", "--source", "pane").returncode, 2)
        self.assertEqual(run(self.home, "delivered", "R1", "--session", "s").returncode, 2)
        self.assertEqual(run(self.home, "answer", "E99", "--text", "x", "--source", "pane").returncode, 2)
        self.assertEqual(run(self.home, "answer", "E8", "--text", "x", "--source", "radio").returncode, 2)

    def test_stdin_meaning(self):  # AC19, AC20
        r = run(self.home, "answer", "E8", "--option", "b", "--source", "pane", stdin="the note\nsecond")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(events(self.home, "answer")[-1]["note"], "the note\nsecond")
        r = run(self.home, "answer", "E18", "--option", "a", "--source", "pane", stdin="")
        self.assertEqual(r.returncode, 2)  # no options on E18
        r = run(self.home, "answer", "E19", "--note", "n", "--source", "pane", stdin="more")
        self.assertEqual(r.returncode, 2)
        r = run(self.home, "answer", "E18", "--text", "t", "--source", "pane", stdin="more")
        self.assertEqual(r.returncode, 2)
        r = run(self.home, "answer", "E8", "--text", "t", "--option", "a", "--source", "pane")
        self.assertEqual(r.returncode, 2)

    def test_option_with_empty_stdin_is_valid(self):  # AC20
        r = run(self.home, "answer", "E8", "--option", "c", "--source", "pane", stdin="")
        self.assertEqual(r.returncode, 0, r.stderr)
        ev = events(self.home, "answer")[-1]
        self.assertEqual((ev["text"], ev["note"]), ("(c) later", None))

    def test_never_hangs(self):  # AC19
        cmd = [sys.executable, "-B", CLI, "--home", str(self.home), "answer", "E8", "--source", "pane"]
        r = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env(), timeout=20)
        self.assertEqual(r.returncode, 2)
        rd, wr = os.pipe()
        os.close(wr)
        r = subprocess.run(cmd, stdin=rd, capture_output=True, text=True, env=env(), timeout=20)
        os.close(rd)
        self.assertEqual(r.returncode, 2)
        master, slave = pty.openpty()
        r = subprocess.run(cmd, stdin=slave, capture_output=True, text=True, env=env(), timeout=20)
        os.close(master)
        os.close(slave)
        self.assertEqual(r.returncode, 2)
        # an open pipe nobody writes to, with --text given: not a wait
        rd, wr = os.pipe()
        r = subprocess.run(cmd + ["--text", "x"], stdin=rd, capture_output=True, text=True, env=env(), timeout=20)
        os.close(rd)
        os.close(wr)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_no_temp_left_and_mode_kept(self):  # AC12
        path = self.home / "escalations.md"
        os.chmod(path, 0o640)
        run(self.home, "answer", "E8", "--option", "a", "--source", "pane")
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)
        self.assertEqual([p.name for p in self.home.iterdir() if p.name.startswith(".escalations-")], [])
        with mock.patch.object(squadinbox.os, "replace", side_effect=OSError("boom")):
            with self.assertRaises(OSError):
                squadinbox.atomic_write(str(path), "x")
        self.assertEqual([p.name for p in self.home.iterdir() if p.name.startswith(".escalations-")], [])


class CellFailureTest(Base):
    def call(self, *argv):
        from importlib import machinery  # the CLI parser lives in bin/squad-inbox
        import importlib.util
        loader = machinery.SourceFileLoader("squad_inbox_cli", str(ROOT / "bin" / "squad-inbox"))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        import io
        stdin = io.TextIOWrapper(io.BytesIO(b""))
        with mock.patch.dict(os.environ, {"SQUAD_ROLE": "manager", "SQUAD_INBOX_NOW": "2026-10-15T10:00:00Z"}), \
                mock.patch.object(sys, "stdin", stdin):
            return mod.main(["--home", str(self.home)] + list(argv))

    def test_cell_write_raises_then_list_repairs(self):  # AC11 (round 1)
        with mock.patch.object(squadinbox, "set_answer_cell", side_effect=OSError("read-only")):
            self.assertEqual(self.call("answer", "E8", "--option", "a", "--source", "pane"), 0)
        self.assertEqual(len(events(self.home, "answer")), 6)  # the fixture's five and ours
        self.assertEqual(by_id(listing(self.home, "--no-write"))["E8"]["state"], "answered-waiting")
        it = by_id(listing(self.home))["E8"]
        self.assertEqual(it["state"], "answered-waiting")  # never answered-file
        row = [r for r in load_board().read_first_table(self.home / "escalations.md") if r.get("question", "").startswith("Ship")][0]
        self.assertEqual(row["answer"], "(a) yes")

    def test_withdraw_cell_failure_is_repaired(self):
        with mock.patch.object(squadinbox, "set_answer_cell", side_effect=OSError("read-only")):
            self.assertEqual(self.call("withdraw", "E8", "--reason", "nope"), 0)
        self.assertEqual(by_id(listing(self.home))["E8"]["done"]["kind"], "withdrawn")
        row = [r for r in load_board().read_first_table(self.home / "escalations.md") if r.get("question", "").startswith("Ship")][0]
        self.assertEqual(row["answer"], "withdrawn: nope")

    def test_crash_between_event_and_cell(self):
        class Boom(BaseException):
            pass
        with mock.patch.object(squadinbox, "set_answer_cell", side_effect=Boom()):
            with self.assertRaises(Boom):
                self.call("answer", "E8", "--option", "b", "--source", "pane")
        self.assertEqual(by_id(listing(self.home))["E8"]["state"], "answered-waiting")

    def test_unwritable_cases_warn_and_record(self):  # AC15
        path = self.home / "escalations.md"
        good = path.read_bytes()
        for name, setup in (
            ("symlink", lambda: (path.rename(self.home / "real.md"), path.symlink_to("real.md"))),
            ("no answer header", lambda: path.write_bytes(good.replace(b"| Answer |", b"| Reply  |"))),
        ):
            with self.subTest(name):
                setup()
                r = run(self.home, "answer", "E8", "--option", "a", "--source", "pane")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("not written", r.stderr)
                self.assertEqual(by_id(listing(self.home, "--no-write"))["E8"]["state"], "answered-waiting")
                self.assertIn("cell-not-written", by_id(listing(self.home))["E8"]["flags"])
                if name == "symlink":
                    self.assertTrue(path.is_symlink())
                    self.assertEqual((self.home / "real.md").read_bytes(), good)
                    path.unlink()
                    (self.home / "real.md").rename(path)
                (self.home / "inbox.jsonl").write_text("".join(l + "\n" for l in (self.home / "inbox.jsonl").read_text().split("\n")
                                                              if '"answer", "id": "E8"' not in l and '"ev": "answer", "id": "E8"' not in l))

    def test_short_row_is_padded_and_answered(self):
        path = self.home / "escalations.md"
        path.write_text(path.read_text().rstrip("\n") + "\n| 9 | 2026-10-15 | Short row |\n")
        item = [i for i in listing(self.home)["items"] if i["title"] == "Short row"][0]
        r = run(self.home, "answer", item["id"], "--text", "x | y", "--source", "pane")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr, "")
        row = [r for r in load_board().read_first_table(path) if r.get("question") == "Short row"][0]
        self.assertEqual(row["answer"], "x | y")
        self.assertEqual(by_id(listing(self.home))[item["id"]]["flags"], [])

    def test_unwritable_home_is_one_clean_line(self):
        if os.geteuid() == 0:
            self.skipTest("root ignores modes")
        os.chmod(self.home, 0o555)
        try:
            r = run(self.home, "answer", "E8", "--option", "a", "--source", "pane")
        finally:
            os.chmod(self.home, 0o755)
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(len(r.stderr.strip().splitlines()), 1)
        self.assertIn("inbox.jsonl.lock", r.stderr)

    def test_duplicate_key_names_both_rows(self):
        path = self.home / "escalations.md"
        txt = path.read_text()
        row = [l for l in txt.splitlines() if "Ship the badge" in l][0]
        path.write_text(txt + row + "\n")
        r = run(self.home, "answer", "E8", "--option", "a", "--source", "pane")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stderr, r"lines \d+, \d+")


class SeparatorTailTest(Base):
    def test_row_ending_in_each_separator(self):  # QAW mutant on set_answer_cell
        for ch in BREAKS:
            for last in (True, False):
                h = self.home / ("s%r%s" % (ch, last))
                os.makedirs(h)
                row = "| 5 | 2026-10-14 | Q? | (a) x; (b) y | | | |"
                head = "| # | Date | Question | Options | Manager's recommendation | Blocks | Answer |\n|---|---|---|---|---|---|---|\n"
                tail = "" if last else "| 4 | 2026-10-13 | Other | | | | |\n"
                (h / "escalations.md").write_bytes((head + row + ch + tail).encode())
                r = run(h, "answer", "E5", "--option", "a", "--source", "pane")
                self.assertEqual(r.returncode, 0, (ch, r.stderr))
                self.assertEqual(r.stderr, "", (ch, r.stderr))
                want = head + row[:-1] + "(a) x |" + ch + tail
                self.assertEqual((h / "escalations.md").read_bytes().decode(), want, repr(ch))

    def test_trailing_spaces_after_last_pipe(self):
        h = self.home / "sp"
        os.makedirs(h)
        head = "| # | Date | Question | Answer |\n|---|---|---|---|\n"
        (h / "escalations.md").write_bytes((head + "| 5 | 2026-10-14 | Q? |  |  \t\n").encode())
        run(h, "answer", "E5", "--text", "t", "--source", "pane")
        self.assertEqual((h / "escalations.md").read_bytes().decode(), head + "| 5 | 2026-10-14 | Q? | t |  \t\n")


class FileShapeTest(Base):
    def one(self, content, answer_id="E5"):
        self.n = getattr(self, "n", 0) + 1
        h = self.home / ("shape%d" % self.n)
        os.makedirs(h)
        (h / "escalations.md").write_bytes(content)
        r = run(h, "answer", answer_id, "--text", "ok | x", "--source", "pane")
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        return (h / "escalations.md").read_bytes()

    def test_shapes(self):  # AC15
        head = "| # | Date | Question | Answer | Blocks |\n|---|---|---|---|---|\n"
        row = "| 5 | 2026-10-14 | Q? |  | X |"
        for eol in ("\n", "\r\n"):
            h = head.replace("\n", eol)
            self.assertEqual(self.one((h + row + eol).encode()), (h + row.replace("|  |", "| ok \\| x |") + eol).encode())
            self.assertEqual(self.one((h + row).encode()), (h + row.replace("|  |", "| ok \\| x |")).encode())
        pre = b"# Notes \xff\xfe bad bytes\n\n"
        self.assertEqual(self.one(pre + (head + row + "\n").encode()),
                         pre + (head + row.replace("|  |", "| ok \\| x |") + "\n").encode())

    def test_stdin_cap(self):
        cap = squadinbox.MAX_BODY
        before = (self.home / "escalations.md").read_bytes()
        r = run(self.home, "answer", "E8", "--source", "pane", stdin="x" * (cap + 1))
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertEqual((self.home / "escalations.md").read_bytes(), before)
        self.assertEqual(len(events(self.home, "answer")), 5)
        r = run(self.home, "answer", "E8", "--source", "pane", stdin="x" * cap)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(events(self.home, "answer")), 6)

    def test_short_row_is_padded(self):
        for name, head, short, want in (
            ("last", "| # | Date | Question | Options | Answer |\n|---|---|---|---|---|\n", "| 5 | 2026-10-14 | Q? |", "| 5 | 2026-10-14 | Q? | | t |"),
            ("middle", "| # | Date | Question | Answer | Blocks |\n|---|---|---|---|---|\n", "| 5 | 2026-10-14 | Q? |", "| 5 | 2026-10-14 | Q? | t | |"),
        ):
            with self.subTest(name):
                h = self.home / name
                os.makedirs(h)
                tail = "\n| 6 | 2026-10-14 | Other | | |\n" if name == "middle" else "\n"
                (h / "escalations.md").write_bytes(("# T\n\n" + head + short + tail).encode())
                r = run(h, "answer", "E5", "--text", "t", "--source", "pane")
                self.assertEqual((r.returncode, r.stderr), (0, ""))
                got = (h / "escalations.md").read_text()
                self.assertTrue(got.startswith("# T\n\n" + head), got)
                rows = [l for l in got.splitlines() if l.startswith("| 5 ")]
                self.assertEqual([c.strip() for c in rows[0].strip("|").split("|")], [c.strip() for c in want.strip("|").split("|")])
                self.assertEqual(got.count("\n"), ("# T\n\n" + head + short + tail).count("\n"))
                self.assertEqual(by_id(listing(h))["E5"]["flags"], [])

    def test_invalid_utf8_row_flags_cell_not_written(self):
        h = self.home / "bad"
        os.makedirs(h)
        head = "| # | Date | Question | Options | Answer |\n|---|---|---|---|---|\n"
        (h / "escalations.md").write_bytes((head + "| 5 | 2026-10-14 | Q").encode() + b"\xff? | | |\n")
        r = run(h, "answer", "E5", "--text", "t", "--source", "pane")
        self.assertEqual(r.returncode, 0)
        self.assertIn("not written", r.stderr)
        self.assertEqual(by_id(listing(h, "--no-write"))["E5"]["flags"], ["cell-not-written"])


class WithdrawDeliveredTest(Base):
    def test_withdraw(self):  # AC8
        self.assertEqual(run(self.home, "withdraw", "E8", "--reason", "").returncode, 2)
        self.assertEqual(run(self.home, "withdraw", "E8", "--reason", "   ").returncode, 2)
        self.assertEqual(run(self.home, "withdraw", "E8", "--reason", "not needed").returncode, 0)
        it = by_id(listing(self.home))["E8"]
        self.assertEqual((it["state"], it["done"]["kind"], it["done"]["reason"]), ("done", "withdrawn", "not needed"))
        row = [r for r in load_board().read_first_table(self.home / "escalations.md") if r.get("question", "").startswith("Ship")][0]
        self.assertEqual(row["answer"], "withdrawn: not needed")
        before = (self.home / "escalations.md").read_bytes()
        r = run(self.home, "withdraw", "R1", "--reason", "old")
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        self.assertEqual((self.home / "escalations.md").read_bytes(), before)
        self.assertEqual(by_id(listing(self.home))["R1"]["done"]["kind"], "withdrawn")
        self.assertEqual(run(self.home, "withdraw", "R1", "--reason", "again").returncode, 3)

    def test_delivered(self):  # AC9
        self.assertEqual(run(self.home, "delivered", "E8", "--session", "s").returncode, 3)  # no answer yet
        r = run(self.home, "delivered", "E11", "--session", "s9")
        self.assertEqual(r.returncode, 0, r.stderr)
        it = by_id(listing(self.home))["E11"]
        self.assertEqual((it["state"], it["done"]["kind"], it["answer"]["delivered_ts"]), ("done", "answered", "2026-10-15T10:00:00Z"))
        self.assertEqual(events(self.home, "delivered")[-1]["session"], "s9")
        r = run(self.home, "delivered", "E11", "--session", "s9", SQUAD_INBOX_NOW="2026-10-16T00:00:00Z")
        self.assertEqual(r.returncode, 3)
        self.assertEqual(by_id(listing(self.home))["E11"]["answer"]["delivered_ts"], "2026-10-15T10:00:00Z")


class RaceTest(Base):
    def race(self, home, cmds):
        gate = threading.Barrier(len(cmds))
        out = [None] * len(cmds)

        def go(i):
            gate.wait()
            out[i] = run(home, *cmds[i])
        ts = [threading.Thread(target=go, args=(i,)) for i in range(len(cmds))]
        [t.start() for t in ts]
        [t.join() for t in ts]
        return out

    def fresh(self, i, with_log):
        h = self.home / ("r%d%s" % (i, with_log))
        os.makedirs(h)
        (h / "escalations.md").write_bytes((self.home / "escalations.md").read_bytes())
        if with_log:
            (h / "inbox.jsonl").write_bytes((self.home / "inbox.jsonl").read_bytes())
        return h

    def cell(self, h):
        return [r for r in load_board().read_first_table(h / "escalations.md") if r.get("question", "").startswith("Ship")][0]["answer"]

    def test_ten_answers(self):  # AC6, AC17
        for i in range(20):
            h = self.fresh(i, i % 2 == 0)
            cmds = [("answer", "E8", "--option", "abc"[k % 3], "--note", "n%d" % k, "--source", "pane") for k in range(10)]
            codes = sorted(r.returncode for r in self.race(h, cmds))
            self.assertEqual(codes, [0] + [3] * 9, i)
            mine = [e for e in events(h, "answer") if e["id"] == "E8"]
            self.assertEqual(len(mine), 1, i)
            self.assertEqual(self.cell(h), mine[0]["text"].replace("\n", "<br>"), i)

    def test_answer_vs_withdraw(self):  # AC6, AC17
        for i in range(20):
            h = self.fresh(i, i % 2 == 0)
            codes = sorted(r.returncode for r in self.race(h, [("answer", "E8", "--option", "a", "--source", "pane"),
                                                              ("withdraw", "E8", "--reason", "w")]))
            self.assertEqual(codes, [0, 3], i)
            a = [e for e in events(h) if e["id"] == "E8" and e["ev"] in ("answer", "withdraw")]
            self.assertEqual(len(a), 1, i)
            self.assertEqual(self.cell(h), "(a) yes" if a[0]["ev"] == "answer" else "withdrawn: w", i)


class OptionsRawTest(Base):
    def test_options_raw(self):  # AC21
        items = by_id(listing(self.home))
        self.assertEqual(items["E6"]["options_raw"], "see (a) above")
        self.assertEqual(items["E6"]["options"], None)
        self.assertEqual(items["E19"]["options_raw"], "(b) x; (a) y")
        self.assertEqual(items["E8"]["options_raw"], None)
        self.assertIsNotNone(items["E8"]["options"])
        self.assertEqual(items["E18"]["options_raw"], None)  # empty cell
        self.assertEqual(items["R1"]["options_raw"], None)
        self.assertTrue(all("options_raw" in i for i in items.values()))
        self.assertEqual(items["E16"]["options_raw"], None)  # removed row: from the snapshot


if __name__ == "__main__":
    unittest.main()
