"""squad board M3: what waits on the PO (ticket 05; architecture.md sections 1, 2, 6).

Route `GET /api/inbox` (goal= or scope=). Read-only: the only inbox call is `squad-inbox --home H list --json --no-write`
(plain `list` writes `seen` events). Parked questions are read with `squadinbox.parse_open_questions` (no second parser).

    data = {rows, count_choice, count_squad, others: [{scope, n}], banner: {entries|None, reason}, parked, status}
    row  = {id, title, age_s, blocks, options: [{key, text, recommended}], kind ("open" question | "answer" to read), scope}

Needs-you = open questions + items to read + ready-for-review branches + permission prompts. A question parked whole
(`From: E<n>`, Status: parked) is not counted and not a row; a point parked (`From: E<n> #<p>`) leaves the item in. The
banner comes from `squadboard_agents.banner` (herdr, one call per read). herdr unknown gives `banner.entries None` and
`unknown: ["herdr"]`, never `[]`. Ready-for-review branches come from ticket 07 (`squadboard_tasks.ready_by_scope(sel)`
-> {scope: n}) or `sel["ready_for_review"]`; with neither, `unknown` names "ready_for_review" and they count 0.
Cost: one CLI call per open scope/goal/squad folder that has an inbox file. Never raises.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

BIN = Path(__file__).resolve().parent
if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))
import squadboard_agents  # noqa: E402
import squadboard_tasks  # noqa: E402
import squadboard_time  # noqa: E402
import squadinbox  # noqa: E402

TIMEOUT_S = 10
VERSION = 1
SQUAD_INBOX = BIN / "squad-inbox"
REC_RE = re.compile(r"\(?([a-z])\)?(?![A-Za-z0-9])")


def argv(home):
    """The one inbox call. `--home` goes before `list` (architecture 2)."""
    return [sys.executable or "python3", str(SQUAD_INBOX), "--home", str(home), "list", "--json", "--no-write"]


def call(home):
    """-> (snapshot dict, None) or (None, reason). Version other than 1 is a reason, not a guess."""
    try:
        r = subprocess.run(argv(home), capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=TIMEOUT_S, stdin=subprocess.DEVNULL)
        if r.returncode != 0:
            return None, "squad-inbox exit %s" % r.returncode
        o = json.loads(r.stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None, "squad-inbox did not answer"
    if not isinstance(o, dict) or o.get("version") != VERSION or not isinstance(o.get("items"), list):
        return None, "squad-inbox version %r not understood" % (o.get("version") if isinstance(o, dict) else None)
    return o, None


def first_seen(home):
    """{item id: epoch of its first `seen`/`add` event}; empty when the log is unreadable."""
    try:
        events, _ = squadinbox.read_log(str(Path(home) / squadinbox.LOG))
    except Exception:
        return {}
    out = {}
    for e in events:
        if e.get("ev") in ("seen", "add") and e["id"] not in out:
            t = squadboard_time.parse_iso(e.get("ts"))
            if t is not None:
                out[e["id"]] = t
    return out


def parked_from(home):
    """-> set of item ids parked whole (`From: E<n>`) in this folder's open-questions.md; an unreadable file gives none."""
    try:
        text = (Path(home) / squadinbox.OQ_FILE).read_text(encoding="utf-8", errors="replace")
        entries, _ = squadinbox.parse_open_questions(text, str(home))
    except (OSError, ValueError):
        return set()
    return {e["from"].strip() for e in entries if e["status"] == "parked" and re.fullmatch(r"E[0-9]+", e["from"].strip())}


def parked_rows(sel, choice):
    """-> (rows, warnings, ok). Parked and resolved questions of the choice's folders and of the squad folder (a squad-level
    question shows under every choice). Row: {id, status parked|resolved, level squad|goal|scope, scope, text, from, blocks,
    parked_iso, resolved_iso, answer, file}. Unparked entries are open again and are not rows. A broken block is a warning."""
    rows, warns, ok, seen = [], [], True, set()
    squad = sel["squad"]
    homes = [(squad.name, squad.path, "squad")] + [(l, h, "goal" if sel.get("kind") == "goal" and str(h) == str(sel.get("home")) else "scope")
                                                   for l, h in choice]
    for label, home, level in homes:
        if str(home) in seen:
            continue
        seen.add(str(home))
        path = Path(home) / squadinbox.OQ_FILE
        if not path.exists():
            continue
        try:
            entries, w = squadinbox.parse_open_questions(path.read_text(encoding="utf-8", errors="replace"), str(path))
        except (OSError, ValueError):
            ok = False
            continue
        warns += w
        for e in entries:
            if e["status"] not in ("parked", "resolved"):
                continue
            rows.append({"id": e["id"], "status": e["status"], "level": level, "scope": label, "text": e["text"],
                         "from": e["from"], "blocks": e["blocks"], "parked_iso": e["parked"], "resolved_iso": e["resolved_ts"],
                         "answer": e["answer"], "file": str(path)})
    rows.sort(key=lambda r: (r["parked_iso"] or "9", r["id"]))
    return rows, warns, ok


