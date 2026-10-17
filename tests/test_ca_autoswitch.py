"""claude-accounts: cautoswitch, usage-popup.sh, record-usage.sh, on the shared harness tests/ca_stubs.py
(temp HOME, stub herdr/claude/pgrep, no network, every started process killed by pid in cleanup).

record-usage.sh input shape (verified against the live status line, ~/.claude/statusline-command.sh):
  record-usage.sh SESSION_ID FIVE_PCT FIVE_RESETS WEEK_PCT WEEK_RESETS
the four values come from the status-line JSON .rate_limits.{five_hour,seven_day}.{used_percentage,resets_at}.
REAL below is one line the live pipeline wrote (usage-1 of the live home). Before the first API reply of a
session the JSON has no rate_limits, so the four values are empty strings (the idle case); nothing is written.

Gap (no offline test possible): the live-fetch branch of usage-popup.sh and cautoswitch.usage(), which call
api.anthropic.com with a valid token. QA whitebox does one read-only live run of `echo x | usage-popup.sh`."""
import importlib.machinery
import importlib.util
import json
import os
import py_compile
import re
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ca_stubs  # noqa: E402
from ca_stubs import SRC, Env, requires_linux  # noqa: E402

REAL = ("10", "1792274400", "79", "1792461600")  # used %, reset epoch, used %, reset epoch

