(function () {
"use strict";
var app = document.getElementById("app");
var D;
try { D = JSON.parse(document.getElementById("report-data").textContent); } catch (e) { D = null; }

function el(tag, cls, text, attrs) {
  var n = document.createElement(tag);
  if (cls) n.setAttribute("class", cls);
  if (text !== undefined && text !== null) n.textContent = String(text);
  if (attrs) for (var k in attrs) n.setAttribute(k, attrs[k]);
  return n;
}
function add(p) { for (var i = 1; i < arguments.length; i++) if (arguments[i]) p.appendChild(arguments[i]); return p; }
function dur(s) {
  s = Math.round(s || 0);
  if (s <= 0) return "0s";
  var d = Math.floor(s / 86400), h = Math.floor(s % 86400 / 3600), m = Math.floor(s % 3600 / 60);
  if (d) return d + "d " + h + "h";
  if (h) return h + "h " + m + "m";
  if (m) return m + "m" + (s < 600 && s % 60 ? " " + (s % 60) + "s" : "");
  return s + "s";
}
function usd(x) { x = x || 0; return "$" + (x >= 100 ? Math.round(x) : x.toFixed(2)); }
function tok(n) { n = n || 0; return n >= 1e6 ? (n / 1e6).toFixed(1) + "M" : n >= 1e3 ? (n / 1e3).toFixed(1) + "k" : String(n); }
function sum(o) { var t = 0; for (var k in o) t += o[k] || 0; return t; }
function ts(iso) { return iso ? Date.parse(iso) / 1000 : null; }
function hm(iso) { return iso ? iso.replace("T", " ").replace(/:\d\dZ$/, "Z") : "–"; }
var BK = ["working", "waiting", "blocking", "idle"];
var BN = { working: "Working (model/tool running)", waiting: "Waiting (long tool call or background job)", blocking: "Blocking (waiting on a reply or on the PO)", idle: "Idle (waiting for work, or for the PO's chat reply)" };

function bar(vals, keys, cls, total) {
  var b = el("div", "bar"), t = total || sum(vals) || 1;
  keys.forEach(function (k) {
    var v = vals[k] || 0;
    if (v <= 0) return;
    add(b, el("i", cls(k), null, { style: "width:" + (v / t * 100).toFixed(2) + "%", title: k + " " + dur(v) }));
  });
  return b;
}
function sw(cls, text) { var s = el("span"); add(s, el("i", "sw " + cls), document.createTextNode(text)); return s; }
function legend(extra, durs) {
  var l = el("div", "legend");
  BK.forEach(function (k) { add(l, sw("b-" + k, durs ? k.charAt(0).toUpperCase() + k.slice(1) + " " + dur(durs[k]) : BN[k])); });
  if (extra) add(l, sw("b-po", "Blocking on the PO (timeline)"));
  return l;
}
function tokbar(t) { return bar(t, ["input", "cache_read", "cache_write", "output"], function (k) { return "t-" + k; }); }
function card(lbl, big, sub, cls) {
  var c = el("div", "card" + (cls ? " " + cls : ""));
  return add(c, el("div", "lbl", lbl), el("div", "big", big), el("div", "sub", sub));
}

// ---------- error state ----------
function fail(why) {
  var c = el("div", "card red", null, { style: "margin:24px" });
  add(c, el("h2", null, "The report data could not be read"), el("p", null, why),
    el("p", "muted", "Fix: re-run `squad-report <scope>` with a squad-report of the same version as this page."));
  app.appendChild(c);
}
if (!D || typeof D !== "object") { fail("the embedded data is not valid JSON"); return; }
if (D.schema_version !== 1) { fail("schema_version " + D.schema_version + " not supported (this page reads 1)"); return; }
if (D.kind !== "scope" || !D.totals || !D.scope) { fail("the data is not a scope report"); return; }

var S = D.scope, T = D.totals, tasks = D.tasks || [], roles = D.roles || [], agents = D.agents || [];
var hasData = (D.sources && D.sources.transcripts > 0) || T.agent_s > 0;
var selected = null, drawerEl = null;
var st = { sort: { k: "cost", dir: -1 }, rsort: { k: "cost", dir: -1 }, q: "", chip: "", iter: "", metric: "cost", compress: true, hi: "" };

// ---------- helpers on data ----------
function roleRows() {
  var m = {}, order = [];
  roles.forEach(function (a) {
    var k = a.role || a.name;
    var r = m[k];
    if (!r) { r = m[k] = { role: k, agents: [], sessions: 0, buckets: { working: 0, waiting: 0, blocking: 0, idle: 0 }, idle_s: { peer: 0, human_input: 0 }, tokens: { input: 0, cache_read: 0, cache_write: 0, output: 0 }, cost: 0, live: false, missing: false }; order.push(k); }
    r.agents.push(a); r.sessions += a.sessions || 0;
    BK.forEach(function (b) { r.buckets[b] += (a.buckets_s || {})[b] || 0; });
    r.idle_s.peer += (a.idle_s || {}).peer || 0; r.idle_s.human_input += (a.idle_s || {}).human_input || 0;
    for (var k2 in r.tokens) r.tokens[k2] += (a.tokens || {})[k2] || 0;
    r.cost += a.cost_usd || 0; r.live = r.live || !!a.live; r.missing = r.missing || a.transcript_found === false;
  });
  return order.map(function (k) { return m[k]; });
}
function roleOf(agent) { var a = roles.filter(function (x) { return x.name === agent; })[0]; return a ? (a.role || a.name) : agent; }
function taskById(id) { return tasks.filter(function (t) { return t.id === id; })[0]; }
function tLabel(t) { return t.id + (t.title ? " " + t.title : ""); }
function share(c) { return T.cost_usd ? Math.round(c / T.cost_usd * 100) + "%" : "–"; }
function ttime(t) { return sum(t.buckets_s || {}); }
function poOnBlock(rr) { return 0; }

// ---------- header + banners ----------
function header() {
  var h = el("header", "page"), l = el("div"), t = el("h1", null, S.name);
  var running = S.status === "running";
  add(t, el("span", "chip " + (running ? "run" : "done"), running ? "running · partial" : (S.status || "done")),
    el("span", "chip", "size " + (S.size || "?")));
  add(l, t, el("div", "muted", "Scope report · " + hm(S.window && S.window.start) + " → " + (running ? "now" : hm(S.window && S.window.end))));
  var m = el("div", "meta");
  add(m, document.createTextNode("Generated " + hm(S.generated_at)), el("br"),
    document.createTextNode("Derived from transcripts, gaps classified by what ends them · cost estimated at list price · schema v" + D.schema_version));
  var href = S.rollup_href;
  if (S.goal && typeof href === "string" && /^[\w.\/-]+\.html$/.test(href) && href.indexOf("//") < 0)
    add(m, el("br"), el("a", null, "Rollup: " + S.goal + " goal →", { href: href }));
  add(h, l, m);
  return h;
}
function banner(cls, text, links) {
  var b = el("div", "banner " + cls, text);
  (links || []).forEach(function (l) { add(b, document.createTextNode(" "), l); });
  return b;
}
function banners() {
  var box = el("div");
  if (!hasData) add(box, banner("", "No session data found for this scope. Cause: no transcripts or messages matched its roster. Run `squad-report " + S.name + "` again after the agents have run."));
  else if (S.partial) add(box, banner("", "Numbers cover up to " + hm(S.window && S.window.end) + ". The scope is still running (" + (S.partial_reasons || []).join(", ") + "); re-run `squad-report " + S.name + "`, rebuilt on `squad-close`."));
  var pct = T.attributed ? T.attributed.time_pct : null;
  if (hasData && pct !== null && pct < 60) add(box, banner("amber", "Only " + Math.round(pct) + "% of agent-time is attributed to tasks. Most work lands in Scope overhead, so the task table understates real task cost. Roles and totals are still right."));
  var flagged = tasks.filter(function (t) { return t.flag; });
  if (flagged.length) {
    var links = flagged.map(function (t) { var b = el("button", "btn", "Task " + t.id); b.addEventListener("click", function () { openTask(t.id); }); return b; });
    var rw = tasks.reduce(function (a, t) { return a + (t.rework_s || 0); }, 0), rc = tasks.reduce(function (a, t) { return a + (t.rework_cost_usd || 0); }, 0);
    add(box, banner("red", flagged.length + " task" + (flagged.length > 1 ? "s" : "") + " reached 3 returns. Rework " + dur(rw) + " · " + usd(rc) + " (estimated, list price).", links));
  }
  var miss = roles.filter(function (a) { return a.transcript_found === false; }).map(function (a) { return a.name; });
  if (miss.length) add(box, banner("amber", "No transcript found for: " + miss.join(", ") + ". Totals exclude them."));
  return box;
}
function nav() {
  var n = el("nav", "sections", null, { "aria-label": "Sections" });
  [["overview", "Overview"], ["tasks", "Tasks"], ["roles", "Roles"], ["grid", "Task × role"], ["timeline", "Timeline"]].forEach(function (p) {
    add(n, el("a", null, p[1], { href: "#" + p[0], "data-nav": p[0] }));
  });
  return n;
}

// ---------- overview ----------
function overview() {
  var s = el("section", null, null, { id: "overview" });
  var k = el("div", "kpis");
  var par = T.wall_s ? (T.agent_s / T.wall_s) : 0;
  var nd = !hasData;
  var c1 = card("Elapsed · derived", nd ? "–" : dur(T.wall_s), nd ? "no data" : "agent-time " + dur(T.agent_s) + " (derived) · parallelism ×" + par.toFixed(1) + "");
  if (!nd) {
    add(c1, bar(T.buckets_s, BK, function (b) { return "b-" + b; }), legend(false, T.buckets_s || {}));
    var l = el("div", "sub");
    l.textContent = "Idle: waiting for work " + dur((T.idle_s || {}).peer) + " · waiting for your chat reply " + dur((T.idle_s || {}).human_input) + " (not PO wait)";
    add(c1, l);
    add(c1, el("div", "sub", roles.length + " agents · bars are shares of agent-time"));
  }
  var po = T.po_wait || { count: 0, total_s: 0, longest_s: 0 }, open = (po.items || []).some(function (i) { return !i.answered_at; });
  var c2 = card("PO wait · elapsed (derived)", nd ? "–" : dur(po.total_s), nd ? "no data" : po.count + " escalations · longest " + dur(po.longest_s) + (open ? " (open now)" : "") + " · " + (po.pct_of_elapsed || 0) + "% of elapsed · not agent cost");
  var c3 = card("Estimated cost · list price", nd ? "–" : usd(T.cost_usd), nd ? "no data" : usd(T.cost_per_passed_task_usd) + " per passed task (" + (T.tasks_passed || 0) + " passed) · estimated, list price");
  if (!nd && T.cost_reported_usd !== null && T.cost_reported_usd !== undefined)
    add(c3, el("div", "sub", "Claude Code reported " + usd(T.cost_reported_usd) + (T.cost_delta_pct !== null && T.cost_delta_pct !== undefined ? " (estimate off by " + Math.abs(T.cost_delta_pct) + "%)" : "")));
  var tk = T.tokens || {};
  var c4 = card("Tokens", nd ? "–" : tok(sum(tk)), nd ? "no data" : "input " + tok(tk.input) + " · cache read " + tok(tk.cache_read) + " · cache write " + tok(tk.cache_write) + " · output " + tok(tk.output));
  if (!nd) add(c4, tokbar(tk));
  var anyFlag = tasks.some(function (t) { return t.flag; });
  var rw = tasks.reduce(function (a, t) { return a + (t.rework_s || 0); }, 0), rc = tasks.reduce(function (a, t) { return a + (t.rework_cost_usd || 0); }, 0);
  var c5 = card("Returns (FAIL messages)", nd ? "–" : (T.returns || 0) + (anyFlag ? " ⚑" : ""), nd ? "no data" : "rework " + dur(rw) + " (derived) · ≈" + usd(rc) + " (estimated, list price)", anyFlag ? "red" : (T.returns ? "amber" : ""));
  var pct = T.attributed ? T.attributed.time_pct : null;
  var c6 = card("Attributed to tasks", nd || pct === null ? "–" : Math.round(pct) + "%", nd ? "no data" : "of agent-time (not idle)", !nd && pct !== null && pct < 60 ? "amber" : "");
  c6.setAttribute("title", "Developer time by roster and branch; other roles by the window first mention → PASS.");
  if (!nd && pct !== null) add(c6, bar({ a: pct, b: 100 - pct }, ["a"], function () { return "b-working"; }, 100));
  [c1, c2, c3, c4, c5, c6].forEach(function (c) { k.appendChild(c); });
  add(s, el("h2", null, "Overview"), k);

  add(s, el("h2", null, "Worth a look"));
  var ul = el("ul", "digest");
  (D.digest || []).slice(0, 8).forEach(function (d, i) {
    var li = el("li"), inner;
    if (d.target) { inner = el("button"); inner.addEventListener("click", function () { go(d.target); }); } else inner = el("div");
    var tx = d.text || "", q = tx.indexOf(': "'), sb = q >= 0 ? tx.slice(q + 2) : digestSub(d);
    if (q >= 0) tx = tx.slice(0, q);
    var t = el("span", "t", tx);
    if (sb) add(t, el("small", null, sb));
    add(inner, el("span", "n", i + 1), t);
    add(li, inner); ul.appendChild(li);
  });
  if (!(D.digest || []).length) add(ul, el("li", "nodata", "Nothing stands out yet."));
  add(s, ul);

  var cols = el("div", "two");
  var lb = el("div"); add(lb, el("h2", null, "Longest blocks"));
  var blocks = longestBlocks();
  if (!blocks.length) add(lb, el("div", "nodata", "No blocks yet."));
  if (blocks.length) {
    var bt = el("table"), bh = el("thead"), br = el("tr");
    ["Who", "Waited on", "Task", "For"].forEach(function (h) { add(br, el("th", h === "For" ? "nosort num" : "nosort", h)); });
    add(bh, br); add(bt, bh);
    var bb = el("tbody");
    blocks.forEach(function (b) {
      var r = el("tr"), on = el("td");
      if (b.on === "PO") add(on, el("span", "chip po", "PO")); else on.textContent = b.on || "?";
      add(r, add(el("td"), el("b", null, b.agent)), on, el("td", null, b.task || "–"), el("td", "num", dur(b.len)));
      bb.appendChild(r);
    });
    add(bt, bb); add(lb, add(el("div", "frame"), bt));
  }
  var bi = el("div"); add(bi, el("h2", null, "By iteration"), el("div", "sub muted", "Each row covers the iteration's message window only, not a full breakdown."));
  var its = D.iterations || [];
  if (!its.length) add(bi, el("div", "nodata", "No iterations."));
  else {
    var tb = el("table"), th = el("thead"), tr = el("tr");
    ["Iter", "Window", "Agent-time", "Cost", "Returns"].forEach(function (h) { add(tr, el("th", "nosort", h)); });
    add(th, tr); add(tb, th);
    var tbd = el("tbody");
    its.forEach(function (it) {
      var r = el("tr");
      add(r, el("td", null, it.n), el("td", null, hm(it.window && it.window.start) + " → " + hm(it.window && it.window.end)), el("td", "num", dur(it.agent_s)), el("td", "num", usd(it.cost_usd)), el("td", "num", it.returns));
      tbd.appendChild(r);
    });
    add(tb, tbd); add(bi, add(el("div", "frame"), tb));
  }
  add(cols, lb, bi); s.appendChild(cols);
  return s;
}
function digestSub(d) {
  var id = d.target && d.target.id, t = id ? taskById(id) : null, pw = T.po_wait || {};
  if (d.kind === "top_cost_task" && t) return usd(t.cost_usd) + " · " + t.returns + " return" + (t.returns === 1 ? "" : "s");
  if (d.kind === "top_cost_role") return "roles · " + id;
  if (d.kind === "scope_overhead") return "no task";
  if (d.kind === "rework_cost") return "rework " + dur(tasks.reduce(function (a, x) { return a + (x.rework_s || 0); }, 0)) + " · estimated";
  if (d.kind === "respawns") return "cache writes after idle > 5 min";
  if (d.kind === "idle_share" || d.kind === "parallelism") return "parallelism ×" + (T.wall_s ? T.agent_s / T.wall_s : 0).toFixed(1);
  if (d.kind === "longest_block") return "see Timeline";
  if (d.kind === "po_wait") return "longest " + dur(pw.longest_s) + " · " + (pw.pct_of_elapsed || 0) + "% of elapsed";
  if (d.kind === "review_wait") return "HANDIN to PASS/FAIL";
  if (d.kind === "most_returns") return "no reason recorded";
  if (d.kind === "attribution_low") return "the rest is in Scope overhead";
  return "";
}
function longestBlocks() {
  var out = [];
  agents.forEach(function (a) {
    (a.segments || []).forEach(function (g) {
      if (g[2] === "b" || g[2] === "a") out.push({ agent: a.name, start: g[0], len: g[1] - g[0], bucket: g[2] === "b" ? "blocking" : "waiting", task: g[3], on: g[4] });
    });
  });
  out.sort(function (a, b) { return b.len - a.len; });
  return out.slice(0, 3);
}

// ---------- sortable table ----------
function table(cols, rows, sortState, rerender, onRow, opts) {
  opts = opts || {};
  var tb = el("table"), th = el("thead"), tr = el("tr");
  cols.forEach(function (c) {
    var h = el("th", (c.num ? "num " : "") + (c.sort ? "" : "nosort"), c.h + (sortState && sortState.k === c.k ? (sortState.dir < 0 ? " ▼" : " ▲") : ""));
    if (c.sort) {
      h.setAttribute("tabindex", "0"); h.setAttribute("role", "columnheader");
      h.setAttribute("aria-sort", sortState.k === c.k ? (sortState.dir < 0 ? "descending" : "ascending") : "none");
      var f = function () { if (sortState.k === c.k) sortState.dir = -sortState.dir; else { sortState.k = c.k; sortState.dir = c.num ? -1 : 1; } rerender(); };
      h.addEventListener("click", f);
      h.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); f(); } });
    }
    tr.appendChild(h);
  });
  add(th, tr); tb.appendChild(th);
  var tbd = el("tbody");
  rows.forEach(function (r) {
    var row = el("tr", (r.cls || ""), null, { tabindex: "0" });
    if (selected === r.key) row.classList.add("sel");
    cols.forEach(function (c) {
      var v = c.cell(r.item), td = el("td", (c.num ? "num " : "") + (c.ell ? "ell" : ""));
      if (v && v.nodeType) td.appendChild(v); else td.textContent = v === undefined || v === null ? "–" : v;
      if (c.tip) td.setAttribute("title", c.tip(r.item) || "");
      row.appendChild(td);
    });
    var open = function () { selected = r.key; onRow(r.item); };
    row.addEventListener("click", open);
    row.addEventListener("keydown", function (e) { if (e.key === "Enter") open(); });
    tbd.appendChild(row);
  });
  tb.appendChild(tbd);
  return tb;
}
function sortRows(items, key, dir, getters, pinLast) {
  var g = getters[key];
  var main = items.filter(function (i) { return !(pinLast && pinLast(i)); }), pin = items.filter(function (i) { return pinLast && pinLast(i); });
  main.sort(function (a, b) {
    var x = g(a), y = g(b);
    if (typeof x === "string") return dir * (x < y ? -1 : x > y ? 1 : 0);
    return dir * ((x || 0) - (y || 0));
  });
  return main.concat(pin);
}

