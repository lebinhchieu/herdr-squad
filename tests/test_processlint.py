"""processlint: each check of design §9 fails on a bad sample, passes on the fixed one, and holds at its boundary."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"
sys.path.insert(0, str(BIN))
import processlint as pl  # noqa: E402

HEAD = "# Process\n\n## Section\n\n"

def doc(body):
    return HEAD + body


def words(n):
    return " ".join(["word"] * n)


def checks(problems):
    return [p.split(": ")[1] for p in problems]


class LengthTest(unittest.TestCase):
    def test_bullet_60_words_passes_61_fails(self):
        self.assertEqual(pl.lint(doc(f"- {words(60)}\n")), [])
        self.assertEqual(checks(pl.lint(doc(f"- {words(61)}\n"))), ["length"])

    def test_bullet_continuation_lines_are_counted(self):
        self.assertEqual(checks(pl.lint(doc(f"- {words(30)}\n  {words(31)}\n"))), ["length"])
        self.assertEqual(pl.lint(doc(f"- {words(30)}\n  {words(30)}\n")), [])

    def test_paragraph_60_passes_61_fails(self):
        self.assertEqual(pl.lint(doc(f"{words(30)}\n{words(30)}\n")), [])
        self.assertEqual(checks(pl.lint(doc(f"{words(30)}\n{words(31)}\n"))), ["length"])

    def test_table_cells_are_counted_per_cell(self):
        row = f"| {words(60)} | {words(60)} |\n"
        self.assertEqual(pl.lint(doc("| a | b |\n|---|---|\n" + row)), [])
        self.assertEqual(checks(pl.lint(doc(f"| a | b |\n|---|---|\n| {words(61)} | x |\n"))), ["length"])

    def test_a_new_bullet_starts_a_new_count(self):
        self.assertEqual(pl.lint(doc(f"- {words(40)} a\n- {words(40)} b\n")), [])

    def test_fenced_long_line_is_ignored(self):
        self.assertEqual(pl.lint(doc(f"```\n{words(200)}\n```\n")), [])


class HedgeTest(unittest.TestCase):
    def test_each_hedge_fails_and_fix_passes(self):
        for hedge in ("try to", "ideally", "preferably", "where possible", "as appropriate", "as needed",
                      "usually", "generally", "properly", "carefully", "etc.", "and so on", "should",
                      "SHOULD", "Try To"):
            with self.subTest(hedge=hedge):
                self.assertEqual(checks(pl.lint(doc(f"- Manager {hedge} act.\n"))), ["hedge"])
        self.assertEqual(pl.lint(doc("- Manager must act.\n")), [])

    def test_whole_words_only(self):
        self.assertEqual(pl.lint(doc("- Manager must act: shoulder, properties, generalize, retry.\n")), [])

    def test_continuation_line_is_reported_on_its_own_line(self):
        problems = pl.lint(doc("- Manager must\n  act carefully.\n"))
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("line 6:"), problems)

    def test_fenced_hedge_is_ignored(self):
        self.assertEqual(pl.lint(doc("```\nyou should act\n```\n")), [])


class HistoryTest(unittest.TestCase):
    def test_each_pattern_fails(self):
        for bad in ("on 2026-10-14", "in 2026", "see the changelog", "formerly X", "previously X",
                    "used to X", "no longer X", "was added", "was changed", "was renamed"):
            with self.subTest(bad=bad):
                self.assertEqual(checks(pl.lint(doc(f"- Manager must act {bad}.\n"))), ["history"])

    def test_fixed_sample_and_non_years_pass(self):
        self.assertEqual(pl.lint(doc("- Manager must act at most 3 times, 15,000 bytes, port 8080.\n")), [])

    def test_fenced_date_is_ignored(self):
        self.assertEqual(pl.lint(doc("```\n## v2 — 2026-10-14\n```\n")), [])


class BoldTest(unittest.TestCase):
    def test_one_span_passes_two_fail_in_a_bullet(self):
        self.assertEqual(pl.lint(doc("- **Label.** Manager must act.\n")), [])
        self.assertEqual(checks(pl.lint(doc("- **Label.** Manager **must** act.\n"))), ["bold"])

    def test_span_15_words_passes_16_fails(self):
        self.assertEqual(pl.lint(doc(f"- **{words(15)}** Manager must act.\n")), [])
        self.assertEqual(checks(pl.lint(doc(f"- **{words(16)}** Manager must act.\n"))), ["bold"])

    def test_long_span_fails_in_a_paragraph_and_a_table_cell(self):
        self.assertEqual(checks(pl.lint(doc(f"**{words(16)}**\n"))), ["bold"])
        self.assertEqual(checks(pl.lint(doc(f"| a |\n|---|\n| **{words(16)}** |\n"))), ["bold"])
        self.assertEqual(pl.lint(doc(f"| a |\n|---|\n| **{words(15)}** |\n")), [])

    def test_two_short_spans_in_a_paragraph_are_allowed(self):
        self.assertEqual(pl.lint(doc("**One.** and **two.**\n")), [])


class DuplicateTest(unittest.TestCase):
    SENTENCE = "The Manager must merge a branch only on the PO's request."

    def test_repeated_sentence_fails_distinct_passes(self):
        self.assertEqual(checks(pl.lint(doc(f"- {self.SENTENCE}\n- {self.SENTENCE}\n"))), ["duplicate"])
        self.assertEqual(pl.lint(doc(f"- {self.SENTENCE}\n- The Manager must never merge a branch alone.\n")), [])

    def test_markup_and_case_are_ignored(self):
        other = "the **manager** must merge a branch only on the `PO's` request."
        self.assertEqual(checks(pl.lint(doc(f"- {self.SENTENCE}\n- {other}\n"))), ["duplicate"])

    def test_sentence_boundary_7_words_ok_8_fails(self):
        seven, eight = "One two three four five six seven.", "One two three four five six seven eight."
        self.assertEqual(pl.lint(doc(f"- {seven}\n- {seven}\n")), [])
        self.assertEqual(checks(pl.lint(doc(f"- {eight}\n- {eight}\n"))), ["duplicate"])

    def test_repeat_inside_one_bullet_fails(self):
        self.assertEqual(checks(pl.lint(doc(f"- {self.SENTENCE} {self.SENTENCE}\n"))), ["duplicate"])

    def test_repeated_table_row_fails_even_when_short(self):
        table = "| a | b |\n|---|---|\n| x | y |\n"
        self.assertEqual(checks(pl.lint(doc(table + "| x | y |\n"))), ["duplicate"])
        self.assertEqual(pl.lint(doc(table + "| x | z |\n")), [])

    def test_fenced_repeat_is_ignored(self):
        self.assertEqual(pl.lint(doc(f"```\n{self.SENTENCE}\n{self.SENTENCE}\n```\n")), [])


class ExceptionsTest(unittest.TestCase):
    BAD = doc("- Manager should act.\n")

    def test_matching_exception_silences(self):
        self.assertEqual(checks(pl.lint(self.BAD)), ["hedge"])
        self.assertEqual(pl.lint(self.BAD, exceptions=[("hedge", "- Manager should", "quoted rule text")]), [])

    def test_exception_is_per_check(self):
        out = pl.lint(self.BAD, exceptions=[("length", "- Manager should", "wrong check")])
        self.assertEqual(sorted(checks(out)), ["hedge", "stale-exception"])

    def test_missing_or_blank_reason_raises(self):
        for exc in (("hedge", "- Manager", ""), ("hedge", "- Manager", "  "), ("hedge", "- Manager"),
                    ("length", "", "x"), ("length", "  ", "x")):
            with self.subTest(exc=exc), self.assertRaises(ValueError):
                pl.lint(self.BAD, exceptions=[exc])

    def test_exception_matching_no_line_is_stale(self):
        out = pl.lint(doc("- Manager must act.\n"), exceptions=[("hedge", "- Gone", "was needed once")])
        self.assertEqual(checks(out), ["stale-exception"])


class CliTest(unittest.TestCase):
    def run_cli(self, text):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "process.md"
            path.write_text(text)
            return subprocess.run([sys.executable, str(BIN / "processlint.py"), str(path)],
                                  capture_output=True, text=True)

    def test_clean_file_exits_0_silently(self):
        r = self.run_cli(doc("- Manager must act.\n"))
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_problem_exits_1_and_prints_it(self):
        r = self.run_cli(doc("- Manager should act.\n"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("line 5: hedge: 'should'", r.stdout)

    def test_missing_file_exits_2_with_one_stderr_line(self):
        r = subprocess.run([sys.executable, str(BIN / "processlint.py"), "/nonexistent/process.md"],
                           capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        self.assertEqual(len(r.stderr.strip().splitlines()), 1)

    def test_no_argument_exits_2(self):
        r = subprocess.run([sys.executable, str(BIN / "processlint.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
