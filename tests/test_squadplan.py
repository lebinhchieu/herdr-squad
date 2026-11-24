"""Plan model of ticket 04 (po-clarity): durations, fields, steps, loops, goal table, the inbox line. Pure: no browser, no git.

Named for the technical AC (T04-n) of `tasks/04-design-notes.md`."""
import re
import signal
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from squadtest import BIN  # noqa: E402

sys.path.insert(0, str(BIN))
import squadplan  # noqa: E402


def scope(tasks, scope_md="# Scope: s\n"):
    """A temp scope folder under `<repo>/.claude/squads/t/scopes/s` with tasks/NN.md; -> (TemporaryDirectory, home)."""
    tmp = tempfile.TemporaryDirectory()
    home = Path(tmp.name) / ".claude" / "squads" / "t" / "scopes" / "s"
    (home / "tasks").mkdir(parents=True)
    (home / "scope.md").write_text(scope_md, encoding="utf-8")
    for nn, body in tasks.items():
        (home / "tasks" / (nn + ".md")).write_text("# %s t%s\n\n%s\n" % (nn, nn, body), encoding="utf-8")
    return tmp, home


def timed(fn, seconds=2):
    """T04-2: a loop must not hang. Alarm fails the test after `seconds`."""
    def boom(*_):
        raise AssertionError("hang")
    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(seconds)
    try:
        return fn()
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class DurationTest(unittest.TestCase):
    def test_T04_3_duration_table(self):
        cases = [("30m", 30), ("1h", 60), (".5h", 30), ("1.5h", 90), ("1h 30m", 90), ("1,5h", None), ("abc", None), ("", None), (None, None)]
        for text, want in cases:
            self.assertEqual(squadplan.duration_min(text), want, repr(text))

    def test_fields_read_a_header_line_with_dots(self):
        f = squadplan.fields_of("# 04\n\nSize: M · Plan: step 2 · Depends on: 01, 03, 06\nAim: do it\nEstimate: 1h 30m\n")
        self.assertEqual(f, {"aim": "do it", "estimate": "1h 30m", "depends": ["01", "03", "06"]})
        self.assertEqual(squadplan.fields_of("Depends on: none\n")["depends"], [])
        self.assertEqual(squadplan.fields_of("# x\n"), {"aim": None, "estimate": None, "depends": None})


class StepsTest(unittest.TestCase):
    def test_T04_2_AC1_chain_gives_steps_1_2_3_with_arrows(self):
        tmp, home = scope({"01": "Aim: first\nEstimate: 1h\nDepends on: none", "02": "Depends on: 01", "03": "Depends on: 01, 02"})
        self.addCleanup(tmp.cleanup)
        rows = squadplan.build_scope(home)["rows"]
        self.assertEqual([(r["id"], r["step"], r["deps"]) for r in rows], [("01", 1, []), ("02", 2, ["01"]), ("03", 3, ["01", "02"])])
        self.assertEqual((rows[0]["aim"], rows[0]["est_min"], rows[1]["aim"], rows[1]["est_min"]), ("first", 60, None, None))

    def test_blocked_by_is_the_fallback_and_a_missing_task_is_unknown(self):
        tmp, home = scope({"01": "Blocked by: none", "02": "Blocked by: 01", "03": "Depends on: 01, 09"})
        self.addCleanup(tmp.cleanup)
        by = {r["id"]: r for r in squadplan.build_scope(home)["rows"]}
        self.assertEqual((by["02"]["deps"], by["02"]["step"]), (["01"], 2))
        self.assertEqual((by["03"]["deps"], by["03"]["unknown_deps"], by["03"]["step"]), (["01"], ["09"], 2))

    def test_T04_2_loops_end_and_are_marked(self):
        for deps, loops in (({"a": ["b"], "b": ["a"]}, {"a", "b"}), ({"a": ["a"]}, {"a"}),
                            ({"a": ["b"], "b": ["a"], "c": ["a"], "d": []}, {"a", "b", "c"})):
            got = timed(lambda: squadplan.steps(deps))
            self.assertEqual({n for n, s in got.items() if s is None}, loops, deps)
        tmp, home = scope({"01": "Depends on: 02", "02": "Depends on: 01", "03": "Depends on: none"})
        self.addCleanup(tmp.cleanup)
        rows = timed(lambda: squadplan.build_scope(home)["rows"])
        self.assertEqual([(r["id"], r["loop"]) for r in rows], [("03", False), ("01", True), ("02", True)])


