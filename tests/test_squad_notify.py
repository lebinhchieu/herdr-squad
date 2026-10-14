"""squad-notify: decision table, skip, title, failure and OSC delivery (no real herdr or WezTerm)."""
import importlib.machinery
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.dont_write_bytecode = True  # the extensionless script would leave bin/__pycache__/*.pyc
SCRIPT = Path(__file__).resolve().parent.parent / "bin" / "squad-notify"
_loader = importlib.machinery.SourceFileLoader("squad_notify", str(SCRIPT))
_spec = importlib.util.spec_from_loader("squad_notify", _loader)
sn = importlib.util.module_from_spec(_spec)
_loader.exec_module(sn)

IN = {"HERDR_ENV": "1"}
SQUAD = {"HERDR_ENV": "1", "SQUAD_NAME": "x"}


def sq(role):
    return {**SQUAD, "SQUAD_ROLE": role}


class DecideTest(unittest.TestCase):
    def test_table(self):
        cases = [
            ("Stop", "", sq("manager"), False, "Waiting for you"),
            ("Stop", "", sq("dev"), False, None),
            ("Stop", "", sq("tech-lead"), False, None),
            ("Notification", "permission_prompt", sq("dev"), False, "Permission prompt"),
            ("Notification", "elicitation_dialog", sq("dev"), False, "Question waiting"),
            ("Notification", "permission_prompt", sq("manager"), False, "Permission prompt"),
            ("Notification", "idle_prompt", sq("manager"), False, None),
            ("Stop", "", IN, False, "Done"),
            ("Notification", "permission_prompt", IN, False, "Needs input"),
            ("Notification", "elicitation_dialog", IN, False, "Needs input"),
            ("Notification", "idle_prompt", IN, False, None),
            ("Stop", "", IN, True, None),
            ("Stop", "", sq("manager"), True, None),
            ("Stop", "", {}, False, None),
            ("Notification", "permission_prompt", {"SQUAD_NAME": "x"}, False, None),
        ]
        for event, ntype, env, sub, want in cases:
            with self.subTest(event=event, ntype=ntype, env=env, sub=sub):
                self.assertEqual(sn.decide(event, ntype, env, sub), want)


FIX = Path(__file__).resolve().parent / "fixtures" / "squad-notify"


def real(name):
    return json.loads((FIX / name).read_text())


class RealPayloadTest(unittest.TestCase):
    """Payloads captured from a live Claude session (evidence/TAB-05/samples)."""

    def body(self, name, env):
        p = real(name)
        return sn.decide(p["hook_event_name"], p.get("notification_type", ""), env, bool(p.get("agent_id")))

    def test_permission_prompt(self):
        self.assertEqual(real("notification-permission_prompt.json")["notification_type"], "permission_prompt")
        self.assertEqual(self.body("notification-permission_prompt.json", sq("dev")), "Permission prompt")
        self.assertEqual(self.body("notification-permission_prompt.json", IN), "Needs input")

    def test_stop(self):
        self.assertNotIn("agent_id", real("stop.json"))
        self.assertEqual(self.body("stop.json", sq("manager")), "Waiting for you")
        self.assertEqual(self.body("stop.json", IN), "Done")

    def test_subagent_stop_is_its_own_event_and_silent(self):
        p = real("subagent-stop.json")
        self.assertEqual((p["hook_event_name"], bool(p["agent_id"])), ("SubagentStop", True))
        for env in (IN, sq("manager"), sq("dev")):
            self.assertIsNone(self.body("subagent-stop.json", env))


class DeliveryTest(unittest.TestCase):
    def test_osc_exact_and_stripped(self):
        self.assertEqual(sn.osc("a · b", "Done"), "\x1b]777;notify;a · b;Done\x1b\\".encode())
        self.assertEqual(sn.osc("a;b\x1b]0;x\x07", "c\nd;"), "\x1b]777;notify;ab]0x;cd\x1b\\".encode())

    def test_write_to_pty_per_client(self):
        m1, s1 = os.openpty()
        m2, s2 = os.openpty()
        n = sn.deliver("t", "b", [os.ttyname(s1), os.ttyname(s2)])
        self.assertEqual(n, 2)
        self.assertEqual(os.read(m1, 100), sn.osc("t", "b"))
        self.assertEqual(os.read(m2, 100), sn.osc("t", "b"))
        for fd in (m1, s1, m2, s2):
            os.close(fd)

    def test_unopenable_tty_is_not_fatal(self):
        self.assertEqual(sn.deliver("t", "b", ["/dev/pts/999999"]), 0)

    def test_find_clients(self):
        with tempfile.TemporaryDirectory() as d:
            def proc(pid, comm, cmdline, fd1):
                p = Path(d) / str(pid)
                (p / "fd").mkdir(parents=True)
                (p / "comm").write_text(comm + "\n")
                (p / "cmdline").write_bytes(cmdline.encode())
                os.symlink(fd1, p / "fd" / "1")
            proc(1, "herdr", "herdr\0", "/dev/pts/3")
            proc(2, "herdr", "herdr\0", "/dev/pts/4")
            proc(3, "herdr", "/bin/herdr\0server\0", "/dev/null")
            proc(4, "herdr", "herdr\0", "/tmp/not-a-pts")
            proc(5, "bash", "herdr\0", "/dev/pts/9")
            self.assertEqual(sorted(sn.find_clients(d)), ["/dev/pts/3", "/dev/pts/4"])

    def test_config(self):
        with tempfile.TemporaryDirectory() as d:
            def cfg(text):
                p = Path(d) / "c.toml"
                p.write_text(text)
                return str(p)
            self.assertTrue(sn.delivery_off(cfg('[ui.toast]\ndelivery = "off"\n')))
            self.assertTrue(sn.delivery_off(cfg('[a]\nx=1\n[ui.toast]\n# c\ndelivery = "off" # no\n[keys]\n')))
            self.assertFalse(sn.delivery_off(cfg('[ui.toast]\ndelivery = "terminal"\n')))
            self.assertFalse(sn.delivery_off(cfg('[ui.toast]\n')))
            self.assertFalse(sn.delivery_off(cfg('[other]\ndelivery = "off"\n')))
            self.assertFalse(sn.delivery_off(str(Path(d) / "missing.toml")))


