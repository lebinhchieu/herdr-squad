"""Ticket 03: the v7 rule files cover every line of v6 process.md and the log rows; fixes and limits hold."""
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
sys.path.insert(0, str(BIN))
import squadrules as sr  # noqa: E402

PROC = ROOT / "templates/squad/process"
V6 = ROOT / "templates/squad/process.md"
MAPPING = ROOT / ".scratch/_done/composed-process/issues/03-convert-process-to-rules/mapping.md"
# The live squad's process-log.md is not tracked: rows 33-49 are the non-`v<N>` rows dated 2026-10-16 to 2026-10-19.
LOG_ROWS = list(range(33, 50))
DROPS = ("dropped: structure", "dropped: replaced by compose")


def _load():
    rules, tombs, problems = sr.load_rules(str(PROC), str(ROOT))
    return rules, problems


def _source_rows(text):
    """Line numbers of the non-blank, non-heading lines that are not table separators or table header rows."""
    lines = text.split("\n")
    skip = set()
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if not s or ln.startswith("#"):
            skip.add(i)
        if s.startswith("|") and re.fullmatch(r"[|\s:-]+", s):
            skip.add(i)
            skip.add(i - 1)
    return [i for i in range(1, len(lines) + 1) if i not in skip]


def _mapping():
    rows = {}
    for ln in MAPPING.read_text(encoding="utf-8").split("\n"):
        if not ln.startswith("| ") or ln.startswith("| Source") or ln.startswith("|---"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        rows[cells[0]] = cells[1]
    return rows


class RuleFiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules, cls.problems = _load()
        cls.ids = {r.id for r in cls.rules}

    def test_lint_passes_on_the_real_tree(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SQUAD_")}
        r = subprocess.run([sys.executable, str(BIN / "squad-process"), "lint", "--plugin-root", str(ROOT)],
                           capture_output=True, encoding="utf-8", env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual([ln for ln in r.stdout.splitlines() if not ln.startswith("warning: ")], [])

    def test_core_has_at_most_40_lines(self):
        n = len((PROC / "core.md").read_text(encoding="utf-8").rstrip("\n").split("\n"))
        self.assertLessEqual(n, 40)

    def test_no_size_clauses_in_rule_text(self):
        for p in sorted(PROC.glob("*.md")):
            text = p.read_text(encoding="utf-8")
            self.assertNotIn("(S:", text, p.name)
            self.assertNotIn("In M and L", text, p.name)

    def test_every_role_gets_rules_at_every_size(self):
        for size in "SML":
            facts = {"size": size, "design": "yes", "qa": "full", "goal": "no", "qa-b": "yes"}
            for role in sr.ROLES:
                got = [r for r in self.rules
                       if ("all" in r.roles or role in r.roles or role in r.aware) and sr.matches(r.when, facts)]
                if size == "S" and role in ("ba", "team-lead", "qa-whitebox", "qa-blackbox"):
                    continue  # the role does not exist at S
                self.assertTrue(got, (role, size))


class Fixes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules, _ = _load()
        cls.by = {r.id: r for r in cls.rules}
        cls.text = "\n".join(r.body for r in cls.rules)

    def test_rows_48_and_49_are_rules(self):
        self.assertIn("style-contract.md", self.by["REV-16"].body)
        self.assertEqual(self.by["REV-16"].roles, ["tech-lead"])
        self.assertIn("all style findings", self.by["REV-17"].body)
        self.assertIn("never assert presentational values", self.by["REV-18a"].body.lower())
        self.assertEqual(self.by["REV-18a"].roles, ["qa-whitebox"])
        self.assertEqual(self.by["REV-18b"].roles, ["qa-blackbox"])

    def test_fix_a_handin_target_by_size(self):
        self.assertEqual((self.by["REV-13a"].when, self.by["REV-13a"].roles), ("size = S", ["dev"]))
        self.assertIn("to the Manager", self.by["REV-13a"].body)
        self.assertNotIn("QA", self.by["REV-13a"].body)
        self.assertIn("QA whitebox and QA blackbox", self.by["REV-13b"].body)

    def test_fix_b_tech_lead_tells_manager_parallel_tasks_in_s(self):
        r = self.by["START-2d"]
        self.assertEqual((r.when, r.roles), ("plan-owner = team-lead", ["tech-lead"]))
        self.assertIn("ready in parallel", r.body)

    def test_fix_c_designer_business_doubt(self):
        self.assertIn("`ASK` the Manager", self.by["MSG-16a"].body)
        self.assertIn("`ASK` the BA", self.by["MSG-16b"].body)
        for r in self.rules:
            self.assertNotRegex(r.body, r"Tech Lead[^.]*writes?[^.]*escalations\.md", r.id)

    def test_fix_d_and_e(self):
        self.assertNotIn("label shape", self.text)
        self.assertNotRegex(self.text, r"(?i)\bRetro\b[^.\n]*section|→ Retro\b|\(Retro\)")
        for rid in ("ITER-6", "ITER-7", "ITER-8", "ITER-9", "ITER-10"):
            self.assertIn(rid, self.by)


class Mapping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules, _ = _load()
        cls.ids = {r.id for r in cls.rules}
        cls.rows = _mapping()

    def test_every_v6_line_has_a_row(self):
        missing = [n for n in _source_rows(V6.read_text(encoding="utf-8"))
                   if f"templates/squad/process.md:{n}" not in self.rows]
        self.assertEqual(missing, [])

    def test_every_log_row_has_a_row(self):
        self.assertEqual([n for n in LOG_ROWS if f"log row {n}" not in self.rows], [])

    def test_every_target_is_a_rule_or_a_closed_drop_form(self):
        for src, target in self.rows.items():
            if target in DROPS or target == "stays in card":
                continue
            if target.startswith("dropped: duplicate of "):
                parts = [target[len("dropped: duplicate of "):]]
            elif target.startswith("dropped: fix "):
                self.assertRegex(target, r"^dropped: fix [a-e]$", src)
                continue
            else:
                parts = [t.strip() for t in target.split(",")]
            for rid in parts:
                self.assertIn(rid, self.ids, f"{src} -> {target}")

    def test_rows_48_and_49_map_to_rules(self):
        for n in (48, 49):
            target = self.rows[f"log row {n}"]
            self.assertFalse(target.startswith("dropped") or target == "stays in card", target)

    def test_duplicate_collapses_point_at_a_surviving_rule(self):
        for src, target in self.rows.items():
            if target.startswith("dropped: duplicate of "):
                self.assertIn(target[len("dropped: duplicate of "):], self.ids, src)


if __name__ == "__main__":
    unittest.main()
