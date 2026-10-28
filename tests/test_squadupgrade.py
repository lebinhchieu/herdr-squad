"""squad-process upgrade / upstream (ticket 07): one fixture per cell of the case table, write guards, CI dry run."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = Path(__file__).resolve().parent / "fixtures" / "upgrade"
BIN = ROOT / "bin"
sys.path.insert(0, str(BIN))
import squadrules as sr  # noqa: E402
import squadruntime as rt  # noqa: E402
import squadupgrade as su  # noqa: E402

CASES = json.loads((FIX / "cases.json").read_text())
NEW_PIN = "0.5.0 bbbbbbb2"


def run(*args, cwd=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("SQUAD_")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run([sys.executable, str(BIN / "squad-process"), *args], capture_output=True,
                          encoding="utf-8", env=env, cwd=cwd)


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def squad(self, case):
        """A writable copy of the case's squad folder in a .claude/squads/x layout (backups go beside it)."""
        sq = Path(self._tmp.name) / ".claude" / "squads" / "x"
        if sq.exists():
            shutil.rmtree(sq.parent.parent)
        shutil.copytree(FIX / case / "squad", sq)
        return sq

    def args(self, mode, case, sq, *extra):
        c = FIX / case
        return ["upgrade", mode, "--squad-dir", str(sq), "--plugin-root", str(c / "new"), "--old-root", str(c / "old"),
                "--new-pin", NEW_PIN, "--today", "2026-10-22", *extra]

    def ops(self, sq):
        return sr.parse_overlay((sq / "process.local.md").read_text(), "process.local.md", [])


class CaseTable(Base):
    def test_check_output_and_exit_for_every_fixture(self):
        for case in CASES:
            if case == "unhandled":
                continue
            with self.subTest(case=case):
                r = run(*self.args("--check", case, FIX / case / "squad"))
                self.assertEqual(r.stdout, (FIX / case / "expect" / "check.txt").read_text())
                self.assertEqual(r.returncode, 3 if "decide:" in r.stdout else 0, r.stderr)

    def test_apply_overlay_for_every_variant(self):
        for case, spec in CASES.items():
            for variant, resolves in spec["variants"].items():
                with self.subTest(case=case, variant=variant):
                    sq = self.squad(case)
                    extra = ["--yes"] + [x for r in resolves for x in ("--resolve", r)]
                    r = run(*self.args("--apply", case, sq, *extra), cwd=FIX / case)
                    self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
                    self.assertEqual((sq / "process.local.md").read_text(),
                                     (FIX / case / "expect" / f"{variant}.md").read_text())
                    self.assertEqual((sq / "plugin.pin").read_text(), "0.5.0 bbbbbbb2\n")

    def test_semantic_values(self):
        """Independent of the golden files: the hash written is the new plugin's, body and attrs kept."""
        new = su.load_plugin(str(FIX / "retarget-op" / "new"))[0]
        sq = self.squad("retarget-op")
        self.assertEqual(run(*self.args("--apply", "retarget-op", sq, "--yes")).returncode, 0)
        (op,) = self.ops(sq)
        self.assertEqual((op.kind, op.id, op.hash), ("replace", "REV-1", new["REV-1"].hash))
        self.assertNotIn("roles", op.attrs)  # takes the new targeting; the body stays
        self.assertEqual(op.body, "Local wording for REV-1.")

    def test_no_operation_is_lost_unless_chosen_or_adopted(self):
        """B07-7: operations before and after, per case and variant."""
        gone = {("change-stale", "take"), ("remove-flag", "drop"), ("split", "drop"), ("adopted", "apply")}
        for case, spec in CASES.items():
            for variant, resolves in spec["variants"].items():
                with self.subTest(case=case, variant=variant):
                    sq = self.squad(case)
                    before = len(self.ops(sq))
                    extra = ["--yes"] + [x for r in resolves for x in ("--resolve", r)]
                    self.assertEqual(run(*self.args("--apply", case, sq, *extra), cwd=FIX / case).returncode, 0)
                    self.assertEqual(len(self.ops(sq)), before - (1 if (case, variant) in gone else 0))

    def test_clash_and_add_are_listed_not_blocked(self):
        for case in ("add-clash", "semantic-clash"):
            r = run(*self.args("--check", case, FIX / case / "squad"))
            self.assertEqual(r.returncode, 0)
            self.assertIn("review (not blocking):", r.stdout)
            self.assertIn("SQ-1 (topic review)", r.stdout)

    def test_adopted_text_is_removed(self):
        sq = self.squad("adopted")
        self.assertEqual(run(*self.args("--apply", "adopted", sq, "--yes")).returncode, 0)
        self.assertEqual(self.ops(sq), [])

    def test_unhandled_op_is_refused(self):
        r = run(*self.args("--check", "unhandled", FIX / "unhandled" / "squad"))
        self.assertEqual(r.returncode, 2)
        self.assertIn("unhandled: REV-9", r.stdout)


