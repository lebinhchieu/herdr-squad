"""squad-process team and the old-format refusal (drop-scope-size, design task 02).
Fixture squads in temp folders."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
sys.path.insert(0, str(BIN))
import squadcompose as sc  # noqa: E402
import squadrules as sr  # noqa: E402

PIN = "0.7.0 abcdef123456"


def run(*args, cwd=None, script="squad-process"):
    env = {k: v for k, v in os.environ.items() if not k.startswith("SQUAD_")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run([sys.executable, str(BIN / script), *args], capture_output=True, encoding="utf-8",
                          env=env, cwd=cwd)




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

    def test_size_only_home_exits_2_with_the_team_line_pointer_and_read_home_raises(self):
        h = self.home(["size: M", "qa: full"])
        r = self.team(h)
        self.assertEqual(r.returncode, 2)
        self.assertIn("scope.md:4", r.stderr)
        self.assertIn("`size:`", r.stderr)
        self.assertIn("one `team:` line", r.stderr)
        self.assertEqual(self.team(h, "--has", "dev").returncode, 2)
        with self.assertRaises(sc.ComposeError):  # read_home derives nothing from `size:`
            sc.read_home(str(h))

    def test_every_old_line_is_named(self):
        h = self.home(["size: L", "design: yes", "architecture: no", "qa-b: yes"])
        r = self.team(h)
        for key in ("size", "design", "architecture", "qa-b"):
            self.assertIn(f"`{key}:`", r.stderr)

    def test_old_line_without_size_is_old_format_too(self):
        r = self.team(self.home(["design: yes"]))
        self.assertEqual(r.returncode, 2)
        self.assertIn("one `team:` line", r.stderr)

    def test_old_format_error_is_one_shared_function(self):
        for nl in ("\n", "\r\n"):
            h = self.home(["size: M", "qa-b: no"], name="e" + str(len(nl)), newline=nl)
            e = sc.old_format_error(str(h))
            self.assertEqual(e.lines, [
                "scope.md:4: old format `size:`; replace the old scope lines by one `team:` line (ADR 0018)",
                "scope.md:5: old format `qa-b:`; replace the old scope lines by one `team:` line (ADR 0018)"])
        self.assertIsNone(sc.old_format_error(str(self.home(["team: none"], name="ok"))))
        # the CLI prints the same lines
        self.assertEqual(self.team(h).stderr.strip().split("\n"), e.lines)

    def test_old_line_beside_team_is_an_error_from_the_engine(self):
        r = self.team(self.home(["team: none", "size: M"]))
        self.assertEqual(r.returncode, 2)
        self.assertIn("scope.md:5", r.stderr)


if __name__ == "__main__":
    unittest.main()
