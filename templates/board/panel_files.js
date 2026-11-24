/* Files panel (ticket 14; design-v5.md "Files"). Rows come from /api/files (bin/squadboard_files.py).
   Cut this panel: delete this file and its <script> line. Pure rules on BOARD: rowsForFiles, mdBlocks; renderMd builds DOM.
   A click on a row opens the file in VS Code through one link (BOARD.vscodeUrl): no new tab and no request (ticket 30). Ticket 07 reverses one line of
   ticket 30: a Preview button on ticket rows reads the ticket from /api/file in the page (and its images in image mode); row clicks still open VS Code.
   A status line (role=status) says what was sent and offers Copy path. Every text reaches the DOM through textContent. */
(function (root) {
  "use strict";
  var BOARD = root.BOARD = root.BOARD || {};

  /* ---------- pure rules ---------- */
  var GROUP = { report: "report", data: "report", evidence: "evidence" };   /* every other kind is an "artifact" */
  var TITLE_MAX = 80;
  function groupOf(kind) { return GROUP[kind] || "artifact"; }
  var FILTERS = [["all", "All"], ["artifact", "Artifacts"], ["report", "Reports"], ["evidence", "Evidences"]];
  /* rowsForFiles(data, filter): {rows, total, missing (text or null), truncated}. The report row is missing in a live scope. */
  function rowsForFiles(data, filter) {
    var d = data || {}, all = d.rows || [], f = filter || "all";
    function shape(r, kind) {
      return { name: r.name, path: r.path, abs: r.abs || null, blocked: !!r.blocked, kind: kind, raw: r.kind, what: r.what, scope: r.scope, mtime: r.mtime,
               iso: typeof r.mtime === "number" ? new Date(r.mtime * 1000).toISOString() : null };
    }
    var rows = all.filter(function (r) { return f === "all" || groupOf(r.kind) === f; }).map(function (r) { return shape(r, groupOf(r.kind)); });
    var folders = (d.folders || []).map(function (r) { return shape(r, "folder"); });   /* always first, not filtered, not counted */
    var missing = d.report_expected && !d.report && !d.closed && (f === "all" || f === "report") ? "no report yet (made at close)" : null;
    return { folders: folders, wsl_distro: d.wsl_distro || null, rows: rows, total: all.length, missing: missing, truncated: !!d.truncated };
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

  /* vscodeUrl(abs, distro): the one link form for every file or folder (ticket 30, O1 answered by the PO).
     "vscode://file/<abs>", or "vscode://vscode-remote/wsl+<distro>/<abs>" when the board runs in WSL. Each segment is percent-encoded, "/" stays.
     Empty gives null. The prefix is fixed, so no javascript: URL can result. */
  function vscodeUrl(abs, distro) {
    if (!abs) return null;
    var p = String(abs).replace(/\\/g, "/").replace(/^\/+/, "");
    var enc = p.split("/").map(function (seg) { return /^[A-Za-z]:$/.test(seg) ? seg : encodeURIComponent(seg); }).join("/");
    return distro ? "vscode://vscode-remote/wsl+" + encodeURIComponent(distro) + "/" + enc : "vscode://file/" + enc;
  }
  BOARD.vscodeUrl = vscodeUrl;

  /* openFile(e, a, abs): ticket 34. A plain left click on a file link asks the board (POST /api/open) to run `code --goto <abs>`.
     The link is followed only when that fails (no VS Code, refused, timeout, no token): the fallback is the ticket-30 click on the same link.
     Returns true when it took the click. Ctrl/Shift/Alt/Meta, middle and right clicks, folder links and the fallback click are left to the browser. */
  BOARD.openTimeoutMs = 5800;
  function openFile(e, a, abs) {
    if (!a || a.dataset.fb || a.dataset.folder || !abs || e.button || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return false;
    var st = BOARD.page && BOARD.page.state, sq = st && st.squad;
    e.preventDefault();
    var done = false;
    function fallback() { if (done) return; done = true; a.dataset.fb = "1"; try { a.click(); } finally { delete a.dataset.fb; } }
    if (!st || !st.token || !sq || !root.fetch) { fallback(); return true; }
    var timer = root.setTimeout(fallback, BOARD.openTimeoutMs);
    try {
      root.fetch("/api/open?squad=" + encodeURIComponent(sq.key), { method: "POST", headers: { "Content-Type": "application/json", "X-Board-Token": st.token },
        body: JSON.stringify({ path: abs }) })
        .then(function (r) { return r.json(); })
        .then(function (j) { root.clearTimeout(timer); if (j && j.data && j.data.ok === true) done = true; else fallback(); })
        .catch(function () { root.clearTimeout(timer); fallback(); });
    } catch (err) { root.clearTimeout(timer); fallback(); }
    return true;
  }
  BOARD.openFile = openFile;

  /* mdBlocks(text) -> [{t: "h", l, s} | {t: "li", s} | {t: "p", s} | {t: "code", s, lang, cap} | {t: "img", alt, src} | {t: "table", rows: [[cell]], head}]
     lang = the first word after the opening fence, cap = the rest of that line. A line that is only ![alt](src) is an img. */
  function mdBlocks(text) {
    var lines = String(text == null ? "" : text).replace(/\r\n?/g, "\n").split("\n"), out = [], i = 0, para = [];
    function flush() { if (para.length) { out.push({ t: "p", s: para.join(" ") }); para = []; } }
    while (i < lines.length) {
      var ln = lines[i], m;
      if ((m = /^\s*```\s*(\S*)\s*(.*?)\s*$/.exec(ln))) {
        flush(); var buf = []; i++;
        while (i < lines.length && !/^\s*```/.test(lines[i])) buf.push(lines[i++]);
        i++; out.push({ t: "code", s: buf.join("\n"), lang: m[1], cap: m[2] }); continue;
      }
      if (!para.length && (m = /^\s*!\[([^\]]*)\]\(([^)\s]*)\)\s*$/.exec(ln))) { out.push({ t: "img", alt: m[1], src: m[2] }); i++; continue; }
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

  /* imgPath(src): the image path a ticket may name, or null. Relative, no "..", no scheme, no leading "/", no backslash, .png/.jpg/.svg only. */
  function imgPath(src) {
    var s = String(src == null ? "" : src);
    if (!s || /^[A-Za-z][A-Za-z0-9+.-]*:/.test(s) || /^[\/\\]/.test(s) || s.indexOf("\\") >= 0 || /[\x00-\x1f?#%]/.test(s)) return null;
    if (s.split("/").some(function (seg) { return seg === ".." || seg === "" ; })) return null;
    return /\.(png|jpg|svg)$/i.test(s) ? s : null;
  }
  BOARD.imgPath = imgPath;

  /* renderMd(doc, host, text, imgUrl): draws the markdown into `host` with createElement/textContent/setAttribute only.
     imgUrl(path) -> url or null: where an allowed image is fetched; without it (or for a refused path) only the alt text shows, and nothing is requested. */
  function renderMd(doc, host, text, imgUrl) {
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
      else if (b.t === "code") {
        if (b.lang.toLowerCase() === "diagram") {
          var fig = mk("div"), bar = mk("div"), chip = mk("span", "diagram");
          fig.className = "mdfig"; bar.className = "mdcap"; chip.className = "chip idle";
          bar.appendChild(chip);
          if (b.cap) bar.appendChild(mk("span", b.cap));
          fig.appendChild(bar); fig.appendChild(mk("pre", b.s)); host.appendChild(fig);
        } else host.appendChild(mk("pre", b.s));
      }
      else if (b.t === "img") host.appendChild(mdImage(doc, b, imgUrl));
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
  function mdImage(doc, b, imgUrl) {
    var wrap = doc.createElement("div"), alt = doc.createElement("span"), path = imgPath(b.src), url = path && imgUrl ? imgUrl(path) : null;
    wrap.className = "mdimg"; alt.className = "mdalt"; alt.textContent = b.alt;
    wrap.appendChild(alt);
    if (!url) return wrap;   /* refused: alt text only, no request */
    var im = doc.createElement("img");
    im.setAttribute("alt", b.alt); im.setAttribute("title", b.alt);
    im.onload = function () { wrap.textContent = ""; wrap.appendChild(im); var c = doc.createElement("div"); c.className = "mdalt"; c.textContent = b.alt; wrap.appendChild(c); };
    im.onerror = function () { alt.setAttribute("title", "image not found"); };
    im.setAttribute("src", url);
    return wrap;
  }

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
      ".chip.wait{border-color:var(--wait)}.chip.idle{background:var(--t-idle);border-color:var(--muted2);color:var(--muted)}.fpath{font-size:.8em;overflow-wrap:anywhere}" +
      ".fl tr[data-open]{cursor:pointer}.fl td.pv{text-align:right;white-space:nowrap}.fl tr.pvr td{background:var(--bg);padding:6px 10px;cursor:default}.fstatus{display:flex;gap:8px;align-items:center;margin:2px 0 6px;font-size:.9em}.fstatus button{border:1px solid var(--border);background:var(--bg);border-radius:8px;padding:0 9px}" +
      ".pvbox{max-height:60vh;overflow:auto}.pvhead{display:flex;gap:10px;align-items:baseline;justify-content:space-between;margin-bottom:4px}.pvbox h1{font-size:1.1em}.pvbox h2,.pvbox h3,.pvbox h4,.pvbox h5,.pvbox h6{font-size:1em;margin:8px 0 2px}" +
      ".pvbox pre{background:var(--panel);border:1px solid var(--border);border-radius:6px;padding:6px 8px;margin:4px 0;font-family:monospace;white-space:pre;overflow-x:auto}" +
      ".pvbox .mdcap{display:flex;gap:8px;align-items:center;color:var(--muted);margin-top:6px}.pvbox .mdfig pre{margin-top:2px}" +
      ".pvbox table{border-collapse:collapse}.pvbox th,.pvbox td{border:1px solid var(--border);padding:2px 6px;text-align:left}.pvbox th{text-transform:uppercase;color:var(--muted);font-size:.875em}" +
      ".pvbox img{max-width:100%;height:auto;border:1px solid var(--border);border-radius:6px;display:block}.pvbox .mdalt{color:var(--muted);font-style:italic}";
    root.document.head.appendChild(s);
  }
  function chip(cls, text) { return el("span", "chip " + cls, text); }

  /* status line: "Sent to VS Code: <abs>" + Copy path, 8 s, kept in module state so a redraw inside the 8 s keeps it */
  var STATUS = null, TIMER = null;
  BOARD.filesStatusMs = 8000;
  function showStatus(body) {
    var old = body.querySelector("[data-status]");
    if (old) old.remove();
    if (!STATUS) return;
    var d = el("div", "fstatus"), b = el("button", null, "Copy path");
    d.setAttribute("role", "status"); d.setAttribute("data-status", "1"); b.type = "button"; b.dataset.copy = STATUS;
    d.appendChild(el("span", null, "Sent to VS Code: " + STATUS)); d.appendChild(root.document.createTextNode(" ")); d.appendChild(b);
    body.insertBefore(d, body.firstChild);
  }
  function sent(body, abs) {
    STATUS = abs;
    if (TIMER) root.clearTimeout(TIMER);
    TIMER = root.setTimeout(function () { STATUS = null; TIMER = null; var o = body.querySelector("[data-status]"); if (o) o.remove(); }, BOARD.filesStatusMs);
    showStatus(body);
  }
  function copyPath(abs) {
    try {
      if (root.navigator && root.navigator.clipboard) { root.navigator.clipboard.writeText(abs).catch(function () { legacyCopy(abs); }); return; }
    } catch (e) { /* fall through */ }
    legacyCopy(abs);
  }
  function legacyCopy(abs) {
    try { var i = el("input"); i.value = abs; root.document.body.appendChild(i); i.select(); root.document.execCommand("copy"); i.remove(); } catch (e) { /* no error text */ }
  }

  /* Preview (ticket 07): one open at a time, kept in module state so a redraw keeps it. PV = {abs, name, state: loading|ok|empty|err, text} */
  var PV = null;
  function pvRow(r, ncols, distro) {
    var tr = el("tr", "pvr"), td = el("td"), box = el("div", "pvbox"), head = el("div", "pvhead"), url = vscodeUrl(PV.abs, distro);
    td.colSpan = ncols + 1;
    head.appendChild(el("b", null, r.name));
    if (url) { var a = el("a", null, "Open in VS Code"); a.href = url; a.rel = "noopener noreferrer"; a.dataset.abs = PV.abs; head.appendChild(a); }
    box.appendChild(head);
    if (PV.state === "loading") box.appendChild(el("div", "pstate", "Loading ticket\u2026"));
    else if (PV.state === "empty") box.appendChild(el("div", "pstate", "This ticket is empty."));
    else if (PV.state === "err") {
      var er = el("div", "pstate perr", "Cannot show this ticket. Open it in VS Code.");
      box.appendChild(er);
    } else {
      var sq = BOARD.page && BOARD.page.state && BOARD.page.state.squad, key = sq ? sq.key : "", base = PV.abs.replace(/\.md$/i, "") + "/";
      renderMd(root.document, box, PV.text, function (p) {
        return "/api/file?squad=" + encodeURIComponent(key) + "&path=" + encodeURIComponent(base + p) + "&img=1&base=" + encodeURIComponent(base);
      });
    }
    td.appendChild(box); tr.appendChild(td);
    return tr;
  }
  function togglePreview(abs, name) {
    if (PV && PV.abs === abs) { PV = null; draw(); return; }
    var me = PV = { abs: abs, name: name, state: "loading", text: "" };
    var sq = BOARD.page && BOARD.page.state && BOARD.page.state.squad;
    function done(state, text) { if (PV !== me) return; me.state = state; me.text = text || ""; draw(); }
    draw();
    try {
      root.fetch("/api/file?squad=" + encodeURIComponent(sq ? sq.key : "") + "&path=" + encodeURIComponent(abs))
        .then(function (r) { if (!r.ok) throw new Error("x"); return r.text(); })
        .then(function (t) { done(/^\s*$/.test(t) ? "empty" : "ok", t); })
        .catch(function () { done("err"); });
    } catch (e) { done("err"); }
  }

  function fileRow(r, cols, c, distro) {
    var tr = el("tr"), cell = {}, a = el("td"), url = r.blocked ? null : vscodeUrl(r.abs, distro);
    if (url) {
      var link = el("a", "of");
      link.href = url; link.rel = "noopener noreferrer"; link.title = r.abs + " \u2014 opens in VS Code"; link.dataset.abs = r.abs;
      if (r.kind === "folder") link.dataset.folder = "1";   /* ticket 34: no route call for a folder, the href does the work */
      var nm = el(r.kind === "folder" ? "b" : "span", null, r.name); link.appendChild(nm);
      a.appendChild(link);
      if (r.kind === "folder") a.appendChild(el("div", "fpath muted", r.abs));
      tr.dataset.open = "1";
    } else { a.appendChild(el("span", "muted", r.name)); tr.className = "muted"; }
    cell.file = a;
    var k = el("td"); k.appendChild(chip(r.kind === "report" ? "wait" : r.kind === "evidence" ? "work" : "idle", r.raw === "ticket" ? "ticket" : r.kind)); cell.kind = k;
    var wtxt = r.what;   /* T29.AC11: a long ticket title is cut with an ellipsis, the full title is the tooltip */
    cell.what = el("td", r.blocked ? "muted" : null, r.raw === "ticket" && wtxt && wtxt.length > TITLE_MAX ? wtxt.slice(0, TITLE_MAX - 1).replace(/\s+$/, "") + "\u2026" : wtxt);
    if (r.raw === "ticket" && wtxt && wtxt.length > TITLE_MAX) cell.what.title = wtxt;
    cell.scope = el("td", null, r.scope);
    var t = el("td", "nw");
    if (r.iso) { var tm = el("time", null, fileTime(r.iso, c.now, c.tz)); tm.dateTime = r.iso; tm.title = r.iso.slice(0, 10) + " " + r.iso.slice(11, 16) + " UTC in the files"; t.appendChild(tm); }
    else t.textContent = "\u2014";
    cell.changed = t;
    cols.forEach(function (k2) { tr.appendChild(cell[k2.id]); });
    if (r.raw === "ticket" && r.abs && !r.blocked) {   /* ticket 07: Preview, a separate button; the row click still opens VS Code */
      var pt = el("td", "pv"), pb = el("button", "pbtn", PV && PV.abs === r.abs ? "\u25be" : "\u25b8");
      pb.type = "button"; pb.dataset.pv = r.abs; pb.title = "Preview"; pb.setAttribute("aria-label", "Preview " + r.name);
      pb.setAttribute("aria-expanded", PV && PV.abs === r.abs ? "true" : "false");
      pt.appendChild(pb); tr.appendChild(pt);
    }
    return tr;
  }

  function draw() {
    if (!LAST) return;
    var body = LAST.body, d = LAST.d, c = LAST.c;
    css();
    body.textContent = "";
    var R = rowsForFiles(d, F);
    c.setCount(R.total, false);
    var empty = !R.total;   /* T29.AC3: the note also shows when only the folder rows and the report placeholder are there */
    var tools = el("div", "ftools");
    FILTERS.forEach(function (f) {
      var b = el("button", null, f[1]); b.type = "button"; b.dataset.ff = f[0]; b.setAttribute("aria-pressed", F === f[0] ? "true" : "false");
      tools.appendChild(b);
    });
    tools.appendChild(el("span", "muted", "Time is the file\u2019s modified time."));
    body.appendChild(tools);
    var tb = el("table", "fl"), hd = el("tr");
    /* one scope selected: every row has the same scope, so the Scope column is left out (its place in the saved order stays) */
    var cols = c.columns(d && d.report_expected ? "scope" : "goal");
    cols.forEach(function (k) { var th = el("th", null, k.label); th.dataset.col = k.id; th.draggable = true; if (k.id === "changed") th.title = "The file\u2019s modified time, in your zone"; hd.appendChild(th); });
    tb.appendChild(hd);
    R.folders.forEach(function (r) { tb.appendChild(fileRow(r, cols, c, R.wsl_distro)); });
    if (R.missing) {
      var mr = el("tr"), n = el("td"); n.appendChild(el("span", null, "report/report.html")); n.appendChild(root.document.createTextNode(" "));
      n.appendChild(chip("unk", R.missing));
      var kd = el("td"); kd.appendChild(chip("wait", "report"));
      var mc = { file: n, kind: kd, what: el("td", null, "scope report"), scope: el("td", null, ""), changed: el("td", null, "\u2014") };
      cols.forEach(function (k2) { mr.appendChild(mc[k2.id]); });
      tb.appendChild(mr);   /* first after the folder rows, so the missing report is seen without scrolling */
    }
    R.rows.forEach(function (r) {
      tb.appendChild(fileRow(r, cols, c, R.wsl_distro));
      if (PV && PV.abs === r.abs) tb.appendChild(pvRow(r, cols.length, R.wsl_distro));
    });
    body.appendChild(tb);
    if (empty) body.appendChild(el("p", "muted", "No other files yet. Artifacts, reports and evidence appear here."));
    else if (!R.rows.length && !R.missing) body.appendChild(el("p", "muted", "No file in this filter."));
    if (R.truncated) body.appendChild(el("p", "note", "The list is cut: this scope has more files than the board lists."));
    showStatus(body);
  }

  function focusPv(body, abs) {
    var bs = body.querySelectorAll("button[data-pv]");
    for (var i = 0; i < bs.length; i++) if (bs[i].dataset.pv === abs) { bs[i].focus(); break; }
  }
  function wire(body) {
    if (wired) return;
    wired = true;
    body.addEventListener("click", function (e) {
      var t = e.target, f = t.closest && t.closest("button[data-ff]");
      if (f) { F = f.dataset.ff; draw(); return; }
      var pv = t.closest && t.closest("button[data-pv]");
      if (pv) { var nm = pv.closest("tr").querySelector("a[data-abs] span"); togglePreview(pv.dataset.pv, nm ? nm.textContent : ""); focusPv(body, pv.dataset.pv); return; }
      var cp = t.closest && t.closest("button[data-copy]");
      if (cp) { copyPath(cp.dataset.copy); return; }
      var a = t.closest && t.closest("a[data-abs]");
      if (a) { sent(body, a.dataset.abs); openFile(e, a, a.dataset.abs); return; }   /* the board opens it; the link is followed only as the fallback */
      var tr = t.closest && t.closest("tr[data-open]");        /* the whole row is the link */
      if (tr && tr.querySelector("a[data-abs]")) tr.querySelector("a[data-abs]").click();
    });
    body.addEventListener("keydown", function (e) {   /* Esc closes the preview and returns focus to its button */
      if (e.key !== "Escape" || !PV) return;
      var abs = PV.abs; PV = null; draw(); focusPv(body, abs);
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
