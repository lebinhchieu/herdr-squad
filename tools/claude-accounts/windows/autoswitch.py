"""Keep a group of Herdr Claude sessions on one account and move them all when it runs low.

Run it in its own Herdr pane (it must outlive the sessions it restarts):
    python -I ~/.claude-accounts/autoswitch.py [--cwd DIR] [--pane ID ...] [--threshold 90]
                                               [--dry-run] [--once]

Every minute it reads every account's 5-hour usage from the usage API. When the group's account
reaches the threshold and another account is lower, the group moves to the lowest one: each
session, once idle, is /exit-ed and resumed on the new account with the same flags it was started
with (read from its claude.exe command line), then nudged to carry on. The whole group moves
together because cross-session messages only reach sessions on the same account.

Which account a session is on can't be read from outside the process, so it is tracked in
autoswitch-state.json; a session not in it is assumed to be on the default account (`cdefault`).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True  # keep ~/.claude-accounts free of __pycache__
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from usage import ACCOUNTS, ACCT_HOME, usage  # noqa: E402

STATE = os.path.join(ACCT_HOME, "autoswitch-state.json")
LOG = os.path.join(ACCT_HOME, "autoswitch.log")
NUDGE = ("You were resumed on Claude account {to} because your previous account reached its usage "
         "limit. Re-read your notes if you keep any, then continue where you left off.")
# An idle agent with a background monitor/shell is not free: /exit would offer to kill it.
BACKGROUND_WORK = re.compile(r"\b\d+ (monitors?|shells?)\b")


def log(msg, dry=False):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + ("[dry-run] " if dry else "") + msg
    print(line, flush=True)
    if not dry:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def herdr(*args, parse=True):
    out = subprocess.run(["herdr", *args], capture_output=True, text=True, encoding="utf-8")
    if not parse:
        return out.stdout
    try:
        return json.loads(out.stdout)["result"]
    except (ValueError, KeyError):
        return None


def load_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"group": None, "sessions": {}}


def save_state(state):
    with open(STATE, "w") as f:
        json.dump(state, f, indent=2)


def seen_account(sid):
    """Account the status line last saw this session on (record-usage.sh), or None."""
    try:
        return open(os.path.join(ACCT_HOME, "sessions", sid)).read().strip() or None
    except (OSError, TypeError):
        return None


def default_account():
    try:
        return open(os.path.join(ACCT_HOME, "default")).read().strip()
    except OSError:
        return "1"


def claude_argv(pane_id):
    """The pane's claude.exe argv without the program and any resume/continue flags."""
    info = herdr("pane", "process-info", "--pane", pane_id) or {}
    for proc in info.get("process_info", {}).get("foreground_processes", []):
        if proc.get("name", "").lower().startswith("claude"):
            argv, keep, skip = proc["argv"][1:], [], False
            for a in argv:
                if skip:
                    skip = False
                elif a in ("--resume", "-r", "--session-id"):
                    skip = True
                elif a not in ("--continue", "-c"):
                    keep.append(a)
            return keep, argv
    return None, None


def session_id(pane, argv):
    sid = (pane.get("agent_session") or {}).get("value")
    if not sid and argv:
        for flag in ("--resume", "-r", "--session-id"):
            if flag in argv and argv.index(flag) + 1 < len(argv):
                return argv[argv.index(flag) + 1]
    return sid


def claude_panes(cwd_prefix, pane_ids):
    panes = (herdr("pane", "list") or {}).get("panes", [])
    out = []
    for p in panes:
        if p.get("agent") != "claude":
            continue
        if pane_ids and p["pane_id"] not in pane_ids:
            continue
        if cwd_prefix and not os.path.normcase(p.get("cwd", "")).startswith(cwd_prefix):
            continue
        out.append(p)
    return out


def is_free(pane_id):
    p = herdr("pane", "get", pane_id) or {}
    if p.get("pane", {}).get("agent_status") not in ("idle", "done"):
        return False
    return not BACKGROUND_WORK.search(herdr("pane", "read", pane_id, "--lines", "3", parse=False))


def wait_for(cond, seconds):
    for _ in range(seconds):
        if cond():
            return True
        time.sleep(1)
    return False


def has_claude(pane_id):
    return (herdr("pane", "get", pane_id) or {}).get("pane", {}).get("agent") == "claude"


