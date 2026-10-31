"""Instruction files (roles, process, skills, templates) must describe the per-scope layout and nothing that was removed."""
import re
import unittest

from rulesview import composed

from squadtest import ROOT
RULES = "\n".join(f.read_text() for f in sorted((ROOT / "templates/squad/process").glob("*.md")))  # the rule folder
AGENTS = sorted((ROOT / "agents").glob("*.md"))
INSTRUCTIONS = AGENTS + [ROOT / "templates/squad/project.md"] \
    + sorted((ROOT / "skills").glob("*/SKILL.md")) + sorted((ROOT / "templates/scope").rglob("*.md")) \
    + sorted((ROOT / "templates/goal").rglob("*.md"))
# Files and places that no longer exist at squad level.
STALE = ["scopes.md", "scopes-done", "$SQUAD_DIR/roster", "$SQUAD_DIR/roles", "$SQUAD_DIR/tasks", "$SQUAD_DIR/evidence",
         "$SQUAD_DIR/contracts", "$SQUAD_DIR/iterations", "$SQUAD_DIR/usage-events", "$SQUAD_DIR/goal.md", "roles/archive",
         "XL", "coach-$SQUAD", "iterations/TEMPLATE"]
# Roles used to be long-lived across a whole run; every role now lives for one scope.
AGENT_STALE = ["long-lived", "whole run", "stay for the whole"]
ALLOWED_STALE = {"templates/scope/iterations/TEMPLATE.md": ["iterations/TEMPLATE"]}


class InstructionsTest(unittest.TestCase):

    def test_no_file_refers_to_something_that_was_removed(self):
        for f in INSTRUCTIONS:
            rel = str(f.relative_to(ROOT))
            text = f.read_text()
            for token in STALE:
                if token in ALLOWED_STALE.get(rel, []):
                    continue
                self.assertNotIn(token, text, f"{rel} still mentions {token!r}")

    def test_every_scope_role_starts_by_reading_its_scope_folder(self):  # was on the cards; the start rules carry it
        for role in ("ba", "team-lead", "tech-lead", "qa-whitebox", "qa-blackbox", "designer", "dev"):
            text = composed(role, "M", goal="yes")
            self.assertIn("$SCOPE_DIR/scope.md", text, role)
            self.assertIn("$GOAL_DIR/goal.md", text, role)
            self.assertIn("shared/", text, role)
            self.assertIn("roles/$SQUAD_NAME.notes.md", text, role)

    def test_process_documents_every_variable_and_every_squad_command(self):  # old assertion on the v6 template, now on the rule folder
        text = RULES
        for token in ("SQUAD_DIR", "SCOPE_DIR", "GOAL_DIR", "squad-start", "squad-close", "squad-respawn",
                      "squad-spawn", "--base", "--in-goal", "promoted:", "shared/decisions.md", "scopes/_done"):
            self.assertIn(token, text)

    def test_every_command_an_instruction_tells_agents_to_run_exists(self):
        names = {p.name for p in (ROOT / "bin").iterdir()}
        for f in INSTRUCTIONS:
            for cmd in re.findall(r"`(squad-[a-z]+)[ `]", f.read_text()):
                self.assertIn(cmd, names, f"{f.name} runs {cmd}")
        for role in ("manager", "dev", "tech-lead", "team-lead"):
            for cmd in re.findall(r"`(squad-[a-z]+)[ `]", composed(role, "M", goal="yes")):
                self.assertIn(cmd, names, f"{role} rules run {cmd}")

    def test_the_manager_covers_both_modes_and_closes_through_squad_close(self):
        text = composed("manager", "M", goal="yes")
        for token in ("goal Manager", "squad-close <squad> --scope", "squad-close <squad> --goal", "--in-goal", "--base",
                      "promoted:", "Never read or write another scope's folder"):
            self.assertIn(token, text)

    def test_the_designer_is_wired_into_process_manager_and_scope_template(self):
        for token in ("design = yes", "ui-design/", "`ux`"):  # was `design: yes` in the v6 template
            self.assertIn(token, RULES)
        self.assertIn("\nteam:\n", (ROOT / "templates/scope/scope.md").read_text())
        self.assertIn("`designer`", composed("manager", "M", "yes"))

    def test_scope_template_lines(self):
        t = (ROOT / "templates/scope/scope.md").read_text()
        self.assertIn("\nteam:\nqa: full\n", t)
        for old in ("\nsize:", "\ndesign:", "\narchitecture:", "\nqa-b:"):
            self.assertNotIn(old, t)


