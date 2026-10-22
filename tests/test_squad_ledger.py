"""squad-ledger: per-task state from messages.jsonl; and the 3rd-return notice of squad-log-message."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"
LEDGER = BIN / "squad-ledger"
HOOK = BIN / "squad-log-message"


def rec(typ, frm, to, text, ts="2026-10-22T00:00:00.000Z"):
    task = text.split()[1].rstrip(":") if len(text.split()) > 1 else None
    return {"ts": ts, "from": frm, "to": to, "type": typ, "task": task, "text": text}


def hi(task, sha, frm="dev"):
    return rec("HANDIN", frm, "qa", "HANDIN %s: branch squad/x/%s, commit %s, run it" % (task, frm, sha))


FIXTURE = [
    hi("03", "aaaaaaa"),
    rec("FAIL", "qaw", "dev", "FAIL 03: finding 1"),
    rec("FAIL", "qab", "dev", "FAIL 03: finding 2"),
    hi("03", "bbbbbbb"),
    rec("PASS", "qaw", "dev", "PASS 03"),
    rec("PASS", "qab", "dev", "PASS 03"),
    hi("04", "1111111"), rec("FAIL", "qaw", "dev", "FAIL 04: a"),
    hi("04", "2222222"), rec("FAIL", "qaw", "dev", "FAIL 04: b"),
    hi("04", "3333333"), rec("FAIL", "qab", "dev", "FAIL 04: c"),
    rec("BLOCKED", "dev", "tl", "BLOCKED 04: 3 returns"),
    rec("ASK", "dev", "tech", "ASK 04: q1"), rec("ANSWER", "tech", "dev", "ANSWER 04: a1"),
    rec("ASK", "dev", "tech", "ASK 04: q2"),
]


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.write(FIXTURE)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, recs):
        (self.home / "messages.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")

    def ledger(self, *args):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run([sys.executable, str(LEDGER), "--home", str(self.home), *args], text=True,
                              encoding="utf-8", env=env, capture_output=True, timeout=10)

    def test_json_matches_expected(self):
        r = self.ledger("--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = {x["task"]: x for x in json.loads(r.stdout)}
        self.assertEqual(rows["03"]["sha"], "bbbbbbb")
        self.assertEqual(rows["03"]["branch"], "squad/x/dev")
        self.assertEqual(rows["03"]["verdicts"], {"qaw": "PASS", "qab": "PASS"})
        self.assertEqual((rows["03"]["returns"], rows["03"]["fail_messages"]), (1, 2))
        self.assertEqual(rows["04"]["returns"], 3)
        self.assertEqual(rows["04"]["verdicts"], {"qab": "FAIL"})
        self.assertEqual(rows["04"]["blocked"], ["BLOCKED 04: 3 returns"])
        self.assertEqual((rows["03"]["ask_rounds"], rows["04"]["ask_rounds"]), (0, 2))

    def test_task_filter_and_table(self):
        r = self.ledger("--task", "4")
        lines = r.stdout.splitlines()
        self.assertEqual(len(lines), 2)
        self.assertRegex(lines[1], r"^04\s+3333333\s+squad/x/dev\s+qab FAIL\s+3\s+1\s+2$")
        self.assertEqual(len(json.loads(self.ledger("--task", "03", "--json").stdout)), 1)

    def test_decision_resets_ask_rounds_and_closes_blocked(self):
        self.write(FIXTURE + [rec("DECISION", "tl", "dev", "DECISION 04: go")])
        row = json.loads(self.ledger("--task", "04", "--json").stdout)[0]
        self.assertEqual((row["ask_rounds"], row["blocked"]), (0, None))

    def test_prefix_shas_anonymous_fail_and_task_key(self):
        self.write([rec("FAIL", "qaw", "dev", "FAIL 7: no handin yet"),
                    hi("03", "abcdef1234567"), rec("FAIL", "qaw", "dev", "FAIL 3: on abcdef1 long"),
                    rec("FAIL", "qab", "dev", "FAIL 03: sha abcdef1234567890 again")])
        rows = {r["task"]: r for r in json.loads(self.ledger("--json").stdout)}
        self.assertEqual((rows["7"]["returns"], rows["7"]["sha"], rows["7"]["verdicts"]), (1, None, None))
        self.assertEqual((rows["03"]["returns"], rows["03"]["fail_messages"]), (1, 2))
        self.assertEqual(len(rows), 2)

    def test_every_row_has_every_key_null_when_empty(self):
        self.write([rec("ASK", "dev", "tech", "ASK 9: q")])
        [row] = json.loads(self.ledger("--json").stdout)
        self.assertEqual(sorted(row), sorted(["task", "sha", "branch", "handin_from", "verdicts", "returns",
                                              "fail_messages", "blocked", "ask_rounds"]))
        self.assertEqual((row["sha"], row["branch"], row["verdicts"], row["blocked"], row["returns"]),
                         (None, None, None, None, 0))

    def test_live_log_read_only(self):
        live = os.environ.get("SCOPE_DIR")
        if not live or not (Path(live) / "messages.jsonl").is_file():
            self.skipTest("no live scope log")
        before = (Path(live) / "messages.jsonl").stat().st_mtime_ns
        r = subprocess.run([sys.executable, str(LEDGER), "--home", live, "--json"], capture_output=True,
                           text=True, encoding="utf-8", timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        for row in json.loads(r.stdout):
            self.assertEqual(len(row), 9)
        self.assertEqual((Path(live) / "messages.jsonl").stat().st_mtime_ns, before)

    def test_evidence_handin_keeps_passed_sha_and_verdicts(self):
        self.write(FIXTURE + [rec("HANDIN", "dev", "tech", "HANDIN 03: evidence sha ccccccc")])
        row = [r for r in json.loads(self.ledger("--json").stdout) if r["task"] == "03"][0]
        self.assertEqual(row["sha"], "bbbbbbb")
        self.assertEqual(row["verdicts"], {"qaw": "PASS", "qab": "PASS"})

    def test_missing_log_and_bad_args(self):
        (self.home / "messages.jsonl").unlink()
        self.assertIn("no tasks", self.ledger().stdout)
        self.assertEqual(self.ledger("--nope").returncode, 2)


class NoticeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.squad = Path(self.tmp.name) / "squad"
        (self.squad / "iterations").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def send(self, text, frm, to="dev"):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        env.update(SQUAD_NAME=frm, SQUAD_DIR=str(self.squad))
        p = {"tool_name": "SendMessage", "tool_input": {"to": to, "message": text},
             "tool_response": {"success": True, "msg_id": "m"}}
        r = subprocess.run([str(HOOK)], input=json.dumps(p), text=True, encoding="utf-8", env=env,
                           capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"] if r.stdout.strip() else None

    def test_fires_once_on_first_fail_of_third_sha_only(self):
        got = []
        for n, sha in enumerate(["aaaaaaa", "bbbbbbb", "ccccccc", "ddddddd"], 1):
            self.send("HANDIN 05: branch b, commit %s" % sha, "dev", "qaw")
            got.append(self.send("FAIL 05: x", "qaw"))
            got.append(self.send("FAIL 05: y", "qab"))  # 2nd checker, same sha
        self.assertEqual([i for i, g in enumerate(got) if g], [4])
        self.assertEqual(got[4], "task 05 has 3 returns: also send `BLOCKED 05: 3 returns` to Team Lead [LC-7b]; tell the Developer to consult the advisor before the next HANDIN and note it in the task file [LC-24]")

    def test_garbage_lines_in_log_do_not_stop_notice(self):
        (self.squad / "messages.jsonl").write_text("garbage line\n\n3\n[1]\n", encoding="utf-8")
        got = None
        for sha in ["aaaaaaa", "bbbbbbb", "ccccccc"]:
            self.send("HANDIN 05: commit %s" % sha, "dev", "qaw")
            got = self.send("FAIL 05: x", "qaw")
        self.assertIn("3 returns", got)

    def test_evidence_handin_is_not_a_new_sha(self):
        for sha in ["aaaaaaa", "bbbbbbb"]:
            self.send("HANDIN 05: commit %s" % sha, "dev", "qaw")
            self.send("FAIL 05: x", "qaw")
        self.send("HANDIN 05: commit ccccccc", "dev", "qaw")
        self.send("PASS 05", "qaw")
        self.send("HANDIN 05: evidence sha ddddddd", "dev", "tech")
        # a FAIL now lands on ccccccc (current sha), not on the evidence sha
        self.assertIn("3 returns", self.send("FAIL 05: late", "qab"))

    def test_pass_does_not_reset_and_size_s_names_manager(self):
        (self.squad / "scope.md").write_text("size: S (one task)\n", encoding="utf-8")
        got = None
        for sha in ["aaaaaaa", "bbbbbbb", "ccccccc"]:
            self.send("HANDIN 5: commit %s" % sha, "dev", "tech")
            self.send("PASS 5", "tech")
            got = self.send("FAIL 5: x", "tech")
        self.assertIn("to Manager [LC-7a]", got)

    def test_two_fails_and_other_tasks_give_no_notice(self):
        for t, sha in (("05", "aaaaaaa"), ("06", "bbbbbbb"), ("05", "ccccccc"), ("06", "ddddddd")):
            self.send("HANDIN %s: commit %s" % (t, sha), "dev", "qaw")
            self.assertIsNone(self.send("FAIL %s: x" % t, "qaw"))

    def test_prefix_sha_counts_once(self):
        self.send("HANDIN 05: commit aaaaaaa1234", "dev", "qaw")
        self.assertIsNone(self.send("FAIL 05: on aaaaaaa", "qaw"))
        self.send("HANDIN 5: commit bbbbbbb", "dev", "qaw")
        self.assertIsNone(self.send("FAIL 5: x", "qaw"))
        self.send("HANDIN 05: commit ccccccc", "dev", "qaw")
        self.assertIn("3 returns", self.send("FAIL 05: x", "qaw"))
        self.assertIsNone(self.send("FAIL 05: aaaaaaa1234 again", "qab"))  # old sha again: not new

    def test_simultaneous_fails_on_third_sha_give_one_notice(self):
        for sha in ("aaaaaaa", "bbbbbbb"):
            self.send("HANDIN 05: commit %s" % sha, "dev", "qaw")
            self.send("FAIL 05: x", "qaw")
        self.send("HANDIN 05: commit ccccccc", "dev", "qaw")
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(2) as ex:
            out = list(ex.map(lambda f: self.send("FAIL 05: x", f), ["qaw", "qab"]))
        self.assertEqual(len([o for o in out if o]), 1)

    def test_forced_failures_exit_0_without_notice(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD_", "SCOPE_DIR", "GOAL_DIR"))}
        env.update(SQUAD_NAME="qaw", SQUAD_DIR=str(self.squad))
        p = json.dumps({"tool_name": "SendMessage", "tool_input": {"to": "d", "message": "FAIL 05: x"},
                        "tool_response": {"success": True}})
        # unreadable log dir, bad payload, no jq on PATH
        bindir = Path(self.tmp.name) / "bin"
        bindir.mkdir()
        for cmd in ("bash", "sed", "head", "date", "flock", "basename", "cat"):
            src = subprocess.run(["which", cmd], capture_output=True, text=True).stdout.strip()
            if src:
                (bindir / cmd).symlink_to(src)
        for raw, e in ((p, dict(env, PATH=str(bindir))), ("not json", env)):
            r = subprocess.run([str(HOOK)], input=raw, text=True, env=e, capture_output=True, timeout=10)
            self.assertEqual((r.returncode, r.stdout), (0, ""))
        (self.squad / "messages.jsonl").mkdir()  # log path is a directory: cannot append or read
        r = subprocess.run([str(HOOK)], input=p, text=True, env=env, capture_output=True, timeout=10)
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_fail_without_task_gives_no_notice(self):
        self.assertIsNone(self.send("FAIL: nothing", "qaw"))


if __name__ == "__main__":
    unittest.main()
