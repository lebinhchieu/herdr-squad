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

    def test_failed_refresh_is_retried_only_after_1800_seconds(self):
        self.write_creds("1", int((time.time() - 3600) * 1000))
        self.usage_file(1, 50, 20)
        self.pane("dev-1", "p1", "w1", "1")
        env = dict(self.e.env, HERDR_ENV="1", HERDR_WORKSPACE_ID="w1")
        env.pop("CLAUDE_STUB_MODE", None)
        refreshes = lambda: len([c for c in self.e.claude_calls() if c["argv"][:1] == ["-p"]])
        with mock.patch.dict(os.environ, env):
            mod = self.module()
            mod.tick(90, True)
            (acct,) = mod.REFRESH_FAILED
            mod.REFRESH_FAILED[acct] -= 1700  # failed 1700 s ago: still inside the limit
            mod.tick(90, True)
            self.assertEqual(refreshes(), 1)
            mod.REFRESH_FAILED[acct] -= 101  # now 1801 s ago: past it
            mod.tick(90, True)
            self.assertEqual(refreshes(), 2)

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


# stands in for the real cswitch like CSWITCH, but also writes the '-> account' line first, samples pending work
# the way the real detached block does (cwake --mark) and takes its outcome from mode.<pane> (done|failed|hang).
CSWITCH_W = """#!/usr/bin/env bash
echo "$1 $2" >> "$HOME/cswitch.calls"
echo "$(date -Is) $2 stub -> account $1: stub" >> "$HOME/.claude-accounts/cswitch.log"
[ "${CSWITCH_WAKE:-on}" = off ] || "$HOME/.claude-accounts/bin/cwake" --mark "$2" --clauses 13
case "$(cat "$HOME/mode.$2" 2>/dev/null || echo done)" in
  done)
    # the pane's claude restarts on the new account: same pane env, new CLAUDE_CONFIG_DIR
    for p in $(cat "$CA_STUB/pids" 2>/dev/null); do
      tr "\\0" "\\n" <"/proc/$p/environ" 2>/dev/null | grep -qx "HERDR_PANE_ID=$2" || continue
      env=$(tr "\\0" "\\n" <"/proc/$p/environ" 2>/dev/null | grep -E "^(SQUAD_NAME|HERDR_WORKSPACE_ID|SCOPE_DIR)=")
      kill "$p"
      sleep 0.2
      cfg="$HOME/.claude-$1"; [ "$1" = 1 ] && cfg=""
      ( export $env HERDR_PANE_ID="$2" HERDR_ENV=1 CLAUDE_STUB_MODE=sleep; [ -n "$cfg" ] && export CLAUDE_CONFIG_DIR="$cfg"
        nohup "$CA_STUB/bin/claude" >/dev/null 2>&1 </dev/null & )
      sleep 0.3
      break
    done
    echo "$(date -Is) $2 stub done" >> "$HOME/.claude-accounts/cswitch.log" ;;
  failed) echo "$(date -Is) $2 FAILED: claude did not restart" >> "$HOME/.claude-accounts/cswitch.log" ;;
esac
"""


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def asst(t, stop, content=None):
    m = {"stop_reason": stop}
    if content is not None:
        m["content"] = content
    return {"type": "assistant", "timestamp": iso(t), "message": m}


def user(t, content=None):
    m = {"stop_reason": None}
    if content is not None:
        m["content"] = content
    return {"type": "user", "timestamp": iso(t), "message": m}


def send(t, call_id, to, error=None):
    """A SendMessage call and its result (error: None = no result yet, True = failed, False = sent)."""
    out = [asst(t, "tool_use", [{"type": "tool_use", "name": "SendMessage", "id": call_id,
                                 "input": {"to": to, "message": "STATUS 02: x"}}])]
    if error is not None:
        out.append(user(t + 1, [{"type": "tool_result", "tool_use_id": call_id, "is_error": error,
                                 "content": "recipient not reachable" if error else "sent"}]))
    return out


