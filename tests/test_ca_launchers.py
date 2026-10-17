"""claude-accounts: lib.sh functions and the c, c1-c3, cdefault, cswitch launchers, run through links in a temp
HOME against stub herdr/claude/pgrep (tests/ca_stubs.py). Pre-existing behaviour is pinned as it is."""
import json
import os
import re
import shlex
import shutil
import subprocess
import time
import unittest
from pathlib import Path

from ca_stubs import FIX, PANE, SRC, Env, live, requires_linux

HERDR = {"HERDR_ENV": "1", "HERDR_WORKSPACE_ID": "w26"}


@requires_linux
class Base(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.cleanup)

    def herdr_calls(self, *prefix):
        return [c for c in self.e.herdr_calls() if c[:len(prefix)] == list(prefix)]


def bash_scripts():
    """Every imported script whose shebang is bash (cautoswitch is Python)."""
    files = [*SRC.glob("*.sh"), *(SRC / "bin").iterdir()]
    return [f for f in files if "bash" in f.read_text(encoding="utf-8").split("\n", 1)[0] or f.suffix == ".sh"]


class HarnessTest(Base):
    def test_path_resolves_to_stubs_and_not_the_pos_tools(self):
        r = self.e.sh("command -v herdr claude pgrep")
        self.assertEqual(r.stdout.split(), [str(self.e.stub / "bin" / n) for n in ("herdr", "claude", "pgrep")])
        self.assertNotIn(".local/bin", self.e.env["PATH"])

    def test_children_see_no_herdr_squad_or_network(self):
        r = self.e.sh("env")
        env = dict(l.split("=", 1) for l in r.stdout.splitlines() if "=" in l)
        self.assertEqual([k for k in env if k.startswith(("HERDR_", "SQUAD_"))], [])
        for k in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY"):
            self.assertEqual(env[k], "http://127.0.0.1:9")
        self.assertEqual(env["HOME"], str(self.e.home))

    def test_stub_claude_records_no_inherited_squad_vars(self):
        self.e.run("c1")
        rec = self.e.claude_calls()[0]
        self.assertIsNone(rec["SQUAD_NAME"])
        self.assertIsNone(rec["HERDR_PANE_ID"])

    def test_stub_pgrep_lists_only_registered_live_pids(self):
        self.assertEqual(self.e.sh("pgrep -x claude").stdout, "")
        p = self.e.spawn_claude("wT:p1")
        self.assertEqual(self.e.sh("pgrep -x claude").stdout.split(), [str(p.pid)])

    def test_scripts_are_syntactically_valid_bash(self):
        scripts = bash_scripts()
        self.assertGreaterEqual(len(scripts), 8)
        for s in scripts:
            r = subprocess.run(["bash", "-n", str(s)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, f"{s}: {r.stderr}")

    @unittest.skipUnless(shutil.which("shellcheck"), "shellcheck is not installed")
    def test_shellcheck_errors(self):
        scripts = bash_scripts()
        r = subprocess.run(["shellcheck", "-s", "bash", "-S", "error", *map(str, scripts)],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout)


class WsIdOkTest(Base):
    def test_accepts_and_rejects(self):
        for good in ("w1", "w2F", "wA", "w26"):
            self.assertEqual(self.e.sh('ws_id_ok "$1"', good).returncode, 0, good)
        for bad in ("", "w", "x1", "w/../x", "w 1", "w1\n", "w1;rm", "W1", "w-1", "w1."):
            self.assertNotEqual(self.e.sh('ws_id_ok "$1"', bad).returncode, 0, repr(bad))


class DefaultAccountTest(Base):
    def default(self, env=None):
        r = self.e.sh("default_account", env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def wsfile(self, name, value):
        d = self.e.acct / "workspace-default"
        d.mkdir(exist_ok=True)
        (d / name).write_text(value, encoding="utf-8")

    def test_global_default_valid_values_and_fallback(self):
        self.assertEqual(self.e.sh("global_default").stdout, "1\n")  # no file
        for v, want in (("1\n", "1"), ("2\n", "2"), ("3", "3"), ("", "1"), ("4", "1"), ("0", "1"),
                        ("abc", "1"), ("12", "1"), ("2x", "1")):
            self.e.default_file(v)
            self.assertEqual(self.e.sh("global_default").stdout, want + "\n", repr(v))

    def test_workspace_file_beats_global_inside_herdr(self):
        self.e.default_file("2")
        for v in "123":
            self.wsfile("w26", v + "\n")
            self.assertEqual(self.default(HERDR), v + "\n")

    def test_workspace_file_ignored_outside_herdr_or_with_a_bad_id(self):
        self.e.default_file("2")
        self.wsfile("w26", "3")
        self.assertEqual(self.default({"HERDR_WORKSPACE_ID": "w26"}), "2\n")  # no HERDR_ENV
        self.assertEqual(self.default({"HERDR_ENV": "0", "HERDR_WORKSPACE_ID": "w26"}), "2\n")
        self.assertEqual(self.default({"HERDR_ENV": "1"}), "2\n")  # no id
        for bad in ("../x", "x26", "w 26"):
            self.assertEqual(self.default({"HERDR_ENV": "1", "HERDR_WORKSPACE_ID": bad}), "2\n", bad)

    def test_garbage_workspace_file_falls_to_global_and_then_1(self):
        for v in ("0", "4", "9", "", "abc", "22", "x"):
            self.wsfile("w26", v)
            self.assertEqual(self.default(HERDR), "1\n", repr(v))  # no global file
            self.e.default_file("3")
            self.assertEqual(self.default(HERDR), "3\n", repr(v))
            (self.e.acct / "default").unlink()


class ResolveWorkspaceTest(Base):
    def resolve(self, ref):
        return self.e.sh('resolve_workspace "$1"', ref)

    def ok(self, ref, want):
        r = self.resolve(ref)
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, want + "\n", ""), ref)

    def test_real_sample_by_id_number_and_label(self):
        self.e.set_workspaces_real()  # w26, number 1, label claude-accounts
        for ref in ("w26", "1", "claude-accounts"):
            self.ok(ref, "w26")

    def test_each_tier_in_a_list_with_several_workspaces(self):
        self.e.set_workspaces(("wA1", 1, "alpha"), ("wB2", 2, "beta"), ("wC3", 3, "beta2"))
        for ref, want in (("wB2", "wB2"), ("3", "wC3"), ("alpha", "wA1"), ("beta2", "wC3")):
            self.ok(ref, want)

    def test_tier_order_id_then_number_then_label(self):
        # id beats a number and a label that hit other workspaces
        self.e.set_workspaces(("w7", 1, "x"), ("wC", 7, "w7"))
        self.ok("w7", "w7")
        # number beats label: "2" is the number of wB and the label of wA
        self.e.set_workspaces(("wA", 1, "2"), ("wB", 2, "other"))
        self.ok("2", "wB")
        # label wins only when no id or number hit
        self.e.set_workspaces(("wA", 1, "2"), ("wB", 5, "other"))
        self.ok("2", "wA")

    def test_number_tier_is_digits_only(self):
        self.e.set_workspaces(("wA", 1, "one"))
        for ref in ("01", "+1", "1.0", " 1"):
            r = self.resolve(ref)
            self.assertEqual(r.returncode, 2, repr(ref))

    def test_ambiguous_in_the_winning_tier_lists_candidates_rc2(self):
        for rows, ref in (((("wA1", 1, "dup"), ("wB2", 2, "dup")), "dup"),
                          ((("wA1", 4, "x"), ("wB2", 4, "y")), "4")):
            self.e.set_workspaces(*rows)
            r = self.resolve(ref)
            self.assertEqual((r.returncode, r.stdout), (2, ""))
            self.assertTrue(r.stderr.startswith(f"ambiguous: {ref} matches\n"), r.stderr)
            for i, n, l in rows:
                self.assertIn(f"{i} (panel {n}) {l}\n", r.stderr)

    def test_no_hit_idshaped_is_a_raw_id_otherwise_rc2(self):
        self.e.set_workspaces_real()
        self.ok("wZ9", "wZ9")
        r = self.resolve("nothing here")
        self.assertEqual((r.returncode, r.stdout, r.stderr), (2, "", "no workspace matches nothing here\n"))
        self.assertEqual(self.resolve("99").returncode, 2)

    def test_blank_ref_rc2(self):
        self.e.set_workspaces_real()
        for ref in ("", "   ", "\t"):
            r = self.resolve(ref)
            self.assertEqual((r.returncode, r.stdout), (2, ""), repr(ref))
            self.assertIn("no workspace matches", r.stderr)

    def test_herdr_failure_or_bad_json_use_the_raw_id_rule(self):
        (self.e.stub / "workspaces.fail").write_text("", encoding="utf-8")
        self.ok("wQ1", "wQ1")
        self.assertEqual(self.resolve("claude-accounts").returncode, 2)
        (self.e.stub / "workspaces.fail").unlink()
        (self.e.stub / "workspaces.bad").write_bytes(b"not json \xff{")
        self.ok("wQ1", "wQ1")
        self.assertEqual(self.resolve("1").returncode, 2)

    def test_a_listed_id_that_is_not_id_shaped_is_not_returned(self):
        self.e.set_workspaces(("bad/id", 1, "alpha"))
        r = self.resolve("alpha")
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        r = self.resolve("1")
        self.assertEqual((r.returncode, r.stdout), (2, ""))


