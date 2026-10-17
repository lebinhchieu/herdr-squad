"""claude-accounts: lib.sh functions and the c, c1-c3, cdefault, cswitch launchers, run against stub herdr/claude."""
import json
import time
import unittest

from ca_stubs import Env

HERDR = {"HERDR_ENV": "1", "HERDR_WORKSPACE_ID": "wA1"}


class Base(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.cleanup)


class WsIdOkTest(Base):
    def test_accepts_and_rejects(self):
        for good in ("w1", "wA1", "w12abZ"):
            self.assertEqual(self.e.sh(f'ws_id_ok {good}').returncode, 0, good)
        for bad in ("", "w", "x1", "w1/../x", "w 1", "w1.", "../w1", "w-1"):
            self.assertNotEqual(self.e.sh(f'ws_id_ok "{bad}"').returncode, 0, bad)


class DefaultAccountTest(Base):
    def default(self, env=None):
        r = self.e.sh("default_account", env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip()

    def test_global_default_is_1_without_file(self):
        self.assertEqual(self.default(), "1")

    def test_global_default_read_and_invalid_falls_back(self):
        self.e.default_file("3\n")
        self.assertEqual(self.default(), "3")
        for junk in ("4", "", "abc", "0"):
            self.e.default_file(junk)
            self.assertEqual(self.default(), "1", junk)

    def test_workspace_default_wins_inside_herdr_only(self):
        self.e.default_file("2")
        (self.e.acct / "workspace-default").mkdir()
        (self.e.acct / "workspace-default" / "wA1").write_text("3\n")
        self.assertEqual(self.default(HERDR), "3")
        self.assertEqual(self.default({"HERDR_WORKSPACE_ID": "wA1"}), "2")  # no HERDR_ENV

    def test_invalid_workspace_file_or_id_falls_back_to_global(self):
        self.e.default_file("2")
        (self.e.acct / "workspace-default").mkdir()
        (self.e.acct / "workspace-default" / "wA1").write_text("9")
        self.assertEqual(self.default(HERDR), "2")
        self.assertEqual(self.default({"HERDR_ENV": "1", "HERDR_WORKSPACE_ID": "../x"}), "2")


class ResolveWorkspaceTest(Base):
    def resolve(self, ref):
        return self.e.sh(f'resolve_workspace "{ref}"')

    def test_by_id_number_and_label(self):
        self.e.herdr_workspaces(("wA1", 1, "alpha"), ("wB2", 2, "beta"))
        for ref, want in (("wB2", "wB2"), ("2", "wB2"), ("alpha", "wA1")):
            r = self.resolve(ref)
            self.assertEqual((r.returncode, r.stdout.strip()), (0, want), ref)

    def test_id_tier_beats_number_and_label(self):
        self.e.herdr_workspaces(("w7", 1, "x"), ("wC", 7, "w7"))
        self.assertEqual(self.resolve("w7").stdout.strip(), "w7")

    def test_ambiguous_label_lists_candidates_rc2(self):
        self.e.herdr_workspaces(("wA1", 1, "dup"), ("wB2", 2, "dup"))
        r = self.resolve("dup")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stdout, "")
        self.assertIn("ambiguous", r.stderr)
        self.assertIn("wA1 (panel 1) dup", r.stderr)
        self.assertIn("wB2 (panel 2) dup", r.stderr)

    def test_no_hit_idshaped_taken_raw_else_rc2(self):
        self.e.herdr_workspaces(("wA1", 1, "alpha"))
        r = self.resolve("wZ9")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "wZ9"))
        r = self.resolve("nothing here")
        self.assertEqual(r.returncode, 2)
        self.assertIn("no workspace matches nothing here", r.stderr)

    def test_herdr_failure_falls_back_to_raw_id(self):
        # no ws-list.json: the stub herdr exits 1
        self.assertEqual(self.resolve("wQ1").stdout.strip(), "wQ1")
        self.assertEqual(self.resolve("alpha").returncode, 2)

    def test_blank_ref_rc2(self):
        self.assertEqual(self.resolve("  ").returncode, 2)

    def test_matched_id_that_is_not_id_shaped_is_not_returned(self):
        self.e.herdr_workspaces(("bad/id", 1, "alpha"))
        r = self.resolve("alpha")
        self.assertEqual(r.returncode, 2)


