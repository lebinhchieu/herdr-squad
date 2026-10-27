"""squadcompose: overlay, facts, composed rules, `rule` and `who` (ticket 04), on fixtures/rules/compose."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
FIX = Path(__file__).resolve().parent / "fixtures" / "rules" / "compose"
sys.path.insert(0, str(BIN))
import squadcompose as sc  # noqa: E402

NOW = "2026-10-22T10:00:00Z"
RUNNING = sc.running_version()
PIN_V = "9.9.9"  # fixed pin version for goldens; PinTest uses RUNNING where the version check matters
PROC = "templates/squad/process"


def cli(*args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("SQUAD_")}
    return subprocess.run([sys.executable, str(BIN / "squad-process"), *args],
                          capture_output=True, encoding="utf-8", env=env)


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.root = self.tmp / "plugin"
        shutil.copytree(FIX, self.root, ignore=shutil.ignore_patterns("golden"))
        self.squad = self.root / "squad"
        self.overlay_path = self.squad / "process.local.md"

    def home(self, size="M", design="no", goal="no", pin=f"{PIN_V} abc1234", extra="", name="scope-a"):
        h = self.tmp / "scopes" / name
        h.mkdir(parents=True, exist_ok=True)
        lines = [f"goal: {goal}" if goal != "no" else "goal:"]
        if size:
            lines.append(f"size: {size}")
        lines += ["qa: full", f"design: {design}"]
        if pin:
            lines.append(f"plugin: {pin}")
        (h / "scope.md").write_text("\n".join(lines) + "\n" + extra, encoding="utf-8", newline="\n")
        return h

    def goal_home(self):
        h = self.tmp / "goals" / "g1"
        h.mkdir(parents=True, exist_ok=True)
        (h / "goal.md").write_text(f"# Goal\n\nplugin: {PIN_V} abc1234\n", encoding="utf-8", newline="\n")
        return h

    def overlay(self, text):
        self.overlay_path.write_text(text, encoding="utf-8", newline="\n")

    def compose(self, role, home, **kw):
        return sc.compose(role, str(home), str(self.root), str(self.overlay_path), kw.get("agent", role), NOW,
                          kw.get("pinned", (PIN_V, "abc1234")))

    def run_cli(self, *args, home=None, squad=True, root=True):
        cmd = list(args)
        if home is not None:
            cmd += ["--home", str(home)]
        if squad:
            cmd += ["--squad-dir", str(self.squad)]
        if root:
            cmd += ["--plugin-root", str(self.root)]
        return cli(*cmd)

    def ids(self, role, home):
        text = self.compose(role, home)
        return next(ln for ln in text.split("\n") if ln.startswith("rules:"))[len("rules: "):].split()


class GoldenTest(Base):
    def check(self, name, text):
        golden = FIX / "golden" / name
        self.assertEqual(text, golden.read_text(encoding="utf-8"))

    def test_golden_dev_replaced_added_aware(self):
        self.check("dev-M-design.rules.md", self.compose("dev", self.home(design="yes"), agent="dev-1"))

    def test_golden_goal_manager_if_tags_and_index(self):
        self.check("manager-goal.rules.md", self.compose("manager", self.goal_home(), agent="mgr"))

    def test_file_ends_with_exactly_one_newline(self):
        t = self.compose("dev", self.home())
        self.assertTrue(t.endswith("\n") and not t.endswith("\n\n"))


class OverlayFailTest(Base):
    def test_stale_replace_exits_2_names_both_hashes_and_writes_nothing(self):
        self.overlay(self.overlay_path.read_text(encoding="utf-8").replace("@203fa130", "@7f3a9c21"))
        out = self.tmp / "roles" / "dev.rules.md"
        r = self.run_cli("compose", "dev", "--out", str(out), "--now", NOW, home=self.home())
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("REV-3: overlay written for @7f3a9c21, plugin now @203fa130", r.stderr)
        self.assertFalse(out.exists())
        self.assertFalse(out.parent.exists())

    def test_stale_with_existing_out_keeps_its_bytes(self):
        self.overlay(self.overlay_path.read_text(encoding="utf-8").replace("@203fa130", "@7f3a9c21"))
        out = self.tmp / "keep.md"
        out.write_bytes(b"old bytes\n")
        r = self.run_cli("compose", "dev", "--out", str(out), "--now", NOW, home=self.home())
        self.assertEqual(r.returncode, 2)
        self.assertEqual(out.read_bytes(), b"old bytes\n")

    def test_every_stale_op_is_listed_one_line_each(self):
        self.overlay("## replace REV-3 @11111111\nwhy: a\nupstream: local-only\nNew body one.\n\n"
                     "## remove MSG-1 @22222222\nwhy: b\nupstream: local-only\n")
        r = self.run_cli("compose", "dev", home=self.home())
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stderr.strip().split("\n"),
                         ["REV-3: overlay written for @11111111, plugin now @203fa130",
                          "MSG-1: overlay written for @22222222, plugin now @76ede794"])

    def test_remove_of_missing_id_exits_2_naming_it(self):
        self.overlay("## remove REV-99 @203fa130\nwhy: a\nupstream: local-only\n")
        r = self.run_cli("compose", "dev", home=self.home())
        self.assertEqual(r.returncode, 2)
        self.assertIn("REV-99", r.stderr)

    def test_replace_of_missing_id_exits_2_naming_it(self):
        self.overlay("## replace REV-99 @203fa130\nwhy: a\nupstream: local-only\nBody.\n")
        r = self.run_cli("compose", "dev", home=self.home())
        self.assertEqual((r.returncode, "REV-99" in r.stderr), (2, True))

    def test_add_of_existing_id_exits_2_naming_it(self):
        self.overlay("## add REV-3 Again\nroles: dev\ntopic: review\nwhy: a\nupstream: local-only\nBody.\n")
        r = self.run_cli("compose", "dev", home=self.home())
        self.assertEqual(r.returncode, 2)
        self.assertIn("REV-3", r.stderr)

    def test_parse_problem_in_the_plugin_rules_exits_2(self):
        p = self.root / PROC / "review.md"
        p.write_text(p.read_text(encoding="utf-8") + "\n## not a rule heading\ntext\n", encoding="utf-8", newline="\n")
        r = self.run_cli("compose", "dev", home=self.home())
        self.assertEqual(r.returncode, 2)
        self.assertIn("review.md", r.stderr)

    def test_remove_drops_the_rule_and_the_index_line(self):
        self.overlay("## remove MSG-1 @76ede794\nwhy: a\nupstream: local-only\n")
        self.assertNotIn("MSG-1", self.ids("manager", self.home()))
        self.assertNotIn("MSG-1", self.compose("tech-lead", self.home()))

    def test_replace_can_retarget_roles(self):
        self.overlay("## replace REV-8 @fc3d3687\nroles: qa-blackbox\nwhy: a\nupstream: local-only\n"
                     "The QA saves one screenshot per design state.\n")
        h = self.home(design="yes")
        self.assertIn("REV-8", self.ids("qa-blackbox", h))
        self.assertNotIn("REV-8", self.ids("dev", h))


class NoRulesTest(Base):
    def test_plugin_without_rule_files_exits_2_not_a_traceback(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        for args in (("compose", "dev", "--home", str(self.home())), ("rule", "CORE-1"), ("who", "CORE-1")):
            with self.subTest(args=args):
                r = cli(*args, "--plugin-root", str(empty), "--squad-dir", str(self.squad))
                self.assertEqual(r.returncode, 2)
                self.assertIn("no rule files", r.stderr)
                self.assertNotIn("Traceback", r.stderr)

    def test_template_folder_missing_exits_2(self):
        shutil.rmtree(self.root / PROC)
        self.assertEqual(self.run_cli("rule", "CORE-1").returncode, 2)


class DeterminismTest(Base):
    def test_repeat_runs_are_byte_identical(self):
        h = self.home()
        a = self.run_cli("compose", "tech-lead", "--now", NOW, home=h).stdout
        b = self.run_cli("compose", "tech-lead", "--now", NOW, home=h).stdout
        self.assertTrue(a)
        self.assertEqual(a, b)

    def test_crlf_inputs_give_the_same_bytes(self):
        h = self.home(design="yes")
        lf = self.run_cli("compose", "manager", "--now", NOW, home=h)
        for p in list(self.root.rglob("*.md")) + [h / "scope.md"]:
            p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
        crlf = self.run_cli("compose", "manager", "--now", NOW, home=h)
        self.assertEqual((lf.returncode, crlf.returncode), (0, 0), crlf.stderr)
        self.assertEqual(lf.stdout.encode(), crlf.stdout.encode())

    def test_out_file_has_lf_only_and_creates_the_folder(self):
        out = self.tmp / "roles" / "a.rules.md"
        r = self.run_cli("compose", "dev", "--out", str(out), "--now", NOW, home=self.home())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")
        data = out.read_bytes()
        self.assertNotIn(b"\r", data)
        self.assertTrue(data.startswith(b"# Your process rules\n"))


class FactsMatrixTest(Base):
    def test_matrix_role_size_design(self):
        core = "CORE-1"
        cases = {
            ("dev", "S", "no"): [core, "REV-7a"],
            ("dev", "M", "no"): [core, "REV-3"],
            ("dev", "M", "yes"): [core, "REV-3", "REV-8"],
            ("dev", "L", "yes"): [core, "REV-3", "REV-8"],
            ("tech-lead", "S", "no"): [core, "REV-7a"],
            ("tech-lead", "M", "no"): [core],
            ("qa-whitebox", "S", "no"): [core],
            ("qa-whitebox", "M", "yes"): [core, "REV-3", "REV-7b"],
            ("qa-blackbox", "L", "no"): [core, "REV-3", "REV-7b"],
            ("manager", "S", "no"): [core, "MSG-1", "MSG-2a"],
            ("manager", "L", "no"): [core, "MSG-1", "MSG-2b"],
            ("team-lead", "M", "no"): [core, "REV-3"],
            ("ba", "M", "no"): [core],
        }
        self.overlay("")
        for (role, size, design), want in cases.items():
            with self.subTest(role=role, size=size, design=design):
                self.assertEqual(self.ids(role, self.home(size=size, design=design)), want)

    def test_size_variant_absent_at_m_and_design_rule_absent_without_design(self):
        self.assertNotIn("REV-7a", self.ids("tech-lead", self.home(size="M")))
        self.assertNotIn("REV-8", self.ids("dev", self.home(size="M", design="no")))

    def test_goal_manager_gets_both_variants(self):
        got = self.ids("manager", self.goal_home())
        self.assertEqual(got, ["CORE-1", "MSG-1", "MSG-2a", "MSG-2b"])  # MSG-3 (design = yes) is not among them
        self.assertIn("MSG-3", self.ids("manager", self.home(design="yes")))

    def test_goal_manager_titles_carry_if_tags_only_for_missing_facts(self):
        t = self.compose("manager", self.goal_home())
        self.assertIn("## MSG-2a Manager reports to the Team Lead [if size = S]\n", t)
        self.assertIn("## MSG-2b Manager reports through the Team Lead [if size in M, L]\n", t)
        self.assertIn("## MSG-1 Manager owns the PO channel\n", t)
        self.assertNotIn("[if", self.compose("manager", self.home(size="S")))

    def test_scope_with_goal_line_has_goal_yes_and_header_facts(self):
        t = self.compose("dev", self.home(size="L", design="yes", goal="composed-process"))
        self.assertIn("(size L, design yes, qa full, goal yes)", t)

    def test_header_of_goal_manager_prints_undecided_team_defaults_and_goal_name(self):
        t = self.compose("manager", self.goal_home(), agent="mgr")
        self.assertIn("agent: mgr · role: manager · scope: goal g1 · team: undecided (design no, qa full, goal yes)", t)
        self.assertIn("\nduties: undecided\n", t)

    def test_size_token_is_first_upper_case_sml(self):
        h = self.home(size="M (confirmed)")
        self.assertIn("size M,", self.compose("dev", h))
        h = self.home(size="small")
        self.assertIn("size n/a,", self.compose("dev", h))

    def test_invalid_design_value_exits_2_naming_the_line(self):
        h = self.home(design="maybe")
        r = self.run_cli("compose", "dev", home=h)
        self.assertEqual(r.returncode, 2)
        self.assertIn("scope.md:", r.stderr)
        self.assertIn("design", r.stderr)

    def test_architecture_header_shown_when_yes_and_absent_line_header_unchanged(self):
        t = self.compose("dev", self.home())
        self.assertNotIn("architecture", t.split("\n")[1])
        self.assertIn("(size M, design no, qa full, goal no)", t)
        self.assertIn("(size M, design no, architecture yes, qa full, goal no)",
                      self.compose("dev", self.home(extra="architecture: yes\n")))
        self.assertIn("architecture yes,", self.compose("dev", self.home(extra="architecture: yes\n")))

    def test_invalid_architecture_value_exits_2_naming_the_line(self):
        h = self.home(extra="architecture: maybe\n")
        r = self.run_cli("compose", "dev", home=h)
        self.assertEqual(r.returncode, 2)
        self.assertIn("scope.md:", r.stderr)
        self.assertIn("architecture", r.stderr)

    def test_goal_home_takes_architecture_default_no(self):
        t = self.compose("manager", self.goal_home(), agent="mgr")
        self.assertNotIn("architecture", t.split("\n")[1])
        self.overlay("## add SQ-2 Arch rule\nroles: manager\nwhen: architecture = yes\ntopic: review\nwhy: a\nupstream: local-only\nBody.\n")
        self.assertNotIn("SQ-2", self.ids("manager", self.goal_home()))  # a missing fact would keep it

    def test_when_architecture_rule_kept_only_when_fact_matches(self):
        self.overlay("## add SQ-2 Arch rule\nroles: dev\nwhen: architecture = yes\ntopic: review\nwhy: a\nupstream: local-only\nBody.\n"
                     "\n## add SQ-3 No arch rule\nroles: dev\nwhen: architecture = no\ntopic: review\nwhy: a\nupstream: local-only\nBody.\n")
        yes = self.ids("dev", self.home(extra="architecture: yes\n"))
        no = self.ids("dev", self.home(extra="architecture: no\n"))
        absent = self.ids("dev", self.home())
        self.assertIn("SQ-2", yes)
        self.assertNotIn("SQ-3", yes)
        self.assertIn("SQ-3", no)
        self.assertNotIn("SQ-2", no)
        self.assertEqual(absent, no)

    def test_unknown_role_exits_2(self):
        self.assertEqual(self.run_cli("compose", "wizard", home=self.home()).returncode, 2)

    def test_index_only_for_manager_and_tech_lead(self):
        h = self.home()
        for role in ("manager", "tech-lead"):
            self.assertIn("## Index of other rules\n", self.compose(role, h))
        for role in ("dev", "qa-whitebox", "ba", "team-lead", "qa-blackbox"):
            self.assertNotIn("Index of other rules", self.compose(role, h))

    def test_index_line_shape_and_order(self):
        t = self.compose("tech-lead", self.home(size="S"))
        idx = t.split("## Index of other rules\n")[1].rstrip("\n").split("\n")
        self.assertEqual(idx[0], "- MSG-1 Manager owns the PO channel (manager)")
        self.assertIn("- REV-3 One verdict per final sha (qa-whitebox, qa-blackbox)", idx)
        self.assertEqual(idx[-1], "- SQ-1 Style contract (tech-lead)")  # added rules come after plugin rules


class TagsTest(Base):
    def test_aware_tag_on_aware_only_rules(self):
        t = self.compose("dev", self.home(size="M"))
        self.assertIn("## REV-3 One verdict per final sha [aware] [squad: replaced]\n", t)
        self.assertIn("## CORE-1 Task states\n", t)

    def test_source_tags_exactly_on_overlay_touched_rules(self):
        t = self.compose("tech-lead", self.home(size="M"))
        tagged = [ln for ln in t.split("\n") if ln.startswith("## ") and "[squad:" in ln]
        self.assertEqual(tagged, ["## SQ-1 Style contract [squad: added]"])
        t = self.compose("qa-whitebox", self.home(size="M"))
        tagged = [ln for ln in t.split("\n") if ln.startswith("## ") and "[squad:" in ln]
        self.assertEqual(tagged, ["## REV-3 One verdict per final sha [squad: replaced]"])

    def test_tag_order_is_aware_if_squad(self):
        self.overlay("## replace MSG-2a @%s\nwhy: a\nupstream: local-only\nAware body.\n" % self.hash("MSG-2a"))
        self.overlay(self.overlay_path.read_text(encoding="utf-8").replace(
            "Aware body.", "roles: tech-lead\naware: manager\nAware body."))
        t = self.compose("manager", self.goal_home())
        self.assertIn("## MSG-2a Manager reports to the Team Lead [aware] [if size = S] [squad: replaced]\n", t)

    def hash(self, rid):
        r = cli("lint", "--hashes", "--plugin-root", str(self.root))
        return next(ln.split()[1] for ln in r.stdout.split("\n") if ln.startswith(rid + " "))

    def test_no_tags_without_overlay(self):
        self.overlay("")
        self.assertNotIn("[squad:", self.compose("tech-lead", self.home()))

    def test_header_counts_every_overlay_op_whatever_the_role(self):
        t = self.compose("ba", self.home())
        self.assertIn("overlay: 2 operations applied", t)

    def test_header_without_overlay_file_is_zero_ops(self):
        self.overlay_path.unlink()
        self.assertIn("overlay: 0 operations applied", self.compose("dev", self.home()))


class RuleAndWhoTest(Base):
    def test_rule_prints_the_effective_rule_with_its_tag(self):
        r = self.run_cli("rule", "REV-3")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "## REV-3 One verdict per final sha [squad: replaced]\n"
                                   "The Tech Lead names one final sha per task; each QA gives one verdict on that sha.\n")

    def test_rule_of_a_plugin_rule_has_no_tag_and_no_role_tags(self):
        r = self.run_cli("rule", "REV-7a")
        self.assertTrue(r.stdout.startswith("## REV-7a Tech Lead reviews alone\n"), r.stdout)

    def test_rule_of_an_added_rule(self):
        r = self.run_cli("rule", "SQ-1")
        self.assertTrue(r.stdout.startswith("## SQ-1 Style contract [squad: added]\n"), r.stdout)

    def test_unknown_rule_exits_2_naming_it(self):
        r = self.run_cli("rule", "REV-404")
        self.assertEqual(r.returncode, 2)
        self.assertIn("REV-404", r.stderr)

    def test_who_lists_acting_and_aware_roles_per_size(self):
        r = self.run_cli("who", "REV-3")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.split("\n")[:3], [
            "S: acts: -; aware: -",
            "M: acts: qa-whitebox, qa-blackbox; aware: dev, team-lead",
            "L: acts: qa-whitebox, qa-blackbox; aware: dev, team-lead"])

    def test_who_for_a_size_s_rule(self):
        r = self.run_cli("who", "REV-7a")
        self.assertEqual(r.stdout.split("\n")[:3], [
            "S: acts: tech-lead; aware: dev", "M: acts: -; aware: -", "L: acts: -; aware: -"])

    def test_who_unknown_exits_2(self):
        self.assertEqual(self.run_cli("who", "REV-404").returncode, 2)

    def test_rule_with_a_stale_overlay_exits_2(self):
        self.overlay(self.overlay_path.read_text(encoding="utf-8").replace("@203fa130", "@7f3a9c21"))
        self.assertEqual(self.run_cli("rule", "REV-3").returncode, 2)


class PinTest(Base):
    def test_no_pin_warns_and_prints_unpinned(self):
        r = self.run_cli("compose", "dev", "--now", NOW, home=self.home(pin=None))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("pin", r.stderr)
        self.assertIn(f"plugin: {RUNNING} unpinned · overlay:", r.stdout)

    def test_pin_prints_version_and_sha(self):
        r = self.run_cli("compose", "dev", "--now", NOW, home=self.home(pin="0.3.0 deadbeef"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("plugin: 0.3.0 deadbeef · overlay:", r.stdout)

    def test_pin_of_another_version_without_plugin_root_exits_2(self):
        r = cli("compose", "dev", "--home", str(self.home(pin="0.0.1 deadbeef")), "--squad-dir", str(self.squad))
        self.assertEqual(r.returncode, 2)
        self.assertIn("--plugin-root", r.stderr)

    def test_unparseable_pin_exits_2(self):
        r = self.run_cli("compose", "dev", home=self.home(pin="justoneword"))
        self.assertEqual(r.returncode, 2)

    def test_goal_home_pin_is_read_from_goal_md(self):
        r = self.run_cli("compose", "manager", "--now", NOW, home=self.goal_home())
        self.assertIn(f"plugin: {PIN_V} abc1234 ·", r.stdout)


# Real `scope.md` lines, copied verbatim (file:line cited per sample; paths under /home/chieule/workspace/).
REAL = {
    # squad/.claude/squads/plugin-bk261023/scopes/_done/refine-process/scope.md:7
    "refine": "size: M, custom pod (PO 2026-10-14): Tech Lead, BA, QA whitebox, Devs; no QA blackbox. Behaviour check: Dev saves evidence "
              "(dev-evidence.md, migration run on a copy of a real squad), QA whitebox checks it. Done = QA whitebox PASS (+ BA sign-off "
              "on the process.md rule audit). Signals: 4-5 tasks, one repo, no UI, changes the contract every squad reads",
    # squad/.claude/squads/plugin-bk261023/scopes/_done/extractor-role/scope.md:8 and :9
    "extractor": "size: M (PO confirmed 2026-10-17, no QA roles) - signals: research spike gates a build of ~4-5 tasks; new role every squad "
                 "sees (role instructions + process.md change need PO approval); one repo; no DB/API risk flag",
    "extractor-qa": "qa: none (PO 2026-10-17): code/test and behaviour checks move to the Tech Lead as in S (tl-review.md, dev-evidence.md)",
    # enhanced-markdown-vscode/.claude/squads/blueprint/scopes/_done/svgdraw/scope.md:7 (design: yes is line 9)
    "svg-l": "size: L \u2014 confirmed by PO (E1 a). Signals: AI-authored SVG in webview = security flag; form is a business question; "
             "user-visible; touches skills/, syntaxes/, validate.mjs",
    # plugin-bk261023 scopes/_done/report-ui-fix/scope.md:7 (the `size: M \u2014 signals:` shape; svgdraw has no such line)
    "m-signals": "size: M \u2014 signals: user-visible UI change, ~5 tasks, one repo, no risk flag, PO requires full QA blackbox (confirmed by PO 2026-10-19, E1)",
}
# enhanced-markdown-vscode/.claude/squads/blueprint/scopes/grillui/scope.md:7-10
GRILLUI = ["size: M", "qa: full", "qa-b: yes", "design: yes"]


class TeamHomeTest(Base):
    def team_home(self, team_line="team: qa-white, qa-black", extra="", name="t1", newline="\n"):
        h = self.tmp / "scopes" / name
        h.mkdir(parents=True, exist_ok=True)
        text = "\n".join(x for x in (team_line, "qa: full", "goal:", f"plugin: {PIN_V} abc1234") if x) + "\n" + extra
        (h / "scope.md").write_bytes(text.replace("\n", newline).encode("utf-8"))
        return h

    def test_decided_team_fills_every_team_fact_and_no_missing_one(self):
        info = sc.read_home(self.team_home("team: ba, qa-white  (PO 2026-10-27)"))
        self.assertEqual((info["team"], info["team_source"]), (["ba", "qa-white"], "team"))
        for key in list(sc.sr.PRESENCE_KEY.values()) + list(sc.sr.DUTIES):
            self.assertIn(key, info["facts"], key)
        self.assertEqual(info["facts"]["qa-black"], "no")
        self.assertEqual(info["facts"]["business-ac"], "ba")
        self.assertEqual(info["facts"]["handin-target"], "qas")

    def test_team_none_is_decided_and_empty(self):
        info = sc.read_home(self.team_home("team: none"))
        self.assertEqual((info["team"], info["team_source"]), ([], "team"))
        self.assertEqual(info["facts"]["plan-owner"], "manager")
        self.assertEqual(info["facts"]["code-check"], "manager")

    def test_blank_team_is_undecided_with_no_team_fact(self):
        info = sc.read_home(self.team_home("team:"))
        self.assertEqual((info["team"], info["team_source"]), (None, "undecided"))
        self.assertNotIn("plan-owner", info["facts"])
        self.assertNotIn("ba", info["facts"])

    def test_no_team_line_and_no_old_line_is_hand_made_undecided(self):
        info = sc.read_home(self.team_home(""))
        self.assertEqual((info["team"], info["team_source"]), (None, "undecided"))

    def test_undecided_manager_header_and_decided_team_has_no_missing_team_fact(self):
        self.assertIn("duties: undecided", self.compose("manager", self.team_home("team:")))
        facts = sc.read_home(self.team_home("team: ba, qa-white"))["facts"]
        self.assertEqual([k for k in list(sc.sr.PRESENCE_KEY.values()) + list(sc.sr.DUTIES) if k not in facts], [])

    def test_old_line_beside_team_is_an_error_naming_each_line(self):
        # Transitional until 04a-06: a team home has no `size` fact while rule files still key on size.
        for nl in ("\n", "\r\n"):
            with self.subTest(newline=nl):
                h = self.team_home("team: ba", extra="size: M\ndesign: no\narchitecture: no\nqa-b: yes\n",
                                   newline=nl)
                with self.assertRaises(sc.ComposeError) as cm:
                    sc.read_home(h)
                self.assertEqual(len(cm.exception.lines), 4)
                for key, n in (("size", 5), ("design", 6), ("architecture", 7), ("qa-b", 8)):
                    self.assertIn(f"scope.md:{n}: old line `{key}:` beside `team:`; the team line decides, "
                                  "delete the old line by hand", cm.exception.lines)
                r = self.run_cli("compose", "manager", home=h)
                self.assertEqual(r.returncode, 2)
                self.assertIn("old line `size:` beside `team:`", r.stderr)
                self.assertNotIn("adopt", r.stderr)

    def test_bad_team_lines_exit_2_naming_line_and_token(self):
        cases = (("team: ba, ba", "scope.md:1", "'ba'"), ("team: ba, wizard", "scope.md:1", "'wizard'"),
                 ("team: manager", "scope.md:1", "'manager'"), ("team: qa-whitebox", "scope.md:1", "'qa-white'"),
                 ("team: qa-blackbox, ba", "scope.md:1", "'qa-black'"), ("team: dev", "scope.md:1", "'dev'"))
        for line, where, token in cases:
            with self.subTest(line=line):
                h = self.team_home(line)
                with self.assertRaises(sc.ComposeError) as cm:
                    sc.read_home(h)
                self.assertIn(where, cm.exception.lines[0])
                self.assertIn(token, cm.exception.lines[0])
                r = self.run_cli("compose", "manager", home=h)  # AC 30
                self.assertEqual(r.returncode, 2)
                self.assertIn(where, r.stderr)
                self.assertIn(token, r.stderr)

    def test_error_line_number_is_the_team_line(self):
        h = self.tmp / "scopes" / "ln"
        h.mkdir(parents=True)
        (h / "scope.md").write_text("# Scope\n\ngoal:\nteam: ba, zz\n", encoding="utf-8")
        with self.assertRaises(sc.ComposeError) as cm:
            sc.read_home(h)
        self.assertTrue(cm.exception.lines[0].startswith("scope.md:4:"), cm.exception.lines)

    def test_crlf_file_reads_the_same(self):
        for line, want in (("team: ba, qa-white", ["ba", "qa-white"]), ("team: none", []), ("team:", None)):
            with self.subTest(line=line):
                self.assertEqual(sc.read_home(self.team_home(line, newline="\r\n", name="c"))["team"], want)
                self.assertEqual(sc.read_home(self.team_home(line, name="c"))["team"], want)

    def test_cli_compose_of_a_team_home_exits_0(self):
        r = self.run_cli("compose", "manager", "--now", NOW, home=self.team_home("team: ba, qa-white"))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_header_index_roles_print_team_and_duties_others_do_not(self):
        h = self.team_home("team: ba, qa-white")
        for role in ("manager", "team-lead", "tech-lead"):
            with self.subTest(role=role):
                lines = self.compose(role, h).split("\n")
                self.assertIn("· team: ba, qa-white (design no, qa full, goal no)", lines[1])
                self.assertTrue(lines[3].startswith("duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, "
                                                    "business-ac=ba, "), lines[3])
                self.assertTrue(lines[4].startswith("rules: "))
        for role in ("dev", "qa-whitebox", "ba", "designer", "token-coach"):
            with self.subTest(role=role):
                t = self.compose(role, h)
                self.assertNotIn("team:", t.split("\n")[1])
                self.assertNotIn("duties:", "\n".join(t.split("\n")[:5]))
                self.assertIn("scope: t1 (design no, qa full, goal no)", t)

    def test_header_team_text_for_none_and_undecided(self):
        self.assertIn("· team: none (", self.compose("manager", self.team_home("team: none")).split("\n")[1])
        self.assertIn("· team: undecided (", self.compose("manager", self.team_home("team:")).split("\n")[1])
        self.assertIn("duties: plan-owner=manager,", self.compose("manager", self.team_home("team: none")))

    def test_duties_line_lists_all_thirteen_in_table_order(self):
        line = next(x for x in self.compose("tech-lead", self.team_home("team: designer")).split("\n") if x.startswith("duties:"))
        names = [part.split("=")[0] for part in line[len("duties: "):].split(", ")]
        self.assertEqual(names, list(sc.sr.DUTIES))
        self.assertIn("ui-check=manager", line)

    def test_design_and_architecture_facts_follow_the_team(self):
        t = self.compose("dev", self.team_home("team: designer, architect"))
        self.assertIn("(design yes, architecture yes, qa full, goal no)", t)

    def test_duties_of_a_team_home_equal_the_old_size_owners(self):
        """Hard-coded from the base SIZE-22 text (see test_team_duties.OLD): L plan-owner team-lead, M handin qas."""
        info = sc.read_home(self.team_home("team: ba, team-lead, tech-lead, qa-white, qa-black"))
        self.assertEqual((info["facts"]["plan-owner"], info["facts"]["business-ac"], info["facts"]["doubt-owner"]),
                         ("team-lead", "ba", "ba"))
        info = sc.read_home(self.team_home("team: qa-white, qa-black", name="m"))
        self.assertEqual((info["facts"]["plan-owner"], info["facts"]["tech-ac"], info["facts"]["handin-target"]),
                         ("manager", "qa-white", "qas"))


class LegacyScaffoldTest(Base):
    def old_home(self, *lines, name="old"):
        h = self.tmp / "scopes" / name
        h.mkdir(parents=True, exist_ok=True)
        (h / "scope.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return h

    def test_size_home_keeps_the_old_path_and_header_without_the_scaffold(self):
        h = self.old_home("size: M", "design: no", "qa-b: yes", "qa: full")
        info = sc.read_home(h)
        self.assertEqual((info["team"], info["team_source"], info["facts"]["size"]), (None, "size", "M"))
        self.assertNotIn("plan-owner", info["facts"])
        self.assertIn("(size M, design no, qa full, goal no)", self.compose("manager", h))
        self.assertNotIn("duties:", self.compose("manager", h))

    def test_scaffold_fills_duty_facts_from_legacy_team(self):
        for sizes, want in (("S", []), ("M", ["qa-white", "qa-black"]), ("L", ["ba", "team-lead", "tech-lead", "qa-white", "qa-black"])):
            with self.subTest(size=sizes):
                info = sc.read_home(self.old_home(f"size: {sizes}", "qa: full"), legacy_scaffold=True)
                self.assertEqual((info["team"], info["team_source"]), (want, "size"))
                self.assertEqual(info["facts"], {**info["facts"], **sc.sr.team_facts(want)})
                self.assertEqual(info["facts"]["size"], sizes)

    def test_scaffold_with_qa_b_no_and_design(self):
        info = sc.read_home(self.old_home("size: M", "qa-b: no"), legacy_scaffold=True)
        self.assertEqual(info["team"], ["qa-white"])
        self.assertEqual(info["facts"]["behaviour-check"], "qa-white")

    def test_scaffold_blank_size_gives_no_team_and_no_duty_fact(self):
        info = sc.read_home(self.old_home("size:", "qa: full"), legacy_scaffold=True)
        self.assertEqual((info["team"], info["team_source"]), (None, "size"))
        self.assertNotIn("plan-owner", info["facts"])

    def test_cli_compose_never_uses_the_scaffold(self):
        h = self.old_home("size: L", "qa: full", f"plugin: {PIN_V} abc1234")
        for path in list(BIN.iterdir()) + list((ROOT / "hooks").rglob("*")):  # nothing outside tests sets it
            if path.is_file() and path.name != "squadcompose.py" and path.suffix not in (".pyc", ".png"):
                try:
                    text = path.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    continue
                self.assertNotIn("legacy_scaffold", text, str(path))
        r = self.run_cli("compose", "manager", "--now", NOW, home=h)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("(size L,", r.stdout)

    def test_real_samples_read_home_takes_sml_anywhere_legacy_team_first_token(self):
        for key, want_size, want_team in (("refine", "M", ["qa-white", "qa-black"]), ("extractor", "M", ["qa-white", "qa-black"]),
                                          ("svg-l", "L", ["ba", "team-lead", "tech-lead", "qa-white", "qa-black"]),
                                          ("m-signals", "M", ["qa-white", "qa-black"])):
            with self.subTest(sample=key):
                info = sc.read_home(self.old_home(REAL[key], name=key), legacy_scaffold=True)
                self.assertEqual(info["facts"]["size"], want_size)
                self.assertEqual(info["team"], want_team)
        h = self.old_home("size: confirmed M by PO", name="anywhere")  # where the two rules differ
        self.assertEqual(sc.read_home(h)["facts"]["size"], "M")
        self.assertIsNone(sc.read_home(h, legacy_scaffold=True)["team"])

    def test_grillui_shape_size_m_qa_b_yes_design_yes(self):
        info = sc.read_home(self.old_home(*GRILLUI, name="grillui"), legacy_scaffold=True)
        self.assertEqual(info["team"], ["qa-white", "qa-black", "designer"])
        self.assertEqual((info["facts"]["size"], info["facts"]["design"], info["facts"]["ui-check"]), ("M", "yes", "qa-black"))

    def test_design_yes_qa_b_no_shape_reads_old_and_maps_to_a_valid_team(self):
        with self.assertRaises(sc.ComposeError):  # the old path still refuses it (task 12 removes the path)
            sc.read_home(self.old_home("size: M", "qa-b: no", "design: yes", name="dq"))
        self.assertEqual(sc.sr.legacy_team("M", "no", "yes"), ["qa-white", "designer"])

    def test_qa_none_does_not_crash_and_the_line_stays_untouched(self):
        h = self.old_home(REAL["extractor"], REAL["extractor-qa"], name="qn")
        before = (h / "scope.md").read_bytes()
        info = sc.read_home(h, legacy_scaffold=True)
        self.assertEqual(info["facts"]["qa"], "full")
        self.assertEqual((h / "scope.md").read_bytes(), before)
        self.assertEqual(self.run_cli("compose", "dev", home=h).returncode, 0)

    def test_qa_none_on_a_team_home_and_other_bad_qa_value(self):
        h = self.tmp / "scopes" / "tq"
        h.mkdir(parents=True)
        (h / "scope.md").write_text(f"team: none\n{REAL['extractor-qa']}\n", encoding="utf-8")
        self.assertEqual(sc.read_home(h)["facts"]["qa"], "full")
        (h / "scope.md").write_text("team: none\nqa: light\n", encoding="utf-8")
        self.assertEqual(sc.read_home(h)["facts"]["qa"], "light")
        (h / "scope.md").write_text("team: none\nqa: maybe\n", encoding="utf-8")
        with self.assertRaises(sc.ComposeError) as cm:
            sc.read_home(h)
        self.assertIn("scope.md:2: qa must be full | light", cm.exception.lines[0])
        self.assertEqual(self.run_cli("compose", "manager", home=h).returncode, 2)

    def test_design_yes_qa_b_no_still_raises_on_the_old_path(self):
        with self.assertRaises(sc.ComposeError):
            sc.read_home(self.old_home("size: M", "design: yes", "qa-b: no"))

    def test_design_yes_qa_b_no_is_a_valid_team_through_the_scaffold_mapping(self):
        self.assertEqual(sc.sr.legacy_team("M", "no", "yes"), ["qa-white", "designer"])


class ChooseTest(Base):
    def test_choose_equals_the_old_compose_filter_and_the_rules_line(self):
        rules, n = sc.load_rules(str(self.root), str(self.overlay_path))
        self.assertEqual(n, 2)
        for h in (self.home(size="S"), self.home(size="L", design="yes"), self.goal_home()):
            facts = sc.read_home(h)["facts"]
            for role in sc.sr.ROLES:
                with self.subTest(home=h.name, role=role):
                    want = [e for e in rules if sc.role_in(e, role) and sc.sr.matches(e.when, facts)]  # the pre-split body
                    self.assertEqual([e.id for e in sc.choose(rules, role, facts)], [e.id for e in want])
                    self.assertEqual(self.ids(role, h), [e.id for e in want])

    def test_split_compose_is_byte_equal_to_the_base_compose_for_size_homes(self):
        """Refactor proof: the base compose (`git show 991cab6:bin/squadcompose.py`, before the split) and today's give
        the same text for the old size path, every role, size S/M/L x design, and a goal home."""
        import importlib.util
        base = subprocess.run(["git", "-C", str(ROOT), "show", "991cab6:bin/squadcompose.py"], capture_output=True)
        if base.returncode != 0:
            self.skipTest("base sha 991cab6 not in this clone")
        d = self.tmp / "basemod"
        d.mkdir()
        (d / "squadcompose_base.py").write_bytes(base.stdout)
        spec = importlib.util.spec_from_file_location("squadcompose_base", d / "squadcompose_base.py")
        old = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old)
        homes = [self.home(size=z, design=dz, name=f"h{z}{dz}") for z in "SML" for dz in ("yes", "no")] + [self.goal_home()]
        n = 0
        for h in homes:
            for role in sc.sr.ROLES:
                got = sc.compose(role, str(h), str(self.root), str(self.overlay_path), role, NOW, (PIN_V, "abc1234"))
                if sc.read_home(h)["scope"].startswith("goal"):  # the one header change: size n/a -> team undecided
                    continue
                want = old.compose(role, str(h), str(self.root), str(self.overlay_path), role, NOW, (PIN_V, "abc1234"))
                self.assertEqual(got, want, f"{h.name} {role}")
                n += 1
        self.assertEqual(n, 60)

    def test_choose_is_pure(self):
        rules, _ = sc.load_rules(str(self.root), str(self.overlay_path))
        facts = {"size": "M", "goal": "no"}
        a = [e.id for e in sc.choose(rules, "dev", facts)]
        self.assertEqual(a, [e.id for e in sc.choose(rules, "dev", dict(facts))])
        self.assertEqual(facts, {"size": "M", "goal": "no"})

    def test_load_rules_raises_compose_error_like_before(self):
        with self.assertRaises(sc.ComposeError):
            sc.load_rules(str(self.tmp / "nothing"), None)


class WhoDutyLinesTest(Base):
    def add(self, when):
        self.overlay(f"## add SQ-9 Duty rule\nroles: ba, dev\naware: manager\nwhen: {when}\ntopic: review\nwhy: a\nupstream: local-only\nBody.\n")

    def lines(self):
        r = self.run_cli("who", "SQ-9")
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.split("\n")

    def test_size_lines_stay_and_duty_lines_follow(self):
        self.add("business-ac = ba and qa-black = yes")
        out = self.lines()
        self.assertEqual(out[:3], ["S: acts: ba, dev; aware: manager", "M: acts: ba, dev; aware: manager",
                                   "L: acts: ba, dev; aware: manager"])  # size lines unchanged: no size key, rule applies at every size
        self.assertIn("business-ac = ba: acts: ba, dev; aware: manager", out)
        self.assertIn("business-ac = ticket: acts: -; aware: -", out)
        self.assertIn("qa-black = yes: acts: ba, dev; aware: manager", out)
        self.assertIn("qa-black = no: acts: -; aware: -", out)
        self.assertEqual(sum(1 for x in out if x.startswith("business-ac = ")), 2)

    def test_presence_key_lines_and_no_duty_lines_for_an_old_when(self):
        self.add("ba = yes")
        self.assertIn("ba = no: acts: -; aware: -", self.lines())
        self.add("size = L and design = yes")
        out = [x for x in self.lines() if x]
        self.assertEqual(out, ["S: acts: -; aware: -", "M: acts: -; aware: -", "L: acts: ba, dev; aware: manager"])

    def test_who_of_a_rule_without_when_has_only_size_lines(self):
        self.overlay("## add SQ-9 No when\nroles: dev\ntopic: review\nwhy: a\nupstream: local-only\nBody.\n")
        out = [x for x in self.lines() if x]
        self.assertEqual(out, ["S: acts: dev; aware: -", "M: acts: dev; aware: -", "L: acts: dev; aware: -"])


class RulesviewTest(unittest.TestCase):
    def test_composed_with_team_and_with_size(self):
        sys.path.insert(0, str(ROOT / "tests"))
        import rulesview as rv
        t = rv.composed("manager", team=("ba", "qa-white"))
        self.assertIn("team: ba, qa-white", t)
        self.assertIn("business-ac=ba", t)
        self.assertIn("team: none", rv.composed("manager", team=()))
        self.assertIn("team: none", rv.composed("manager", team=""))
        self.assertIn("(size M,", rv.composed("dev"))  # old path, scaffold on
        self.assertIn("duties: plan-owner=manager", rv.composed("manager", team="qa-white, qa-black"))

    def test_who_parses_size_and_duty_lines(self):
        sys.path.insert(0, str(ROOT / "tests"))
        import rulesview as rv
        rv.who.cache_clear()
        text = "S: acts: dev; aware: -\nM: acts: -; aware: -\nbusiness-ac = ba: acts: ba, dev; aware: manager\nqa-black = no: acts: -; aware: -\n"
        fake = type("R", (), {"returncode": 0, "stdout": text, "stderr": ""})()
        orig = rv.run
        rv.run = lambda *a: fake
        try:
            w = rv.who("X-1")
        finally:
            rv.run = orig
            rv.who.cache_clear()
        self.assertEqual(w["S"], (("dev",), ()))
        self.assertEqual(w["business-ac = ba"], (("ba", "dev"), ("manager",)))
        self.assertEqual(w["qa-black = no"], ((), ()))
        self.assertEqual(set(w), {"S", "M", "business-ac = ba", "qa-black = no"})


if __name__ == "__main__":
    unittest.main()
