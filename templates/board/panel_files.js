/* Files panel (ticket 14; design-v5.md "Files"). Rows come from /api/files (bin/squadboard_files.py).
   Cut this panel: delete this file and its <script> line. Pure rules on BOARD: rowsForFiles, mdBlocks; renderMd builds DOM.
   A click opens the file through the existing /api/file route in a new tab: HTML is served sandboxed by the server; a markdown
   file is fetched and drawn here as headings, lists and tables (no raw # marks). Every text reaches the DOM through textContent. */
(function (root) {
  "use strict";
  var BOARD = root.BOARD = root.BOARD || {};

  /* ---------- pure rules ---------- */
  var GROUP = { report: "report", data: "report", evidence: "evidence" };   /* every other kind is an "artifact" */
  function groupOf(kind) { return GROUP[kind] || "artifact"; }
  var FILTERS = [["all", "All"], ["artifact", "Artifacts"], ["report", "Reports"], ["evidence", "Evidences"]];
  /* rowsForFiles(data, filter): {rows, total, missing (text or null), truncated}. The report row is missing in a live scope. */
  function rowsForFiles(data, filter) {
    var d = data || {}, all = d.rows || [], f = filter || "all";
    var rows = all.filter(function (r) { return f === "all" || groupOf(r.kind) === f; }).map(function (r) {
      return { name: r.name, path: r.path, kind: groupOf(r.kind), what: r.what, scope: r.scope, mtime: r.mtime,
               iso: typeof r.mtime === "number" ? new Date(r.mtime * 1000).toISOString() : null, md: /\.md$/i.test(r.path || "") };
    });
    var missing = d.report_expected && !d.report && !d.closed && (f === "all" || f === "report") ? "no report yet (made at close)" : null;
    return { rows: rows, total: all.length, missing: missing, truncated: !!d.truncated };
  }
  BOARD.rowsForFiles = rowsForFiles;

  /* fileTime(iso, nowMs, tz): "08:00" for a file changed today in the zone, "Oct 20 08:00" for an older day. Uses BOARD.fmtDate/fmtTime. */
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  function fileTime(iso, nowMs, tz) {
    var hm = BOARD.fmtTime(iso, tz), day = BOARD.fmtDate(iso, tz);
    if (day === "unknown" || day === BOARD.fmtDate(new Date(nowMs).toISOString(), tz)) return hm;
    var m = /^\d{4}-(\d\d)-(\d\d)$/.exec(day);
    return m ? MONTHS[+m[1] - 1] + " " + (+m[2]) + " " + hm : day + " " + hm;
  }
  BOARD.fileTime = fileTime;

  /* mdBlocks(text) -> [{t: "h", l, s} | {t: "li", s} | {t: "p", s} | {t: "code", s} | {t: "table", rows: [[cell]], head}] */
  function mdBlocks(text) {
    var lines = String(text == null ? "" : text).replace(/\r\n?/g, "\n").split("\n"), out = [], i = 0, para = [];
    function flush() { if (para.length) { out.push({ t: "p", s: para.join(" ") }); para = []; } }
    while (i < lines.length) {
      var ln = lines[i], m;
      if (/^\s*```/.test(ln)) {
        flush(); var buf = []; i++;
        while (i < lines.length && !/^\s*```/.test(lines[i])) buf.push(lines[i++]);
        i++; out.push({ t: "code", s: buf.join("\n") }); continue;
      }
      if ((m = /^(#{1,6})\s+(.*)$/.exec(ln))) { flush(); out.push({ t: "h", l: m[1].length, s: m[2].replace(/\s+#+\s*$/, "") }); i++; continue; }
      if (/^\s*\|.*\|\s*$/.test(ln)) {
        flush(); var rows = [];
        while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) {
          var cells = lines[i].trim().replace(/^\||\|$/g, "").split("|").map(function (c) { return c.trim(); });
          if (!cells.every(function (c) { return /^:?-{2,}:?$/.test(c); })) rows.push(cells);
          i++;
        }
        out.push({ t: "table", rows: rows }); continue;
      }
      if ((m = /^\s*(?:[-*+]|\d+[.)])\s+(.*)$/.exec(ln))) { flush(); out.push({ t: "li", s: m[1] }); i++; continue; }
      if (/^\s*$/.test(ln)) { flush(); i++; continue; }
      para.push(ln.trim()); i++;
    }
    flush();
    return out;
  }
  BOARD.mdBlocks = mdBlocks;

  /* inline(text) -> [{t: "text"|"b"|"code", s}] for **bold** and `code`; everything else is plain text. */
  function inline(s) {
    var out = [], re = /(\*\*[^*]+\*\*|`[^`]+`)/g, last = 0, m;
    s = String(s);
    while ((m = re.exec(s))) {
      if (m.index > last) out.push({ t: "text", s: s.slice(last, m.index) });
      var tok = m[1];
      out.push(tok[0] === "`" ? { t: "code", s: tok.slice(1, -1) } : { t: "b", s: tok.slice(2, -2) });
      last = m.index + tok.length;
    }
    if (last < s.length) out.push({ t: "text", s: s.slice(last) });
    return out;
  }
  BOARD.mdInline = inline;

  /* renderMd(doc, host, text): draws the markdown into `host` with createElement/textContent only. */
  function renderMd(doc, host, text) {
    function mk(tag, s) { var e = doc.createElement(tag); if (s != null) e.textContent = s; return e; }
    function fill(e, s) {
      inline(s).forEach(function (p) { e.appendChild(p.t === "text" ? doc.createTextNode(p.s) : mk(p.t === "b" ? "strong" : "code", p.s)); });
      return e;
    }
    var ul = null;
    mdBlocks(text).forEach(function (b) {
      if (b.t !== "li") ul = null;
      if (b.t === "h") host.appendChild(fill(mk("h" + Math.min(6, b.l)), b.s));
      else if (b.t === "p") host.appendChild(fill(mk("p"), b.s));
      else if (b.t === "code") host.appendChild(mk("pre", b.s));
      else if (b.t === "li") { if (!ul) { ul = mk("ul"); host.appendChild(ul); } ul.appendChild(fill(mk("li"), b.s)); }
      else if (b.t === "table") {
        var tb = mk("table");
        b.rows.forEach(function (r, ri) {
          var tr = mk("tr");
          r.forEach(function (c) { tr.appendChild(fill(mk(ri === 0 ? "th" : "td"), c)); });
          tb.appendChild(tr);
        });
        host.appendChild(tb);
      }
    });
    return host;
  }
  BOARD.renderMd = renderMd;

  /* The new window cannot see the board's tokens, so it uses system colours and translucent greys only. */
  var MD_CSS = "body{font:15px/1.5 system-ui,sans-serif;max-width:60em;margin:1.5em auto;padding:0 1em}" +
    "pre,code{font-family:ui-monospace,Menlo,Consolas,monospace}pre{background:rgba(0,0,0,.06);padding:.6em;overflow:auto}" +
    "table{border-collapse:collapse}th,td{border:1px solid rgba(0,0,0,.25);padding:2px 8px;text-align:left}.bar{color:GrayText;font-size:.85em}";

  /* openMarkdown(win, name, text): draws a markdown file into a freshly opened window. */
  function openMarkdown(win, name, text) {
    var doc = win.document;
    doc.title = name;
    var st = doc.createElement("style"); st.textContent = MD_CSS; doc.head.appendChild(st);
    var bar = doc.createElement("p"); bar.className = "bar"; bar.textContent = name; doc.body.appendChild(bar);
    renderMd(doc, doc.body, text);
  }
  BOARD.openMarkdown = openMarkdown;

  /* ---------- drawing ---------- */
  var F = "all", LAST = null, wired = false;
  var COLS = [{ id: "file", label: "File", identity: true }, { id: "kind", label: "Kind" }, { id: "what", label: "What" },
              { id: "scope", label: "Scope", only: "goal" }, { id: "changed", label: "Changed" }];   /* the columns the panel really has (ticket 20) */
  function el(tag, cls, text) {
    var e = root.document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function css() {
    if (root.document.getElementById("files-css")) return;
    var s = el("style");
    s.id = "files-css";
    s.textContent =
      ".fl{width:100%;border-collapse:collapse}.fl th{text-align:left;font-size:.875em;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);font-weight:600;padding:2px 8px 3px 0;border-bottom:1px solid var(--border)}" +
      ".fl td{padding:4px 8px 4px 0;border-bottom:1px solid var(--border);vertical-align:top}.fl td:first-child{overflow-wrap:anywhere}.fl .nw{white-space:nowrap}" +
      ".ftools{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin:2px 0 6px}.ftools button{border:1px solid var(--border);background:var(--bg);border-radius:8px;padding:0 9px}" +
      ".ftools button[aria-pressed=true]{background:var(--ink);color:var(--bg)}.chip.work{background:var(--t-work);border-color:var(--work)}" +
      ".chip.wait{border-color:var(--wait)}.chip.idle{background:var(--t-idle);border-color:var(--muted2);color:var(--muted)}";
    root.document.head.appendChild(s);
  }
  function chip(cls, text) { return el("span", "chip " + cls, text); }

  function fileUrl(c, path) {
    var sq = c && c.squadKey ? "squad=" + encodeURIComponent(c.squadKey) + "&" : "";
    return "/api/file?" + sq + "path=" + encodeURIComponent(path);
  }

  function draw() {
    if (!LAST) return;
    var body = LAST.body, d = LAST.d, c = LAST.c;
    css();
    body.textContent = "";
    var R = rowsForFiles(d, F);
    c.setCount(R.total, false);
    if (!R.total && !R.missing && !(d && d.report_expected)) {
      body.appendChild(el("p", "muted", "No files yet. Artifacts, reports and evidences appear as the team writes them."));
      return;
    }
    var tools = el("div", "ftools");
    FILTERS.forEach(function (f) {
      var b = el("button", null, f[1]); b.type = "button"; b.dataset.ff = f[0]; b.setAttribute("aria-pressed", F === f[0] ? "true" : "false");
      tools.appendChild(b);
    });
    tools.appendChild(el("span", "muted", "Time is the file’s modified time."));
    body.appendChild(tools);
    var tb = el("table", "fl"), hd = el("tr");
    /* one scope selected: every row has the same scope, so the Scope column is left out (its place in the saved order stays) */
    var cols = c.columns(d && d.report_expected ? "scope" : "goal");
    cols.forEach(function (k) { var th = el("th", null, k.label); th.dataset.col = k.id; th.draggable = true; if (k.id === "changed") th.title = "The file\u2019s modified time, in your zone"; hd.appendChild(th); });
    tb.appendChild(hd);
    R.rows.forEach(function (r) {
      var tr = el("tr"), cell = {}, a = el("td"), link = el("a", "of", r.name);
      link.href = fileUrl(c, r.path); link.target = "_blank"; link.rel = "noopener noreferrer";
      link.title = "Opens in a new tab (read-only)"; if (r.md) link.dataset.md = r.path;
      a.appendChild(link); cell.file = a;
      var k = el("td"); k.appendChild(chip(r.kind === "report" ? "wait" : r.kind === "evidence" ? "work" : "idle", r.kind)); cell.kind = k;
      cell.what = el("td", null, r.what);
      cell.scope = el("td", null, r.scope);
      var t = el("td", "nw");
      if (r.iso) { var tm = el("time", null, fileTime(r.iso, c.now, c.tz)); tm.dateTime = r.iso; tm.title = r.iso.slice(0, 10) + " " + r.iso.slice(11, 16) + " UTC in the files"; t.appendChild(tm); }
      else t.textContent = "—";
      cell.changed = t;
      cols.forEach(function (k2) { tr.appendChild(cell[k2.id]); }); tb.appendChild(tr);
    });
    if (R.missing) {
      var mr = el("tr"), n = el("td"); n.appendChild(el("span", null, "report/report.html")); n.appendChild(root.document.createTextNode(" "));
      n.appendChild(chip("unk", R.missing));
      var kd = el("td"); kd.appendChild(chip("wait", "report"));
      var mc = { file: n, kind: kd, what: el("td", null, "scope report"), scope: el("td", null, ""), changed: el("td", null, "—") };
      cols.forEach(function (k2) { mr.appendChild(mc[k2.id]); });
      tb.insertBefore(mr, hd.nextSibling);   /* first, so the missing report is seen without scrolling */
    }
    body.appendChild(tb);
    if (!R.rows.length && !R.missing) body.appendChild(el("p", "muted", "No file in this filter."));
    if (R.truncated) body.appendChild(el("p", "note", "The list is cut: this scope has more files than the board lists."));
  }

  function wire(body) {
    if (wired) return;
    wired = true;
    body.addEventListener("click", function (e) {
      var t = e.target, f = t.closest && t.closest("button[data-ff]");
      if (f) { F = f.dataset.ff; draw(); return; }
      var a = t.closest && t.closest("a[data-md]");
      if (!a || e.button || e.ctrlKey || e.metaKey || e.shiftKey || !LAST) return;
      var w = root.open("", "_blank");
      if (!w) return;                                   /* popup blocked: the link still opens the plain file */
      e.preventDefault();
      root.fetch(a.href).then(function (r) { return r.ok ? r.text() : Promise.reject(new Error(String(r.status))); })
        .then(function (txt) { openMarkdown(w, a.textContent, txt); })
        .catch(function () { w.document.body.textContent = "Could not open " + a.textContent; });
    });
  }

  BOARD.registerPanel({
    id: "files", columns: COLS, title: "Files", route: "/api/files", span: 8, spans: [4, 8], maxPx: 380,
    isEmpty: function (d) { return !d; },
    render: function (body, d, c) {
      var sq = BOARD.page && BOARD.page.state && BOARD.page.state.squad;
      c.squadKey = sq ? sq.key : "";
      LAST = { body: body, d: d, c: c };
      wire(body);
      draw();
    }
  });
})(typeof window !== "undefined" ? window : this);
