"""The PO inbox store. The only place the log format, the id rules and the escalations projection live.

Read items are `add`/`read` events in <home>/inbox.jsonl; answer items are rows of <home>/escalations.md and reach
the log as `seen` snapshots, so a deleted row stays listable. State is folded from the log on every call, never stored.
Writes happen under flock on inbox.jsonl.lock. `gone`/`filled` events record when sync first noticed a row vanish or get
an Answer cell by hand, so their time is stable between calls.
"""
import hashlib
import json
import os
import re
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone

try:
    import fcntl
except ImportError:  # Windows: the lock is msvcrt.locking
    fcntl = None
IS_WINDOWS = os.name == "nt"

LOG, TABLE, LOCK = "inbox.jsonl", "escalations.md", "inbox.jsonl.lock"
EVENTS = {"add", "seen", "read", "answer", "withdraw", "delivered", "gone", "filled"}
ID_RE = re.compile(r"[ER][0-9]{1,6}")
TITLE_MAX = 80
BR_RE = re.compile(r"<br\s*/?>", re.I)
MARKER_RE = re.compile(r"(?<![^\s;])\(([a-z])\)")
# header of the first table -> key; the recommendation header is "Manager's recommendation"
COLUMNS = ("#", "date", "question", "options", "recommendation", "blocks", "answer")


class Refused(Exception):
    def __init__(self, msg, code=2):
        super().__init__(msg)
        self.code = code


def now():
    return os.environ.get("SQUAD_INBOX_NOW") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def home_of(args):
    home = args.home or os.environ.get("SCOPE_DIR") or os.environ.get("GOAL_DIR")
    if not home:
        raise Refused("no home: pass --home or set SCOPE_DIR / GOAL_DIR")
    return home


# --- escalations.md: the table reader (first_table, clean_cell) -----------------------------------------------------

def clean_cell(cell):
    return cell.replace("\\|", "|").replace("**", "").replace("`", "").strip()


def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace", newline="") as f:
            return f.read()
    except OSError:
        return ""


def table_lines(text):
    """[(line_no, stripped line)] of the first table's lines (header, separator, rows)."""
    out = []
    for no, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line.startswith("|"):
            if out:
                break
            continue
        out.append((no, line))
    return out


def raw_cell(cell):
    """The cell as typed, `\\|` unescaped and trimmed; `**` and backticks stay (an item's body keeps its markup)."""
    return cell.replace("\\|", "|").strip()


def split_row(line, clean=True):
    body = re.sub(r"^\||(?<!\\)\|$", "", line)
    return [(clean_cell if clean else raw_cell)(c) for c in re.split(r"(?<!\\)\|", body)]


def first_table(text, clean=True):
    """(header, rows): header lower-cased; rows are (line_no, cells). With clean, cells are stripped of `**` and backticks."""
    header, rows = None, []
    for no, line in table_lines(text):
        cells = split_row(line, clean)
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        if header is None:
            header = [c.lower() for c in cells]
        else:
            rows.append((no, cells))
    return header, rows


def column_map(header):
    m = {}
    for i, h in enumerate(header):
        name = "recommendation" if "recommend" in h else h
        if name in COLUMNS and name not in m:
            m[name] = i
    return m


def parse_options(raw):
    """`(a) x; (b) y` -> [{key, text}] when the markers a, b, ... come in order from the start; else None."""
    raw = (raw or "").strip()
    marks, expect = [], 0
    for m in MARKER_RE.finditer(raw):
        if m.group(1) == chr(97 + expect):
            marks.append(m)
            expect += 1
    if len(marks) < 2 or marks[0].start() != 0:
        return None
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(raw)
        text = raw[m.end():end].strip().rstrip(";").strip()
        if not text:
            return None
        out.append({"key": m.group(1), "text": text})
    return out


def row_key(date, question):
    return hashlib.sha1((date + "|" + question).encode("utf-8", "surrogateescape")).hexdigest()[:10]


