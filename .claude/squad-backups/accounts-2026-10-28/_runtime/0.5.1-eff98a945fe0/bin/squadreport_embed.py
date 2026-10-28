"""squad-report embed: plugin assets, safe JSON for a <script> tag, one-file assembly, atomic write. Pure python."""
import json
import os
import re
import tempfile

PLACEHOLDER = re.compile(r"__(CSS|JS|DATA)__")
ASSET_FILES = ("template.html", "report.css", "report.js")


def assets_dir():
    """templates/report of the plugin this file sits in; never the squad."""
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "templates", "report")


def plugin_assets(root=None):
    """-> (template, css, js) text. `root` overrides the assets folder (tests only)."""
    base = root or assets_dir()
    out = []
    for name in ASSET_FILES:
        with open(os.path.join(base, name), encoding="utf-8", newline="") as f:
            out.append(f.read())
    return tuple(out)


def dumps(obj):
    """Canonical JSON: sorted keys, compact, UTF-8 text."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def json_for_script(obj):
    """JSON safe inside <script type=application/json>: < > & U+2028/9 and '://' are escaped inside strings."""
    s = dumps(obj)
    for ch, esc in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"), (" ", "\\u2028"), (" ", "\\u2029"),
                    ("://", ":\\u002f/")):
        s = s.replace(ch, esc)
    return s


def assemble(template, css, js, data):
    """One file: __CSS__ __JS__ __DATA__ replaced in a single pass (a value is never scanned again)."""
    vals = {"CSS": css, "JS": js, "DATA": json_for_script(data)}
    return PLACEHOLDER.sub(lambda m: vals[m.group(1)], template)


def atomic_write(path, text):
    """Write to a temp name in the same folder, then os.replace. UTF-8, LF."""
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", suffix=os.path.basename(path), dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
