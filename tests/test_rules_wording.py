"""Rule wording and citations: sentences a composed role must carry, `[ID]` pointers that resolve, card lines.
One home for the small per-ticket files it replaces (advisor, designer, manager M/L, manager inbox, process citations)."""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rulesview import ROOT, composed, run

MANAGER = composed("manager", "M")


def rule(rid):
    return MANAGER.split(f"## {rid} ")[1].split(" ## ")[0]


class CitationsTest(unittest.TestCase):
    def test_lint_resolves_every_pointer(self):
        r = run("lint", "--plugin-root", str(ROOT))
        self.assertEqual((r.returncode, r.stdout.strip()), (0, ""), r.stdout)

    def test_an_unknown_pointer_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "plugin"
            shutil.copytree(ROOT / "templates/squad/process", root / "templates/squad/process")
            f = root / "templates/squad/process/core.md"
            f.write_text(f.read_text().replace("[WHO-1a]", "[MSG-99]"))
            r = run("lint", "--plugin-root", str(root))
        self.assertEqual(r.returncode, 1)
        self.assertIn("unknown pointer [MSG-99]", r.stdout)

    def test_third_return_notice_cites_a_real_rule(self):
        src = (ROOT / "bin" / "squad-log-message").read_text(encoding="utf-8")
        self.assertIn("consult the advisor before the next HANDIN; note it in the task file [LC-25]", src)
        r = run("rule", "LC-25")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith("## LC-25 "))

    def test_overlay_can_turn_the_advisor_off(self):
        # "" turns it off; null makes Claude Code refuse the whole settings file (probed 2026-10-22).
        def effective(tmp):
            return subprocess.run([sys.executable, str(ROOT / "bin" / "squadsettings.py"), "effective", "--role", "dev",
                                   "--squad-dir", tmp, "--template-root", str(ROOT)], capture_output=True, encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            sd = Path(tmp) / "settings"
            sd.mkdir()
            (sd / "dev.local.json").write_text(json.dumps({"advisorModel": ""}), encoding="utf-8")
            r = effective(tmp)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(json.loads(r.stdout)["advisorModel"], "")
            (sd / "dev.local.json").write_text("{}", encoding="utf-8")
            self.assertEqual(json.loads(effective(tmp).stdout)["advisorModel"], "opus")


class ManagerWordingTest(unittest.TestCase):
    def test_s_keeps_developer_spawning_and_routing(self):
        ms = composed("manager", "S")
        self.assertIn("## SPAWN-5a Developers, Manager plans", ms)
        self.assertIn("## SPAWN-5a", MANAGER)
        self.assertIn("## MSG-18 Routing, Manager", ms)
        mm = composed("manager", "L")  # Team Lead exists at L only
        self.assertNotIn("## SPAWN-5a", mm)
        self.assertNotIn("## MSG-18", mm)

    def test_manager_three_returns_rule_per_team_shape(self):
        """Every Manager gets a three-returns rule when it is the plan owner; the Team Lead's shape only hears of it."""
        from test_dev_rules_size import compose
        def ids(size):
            return set(re.findall(r"(?m)^## (LC-7[a-z]?) ", compose("manager", size).decode()))
        def body(size):
            return compose("manager", size).decode().split("## LC-7a")[1].split("\n## ")[0]
        self.assertEqual(ids("S") & {"LC-7a", "LC-7b", "LC-7c"}, {"LC-7a"})
        self.assertIn("you step in; with QAs on the team", body("S"))  # conditional, so valid with no QA
        self.assertEqual(ids("M") & {"LC-7a", "LC-7b", "LC-7c"}, {"LC-7a"})  # qa-white + qa-black, no Team Lead
        self.assertIn("with QAs on the team the 3rd failing QA sends you `BLOCKED NN: 3 returns`", body("M"))
        self.assertEqual(ids("L") & {"LC-7a", "LC-7b", "LC-7c"}, {"LC-7b"})  # aware only: the Team Lead decides

    def test_retained_duties(self):
        for token in ("Adding a role", "Merge only on the PO's request", "squad-inbox add", "Token Coach", "squad-close <squad> --scope"):
            self.assertIn(token, composed("manager", "L", goal="yes"))


class DesignerAndTaskIdWordingTest(unittest.TestCase):
    def test_consuming_roles_mention_the_design_folder(self):
        for role in ("dev", "qa-blackbox", "tech-lead"):
            self.assertIn("ui-design/", composed(role, "M", design="yes"), role)

    def test_tech_lead_keys_on_design_yes(self):
        self.assertIn("## LC-11 Design with a UI", composed("tech-lead", "L", design="yes"))
        self.assertNotIn("## LC-11 ", composed("tech-lead", "L", design="no"))

    def test_task_id_rule_text_reaches_dev_qa_and_team_lead(self):
        for role in ("dev", "qa-whitebox", "team-lead"):
            self.assertIn("the ticket number `NN` alone, never an alias or slug", composed(role, "M"))


class CardRoutesTest(unittest.TestCase):
    COMMON = ["started by the squad Manager", "the Manager's briefing", "message from the Manager"]
    ALLOW = {  # a card line that says "Manager" must carry one of these
        "team-lead.md": COMMON + ["the Manager hears from you only"], "token-coach.md": COMMON + ["the Manager decides"],
        "tech-lead.md": COMMON + ["go to the Manager"], "manager.md": [""],  # the Manager's own card
    }

    def test_every_manager_line_of_a_card_is_allowed(self):
        for p in sorted((ROOT / "agents").glob("*.md")):
            allowed = self.ALLOW.get(p.name, self.COMMON + ["unless the Manager settles a dispute"])
            for n, line in enumerate(p.read_text().splitlines(), 1):
                if "Manager" in line:
                    with self.subTest(file=p.name, line=n):
                        self.assertTrue(any(a in line for a in allowed), f"{p.name}:{n}: {line}")


class ManagerInboxWordingTest(unittest.TestCase):
    BULLET, CARRIES, CHECKIN = rule("ITER-4"), rule("ITER-5"), rule("ITER-11")  # the inbox lines moved from the card to these rules

    def test_a_note_with_nothing_to_decide_goes_through_kind_read(self):
        self.assertIn("A note with nothing to decide", self.BULLET)
        self.assertIn("goes through `squad-inbox add --kind read`", self.BULLET)

    def test_a_resolved_question_is_withdrawn(self):
        self.assertIn('`squad-inbox withdraw E<n> --reason "<why>"`), not left open', self.BULLET)

    def test_existing_rules_of_the_bullet_stay(self):
        for s in ("One `squad-inbox add` per Bash call, never two.", '`--blocks ""`', "no pipe and no unquoted heredoc"):
            self.assertIn(s, self.BULLET)

    def test_checkin_is_one_inbox_item(self):
        for s in ("squad-inbox add", "--kind read", "--kind answer"):
            self.assertIn(s, self.CHECKIN)

    def test_checkin_keeps_its_contents_and_cleanup(self):
        for s in ("evidence links", "3 returns", "open escalations", "proposed role-instruction changes",
                  "delete its row from `escalations.md`"):
            self.assertIn(s, self.CHECKIN)

    def test_carries_only_existing_sentences_stay(self):
        for s in ("Never offer a merge, push or deploy as an item", "that stays the PO's explicit request in this chat"):
            self.assertIn(s, self.CARRIES)


class WordingATest(unittest.TestCase):
    """Task 01 (fable-advisor): done means merged; attached rules; one session per run; no dead clause."""

    PROC = ROOT / "templates/squad/process"

    def text(self, name):
        return (self.PROC / name).read_text()

    def test_passed_is_not_called_done(self):
        for name, old in (("lifecycle.md", "never enough for done"), ("sizes.md", "counts as done"), ("starting.md", "Done rule"),
                          ("starting.md", "dependencies are done"), ("teams.md", "new Done"), ("spawning.md", "task is done"),
                          ("goal.md", "scope is done"), ("cost.md", "after every DONE"), ("iterations.md", "what is done")):
            with self.subTest(old=old):
                self.assertNotIn(old, self.text(name))

    def test_live_run_and_design_shots_roles_are_not_empty(self):
        for name, rid in (("review.md", "REV-5a"), ("evidence.md", "EVID-5")):
            self.assertIn(f"## {rid} ", self.text(name))
            self.assertRegex(self.text(name), rf"## {rid} [^\n]*\nroles: dev\n")

    def test_developer_session_may_run_a_queue(self):
        self.assertIn("queued run of tasks in one area", self.text("starting.md"))

    def test_no_dead_suggest_clause(self):
        for f in self.PROC.glob("*.md"):
            self.assertNotIn("never suggest it to the PO", f.read_text())


class TaskStageWordsTest(unittest.TestCase):
    """Ticket 05 (task-claim-gates): process text uses passed/merged, no confirmer, gates warn."""

    def test_no_stage_called_done_and_no_confirmer_pass(self):
        core = composed("dev", "M").split("## CORE-1 ")[1].split(" ## ")[0]
        self.assertIn("checking → passed", core)
        self.assertNotIn("→ done", core)
        rev = (ROOT / "templates/squad/process/review.md").read_text()
        self.assertIn("Send no `PASS`", rev)
        self.assertIn("never `PASS`", rev)
        lc = rule("LC-27")
        for s in ("only `merged` is done", "Gates warn, never block", "squad-task", "`squad-evidence check`"):
            self.assertIn(s, lc)
        self.assertIn("squad-task merged NN", rule("MRG-4"))


if __name__ == "__main__":
    unittest.main()