// ---------- tasks ----------
function overheadItem() {
  var row = { id: "overhead", over: true, title: "Scope overhead", buckets_s: { working: 0, waiting: 0, blocking: 0, idle: 0 }, tokens: {}, cost_usd: 0 };
  (D.matrix || []).filter(function (m) { return !m.task; }).forEach(function (m) {
    BK.forEach(function (b) { row.buckets_s[b] += (m.buckets_s || {})[b] || 0; });
    row.cost_usd += m.cost_usd || 0;
  });
  return row;
}
function taskCols() {
  return [
    { h: "Task", k: "id", sort: 1, cell: function (t) { return t.over ? "Overhead" : t.id; } },
    { h: "Title", k: "title", sort: 1, ell: 1, cell: function (t) { var s = t.title || ""; return t.over ? t.title : (s.length > 34 ? s.slice(0, 33) + "…" : (s || "–")); }, tip: function (t) { return t.title; } },
    { h: "Iter", k: "iter", sort: 1, num: 1, cell: function (t) { return t.over ? "–" : t.iteration; } },
    { h: "Dev", k: "dev", sort: 1, cell: function (t) { return t.over ? "–" : t.dev; } },
    { h: "Status", k: "status", sort: 1, cell: function (t) { return t.over ? "–" : el("span", "chip", t.status); } },
    { h: "Returns (FAIL)", k: "returns", sort: 1, num: 1, cell: function (t) { if (t.over) return "–"; var r = t.returns || 0; return el("span", "pill" + (r >= 3 ? " r" : r ? " m" : ""), r + (t.flag ? " ⚑" : "")); } },
    { h: "Time by bucket", k: "time", sort: 1, num: 1, cell: function (t) { var w = el("div"); add(w, bar(t.buckets_s, BK, function (b) { return "b-" + b; }), el("span", "muted", dur(ttime(t)) + " (derived)")); return w; } },
    { h: "Cycle", k: "cycle", sort: 1, num: 1, cell: function (t) { return t.over ? "–" : (t.status === "running" ? dur(t.cycle_s) + " …" : t.cycle_s ? dur(t.cycle_s) : "–"); } },
    { h: "Review wait", k: "rw", sort: 1, num: 1, cell: function (t) { if (t.over) return "–"; var w = (t.review_waits || []).reduce(function (a, r) { return a + (r.wait_s || 0); }, 0); return w ? dur(w) : "–"; } },
    { h: "Tokens", k: "tokens", sort: 1, num: 1, cell: function (t) { var n = sum(t.tokens || {}); return n ? tok(n) : "–"; } },
    { h: "Cost (est., list price)", k: "cost", sort: 1, num: 1, cell: function (t) { return t.cost_usd ? usd(t.cost_usd) + " · " + share(t.cost_usd) : "–"; } },
    { h: "Rework", k: "rework", sort: 1, num: 1, cell: function (t) { return t.rework_s ? dur(t.rework_s) + " · " + usd(t.rework_cost_usd) : "–"; } }
  ];
}
var TG = {
  id: function (t) { return t.id; }, title: function (t) { return t.title || ""; }, iter: function (t) { return t.iteration; }, dev: function (t) { return t.dev || ""; },
  status: function (t) { return t.status || ""; }, returns: function (t) { return t.returns; }, time: ttime, cycle: function (t) { return t.cycle_s; },
  rw: function (t) { return (t.review_waits || []).reduce(function (a, r) { return a + (r.wait_s || 0); }, 0); },
  tokens: function (t) { return sum(t.tokens || {}); }, cost: function (t) { return t.cost_usd; }, rework: function (t) { return t.rework_s; }
};
function tasksSection() {
  var s = el("section", null, null, { id: "tasks" }), body = el("div");
  add(s, el("h2", null, "Tasks"));
  function draw() {
    body.textContent = "";
    var q = st.q.toLowerCase();
    var list = tasks.filter(function (t) {
      if (q && (t.id + " " + (t.title || "") + " " + (t.dev || "")).toLowerCase().indexOf(q) < 0) return false;
      if (st.chip === "returns" && !t.returns) return false;
      if (st.chip === "flag" && !t.flag) return false;
      if (st.chip === "open" && t.status === "passed") return false;
      if (st.iter && String(t.iteration) !== st.iter) return false;
      return true;
    });
    if (!tasks.length) { add(body, el("div", "nodata", "No tasks yet")); return; }
    var rows = sortRows(list, st.sort.k, st.sort.dir, TG).map(function (t) { return { item: t, key: "t" + t.id, cls: t.flag ? "flag" : "" }; });
    if (!q && !st.chip && !st.iter) { var o = overheadItem(); rows.push({ item: o, key: "over", cls: "over" }); }
    if (!rows.length) { add(body, el("div", "nodata", "No task matches the filter")); return; }
    add(body, add(el("div", "frame"), table(taskCols(), rows, st.sort, draw, function (t) { if (t.over) openOverhead(); else openTask(t.id); })));
  }
  var tools = el("div", "tools");
  var inp = el("input", null, null, { type: "search", placeholder: "Filter id, title, dev", "aria-label": "Filter tasks" });
  inp.addEventListener("input", function () { st.q = inp.value; draw(); });
  add(tools, inp);
  [["returns", "Has returns"], ["flag", "Flagged"], ["open", "Not passed"]].forEach(function (c) {
    var b = el("button", null, c[1], { type: "button", "aria-pressed": "false" });
    b.addEventListener("click", function () { st.chip = st.chip === c[0] ? "" : c[0]; Array.prototype.forEach.call(tools.querySelectorAll("button"), function (x) { x.classList.remove("on"); x.setAttribute("aria-pressed", "false"); }); if (st.chip) { b.classList.add("on"); b.setAttribute("aria-pressed", "true"); } draw(); });
    tools.appendChild(b);
  });
  var iters = {}; tasks.forEach(function (t) { if (t.iteration !== null && t.iteration !== undefined) iters[t.iteration] = 1; });
  var sel = el("select", null, null, { "aria-label": "Iteration" });
  add(sel, el("option", null, "All iterations", { value: "" }));
  Object.keys(iters).sort().forEach(function (i) { add(sel, el("option", null, "Iteration " + i, { value: i })); });
  sel.addEventListener("change", function () { st.iter = sel.value; draw(); drawGrid(); });
  add(tools, sel);
  add(s, tools, body); draw();
  return s;
}

