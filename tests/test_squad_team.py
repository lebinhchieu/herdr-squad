"""squad-team add|remove (drop-scope-size, design task 08). Fixture plugin root and scopes in temp folders."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
sys.path.insert(0, str(BIN))
import squadteam as st  # noqa: E402

RULE = "## {id} {title}\nroles: {roles}\n{when}topic: teams\n\n{body}\n"
RULES = [  # (id, roles, when, body)
    ("TEAM-1", "manager", "plan-owner = manager", "The Manager plans."),
    ("TEAM-2", "team-lead", "plan-owner = team-lead", "The Team Lead plans."),
    ("TEAM-3", "tech-lead", "code-check = tech-lead", "The Tech Lead checks the code."),
    ("TEAM-5", "dev", "plan-owner = manager", "Ask the Manager for the plan."),
]
DESIGN_RULE = ("TEAM-6", "manager", "design = yes", "Manager: the Designer is on the team.")


def run(*args, env=None):
    e = {k: v for k, v in os.environ.items() if not k.startswith("SQUAD_") and k != "SCOPE_DIR"}
    e.update(env or {})
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run([sys.executable, str(BIN / "squad-team"), *args], capture_output=True, encoding="utf-8", env=e)


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def plugin(self, extra=(), name="plugin"):
        proc = self.tmp / name / "templates" / "squad" / "process"
        proc.mkdir(parents=True, exist_ok=True)
        (proc / "core.md").write_text("## CORE-1 Core\nroles: all\ntopic: core\n\nBe kind.\n", encoding="utf-8")
        text = "\n".join(RULE.format(id=i, title="T " + i, roles=r, when=f"when: {w}\n", body=b)
                         for i, r, w, b in [*RULES, *extra])
        (proc / "teams.md").write_text(text, encoding="utf-8")
        return self.tmp / name

    def home(self, lines, name="s1", newline="\n", bom=False):
        h = self.tmp / "scopes" / name
        h.mkdir(parents=True, exist_ok=True)
        text = "\n".join(["# Scope: " + name, "", "goal:", *lines, "", "## Constraints", "- one"]) + "\n"
        data = text.replace("\n", newline).encode()
        (h / "scope.md").write_bytes((b"\xef\xbb\xbf" if bom else b"") + data)
        return h

    def team(self, mode, role, home, *extra, root=None):
        return run(mode, role, "--home", str(home), "--plugin-root", str(root or self.plugin()), *extra)

    def scope(self, home):
        return (Path(home) / "scope.md").read_bytes()


class RefusalTest(Base):
    def refused(self, mode, role, home, *extra, want=""):
        before = self.scope(home)
        r = self.team(mode, role, home, *extra)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn(want, r.stderr)
        self.assertEqual(self.scope(home), before)
        self.assertEqual(r.stdout, "")

    def test_pinned_below_0_6_0(self):
        for pin in ("0.5.2 abc123", "0.5.9 abc123", "0.4.0 abc123", "weird abc123"):
            h = self.home(["team: tech-lead", f"plugin: {pin}"], name="p" + pin[:3])
            self.refused("add", "ba", h, want="pinned")

    def test_goal_home(self):
        h = self.home(["team: tech-lead"])
        (h / "goal.md").write_text("# Goal\nteam: tech-lead\n", encoding="utf-8")
        self.refused("add", "ba", h, want="goal home")

    def test_undecided_team_for_remove_and_add(self):
        for lines in (["team:"], []):
            h = self.home(lines, name=f"u{len(lines)}")
            self.refused("remove", "ba", h, "--at-boundary", want="undecided")
            self.refused("add", "ba", h, want="undecided")

    def test_unknown_and_implicit_roles(self):
        h = self.home(["team: tech-lead"])
        self.refused("add", "wizard", h, want="unknown role")
        self.refused("add", "dev", h, want="always on the team")
        self.refused("remove", "manager", h, "--at-boundary", want="always on the team")
        self.refused("add", "qa-whitebox; touch X", h, want="unknown role")
        self.assertFalse(Path("X").exists())

    def test_add_present_remove_absent(self):
        h = self.home(["team: tech-lead, qa-white"])
        self.refused("add", "qa-whitebox", h, want="already on the team")
        self.refused("add", "tech-lead", h, want="already on the team")
        self.refused("remove", "ba", h, "--at-boundary", want="not on the team")

    def test_old_size_format_and_missing_scope(self):
        h = self.home(["size: M", "design: no", "qa: full"])
        self.refused("add", "ba", h, want="one `team:` line")
        r = self.team("add", "ba", self.tmp / "nope")
        self.assertEqual(r.returncode, 2)

    def test_no_home_given(self):
        r = run("add", "ba")
        self.assertEqual(r.returncode, 2)
        self.assertIn("SCOPE_DIR", r.stderr)

    def test_bad_usage(self):
        self.assertEqual(run("frob", "ba").returncode, 2)
        self.assertEqual(run().returncode, 2)

    def test_hostile_team_value_in_scope_runs_nothing(self):
        for i, bad in enumerate(("qa-white; touch X", "$(touch X)", "`touch X`")):
            h = self.home([f"team: {bad}"], name=f"h{i}")
            self.refused("add", "ba", h, want="unknown team token")
        self.assertFalse(Path("X").exists())

    def test_pin_other_than_running_needs_plugin_root(self):
        h = self.home(["team: tech-lead", "plugin: 9.9.9 abc123"])
        r = run("add", "ba", "--home", str(h))
        self.assertEqual(r.returncode, 2)
        self.assertIn("--plugin-root", r.stderr)
        self.assertIn("tech-lead", self.scope(h).decode())
        r = self.team("add", "ba", h)
        self.assertEqual(r.returncode, 0, r.stderr)


class GuardFlagTest(Base):
    def test_po_ok_for_designer_and_architect(self):
        for role, token in (("designer", "designer"), ("architect", "architect")):
            h = self.home(["team: tech-lead"], name=role)
            before = self.scope(h)
            r = self.team("add", role, h)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("--po-ok", r.stderr)
            self.assertEqual(self.scope(h), before)
            r = self.team("add", role, h, "--po-ok")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn(f"team: {token}, tech-lead".replace("designer, tech-lead", "tech-lead, designer")
                          .replace("architect, tech-lead", "tech-lead, architect"), self.scope(h).decode())

    def test_po_ok_not_needed_for_others(self):
        h = self.home(["team: tech-lead"])
        self.assertEqual(self.team("add", "ba", h).returncode, 0)

    def test_at_boundary_for_remove(self):
        h = self.home(["team: ba, tech-lead"])
        before = self.scope(h)
        r = self.team("remove", "ba", h)
        self.assertEqual(r.returncode, 2)
        self.assertIn("--at-boundary", r.stderr)
        self.assertEqual(self.scope(h), before)
        r = self.team("remove", "ba", h, "--at-boundary")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("\nteam: tech-lead\n", self.scope(h).decode())

    def test_remove_last_role_writes_none(self):
        h = self.home(["team: ba"])
        self.assertEqual(self.team("remove", "ba", h, "--at-boundary").returncode, 0)
        self.assertIn("\nteam: none\n", self.scope(h).decode())
        self.assertEqual(self.team("add", "ba", h).returncode, 0)  # none is a decided, empty team
        self.assertIn("\nteam: ba\n", self.scope(h).decode())


class EditTest(Base):
    def test_other_lines_and_commentary_kept_canonical_order(self):
        h = self.home(["touches: a, b", "team: tech-lead, ba  (PO said so)", "qa: full"])
        r = self.team("add", "qa-whitebox", h)
        self.assertEqual(r.returncode, 0, r.stderr)
        want = self.scope(h).decode()
        self.assertIn("\nteam: ba, tech-lead, qa-white  (PO said so)\n", want)
        self.assertIn("touches: a, b\n", want)
        self.assertIn("qa: full\n\n## Constraints\n- one\n", want)

    def test_crlf_and_bom_kept_byte_for_byte(self):
        for nl, bom in (("\r\n", False), ("\r\n", True), ("\n", True)):
            h = self.home(["team: tech-lead  (note)", "qa: full"], name=f"c{len(nl)}{bom}", newline=nl, bom=bom)
            old = self.scope(h)
            self.assertEqual(self.team("add", "ba", h).returncode, 0)
            new = self.scope(h)
            self.assertEqual(new, old.replace(f"team: tech-lead  (note){nl}".encode(),
                                              f"team: ba, tech-lead  (note){nl}".encode()))
            self.assertEqual(new.startswith(b"\xef\xbb\xbf"), bom)
            self.assertEqual(b"\r\n" in new, nl == "\r\n")

    def test_only_first_team_line_changes(self):
        h = self.home(["team: tech-lead", "team: ba"])
        self.assertEqual(self.team("add", "ba", h).returncode, 0)
        self.assertIn("team: ba, tech-lead\nteam: ba\n", self.scope(h).decode())

    def test_atomic_write_keeps_original_on_failure(self):
        h = self.home(["team: tech-lead"])
        before = self.scope(h)
        plugin = self.plugin()
        with mock.patch("squadteam.os.replace", side_effect=OSError("disk full")):
            rc = st.run(["add", "ba", "--home", str(h), "--plugin-root", str(plugin)])
        self.assertEqual(rc, 2)
        self.assertEqual(self.scope(h), before)
        self.assertEqual(sorted(p.name for p in h.iterdir()), ["scope.md"])

    def test_dry_run_writes_nothing_and_prints_plan(self):
        h = self.home(["team: tech-lead"])
        before = self.scope(h)
        r = self.team("add", "team-lead", h, "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("dry run", r.stdout)
        self.assertIn("respawn: ", r.stdout)
        self.assertEqual(self.scope(h), before)

    def test_home_from_scope_dir_env(self):
        h = self.home(["team: tech-lead"])
        r = run("add", "ba", "--plugin-root", str(self.plugin()), env={"SCOPE_DIR": str(h)})
        self.assertEqual(r.returncode, 0, r.stderr)


class RespawnListTest(Base):
    def lines(self, r):
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.splitlines()

    def test_add_team_lead_lists_manager_tech_lead_dev(self):
        h = self.home(["team: tech-lead"])
        out = self.lines(self.team("add", "team-lead", h))
        self.assertIn("respawn: manager, tech-lead, dev", out)  # ROLES order
        self.assertIn("spawn: team-lead", out)
        self.assertIn("duty plan-owner: manager -> team-lead", out)
        self.assertIn("team: team-lead, tech-lead", out)

    def test_add_qa_white_lists_manager_and_tech_lead_not_dev(self):
        h = self.home(["team: tech-lead"])
        out = self.lines(self.team("add", "qa-whitebox", h))
        self.assertIn("respawn: manager, tech-lead", out)
        self.assertIn("spawn: qa-whitebox", out)
        self.assertIn("duty code-check: tech-lead -> qa-white", out)

    def test_remove_qa_white_lists_roles_and_retires_it(self):
        h = self.home(["team: tech-lead, qa-white"])
        out = self.lines(self.team("remove", "qa-white", h, "--at-boundary"))
        self.assertIn("respawn: manager, tech-lead", out)
        self.assertIn("retire: qa-whitebox", out)
        self.assertIn("duty code-check: qa-white -> tech-lead", out)

    def test_only_the_manager(self):
        root = self.plugin(extra=[DESIGN_RULE])
        h = self.home(["team: tech-lead"])
        out = self.lines(self.team("add", "designer", h, "--po-ok", root=root))
        self.assertIn("respawn: manager", out)
        self.assertFalse([x for x in out if x.startswith("duty ")], out)

    def test_header_only_change_lists_nobody(self):
        h = self.home(["team: tech-lead"])  # fixture has no design rule: only the `team:` header would differ
        out = self.lines(self.team("add", "designer", h, "--po-ok"))
        self.assertIn("respawn: none", out)
        self.assertIn("team: tech-lead, designer", out)

    def test_respawn_equals_roles_whose_text_differs(self):
        """Independent check: compose before and after per role, drop header lines, compare."""
        import squadcompose as sc
        plugin = self.plugin()
        for start, mode, role, extra in (("tech-lead", "add", "team-lead", ()), ("tech-lead", "add", "qa-whitebox", ()),
                                         ("tech-lead, qa-white", "remove", "qa-white", ("--at-boundary",))):
            h = self.home([f"team: {start}"], name="x" + mode + role)
            roles = [r for r in ("manager", "team-lead", "tech-lead", "qa-whitebox", "dev")
                     if r in ("manager", "dev") or sr_key(r) in start]

            def body(text):
                return [x for x in text.splitlines() if not x.startswith(("agent:", "plugin:", "# ")) and "team:" not in x]
            old = {r: body(sc.compose(r, str(h), str(plugin), None, "a", "t")) for r in roles}
            r = self.team(mode, role, h, *extra, root=plugin)
            new_roles = [x for x in roles if not (mode == "remove" and sr_key(x) == sr_key(role))]
            new = {x: body(sc.compose(x, str(h), str(plugin), None, "a", "t")) for x in new_roles}
            want = [x for x in new_roles if x in old and old[x] != new[x]]
            got = [x for x in r.stdout.splitlines() if x.startswith("respawn: ")][0][9:]
            self.assertEqual(sorted(got.split(", ") if got != "none" else []), sorted(want), (start, role))


def sr_key(role):
    return {"qa-whitebox": "qa-white", "qa-blackbox": "qa-black"}.get(role, role)


if __name__ == "__main__":
    unittest.main()
