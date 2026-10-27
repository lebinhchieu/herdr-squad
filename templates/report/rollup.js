(function () {
  "use strict";
  var D = JSON.parse(document.getElementById("data").textContent);
  var app = document.getElementById("app");
  var BK = ["working", "waiting", "blocking", "idle"], KINDS = ["input", "cache_read", "cache_write", "output"];
  var BL = { working: "Working", waiting: "Waiting (long tool call or background job)", blocking: "Blocking (waiting on a reply or the PO)",
    idle: "Idle (waiting for work, or for the PO's chat reply)" };
  var KL = { input: "Input", cache_read: "Cache read", cache_write: "Cache write", output: "Output" };
  var PAL = ["#E8820E", "#0C8A80", "#2A6DC0", "#9A40CF", "#CE1D6C", "#368A1E", "#9E7A00", "#857A68", "#CE7000", "#4A8FE0"];
  var INC = ["done", "running", "stale"];
  var CHIP = { done: ["done", "done"], running: ["running · partial", "run"], stale: ["stale", "warn"], no_data: ["no data", "bad"],
    schema_mismatch: ["old schema", "bad"], skipped: ["skipped", ""], unreadable: ["unreadable", "bad"] };

  function add(e, c) {
    if (c === null || c === undefined || c === false) return;
    if (Array.isArray(c)) c.forEach(function (x) { add(e, x); });
    else e.appendChild(typeof c === "object" ? c : document.createTextNode(String(c)));
  }
  function h(tag, attrs) {
    var e = document.createElement(tag), i;
    for (var k in (attrs || {})) {
      if (k === "class") e.className = attrs[k];
      else if (k === "title") e.title = attrs[k];
      else if (attrs[k] !== null) e.setAttribute(k, attrs[k]);
    }
    for (i = 2; i < arguments.length; i++) add(e, arguments[i]);
    return e;
  }
  function dur(s) { if (s == null) return "–"; s = Math.round(s); if (s < 60) return s + "s"; var m = Math.round(s / 60); if (m < 60) return m + "m";
    var hh = Math.floor(m / 60), mm = m % 60; if (hh < 48) return hh + "h" + (mm ? " " + mm + "m" : ""); return Math.floor(hh / 24) + "d " + (hh % 24) + "h"; }
  function usd(x) { return x == null ? "–" : "$" + (x >= 100 ? Math.round(x).toLocaleString("en") : x.toFixed(2)); }
  function tok(n) { if (n == null) return "–"; if (n >= 1e9) return (n / 1e9).toFixed(2) + "B"; if (n >= 1e6) return (n / 1e6).toFixed(1) + "M"; if (n >= 1e3) return Math.round(n / 1e3) + "k"; return String(n); }
  function sum(o) { return Object.keys(o).reduce(function (a, k) { return a + o[k]; }, 0); }
  function pc(x) { return x == null ? "–" : Math.round(x * 100) + "%"; }
  function ts(s) { var t = s ? Date.parse(s) : NaN; return isNaN(t) ? null : t / 1000; }
  function dt(t) { return t == null ? "–" : new Date(t * 1000).toLocaleString("en-GB", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "UTC" }) + " UTC"; }
  function label(r) { return r.name + (r.squad ? " · " + r.squad : ""); }
  function nm(r) { return h("span", null, r.name, r.squad ? h("span", { class: "faint" }, " · " + r.squad) : null); }
  function chip(r) { var c = CHIP[r.status] || [r.status, ""]; return h("span", { class: "chip " + c[1] }, c[0]); }
  function staleS(r) { var g = ts(r.generated_at), l = ts(r.last_message_at); return g != null && l != null && l > g ? l - g : r.age_s; }
  function banner(cls, ic, head, parts) {
    return h("div", { class: "banner " + cls, role: cls === "bad" ? "alert" : "status" }, h("span", { class: "ic" }, ic), h("div", null, h("b", null, head), " ", parts));
  }
  function names(list) { var out = []; list.forEach(function (r, i) { if (i) out.push(", "); out.push(h("b", null, r.name)); return r; }); return out; }
  function link(r, text, cls, hash) {
    var a = h("a", { title: r.report_href, class: cls || "" }, text); a.setAttribute("href", r.report_href + (hash || "")); return a;
  }
  function noReport(r) {
    return h("span", { class: "faint", "data-tip": r.status === "no_data" ? "no data.json" : r.source ? "built from a data.json file: no report.html beside it" : (r.reason || "no report") }, "no report");
  }
  function bar(map, keys, cls, lg) {
    var tot = sum(map) || 1;
    return h("div", { class: "bar" + (lg ? " lg" : ""), role: "img", "aria-label": keys.map(function (k) { return k + " " + pc(map[k] / tot); }).join(", ") },
      keys.map(function (k) {
        var i = h("i", { class: cls + k, "data-tip": (cls === "b-" ? BL[k] + ": " + dur(map[k]) : KL[k] + ": " + tok(map[k])) + " (" + pc(map[k] / tot) + ")" });
        i.style.width = (map[k] / tot * 100).toFixed(2) + "%"; return i;
      }));
  }
  function legend(keys, cls, labels) { return h("div", { class: "legend" }, keys.map(function (k) { return h("span", null, h("i", { class: "sw " + cls + k }), labels[k]); })); }
  function empty(head, text) { return h("div", { class: "empty" }, head ? h("b", null, head) : null, text); }

  var rows = D.scopes, T = D.totals, GOAL = D.form === "goal";
  var inc = rows.filter(function (r) { return INC.indexOf(r.status) >= 0; });
  function isInc(r) { return INC.indexOf(r.status) >= 0; }
  function col(r) { return PAL[rows.indexOf(r) % PAL.length]; }
  function swatch(r) { var s = h("span", { class: "sw" }); s.style.background = col(r); s.style.marginRight = "6px"; return s; }

  /* ---- tooltip, drawer ---- */
  var tip = h("div", { id: "tip" });
  document.addEventListener("mousemove", function (e) {
    var t = e.target.closest && e.target.closest("[data-tip]");
    if (!t) { tip.style.display = "none"; return; }
    tip.textContent = t.getAttribute("data-tip"); tip.style.display = "block";
    tip.style.left = Math.min(e.clientX + 12, innerWidth - 310) + "px"; tip.style.top = (e.clientY + 14) + "px";
  });
  var drawer = h("aside", { id: "drawer", "aria-label": "Details", tabindex: "-1" });
  function closeDrawer() { drawer.classList.remove("open"); Array.prototype.forEach.call(document.querySelectorAll("tr.sel"), function (x) { x.classList.remove("sel"); }); }
  function openDrawer(nodes) {
    drawer.textContent = "";
    var x = h("button", { class: "x", "aria-label": "Close" }, "×"); x.onclick = closeDrawer;
    drawer.appendChild(x); nodes.forEach(function (n) { if (n) drawer.appendChild(n); });
    drawer.classList.add("open"); drawer.focus();
  }
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeDrawer(); });
  function jump(id) { var e = document.getElementById(id); if (!e) return; e.scrollIntoView({ block: "start" }); e.classList.remove("flash"); void e.offsetWidth; e.classList.add("flash"); }

  function pre(text) { return h("pre", { class: "mut", style: "background:var(--panel);border:1px solid var(--bd);border-radius:8px;padding:10px;font-size:12.5px" }, text); }
  function openScope(r, tr) {
    Array.prototype.forEach.call(document.querySelectorAll("#scopetbl tr.sel"), function (x) { x.classList.remove("sel"); });
    if (tr) tr.classList.add("sel");
    var head = h("h2", null, swatch(r), nm(r), " ", chip(r));
    if (!isInc(r)) {
      var skipped = r.status === "skipped";
      var nodes = [head, h("div", { class: "empty" }, h("b", null, r.reason || ""), skipped ? "This scope is left out of the totals and stays listed so the gap is visible." : "Not in the totals. Build its data, then rebuild this rollup:")];
      if (!skipped) nodes.push(pre((r.command || "squad-report " + r.name) + (GOAL ? "\nsquad-report " + D.title : "")));
      if (r.source) nodes.push(h("p", { class: "mut" }, "File: " + r.source));
      return openDrawer(nodes);
    }
    var t = r.totals, att = t.attributed_time_pct, w = r.window || {};
    var rs = r.roles.filter(function (q) { return q.cost_usd > 0; }).sort(function (a, b) { return b.cost_usd - a.cost_usd; });
    var gap = r.status === "stale" ? staleS(r) : null;
    openDrawer([head,
      h("div", { class: "mut" }, (r.team ? "team " + r.team : "size " + (r.size || "–")) + " · " + dt(ts(w.start)) + " → " + (r.status === "running" ? "now" : dt(ts(w.end)))),
      h("div", { class: "card", style: "margin-top:8px" }, h("b", null, dur(t.wall_s)), " elapsed · ", h("b", null, dur(t.agent_s)), " agent-time · ", h("b", null, usd(t.cost_usd)), " · ",
        h("b", null, tok(sum(t.tokens))), " tokens ", bar(t.buckets_s, BK, "b-", true), h("div", { style: "height:6px" }), bar(t.tokens, KINDS, "k-")),
      h("p", null, t.tasks + " tasks, " + t.passed + " passed · " + t.returns + " returns" + (t.flagged_tasks ? " (" + t.flagged_tasks + " flagged)" : "") + " · PO wait " + dur(t.po_wait_s) + " · " + (att == null ? "–" : Math.round(att) + "%") + " attributed"),
      h("h3", null, "By role"),
      h("div", { class: "tw" }, h("table", null, h("tbody", null, rs.map(function (q) {
        var b = h("div", { class: "bar" }, h("i")); b.firstChild.style.width = (t.cost_usd ? q.cost_usd / t.cost_usd * 100 : 0).toFixed(2) + "%"; b.firstChild.style.background = "var(--teal)";
        return h("tr", { style: "cursor:default" }, h("td", null, q.role), h("td", null, b), h("td", { class: "num" }, usd(q.cost_usd)), h("td", { class: "num" }, dur(q.agent_s)));
      })))),
      r.redacted ? h("p", { class: "mut" }, h("b", null, "Not shared:"), " task titles and return reasons (the file was written with --redact). Numbers are complete.") : null,
      r.status === "stale" ? banner("warn", "!", "Stale.", "data.json is " + dur(gap) + " older than the scope's last message.") : null,
      r.report_href ? h("div", { style: "display:flex;gap:8px" }, link(r, "Open full report →", "act")) : null]);
  }

  /* ---- sections ---- */
  function kpi(l, v, s, cls, extra) { return h("div", { class: "card kpi " + (cls || "") }, h("div", { class: "l" }, l), h("div", { class: "v" }, v), s ? h("div", { class: "s" }, s) : null, extra); }
  function digestItem(d) {
    var r = rows.filter(function (q) { return q.squad + "/" + q.name === d.target.id && isInc(q); })[0], t = r && r.totals, title = d.text, sub = "";
    if (r) {
      if (d.kind === "top_cost_scope") { title = label(r) + " is " + pc(d.value / 100) + " of cost"; sub = usd(t.cost_usd) + " · " + t.tasks + " tasks"; }
      else if (d.kind === "most_returns_scope") { title = label(r) + ": " + t.returns + " returns" + (t.flagged_tasks ? " (" + t.flagged_tasks + " flagged)" : "");
        sub = r.redacted ? h("i", null, "reasons not shared") : r.top_reason ? "“" + r.top_reason + "”" + (r.reasons_n > 1 ? " +" + (r.reasons_n - 1) + " more" : "") : ""; }
      else if (d.kind === "top_po_wait_scope") { title = "PO wait highest in " + label(r); sub = dur(t.po_wait_s) + " · " + pc(t.po_wait_s / (t.wall_s || 1)) + " of its elapsed"; }
      else if (d.kind === "weakest_attribution_scope") { title = "Weakest attribution: " + label(r) + ", " + Math.round(t.attributed_time_pct) + "%"; sub = t.attributed_time_pct < 60 ? "task table there is unreliable" : "above the 60% line"; }
    }
    return { title: title, sub: sub, row: r };
  }
  function overview() {
    var none = !inc.length, att = T.attributed_time_pct, par = T.wall_s ? T.agent_s / T.wall_s : null;
    var cards = [
      kpi("Calendar span · derived", none ? "–" : dur(T.span_s), none ? "no data" : "agent-time " + dur(T.agent_s) + (par ? " · parallelism ×" + par.toFixed(1) + " avg" : ""), "",
        none ? null : [bar(T.buckets_s, BK, "b-", true), legend(BK, "b-", { working: "Working " + dur(T.buckets_s.working), waiting: "Waiting " + dur(T.buckets_s.waiting), blocking: "Blocking " + dur(T.buckets_s.blocking), idle: "Idle " + dur(T.buckets_s.idle) })]),
      kpi("Estimated cost · list price", none ? "–" : usd(T.cost_usd), T.passed ? usd(T.cost_usd / T.passed) + " per passed task (" + T.passed + " passed of " + T.tasks + ")" : "no task passed yet"),
      kpi("Tokens", none ? "–" : tok(sum(T.tokens)), "", "", none ? null : [bar(T.tokens, KINDS, "k-", true), legend(KINDS, "k-", { input: "Input " + tok(T.tokens.input), cache_read: "Cache read " + tok(T.tokens.cache_read), cache_write: "Cache write " + tok(T.tokens.cache_write), output: "Output " + tok(T.tokens.output) })]),
      kpi("Returns (FAIL messages)", none ? "–" : T.returns + (T.flagged_tasks ? " ⚑" : ""), none ? "" : T.flagged_tasks ? T.flagged_tasks + " flagged task" + (T.flagged_tasks > 1 ? "s" : "") + " (3+ returns)" : T.returns ? "no flagged task" : "none", T.flagged_tasks ? "bad" : T.returns ? "warn" : ""),
      kpi("PO wait · elapsed", none ? "–" : dur(T.po_wait_s), "summed over scopes · not agent cost"),
      kpi("Attributed to tasks", att == null ? "–" : Math.round(att) + "%", "agent-time weighted" + (T.under_60 ? " · " + T.under_60 + " scope" + (T.under_60 > 1 ? "s" : "") + " under 60%" : ""), att != null && att < 60 ? "warn" : "",
        (function () { var m = h("div", { class: "meter" + (att != null && att < 60 ? " warn" : "") }, h("i")); m.firstChild.style.width = (att || 0) + "%"; return m; })())
    ];
    var s = h("section", { id: "overview" }, h("div", { class: "sh" }, h("h2", null, "Overview"), h("span", { class: "sub" }, T.included + " of " + T.listed + " scopes included")), h("div", { class: "kpis" }, cards));
    if (D.digest.length && inc.length > 1) s.appendChild(h("div", null, h("h3", { style: "margin-top:14px" }, "Worth a look"),
      h("div", { class: "digest" }, D.digest.slice(0, 4).map(function (d, i) {
        var it = digestItem(d), b = h("button", { class: "dg" }, h("span", { class: "n" }, i + 1), h("span", { class: "t" }, it.title, it.sub ? h("small", null, it.sub) : null));
        b.onclick = function () { if (it.row) { jump("scopes"); openScope(it.row); } }; return b;
      }))));
    return s;
  }
  var COLS = [
    { k: "name", label: "Scope", val: function (r) { return r.name.toLowerCase(); }, fmt: function (r) { return h("span", null, swatch(r), h("b", null, nm(r)), (r.team || r.size) ? [" ", h("span", { class: "faint" }, r.team || r.size)] : null); } },
    { k: "status", label: "Status", val: function (r) { return r.status; }, fmt: function (r) { var g = r.status === "stale" ? staleS(r) : null; return h("span", null, chip(r), g != null ? [" ", h("span", { class: "faint" }, dur(g) + " old")] : null); } },
    { k: "wall", label: "Elapsed", num: 1, val: function (r) { return r.totals ? r.totals.wall_s : -1; }, fmt: function (r) { return r.totals ? dur(r.totals.wall_s) : "–"; } },
    { k: "time", label: "Agent-time by bucket", num: 1, val: function (r) { return r.totals ? r.totals.agent_s : -1; },
      fmt: function (r) { if (!r.totals) return h("span", { class: "faint" }, r.reason || "");
        var t = h("span", { style: "min-width:48px;text-align:right" }, dur(r.totals.agent_s));
        return h("span", { style: "display:inline-flex;align-items:center;gap:8px" }, bar(r.totals.buckets_s, BK, "b-"), t); } },
    { k: "cost", label: "Cost · share", num: 1, val: function (r) { return r.totals ? r.totals.cost_usd : -1; }, fmt: function (r) { return r.totals ? h("span", null, usd(r.totals.cost_usd), " ", h("span", { class: "faint" }, pc(r.totals.cost_usd / (T.cost_usd || 1)))) : "–"; } },
    { k: "tokens", label: "Tokens", num: 1, val: function (r) { return r.totals ? sum(r.totals.tokens) : -1; }, fmt: function (r) { return r.totals ? tok(sum(r.totals.tokens)) : "–"; } },
    { k: "tasks", label: "Tasks passed", num: 1, val: function (r) { return r.totals ? r.totals.tasks : -1; }, fmt: function (r) { return r.totals ? r.totals.passed + "/" + r.totals.tasks : "–"; } },
    { k: "ret", label: "Returns (FAIL)", num: 1, val: function (r) { return r.totals ? r.totals.returns : -1; },
      fmt: function (r) { if (!r.totals) return ""; var n = r.totals.returns, f = r.totals.flagged_tasks;
        return h("span", { class: "ret " + (f ? "r3" : n ? "r1" : ""), "data-tip": f ? "3 or more returns: flagged" : null }, n + (f ? " ⚑" : "")); } },
    { k: "po", label: "PO wait", num: 1, val: function (r) { return r.totals ? r.totals.po_wait_s : -1; }, fmt: function (r) { return r.totals ? dur(r.totals.po_wait_s) : "–"; } },
    { k: "att", label: "Attributed", num: 1, val: function (r) { return r.totals && r.totals.attributed_time_pct != null ? r.totals.attributed_time_pct : -1; },
      fmt: function (r) { var p = r.totals && r.totals.attributed_time_pct; if (p == null) return "–"; return h("span", { style: p < 60 ? "color:var(--mango-d);font-weight:700" : "" }, Math.round(p) + "%"); } },
    { k: "rep", label: "Report", val: function (r) { return r.report_href ? 1 : 0; }, fmt: function (r) { return r.report_href ? link(r, "open report →", "rl") : noReport(r); } }
  ];
  function scopesSection() {
    var sk = "cost", desc = true, fText = "", fStatus = "", fSize = "";
    var host = h("div", { id: "scopetbl" }), q = h("input", { type: "search", id: "sq", placeholder: "Filter scopes…", "aria-label": "Filter scopes" });
    var st = h("select", { id: "sst", "aria-label": "Status" }, [["", "all"], ["done", "done"], ["running", "running"], ["out", "not included"]].map(function (o) { return h("option", { value: o[0] }, o[1]); }));
    var sz = h("select", { id: "ssz", "aria-label": "Size" }, [["", "all"], ["S", "S"], ["M", "M"], ["L", "L"]].map(function (o) { return h("option", { value: o[0] }, o[1]); }));
    function draw() {
      var list = rows.filter(function (r) {
        if (fText && (r.name + " " + r.squad).toLowerCase().indexOf(fText) < 0) return false;
        if (fStatus === "out" ? isInc(r) : fStatus && r.status !== fStatus) return false;
        return !fSize || r.size === fSize;
      });
      var c = COLS.filter(function (x) { return x.k === sk; })[0];
      list.sort(function (a, b) { var x = c.val(a), y = c.val(b); return (x > y ? 1 : x < y ? -1 : 0) * (desc ? -1 : 1); });
      host.textContent = "";
      var head = h("tr", null, COLS.map(function (x) {
        var th = h("th", { class: x.num ? "num" : "", tabindex: "0", role: "columnheader" }, x.label); if (x.k === sk) th.setAttribute("aria-sort", desc ? "descending" : "ascending");
        var go = function () { if (sk === x.k) desc = !desc; else { sk = x.k; desc = !!x.num; } draw(); }; th.onclick = go; th.onkeydown = function (e) { if (e.key === "Enter") go(); }; return th; }));
      var body = list.length ? list.map(function (r) {
        var tr = h("tr", { class: r.totals && r.totals.flagged_tasks ? "flag" : "", tabindex: "0" }, COLS.map(function (x) {
          var td = h("td", { class: x.num ? "num" : "" }, x.fmt(r)); if (x.k === "rep") td.onclick = function (e) { e.stopPropagation(); }; return td; }));
        tr.onclick = function () { openScope(r, tr); }; tr.onkeydown = function (e) { if (e.key === "Enter") openScope(r, tr); }; return tr;
      }) : h("tr", null, h("td", { colspan: COLS.length }, rows.length ? empty("No scope matches the filter.", "Clear the filter.") : empty("No scopes.", "Nothing to show: nothing to roll up yet.")));
      var foot = inc.length && list.length ? h("tfoot", null, h("tr", null, h("td", null, "Total · " + T.included + " of " + T.listed), h("td"), h("td", { class: "num" }), h("td", { class: "num" }, dur(T.agent_s)), h("td", { class: "num" }, usd(T.cost_usd)),
        h("td", { class: "num" }, tok(sum(T.tokens))), h("td", { class: "num" }, T.passed + "/" + T.tasks), h("td", { class: "num" }, String(T.returns)), h("td", { class: "num" }, dur(T.po_wait_s)), h("td"), h("td"))) : null;
      host.appendChild(h("div", { class: "tw" }, h("table", { id: "scopes-table" }, h("thead", null, head), h("tbody", null, body), foot)));
    }
    q.oninput = function () { fText = q.value.toLowerCase(); draw(); }; st.onchange = function () { fStatus = st.value; draw(); }; sz.onchange = function () { fSize = sz.value; draw(); };
    draw();
    return h("section", { id: "scopes" }, h("div", { class: "sh" }, h("h2", null, "Scopes"), h("span", { class: "sub" }, "click a row for its summary; the link opens its own report"),
      h("div", { class: "tools" }, q, h("label", { class: "mut" }, "Status ", st), h("label", { class: "mut" }, "Size ", sz))), host, legend(BK, "b-", BL));
  }
  function share() {
    var box = h("div", { id: "sharebox" });
    if (!inc.length) box.appendChild(h("div", { class: "card empty" }, h("b", null, "No share to show."), "Nothing to show: no scope has data yet."));
    else {
      var card = h("div", { class: "card" });
      [["Estimated cost", function (r) { return r.totals.cost_usd; }, usd], ["Agent-time", function (r) { return r.totals.agent_s; }, dur], ["Returns", function (r) { return r.totals.returns; }, function (v) { return v + " total"; }]].forEach(function (m) {
        var tot = inc.reduce(function (a, r) { return a + m[1](r); }, 0), line = h("div", { class: "bar lg", style: "height:26px" });
        card.appendChild(h("div", { style: "margin:10px 0 2px" }, h("b", null, m[0]), " ", h("span", { class: "mut" }, m[2](tot))));
        inc.filter(function (r) { return m[1](r) > 0; }).sort(function (a, b) { return m[1](b) - m[1](a); }).forEach(function (r) {
          var v = m[1](r), f = tot ? v / tot : 0, i = h("i", { "data-tip": r.name + ": " + m[2](v) + " (" + pc(f) + ")" }, f > .12 ? pc(f) : "");
          i.style.cssText = "width:" + (f * 100) + "%;background:" + col(r) + ";display:flex;align-items:center;justify-content:center;color:#FCF8F1;font-size:12px;font-weight:700;overflow:hidden";
          line.appendChild(i);
        });
        card.appendChild(line);
      });
      card.appendChild(h("div", { class: "legend" }, inc.map(function (r) { return h("span", null, (function () { var s = h("i", { class: "sw" }); s.style.background = col(r); return s; })(), r.name); })));
      if (rows.length > inc.length) card.appendChild(h("div", { class: "mut", style: "font-size:12px;margin-top:6px" }, (rows.length - inc.length) + " scope" + (rows.length - inc.length > 1 ? "s" : "") + " not included (no data)."));
      box.appendChild(card);
    }
    return h("section", { id: "share" }, h("div", { class: "sh" }, h("h2", null, "Share by scope"), h("span", { class: "sub" }, "who took the money and the time")), box);
  }
  function rolesSection() {
    var metric = "cost", host = h("div", { id: "gridbox" });
    var sel = h("select", { id: "mx", "aria-label": "Metric" }, [["cost", "Cost"], ["time", "Time"], ["tokens", "Tokens"]].map(function (o) { return h("option", { value: o[0] }, o[1]); }));
    function get(q) { return !q ? 0 : metric === "cost" ? q.cost_usd : metric === "time" ? q.agent_s : q.tokens; }
    function f(v) { return metric === "cost" ? usd(v) : metric === "time" ? dur(v) : tok(v); }
    function cell(r, n) { return get(r.roles.filter(function (z) { return z.role === n; })[0]); }
    function draw() {
      host.textContent = "";
      var rn = D.roles.map(function (r) { return r.role; });
      if (!rn.length || !inc.length) { host.appendChild(h("div", { class: "card empty" }, h("b", null, "Nothing to cross yet."), "Nothing to show: the grid needs at least one scope with data.")); return; }
      var max = 0, grid = rn.map(function (n) { return inc.map(function (r) { var v = cell(r, n); max = Math.max(max, v); return v; }); });
      var head = h("tr", null, h("th", { class: "rl" }), inc.map(function (r) { return h("th", { title: r.name }, r.name.length > 14 ? r.name.slice(0, 13) + "…" : r.name); }), h("th", null, "Total"));
      var body = rn.map(function (n, i) {
        return h("tr", null, h("td", { class: "rl" }, n), inc.map(function (r, j) {
          var v = grid[i][j], a = max ? Math.min(.85, v / max * .85) : 0, td = h("td", { class: "cell " + (v ? "" : "zero"), "data-r": n, "data-c": String(j) }, v ? f(v) : "·");
          td.style.background = "rgba(232,130,14," + a.toFixed(2) + ")";
          td.onclick = function () { cellDrawer(r, n); }; return td; }),
          h("td", { class: "cell zero", style: "cursor:default" }, h("b", null, f(grid[i].reduce(function (x, y) { return x + y; }, 0)))));
      });
      var ct = inc.map(function (r, j) { return grid.reduce(function (x, a) { return x + a[j]; }, 0); });
      var foot = h("tfoot", null, h("tr", null, h("td", { class: "rl", style: "background:var(--panel)" }, "Total"), ct.map(function (v) { return h("td", null, f(v)); }), h("td", null, f(ct.reduce(function (x, y) { return x + y; }, 0)))));
      host.appendChild(h("div", { class: "tw" }, h("table", { class: "mx" }, h("thead", null, head), h("tbody", null, body), foot)));
      host.appendChild(h("div", { class: "mut", style: "font-size:12px;margin-top:4px" }, "Same role names in every scope; respawned agents are already rolled up."));
    }
    function cellDrawer(r, n) {
      var q = r.roles.filter(function (z) { return z.role === n; })[0]; if (!q) return;
      var all = inc.reduce(function (a, x) { return a + x.totals.cost_usd; }, 0);
      openDrawer([h("h2", null, n + " in " + r.name),
        h("div", { class: "card" }, h("b", null, dur(q.agent_s)), " · ", h("b", null, usd(q.cost_usd)), " · ", h("b", null, tok(q.tokens)), " tokens"),
        h("p", { class: "mut" }, pc(q.cost_usd / (r.totals.cost_usd || 1)) + " of this scope's cost; " + pc(q.cost_usd / (all || 1)) + " of the rollup."),
        r.report_href ? link(r, "Open " + r.name + " roles →", "act", "#roles") : null]);
    }
    sel.onchange = function () { metric = sel.value; draw(); }; draw();
    return h("section", { id: "roles" }, h("div", { class: "sh" }, h("h2", null, "Roles across scopes"), h("span", { class: "sub" }, "click a cell for that role in that scope"),
      h("div", { class: "tools" }, h("label", { class: "mut" }, "Show ", sel))), host);
  }
  function whenSection() {
    var box = h("div", { id: "whenbox" });
    if (!rows.length) box.appendChild(h("div", { class: "card empty" }, h("b", null, "No scopes."), "Nothing to show."));
    else {
      var w = inc.map(function (r) { return [ts((r.window || {}).start), ts((r.window || {}).end)]; }).filter(function (x) { return x[0] != null && x[1] != null; });
      var a = Math.min.apply(null, w.map(function (x) { return x[0]; })), b = Math.max.apply(null, w.map(function (x) { return x[1]; })), sp = (b - a) || 1;
      var grid = h("div", { style: "display:grid;grid-template-columns:150px 1fr;gap:6px 10px;align-items:center" });
      rows.forEach(function (r) {
        var lane = h("div", { style: "position:relative;height:16px;background:#fff;border:1px solid var(--bd);border-radius:4px" }), s = ts((r.window || {}).start), e = ts((r.window || {}).end);
        if (isInc(r) && s != null && e != null) {
          var i = h("i", { "data-tip": r.name + " · " + dt(s) + " → " + (r.status === "running" ? "now" : dt(e)) + " · " + dur(r.totals.wall_s) });
          i.style.cssText = "position:absolute;left:" + ((s - a) / sp * 100) + "%;width:" + Math.max(.6, (e - s) / sp * 100) + "%;top:2px;bottom:2px;background:" + col(r) + ";border-radius:3px;" + (r.status === "running" ? "border-right:3px dashed #3E372E;" : "");
          lane.appendChild(i);
        } else lane.appendChild(h("span", { class: "faint", style: "position:absolute;left:8px;top:-1px;font-size:11.5px" }, (CHIP[r.status] || [r.status])[0]));
        grid.appendChild(h("div", { style: "text-align:right;font-size:12.5px" }, r.name)); grid.appendChild(lane);
      });
      box.appendChild(h("div", { class: "card" }, grid, w.length ? h("div", { class: "mut", style: "font-size:12px;margin-top:6px;display:flex;justify-content:space-between" }, h("span", null, dt(a)), h("span", null, dt(b))) : null));
    }
    return h("section", { id: "when" }, h("div", { class: "sh" }, h("h2", null, "When"), h("span", { class: "sub" }, "calendar span of each scope; overlap = parallel scopes")), box);
  }
  function navSpy() {
    var links = Array.prototype.slice.call(document.querySelectorAll("nav.sections a"));
    if (typeof IntersectionObserver === "undefined") return;
    var io = new IntersectionObserver(function (es) { es.forEach(function (en) { if (en.isIntersecting) links.forEach(function (a) { a.classList.toggle("on", a.getAttribute("href") === "#" + en.target.id); }); }); }, { rootMargin: "-90px 0px -70% 0px" });
    Array.prototype.forEach.call(document.querySelectorAll("main section[id]"), function (s) { io.observe(s); });
  }

  /* ---- page ---- */
  function page() {
    if (D.kind !== "rollup" || D.schema_version !== 1) {
      app.appendChild(h("div", { class: "errbox" }, h("h1", null, "The rollup data could not be read"),
        h("p", { class: "mut" }, "This page shows the rollup ", h("code", null, "data.json"), ", and it failed a check."),
        D.kind !== "rollup" ? banner("bad", "!", "kind \"rollup\" expected.", "This file is " + (D.kind ? "a " + D.kind + " report" : "not a rollup") + ", not a rollup.")
          : banner("bad", "!", "schema_version 1 expected.", "This file has schema_version " + D.schema_version + "; this page reads 1."),
        pre("report/data.json  kind: " + D.kind + "\nexpected: rollup\nFix: run  squad-report " + (D.title || "<goal>") + "  to rebuild the goal rollup.")));
      return;
    }
    var none = !rows.length, out = rows.filter(function (r) { return !isInc(r); }), run = rows.filter(function (r) { return r.status === "running"; });
    var stale = rows.filter(function (r) { return r.status === "stale"; }), done = rows.filter(function (r) { return r.status === "done"; });
    var counts = none ? "no scopes" : rows.length + " scope" + (rows.length > 1 ? "s" : "") + " · " + done.length + " done" + (run.length ? " · " + run.length + " running" : "") + (out.length ? " · " + out.length + " not included" : "");
    var partial = out.length || run.length;
    app.appendChild(h("header", { class: "page" },
      h("div", null, h("h1", null, D.title, " ", h("span", { class: "chip" }, GOAL ? "goal rollup" : "from files"), " ", none ? null : h("span", { class: "chip " + (partial ? "warn" : "done") }, partial ? "partial" : "complete")), h("div", { class: "mut" }, counts)),
      h("div", { class: "meta" }, "Generated " + dt(ts(D.generated_at)), h("br"), "Built from the scopes' data.json files, no transcript read · cost estimated at list price · schema v1")));
    var bad = out.filter(function (r) { return r.status === "schema_mismatch" || r.status === "unreadable"; });
    if (!inc.length && bad.length) {
      app.appendChild(h("div", { class: "errbox card" }, h("h2", null, "No file could be read"), h("p", null, bad[0].reason), h("p", null, "Check the file was written by ", h("code", null, "squad-report <scope>"), " (kind scope, schema_version 1), then run the rollup again.")));
      return;
    }
    app.appendChild(h("nav", { class: "sections", "aria-label": "Sections" }, ["overview", "scopes", "share", "roles", "when"].map(function (s) { return h("a", { href: "#" + s }, s.charAt(0).toUpperCase() + s.slice(1)); })));
    var main = h("main");
    if (none) main.appendChild(banner("info", "i", "No scopes to roll up.", GOAL ? ["This goal has no scopes yet. A rollup appears once a scope has a ", h("code", null, "data.json"), "; run ", h("code", null, "squad-report <scope>"), " for each."]
      : ["No data.json file was given. Pass one or more scope data.json files (yours or a teammate's) to ", h("code", null, "squad-report rollup"), "."]));
    else if (!inc.length) main.appendChild(banner("info", "i", "Nothing to roll up.", GOAL ? ["No scope of this goal has a data.json. Run ", h("code", null, "squad-report <scope>")] : ["No scope data.json was given. Run ", h("code", null, "squad-report rollup <data.json>...")]));
    if (out.length) main.appendChild(banner("warn", "!", "Totals are partial.", [out.map(function (r, i) { return [i ? ", " : "", h("b", null, r.name), " (" + (CHIP[r.status] || [r.status])[0] + ")"]; }), (out.length > 1 ? " are" : " is") + " not in the totals. Each row says what to run."]));
    if (T.mixed_prices && !none) main.appendChild(banner("info", "i", "Mixed price tables.", "These scopes were priced with different squad price settings. Each cost is that scope's own estimate, summed as is."));
    if (run.length) main.appendChild(banner("info", "i", "Still running:", [names(run), ". Its numbers stop at its last report and will grow."]));
    if (stale.length) main.appendChild(banner("warn", "!", "Stale data:", [names(stale), ": its ", h("code", null, "data.json"), " is older than its last message (" + dur(staleS(stale[0])) + "). Included as is; re-run ", h("code", null, "squad-report " + stale[0].name), "."]));
    main.appendChild(overview()); main.appendChild(scopesSection()); main.appendChild(share()); main.appendChild(rolesSection()); main.appendChild(whenSection());
    app.appendChild(main);
    navSpy();
  }
  document.body.appendChild(tip);
  document.body.appendChild(drawer);
  page();
})();
