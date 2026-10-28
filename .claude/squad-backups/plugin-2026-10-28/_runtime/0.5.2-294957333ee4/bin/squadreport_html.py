"""squad-report HTML: one self-contained report.html for a scope. Pure python, no network."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import squadreport_embed as emb  # noqa: E402


def render(data, root=None):
    """The report.html text for `data` (the dict that is written as data.json)."""
    template, css, js = emb.plugin_assets(root)
    return emb.assemble(template, css, js, data)


def render_scope(data, out_dir):
    """Write <out_dir>/report.html atomically; returns its path."""
    path = os.path.join(str(out_dir), "report.html")
    emb.atomic_write(path, render(data))
    return path
