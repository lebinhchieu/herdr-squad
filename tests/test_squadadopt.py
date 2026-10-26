"""squad-process adopt / scaffold (ticket 09): fixture squads in temp folders; the live squad folder is never touched."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
sys.path.insert(0, str(BIN))
import squadadopt as sa  # noqa: E402
import squadrules as sr  # noqa: E402
import squadruntime as rt  # noqa: E402
import squadsettings as ss  # noqa: E402

V6 = (ROOT / "skills/squad-process-update/history/process-v6.md").read_text(encoding="utf-8")
PIN = "0.7.0 abcdef123456"
EDIT_FROM = "- When unsure, size up."
EDIT_TO = "- When unsure, size up and say why in the iteration file."
DELETED = "- The Manager logs every size change in `scope.md` and the iteration file."
PARAGRAPH = "A squad paragraph about pigeons that no rule covers."


def run(*args, cwd=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("SQUAD_")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run([sys.executable, str(BIN / "squad-process"), *args], capture_output=True,
                          encoding="utf-8", env=env, cwd=cwd)


def tree(folder):
    """{relative path: sha256} of every file: byte-identical comparison of two states."""
    out = {}
    for p in sorted(Path(folder).rglob("*")):
        if p.is_file():
            out[str(p.relative_to(folder))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def v6_edited():
    t = V6.replace(EDIT_FROM, EDIT_TO)
    assert EDIT_TO in t and DELETED in t
    t = t.replace(DELETED + "\n", "")
    t = t.replace("| BA, Team Lead, Tech Lead, Manager | everything |\n",
                  "| BA, Team Lead, Tech Lead, Manager | everything |\n\n" + PARAGRAPH + "\n")
    assert PARAGRAPH in t
    return t


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def squad(self, process=None, settings=True, code_deny=True):
        """An old-layout squad in <tmp>/.claude/squads/x: process.md, full settings, an open scope and goal."""
        sq = self.root / ".claude" / "squads" / "x"
        (sq / "scopes" / "s1").mkdir(parents=True)
        (sq / "scopes" / "_done" / "old").mkdir(parents=True)
        (sq / "goals" / "g1").mkdir(parents=True)
        (sq / "process.md").write_text(process if process is not None else V6, encoding="utf-8")
        (sq / "project.md").write_text("# Project\n", encoding="utf-8")
        (sq / "scopes" / "s1" / "scope.md").write_text("# Scope: s1\n\nsize: M\n\n## Constraints\n- none\n", encoding="utf-8")
        (sq / "scopes" / "_done" / "old" / "scope.md").write_text("# Scope: old\n\nsize: S\n", encoding="utf-8")
        (sq / "goals" / "g1" / "goal.md").write_text("# Goal: g1\n\n## Scopes\n- s1\n", encoding="utf-8")
        if settings:
            (sq / "settings").mkdir()
            for f in (ROOT / "templates/squad/settings").glob("*.json"):
                d = json.loads(f.read_text())
                perms = d["permissions"]
                # what an old squad-init wrote: the full template, minus a later-added entry, plus the squad's own
                perms["allow"] = [e for e in perms["allow"] if "squad-process" not in e] + ["Bash(squad-process show:*)",
                                                                                           "Bash(make test:*)"]
                if f.stem == "qa-blackbox" and code_deny:
                    perms["deny"] = [e for e in perms["deny"] if "CODE_PATHS" not in e] + [
                        "Read(///srv/app/src/**)", "Read(//srv/app/web/**)", f"Read(//{self.root}/.worktrees/**)"]
                d.pop("model", None)  # the old files carried no model or effort keys, except where the squad set one
                d.pop("effortLevel", None)
                if f.stem == "dev":
                    d["effortLevel"] = "high"  # a scalar the squad changed
                (sq / "settings" / f.name).write_text(json.dumps(d, indent=2), encoding="utf-8")
        return sq

    def adopt(self, sq, *extra):
        return run("adopt", "--squad-dir", str(sq), "--plugin-root", str(ROOT), "--new-pin", PIN,
                   "--today", "2026-10-22", *extra)


class MapData(unittest.TestCase):
    def test_every_target_id_exists_in_the_templates_or_the_tombstones(self):
        import squadupgrade as su
        rules, tombs = su.load_plugin(str(ROOT))
        m = sa.load_map(str(ROOT), 6)
        self.assertGreater(len(m), 150)
        for n, targets in m.items():
            for t in sa._ids(targets):
                self.assertTrue(t in rules or t in tombs, f"v6 line {n}: {t}")

    def test_map_lines_are_lines_of_the_archived_v6(self):
        total = len(V6.split("\n"))
        self.assertTrue(all(1 <= n <= total for n in sa.load_map(str(ROOT), 6)))

    def test_a_version_without_a_map_is_refused(self):
        with self.assertRaises(sa.AdoptError):
            sa.load_map(str(ROOT), 5)


class TwoOpsOneItem(Base):
    """AC 2: one local edit, one deleted bullet, one unmappable paragraph -> two operations and one PO item."""

    def test_dry_run_lists_two_operations_and_one_item_and_writes_nothing(self):
        sq = self.squad(v6_edited())
        before = tree(sq)
        r = self.adopt(sq, "--dry-run")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("overlay with 2 operation(s)", r.stdout)
        self.assertIn("replace SIZE-4", r.stdout)
        self.assertRegex(r.stdout, r"(remove|replace) SIZE-16")
        self.assertIn("PO items (1 open of 1)", r.stdout)
        self.assertIn(PARAGRAPH, r.stdout)
        self.assertEqual(tree(sq), before)

    def test_nothing_is_written_without_an_answer_and_a_yes(self):
        sq = self.squad(v6_edited())
        before = tree(sq)
        r = self.adopt(sq, "--yes")  # --yes alone does not answer the item
        self.assertEqual(r.returncode, 3)
        self.assertIn("NOT APPLIED", r.stdout)
        self.assertEqual(tree(sq), before)
        r = self.adopt(sq, "--resolve", "L12+=drop")  # an answer alone is not the PO's yes
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertIn("NOT APPLIED", r.stdout)
        self.assertEqual(tree(sq), before)

    def item_key(self, sq):
        return re.search(r"^  (L\d+\+?)  ", self.adopt(sq, "--dry-run").stdout, re.M).group(1)

    def test_resolved_run_writes_two_operations_that_lint(self):
        sq = self.squad(v6_edited())
        key = self.item_key(sq)
        r = self.adopt(sq, "--resolve", f"{key}=drop", "--yes")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        ops = sr.parse_overlay((sq / "process.local.md").read_text(), "process.local.md", [])
        self.assertEqual(sorted(o.id for o in ops), ["SIZE-16", "SIZE-4"])
        self.assertTrue(all(o.upstream == "proposed" for o in ops))
        size4 = next(o for o in ops if o.id == "SIZE-4")
        self.assertEqual(size4.kind, "replace")
        self.assertIn("size up and say why", size4.body)
        self.assertEqual(run("lint", "--squad-dir", str(sq), "--plugin-root", str(ROOT)).returncode, 0)

    def test_add_choice_makes_a_squad_rule_for_the_roles_the_po_names(self):
        sq = self.squad(v6_edited())
        key = self.item_key(sq)
        r = self.adopt(sq, "--resolve", f"{key}=add:manager,tech-lead", "--yes")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        ops = sr.parse_overlay((sq / "process.local.md").read_text(), "process.local.md", [])
        added = next(o for o in ops if o.kind == "add")
        self.assertEqual((added.id, added.attrs["roles"], added.upstream), ("SQ-1", "manager, tech-lead", "local-only"))
        self.assertIn("pigeons", added.body)

    def test_replace_choice_takes_the_pos_file(self):
        sq = self.squad(v6_edited())
        f = self.root / "mine.md"
        f.write_text("The PO's own wording.\n", encoding="utf-8")
        key = self.item_key(sq)
        r = self.adopt(sq, "--resolve", f"{key}=replace:CORE-1:{f}", "--yes")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        ops = sr.parse_overlay((sq / "process.local.md").read_text(), "process.local.md", [])
        self.assertEqual(next(o for o in ops if o.id == "CORE-1").body, "The PO's own wording.")

    def test_bad_answers_are_refused_and_write_nothing(self):
        sq = self.squad(v6_edited())
        before = tree(sq)
        key = self.item_key(sq)
        for bad in (f"{key}=maybe", f"{key}=add:", "L999=drop", f"{key}=replace:NOPE-1:/nonexistent", "nokey"):
            r = self.adopt(sq, "--resolve", bad, "--yes")
            self.assertEqual(r.returncode, 2, bad)
        self.assertEqual(tree(sq), before)

    def test_an_inexact_edit_is_an_item_not_an_operation(self):
        # the old line occurs in no mapped rule body, so it is never guessed into an operation
        sq = self.squad(V6.replace("- A returned task stays with its Developer and task file.", "- A returned task stays with its Developer and task file, always."))
        out = self.adopt(sq, "--dry-run").stdout
        self.assertIn("overlay with 0 operation(s)", out)
        self.assertIn("PO items (1 open of 1)", out)
        self.assertIn("candidate rules: LC-3a, LC-3b", out)


class RoleFilesTest(unittest.TestCase):
    def test_architect_is_an_adopt_role_file(self):
        self.assertIn("architect", sa.ROLE_FILES)
        self.assertIn("designer", sa.ROLE_FILES)


class ArchiveAndSettings(Base):
    """AC 3 and B09-3/8: archive, pin, local settings with only the difference."""

    def adopted(self):
        sq = self.squad(v6_edited())
        key = re.search(r"^  (L\d+\+?)  ", self.adopt(sq, "--dry-run").stdout, re.M).group(1)
        self.original = (sq / "process.md").read_bytes()
        self.old_settings = {f.stem: json.loads(f.read_text()) for f in (sq / "settings").glob("*.json")}
        r = self.adopt(sq, "--resolve", f"{key}=drop", "--yes")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return sq

    def test_process_md_is_archived_not_deleted_and_the_pin_is_written(self):
        sq = self.adopted()
        self.assertFalse((sq / "process.md").exists())
        self.assertEqual((sq / "process.v6-archived.md").read_bytes(), self.original)
        self.assertEqual((sq / "plugin.pin").read_text().strip(), PIN)
        self.assertEqual(rt.mode(str(sq)), "composed")
        self.assertIn("adopt: process.md v6", (sq / "process-log.md").read_text())

    def test_each_settings_file_is_archived_and_the_local_file_holds_only_the_difference(self):
        sq = self.adopted()
        for role, old in self.old_settings.items():
            self.assertFalse((sq / "settings" / f"{role}.json").exists(), role)
            self.assertEqual(json.loads((sq / "settings" / f"{role}.v6-archived.json").read_text()), old, role)
            local = json.loads((sq / "settings" / f"{role}.local.json").read_text())
            allow = local.get("permissions", {}).get("allow", [])
            self.assertIn("Bash(make test:*)", allow, role)
            self.assertNotIn("Bash(squad-process show:*)", allow, role)  # retired
            self.assertNotIn("Bash(git status:*)", allow, role)  # template entry: not repeated
            self.assertNotIn("model", local)

    def test_scalar_the_squad_changed_is_kept_and_code_paths_are_extracted(self):
        sq = self.adopted()
        self.assertEqual(json.loads((sq / "settings/dev.local.json").read_text())["effortLevel"], "high")
        qb = json.loads((sq / "settings/qa-blackbox.local.json").read_text())
        self.assertEqual(qb["codePaths"], ["/srv/app/src", "/srv/app/web"])
        self.assertNotIn("deny", qb.get("permissions", {}))

    def test_effective_settings_keep_every_old_deny_and_allow(self):
        sq = self.adopted()
        for role, old in self.old_settings.items():
            eff = ss.effective(role, str(sq), str(ROOT), project_dir=str(self.root))
            for key in ("allow", "deny"):
                for e in old["permissions"][key]:
                    if e == "Bash(squad-process show:*)":
                        self.assertNotIn(e, eff["permissions"][key])
                    elif e.startswith("Read(//") and "CODE" not in e and not e.startswith("Read(//tmp/"):
                        self.assertIn("Read(//" + e[len("Read("):].lstrip("/"), eff["permissions"][key])
                    else:
                        self.assertIn(e, eff["permissions"][key], f"{role} {key} {e}")
            self.assertNotIn("codePaths", eff)

    def test_dry_run_lists_regained_permissions_and_keys(self):
        sq = self.squad(v6_edited())
        out = self.adopt(sq, "--dry-run").stdout
        self.assertIn("permissions regained from the template", out)
        self.assertIn("dev: Bash(squad-process rule:*)", out)
        self.assertIn("ba: model=", out)

    def test_a_squad_that_lost_a_template_entry_regains_it_and_is_told(self):
        sq = self.squad(v6_edited())
        f = sq / "settings" / "team-lead.json"
        d = json.loads(f.read_text())
        d["permissions"]["allow"].remove("Bash(squad-spawn dev:*)")
        f.write_text(json.dumps(d))
        out = self.adopt(sq, "--dry-run").stdout
        self.assertIn("team-lead: Bash(squad-spawn dev:*)", out)

    def test_adopt_never_narrows_a_permission_silently(self):
        sq = self.squad(v6_edited())
        f = sq / "settings" / "dev.json"
        d = json.loads(f.read_text())
        d["permissions"]["deny"] = []  # the template denies; the old file did not: widening is fine
        d["permissions"]["allow"].append("Bash(rm -rf:*)")
        f.write_text(json.dumps(d))
        out = self.adopt(sq, "--dry-run").stdout
        self.assertIn("dev.local.json: +", out)  # kept as the squad's own entry, listed in the plan


class OpenWork(Base):
    """B09-7 / BA G2: open scopes and goals get the squad's pin; a second run changes nothing."""

    def adopted(self):
        sq = self.squad(v6_edited())
        key = re.search(r"^  (L\d+\+?)  ", self.adopt(sq, "--dry-run").stdout, re.M).group(1)
        self.assertIn("would pin scopes/s1", self.adopt(sq, "--dry-run").stdout)
        self.assertIn("would pin goals/g1", self.adopt(sq, "--dry-run").stdout)
        self.before = {p: (sq / p).read_text() for p in ("scopes/s1/scope.md", "goals/g1/goal.md")}
        self.done_before = (sq / "scopes/_done/old/scope.md").read_bytes()
        self.assertEqual(self.adopt(sq, "--resolve", f"{key}=drop", "--yes").returncode, 0)
        return sq

    def test_open_scope_and_goal_get_the_pin_and_the_rest_of_the_file_is_untouched(self):
        sq = self.adopted()
        for rel, old in self.before.items():
            new = (sq / rel).read_text()
            self.assertIn(f"plugin: {PIN}", new)
            self.assertEqual(new.replace(f"plugin: {PIN}\n\n", "", 1), old, rel)
        self.assertEqual((sq / "scopes/_done/old/scope.md").read_bytes(), self.done_before)

    def test_both_still_compose_their_rules_so_spawn_and_respawn_work(self):
        sq = self.adopted()
        for home in ("scopes/s1", "goals/g1"):
            self.assertEqual(rt.home_pin(str(sq / home)), tuple(PIN.split()), home)
            r = run("compose", "dev" if home.startswith("scopes") else "manager", "--home", str(sq / home),
                    "--squad-dir", str(sq), "--plugin-root", str(ROOT), "--out", str(self.root / "o.md"))
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_a_scope_that_has_a_pin_keeps_it_and_a_second_run_is_a_no_op(self):
        sq = self.adopted()
        (sq / "scopes/s1/scope.md").write_text("# s1\n\nplugin: 0.6.0 1234567\n", encoding="utf-8")
        after = tree(sq)
        r = self.adopt(sq, "--yes")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("nothing to do", r.stdout)
        self.assertEqual(tree(sq), after)

    def test_a_cut_short_run_is_finished_by_the_next_one(self):
        sq = self.adopted()
        (sq / "process.v6-archived.md").rename(sq / "process.md")  # as if the crash came before the archive
        for p in ("scopes/s1/scope.md", "goals/g1/goal.md"):
            (sq / p).write_text(self.before[p], encoding="utf-8")
        r = self.adopt(sq, "--yes")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((sq / "process.v6-archived.md").exists())
        self.assertFalse((sq / "process.md").exists())
        self.assertIn(f"plugin: {PIN}", (sq / "scopes/s1/scope.md").read_text())


