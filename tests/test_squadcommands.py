"""The commands table (ticket 02): names are checked, texts are one shell word per name, no run path, one record adds a command."""
import os
import shlex
import sys
import unittest
import unittest.mock

from squadtest import BIN

sys.path.insert(0, str(BIN))
import squadcommands as C  # noqa: E402

COMMAND_KEYS = {"id", "label", "text", "changes", "runs_by", "group", "state", "reason", "placeholder", "when"}


def info(kind="scope", status="open", name="api", **kw):
    base = {"kind": kind, "name": name, "status": status, "home": "/r/.claude/squads/plugin/%ss/%s" % (kind, name),
            "squad": "plugin", "squad_path": "/r/.claude/squads/plugin", "goal": None, "facts": None,
            "open_scopes": [], "flat": False}
    base.update(kw)
    return base


def facts(**kw):
    f = {"needs_you": 0, "stuck": 0, "tasks_done": 1, "tasks_total": 3, "agents_working": 0, "last_active": None}
    f.update(kw)
    return f


def by_id(cmds):
    return {c["id"]: c for c in cmds}


class CommandTests(unittest.TestCase):
    def test_T1_9a_unsafe_names_get_no_commands(self):
        for bad in ("a b", "x;rm", "$(x)", "../x", ""):
            self.assertEqual(C.commands_for(info(name=bad)), [], bad)
        self.assertTrue(C.commands_for(info(name="ok-1.2")))

    def test_T1_9b_quoting_keeps_one_word_per_name(self):
        text = by_id(C.commands_for(info(home="/a b/c")))["inbox"]["text"]
        self.assertEqual(shlex.split(text), ["squad-inbox", "--home", "/a b/c", "list", "--open", "--no-write"])
        with unittest.mock.patch.object(C.os, "name", "nt"):
            self.assertEqual(C.q("a b"), '"a b"')

    def test_T1_9c_9d_only_the_command_keys_and_never_force(self):
        for i in (info(), info("goal"), info(status="done"), info("squad", name="plugin"), info("goal", status="done")):
            for c in C.commands_for(i):
                self.assertEqual(set(c), COMMAND_KEYS)
                self.assertNotIn("--force", c["text"])

    def test_T1_9e_9f_scope_in_goal_and_wait_reasons(self):
        c = by_id(C.commands_for(info(goal="g1", facts=facts(agents_working=2, needs_you=0))))
        self.assertEqual(c["resume"]["text"], "squad-start --resume g1 --squad plugin")  # the goal's name
        self.assertEqual((c["resume"]["state"], c["resume"]["reason"]), ("wait", "agents are working"))
        rs = c["resume-session"]
        self.assertEqual((rs["state"], rs["reason"]), ("wait", "no Manager session in roster.md"))
        mgr = {"name": "plugin-mgr-g1", "kind": "goal", "home": "/r/sq/goals/g1", "home_name": "g1", "session": "s-1",
               "cwd": "/r", "composed": True, "lean": "/r/l.json", "settings": None, "rules": "/r/rules.md"}
        c = by_id(C.commands_for(info(goal="g1", manager=mgr, facts=facts(agents_working=2, needs_you=0))))
        self.assertEqual((c["resume-session"]["state"], c["resume-session"]["reason"]), ("wait", "agents are working"))
        words = shlex.split(c["resume-session"]["text"])
        self.assertIn("claude", words)
        self.assertNotIn("squad-start", words)
        for w in ("SQUAD=plugin", "SQUAD_NAME=plugin-mgr-g1", "SQUAD_ROLE=manager", "SQUAD_SCOPE=", "GOAL_DIR=/r/sq/goals/g1",
                  "SQUAD_DIR=/r/.claude/squads/plugin"):
            self.assertIn(w, words)
        tail = words[words.index("claude"):]
        self.assertEqual(tail[1:5], ["--resume", "s-1", "--agent", "squad:manager"])  # the goal Manager's roster session
        for flag in ("--settings", "--plugin-dir", "--append-system-prompt-file", "--setting-sources"):
            self.assertIn(flag, tail)
        self.assertEqual((c["inbox"]["state"], c["inbox"]["reason"]), ("wait", "no open questions"))
        self.assertEqual((c["close-scope"]["state"], c["close-scope"]["reason"]), ("wait", "tasks open"))
        g = by_id(C.commands_for(info("goal", name="g1", open_scopes=["a", "b"], facts=facts())))
        self.assertEqual((g["close-goal"]["state"], g["close-goal"]["reason"]), ("wait", "scope a is open"))
        self.assertEqual(g["close-goal"]["text"], "squad-close plugin --goal g1 --dry-run")

    def test_T1_9g_retire_only_on_done_lone_scope_and_done_goal(self):
        has = lambda i: "retire" in by_id(C.commands_for(i))  # noqa: E731
        self.assertTrue(has(info(status="done")))
        self.assertTrue(has(info("goal", status="done")))
        self.assertFalse(has(info(status="done", goal="g0")))
        self.assertFalse(has(info()))
        self.assertEqual(by_id(C.commands_for(info(status="done")))["retire"]["text"], "squad-retire plugin-mgr-api")

    def test_T1_9j_inbox_text_and_squad_report_names_a_path(self):
        c = by_id(C.commands_for(info()))
        self.assertEqual(c["inbox"]["text"], "squad-inbox --home /r/.claude/squads/plugin/scopes/api list --open --no-write")
        # squad-report takes a squad NAME only when $SQUAD_DIR is set: Chieu's plain shell has none, so a path
        self.assertEqual(c["report"]["text"], "squad-report api --squad /r/.claude/squads/plugin")

    def test_T1_9_copy_only_no_run_keys(self):
        for c in C.commands_for(info()):
            self.assertFalse({"run_ok", "argv"} & set(c))

    def test_T1_9i_one_record_makes_a_command_appear(self):
        extra = C._rec("zzz", "Zzz", lambda i: "squad-zzz %s" % C.q(i["name"]), ("scope",), "open", "read", "A test.")
        got = by_id(C.commands_for(info(), C.COMMANDS + [extra]))
        self.assertEqual(got["zzz"]["text"], "squad-zzz api")
        self.assertNotIn("zzz", by_id(C.commands_for(info("goal"), C.COMMANDS + [extra])))


if __name__ == "__main__":
    unittest.main()