def project_rows(text):
    """(rows, errors): rows are dicts of what the file says; a bad row goes to errors and never stops the rest."""
    header, raw_rows = first_table(text, clean=False)
    rows, errors = [], []
    if header is None:
        return rows, errors
    cm = column_map(header)
    if "question" not in cm:
        return rows, [{"file": TABLE, "row": 0, "message": "the first table has no Question column"}]
    for no, cells in raw_rows:
        if all(not c for c in cells):
            continue
        if len(cells) < len(header) and len(cells) > cm["question"]:  # a short row reaching the question is fine
            cells = cells + [""] * (len(header) - len(cells))
        if len(cells) != len(header):
            errors.append({"file": TABLE, "row": no, "message": "row has %d cells, header has %d" % (len(cells), len(header))})
            continue
        g = {k: cells[i] for k, i in cm.items()}
        if not g.get("#") and not g["question"]:
            continue
        if not g["question"]:
            errors.append({"file": TABLE, "row": no, "message": "row has no question"})
            continue
        g.update(row_no=no, key=row_key(g.get("date", ""), g["question"]))
        rows.append(g)
    return rows, errors


def title_of(question):
    return BR_RE.split(question.split("\n", 1)[0], 1)[0].strip()[:TITLE_MAX]


# --- the log ------------------------------------------------------------------------------------------------------

ID_RE = re.compile(r"[ER][0-9]{1,6}")


def read_log(path):
    """(events, errors): a malformed line goes to errors and is skipped."""
    events, errors = [], []
    for no, line in enumerate(read_text(path).split("\n"), 1):
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
            if not isinstance(ev, dict) or not isinstance(ev.get("ev"), str):
                raise ValueError("not an event object")
            if ev["ev"] == "add" and not all(isinstance(ev.get(k), str) and ev[k] for k in ("id", "title", "ts")):
                raise ValueError("add event lacks id, title or ts")
            if not isinstance(ev.get("id"), str) or not ID_RE.fullmatch(ev["id"]):
                raise ValueError("event has no valid id")
            if ev["ev"] not in EVENTS:
                raise ValueError("unknown event type %r" % ev["ev"])
            if ev["ev"] == "seen" and not (isinstance(ev.get("key"), str) and ev["key"]):
                raise ValueError("seen event has no key")
        except ValueError as e:
            errors.append({"file": LOG, "row": no, "message": "malformed line: %s" % e})
            continue
        events.append(ev)
    return events, errors


def append_events(path, events):
    """One O_APPEND write; a torn last line (no newline) is closed first so it cannot swallow ours."""
    data = "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events).encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_BINARY", 0), 0o644)
    try:
        if os.fstat(fd).st_size:
            with open(path, "rb") as f:
                f.seek(-1, os.SEEK_END)
                if f.read(1) != b"\n":
                    data = b"\n" + data
        os.write(fd, data)
    finally:
        os.close(fd)


@contextmanager
def locked(home):
    try:
        fd = os.open(os.path.join(home, LOCK), os.O_WRONLY | os.O_CREAT | getattr(os, "O_BINARY", 0), 0o644)
    except OSError as e:
        raise Refused("cannot open %s: %s" % (os.path.join(home, LOCK), e.strerror or e), 1)
    try:
        if fcntl is None:
            import msvcrt  # LK_LOCK retries for about 10 s, then raises OSError
            os.lseek(fd, 0, os.SEEK_SET)
            try:
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
            except OSError:
                raise Refused("the inbox is locked by another squad-inbox", 1)
            try:
                yield
            finally:
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
    finally:
        os.close(fd)


def ids_in(events):
    return {e["id"] for e in events if e.get("ev") in ("add", "seen") and isinstance(e.get("id"), str)}


def next_number(used, prefix, extra=()):
    nums = [int(i[1:]) for i in used if i[0] == prefix and i[1:].isdigit()] + [int(x) for x in extra]
    return max(nums, default=0) + 1


def num(cell):
    return int(cell) if re.fullmatch(r"[0-9]{1,6}", cell or "") else None


