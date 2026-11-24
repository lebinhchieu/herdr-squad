"""hooks/hooks.json: valid, existing hooks kept, squad-notify wired for Stop and Notification."""
import json
import os
import unittest
from pathlib import Path

HOOKS_FILE = json.loads((Path(__file__).resolve().parent.parent / "hooks" / "hooks.json").read_text())
HOOKS = HOOKS_FILE["hooks"]
NOTIFY = '"${CLAUDE_PLUGIN_ROOT}/bin/squad-notify"'


def commands(event, matcher=None):
    return [(h["command"], h.get("async"), h.get("timeout")) for g in HOOKS[event]
            if g.get("matcher") == matcher for h in g["hooks"]]


class HooksJsonTest(unittest.TestCase):

    def test_path_guard_on_the_write_tools_only(self):
        guard = '"${CLAUDE_PLUGIN_ROOT}/bin/squad-path-guard"'
        self.assertEqual(commands("PreToolUse", "Write|Edit|MultiEdit|NotebookEdit"), [(guard, None, None)])
        self.assertEqual(len(HOOKS["PreToolUse"]), 3)
        self.assertTrue((Path(__file__).resolve().parent.parent / "bin" / "squad-path-guard").is_file())

    def test_manager_guard_on_bash_only(self):
        guard = '"${CLAUDE_PLUGIN_ROOT}/bin/squad-manager-guard"'
        self.assertEqual(commands("PreToolUse", "Bash"), [(guard, None, None)])
        self.assertTrue((Path(__file__).resolve().parent.parent / "bin" / "squad-manager-guard").is_file())

    def test_handin_gate_before_send_message(self):  # EVID-0: the one blocking gate
        gate = '"${CLAUDE_PLUGIN_ROOT}/bin/squad-handin-gate"'
        self.assertEqual(commands("PreToolUse", "SendMessage"), [(gate, None, 30)])
        self.assertTrue(os.access(Path(__file__).resolve().parent.parent / "bin" / "squad-handin-gate", os.X_OK))

    def test_notify_on_notification(self):
        self.assertEqual(commands("Notification", "permission_prompt|elicitation_dialog"), [(NOTIFY, True, 5)])

    def test_herdr_bg_on_bash_monitor_taskstop_and_stop(self):
        bg = '"${CLAUDE_PLUGIN_ROOT}/hooks/herdr-bg" hook'
        self.assertEqual(commands("PostToolUse", "Bash|Monitor|TaskStop"), [(bg, None, 5)])
        self.assertIn((bg, None, 5), commands("Stop"))
        self.assertTrue((Path(__file__).resolve().parent.parent / "hooks" / "herdr-bg").is_file())

    def test_one_module_listed_beside_the_command_hooks(self):
        # The engine takes one module per plugin: ./register.tsx runs po-inbox and squads.
        self.assertEqual(HOOKS_FILE["modules"], ["./register.tsx"])
        hooks = Path(__file__).resolve().parent.parent / "hooks"
        for mod in ("register.tsx", "po-inbox/register.tsx", "squads/register.tsx"):
            self.assertTrue((hooks / mod).is_file())


if __name__ == "__main__":
    unittest.main()
