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
var BN = { working: "Working", waiting: "Waiting (long tool call or background job)", blocking: "Blocking (waiting on a reply or the PO)", idle: "Idle (waiting for work, or for the PO's chat reply)" };

function bar(vals, keys, cls, total) {
  var b = el("div", "bar"), t = total || sum(vals) || 1;
  keys.forEach(function (k) {
    var v = vals[k] || 0;
    if (v <= 0) return;
    add(b, el("i", cls(k), null, { style: "width:" + (v / t * 100).toFixed(2) + "%", "data-tip": k + " " + dur(v) }));
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
function fail(title, text, detail) {
  var e = el("div", "errbox"), b = el("div", "banner bad", null, { role: "alert" });
  add(b, el("span", "ic", "!"), add(el("div"), el("b", null, title), document.createTextNode(" " + text)));
  add(e, el("h1", null, "The report data could not be read"), add(el("p", "muted"), document.createTextNode("This page shows "), el("code", null, "data.json"), document.createTextNode(", and it failed a check.")), b,
    el("pre", null, detail + "\nFix: run  squad-report <scope>  to rebuild report.html with the installed plugin."));
  app.appendChild(e);
}
if (!D || typeof D !== "object") { fail("The embedded data is not valid JSON.", "The report cannot be drawn.", "report/data.json  not valid JSON"); return; }
if (D.schema_version !== 1) { fail("schema_version " + D.schema_version + " not supported.", "This report was written by a newer squad-report; this page understands version 1.", "report/data.json  schema_version: " + D.schema_version + "\nexpected: 1"); return; }
if (D.kind !== "scope" || !D.totals || !D.scope) { fail("The data is not a scope report.", "Expected kind scope with totals and scope blocks.", "report/data.json  kind: " + D.kind); return; }

var S = D.scope, T = D.totals, tasks = D.tasks || [], roles = D.roles || [], agents = D.agents || [];
var hasData = (D.sources && D.sources.transcripts > 0) || T.agent_s > 0;
var selected = null, drawerEl = null;
var st = { sort: { k: "cost", dir: -1 }, rsort: { k: "cost", dir: -1 }, q: "", f: { ret: 0, flag: 0, run: 0 }, iter: "", metric: "cost", compress: true, hi: "" };

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
function banner(kind, title, text, links) {
  var b = el("div", "banner " + kind, null, { role: kind === "bad" ? "alert" : "status" });
  var d = el("div");
  add(d, el("b", null, title));
  if (text) add(d, document.createTextNode(" " + text));
  (links || []).forEach(function (l, i) { add(d, document.createTextNode(i ? ", " : " "), l); });
  add(b, el("span", "ic", kind === "info" ? "i" : "!"), d);
  return b;
}
// order as the mock: partial, empty, missing, low attribution, flag; each only when true for the data
function banners() {
  var box = el("div");
  if (S.status === "running")
    add(box, banner("info", "Partial: the scope is still running.", "Numbers cover up to " + hm(S.window && S.window.end) + ". Open tasks show their time so far. Re-run `squad-report " + S.name + "` to refresh; it is rebuilt on `squad-close`."));
  if (!hasData)
    add(box, banner("info", "No session data found for this scope.", "No transcript matched the roster and there are no messages yet. Nothing to chart. Check that the scope ran under this project, then run `squad-report " + S.name + "` again."));
  var miss = hasData ? roles.filter(function (a) { return a.transcript_found === false; }).map(function (a) { return a.name; }) : [];
  if (miss.length) add(box, banner("warn", "Transcripts missing:", miss.join(", ") + ". Their time and cost are not in the totals (shown as \u201cno transcript\u201d)."));
  var pct = T.attributed ? T.attributed.time_pct : null;
  if (hasData && pct !== null && pct < 60) add(box, banner("warn", "Only " + Math.round(pct) + "% of agent-time is attributed to tasks.", "Most work lands in Scope overhead, so the task table understates real task cost. Roles and totals are still right."));
  var flagged = tasks.filter(function (t) { return t.flag; });
  if (flagged.length) {
    var rw = tasks.reduce(function (a, t) { return a + (t.rework_s || 0); }, 0), rc = tasks.reduce(function (a, t) { return a + (t.rework_cost_usd || 0); }, 0);
    var n = flagged.length, fb = banner("bad", n + " task" + (n > 1 ? "s" : "") + " reached 3 or more returns", ""), bd = fb.querySelector("div");
    add(bd, document.createTextNode(" ("));
    flagged.forEach(function (t, i) {
      var a = el("a", null, "Task " + t.id, { href: "#tasks" });
      a.addEventListener("click", function (e) { e.preventDefault(); openTask(t.id); });
      add(bd, i ? document.createTextNode(", ") : null, a, document.createTextNode(": " + t.returns));
    });
    add(bd, document.createTextNode(") of " + (T.returns || 0) + " in all. Rework so far " + dur(rw) + ", about " + usd(rc) + "."));
    add(box, fb);
  }
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
  var c2 = card("PO wait · elapsed (derived)", nd ? "–" : dur(po.total_s), nd ? "no data" : po.count + " escalation" + (po.count === 1 ? "" : "s") + " · longest " + dur(po.longest_s) + (open ? " (open now)" : "") + " · " + (po.pct_of_elapsed || 0) + "% of elapsed · not agent cost");
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

// ---------- tables ----------
function faint(t) { return el("span", "faint", t); }
function fa(v, f) { return v ? f(v) : faint("–"); }
function table(cols, rows, sortState, rerender, onRow, emptyNode) {
  var tb = el("table"), th = el("thead"), tr = el("tr");
  cols.forEach(function (c) {
    var h = el("th", (c.num ? "num " : "") + (c.sort ? "" : "nosort"), c.h);
    if (c.tip) h.setAttribute("title", c.tip);
    if (c.sort) {
      h.setAttribute("tabindex", "0"); h.setAttribute("role", "columnheader");
      if (sortState.k === c.k) h.setAttribute("aria-sort", sortState.dir < 0 ? "descending" : "ascending");
      var f = function () { if (sortState.k === c.k) sortState.dir = -sortState.dir; else { sortState.k = c.k; sortState.dir = c.num ? -1 : 1; } rerender(); };
      h.addEventListener("click", f);
      h.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); f(); } });
    }
    tr.appendChild(h);
  });
  add(th, tr); tb.appendChild(th);
  var tbd = el("tbody");
  if (!rows.length && emptyNode) add(tbd, add(el("tr", null, null, { style: "cursor:default" }), add(el("td", null, null, { colspan: String(cols.length) }), emptyNode)));
  rows.forEach(function (r) {
    var row = el("tr", (r.cls || ""), null, { tabindex: "0", "data-key": r.key });
    if (selected === r.key) row.classList.add("sel");
    cols.forEach(function (c) {
      var v = c.cell(r.item), td = el("td", c.num ? "num" : "");
      if (c.ell) td.classList.add("ell");
      if (v && v.nodeType) td.appendChild(v); else td.textContent = v === undefined || v === null ? "–" : v;
      if (c.ttip) td.setAttribute("title", c.ttip(r.item) || "");
      row.appendChild(td);
    });
    var open = function () { setSel(r.key); onRow(r.item); };
    row.addEventListener("click", open);
    row.addEventListener("keydown", function (e) { if (e.key === "Enter") open(); });
    tbd.appendChild(row);
  });
  tb.appendChild(tbd);
  return tb;
}
function frame(t) { return add(el("div", "frame"), t); }
function emptyBox(b, msg) { return add(el("div", "empty"), el("b", null, b), document.createTextNode(msg)); }
function setSel(key) {
  selected = key;
  Array.prototype.forEach.call(document.querySelectorAll("tr.sel,td.sel"), function (x) { x.classList.remove("sel"); });
  if (key) Array.prototype.forEach.call(document.querySelectorAll('tr[data-key="' + String(key).replace(/"/g, "") + '"]'), function (x) { x.classList.add("sel"); });
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
function tb(buckets, total) { return add(el("span", "tb"), bar(buckets, BK, function (b) { return "b-" + b; }), el("span", "d", dur(total))); }
function costCell(c) { var w = el("span"); add(w, document.createTextNode(usd(c) + " "), faint(share(c))); return w; }
function ret(n, flag) {
  var p = el("span", "pill" + (n >= 3 ? " r" : n ? " m" : ""), n + (flag ? " ⚑" : ""));
  if (n >= 3) p.setAttribute("title", "3 or more returns: flagged");
  return p;
}
function sh(title, sub, tools) { return add(el("div", "sh"), el("h2", null, title), el("span", "sub", sub), tools); }

// ---------- tasks ----------
function overheadItem() {
  var row = { id: "overhead", over: true, title: "Scope overhead (unattributed)", buckets_s: { working: 0, waiting: 0, blocking: 0, idle: 0 }, tokens: { input: 0, cache_read: 0, cache_write: 0, output: 0 }, cost_usd: 0 };
  (D.matrix || []).filter(function (m) { return !m.task; }).forEach(function (m) {
    BK.forEach(function (b) { row.buckets_s[b] += (m.buckets_s || {})[b] || 0; });
    for (var k in row.tokens) row.tokens[k] += (m.tokens || {})[k] || 0;
    row.cost_usd += m.cost_usd || 0;
  });
  return row;
}
function reviewWait(t) { return (t.review_waits || []).reduce(function (a, r) { return a + (r.wait_s || 0); }, 0); }
function taskCols() {
  return [
    { h: "Task", k: "id", sort: 1, cell: function (t) { return t.over ? "—" : el("b", null, t.id); } },
    { h: "Title", k: "title", sort: 1, ell: 1, cell: function (t) { var s = t.title || ""; return el("span", t.over ? "muted" : "", s.length > 34 ? s.slice(0, 33) + "…" : (s || "–")); }, ttip: function (t) { return t.title; } },
    { h: "Iter", k: "iter", sort: 1, num: 1, cell: function (t) { return t.over ? "" : t.iteration; } },
    { h: "Dev", k: "dev", sort: 1, cell: function (t) { return t.over || !t.dev ? faint("–") : t.dev; } },
    { h: "Status", k: "status", sort: 1, cell: function (t) { return t.over ? "" : el("span", "chip " + (t.status === "passed" ? "done" : t.status === "running" ? "run" : ""), t.status); } },
    { h: "Returns (FAIL)", k: "returns", sort: 1, num: 1, cell: function (t) { return t.over ? "" : ret(t.returns || 0, t.flag); } },
    { h: "Time by bucket", k: "time", sort: 1, num: 1, cell: function (t) { return tb(t.buckets_s || {}, ttime(t)); } },
    { h: "Cycle", k: "cycle", sort: 1, num: 1, cell: function (t) { return t.over || !t.cycle_s ? faint("–") : document.createTextNode(dur(t.cycle_s) + (t.status === "running" ? " …" : "")); } },
    { h: "Review wait", k: "rw", sort: 1, num: 1, cell: function (t) { return fa(t.over ? 0 : reviewWait(t), dur); } },
    { h: "Tokens", k: "tokens", sort: 1, num: 1, cell: function (t) { return tok(sum(t.tokens || {})); } },
    { h: "Cost", k: "cost", sort: 1, num: 1, tip: "Estimated cost at list price", cell: function (t) { return costCell(t.cost_usd || 0); } },
    { h: "Rework", k: "rework", sort: 1, num: 1, cell: function (t) { return t.rework_s ? dur(t.rework_s) + " · " + usd(t.rework_cost_usd) : faint("–"); } }
  ];
}
var TG = {
  id: function (t) { return t.id; }, title: function (t) { return t.title || ""; }, iter: function (t) { return t.iteration; }, dev: function (t) { return t.dev || ""; },
  status: function (t) { return t.status || ""; }, returns: function (t) { return t.returns; }, time: ttime, cycle: function (t) { return t.cycle_s; },
  rw: reviewWait, tokens: function (t) { return sum(t.tokens || {}); }, cost: function (t) { return t.cost_usd; }, rework: function (t) { return t.rework_s; }
};
function tasksSection() {
  var s = el("section", null, null, { id: "tasks" }), body = el("div");
  function draw() {
    body.textContent = "";
    var q = st.q.toLowerCase();
    var list = tasks.filter(function (t) {
      if (q && (t.id + " " + (t.title || "") + " " + (t.dev || "")).toLowerCase().indexOf(q) < 0) return false;
      if (st.f.ret && !t.returns) return false;
      if (st.f.flag && !t.flag) return false;
      if (st.f.run && (!t.status || t.status === "passed")) return false;
      if (st.iter && String(t.iteration) !== st.iter) return false;
      return true;
    });
    var rows = sortRows(list, st.sort.k, st.sort.dir, TG).map(function (t) { return { item: t, key: "t" + t.id, cls: t.flag ? "flag" : "" }; });
    if (tasks.length && !q && !st.f.ret && !st.f.flag && !st.f.run && !st.iter) { var o = overheadItem(); rows.push({ item: o, key: "over", cls: "over" }); }
    var none = tasks.length ? emptyBox("No task matches the filter.", "Clear the filter or chips.") : emptyBox("No tasks yet.", "Tasks appear when the scope has sessions and messages.");
    add(body, frame(table(taskCols(), rows, st.sort, draw, function (t) { if (t.over) openTask("overhead"); else openTask(t.id); }, none)));
  }
  var tools = el("div", "tools");
  var inp = el("input", null, null, { type: "search", id: "tq", placeholder: "Filter tasks…", "aria-label": "Filter tasks" });
  inp.addEventListener("input", function () { st.q = inp.value; draw(); });
  add(tools, inp);
  [["ret", "Has returns"], ["flag", "Flagged"], ["run", "Not passed"]].forEach(function (c) {
    var b = el("button", "chip btn", c[1], { type: "button", "aria-pressed": "false" });
    b.addEventListener("click", function () { st.f[c[0]] = !st.f[c[0]]; b.setAttribute("aria-pressed", String(!!st.f[c[0]])); draw(); });
    tools.appendChild(b);
  });
  var iters = {}; tasks.forEach(function (t) { if (t.iteration !== null && t.iteration !== undefined) iters[t.iteration] = 1; });
  var sel = el("select", null, null, { "aria-label": "Iteration", id: "itf" });
  add(sel, el("option", null, "all", { value: "" }));
  Object.keys(iters).sort().forEach(function (i) { add(sel, el("option", null, i, { value: i })); });
  sel.addEventListener("change", function () { st.iter = sel.value; draw(); drawGrid(); });
  add(tools, add(el("label"), document.createTextNode("Iteration "), sel));
  add(s, sh("Tasks", "click a row for the task × role detail", tools), body, legend(false));
  draw();
  return s;
}

// ---------- roles ----------
var RG = {
  role: function (r) { return r.role; }, agents: function (r) { return r.agents.length; }, resp: function (r) { return Math.max(0, r.sessions - r.agents.length); },
  time: function (r) { return sum(r.buckets); }, po: function (r) { return r.po; }, tokens: function (r) { return sum(r.tokens); }, cost: function (r) { return r.cost; }
};
function rolesSection() {
  var s = el("section", null, null, { id: "roles" }), body = el("div");
  add(s, sh("Roles", "scope-wide, per agent"), body);
  var rr = roleRows();
  rr.forEach(function (r) { r.po = poByRole()[r.role] || 0; r.gone = r.agents.every(function (a) { return a.transcript_found === false; }); });
  var cols = [
    { h: "Role", k: "role", sort: 1, cell: function (r) { var w = el("span"); add(w, el("b", null, r.role)); if (r.live) add(w, el("span", "chip run", "live")); return w; } },
    { h: "Agents", k: "agents", sort: 1, num: 1, cell: function (r) { return r.gone ? el("span", "chip warn", "no transcript") : r.agents.length; } },
    { h: "Respawns", k: "resp", sort: 1, num: 1, cell: function (r) { return r.gone ? "–" : RG.resp(r); } },
    { h: "Time by bucket", k: "time", sort: 1, num: 1, cell: function (r) { return r.gone ? faint("–") : tb(r.buckets, sum(r.buckets)); } },
    { h: "Blocked on PO", k: "po", sort: 1, num: 1, cell: function (r) { return fa(r.po, dur); } },
    { h: "Tokens", k: "tokens", sort: 1, num: 1, cell: function (r) { return r.gone ? "–" : tok(sum(r.tokens)); } },
    { h: "Cost", k: "cost", sort: 1, num: 1, tip: "Estimated cost at list price", cell: function (r) { return r.gone ? "–" : costCell(r.cost); } }
  ];
  function draw() {
    body.textContent = "";
    var rows = sortRows(rr, st.rsort.k, st.rsort.dir, RG).map(function (r) { return { item: r, key: "r" + r.role }; });
    add(body, frame(table(cols, rows, st.rsort, draw, function (r) { openRole(r.role); }, emptyBox("No roles.", "")))); 
  }
  draw();
  return s;
}
var poBy = null;
function poByRole() {
  if (poBy) return poBy;
  poBy = {};
  agents.forEach(function (a) { var k = roleOf(a.name); (a.segments || []).forEach(function (g) { if (g[2] === "b" && g[4] === "PO") poBy[k] = (poBy[k] || 0) + g[1] - g[0]; }); });
  return poBy;
}

// ---------- grid ----------
var gridBody;
function cellVal(m) { return st.metric === "cost" ? m.cost_usd : st.metric === "time" ? sum(m.buckets_s || {}) : sum(m.tokens || {}); }
function fmtVal(v) { return st.metric === "cost" ? usd(v) : st.metric === "time" ? dur(v) : tok(v); }
function drawGrid() {
  if (!gridBody) return;
  gridBody.textContent = "";
  var mat = D.matrix || [];
  var trs = tasks.filter(function (t) { return !st.iter || String(t.iteration) === st.iter; }).map(function (t) { return { id: t.id, t: t }; });
  if (mat.some(function (m) { return !m.task; })) trs.push({ id: "", t: null });
  var rl = roleRows().map(function (r) { return r.role; });
  if (!tasks.length || !rl.length) { add(gridBody, add(el("div", "card empty"), el("b", null, "Nothing to cross yet."), document.createTextNode("The grid needs at least one task and one agent with a transcript."))); return; }
  var cells = {}, mx = 0;
  mat.forEach(function (m) {
    var k = (m.task || "") + "|" + roleOf(m.agent); cells[k] = (cells[k] || 0) + cellVal(m);
  });
  var rows = trs.map(function (r) { return rl.map(function (c) { var v = cells[r.id + "|" + c] || 0; mx = Math.max(mx, v); return v; }); });
  var rt = rows.map(function (a) { return a.reduce(function (x, y) { return x + y; }, 0); });
  var ct = rl.map(function (c, j) { return rows.reduce(function (x, a) { return x + a[j]; }, 0); });
  var tbl = el("table", "mx"), h = el("tr");
  add(h, el("th", "rl nosort"));
  rl.forEach(function (r) {
    var n = roleRows().filter(function (x) { return x.role === r; })[0].agents.length;
    add(h, el("th", "nosort", r, { title: n + " agent(s)" }));
  });
  add(h, el("th", "nosort", "Total")); add(tbl, add(el("thead"), h));
  var tbd = el("tbody");
  trs.forEach(function (r, i) {
    var tr = el("tr", null, null, { "data-key": "g" + r.id }), lab = el("td", "rl");
    if (r.t) {
      var ti = r.t.title || "";
      add(lab, el("b", null, r.t.id), document.createTextNode(" "), el("span", "muted", ti.slice(0, 22) + (ti.length > 22 ? "…" : "")));
      if (r.t.flag) lab.appendChild(document.createTextNode(" ⚑"));
    } else add(lab, el("span", "muted", "overhead"));
    tr.appendChild(lab);
    rl.forEach(function (c, j) {
      var v = rows[i][j], a = mx ? Math.min(0.85, v / mx * 0.85) : 0;
      var td = el("td", "cell" + (v ? "" : " zero"), v ? fmtVal(v) : "·", { style: "background:rgba(232,130,14," + a.toFixed(2) + ")" });
      if (v) {
        td.setAttribute("tabindex", "0");
        var f = function () { setSel(null); openCell(r.id, c); td.classList.add("sel"); };
        td.addEventListener("click", f); td.addEventListener("keydown", function (e) { if (e.key === "Enter") f(); });
      }
      tr.appendChild(td);
    });
    add(tr, add(el("td", "cell zero tot"), el("b", null, fmtVal(rt[i])))); tbd.appendChild(tr);
  });
  tbl.appendChild(tbd);
  var fr = el("tr"); add(fr, el("td", "rl", "Total"));
  ct.forEach(function (v) { add(fr, el("td", null, fmtVal(v))); });
  add(fr, el("td", null, fmtVal(rt.reduce(function (a, b) { return a + b; }, 0))));
  add(tbl, add(el("tfoot"), fr));
  add(gridBody, frame(tbl), el("div", "hint", "Cell colour = share of the largest cell. “·” = no activity."));
}
function gridSection() {
  var s = el("section", null, null, { id: "grid" });
  var tools = el("div", "tools");
  var sel = el("select", null, null, { id: "mx", "aria-label": "Metric" });
  [["cost", "Cost"], ["time", "Time"], ["tokens", "Tokens"]].forEach(function (m) { add(sel, el("option", null, m[1], { value: m[0] })); });
  sel.value = st.metric;
  sel.addEventListener("change", function () { st.metric = sel.value; drawGrid(); });
  add(tools, add(el("label"), document.createTextNode("Show "), sel));
  gridBody = el("div");
  add(s, sh("Task × role", "who spent what on which task; click a cell. Follows the iteration filter", tools), gridBody);
  drawGrid();
  return s;
}

// ---------- timeline ----------
var tlBody;
var SVGNS = "http:" + "//www.w3.org/2000/svg";
function sv(tag, attrs, text) {
  var n = document.createElementNS(SVGNS, tag);
  if (attrs) for (var k in attrs) n.setAttribute(k, attrs[k]);
  if (text !== undefined) n.textContent = text;
  return n;
}
function dt(sec) {
  return new Date(sec * 1000).toLocaleString("en-GB", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "UTC" }) + " UTC";
}
function timelineSection() {
  var s = el("section", null, null, { id: "timeline" });
  var tools = el("div", "tools");
  var cb = el("input", null, null, { type: "checkbox", id: "cmp" });
  cb.checked = st.compress;
  cb.addEventListener("change", function () { st.compress = cb.checked; drawTimeline(); });
  var sel = el("select", null, null, { "aria-label": "Highlight task", id: "hi" });
  add(sel, el("option", null, "none", { value: "" }));
  tasks.forEach(function (t) { add(sel, el("option", null, t.id, { value: t.id })); });
  sel.addEventListener("change", function () { st.hi = sel.value; drawTimeline(); });
  add(tools, add(el("label"), cb, document.createTextNode(" Compress idle gaps > 1 h")), add(el("label"), document.createTextNode("Highlight task "), sel));
  tlBody = el("div", "tl");
  var lg = legend(false), gl = el("div", "legend");
  add(gl, el("span", null, "▲ blocked"), el("span", null, "✕ FAIL (return)", { style: "color:var(--fail)" }), el("span", null, "▸ HANDIN", { style: "color:var(--mangotxt)" }), el("span", null, "✓ PASS", { style: "color:var(--work)" }), sw("b-po", "blocking, waiting on the PO"));
  add(s, sh("Timeline", "one lane per agent, coloured by bucket", tools), tlBody, lg, gl);
  return s;
}
function drawTimeline() {
  tlBody.textContent = "";
  var items = (T.po_wait || {}).items || [];
  if (!agents.some(function (a) { return (a.segments || []).length; })) { add(tlBody, emptyBox("No timeline.", "No agent has transcript activity in this scope yet.")); return; }
  var t0 = ts(S.window && S.window.start) || 0;
  var T1 = T.wall_s || Math.max.apply(null, agents.map(function (a) { var g = a.segments || []; return g.length ? g[g.length - 1][1] : 0; }));
  var wend = ts(S.window && S.window.end) ? ts(S.window.end) - t0 : T1;
  var W = Math.max(300, tlBody.clientWidth - 24), LW = W > 700 ? 150 : 90, LH = 22, GAP = 6, TOP = 22, H = TOP + (agents.length + 1) * (LH + GAP) + 8;
  var act = [];
  agents.forEach(function (a) { (a.segments || []).forEach(function (g) { if (g[2] !== "i") act.push([g[0], g[1]]); }); });
  pw = items.map(function (i) { var a = ts(i.raised_at) - t0; return [a, (i.answered_at ? ts(i.answered_at) - t0 : wend), !i.answered_at, i]; });
  var pw = items.map(function (i) { var a = ts(i.raised_at) - t0; return [a, (i.answered_at ? ts(i.answered_at) - t0 : wend), !i.answered_at, i]; });
  pw.forEach(function (p) { act.push([p[0], p[1]]); });
  act.sort(function (a, b) { return a[0] - b[0]; });
  var un = [];
  act.forEach(function (g) { var l = un[un.length - 1]; if (l && g[0] <= l[1] + 3600) l[1] = Math.max(l[1], g[1]); else un.push([g[0], g[1]]); });
  var pcs = [], c = 0;
  if (st.compress) {
    un.forEach(function (u) { if (u[0] > c + 3600) pcs.push({ a: c, b: u[0], z: 1 }); pcs.push({ a: Math.max(c, u[0] > c + 3600 ? u[0] : c), b: u[1] }); c = u[1]; });
    if (T1 > c + 3600) pcs.push({ a: c, b: T1, z: 1 }); else pcs.push({ a: c, b: T1 });
  } else pcs = [{ a: 0, b: T1 }];
  var CW = 34, nz = pcs.filter(function (p) { return p.z; }).length, usable = W - LW - nz * CW;
  var secs = pcs.filter(function (p) { return !p.z; }).reduce(function (a, p) { return a + p.b - p.a; }, 0) || 1, k = usable / secs, x = LW;
  pcs.forEach(function (p) { p.x = x; p.w = p.z ? CW : (p.b - p.a) * k; x += p.w; });
  function X(t) { var p = pcs.filter(function (q) { return t >= q.a && t <= q.b; })[0] || pcs[pcs.length - 1]; return p.x + (t - p.a) / (p.b - p.a || 1) * p.w; }
  var hiT = st.hi ? taskById(st.hi) : null;
  var svg = sv("svg", { viewBox: "0 0 " + W + " " + H, height: H, role: "img", "aria-label": "Per-agent timeline" });
  var defs = sv("defs");
  [["hatch", "#DB3B22", "#E9705B"], ["hatchpo", "#9A40CF", "#B966E8"]].forEach(function (p) {
    var pt = sv("pattern", { id: p[0], width: 6, height: 6, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" });
    add(pt, sv("rect", { width: 6, height: 6, fill: p[1] }), sv("rect", { width: 3, height: 6, fill: p[2] }));
    defs.appendChild(pt);
  });
  svg.appendChild(defs);
  pcs.forEach(function (p) {
    if (p.z) {
      var cx = p.x + p.w / 2;
      add(svg, sv("rect", { x: p.x, y: TOP - 4, width: p.w, height: H - TOP, fill: "#F4ECDD" }),
        sv("text", { "class": "gaptx", x: cx, y: TOP + 14, "text-anchor": "middle", transform: "rotate(-90 " + cx + " " + (TOP + 14) + ")", dy: 3, "data-tip": "Idle gap " + dur(p.b - p.a) + " compressed" }, "⋯ " + dur(p.b - p.a)));
    } else {
      add(svg, sv("line", { x1: p.x, x2: p.x, y1: TOP - 4, y2: H, stroke: "#E7DBC8" }));
      if (st.compress && !(S.status === "running" && p.x > W - 100)) { var late = p.x > W - 100; add(svg, sv("text", { "class": "ax", x: late ? p.x - 3 : p.x + 3, y: 12, "text-anchor": late ? "end" : "start" }, dt(t0 + p.a).replace(" UTC", ""))); }
    }
  });
  if (!st.compress) for (var t = Math.ceil(t0 / 21600) * 21600; t < t0 + T1; t += 21600)
    add(svg, sv("line", { x1: X(t - t0), x2: X(t - t0), y1: TOP - 4, y2: H, stroke: "#E7DBC8", "stroke-dasharray": "2 4" }), sv("text", { "class": "ax", x: X(t - t0) + 3, y: 12 }, new Date(t * 1000).toISOString().slice(5, 16).replace("T", " ")));
  if (hiT && hiT.window) {
    var ha = Math.max(ts(hiT.window.start) - t0, 0), hb = Math.min(ts(hiT.window.end) - t0, T1);
    if (hb > ha) add(svg, sv("rect", { x: X(ha), y: TOP - 4, width: Math.max(2, X(hb) - X(ha)), height: H - TOP, fill: "#E8820E", opacity: ".08" }));
  }
  function lane(i, name, cls, onName, full) {
    var y = TOP + i * (LH + GAP), mc = Math.floor((LW - 12) / 6.4);
    var lbl = sv("text", { "class": "lane-l" + (cls ? " " + cls : ""), x: LW - 8, y: y + LH / 2 + 4, "text-anchor": "end" }, name.length > mc ? name.slice(0, Math.ceil((mc - 1) / 2)) + "…" + name.slice(name.length - Math.floor((mc - 1) / 2)) : name);
    if (name.length > mc || full) lbl.setAttribute("data-tip", full || name);
    if (onName) { lbl.setAttribute("tabindex", "0"); lbl.addEventListener("click", onName); lbl.addEventListener("keydown", function (e) { if (e.key === "Enter") onName(); }); }
    add(svg, lbl, sv("rect", { x: LW, y: y, width: W - LW, height: LH, fill: "#FCF8F1", stroke: "#E7DBC8", rx: 3 }));
    return y;
  }
  var py = lane(0, "PO wait", "po");
  pw.forEach(function (p) {
    add(svg, sv("rect", { x: X(p[0]), y: py + 2, width: Math.max(2, X(p[1]) - X(p[0])), height: LH - 4, fill: "url(#hatchpo)", "data-tip": "Escalation open " + dur(p[1] - p[0]) + (p[2] ? " (still open)" : "") + " · " + dt(t0 + p[0]) }));
  });
  var CLS = { w: "working", a: "waiting", b: "blocking", i: "idle" }, FILL = { w: "var(--work)", a: "var(--wait)", i: "var(--idle)" };
  var GL = { FAIL: ["✕", "#CE1D6C"], HANDIN: ["▸", "#CE7000"], PASS: ["✓", "#368A1E"] };
  agents.forEach(function (a, i0) {
    var y = lane(i0 + 1, a.name, "", function () { openAgent(a.name); });
    if (a.transcript_found === false) { add(svg, sv("text", { "class": "gaptx", x: LW + 8, y: y + LH / 2 + 4 }, "no transcript")); return; }
    (a.segments || []).forEach(function (g) {
      var x1 = X(g[0]), x2 = X(g[1]), w = Math.max(1, x2 - x1), po = g[2] === "b" && g[4] === "PO";
      if (g[2] === "i" && x2 - x1 < 0.5) return;
      var dim = hiT && g[3] !== hiT.id;
      var r = sv("rect", { "class": "seg" + (dim ? " dim" : ""), x: x1.toFixed(1), y: y + 2, width: w.toFixed(1), height: LH - 4, fill: g[2] === "b" ? (po ? "url(#hatchpo)" : "url(#hatch)") : FILL[g[2]],
        "data-tip": a.name + " · " + BN[CLS[g[2]]] + (po ? " – waiting on the PO" : g[4] ? " – on " + g[4] : "") + " · " + dur(g[1] - g[0]) + (g[3] ? " · task " + g[3] : "") + " · " + dt(t0 + g[0]) });
      if (g[2] === "i") r.setAttribute("opacity", ".35");
      svg.appendChild(r);
    });
    (a.events || []).forEach(function (e) {
      var g = GL[e[1]]; if (!g) return;
      var dim = hiT && e[2] !== hiT.id;
      var ev = sv("text", { "class": "ev", x: X(e[0]), y: y + LH / 2 + 5, "text-anchor": "middle", "font-size": 14, "font-weight": 800, fill: g[1], stroke: "#fff", "stroke-width": 2.5, "paint-order": "stroke", "data-tip": e[1] + (e[2] ? " task " + e[2] : "") + " · " + dt(t0 + e[0]) }, g[0]);
      if (dim) ev.setAttribute("opacity", ".25");
      svg.appendChild(ev);
    });
    if (a.live) add(svg, sv("text", { x: W - 6, y: y + LH / 2 + 4, "text-anchor": "end", "font-size": 11, fill: "#CE7000" }, "▸ live"));
  });
  if (S.status === "running") add(svg, sv("line", { x1: X(T1), x2: X(T1), y1: TOP - 4, y2: H, stroke: "#E8820E", "stroke-width": 2, "stroke-dasharray": "4 3" }), sv("text", { "class": "ax", x: X(T1) - 4, y: 12, "text-anchor": "end", fill: "#CE7000" }, "now"));
  tlBody.appendChild(svg);
}

// ---------- drawer ----------
var closeT = 0;
drawerEl = el("aside", "drawer", null, { role: "dialog", "aria-label": "Details", "aria-hidden": "true" });
function closeDrawer() {
  drawerEl.classList.remove("open"); drawerEl.setAttribute("aria-hidden", "true");
  setSel(null);
  clearTimeout(closeT);
  closeT = setTimeout(function () { if (!drawerEl.classList.contains("open")) drawerEl.textContent = ""; }, 300);
}
function drawer(label) {
  clearTimeout(closeT);
  drawerEl.textContent = "";
  drawerEl.setAttribute("aria-label", label); drawerEl.removeAttribute("aria-hidden");
  var x = el("button", "x", "×", { "aria-label": "Close", type: "button" });
  x.addEventListener("click", closeDrawer);
  drawerEl.appendChild(x);
  drawerEl.classList.add("open"); drawerEl.scrollTop = 0; x.focus();
  return drawerEl;
}
function h3(text, extra) { var h = el("h3", null, text); if (extra) add(h, document.createTextNode(" "), extra); return h; }
function mini(rows, heads, nums) {
  nums = nums || [];
  var t = el("table");
  if (heads) { var tr = el("tr"); heads.forEach(function (h, i) { add(tr, el("th", "nosort" + (nums.indexOf(i) >= 0 ? " num" : ""), h)); }); add(t, add(el("thead"), tr)); }
  var tbd = el("tbody");
  rows.forEach(function (r) {
    var row = el("tr");
    r.cells.forEach(function (c, i) { var td = el("td", nums.indexOf(i) >= 0 ? "num" : ""); if (c && c.nodeType) td.appendChild(c); else td.textContent = c === undefined || c === null ? "" : c; row.appendChild(td); });
    if (r.onclick) { row.setAttribute("tabindex", "0"); row.addEventListener("click", r.onclick); row.addEventListener("keydown", function (e) { if (e.key === "Enter") r.onclick(); }); }
    else row.style.cursor = "default";
    tbd.appendChild(row);
  });
  t.appendChild(tbd); return frame(t);
}
function btn(text, f, ghost) { var b = el("button", "act" + (ghost ? " ghost" : ""), text, { type: "button" }); b.addEventListener("click", f); return b; }
function idleSub(peer, human) {
  var d = el("div", "idlesub", "Idle: waiting for work " + dur(peer) + " · waiting for your chat reply " + dur(human) + " ");
  return add(d, faint("(not PO wait)"));
}
function legendK() {
  var l = el("div", "legend"), L = { input: "Input", cache_read: "Cache read", cache_write: "Cache write", output: "Output" };
  ["input", "cache_read", "cache_write", "output"].forEach(function (k) { add(l, sw("t-" + k, L[k])); });
  return l;
}
function showInTimeline(task) {
  if (task) { st.hi = task; var s = document.getElementById("hi"); if (s) s.value = task; drawTimeline(); }
  closeDrawer(); scrollTo("timeline");
}
function byTaskRows(filter, role) {
  var by = {};
  (D.matrix || []).forEach(function (m) {
    if (!filter(m)) return;
    var k = m.task || "overhead", o = by[k] = by[k] || { b: { working: 0, waiting: 0, blocking: 0, idle: 0 }, c: 0 };
    BK.forEach(function (b) { o.b[b] += (m.buckets_s || {})[b] || 0; }); o.c += m.cost_usd || 0;
  });
  return Object.keys(by).sort(function (a, b) { return by[b].c - by[a].c; }).map(function (k) {
    var o = by[k];
    return { cells: [k === "overhead" ? "overhead" : "Task " + k, bar(o.b, BK, function (b) { return "b-" + b; }), dur(sum(o.b)), usd(o.c)], onclick: role && k !== "overhead" ? function () { openCell(k, role); } : role ? function () { openCell("", role); } : null };
  });
}
function openTask(id) {
  var over = id === "overhead", t = over ? overheadItem() : taskById(id); if (!t) return;
  var d = drawer(over ? "Scope overhead" : "Task " + t.id);
  setSel(over ? "over" : "t" + id);
  var h = el("h2", null, over ? "Scope overhead " : "Task " + t.id + " ");
  add(h, over ? el("span", "chip", "unattributed") : el("span", "chip " + (t.status === "passed" ? "done" : t.status === "running" ? "run" : ""), t.status));
  add(d, h);
  var info = el("div", "muted", null, { style: "margin:2px 0 10px" });
  add(info, document.createTextNode((t.title || "") + (t.dev ? " · dev " + t.dev : "")));
  if (t.window && t.window.start) add(info, el("br"), document.createTextNode(dt(ts(t.window.start)) + " → " + dt(ts(t.window.end))));
  if ((t.aliases || []).length) add(info, el("br"), faint("also named " + t.aliases.join(", ")));
  add(d, info);
  var c = el("div", "card"), b = function (x) { return el("b", null, x); };
  add(c, b(dur(ttime(t))), document.createTextNode(" agent-time" + (t.cycle_s ? " · cycle " + dur(t.cycle_s) : "") + (!over && reviewWait(t) ? " · review wait " + dur(reviewWait(t)) : "") + " · "), b(usd(t.cost_usd)), document.createTextNode(" · "), b(tok(sum(t.tokens || {}))), document.createTextNode(" tokens "),
    bar(t.buckets_s, BK, function (k) { return "b-" + k; }), el("div", null, null, { style: "height:6px" }), tokbar(t.tokens || {}));
  add(d, c);
  add(d, h3("Returns (FAIL messages)", t.flag ? el("span", "chip bad", "3+ flagged") : null));
  var rl = t.returns_list || [];
  if (!rl.length) add(d, el("div", "muted", "No returns."));
  else {
    var tbl = el("table"), hr = el("tr");
    [["#", 0], ["FAIL · by", 0], ["Next HANDIN", 0], ["Rework", 1]].forEach(function (x) { add(hr, el("th", "nosort" + (x[1] ? " num" : ""), x[0])); });
    add(tbl, add(el("thead"), hr));
    var tbd = el("tbody");
    rl.forEach(function (r, i) {
      var row = el("tr", null, null, { style: "cursor:default" }), f = el("td");
      add(f, document.createTextNode(r.fail_at ? dt(ts(r.fail_at)) : "–"));
      if (r.fail_by) add(f, el("br"), faint("by " + r.fail_by));
      add(row, el("td", null, i + 1), f, el("td", null, r.handin_at ? dt(ts(r.handin_at)) : "–"), el("td", "num", r.rework_s ? dur(r.rework_s) : "–"));
      tbd.appendChild(row);
      var rr = el("tr", "rsn", null, { style: "cursor:default" }), td = el("td", null, null, { colspan: "3" }), hide = r.reason === null || r.reason === undefined;
      add(td, hide ? faint("not shared") : el("span", "reason", r.reason));
      add(rr, el("td"), td); tbd.appendChild(rr);
    });
    add(tbl, tbd, add(el("tfoot"), add(el("tr"), el("td", null, "Total rework", { colspan: "3" }), el("td", "num", dur(t.rework_s) + " · " + usd(t.rework_cost_usd)))));
    add(d, frame(tbl));
  }
  add(d, h3("By role"));
  var byRole = {};
  (D.matrix || []).filter(function (m) { return over ? !m.task : m.task === t.id; }).forEach(function (m) {
    var r = roleOf(m.agent), o = byRole[r] = byRole[r] || { b: { working: 0, waiting: 0, blocking: 0, idle: 0 }, c: 0 };
    BK.forEach(function (k) { o.b[k] += (m.buckets_s || {})[k] || 0; }); o.c += m.cost_usd || 0;
  });
  var rows = Object.keys(byRole).sort(function (p, q) { return byRole[q].c - byRole[p].c; }).map(function (r) {
    return { cells: [r, tb(byRole[r].b, sum(byRole[r].b)), usd(byRole[r].c)], onclick: function () { openCell(over ? "" : t.id, r); } };
  });
  add(d, rows.length ? mini(rows, ["Role", "Time", "Cost"], [2]) : el("div", "muted", "No agent time."));
  add(d, add(el("div", "acts"), btn("Show in timeline", function () { if (over) { closeDrawer(); scrollTo("timeline"); } else showInTimeline(t.id); }), btn("Show in grid", function () { closeDrawer(); scrollTo("grid"); }, true)));
  add(d, el("p", "note", over ? "Time that no rule could attach to a task: planning, BA, Manager, retro." : "Developer time by roster and branch; other roles by the window first mention → PASS."));
}
function openOverhead() { openTask("overhead"); }
function openRole(name) {
  var r = roleRows().filter(function (x) { return x.role === name; })[0]; if (!r) return;
  if (r.agents.every(function (a) { return a.transcript_found === false; })) return;
  var d = drawer("Role " + name); setSel("r" + name);
  var respawns = Math.max(0, r.sessions - r.agents.length);
  add(d, add(el("h2", null, name + " "), el("span", "chip", r.agents.length + " agent" + (r.agents.length > 1 ? "s" : "") + " · " + respawns + " respawns")));
  var c = el("div", "card", null, { style: "margin-top:8px" });
  add(c, el("b", null, dur(sum(r.buckets))), document.createTextNode(" · "), el("b", null, usd(r.cost)), document.createTextNode(" "), bar(r.buckets, BK, function (b) { return "b-" + b; }), idleSub(r.idle_s.peer, r.idle_s.human_input));
  add(d, c, h3("Agents"));
  add(d, mini(r.agents.map(function (a) {
    var ok = a.transcript_found !== false;
    return { cells: [a.name, ok ? a.sessions + " session" + (a.sessions > 1 ? "s" : "") : el("span", "chip warn", "no transcript"), ok ? dur(sum(a.buckets_s || {})) : "", ok ? usd(a.cost_usd) : ""], onclick: function () { openAgent(a.name); } };
  }), null, [2, 3]));
  add(d, h3("By task"), mini(byTaskRows(function (m) { return roleOf(m.agent) === name; }, name), null, [2, 3]));
}
function openAgent(name) {
  var a = roles.filter(function (x) { return x.name === name; })[0]; if (!a || a.transcript_found === false) return;
  var d = drawer("Agent " + name); setSel(null);
  add(d, el("h2", null, name), el("div", "muted", (a.role || "") + " · " + a.sessions + " session" + (a.sessions > 1 ? "s" : "")));
  var c = el("div", "card", null, { style: "margin-top:8px" });
  add(c, el("b", null, dur(sum(a.buckets_s || {}))), document.createTextNode(" · "), el("b", null, usd(a.cost_usd)), document.createTextNode(" "), bar(a.buckets_s, BK, function (b) { return "b-" + b; }), idleSub((a.idle_s || {}).peer, (a.idle_s || {}).human_input));
  add(d, c, h3("By task"), mini(byTaskRows(function (m) { return m.agent === name; }, null), null, [2, 3]));
  add(d, add(el("div", "acts"), btn("← " + (a.role || "role"), function () { openRole(a.role || name); }, true), btn("Show lane in timeline", function () { closeDrawer(); scrollTo("timeline"); })));
}
function openCell(task, role) {
  var d = drawer((task ? "Task " + task : "Scope overhead") + " × " + role); setSel(null);
  add(d, el("h2", null, (task ? "Task " + task : "Scope overhead") + " × " + role));
  var ms = (D.matrix || []).filter(function (m) { return (m.task || "") === (task || "") && roleOf(m.agent) === role; });
  var b = { working: 0, waiting: 0, blocking: 0, idle: 0 }, tk = { input: 0, cache_read: 0, cache_write: 0, output: 0 }, c = 0;
  ms.forEach(function (m) { BK.forEach(function (k) { b[k] += (m.buckets_s || {})[k] || 0; }); for (var k in tk) tk[k] += (m.tokens || {})[k] || 0; c += m.cost_usd || 0; });
  if (!ms.length) add(d, emptyBox("No activity.", "This agent did not work on this task."));
  else {
    var cd = el("div", "card");
    add(cd, el("b", null, dur(sum(b))), document.createTextNode(" · "), el("b", null, usd(c)), document.createTextNode(" · "), el("b", null, tok(sum(tk))), document.createTextNode(" tokens "),
      bar(b, BK, function (k) { return "b-" + k; }), el("div", null, null, { style: "height:6px" }), tokbar(tk), legendK());
    add(d, cd);
  }
  var t0 = ts(S.window && S.window.start) || 0, evs = [];
  agents.forEach(function (a) { if (roleOf(a.name) === role) (a.events || []).forEach(function (e) { if (e[1] !== "BLOCKED" && (e[2] || "") === (task || "")) evs.push(e); }); });
  evs.sort(function (p, q) { return p[0] - q[0]; });
  if (evs.length) add(d, h3("Messages"), mini(evs.map(function (e) { return { cells: [dt(t0 + e[0]), el("b", null, e[1])] }; }), null));
  var acts = el("div", "acts", null, { style: "margin-top:10px" });
  if (task && taskById(task)) add(acts, btn("← Task " + task, function () { openTask(task); }, true));
  add(acts, btn("Show in timeline", function () { showInTimeline(task && taskById(task) ? task : ""); }));
  add(d, acts);
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
function scrollTo(id) {
  var n = document.getElementById(id); if (!n) return;
  n.scrollIntoView({ block: "start" });
  n.classList.remove("flash"); void n.offsetWidth; n.classList.add("flash");
}

var tipEl = el("div", null, null, { id: "tip" });
document.addEventListener("mousemove", function (e) {
  var t = e.target.closest && e.target.closest("[data-tip]");
  if (!t) { tipEl.style.display = "none"; return; }
  tipEl.textContent = t.getAttribute("data-tip"); tipEl.style.display = "block";
  tipEl.style.left = Math.max(4, Math.min(e.clientX + 12, innerWidth - 310)) + "px"; tipEl.style.top = (e.clientY + 14) + "px";
});
document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeDrawer(); });

// ---------- assemble ----------
var mainEl = el("main");
add(mainEl, banners(), overview(), tasksSection(), rolesSection(), gridSection(), timelineSection());
add(app, header(), nav(), mainEl);
document.body.appendChild(drawerEl); document.body.appendChild(tipEl);
drawTimeline();
var rzT; window.addEventListener("resize", function () { clearTimeout(rzT); rzT = setTimeout(drawTimeline, 120); });
function spy() {
  var cur = "overview";
  ["overview", "tasks", "roles", "grid", "timeline"].forEach(function (id) { var n = document.getElementById(id); if (n && n.getBoundingClientRect().top < 90) cur = id; });
  Array.prototype.forEach.call(document.querySelectorAll("nav.sections a"), function (a) { a.classList.toggle("on", a.getAttribute("data-nav") === cur); });
}
window.addEventListener("scroll", spy);
spy();
})();