def sync_events(events, rows, ts):
    """Events the log lacks: `seen` for a new row, `gone` for a vanished open row, `filled` for a hand-answered one."""
    out, known = [], {e["key"]: e["id"] for e in events if e.get("ev") == "seen" and "key" in e}
    used = ids_in(events)
    file_nums = [n for n in (num(r.get("#")) for r in rows) if n]
    present = set()
    for r in rows:
        if r["key"] in known:
            present.add(r["key"])
            continue
        if r["key"] in present:  # a second row with the same date and question is the same item
            continue
        present.add(r["key"])
        n = num(r.get("#"))
        if not n or "E%d" % n in used:
            n = next_number(used, "E", file_nums)
            file_nums.append(n)
        eid = "E%d" % n
        used.add(eid)
        known[r["key"]] = eid
        out.append({"ev": "seen", "id": eid, "ts": ts, "key": r["key"], "title": title_of(r["question"]),
                    "body": r["question"], "options": r.get("options", ""), "rec": r.get("recommendation", ""),
                    "blocks": r.get("blocks", ""), "date": r.get("date", ""), "row_no": r["row_no"]})
    done, filled, gone = fold_marks(events)
    cells = {r["key"]: r for r in rows}
    for key, eid in known.items():
        row = cells.get(key)
        if row is None and eid not in done and eid not in gone:
            out.append({"ev": "gone", "id": eid, "ts": ts})
        elif row is not None and row.get("answer") and eid not in done and eid not in filled:
            out.append({"ev": "filled", "id": eid, "ts": ts})
    return out


def fold_marks(events):
    done = {e["id"] for e in events if e.get("ev") in ("answer", "withdraw")}
    filled = {e["id"] for e in events if e.get("ev") == "filled"}
    gone = {e["id"] for e in events if e.get("ev") == "gone"}
    return done, filled, gone


# --- folding to the contract --------------------------------------------------------------------------------------

def clean_blocks(text):
    """'nothing' and '-' mean the item blocks nothing."""
    text = (text or "").strip()
    return "" if text.lower() in ("nothing", "-") else text


def raw_options(cell):
    """The Options cell when it has text that is not in the `(a) x; (b) y` format, else None."""
    cell = (cell or "").strip()
    return cell if cell and parse_options(cell) is None else None


def iso_day(date):
    return date + "T00:00:00Z" if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date or "") else None


