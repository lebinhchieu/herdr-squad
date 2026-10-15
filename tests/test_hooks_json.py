"""hooks/hooks.json: valid, existing hooks kept, squad-notify wired for Stop and Notification."""
import json
import unittest
from pathlib import Path

HOOKS_FILE = json.loads((Path(__file__).resolve().parent.parent / "hooks" / "hooks.json").read_text())
HOOKS = HOOKS_FILE["hooks"]
NOTIFY = '"${CLAUDE_PLUGIN_ROOT}/bin/squad-notify"'


def commands(event, matcher=None):
    return [(h["command"], h.get("async"), h.get("timeout")) for g in HOOKS[event]
            if g.get("matcher") == matcher for h in g["hooks"]]


class HooksJsonTest(unittest.TestCase):
    def test_existing_hooks_kept(self):
        self.assertEqual(commands("PostToolUse", "SendMessage")[0][0], '"${CLAUDE_PLUGIN_ROOT}/bin/squad-log-message"')
        self.assertEqual(commands("Stop")[0][0], '"${CLAUDE_PLUGIN_ROOT}/bin/squad-usage-hook"')

    def test_notify_on_stop(self):
        self.assertIn((NOTIFY, True, 5), commands("Stop"))

    def test_notify_on_notification(self):
        self.assertEqual(commands("Notification", "permission_prompt|elicitation_dialog"), [(NOTIFY, True, 5)])

    def test_po_inbox_module_listed_beside_the_command_hooks(self):
        self.assertEqual(HOOKS_FILE["modules"], ["./po-inbox/register.tsx"])
        self.assertTrue((Path(__file__).resolve().parent.parent / "hooks" / "po-inbox" / "register.tsx").is_file())


if __name__ == "__main__":
    unittest.main()
