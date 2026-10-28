#!/usr/bin/env bash
# Herdr popup (prefix+u): both accounts' usage, fetched live from Anthropic's usage
# endpoint (what /usage shows) with each account's own login token. Falls back to the
# status-line cache (record-usage.sh) when a token has expired or the request fails.
H="$HOME/.claude-accounts"
default=$(cat "$H/default" 2>/dev/null || echo 1)
python3 -I - "$H" "$default" "$HOME/.claude" "$HOME/.claude-2" "$HOME/.claude-3" <<'PY'
import json, sys, time, urllib.request
from datetime import datetime
home, default, *dirs = sys.argv[1:]
now = time.time()

def live(cfg):
    """(five_pct, five_reset_epoch, week_pct, week_reset_epoch), or a reason string."""
    try:
        c = json.load(open(f"{cfg}/.credentials.json"))["claudeAiOauth"]
    except (OSError, KeyError, ValueError):
        return "not logged in"
    # Refreshing here could rotate the token out from under Claude Code's own login.
    if c.get("expiresAt", 0) / 1000 < now:
        return "token expired - run it once to refresh"
    req = urllib.request.Request("https://api.anthropic.com/api/oauth/usage", headers={
        "Authorization": "Bearer " + c["accessToken"], "anthropic-beta": "oauth-2025-04-20"})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=8).read())
    except Exception as e:
        return f"request failed ({e})"
    ts = lambda s: datetime.fromisoformat(s).timestamp() if s else 0
    return (d["five_hour"]["utilization"], ts(d["five_hour"]["resets_at"]),
            d["seven_day"]["utilization"], ts(d["seven_day"]["resets_at"]))

def cached(a):
    try:
        f5, r5, f7, r7, at = open(f"{home}/usage-{a}").read().split()
        return (float(f5), float(r5), float(f7), float(r7)), float(at)
    except (OSError, ValueError):
        return None, None

def bar(p):
    n = max(0, min(10, round(p / 10)))
    return "#" * n + "." * (10 - n)

print("\n  Claude accounts\n")
for a, cfg in zip(("1", "2", "3"), dirs):
    tag = "  (default)" if a == default else ""
    u = live(cfg)
    if isinstance(u, tuple):
        note = "live"
    else:
        reason = u
        u, at = cached(a)
        note = f"{reason}; cached {int((now - at) // 60)}m ago" if u else reason
    print(f"  c{a}{tag}   {note}")
    if u:
        f5, r5, f7, r7 = u
        print(f"    5h  {bar(f5)} {f5:3.0f}%  resets {time.strftime('%H:%M', time.localtime(r5)) if r5 else '-'}")
        print(f"    7d  {bar(f7)} {f7:3.0f}%  resets {time.strftime('%a %H:%M', time.localtime(r7)) if r7 else '-'}")
    print()
PY
printf '  press any key to close'
read -rsn1