def options_of(item):
    """[{key, text, recommended}], the text unmodified; the mark is data, the word is the page's."""
    rec = (item.get("recommendation") or "").strip().lower()
    m = REC_RE.match(rec)
    rec_key = m.group(1) if m else None
    return [{"key": o["key"], "text": o["text"], "recommended": o["key"] == rec_key}
            for o in (item.get("options") or [])]


def rows_of(home, label, snap, now):
    """-> (rows, parked ids that were open). Only state `open` waits on the PO."""
    parked = parked_from(home)
    seen = first_seen(home)
    rows, hidden = [], []
    for it in snap["items"]:
        if it.get("state") != "open":
            continue
        if it["id"] in parked:
            hidden.append({"id": it["id"], "scope": label})
            continue
        t = seen.get(it["id"])
        rows.append({"id": it["id"], "title": it.get("title") or "", "age_s": None if t is None else max(0, int(now - t)),
                     "blocks": it.get("blocks") or "", "options": options_of(it),
                     "kind": "open" if it.get("kind") == "answer" else "answer", "scope": label})
    rows.sort(key=lambda r: (r["age_s"] is None, -(r["age_s"] or 0)))  # oldest first, unknown age last
    return rows, hidden


def _homes(sel):
    """-> (choice [(label, folder)], all [(label, folder)] of the squad: open goals, open scopes, the squad folder)."""
    squad = sel["squad"]
    choice = squadboard_agents._homes(sel)
    allh = squadboard_agents._all_homes(squad)
    allh.append((squad.name, squad.path))
    seen = {str(h) for _, h in allh}
    for label, h in choice:  # a closed choice is read-only but still shown
        if str(h) not in seen:
            allh.append((label, h))
    return choice, allh


def _ready(sel):
    """-> ({scope: n}, ok). `sel["ready_for_review"]` is a test hook; else ticket 07's `ready_by_scope`."""
    fn = sel.get("ready_for_review") or squadboard_tasks.ready_by_scope
    try:
        return {k: int(v) for k, v in (fn(sel) or {}).items()}, True
    except Exception:
        return {}, False


def read(sel):
    try:
        choice, allh = _homes(sel)
        in_choice = {str(h) for _, h in choice}
        names = {l for l, _ in choice}
        unknown, rows, per_scope = [], [], {}
        for label, home in allh:
            if not any((Path(home) / f).exists() for f in (squadinbox.LOG, squadinbox.TABLE)):
                continue
            snap, why = call(home)
            if snap is None:
                if "inbox" not in unknown:
                    unknown.append("inbox")
                continue
            r, _hidden = rows_of(home, label, snap, sel.get("now") or 0)
            per_scope[label] = per_scope.get(label, 0) + len(r)
            if str(home) in in_choice:
                rows += r
        rows.sort(key=lambda r: (r["age_s"] is None, -(r["age_s"] or 0)))
        parked_n = sum(len(parked_from(h)) for _, h in allh)
        ready, ok_ready = _ready(sel)
        if not ok_ready:
            unknown.append("ready_for_review")
        for k, n in ready.items():
            per_scope[k] = per_scope.get(k, 0) + n
        b = squadboard_agents.banner(sel)
        entries = b["entries"]
        if entries is None:
            unknown.append("herdr")
        else:
            for e in entries:
                per_scope[e["scope"]] = per_scope.get(e["scope"], 0) + 1
        count_squad = sum(per_scope.values())
        count_choice = sum(n for k, n in per_scope.items() if k in names)
        others = [{"scope": k, "n": n} for k, n in sorted(per_scope.items()) if k not in names and n]
        prows, pwarn, pok = parked_rows(sel, choice)
        if not pok:
            unknown.append("open-questions")
        data = {"status": "unknown" if "inbox" in unknown else "ok", "rows": rows, "count_choice": count_choice,
                "count_squad": count_squad, "others": others,
                "banner": {"entries": entries, "reason": b.get("reason")}, "parked": parked_n,
                "parked_rows": prows, "parked_warnings": pwarn}
        return {"data": data, "quality": "unknown" if unknown else "exact", "unknown": unknown}
    except Exception:
        return {"data": None, "quality": "unknown", "unknown": ["inbox"]}


ROUTE = {"name": "inbox", "path": "/api/inbox", "read": read, "selection": True}