# stands in for the real cswitch (which detaches and drives herdr): records the call, writes the " done" line.
CSWITCH = """#!/usr/bin/env bash
echo "$1 $2" >> "$HOME/cswitch.calls"
echo "$(date -Is) $2 stub done" >> "$HOME/.claude-accounts/cswitch.log"
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.cleanup)
        self.H = self.e.acct
        self.e.env["TZ"] = "UTC"
        self.e.set_workspaces(("w1", 1, "one"), ("w2", 2, "two"))

    def usage_file(self, acct, five, week, age=0, r5="1792274400", r7="1792461600"):
        (self.H / f"usage-{acct}").write_text(f"{five} {r5} {week} {r7} {int(time.time()) - age}\n",
                                              encoding="utf-8")

    def write_creds(self, acct, expires_ms):
        """A fake login. A future expiry would make cautoswitch/popup call the real API: refused."""
        if expires_ms / 1000 > time.time():
            raise AssertionError("a test login must be expired: a valid token reaches the network")
        d = self.e.home / (".claude" if acct == "1" else f".claude-{acct}")
        d.mkdir(exist_ok=True)
        (d / ".credentials.json").write_text(
            json.dumps({"claudeAiOauth": {"accessToken": "fake", "expiresAt": expires_ms}}), encoding="utf-8")

    def log(self):
        p = self.H / "cswitch.log"
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def stub_cswitch(self):
        p = self.H / "bin" / "cswitch"
        p.unlink()
        p.write_text(CSWITCH, encoding="utf-8")
        p.chmod(0o755)

    def switch_calls(self):
        p = self.e.home / "cswitch.calls"
        return p.read_text(encoding="utf-8").splitlines() if p.exists() else []


@requires_linux
class RecordUsageTest(Base):
    def rec(self, *args, **env):
        return subprocess.run([str(self.H / "record-usage.sh"), *args], env={**self.e.env, **env},
                              capture_output=True, text=True, encoding="utf-8", timeout=20)

    def fields(self, acct="1"):
        return (self.H / f"usage-{acct}").read_text(encoding="utf-8").split()

    def test_account_1_without_config_dir(self):
        before = int(time.time())
        r = self.rec("sess-1", *REAL)
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        five, r5, week, r7, at = self.fields()
        self.assertEqual((five, r5, week, r7), REAL)
        self.assertTrue(before <= int(at) <= int(time.time()))

    def test_account_from_config_dir_suffix(self):
        r = self.rec("s", *REAL, CLAUDE_CONFIG_DIR=str(self.e.home / ".claude-3"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.fields("3")[:4], list(REAL))
        self.assertFalse((self.H / "usage-1").exists())
        self.assertFalse((self.H / "usage-2").exists())

    def test_constant_usage_overwrites_one_line(self):
        self.rec("s", *REAL)
        self.rec("s", *REAL)
        self.assertEqual(len((self.H / "usage-1").read_text(encoding="utf-8").splitlines()), 1)
        self.rec("s", "11", "1792274400", "80", "1792461600")
        self.assertEqual(self.fields()[:4], ["11", "1792274400", "80", "1792461600"])

    def test_idle_status_line_writes_nothing_and_keeps_the_old_cache(self):
        self.rec("s", "", "", "", "")
        self.assertFalse((self.H / "usage-1").exists())
        self.rec("s", *REAL)
        old = (self.H / "usage-1").read_text(encoding="utf-8")
        self.rec("s", "", "", "", "")
        self.assertEqual((self.H / "usage-1").read_text(encoding="utf-8"), old)

    def test_no_args_writes_nothing(self):
        self.rec()
        self.assertEqual(list(self.H.glob("usage-[0-9]")), [])


@requires_linux
class PopupTest(Base):
    def popup(self):
        r = subprocess.run([str(self.H / "usage-popup.sh")], env=self.e.env, input="x", capture_output=True,
                           text=True, encoding="utf-8", timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    @staticmethod
    def section(out, acct):
        parts = out.split(f"  c{acct}")
        assert len(parts) == 2, out
        return parts[1].split("\n\n")[0]

    def test_no_logins_no_cache_names_only_the_reason(self):
        out = self.popup()
        for a in "123":
            self.assertEqual(self.section(out, a).split("\n")[0].strip(), "not logged in" if a != "1"
                             else "(default)   not logged in")
        self.assertNotIn("5h", out)
        self.assertIn("press any key to close", out)

    def test_cache_shown_for_a_logged_out_account(self):
        self.usage_file(2, "40", "79", age=600)
        s = self.section(self.popup(), "2")
        self.assertIn("not logged in; cached 10m ago", s)
        self.assertIn("5h  ####......  40%", s)
        self.assertIn("7d  ########..  79%", s)
        r5 = datetime.fromtimestamp(1792274400, timezone.utc).strftime("%H:%M")
        r7 = datetime.fromtimestamp(1792461600, timezone.utc).strftime("%a %H:%M")
        self.assertIn(f"resets {r5}", s)
        self.assertIn(f"resets {r7}", s)

    def test_default_marker_follows_the_global_default_file(self):
        self.assertIn("c1  (default)", self.popup())
        self.e.default_file("2")
        out = self.popup()
        self.assertIn("c2  (default)", out)
        self.assertNotIn("c1  (default)", out)

    def test_expired_token_falls_back_to_the_cache(self):
        self.write_creds("2", int((time.time() - 3600) * 1000))
        self.usage_file(2, "68", "21", age=120, r5="0", r7="0")
        s = self.section(self.popup(), "2")
        self.assertIn("token expired - run it once to refresh; cached 2m ago", s)
        self.assertIn("68%", s)
        self.assertIn("resets -", s)  # an idle account has no reset time (0)

    def test_expired_token_and_no_cache_shows_only_the_reason(self):
        self.write_creds("3", int((time.time() - 3600) * 1000))
        s = self.section(self.popup(), "3")
        self.assertIn("token expired - run it once to refresh", s)
        self.assertNotIn("cached", s)
        self.assertNotIn("5h", s)

    def test_malformed_cache_is_ignored(self):
        (self.H / "usage-1").write_text("garbage\n", encoding="utf-8")
        s = self.section(self.popup(), "1")
        self.assertIn("not logged in", s)
        self.assertNotIn("5h", s)

    def test_bar_is_clamped_at_ten(self):
        self.usage_file(1, "150", "0", age=1)
        s = self.section(self.popup(), "1")
        self.assertIn("##########", s)
        self.assertNotIn("###########", s)


@requires_linux
class AutoswitchTest(Base):
    def pane(self, name, pane, ws, acct):
        """A stub claude of a squad pane (sleep mode, registered with the stub pgrep)."""
        extra = {"HERDR_WORKSPACE_ID": ws}
        if name:
            extra["SQUAD_NAME"] = name
        if acct != "1":
            extra["CLAUDE_CONFIG_DIR"] = str(self.e.home / f".claude-{acct}")
        return self.e.spawn_claude(pane, extra_env=extra)

    def auto(self, *args, herdr=True, env=None, timeout=90):
        e = dict(self.e.env, **(env or {}))
        if herdr:
            e["HERDR_ENV"] = "1"
        return subprocess.run([str(self.H / "bin" / "cautoswitch"), "--once", *args], env=e, capture_output=True,
                              text=True, encoding="utf-8", timeout=timeout)

    def ws_default(self, ws):
        return (self.e.ws_file(ws) or "").strip() or None

    def module(self):
        """cautoswitch loaded in this process under the harness HOME/PATH (for pending() and two ticks)."""
        spec = importlib.util.spec_from_loader(
            "cautoswitch_t", importlib.machinery.SourceFileLoader("cautoswitch_t", str(SRC / "bin" / "cautoswitch")))
        mod = importlib.util.module_from_spec(spec)
        old, sys.dont_write_bytecode = sys.dont_write_bytecode, True  # no __pycache__ in the repo
        try:
            spec.loader.exec_module(mod)
        finally:
            sys.dont_write_bytecode = old
        return mod

    def test_syntax_checks_leave_no_pycache(self):
        with tempfile.TemporaryDirectory() as d:
            py_compile.compile(str(SRC / "bin" / "cautoswitch"), cfile=os.path.join(d, "c.pyc"), doraise=True)
        for s in (SRC / "usage-popup.sh", SRC / "record-usage.sh"):
            r = subprocess.run(["bash", "-n", str(s)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual((r.returncode, r.stderr), (0, ""), s.name)
        self.assertFalse((SRC / "bin" / "__pycache__").exists())

    def test_refuses_outside_herdr(self):
        r = self.auto(herdr=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not inside Herdr", r.stderr)

    def test_no_squad_panes(self):
        r = self.auto("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ok: no squad panes", r.stdout)

    def test_only_registered_squad_claudes_are_found(self):
        # a process the stub pgrep does not list (a stand-in for the PO's live agents) never appears
        self.e.popen(["sleep", "100"], env={"SQUAD_NAME": "real-agent", "HERDR_PANE_ID": "p9",
                                            "HERDR_WORKSPACE_ID": "w1"})
        self.pane("", "p1", "w1", "1")  # no SQUAD_NAME
        d = self.e.tmp / "dd"
        d.mkdir()
        (d / "daemon").write_text("sleep 100\n", encoding="utf-8")
        daemon = self.e.popen(["bash", "daemon", "run"], cwd=d, env={
            "SQUAD_NAME": "dev-d", "HERDR_PANE_ID": "p2", "HERDR_WORKSPACE_ID": "w1"})
        with open(self.e.stub / "pids", "a", encoding="utf-8") as f:
            f.write(f"{daemon.pid}\n")
        r = self.auto("--dry-run")
        self.assertIn("ok: no squad panes", r.stdout)
        self.assertNotIn("real-agent", r.stdout + self.log())

    def test_claude_missing_pane_or_workspace_id_is_skipped_without_error(self):
        for i, env in enumerate(({"SQUAD_NAME": "a", "HERDR_WORKSPACE_ID": "w1"},
                                 {"SQUAD_NAME": "b", "HERDR_PANE_ID": "p5"})):
            p = self.e.popen(["sleep", "100"], env=env)
            with open(self.e.stub / "pids", "a", encoding="utf-8") as f:
                f.write(f"{p.pid}\n")
        self.usage_file(1, 50, 20)
        self.pane("dev-1", "p1", "w1", "1")
        r = self.auto("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ok: w1 -> c1 5h 50% 7d 20%", r.stdout)  # only the complete pane is found
        self.assertNotIn("w2", r.stdout)
        self.assertNotIn("error:", r.stdout + self.log())

    def test_cache_younger_than_900s_is_used(self):
        self.pane("dev-1", "p1", "w1", "1")
        self.usage_file(2, 20, 10)
        for age in (600, 899):
            self.usage_file(1, 95, 80, age=age)
            self.auto("--dry-run")
            self.assertEqual(self.log().count("would set w1 default to c2"), 1 if age == 600 else 2, age)

    def test_account_comes_from_config_dir_and_unset_means_1(self):
        self.usage_file(1, 95, 80)
        self.usage_file(2, 20, 10)
        self.usage_file(3, 20, 10)
        self.e.default_file("1")
        self.pane("dev-1", "p1", "w1", "1")
        self.pane("dev-2", "p2", "w1", "2")
        self.pane("dev-3", "p3", "w2", "3")
        r = self.auto("--dry-run")
        self.assertIn("w1 -> c1 5h 95% 7d 80%", r.stdout)
        self.assertIn("w2 -> c1 5h 95% 7d 80%", r.stdout)  # both workspaces fall back to the global default 1
        self.assertIn("would cswitch dev-2(p2) c2 -> c1", self.log())
        self.assertIn("would cswitch dev-3(p3) c3 -> c1", self.log())
        self.assertNotIn("dev-1(p1)", self.log())

    def test_below_threshold_stays(self):
        self.usage_file(1, 50, 20)
        self.pane("dev-1", "p1", "w1", "1")
        r = self.auto("--dry-run")
        self.assertIn("w1 -> c1 5h 50% 7d 20%", r.stdout)
        self.assertNotIn("would set", self.log())

    def test_over_threshold_picks_the_lowest_5h_of_the_better_accounts(self):
        self.usage_file(1, 95, 80)
        self.usage_file(2, 30, 10)
        self.usage_file(3, 20, 20)
        self.pane("dev-1", "p1", "w1", "1")
        self.auto("--dry-run")
        self.assertIn("[dry-run] would set w1 default to c3: c1 5h 95% 7d 80%; c3 5h 20% 7d 20%", self.log())

    def test_at_threshold_counts_as_over(self):
        self.usage_file(1, 90, 80)
        self.usage_file(2, 20, 10)
        self.pane("dev-1", "p1", "w1", "1")
        self.auto("--dry-run")
        self.assertIn("would set w1 default to c2", self.log())

    def test_other_account_must_be_lower_on_both_windows(self):
        self.usage_file(1, 95, 10)
        self.usage_file(2, 20, 50)  # lower 5h, higher 7d
        self.usage_file(3, 99, 5)  # lower 7d, higher 5h
        self.pane("dev-1", "p1", "w1", "1")
        self.auto("--dry-run")
        self.assertIn("w1 c1 over 90% but no other account is lower on both; staying", self.log())
        self.assertNotIn("would set", self.log())

    def test_threshold_option(self):
        self.usage_file(1, 60, 50)
        self.usage_file(2, 10, 10)
        self.pane("dev-1", "p1", "w1", "1")
        self.auto("--dry-run")
        self.assertNotIn("would set", self.log())
        self.auto("--dry-run", "--threshold", "50")
        self.assertIn("would set w1 default to c2", self.log())

    def test_usage_unavailable_stays(self):
        self.pane("dev-1", "p1", "w1", "1")
        r = self.auto("--dry-run")  # no cache at all
        self.assertIn("w1 -> c1 n/a", r.stdout)
        self.usage_file(1, 99, 99, age=901)  # stale
        self.usage_file(2, 1, 1)
        r = self.auto("--dry-run")
        self.assertIn("w1 -> c1 n/a", r.stdout)
        self.assertNotIn("would set", self.log())

    def test_workspace_default_comes_from_cdefault(self):
        self.usage_file(1, 95, 80)
        self.usage_file(2, 20, 10)
        self.usage_file(3, 20, 10)
        self.e.default_file("1")
        (self.H / "workspace-default").mkdir()
        (self.H / "workspace-default" / "w2").write_text("2\n", encoding="utf-8")
        self.pane("dev-1", "p1", "w1", "1")
        self.pane("dev-2", "p2", "w2", "2")
        r = self.auto("--dry-run")
        self.assertIn("w1 -> c1 5h 95% 7d 80%", r.stdout)  # global default
        self.assertIn("w2 -> c2 5h 20% 7d 10%", r.stdout)  # its own file
        self.assertIn("would set w1 default to c2", self.log())
        self.assertNotIn("would set w2", self.log())

    def test_dry_run_changes_nothing_and_logs_the_would_cswitch(self):
        self.usage_file(3, 10, 10)
        (self.H / "workspace-default").mkdir()
        (self.H / "workspace-default" / "w1").write_text("3\n", encoding="utf-8")
        self.stub_cswitch()
        self.pane("dev-1", "p1", "w1", "1")
        r = self.auto("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("[dry-run] would cswitch dev-1(p1) c1 -> c3", self.log())
        self.assertEqual(self.switch_calls(), [])
        self.assertEqual(self.ws_default("w1"), "3")
        self.assertEqual([c for c in self.e.herdr_calls() if c[:2] == ["workspace", "report-metadata"]], [])

    def test_recent_pending_switch_suppresses_the_retry(self):
        self.usage_file(3, 10, 10)
        (self.H / "workspace-default").mkdir()
        (self.H / "workspace-default" / "w1").write_text("3\n", encoding="utf-8")
        self.stub_cswitch()
        self.pane("dev-1", "p1", "w1", "1")
        recent = time.strftime("%Y-%m-%dT%H:%M:%S")
        (self.H / "cswitch.log").write_text(f"{recent} p1 dev-1 -> account 3: c3 --resume x\n", encoding="utf-8")
        self.auto()
        self.assertEqual(self.switch_calls(), [])

    def test_pending_ages_out_after_15_minutes(self):
        with mock.patch.dict(os.environ, self.e.env):
            mod = self.module()
            ts = lambda age: time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time() - age))
            log = self.H / "cswitch.log"
            self.assertFalse(mod.pending("p1"))  # no log
            log.write_text(f"{ts(60)} p1 dev-1 -> account 3: c3\n", encoding="utf-8")
            self.assertTrue(mod.pending("p1"))
            self.assertFalse(mod.pending("p2"))  # another pane
            log.write_text(f"{ts(1000)} p1 dev-1 -> account 3: c3\n", encoding="utf-8")
            self.assertFalse(mod.pending("p1"))
            log.write_text(f"{ts(60)} p1 dev-1 -> account 3: c3\n{ts(30)} p1 dev-1 done\n", encoding="utf-8")
            self.assertFalse(mod.pending("p1"))  # the last line is the done line

    def test_expired_token_runs_one_refresh_then_uses_the_cache_and_does_not_retry(self):
        self.write_creds("1", int((time.time() - 3600) * 1000))
        self.usage_file(1, 50, 20)
        self.pane("dev-1", "p1", "w1", "1")
        env = dict(self.e.env, HERDR_ENV="1", HERDR_WORKSPACE_ID="w1")
        env.pop("CLAUDE_STUB_MODE", None)
        with mock.patch.dict(os.environ, env):
            mod = self.module()
            mod.tick(90, True)
            mod.tick(90, True)  # within 1800 s: no second refresh
        refresh = [c for c in self.e.claude_calls() if c["argv"][:1] == ["-p"]]
        self.assertEqual([c["argv"] for c in refresh],
                         [["-p", "ok", "--model", "haiku", "--no-session-persistence"]])
        self.assertEqual(refresh[0]["CLAUDE_CONFIG_DIR"], None)  # account 1
        self.assertIsNone(self.e.ws_file("w1"))  # ACCT_NO_WS_DEFAULT: the refresh is not a workspace default
        self.assertEqual(self.log().count("c1 token still expired after claude -p"), 1)

    def test_error_in_a_tick_is_logged_not_fatal(self):
        self.usage_file(1, 95, 80)
        self.usage_file(2, 20, 10)
        self.pane("dev-1", "p1", "w1", "1")
        p = self.H / "bin" / "cdefault"
        p.unlink()
        p.write_text("#!/usr/bin/env bash\n[ $# -gt 0 ] && exit 1\necho 1\n", encoding="utf-8")
        p.chmod(0o755)
        r = self.auto()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("autoswitch: error:", self.log())

    def test_full_chain_switches_the_workspace_default_then_the_pane(self):
        # the slow test (about 15 s): real cdefault and real cswitch against the stub herdr/claude
        pane = ca_stubs.PANE
        self.e.set_workspaces_real()  # the real capture: workspace w26
        self.e.set_pane()
        self.e.set_agents()
        self.usage_file(1, 95, 80)
        self.usage_file(2, 20, 10)
        self.usage_file(3, 90, 90)
        self.e.spawn_claude(pane, extra_env={"SQUAD_NAME": "plugin-tech-ca-repo", "HERDR_WORKSPACE_ID": "w26"})
        r = self.auto(env={"CLAUDE_STUB_MODE": "sleep"})  # the relaunched claude stays up
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.ws_default("w26"), "2")
        self.assertFalse((self.H / "default").exists())  # the global default is untouched
        self.assertIn("setting w26 default to c2", self.log())
        self.assertIn(["workspace", "report-metadata", "w26", "--source", "claude-accounts", "--token", "account=c2"],
                      [c[:7] for c in self.e.herdr_calls()])
        log = self.log()
        self.assertRegex(log, rf" {re.escape(pane)} plugin-tech-ca-repo -> account 2: ")
        self.assertRegex(log, re.compile(rf" {re.escape(pane)} plugin-tech-ca-repo done$", re.M))
        self.assertNotIn("FAILED", log)
        self.assertIn("retry: cswitch plugin-tech-ca-repo(" + pane + ") c1 -> c2", log)


if __name__ == "__main__":
    unittest.main()