class SetWorkspaceDefaultTest(Base):
    def test_bad_account_rc2_and_no_file(self):
        for acct in ("4", "0", "x", "", "12"):
            r = self.e.sh('set_workspace_default "$1" w26', acct)
            self.assertEqual(r.returncode, 2, repr(acct))
        self.assertFalse((self.e.acct / "workspace-default").exists())

    def test_outside_herdr_without_id_is_a_noop(self):
        self.e.set_workspaces_real()
        r = self.e.sh("set_workspace_default 2", env={"HERDR_WORKSPACE_ID": "w26"})
        self.assertEqual(r.returncode, 0)
        self.assertFalse((self.e.acct / "workspace-default").exists())
        self.assertEqual(self.e.herdr_calls(), [])

    def test_env_id_inside_herdr_and_report_metadata_once(self):
        self.e.set_workspaces_real()
        r = self.e.sh("set_workspace_default 2", env=HERDR)
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        self.assertEqual(self.e.ws_file("w26"), "2\n")
        calls = self.herdr_calls("workspace", "report-metadata")
        self.assertEqual(len(calls), 1)
        argv = calls[0]
        self.assertEqual(argv[:7], ["workspace", "report-metadata", "w26", "--source", "claude-accounts",
                                    "--token", "account=c2"])
        self.assertEqual(argv[7], "--seq")
        self.assertRegex(argv[8], r"^\d{13}$")
        self.assertLess(abs(int(argv[8]) - time.time() * 1000), 60000)

    def test_seq_is_epoch_ms_and_increases(self):
        self.e.set_workspaces_real()
        seqs = []
        for _ in range(3):
            self.e.sh("set_workspace_default 1 w26")
            time.sleep(0.01)
        seqs = [int(c[8]) for c in self.herdr_calls("workspace", "report-metadata")]
        self.assertEqual(len(seqs), 3)
        self.assertEqual(seqs, sorted(set(seqs)))

    def test_explicit_id_works_outside_herdr_and_overwrites(self):
        self.e.set_workspaces(("wB2", 2, "b"))
        self.assertEqual(self.e.sh("set_workspace_default 3 wB2").returncode, 0)
        self.assertEqual(self.e.ws_file("wB2"), "3\n")
        self.assertEqual(self.e.sh("set_workspace_default 1 wB2").returncode, 0)
        self.assertEqual(self.e.ws_file("wB2"), "1\n")
        self.assertEqual([p.name for p in (self.e.acct / "workspace-default").iterdir()], ["wB2"])  # no .tmp.*

    def test_bad_id_is_rc0_and_writes_nothing(self):
        for bad in ("../evil", "x1", "w/1", "w 1", "w"):
            self.assertEqual(self.e.sh('set_workspace_default 1 "$1"', bad).returncode, 0, bad)
        self.assertFalse((self.e.acct / "workspace-default").exists())
        r = self.e.sh("set_workspace_default 1", env={"HERDR_ENV": "1", "HERDR_WORKSPACE_ID": "../x"})
        self.assertEqual(r.returncode, 0)
        self.assertFalse((self.e.acct / "workspace-default").exists())

    def test_parallel_writers_all_land(self):
        ids = [f"w{i}" for i in range(1, 9)]
        self.e.set_workspaces(*[(i, n, f"l{n}") for n, i in enumerate(ids, 1)])
        procs = [self.e.popen(["bash", "-c", '. "$HOME/.claude-accounts/lib.sh"; set_workspace_default "$1" "$2"',
                               "bash", str(n % 3 + 1), i]) for n, i in enumerate(ids)]
        for p in procs:
            self.assertEqual(p.wait(timeout=30), 0)
        wd = self.e.acct / "workspace-default"
        self.assertEqual(sorted(p.name for p in wd.iterdir()), sorted(ids))
        for n, i in enumerate(ids):
            self.assertEqual(self.e.ws_file(i), f"{n % 3 + 1}\n", i)

    def test_hanging_report_metadata_returns_within_6s(self):
        self.e.set_workspaces_real()
        (self.e.stub / "report.hang").write_text("", encoding="utf-8")
        t = time.time()
        r = self.e.sh("set_workspace_default 2 w26", timeout=20)
        self.assertLess(time.time() - t, 6)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.e.ws_file("w26"), "2\n")

    def test_prune_removes_unlisted_and_keeps_listed_current_and_non_id_files(self):
        wd = self.e.acct / "workspace-default"
        wd.mkdir()
        for n in ("wGone", "wKeep", "wCur", "w.x", "w-1", "notws"):
            (wd / n).write_text("2\n", encoding="utf-8")
        self.e.set_workspaces(("wKeep", 1, "k"), ("wOther", 2, "o"))  # the current id is not even listed
        self.e.sh("set_workspace_default 1 wCur")
        self.assertEqual(sorted(p.name for p in wd.iterdir()), ["notws", "w-1", "w.x", "wCur", "wKeep"])

    def test_no_prune_when_list_fails_is_empty_or_bad(self):
        wd = self.e.acct / "workspace-default"
        wd.mkdir()
        (wd / "wOld").write_text("2\n", encoding="utf-8")
        (self.e.stub / "workspaces.fail").write_text("", encoding="utf-8")
        self.assertEqual(self.e.sh("set_workspace_default 1 wA").returncode, 0)
        (self.e.stub / "workspaces.fail").unlink()
        (self.e.stub / "workspaces.bad").write_bytes(b"{bad")
        self.assertEqual(self.e.sh("set_workspace_default 1 wA").returncode, 0)
        (self.e.stub / "workspaces.bad").unlink()
        self.e.set_workspaces()  # empty list
        self.assertEqual(self.e.sh("set_workspace_default 1 wA").returncode, 0)
        self.assertTrue((wd / "wOld").exists())
        self.assertEqual(self.e.ws_file("wA"), "1\n")

    def test_unwritable_workspace_default_is_rc1(self):
        (self.e.acct / "workspace-default").write_text("a file, not a dir", encoding="utf-8")
        self.assertEqual(self.e.sh("set_workspace_default 2 w26").returncode, 1)
        self.assertEqual(self.herdr_calls("workspace", "report-metadata"), [])

    def test_mv_failure_after_mktemp_is_rc1_leaves_no_tmp_and_does_not_report(self):
        # workspace-default/w26 is a directory the user cannot write: mktemp works, mv -f into it fails
        wd = self.e.acct / "workspace-default"
        (wd / "w26").mkdir(parents=True)
        (wd / "w26").chmod(0o500)
        try:
            r = self.e.sh("set_workspace_default 2 w26")
            self.assertEqual(r.returncode, 1, r.stderr)
            self.assertEqual([p.name for p in wd.glob(".tmp.*")], [])
            self.assertEqual(self.herdr_calls("workspace", "report-metadata"), [])
        finally:
            (wd / "w26").chmod(0o700)