NOW = time.time()
IDLE = [asst(NOW - 600, "end_turn")]
CUT_OFF = [asst(NOW - 600, "end_turn"), user(NOW - 300), asst(NOW - 290, "tool_use")]


@requires_linux
class WakeTest(Base):
    """Pending-work wake (design: tasks/01.md ## Design): every off-default pane moves, only a pane with pending
    work gets one wake prompt, after its workspace batch is back."""

    auto = AutoswitchTest.auto
    module = AutoswitchTest.module
    ws_default = AutoswitchTest.ws_default

    def setUp(self):
        super().setUp()
        self.e.env["CWAKE_TIMEOUT_MS"] = "300"
        self.e.env["CSWITCH_WAKE_GAP"] = "0"
        (self.H / "workspace-default").mkdir()
        (self.H / "workspace-default" / "w1").write_text("3\n", encoding="utf-8")  # target c3; panes run c2
        self.stub_cswitch_w()
        self.rows = []
        self.scope = self.e.tmp / "scope"
        self.scope.mkdir()

    def stub_cswitch_w(self):
        p = self.H / "bin" / "cswitch"
        p.unlink()
        p.write_text(CSWITCH_W, encoding="utf-8")
        p.chmod(0o755)

    def squad(self, name, pane, recs=IDLE, status="idle", ws="w1", acct="2", sid=None):
        sid = sid or f"sid-{name}"
        extra = {"HERDR_WORKSPACE_ID": ws, "SQUAD_NAME": name, "SCOPE_DIR": str(self.scope)}
        if acct != "1":
            extra["CLAUDE_CONFIG_DIR"] = str(self.e.home / f".claude-{acct}")
        self.e.spawn_claude(pane, extra_env=extra)
        self.rows.append((pane, name, ws, sid, status))
        self.e.set_agent_rows(*self.rows)
        if recs is not None:
            self.e.set_transcript(sid, recs)

    def mode(self, pane, value):
        (self.e.home / f"mode.{pane}").write_text(value, encoding="utf-8")

    def tick(self, n=1, fake_clock=None):
        """cautoswitch.tick in this process (HOME/PATH of the harness), sleeps shortened."""
        env = dict(self.e.env, HERDR_ENV="1")
        real_sleep = time.sleep
        with mock.patch.dict(os.environ, env):
            mod = self.module()
            clock = [0]
            fast = lambda s: (clock.__setitem__(0, clock[0] + s), real_sleep(0.02))
            patches = [mock.patch("time.sleep", fast)]
            if fake_clock:
                real_time = time.time
                patches.append(mock.patch("time.time", lambda: real_time() + clock[0]))
            for pt in patches:
                pt.start()
            try:
                for _ in range(n):
                    mod.tick(90, False)
            finally:
                for pt in patches:
                    pt.stop()
        return mod

    def prompts(self):
        """Wake prompts (every `agent prompt` that is not /exit): [(pane, text)]."""
        return [(c[2], c[3]) for c in self.e.herdr_calls() if c[:2] == ["agent", "prompt"] and c[3] != "/exit"]

    def marker(self, pane):
        p = self.H / "wake-pending" / pane
        return p.read_text(encoding="utf-8").split(None, 2) if p.exists() else None

    def test_cut_off_pane_is_woken_once_and_an_idle_pane_is_only_moved(self):
        self.squad("dev-a", "p1", CUT_OFF)
        self.squad("dev-b", "p2", IDLE, status="working")  # mid-turn at tick start; idle again when sampled
        self.tick(2)
        self.assertEqual(sorted(self.switch_calls()), ["3 p1", "3 p2"])
        got = self.prompts()
        self.assertEqual([p for p, _ in got], ["p1"])
        self.assertIn("Your Claude account changed (2 -> 3)", got[0][1])
        self.assertIn("answer with one line", got[0][1])
        self.assertRegex(self.log(), r" p1 dev-a wake sent$")
        self.assertIsNone(self.marker("p1"))  # one tick moved them; the second must not re-wake
        self.assertNotIn(" p2 dev-b wake", self.log())
        self.assertEqual(len(self.prompts()), 1)

    def test_blocked_at_sample_time_marks_and_a_later_idle_wakes(self):
        self.squad("dev-a", "p1", IDLE, status="blocked")
        self.e.set_status("p1", "blocked")
        r = subprocess.run([str(self.H / "bin" / "cwake"), "--mark", "p1", "--clauses", "13"],
                           env=dict(self.e.env), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([x.strip() for x in self.marker("p1")[1:]], ["dev-a", "blocked"])
        self.e.set_status("p1", "idle")
        self.tick()
        self.assertEqual([p for p, _ in self.prompts()], ["p1"])

    def test_unanswered_message_marks_the_pane(self):
        self.squad("dev-a", "p1", IDLE)
        (self.scope / "messages.jsonl").write_text(
            json.dumps({"ts": iso(NOW - 100), "from": "x", "to": "dev-a", "type": "ASK", "task": "02"}) + "\n"
            + json.dumps({"ts": iso(NOW - 100), "from": "x", "to": "other", "type": "ASK", "task": "02"}) + "\n",
            encoding="utf-8")
        self.tick()
        self.assertEqual([p for p, _ in self.prompts()], ["p1"])

    def test_message_older_than_the_last_turn_is_not_pending(self):
        self.squad("dev-a", "p1", IDLE)
        (self.scope / "messages.jsonl").write_text(
            json.dumps({"ts": iso(NOW - 900), "from": "x", "to": "dev-a"}) + "\n", encoding="utf-8")
        self.tick()
        self.assertEqual(self.prompts(), [])

    def test_failed_send_sender_is_woken_only_after_the_last_pane_is_back(self):
        # failure timestamp after T0 (the '-> account' line written during the tick): a future time in the fixture
        self.squad("dev-a", "p1", IDLE + send(NOW + 600, "t1", "dev-b", error=True) + [asst(NOW + 610, "end_turn")])
        self.squad("dev-b", "p2", IDLE)
        self.tick()
        self.assertEqual(sorted(self.switch_calls()), ["3 p1", "3 p2"])
        self.assertEqual([p for p, _ in self.prompts()], ["p1"])
        lines = self.log().splitlines()
        done2 = max(i for i, l in enumerate(lines) if " p2 stub done" in l)
        sent = next(i for i, l in enumerate(lines) if " p1 dev-a wake sent" in l)
        self.assertLess(done2, sent)
        self.tick()
        self.assertEqual(len(self.prompts()), 1)  # a later tick does not re-wake the woken sender

    def test_failed_send_before_the_batch_or_followed_by_a_success_is_not_pending(self):
        self.squad("dev-a", "p1", IDLE + send(NOW - 5000, "t1", "dev-b", error=True) + [asst(NOW - 4990, "end_turn")])
        self.squad("dev-c", "p3", IDLE + send(NOW + 600, "t2", "dev-b", error=True)
                   + send(NOW + 620, "t3", "dev-b", error=False) + [asst(NOW + 640, "end_turn")])
        self.tick()
        self.assertEqual(sorted(self.switch_calls()), ["3 p1", "3 p3"])
        self.assertEqual(self.prompts(), [])

    def test_pane_not_idle_in_the_gate_gets_no_prompt_and_a_skip_line(self):
        self.squad("dev-a", "p1", CUT_OFF)
        self.e.set_status("p1", "working")
        self.tick()
        self.assertEqual(self.switch_calls(), ["3 p1"])  # still moved
        self.assertEqual(self.prompts(), [])
        self.assertIn("WAKE SKIPPED p1 state=working", self.log())
        self.assertRegex(self.log(), r" p1 dev-a wake skipped$")
        self.assertIsNone(self.marker("p1"))  # no retry loop
        self.tick()
        self.assertEqual(self.prompts(), [])

    def test_pane_without_squad_name_is_neither_moved_nor_woken(self):
        self.e.spawn_claude("p9", extra_env={"HERDR_WORKSPACE_ID": "w1", "CLAUDE_CONFIG_DIR": str(self.e.home / ".claude-2")})
        self.squad("dev-a", "p1", IDLE)
        self.tick()
        self.assertEqual(self.switch_calls(), ["3 p1"])
        self.assertEqual(self.prompts(), [])
        self.assertNotIn("p9", self.log())

    def test_wake_off_moves_everything_and_samples_and_sends_nothing(self):
        self.e.env["CSWITCH_WAKE"] = "off"
        self.squad("dev-a", "p1", CUT_OFF)
        self.squad("dev-b", "p2", CUT_OFF)
        self.tick()
        self.assertEqual(sorted(self.switch_calls()), ["3 p1", "3 p2"])
        self.assertEqual(self.prompts(), [])
        self.assertFalse((self.H / "wake-pending").exists())
        self.assertNotIn("wake", self.log().replace("autoswitch:", ""))

    def test_failed_move_keeps_its_marker_while_the_others_are_woken_and_a_retry_wakes_it(self):
        self.squad("dev-a", "p1", CUT_OFF)
        self.squad("dev-b", "p2", CUT_OFF)
        self.squad("dev-c", "p3", CUT_OFF)
        self.mode("p3", "failed")
        self.tick()
        self.assertEqual(sorted(p for p, _ in self.prompts()), ["p1", "p2"])  # C does not hold them up
        self.assertIsNotNone(self.marker("p3"))
        # retry fails again: still no wake, marker kept
        self.tick()
        self.assertEqual(len(self.prompts()), 2)
        self.assertIsNotNone(self.marker("p3"))
        self.assertEqual(self.switch_calls().count("3 p3"), 2)
        # retry succeeds: C is woken, A and B are not woken again
        self.mode("p3", "done")
        self.tick()
        self.assertEqual(sorted(p for p, _ in self.prompts()), ["p1", "p2", "p3"])
        self.assertIsNone(self.marker("p3"))
        self.assertEqual(self.switch_calls().count("3 p1"), 1)

    def test_a_move_still_running_at_the_deadline_is_not_woken_and_others_are(self):
        self.squad("dev-a", "p1", CUT_OFF)
        self.squad("dev-c", "p3", CUT_OFF)
        self.mode("p3", "hang")  # neither done nor FAILED
        self.tick(fake_clock=True)
        self.assertEqual([p for p, _ in self.prompts()], ["p1"])
        self.assertIsNotNone(self.marker("p3"))
        self.assertEqual(self.switch_calls().count("3 p3"), 1)

    def test_a_cswitch_still_in_its_15_minutes_delays_the_workspace_wake_to_the_next_tick(self):
        self.squad("dev-a", "p1", CUT_OFF)
        self.squad("dev-c", "p3", IDLE)
        recent = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time() - 60))
        (self.H / "cswitch.log").write_text(f"{recent} p3 dev-c -> account 3: c3 --resume x\n", encoding="utf-8")
        self.tick()
        self.assertEqual(self.switch_calls(), ["3 p1"])  # p3 is skipped by pending()
        self.assertEqual(self.prompts(), [])
        self.assertIsNotNone(self.marker("p1"))

    def test_unreadable_transcript_is_not_pending_and_logs_one_line(self):
        self.squad("dev-a", "p1", None)  # no transcript file for the session
        self.tick()
        self.assertEqual(self.switch_calls(), ["3 p1"])
        self.assertEqual(self.prompts(), [])
        self.assertEqual(self.log().count("p1 dev-a transcript unreadable"), 1)

    def test_unreadable_messages_file_is_not_pending_and_logs_one_line(self):
        self.squad("dev-a", "p1", IDLE)  # SCOPE_DIR has no messages.jsonl
        self.tick()
        self.assertEqual(self.prompts(), [])
        self.assertEqual(self.log().count("p1 dev-a messages.jsonl unreadable"), 1)

    def test_herdr_failure_is_not_pending_and_never_wake_all(self):
        self.squad("dev-a", "p1", CUT_OFF)
        (self.e.stub / "agents.json").unlink()  # agent get/list fail
        self.tick()
        self.assertEqual(self.prompts(), [])
        self.assertIn("herdr agent get failed", self.log())

    def test_marker_older_than_30_minutes_is_deleted_unsent(self):
        self.squad("dev-a", "p1", IDLE)
        (self.H / "wake-pending").mkdir()
        (self.H / "wake-pending" / "p1").write_text(f"{int(time.time()) - 1900} dev-a cut-off\n", encoding="utf-8")
        self.tick()
        self.assertIsNone(self.marker("p1"))
        self.assertEqual(self.prompts(), [])
        self.assertIn("wake marker of dev-a(p1) older than 30 min; deleted unsent", self.log())

    def test_dry_run_writes_and_sends_nothing(self):
        self.squad("dev-a", "p1", CUT_OFF)
        (self.H / "wake-pending").mkdir()
        (self.H / "wake-pending" / "p1").write_text(f"{int(time.time()) - 1900} dev-a cut-off\n", encoding="utf-8")
        r = self.auto("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.switch_calls(), [])
        self.assertEqual(self.prompts(), [])
        self.assertEqual(sorted(os.listdir(self.H / "wake-pending")), ["p1"])  # not even the expiry
        self.assertNotIn("wake", self.log().replace("would cswitch", ""))

    def test_full_chain_real_cswitch_marks_before_exit_and_the_wake_follows_the_batch(self):
        # slow (about 15 s): real cswitch + cwake + cautoswitch against the stub herdr/claude
        pane, sid = ca_stubs.PANE, "25082cb8-e1f2-4ad2-b562-2b271b63e302"
        (self.H / "bin" / "cswitch").unlink()
        (self.H / "bin" / "cswitch").symlink_to(SRC / "bin" / "cswitch")  # the real one
        self.e.set_workspaces_real()
        self.e.set_pane()
        self.e.set_agents()
        self.e.set_transcript(sid, CUT_OFF)
        (self.H / "workspace-default").mkdir(exist_ok=True)
        (self.H / "workspace-default" / "w26").write_text("2\n", encoding="utf-8")
        self.e.set_status(pane, "idle")
        self.e.set_pane_env(pane, SQUAD_NAME="plugin-tech-ca-repo", SCOPE_DIR=str(self.scope))
        self.e.spawn_claude(pane, extra_env={"SQUAD_NAME": "plugin-tech-ca-repo", "HERDR_WORKSPACE_ID": "w26",
                                             "SCOPE_DIR": str(self.scope)})
        r = self.auto(env={"CLAUDE_STUB_MODE": "sleep"})
        self.assertEqual(r.returncode, 0, r.stderr)
        log = self.log()
        self.assertRegex(log, re.compile(rf" {re.escape(pane)} plugin-tech-ca-repo done$", re.M))
        self.assertRegex(log, re.compile(rf" {re.escape(pane)} plugin-tech-ca-repo wake sent$", re.M))
        calls = [c[:2] for c in self.e.herdr_calls() if c[0] == "agent"]
        self.assertLess(calls.index(["agent", "wait"]), calls.index(["agent", "prompt"]))  # wait, /exit ...
        prompts = [c for c in self.e.herdr_calls() if c[:2] == ["agent", "prompt"]]
        self.assertEqual([c[3] for c in prompts][0], "/exit")
        self.assertIn("Your Claude account changed (1 -> 2)", prompts[-1][3])  # after the move, once
        self.assertEqual(len(prompts), 2)

    def test_wakes_go_oldest_marker_first(self):
        self.squad("dev-a", "p1", CUT_OFF)
        self.squad("dev-b", "p2", CUT_OFF)
        self.squad("dev-c", "p3", CUT_OFF)
        for pane, age in (("p1", 30), ("p2", 90), ("p3", 60)):
            (self.H / "wake-pending").mkdir(exist_ok=True)
            (self.H / "wake-pending" / pane).write_text(f"{int(time.time()) - age} dev-x cut-off\n", encoding="utf-8")
        # pre-existing markers keep their epoch (cwake --mark does not reset it)
        self.tick()
        self.assertEqual([p for p, _ in self.prompts()], ["p2", "p3", "p1"])


if __name__ == "__main__":
    unittest.main()