// ---------- roles ----------
var RG = {
  role: function (r) { return r.role; }, agents: function (r) { return r.agents.length; }, resp: function (r) { return Math.max(0, r.sessions - r.agents.length); },
  time: function (r) { return sum(r.buckets); }, po: function (r) { return r.po; }, tokens: function (r) { return sum(r.tokens); }, cost: function (r) { return r.cost; }
};
function rolesSection() {
  var s = el("section", null, null, { id: "roles" }), body = el("div");
  add(s, el("h2", null, "Roles"), body);
  var rr = roleRows();
  var poBy = {};
  agents.forEach(function (a) { var k = roleOf(a.name); (a.segments || []).forEach(function (g) { if (g[2] === "b" && g[4] === "PO") poBy[k] = (poBy[k] || 0) + g[1] - g[0]; }); });
  rr.forEach(function (r) { r.po = poBy[r.role] || 0; });
  var cols = [
    { h: "Role", k: "role", sort: 1, cell: function (r) { var w = el("span", null, r.role); if (r.live) add(w, el("span", "chip run", "live")); if (r.missing) add(w, el("span", "chip amber", "no transcript")); return w; } },
    { h: "Agents", k: "agents", sort: 1, num: 1, cell: function (r) { return r.agents.length; } },
    { h: "Respawns", k: "resp", sort: 1, num: 1, cell: function (r) { return RG.resp(r); } },
    { h: "Time by bucket", k: "time", sort: 1, num: 1, cell: function (r) { var w = el("div"); add(w, bar(r.buckets, BK, function (b) { return "b-" + b; }), el("span", "muted", dur(sum(r.buckets)) + " (derived)")); return w; } },
    { h: "Blocked on PO", k: "po", sort: 1, num: 1, cell: function (r) { return r.po ? dur(r.po) : "–"; } },
    { h: "Tokens", k: "tokens", sort: 1, num: 1, cell: function (r) { var n = sum(r.tokens); return n ? tok(n) : "–"; } },
    { h: "Cost (est., list price)", k: "cost", sort: 1, num: 1, cell: function (r) { return r.cost ? usd(r.cost) + " · " + share(r.cost) : "–"; } }
  ];
  function draw() {
    body.textContent = "";
    if (!rr.length) { add(body, el("div", "nodata", "No roles listed")); return; }
    var rows = sortRows(rr, st.rsort.k, st.rsort.dir, RG).map(function (r) { return { item: r, key: "r" + r.role }; });
    add(body, add(el("div", "frame"), table(cols, rows, st.rsort, draw, function (r) { openRole(r.role); })));
  }
  draw();
  return s;
}

