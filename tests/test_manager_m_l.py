"""manager.md: Team Lead runs the pod in M and L; S text stays as it was."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
M = (ROOT / "agents/manager.md").read_text()


def section(title):
    return M.split(f"## {title}")[1].split("\n## ")[0]


class ManagerMLTest(unittest.TestCase):
    def test_s_keeps_developer_spawning_and_routing(self):
        self.assertIn("**Developers (S only): one per ready task, up to the cap.**", M)
        self.assertIn("In S spawn one Developer per task that is ready", M)
        self.assertIn("**Routing (S only).**", M)
        self.assertIn("`dev` in S only (M, L: the Team Lead spawns Developers)", M)

    def test_s_keeps_the_pod_health_checks(self):
        h = section("Keeping the squad healthy")
        s = h.split("**S: you run the pod's health checks.**")[1]
        for token in ("`herdr agent list`", "ASK <name>: STATUS?", "**Looping**", "**Context filling**", "**3 returns on one task**"):
            self.assertIn(token, s)

    def test_m_l_manager_does_not_spawn_or_poll_developers(self):
        self.assertIn("the Team Lead spawns and retires Developers within its share of the cap; you do not", M)
        self.assertIn("you do not poll Developers", M)
        self.assertNotIn("The Team Lead (Tech Lead in S and M) tells you", M)
        self.assertNotIn("tell the PO which pane", M)
        self.assertNotRegex(M, r"(?m)^- \*\*`blocked`\*\*")

    def test_m_l_watch_the_team_lead_only(self):
        h = section("Keeping the squad healthy")
        self.assertIn("**M and L: watch the Team Lead only.**", h)
        self.assertIn("is the Team Lead alive", h)
        self.assertIn("`iterations/<n>.summary.md`", h)
        self.assertIn("respawn it from its notes", h)

    def test_team_lead_briefing_carries_size_and_cap_share(self):
        self.assertIn("Tell each Team Lead its Developer share of the cap in its first prompt", M)
        self.assertIn("A lone scope gets the whole cap", M)
        self.assertIn("divides the cap among the scopes running at that time, shares summing to at most the cap", M)
        self.assertIn("A finished scope's share goes to the scopes still running at their next briefing or respawn", M)
        self.assertIn("give each M or L scope's Team Lead a share in its briefing", M)

    def test_disputes_split_and_final_stay(self):
        self.assertIn("except plan, order and assignment ones in M and L, which the Team Lead settles", M)
        self.assertIn("no one relays", M)
        self.assertIn("Start a ruling with `FINAL:` and send it once.", M)

    def test_stacked_base_named_by_manager_used_by_team_lead(self):
        self.assertIn("you check the base and name it in the iteration file; the Team Lead spawns its Developers with that base", M)

    def test_retained_duties(self):
        for token in ("Sizing and changing size", "Merge only on the PO's request", "squad-inbox add", "Token Coach", "squad-close <squad> --scope"):
            self.assertIn(token, M)


if __name__ == "__main__":
    unittest.main()
