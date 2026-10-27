"""drop-scope-size 06: the eight small rule files compose, for each of the 7 legacy shapes and each role, the same rules as BASE.

GOLDEN was generated from BASE (merge-base with main, 2949573) with its own tests/rulesview.composed, over every
`## <ID>` heading of who/starting/files/goal/promotion/closing/notes/iterations. IDS are the rules whose body (and roles) did not change; a `when:` retarget of them keeps
the set a role sees at a shape. Rewritten rules (WHO-1b, WHO-2b ...) are covered by their own tests."""
import re
import unittest

from rulesview import composed
from squadrules import ROLE_KEY, legacy_team

SHAPES = {"S": dict(size="S"), "M": dict(size="M"), "L": dict(size="L"), "Lnoqb": dict(size="L", qa="no"),
          "Mdesign": dict(size="M", design="yes"), "March": dict(size="M", architecture="yes"),
          "Lgoal": dict(size="L", goal="yes")}
SHAPE_ARGS = {"S": ("S",), "M": ("M",), "L": ("L",), "Lnoqb": ("L", "no"), "Mdesign": ("M", "yes", "yes"),
              "March": ("M", "yes", "no", "yes"), "Lgoal": ("L",)}
IDS = "WHO-4 WHO-5 WHO-6 WHO-7 WHO-8 WHO-8c START-2b START-2d START-4 START-4a START-5 START-5a START-6 START-7 START-8 START-9 START-10 START-11 START-12 START-13 START-14 START-15 START-16 START-17 START-18 START-20 FILE-1 FILE-2 FILE-3 FILE-4 FILE-5c FILE-8 FILE-9 FILE-11 GOAL-1 GOAL-2 GOAL-3b GOAL-4 GOAL-5 GOAL-6a GOAL-6c GOAL-7 PROMO-1 PROMO-2 PROMO-4 PROMO-5 PROMO-6 PROMO-7 PROMO-8 CLOSE-2 CLOSE-3a CLOSE-3b CLOSE-4 CLOSE-5 NOTE-1 NOTE-2 NOTE-3 ITER-2 ITER-3 ITER-4 ITER-5 ITER-6c ITER-7 ITER-8 ITER-9 ITER-10 ITER-11 ITER-12 ITER-13 ITER-14 ITER-15 ITER-16".split()
GOLDEN = {
    "L/architect": "START-6 START-9 FILE-9 FILE-11 NOTE-1",
    "L/ba": "WHO-7 START-6 START-9 START-11 FILE-1 FILE-2 FILE-3 FILE-11 NOTE-1",
    "L/designer": "START-6 START-9 START-12 FILE-9 FILE-11 NOTE-1",
    "L/dev": "START-6 START-10",
    "L/manager": "WHO-5 WHO-6 WHO-7 WHO-8 START-4 START-5 START-18 FILE-1 FILE-2 FILE-3 FILE-4 FILE-8 FILE-11 GOAL-4 GOAL-7 PROMO-1 PROMO-4 CLOSE-2 CLOSE-5 NOTE-1 NOTE-2 ITER-2 ITER-4 ITER-5 ITER-6c ITER-10 ITER-11 ITER-12 ITER-15 ITER-16",
    "L/qa-blackbox": "START-6 START-13 FILE-9 FILE-11 NOTE-1",
    "L/qa-whitebox": "START-6 START-9 START-14 FILE-9 FILE-11 PROMO-8 NOTE-1",
    "L/team-lead": "WHO-7 WHO-8c START-2b START-4 START-5 START-6 START-9 START-15 FILE-1 FILE-2 FILE-3 FILE-4 FILE-5c FILE-8 FILE-11 PROMO-5 NOTE-1 NOTE-3 ITER-3",
    "L/tech-lead": "WHO-7 START-2d START-6 START-9 START-16 FILE-1 FILE-2 FILE-3 FILE-9 FILE-11 PROMO-1 PROMO-2 PROMO-4 NOTE-1",
    "Lgoal/architect": "START-6 START-7 START-9 FILE-9 FILE-11 NOTE-1",
    "Lgoal/ba": "WHO-7 START-6 START-7 START-9 START-11 FILE-1 FILE-2 FILE-3 FILE-11 NOTE-1",
    "Lgoal/designer": "START-6 START-7 START-9 START-12 FILE-9 FILE-11 NOTE-1",
    "Lgoal/dev": "START-6 START-10",
    "Lgoal/manager": "WHO-5 WHO-6 WHO-7 WHO-8 START-4 START-5 START-18 FILE-1 FILE-2 FILE-3 FILE-4 FILE-8 FILE-11 GOAL-1 GOAL-2 GOAL-5 GOAL-6c GOAL-7 PROMO-1 PROMO-6 PROMO-7 CLOSE-2 CLOSE-3b CLOSE-4 CLOSE-5 NOTE-1 NOTE-2 ITER-2 ITER-4 ITER-5 ITER-6c ITER-10 ITER-11 ITER-12 ITER-15 ITER-16",
    "Lgoal/qa-blackbox": "START-6 START-8 START-13 FILE-9 FILE-11 NOTE-1",
    "Lgoal/qa-whitebox": "START-6 START-7 START-9 START-14 FILE-9 FILE-11 GOAL-3b PROMO-8 NOTE-1",
    "Lgoal/team-lead": "WHO-7 WHO-8c START-2b START-4 START-5 START-6 START-7 START-9 START-15 FILE-1 FILE-2 FILE-3 FILE-4 FILE-5c FILE-8 FILE-11 PROMO-5 NOTE-1 NOTE-3 ITER-3",
    "Lgoal/tech-lead": "WHO-7 START-2d START-6 START-7 START-9 START-16 FILE-1 FILE-2 FILE-3 FILE-9 FILE-11 GOAL-6a PROMO-1 PROMO-2 PROMO-6 CLOSE-3a NOTE-1",
    "M/architect": "START-6 START-9 FILE-9 FILE-11 NOTE-1",
    "M/ba": "WHO-7 START-6 START-9 START-11 FILE-1 FILE-2 FILE-3 FILE-11 NOTE-1",
    "M/designer": "START-6 START-9 START-12 FILE-9 FILE-11 NOTE-1",
    "M/dev": "START-6 START-10",
    "M/manager": "WHO-5 WHO-6 WHO-7 WHO-8 START-4 START-5 START-18 FILE-1 FILE-2 FILE-3 FILE-4 FILE-8 FILE-11 GOAL-4 GOAL-7 PROMO-1 PROMO-4 CLOSE-2 CLOSE-5 NOTE-1 NOTE-2 ITER-2 ITER-4 ITER-5 ITER-6c ITER-10 ITER-11 ITER-12 ITER-15 ITER-16",
    "M/qa-blackbox": "START-6 START-13 FILE-9 FILE-11 NOTE-1",
    "M/qa-whitebox": "START-6 START-9 START-14 FILE-9 FILE-11 PROMO-8 NOTE-1",
    "M/team-lead": "WHO-7 START-4 START-5 START-6 START-9 START-15 FILE-1 FILE-2 FILE-3 FILE-4 FILE-8 FILE-11 NOTE-1",
    "M/tech-lead": "WHO-7 START-6 START-9 START-16 FILE-1 FILE-2 FILE-3 FILE-9 FILE-11 PROMO-1 PROMO-4 NOTE-1",
    "March/architect": "START-6 START-9 START-20 FILE-9 FILE-11 NOTE-1",
    "March/ba": "WHO-7 START-6 START-9 START-11 FILE-1 FILE-2 FILE-3 FILE-11 NOTE-1",
    "March/designer": "START-6 START-9 START-12 FILE-9 FILE-11 NOTE-1",
    "March/dev": "START-6 START-10",
    "March/manager": "WHO-5 WHO-6 WHO-7 WHO-8 START-4 START-4a START-5 START-5a START-18 FILE-1 FILE-2 FILE-3 FILE-4 FILE-8 FILE-11 GOAL-4 GOAL-7 PROMO-1 PROMO-4 CLOSE-2 CLOSE-5 NOTE-1 NOTE-2 ITER-2 ITER-4 ITER-5 ITER-6c ITER-10 ITER-11 ITER-12 ITER-15 ITER-16",
    "March/qa-blackbox": "START-6 START-13 FILE-9 FILE-11 NOTE-1",
    "March/qa-whitebox": "START-6 START-9 START-14 FILE-9 FILE-11 PROMO-8 NOTE-1",
    "March/team-lead": "WHO-7 START-4 START-5 START-5a START-6 START-9 START-15 FILE-1 FILE-2 FILE-3 FILE-4 FILE-8 FILE-11 NOTE-1",
    "March/tech-lead": "WHO-7 START-6 START-9 START-16 FILE-1 FILE-2 FILE-3 FILE-9 FILE-11 PROMO-1 PROMO-4 NOTE-1",
    "Mdesign/architect": "START-6 START-9 FILE-9 FILE-11 NOTE-1",
    "Mdesign/ba": "WHO-7 START-6 START-9 START-11 FILE-1 FILE-2 FILE-3 FILE-11 NOTE-1",
    "Mdesign/designer": "WHO-4 START-6 START-9 START-12 FILE-9 FILE-11 NOTE-1",
    "Mdesign/dev": "START-6 START-10",
    "Mdesign/manager": "WHO-4 WHO-5 WHO-6 WHO-7 WHO-8 START-4 START-5 START-18 FILE-1 FILE-2 FILE-3 FILE-4 FILE-8 FILE-11 GOAL-4 GOAL-7 PROMO-1 PROMO-4 CLOSE-2 CLOSE-5 NOTE-1 NOTE-2 ITER-2 ITER-4 ITER-5 ITER-6c ITER-10 ITER-11 ITER-12 ITER-15 ITER-16",
    "Mdesign/qa-blackbox": "START-6 START-13 FILE-9 FILE-11 NOTE-1",
    "Mdesign/qa-whitebox": "START-6 START-9 START-14 FILE-9 FILE-11 PROMO-8 NOTE-1",
    "Mdesign/team-lead": "WHO-7 START-4 START-5 START-6 START-9 START-15 FILE-1 FILE-2 FILE-3 FILE-4 FILE-8 FILE-11 NOTE-1",
    "Mdesign/tech-lead": "WHO-4 WHO-7 START-6 START-9 START-16 FILE-1 FILE-2 FILE-3 FILE-9 FILE-11 PROMO-1 PROMO-4 NOTE-1",
    "S/architect": "START-6 START-9 FILE-9 FILE-11 NOTE-1",
    "S/ba": "WHO-7 START-6 START-9 START-11 FILE-1 FILE-2 FILE-3 FILE-11 NOTE-1",
    "S/designer": "START-6 START-9 START-12 FILE-9 FILE-11 NOTE-1",
    "S/dev": "START-6 START-10",
    "S/manager": "WHO-5 WHO-6 WHO-7 WHO-8 START-4 START-5 START-18 FILE-1 FILE-2 FILE-3 FILE-4 FILE-11 GOAL-4 GOAL-7 PROMO-1 PROMO-4 CLOSE-2 CLOSE-5 NOTE-1 NOTE-2 ITER-2 ITER-4 ITER-5 ITER-6c ITER-10 ITER-11 ITER-12 ITER-15 ITER-16",
    "S/qa-blackbox": "START-6 START-13 FILE-9 FILE-11 NOTE-1",
    "S/qa-whitebox": "START-6 START-9 START-14 FILE-9 FILE-11 NOTE-1",
    "S/team-lead": "WHO-7 START-4 START-5 START-6 START-9 START-15 FILE-1 FILE-2 FILE-3 FILE-4 FILE-11 NOTE-1",
    "S/tech-lead": "WHO-7 START-6 START-9 START-16 FILE-1 FILE-2 FILE-3 FILE-9 FILE-11 PROMO-1 PROMO-4 NOTE-1",
}