def quote(arg):
    # Single quotes work in PowerShell and bash panes; PowerShell escapes ' as ''.
    return "'" + arg.replace("'", "''") + "'"


def switch(pane_id, sid, args, to):
    """Exit the idle session and resume it on account `to`. True on success."""
    herdr("agent", "prompt", pane_id, "/exit")
    if not wait_for(lambda: not has_claude(pane_id), 60):
        herdr("pane", "send-keys", pane_id, "escape")  # e.g. a "background work is running" dialog
        log(f"{pane_id}: /exit did not close the session; will retry")
        return False
    time.sleep(2)  # let the shell prompt come back before typing
    herdr("pane", "run", pane_id, f"c{to} --resume {sid} " + " ".join(quote(a) for a in args))
    if not wait_for(lambda: has_claude(pane_id) and is_free(pane_id), 180):
        log(f"{pane_id}: resumed session not ready after 3 min; check the pane")
        return False
    herdr("agent", "prompt", pane_id, NUDGE.format(to=to))
    return True


def tick(opts, state):
    u = {a: usage(a) for a in ACCOUNTS}
    group = state["group"] or default_account()
    if not u[group]:
        log(f"usage unknown for account {group}; skipping this pass")
        return
    # An account not logged in has no usage; one with its 7-day window spent can't take the group.
    others = {a: v for a, v in u.items() if a != group and v and v["week"] < opts.threshold}
    other = min(others, key=lambda a: others[a]["five"], default=None)
    spent = u[group]["five"] >= opts.threshold or u[group]["week"] >= opts.threshold
    if other and spent and (u[other]["five"] < u[group]["five"] or u[group]["week"] >= opts.threshold):
        log(f"account {group} at {u[group]['five']:.0f}%/7d {u[group]['week']:.0f}% "
            f"(account {other} {u[other]['five']:.0f}%): "
            f"moving the group to account {other}", opts.dry_run)
        group = other
        if not opts.dry_run:
            state["group"] = group
            save_state(state)
    for pane in claude_panes(opts.cwd, opts.pane):
        pid = pane["pane_id"]
        args, argv = claude_argv(pid)
        sid = session_id(pane, argv)
        if not sid or args is None:
            continue
        # Herdr can report a new session id for a resumed session (e.g. after compaction);
        # fall back to the id the process was resumed with.
        resumed = argv[argv.index("--resume") + 1] if "--resume" in argv[:-1] else None
        # Unknown account: wait for the status line to record it rather than guess the default
        # (a wrong guess restarts a session onto the account it is already on).
        current = (seen_account(sid) or seen_account(resumed) or state["sessions"].get(sid)
                   or state["sessions"].get(resumed))
        if current is None:
            continue
        if current == group:
            continue
        if not is_free(pid):
            continue  # busy or has background work; retry on the next pass
        log(f"{pid}: session {sid} account {current} -> {group}", opts.dry_run)
        if not opts.dry_run and switch(pid, sid, args, group):
            state["sessions"][sid] = group
            save_state(state)
            # The status line rewrites this on the next render; until then it still names the old account.
            with open(os.path.join(ACCT_HOME, "sessions", sid), "w") as f:
                f.write(group)
            log(f"{pid}: resumed on account {group} and nudged")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--cwd", help="only sessions whose working directory starts with this")
    ap.add_argument("--pane", action="append", help="only this pane (repeatable)")
    ap.add_argument("--threshold", type=float, default=90, help="5-hour usage %% that triggers a move")
    ap.add_argument("--interval", type=int, default=60, help="seconds between passes")
    ap.add_argument("--dry-run", action="store_true", help="log what would happen, change nothing")
    ap.add_argument("--once", action="store_true", help="run one pass and exit")
    opts = ap.parse_args()
    if opts.cwd:
        opts.cwd = os.path.normcase(os.path.abspath(opts.cwd))
    state = load_state()
    log(f"start: cwd={opts.cwd} panes={opts.pane} threshold={opts.threshold}% "
        f"group account={state['group'] or default_account()}", opts.dry_run)
    while True:
        tick(opts, state)
        if opts.once:
            return
        time.sleep(opts.interval)


if __name__ == "__main__":
    main()
