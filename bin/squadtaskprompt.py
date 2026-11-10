"""Builds the first prompt for `squad-spawn --task NN`: scope, ticket, files to read first, duties, team, HANDIN target
and owner names, from the ticket, scope.md `team:` and roster.md. No second copy of the SIZE-22 chains: the hand-in
target comes from squadrules.resolve_duties. Ticket lines are quoted with json.dumps, so they stay one line of data."""
import json
import re
from pathlib import Path

import squadrules
import squadreviewpack

USAGE = "usage: squad-task-prompt NN --role ROLE --name AGENT --scope-home DIR [--repo-root DIR]"
ROLE_OF_TOKEN = {"qa-white": "qa-whitebox", "qa-black": "qa-blackbox", "team-lead": "team-lead", "tech-lead": "tech-lead",
                 "ba": "ba", "manager": "manager", "dev": "dev"}


class Refuse(Exception):
    pass


def parse(argv):
    if not argv or not re.fullmatch(r"\d+", argv[0]):
        raise Refuse("bad ticket number %r (digits only). %s" % (argv[:1] and argv[0] or "", USAGE))
    out = {"nn": argv[0], "role": "", "name": "", "scope": "", "repo": ""}
    keys = {"--role": "role", "--name": "name", "--scope-home": "scope", "--repo-root": "repo"}
    i = 1
    while i < len(argv):
        if argv[i] not in keys or i + 1 >= len(argv):
            raise Refuse(USAGE)
        out[keys[argv[i]]] = argv[i + 1]
        i += 2
    if not (out["role"] and out["name"] and out["scope"]):
        raise Refuse(USAGE)
    return out


def roster(scope):
    """-> [(agent, role, owns, status)] of roster.md rows."""
    try:
        text = (Path(scope) / "roster.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.strip().startswith("|") and len(cells) >= 5 and cells[0] != "Agent" and not set(cells[0]) <= set("-: "):
            rows.append((cells[0], cells[1], cells[3], cells[4].lower()))
    return rows


def names_of(rows, role):
    live = [a for a, r, _, st in rows if r == role and not st.startswith("retired")]
    return live or [a for a, r, _, _ in rows if r == role]


def field(text, label):
    m = re.search(r"^%s:[ \t]*(.*\S)[ \t]*$" % label, text, re.M)
    return m.group(1) if m else ""


def team_of(scope):
    try:
        text = (Path(scope) / "scope.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        raise Refuse("no scope.md in %s" % scope)
    try:
        team = squadrules.parse_team(field(text, "team"), "scope.md")
    except ValueError as e:
        raise Refuse(str(e))
    if team is None:
        raise Refuse("the team is undecided in %s/scope.md" % scope)
    return team


def handin_names(team, rows):
    owner = squadrules.resolve_duties(team)["handin-target"]
    roles = [ROLE_OF_TOKEN[t] for t in ("qa-white", "qa-black") if t in team] if owner == "qas" else [ROLE_OF_TOKEN[owner]]
    names = []
    for role in roles:
        found = names_of(rows, role)
        if not found:
            raise Refuse("roster.md has no %s row, the HANDIN target (add it before spawning)" % role)
        names.append(found[0])
    return names


def developer_of(rows, nn):
    for a, r, owns, _ in rows:
        if r == "dev" and "ticket" in owns.lower() and re.search(r"(?<!\d)0*%d(?!\d)" % int(nn), owns):
            return a
    return ""


def build(a):
    scope = a["scope"]
    top = a["repo"] or scope
    try:
        path, _ = squadreviewpack.find_ticket(scope, a["nn"], top)
    except squadreviewpack.Usage as e:
        raise Refuse(str(e))
    text = path.read_text(encoding="utf-8", errors="replace")
    duties, files = field(text, "Duties"), field(text, "Files")
    for label, val in (("Duties:", duties), ("Files:", files)):
        if not val:
            raise Refuse("ticket %s: no %s line in %s; nothing spawned" % (a["nn"], label, path))
    team = team_of(scope)
    rows = roster(scope)
    target = handin_names(team, rows)
    mgr = (names_of(rows, "manager") or ["the Manager"])[0]
    tech = squadrules.resolve_duties(team)["tech-ac"]
    tech_name = (names_of(rows, ROLE_OF_TOKEN[tech]) or [tech])[0] if tech != "dev" else a["name"]
    common = ("Ticket %s of scope %s. Ticket file: %s. Scope folder: %s. Team: %s. Duties (quoted from the ticket): %s. "
              "Files to read first (quoted from the ticket): %s. " % (
                  a["nn"], Path(scope).name, path, scope, ", ".join(team) or "none", json.dumps(duties), json.dumps(files)))
    if a["role"] == "dev":
        return (common + "You are %s, the Developer. Your working directory is your worktree. Build this one ticket as written; "
                "run squad-label first. HANDIN to %s. Ask %s for technical acceptance criteria and %s for anything else."
                % (a["name"], " and ".join(target), tech_name, mgr))
    dev = developer_of(rows, a["nn"]) or "the Developer who owns the ticket"
    return (common + "You are %s, %s. Check this ticket when %s sends HANDIN; send PASS or FAIL to that Developer. "
            "Plain questions go to %s." % (a["name"], a["role"], dev, mgr))


def run(argv):
    import sys
    try:
        sys.stdout.write(build(parse(argv)) + "\n")
        return 0
    except Refuse as e:
        sys.stderr.write("squad-task-prompt: %s\n" % e)
        return 2
