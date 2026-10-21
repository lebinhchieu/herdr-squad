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

    def test_header_of_goal_manager_prints_na_size_defaults_and_goal_name(self):
        t = self.compose("manager", self.goal_home(), agent="mgr")
        self.assertIn("agent: mgr · role: manager · scope: goal g1 (size n/a, design no, qa full, goal yes)", t)

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


if __name__ == "__main__":
    unittest.main()
