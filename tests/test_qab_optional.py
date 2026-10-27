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
from rulesview import who  # noqa: E402

GOLDEN = Path(__file__).resolve().parent / "fixtures" / "qab" / "golden.json"
NOW = "2026-10-22T10:00:00Z"
GOLDEN_VERSION = "0.4.1"  # the plugin version in the composed header when golden.json was hashed
NEW_IDS = ("REV-19", "REV-20", "REV-21", "EVID-6", "EVID-7", "SIZE-19", "SIZE-20", "SIZE-21")  # the golden is regenerated from the merged tree, so letters added later need no entry
ROLE_LIST = sr.ROLES


def compose(role, size="M", qab=None, design="no", qa="full", root=ROOT):
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "scopes" / "fx"
        home.mkdir(parents=True)
        team = sr.legacy_team(size, qab or "yes", design)  # the converter's mapping: today's shapes as teams
        lines = ["goal:", f"team: {', '.join(team) or 'none'}", f"qa: {qa}"]
        (home / "scope.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        env = {k: v for k, v in os.environ.items() if not k.startswith("SQUAD_")}
        r = subprocess.run([sys.executable, "-B", str(root / "bin" / "squad-process"), "compose", role, "--home", str(home),
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
    text = re.sub(r"(?m)^(plugin: )\d+\.\d+\.\d+(?= )", r"\g<1>" + GOLDEN_VERSION, text)  # a plugin version bump is not a rules change
    return re.sub(r"\n{3,}", "\n\n", text)


class NoLineUnchanged(unittest.TestCase):
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
        pairs = {"REV-13b": ("REV-19b", "REV-13d"), "REV-19b": ("REV-13d",), "EVID-3b": ("EVID-7", "EVID-8"),
                 "REV-8": ("REV-21",), "SIZE-5b": ("REV-21",)}
        for size in "ML":
            for base, variants in pairs.items():
                for var in variants:
                    for role in ROLE_LIST:
                        for qab in ("yes", "no"):
                            t = compose(role, size, qab).stdout
                            if base in ids(t) and var in ids(t):
                                self.fail(f"{base} and {var} both compose for {role} at {size} qa-b {qab}")

    def test_dev_gets_behaviour_per_ac_and_no_blackbox_handin(self):
        for size in "ML":
            t = compose("dev", size, "no").stdout
            self.assertIn("EVID-6", ids(t))
            self.assertIn("REV-19b", ids(t))
            for gone in ("REV-13b", "REV-13d"):
                self.assertNotIn(gone, ids(t))
            body = re.search(r"(?ms)^## REV-19b .*?(?=^## |\Z)", t).group(0)
            self.assertNotIn("QA blackbox", body.replace("no QA blackbox", ""))
            self.assertNotIn("both QAs", t)
        y = compose("dev", "M", "yes").stdout
        self.assertIn("REV-13b", ids(y))
        self.assertNotIn("REV-19b", ids(y))

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

    def test_m_without_qa_blackbox_has_no_ba_in_rev_21(self):
        t = compose("qa-whitebox", "M", "no").stdout
        self.assertIn("REV-21b", ids(t))
        self.assertNotIn("REV-21", ids(t))
        self.assertEqual(who("REV-21")["business-ac = ticket"], ((), ()))
        self.assertEqual(who("REV-21b")["business-ac = ticket"][0], ("qa-whitebox",))
        self.assertIn("REV-21", ids(compose("ba", "L", "no").stdout))
        self.assertNotIn("REV-21b", ids(compose("qa-whitebox", "L", "no").stdout))

    def test_manager_spawns_only_the_roles_on_the_team(self):
        t = compose("manager", "M", "no").stdout
        self.assertIn("SIZE-21a", ids(t))
        body = re.search(r"(?ms)^## SIZE-21a .*?(?=^## |\Z)", t).group(0)
        self.assertIn("Spawn only the roles in `team:`", body)
        self.assertIn("SIZE-1", ids(compose("manager", "M").stdout))  # the team proposal, every team
        self.assertNotIn("SIZE-19", ids(t))  # tombstoned: QA blackbox off is a non-pick

    def test_qa_blackbox_rules_absent_in_who(self):
        out = subprocess.run([sys.executable, "-B", str(ROOT / "bin" / "squad-process"), "who", "SIZE-8b"],
                             capture_output=True, encoding="utf-8").stdout
        self.assertIn("behaviour-check = manager: acts: -; aware: -", out)
        self.assertIn("behaviour-check = qa-black: acts: qa-blackbox; aware: -", out)
        for rid in ("REV-13d", "REV-18a"):  # rules a team without QA blackbox never composes (its own role is not on the team)
            for size in "ML":
                for role in (r for r in ROLE_LIST if r != "qa-blackbox"):
                    self.assertNotIn(rid, ids(compose(role, size, "no").stdout), (rid, role, size))
        for rid in ("REV-9", "REV-11", "REV-13b"):
            out = subprocess.run([sys.executable, "-B", str(ROOT / "bin" / "squad-process"), "who", rid],
                                 capture_output=True, encoding="utf-8").stdout
            self.assertIn("M qa-b no: acts: -; aware: -", out, rid)
            self.assertNotIn("M qa-b yes: acts: -", out, rid)


class QabNoWithDesign(unittest.TestCase):
    def test_designer_without_qa_blackbox_is_a_valid_team(self):
        r = compose("dev", "M", "no", design="yes")  # I8 (a): all 128 shapes are valid; ui-check falls to the Manager
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("SIZE-10a", ids(compose("manager", "M", "no", design="yes").stdout))
        self.assertNotIn("SIZE-10b", ids(compose("manager", "M", "no", design="yes").stdout))

    def test_light_qa_combines(self):
        r = compose("qa-whitebox", "M", "no", qa="light")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("LC-21", ids(r.stdout))
        self.assertIn("REV-20", ids(r.stdout))


if __name__ == "__main__":
    unittest.main()
