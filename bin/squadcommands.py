"""The commands table of the /squads pane (design-notes section 3): THE one list of commands, with who runs each,
what it changes and when it applies. A new command is one record in COMMANDS; commands_for() filters the table.

`info` is a plain dict about one squad, goal or scope:
  kind (squad|goal|scope), name, squad_path (the squad folder: squad-report takes a name only with $SQUAD_DIR set), status (open|done), home, squad (folder name), goal (name of the existing goal a
  scope sits in, else None), facts (dict or None), open_scopes (names of a goal's open scopes, sorted), flat, lone.
Copy only: no record has an argv or a run flag. `--force` is never in a text.
"""
import os
import re
import shlex
import subprocess

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
KEYS = ("id", "label", "text", "changes", "runs_by", "group", "state", "reason", "placeholder", "when")


def q(s):
    """One shell word: shlex.quote on POSIX, list2cmdline on Windows (ADR 0011)."""
    return subprocess.list2cmdline([s]) if os.name == "nt" else shlex.quote(s)


def name_safe(name):
    return isinstance(name, str) and bool(NAME_RE.match(name))


def _f(info, key):
    return (info.get("facts") or {}).get(key)


def _resume_name(i):
    return i["goal"] or i["name"]  # squad-start refuses a scope that has a goal: use the goal's name


def _board_text(i):
    if i["kind"] == "squad":
        return "squad-board --squad %s" % q(i["squad"])
    return "squad-board --squad %s --%s %s" % (q(i["squad"]), i["kind"], q(i["name"]))


def _board_when(i):
    stop = "Keeps running: stop with Ctrl-C."
    if i["kind"] == "squad" or i["status"] == "open":
        return "Open the board. " + stop
    return "See the closed %s. %s" % (i["kind"], stop)


def _resume_ready(i):
    return ("wait", "agents are working") if (_f(i, "agents_working") or 0) > 0 else ("ready", None)


def _inbox_ready(i):
    return ("wait", "no open questions") if _f(i, "needs_you") == 0 else ("ready", None)


def _close_scope_ready(i):
    f = i.get("facts") or {}
    return ("wait", "tasks open") if (f.get("tasks_done") or 0) < (f.get("tasks_total") or 0) else ("ready", None)


def _close_goal_ready(i):
    o = i.get("open_scopes") or []
    return ("wait", "scope %s is open" % o[0]) if o else ("ready", None)


def _new_work_ready(i):
    return ("wait", "flat layout: squad-start refuses it") if i.get("flat") else ("ready", None)


def _rec(id, label, text, kinds, status, changes, when, ready=None, placeholder=False, where=None,
         runs_by="chieu", group="yours"):
    return {"id": id, "label": label, "text": text, "kinds": kinds, "status": status, "changes": changes,
            "when": when, "ready": ready, "placeholder": placeholder, "where": where, "runs_by": runs_by,
            "group": group}


def _lone_or_goal(i):
    return i["kind"] == "goal" or not i.get("goal")


TEAM_TOOLS = ("squad-spawn", "squad-respawn", "squad-team", "squad-usage", "squad-task", "squad-merge-check",
              "squad-review-pack", "squad-label", "squad-evidence", "squad-process", "squad-ledger")

COMMANDS = [
    _rec("new-work", "New work", lambda i: 'squad-start "<text>" --squad %s' % q(i["squad"]), ("squad",), "any",
         "starts", "Start new work.", _new_work_ready, True),
    _rec("resume", "Resume", lambda i: "squad-start --resume %s --squad %s" % (q(_resume_name(i)), q(i["squad"])),
         ("goal", "scope"), "open", "starts", "Start the Manager again.", _resume_ready),
    _rec("board", "Board", _board_text, ("squad", "goal", "scope"), "any", "read", _board_when),
    _rec("report", "Report", lambda i: "squad-report %s --squad %s" % (q(i["name"]), q(i["squad_path"])),
         ("goal", "scope"), "any", "writes", "Write the report."),
    _rec("report-status", "Report status",
         lambda i: "squad-report status %s --squad %s" % (q(i["name"]), q(i["squad_path"])), ("scope",), "any", "read",
         "Read the status."),
    _rec("inbox", "Inbox list", lambda i: "squad-inbox --home %s list --open --no-write" % q(i["home"]),
         ("goal", "scope"), "open", "read", "List open questions.", _inbox_ready),
    _rec("watchdog", "Watchdog status", lambda i: "squad-watchdog status --home %s" % q(i["home"]),
         ("goal", "scope"), "open", "read", "Is the watchdog on?"),
    _rec("sleep", "Sleep when idle", lambda i: "squad-watchdog sleep on --home %s" % q(i["home"]),
         ("goal", "scope"), "open", "writes",
         lambda i: "Use when leaving the machine." if i["kind"] == "goal" else "Pause the watchdog."),
    _rec("new-scope", "New scope",
         lambda i: 'squad-start "<text>" --in-goal %s --name <N> --squad %s' % (q(i["name"]), q(i["squad"])),
         ("goal",), "open", "starts", "Add a scope to the goal.", placeholder=True),
    _rec("close-scope", "Close scope",
         lambda i: "squad-close %s --scope %s --dry-run" % (q(i["squad"]), q(i["name"])), ("scope",), "open",
         "destructive", "Close the scope.", _close_scope_ready),
    _rec("close-goal", "Close goal", lambda i: "squad-close %s --goal %s" % (q(i["squad"]), q(i["name"])),
         ("goal",), "open", "destructive", "Close the goal.", _close_goal_ready),
    _rec("close-squad", "Close squad", lambda i: "squad-close %s" % q(i["squad"]), ("squad",), "any",
         "destructive", "Work finished. Warning: retires every agent and archives the squad."),
    _rec("retire", "Retire Manager", lambda i: "squad-retire %s-mgr-%s" % (i["squad"], i["name"]),
         ("goal", "scope"), "done", "destructive", "Retire the finished Manager.",
         where=lambda i: i["kind"] == "goal" or (not i.get("goal"))),
] + [_rec(t, t, (lambda t: lambda i: "%s --help" % t)(t), ("scope",), "open", "varies", "Used by the team.",
          runs_by="team", group="team") for t in TEAM_TOOLS]


def commands_for(info, table=None):
    """The Command dicts of one node, in table order. [] when a name is not safe for a command."""
    if not name_safe(info["name"]) or not name_safe(info["squad"]):
        return []
    out = []
    for r in COMMANDS if table is None else table:
        if info["kind"] not in r["kinds"]:
            continue
        if r["status"] != "any" and info["status"] != r["status"]:
            continue
        if r["where"] and not r["where"](info):
            continue
        state, reason = r["ready"](info) if r["ready"] else ("ready", None)
        when = r["when"](info) if callable(r["when"]) else r["when"]
        out.append({"id": r["id"], "label": r["label"], "text": r["text"](info), "changes": r["changes"],
                    "runs_by": r["runs_by"], "group": r["group"], "state": state, "reason": reason,
                    "placeholder": r["placeholder"], "when": when})
    return out