def fold(events, rows, ts):
    """Items of the version-1 contract, in order, from the log and the rows now in the file."""
    by_key = {r["key"]: r for r in rows}
    items = {}
    for e in events:
        ev, eid = e["ev"], e.get("id")
        if ev == "add":
            items[eid] = {"id": eid, "kind": "read", "state": "open", "title": e.get("title", ""), "body": e.get("body", ""),
                          "options": None, "options_raw": None, "recommendation": None, "blocks": clean_blocks(e.get("blocks")),
                          "created": e.get("ts"), "created_precision": "second", "answer": None, "done": None, "flags": []}
        elif ev == "seen":
            row = by_key.get(e.get("key"))
            items[eid] = {"id": eid, "kind": "answer", "state": "open", "title": e.get("title", ""), "body": e.get("body", ""),
                          "options": parse_options(e.get("options")), "options_raw": raw_options(e.get("options")),
                          "recommendation": e.get("rec") or None, "blocks": clean_blocks(e.get("blocks")), "created": iso_day(e.get("date")) or e.get("ts"),
                          "created_precision": "day" if iso_day(e.get("date")) else "second", "answer": None,
                          "done": None, "flags": [], "_row": row}
    for e in events:
        it = items.get(e.get("id"))
        if it is None:
            continue
        ev = e["ev"]
        if it["done"] and ev != "delivered":
            continue
        if ev == "read" and it["kind"] == "read":
            it["state"], it["done"] = "done", {"kind": "read", "ts": e.get("ts"), "reason": None}
        elif ev == "answer" and it["kind"] == "answer":
            it["answer"] = {"text": e.get("text"), "option": e.get("option"), "note": e.get("note"), "ts": e.get("ts"),
                            "source": e.get("source"), "delivered_ts": None}
            if e.get("source") == "chat":
                it["answer"]["delivered_ts"] = e.get("ts")
                it["state"], it["done"] = "done", {"kind": "answered", "ts": e.get("ts"), "reason": None}
            else:
                it["state"] = "answered-waiting"
        elif ev == "delivered" and it["answer"] and not it["answer"]["delivered_ts"]:
            it["answer"]["delivered_ts"] = e.get("ts")
            it["state"], it["done"] = "done", {"kind": "answered", "ts": e.get("ts"), "reason": None}
        elif ev == "withdraw" and it["state"] == "open":
            it["state"], it["done"] = "done", {"kind": "withdrawn", "ts": e.get("ts"), "reason": e.get("reason")}
    marks = {}
    for e in events:
        if e["ev"] in ("gone", "filled"):
            marks.setdefault((e.get("id"), e["ev"]), e.get("ts"))
    for it in items.values():
        row = it.pop("_row", None)
        if it["kind"] != "answer":
            continue
        if row is not None:  # the file is the truth while the row exists; the `seen` snapshot is for a removed row
            it.update(title=title_of(row["question"]), body=row["question"], options=parse_options(row.get("options")),
                      options_raw=raw_options(row.get("options")), recommendation=row.get("recommendation") or None, blocks=clean_blocks(row.get("blocks")))
        if row is None:
            it["flags"].append("row-removed")
        elif it["answer"] and not row.get("answer"):
            it["flags"].append("cell-not-written")
        if it["state"] != "open":
            continue
        if row is None:
            it["state"], it["done"] = "done", {"kind": "removed", "ts": marks.get((it["id"], "gone"), ts), "reason": None}
        elif row.get("answer"):
            it["state"] = "done"
            it["done"] = {"kind": "answered-file", "ts": marks.get((it["id"], "filled"), ts), "reason": row["answer"]}
            it["flags"].append("answer-by-hand")
    return order(list(items.values()))


def order(items):
    def number(it):
        return int(it["id"][1:])

    def oldest(it):
        return (it["created"] or "", it["kind"], number(it))

    def newest_first(key):
        return tuple(-ord(c) for c in key)

    opened = sorted((i for i in items if i["state"] == "open"), key=lambda i: (not i["blocks"].strip(),) + oldest(i))
    waiting = sorted((i for i in items if i["state"] == "answered-waiting"), key=lambda i: (i["answer"]["ts"] or "", number(i)))
    done = sorted((i for i in items if i["state"] == "done"), key=lambda i: (newest_first(i["done"]["ts"] or ""), i["id"]))
    return opened + waiting + done


def find_repairs(events, rows):
    """[(key, text)]: rows whose item has an `answer` event but an empty Answer cell (a crash between event and cell)."""
    keys = {e["id"]: e.get("key") for e in events if e["ev"] == "seen"}
    cells = {r["key"]: r for r in rows}
    out, seen_ids = [], set()
    for e in events:
        if e["ev"] not in ("answer", "withdraw") or e.get("id") in seen_ids:
            continue
        seen_ids.add(e.get("id"))
        text = e.get("text") if e["ev"] == "answer" else "withdrawn: %s" % e.get("reason")
        row = cells.get(keys.get(e.get("id")))
        if row is not None and not row.get("answer") and isinstance(text, str) and text.strip():
            out.append((row["key"], text))
    return out


