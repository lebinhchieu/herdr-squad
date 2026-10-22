"""squad-process plan / compose / apply on toy plugins (v1-v3) and temp squads."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
import squadprocess as sp  # noqa: E402

CLI = ROOT / "bin" / "squad-process"

V1 = "# T\n\n**Writing rule.** One rule per bullet.\n\n## A\na1\n\n## B\nb1\n\n## D\nd1\n\n## E\ne1\n"
V2 = "# T\n\nprocess-version: 2\n\n**Writing rule.** One rule per bullet.\n\n## A\na2\n\n## B\nb1\n\n## C\nc2\n\n## E\ne2\n"
V3 = "# T\n\nprocess-version: 3\n\n**Writing rule.** One rule per bullet.\n\n## A\na2\n\n## B\nb3\n\n## C\nc2\n\n## E\ne2\n"
CHANGELOG = """# Changelog

## v3 — 2026-02-01
- snapshot: history/process-v3.md

### Reword B
- sections: ## B
- change: reword
- why: clearer
- old: snapshot
- new: snapshot

## v2 — 2026-01-01
- snapshot: history/process-v2.md

### Rework A, add C, drop D
- sections: ## A; ## C; ## D
- change: rule
- why: simpler
- old: snapshot
- new: snapshot

### Tighten E
- sections: ## E
- change: reword
- why: shorter
- old: snapshot
- new: snapshot
"""


def toy_plugin(root):
    snaps = {1: V1, 2: V2, 3: V3}
    skill = Path(root) / "skills" / "squad-process-update"
    (skill / "history").mkdir(parents=True)
    (Path(root) / "templates" / "squad").mkdir(parents=True)
    (Path(root) / "templates" / "squad" / "process.md").write_text(V3, encoding="utf-8")
    for n, t in snaps.items():
        (skill / "history" / f"process-v{n}.md").write_text(t, encoding="utf-8")
    (skill / "changelog.md").write_text(CHANGELOG, encoding="utf-8")
    return Path(root)


def make_squad(tmp, text, log=True):
    d = Path(tmp) / "proj" / ".claude" / "squads" / "s"
    (d / "scopes").mkdir(parents=True, exist_ok=True)
    (d / "process.md").write_text(text, encoding="utf-8")
    if log:
        (d / "process-log.md").write_text(sp.LOG_HEADER + "| 2026-01-01 | old row | because |\n", encoding="utf-8")
    return d


def tree_hash(d):
    h = hashlib.sha256()
    for p in sorted(Path(d).rglob("*")):
        h.update(str(p.relative_to(d)).encode())
        if p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()


def listing(d):
    return sorted(str(p.relative_to(d)) for p in Path(d).rglob("*"))


class Base(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.tmp = Path(self.t.name)
        self.plugin = toy_plugin(self.tmp / "plug")

    def squad(self, text):
        return make_squad(self.tmp, text)

    def states(self, d):
        return {r["heading"]: r["state"] for r in sp.plan(d, self.plugin)["sections"]}

    def cli(self, *args, d):
        return subprocess.run([sys.executable, str(CLI), *args, "--squad-dir", str(d),
                               "--plugin-root", str(self.plugin)], capture_output=True, text=True)


class PlanStatesTest(Base):
    def test_every_state_of_the_table(self):
        s = V1.replace("a1", "a1 mine").replace("e1", "e9") + "\n## Mine\nown\n"
        st = self.states(self.squad(s))
        self.assertEqual(st["## A"], "conflict")
        self.assertEqual(st["## B"], "clean")
        self.assertEqual(st["## C"], "added")
        self.assertEqual(st["## D"], "removed")
        self.assertEqual(st["## E"], "conflict")
        self.assertEqual(st["## Mine"], "local-section")

    def test_local_already_and_conflict_on_removed(self):
        self.assertEqual(self.states(self.squad(V1.replace("d1", "d1 mine")))["## D"], "conflict")
        st = self.states(self.squad(V2.replace("a2", "a2 mine")))  # v2 -> v3: A untouched by plugin
        self.assertEqual(st["## A"], "local")
        self.assertEqual(st["## B"], "clean")
        self.assertEqual(st["## C"], "already")

    def test_two_versions_behind_collects_both_versions_items(self):
        pl = sp.plan(self.squad(V1), self.plugin)
        self.assertEqual((pl["squad"], pl["plugin"], pl["state"]), (1, 3, "behind"))
        self.assertEqual([i["version"] for i in pl["items"]], [2, 2, 3])
        pl2 = sp.plan(self.squad(V2), self.plugin)
        self.assertEqual([i["version"] for i in pl2["items"]], [3])

    def test_conflict_carries_both_diffs_in_json_and_text(self):
        d = self.squad(V1.replace("a1", "a1 mine"))
        r = next(x for x in sp.plan(d, self.plugin)["sections"] if x["heading"] == "## A")
        self.assertIn("+a1 mine", r["squad_vs_old"])
        self.assertIn("+a2", r["old_vs_new"])
        out = self.cli("plan", d=d).stdout
        self.assertIn("+a1 mine", out)
        self.assertIn("+a2", out)
        j = json.loads(self.cli("plan", "--json", d=d).stdout)
        self.assertIn("squad_vs_old", next(x for x in j["sections"] if x["heading"] == "## A"))

    def test_current_is_up_to_date(self):
        d = self.squad(V3)
        self.assertEqual(sp.plan(d, self.plugin)["state"], "current")
        self.assertIn("up to date", self.cli("plan", d=d).stdout)

    def test_ahead_flat_layout_and_missing_snapshot_refuse(self):
        self.assertEqual(self.cli("plan", d=self.squad("# T\n\nprocess-version: 9\n")).returncode, 2)
        flat = make_squad(self.tmp / "x", V1)
        (flat / "scopes").rmdir()
        r = self.cli("plan", d=flat)
        self.assertEqual(r.returncode, 2)
        self.assertIn("squad-migrate", r.stderr)
        (self.plugin / "skills/squad-process-update/history/process-v1.md").unlink()
        self.assertEqual(self.cli("plan", d=self.squad(V1)).returncode, 2)

    def test_unstamped_and_malformed_count_as_version_1(self):
        for text in (V1, V1.replace("# T\n", "# T\n\nprocess-version: 1.5\n")):
            pl = sp.plan(self.squad(text), self.plugin)
            self.assertEqual(pl["squad"], 1)
            self.assertEqual({r["heading"]: r["state"] for r in pl["sections"]}["## A"], "clean")


class ComposeTest(Base):
    def test_refuses_unresolved_conflict_and_names_it(self):
        d = self.squad(V1.replace("a1", "a1 mine"))
        out = self.tmp / "out.md"
        r = self.cli("compose", "--out", str(out), d=d)
        self.assertEqual(r.returncode, 2)
        self.assertIn("## A", r.stderr)
        self.assertFalse(out.exists())

    def test_out_inside_squad_refused(self):
        d = self.squad(V1)
        r = self.cli("compose", "--out", str(d / "x.md"), d=d)
        self.assertEqual(r.returncode, 2)
        self.assertFalse((d / "x.md").exists())

    def test_resolutions_and_local_edit_word_for_word(self):
        mine = "a1 mine, my own wording\nsecond line"
        d = self.squad(V1.replace("a1", mine).replace("e1", "e1 kept by me"))
        own = self.tmp / "own.txt"
        own.write_text("my wording for E\n", encoding="utf-8")
        out = self.tmp / "out.md"
        r = self.cli("compose", "--out", str(out), "--resolve", "## A=ours", "--resolve",
                     f"## E=file:{own}", d=d)
        self.assertEqual(r.returncode, 0, r.stderr)
        text = out.read_text(encoding="utf-8")
        self.assertIn(mine, text)
        self.assertIn("my wording for E", text)
        self.assertNotIn("e2", text)
        self.assertEqual(text.splitlines()[2], "process-version: 3")
        self.assertNotIn("## D", text)
        self.assertLess(text.index("## B"), text.index("## C"))
        self.assertEqual(dict(sp.sections(text))["## B"], "b3")

    def test_theirs_and_untouched_local_section(self):
        d = self.squad(V1.replace("a1", "a1 mine") + "\n## Mine\nown\n")
        out = self.tmp / "o.md"
        sp.compose(d, self.plugin, out, {"## A": "theirs"})
        body = dict(sp.sections(out.read_text(encoding="utf-8")))
        self.assertEqual(body["## A"], "a2")
        self.assertEqual(body["## Mine"], "own")

    def test_own_wording_with_its_heading_line_is_stripped_other_headings_refused(self):
        d = self.squad(V1.replace("a1", "a1 mine"))
        own = self.tmp / "own.txt"
        own.write_text("## A\nmy A wording\n", encoding="utf-8")
        out = self.tmp / "o.md"
        sp.compose(d, self.plugin, out, {"## A": f"file:{own}"})
        self.assertEqual(out.read_text(encoding="utf-8").count("## A"), 1)
        self.assertEqual(dict(sp.sections(out.read_text(encoding="utf-8")))["## A"], "my A wording")
        self.assertTrue(sp.apply(d, self.plugin, out)["diff"])  # apply accepts it
        own.write_text("my A wording\n", encoding="utf-8")  # body alone gives the same result
        out2 = self.tmp / "oa.md"
        sp.compose(d, self.plugin, out2, {"## A": f"file:{own}"})
        self.assertEqual(out2.read_text(encoding="utf-8"), out.read_text(encoding="utf-8"))
        own.write_text("my A\n\n## Other\nx\n", encoding="utf-8")
        with self.assertRaises(sp.ProcessError):
            sp.compose(d, self.plugin, self.tmp / "o2.md", {"## A": f"file:{own}"})
        self.assertFalse((self.tmp / "o2.md").exists())

    def test_local_deletion_of_an_unchanged_section_is_a_conflict(self):
        d = self.squad(V2.replace("\n## A\na2\n", ""))  # v3 leaves A as it is in v2
        self.assertEqual(self.states(d)["## A"], "conflict")
        self.assertIn("`ours` is not offered", self.cli("plan", d=d).stdout)
        with self.assertRaises(sp.ProcessError):
            sp.compose(d, self.plugin, self.tmp / "o.md", {"## A": "ours"})

    def test_ours_that_would_drop_a_heading_of_the_new_version_is_refused(self):
        d = self.squad(V1.replace("\n## E\ne1\n", ""))  # squad deleted E; plugin changed it
        self.assertEqual(self.states(d)["## E"], "conflict")
        with self.assertRaises(sp.ProcessError) as cm:
            sp.compose(d, self.plugin, self.tmp / "o.md", {"## E": "ours"})
        self.assertIn("theirs", str(cm.exception))
        self.assertFalse((self.tmp / "o.md").exists())
        sp.compose(d, self.plugin, self.tmp / "o.md", {"## E": "theirs"})
        own = self.tmp / "own.txt"
        own.write_text("own E\n", encoding="utf-8")
        sp.compose(d, self.plugin, self.tmp / "o2.md", {"## E": f"file:{own}"})
        self.assertIn("own E", (self.tmp / "o2.md").read_text(encoding="utf-8"))

    def test_resolve_of_a_non_conflict_is_refused(self):
        with self.assertRaises(sp.ProcessError):
            sp.compose(self.squad(V1), self.plugin, self.tmp / "o.md", {"## A": "ours"})


class ApplyTest(Base):
    def composed(self, d, resolve=None):
        out = self.tmp / "combined.md"
        sp.compose(d, self.plugin, out, resolve or {})
        return out

    def test_without_yes_squad_folder_is_byte_identical(self):
        d = self.squad(V1)
        f = self.composed(d)
        proj = d.parent.parent.parent
        before, listed = tree_hash(proj), listing(proj)
        r = self.cli("apply", "--legacy", "--file", str(f), d=d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("NOT APPLIED", r.stdout)
        self.assertIn("+process-version: 3", r.stdout)
        self.assertEqual(tree_hash(proj), before)
        self.assertEqual(listing(proj), listed)

    def test_yes_writes_backup_file_log_and_nothing_else(self):
        d = self.squad(V1.replace("a1", "a1 mine"))
        (d / "project.md").write_text("keep", encoding="utf-8")
        f = self.composed(d, {"## A": "ours"})
        proj = d.parent.parent.parent
        before = listing(proj)
        original = (d / "process.md").read_text(encoding="utf-8")
        r = self.cli("apply", "--legacy", "--file", str(f), "--yes", d=d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((d / "process.md").read_text(encoding="utf-8"), f.read_text(encoding="utf-8"))
        backup = proj / ".claude" / "squad-backups" / f"s-process-{sp.datetime.date.today()}.md"
        self.assertEqual(backup.read_text(encoding="utf-8"), original)
        added = set(listing(proj)) - set(before)
        self.assertEqual(added, {".claude/squad-backups", str(backup.relative_to(proj))})
        self.assertEqual((d / "project.md").read_text(encoding="utf-8"), "keep")
        log = (d / "process-log.md").read_text(encoding="utf-8").splitlines()
        head = log.index("|---|---|---|")
        self.assertIn("conflict ## A: kept ours", log[head + 1])
        self.assertIn("v3 Reword B", log[head + 2])
        self.assertEqual(len([ln for ln in log[head + 1:] if "old row" not in ln]), 4)  # 3 items + 1 conflict
        self.assertIn("old row", log[-1])
        self.assertIn("changed sections", r.stdout)
        self.assertIn("backup:", r.stdout)
        self.assertEqual(sp.check(d, self.plugin)["state"], "current")

    def test_second_run_is_a_noop(self):
        d = self.squad(V1)
        f = self.composed(d)
        self.assertEqual(self.cli("apply", "--legacy", "--file", str(f), "--yes", d=d).returncode, 0)
        proj = d.parent.parent.parent
        before = tree_hash(proj)
        r = self.cli("apply", "--legacy", "--file", str(f), "--yes", d=d)
        self.assertEqual(r.returncode, 0)
        self.assertIn("up to date", r.stdout)
        self.assertEqual(tree_hash(proj), before)

    def test_backup_numbering_and_missing_log_created(self):
        d = self.squad(V1)
        (d / "process-log.md").unlink()
        proj = d.parent.parent.parent
        today = sp.datetime.date.today()
        bdir = proj / ".claude" / "squad-backups"
        bdir.mkdir(parents=True)
        (bdir / f"s-process-{today}.md").write_text("x", encoding="utf-8")
        (bdir / f"s-process-{today}-2.md").write_text("x", encoding="utf-8")
        sp.apply(d, self.plugin, self.composed(d), yes=True)
        self.assertTrue((bdir / f"s-process-{today}-3.md").exists())
        self.assertTrue((d / "process-log.md").read_text(encoding="utf-8").startswith("# Process log"))

    def test_invalid_file_refused_nothing_written(self):
        d = self.squad(V1)
        good = self.composed(d).read_text(encoding="utf-8")
        cases = {
            "empty": "",
            "no version": good.replace("process-version: 3\n", ""),
            "wrong version": good.replace("process-version: 3", "process-version: 2"),
            "two versions": good.replace("## A", "process-version: 3\n\n## A"),
            "missing heading": good.replace("## E\n\ne2\n", ""),
        }
        proj = d.parent.parent.parent
        before = tree_hash(proj)
        for name, text in cases.items():
            f = self.tmp / "bad.md"
            f.write_text(text, encoding="utf-8")
            r = self.cli("apply", "--legacy", "--file", str(f), "--yes", d=d)
            self.assertEqual(r.returncode, 2, name)
            self.assertEqual(tree_hash(proj), before, name)

    def test_version_line_problems_are_refused_with_their_own_message(self):
        d = self.squad(V1)
        good = self.composed(d).read_text(encoding="utf-8")
        proj = d.parent.parent.parent
        before = tree_hash(proj)
        for name, text in {"two lines": good.replace("## A", "process-version: 3\n\n## A"),
                           "not a number": good.replace("process-version: 3", "process-version: two"),
                           "missing": good.replace("process-version: 3\n", "")}.items():
            f = self.tmp / "bad.md"
            f.write_text(text, encoding="utf-8")
            r = self.cli("apply", "--legacy", "--file", str(f), "--yes", d=d)
            self.assertEqual(r.returncode, 2, name)
            self.assertIn("exactly one `process-version: 3` line", r.stderr, name)
            self.assertEqual(tree_hash(proj), before, name)

    def test_missing_heading_allowed_when_a_remove_item_names_it(self):
        (self.plugin / "skills/squad-process-update/changelog.md").write_text(
            CHANGELOG.replace("- change: reword\n- why: clearer", "- change: remove\n- why: gone"), encoding="utf-8")
        (self.plugin / "skills/squad-process-update/history/process-v3.md").write_text(
            V3.replace("## B\nb3\n\n", ""), encoding="utf-8")
        d = self.squad(V2)
        f = self.composed(d)
        self.assertNotIn("## B", f.read_text(encoding="utf-8"))
        self.assertTrue(sp.apply(d, self.plugin, f, yes=True)["applied"])

    def test_lint_findings_warn_but_still_apply(self):
        d = self.squad(V1.replace("e1", "e1 " + "word " * 70))
        r = self.cli("apply", "--legacy", "--file", str(self.composed(d, {"## E": "ours"})), "--yes", d=d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("WARNING lint:", r.stdout)
        self.assertEqual(sp.check(d, self.plugin)["state"], "current")

    def test_no_findings_no_warning(self):
        d = self.squad(V1)
        r = self.cli("apply", "--legacy", "--file", str(self.composed(d)), d=d)
        self.assertNotIn("WARNING", r.stdout)

    def test_local_edit_in_untouched_section_survives(self):
        d = self.squad(V1.replace("\n## E", "\n## Mine\nmy own rule\n\n## E"))
        sp.apply(d, self.plugin, self.composed(d), yes=True)
        self.assertEqual(dict(sp.sections((d / "process.md").read_text(encoding="utf-8")))["## Mine"], "my own rule")

    def test_hand_edited_combined_file_is_logged_as_own_wording(self):
        d = self.squad(V1.replace("a1", "a1 mine"))
        f = self.composed(d, {"## A": "ours"})
        f.write_text(f.read_text(encoding="utf-8").replace("a1 mine", "reworded by the PO"), encoding="utf-8")
        r = sp.apply(d, self.plugin, f, yes=True)
        self.assertIn("conflict ## A: kept own wording", "\n".join(r["log_rows"]))


if __name__ == "__main__":
    unittest.main()
