"""The Architect: its card and settings, the rules it brings (only with `architecture: yes`), and who consumes architecture.md."""
import json
import re
import unittest

from rulesview import ROOT, acts, composed

NEW_RULES = ("SIZE-3a", "SIZE-9a", "SIZE-22a", "SIZE-23c", "SIZE-23d", "REV-22a", "WHO-2e", "SPAWN-4a", "START-4a",
             "START-5a", "START-20", "LC-11c", "LC-11d", "LC-19c", "MSG-20", "MSG-20a", "MSG-20b")
ALL_ROLES = ("manager", "ba", "team-lead", "tech-lead", "qa-whitebox", "qa-blackbox", "designer", "dev", "token-coach")


def ids(role, size, **kw):
    return re.search(r"rules: ([^#]*?)(?= ## )", composed(role, size, **kw)).group(1).split()


class CardAndSettingsTest(unittest.TestCase):
    def test_card_is_an_architect_card_without_model_or_effort(self):
        text = (ROOT / "agents/architect.md").read_text()
        head = text.split("---")[1]
        self.assertIn("name: architect", head)
        self.assertNotRegex(head, r"(?m)^(model|effort):")
        for token in ("architecture.md", "never code", "check no built code", "roles/architect.rules.md"):
            self.assertIn(token, text)

    def test_architect_may_write_only_architecture_md_and_tasks(self):
        perms = json.loads((ROOT / "templates/squad/settings/architect.json").read_text())["permissions"]
        writes = sorted(p for p in perms["allow"] if p.startswith(("Write(", "Edit(")))
        self.assertEqual(writes, ["Edit(/.claude/squads/*/scopes/*/architecture.md)", "Edit(/.claude/squads/*/scopes/*/tasks/**)",
                                  "Write(/.claude/squads/*/scopes/*/architecture.md)", "Write(/.claude/squads/*/scopes/*/tasks/**)"])
        for level in ("*/*.md", "*/goals/*/*.md", "*/settings/**"):
            self.assertIn(f"Write(/.claude/squads/{level})", perms["deny"])
        for f in ("scope", "roster", "escalations"):
            self.assertIn(f"Write(/.claude/squads/*/scopes/*/{f}.md)", perms["deny"])
        # a deny wins over an allow: none may shadow the deliverable
        self.assertNotIn("Write(/.claude/squads/*/scopes/*/*.md)", perms["deny"])
        self.assertNotIn("Edit(/.claude/squads/*/scopes/*/*.md)", perms["deny"])
        self.assertIn("Bash(squad-respawn:*)", perms["allow"])

    def test_default_model_is_sonnet_high_with_the_advisor(self):
        d = json.loads((ROOT / "templates/squad/settings/architect.json").read_text())
        self.assertEqual((d["model"], d["effortLevel"], d["advisorModel"]), ("sonnet", "high", "opus"))


class NoLeakTest(unittest.TestCase):
    def test_a_scope_without_the_flag_carries_no_architecture_rule_for_any_role(self):
        for role in ALL_ROLES:
            for size in "SML":
                if size == "S" and role in ("qa-whitebox", "qa-blackbox", "ba", "team-lead", "tech-lead"):
                    continue
                with self.subTest(role=role, size=size):
                    self.assertFalse(set(NEW_RULES) & set(ids(role, size)))
                    if role != "manager":  # the Manager's team proposal (SIZE-1) names every role, the Architect included
                        self.assertNotIn("architect", composed(role, size).lower())

    def test_the_index_of_a_scope_without_the_flag_names_no_architecture_rule(self):
        for role in ("manager", "tech-lead"):
            idx = composed(role, "L").split("## Index of other rules")[1]
            self.assertNotIn("rchitect", idx, role)

    def test_with_the_flag_the_index_lists_the_architecture_rules_not_chosen(self):
        idx = composed("manager", "L", architecture="yes").split("## Index of other rules")[1]
        self.assertIn("- SIZE-9a Architecture (architect)", idx)

    def test_the_flag_only_adds_rules(self):
        for role in ALL_ROLES:
            no, yes = ids(role, "M"), ids(role, "M", architecture="yes")
            self.assertEqual([i for i in yes if i in no], no, role)


