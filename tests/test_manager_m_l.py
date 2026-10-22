"""Manager rules: Team Lead runs the pod in M and L; S text differs. Checked on the composed Manager rules."""
import unittest

from rulesview import composed

MS = composed("manager", "S")
MM = composed("manager", "L")  # Team Lead exists at L only
MG = composed("manager", "L", goal="yes")


class ManagerMLTest(unittest.TestCase):
    def test_s_keeps_developer_spawning_and_routing(self):
        self.assertIn("## SPAWN-5a Developers, Manager in S and M", MS)
        self.assertIn("## SPAWN-5a", composed("manager", "M"))
        self.assertIn("## MSG-18 Routing, Manager in S", MS)
        self.assertNotIn("## SPAWN-5a", MM)
        self.assertNotIn("## MSG-18", MM)

    def test_s_keeps_the_pod_health_checks(self):
        s = MS.split("## SPAWN-10a")[1].split("## SPAWN-11")[0] if "## SPAWN-11" in MS.split("## SPAWN-10a")[1] else MS.split("## SPAWN-10a")[1]
        for token in ("`herdr agent list`", "ASK <name>: STATUS?", "Looping", "Context filling"):
            self.assertIn(token, s)
        self.assertIn("## LC-7a Three returns, S", MS)

    def test_m_l_manager_does_not_spawn_or_poll_developers(self):
        self.assertIn("The Team Lead spawns and retires Developers within its share of the cap; the Manager does not", MM)
        self.assertIn("Watch the Team Lead only; the Team Lead runs the pod's health checks", MM)
        self.assertNotIn("The Team Lead (Tech Lead in S and M) tells you", MM)
        self.assertNotIn("tell the PO which pane", MM)

    def test_m_l_watch_the_team_lead_only(self):
        h = MM.split("## SPAWN-10b")[1]
        self.assertIn("Watch the Team Lead only", h)
        self.assertIn("is the Team Lead alive", h)
        self.assertIn("`iterations/<n>.summary.md`", h)
        self.assertIn("respawn it from its notes", h)

    def test_team_lead_briefing_carries_size_and_cap_share(self):
        self.assertIn("Tell each Team Lead its Developer share of the cap in its first prompt", MM)
        self.assertIn("A lone scope gets the whole cap", MM)
        self.assertIn("divides the cap among the scopes running at that time, shares summing to at most the cap", MG)
        self.assertIn("A finished scope's share goes to the scopes still running, at their next briefing or respawn", composed("team-lead", "L"))

    def test_disputes_split_and_final_stay(self):
        self.assertIn("except plan, order and assignment ones, which the Team Lead settles", MM)
        self.assertIn("no one relays", MM)
        self.assertIn("starts with `FINAL:` and is sent once", MM)

    def test_stacked_base_named_by_manager_used_by_team_lead(self):
        self.assertIn("The Manager checks the base ([GOAL-7]) and names it in the iteration file; the spawner passes that base and no other", MG)

    def test_retained_duties(self):
        for token in ("Moving up", "Merge only on the PO's request", "squad-inbox add", "Token Coach", "squad-close <squad> --scope"):
            self.assertIn(token, MG)

    def test_merging_reads_sha_from_files_and_checkin_gets_three_returns_line(self):
        self.assertIn("passed sha and checkers from `iterations/<n>.summary.md` or the task files, never from messages", MM)
        self.assertNotIn("(B15)", MM)
        self.assertIn("the Team Lead's one line at 3 returns on a task (M, L)", MM)


if __name__ == "__main__":
    unittest.main()