class SetWorkspaceDefaultTest(Base):
    def test_writes_file_and_reports_metadata_inside_herdr(self):
        self.e.herdr_workspaces(("wA1", 1, "a"))
        r = self.e.sh("set_workspace_default 2", HERDR)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.e.ws_file("wA1"), "2")
        calls = self.e.herdr_calls()
        self.assertTrue(any(c.startswith("workspace report-metadata wA1 --source claude-accounts --token account=c2 --seq ")
                            for c in calls), calls)

    def test_noop_outside_herdr_without_explicit_id(self):
        r = self.e.sh("set_workspace_default 2")
        self.assertEqual(r.returncode, 0)
        self.assertFalse((self.e.acct / "workspace-default").exists())

    def test_explicit_id_works_outside_herdr(self):
        self.e.herdr_workspaces(("wB2", 2, "b"))
        self.assertEqual(self.e.sh("set_workspace_default 3 wB2").returncode, 0)
        self.assertEqual(self.e.ws_file("wB2"), "3")

    def test_bad_account_rc2_and_bad_id_noop(self):
        self.assertEqual(self.e.sh("set_workspace_default 4 wA1").returncode, 2)
        self.assertEqual(self.e.sh("set_workspace_default x wA1").returncode, 2)
        self.assertEqual(self.e.sh("set_workspace_default 1 '../evil'").returncode, 0)
        self.assertFalse((self.e.acct / "workspace-default").exists())

    def test_overwrite_and_no_tmp_left(self):
        self.e.herdr_workspaces(("wA1", 1, "a"))
        self.e.sh("set_workspace_default 2", HERDR)
        self.e.sh("set_workspace_default 3", HERDR)
        self.assertEqual(self.e.ws_file("wA1"), "3")
        self.assertEqual([p.name for p in (self.e.acct / "workspace-default").iterdir()], ["wA1"])

    def test_prunes_files_of_workspaces_herdr_no_longer_lists(self):
        wd = self.e.acct / "workspace-default"
        wd.mkdir()
        (wd / "wGone").write_text("2")
        (wd / "wKeep").write_text("2")
        (wd / "notws").write_text("keep me")  # not id-shaped: never pruned
        self.e.herdr_workspaces(("wA1", 1, "a"), ("wKeep", 2, "k"))
        self.e.sh("set_workspace_default 1", HERDR)
        self.assertEqual(sorted(p.name for p in wd.iterdir()), ["notws", "wA1", "wKeep"])

    def test_no_prune_when_list_fails_or_is_empty(self):
        wd = self.e.acct / "workspace-default"
        wd.mkdir()
        (wd / "wOld").write_text("2")
        self.e.sh("set_workspace_default 1", HERDR)  # herdr list fails
        self.assertTrue((wd / "wOld").exists())
        self.e.herdr_workspaces()  # empty list
        self.e.sh("set_workspace_default 1", HERDR)
        self.assertTrue((wd / "wOld").exists())

    def test_unwritable_dir_returns_1(self):
        (self.e.acct / "workspace-default").write_text("a file, not a dir")
        self.assertEqual(self.e.sh("set_workspace_default 2", HERDR).returncode, 1)