GOAL = """# Goal: erd

## Scopes

| Scope | Depends on | Aim | Est | Status |
|---|---|---|---|---|
| erd-a | - | Base model | 2h | passed |
| ERD2 | erd-a | Second part | 1h 30m | building |
| erd-c | erd-a, Matt A5, A6 | Third part | abc | open |
"""


class GoalTest(unittest.TestCase):
    def test_T04_5_goal_columns_steps_and_outside_waits(self):
        rows = {r["id"]: r for r in squadplan.build_goal(GOAL)["rows"]}
        self.assertEqual((rows["erd-a"]["step"], rows["erd-a"]["est_min"], rows["erd-a"]["passed"]), (1, 120, True))
        self.assertEqual((rows["ERD2"]["step"], rows["ERD2"]["deps"], rows["ERD2"]["est_min"]), (2, ["erd-a"], 90))
        self.assertEqual((rows["erd-c"]["deps"], rows["erd-c"]["waits"], rows["erd-c"]["est_min"]), (["erd-a"], "Matt A5, A6", None))

    def test_T04_5_a_table_without_those_columns_still_renders(self):
        rows = squadplan.build_goal("## Scopes\n\n| Scope | Status |\n|---|---|\n| one | open |\n| two | open |\n")["rows"]
        self.assertEqual([(r["id"], r["step"], r["aim"], r["est_min"], r["deps"]) for r in rows], [("one", 1, None, None, []), ("two", 1, None, None, [])])
        self.assertEqual(squadplan.build_goal(None)["rows"], [])


class ReuseTest(unittest.TestCase):
    def test_T04_7_aim_check_is_the_one_of_ticket_03(self):
        src = (BIN / "squadplan.py").read_text(encoding="utf-8")
        self.assertIn("squadids.bare_ids", src)
        self.assertIsNone(re.search(r"\[A-Z\]", src))   # no second regex of an ID token
        tmp, home = scope({"01": "Aim: fix D73 now"})
        self.addCleanup(tmp.cleanup)
        self.assertEqual(squadplan.build_scope(home)["rows"][0]["aim_bare_ids"], ["D73"])


class LineTest(unittest.TestCase):
    def test_plan_line_parts_goal_and_scope(self):
        tmp, home = scope({"01": "Aim: first\nDepends on: none", "02": "Aim: second\nDepends on: 01"})
        self.addCleanup(tmp.cleanup)
        self.assertEqual(squadplan.plan_line_parts(home, "2", None),
                         {"pos": "task 2 of 2", "step": "step 2", "aim": "second", "next": "next: nothing, last one"})
        self.assertEqual(squadplan.plan_line_parts(home, "01 and more", None)["next"], "next: t02")
        self.assertIsNone(squadplan.plan_line_parts(home, "blocks", None))
        self.assertIsNone(squadplan.plan_line_parts(home, "", None))
        gtmp = tempfile.TemporaryDirectory()
        self.addCleanup(gtmp.cleanup)
        (Path(gtmp.name) / "goal.md").write_text(GOAL, encoding="utf-8")
        got = squadplan.plan_line_parts(gtmp.name, "ERD2")
        self.assertEqual((got["pos"], got["step"], got["aim"], got["next"]), ("scope 2 of 3", "step 2", "Second part", "next: erd-c"))

    def test_cost_no_git_and_no_worktime(self):
        import squadboard_git
        import squadboard_worktime
        tmp, home = scope({"01": "Aim: first", "02": "Depends on: 01"})
        self.addCleanup(tmp.cleanup)
        boom = AssertionError("not allowed in the model")
        with unittest.mock.patch.object(squadboard_git, "_git", side_effect=boom), \
                unittest.mock.patch.object(squadboard_worktime, "read", side_effect=boom), \
                unittest.mock.patch("subprocess.run", side_effect=boom):
            self.assertIsNotNone(squadplan.plan_line_parts(home, "01"))
            self.assertEqual(len(squadplan.build_scope(home)["rows"]), 2)


if __name__ == "__main__":
    unittest.main()