class LaunchersTest(Base):
    def last(self):
        calls = self.e.claude_calls()
        self.assertEqual(len(calls), 1, calls)
        return calls[0]

    def test_c1_unsets_config_dir_even_if_the_parent_exports_it(self):
        r = self.e.run("c1", env={"CLAUDE_CONFIG_DIR": "/should/vanish"})
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        self.assertIsNone(self.last()["CLAUDE_CONFIG_DIR"])

    def test_c2_and_c3_set_their_config_dir(self):
        for n in (2, 3):
            self.e.run(f"c{n}")
            self.assertEqual(self.e.claude_calls()[-1]["CLAUDE_CONFIG_DIR"], f"{self.e.home}/.claude-{n}")

    def test_args_pass_intact(self):
        args = ["--model", "a b", "it's", "", "-x", "--", '"q"', "$HOME", "*"]
        for n in (1, 2, 3):
            self.e.run(f"c{n}", *args)
            self.assertEqual(self.e.claude_calls()[-1]["argv"], args)
        self.e.run("c", *args)
        self.assertEqual(self.e.claude_calls()[-1]["argv"], args)

    def test_link_shared_links_what_exists_in_claude_and_skips_the_rest(self):
        (self.e.home / ".claude" / "settings.local.json").unlink(missing_ok=True)
        self.e.run("c2")
        d = self.e.home / ".claude-2"
        for f in ("CLAUDE.md", "settings.json", "skills"):
            self.assertTrue((d / f).is_symlink(), f)
            self.assertEqual(os.readlink(d / f), str(self.e.home / ".claude" / f))
        for f in ("settings.local.json", ".mcp.json", "plugins", "hooks"):  # missing source: skipped
            self.assertFalse(os.path.lexists(d / f), f)

    def test_link_shared_keeps_an_existing_symlink_and_other_files(self):
        d = self.e.home / ".claude-3"
        d.mkdir()
        other = self.e.tmp / "other"
        other.write_text("x", encoding="utf-8")
        (d / "CLAUDE.md").symlink_to(other)
        (d / ".claude.json").write_text("{login}", encoding="utf-8")  # not in SHARED: untouched
        (d / "history.txt").write_text("h", encoding="utf-8")
        self.e.run("c3")
        self.assertEqual(os.readlink(d / "CLAUDE.md"), str(other))
        self.assertEqual((d / ".claude.json").read_text(encoding="utf-8"), "{login}")
        self.assertEqual((d / "history.txt").read_text(encoding="utf-8"), "h")

    def test_link_shared_replaces_a_real_file_or_dir_in_shared_pinned_hazard(self):
        # Pre-existing hazard (lib.sh link_shared: rm -rf): a real settings.json or skills/ dir in
        # ~/.claude-2 is deleted and replaced by a link. Pinned, not fixed in this scope.
        d = self.e.home / ".claude-2"
        (d / "skills").mkdir(parents=True)
        (d / "skills" / "mine.md").write_text("precious", encoding="utf-8")
        (d / "settings.json").write_text("{mine}", encoding="utf-8")
        self.e.run("c2")
        self.assertTrue((d / "skills").is_symlink())
        self.assertTrue((d / "settings.json").is_symlink())
        self.assertEqual((d / "settings.json").read_text(encoding="utf-8"), "{}\n")

    def test_unknown_account_to_run_claude_is_rc2_with_the_text(self):
        for a in ("4", "0", "x"):
            r = self.e.sh('run_claude "$1"', a)
            self.assertEqual((r.returncode, r.stdout, r.stderr), (2, "", f"unknown account '{a}' (use 1, 2 or 3)\n"))
        self.assertEqual(self.e.claude_calls(), [])

    def test_cN_inside_herdr_writes_the_workspace_file_and_reports(self):
        self.e.set_workspaces_real()
        for n in (1, 2, 3):
            self.e.run(f"c{n}", env=HERDR)
            self.assertEqual(self.e.ws_file("w26"), f"{n}\n")
            self.assertEqual(self.herdr_calls("workspace", "report-metadata")[-1][2:7],
                             ["w26", "--source", "claude-accounts", "--token", f"account=c{n}"])

    def test_cN_outside_herdr_writes_nothing(self):
        for n in (1, 2, 3):
            self.e.run(f"c{n}", env={"HERDR_WORKSPACE_ID": "w26"})
        self.assertFalse((self.e.acct / "workspace-default").exists())
        self.assertEqual(self.herdr_calls("workspace", "report-metadata"), [])
        self.assertEqual(len(self.e.claude_calls()), 3)

    def test_opt_out_skips_the_workspace_write_for_every_launcher(self):
        self.e.set_workspaces_real()
        for n in (1, 2, 3):
            self.e.run(f"c{n}", env=dict(HERDR, ACCT_NO_WS_DEFAULT="1"))
        self.assertFalse((self.e.acct / "workspace-default").exists())
        self.assertEqual(self.herdr_calls("workspace", "report-metadata"), [])
        self.assertEqual(len(self.e.claude_calls()), 3)

    def test_cN_starts_claude_even_if_the_workspace_write_fails(self):
        (self.e.acct / "workspace-default").write_text("blocker", encoding="utf-8")
        for n in (1, 2, 3):
            self.assertEqual(self.e.run(f"c{n}", env=HERDR).returncode, 0)
        self.assertEqual(len(self.e.claude_calls()), 3)

    def test_c_runs_the_default_account_and_writes_nothing(self):
        want = lambda n: None if n == 1 else f"{self.e.home}/.claude-{n}"
        self.e.run("c")
        self.assertEqual(self.e.claude_calls()[-1]["CLAUDE_CONFIG_DIR"], None)  # fallback 1
        self.e.default_file("2")
        self.e.run("c")
        self.assertEqual(self.e.claude_calls()[-1]["CLAUDE_CONFIG_DIR"], want(2))
        wd = self.e.acct / "workspace-default"
        wd.mkdir()
        (wd / "w26").write_text("3\n", encoding="utf-8")
        self.e.run("c", env=HERDR)
        self.assertEqual(self.e.claude_calls()[-1]["CLAUDE_CONFIG_DIR"], want(3))
        self.e.run("c")  # outside herdr: the global one again
        self.assertEqual(self.e.claude_calls()[-1]["CLAUDE_CONFIG_DIR"], want(2))
        for bad in ("9", "", "x"):
            (wd / "w26").write_text(bad, encoding="utf-8")
            self.e.run("c", env=HERDR)
            self.assertEqual(self.e.claude_calls()[-1]["CLAUDE_CONFIG_DIR"], want(2), repr(bad))
        self.assertEqual((self.e.acct / "default").read_text(encoding="utf-8"), "2")
        self.assertEqual(self.herdr_calls("workspace", "report-metadata"), [])