def snapshot(home, write):
    """The contract dict for a home; with write, missing sync events are appended and empty Answer cells repaired
    (under the lock). Without write nothing changes on disk and the result is the same as if it had."""
    log_path, table_path = os.path.join(home, LOG), os.path.join(home, TABLE)
    ts = now()

    def load():
        events, errors = read_log(log_path)
        rows, row_errors = project_rows(read_text(table_path))
        return events, rows, errors + row_errors

    events, rows, errors = load()
    pending = sync_events(events, rows, ts)
    if write and (pending or find_repairs(events, rows)):
        with locked(home):
            events, rows, errors = load()
            pending = sync_events(events, rows, ts)
            if pending:
                append_events(log_path, pending)
            for key, text in find_repairs(events, rows):
                try:
                    set_answer_cell(home, key, text)
                except (Refused, OSError) as e:
                    print("squad-inbox: could not repair the Answer cell: %s" % e, file=sys.stderr)
        events, rows, errors = load()
        pending = []
    events = events + pending  # --no-write: fold as if synced, write nothing
    items = fold(events, rows, ts)
    counts = {"answer_open": sum(1 for i in items if i["kind"] == "answer" and i["state"] == "open"),
              "read_open": sum(1 for i in items if i["kind"] == "read" and i["state"] == "open"),
              "waiting": sum(1 for i in items if i["state"] == "answered-waiting")}
    return {"version": 1, "home": home, "now": ts, "counts": counts, "items": items, "errors": errors}


# --- writing escalations.md (bytes in, bytes out: invalid UTF-8, line endings and a missing final newline survive) --------

BREAK_RE = re.compile("\r\n|[\n\r\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029]")  # what str.splitlines() splits on


def cell_text(s):
    return BREAK_RE.sub("<br>", s.replace("|", "\\|"))


def read_raw(path):
    if os.path.islink(path):
        raise Refused("%s is a symlink: refusing to write through it" % TABLE, 1)
    with open(path, "rb") as f:
        return f.read().decode("utf-8", "surrogateescape")


def add_row(home, title, body, options, rec, blocks):
    """Insert one row at the top of the table body; every other byte of the file stays."""
    path = os.path.join(home, TABLE)
    raw = read_raw(path) if os.path.lexists(path) else ""
    lines = raw.splitlines(keepends=True)
    tl = table_lines(raw)
    if len(tl) < 2:
        raise Refused("%s has no table to add a row to" % TABLE)
    header, rows = first_table(raw)
    cm = column_map(header)
    if "question" not in cm:
        raise Refused("%s: the table has no Question column" % TABLE)
    sep_no = tl[1][0]
    numbers = [n for n in (num(c[cm["#"]]) for _, c in rows if "#" in cm) if n]
    events, _ = read_log(os.path.join(home, LOG))
    n = next_number(ids_in(events), "E", numbers)
    values = {"#": str(n), "date": now()[:10], "question": title + "\n" + body, "options": options or "",
              "recommendation": rec or "", "blocks": blocks or "", "answer": ""}
    at = {i: k for k, i in cm.items()}
    cells = [cell_text(values[at[c]]) if c in at else "" for c in range(len(header))]
    sep = lines[sep_no - 1]
    eol = sep[len(sep.rstrip("\r\n\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029")):]
    row = "| " + " | ".join(c if c else "" for c in cells) + " |"
    if eol:
        lines.insert(sep_no, row + eol)
    else:  # the separator was the last line, without a newline: the new last line keeps that
        eol = "\r\n" if "\r\n" in raw else "\n"
        lines[sep_no - 1] = sep + eol
        lines.append(row)
    text = "".join(lines)
    all_rows = project_rows(text)[0]
    mine = [r for r in all_rows if r.get("#") == str(n)]
    twins = [r for r in all_rows if mine and r["key"] == mine[0]["key"] and r is not mine[0]]
    if twins:
        known = {e["key"]: e["id"] for e in events if e.get("ev") == "seen" and "key" in e}
        was = known.get(twins[0]["key"]) or "E%s" % twins[0].get("#")
        raise Refused("the same title and body was already added today as %s" % was, 3)
    atomic_write(path, text)
    return "E%d" % n


