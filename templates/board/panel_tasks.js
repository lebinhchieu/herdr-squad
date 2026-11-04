/* Tasks panel (ticket 12; design-v5.md, proto-v5 "Tasks"). Rows come from /api/tasks (ticket 07); a click opens the detail of one
   task (the `detail` payload of the same route), a second click or Esc closes it. No event feed.
   Cut this panel: delete this file and its <script> line. Pure rules are on BOARD (rowsForTasks, stageClass).
   Untrusted text (titles, FAIL reasons, agent names) reaches the DOM only through textContent. */
(function (root) {
  "use strict";
  var BOARD = root.BOARD = root.BOARD || {};

  /* ---------- pure rules ---------- */
  var DONE = { done: 1, merged: 1 };
  function isReady(stage) { return stage === "ready for review"; }
  function isDone(stage) { return !!DONE[stage]; }
  function stageClass(stage) {
    if (isReady(stage)) return "need";
    if (stage === "blocked") return "bad";
    if (stage === "returned") return "fail";
    if (stage === "in progress" || /^checking/.test(stage)) return "run";
    if (stage === "sha changed after PASS") return "quiet";
    if (isDone(stage)) return "work";
    return "idle";
  }
  /* rowsForTasks(data, nowMs): one object per row, the cell texts the panel shows */
  function rowsForTasks(data, nowMs) {
    var d = data || {};
    return (d.rows || []).map(function (r) {
      var secs = typeof r.last_active === "number" && typeof nowMs === "number" ? Math.max(0, Math.floor(nowMs / 1000 - r.last_active)) : null;
      return { key: (r.scope ? r.scope + "/" : "") + r.id, id: r.id, scope: r.scope || "", title: r.title, stage: r.stage, ready: isReady(r.stage),
               done: isDone(r.stage), cls: stageClass(r.stage), owner: r.owner, waits: r.waits_on, lastIso: r.last_active_iso || null,
               last: secs == null ? "no activity recorded" : BOARD.ageWords(secs), returns: r.returns || 0, failLine: r.last_fail_line || "",
               note: r.detail_note || "", branch: r.branch || "", newCount: r.new_count > 0 ? r.new_count : 0 };
    });
  }
  function filterRows(rows, f) {
    return rows.filter(function (r) { return f === "all" || (f === "open" ? !r.done : f === "review" ? r.ready : r.done); });
  }
  /* the columns the panel really has (ticket 20); the Columns control in board.js lists these */
  var COLS = [{ id: "task", label: "Task", identity: true }, { id: "title", label: "Title" }, { id: "stage", label: "Stage" },
              { id: "last_active", label: "Last active" }, { id: "happened", label: "What happened" }, { id: "owner", label: "Owner" },
              { id: "waits", label: "Waits on" }];
  BOARD.rowsForTasks = rowsForTasks; BOARD.taskStageClass = stageClass; BOARD.taskFilter = filterRows;

  /* ---------- drawing ---------- */
  var F = "all", OPEN = null, DET = {}, LAST = null, wired = false;

  function el(tag, cls, text) {
    var e = root.document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function css() {
    if (root.document.getElementById("tasks-css")) return;
    var s = el("style");
    s.id = "tasks-css";
    s.textContent =
      ".chip{align-items:center;justify-content:center;line-height:1;height:1.65em;box-sizing:border-box}" +
      ".chip.run{background:var(--t-need2);border-color:var(--t-edge)}.chip.work{background:var(--t-work);border-color:var(--work)}.chip.idle{background:var(--t-idle);border-color:var(--muted2);color:var(--muted)}" +
      ".chip.bad{background:var(--t-bad);border-color:var(--block)}.chip.fail{border-color:var(--fail);color:var(--fail)}.chip.quiet{background:var(--t-amber);border-color:var(--amber);color:var(--amber)}" +
      ".tk{width:100%;border-collapse:collapse}.tk th{text-align:left;font-size:.875em;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);font-weight:600;padding:2px 8px 3px 0;border-bottom:1px solid var(--border);white-space:nowrap}" +
      ".tk td{padding:4px 8px 4px 0;border-bottom:1px solid var(--border);vertical-align:top}.tk tr.r{cursor:pointer}.tk tr.r:hover td{background:var(--t-need3)}" +
      ".tk tr.on td{background:var(--t-need2)}.tk tr.done td{color:var(--muted)}.tk tr.need td:first-child{box-shadow:inset 3px 0 var(--mango);padding-left:6px}" +
      ".tk tr.need td{background:var(--t-need3)}.tk tr.x td{background:var(--bg);padding:6px 10px;cursor:default}.tk .nw{white-space:nowrap}" +
      ".tk .bt{margin-top:3px;padding:3px 8px;border-left:3px solid var(--block);background:var(--bg);border-radius:0 4px 4px 0}" +
      ".tk .chips{display:flex;gap:3px;flex-wrap:wrap;margin:4px 0}.tk .steps{margin:2px 0 0;padding-left:16px}.tk .steps li{margin:1px 0}" +
      ".tk .failfirst{margin-top:3px;padding:3px 8px;border-left:3px solid var(--fail);background:var(--panel);border-radius:0 4px 4px 0}" +
      ".tools{display:flex;gap:6px;align-items:center;margin:0 0 4px;flex-wrap:wrap}.tools button{border:1px solid var(--border);background:var(--bg);border-radius:12px;padding:0 9px}" +
      ".tools button.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}" +
      ".tk .cp{border:1px solid var(--border);background:var(--bg);border-radius:5px;padding:0 6px;font-size:.92em}.tk .cp:hover{border-color:var(--mango)}";
    root.document.head.appendChild(s);
  }
  /* the "N new" of a row: the server's count minus what the PO already opened (ticket 13) */
  function seenScope(r) { var s = BOARD.ctx && BOARD.ctx.seen; return r.scope || (s ? s.scopeKey() : ""); }
  function newOf(r) { var s = BOARD.ctx && BOARD.ctx.seen; return s ? s.shown(seenScope(r), r.id, r.newCount) : r.newCount; }
  function chip(cls, text) { return el("span", "chip " + cls, text); }

  function copyIt(btn) {
    var t = btn.getAttribute("data-copy") || "";
    try { root.navigator.clipboard.writeText(t); btn.textContent = "copied"; root.setTimeout(function () { btn.textContent = "copy"; }, 1500); }
    catch (e) { /* the text stays visible; select it by hand */ }
    return t;
  }

  function stepTime(iso, tz) {
    if (!iso) return "time unknown";
    return BOARD.fmtDate(iso, tz) + " " + BOARD.fmtTime(iso, tz);
  }

  function detailNode(r, c) {
    var box = el("div");
    box.appendChild(el("b", null, r.key)); box.appendChild(root.document.createTextNode(" " + r.title));
    if (r.returns && r.failLine) box.appendChild(el("div", "failfirst", "FAIL: " + r.failLine));
    if (r.note) box.appendChild(el("div", "bt", r.note));
    var det = DET[r.key];
    if (!det || det.state === "loading") { box.appendChild(el("p", "muted", "Reading the steps…")); return box; }
    if (det.state === "fail") { box.appendChild(el("p", "muted", "unknown: the steps could not be read")); return box; }
    var agents = (det.data && det.data.agents) || [], steps = (det.data && det.data.steps) || [];
    var ch = el("div", "chips");
    if (agents.length) agents.forEach(function (a) { ch.appendChild(chip("idle", a)); });
    else ch.appendChild(el("span", "muted", "no one yet"));
    box.appendChild(ch);
    if (steps.length) {
      var ol = el("ol", "steps");
      steps.forEach(function (s) {
        var li = el("li", null, stepTime(s.iso, c.tz) + " " + (s.agent || "unknown") + " " + (s.type || ""));
        if (s.reason) li.appendChild(root.document.createTextNode(": " + s.reason));
        ol.appendChild(li);
      });
      box.appendChild(ol);
    } else box.appendChild(el("p", "muted", "No message, commit or transcript record: no activity recorded."));
    if (r.ready && r.branch) {
      var p = el("p"); p.appendChild(el("b", null, "Ready for your review. ")); p.appendChild(root.document.createTextNode("Every checker PASSed this tip. Only you merge: "));
      var cmd = "git merge " + r.branch;
      p.appendChild(el("code", null, cmd));
      var b = el("button", "cp", "copy"); b.type = "button"; b.setAttribute("data-copy", cmd); p.appendChild(root.document.createTextNode(" ")); p.appendChild(b);
      box.appendChild(p);
    }
    return box;
  }

  function queryOf() {
    var ctx = BOARD.ctx, S = ctx && ctx.state;
    if (!S || !S.squad || !S.choice) return null;
    return "squad=" + encodeURIComponent(S.squad.key) + "&" + S.choice.kind + "=" + encodeURIComponent(S.choice.name);
  }
  function fetchDetail(r) {
    var q = queryOf();
    if (!q) return;
    var key = r.key, cur = DET[key];
    if (cur && cur.stamp === r.lastIso && cur.state !== "fail") return;
    DET[key] = { state: cur && cur.data ? "ok" : "loading", data: cur && cur.data, stamp: r.lastIso };
    BOARD.ctx.getJson("/api/tasks?" + q + "&detail=" + encodeURIComponent(r.id)).then(function (j) {
      var rows = (j && j.data && j.data.rows) || [], row = rows.filter(function (x) { return (x.scope || "") === r.scope; })[0];
      DET[key] = row && row.detail ? { state: "ok", data: row.detail, stamp: r.lastIso } : { state: "fail", stamp: r.lastIso };
      if (OPEN === key) draw();
    }, function () { DET[key] = { state: "fail", stamp: r.lastIso }; if (OPEN === key) draw(); });
  }

  function closeDetail() { if (OPEN != null) { OPEN = null; draw(); } }

  function draw() {
    if (!LAST) return;
    var body = LAST.body, d = LAST.d, c = LAST.c;
    css();
    body.textContent = "";
    var all = rowsForTasks(d, c.now), rows = filterRows(all, F);
    var nOpen = all.filter(function (r) { return !r.done; }).length, nReady = all.filter(function (r) { return r.ready; }).length;
    c.setCount(all.length, nReady > 0);
    if (!all.length) { body.appendChild(el("p", "muted", "No tasks yet. The Manager has not published tickets for this choice.")); return; }
    var tools = el("div", "tools");
    [["all", "All (" + all.length + ")"], ["open", "Open (" + nOpen + ")"], ["review", "Ready for review (" + nReady + ")"],
     ["done", "Done (" + (all.length - nOpen) + ")"]].forEach(function (f) {
      var b = el("button", f[0] === F ? "on" : "", f[1]); b.type = "button"; b.dataset.tf = f[0]; b.setAttribute("aria-pressed", f[0] === F ? "true" : "false");
      tools.appendChild(b);
    });
    tools.appendChild(el("span", "muted", "Click a row for the steps in time order."));
    body.appendChild(tools);
    var tb = el("table", "tk"), hd = el("tr"), cols = c.columns();
    cols.forEach(function (k) { var th = el("th", null, k.label); th.dataset.col = k.id; th.draggable = true; hd.appendChild(th); });
    tb.appendChild(hd);
    rows.forEach(function (r) {
      var cell = {}, tr = el("tr", "r" + (r.ready ? " need" : r.done ? " done" : "") + (OPEN === r.key ? " on" : ""));
      tr.dataset.k = r.key; tr.tabIndex = 0;
      var a = el("td", "nw");
      if (r.scope) a.appendChild(el("span", "muted", r.scope + "/"));
      a.appendChild(el("b", null, r.id));
      var nn = newOf(r); if (nn > 0) { a.appendChild(root.document.createTextNode(" ")); a.appendChild(BOARD.newBadge(nn)); }
      cell.task = a;
      cell.title = el("td", null, r.title);
      var st = el("td"); st.appendChild(chip(r.cls, r.stage));
      if (r.returns >= 1 && !r.done) st.appendChild(chip("fail", r.returns + (r.returns === 1 ? " return" : " returns")));
      cell.stage = st;
      var la = el("td"); la.appendChild(el("b", null, r.last));
      if (r.lastIso) la.appendChild(el("div", "muted", stepTime(r.lastIso, c.tz)));
      cell.last_active = la;
      var wh = el("td");
      if (r.failLine) wh.appendChild(el("div", null, "FAIL: " + r.failLine));
      if (r.note) wh.appendChild(el("div", r.stage === "blocked" ? "bt" : "muted", r.note));
      cell.happened = wh;
      cell.owner = el("td", null, r.owner);
      cell.waits = el("td", null, r.waits);
      cols.forEach(function (k) { tr.appendChild(cell[k.id]); });
      tb.appendChild(tr);
      if (OPEN === r.key) {
        var x = el("tr", "x"), xd = el("td"); xd.colSpan = cols.length; xd.appendChild(detailNode(r, c)); x.appendChild(xd); tb.appendChild(x);
      }
    });
    body.appendChild(tb);
    if (!rows.length) body.appendChild(el("p", "muted", "No task in this filter."));
  }

  function wire(body) {
    if (wired) return;
    wired = true;
    body.addEventListener("click", function (e) {
      var t = e.target;
      var f = t.closest && t.closest("[data-tf]");
      if (f) { F = f.dataset.tf; draw(); return; }
      var cp = t.closest && t.closest("button[data-copy]");
      if (cp) { copyIt(cp); return; }
      if (t.closest && t.closest("tr.x")) return;
      var tr = t.closest && t.closest("tr.r");
      if (!tr) return;
      var k = tr.dataset.k;
      if (OPEN === k) { OPEN = null; draw(); return; }
      var row = rowsForTasks(LAST.d, LAST.c.now).filter(function (r) { return r.key === k; })[0];
      if (row && row.newCount > 0 && BOARD.ctx && BOARD.ctx.seen) {   /* opening the detail clears the dot; the picker rows drop by the same count */
        BOARD.ctx.seen.clear(seenScope(row), row.id, row.newCount);
        if (BOARD.hooks.paint) BOARD.hooks.paint(BOARD.ctx.state);
      }
      OPEN = k; draw();
      if (row) fetchDetail(row);
    });
    body.addEventListener("keydown", function (e) { if (e.key === "Enter" && e.target.tagName === "TR") e.target.click(); });
    root.document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeDetail(); });
  }

  BOARD.registerPanel({
    id: "tasks", columns: COLS, title: "Tasks", route: "/api/tasks", span: 8, spans: [4, 6, 8, 12], maxPx: 560,
    isEmpty: function (d) { return !d; },
    render: function (body, d, c) {
      LAST = { body: body, d: d, c: c };
      wire(body);
      if (OPEN != null) {
        var open = rowsForTasks(d, c.now).filter(function (r) { return r.key === OPEN; })[0];
        if (!open) OPEN = null; else fetchDetail(open);
      }
      draw();
    }
  });
})(typeof window !== "undefined" ? window : this);