class Scaffold(Base):
    """AC 4: a new squad has no process.md and lints."""

    def test_scaffold_creates_the_composed_layout_and_lints(self):
        sq = self.root / ".claude" / "squads" / "new"
        r = run("scaffold", "--squad-dir", str(sq), "--plugin-root", str(ROOT), "--new-pin", PIN,
                "--code-path", "/srv/app/src")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((sq / "process.md").exists())
        for f in ("process.local.md", "plugin.pin", "project.md"):
            self.assertTrue((sq / f).is_file(), f)
        self.assertEqual(len(list((sq / "settings").glob("*.local.json"))), 9)
        self.assertEqual(list((sq / "settings").glob("*.json")), list((sq / "settings").glob("*.local.json")))
        self.assertEqual(json.loads((sq / "settings/qa-blackbox.local.json").read_text()), {"codePaths": ["/srv/app/src"]})
        self.assertEqual(json.loads((sq / "settings/dev.local.json").read_text()), {})
        self.assertEqual(rt.mode(str(sq)), "composed")
        lint = run("lint", "--squad-dir", str(sq), "--plugin-root", str(ROOT))
        self.assertEqual(lint.returncode, 0, lint.stdout + lint.stderr)
        self.assertTrue((sq / "scopes").is_dir() and (sq / "goals").is_dir())

    def test_effective_settings_of_a_scaffolded_squad_fail_closed_without_code_paths(self):
        sq = self.root / ".claude" / "squads" / "new"
        r = run("scaffold", "--squad-dir", str(sq), "--plugin-root", str(ROOT), "--new-pin", PIN)
        self.assertIn("no codePaths", r.stdout)
        with self.assertRaises(ss.SettingsError):
            ss.effective("qa-blackbox", str(sq), str(ROOT))

    def test_scaffold_never_overwrites_and_refuses_a_legacy_squad(self):
        sq = self.root / ".claude" / "squads" / "new"
        run("scaffold", "--squad-dir", str(sq), "--plugin-root", str(ROOT), "--new-pin", PIN)
        (sq / "process.local.md").write_text("# mine\n", encoding="utf-8")
        (sq / "project.md").write_text("# mine\n", encoding="utf-8")
        r = run("scaffold", "--squad-dir", str(sq), "--plugin-root", str(ROOT), "--new-pin", "0.8.0 1111111")
        self.assertEqual(r.returncode, 0)
        self.assertEqual((sq / "process.local.md").read_text(), "# mine\n")
        self.assertEqual((sq / "plugin.pin").read_text().strip(), PIN)
        old = self.squad()
        self.assertEqual(run("scaffold", "--squad-dir", str(old), "--plugin-root", str(ROOT), "--new-pin", PIN).returncode, 2)