class OldWhenLanguage(Base):
    """AC 21: an overlay op written in the old `when:` language is listed with its translation; only --apply --yes writes."""

    def squad_with(self, when):
        sq = self.squad("add-free")
        f = sq / "process.local.md"
        f.write_text(f.read_text().replace("why: local need", f"when: {when}\nwhy: local need"), encoding="utf-8", newline="\n")
        return sq

    def snapshot(self, sq):
        return {str(p.relative_to(sq.parent)): p.read_bytes() for p in sq.parent.rglob("*") if p.is_file()}

    def test_check_lists_each_old_condition_with_its_translation_and_writes_nothing(self):
        sq = self.squad_with("qa-b = no and size = L")
        before = self.snapshot(sq)
        r = run(*self.args("--check", "add-free", sq))
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("REV-1 (line 3): qa-b = no -> qa-black = no", r.stdout)
        self.assertIn("REV-1 (line 3): size = L -> ba = yes", r.stdout)
        self.assertNotIn("nothing needs a decision", r.stdout)
        self.assertEqual(self.snapshot(sq), before)

    def test_other_l_role_rule_lists_both_alternatives(self):
        for roles in ("tech-lead", "team-lead", "tech-lead, team-lead"):
            with self.subTest(roles=roles):
                sq = self.squad_with("size = L")
                f = sq / "process.local.md"
                f.write_text(f.read_text().replace("when: size = L", f"roles: {roles}\nwhen: size = L"),
                             encoding="utf-8", newline="\n")
                before = self.snapshot(sq)
                r = run(*self.args("--check", "add-free", sq))
                self.assertEqual(r.returncode, 3, r.stderr)
                self.assertIn("size = L -> ba = yes", r.stdout)
                self.assertIn("alternative: team-lead = yes", r.stdout)
                self.assertIn("alternative: tech-lead = yes", r.stdout)
                self.assertEqual(self.snapshot(sq), before)
                r = run(*self.args("--apply", "add-free", sq, "--yes"))
                self.assertEqual(r.returncode, 3, r.stderr)
                self.assertIn("NOT APPLIED", r.stdout)
                self.assertEqual(self.snapshot(sq), before)

    def test_ba_or_unroled_rule_lists_no_alternatives(self):
        sq = self.squad_with("size = L")
        r = run(*self.args("--check", "add-free", sq))
        self.assertNotIn("alternative:", r.stdout)

    def test_value_sets_and_unmapped_conditions(self):
        self.assertEqual(su.old_when_conditions("size in M, L"),
                         [("size in M, L", "no single key (write one rule per case)")])
        self.assertEqual(su.old_when_conditions("qa-b in yes, no"), [("qa-b in yes, no", "qa-black in yes, no")])
        self.assertEqual(su.old_when_conditions("qa-whitebox = yes"), [("qa-whitebox = yes", "qa-white = yes")])
        self.assertEqual(su.old_when_conditions("design = yes and ba = yes"), [])
        self.assertEqual(su.old_when_conditions("size = XL"), [("size = XL", "")])

    def test_apply_refuses_without_writing_even_with_yes(self):
        sq = self.squad_with("size = L")
        before = self.snapshot(sq)
        r = run(*self.args("--apply", "add-free", sq, "--yes"))
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("NOT APPLIED", r.stdout)
        self.assertIn("size = L -> ba = yes", r.stdout)
        self.assertEqual(self.snapshot(sq), before)

    def test_new_language_overlay_is_untouched_by_the_listing(self):
        sq = self.squad_with("qa-black = no")
        r = run(*self.args("--check", "add-free", sq))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("old `when:`", r.stdout)


