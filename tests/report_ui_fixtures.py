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


FIXTURES = {"F-e": f_e_goal_link, "F-e-null": f_e_goal_no_rollup}


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
