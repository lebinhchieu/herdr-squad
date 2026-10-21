"""squadrules: parser, hash, when, lint (ticket 02). Each lint class has a mutation of the clean fixture that triggers only it."""
import importlib.machinery
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
FIX = Path(__file__).resolve().parent / "fixtures" / "rules"
sys.path.insert(0, str(BIN))
import squadrules as sr  # noqa: E402

GOLDEN_ATTRS = "roles: qa-whitebox, qa-blackbox\naware: dev, team-lead\nwhen: size in M, L\ntopic: review"
GOLDEN_BODY = ("The Tech Lead names one final sha per task before QA verdicts; "
               "each QA gives one verdict on that sha.")
SAFE_SENTENCE = "The Developer edits files only inside the own worktree and never pushes."
PROC = "templates/squad/process"


def cli(*args, root=None, squad=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("SQUAD_")}
    cmd = [sys.executable, str(BIN / "squad-process"), *args]
    if root is not None:
        cmd += ["--plugin-root", str(root)]
    if squad is not None:
        cmd += ["--squad-dir", str(squad)]
    return subprocess.run(cmd, capture_output=True, encoding="utf-8", env=env)


class Clean(unittest.TestCase):
    """A copy of fixtures/rules/clean in a temp dir; helpers edit and lint it."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "plugin"
        shutil.copytree(FIX / "clean", self.root)
        self.squad = self.root / "squad"

    def edit(self, rel, fn):
        p = self.root / rel
        p.write_text(fn(p.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")

    def append(self, rel, text):
        self.edit(rel, lambda t: t + text)

    def lint(self, cards="warn"):
        return sr.lint(str(self.root), str(self.squad), cards)

    def only(self, needle, cards="warn"):
        errs, _w, _h = self.lint(cards)
        self.assertEqual(len(errs), 1, errs)
        self.assertIn(needle, errs[0])
        return errs[0]

    def overlay(self, text):
        (self.squad / "process.local.md").write_text(text, encoding="utf-8", newline="\n")


class ParseTest(Clean):
    def test_clean_fixture_parses_to_the_expected_objects(self):
        rules, tombs, problems = sr.load_rules(str(self.root / PROC), str(self.root))
        self.assertEqual(problems, [])
        self.assertEqual([r.id for r in rules], ["CORE-1", "REV-3", "REV-4", "SAFE-1"])  # FILE_ORDER
        core, rev3, rev4, safe = rules
        self.assertEqual((core.roles, core.topic, core.when, core.aware), (["all"], "core", "", []))
        self.assertEqual(core.file, f"{PROC}/core.md")
        self.assertEqual(core.line, 3)
        self.assertEqual(core.title, "Task states")
        self.assertEqual((rev3.roles, rev3.aware, rev3.when, rev3.topic),
                         (["qa-whitebox", "qa-blackbox"], ["dev", "team-lead"], "size in M, L", "review"))
        self.assertEqual((rev3.body, rev3.line, rev3.body_line), (GOLDEN_BODY, 3, 9))
        self.assertEqual(rev3.attr_text, GOLDEN_ATTRS)
        self.assertEqual((rev4.when, rev4.line), ("qa-b = no and size = S", 11))
        self.assertTrue(rev4.body.startswith("- The Developer saves"))
        self.assertEqual(safe.body, SAFE_SENTENCE)
        self.assertEqual([(t.id, t.version, t.replaced_by, t.line) for t in tombs],
                         [("SAFE-9", "0.4.0", ["SAFE-1"], 3)])

    def test_two_topic_files_and_overlay(self):
        ops = sr.parse_overlay(sr.read_text(str(self.squad / "process.local.md")), "process.local.md", [])
        self.assertEqual([(o.kind, o.id, o.hash, o.line) for o in ops],
                         [("replace", "REV-3", "203fa130", 1), ("add", "SQ-1", "", 6), ("remove", "SAFE-1", "22f7e05d", 15)])
        self.assertEqual((ops[0].why, ops[0].upstream), ("report-ui-fix: 8 style returns", "proposed"))
        self.assertTrue(ops[0].body.startswith("The Tech Lead names one final sha"))
        self.assertEqual((ops[1].title, ops[1].attrs["roles"], ops[1].attrs["topic"]), ("Style contract", "tech-lead, qa-blackbox", "review"))
        self.assertEqual(ops[2].body, "")

    def test_overlay_spec_example_with_blank_line_before_body(self):
        text = "## replace REV-3 @7f3a9c21\nwhy: w\nupstream: proposed\n\nNew body.\n"
        ops = sr.parse_overlay(text, "o", [])
        self.assertEqual((ops[0].body, ops[0].upstream), ("New body.", "proposed"))

    def test_crlf_and_bom_parse_the_same(self):
        a = sr.load_rules(str(self.root / PROC), str(self.root))
        for p in (self.root / PROC).glob("*.md"):
            data = p.read_bytes().replace(b"\n", b"\r\n")
            p.write_bytes(b"\xef\xbb\xbf" + data)
        b = sr.load_rules(str(self.root / PROC), str(self.root))
        self.assertEqual(b[2], [])
        key = lambda r: (r.id, r.title, r.roles, r.aware, r.when, r.topic, r.body, r.line, r.hash)  # noqa: E731
        self.assertEqual([key(r) for r in a[0]], [key(r) for r in b[0]])

    def test_heading_inside_a_code_fence_is_not_a_rule(self):
        self.append(f"{PROC}/safety.md", "\n## SAFE-2 Fenced\nroles: dev\ntopic: safety\n\nBody.\n\n```\n## SAFE-5 Not a rule\n```\n")
        rules, _t, problems = sr.load_rules(str(self.root / PROC), str(self.root))
        self.assertEqual(problems, [])
        self.assertEqual([r.id for r in rules if r.topic == "safety"], ["SAFE-1", "SAFE-2"])

    def test_load_rules_reports_what_compose_must_refuse(self):
        self.edit(f"{PROC}/safety.md", lambda t: t.replace("topic: safety", "when: colour = red\ntopic: safety"))
        _r, _t, problems = sr.load_rules(str(self.root / PROC), str(self.root))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("unknown when key 'colour'", problems[0])
        self.append(f"{PROC}/safety.md", "\n## SAFE-1 Again\nroles: dev\ntopic: safety\n\nShort.\n")
        self.assertTrue(any("duplicate ID SAFE-1" in p for p in sr.load_rules(str(self.root / PROC), str(self.root))[2]))

    def test_pointer_in_rule_body_must_name_a_base_rule(self):
        self.append(f"{PROC}/core.md", "\n## CORE-2 Points\nroles: all\ntopic: core\n\nSee [REV-3], [SEC-04] and [REV-99].\n")
        errs = self.lint()[0]
        bad = [e for e in errs if "unknown pointer" in e]
        self.assertEqual(len(bad), 1, errs)
        self.assertIn("[REV-99]", bad[0])
        self.assertRegex(bad[0], r"^templates/squad/process/core\.md:\d+: unknown pointer")

    def test_clean_fixture_lints_clean(self):
        self.assertEqual(self.lint(), ([], [], True))


class HashTest(unittest.TestCase):
    def test_golden(self):
        self.assertEqual(sr.rule_hash(GOLDEN_ATTRS, GOLDEN_BODY), "203fa130")

    def test_stable_across_crlf_bom_and_trailing_spaces(self):
        want = sr.rule_hash(GOLDEN_ATTRS, GOLDEN_BODY)
        self.assertEqual(sr.rule_hash(GOLDEN_ATTRS.replace("\n", "\r\n"), GOLDEN_BODY + "\r\n"), want)
        self.assertEqual(sr.rule_hash(GOLDEN_ATTRS.replace("\n", "  \n") + " ", "\n" + GOLDEN_BODY + "\t\n\n"), want)

    def test_changes_with_a_word_or_an_attribute_or_their_order(self):
        want = sr.rule_hash(GOLDEN_ATTRS, GOLDEN_BODY)
        self.assertNotEqual(sr.rule_hash(GOLDEN_ATTRS, GOLDEN_BODY.replace("one verdict", "two verdicts")), want)
        self.assertNotEqual(sr.rule_hash(GOLDEN_ATTRS.replace("M, L", "S"), GOLDEN_BODY), want)
        a = GOLDEN_ATTRS.split("\n")
        self.assertNotEqual(sr.rule_hash("\n".join([a[1], a[0], a[2], a[3]]), GOLDEN_BODY), want)

    def test_rule_hash_of_a_crlf_file_equals_lf(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "review.md"
            src = (FIX / "clean" / PROC / "review.md").read_bytes()
            p.write_bytes(src.replace(b"\n", b"\r\n"))
            rules = sr.parse_rule_file(sr.read_text(str(p)), "review.md", [])
            self.assertEqual(rules[0].hash, "203fa130")


class MatchesTest(unittest.TestCase):
    def test_truth_table(self):
        w = "size in M, L"
        self.assertFalse(sr.matches(w, {"size": "S"}))
        self.assertTrue(sr.matches(w, {"size": "M"}))
        self.assertTrue(sr.matches(w, {}))
        w = "size = S and design = yes"
        self.assertTrue(sr.matches(w, {"size": "S", "design": "yes"}))
        self.assertFalse(sr.matches(w, {"size": "S", "design": "no"}))
        self.assertFalse(sr.matches(w, {"size": "M", "design": "yes"}))
        self.assertTrue(sr.matches(w, {"size": "S"}))  # design missing: true
        self.assertTrue(sr.matches("", {"size": "S"}))

    def test_qa_b_is_a_key(self):
        self.assertTrue(sr.matches("qa-b = no", {"qa-b": "no"}))
        self.assertFalse(sr.matches("qa-b = no", {"qa-b": "yes"}))

    def test_unknown_key_or_value_raises(self):
        for bad in ("colour = red", "size = XL", "size in M, Q", "size M", "size = S and"):
            with self.assertRaises(ValueError, msg=bad):
                sr.matches(bad, {})

    def test_missing_fact_keys(self):
        self.assertEqual(sr.missing_fact_keys("size = S and design = no", {"design": "no"}), ["size"])


class LintClassTest(Clean):
    def test_duplicate_id(self):
        self.append(f"{PROC}/safety.md", "\n## SAFE-1 Again\nroles: dev\ntopic: safety\n\nA different short sentence.\n")
        self.assertIn("safety.md:9: duplicate ID SAFE-1", self.only("duplicate ID SAFE-1"))

    def test_missing_roles(self):
        self.edit(f"{PROC}/safety.md", lambda t: t.replace("roles: dev\n", ""))
        self.only("missing roles:")

    def test_missing_topic(self):
        self.edit(f"{PROC}/safety.md", lambda t: t.replace("topic: safety\n", ""))
        self.only("missing topic:")

    def test_unknown_role(self):
        self.edit(f"{PROC}/safety.md", lambda t: t.replace("roles: dev", "roles: dev, wizard"))
        self.only("unknown role 'wizard'")

    def test_unknown_when_key_and_value(self):
        self.edit(f"{PROC}/safety.md", lambda t: t.replace("topic: safety", "when: colour = red\ntopic: safety"))
        self.only("unknown when key 'colour'")
        self.edit(f"{PROC}/safety.md", lambda t: t.replace("colour = red", "size = XL"))
        self.only("unknown value 'XL'")

    def test_qa_b_when_is_valid(self):
        self.edit(f"{PROC}/safety.md", lambda t: t.replace("topic: safety", "when: qa-b = no\ntopic: safety"))
        self.assertEqual(self.lint()[0], [])

    def test_id_prefix_not_matching_file(self):
        self.append(f"{PROC}/safety.md", "\n## REV-9 Wrong file\nroles: dev\ntopic: safety\n\nA different short sentence.\n")
        self.only("ID REV-9 does not match the file prefix SAFE")

    def test_unknown_file_stem(self):
        (self.root / PROC / "misc.md").write_text("## SAFE-5 X\nroles: dev\ntopic: safety\n\nShort.\n", encoding="utf-8")
        self.only("unknown file stem 'misc'")

    def test_attribute_order(self):
        self.edit(f"{PROC}/review.md", lambda t: t.replace(
            "roles: dev\nwhen: qa-b = no and size = S\ntopic: review", "when: qa-b = no and size = S\nroles: dev\ntopic: review"))
        self.only("out of order")

    def test_text_outside_a_rule(self):
        self.edit(f"{PROC}/safety.md", lambda t: t.replace("## SAFE-1", "Loose text.\n\n## SAFE-1"))
        self.only("text outside a rule")

    def test_core_over_40_lines(self):
        self.append(f"{PROC}/core.md", "\n" + "\n".join(f"filler {i}" for i in range(40)) + "\n")
        errs = self.lint()[0]
        self.assertTrue(any("core.md has" in e for e in errs), errs)

    def test_body_over_60_words_per_bullet(self):
        long = " ".join(["word"] * 61)
        self.edit(f"{PROC}/safety.md", lambda t: t.replace(SAFE_SENTENCE, f"- {long}"))
        self.assertEqual(self.only("length"), f"{PROC}/safety.md:7: length: 61 words > 60")

    def test_writing_rule_line_is_the_file_line(self):
        self.edit(f"{PROC}/safety.md", lambda t: t.replace(SAFE_SENTENCE, "Line one.\n\nThe Developer should stop."))
        self.assertEqual(self.only("hedge"), f"{PROC}/safety.md:9: hedge: 'should'")

    def test_overlay_on_missing_id(self):
        self.overlay("## remove REV-77 @00000000\nwhy: w\nupstream: local-only\n")
        self.assertEqual(self.only("does not exist"), "process.local.md:1: remove of REV-77, which does not exist")

    def test_two_operations_on_one_id(self):
        self.overlay("## remove SAFE-1 @00000000\nwhy: w\nupstream: local-only\n\n## remove SAFE-1 @00000000\nwhy: w\nupstream: local-only\n")
        self.only("second operation on SAFE-1")

    def test_operation_without_why_or_upstream(self):
        self.overlay("## remove SAFE-1 @00000000\nupstream: local-only\n")
        self.only("no why:")
        self.overlay("## remove SAFE-1 @00000000\nwhy: w\n")
        self.only("no upstream:")
        self.overlay("## remove SAFE-1 @00000000\nwhy: w\nupstream: maybe\n")
        self.only("upstream must be")

    def test_add_with_hash_or_non_sq_id_or_missing_hash(self):
        body = "roles: dev\ntopic: safety\nwhy: w\nupstream: proposed\nShort.\n"
        self.overlay(f"## add SQ-1 @00000000 T\n{body}")
        self.only("add takes no hash")
        self.overlay(f"## add LOCAL-1 T\n{body}")
        self.only("needs an SQ-<n> ID")
        self.overlay("## replace SAFE-1\nwhy: w\nupstream: proposed\nShort.\n")
        self.only("needs its hash")

    def test_12_word_sentence_in_two_rules_but_not_11(self):
        self.append(f"{PROC}/safety.md", f"\n## SAFE-2 Same\nroles: dev\ntopic: safety\n\n{SAFE_SENTENCE}\n")
        self.assertIn("safety.md:13: sentence repeats SAFE-1", self.only("sentence repeats SAFE-1"))
        eleven = SAFE_SENTENCE.replace("only ", "")
        self.edit(f"{PROC}/safety.md", lambda t: t.replace(f"{SAFE_SENTENCE}\n", f"{eleven}\n", 2))
        self.assertEqual(len(eleven.split()), 11)
        # SAFE-1 and SAFE-2 now both carry the 11-word form
        self.assertEqual(self.lint()[0], [])

    def test_sentence_in_a_rule_and_in_an_agents_file(self):
        self.append("agents/x.md", f"\n{SAFE_SENTENCE}\n")
        errs, warns, _ = self.lint("warn")
        self.assertEqual(errs, [])
        self.assertEqual(len(warns), 1)
        self.assertTrue(warns[0].startswith("agents/x.md:6: sentence repeats SAFE-1"), warns)
        self.only("agents/x.md:6: sentence repeats SAFE-1", cards="error")

    def test_pointer_to_a_missing_rule(self):
        self.append("bin/tool.py", "# also [REV-9]\n")
        self.assertEqual(self.only("does not exist"), "bin/tool.py:2: [REV-9] cites a rule that does not exist")

    def test_bare_ids_are_not_pointers(self):
        self.append("agents/x.md", "\nBare SEC-04, UTF-8 and [SEC-04] and [UTF-8] and [NOPE-1] are no rule pointers.\n")
        self.assertEqual(self.lint()[0], [])

    def test_changelog_is_not_scanned(self):
        (self.root / "skills" / "s" / "changelog.md").write_text("Old [REV-9] note.\n", encoding="utf-8")
        self.assertEqual(self.lint()[0], [])

    def test_tombstone_still_present_as_a_rule(self):
        self.append(f"{PROC}/safety.md", "\n## SAFE-9 Back\nroles: dev\ntopic: safety\n\nA different short sentence.\n")
        self.only("removed ID SAFE-9 is still a rule")

    def test_tombstone_replaced_by_missing(self):
        self.edit(f"{PROC}/_removed.md", lambda t: t.replace("replaced_by: SAFE-1", "replaced_by: SAFE-7"))
        self.only("replaced_by names missing ID SAFE-7")


class CliTest(unittest.TestCase):
    def test_no_rule_folder_exits_0(self):
        with tempfile.TemporaryDirectory() as d:
            r = cli("lint", root=d)
        self.assertEqual((r.returncode, r.stdout.strip(), r.stderr), (0, "no rule files", ""))

    def test_template_has_no_rule_files_yet(self):
        r = cli("lint")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "no rule files"))

    def test_clean_fixture_exit_0_prints_nothing(self):
        r = cli("lint", root=FIX / "clean", squad=FIX / "clean" / "squad")
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_errors_fixture_prints_every_class_as_file_line_problem(self):
        r = cli("lint", "--cards", "error", root=FIX / "errors", squad=FIX / "errors" / "squad")
        self.assertEqual(r.returncode, 1)
        lines = r.stdout.splitlines()
        for ln in lines:
            self.assertRegex(ln, r"^[\w./-]+:\d+: \S")
        p, s = PROC, "templates/squad/process/safety.md"
        expected = [
            f"{s}:9: duplicate ID SAFE-1 (first at {s}:3)",
            f"{s}:15: missing roles:",
            f"{s}:20: missing topic:",
            f"{s}:25: unknown role 'wizard' in roles:",
            f"{s}:25: unknown when key 'colour'",
            f"{s}:44: unknown value 'XL' for when key 'size'",
            f"{s}:32: ID REV-9 does not match the file prefix SAFE",
            f"{s}:42: length: 61 words > 60",
            f"{s}:51: attribute lines out of order (expected roles, aware, when, topic)",
            f"{s}:13: sentence repeats SAFE-1 ({s}:7)",
            f"agents/x.md:6: sentence repeats SAFE-1 ({s}:7)",
            f"{p}/_removed.md:3: removed ID SAFE-9 is still a rule ({s}:58)",
            f"{p}/_removed.md:7: replaced_by names missing ID SAFE-77",
            f"{p}/core.md:1: core.md has 47 lines, over 40",
            f"{p}/misc.md:1: unknown file stem 'misc' (not in FILE_ORDER)",
            f"{p}/misc.md:3: text outside a rule (before the first `## ` heading)",
            "process.local.md:1: remove of NOPE-1, which does not exist",
            "process.local.md:8: second operation on SAFE-1 (first at line 5)",
            "process.local.md:5: remove SAFE-1 has no upstream:",
            "process.local.md:8: remove SAFE-1 has no why:",
            "bin/tool.py:1: [REV-8] cites a rule that does not exist",
        ]
        self.assertEqual(sorted(lines), sorted(expected))
        self.assertFalse([ln for ln in lines if "SEC-04" in ln or "UTF-8" in ln])

    def test_cards_warn_exits_0_error_exits_1(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "p"
            shutil.copytree(FIX / "clean", root)
            with open(root / "agents" / "x.md", "a", encoding="utf-8", newline="\n") as f:
                f.write(f"\n{SAFE_SENTENCE}\n")
            w = cli("lint", "--cards", "warn", root=root, squad=root / "squad")
            e = cli("lint", "--cards", "error", root=root, squad=root / "squad")
        self.assertEqual((w.returncode, e.returncode), (0, 1))
        self.assertTrue(w.stdout.startswith("warning: agents/x.md:6:"), w.stdout)
        self.assertTrue(e.stdout.startswith("agents/x.md:6:"), e.stdout)

    def test_hashes_after_problems_do_not_change_exit(self):
        r = cli("lint", "--hashes", root=FIX / "clean", squad=FIX / "clean" / "squad")
        self.assertEqual(r.returncode, 0)
        self.assertIn("REV-3 203fa130", r.stdout.splitlines())
        self.assertEqual([ln.split()[0] for ln in r.stdout.splitlines()], ["CORE-1", "REV-3", "REV-4", "SAFE-1"])
        bad = cli("lint", "--hashes", root=FIX / "errors", squad=FIX / "errors" / "squad")
        self.assertEqual(bad.returncode, 1)
        lines = bad.stdout.splitlines()
        first_hash = next(i for i, ln in enumerate(lines) if ln.startswith("CORE-1 "))
        self.assertTrue(all(":" in ln for ln in lines[:first_hash]))

    def test_hash_of_one_edited_line_crlf_vs_lf(self):
        with tempfile.TemporaryDirectory() as d:
            outs = {}
            for name, nl in (("lf", b"\n"), ("crlf", b"\r\n")):
                root = Path(d) / name
                shutil.copytree(FIX / "clean", root)
                p = root / PROC / "safety.md"
                p.write_bytes(p.read_bytes().replace(b"\n", nl))
                outs[name] = cli("lint", "--hashes", root=root, squad=root / "squad").stdout
            self.assertEqual(outs["lf"], outs["crlf"])
            root = Path(d) / "edited"
            shutil.copytree(FIX / "clean", root)
            p = root / PROC / "safety.md"
            p.write_text(p.read_text(encoding="utf-8").replace("never pushes", "never pulls"), encoding="utf-8", newline="\n")
            self.assertNotEqual(cli("lint", "--hashes", root=root, squad=root / "squad").stdout, outs["lf"])


class DelegationTest(unittest.TestCase):
    """compose <role> goes to the composer; compose --out F stays the v6 merge."""

    def load(self):
        loader = importlib.machinery.SourceFileLoader("squad_process_cli", str(BIN / "squad-process"))
        spec = importlib.util.spec_from_loader("squad_process_cli", loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        return mod

    def test_routing(self):
        mod = self.load()
        import squadrules_cli
        seen = []
        old = squadrules_cli.main
        squadrules_cli.main = lambda argv=None: seen.append(list(argv)) or 7
        mod._mutating = lambda a: seen.append(("v6", a.cmd, a.out)) or 3
        try:
            self.assertEqual(mod.main(["compose", "dev", "--home", "D"]), 7)
            self.assertEqual(mod.main(["compose", "--out", "F"]), 3)
            self.assertEqual(mod.main(["compose", "--out", "F", "--resolve", "## H=ours"]), 3)
            self.assertEqual(mod.main(["lint"]), 7)
            self.assertEqual(mod.main(["rule", "REV-3"]), 7)
            self.assertEqual(mod.main(["who", "REV-3"]), 7)
        finally:
            squadrules_cli.main = old
        self.assertEqual(seen, [["compose", "dev", "--home", "D"], ("v6", "compose", "F"), ("v6", "compose", "F"),
                                ["lint"], ["rule", "REV-3"], ["who", "REV-3"]])

    def test_compose_by_role_is_refused_until_04(self):
        r = cli("compose", "dev")
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