class SevenShapeEquivalence(unittest.TestCase):
    def test_same_rules_per_shape_and_role_as_base(self):
        for key, want in GOLDEN.items():
            shape, role = key.split("/")
            if role not in ("manager", "dev") and ROLE_KEY.get(role, role) not in legacy_team(*SHAPE_ARGS[shape]):
                continue  # an absent role composes nothing meaningful
            with self.subTest(key):
                text = composed(role, **SHAPES[shape])
                got = " ".join(i for i in IDS if re.search(r"## " + re.escape(i) + r"\b", text))
                self.assertEqual(got, want)


# Rewritten or retargeted rules (body or roles changed): the same check. The two known differences are by design:
# WHO-1b is now the one unconditional "Task done" row (the Manager sees it at every shape; base L only) and WHO-2b
# (promotion owner QA whitebox) is not the Manager's when the Developer promotes (S).
CHANGED_IDS = "WHO-1a WHO-1b WHO-2 WHO-2d WHO-2e WHO-2b WHO-2c WHO-3a WHO-3b WHO-8a WHO-8b START-1 START-2a START-2c START-3 START-3b START-19 FILE-5a FILE-5b FILE-6 FILE-7 FILE-10 GOAL-3a GOAL-3c GOAL-6b GOAL-6d PROMO-3a PROMO-3b PROMO-5b CLOSE-1 CLOSE-3c ITER-1 ITER-3b ITER-6 ITER-6a ITER-6b".split()
CHANGED = {
    "L/architect": "",
    "L/ba": "WHO-1b WHO-2c PROMO-3a",
    "L/designer": "",
    "L/dev": "",
    "L/manager": "WHO-1b WHO-2 WHO-2c WHO-3b WHO-8b START-1 START-2c START-3 START-3b START-19 FILE-5b FILE-6 FILE-7 GOAL-6b CLOSE-1 ITER-1 ITER-6 ITER-6b",
    "L/qa-blackbox": "",
    "L/qa-whitebox": "",
    "L/team-lead": "WHO-1b WHO-3b FILE-7",
    "L/tech-lead": "WHO-1b WHO-2 WHO-2c FILE-7 GOAL-6b",
    "Lgoal/architect": "",
    "Lgoal/ba": "WHO-1b WHO-2c PROMO-3a",
    "Lgoal/designer": "",
    "Lgoal/dev": "",
    "Lgoal/manager": "WHO-1b WHO-2 WHO-2c WHO-3b WHO-8b START-1 START-2c START-3 START-3b START-19 FILE-5b FILE-6 FILE-7 FILE-10 GOAL-6b CLOSE-1 ITER-1 ITER-6 ITER-6b",
    "Lgoal/qa-blackbox": "",
    "Lgoal/qa-whitebox": "",
    "Lgoal/team-lead": "WHO-1b WHO-3b FILE-7",
    "Lgoal/tech-lead": "WHO-1b WHO-2 WHO-2c FILE-7 FILE-10 GOAL-3a GOAL-6b",
    "M/architect": "",
    "M/ba": "",
    "M/designer": "",
    "M/dev": "",
    "M/manager": "WHO-1a WHO-2d WHO-2b WHO-3a WHO-8a START-1 START-2a START-3 START-3b START-19 FILE-5a FILE-6 FILE-7 GOAL-6b PROMO-5b CLOSE-1 ITER-1 ITER-3b ITER-6 ITER-6b",
    "M/qa-blackbox": "",
    "M/qa-whitebox": "",
    "M/team-lead": "FILE-7",
    "M/tech-lead": "FILE-7 GOAL-6b",
    "March/architect": "WHO-2e",
    "March/ba": "",
    "March/designer": "",
    "March/dev": "",
    "March/manager": "WHO-1a WHO-2d WHO-2e WHO-2b WHO-3a WHO-8a START-1 START-2a START-3 START-3b START-19 FILE-5a FILE-6 FILE-7 GOAL-6b PROMO-5b CLOSE-1 ITER-1 ITER-3b ITER-6 ITER-6b",
    "March/qa-blackbox": "",
    "March/qa-whitebox": "",
    "March/team-lead": "FILE-7",
    "March/tech-lead": "WHO-2e FILE-7 GOAL-6b",
    "Mdesign/architect": "",
    "Mdesign/ba": "",
    "Mdesign/designer": "",
    "Mdesign/dev": "",
    "Mdesign/manager": "WHO-1a WHO-2d WHO-2b WHO-3a WHO-8a START-1 START-2a START-3 START-3b START-19 FILE-5a FILE-6 FILE-7 GOAL-6b PROMO-5b CLOSE-1 ITER-1 ITER-3b ITER-6 ITER-6b",
    "Mdesign/qa-blackbox": "",
    "Mdesign/qa-whitebox": "",
    "Mdesign/team-lead": "FILE-7",
    "Mdesign/tech-lead": "FILE-7 GOAL-6b",
    "S/architect": "",
    "S/ba": "",
    "S/designer": "",
    "S/dev": "",
    "S/manager": "WHO-1a WHO-2d WHO-2b WHO-3a WHO-8a START-1 START-2a START-3 START-3b START-19 FILE-5a FILE-6 FILE-7 GOAL-6b PROMO-3b PROMO-5b CLOSE-1 ITER-1 ITER-6 ITER-6a",
    "S/qa-blackbox": "",
    "S/qa-whitebox": "",
    "S/team-lead": "FILE-7",
    "S/tech-lead": "FILE-7 GOAL-6b",
}



class ChangedRulesEquivalence(unittest.TestCase):
    def test_changed_rules_same_per_shape_and_role_except_the_two_known(self):
        for key, want in CHANGED.items():
            shape, role = key.split("/")
            if role not in ("manager", "dev") and ROLE_KEY.get(role, role) not in legacy_team(*SHAPE_ARGS[shape]):
                continue
            with self.subTest(key):
                text = composed(role, **SHAPES[shape])
                got = {i for i in CHANGED_IDS if re.search(r"## " + re.escape(i) + r"\b", text)}
                exp = set(want.split())
                if key == "S/manager":
                    exp = (exp - {"WHO-2b"}) | {"WHO-1b"}
                elif key in ("M/manager", "March/manager", "Mdesign/manager"):
                    exp = exp | {"WHO-1b"}
                self.assertEqual(sorted(got), sorted(exp))


if __name__ == "__main__":
    unittest.main()