// ---------- grid (Could) ----------
var gridBody;
function cellVal(m) { return st.metric === "cost" ? m.cost_usd : st.metric === "time" ? sum(m.buckets_s || {}) : sum(m.tokens || {}); }
function fmtVal(v) { return !v ? "·" : st.metric === "cost" ? usd(v) : st.metric === "time" ? dur(v) : tok(v); }
function drawGrid() {
  if (!gridBody) return;
  gridBody.textContent = "";
  var ms = (D.matrix || []).filter(function (m) { var t = m.task ? taskById(m.task) : null; return !st.iter || !m.task || (t && String(t.iteration) === st.iter); });
  if (!ms.length) { add(gridBody, el("div", "nodata", "Nothing to cross yet")); return; }
  var rl = []; ms.forEach(function (m) { var r = roleOf(m.agent); if (rl.indexOf(r) < 0) rl.push(r); });
  var tl = []; ms.forEach(function (m) { var k = m.task || ""; if (tl.indexOf(k) < 0) tl.push(k); });
  var cells = {}, mx = 0, rt = {}, ct = {};
  ms.forEach(function (m) {
    var k = (m.task || "") + "|" + roleOf(m.agent); cells[k] = cells[k] || { sum: 0, items: [] };
    var v = cellVal(m); cells[k].sum += v; cells[k].items.push(m);
    rt[m.task || ""] = (rt[m.task || ""] || 0) + v; ct[roleOf(m.agent)] = (ct[roleOf(m.agent)] || 0) + v;
  });
  for (var k in cells) mx = Math.max(mx, cells[k].sum);
  var tb = el("table", "grid"), h = el("tr");
  add(h, el("th", "nosort", "Task"));
  rl.forEach(function (r) { add(h, el("th", "nosort num", r)); });
  add(h, el("th", "nosort num", "Total")); add(tb, add(el("thead"), h));
  var tbd = el("tbody");
  tl.forEach(function (t) {
    var tr = el("tr"); add(tr, el("td", null, t || "Overhead"));
    rl.forEach(function (r) {
      var c = cells[t + "|" + r], v = c ? c.sum : 0, td = el("td", "cell" + (v ? " hot" : ""), fmtVal(v));
      if (v) {
        td.setAttribute("style", "background:rgba(232,130,14," + (0.12 + 0.6 * v / (mx || 1)).toFixed(2) + ")");
        td.setAttribute("tabindex", "0");
        var f = function () { openCell(t, r); };
        td.addEventListener("click", f); td.addEventListener("keydown", function (e) { if (e.key === "Enter") f(); });
      }
      tr.appendChild(td);
    });
    add(tr, el("td", "cell", fmtVal(rt[t]))); tbd.appendChild(tr);
  });
  var fr = el("tr"); add(fr, el("td", null, "Total"));
  rl.forEach(function (r) { add(fr, el("td", "cell", fmtVal(ct[r]))); });
  add(fr, el("td", "cell", fmtVal(Object.keys(rt).reduce(function (a, k) { return a + rt[k]; }, 0))));
  tbd.appendChild(fr); tb.appendChild(tbd);
  add(gridBody, add(el("div", "frame"), tb));
}
function gridSection() {
  var s = el("section", null, null, { id: "grid" });
  add(s, el("h2", null, "Task × role"));
  var tools = el("div", "tools");
  [["cost", "Cost"], ["time", "Time"], ["tokens", "Tokens"]].forEach(function (m) {
    var b = el("button", st.metric === m[0] ? "on" : "", m[1], { type: "button" });
    b.addEventListener("click", function () { st.metric = m[0]; Array.prototype.forEach.call(tools.querySelectorAll("button"), function (x) { x.classList.remove("on"); }); b.classList.add("on"); drawGrid(); });
    tools.appendChild(b);
  });
  gridBody = el("div"); add(s, tools, gridBody);
  drawGrid();
  return s;
}