class WriteGuards(Base):
    def snapshot(self, sq):
        root = sq.parent.parent
        return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}

    def test_nothing_written_without_resolve(self):
        sq = self.squad("change-stale")
        before = self.snapshot(sq)
        r = run(*self.args("--apply", "change-stale", sq, "--yes"))
        self.assertEqual(r.returncode, 3)
        self.assertIn("NOT APPLIED", r.stdout)
        self.assertEqual(self.snapshot(sq), before)

    def test_nothing_written_without_yes(self):
        sq = self.squad("change-stale")
        before = self.snapshot(sq)
        r = run(*self.args("--apply", "change-stale", sq, "--resolve", "REV-2=keep"))
        self.assertEqual(r.returncode, 3)
        self.assertIn("NOT APPLIED", r.stdout)
        self.assertEqual(self.snapshot(sq), before)

    def test_bad_resolve_is_refused_and_writes_nothing(self):
        sq = self.squad("change-stale")
        before = self.snapshot(sq)
        for bad in ("REV-2=drop", "REV-1=keep", "REV-2", "REV-2=retarget:REV-1"):
            r = run(*self.args("--apply", "change-stale", sq, "--yes", "--resolve", bad))
            self.assertEqual(r.returncode, 2, bad)
        self.assertEqual(self.snapshot(sq), before)

    def test_backup_log_and_scope_pin(self):
        sq = self.squad("change-stale")
        scope = (sq / "scopes" / "s1" / "scope.md").read_bytes()
        original = (sq / "process.local.md").read_bytes()
        r = run(*self.args("--apply", "change-stale", sq, "--yes", "--resolve", "REV-2=keep"))
        self.assertEqual(r.returncode, 0, r.stderr)
        backups = list((sq.parent.parent / "squad-backups").glob("x-process.local-2026-10-22*.md"))
        self.assertEqual([b.read_bytes() for b in backups], [original])
        self.assertEqual((sq / "scopes" / "s1" / "scope.md").read_bytes(), scope)  # a running scope keeps its pin
        self.assertEqual((sq / "plugin.pin").read_text(), "0.5.0 bbbbbbb2\n")
        log = (sq / "process-log.md").read_text()
        self.assertIn("| 2026-10-22 | Upgraded plugin 0.4.0 aaaaaaa1 -> 0.5.0 bbbbbbb2", log)
        self.assertIn("overlay replace REV-2: local text kept", log)

    def test_missing_runtime_is_exit_1_with_path(self):
        sq = self.squad("add-free")
        r = run("upgrade", "--check", "--squad-dir", str(sq), "--plugin-root", str(FIX / "add-free" / "new"),
                "--new-pin", NEW_PIN)
        self.assertEqual(r.returncode, 1)
        self.assertIn("_runtime", r.stderr)
        self.assertIn("0.4.0-aaaaaaa1", r.stderr)

    def test_pinned_runtime_is_the_old_side(self):
        sq = self.squad("change-stale")
        shutil.copytree(FIX / "change-stale" / "old", rt.runtime_path(str(sq), "0.4.0", "aaaaaaa1"))
        r = run("upgrade", "--check", "--squad-dir", str(sq), "--plugin-root", str(FIX / "change-stale" / "new"),
                "--new-pin", NEW_PIN)
        self.assertEqual(r.returncode, 3, r.stderr)

    def test_legacy_squad_says_not_adopted_and_writes_nothing(self):
        sq = self.squad("add-free")
        (sq / "process.local.md").rename(sq / "process.md")
        before = self.snapshot(sq)
        r = run(*self.args("--check", "add-free", sq))
        self.assertEqual(r.returncode, 2)
        self.assertIn("not adopted", r.stderr)
        self.assertIn("adopt", r.stderr)
        self.assertEqual(run(*self.args("--apply", "add-free", sq, "--yes")).returncode, 2)
        self.assertEqual(self.snapshot(sq), before)

    def test_second_apply_is_a_noop(self):
        sq = self.squad("add-free")
        self.assertEqual(run(*self.args("--apply", "add-free", sq, "--yes")).returncode, 0)
        r = run(*self.args("--apply", "add-free", sq, "--yes"))
        self.assertEqual(r.returncode, 0)
        self.assertIn("nothing to do", r.stdout)