class BashrcLineTest(Base):
    """The PO's ~/.bashrc line must find the launchers and pick the account from cdefault."""
    LINE = ('export PATH="$HOME/.claude-accounts/bin:$PATH"; '
            'd=$("$HOME/.claude-accounts/bin/cdefault" 2>/dev/null); '
            'case "$d" in 2|3) export CLAUDE_CONFIG_DIR="$HOME/.claude-$d" ;; *) unset CLAUDE_CONFIG_DIR ;; esac; unset d; '
            'echo "cfg=${CLAUDE_CONFIG_DIR-<unset>}"; command -v c c1 c2 c3 cdefault cswitch')

    def run_line(self):
        r = subprocess.run(["bash", "-c", self.LINE], env=dict(self.e.env, CLAUDE_CONFIG_DIR="/stale"),
                           capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.splitlines()

    def test_default_picks_config_dir_and_path_finds_the_launchers(self):
        found = [f"{self.e.acct}/bin/{n}" for n in ("c", "c1", "c2", "c3", "cdefault", "cswitch")]
        for d, want in (("2", f"cfg={self.e.home}/.claude-2"), ("3", f"cfg={self.e.home}/.claude-3"),
                        ("1", "cfg=<unset>"), ("9", "cfg=<unset>")):
            self.e.default_file(d)
            self.assertEqual(self.run_line(), [want, *found], d)

    def test_no_default_file_unsets(self):
        self.assertEqual(self.run_line()[0], "cfg=<unset>")


class CdefaultTest(Base):
    def test_print_effective_default(self):
        self.assertEqual(self.e.run("cdefault").stdout, "1\n")
        self.e.default_file("2")
        self.assertEqual(self.e.run("cdefault").stdout, "2\n")
        wd = self.e.acct / "workspace-default"
        wd.mkdir()
        (wd / "w26").write_text("3\n", encoding="utf-8")
        self.assertEqual(self.e.run("cdefault", env=HERDR).stdout, "3\n")
        self.assertEqual(self.e.run("cdefault").stdout, "2\n")

    def test_set_global(self):
        for n in "123":
            r = self.e.run("cdefault", n)
            self.assertEqual((r.returncode, r.stdout, r.stderr), (0, f"default account: {n}\n", ""))
            self.assertEqual((self.e.acct / "default").read_text(encoding="utf-8"), n + "\n")

    def test_set_global_rejects_bad_values(self):
        for bad in ("4", "abc", "0", "12", "--x"):
            r = self.e.run("cdefault", bad)
            self.assertEqual((r.returncode, r.stdout, r.stderr), (2, "", "use 1, 2 or 3\n"), bad)
        self.assertFalse((self.e.acct / "default").exists())

    def test_ws_current_workspace_in_herdr(self):
        self.e.set_workspaces_real()
        r = self.e.run("cdefault", "--ws", "2", env=HERDR)
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "default account of w26: 2\n", ""))
        self.assertEqual(self.e.ws_file("w26"), "2\n")

    def test_ws_current_outside_herdr_is_rc2(self):
        r = self.e.run("cdefault", "--ws", "2", env={"HERDR_WORKSPACE_ID": "w26"})
        self.assertEqual((r.returncode, r.stdout, r.stderr), (2, "", "usage: not inside herdr: give a workspace\n"))
        self.assertFalse((self.e.acct / "workspace-default").exists())

    def test_ws_by_id_number_and_label(self):
        self.e.set_workspaces(("wA1", 1, "alpha"), ("wB2", 2, "beta"))
        for ref, want in (("beta", "wB2"), ("1", "wA1"), ("wB2", "wB2"), ("wZ9", "wZ9")):
            r = self.e.run("cdefault", "--ws", ref, "3")
            self.assertEqual((r.returncode, r.stdout, r.stderr), (0, f"default account of {want}: 3\n", ""), ref)
            self.assertEqual(self.e.ws_file(want), "3\n")

    def test_ws_ambiguous_and_unknown_are_rc2_and_write_nothing(self):
        self.e.set_workspaces(("wA1", 1, "dup"), ("wB2", 2, "dup"))
        r = self.e.run("cdefault", "--ws", "dup", "2")
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        self.assertIn("ambiguous: dup matches", r.stderr)
        r = self.e.run("cdefault", "--ws", "no such", "2")
        self.assertEqual((r.returncode, r.stdout, r.stderr), (2, "", "no workspace matches no such\n"))
        self.assertFalse((self.e.acct / "workspace-default").exists())

    def test_ws_bad_usage_is_rc2(self):
        usage = "usage: cdefault --ws [<workspace id|panel number|label>] <1|2|3>\n"
        for args in (["--ws"], ["--ws", "4"], ["--ws", "w26", "4"], ["--ws", "a", "b", "1"],
                     ["--ws", "a", "1", "extra"], ["--ws", "w26", "1", "2", "3"]):
            r = self.e.run("cdefault", *args, env=HERDR)
            self.assertEqual((r.returncode, r.stdout, r.stderr), (2, "", usage), args)
        self.assertFalse((self.e.acct / "workspace-default").exists())

    def test_ws_write_failure_is_rc1(self):
        (self.e.acct / "workspace-default").write_text("blocker", encoding="utf-8")
        r = self.e.run("cdefault", "--ws", "w26", "2")
        self.assertEqual((r.returncode, r.stdout, r.stderr), (1, "", "could not write the workspace default\n"))


