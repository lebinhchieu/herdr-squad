"""squad-process team, the scope.md converter (adopt) and squad-migrate's team line (drop-scope-size, design task 02).
Fixture squads in temp folders; the live squad folders are only read, by tests that skip when they are absent."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
sys.path.insert(0, str(BIN))
sys.path.insert(0, str(ROOT / "tests"))
import squadadopt as sa  # noqa: E402
import squadcompose as sc  # noqa: E402
import squadrules as sr  # noqa: E402
from test_squadcompose import REAL, GRILLUI  # noqa: E402

PIN = "0.7.0 abcdef123456"
LIVE = Path("/home/chieule/workspace/squad/.claude/squads/plugin-bk261023")


def run(*args, cwd=None, script="squad-process"):
    env = {k: v for k, v in os.environ.items() if not k.startswith("SQUAD_")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run([sys.executable, str(BIN / script), *args], capture_output=True, encoding="utf-8",
                          env=env, cwd=cwd)


SCOPE_TEMPLATE = ("# Scope: {{name}}\n\n**{{brief}}**\n\ngoal: {{goal}}\ntouches: {{touches}}\nteam:\nqa: full\n\n## Constraints\n- one\n")


def fixture_plugin(dest, template=SCOPE_TEMPLATE):
    """A plugin root whose bin/ is a copy of this one and whose scope template is `template` (the tree's template
    changes in another ticket; migrate is tested against the contract, the integration run uses the real one)."""
    dest = Path(dest)
    if not dest.exists():
        shutil.copytree(BIN, dest / "bin", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "templates", dest / "templates")
    (dest / "templates" / "scope").mkdir(parents=True, exist_ok=True)
    (dest / "templates" / "scope" / "scope.md").write_text(template, encoding="utf-8")
    return dest


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def home(self, lines, name="s1", newline="\n", pinned=False, squad=None):
        h = (squad or self.tmp) / "scopes" / name
        h.mkdir(parents=True, exist_ok=True)
        body = list(lines) + ([f"plugin: {PIN}"] if pinned else []) + ["", "## Constraints", "- one"]
        (h / "scope.md").write_bytes(("\n".join(["# Scope: " + name, "", "goal:"] + body) + "\n").replace("\n", newline).encode())
        return h

    def squad(self):
        """A composed squad folder (overlay + plugin.pin) so adopt only has scopes to do."""
        sq = self.tmp / "squad"
        (sq).mkdir()
        (sq / "process.local.md").write_text("# Local process\n", encoding="utf-8")
        (sq / "plugin.pin").write_text(PIN + "\n", encoding="utf-8")
        return sq

    def adopt(self, sq, *extra):
        return run("adopt", "--squad-dir", str(sq), "--new-pin", PIN, *extra)


class TeamCliTest(Base):
    def team(self, home, *extra):
        return run("team", "--home", str(home), *extra)

    def test_prints_comma_list_none_and_undecided(self):
        for line, want in (("team: ba, qa-white  (PO)", "ba, qa-white"), ("team: none", "none"), ("team:", "undecided")):
            r = self.team(self.home([line], name="a" + str(abs(hash(line)))))
            self.assertEqual((r.returncode, r.stdout.strip()), (0, want), r.stderr)
        r = self.team(self.home([], name="hand"))
        self.assertEqual(r.stdout.strip(), "undecided")

    def test_has_exit_codes_use_role_names(self):
        h = self.home(["team: qa-white, designer"])
        for role, code in (("qa-whitebox", 0), ("qa-blackbox", 1), ("designer", 0), ("architect", 1), ("ba", 1),
                           ("manager", 0), ("dev", 0), ("token-coach", 0)):
            r = self.team(h, "--has", role)
            self.assertEqual((role, r.returncode, r.stdout), (role, code, ""), r.stderr)

    def test_undecided_team_has_only_the_manager(self):
        h = self.home(["team:"])
        self.assertEqual([self.team(h, "--has", r).returncode for r in ("manager", "dev", "qa-whitebox")], [0, 1, 1])

    def test_unknown_role_exits_2(self):
        r = self.team(self.home(["team: none"]), "--has", "qa-white")  # a token, not a role name
        self.assertEqual(r.returncode, 2)
        self.assertIn("unknown role", r.stderr)

    def test_no_from_size(self):
        r = self.team(self.home(["team: none"]), "--from-size", "M")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("from-size", (ROOT / "bin/squadrules_cli.py").read_text(encoding="utf-8").replace("--from-size does not", ""))

    def test_bad_team_exits_2_naming_the_line(self):
        r = self.team(self.home(["team: qa-whitebox"]))
        self.assertEqual(r.returncode, 2)
        self.assertIn("scope.md:4", r.stderr)

    def test_hostile_value_runs_nothing_and_prints_no_foreign_token(self):
        marker = self.tmp / "X"
        for i, bad in enumerate((f"qa-white; touch {marker}", f"$(touch {marker})", f"`touch {marker}`")):
            r = self.team(self.home([f"team: {bad}"], name=f"h{i}"))
            self.assertEqual(r.returncode, 2, bad)
            self.assertEqual(r.stdout, "")
        self.assertFalse(marker.exists())
        for key in sr.TEAM_KEYS:  # every printed token is from the fixed set
            r = self.team(self.home([f"team: {key}"], name="k" + key))
            self.assertIn(r.stdout.strip(), sr.TEAM_KEYS)

    def test_size_only_home_exits_2_with_the_converter_pointer_but_still_composes_via_scaffold(self):
        h = self.home(["size: M", "qa: full"])
        r = self.team(h)
        self.assertEqual(r.returncode, 2)
        self.assertIn("scope.md:4", r.stderr)
        self.assertIn("`size:`", r.stderr)
        self.assertIn("squad-process adopt", r.stderr)
        self.assertEqual(self.team(h, "--has", "dev").returncode, 2)
        self.assertEqual(sc.read_home(str(h), legacy_scaffold=True)["team"], ["qa-white", "qa-black"])

    def test_every_old_line_is_named(self):
        h = self.home(["size: L", "design: yes", "architecture: no", "qa-b: yes"])
        r = self.team(h)
        for key in ("size", "design", "architecture", "qa-b"):
            self.assertIn(f"`{key}:`", r.stderr)

    def test_old_line_without_size_is_old_format_too(self):
        r = self.team(self.home(["design: yes"]))
        self.assertEqual(r.returncode, 2)
        self.assertIn("squad-process adopt", r.stderr)

    def test_old_format_error_is_one_shared_function(self):
        for nl in ("\n", "\r\n"):
            h = self.home(["size: M", "qa-b: no"], name="e" + str(len(nl)), newline=nl)
            e = sc.old_format_error(str(h))
            self.assertEqual(e.lines, [
                "scope.md:4: old format `size:`; run `squad-process adopt` (dry run first) to convert the scope to a `team:` line",
                "scope.md:5: old format `qa-b:`; run `squad-process adopt` (dry run first) to convert the scope to a `team:` line"])
        self.assertIsNone(sc.old_format_error(str(self.home(["team: none"], name="ok"))))
        # the CLI prints the same lines
        self.assertEqual(self.team(h).stderr.strip().split("\n"), e.lines)

    def test_old_line_beside_team_is_an_error_from_the_engine(self):
        r = self.team(self.home(["team: none", "size: M"]))
        self.assertEqual(r.returncode, 2)
        self.assertIn("scope.md:5", r.stderr)


def team_of(home):
    return sc.read_home(str(home))["team"]


class ConverterTest(Base):
    def scope_text(self, sq, name="s1"):
        return (sq / "scopes" / name / "scope.md").read_bytes()

    def test_mapping_s_m_l_flags_and_blank(self):
        cases = [
            (["size: S"], []),
            (["size: M"], ["qa-white", "qa-black"]),
            (["size: M", "qa-b: no"], ["qa-white"]),                                   # spec AC 22
            (["size: L"], ["ba", "team-lead", "tech-lead", "qa-white", "qa-black"]),
            (["size: L", "qa-b: no"], ["ba", "team-lead", "tech-lead", "qa-white"]),   # spec AC 21/22 variant
            (["size: S", "design: yes", "architecture: yes"], ["designer", "architect"]),
            (["size: M", "design: yes", "qa-b: no"], ["qa-white", "designer"]),        # I8 (a)
            (["size:"], None),
        ]
        for i, (lines, want) in enumerate(cases):
            sq = self.tmp / f"sq{i}"
            sq.mkdir()
            self.home(lines + ["qa: full"], squad=sq)
            self.assertEqual(sa.plan_scopes(str(sq))[0].team, want, lines)
            sa.apply_scopes(sa.plan_scopes(str(sq)))
            self.assertEqual(team_of(sq / "scopes" / "s1"), want, lines)
            self.assertEqual(sc.old_format_lines(str(sq / "scopes" / "s1")), [])

    def test_dry_run_writes_nothing_and_lists_every_scope_and_the_pinned_skip(self):
        sq = self.squad()
        self.home(["size: M", "qa: full"], "a", squad=sq)
        self.home(["size: L", "qa: full"], "b", squad=sq)
        self.home(["size: S", "qa: full"], "c", squad=sq, pinned=True)
        before = {p: p.read_bytes() for p in sq.rglob("*") if p.is_file()}
        r = self.adopt(sq, "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        for s in ("scopes/a/scope.md", "scopes/b/scope.md"):
            self.assertIn("would convert " + s, r.stdout)
        self.assertIn("skip scopes/c/scope.md: pinned", r.stdout)
        self.assertEqual(before, {p: p.read_bytes() for p in sq.rglob("*") if p.is_file()})

    def test_default_without_yes_changes_nothing(self):
        sq = self.squad()
        self.home(["size: M"], squad=sq)
        before = self.scope_text(sq)
        r = self.adopt(sq)
        self.assertEqual(r.returncode, 3)
        self.assertEqual(before, self.scope_text(sq))

    def test_apply_backup_restore_idempotent(self):
        sq = self.squad()
        self.home(["size: M (confirmed by PO 2026-10-23)", "qa: full", "design: no", "architecture: no", "qa-b: no  (task 03 only changes tests)"], squad=sq)
        orig = self.scope_text(sq)
        r = self.adopt(sq, "--yes")
        self.assertEqual(r.returncode, 0, r.stderr)
        new = self.scope_text(sq).decode()
        self.assertIn("\nteam: qa-white\n", new)
        for key in ("size", "design", "architecture", "qa-b"):
            self.assertNotIn(f"\n{key}:", new)
        self.assertIn("qa: full", new)
        bak = sq / "scopes/s1/scope.md.pre-team.bak"
        self.assertEqual(bak.read_bytes(), orig)  # restoring it gives the byte-identical scope.md
        # idempotent: no change, no second backup
        after = self.scope_text(sq)
        r2 = self.adopt(sq, "--yes")
        self.assertEqual((r2.returncode, self.scope_text(sq)), (0, after))
        self.assertEqual(sorted(p.name for p in (sq / "scopes/s1").iterdir()), ["scope.md", "scope.md.pre-team.bak"])

    def test_restored_backup_composes_under_the_old_engine_shape(self):
        sq = self.squad()
        h = self.home(["size: M", "qa: full"], squad=sq)
        self.adopt(sq, "--yes")
        shutil.copyfile(h / "scope.md.pre-team.bak", h / "scope.md")
        self.assertEqual(sc.read_home(str(h), legacy_scaffold=True)["team"], ["qa-white", "qa-black"])

    def test_missing_or_file_home_exits_2_but_home_without_scope_md_is_undecided(self):
        for bad in (self.tmp / "nope", self.tmp / "afile"):
            (self.tmp / "afile").write_text("x")
            r = run("team", "--home", str(bad))
            self.assertEqual(r.returncode, 2, r.stdout)
            self.assertEqual(r.stdout, "")
        empty = self.tmp / "emptyhome"
        empty.mkdir()
        r = run("team", "--home", str(empty))
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "undecided"), r.stderr)

    def test_blank_size_becomes_blank_team(self):
        sq = self.squad()
        self.home(["size:", "qa: full"], squad=sq)
        self.adopt(sq, "--yes")
        self.assertIn("\nteam:\n", self.scope_text(sq).decode())
        self.assertEqual(sc.read_home(str(sq / "scopes/s1"))["team_source"], "undecided")

    def test_blank_size_with_flags_keeps_dropped_lines_in_file(self):
        sq = self.squad()
        self.home(["size:", "design: yes", "architecture: yes", "qa-b: no", "qa: full"], squad=sq)
        plan = sa.plan_scopes(str(sq))[0]
        self.assertTrue(plan.check)
        sa.apply_scopes([plan])
        text = self.scope_text(sq).decode()
        self.assertIn("<!-- converted from ", text)
        for line in ("size: ;", "design: yes", "architecture: yes", "qa-b: no"):
            self.assertIn(line.rstrip(";"), text.split("-->")[0])
        self.assertNotIn("\ndesign: yes\n", text)

    def test_unreadable_size_is_flagged_not_dropped(self):
        sq = self.squad()
        self.home(["size: XL", "qa: full"], squad=sq)
        r = self.adopt(sq, "--dry-run")
        self.assertIn("check: size 'XL' is not S, M or L", r.stdout)

    def test_commentary_printed_and_flagged_check_and_kept(self):
        for key in ("refine", "extractor"):
            sq = self.tmp / key
            sq.mkdir()
            lines = [REAL[key]] + ([REAL["extractor-qa"]] if key == "extractor" else ["qa: full"])
            self.home(lines, squad=sq)
            plan = sa.plan_scopes(str(sq))[0]
            out = sa.format_scopes([plan], True)
            self.assertIn("check:", out, key)
            self.assertIn("commentary kept beside it: size: M", out)
            sa.apply_scopes([plan])
            text = (sq / "scopes/s1/scope.md").read_text(encoding="utf-8")
            self.assertIn("<!-- converted from size: M", text)  # the commentary is kept in the file
            self.assertTrue(team_of(sq / "scopes/s1") is not None)
            if key == "extractor":
                self.assertIn("qa: none (PO 2026-10-17)", text)  # qa line untouched

    def test_plain_commentary_is_printed_without_check(self):
        sq = self.tmp / "p"
        sq.mkdir()
        self.home(["size: M (PO confirmed 2026-10-23)", "qa: full"], squad=sq)
        out = sa.format_scopes(sa.plan_scopes(str(sq)), True)
        self.assertIn("commentary kept beside it", out)
        self.assertNotIn("check:", out)

    def test_real_samples(self):
        for key in ("svg-l", "m-signals"):
            sq = self.tmp / key
            sq.mkdir()
            self.home([REAL[key], "qa: full"], squad=sq)
            e = sa.plan_scopes(str(sq))[0]
            self.assertEqual(e.team, sr.legacy_team(REAL[key].split(":", 1)[1]))
        sq = self.tmp / "grill"
        sq.mkdir()
        self.home(GRILLUI, squad=sq)
        self.assertEqual(sa.plan_scopes(str(sq))[0].team, ["qa-white", "qa-black", "designer"])

    def test_both_size_and_team_is_an_error_nothing_written(self):
        sq = self.squad()
        self.home(["team: none", "size: M"], squad=sq)
        before = self.scope_text(sq)
        for extra in (("--dry-run",), ("--yes",)):
            r = self.adopt(sq, *extra)
            self.assertEqual(r.returncode, 2)
            self.assertIn("`team:` line 4", r.stderr)
            self.assertIn("`size:` line 5", r.stderr)
        self.assertEqual(before, self.scope_text(sq))
        self.assertEqual([p.name for p in (sq / "scopes/s1").iterdir()], ["scope.md"])

    def test_crlf_is_kept(self):
        sq = self.squad()
        self.home(["size: L", "qa: full", "design: yes"], squad=sq, newline="\r\n")
        self.adopt(sq, "--yes")
        raw = self.scope_text(sq)
        self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))
        self.assertIn(b"team: ba, team-lead, tech-lead, qa-white, qa-black, designer\r\n", raw)

    def test_pin_step_keeps_crlf_too(self):
        sq = self.squad()
        self.home(["size: S", "qa: full"], squad=sq, newline="\r\n")
        self.adopt(sq, "--yes")
        raw = self.scope_text(sq)
        self.assertIn(b"plugin: " + PIN.encode() + b"\r\n", raw)
        self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))

    def test_pinned_scope_is_byte_identical_after_dry_run_and_apply(self):
        sq = self.squad()
        self.home(["size: L", "qa: full"], squad=sq, pinned=True)
        before = self.scope_text(sq)
        for extra in (("--dry-run",), ("--yes",)):
            self.adopt(sq, *extra)
            self.assertEqual(before, self.scope_text(sq))
        self.assertEqual([p.name for p in (sq / "scopes/s1").iterdir()], ["scope.md"])

    def test_injected_failure_between_backup_and_write_leaves_the_original(self):
        sq = self.squad()
        self.home(["size: M", "qa: full"], squad=sq)
        orig = self.scope_text(sq)
        entries = sa.plan_scopes(str(sq))
        real, calls = sa._atomic, []

        def boom(path, text):
            calls.append(path)
            if len(calls) == 2:
                raise OSError("killed")
            return real(path, text)
        sa._atomic = boom
        try:
            with self.assertRaises(OSError):
                sa.apply_scopes(entries)
        finally:
            sa._atomic = real
        self.assertEqual(self.scope_text(sq), orig)
        self.assertEqual((sq / "scopes/s1/scope.md.pre-team.bak").read_bytes(), orig)
        self.assertEqual(sa.plan_scopes(str(sq))[0].status, "convert")  # a rerun still converts

    @unittest.skipIf(os.name == "nt", "symlinks")
    def test_symlinked_scope_is_refused(self):
        sq = self.squad()
        outside = self.tmp / "outside"
        outside.mkdir()
        (outside / "scope.md").write_text("size: M\nqa: full\n\n## x\n", encoding="utf-8")
        (sq / "scopes").mkdir()
        (sq / "scopes" / "ln").symlink_to(outside)
        r = self.adopt(sq, "--yes")
        self.assertEqual(r.returncode, 2)
        self.assertIn("symlink", r.stderr)
        self.assertEqual((outside / "scope.md").read_text(encoding="utf-8"), "size: M\nqa: full\n\n## x\n")
        sq2 = self.tmp / "sq2"
        sq2.mkdir()
        (sq2 / "process.local.md").write_text("# Local process\n", encoding="utf-8")
        (sq2 / "plugin.pin").write_text(PIN + "\n", encoding="utf-8")
        (sq2 / "scopes").mkdir()
        (sq2 / "scopes" / "f").mkdir()
        (sq2 / "scopes" / "f" / "scope.md").symlink_to(outside / "scope.md")
        self.assertEqual(self.adopt(sq2, "--yes").returncode, 2)

    def test_old_line_below_the_header_is_an_error(self):
        sq = self.squad()
        h = self.home(["size: M"], squad=sq)
        with open(h / "scope.md", "a", encoding="utf-8") as f:
            f.write("size: L\n")  # body line equal to an old key: the converter will not guess
        entries = sa.plan_scopes(str(sq))
        self.assertEqual(entries[0].status, "error")
        self.assertIn("below the header", entries[0].note)
        self.assertEqual(self.adopt(sq, "--yes").returncode, 2)

    def test_goal_homes_and_done_scopes_are_not_converted(self):
        sq = self.squad()
        (sq / "goals" / "g").mkdir(parents=True)
        (sq / "goals" / "g" / "goal.md").write_text("size: M\n", encoding="utf-8")
        self.home(["size: M"], "_done", squad=sq)
        (sq / "scopes" / "_done").rename(sq / "scopes" / "_gone")
        self.assertEqual(sa.plan_scopes(str(sq)), [])

    def test_only_writes_inside_the_squad_folder(self):
        sq = self.squad()
        self.home(["size: M"], squad=sq)
        before = {p for p in self.tmp.rglob("*")}
        self.adopt(sq, "--yes")
        new = {p for p in self.tmp.rglob("*")} - before
        self.assertTrue(all(sq in p.parents for p in new), new)


class MigrateTest(Base):
    def migrate(self, size_cell):
        sq = self.tmp / ".claude" / "squads" / "t"
        shutil.rmtree(sq, ignore_errors=True)
        sq.mkdir(parents=True)
        (sq / "process.md").write_text("p", encoding="utf-8")
        (sq / "roster.md").write_text("# Roster\n\n| Agent | Role |\n| --- | --- |\n", encoding="utf-8")
        if size_cell is not None:
            (sq / "scopes.md").write_text(f"# Scopes\n\n| Scope | Size |\n| --- | --- |\n| mine | {size_cell} |\n", encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        env.update(SQUAD_DIR=str(sq), PYTHONDONTWRITEBYTECODE="1")
        r = subprocess.run([sys.executable, str(fixture_plugin(self.tmp / "plugin") / "bin" / "squad-migrate"), "t", "--to", "per-scope", "--scope", "mine", "--no-backup"],
                           env=env, cwd=self.tmp, capture_output=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.home_dir = sq / "scopes" / "mine"
        return (self.home_dir / "scope.md").read_text(encoding="utf-8"), r.stdout

    def test_team_line_from_the_size_row(self):
        for cell, want in (("S", "team: none"), ("M", "team: qa-white, qa-black"),
                           ("**L** (PO)", "team: ba, team-lead, tech-lead, qa-white, qa-black")):
            text, out = self.migrate(cell)
            self.assertIn("\n" + want + "\n", text, cell)
            for key in ("size", "design", "architecture", "qa-b"):
                self.assertNotRegex(text, rf"(?m)^{key}:")
            self.assertIn(want, out)

    def test_template_without_a_team_line_fails_loudly_and_writes_nothing(self):
        fixture_plugin(self.tmp / "plugin", SCOPE_TEMPLATE.replace("team:\n", "size:\n"))
        sq = self.tmp / ".claude" / "squads" / "t"
        sq.mkdir(parents=True)
        (sq / "process.md").write_text("p", encoding="utf-8")
        (sq / "roster.md").write_text("# Roster\n", encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SQUAD", "SCOPE_DIR", "GOAL_DIR"))}
        env.update(SQUAD_DIR=str(sq), PYTHONDONTWRITEBYTECODE="1")
        before = sorted(p.name for p in sq.rglob("*"))
        r = subprocess.run([sys.executable, str(self.tmp / "plugin/bin/squad-migrate"), "t", "--to", "per-scope",
                            "--scope", "mine", "--no-backup"], env=env, cwd=self.tmp, capture_output=True, encoding="utf-8")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no `team:` line", r.stderr + r.stdout)
        self.assertEqual(before, sorted(p.name for p in sq.rglob("*")))

    def test_no_row_leaves_a_blank_team(self):
        for cell in (None, "XL"):
            text, _ = self.migrate(cell)
            self.assertRegex(text, r"(?m)^team:$")
            self.assertEqual(sc.read_home(str(self.home_dir))["team_source"], "undecided")


@unittest.skipUnless(LIVE.is_dir(), "live squad folder not present")
class LiveCopyTest(Base):
    """The `_done` scopes of plugin-bk261023 copied into scopes/ of a copy: convert, compose every role, owners equal."""
    def test_converted_copy_composes_every_role_with_the_old_sizes_owners(self):
        sq = self.tmp / "copy"
        (sq / "scopes").mkdir(parents=True)
        (sq / "process.local.md").write_text("# Local process\n", encoding="utf-8")
        (sq / "plugin.pin").write_text(PIN + "\n", encoding="utf-8")
        old = {}
        for d in sorted((LIVE / "scopes/_done").iterdir()):
            if (d / "scope.md").is_file():
                shutil.copytree(d, sq / "scopes" / d.name)
                old[d.name] = sc.read_home(str(d), legacy_scaffold=True)["team"]
        self.assertTrue(old)
        r = run("adopt", "--squad-dir", str(sq), "--new-pin", PIN, "--yes")
        self.assertEqual(r.returncode, 0, r.stderr)
        for name, want in old.items():
            home = sq / "scopes" / name
            info = sc.read_home(str(home))
            self.assertEqual(info["team"], want, name)
            if want is None:
                continue
            self.assertEqual(sr.resolve_duties(info["team"]), sr.resolve_duties(want))
            for role in sr.ROLES:
                c = run("compose", role, "--home", str(home), "--plugin-root", str(ROOT), "--now", "2026-10-27T00:00:00Z")
                self.assertEqual(c.returncode, 0, f"{name} {role}: {c.stderr}")


if __name__ == "__main__":
    unittest.main()