def set_answer_cell(home, key, text):
    """Replace only the Answer cell of the row with this key. Refuses (exit 1) rather than guess."""
    path = os.path.join(home, TABLE)
    raw = read_raw(path)
    header, rows = first_table(raw, clean=False)
    if header is None or "answer" not in column_map(header):
        raise Refused("%s has no Answer column" % TABLE, 1)
    idx = column_map(header)["answer"]
    hits = [(no, cells) for no, cells in rows if row_key_of(header, cells) == key]
    if len(hits) != 1:
        raise Refused("cannot write the Answer cell: %d rows match" % len(hits) + (
            " (lines %s)" % ", ".join(str(no) for no, _ in hits) if hits else ""), 1)
    no, cells = hits[0]
    if len(cells) > len(header):
        raise Refused("row on line %d has %d cells, header has %d" % (no, len(cells), len(header)), 1)
    lines = raw.splitlines(keepends=True)
    line = lines[no - 1]
    content = line.rstrip("\r\n\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029")
    tail = line[len(content):]
    stripped = content.rstrip()
    if len(cells) < len(header):  # a short row: pad it to the header width so the Answer cell exists
        if not re.search(r"(?<!\\)\|$", stripped):
            stripped += " |"
        stripped += " |" * (len(header) - len(cells))
        content = stripped
    pipes = [m.start() for m in re.finditer(r"(?<!\\)\|", stripped)]
    start = pipes[idx] + 1  # cell k sits after pipe k; pipe 0 opens the row
    end = pipes[idx + 1] if idx + 1 < len(pipes) else len(stripped)
    new = stripped[:start] + " " + cell_text(text) + " " + ("|" if end == len(stripped) and idx + 1 >= len(pipes) else "") + stripped[end:] + content[len(stripped):] + tail
    lines[no - 1] = new
    atomic_write(path, "".join(lines))


def row_key_of(header, cells):
    g = dict(zip(header, cells))
    return row_key(g.get("date", ""), g.get("question", ""))


def atomic_write(path, text):
    folder = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".escalations-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(text.encode("utf-8", "surrogateescape"))
        try:
            os.chmod(tmp, os.stat(path).st_mode & 0o777)
        except OSError:
            pass
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


# --- commands -----------------------------------------------------------------------------------------------------

def require_manager():
    if os.environ.get("SQUAD_ROLE") != "manager":
        raise Refused("only the Manager writes inbox items (SQUAD_ROLE is not manager)")


MAX_BODY = 64 * 1024
TITLE_CTRL_RE = re.compile("[\x00-\x1f\x7f-\x9f\u2028\u2029]+")