class CswitchTest(Base):
    def test_usage_errors_are_rc2(self):
        for args in ([], ["4"], ["x"], ["0"]):
            r = self.e.run("cswitch", *args, env=HERDR)
            self.assertEqual((r.returncode, r.stdout, r.stderr), (2, "", "usage: cswitch 1|2|3 [pane]\n"), args)

    def test_outside_herdr_is_rc1(self):
        r = self.e.run("cswitch", "2", PANE)
        self.assertEqual((r.returncode, r.stdout, r.stderr), (1, "", "not inside Herdr\n"))

    def test_pane_without_a_session_is_rc1(self):
        self.e.set_pane("pane-get-nosession.derived.json")
        r = self.e.run("cswitch", "2", PANE, env=HERDR)
        self.assertEqual((r.returncode, r.stdout, r.stderr), (1, "", f"no Claude session found in pane {PANE}\n"))
        self.assertEqual(self.herdr_calls("agent", "wait"), [])

    def test_herdr_pane_get_failure_is_rc1(self):
        r = self.e.run("cswitch", "2", PANE, env=HERDR)  # the stub has no such pane: rc 1
        self.assertEqual((r.returncode, r.stderr), (1, f"no Claude session found in pane {PANE}\n"))

    def test_happy_path_resumes_on_the_new_account_with_the_original_args(self):
        sid = json.loads((FIX / "pane-get-claude.real.json").read_text(encoding="utf-8"))[
            "result"]["pane"]["agent_session"]["value"]
        self.e.set_pane()
        self.e.set_agents()
        self.e.set_workspaces_real()
        decoy = self.e.spawn_decoy(PANE)  # `claude daemon run` of the same pane, first in pgrep's list
        launch = ["--agent", "x", "--settings", "s", "--model", "m", "--session-id", "S", "--resume", "R",
                  "-r", "R2", "-c", "--continue", "--session-id=S2", "--resume=R3"]
        old = self.e.spawn_claude(PANE, launch)
        r = self.e.popen([str(self.e.acct / "bin" / "cswitch"), "2"], session=True,
                         env=dict(HERDR, HERDR_PANE_ID=PANE, CLAUDE_STUB_MODE="sleep"),
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        out, err = r.communicate(timeout=30)
        self.assertEqual((r.returncode, err), (0, ""))
        self.assertEqual(out, f"will resume session {sid} on account 2 in pane {PANE} once idle\n")
        log = self.e.acct / "cswitch.log"
        done = re.compile(rf" {re.escape(PANE)} plugin-tech-ca-repo done$", re.M)
        self.e.wait_for(lambda: log.exists() and done.search(log.read_text(encoding="utf-8")),
                        "no ' done' line in cswitch.log: " + (log.read_text(encoding="utf-8") if log.exists() else "<no log>"))
        text = log.read_text(encoding="utf-8")
        self.assertNotIn("FAILED", text)
        self.assertRegex(text.splitlines()[0], rf"^\S+ {re.escape(PANE)} plugin-tech-ca-repo -> account 2: ")

        # the typed command: the launcher with the original args, old resume/session flags dropped, one --resume
        # (the stub claude runs as `python3 <stub> args`, so the stub path is its first "arg", as in /proc)
        stub = str(self.e.stub / "bin" / "claude")
        want = [f"{self.e.acct}/bin/c2", stub, "--agent", "x", "--settings", "s", "--model", "m", "--resume", sid]
        runs = self.herdr_calls("pane", "run")
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0][:2], ["pane", "run"])
        self.assertEqual(runs[0][2], PANE)
        self.assertEqual(shlex.split(runs[0][3]), want)
        self.assertIn(f"-> account 2: {runs[0][3]}", text.splitlines()[0])

        # order of the herdr calls of the detached part
        kinds = [c[:2] for c in self.e.herdr_calls() if c[0] in ("agent", "pane")]
        self.assertEqual(kinds[:3], [["pane", "get"], ["agent", "list"], ["agent", "wait"]])
        self.assertEqual(self.herdr_calls("agent", "wait"), [["agent", "wait", PANE, "--timeout", "600000"]])
        self.assertEqual(self.herdr_calls("agent", "prompt"), [["agent", "prompt", PANE, "/exit"]])
        self.assertEqual(self.herdr_calls("agent", "rename"), [["agent", "rename", PANE, "plugin-tech-ca-repo"]])
        order = [c[:2] for c in self.e.herdr_calls()]
        self.assertLess(order.index(["agent", "prompt"]), order.index(["pane", "run"]))
        self.assertLess(order.index(["pane", "run"]), order.index(["agent", "rename"]))

        # the old claude was told to exit; the new one runs on account 2 with the same args
        self.assertTrue(old.wait(timeout=5) is not None and not live(old.pid))
        self.assertIsNone(decoy.poll())  # the daemon look-alike was neither used nor killed
        new = [c for c in self.e.claude_calls() if c["CLAUDE_CONFIG_DIR"]]
        self.assertEqual(len(new), 1, self.e.claude_calls())
        self.assertEqual(new[0]["CLAUDE_CONFIG_DIR"], f"{self.e.home}/.claude-2")
        self.assertEqual(new[0]["argv"], want[1:])
        self.assertEqual(new[0]["HERDR_PANE_ID"], PANE)
        self.assertEqual(self.e.ws_file("w26"), "2\n")  # c2 inside herdr records the workspace default


    def _switch_and_wait(self, expect_name, others=()):
        """cswitch 2 in PANE with one stub claude per pane in `others` registered first; returns the log text."""
        self.e.set_pane()
        self.e.set_workspaces_real()
        for pane, args in others:
            self.e.spawn_claude(pane, args)
        self.e.spawn_claude(PANE, ["--agent", "target", "--model", "m"])
        r = self.e.popen([str(self.e.acct / "bin" / "cswitch"), "2"], session=True,
                         env=dict(HERDR, HERDR_PANE_ID=PANE, CLAUDE_STUB_MODE="sleep"),
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        r.communicate(timeout=30)
        self.assertEqual(r.returncode, 0)
        log = self.e.acct / "cswitch.log"
        done = re.compile(rf" {re.escape(PANE)} {re.escape(expect_name)} done$", re.M)
        self.e.wait_for(lambda: log.exists() and done.search(log.read_text(encoding="utf-8")),
                        "no ' done' line in cswitch.log: " + (log.read_text(encoding="utf-8") if log.exists() else "<no log>"))
        return log.read_text(encoding="utf-8")

    def test_takes_the_args_of_the_target_pane_not_of_another_panes_claude(self):
        self.e.set_agents()
        self._switch_and_wait("plugin-tech-ca-repo",
                              others=[("w26:p9", ["--agent", "other", "--model", "WRONG"])])
        runs = self.herdr_calls("pane", "run")
        self.assertEqual(len(runs), 1)
        typed = shlex.split(runs[0][3])
        self.assertIn("target", typed)
        self.assertNotIn("other", typed)
        self.assertNotIn("WRONG", typed)
        # only the target pane's claude was told to exit
        self.assertEqual(self.herdr_calls("agent", "prompt"), [["agent", "prompt", PANE, "/exit"]])

    def test_pane_without_an_agent_name_is_not_renamed(self):
        listing = json.loads((FIX / "agent-list.real.json").read_text(encoding="utf-8"))
        for a in listing["result"]["agents"]:
            if a["pane_id"] == PANE:
                a.pop("name", None)
        (self.e.stub / "agents.json").write_text(json.dumps(listing), encoding="utf-8")
        text = self._switch_and_wait("?")
        self.assertEqual(self.herdr_calls("agent", "rename"), [])
        self.assertRegex(text.splitlines()[0], rf"^\S+ {re.escape(PANE)} \? -> account 2: ")
        self.assertNotIn("FAILED", text)


if __name__ == "__main__":
    unittest.main()
