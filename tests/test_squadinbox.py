"""PI-01: squad-inbox add / list / read, the escalations projection, and the escalations.md table reader against its golden file."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = str(ROOT / "bin" / "squad-inbox")
FIX = ROOT / "tests" / "fixtures" / "inbox"
NOW = "2026-10-15T10:00:00Z"
AGENT_ENV = ("SQUAD_DIR", "SCOPE_DIR", "GOAL_DIR", "SQUAD_NAME", "SQUAD_ROLE", "SQUAD_SCOPE", "SQUAD_INBOX_NOW")
try:
    import pty
except ImportError:  # pty needs termios, which Windows lacks
    pty = None
HAVE_PTY = pty is not None


def _can_symlink():
    with tempfile.TemporaryDirectory() as d:
        try:
            os.symlink(os.path.join(d, "t"), os.path.join(d, "l"))
        except (OSError, NotImplementedError):  # WinError 1314: creating a symlink needs a privilege
            return False
    return True


CAN_SYMLINK = _can_symlink()
KEYS = {"id", "kind", "state", "title", "body", "options", "options_raw", "recommendation", "blocks", "created", "created_precision", "answer", "done", "flags"}


def env(role="manager", **extra):
    e = {k: v for k, v in os.environ.items() if k not in AGENT_ENV}
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    e["SQUAD_INBOX_NOW"] = NOW
    if role:
        e["SQUAD_ROLE"] = role
    e.update(extra)
    return e


def run(home, *args, stdin="", role="manager", **extra):
    return subprocess.run([sys.executable, "-B", CLI, "--home", str(home)] + [a.encode("utf-8") if isinstance(a, str) else a for a in args], input=stdin, text=True,
                          capture_output=True, env=env(role, **extra), encoding="utf-8")


def listing(home, *args):
    r = run(home, "list", "--json", *args)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def by_id(snap):
    return {i["id"]: i for i in snap["items"]}


def digest(folder):
    """File hash and mtime of everything but the lock file, which a refused write may leave behind."""
    return {p.name: (hashlib.sha1(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            for p in sorted(Path(folder).iterdir()) if not p.name.endswith(".lock")}


def rows_of(path):
    """The rows of the escalations.md table at `path`, as dicts keyed by the lower-cased header; [] without a header."""
    sys.dont_write_bytecode = True
    if str(ROOT / "bin") not in sys.path:
        sys.path.insert(0, str(ROOT / "bin"))
    import squadinbox
    header, rows = squadinbox.first_table(squadinbox.read_text(path))
    mine = [dict(zip(header, cells)) for _, cells in rows] if header else []
    return mine


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = Path(self.tmp) / "home"
        shutil.copytree(FIX / "home", self.home)

    def empty_home(self):
        h = Path(self.tmp) / "empty"
        h.mkdir()
        return h


class ProjectionTest(Base):
    def test_real_rows_and_odd_rows(self):  # AC1, AC10, AC11
        snap = listing(self.home)
        items = by_id(snap)
        for n in ("E1", "E2", "E3"):  # the real rows, answered by hand
            self.assertEqual(items[n]["state"], "done")
            self.assertEqual(items[n]["done"]["kind"], "answered-file")
            self.assertIn("answer-by-hand", items[n]["flags"])
        self.assertIn("goal.md sets size S", items["E1"]["body"])  # body is the whole cell
        self.assertIsNone(items["E1"]["options"])  # real options cells are `A) ... B) ...` prose
        self.assertEqual(items["E8"]["state"], "open")
        self.assertEqual(items["E8"]["title"], "Ship the badge?")
        self.assertEqual(items["E8"]["body"], "Ship the badge?<br>It touches CART-04.")  # the raw cell
        self.assertEqual([o["key"] for o in items["E8"]["options"]], ["a", "b", "c"])
        self.assertEqual(items["E6"]["title"], "Use a | b or c?")  # `\|` unescaped
        self.assertEqual(items["E18"]["title"], "A row with no number")  # no `#`: above the max of the file and the log
        self.assertEqual(items["E19"]["title"], "Same number as the badge row")  # duplicate `#`
        self.assertEqual(items["E8"]["title"], "Ship the badge?")
        self.assertEqual(snap["errors"], [{"file": "escalations.md", "row": 17, "message": "row has 2 cells, header has 7"}])
        self.assertFalse(any(i["title"] == "" for i in snap["items"]))  # the blank row is skipped

    def test_contract_shape(self):  # AC6
        snap = listing(self.home)
        self.assertEqual(snap["version"], 1)
        self.assertEqual(set(snap), {"version", "home", "now", "counts", "items", "errors"})
        self.assertEqual(snap["now"], NOW)
        for it in snap["items"]:
            self.assertEqual(set(it), KEYS, it["id"])
        r1 = by_id(snap)["R1"]
        self.assertEqual((r1["options"], r1["answer"], r1["done"], r1["recommendation"]), (None, None, None, None))
        self.assertEqual(snap["counts"], {"answer_open": 4, "read_open": 1, "waiting": 2})

    def test_order(self):  # AC6
        ids = [i["id"] for i in listing(self.home)["items"]]
        # open: blocking first (E8, R1; oldest first), then non-blocking oldest first; waiting; done newest first by handled time
        self.assertEqual(ids, ["E8", "R1", "E18", "E19", "E6", "E11", "E12", "E1", "E2", "E3", "E7",
                               "E17", "E16", "E15", "E14", "E13", "R3", "R2"])

    def test_empty_blocks_is_not_blocking(self):
        h = self.empty_home()
        run(h, "add", "--kind", "read", "--title", "First", stdin="b")
        run(h, "add", "--kind", "read", "--title", "Blocker", "--blocks", "PI-9", stdin="b", SQUAD_INBOX_NOW="2026-10-16T00:00:00Z")
        items = listing(h)["items"]
        self.assertEqual([(i["id"], i["blocks"]) for i in items], [("R2", "PI-9"), ("R1", "")])

    def test_nothing_is_not_blocking(self):  # QA-B F1
        h = self.empty_home()
        for t, b in (("A", " Nothing "), ("B", "-")):
            run(h, "add", "--kind", "read", "--title", t, "--blocks", b, stdin="b")
        self.assertEqual([i["blocks"] for i in listing(h)["items"]], ["", ""])

    def test_add_event_missing_fields_is_an_error(self):  # QA-B F2
        h = self.empty_home()
        (h / "inbox.jsonl").write_text('{"ev":"add","id":"R2"}\n', encoding="utf-8")
        snap = listing(h)
        self.assertEqual(snap["items"], [])
        self.assertEqual([(e["file"], e["row"]) for e in snap["errors"]], [("inbox.jsonl", 1)])

    def test_live_row_wins_over_seen_snapshot(self):  # AC26
        h = self.home
        run(h, "add", "--kind", "answer", "--title", "Qlive?", "--options", "(a) x; (b) y", "--rec", "old rec", "--blocks", "PI-9", stdin="body")
        listing(h)
        t = (h / "escalations.md").read_text(encoding="utf-8")
        (h / "escalations.md").write_text(t.replace("(a) x; (b) y", "(a) x; (b) y; (c) z").replace("PI-9", "").replace("old rec", "new rec"), encoding="utf-8")
        it = [i for i in listing(h)["items"] if i["title"] == "Qlive?"][0]
        self.assertEqual(([o["key"] for o in it["options"]], it["blocks"]), (["a", "b", "c"], ""))
        self.assertEqual(it["recommendation"], "new rec")

    def test_every_event_is_validated(self):  # AC27
        h = self.home
        run(h, "add", "--kind", "answer", "--title", "Qev?", stdin="body")
        listing(h)
        log = (h / "inbox.jsonl").read_text(encoding="utf-8").splitlines()
        key = next(json.loads(l)["key"] for l in log if '"Qev?"' in l)
        bad = ['{"ev":"seen","id":"zz","key":"%s"}' % key, '{"ev":"seen","id":5,"key":"%s"}' % key, '{"ev":"seen","id":"E9"}',
               '{"ev":"answer","id":"x"}', '{"ev":"withdraw"}', '{"ev":"delivered","id":7}', '{"ev":"read","id":"R0x"}',
               '{"ev":"gone","id":null}', '{"ev":"frobnicate","id":"E1"}', '{"ev":"filled","id":"e1"}']
        before = len(listing(h)["items"])
        with open(h / "inbox.jsonl", "a", encoding="utf-8") as f:
            f.write("\n".join(bad) + "\n")
        snap = listing(h)
        self.assertEqual(len(snap["items"]), before)
        rows = sorted(e["row"] for e in snap["errors"] if e["file"] == "inbox.jsonl")
        self.assertEqual(rows, list(range(len(log) + 1, len(log) + 1 + len(bad))))

    def test_duplicate_answer_add_refused(self):  # AC28
        h = self.home
        self.assertEqual(run(h, "add", "--kind", "answer", "--title", "Qdup?", stdin="body").returncode, 0)
        before = (h / "escalations.md").read_bytes()
        r = run(h, "add", "--kind", "answer", "--title", "Qdup?", stdin="body")
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertRegex(r.stderr, r"as E\d+")
        self.assertEqual((h / "escalations.md").read_bytes(), before)

    def test_short_row_reaching_the_question(self):  # AC29
        h = self.empty_home()
        (h / "escalations.md").write_text("| # | Date | Question | Options | Recommendation | Blocks | Answer |\n|---|---|---|---|---|---|---|\n| 4 | 2026-10-12 | short one |\n", encoding="utf-8")
        snap = listing(h)
        self.assertEqual(([i["title"] for i in snap["items"]], snap["errors"]), (["short one"], []))

    def test_no_files(self):  # AC12, AC13
        h = self.empty_home()
        snap = listing(h, "--no-write")
        self.assertEqual((snap["items"], snap["errors"]), ([], []))
        self.assertEqual(os.listdir(h), [])
        self.assertEqual(listing(h)["items"], [])
        self.assertEqual(os.listdir(h), [])  # nothing to sync, so nothing created

    def test_empty_file_and_no_table(self):
        h = self.empty_home()
        (h / "escalations.md").write_text("", encoding="utf-8")
        self.assertEqual(listing(h)["items"], [])
        shutil.copy(FIX / "no-table" / "escalations.md", h / "escalations.md")
        snap = listing(h)
        self.assertEqual((snap["items"], snap["errors"]), ([], []))

    def test_no_write_writes_nothing(self):  # AC13
        before = digest(self.home)
        listing(self.home, "--no-write")
        self.assertEqual(digest(self.home), before)
        self.assertFalse((self.home / "inbox.jsonl.lock").exists())

    def test_list_writes_seen_once(self):
        listing(self.home)
        after = digest(self.home)
        self.assertEqual(sum('"ev": "seen"' in l for l in (self.home / "inbox.jsonl").read_text(encoding="utf-8").splitlines()), 15)
        listing(self.home)
        self.assertEqual(digest(self.home), after)  # AC18: the second list writes zero bytes

    def test_human_list_and_open(self):
        r = run(self.home, "list", "--open")
        self.assertEqual(r.returncode, 0)
        self.assertIn("4 to answer, 1 to read, 2 waiting", r.stdout)
        self.assertNotIn("R2", r.stdout)

    def test_no_home(self):
        r = subprocess.run([sys.executable, "-B", CLI, "list"], capture_output=True, text=True, env=env(), encoding="utf-8")
        self.assertEqual(r.returncode, 2)

    def test_home_from_env(self):
        r = subprocess.run([sys.executable, "-B", CLI, "list", "--json", "--no-write"], capture_output=True, text=True,
                           env=env(GOAL_DIR=str(self.home)), encoding="utf-8")
        self.assertEqual(json.loads(r.stdout)["home"], str(self.home))
        r = subprocess.run([sys.executable, "-B", CLI, "list", "--json", "--no-write"], capture_output=True, text=True,
                           env=env(GOAL_DIR="/nonexistent", SCOPE_DIR=str(self.home)), encoding="utf-8")
        self.assertEqual(json.loads(r.stdout)["home"], str(self.home))

    def test_control_characters_pass_through(self):  # the mod strips them, not the CLI
        h = self.empty_home()
        run(h, "add", "--kind", "read", "--title", "t", stdin="a\x1b[31mred\x07")
        self.assertEqual(listing(h)["items"][0]["body"], "a\x1b[31mred\x07")


class OptionsTest(unittest.TestCase):
    def setUp(self):
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(ROOT / "bin"))
        import squadinbox
        self.parse = squadinbox.parse_options

    def test_cases(self):  # AC7
        self.assertEqual(self.parse("(a) x; (b) y"), [{"key": "a", "text": "x"}, {"key": "b", "text": "y"}])
        self.assertIsNone(self.parse("(a) only one"))
        self.assertIsNone(self.parse("(b) x; (a) y"))
        self.assertIsNone(self.parse("see (a) above"))
        self.assertIsNone(self.parse("see (a) above; (b) other"))
        self.assertIsNone(self.parse(""))
        self.assertIsNone(self.parse("(a) x; (b)"))

    def test_letters_and_text(self):
        got = self.parse("(a) first: with colon; (b) second, see (a) above; (c) third; (d) d;")
        self.assertEqual([o["key"] for o in got], ["a", "b", "c", "d"])
        self.assertEqual(got[0]["text"], "first: with colon")
        self.assertEqual(got[1]["text"], "second, see (a) above")  # an out-of-order marker is text
        self.assertEqual(got[3]["text"], "d")
        many = "; ".join("(%s) t%s" % (chr(97 + i), i) for i in range(8))
        self.assertEqual(len(self.parse(many)), 8)


class AddReadTest(Base):
    def test_add_read_ids_and_file(self):  # AC2, AC5
        h = self.empty_home()
        r = run(h, "add", "--kind", "read", "--title", "Hello", stdin="the body\n")
        self.assertEqual((r.returncode, r.stdout), (0, "1 new item in the inbox: Hello\n"))
        self.assertNotIn("the body", r.stdout + r.stderr)
        run(h, "add", "--kind", "read", "--title", "Two", stdin="b2")
        lines = (h / "inbox.jsonl").read_text(encoding="utf-8").splitlines()
        evs = [json.loads(l) for l in lines]
        self.assertEqual([(e["ev"], e["id"]) for e in evs], [("add", "R1"), ("add", "R2")])
        self.assertEqual(evs[0]["body"], "the body")

    def test_body_file(self):
        h = self.empty_home()
        (Path(self.tmp) / "b.txt").write_text("from file", encoding="utf-8")
        run(h, "add", "--kind", "read", "--title", "T", "--body-file", str(Path(self.tmp) / "b.txt"))
        self.assertEqual(listing(h)["items"][0]["body"], "from file")

    def test_concurrent_adds(self):  # AC2
        h = self.empty_home()
        procs = [subprocess.Popen([sys.executable, "-B", CLI, "--home", str(h), "add", "--kind", "read", "--title", "t%d" % i],
                                  stdin=subprocess.PIPE, text=True, stdout=subprocess.DEVNULL, env=env(), encoding="utf-8") for i in range(8)]
        for p in procs:
            p.communicate("body")
        self.assertEqual([p.returncode for p in procs], [0] * 8)
        evs = [json.loads(l) for l in (h / "inbox.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len({e["id"] for e in evs}), 8)

    def test_add_answer_row_on_top(self):  # AC3
        before = (self.home / "escalations.md").read_bytes()
        r = run(self.home, "add", "--kind", "answer", "--title", "Pick | one", "--options", "(a) x; (b) y", "--rec", "a",
                "--blocks", "PI-04", stdin="Line one\nline | two\r\nthree")
        self.assertEqual(r.returncode, 0, r.stderr)
        after = (self.home / "escalations.md").read_bytes()
        old, new = before.splitlines(keepends=True), after.splitlines(keepends=True)
        sep = next(i for i, l in enumerate(old) if l.startswith(b"|---"))
        self.assertEqual(new[:sep + 1], old[:sep + 1])
        self.assertEqual(new[sep + 2:], old[sep + 1:])  # the rest byte-identical
        self.assertEqual(new[sep + 1].decode(), "| 18 | 2026-10-15 | Pick \\| one<br>Line one<br>line \\| two<br>three | (a) x; (b) y | a | PI-04 |  |\n")
        rows = rows_of(self.home / "escalations.md")
        self.assertEqual(rows[0]["question"], "Pick | one<br>Line one<br>line | two<br>three")
        item = by_id(listing(self.home))["E18"]
        self.assertEqual((item["title"], item["body"]), ("Pick | one", "Pick | one<br>Line one<br>line | two<br>three"))
        self.assertEqual(item["blocks"], "PI-04")

    def test_next_number_skips_ids_in_log(self):
        h = self.empty_home()
        shutil.copy(self.home / "escalations.md", h / "escalations.md")
        listing(h)  # seen: E1..E17 now in the log
        run(h, "add", "--kind", "answer", "--title", "t", stdin="b")
        self.assertTrue((h / "escalations.md").read_text(encoding="utf-8").split("|---|---|---|---|---|---|---|\n")[1].startswith("| 18 |"))

    def test_refusals_change_nothing(self):  # AC4
        cases = [(("--kind", "read"), "b", "manager"),  # no title
                 (("--kind", "read", "--title", "  "), "b", "manager"),
                 (("--kind", "read", "--title", "t"), "", "manager"),
                 (("--kind", "read", "--title", "t"), " \n\t", "manager"),
                 (("--kind", "approve", "--title", "t"), "b", "manager"),
                 (("--kind", "", "--title", "t"), "b", "manager"),
                 (("--kind", "read", "--title", "t"), "b", None),
                 (("--kind", "read", "--title", "t"), "b", "dev"),
                 (("--kind", "answer", "--title", "t", "--options", "(a) one"), "b", "manager"),
                 (("--kind", "read", "--title", "t", "--options", "(a) x; (b) y"), "b", "manager"),
                 (("--kind", "read", "--title", " \n\x1b "), "b", "manager"),
                 (("--kind", "read", "--title", "t"), "x" * (64 * 1024 + 1), "manager")]
        before = digest(self.home)
        for args, body, role in cases:
            r = run(self.home, "add", *args, stdin=body, role=role)
            self.assertEqual(r.returncode, 2, (args, role, r.stderr))
            self.assertNotEqual(r.stderr, "")
            self.assertEqual(r.stdout, "")
            self.assertEqual(digest(self.home), before, (args, role))

    def test_add_answer_without_table_refuses(self):
        h = self.empty_home()
        shutil.copy(FIX / "no-table" / "escalations.md", h / "escalations.md")
        before = digest(h)
        self.assertEqual(run(h, "add", "--kind", "answer", "--title", "t", stdin="b").returncode, 2)
        self.assertEqual(digest(h), before)

    def test_read(self):  # AC9
        r = run(self.home, "read", "R1")
        self.assertEqual(r.returncode, 0, r.stderr)
        it = by_id(listing(self.home))["R1"]
        self.assertEqual((it["state"], it["done"]), ("done", {"kind": "read", "ts": NOW, "reason": None}))
        again = run(self.home, "read", "R1", SQUAD_INBOX_NOW="2026-10-16T00:00:00Z")
        self.assertEqual(again.returncode, 3)
        self.assertEqual(by_id(listing(self.home))["R1"]["done"]["ts"], NOW)
        self.assertEqual(run(self.home, "read", "E8").returncode, 2)
        self.assertEqual(run(self.home, "read", "R99").returncode, 2)

    def test_listing_never_marks_read(self):  # B-11
        for _ in range(3):
            listing(self.home)
        self.assertEqual(by_id(listing(self.home))["R1"]["state"], "open")

    def test_bad_ids(self):  # AC14
        for bad in ("../../x", "R", "r1", "R1234567", "R1/../x", "E1;ls", ""):
            r = run(self.home, "read", bad)
            self.assertEqual(r.returncode, 2, bad)

    def test_read_no_role_needed(self):
        self.assertEqual(run(self.home, "read", "R1", role=None).returncode, 0)


class SyncTest(Base):
    def delete_row(self, text):
        p = self.home / "escalations.md"
        p.write_text("".join(l for l in p.read_text(encoding="utf-8").splitlines(keepends=True) if text not in l), encoding="utf-8")

    def test_deleted_row_is_kept(self):  # AC8
        listing(self.home)
        self.delete_row("Ship the badge")
        it = by_id(listing(self.home))["E8"]
        self.assertEqual(it["done"]["kind"], "removed")
        self.assertEqual((it["title"], it["body"]), ("Ship the badge?", "Ship the badge?<br>It touches CART-04."))
        self.assertEqual([o["key"] for o in it["options"]], ["a", "b", "c"])
        self.assertEqual(it["done"]["ts"], NOW)
        self.assertEqual(it["flags"], ["row-removed"])
        later = json.loads(run(self.home, "list", "--json", SQUAD_INBOX_NOW="2026-10-20T00:00:00Z").stdout)
        self.assertEqual(by_id(later)["E8"]["done"]["ts"], NOW)  # the removal time is stable across calls

    def test_removed_with_no_write_still_reports_it(self):
        listing(self.home)
        self.delete_row("Ship the badge")
        self.assertEqual(by_id(listing(self.home, "--no-write"))["E8"]["done"]["kind"], "removed")

    def test_reused_number_gets_new_id(self):  # AC8, B-33
        listing(self.home)
        self.delete_row("Ship the badge")
        listing(self.home)
        run(self.home, "add", "--kind", "answer", "--title", "New one", stdin="b")  # next free: not 8
        items = by_id(listing(self.home))
        self.assertEqual(items["E8"]["title"], "Ship the badge?")
        self.assertEqual(items["E8"]["done"]["kind"], "removed")
        self.assertEqual(items["E20"]["title"], "New one")
        # a hand-written row that reuses `#8` for a different question
        p = self.home / "escalations.md"
        text = p.read_text(encoding="utf-8")
        p.write_text(text.replace("|---|---|---|---|---|---|---|\n", "|---|---|---|---|---|---|---|\n| 8 | 2026-10-15 | Reused eight | | | | |\n", 1), encoding="utf-8")
        items = by_id(listing(self.home))
        self.assertEqual(items["E8"]["title"], "Ship the badge?")
        self.assertEqual(items["E8"]["done"]["kind"], "removed")
        self.assertEqual(next(i for i in items.values() if i["title"] == "Reused eight")["id"], "E21")

    def test_answer_filled_by_hand_later(self):
        listing(self.home)
        p = self.home / "escalations.md"
        p.write_text(p.read_text(encoding="utf-8").replace("(c) later | a | CART-04 | |", "(c) later | a | CART-04 | yes |"), encoding="utf-8")
        it = by_id(listing(self.home))["E8"]
        self.assertEqual((it["done"]["kind"], it["done"]["reason"], it["flags"]), ("answered-file", "yes", ["answer-by-hand"]))


class ErrorsTest(Base):
    def test_malformed_jsonl_line(self):  # AC11
        with open(self.home / "inbox.jsonl", "a", encoding="utf-8") as f:
            f.write("{not json\n[1,2]\n")
        snap = listing(self.home)
        rows = {(e["file"], e["row"]) for e in snap["errors"]}
        n = len((FIX / "home" / "inbox.jsonl").read_text(encoding="utf-8").splitlines())
        self.assertEqual(rows, {("inbox.jsonl", n + 1), ("inbox.jsonl", n + 2), ("escalations.md", 17)})
        self.assertIn("R1", by_id(snap))

    def test_torn_last_line_does_not_swallow_next_event(self):
        with open(self.home / "inbox.jsonl", "a", encoding="utf-8") as f:
            f.write('{"ev": "add"')
        run(self.home, "add", "--kind", "read", "--title", "After", stdin="b")
        titles = [i["title"] for i in listing(self.home)["items"]]
        self.assertIn("After", titles)

    def test_bad_header(self):
        h = self.empty_home()
        (h / "escalations.md").write_text("| a | b |\n|---|---|\n| 1 | 2 |\n", encoding="utf-8")
        snap = listing(h)
        self.assertEqual(snap["items"], [])
        self.assertEqual(len(snap["errors"]), 1)


class ReaderGoldenTest(Base):
    def test_same_rows_as_the_golden(self):  # AC1: the reader's output on fixed inputs cannot drift
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(ROOT / "bin"))
        import squadinbox
        golden = json.loads((FIX / "board-reader-golden.json").read_text(encoding="utf-8"))
        for name, case in golden["tables"].items():
            text = case["text"] if "text" in case else (FIX / name).read_text(encoding="utf-8")
            header, rows = squadinbox.first_table(text)
            self.assertEqual([dict(zip(header, c)) for _, c in rows] if header else [], case["rows"], name)
        for cell, want in golden["clean_cell"].items():
            self.assertEqual(squadinbox.clean_cell(cell), want)


BREAKS = ["\r\n", "\n", "\r", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"]


class RowWriterTest(Base):
    """AC16: the row writer, in bytes, against the escalations.md table reader."""

    def structure(self):
        return [(len(r), tuple(r)) for r in rows_of(self.home / "escalations.md")]

    def test_each_break_becomes_one_br(self):
        for i, ch in enumerate(BREAKS):
            before = len(rows_of(self.home / "escalations.md"))
            run(self.home, "add", "--kind", "answer", "--title", "t%d" % i, stdin="one%stwo" % ch)
            rows = rows_of(self.home / "escalations.md")
            self.assertEqual(len(rows), before + 1, repr(ch))
            self.assertEqual(rows[0]["question"], "t%d<br>one<br>two" % i, repr(ch))
            self.assertEqual(len(rows[0]), 7, repr(ch))

    def test_endings_pipes_and_backslashes(self):
        for tail in ("\\", "\\\\", "\\|", "|", "a|", "**b** `c`"):
            before = len(rows_of(self.home / "escalations.md"))
            run(self.home, "add", "--kind", "answer", "--title", "t", "--rec", "r" + tail, stdin="body" + tail)
            rows = rows_of(self.home / "escalations.md")
            self.assertEqual((len(rows), len(rows[0])), (before + 1, 7), tail)
            self.assertEqual(rows[0]["blocks"], "", tail)
        bodies = [i["body"] for i in listing(self.home)["items"]]
        self.assertTrue(any(b.endswith("<br>body**b** `c`") for b in bodies))  # the body keeps markup clean_cell strips

    def test_bytes_survive(self):
        for name, data in (("crlf", b"| # | Date | Question | Options | Rec | Blocks | Answer |\r\n|---|---|---|---|---|---|---|\r\n| 1 | d | q | | | | |\r\n"),
                           ("nonl", b"intro \xff\xfe\n| # | Date | Question | Options | Rec | Blocks | Answer |\n|---|---|---|---|---|---|---|\n| 1 | d | q \xff | | | | |"),
                           ("sep-last", b"| # | Date | Question | Answer |\n|---|---|---|---|")):
            h = self.empty_home() if False else Path(self.tmp) / name
            h.mkdir()
            (h / "escalations.md").write_bytes(data)
            r = run(h, "add", "--kind", "answer", "--title", "t", stdin="b")
            self.assertEqual(r.returncode, 0, (name, r.stderr))
            out = (h / "escalations.md").read_bytes()
            if name == "crlf":
                self.assertEqual(out.count(b"\r\n"), 4)
                self.assertEqual(out.count(b"\n"), 4)
            if name == "nonl":
                self.assertTrue(out.endswith(b"q \xff | | | | |"))
                self.assertIn(b"intro \xff\xfe\n", out)
            if name == "sep-last":
                self.assertFalse(out.endswith(b"\n"))
                self.assertEqual(len(rows_of(h / "escalations.md")), 1)

    @unittest.skipUnless(CAN_SYMLINK, "symlinks need a privilege on Windows (WinError 1314)")
    def test_symlink_refused(self):
        h = self.empty_home()
        real = Path(self.tmp) / "real.md"
        shutil.copy(FIX / "home" / "escalations.md", real)
        os.symlink(real, h / "escalations.md")
        before = real.read_bytes()
        r = run(h, "add", "--kind", "answer", "--title", "t", stdin="b")
        self.assertEqual(r.returncode, 1)
        self.assertIn("symlink", r.stderr)
        self.assertEqual(real.read_bytes(), before)

    def test_mode_kept(self):
        p = self.home / "escalations.md"
        os.chmod(p, 0o640)
        run(self.home, "add", "--kind", "answer", "--title", "t", stdin="b")
        if sys.platform != "win32":  # Windows file modes differ (438 != 416); the temp-file check below still runs
            self.assertEqual(p.stat().st_mode & 0o777, 0o640)
        self.assertEqual([f for f in os.listdir(self.home) if f.startswith(".escalations-")], [])

    def test_numbers_after_deleting_rows(self):  # AC17 (W7)
        listing(self.home)
        p = self.home / "escalations.md"
        p.write_text("".join(l for l in p.read_text(encoding="utf-8").splitlines(keepends=True) if not l.startswith(("| 1 ", "| 2 ", "| 3 "))), encoding="utf-8")
        listing(self.home)
        run(self.home, "add", "--kind", "answer", "--title", "fresh", stdin="b")
        it = next(i for i in listing(self.home)["items"] if i["title"] == "fresh")
        row = next(l for l in p.read_text(encoding="utf-8").splitlines() if "fresh" in l)
        self.assertEqual(row.split("|")[1].strip(), it["id"][1:])
        self.assertGreaterEqual(int(it["id"][1:]), 4)

    def test_edited_question_changes_key(self):  # AC17 (W8)
        listing(self.home)
        p = self.home / "escalations.md"
        p.write_text(p.read_text(encoding="utf-8").replace("Ship the badge?", "Ship the badge now?"), encoding="utf-8")
        items = by_id(listing(self.home))
        self.assertEqual(items["E8"]["done"]["kind"], "removed")
        self.assertTrue(any(i["title"] == "Ship the badge now?" and i["state"] == "open" for i in items.values()))


class RaceAndStdinTest(Base):
    @unittest.skipIf(sys.platform == "win32", "os.execv on Windows returns early instead of replacing the process")
    def test_concurrent_adds_on_a_barrier(self):  # AC19
        script = ("import os,sys,time\nwhile not os.path.exists(sys.argv[1]): time.sleep(0.001)\n"
                  "os.execv(sys.executable, [sys.executable,'-B',%r,'--home',sys.argv[2],'add','--kind','read','--title','t'])" % CLI)
        for rnd in range(20):
            h = Path(self.tmp) / ("r%d" % rnd)
            h.mkdir()
            go = h / "go"
            procs = [subprocess.Popen([sys.executable, "-c", script, str(go), str(h)], stdin=subprocess.PIPE, text=True,
                                      stdout=subprocess.DEVNULL, env=env(), encoding="utf-8") for _ in range(8)]
            go.write_text("", encoding="utf-8")
            for p in procs:
                p.communicate("body")
            self.assertEqual([p.returncode for p in procs], [0] * 8, rnd)
            evs = [json.loads(l) for l in (h / "inbox.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(sorted(e["id"] for e in evs), sorted("R%d" % i for i in range(1, 9)), rnd)

    def test_stdin_never_hangs(self):  # AC20
        h = self.empty_home()
        args = [sys.executable, "-B", CLI, "--home", str(h), "add", "--kind", "read", "--title", "t"]
        r = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env(), timeout=20, encoding="utf-8")
        self.assertEqual(r.returncode, 2)
        r = subprocess.run(args, input="", capture_output=True, text=True, env=env(), timeout=20, encoding="utf-8")
        self.assertEqual(r.returncode, 2)
        with self.subTest("pty"):
            if not HAVE_PTY:
                self.skipTest("pty (termios) is not available on Windows")
            master, slave = pty.openpty()
            try:
                r = subprocess.run(args, stdin=slave, capture_output=True, text=True, env=env(), timeout=20, encoding="utf-8")
            finally:
                os.close(master)
                os.close(slave)
            self.assertEqual(r.returncode, 2)
        self.assertEqual(os.listdir(h), [] if not (h / "inbox.jsonl.lock").exists() else ["inbox.jsonl.lock"])

    def test_body_cap(self):
        h = self.empty_home()
        self.assertEqual(run(h, "add", "--kind", "read", "--title", "t", stdin="x" * (64 * 1024)).returncode, 0)

    def test_title_collapsed(self):  # AC21
        h = self.empty_home()
        run(h, "add", "--kind", "read", "--title", "a\nb\r\nc\x1b[2Jd\te\u2028f", stdin="b")
        title = listing(h)["items"][0]["title"]
        self.assertEqual(title, "a b c [2Jd e f")
        self.assertNotRegex(title, "[\x00-\x1f\x7f-\x9f\u2028\u2029]")


class ContractTest(Base):
    """AC22: closed sets, precision, counts; the fixture home hits every combination."""

    def test_closed_sets_and_combinations(self):
        snap = listing(self.home)
        combos = set()
        for it in snap["items"]:
            self.assertIn(it["kind"], ("answer", "read"))
            self.assertIn(it["state"], ("open", "answered-waiting", "done"))
            self.assertLessEqual(set(it["flags"]), {"answer-by-hand", "row-removed"})
            self.assertRegex(it["created"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
            self.assertEqual(it["created_precision"], "day" if it["kind"] == "answer" and it["created"].endswith("T00:00:00Z") else "second")
            if it["done"]:
                self.assertIn(it["done"]["kind"], ("read", "answered", "answered-file", "withdrawn", "removed"))
            if it["answer"]:
                self.assertIn(it["answer"]["source"], ("pane", "chat"))
            combos.add((it["kind"], it["state"], it["done"] and it["done"]["kind"], tuple(it["flags"])))
        self.assertEqual(combos, {
            ("answer", "open", None, ()), ("answer", "answered-waiting", None, ()),
            ("answer", "answered-waiting", None, ("row-removed",)),
            ("answer", "done", "answered", ()), ("answer", "done", "answered", ("row-removed",)),
            ("answer", "done", "answered-file", ("answer-by-hand",)), ("answer", "done", "withdrawn", ()),
            ("answer", "done", "removed", ("row-removed",)), ("read", "open", None, ()),
            ("read", "done", "read", ()), ("read", "done", "withdrawn", ())})
        c = snap["counts"]
        its = snap["items"]
        self.assertEqual(c["answer_open"], sum(1 for i in its if i["kind"] == "answer" and i["state"] == "open"))
        self.assertEqual(c["read_open"], sum(1 for i in its if i["kind"] == "read" and i["state"] == "open"))
        self.assertEqual(c["waiting"], sum(1 for i in its if i["state"] == "answered-waiting"))

    def test_output_is_stable(self):
        a = run(self.home, "list", "--json", "--no-write").stdout
        b = run(self.home, "list", "--json", "--no-write").stdout
        self.assertEqual(a, b)


class RepairTest(Base):
    """AC25: a plain list repairs an empty Answer cell from the answer event; --no-write repairs nothing."""

    def test_repair(self):
        p = self.home / "escalations.md"
        p.write_text(p.read_text(encoding="utf-8").replace("| PI-02 | (a) x |", "| PI-02 | |"), encoding="utf-8")
        rows = len(rows_of(p))
        before = digest(self.home)
        it = by_id(listing(self.home, "--no-write"))["E11"]
        self.assertEqual(it["state"], "answered-waiting")
        self.assertEqual(digest(self.home), before)
        it = by_id(listing(self.home))["E11"]
        self.assertEqual((it["state"], it["answer"]["text"]), ("answered-waiting", "(a) x"))
        self.assertIn("| PI-02 | (a) x |", p.read_text(encoding="utf-8"))
        self.assertEqual(len(rows_of(p)), rows)
        after = digest(self.home)
        listing(self.home)
        self.assertEqual(digest(self.home), after)


class Python39Test(unittest.TestCase):
    def test_sources_parse_as_3_9(self):  # AC24
        import ast
        for path in (ROOT / "bin" / "squadinbox.py", ROOT / "bin" / "squad-inbox", Path(__file__)):
            src = path.read_text(encoding="utf-8")
            tree = ast.parse(src, feature_version=(3, 9))
            for node in ast.walk(tree):
                self.assertNotIsInstance(node, ast.Match, path.name)
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
                    for side in (node.left, node.right):
                        self.assertFalse(isinstance(side, ast.Constant) and side.value is None, "X | None in %s" % path.name)


class NoBytecodeTest(Base):
    def test_no_pyc(self):  # AC15
        run(self.home, "list")
        self.assertEqual(list((ROOT / "bin").rglob("*.pyc")), [])
        self.assertEqual(list((ROOT / "bin").rglob("__pycache__")), [])


if __name__ == "__main__":
    unittest.main()
