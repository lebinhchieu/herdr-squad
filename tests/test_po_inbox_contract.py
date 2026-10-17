"""PI-07: `squad-inbox list --json` and the mod's fixtures agree, in both directions (C4)."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import po_inbox_fixtures as fx

ROOT = fx.ROOT
HOME = ROOT / "tests" / "fixtures" / "inbox" / "home"

# (kind, state, done.kind, flags) the contract allows and the fixture home must produce (design.md → The contract).
ALLOWED = {
    ("answer", "open", None, ()),
    ("answer", "answered-waiting", None, ()),
    ("answer", "answered-waiting", None, ("row-removed",)),
    ("answer", "answered-waiting", None, ("cell-not-written",)),
    ("answer", "done", "answered", ()),
    ("answer", "done", "answered", ("row-removed",)),
    ("answer", "done", "answered-file", ("answer-by-hand",)),
    ("answer", "done", "withdrawn", ()),
    ("answer", "done", "removed", ("row-removed",)),
    ("read", "open", None, ()),
    ("read", "done", "read", ()),
    ("read", "done", "withdrawn", ()),
}
CLOSED = {"kind": {"answer", "read"}, "state": {"open", "answered-waiting", "done"},
          "done.kind": {"read", "answered", "answered-file", "withdrawn", "removed"}, "source": {"pane", "chat"},
          "flags": {"answer-by-hand", "row-removed", "cell-not-written"}}


def list_json(home, now=fx.NOW, write=False):
    env = {k: v for k, v in os.environ.items() if k not in fx.AGENT_ENV}
    env.update(SQUAD_INBOX_NOW=now, PYTHONDONTWRITEBYTECODE="1")
    args = [sys.executable, fx.CLI, "--home", str(home), "list", "--json"] + ([] if write else ["--no-write"])
    done = subprocess.run(args, capture_output=True, text=True, env=env, encoding="utf-8")
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


def unwrap(path):
    m = re.fullmatch(r"//[^\n]*\nexport default (\".*\")\n", path.read_text(encoding="utf-8"), re.S)
    assert m, "%s is not a generated fixture" % path
    return json.loads(m.group(1))


class ContractTest(unittest.TestCase):
    def full_home_with_unwritten_cell(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        home = Path(tmp.name) / "home"
        shutil.copytree(HOME, home)
        with open(home / "escalations.md", "ab") as f:  # invalid UTF-8 in the row: its Answer cell cannot be written
            f.write(b"| 30 | 2026-10-12 | No cell \xff | (a) x; (b) y | | | |\n")
        env = {k: v for k, v in os.environ.items() if k not in fx.AGENT_ENV}
        env.update(SQUAD_ROLE="manager", SQUAD_INBOX_NOW=fx.NOW, PYTHONDONTWRITEBYTECODE="1")
        done = subprocess.run([sys.executable, fx.CLI, "--home", str(home), "answer", "E30", "--option", "a", "--source", "pane"],
                              input="", text=True, capture_output=True, env=env, encoding="utf-8")
        self.assertEqual(done.returncode, 0, done.stderr)
        return home

    def test_fixture_home_produces_every_allowed_combination(self):  # (i)
        snap = list_json(self.full_home_with_unwritten_cell())
        seen = {(i["kind"], i["state"], (i["done"] or {}).get("kind"), tuple(i["flags"])) for i in snap["items"]}
        self.assertEqual(ALLOWED - seen, set(), "missing combinations")
        for i in snap["items"]:
            self.assertIn(i["kind"], CLOSED["kind"])
            self.assertIn(i["state"], CLOSED["state"])
            self.assertTrue(set(i["flags"]) <= CLOSED["flags"], i["flags"])
            if i["done"]:
                self.assertIn(i["done"]["kind"], CLOSED["done.kind"])
            if i["answer"]:
                self.assertIn(i["answer"]["source"], CLOSED["source"])
        self.assertEqual({i["answer"]["source"] for i in snap["items"] if i["answer"]}, CLOSED["source"])

    def test_counts_are_derived_from_items(self):
        snap = list_json(HOME)
        items = snap["items"]
        self.assertEqual(snap["counts"], {
            "answer_open": sum(1 for i in items if i["kind"] == "answer" and i["state"] == "open"),
            "read_open": sum(1 for i in items if i["kind"] == "read" and i["state"] == "open"),
            "waiting": sum(1 for i in items if i["state"] == "answered-waiting")})

    def test_fixture_files_are_the_cli_output_byte_for_byte(self):  # (ii)
        for name, build in fx.FIXTURES.items():
            with self.subTest(name):
                path = fx.OUT / (name + ".ts")
                self.assertEqual(path.read_text(encoding="utf-8"), fx.ts_text(name, build()), "run python3 tests/po_inbox_fixtures.py")
                self.assertEqual(unwrap(path), build())

    def test_every_fixture_file_is_listed_for_the_mod_tests(self):
        index = (fx.OUT / "index.ts").read_text(encoding="utf-8")
        files = {p.stem for p in fx.OUT.glob("contract-*.ts")}
        self.assertEqual(files, set(fx.FIXTURES))
        for name in files:
            self.assertIn("'%s':" % name, index)

    def test_the_mod_parses_every_fixture_and_the_extra_key_case(self):  # (ii), (iii): run by `claude plugin test`
        tests = "".join(p.read_text(encoding="utf-8") for p in (ROOT / "hooks" / "po-inbox").glob("*.test.ts"))
        self.assertIn("Object.entries(FIXTURES)", tests)
        self.assertIn("an extra key anywhere is ignored", tests)
        self.assertIn("another version", tests)


if __name__ == "__main__":
    unittest.main()