class DryRunAndRetirement(Base):
    def test_adopt_with_nothing_to_adopt_exits_1(self):
        r = self.adopt(self.root / "nope")
        self.assertEqual(r.returncode, 1)

    def test_show_is_retired_and_apply_needs_legacy(self):
        self.assertNotEqual(run("show", "dev").returncode, 0)
        sq = self.squad()
        r = run("apply", "--file", str(self.root / "f.md"), "--squad-dir", str(sq))
        self.assertEqual(r.returncode, 2)
        self.assertIn("--legacy", r.stderr)

    def test_no_command_card_or_prompt_calls_show(self):
        hits = []
        for d in ("agents", "skills", "bin", "templates", "hooks"):
            for p in (ROOT / d).rglob("*"):
                if p.is_file() and p.suffix in ("", ".md", ".py", ".json", ".sh") and "history" not in p.parts:
                    t = p.read_text(encoding="utf-8", errors="ignore")
                    if p.name == "squadadopt.py":
                        continue  # names the retired allow entry it refuses to carry over
                    if "squad-process show" in t or "ROLE_SECTIONS" in t:
                        hits.append(str(p.relative_to(ROOT)))
        self.assertEqual(hits, [])

    def test_the_live_squad_overlay_fixture_lints_and_classifies(self):
        import squadupgrade as su
        path = ROOT / "tests/fixtures/upgrade/live-squad.local.md"
        problems = []
        ops = sr.parse_overlay(path.read_text(), path.name, problems)
        self.assertEqual(problems, [])
        new, tombs = su.load_plugin(str(ROOT))
        self.assertEqual([i.op.id for i in su.classify(None, new, tombs, ops).unhandled], [])
        self.assertEqual(sr._lint_ops(ops, new), [])


if __name__ == "__main__":
    unittest.main()
