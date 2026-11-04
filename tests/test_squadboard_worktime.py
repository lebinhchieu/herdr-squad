"""squadboard_worktime (ticket 15): work time pieces, marks, collapsible gaps. Test names carry the AC id."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "bin"))
import squadboard_worktime as wt  # noqa: E402
import squadreport as sr  # noqa: E402
import squadreport_tasks as rt  # noqa: E402

FIX = Path(HERE) / "fixtures" / "board" / "worktime"
B = 1_700_000_000
H = 3600


def msg(t, frm, to, text):
    p = text.split()
    return sr.Msg(B + t, frm, to, p[0], p[1] if len(p) > 1 else "", text)


def seg(a, b, bucket, on=None, stalled=False):
    return sr.Seg(B + a, B + b, bucket, "peer" if bucket == "blocking" else ("human_input" if bucket == "idle" else None),
                  on, stalled)


def collected(agents, msgs=(), roster=()):
    return sr.Collected(Path("/x"), "sq", "sc", "", "", (B, B + 100 * H), agents, list(msgs), [], list(roster), {}, {}, [])


def tl(name, segs, found=True):
    return sr.AgentTL(name, "developer", found, False, 1, list(segs), [])


def build(c, lo=B, hi=B + 100 * H, gap_s=3600):
    return wt.build(c, lo, hi, gap_s)[0]


class Pieces(unittest.TestCase):
    def setUp(self):
        # Developer on task 03 for 2 h: 1 h working, 30 min waiting, 30 min idle; a 5 s piece in the middle.
        self.msgs = [msg(0, "lead", "dev", "ASSIGN 03 go")]
        self.dev = tl("dev", [seg(0, 1800, "working"), seg(1800, 1805, "working"), seg(1805, 3600, "working"),
                              seg(3600, 5400, "waiting"), seg(5400, 7200, "idle")])
        self.c = collected({"dev": self.dev}, self.msgs)

    def test_T15_AC1_TA2_buckets_sum_to_the_two_hours_and_match_the_report(self):
        d = build(self.c)
        a = d["agents"][0]
        b = a["totals"]["buckets_s"]
        self.assertEqual(sum(b.values()), 2 * H)
        self.assertEqual((b["working"], b["waiting"], b["idle"]), (H, 1800, 1800))
        rep, _, _, _ = sr._sum_segs(self.dev.segs)
        self.assertEqual((b["working"], b["waiting"], b["idle"], b["blocked"]),
                         (rep["working"], rep["waiting"], rep["idle"], rep["blocking"]))
        self.assertTrue(all(p["task"] == "03" for p in a["pieces"] if p["bucket"] != "idle"))

    def test_T15_TA2_short_piece_kept_where_the_report_drawing_drops_it(self):
        mine = [p for p in build(self.c)["agents"][0]["pieces"] if p["end"] - p["start"] == 5]
        self.assertEqual(len(mine), 1)
        drawn = rt._segments([(B, B + 1800, "working", None, "03"), (B + 1800, B + 1805, "waiting", None, "03"),
                              (B + 1805, B + 3600, "working", None, "03")], B, 30)
        self.assertTrue(all(s[1] - s[0] >= 30 for s in drawn))
        self.assertEqual(rt._segments([(B, B + 5, "working", None, "03")], B, 0)[0][1], 5)  # no minimum: kept

    def test_T15_TA3_AC3_piece_shape_and_approx(self):
        d = build(self.c)
        keys = {"start", "end", "bucket", "on", "task", "worktree", "branch", "approx", "collapsible", "open"}
        for p in d["agents"][0]["pieces"]:
            self.assertEqual(set(p), keys)
            self.assertIn(p["bucket"], ("working", "waiting", "blocked", "idle"))
            self.assertIsNotNone(p["end"])
            self.assertEqual((p["worktree"], p["branch"], p["open"]), ("", "", False))
            self.assertEqual(p["approx"], p["task"] is not None)
        self.assertTrue(any(p["approx"] for p in d["agents"][0]["pieces"]))

    def test_T15_TA3_blocking_is_renamed_blocked_in_one_place(self):
        c = collected({"dev": tl("dev", [seg(0, 600, "blocking", "qa")])})
        p = build(c)["agents"][0]["pieces"][0]
        self.assertEqual((p["bucket"], p["on"]), ("blocked", "qa"))

    def test_T15_AC2_TA5_unattributed_in_hours_minutes_never_percent(self):
        # 03 starts at 3600: the first hour has no task (no message, no roster Owns).
        c = collected({"dev": tl("dev", [seg(0, 3600, "working"), seg(3600, 4500, "working")])},
                      [msg(3600, "lead", "dev", "ASSIGN 03 go")])
        d = build(c)
        u = d["agents"][0]["totals"]["unattributed"]
        self.assertEqual((u["seconds"], u["hours"], u["minutes"], u["label"]), (3600, 1, 0, "1 h 0 min"))
        self.assertNotIn("%", json.dumps(d))

    def test_T15_TA5_roster_owns_is_the_second_layer(self):
        c = collected({"dev": tl("dev", [seg(0, 600, "working")])}, [], [{"Agent": "dev", "Owns": "ticket 07"}])
        self.assertEqual(build(c)["agents"][0]["pieces"][0]["task"], "07")

    def test_T15_AC4_TA8_no_transcript_no_time(self):
        c = collected({"ghost": tl("ghost", [], found=False)}, [msg(10, "ghost", "lead", "HANDIN 03 x")])
        a = build(c)["agents"][0]
        self.assertEqual((a["pieces"], a["note"]), ([], "no transcript: ghost"))
        self.assertNotIn("totals", a)

    def test_T15_AC7_TA4_range_clips_and_drops(self):
        d = build(self.c, lo=B + 600, hi=B + 1200)
        ps = d["agents"][0]["pieces"]
        self.assertEqual((ps[0]["start"], ps[-1]["end"]), (B + 600, B + 1200))
        self.assertEqual(build(self.c, lo=B + 9 * H, hi=B + 10 * H)["agents"][0]["pieces"], [])


class Gaps(unittest.TestCase):
    def test_T15_AC5_TA7_system_ended_night_gap_is_collapsible_and_not_work(self):
        night = int(11.2 * H)
        c = collected({"dev": tl("dev", [seg(0, 600, "working"), seg(600, 600 + night, "working", stalled=True),
                                         seg(600 + night, 900 + night, "working")])})
        a = build(c)["agents"][0]
        flags = [p["collapsible"] for p in a["pieces"]]
        self.assertEqual(flags, [False, True, False])
        self.assertEqual(a["totals"]["counted_s"]["working"], 900)
        self.assertEqual(a["totals"]["collapsed_s"], night)

    def test_T15_TA7_waiting_and_blocked_never_collapse_idle_does(self):
        c = collected({"dev": tl("dev", [seg(0, 5 * H, "waiting"), seg(5 * H, 9 * H, "blocking", "PO"),
                                         seg(9 * H, 14 * H, "idle")])})
        self.assertEqual([p["collapsible"] for p in build(c)["agents"][0]["pieces"]], [False, False, True])

    def test_T15_TA7_threshold_is_over_n_minutes(self):
        c = collected({"dev": tl("dev", [seg(0, 900, "idle"), seg(900, 1801, "idle")])})
        self.assertEqual([p["collapsible"] for p in build(c, gap_s=900)["agents"][0]["pieces"]], [False, True])

    def test_T15_TA7_gap_min_clamped_to_15_240(self):
        sel = lambda g: {"kind": "scope", "squad": mock.Mock(path=Path("/nowhere")), "name": "s", "home": Path("/nowhere/s"),
                         "now": B, "params": {"gap_min": g, "from": "0", "to": "1"}}
        got = {g: wt.read(sel(g))["data"]["gap_min"] for g in ("14", "15", "240", "241", "abc")}
        self.assertEqual(got, {"14": 15, "15": 15, "240": 240, "241": 240, "abc": 60})

    def test_T15_AC6_TA7_dst_gap_is_real_elapsed_seconds(self):
        # Europe/Berlin ends DST 2026-10-25 01:00 UTC; America/New_York 2026-11-01 06:00 UTC: 1 h more on the local clock.
        old = os.environ.get("TZ")
        try:
            for tz, start in (("Europe/Berlin", 1_792_886_400 - 2 * H), ("America/New_York", 1_793_512_800 - 2 * H)):
                os.environ["TZ"] = tz
                time.tzset()
                c = collected({"dev": tl("dev", [sr.Seg(start, start + 12 * H, "idle", "human_input", None)])})
                p = wt.build(c, start, start + 20 * H, 3600)[0]["agents"][0]["pieces"][0]
                self.assertEqual(p["end"] - p["start"], 12 * H, tz)
                self.assertEqual(wt.hm(p["end"] - p["start"])["label"], "12 h 0 min")
        finally:
            if old is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = old
            time.tzset()


class Marks(unittest.TestCase):
    def test_T15_TA6_AC3_message_marks_deduped_without_approx(self):
        ms = [msg(100, "dev", "qa", "HANDIN 03 a"), msg(105, "dev", "qb", "HANDIN 03 a"), msg(900, "qa", "dev", "FAIL 03 no"),
              msg(1500, "qa", "dev", "PASS 03"), msg(1600, "dev", "lead", "BLOCKED 03 x"), msg(1700, "lead", "dev", "STATUS? go")]
        marks = build(collected({"dev": tl("dev", [seg(0, 10, "working")])}, ms))["marks"]
        self.assertEqual([m["kind"] for m in marks], ["handin", "fail", "pass", "blocked"])
        self.assertTrue(all(set(m) == {"ts", "kind", "agent", "task"} for m in marks))

    def test_T15_TA6_commit_marks_from_scope_branches_and_missing_git(self):
        with tempfile.TemporaryDirectory() as d:
            env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                   "GIT_COMMITTER_EMAIL": "t@t", "GIT_AUTHOR_DATE": "@%d +0000" % (B + 50), "GIT_COMMITTER_DATE": "@%d +0000" % (B + 50)}
            for a in (["init", "-q", "-b", "squad/sq/sc/dev"], ["commit", "-q", "--allow-empty", "-m", "x"]):
                subprocess.run(["git", "-C", d, *a], check=True, capture_output=True, env=env)
            marks, ok = wt.commit_marks(d, "sq", "sc", B, B + 100)
            self.assertEqual((ok, [(m["ts"], m["kind"]) for m in marks]), (True, [(B + 50, "commit")]))
            self.assertNotIn("approx", marks[0])
            self.assertEqual(wt.commit_marks(d, "sq", "other", B, B + 100), ([], True))
            with mock.patch("subprocess.run", side_effect=FileNotFoundError):
                data, unknown = wt.build(collected({}), B, B + 100, 3600, repo=d, squad="sq", scope="sc")
            self.assertEqual((data["marks"], unknown), ([], ["git"]))


def write_squad(tmp, fixture="normal.jsonl", session="sess1", agent="wt-dev-normal", messages=None):
    home = Path(tmp) / ".claude" / "squads" / "sq" / "scopes" / "sc"
    home.mkdir(parents=True)
    (home / "scope.md").write_text("# sc\n", encoding="utf-8")
    (home / "roster.md").write_text(
        "| Agent | Role | Scope | Owns | Status | Session |\n| --- | --- | --- | --- | --- | --- |\n"
        "| %s | developer | sc | ticket 03 | live | %s |\n| ghost | developer | sc | - | live | nosuch |\n" % (agent, session),
        encoding="utf-8")
    (home / "messages.jsonl").write_text(messages if messages is not None else "", encoding="utf-8")
    proj = Path(tmp) / "cfg" / "projects" / "-proj"
    proj.mkdir(parents=True)
    shutil.copy(FIX / fixture, proj / (session + ".jsonl"))
    return home, proj / (session + ".jsonl")


def sel_for(tmp, home, **params):
    import squadboard
    squad = squadboard.Squad(home.parent.parent, "sq")
    return {"squads": [squad], "squad": squad, "kind": "scope", "name": "sc", "home": home,
            "repo_root": Path(tmp) / "norepo", "now": 2 * B, "params": params}


def snapshot(root):
    return sorted((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in Path(root).rglob("*") if p.is_file())


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        self.env = mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(Path(self.tmp) / "cfg")})
        self.env.start()
        self.addCleanup(self.env.stop)
        wt._CACHE.clear()
        wt._PATHS.clear()

    def test_T15_TA9_TA1_TA2_real_normal_sample_matches_the_report(self):
        home, _ = write_squad(self.tmp)
        r = wt.read(sel_for(self.tmp, home, **{"from": "0", "to": str(2 * B)}))
        self.assertEqual(r["quality"], "approx")
        a = next(x for x in r["data"]["agents"] if x["agent"] == "wt-dev-normal")
        c = sr.collect(home, home.parent.parent, wt.BIN.parent, final=True)
        rep, _, _, _ = sr._sum_segs(c.agents["wt-dev-normal"].segs)
        b = a["totals"]["buckets_s"]
        self.assertEqual((b["working"], b["waiting"], b["blocked"], b["idle"]),
                         (rep["working"], rep["waiting"], rep["blocking"], rep["idle"]))
        self.assertGreater(b["working"], 0)
        self.assertTrue(all(p["task"] == "03" for p in a["pieces"] if p["bucket"] != "idle"))  # roster Owns
        ghost = next(x for x in r["data"]["agents"] if x["agent"] == "ghost")
        self.assertEqual((ghost["pieces"], ghost["note"]), ([], "no transcript: ghost"))
        self.assertIn("transcript", r["unknown"])

    def test_T15_AC5_TA9_real_long_gap_sample_is_collapsed_not_work(self):
        home, _ = write_squad(self.tmp, "long-gap.jsonl", "sess2", "wt-dev-long")
        a = next(x for x in wt.read(sel_for(self.tmp, home, **{"from": "0", "to": str(2 * B)}))["data"]["agents"]
                 if x["agent"] == "wt-dev-long")
        big = [p for p in a["pieces"] if p["end"] - p["start"] > 11 * H]
        self.assertEqual((len(big), big[0]["bucket"], big[0]["collapsible"]), (1, "working", True))
        self.assertLess(a["totals"]["counted_s"]["working"], H)
        self.assertGreater(a["totals"]["collapsed_s"], 11 * H)

    def test_T15_AC7_TA4_refusals(self):
        home, _ = write_squad(self.tmp)
        s = sel_for(self.tmp, home)
        self.assertEqual(wt.read({**s, "kind": None, "name": None, "home": None})["refused"], 400)  # no choice
        self.assertEqual(wt.read(sel_for(self.tmp, home, **{"from": "10", "to": "10"}))["refused"], 400)
        self.assertEqual(wt.read(sel_for(self.tmp, home, **{"from": "abc"}))["refused"], 400)
        ok = wt.read(sel_for(self.tmp, home))
        self.assertEqual((ok.get("refused"), ok["data"]["gap_min"]), (None, 60))
        self.assertIn("quality", ok)
        self.assertIn("unknown", ok)

    def test_T15_TA10_cache_never_serves_a_grown_transcript(self):
        home, tr = write_squad(self.tmp)
        sel = sel_for(self.tmp, home, **{"from": "0", "to": str(2 * B)})

        def working():
            return next(x for x in wt.read(sel)["data"]["agents"] if x["agent"] == "wt-dev-normal")["totals"]["buckets_s"]["working"]
        first = working()
        with mock.patch.object(sr, "collect", wraps=sr.collect) as spy:
            self.assertEqual(working(), first)
            self.assertEqual(spy.call_count, 0)  # same mtime + size: from the cache
        last = json.loads(tr.read_text(encoding="utf-8").splitlines()[-1])
        from datetime import datetime, timedelta
        t = datetime.fromisoformat(last["timestamp"].replace("Z", "+00:00")) + timedelta(seconds=90)
        rec = {"type": "assistant", "timestamp": t.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "isSidechain": False,
               "message": {"id": "m9", "model": "x", "content": [], "usage": {}}}
        with open(tr, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(rec) + "\n")
        self.assertEqual(working(), first + 90)

    def test_T15_TA10_TA8_broken_sources_never_raise(self):
        home, tr = write_squad(self.tmp, messages='{"ts": "2026-01-01T00:00:00Z", "text": "HANDIN 03 x"\n{broken')
        with open(tr, "a", encoding="utf-8", newline="\n") as f:
            f.write('{"type":"assistant","timestamp":"2026-10-2')  # truncated last line
        r = wt.read(sel_for(self.tmp, home, **{"from": "0", "to": str(2 * B)}))
        self.assertIsNotNone(r["data"])  # transcript + messages broken; git is absent (repo_root has no repo)
        self.assertIn("git", r["unknown"])
        self.assertEqual(wt.read({"kind": "scope", "squad": object(), "name": "x"})["unknown"], ["worktime"])

    def test_T15_TA10_cache_is_thread_safe(self):
        homes = []
        for i in range(wt.CACHE_MAX + 1):
            home = Path(self.tmp) / ("h%d" % i)
            home.mkdir()
            (home / "roster.md").write_text("", encoding="utf-8")
            homes.append(home)
        errors = []

        def work():
            try:
                for _ in range(3):
                    for h in homes:
                        wt.collected(h, Path(self.tmp))
            except Exception as e:  # noqa: BLE001
                errors.append(e)
        ts = [threading.Thread(target=work) for _ in range(4)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        self.assertEqual(errors, [])

    def test_T15_TA11_read_only(self):
        home, _ = write_squad(self.tmp)
        before = snapshot(self.tmp)
        wt.read(sel_for(self.tmp, home, **{"from": "0", "to": str(2 * B)}))
        self.assertEqual(snapshot(self.tmp), before)


if __name__ == "__main__":
    unittest.main()