// ---------- timeline (Could) ----------
var tlBody;
function timelineSection() {
  var s = el("section", null, null, { id: "timeline" });
  add(s, el("h2", null, "Timeline"));
  var tools = el("div", "tools");
  var cb = el("input", null, null, { type: "checkbox", id: "compress", "aria-label": "Compress idle gaps over 1 h" });
  cb.checked = st.compress;
  cb.addEventListener("change", function () { st.compress = cb.checked; drawTimeline(); });
  var lab = el("label", null, " Compress idle gaps > 1 h (off = true scale)", { "for": "compress" });
  var sel = el("select", null, null, { "aria-label": "Highlight task", id: "hi" });
  add(sel, el("option", null, "Highlight task: none", { value: "" }));
  tasks.forEach(function (t) { add(sel, el("option", null, "Task " + t.id, { value: t.id })); });
  sel.addEventListener("change", function () { st.hi = sel.value; drawTimeline(); });
  add(tools, cb, lab, sel); add(s, tools, legend(true));
  tlBody = el("div"); s.appendChild(tlBody);
  drawTimeline();
  return s;
}
function drawTimeline() {
  tlBody.textContent = "";
  var total = T.wall_s || 0;
  var any = agents.some(function (a) { return (a.segments || []).length; });
  if (!any && !((T.po_wait || {}).items || []).length) { add(tlBody, el("div", "nodata", "No timeline")); return; }
  var t0 = ts(S.window && S.window.start) || 0;
  var end = total || Math.max.apply(null, agents.map(function (a) { var s = a.segments || []; return s.length ? s[s.length - 1][1] : 0; }));
  // active stretches (non-idle) for compression
  var act = [];
  agents.forEach(function (a) { (a.segments || []).forEach(function (g) { if (g[2] !== "i") act.push([g[0], g[1]]); }); });
  var items = (T.po_wait || {}).items || [];
  items.forEach(function (i) { var a = ts(i.raised_at) - t0, b = (i.answered_at ? ts(i.answered_at) : ts(S.window.end)) - t0; act.push([a, b]); });
  act.sort(function (a, b) { return a[0] - b[0]; });
  var merged = [];
  act.forEach(function (r) { var l = merged[merged.length - 1]; if (l && r[0] - l[1] <= 3600) l[1] = Math.max(l[1], r[1]); else merged.push([r[0], r[1]]); });
  var PX = 0.04, GAP = 34, map, width, gaps = [];
  if (st.compress && merged.length) {
    var acc = 0, pts = [];
    merged.forEach(function (m, i) {
      if (i > 0) { gaps.push({ x: acc, from: merged[i - 1][1], to: m[0] }); acc += GAP; }
      pts.push({ a: m[0], b: m[1], x: acc }); acc += (m[1] - m[0]) * PX;
    });
    width = acc;
    map = function (t) {
      for (var i = 0; i < pts.length; i++) { if (t <= pts[i].b || i === pts.length - 1) { return pts[i].x + Math.min(Math.max(t - pts[i].a, 0), pts[i].b - pts[i].a) * PX; } }
      return width;
    };
    // segments inside a gap collapse onto its edge; only idle ones live there
  } else { width = end * PX; map = function (t) { return t * PX; }; }
  width = Math.max(width, 200);
  var wrap = el("div", "tl");
  var hiT = st.hi ? taskById(st.hi) : null;
  function lane(name, onName) {
    var l = el("div", "lane"), nm = el("div", "nm", name, { title: name, tabindex: onName ? "0" : "-1" });
    if (onName) { nm.addEventListener("click", onName); nm.addEventListener("keydown", function (e) { if (e.key === "Enter") onName(); }); }
    var tr = el("div", "track", null, { style: "width:" + width.toFixed(0) + "px" });
    add(l, nm, tr); wrap.appendChild(l);
    gaps.forEach(function (g) { add(tr, el("div", "gap", "⋯ " + dur(g.to - g.from), { style: "left:" + g.x.toFixed(1) + "px;width:" + GAP + "px", title: "idle gap " + dur(g.to - g.from) })); });
    return tr;
  }
  // PO lane
  var pl = lane("PO wait", null);
  items.forEach(function (i) {
    var a = ts(i.raised_at) - t0, b = (i.answered_at ? ts(i.answered_at) : ts(S.window.end)) - t0, x = map(a);
    add(pl, el("div", "seg b-po", null, { style: "left:" + x.toFixed(1) + "px;width:" + Math.max(2, map(b) - x).toFixed(1) + "px", title: "escalation " + i.id + " " + (i.title || "") + " · " + dur(b - a) + (i.answered_at ? "" : " (open now)") }));
  });
  var CLS = { w: "working", a: "waiting", b: "blocking", i: "idle" };
  agents.forEach(function (a) {
    var tr = lane(a.name + (a.live ? " ▸ live" : ""), function () { openAgent(a.name); });
    if (a.transcript_found === false) { add(tr, el("span", "muted", "no transcript")); return; }
    (a.segments || []).forEach(function (g) {
      var x0 = map(g[0]), x1 = map(g[1]);
      if (x1 - x0 < 0.5 && g[2] === "i") return;
      var cls = CLS[g[2]] === "blocking" && g[4] === "PO" ? "b-po" : "b-" + CLS[g[2]];
      var dim = hiT && g[3] !== hiT.id;
      add(tr, el("div", "seg " + cls + (dim ? " dim" : ""), null, { style: "left:" + x0.toFixed(1) + "px;width:" + Math.max(1, x1 - x0).toFixed(1) + "px", title: CLS[g[2]] + " " + dur(g[1] - g[0]) + (g[3] ? " · task " + g[3] : "") + (g[4] ? " · on " + g[4] : "") + " · +" + dur(g[0]) }));
    });
    (a.events || []).forEach(function (e) {
      var sym = e[1] === "FAIL" ? "✕" : e[1] === "PASS" ? "✓" : "▸";
      add(tr, el("span", "ev " + e[1], sym, { style: "left:" + map(e[0]).toFixed(1) + "px;opacity:" + (hiT && e[2] !== hiT.id ? ".25" : "1"), title: e[1] + " " + (e[2] || "") + " · +" + dur(e[0]) }));
    });
    if (S.partial) add(tr, el("div", "nowline", null, { style: "left:" + map(end).toFixed(1) + "px", title: "now" }));
  });
  tlBody.appendChild(wrap);
}

