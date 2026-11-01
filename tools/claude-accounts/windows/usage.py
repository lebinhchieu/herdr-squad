"""Usage of all Claude accounts, read live from Anthropic's usage endpoint (what /usage shows).

As a script: prints the Herdr popup (prefix+u). As a module: `usage(account)` for autoswitch.py.
A token is never refreshed here (that could rotate it out from under Claude Code's own login);
when it has expired or the request fails, the status-line cache written by record-usage.sh is used.
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime

HOME = os.path.expanduser("~")
ACCT_HOME = os.path.join(HOME, ".claude-accounts")
# Account 2 lives in ~/.claude-2, account 3 in ~/.claude-3.
CONFIG_DIR = {"1": os.path.join(HOME, ".claude"),
              "2": os.path.join(HOME, ".claude-2"),
              "3": os.path.join(HOME, ".claude-3")}
ACCOUNTS = tuple(CONFIG_DIR)


def live(account):
    """{'five', 'five_reset', 'week', 'week_reset'} from the API, or a reason string."""
    try:
        with open(os.path.join(CONFIG_DIR[account], ".credentials.json")) as f:
            cred = json.load(f)["claudeAiOauth"]
    except (OSError, KeyError, ValueError):
        return "not logged in"
    if cred.get("expiresAt", 0) / 1000 < time.time():
        return "token expired - run it once to refresh"
    req = urllib.request.Request("https://api.anthropic.com/api/oauth/usage", headers={
        "Authorization": "Bearer " + cred["accessToken"], "anthropic-beta": "oauth-2025-04-20"})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=8).read())
    except Exception as e:
        return f"request failed ({e})"
    ts = lambda s: datetime.fromisoformat(s).timestamp() if s else 0
    return {"five": d["five_hour"]["utilization"], "five_reset": ts(d["five_hour"]["resets_at"]),
            "week": d["seven_day"]["utilization"], "week_reset": ts(d["seven_day"]["resets_at"])}


def cached(account):
    """(usage dict, epoch it was cached) from the status-line cache, or (None, None)."""
    try:
        with open(os.path.join(ACCT_HOME, f"usage-{account}")) as f:
            five, five_reset, week, week_reset, at = map(float, f.read().split())
    except (OSError, ValueError):
        return None, None
    return {"five": five, "five_reset": five_reset, "week": week, "week_reset": week_reset}, at


def usage(account):
    """Best available usage dict for an account (a window past its reset counts as 0), or None."""
    u = live(account)
    if isinstance(u, str):
        u, _ = cached(account)
        if u is None:
            return None
    now = time.time()
    if u["five_reset"] and u["five_reset"] < now:
        u["five"] = 0
    if u["week_reset"] and u["week_reset"] < now:
        u["week"] = 0
    return u


def popup():
    try:
        default = open(os.path.join(ACCT_HOME, "default")).read().strip()
    except OSError:
        default = "1"
    bar = lambda p: "#" * max(0, min(10, round(p / 10))) + "." * (10 - max(0, min(10, round(p / 10))))
    print("\n  Claude accounts\n")
    for a in ACCOUNTS:
        u = live(a)
        note = "live"
        if isinstance(u, str):
            reason = u
            u, at = cached(a)
            note = f"{reason}; cached {int((time.time() - at) // 60)}m ago" if u else reason
        print(f"  c{a}{'  (default)' if a == default else ''}   {note}")
        if u:
            five_at = time.strftime("%H:%M", time.localtime(u["five_reset"])) if u["five_reset"] else "-"
            week_at = time.strftime("%a %H:%M", time.localtime(u["week_reset"])) if u["week_reset"] else "-"
            print(f"    5h  {bar(u['five'])} {u['five']:3.0f}%  resets {five_at}")
            print(f"    7d  {bar(u['week'])} {u['week']:3.0f}%  resets {week_at}")
        print()


if __name__ == "__main__":
    popup()