class ManagerInboxTest(unittest.TestCase):
    text = composed("manager", "M")

    def test_the_inbox_bullets_carry_the_three_live_wording_rules(self):  # PI-08 AC4
        self.assertIn("One `squad-inbox add` per Bash call, never two.", self.text)  # M1
        self.assertIn("your reply is the printed line and nothing else: no body, options or recommendation", self.text)  # M2
        self.assertIn("Run `squad-inbox list` first; never answer from memory of what is open.", self.text)  # M3

    def test_every_squad_inbox_word_is_a_cli_command(self):
        words = set(re.findall(r"squad-inbox ([a-z]+)", self.text))
        self.assertTrue(words)
        self.assertLessEqual(words, {"add", "list", "read", "answer", "withdraw", "delivered", "guide"})


class CardShapeTest(unittest.TestCase):
    """Ticket 06: a card holds identity, stance and tool names; never a start step, route or citation."""

    def test_each_card_is_at_most_30_lines_after_frontmatter(self):
        for f in AGENTS:
            body = f.read_text().split("---\n", 2)[2].strip("\n").splitlines()
            self.assertLessEqual(len(body), 30, f.name)

    def test_each_card_ends_with_the_pointer_line(self):
        for f in AGENTS:
            last = f.read_text().rstrip().splitlines()[-1]
            self.assertIn(f"`roles/{f.stem}.rules.md`", last, f.name)
            self.assertIn("[CORE-3]", last, f.name)

    def test_no_card_calls_show_or_names_process_md(self):  # replaces SectionViewTest's card checks
        for f in AGENTS:
            text = f.read_text().split("---\n", 2)[2]  # frontmatter keys stay as they were
            self.assertNotIn("squad-process show", text, f.name)
            self.assertNotIn("process.md", text, f.name)

    def test_every_card_names_only_existing_tools(self):
        names = {p.name for p in (ROOT / "bin").iterdir()}
        for f in AGENTS:
            for cmd in re.findall(r"`(squad-[a-z]+)`", f.read_text()):
                self.assertIn(cmd, names, f.name)


class RuleDutiesTest(unittest.TestCase):
    """Duties that used to be asserted on card text, now on the composed rules."""

    def test_all_ten_settings_allow_rule_and_who_and_none_allows_show_or_a_wildcard(self):  # ticket 09
        import json
        files = sorted((ROOT / "templates/squad/settings").glob("*.json"))
        self.assertEqual(len(files), 10)
        for f in files:
            allow = json.loads(f.read_text())["permissions"]["allow"]
            self.assertIn("Bash(squad-process rule:*)", allow, f.name)
            self.assertIn("Bash(squad-process who:*)", allow, f.name)
            self.assertNotIn("Bash(squad-process show:*)", allow, f.name)
            self.assertNotIn("Bash(squad-process:*)", allow, f.name)

    def test_dev_writes_evidence_md_with_inline_screenshots_and_assembles_it(self):
        dev = composed("dev", "S")
        for needle in ("evidence.md", "img/", "squad-evidence add", "squad-evidence check", "evidence sha"):
            self.assertIn(needle, dev + composed("dev", "M"))

    def test_tech_lead_checks_evidence_md_and_the_evidence_sha(self):
        tl = composed("tech-lead", "L")
        self.assertIn("squad-evidence check", tl)
        self.assertIn("--base", tl)
        self.assertIn("evidence.md", tl)
        for size in "SM":  # no Tech Lead below L: the Manager checks
            self.assertIn("squad-evidence check", composed("manager", size))


if __name__ == "__main__":
    unittest.main()
