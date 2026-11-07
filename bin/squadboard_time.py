"""squad board: ISO 8601 string -> epoch seconds. Offset aware, stdlib only.

parse_iso(s) returns a float, or None (unknown) for anything it cannot read. Never raises.
A string with no offset is read as UTC.
"""
from datetime import datetime, timezone


def parse_iso(s):
    if not isinstance(s, str) or not s.strip():
        return None
    s = s.strip()
    if s[-1] in "zZ":
        s = s[:-1] + "+00:00"
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    try:
        return d.timestamp()
    except (OverflowError, OSError, ValueError):
        return None
