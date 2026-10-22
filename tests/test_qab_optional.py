"""Ticket 14: `qa-b: no` composes the QA-blackbox-free rules; no `qa-b` line composes as `qa-b: yes`.
The golden is the merged tree (integration 27); 14's byte-identity to 4901cab was proven at 99796ce."""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
import squadcompose as sc  # noqa: E402
import squadrules as sr  # noqa: E402

GOLDEN = Path(__file__).resolve().parent / "fixtures" / "qab" / "golden.json"
NOW = "2026-10-22T10:00:00Z"
NEW_IDS = ("REV-19", "REV-20", "REV-21", "EVID-6", "EVID-7", "SIZE-19", "SIZE-20", "SIZE-21")
ROLE_LIST = sr.ROLES


def compose(role, size="M", qab=None, design="no", qa="full", root=ROOT):
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "scopes" / "fx"
        home.mkdir(parents=True)
        lines = ["goal:", f"size: {size}", f"qa: {qa}", f"design: {design}"]
        if qab:
            lines.append(f"qa-b: {qab}")
        (home / "scope.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        env = {k: v for k, v in os.environ.items() if not k.startswith("SQUAD_")}
        r = subprocess.run([sys.executable, str(root / "bin" / "squad-process"), "compose", role, "--home", str(home),
                            "--now", NOW, "--agent", f"fx-{role}"], capture_output=True, encoding="utf-8", env=env)
        return r


def ids(text):
    return re.findall(r"(?m)^## ([A-Z]+-\d+[a-z]?) ", text)


def normalise(text):
    """Drop what ticket 14 adds: its rule sections, its tokens in `rules:` and its lines in the index."""
    for i in NEW_IDS:
        text = re.sub(rf"(?ms)^## {i} .*?(?=^## |\Z)", "", text)
        text = re.sub(rf"(?m)^- {i} .*\n", "", text)
        text = re.sub(rf"(?m)^(rules: .*?) {i}\b", r"\1", text)
    return re.sub(r"\n{3,}", "\n\n", text)


class NoLineUnchanged(unittest.TestCase):
    def test_every_role_matches_the_4901cab_golden(self):
        golden = json.loads(GOLDEN.read_text())
        for key, want in golden.items():
            role, size, design = key.split("/")
            with self.subTest(key):
                r = compose(role, size, None, design)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(hashlib.sha256(normalise(r.stdout).encode()).hexdigest(), want)

    def test_no_line_equals_qab_yes_at_merged_sha(self):
        for size in "SML":
            for role in ROLE_LIST:
                with self.subTest(f"{role}/{size}"):
                    self.assertEqual(compose(role, size).stdout, compose(role, size, "yes").stdout)

    def test_qab_no_at_s_composes_as_no_line(self):
        for role in ROLE_LIST:
            with self.subTest(role):
                self.assertEqual(compose(role, "S", "no").stdout, compose(role, "S").stdout)


class QabNo(unittest.TestCase):
    def test_qa_blackbox_rule_blocks_never_compose_with_their_variant(self):
        pairs = {"REV-13b": "REV-19", "REV-14b": "REV-19", "LC-20b": "REV-19", "EVID-3b": "EVID-7",
                 "SPAWN-2b": "SIZE-21a", "SPAWN-2c": "SIZE-21b", "REV-8": "REV-21", "SIZE-5b": "REV-21"}
        for size in "ML":
            for base, var in pairs.items():
                for role in ROLE_LIST:
                    for qab in ("yes", "no"):
                        t = compose(role, size, qab).stdout
                        if base in ids(t) and var in ids(t):
                            self.fail(f"{base} and {var} both compose for {role} at {size} qa-b {qab}")

    def test_dev_gets_behaviour_per_ac_and_no_blackbox_handin(self):
        t = compose("dev", "M", "no").stdout
        self.assertIn("EVID-6", ids(t))
        self.assertIn("REV-19", ids(t))
        for gone in ("REV-13b", "REV-14b", "LC-20b"):
            self.assertNotIn(gone, ids(t))
        body = re.search(r"(?ms)^## REV-19 .*?(?=^## |\Z)", t).group(0)
        self.assertNotIn("QA blackbox", body.replace("no QA blackbox", ""))
        self.assertNotIn("both QAs", t)
        y = compose("dev", "M", "yes").stdout
        self.assertIn("REV-13b", ids(y))
        self.assertNotIn("REV-19", ids(y))

    def test_qa_whitebox_checks_behaviour(self):
        t = compose("qa-whitebox", "L", "no").stdout
        self.assertIn("REV-20", ids(t))
        self.assertIn("EVID-7", ids(t))
        self.assertNotIn("REV-20", ids(compose("qa-whitebox", "L").stdout))

    def test_ba_writes_ac_alone(self):
        t = compose("ba", "L", "no").stdout
        self.assertIn("REV-21", ids(t))
        for gone in ("REV-8", "SIZE-5b"):
            self.assertNotIn(gone, ids(t))

    def test_manager_does_not_spawn_qa_blackbox(self):
        t = compose("manager", "M", "no").stdout
        self.assertNotIn("SPAWN-2b", ids(t))
        self.assertIn("SIZE-21a", ids(t))
        body = re.search(r"(?ms)^## SIZE-21a .*?(?=^## |\Z)", t).group(0)
        self.assertIn("not QA blackbox", body)
        self.assertIn("qa-b: yes", body)  # the flip back
        self.assertIn("SIZE-19", ids(compose("manager", "M").stdout))  # the proposal rule at the default

    def test_qa_blackbox_rules_absent_in_who(self):
        for rid in ("REV-9", "REV-11", "SIZE-8b", "REV-13b", "SPAWN-2b"):
            out = subprocess.run([sys.executable, str(ROOT / "bin" / "squad-process"), "who", rid],
                                 capture_output=True, encoding="utf-8").stdout
            self.assertIn("M qa-b no: acts: -; aware: -", out, rid)
            self.assertNotIn("M qa-b yes: acts: -", out, rid)


class QabNoWithDesign(unittest.TestCase):
    def test_compose_and_lint_refuse(self):
        r = compose("dev", "M", "no", design="yes")
        self.assertEqual(r.returncode, 2)
        self.assertIn("qa-b", r.stderr)
        self.assertIn("design", r.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "scope.md").write_text("size: M\nqa-b: no\ndesign: yes\n")
            lint = subprocess.run([sys.executable, str(ROOT / "bin" / "squad-process"), "lint", "--home", tmp],
                                  capture_output=True, encoding="utf-8")
            self.assertNotEqual(lint.returncode, 0)
            self.assertIn("qa-b", lint.stdout)
            self.assertIn("design", lint.stdout)

    def test_light_qa_combines(self):
        r = compose("qa-whitebox", "M", "no", qa="light")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("LC-21", ids(r.stdout))
        self.assertIn("REV-20", ids(r.stdout))

    def test_qab_value_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "scope.md").write_text("size: M\nqa-b: maybe\n")
            with self.assertRaises(sc.ComposeError):
                sc.read_home(tmp)


if __name__ == "__main__":
    unittest.main()