class RulesTest(unittest.TestCase):
    def test_the_manager_carries_flag_spawn_name_lifetime_gate_and_owner_rules(self):
        for size in "SM":
            got = ids("manager", size, architecture="yes")
            for rid in ("SIZE-1", "SIZE-22", "WHO-2e", "SPAWN-4a", "START-4a", "START-5a", "LC-11c", "MSG-20"):
                self.assertIn(rid, got, (rid, size))
            self.assertNotIn("LC-11d", got)
        text = composed("manager", "M", architecture="yes")
        for token in ("| Architect |", "role-short is `arch`", "`Status: final`", "PO decides"):
            self.assertIn(token, text)

    def test_the_architect_carries_its_deliverable_and_start_rules_at_every_size(self):
        for size in "SML":
            got = ids("architect", size, architecture="yes")
            for rid in ("CORE-1", "START-6", "START-20", "SIZE-9a", "LC-25", "WHO-2e", "MSG-20"):
                self.assertIn(rid, got, (rid, size))
        text = composed("architect", "M", architecture="yes")
        for token in ("architecture.md", "Status: draft|final", "components and modules", "boundaries and seams",
                      "contracts and data shapes", "constraints", "irreversible choice", "$SCOPE_DIR/tasks/", "FILE-11", "consult the advisor"):
            self.assertIn(token, text)

    def test_the_plan_waits_for_the_architecture(self):
        self.assertEqual(acts("LC-11c", "plan-owner = manager"), ("manager",))
        self.assertEqual(acts("LC-11c", "plan-owner = team-lead"), ())
        self.assertEqual(acts("LC-11d", "plan-owner = team-lead"), ("team-lead",))
        self.assertEqual(acts("LC-11e", "tech-lead = yes"), ("tech-lead",))
        self.assertIn("`Status: final`", composed("team-lead", "L", architecture="yes"))
        self.assertIn("Split the tasks only after", composed("manager", "S", architecture="yes"))

    def test_conformance_joins_the_technical_ac_of_the_existing_checker(self):
        self.assertEqual(acts("SIZE-23c", "M"), ("qa-whitebox",))
        self.assertEqual(acts("SIZE-23d", "L"), ("tech-lead",))
        self.assertEqual(acts("SIZE-23c", "L"), ("qa-whitebox",))
        self.assertEqual(acts("REV-22a", "qa-white = no"), ("dev",))
        self.assertEqual(acts("REV-22a", "qa-white = yes"), ())
        for role, size in (("qa-whitebox", "M"), ("qa-whitebox", "L"), ("tech-lead", "L"), ("dev", "S")):
            self.assertIn("architecture.md", composed(role, size, architecture="yes"), (role, size))
        self.assertNotIn("SIZE-23c", ids("architect", "M", architecture="yes"))

    def test_the_team_follows_or_asks_the_architect_and_the_manager_decides_after_two_rounds(self):
        for role in ("manager", "qa-whitebox"):
            self.assertIn("MSG-20", ids(role, "M", architecture="yes"), role)
        self.assertIn("LC-19c", ids("dev", "M", architecture="yes"))
        self.assertIn("ASK` the Architect; unsettled after 2 rounds: the Manager", composed("dev", "M", architecture="yes"))

    def test_the_architect_proposes_irreversible_choices_and_the_po_decides(self):
        text = composed("manager", "M", architecture="yes")
        self.assertIn("Architect, then Tech Lead, then Manager propose; the PO decides every time", text)
        self.assertIn("Architect lists and recommends", text)
        self.assertIn("The PO decides", text)

    def test_nothing_in_the_architects_rules_lets_it_check_code(self):
        text = composed("architect", "L", architecture="yes")
        self.assertIn("check no built code", text)

    def test_size_text_stays_clean_for_an_absent_role(self):
        for size in "SM":
            for role in ("dev", "qa-whitebox"):
                t = composed(role, size, architecture="yes").split("## Index of other rules")[0]
                for name in ("Tech Lead", "Team Lead", "the BA"):
                    self.assertNotIn(name, t, (role, size, name))


if __name__ == "__main__":
    unittest.main()
