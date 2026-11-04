/* Agents now panel (ticket 12; design-v5.md, proto-v5 "Agents now"). Rows come from /api/agents (ticket 08).
   Cut this panel: delete this file and its <script> line. Pure rule on BOARD: rowsForAgents.
   "N retired" is a toggle over data already in the answer (no extra request). Text reaches the DOM only through textContent. */
(function (root) {
  "use strict";
  var BOARD = root.BOARD = root.BOARD || {};

  /* ---------- pure rules ---------- */
  function statusOf(a) {
    if (a.status === "blocked") return { text: "blocked: permission prompt", cls: "need" };
    if (a.status === "working") return { text: "working", cls: "work" };
    if (a.status === "idle") return { text: "idle", cls: "idle" };
    return { text: "status unknown", cls: "unk" };
  }
  /* rowsForAgents(data, nowMs): {live: [row], retired: [row], retiredLabel, unknown} */
  function rowsForAgents(data, nowMs) {
    var d = data || {};
    var mk = function (a) {
      var st = statusOf(a), secs = typeof a.last_activity === "number" && typeof nowMs === "number" ? Math.max(0, Math.floor(nowMs / 1000 - a.last_activity)) : null;
      return { name: a.name, role: a.role, owns: a.task || "", status: st.text, cls: st.cls, scope: a.scope || "",
               last: secs == null ? "no activity recorded" : BOARD.ageWords(secs), lastEpoch: typeof a.last_activity === "number" ? a.last_activity : null };
    };
    var n = typeof d.retired_count === "number" ? d.retired_count : (d.retired || []).length;
    return { live: (d.agents || []).map(mk), retired: (d.retired || []).map(mk), retiredCount: n, retiredLabel: n + " retired",
             unknown: d.status === "unknown" ? "status unknown: " + (d.reason || "herdr not running") : null };
  }
  BOARD.rowsForAgents = rowsForAgents;

  /* ---------- drawing ---------- */
  var SHOW = false, LAST = null, wired = false;
  function el(tag, cls, text) {
    var e = root.document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function css() {
    if (root.document.getElementById("agents-css")) return;
    var s = el("style");
    s.id = "agents-css";
    s.textContent =
      ".chip{align-items:center;justify-content:center;line-height:1;height:1.65em;box-sizing:border-box}" +
      ".chip.work{background:var(--t-work);border-color:var(--work)}.chip.idle{background:var(--t-idle);border-color:var(--muted2);color:var(--muted)}" +
      ".ag{width:100%;border-collapse:collapse}.ag th{text-align:left;font-size:.875em;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);font-weight:600;padding:2px 8px 3px 0;border-bottom:1px solid var(--border);white-space:nowrap}" +
      ".ag td{padding:4px 8px 4px 0;border-bottom:1px solid var(--border);vertical-align:top}.ag tr.need td:first-child{box-shadow:inset 3px 0 var(--mango);padding-left:6px}" +
      ".ag .nm{font-weight:600}.ag small{display:block;color:var(--muted)}.ag-more{margin-top:6px}.ag-more ul{margin:4px 0 0;padding-left:16px;color:var(--muted)}" +
      ".ag-btn{border:1px solid var(--border);background:var(--bg);border-radius:12px;padding:0 9px;color:var(--muted)}.ag-btn:hover{border-color:var(--ink);color:var(--ink)}";
    root.document.head.appendChild(s);
  }
  function chip(cls, text) { return el("span", "chip " + cls, text); }

  function draw() {
    if (!LAST) return;
    var body = LAST.body, d = LAST.d, c = LAST.c;
    css();
    body.textContent = "";
    var R = rowsForAgents(d, c.now);
    c.setCount(R.live.length, false);
    if (R.unknown) { var n = el("p", "note"); n.appendChild(el("b", null, R.unknown + ".")); n.appendChild(root.document.createTextNode(" Roles and tasks come from roster.md.")); body.appendChild(n); }
    if (!R.live.length) body.appendChild(el("p", "muted", "No live agents. roster.md lists none yet."));
    else {
      var tb = el("table", "ag"), hd = el("tr");
      ["Agent", "Owns", "Status", "Last active"].forEach(function (h) { hd.appendChild(el("th", null, h)); });
      tb.appendChild(hd);
      R.live.forEach(function (r) {
        var tr = el("tr", r.cls === "need" ? "need" : "");
        var a = el("td"); var nm = el("span", "nm", r.name); nm.title = r.role; a.appendChild(nm);
        a.appendChild(el("small", null, r.role + (r.scope ? " · " + r.scope : ""))); tr.appendChild(a);
        tr.appendChild(el("td", null, r.owns));
        var st = el("td"); st.appendChild(chip(r.cls, r.status)); tr.appendChild(st);
        var la = el("td"); la.appendChild(el("b", null, r.last));
        if (r.lastEpoch != null) { var iso = new Date(r.lastEpoch * 1000).toISOString(); la.appendChild(el("small", null, c.fmtTime(iso))); }
        tr.appendChild(la);
        tb.appendChild(tr);
      });
      body.appendChild(tb);
    }
    if (R.retiredCount > 0) {
      var m = el("div", "ag-more");
      var b = el("button", "ag-btn", SHOW ? "Hide " + R.retiredLabel : R.retiredLabel + ", hidden");
      b.type = "button"; b.dataset.retired = "1"; b.setAttribute("aria-expanded", SHOW ? "true" : "false");
      m.appendChild(b);
      if (SHOW) {
        var ul = el("ul");
        R.retired.forEach(function (r) { ul.appendChild(el("li", null, r.name + " · " + r.owns)); });
        m.appendChild(ul);
      }
      body.appendChild(m);
    }
  }

  BOARD.registerPanel({
    id: "agents", title: "Agents now", route: "/api/agents", span: 4, spans: [4, 6, 8], maxPx: 380,
    isEmpty: function (d) { return !d; },
    render: function (body, d, c) {
      LAST = { body: body, d: d, c: c };
      if (!wired) {
        wired = true;
        body.addEventListener("click", function (e) {
          var b = e.target.closest && e.target.closest("button[data-retired]");
          if (b) { SHOW = !SHOW; draw(); }
        });
      }
      draw();
    }
  });
})(typeof window !== "undefined" ? window : this);
