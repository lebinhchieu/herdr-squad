"""Fixture generator for the squad-report UI tests: one function per fixture, each returns (data, expected).

`python3 tests/report_ui_fixtures.py <outdir>` writes <outdir>/<name>/{data.json,report.html,expected.json}.
Data starts from the real-shaped real_data() of test_squadreport_html.py.
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "bin"))
import squadreport_embed as emb  # noqa: E402
import squadreport_html as html  # noqa: E402

_BASE = []


def base():
    if not _BASE:
        from test_squadreport_html import real_data
        _BASE.append(real_data())
    return copy.deepcopy(_BASE[0])


def _done(d):
    d["scope"].update(status="done", partial=False, partial_reasons=[])
    return d


def _rename(d, old, new):
    for r in d["roles"] + d["agents"]:
        if r["name"] == old:
            r["name"] = new


def _task(tid, returns, rework_s=300, status="passed"):
    t = {"id": tid, "aliases": [], "title": "Task " + tid, "dev": "dev-x", "status": status, "iteration": 1,
         "window": {"start": "2027-01-15T08:00:50Z", "end": "2027-01-15T08:33:20Z"}, "cycle_s": 1950,
         "buckets_s": {"working": 1150, "waiting": 0, "blocking": 0, "idle": 0},
         "tokens": {"input": 1000, "cache_read": 0, "cache_write": 0, "output": 0}, "cost_usd": 0.001,
         "returns": returns, "flag": returns >= 3,
         "returns_list": [{"fail_at": "2027-01-15T08:25:00Z", "fail_by": "qa", "handin_at": "2027-01-15T08:30:00Z",
                           "reason": "finding %d" % (i + 1)} for i in range(returns)],
         "rework_s": rework_s if returns else 0, "rework_cost_usd": 0.5 if returns else 0, "review_waits": []}
    return t


def f_a_retired_with_transcript():
    d = _done(base())
    _rename(d, "dev", "dev-x")
    return d, {"banners": 0, "absent_text": ["still running", "no transcript"], "role": "dev-x"}


def f_b_retired_no_transcript():
    d = _done(base())
    d["scope"]["partial_reasons"] = ["no_transcript:dev-y"]
    _rename(d, "dev", "dev-y")
    for r in d["roles"] + d["agents"]:
        if r["name"] == "dev-y":
            r["transcript_found"] = False
    return d, {"banners": 1, "banner_names": ["dev-y"], "absent_text": ["still running"]}


def f_c_eight_returns():
    d = _done(base())
    d["tasks"] = [_task("03", 2), _task("04", 3), _task("06", 1), _task("07", 1), _task("08", 1)]
    d["totals"]["returns"] = 8
    rw = sum(t["rework_s"] for t in d["tasks"])
    return d, {"banners": 1, "returns_total": 8, "flagged": {"04": 3}, "pills": [2, 3, 1, 1, 1], "rework_s": rw,
               "banner_text_start": "1 task reached 3 or more returns (Task 04: 3) of 8 in all. Rework so far "}


def f_d_running_live():
    d = base()
    d["scope"].update(status="running", partial=True, partial_reasons=["running"])
    _rename(d, "dev", "dev-z")
    for r in d["roles"] + d["agents"]:
        if r["name"] == "dev-z":
            r["live"] = True
    d["tasks"][0].update(id="09", status="running")
    return d, {"banners": 1, "banner_kind": "info", "live_role": "dev-z"}


def f_e_goal_link():
    d = base()
    d["scope"]["goal"] = "g1"
    d["scope"]["rollup_href"] = "../../../goals/g1/report/report.html"
    return d, {"rollup_link": "Rollup: g1 goal →", "href": d["scope"]["rollup_href"]}


def f_e_goal_no_rollup():
    d = base()
    d["scope"]["goal"] = "g1"
    d["scope"]["rollup_href"] = None
    return d, {"rollup_link": None}


FIXTURES = {"F-a": f_a_retired_with_transcript, "F-b": f_b_retired_no_transcript, "F-c": f_c_eight_returns,
            "F-d": f_d_running_live, "F-e": f_e_goal_link, "F-e-null": f_e_goal_no_rollup}


def write_all(out):
    for name, fn in FIXTURES.items():
        d, exp = fn()
        os.makedirs(os.path.join(out, name), exist_ok=True)
        with open(os.path.join(out, name, "data.json"), "w", encoding="utf-8") as f:
            f.write(emb.dumps(d) + "\n")
        html.render_scope(d, os.path.join(out, name))
        with open(os.path.join(out, name, "expected.json"), "w", encoding="utf-8") as f:
            json.dump(exp, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    write_all(sys.argv[1])