class Upstream(Base):
    def test_lists_proposed_with_why_and_body(self):
        sq = self.squad("adopted")
        r = run("upstream", "--squad-dir", str(sq))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1 proposed operation", r.stdout)
        self.assertIn("### replace REV-2", r.stdout)
        self.assertIn("Why: proposed upstream", r.stdout)
        self.assertIn("QA whitebox runs the touched tests", r.stdout)
        self.assertIn("0 proposed", run("upstream", "--squad-dir", str(self.squad("add-free"))).stdout)


class CiDryRun(unittest.TestCase):
    """Every overlay in fixtures/upgrade is dry-run against the template; an unplaceable operation fails."""

    def test_every_overlay_is_placeable(self):
        found = (list(FIX.glob("*/squad/process.local.md")) + list(FIX.glob("overlays/*.md"))
                 + list(FIX.glob("live-squad.local.md")))  # the last one is built by `adopt` (ticket 09)
        self.assertGreaterEqual(len(found), len(CASES))
        for path in found:
            case = path.parent.parent if path.parent.name == "squad" else None
            if case and case.name == "unhandled":
                continue  # the one fixture that proves the failure below
            with self.subTest(overlay=str(path.relative_to(FIX))):
                new, tombs = su.load_plugin(str(case / "new" if case else ROOT))
                problems = []
                ops = sr.parse_overlay(path.read_text(), path.name, problems)
                self.assertEqual(problems, [])
                old = su.load_plugin(str(case / "old"))[0] if case else None
                plan = su.classify(old, new, tombs, ops)
                self.assertEqual([i.op.id for i in plan.unhandled], [])

    def test_unplaceable_operation_fails_the_dry_run(self):
        new, tombs = su.load_plugin(str(FIX / "unhandled" / "new"))
        ops = sr.parse_overlay((FIX / "unhandled" / "squad" / "process.local.md").read_text(), "x", [])
        self.assertEqual([i.op.id for i in su.classify(None, new, tombs, ops).unhandled], ["REV-9"])


class OddInstalledPlugins(unittest.TestCase):
    """Open item from scope A: squadruntime._installed_cache on a malformed installed_plugins.json."""

    def test_odd_shapes_do_not_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            for n, data in enumerate([[], {"plugins": []}, {"plugins": {"squad@x": {"a": 1}}},
                                      {"plugins": {"squad@x": ["str", 3, None]}}, {"plugins": None}]):
                p = Path(tmp) / f"i{n}.json"
                p.write_text(json.dumps(data))
                self.assertIsNone(rt._installed_cache("0.4.0", "aaaaaaa1", [str(p)]), data)


if __name__ == "__main__":
    unittest.main()
