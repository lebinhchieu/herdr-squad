(function () {
  "use strict";
  var D = JSON.parse(document.getElementById("data").textContent);
  var app = document.getElementById("app");
  var BK = ["working", "waiting", "blocking", "idle"], KINDS = ["input", "cache_read", "cache_write", "output"];
  var PAL = ["#E8820E", "#0C8A80", "#2A6DC0", "#9A40CF", "#368A1E", "#CE1D6C", "#9E7A00", "#DB3B22"];
  var INC = ["done", "running", "stale"];
  var CHIP = { done: ["done", "done"], running: ["running · partial", "run"], stale: ["stale", "warn"], no_data: ["no data", "bad"],
    schema_mismatch: ["old schema", "bad"], skipped: ["skipped", ""], unreadable: ["unreadable", "bad"] };

  function h(tag, attrs) {
    var e = document.createElement(tag), i, c;
    for (var k in (attrs || {})) {
      if (k === "class") e.className = attrs[k];
      else if (k === "title") e.title = attrs[k];
      else e.setAttribute(k, attrs[k]);
    }
    for (i = 2; i < arguments.length; i++) {
      c = arguments[i];
      if (c === null || c === undefined || c === false) continue;
      if (Array.isArray(c)) c.forEach(function (x) { if (x) e.appendChild(typeof x === "object" ? x : document.createTextNode(String(x))); });
      else e.appendChild(typeof c === "object" ? c : document.createTextNode(String(c)));
    }
    return e;
  }
  function dur(s) { if (s == null) return "–"; s = Math.round(s); if (s < 60) return s + "s"; var m = Math.round(s / 60); if (m < 60) return m + "m";
    var hh = Math.floor(m / 60), mm = m % 60; if (hh < 48) return hh + "h" + (mm ? " " + mm + "m" : ""); return Math.floor(hh / 24) + "d " + (hh % 24) + "h"; }
  function usd(x) { return x == null ? "–" : "$" + (x >= 100 ? Math.round(x) : x.toFixed(2)); }
  function tok(n) { if (n == null) return "–"; if (n >= 1e9) return (n / 1e9).toFixed(2) + "B"; if (n >= 1e6) return (n / 1e6).toFixed(1) + "M"; if (n >= 1e3) return Math.round(n / 1e3) + "k"; return String(n); }
  function sum(o) { return Object.keys(o).reduce(function (a, k) { return a + o[k]; }, 0); }
  function pc(x) { return x == null ? "–" : Math.round(x * 100) + "%"; }
  function name(r) { return h("span", null, r.name, r.squad ? h("span", { class: "mut" }, " · " + r.squad) : null); }
  function key(r) { return r.squad + "/" + r.name; }
  function chip(r) { var c = CHIP[r.status] || [r.status, ""]; var t = c[0];
    if (r.status === "stale" && r.age_s != null) t += " · " + dur(r.age_s) + " old";
    return h("span", { class: "chip " + c[1] }, t); }
  function banner(cls, ic, head, text, cmd) { return h("div", { class: "banner " + cls }, h("span", { class: "ic" }, ic), h("div", null, h("b", null, head + " "), text, cmd ? [" ", h("code", null, cmd)] : null)); }
  function link(r) {
    if (r.report_href) { var a = h("a", { title: r.report_href }, "open report →"); a.setAttribute("href", r.report_href); return a; }
    return h("span", { class: "faint", title: "built from a data.json file: no report.html beside it" }, "no report");
  }

  var rows = D.scopes, inc = rows.filter(function (r) { return INC.indexOf(r.status) >= 0; }), T = D.totals;
  var color = {}; rows.forEach(function (r, i) { color[key(r) + "|" + i] = PAL[i % PAL.length]; });
  function col(r) { return PAL[rows.indexOf(r) % PAL.length]; }

  /* ---- drawer ---- */
  var drawer = h("aside", { id: "drawer", "aria-label": "Scope details" });
  function bars(map, keys, cls) { var tot = sum(map) || 1;
    return h("div", { class: "bar" }, keys.map(function (k) { var i = h("i", { class: cls + k, title: k + " " + pc(map[k] / tot) }); i.style.width = (map[k] / tot * 100).toFixed(2) + "%"; return i; })); }
  function openDrawer(r) {
    drawer.textContent = "";
    var x = h("button", { class: "x", "aria-label": "Close" }, "×"); x.onclick = function () { drawer.classList.remove("open"); };
    drawer.appendChild(x); drawer.appendChild(h("h2", null, name(r))); drawer.appendChild(h("p", null, chip(r), " ", r.size ? "size " + r.size : ""));
    if (INC.indexOf(r.status) < 0) {
      drawer.appendChild(h("p", null, r.reason || ""));
      if (r.command) { drawer.appendChild(h("p", null, "Create it: ", h("code", null, r.command))); if (D.form === "goal") drawer.appendChild(h("p", null, "Then: ", h("code", null, "squad-report " + D.title))); }
      if (r.source) drawer.appendChild(h("p", { class: "mut" }, "File: " + r.source));
    } else {
      var t = r.totals, att = t.attributed_time_pct;
      drawer.appendChild(h("p", { class: "mut" }, "Elapsed " + dur(t.wall_s) + " · agent-time " + dur(t.agent_s) + " · cost " + usd(t.cost_usd) + " · tokens " + tok(sum(t.tokens))));
      drawer.appendChild(bars(t.buckets_s, BK, "b-")); drawer.appendChild(h("div", { style: "height:6px" })); drawer.appendChild(bars(t.tokens, KINDS, "k-"));
      drawer.appendChild(h("p", null, "Tasks passed " + t.passed + "/" + t.tasks + " · returns (FAIL messages) " + t.returns + " · PO wait " + dur(t.po_wait_s) + " · attributed " + (att == null ? "–" : att + "%")));
      if (r.redacted) drawer.appendChild(h("p", { class: "mut" }, "Not shared: task titles and return reasons."));
      var rt = h("table", null, h("thead", null, h("tr", null, h("th", null, "Role"), h("th", { class: "num" }, "Cost"), h("th", { class: "num" }, "Agent-time"))),
        h("tbody", null, r.roles.map(function (q) { return h("tr", null, h("td", null, q.role), h("td", { class: "num" }, usd(q.cost_usd)), h("td", { class: "num" }, dur(q.agent_s))); })));
      drawer.appendChild(h("div", { class: "tw" }, rt));
      if (r.report_href) drawer.appendChild(link(r));
    }
    drawer.classList.add("open");
  }
  function drawerByKey(k) { var r = rows.filter(function (q) { return key(q) === k; })[0]; if (r) openDrawer(r); }

  /* ---- sections ---- */
  function kpi(l, v, s, cls) { return h("div", { class: "card kpi " + (cls || "") }, h("div", { class: "l" }, l), h("div", { class: "v" }, v), h("div", { class: "s" }, s)); }
  function overview() {
    var empty = !inc.length, att = T.attributed_time_pct;
    var cards = [
      kpi("Calendar span", empty ? "–" : dur(T.span_s), empty ? "" : "agent-time " + dur(T.agent_s) + (T.parallelism ? " · ×" + T.parallelism + " parallel" : "")),
      kpi("Cost (est.)", empty ? "–" : usd(T.cost_usd), empty || T.cost_per_passed_task_usd == null ? "" : usd(T.cost_per_passed_task_usd) + " per passed task"),
      kpi("Tokens", empty ? "–" : tok(sum(T.tokens)), empty ? "" : "output " + tok(T.tokens.output)),
      kpi("Returns (FAIL messages)", empty ? "–" : String(T.returns), empty ? "" : T.flagged_tasks + " flagged task" + (T.flagged_tasks === 1 ? "" : "s"), T.flagged_tasks ? "bad" : ""),
      kpi("PO wait (summed)", empty ? "–" : dur(T.po_wait_s), "elapsed, not cost"),
      kpi("Attributed", empty ? "–" : (att == null ? "–" : att + "%"), empty ? "" : T.under_60 + " scope" + (T.under_60 === 1 ? "" : "s") + " under 60%", T.under_60 ? "warn" : "")
    ];
    var s = h("section", { id: "overview" }, h("div", { class: "sh" }, h("h2", null, "Overview"), h("span", { class: "sub" }, "included scopes only: " + T.included + " of " + T.listed)), h("div", { class: "kpis" }, cards));
    if (D.digest.length) s.appendChild(h("div", null, h("h3", { style: "margin-top:14px" }, "Worth a look"),
      h("div", { class: "digest" }, D.digest.slice(0, 4).map(function (d, i) { var b = h("button", { class: "dg" }, h("span", { class: "n" }, i + 1), h("span", { class: "t" }, d.text)); b.onclick = function () { drawerByKey(d.target.id); }; return b; }))));
    return s;
  }
  var COLS = [
    { k: "name", label: "Scope", val: function (r) { return r.name.toLowerCase(); }, fmt: function (r) { return h("span", null, h("i", { class: "sc-sw", style: "background:" + col(r) }), r.report_href ? name(r) : name(r)); } },
    { k: "status", label: "Status", val: function (r) { return r.status; }, fmt: function (r) { return INC.indexOf(r.status) >= 0 ? chip(r) : h("span", null, chip(r), " ", h("span", { class: "mut" }, r.reason)); } },
    { k: "wall", label: "Elapsed", num: 1, val: function (r) { return r.totals ? r.totals.wall_s : -1; }, fmt: function (r) { return r.totals ? dur(r.totals.wall_s) : "–"; } },
    { k: "agent", label: "Agent-time", num: 1, val: function (r) { return r.totals ? r.totals.agent_s : -1; }, fmt: function (r) { return r.totals ? h("span", null, bars(r.totals.buckets_s, BK, "b-"), " ", dur(r.totals.agent_s)) : "–"; } },
    { k: "cost", label: "Cost", num: 1, val: function (r) { return r.totals ? r.totals.cost_usd : -1; }, fmt: function (r) { return r.totals ? usd(r.totals.cost_usd) + (T.cost_usd ? " (" + pc(r.totals.cost_usd / T.cost_usd) + ")" : "") : "–"; } },
    { k: "tokens", label: "Tokens", num: 1, val: function (r) { return r.totals ? sum(r.totals.tokens) : -1; }, fmt: function (r) { return r.totals ? tok(sum(r.totals.tokens)) : "–"; } },
    { k: "tasks", label: "Tasks passed", num: 1, val: function (r) { return r.totals ? r.totals.passed : -1; }, fmt: function (r) { return r.totals ? r.totals.passed + "/" + r.totals.tasks : "–"; } },
    { k: "ret", label: "Returns (FAIL)", num: 1, val: function (r) { return r.totals ? r.totals.returns : -1; }, fmt: function (r) { if (!r.totals) return "–"; var n = r.totals.returns; return h("span", { class: "ret " + (r.totals.flagged_tasks ? "r3" : n ? "r1" : "") }, n + (r.totals.flagged_tasks ? " ⚑" : "")); } },
    { k: "po", label: "PO wait", num: 1, val: function (r) { return r.totals ? r.totals.po_wait_s : -1; }, fmt: function (r) { return r.totals ? dur(r.totals.po_wait_s) : "–"; } },
    { k: "att", label: "Attributed", num: 1, val: function (r) { return r.totals && r.totals.attributed_time_pct != null ? r.totals.attributed_time_pct : -1; }, fmt: function (r) { var p = r.totals && r.totals.attributed_time_pct; if (p == null) return "–"; return h("span", { style: p < 60 ? "color:var(--mango-d);font-weight:700" : "" }, p + "%"); } },
    { k: "rep", label: "Report", val: function (r) { return r.report_href ? 1 : 0; }, fmt: function (r) { return INC.indexOf(r.status) >= 0 ? link(r) : "–"; } }
  ];
  function scopesSection() {
    var sk = "cost", desc = true, fText = "", fStatus = "", fSize = "";
    var host = h("div"), q = h("input", { type: "search", placeholder: "Filter scope or squad", "aria-label": "Filter" });
    var st = h("select", { "aria-label": "Status" }, h("option", { value: "" }, "All statuses"), h("option", { value: "done" }, "done"), h("option", { value: "running" }, "running"), h("option", { value: "out" }, "not included"));
    var sizes = {}; rows.forEach(function (r) { if (r.size) sizes[r.size] = 1; });
    var sz = h("select", { "aria-label": "Size" }, h("option", { value: "" }, "All sizes"), Object.keys(sizes).sort().map(function (s) { return h("option", { value: s }, s); }));
    function draw() {
      var list = rows.filter(function (r) {
        if (fText && (r.name + " " + r.squad).toLowerCase().indexOf(fText) < 0) return false;
        if (fStatus === "out" ? INC.indexOf(r.status) >= 0 : fStatus && r.status !== fStatus) return false;
        return !fSize || r.size === fSize;
      });
      var c = COLS.filter(function (x) { return x.k === sk; })[0];
      list.sort(function (a, b) { var x = c.val(a), y = c.val(b); return (x > y ? 1 : x < y ? -1 : 0) * (desc ? -1 : 1); });
      host.textContent = "";
      if (!list.length) { host.appendChild(h("div", { class: "empty" }, h("b", null, rows.length ? "No scope matches the filter." : "Nothing to show."), rows.length ? "Clear the filter." : "No scopes were given.")); return; }
      var head = h("tr", null, COLS.map(function (x) { var th = h("th", { class: x.num ? "num" : "", tabindex: "0" }, x.label); if (x.k === sk) th.setAttribute("aria-sort", desc ? "descending" : "ascending");
        var go = function () { if (sk === x.k) desc = !desc; else { sk = x.k; desc = !!x.num; } draw(); }; th.onclick = go; th.onkeydown = function (e) { if (e.key === "Enter") go(); }; return th; }));
      var body = list.map(function (r) { var tr = h("tr", { class: r.totals && r.totals.flagged_tasks ? "flag" : "", tabindex: "0" }, COLS.map(function (x) { var td = h("td", { class: x.num ? "num" : "" }, x.fmt(r)); if (x.k === "rep") td.onclick = function (e) { e.stopPropagation(); }; return td; }));
        tr.onclick = function () { openDrawer(r); }; tr.onkeydown = function (e) { if (e.key === "Enter") openDrawer(r); }; return tr; });
      var foot = h("tr", null, h("td", null, "Total · " + T.included + " of " + T.listed), h("td"), h("td", { class: "num" }, dur(T.span_s)), h("td", { class: "num" }, dur(T.agent_s)), h("td", { class: "num" }, usd(T.cost_usd)),
        h("td", { class: "num" }, tok(sum(T.tokens))), h("td", { class: "num" }, T.passed + "/" + T.tasks), h("td", { class: "num" }, String(T.returns)), h("td", { class: "num" }, dur(T.po_wait_s)),
        h("td", { class: "num" }, T.attributed_time_pct == null ? "–" : T.attributed_time_pct + "%"), h("td"));
      host.appendChild(h("div", { class: "tw" }, h("table", null, h("thead", null, head), h("tbody", null, body), h("tfoot", null, foot))));
    }
    q.oninput = function () { fText = q.value.toLowerCase(); draw(); }; st.onchange = function () { fStatus = st.value; draw(); }; sz.onchange = function () { fSize = sz.value; draw(); };
    draw();
    return h("section", { id: "scopes" }, h("div", { class: "sh" }, h("h2", null, "Scopes"), h("span", { class: "tools" }, q, st, sz)), host);
  }
  function stacked(title, get, fmt) {
    var tot = 0, items = inc.filter(function (r) { return get(r) > 0; }); items.forEach(function (r) { tot += get(r); });
    var card = h("div", { class: "card" }, h("h3", null, title));
    if (!tot) { card.appendChild(h("div", { class: "empty" }, "Nothing to show.")); return card; }
    card.appendChild(h("div", { class: "seg-bar" }, items.map(function (r) { var i = h("i", { title: label(r) + ": " + fmt(get(r)) + " (" + pc(get(r) / tot) + ")" }); i.style.width = (get(r) / tot * 100).toFixed(2) + "%"; i.style.background = col(r); return i; })));
    card.appendChild(h("div", { class: "legend" }, items.map(function (r) { return h("span", null, h("i", { class: "sw", style: "background:" + col(r) }), label(r) + " " + pc(get(r) / tot)); })));
    return card;
  }
  function label(r) { return r.name + (r.squad ? " · " + r.squad : ""); }
  function share() {
    return h("section", { id: "share" }, h("div", { class: "sh" }, h("h2", null, "Share"), h("span", { class: "sub" }, "one colour per scope")),
      h("div", { class: "two" }, stacked("Cost", function (r) { return r.totals.cost_usd; }, usd), stacked("Agent-time", function (r) { return r.totals.agent_s; }, dur), stacked("Returns", function (r) { return r.totals.returns; }, String)));
  }
  function rolesSection() {
    var metric = "cost", host = h("div");
    var sel = h("select", { "aria-label": "Metric" }, h("option", { value: "cost" }, "Cost"), h("option", { value: "time" }, "Agent-time"), h("option", { value: "tokens" }, "Tokens"));
    function get(q) { return metric === "cost" ? q.cost_usd : metric === "time" ? q.agent_s : q.tokens; }
    function f(v) { return metric === "cost" ? usd(v) : metric === "time" ? dur(v) : tok(v); }
    function draw() {
      host.textContent = "";
      var names = D.roles.map(function (r) { return r.role; });
      if (!names.length || !inc.length) { host.appendChild(h("div", { class: "empty" }, h("b", null, "Nothing to show."))); return; }
      var max = 0; inc.forEach(function (r) { r.roles.forEach(function (q) { max = Math.max(max, get(q)); }); });
      var head = h("tr", null, h("th", { class: "rl" }, "Role"), inc.map(function (r) { return h("th", { title: label(r) }, h("i", { class: "sc-sw", style: "background:" + col(r) }), r.name); }), h("th", null, "Total"));
      var body = names.map(function (n) { var tot = D.roles.filter(function (r) { return r.role === n; })[0];
        return h("tr", null, h("td", { class: "rl" }, n), inc.map(function (r) { var q = r.roles.filter(function (z) { return z.role === n; })[0], v = q ? get(q) : 0;
          var td = h("td", { class: "cell" + (v ? "" : " zero") }, v ? f(v) : "–"); if (v) { td.style.background = "rgba(232,130,14," + (0.08 + 0.4 * v / (max || 1)).toFixed(2) + ")"; td.onclick = function () { openDrawer(r); }; } return td; }), h("td", { class: "cell" }, f(get(tot)))); });
      host.appendChild(h("div", { class: "tw" }, h("table", { class: "mx" }, h("thead", null, head), h("tbody", null, body))));
    }
    sel.onchange = function () { metric = sel.value; draw(); }; draw();
    return h("section", { id: "roles" }, h("div", { class: "sh" }, h("h2", null, "Roles"), h("span", { class: "tools" }, sel)), host);
  }

  /* ---- page ---- */
  function page() {
    var goal = D.form === "goal";
    var header = h("header", { class: "page" }, h("div", null, h("h1", null, D.title), h("div", { class: "mut" }, T.listed + " listed · " + T.included + " included")),
      h("span", { class: "chip" }, goal ? "goal rollup" : "from files"), h("span", { class: "chip " + (T.partial ? "warn" : "done") }, T.partial ? "partial" : "complete"),
      h("div", { class: "meta" }, "generated " + D.generated_at));
    app.appendChild(header);
    var bad = rows.filter(function (r) { return r.status === "schema_mismatch" || r.status === "unreadable"; });
    if (!inc.length && bad.length) {
      app.appendChild(h("div", { class: "errbox card" }, h("h2", null, "No file could be read"), h("p", null, bad[0].reason), h("p", null, "Check the file was written by ", h("code", null, "squad-report <scope>"), " (kind scope, schema_version 1), then run the rollup again.")));
      return;
    }
    var main = h("main");
    if (!inc.length) main.appendChild(banner("info", "i", "Nothing to roll up.", D.form === "goal" ? "No scope of this goal has a data.json. Run" : "No scope data.json was given. Run", D.form === "goal" ? "squad-report <scope>" : "squad-report rollup <data.json>..."));
    if (T.mixed_prices) main.appendChild(banner("info", "i", "Mixed price tables.", "These scopes were priced with different squad price settings. Each cost is that scope's own estimate, summed as is."));
    var out = rows.filter(function (r) { return INC.indexOf(r.status) < 0; });
    if (out.length) main.appendChild(banner("", "!", "Totals are partial.", "Left out: " + out.map(function (r) { return label(r) + " (" + r.status + ")"; }).join(", ") + "."));
    var run = rows.filter(function (r) { return r.status === "running"; });
    if (run.length) main.appendChild(banner("info", "i", "Still running.", run.map(label).join(", ") + " is included as it stands now."));
    var stale = rows.filter(function (r) { return r.status === "stale"; });
    if (stale.length) main.appendChild(banner("", "!", "Stale data.", stale.map(label).join(", ") + " changed after its data.json was written. Re-run", "squad-report <scope>"));
    var nav = h("nav", { class: "sections" }, ["overview", "scopes", "share", "roles"].map(function (s) { return h("a", { href: "#" + s }, s.charAt(0).toUpperCase() + s.slice(1)); }));
    app.appendChild(nav);
    main.appendChild(overview()); main.appendChild(scopesSection()); main.appendChild(share()); main.appendChild(rolesSection());
    app.appendChild(main);
  }
  page();
  document.body.appendChild(drawer);
})();
