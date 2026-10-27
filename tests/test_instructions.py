"""Instruction files (roles, process, skills, templates) must describe the per-scope layout and nothing that was removed."""
import re
import unittest
from pathlib import Path

from rulesview import composed, run

ROOT = Path(__file__).resolve().parent.parent
AGENTS = sorted((ROOT / "agents").glob("*.md"))
INSTRUCTIONS = AGENTS + [ROOT / "templates/squad/process.md", ROOT / "templates/squad/project.md"] \
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
    def test_manager_and_dev_know_the_label_rule(self):  # now on the rules: SPAWN-7 (manager), REV/LC label rule (dev)
        manager = composed("manager", "M")
        self.assertIn("--title", manager)
        self.assertIn("squad-label --agent", manager)
        self.assertIn("squad-label", composed("dev", "M"))

    def test_project_instructions_row_names_the_team_file(self):
        rows = [r for r in (ROOT / "templates/squad/project.md").read_text().splitlines()
                if r.startswith("| Project instructions |")]
        self.assertEqual(len(rows), 1)
        self.assertIn("AGENTS.md", rows[0])
        self.assertIn("Project instructions", (ROOT / "skills/squad-init/SKILL.md").read_text())

    def test_no_file_refers_to_something_that_was_removed(self):
        for f in INSTRUCTIONS:
            rel = str(f.relative_to(ROOT))
            text = f.read_text()
            for token in STALE:
                if token in ALLOWED_STALE.get(rel, []):
                    continue
                self.assertNotIn(token, text, f"{rel} still mentions {token!r}")

    def test_no_role_is_described_as_living_beyond_its_scope(self):
        for f in AGENTS:
            for token in AGENT_STALE:
                self.assertNotIn(token, f.read_text(), f"{f.name} still mentions {token!r}")

    def test_every_scope_role_starts_by_reading_its_scope_folder(self):  # was on the cards; the start rules carry it
        for role in ("ba", "team-lead", "tech-lead", "qa-whitebox", "qa-blackbox", "designer", "dev"):
            text = composed(role, "M", goal="yes")
            self.assertIn("$SCOPE_DIR/scope.md", text, role)
            self.assertIn("$GOAL_DIR/goal.md", text, role)
            self.assertIn("shared/", text, role)
            self.assertIn("roles/$SQUAD_NAME.notes.md", text, role)

    def test_no_role_still_writes_its_notes_to_a_squad_level_roles_folder(self):
        for f in AGENTS:
            for m in re.finditer(r"`roles/\$SQUAD_NAME\.notes\.md`", f.read_text()):
                start = f.read_text()[max(0, m.start() - 12):m.start()]
                self.assertNotIn("$SQUAD_DIR/", start, f.name)

    def test_process_documents_every_variable_and_every_squad_command(self):  # v6 template, until ticket 09 retires it
        text = (ROOT / "templates/squad/process.md").read_text()
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

    def test_init_ignores_the_message_logs_when_everything_is_committed(self):
        text = (ROOT / "skills/squad-init/SKILL.md").read_text()
        option = text.split("- **Commit everything.**")[1].split("- **Ignore everything.**")[0]
        self.assertIn("*.jsonl", option)

    def test_the_manager_covers_both_modes_and_closes_through_squad_close(self):
        text = composed("manager", "M", goal="yes")
        for token in ("goal Manager", "squad-close <squad> --scope", "squad-close <squad> --goal", "--in-goal", "--base",
                      "promoted:", "Never read or write another scope's folder"):
            self.assertIn(token, text)

    def test_the_designer_is_wired_into_process_manager_and_scope_template(self):
        process = (ROOT / "templates/squad/process.md").read_text()
        for token in ("design: yes", "ui-design/", "`ux`"):
            self.assertIn(token, process)
        self.assertIn("\nteam:\n", (ROOT / "templates/scope/scope.md").read_text())
        self.assertIn("`designer`", composed("manager", "M"))

    def test_scope_template_lines(self):
        t = (ROOT / "templates/scope/scope.md").read_text()
        self.assertIn("\nteam:\nqa: full\n", t)
        for old in ("\nsize:", "\ndesign:", "\narchitecture:", "\nqa-b:"):
            self.assertNotIn(old, t)

    def test_the_architect_starts_by_reading_its_scope_folder(self):
        text = composed("architect", "M", goal="yes", architecture="yes")
        for token in ("$SCOPE_DIR/scope.md", "$GOAL_DIR/goal.md", "shared/", "roles/$SQUAD_NAME.notes.md"):
            self.assertIn(token, text)
        self.assertIn("`architect`", composed("manager", "M", architecture="yes"))
        self.assertIn("\nteam:\n", (ROOT / "templates/scope/scope.md").read_text())