def read_body(path):
    """The body from --body-file or a non-terminal stdin; a terminal is an empty body, never a wait."""
    try:
        if path:
            with open(path, "rb") as f:
                data = f.read(MAX_BODY + 1)
        elif sys.stdin is None or sys.stdin.isatty():
            return ""
        else:
            data = sys.stdin.buffer.read(MAX_BODY + 1)
    except OSError as e:
        raise Refused("cannot read the body: %s" % e)
    if len(data) > MAX_BODY:
        raise Refused("the body is over %d KiB" % (MAX_BODY // 1024))
    text = decode_utf8(data, "--body-file" if path else "the body on stdin")
    return text.replace("\r\n", "\n").replace("\r", "\n")  # a Windows file or pipe has CRLF


def cmd_add(home, args):
    require_manager()
    if args.kind not in ("read", "answer"):
        raise Refused("kind must be read or answer, not %r" % args.kind)
    title = TITLE_CTRL_RE.sub(" ", args.title or "").strip()
    if not title:
        raise Refused("an item needs a --title")
    body = read_body(args.body_file)
    if not body.strip():
        raise Refused("an item needs a body (--body-file or stdin)")
    body = body.rstrip("\n")
    if args.kind == "read":
        if args.options or args.rec:
            raise Refused("--options and --rec are for answer items")
    elif args.options and parse_options(args.options) is None:
        raise Refused("--options must read '(a) text; (b) text' with at least two choices")
    if not os.path.isdir(home):
        raise Refused("home %s is not a folder" % home)
    with locked(home):
        if args.kind == "answer":
            add_row(home, title, body, args.options, args.rec, args.blocks)
        else:
            events, _ = read_log(os.path.join(home, LOG))
            eid = "R%d" % next_number(ids_in(events), "R")
            append_events(os.path.join(home, LOG), [{"ev": "add", "id": eid, "ts": now(), "title": title, "body": body,
                                                    "blocks": (args.blocks or "").strip()}])
    print("1 new item in the inbox: %s" % title)
    return 0


def cmd_list(home, args):
    if not os.path.isdir(home):
        raise Refused("home %s is not a folder" % home)
    snap = snapshot(home, write=not args.no_write)
    if args.open:
        snap["items"] = [i for i in snap["items"] if i["state"] != "done"]
    if args.json:
        print(json.dumps(snap, ensure_ascii=False, indent=2))
        return 0
    c = snap["counts"]
    print("%d to answer, %d to read, %d waiting" % (c["answer_open"], c["read_open"], c["waiting"]))
    for i in snap["items"]:
        print("%s [%s] %s" % (i["id"], i["done"]["kind"] if i["done"] else i["state"], i["title"]))
    for e in snap["errors"]:
        print("error: %s row %s: %s" % (e["file"], e["row"], e["message"]))
    return 0


def check_id(raw):
    if not ID_RE.fullmatch(raw or ""):
        raise Refused("bad id %r: expected E<n> or R<n>" % raw)
    return raw


def cmd_read(home, args):
    eid = check_id(args.id)
    if eid[0] != "R":
        raise Refused("only read items (R<n>) are marked read")
    if not os.path.isdir(home):
        raise Refused("home %s is not a folder" % home)
    with locked(home):
        snap = snapshot(home, write=False)
        item = next((i for i in snap["items"] if i["id"] == eid), None)
        if item is None:
            raise Refused("no item %s" % eid)
        if item["state"] != "open":
            raise Refused("%s is already handled (%s at %s)" % (eid, item["done"]["kind"], item["done"]["ts"]), 3)
        append_events(os.path.join(home, LOG), [{"ev": "read", "id": eid, "ts": now()}])
    return 0


def stdin_text(only_if_ready):
    """Piped stdin as text. A terminal is empty; with only_if_ready an open pipe nobody wrote to is empty too, never a wait."""
    try:
        if sys.stdin is None or sys.stdin.isatty():
            return ""
        if only_if_ready:
            if IS_WINDOWS:
                return ""  # select() fails on a Windows pipe, and --note/--text is already given
            import select
            if not select.select([sys.stdin], [], [], 0)[0]:
                return ""
        data = sys.stdin.buffer.read(MAX_BODY + 1)
    except (OSError, ValueError):
        return ""
    if len(data) > MAX_BODY:
        raise Refused("the answer is over %d KiB" % (MAX_BODY // 1024))
    return decode_utf8(data, "the text on stdin")


def prepare(home, eid):
    """Under the lock: bring the log up to date with the file, then the item `eid` and its row key."""
    if not os.path.isdir(home):
        raise Refused("home %s is not a folder" % home)
    log_path = os.path.join(home, LOG)
    events, _ = read_log(log_path)
    rows, _ = project_rows(read_text(os.path.join(home, TABLE)))
    pending = sync_events(events, rows, now())
    if pending:
        append_events(log_path, pending)
        events += pending
    item = next((i for i in fold(events, rows, now()) if i["id"] == eid), None)
    if item is None:
        raise Refused("no item %s" % eid)
    key = next((e.get("key") for e in events if e["ev"] == "seen" and e.get("id") == eid), None)
    return item, key


def winner(item):
    """Who handled the item first, for an exit-3 message."""
    a, d = item["answer"], item["done"]
    if a:
        return "answered at %s (%s)" % (a["ts"], a["source"])
    if d and d["kind"] == "withdrawn":
        return "withdrawn at %s: %s" % (d["ts"], d["reason"])
    if d and d["kind"] == "answered-file":
        return "answered in the file, not through the inbox (%s)" % d["reason"]
    if d:
        return "already handled (%s at %s)" % (d["kind"], d["ts"])
    return "already handled"


def write_cell(home, key, text):
    """After the event: the cell. A failure is a warning, the answer is in the log and `list` fills the cell later."""
    try:
        if key is None:
            raise Refused("the item has no row")
        set_answer_cell(home, key, text)
    except (Refused, OSError) as e:
        print("squad-inbox: recorded, but the Answer cell was not written: %s" % e, file=sys.stderr)


def cmd_answer(home, args):
    require_manager()
    eid = check_id(args.id)
    if eid[0] != "E":
        raise Refused("only answer items (E<n>) take an answer")
    given = args.note if args.note is not None else args.text
    piped = stdin_text(only_if_ready=given is not None)
    if given is not None and piped:
        raise Refused("give the answer with --note/--text or on stdin, not both")
    body = given if given is not None else piped
    if args.option is None:
        if not body.strip():
            raise Refused("an empty answer is not recorded")
    elif args.text is not None:
        raise Refused("with --option the words are a --note, not --text")
    with locked(home):
        item, key = prepare(home, eid)
        if item["kind"] != "answer":
            raise Refused("%s is not an answer item" % eid)
        if item["state"] != "open" and not (item["done"] and item["done"]["kind"] == "removed" and not item["answer"]):
            raise Refused("%s is %s" % (eid, winner(item)), 3)
        if args.option is None:
            text, option, note = body, None, None
        else:
            if item["options"] is None:
                raise Refused("%s has no options to pick from" % eid)
            hit = next((o for o in item["options"] if o["key"] == args.option), None)
            if hit is None:
                raise Refused("%s has no option %r (it has %s)" % (eid, args.option, ", ".join(o["key"] for o in item["options"])))
            note = body if body.strip() else None
            text, option = "(%s) %s" % (hit["key"], hit["text"]) + ("\n" + note if note else ""), hit["key"]
        append_events(os.path.join(home, LOG), [{"ev": "answer", "id": eid, "ts": now(), "text": text, "option": option,
                                                "note": note, "source": args.source}])
        write_cell(home, key, text)
    return 0


def cmd_withdraw(home, args):
    require_manager()
    eid = check_id(args.id)
    reason = (args.reason or "").strip()
    if not reason:
        raise Refused("a withdrawal needs a --reason")
    with locked(home):
        item, key = prepare(home, eid)
        if item["state"] != "open":
            raise Refused("%s is %s" % (eid, winner(item)), 3)
        append_events(os.path.join(home, LOG), [{"ev": "withdraw", "id": eid, "ts": now(), "reason": reason}])
        if eid[0] == "E":
            write_cell(home, key, "withdrawn: %s" % reason)
    return 0


def cmd_delivered(home, args):
    require_manager()
    eid = check_id(args.id)
    if eid[0] != "E":
        raise Refused("only answers (E<n>) are delivered")
    with locked(home):
        item, _ = prepare(home, eid)
        a = item["answer"]
        if a is None:
            raise Refused("%s has no answer to deliver (%s)" % (eid, item["state"]), 3)
        if a["delivered_ts"]:
            raise Refused("%s was already delivered at %s" % (eid, a["delivered_ts"]), 3)
        append_events(os.path.join(home, LOG), [{"ev": "delivered", "id": eid, "ts": now(), "session": args.session or ""}])
    return 0


def check_utf8(args):
    """An argument holding a lone surrogate is bad input, not a traceback. A non-UTF-8 locale (cp1252, C)
    smuggles valid UTF-8 argv bytes as surrogates: those are decoded back, the rest is refused."""
    for name, value in vars(args).items():
        if isinstance(value, str):
            try:
                value.encode("utf-8")
            except UnicodeEncodeError:
                try:
                    setattr(args, name, value.encode("utf-8", "surrogateescape").decode("utf-8"))
                except UnicodeError:
                    raise Refused("--%s is not valid UTF-8" % name.replace("_", "-"))


def decode_utf8(data, what):
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise Refused("%s is not valid UTF-8" % what)


def run(args):
    check_utf8(args)
    home = home_of(args)
    return {"add": cmd_add, "list": cmd_list, "read": cmd_read, "answer": cmd_answer, "withdraw": cmd_withdraw,
            "delivered": cmd_delivered}[args.cmd](home, args)