class RunTest(unittest.TestCase):
    """Whole hook as a subprocess with a fake herdr, a pty as client tty is impossible there (real /proc),
    so run() is called in-process with a fake proc root and a pty pair."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.master, self.slave = os.openpty()
        p = self.d / "proc" / "1"
        (p / "fd").mkdir(parents=True)
        (p / "comm").write_text("herdr\n")
        (p / "cmdline").write_bytes(b"herdr\0")
        os.symlink(os.ttyname(self.slave), p / "fd" / "1")
        self.cfg = self.d / "config.toml"
        self.cfg.write_text('[ui.toast]\ndelivery = "off"\n')
        self.state = {"focused": False, "active": "w:t2", "ws": "squad-tabs", "tab": "🦀 Manager"}
        self.fake = self.d / "herdr"
        self.fake.write_text(
            "#!/usr/bin/env python3\nimport json,sys,time,os\n"
            f"s=json.load(open({str(self.d / 'state.json')!r}))\n"
            "if s.get('hang'): time.sleep(30)\n"
            "if s.get('fail'): sys.exit(1)\n"
            "if sys.argv[1]=='workspace': r={'workspace':{'focused':s['focused'],'active_tab_id':s['active'],'label':s['ws']}}\n"
            "else: r={'tab':{'label':s['tab']}}\n"
            "print(json.dumps({'result':r}))\n")
        self.fake.chmod(0o755)
        self.save()
        self.env = {**os.environ, "HERDR_ENV": "1", "SQUAD_NAME": "x", "SQUAD_ROLE": "manager",
                    "HERDR_BIN_PATH": str(self.fake), "HERDR_CONFIG_PATH": str(self.cfg),
                    "HERDR_WORKSPACE_ID": "w", "HERDR_TAB_ID": "w:t1"}

    def tearDown(self):
        os.close(self.master)
        os.close(self.slave)
        self.tmp.cleanup()

    def save(self):
        (self.d / "state.json").write_text(json.dumps(self.state))

    def fire(self, payload=None, env=None):
        sn.run(payload or {"hook_event_name": "Stop"}, env or self.env, str(self.d / "proc"))
        os.set_blocking(self.master, False)
        try:
            return os.read(self.master, 1000)
        except BlockingIOError:
            return b""

    def test_title_and_body(self):
        self.assertEqual(self.fire(), sn.osc("squad-tabs · 🦀 Manager", "Waiting for you"))

    def test_relabel_is_current(self):
        self.state["tab"] = "renamed"
        self.save()
        self.assertEqual(self.fire(), sn.osc("squad-tabs · renamed", "Waiting for you"))

    def test_skip_when_focused_active(self):
        self.state.update(focused=True, active="w:t1")
        self.save()
        self.assertEqual(self.fire(), b"")

    def test_no_skip_other_tab_or_unfocused(self):
        for focused, active in ((True, "w:t2"), (False, "w:t1")):
            self.state.update(focused=focused, active=active)
            self.save()
            self.assertNotEqual(self.fire(), b"", (focused, active))

    def test_dormant_unless_off(self):
        self.cfg.write_text('[ui.toast]\ndelivery = "terminal"\n')
        self.assertEqual(self.fire(), b"")

    def test_no_decision_no_toast(self):
        self.assertEqual(self.fire({"hook_event_name": "Stop", "agent_id": "a"}), b"")

    def test_no_client_found(self):
        sn.run({"hook_event_name": "Stop"}, self.env, str(self.d / "nowhere"))

    def test_herdr_failing_still_toasts_without_crash(self):
        self.state["fail"] = True
        self.save()
        self.assertEqual(self.fire(), sn.osc("herdr", "Waiting for you"))


class CliTest(unittest.TestCase):
    def run_cli(self, stdin, env):
        t = time.time()
        r = subprocess.run([sys.executable, str(SCRIPT)], input=stdin, capture_output=True, text=True,
                           env=env, timeout=20)
        return r, time.time() - t

    def test_garbage_and_hang_exit_zero_quiet(self):
        with tempfile.TemporaryDirectory() as d:
            fake = Path(d) / "herdr"
            fake.write_text("#!/bin/sh\nsleep 30\n")
            fake.chmod(0o755)
            cfg = Path(d) / "c.toml"
            cfg.write_text('[ui.toast]\ndelivery = "off"\n')
            env = {**os.environ, "HERDR_ENV": "1", "HERDR_BIN_PATH": str(fake), "HERDR_CONFIG_PATH": str(cfg)}
            env.pop("SQUAD_NAME", None)
            r, took = self.run_cli('{"hook_event_name": "Stop"}', env)
            self.assertEqual((r.returncode, r.stdout), (0, ""))
            self.assertLess(took, 8)
            r, _ = self.run_cli("not json", env)
            self.assertEqual((r.returncode, r.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
