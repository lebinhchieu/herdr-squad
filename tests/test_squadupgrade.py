"""squad-process upgrade / upstream (ticket 07): one fixture per cell of the case table, write guards, CI dry run."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from squadtest import BIN, ROOT, _stamp_version, clean_env, fake_herdr, git, plugin_clone
FIX = Path(__file__).resolve().parent / "fixtures" / "upgrade"
sys.path.insert(0, str(BIN))
import squadhomes as homes_mod  # noqa: E402
import squadrules as sr  # noqa: E402
import squadruntime as rt  # noqa: E402
import squadupgrade as su  # noqa: E402

CASES = json.loads((FIX / "cases.json").read_text())
NEW_PIN = "0.5.0 bbbbbbb2"


def run(*args, cwd=None, extra_env=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("SQUAD_")}
    env.update(extra_env or {})
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


class InstalledCache(Base):
    """No flags: old root and new pin come from installed_plugins.json (a marketplace install has no .git)."""

    def setUp(self):
        super().setUp()
        tmp = Path(self._tmp.name)
        self.old, self.new = tmp / "cache" / "0.4.0", tmp / "cache" / "0.5.0"
        for dest, src, ver in ((self.old, "old", "0.4.0"), (self.new, "new", "0.5.0")):
            shutil.copytree(FIX / "add-free" / src, dest)
            (dest / ".claude-plugin").mkdir()
            (dest / ".claude-plugin" / "plugin.json").write_text(json.dumps({"version": ver}), encoding="utf-8")
        self.listing = tmp / "installed_plugins.json"
        self.write(self.old, self.new)

    def write(self, old, new):
        entries = [{"scope": "user", "installPath": str(p), "version": v, "gitCommitSha": s}
                   for p, v, s in ((old, "0.4.0", "aaaaaaa1"), (new, "0.5.0", "bbbbbbb2"))]
        self.listing.write_text(json.dumps({"version": 2, "plugins": {"squad@market": entries}}), encoding="utf-8")

    def go(self, mode, sq, *extra):
        return run("upgrade", mode, "--squad-dir", str(sq), "--plugin-root", str(self.new), "--today", "2026-10-22", *extra,
                   extra_env={"SQUAD_INSTALLED_PLUGINS": str(self.listing)})

    def test_check_and_apply_need_no_flags(self):
        sq = self.squad("add-free")
        want = (FIX / "add-free" / "expect" / "check.txt").read_text()
        r = self.go("--check", sq)
        self.assertEqual((r.returncode, r.stdout), (0, want), r.stderr)
        r = self.go("--apply", sq, "--yes")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((sq / "plugin.pin").read_text(encoding="utf-8").strip(), NEW_PIN)

    def test_old_root_flag_overrides_the_cache(self):
        sq = self.squad("add-free")
        self.write(self.old.parent / "gone", self.new)  # the cache entry for the old pin is now unusable
        self.assertEqual(self.go("--check", sq).returncode, 1)
        r = self.go("--check", sq, "--old-root", str(FIX / "add-free" / "old"))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_without_a_matching_cache_the_runtime_error_stays(self):
        sq = self.squad("add-free")
        self.write(self.old.parent / "gone", self.new)
        r = self.go("--check", sq)
        self.assertEqual(r.returncode, 1)
        self.assertIn("the pinned runtime is missing", r.stdout + r.stderr)

    def test_no_installed_entry_for_the_new_plugin_names_new_pin(self):
        sq = self.squad("add-free")
        self.write(self.old, self.old.parent / "gone")
        r = self.go("--check", sq)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--new-pin", r.stdout + r.stderr)


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

    def test_removed_team_lead_conditions_are_listed_with_their_translation(self):  # ticket 02 AC4
        for old, new in (("plan-owner = team-lead", "drop the condition"), ("plan-owner = manager", "drop the operation"),
                         ("team-lead = no", "drop the operation"), ("team-lead = yes", "drop the condition")):
            with self.subTest(when=old):
                sq = self.squad_with(old)
                before = self.snapshot(sq)
                r = run(*self.args("--check", "add-free", sq))
                self.assertEqual(r.returncode, 3, r.stderr)  # same exit code as the `size` case
                self.assertRegex(r.stdout, rf"REV-1 \(line 3\): {old} -> .*{new}")
                self.assertEqual(self.snapshot(sq), before)

    def test_old_root_keeps_removed_when_keys_as_text(self):  # ticket 02 AC11
        case = Path(self._tmp.name) / "case"
        shutil.copytree(FIX / "add-free", case)
        rev = case / "old" / "templates" / "squad" / "process" / "review.md"
        rev.write_text(rev.read_text().replace("roles: tech-lead\ntopic: review\n\nThe Tech Lead reads",
                                               "roles: tech-lead\nwhen: plan-owner = manager\ntopic: review\n\nThe Tech Lead reads", 1),
                       encoding="utf-8", newline="\n")
        self.assertIn("when: plan-owner = manager", rev.read_text())
        self.assertEqual(su.load_plugin(str(case / "old"), old=True)[0]["REV-1"].when, "plan-owner = manager")
        with self.assertRaises(su.UpgradeError):  # the new root stays strict
            su.load_plugin(str(case / "old"))
        sq = self.squad_with("plan-owner = manager")
        args = self.args("--check", "add-free", sq)
        args[args.index("--old-root") + 1] = str(case / "old")
        r = run(*args)
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("REV-1 (line 3): plan-owner = manager -> ", r.stdout)

    def test_other_l_role_rule_lists_the_tech_lead_alternative(self):
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
                self.assertNotIn("alternative: team-lead = yes", r.stdout)  # that key is gone
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
        self.assertIn("not composed", r.stderr)
        self.assertNotIn("adopt", r.stderr)
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
                 + list(FIX.glob("live-squad.local.md")))
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


class Homes(unittest.TestCase):
    """squad-process homes: a squad whose plugin.pin is B and whose open homes are pinned A."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.plug = Path(cls.tmp.name) / "plug"
        a = plugin_clone(cls.plug)
        core = cls.plug / "templates" / "squad" / "process" / "core.md"
        core.write_text(core.read_text(encoding="utf-8").rstrip("\n") + " Edited in B.\n", encoding="utf-8", newline="\n")
        _stamp_version(cls.plug, "0.6.1")
        stub = cls.plug / "bin" / "squad-respawn"  # B's runtime runs this stub: it records argv and the home env
        stub.write_text('#!/usr/bin/env bash\necho "respawn $0 $* SQUAD_DIR=${SQUAD_DIR-unset} SCOPE_DIR=${SCOPE_DIR-unset} '
                        'GOAL_DIR=${GOAL_DIR-unset}" >> "$HERDR_LOG"\n', encoding="utf-8", newline="\n")
        stub.chmod(0o755)
        git("commit", "-q", "-am", "B", cwd=cls.plug)
        cls.a, cls.b = ("0.6.0", a.sha), ("0.6.1", git("rev-parse", "HEAD", cwd=cls.plug))
        rules, _, _ = sr.load_rules(str(cls.plug / "templates" / "squad" / "process"), str(cls.plug))
        cls.core_hash = next(r.hash for r in rules if r.id == "CORE-1")

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.sq = self.root / ".claude" / "squads" / "x"
        self.sq.mkdir(parents=True)
        (self.sq / "plugin.pin").write_text("%s %s\n" % self.b, encoding="utf-8")
        self.overlay("")
        rt.materialise(str(self.sq), *self.a, plugin_root=str(self.plug))

    def overlay(self, ops):
        (self.sq / "process.local.md").write_text("# Local process\n" + ops, encoding="utf-8", newline="\n")

    def scope(self, name, goal="none", pin=None, eol="\n", done=False):
        d = self.sq / "scopes" / ("_done" if done else "") / name
        d.mkdir(parents=True)
        text = f"# Scope: {name}\n\ngoal: {goal}\nteam: tech-lead\nqa: full\nplugin: {pin or '%s %s' % self.a}\n"
        (d / "scope.md").write_bytes(text.replace("\n", eol).encode())
        return d

    def goal(self, name):
        d = self.sq / "goals" / name
        d.mkdir(parents=True)
        (d / "goal.md").write_text("# Goal: %s\n\nplugin: %s %s\n" % ((name,) + self.a), encoding="utf-8", newline="\n")
        return d

    def homes(self, mode, home, *extra):
        return run("homes", mode, "--squad-dir", str(self.sq), "--home", str(home), "--plugin-root", str(self.plug),
                   "--today", "2026-11-21", *extra)

    def snapshot(self):
        return {str(p.relative_to(self.sq)): p.read_bytes() for p in self.sq.rglob("*")
                if p.is_file() and "_runtime" not in p.parts}

    def test_list_for_a_lone_scope_and_for_a_goal(self):
        solo = self.scope("solo")
        g = self.goal("g1")
        self.scope("s1", goal="g1")
        self.scope("s2", goal="other")
        self.scope("old", goal="g1", done=True)
        r = self.homes("--check", solo)
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("scope solo", r.stdout)
        self.assertNotIn("goal g1", r.stdout)
        r = self.homes("--check", g)
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("goal g1", r.stdout)
        self.assertIn("scope s1", r.stdout)
        self.assertNotIn("s2", r.stdout)
        self.assertNotIn("scope old", r.stdout)
        self.assertNotIn("scope solo", r.stdout)

    def test_a_stale_overlay_op_moves_at_the_target_and_warns_about_the_stranded_home(self):
        self.overlay(f"\n## replace CORE-1 @{self.core_hash}\nwhy: local\nupstream: local-only\nLocal wording.\n")
        g = self.goal("g1")
        self.scope("lone")  # not offered from the goal home; composes only at A, where the op is stale
        r = self.homes("--check", g)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertRegex(r.stdout, r"goal g1 .* moves")
        self.assertIn("will refuse spawn and respawn: scope lone: CORE-1: overlay written for", r.stdout)

    def test_a_refused_compose_writes_nothing(self):
        self.overlay("\n## replace NOPE-9 @deadbeef\nwhy: x\nupstream: local-only\nBody.\n")
        s = self.scope("solo")
        before = self.snapshot()
        r = self.homes("--check", s)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("refused", r.stdout)
        r = self.homes("--apply", s, "--yes")
        self.assertEqual(r.returncode, 2)
        self.assertIn("NOPE-9", r.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_apply_needs_yes_then_changes_one_line_and_keeps_crlf(self):
        s = self.scope("solo", eol="\r\n")
        before = self.snapshot()
        r = self.homes("--apply", s)
        self.assertEqual(r.returncode, 3)
        self.assertIn("NOT APPLIED", r.stdout)
        self.assertEqual(self.snapshot(), before)
        r = self.homes("--apply", s, "--yes")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("moved scope solo: %s %s -> %s %s" % (self.a + self.b), r.stdout)
        after = self.snapshot()
        changed = [k for k in after if after.get(k) != before.get(k)]
        self.assertEqual(sorted(changed), ["process-log.md", "scopes/solo/scope.md"])
        old, new = before["scopes/solo/scope.md"].split(b"\r\n"), after["scopes/solo/scope.md"].split(b"\r\n")
        self.assertEqual([(o, n) for o, n in zip(old, new) if o != n],
                         [(b"plugin: %s %s" % tuple(x.encode() for x in self.a),
                           b"plugin: %s %s" % tuple(x.encode() for x in self.b))])
        self.assertEqual(len(old), len(new))
        self.assertEqual(after["process-log.md"].decode().count("Home scope solo plugin"), 1)
        self.assertIn("nothing to move", self.homes("--apply", s, "--yes").stdout)

    def test_only_limits_the_move_and_a_name_not_offered_exits_2(self):
        g = self.goal("g1")
        self.scope("s1", goal="g1")
        self.scope("s2", goal="g1")
        r = self.homes("--apply", g, "--yes", "--only", "s2")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("moved scope s2", r.stdout)
        self.assertNotIn("moved scope s1", r.stdout)
        self.assertIn("%s %s" % self.a, (self.sq / "scopes" / "s1" / "scope.md").read_text(encoding="utf-8"))
        self.assertIn("%s %s" % self.a, (g / "goal.md").read_text(encoding="utf-8"))
        r = self.homes("--apply", g, "--yes", "--only", "nope")
        self.assertEqual(r.returncode, 2)
        self.assertIn("not an offered home", r.stderr)

    # --- respawn stage (ticket 02) ---
    def roster(self, home, *rows):
        lines = ["# Roster", "", "| Agent | Role | Scope | Owns | Status | Session |", "| --- | --- | --- | --- | --- | --- |"]
        lines += [f"| {n} | {r} | x |  | {st} | s-{n} |" for n, r, st in rows]
        (home / "roster.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    def herdr_run(self, mode, home, *extra, **env):
        bindir = self.root / "bin"
        bindir.mkdir(exist_ok=True)
        fake_herdr(bindir, "live")
        self.log = self.root / "herdr.log"
        self.log.write_text("", encoding="utf-8")
        e = clean_env(HERDR_LOG=str(self.log), PATH=f"{bindir}{os.pathsep}{os.environ['PATH']}", **env)
        return subprocess.run([sys.executable, str(BIN / "squad-process"), "homes", mode, "--squad-dir", str(self.sq),
                               "--home", str(home), "--plugin-root", str(self.plug), "--today", "2026-11-21", *extra],
                              capture_output=True, text=True, encoding="utf-8", env=e)

    def calls(self):
        return self.log.read_text(encoding="utf-8").splitlines()

    def goal_with_pods(self):
        g = self.goal("g1")
        s1, s2 = self.scope("s1", goal="g1"), self.scope("s2", goal="g1")
        self.roster(g, ("mgr", "manager", "live"), ("gtl", "team-lead", "live"))
        self.roster(s1, ("s1-tl", "team-lead", "live"), ("s1-dev", "dev", "live"), ("s1-qw", "qa-whitebox", "live"),
                    ("s1-old", "dev", "retired"))
        self.roster(s2, ("s2-dev", "dev", "live"), ("s2-tech", "tech-lead", "live"))
        return g, s1, s2

    def test_respawn_prompts_then_respawns_in_order_with_each_own_home_and_skips_the_caller(self):
        g, s1, s2 = self.goal_with_pods()
        r = self.herdr_run("--apply", g, "--yes", SQUAD_NAME="mgr", DEAD="s2-tech")
        self.assertEqual(r.returncode, 0, r.stderr)
        c = self.calls()
        self.assertFalse([x for x in c if x.split()[2:3] == ["mgr"]])
        agents = [x.split()[2] for x in c if x.startswith("agent prompt")]
        # the pod before its coordinator, within a home
        self.assertLess(agents.index("s1-dev"), agents.index("s1-qw"))
        self.assertLess(agents.index("s1-qw"), agents.index("s1-tl"))
        self.assertNotIn("s2-tech", agents)
        self.assertNotIn("s1-old", " ".join(c))
        for name in agents:
            p = next(i for i, x in enumerate(c) if x.startswith(f"agent prompt {name} "))
            q = next(i for i, x in enumerate(c) if x.startswith("respawn ") and x.split()[2] == name)
            self.assertLess(p, q)
            self.assertIn("--wait --timeout 300000", c[p])
        rs = {x.split()[2]: x for x in c if x.startswith("respawn ")}
        rt_bin = os.path.join(rt.runtime_path(str(self.sq), *self.b), "bin", "squad-respawn")
        self.assertTrue(all(x.split()[1] == rt_bin and "--force" not in x for x in rs.values()), rs)
        self.assertIn(f"SQUAD_DIR={self.sq} SCOPE_DIR={s1} GOAL_DIR=unset", rs["s1-dev"])
        self.assertIn(f"SQUAD_DIR={self.sq} SCOPE_DIR=unset GOAL_DIR={g}", rs["gtl"])
        self.assertEqual(r.stdout.splitlines()[-1], "caller mgr: last step: report to Chieu, write your notes, "
                                                    "then run squad-respawn mgr")
        self.assertIn("not running s2-tech", r.stdout)

    def test_a_prompt_without_done_leaves_the_agent_pending_exit_4_and_the_rest_respawn(self):
        g, s1, s2 = self.goal_with_pods()
        r = self.herdr_run("--apply", g, "--yes", SQUAD_NAME="nobody", FAIL_PROMPT="s1-dev",
                           SQUAD_HOMES_PROMPT_TIMEOUT_MS="50")
        self.assertEqual(r.returncode, 4, r.stderr)
        self.assertIn("pending s1-dev: prompt did not settle; run squad-respawn s1-dev after it saved its notes", r.stdout)
        self.assertIn("respawned s1-qw", r.stdout)
        self.assertNotIn("caller", r.stdout)
        self.assertTrue(any(x.startswith("agent prompt s1-dev ") and "--timeout 50" in x for x in self.calls()))
        self.assertFalse(any(x.startswith("respawn ") and x.split()[2] == "s1-dev" for x in self.calls()))
        self.assertIn("%s %s" % self.b, (s1 / "scope.md").read_text(encoding="utf-8"))
        # an invalid value falls back to the default
        os.environ["SQUAD_HOMES_PROMPT_TIMEOUT_MS"] = "x"
        self.addCleanup(os.environ.pop, "SQUAD_HOMES_PROMPT_TIMEOUT_MS", None)
        self.assertEqual(homes_mod.prompt_ms(), 300000)

    def test_no_herdr_call_without_yes_or_with_no_respawn_and_the_plan_is_listed(self):
        g, s1, s2 = self.goal_with_pods()
        r = self.herdr_run("--apply", g, SQUAD_NAME="mgr")
        self.assertEqual(r.returncode, 3)
        self.assertIn("would respawn: s1-dev", r.stdout)
        self.assertEqual(self.calls(), [])
        r = self.herdr_run("--apply", g, "--yes", "--no-respawn", SQUAD_NAME="mgr")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.calls(), [])

    def test_a_home_refused_at_read_is_named_by_apply_and_exits_2(self):
        s = self.scope("solo")
        sf = s / "scope.md"
        sf.write_text(sf.read_text(encoding="utf-8").replace("plugin: ", "plugin: bad "), encoding="utf-8", newline="\n")
        before = self.snapshot()
        r = self.homes("--apply", s, "--yes")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("refused scope solo", r.stderr)
        self.assertNotIn("nothing to move", r.stdout)
        self.assertEqual(self.snapshot(), before)
        # next to a home that moves: still exit 2, nothing written; --only deselects the refused one
        g = self.goal("g1")
        s2 = self.scope("s1", goal="g1")
        sf = s2 / "scope.md"
        sf.write_text(sf.read_text(encoding="utf-8").replace("plugin: ", "plugin: bad "), encoding="utf-8", newline="\n")
        before = self.snapshot()
        r = self.homes("--apply", g, "--yes", "--no-respawn")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("refused scope s1", r.stderr)
        self.assertEqual(self.snapshot(), before)
        r = self.homes("--apply", g, "--yes", "--no-respawn", "--only", "g1")
        self.assertEqual(r.returncode, 0, r.stderr)