class RunClaudeTest(Base):
    def test_account_1_unsets_config_dir_and_passes_args(self):
        r = self.e.run("c1", "--model", "x y", env={"CLAUDE_CONFIG_DIR": "/should/vanish"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.e.claude_out(), ["CLAUDE_CONFIG_DIR=<unset>", "ARG=--model", "ARG=x y"])

    def test_accounts_2_and_3_set_config_dir_and_link_shared(self):
        (self.e.home / ".claude" / "CLAUDE.md").write_text("hi")
        (self.e.home / ".claude" / "skills").mkdir()
        for n in (2, 3):
            r = self.e.run(f"c{n}", "-p", "hello")
            self.assertEqual(r.returncode, 0, r.stderr)
            d = self.e.home / f".claude-{n}"
            self.assertEqual(self.e.claude_out(), [f"CLAUDE_CONFIG_DIR={d}", "ARG=-p", "ARG=hello"])
            self.assertEqual((d / "CLAUDE.md").resolve(), (self.e.home / ".claude" / "CLAUDE.md").resolve())
            self.assertTrue((d / "skills").is_symlink())
            self.assertFalse((d / "settings.json").exists())  # absent in ~/.claude: not linked

    def test_link_shared_keeps_existing_links_and_replaces_real_files(self):
        (self.e.home / ".claude" / "CLAUDE.md").write_text("src")
        (self.e.home / ".claude" / "settings.json").write_text("{}")
        d = self.e.home / ".claude-2"
        d.mkdir()
        (d / "settings.json").write_text("stale real file")
        other = self.e.tmp / "other"
        other.write_text("x")
        (d / "CLAUDE.md").symlink_to(other)
        self.e.run("c2")
        self.assertEqual((d / "CLAUDE.md").resolve(), other.resolve())  # existing symlink left alone
        self.assertTrue((d / "settings.json").is_symlink())

    def test_unknown_account_rc2(self):
        r = self.e.sh("run_claude 4")
        self.assertEqual(r.returncode, 2)
        self.assertIn("unknown account '4'", r.stderr)
        self.assertIsNone(self.e.claude_out())


class LaunchersTest(Base):
    def test_c_uses_global_default(self):
        self.e.default_file("2")
        self.e.run("c", "a")
        self.assertEqual(self.e.claude_out(), [f"CLAUDE_CONFIG_DIR={self.e.home}/.claude-2", "ARG=a"])

    def test_c_without_default_is_account_1(self):
        self.e.run("c")
        self.assertEqual(self.e.claude_out(), ["CLAUDE_CONFIG_DIR=<unset>"])

    def test_c_uses_workspace_default_in_herdr_and_does_not_set_it(self):
        self.e.default_file("1")
        (self.e.acct / "workspace-default").mkdir()
        (self.e.acct / "workspace-default" / "wA1").write_text("3")
        self.e.run("c", env=HERDR)
        self.assertEqual(self.e.claude_out(), [f"CLAUDE_CONFIG_DIR={self.e.home}/.claude-3"])
        self.assertEqual(self.e.ws_file("wA1"), "3")

    def test_cN_sets_workspace_default_in_herdr(self):
        self.e.herdr_workspaces(("wA1", 1, "a"))
        for n in (1, 2, 3):
            self.e.run(f"c{n}", env=HERDR)
            self.assertEqual(self.e.ws_file("wA1"), str(n))

    def test_cN_does_not_set_workspace_default_outside_herdr_or_when_opted_out(self):
        self.e.run("c2")
        self.assertFalse((self.e.acct / "workspace-default").exists())
        self.e.run("c2", env=dict(HERDR, ACCT_NO_WS_DEFAULT="1"))
        self.assertFalse((self.e.acct / "workspace-default").exists())
        self.assertEqual(self.e.claude_out()[0], f"CLAUDE_CONFIG_DIR={self.e.home}/.claude-2")

    def test_cN_launches_even_if_workspace_default_cannot_be_written(self):
        (self.e.acct / "workspace-default").write_text("blocker")
        r = self.e.run("c3", env=HERDR)
        self.assertEqual(r.returncode, 0)
        self.assertIsNotNone(self.e.claude_out())


class CdefaultTest(Base):
    def test_print_global_and_workspace(self):
        self.assertEqual(self.e.run("cdefault").stdout, "1\n")
        self.e.default_file("2")
        self.assertEqual(self.e.run("cdefault").stdout, "2\n")
        (self.e.acct / "workspace-default").mkdir()
        (self.e.acct / "workspace-default" / "wA1").write_text("3")
        self.assertEqual(self.e.run("cdefault", env=HERDR).stdout, "3\n")

    def test_set_global(self):
        r = self.e.run("cdefault", "3")
        self.assertEqual((r.returncode, r.stdout), (0, "default account: 3\n"))
        self.assertEqual((self.e.acct / "default").read_text().strip(), "3")

    def test_set_global_rejects_bad_value(self):
        for bad in ("4", "x", "12"):
            r = self.e.run("cdefault", bad)
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn("use 1, 2 or 3", r.stderr)
        self.assertFalse((self.e.acct / "default").exists())

    def test_ws_current_workspace_in_herdr(self):
        self.e.herdr_workspaces(("wA1", 1, "a"))
        r = self.e.run("cdefault", "--ws", "2", env=HERDR)
        self.assertEqual((r.returncode, r.stdout), (0, "default account of wA1: 2\n"))
        self.assertEqual(self.e.ws_file("wA1"), "2")

    def test_ws_current_outside_herdr_is_usage_error(self):
        r = self.e.run("cdefault", "--ws", "2")
        self.assertEqual(r.returncode, 2)
        self.assertIn("not inside herdr", r.stderr)

    def test_ws_by_label_number_and_id(self):
        self.e.herdr_workspaces(("wA1", 1, "alpha"), ("wB2", 2, "beta"))
        for ref, want in (("beta", "wB2"), ("1", "wA1"), ("wB2", "wB2")):
            r = self.e.run("cdefault", "--ws", ref, "3")
            self.assertEqual((r.returncode, r.stdout), (0, f"default account of {want}: 3\n"), ref)
            self.assertEqual(self.e.ws_file(want), "3")

    def test_ws_ambiguous_and_unknown_rc2_nothing_written(self):
        self.e.herdr_workspaces(("wA1", 1, "dup"), ("wB2", 2, "dup"))
        r = self.e.run("cdefault", "--ws", "dup", "2")
        self.assertEqual(r.returncode, 2)
        self.assertIn("ambiguous", r.stderr)
        r = self.e.run("cdefault", "--ws", "no such", "2")
        self.assertEqual(r.returncode, 2)
        self.assertFalse((self.e.acct / "workspace-default").exists())

    def test_ws_bad_usage(self):
        for args in (["--ws"], ["--ws", "9"], ["--ws", "wA1", "9"], ["--ws", "a", "b", "1"]):
            r = self.e.run("cdefault", *args, env=HERDR)
            self.assertEqual(r.returncode, 2, args)
            self.assertIn("usage: cdefault --ws", r.stderr)

    def test_ws_write_failure_rc1(self):
        (self.e.acct / "workspace-default").write_text("blocker")
        r = self.e.run("cdefault", "--ws", "wA1", "2")
        self.assertEqual(r.returncode, 1)
        self.assertIn("could not write", r.stderr)


class CswitchTest(Base):
    def pane(self, session="sess-123"):
        agent = {"value": session} if session else None
        (self.e.log / "pane-get.json").write_text(json.dumps({"result": {"pane": {"agent_session": agent}}}))

    def nohup_argv(self):
        # cswitch backgrounds the nohup job; wait for the stub to have written it (a file that stays).
        f = self.e.log / "nohup.argv"
        for _ in range(100):
            if f.exists() and f.stat().st_size:
                break
            time.sleep(0.05)
        self.assertTrue(f.exists(), "nohup stub never ran")
        return f.read_bytes().split(b"\0")[:-1]

    def test_usage_errors(self):
        for args in ([], ["4"], ["x"]):
            r = self.e.run("cswitch", *args, env=HERDR)
            self.assertEqual(r.returncode, 2, args)
            self.assertIn("usage: cswitch 1|2|3 [pane]", r.stderr)

    def test_outside_herdr_rc1(self):
        r = self.e.run("cswitch", "2")
        self.assertEqual(r.returncode, 1)
        self.assertIn("not inside Herdr", r.stderr)

    def test_no_claude_session_rc1(self):
        self.pane(session=None)
        r = self.e.run("cswitch", "2", "p1", env=HERDR)
        self.assertEqual(r.returncode, 1)
        self.assertIn("no Claude session found in pane p1", r.stderr)
        self.assertFalse((self.e.log / "nohup.argv").exists())  # failed before the job was scheduled

    def test_herdr_pane_get_failure_rc1(self):
        r = self.e.run("cswitch", "2", "p1", env=HERDR)
        self.assertEqual(r.returncode, 1)

    def test_schedules_resume_on_the_chosen_account(self):
        self.pane("sess-123")
        (self.e.log / "agent-list.json").write_text(json.dumps(
            {"result": {"agents": [{"pane_id": "p9", "name": "other"}, {"pane_id": "p1", "name": "my agent"}]}}))
        r = self.e.run("cswitch", "3", "p1", env=HERDR)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "will resume session sess-123 on account 3 in pane p1 once idle\n")
        argv = self.nohup_argv()
        self.assertEqual(argv[:3], [b"bash", b"-c", argv[2]])
        pane, cmd, name = (x.decode() for x in argv[-3:])
        self.assertEqual((pane, name), ("p1", "my agent"))
        self.assertEqual(cmd.split(), [f"{self.e.acct}/bin/c3", "--resume", "sess-123"])
        log = (self.e.acct / "cswitch.log").read_text()
        self.assertIn("p1 my agent -> account 3:", log)

    def test_pane_defaults_to_herdr_pane_id_and_missing_agent_name_is_empty(self):
        self.pane()
        r = self.e.run("cswitch", "1", env=dict(HERDR, HERDR_PANE_ID="pZ"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("in pane pZ", r.stdout)
        argv = self.nohup_argv()
        self.assertEqual(argv[-1], b"")
        self.assertIn("pZ ? -> account 1", (self.e.acct / "cswitch.log").read_text())
        self.assertIn("pane get pZ", self.e.herdr_calls())


if __name__ == "__main__":
    unittest.main()
