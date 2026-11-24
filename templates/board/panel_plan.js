/* Plan panel (po-clarity ticket 04; ui-design/04.md). Rows come from /api/plan: one per task (scope home) or per scope (goal home),
   grouped by step. No Needs-you list (the inbox panel has it) and no mango. Cut this panel: delete this file and its <script> line.
   Pure rules are on BOARD (planModel, planDuration, planDeps). Untrusted text (aims, titles, waits) reaches the DOM only through textContent. */
(function (root) {
  "use strict";
  var BOARD = root.BOARD = root.BOARD || {};
  var AIM_MAX = 60, OVER = 1.5;

  /* ---------- pure rules ---------- */
  function fmtMin(m) {
    if (typeof m !== "number" || !isFinite(m) || m < 0) return "–";
    var h = Math.floor(m / 60), r = Math.round(m - h * 60);
    return h && r ? h + "h " + r + "m" : h ? h + "h" : r + "m";
  }
  function clip(s, n) { s = String(s == null ? "" : s); return s.length > n ? s.slice(0, n - 1) + "…" : s; }
  /* "01-05" for a run of 3 or more consecutive numbers, else the ids; unknown ones keep a "?" */
  function planDeps(deps, unknown) {
    var ids = (deps || []).slice(), out = [];
    var num = function (x) { return /^\d+$/.test(x) ? parseInt(x, 10) : null; };
    ids.sort(function (a, b) { var x = num(a), y = num(b); return x != null && y != null ? x - y : String(a).localeCompare(String(b)); });
    for (var i = 0; i < ids.length;) {
      var j = i;
      while (j + 1 < ids.length && num(ids[j]) != null && num(ids[j + 1]) === num(ids[j]) + 1) j++;
      if (j - i >= 2) out.push(ids[i] + "-" + ids[j]); else for (var k = i; k <= j; k++) out.push(ids[k]);
      i = j + 1;
    }
    return { text: out.join(", "), unknown: (unknown || []).map(function (u) { return u + "?"; }) };
  }
  function stateOf(r, goal) {
    var s = String(r.state || "");
    if (r.loop) return { cls: "fail", text: "loop" };
    if (r.passed) return { cls: "work", text: "passed" };
    var cls = goal ? (/^(building|checking|active|running|in|working)/.test(s) ? "run" : /^blocked/.test(s) ? "bad" : /^returned/.test(s) ? "fail" : "idle")
                   : (BOARD.taskStageClass ? BOARD.taskStageClass(s) : "idle");
    if (cls === "need") cls = "work";   /* passed is green here: mango means "needs the PO" and lives in the inbox panel */
    if (cls === "run") return { cls: "run", text: "▶ now" };
    return { cls: cls, text: s || "–" };
  }
  function over(r) { return typeof r.est_min === "number" && typeof r.spent_min === "number" && r.est_min > 0 && r.spent_min > OVER * r.est_min; }
  /* planModel(data) -> {goal, name, aim, aimClip, steps [{n, label, loop, rows, passed}], total, passedN, est, estUnset, spent, over, text} */
  function planModel(data) {
    var d = data || {}, goal = d.kind === "goal", rows = (d.rows || []).map(function (r) {
      var st = stateOf(r, goal), dp = planDeps(r.deps, r.unknown_deps);
      return { id: String(r.id), title: r.title || "", aim: r.aim || "", aimClip: r.aim ? clip(r.aim, AIM_MAX) : "–", est: fmtMin(r.est_min),
               estMin: typeof r.est_min === "number" ? r.est_min : null, spentMin: typeof r.spent_min === "number" ? r.spent_min : null,
               deps: (r.deps || []).map(String), depText: dp.text, unknownDeps: dp.unknown, waits: r.waits || "", over: over(r), cls: st.cls,
               stateText: st.text, passed: !!r.passed, loop: !!r.loop, step: r.step, spent: fmtMin(r.spent_min) };
    });
    var order = [], by = {};
    rows.forEach(function (r) {
      var k = r.loop ? "loop" : String(r.step || 1);
      if (!by[k]) { by[k] = { n: r.loop ? null : (r.step || 1), loop: r.loop, rows: [] }; order.push(k); }
      by[k].rows.push(r);
    });
    var steps = order.map(function (k) { return by[k]; });
    steps.sort(function (a, b) { return (a.loop ? 1e9 : a.n) - (b.loop ? 1e9 : b.n); });
    steps.forEach(function (s, i) {
      s.label = s.loop ? "STEP ? · loop" : (s.n === 1 ? "STEP 1 · can start now" : "STEP " + s.n + " · after step " + (s.n - 1));
      s.passed = s.rows.every(function (r) { return r.passed; });
      s.folded = s.passed && s.rows.length > 0 && steps.slice(i + 1).some(function (t) { return t.rows.some(function (r) { return !r.passed; }); });
    });
    var known = rows.filter(function (r) { return r.estMin != null; }), sp = rows.filter(function (r) { return r.spentMin != null; });
    var m = { goal: goal, name: d.name || "", aim: d.aim || "", aimClip: d.aim ? clip(d.aim, AIM_MAX) : "–", steps: steps, total: rows.length,
              passedN: rows.filter(function (r) { return r.passed; }).length, estUnset: rows.length - known.length };
    m.est = known.length ? known.reduce(function (a, r) { return a + r.estMin; }, 0) : null;
    m.spent = !goal && sp.length ? sp.reduce(function (a, r) { return a + r.spentMin; }, 0) : null;
    m.over = m.est != null && m.spent != null && m.est > 0 && m.spent > OVER * m.est;
    m.count = m.passedN + " of " + m.total;
    return m;
  }
  BOARD.planModel = planModel; BOARD.planDuration = fmtMin; BOARD.planDeps = planDeps;

  /* ---------- drawing ---------- */
  var OPEN = {}, LAST = null, wired = false;
  function el(tag, cls, text) {
    var e = root.document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function css() {
    if (root.document.getElementById("plan-css")) return;
    var s = el("style");
    s.id = "plan-css";
    s.textContent =
      ".pl-wrap{container:plan/inline-size}.pl .chip{align-items:center;justify-content:center;line-height:1;height:1.65em;box-sizing:border-box}" +
      ".pl .chip.run{background:var(--t-need2);border-color:var(--t-edge)}.pl .chip.work{background:var(--t-work);border-color:var(--work)}" +
      ".pl .chip.idle{background:var(--t-idle);border-color:var(--muted2);color:var(--muted)}.pl .chip.bad{background:var(--t-bad);border-color:var(--block)}" +
      ".pl .chip.fail{border-color:var(--fail);color:var(--fail)}.pl .chip.quiet{background:var(--t-amber);border-color:var(--amber);color:var(--amber)}" +
      ".pl .chip.wait{border-color:var(--wait);color:var(--wait)}" +
      ".pl-aim{margin:2px 0 4px}.pl-aim b{color:var(--muted);font-weight:600;margin-right:4px}" +
      ".pl-prog{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:0 0 6px}.pl-bar{flex:0 1 14em;min-width:6em;height:8px;border-radius:4px;background:var(--t-idle);overflow:hidden}" +
      ".pl-bar i{display:block;height:100%;background:var(--work)}" +
      ".pl-t{width:100%;border-collapse:collapse}.pl-t td{padding:4px 8px 4px 0;border-bottom:1px solid var(--border);vertical-align:top}" +
      ".pl-step td{position:sticky;top:0;z-index:1;background:var(--bg);font-size:.92em;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);font-weight:600;padding:6px 0 2px;cursor:default}" +
      ".pl-step.fold td{cursor:pointer}.pl-step button{border:0;background:none;padding:0;font:inherit;color:inherit;text-transform:inherit;letter-spacing:inherit;cursor:pointer}" +
      ".pl-r{cursor:default}.pl-r td:first-child{padding-left:6px}.pl-r.pl-hov td{box-shadow:none}.pl-r.pl-hov td:first-child,.pl-r:focus td:first-child{box-shadow:inset 3px 0 var(--ink)}" +
      ".pl-r.pl-dep td{background:var(--t-idle)}.pl-id{font-weight:700;white-space:nowrap}.pl-dp,.pl-est{white-space:nowrap}.pl-dp{color:var(--muted)}.pl-est{text-align:right}" +
      ".pl-t td:nth-child(2){min-width:9em}.pl-tt{font-weight:700;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere}" +
      ".pl-sp{color:var(--muted);font-size:.92em}.pl-a{font-size:.92em;max-width:15em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.pl-a2{display:none;color:var(--muted);font-size:.92em}" +
      ".pl-t.goal .pl-dp{white-space:normal;min-width:7em}.pl-st{white-space:nowrap}.pl-st .chip{margin:0 2px 2px 0}.pl-r.done td{color:var(--muted)}" +
      "@container plan (max-width:560px){.pl-a{display:none}.pl-a2{display:block}}";
    root.document.head.appendChild(s);
  }
  function chip(cls, text) { return el("span", "chip " + cls, text); }

  function stepRows(tb, s, m) {
    s.rows.forEach(function (r) {
      var tr = el("tr", "pl-r" + (r.passed ? " done" : "")); tr.tabIndex = 0; tr.setAttribute("data-id", r.id); tr.setAttribute("data-deps", r.deps.join(" "));
      tr.appendChild(el("td", "pl-id", r.id));
      var tt = el("td"), t = el("div", "pl-tt", r.title || (m.goal ? "" : "–")); if (r.title) t.title = r.title;
      tt.appendChild(t);
      if (r.waits) { var w = chip("wait", "waits: " + clip(r.waits, 40)); w.title = "waits: " + r.waits; tt.appendChild(w); }
      var a2 = el("div", "pl-a2", r.aimClip); if (r.aim) a2.title = r.aim; tt.appendChild(a2);
      if (r.over) tt.appendChild(el("div", "pl-sp", "est " + r.est + " · spent " + r.spent));
      tr.appendChild(tt);
      var dp = el("td", "pl-dp");
      var unk = m.goal ? [] : r.unknownDeps;   /* a goal's outside waits show as the "waits:" chip, in the words of goal.md */
      if (r.depText || unk.length) {
        dp.appendChild(root.document.createTextNode("← " + r.depText));
        unk.forEach(function (u, i) { var x = el("span", "muted", (r.depText || i ? ", " : "") + u); x.title = "no such task"; dp.appendChild(x); });
      } else dp.textContent = "–";
      tr.appendChild(dp);
      var a = el("td", "pl-a", r.aimClip); if (r.aim) a.title = r.aim; tr.appendChild(a);
      tr.appendChild(el("td", "pl-est", r.est));
      var st = el("td", "pl-st"); st.appendChild(chip(r.cls, r.stateText));
      if (r.over) st.appendChild(chip("quiet", "over estimate"));
      tr.appendChild(st);
      tb.appendChild(tr);
    });
  }

  function draw() {
    if (!LAST) return;
    var body = LAST.body, c = LAST.c, m = planModel(LAST.d);
    css();
    body.textContent = "";
    var h2 = body.closest && body.closest(".panel") ? body.closest(".panel").querySelector(".ph h2") : null;
    if (h2) {   /* the home's name, muted, next to the title */
      var old = h2.querySelector(".pl-home"); if (old) old.remove();
      if (m.name) { h2.appendChild(root.document.createTextNode(" ")); h2.appendChild(el("span", "pl-home muted", m.name)); }
    }
    if (c.setCount) c.setCount(m.count, false);
    if (!m.total) {
      body.appendChild(el("p", "note pstate", "Nothing planned yet. Rows appear when " + (m.goal ? "the scope table in goal.md." : "the Manager writes tasks/NN.md.")));
      return;
    }
    var wrap = el("div", "pl-wrap pl"), a = el("p", "pl-aim"), a1 = el("b", null, "Aim:");
    a.appendChild(a1); var at = el("span", null, m.aimClip); if (m.aim) at.title = m.aim; a.appendChild(at); wrap.appendChild(a);
    var pg = el("div", "pl-prog"), bar = el("div", "pl-bar"), fill = el("i");
    bar.setAttribute("role", "progressbar"); bar.setAttribute("aria-valuemin", "0"); bar.setAttribute("aria-valuemax", String(m.total));
    bar.setAttribute("aria-valuenow", String(m.passedN)); bar.setAttribute("aria-label", "passed");
    fill.style.width = Math.round(100 * m.passedN / m.total) + "%"; bar.appendChild(fill); pg.appendChild(bar);
    var line = m.passedN + " of " + m.total + (m.goal ? " scopes" : "") + " passed · est " + fmtMin(m.est);
    if (!m.goal) line += " · spent " + fmtMin(m.spent);
    var lt = el("span", "pl-line", line);
    if (m.estUnset && m.est != null) lt.appendChild(el("span", "muted", " · " + m.estUnset + " not set"));
    pg.appendChild(lt);
    if (m.over) pg.appendChild(chip("quiet", "over estimate"));
    wrap.appendChild(pg);
    var tbl = el("table", "pl-t" + (m.goal ? " goal" : "")), tb = el("tbody");
    m.steps.forEach(function (s, i) {
      var key = s.loop ? "loop" : String(s.n), folded = s.folded && !OPEN[key];
      var hr = el("tr", "pl-step" + (s.folded ? " fold" : "")), hd = el("td"); hd.colSpan = 6;
      if (s.folded) {
        var b = el("button", null, s.label + " · " + s.rows.length + " passed " + (folded ? "▸" : "▾")); b.type = "button";
        b.setAttribute("data-step", key); b.setAttribute("aria-expanded", folded ? "false" : "true"); hd.appendChild(b);
      } else hd.textContent = s.label;
      hr.appendChild(hd); tb.appendChild(hr);
      if (!folded) stepRows(tb, s, m);
    });
    tbl.appendChild(tb); wrap.appendChild(tbl); body.appendChild(wrap);
  }

  function mark(tr, on) {
    var table = tr.closest("table"), id = tr.getAttribute("data-id");
    Array.prototype.forEach.call(table.querySelectorAll("tr.pl-r"), function (x) {
      var blocks = on && (x.getAttribute("data-deps") || "").split(" ").indexOf(id) >= 0;
      x.classList.toggle("pl-dep", !!blocks);
    });
    tr.classList.toggle("pl-hov", on);
  }
  function wire(body) {
    if (wired) return;
    wired = true;
    var row = function (e) { return e.target.closest && e.target.closest("tr.pl-r"); };
    body.addEventListener("mouseover", function (e) { var r = row(e); if (r) mark(r, true); });
    body.addEventListener("mouseout", function (e) { var r = row(e); if (r) mark(r, false); });
    body.addEventListener("focusin", function (e) { var r = row(e); if (r) mark(r, true); });
    body.addEventListener("focusout", function (e) { var r = row(e); if (r) mark(r, false); });
    body.addEventListener("click", function (e) {
      var b = e.target.closest && e.target.closest("button[data-step]");
      if (b) { var k = b.getAttribute("data-step"); OPEN[k] = !OPEN[k]; draw(); }
    });
  }

  BOARD.registerPanel({
    id: "plan", title: "Plan", route: "/api/plan", maxPx: 620,
    isEmpty: function (d) { return !d; },
    render: function (body, d, c) {
      LAST = { body: body, d: d, c: c };
      wire(body);
      draw();
    }
  });
})(typeof window !== "undefined" ? window : this);