class ManagerInboxTest(unittest.TestCase):
    text = composed("manager", "M")

    def test_the_manager_names_each_inbox_command_and_flag(self):
        for token in ("squad-inbox add", "--kind answer|read", "Never offer a merge, push or deploy as an item", "<<'EOF'", "(a) ", "squad-inbox answer", "--source chat", "squad-inbox withdraw",
                      '--blocks ""'):
            self.assertIn(token, self.text)

    def test_the_add_bullet_says_the_body_comes_from_a_quoted_heredoc(self):  # PI-07 AC9
        self.assertIn("body goes in a quoted heredoc, `squad-inbox add ... <<'EOF' … EOF`; no pipe and no unquoted heredoc (the body would show in chat)", self.text)

    def test_the_inbox_bullets_carry_the_three_live_wording_rules(self):  # PI-08 AC4
        self.assertIn("One `squad-inbox add` per Bash call, never two.", self.text)  # M1
        self.assertIn("your reply is the printed line and nothing else: no body, options or recommendation", self.text)  # M2
        self.assertIn("Run `squad-inbox list` first; never answer from memory of what is open.", self.text)  # M3

    def test_an_inbox_answer_is_never_a_merge_push_or_deploy_request(self):
        self.assertRegex(self.text, r"(?is)never[^.]*merge, push or deploy")
        self.assertIn("that stays the PO's explicit request in this chat", self.text)

    def test_every_squad_inbox_word_is_a_cli_command(self):
        words = set(re.findall(r"squad-inbox ([a-z]+)", self.text))
        self.assertTrue(words)
        self.assertLessEqual(words, {"add", "list", "read", "answer", "withdraw", "delivered"})


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

    def test_review_finding_4_text_is_gone(self):
        manager = (ROOT / "agents/manager.md").read_text()
        self.assertNotIn("label shape", manager)
        self.assertNotIn("(Retro)", manager)
        self.assertNotIn("escalations.md", (ROOT / "agents/tech-lead.md").read_text())

    def test_no_role_file_still_says_dev_evidence(self):
        for f in AGENTS:
            self.assertNotIn("dev-evidence", f.read_text(), f.name)

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

    def test_dev_copies_reports_to_evidence_and_sends_a_diff_check_after_a_pass(self):
        dev = composed("dev", "L")
        rev15 = run("rule", "REV-15").stdout  # 22: on demand for the Developer; the task file cites it
        self.assertIn("## REV-15 Report deliverables", composed("tech-lead", "L"))
        self.assertIn("## REV-15 Report deliverables", composed("manager", "S"))
        self.assertIn("evidence/<task>/", rev15)
        self.assertIn("handed in", rev15)
        after = dev.split("## REV-14b")[1].split("##")[0]
        self.assertIn("diff check", after)
        self.assertIn("both QAs", after)

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

    def test_qas_write_findings_to_scope_evidence_and_embed_screenshots(self):
        for name in ("qa-whitebox", "qa-blackbox"):
            text = composed(name, "M")
            self.assertIn("$SCOPE_DIR/evidence/", text, name)
            self.assertIn("![alt](path)", text, name)

    def test_manager_and_team_lead_link_each_tickets_evidence_md(self):
        for name in ("manager", "team-lead"):
            self.assertIn("evidence.md", composed(name, "M"), name)


# Old name -> new name (ticket 06 assertion map; SectionViewTest is retired with `squad-process show`):
#   SectionViewTest.test_each_section_role_runs_its_own_show_command            deleted: cards no longer call show (CardShapeTest.test_no_card_calls_show_or_names_process_md)
#   SectionViewTest.test_other_roles_do_not_use_show                            CardShapeTest.test_no_card_calls_show_or_names_process_md
#   SectionViewTest.test_the_fallback_sentence_names_exactly_the_role_view      deleted: the fallback sentence is gone with `show`
#   SectionViewTest.test_every_citation_is_in_the_role_view_or_listed_as_outside_it   deleted: [ID] pointers are linted (test_process_citations)
#   SectionViewTest.test_show_is_allowed_for_exactly_the_four_roles_...          RuleDutiesTest.test_all_nine_settings_allow_rule_and_who_... (ticket 09: show retired)
#   SectionViewTest.test_dev_copies_reports_...                                  RuleDutiesTest.test_dev_copies_reports_...
#   SectionViewTest.test_dev_writes_evidence_md_...                              RuleDutiesTest.test_dev_writes_evidence_md_...
#   SectionViewTest.test_tech_lead_checks_evidence_md_...                        RuleDutiesTest.test_tech_lead_checks_evidence_md_...
#   SectionViewTest.test_qas_write_findings_...                                  RuleDutiesTest.test_qas_write_findings_...
#   SectionViewTest.test_manager_and_team_lead_link_...                          RuleDutiesTest.test_manager_and_team_lead_link_...
#   SectionViewTest.test_no_role_file_still_says_dev_evidence                    CardShapeTest.test_no_role_file_still_says_dev_evidence


if __name__ == "__main__":
    unittest.main()