// ---------- drawer ----------
function closeDrawer() { if (drawerEl) { drawerEl.remove(); drawerEl = null; } selected = null; }
function drawer(title) {
  closeDrawer();
  var d = el("aside", "drawer", null, { role: "dialog", "aria-label": title });
  var x = el("button", "x", "×", { "aria-label": "Close" });
  x.addEventListener("click", closeDrawer);
  add(d, x, el("h3", null, title));
  document.body.appendChild(d); drawerEl = d; x.focus();
  return d;
}
function mini(rows, heads) {
  var tb = el("table"), tr = el("tr");
  heads.forEach(function (h) { add(tr, el("th", "nosort", h)); });
  add(tb, add(el("thead"), tr));
  var tbd = el("tbody");
  rows.forEach(function (r) {
    var row = el("tr");
    r.cells.forEach(function (c) { var td = el("td", null, c); if (r.wrap) td.setAttribute("style", "white-space:normal"); row.appendChild(td); });
    if (r.onclick) { row.setAttribute("tabindex", "0"); row.addEventListener("click", r.onclick); row.addEventListener("keydown", function (e) { if (e.key === "Enter") r.onclick(); }); }
    tbd.appendChild(row);
  });
  tb.appendChild(tbd); return tb;
}
function btn(text, f) { var b = el("button", "btn", text, { type: "button" }); b.addEventListener("click", f); return b; }
function openTask(id) {
  var t = taskById(id); if (!t) return;
  var d = drawer("Task " + t.id + (t.title ? " · " + t.title : ""));
  selected = "t" + id;
  add(d, el("div", "muted", t.status + " · dev " + (t.dev || "–") + " · " + hm(t.window && t.window.start) + " → " + hm(t.window && t.window.end)));
  if ((t.aliases || []).length) add(d, el("div", "muted", "also named " + t.aliases.join(", ")));
  var c = el("div", "card", null, { style: "margin-top:8px" });
  add(c, el("div", null, "Agent-time " + dur(ttime(t)) + " (derived) · cycle " + (t.cycle_s ? dur(t.cycle_s) : "–") + " · cost " + usd(t.cost_usd) + " (estimated, list price) · tokens " + tok(sum(t.tokens || {}))),
    bar(t.buckets_s, BK, function (b) { return "b-" + b; }), legend(false), tokbar(t.tokens || {}));
  d.appendChild(c);
  var rw = (t.review_waits || []).reduce(function (a, r) { return a + (r.wait_s || 0); }, 0);
  if (rw) add(d, el("div", "muted", "Review wait " + dur(rw) + " (derived)"));
  add(d, el("h4", null, "Returns (FAIL messages)"));
  var rl = t.returns_list || [];
  if (!rl.length) add(d, el("div", "nodata", "No returns"));
  else {
    var tb = el("table"), tr = el("tr");
    ["#", "FAIL at", "Next HANDIN", "Rework"].forEach(function (h) { add(tr, el("th", "nosort", h)); });
    add(tb, add(el("thead"), tr));
    var tbd = el("tbody");
    rl.forEach(function (r, i) {
      var row = el("tr"); add(row, el("td", null, i + 1), el("td", null, hm(r.fail_at) + (r.fail_by ? " by " + r.fail_by : "")), el("td", null, hm(r.handin_at)), el("td", null, r.rework_s ? dur(r.rework_s) : "–"));
      tbd.appendChild(row);
      var rr = el("tr"), td = el("td", "reason", r.reason === null || r.reason === undefined ? "not shared" : r.reason, { colspan: "4" });
      if (r.reason === null || r.reason === undefined) td.classList.add("muted");
      add(rr, td); tbd.appendChild(rr);
    });
    tb.appendChild(tbd); d.appendChild(tb);
    add(d, el("div", "muted", "Total rework " + dur(t.rework_s) + " · " + usd(t.rework_cost_usd) + " (estimated, list price)"));
  }
  add(d, el("h4", null, "By role"));
  var byRole = {};
  (D.matrix || []).filter(function (m) { return m.task === t.id; }).forEach(function (m) {
    var r = roleOf(m.agent), o = byRole[r] = byRole[r] || { t: 0, c: 0 };
    o.t += sum(m.buckets_s || {}); o.c += m.cost_usd || 0;
  });
  var rows = Object.keys(byRole).map(function (r) { return { cells: [r, dur(byRole[r].t), usd(byRole[r].c)], onclick: function () { openCell(t.id, r); } }; });
  add(d, rows.length ? mini(rows, ["Role", "Time", "Cost"]) : el("div", "nodata", "No role data"));
  var bt = el("div", "tools");
  add(bt, btn("Show in timeline", function () { st.hi = t.id; var s = document.getElementById("hi"); if (s) s.value = t.id; drawTimeline(); scrollTo("timeline"); }), btn("Show in grid", function () { scrollTo("grid"); }));
  add(d, bt, el("div", "muted", "Developer time is attributed by roster and branch; other roles by the window from first mention to PASS."));
}
function openOverhead() {
  var d = drawer("Scope overhead"); selected = "over";
  var o = overheadItem();
  add(d, el("p", null, "Work that no task claims: agent turns outside any task window, plus idle time. It is a real cost, not an error."),
    el("div", null, "Agent-time " + dur(ttime(o)) + " (derived) · cost " + usd(o.cost_usd) + " (estimated, list price)"), bar(o.buckets_s, BK, function (b) { return "b-" + b; }));
}
function openRole(name) {
  var r = roleRows().filter(function (x) { return x.role === name; })[0]; if (!r) return;
  var d = drawer("Role " + name); selected = "r" + name;
  add(d, el("div", "muted", r.agents.length + " agents · " + r.sessions + " sessions · cost " + usd(r.cost) + " (estimated, list price)"),
    bar(r.buckets, BK, function (b) { return "b-" + b; }), legend(false),
    el("div", "sub muted", "Idle: waiting for work " + dur(r.idle_s.peer) + " · waiting for your chat reply " + dur(r.idle_s.human_input) + " (not PO wait)"));
  add(d, el("h4", null, "Agents"));
  add(d, mini(r.agents.map(function (a) { return { cells: [a.name + (a.live ? " (live)" : "") + (a.transcript_found === false ? " (no transcript)" : ""), a.sessions, dur(sum(a.buckets_s || {})), usd(a.cost_usd)], onclick: function () { openAgent(a.name); } }; }), ["Agent", "Sessions", "Time", "Cost"]));
  add(d, el("h4", null, "By task"));
  var byT = {};
  (D.matrix || []).forEach(function (m) { if (roleOf(m.agent) !== name) return; var k = m.task || "overhead"; var o = byT[k] = byT[k] || { t: 0, c: 0 }; o.t += sum(m.buckets_s || {}); o.c += m.cost_usd || 0; });
  add(d, mini(Object.keys(byT).map(function (k) { return { cells: [k, dur(byT[k].t), usd(byT[k].c)], onclick: k === "overhead" ? null : function () { openCell(k, name); } }; }), ["Task", "Time", "Cost"]));
}
function openAgent(name) {
  var a = roles.filter(function (x) { return x.name === name; })[0]; if (!a) return;
  var d = drawer("Agent " + name);
  add(d, el("div", "muted", (a.role || "") + " · " + a.sessions + " sessions" + (a.transcript_found === false ? " · no transcript" : "")),
    bar(a.buckets_s, BK, function (b) { return "b-" + b; }),
    el("div", "sub muted", "Idle: waiting for work " + dur((a.idle_s || {}).peer) + " · waiting for your chat reply " + dur((a.idle_s || {}).human_input) + " (not PO wait)"));
  add(d, btn("← " + (a.role || "role"), function () { openRole(a.role || name); }));
  var byT = {};
  (D.matrix || []).forEach(function (m) { if (m.agent !== name) return; var k = m.task || "overhead"; var o = byT[k] = byT[k] || { t: 0, c: 0 }; o.t += sum(m.buckets_s || {}); o.c += m.cost_usd || 0; });
  add(d, el("h4", null, "By task"), mini(Object.keys(byT).map(function (k) { return { cells: [k, dur(byT[k].t), usd(byT[k].c)] }; }), ["Task", "Time", "Cost"]));
}
function openCell(task, role) {
  var d = drawer((task ? "Task " + task : "Overhead") + " × " + role);
  var ms = (D.matrix || []).filter(function (m) { return (m.task || "") === (task || "") && roleOf(m.agent) === role; });
  var b = { working: 0, waiting: 0, blocking: 0, idle: 0 }, tk = { input: 0, cache_read: 0, cache_write: 0, output: 0 }, c = 0;
  ms.forEach(function (m) { BK.forEach(function (k) { b[k] += (m.buckets_s || {})[k] || 0; }); for (var k in tk) tk[k] += (m.tokens || {})[k] || 0; c += m.cost_usd || 0; });
  add(d, el("div", null, "Time " + dur(sum(b)) + " (derived) · cost " + usd(c) + " (estimated, list price)"), bar(b, BK, function (k) { return "b-" + k; }), tokbar(tk));
  var t = task ? taskById(task) : null;
  if (t) add(d, btn("← Task " + task, function () { openTask(task); }), btn("Show in timeline", function () { st.hi = task; var s = document.getElementById("hi"); if (s) s.value = task; drawTimeline(); scrollTo("timeline"); }));
}
function go(target) {
  if ((target.view === "tasks" || target.view === "returns") && target.id && taskById(target.id)) { scrollTo("tasks"); openTask(target.id); }
  else if (target.view === "roles" && target.id) { scrollTo("roles"); openRole(target.id); }
  else if (target.view === "tasks") scrollTo("tasks");
  else if (target.view === "roles") scrollTo("roles");
  else if (target.view === "matrix") scrollTo("grid");
  else if (target.view === "timeline" || target.view === "waits" || target.view === "returns") scrollTo(target.view === "returns" ? "tasks" : "timeline");
  else scrollTo("overview");
}
function scrollTo(id) { var n = document.getElementById(id); if (n) n.scrollIntoView(); }

document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeDrawer(); });

// ---------- assemble ----------
var mainEl = el("main");
add(mainEl, banners(), overview(), tasksSection(), rolesSection(), gridSection(), timelineSection());
add(app, header(), nav(), mainEl);
function spy() {
  var cur = "overview";
  ["overview", "tasks", "roles", "grid", "timeline"].forEach(function (id) { var n = document.getElementById(id); if (n && n.getBoundingClientRect().top < 90) cur = id; });
  Array.prototype.forEach.call(document.querySelectorAll("nav.sections a"), function (a) { a.classList.toggle("on", a.getAttribute("data-nav") === cur); });
}
window.addEventListener("scroll", spy);
spy();
})();
