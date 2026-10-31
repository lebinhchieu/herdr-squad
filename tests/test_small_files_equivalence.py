"""drop-scope-size 06: the eight small rule files compose, for two shapes (M, the default; Lgoal, the one that differs: every
role and a goal) and each role, the same rules as BASE. Ticket 10b cut the other five shapes (S, L, Lnoqb, Mdesign, March).

GOLDEN was generated from BASE (merge-base with main, 2949573) with its own tests/rulesview.composed, over every
`## <ID>` heading of who/starting/files/goal/promotion/closing/notes/iterations. IDS are the rules whose body (and roles) did not change; a `when:` retarget of them keeps
the set a role sees at a shape. Rewritten rules (WHO-1b, WHO-2b ...) are covered by their own tests."""
import re
import unittest

from rulesview import composed, shape_team
from squadrules import ROLE_KEY

SHAPES = {"M": dict(size="M"), "Lgoal": dict(size="L", goal="yes")}
SHAPE_ARGS = {"M": ("M",), "Lgoal": ("L",)}
IDS = "WHO-4 WHO-5 WHO-6 WHO-7 WHO-8 WHO-8c START-2b START-2d START-4 START-4a START-5 START-5a START-6 START-7 START-8 START-9 START-10 START-11 START-12 START-13 START-14 START-15 START-16 START-17 START-18 START-20 FILE-1 FILE-2 FILE-3 FILE-4 FILE-5c FILE-8 FILE-9 FILE-11 GOAL-1 GOAL-2 GOAL-3b GOAL-4 GOAL-5 GOAL-6a GOAL-6c GOAL-7 PROMO-1 PROMO-2 PROMO-4 PROMO-5 PROMO-6 PROMO-7 PROMO-8 CLOSE-2 CLOSE-3a CLOSE-3b CLOSE-4 CLOSE-5 NOTE-1 NOTE-2 NOTE-3 ITER-2 ITER-3 ITER-4 ITER-5 ITER-6c ITER-7 ITER-8 ITER-9 ITER-10 ITER-11 ITER-12 ITER-13 ITER-14 ITER-15 ITER-16".split()
GOLDEN = {
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
}


class SevenShapeEquivalence(unittest.TestCase):
    def test_same_rules_per_shape_and_role_as_base(self):
        for key, want in GOLDEN.items():
            shape, role = key.split("/")
            if role not in ("manager", "dev") and ROLE_KEY.get(role, role) not in shape_team(*SHAPE_ARGS[shape]):
                continue  # an absent role composes nothing meaningful
            with self.subTest(key):
                text = composed(role, **SHAPES[shape])
                got = " ".join(i for i in IDS if re.search(r"## " + re.escape(i) + r"\b", text))
                self.assertEqual(got, want)


# Rewritten or retargeted rules (body or roles changed): the same check. The known difference is by design:
# WHO-1b is now the one unconditional "Task done" row (the Manager sees it at every shape; base L only).
CHANGED_IDS = "WHO-1a WHO-1b WHO-2 WHO-2d WHO-2e WHO-2b WHO-2c WHO-3a WHO-3b WHO-8a WHO-8b START-1 START-2a START-2c START-3 START-3b START-19 FILE-5a FILE-5b FILE-6 FILE-7 FILE-10 GOAL-3a GOAL-3c GOAL-6b GOAL-6d PROMO-3a PROMO-3b PROMO-5b CLOSE-1 CLOSE-3c ITER-1 ITER-3b ITER-6 ITER-6a ITER-6b".split()
CHANGED = {
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
}



class ChangedRulesEquivalence(unittest.TestCase):
    def test_changed_rules_same_per_shape_and_role_except_the_two_known(self):
        for key, want in CHANGED.items():
            shape, role = key.split("/")
            if role not in ("manager", "dev") and ROLE_KEY.get(role, role) not in shape_team(*SHAPE_ARGS[shape]):
                continue
            with self.subTest(key):
                text = composed(role, **SHAPES[shape])
                got = {i for i in CHANGED_IDS if re.search(r"## " + re.escape(i) + r"\b", text)}
                exp = set(want.split())
                if key == "M/manager":
                    exp = exp | {"WHO-1b"}
                self.assertEqual(sorted(got), sorted(exp))


if __name__ == "__main__":
    unittest.main()
