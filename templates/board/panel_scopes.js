/* squad-board picker and views (ticket 11): the landing picker, the header context line with the switcher sheet,
   the opening order (flag, URL, saved choice, picker), and the "Scopes of this goal" panel.
   Pure rules are on BOARD (filterRows, topRow, pushRecent, parseHash, openingOrder, notFoundText, shouldFocusSearch,
   flatRows, otherNeeds) so a test page can call them. Names come from agent-written files and from the URL:
   they reach the DOM only through textContent, and are matched against the API's list, never used as code or selectors. */
(function (root) {
  "use strict";
  var BOARD = root.BOARD = root.BOARD || {};
  var RECENT_MAX = 5;
  var NAME_OK = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;

  /* ---------- pure rules ---------- */
  /* case-insensitive substring on name or brief; empty text keeps every row (Done rows included) */
  function filterRows(rows, text) {
    var t = String(text == null ? "" : text).trim().toLowerCase();
    if (!t) return (rows || []).slice();
    return (rows || []).filter(function (r) {
      return String(r.name || "").toLowerCase().indexOf(t) >= 0 || String(r.brief || "").toLowerCase().indexOf(t) >= 0;
    });
  }
  /* the row Enter opens: the first visible one */
  function topRow(visible) { return visible && visible.length ? visible[0] : null; }
  /* newest first, the same choice once, at most 5 */
  function pushRecent(list, choice) {
    if (!choice || !choice.kind || !choice.name) return (list || []).slice(0, RECENT_MAX);
    var rest = (list || []).filter(function (c) { return !(c && c.kind === choice.kind && c.name === choice.name); });
    return [{ kind: choice.kind, name: choice.name }].concat(rest).slice(0, RECENT_MAX);
  }
  /* "#/goal/G" or "#/scope/S" -> {kind, name}; anything else is null (the picker) */
  function parseHash(h) {
    var m = /^#\/(goal|scope)\/(.+)$/.exec(String(h || ""));
    if (!m) return null;
    var name;
    try { name = decodeURIComponent(m[2]); } catch (e) { return null; }
    return name ? { kind: m[1], name: name } : null;
  }
  function hashFor(c) { return "#/" + c.kind + "/" + encodeURIComponent(c.name); }
  function notFoundText(c, source) {
    if (!c) return "";
    if (source === "saved") return "saved choice " + c.name + " not found";
    return c.kind + " " + c.name + " not found";
  }
  /* flag > URL > saved choice > picker. exists(choice) answers "open", "closed" or "gone".
     -> {choice, source, closed, notFound}. A name that is gone never opens; the picker says so. */
  function openingOrder(o) {
    var steps = [["flag", o.flag, "flag"], ["url", o.hash, "url"], ["saved", o.saved, "saved"]];
    for (var i = 0; i < steps.length; i++) {
      var c = steps[i][1];
      if (!c || !c.kind || !c.name) continue;
      var st = o.exists ? o.exists(c) : "open";
      if (st === "gone") return { choice: null, source: "picker", closed: false, notFound: notFoundText(c, steps[i][0]) };
      return { choice: { kind: c.kind, name: c.name }, source: steps[i][0], closed: st === "closed", notFound: null };
    }
    return { choice: null, source: "picker", closed: false, notFound: null };
  }
  /* "/" must not steal the key from a text field */
  function shouldFocusSearch(t) {
    if (!t) return true;
    var tag = String(t.tagName || "").toUpperCase();
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return false;
    if (t.isContentEditable) return false;
    if (typeof t.closest === "function" && t.closest("[contenteditable]")) return false;
    return true;
  }
  /* open rows (a goal's scopes follow it when known), then done rows; one flat list for search and the sheet */
  function flatRows(sq, kids) {
    var out = [];
    ((sq && sq.open) || []).forEach(function (r) {
      out.push(r);
      if (r.kind === "goal" && kids && kids[r.name]) kids[r.name].forEach(function (k) { out.push(k); });
    });
    ((sq && sq.done) || []).forEach(function (r) { out.push(r); });
    return out;
  }
  /* "open", "closed", "gone", or "?" (a scope inside a goal is not in the picker lists: ask the server) */
  function statusOf(sq, c) {
    if (!sq || !c) return "?";
    var live = c.kind === "goal" ? sq.goals : sq.scopes;
    if ((live || []).indexOf(c.name) >= 0) return "open";
    if ((sq.done || []).some(function (r) { return r.kind === c.kind && r.name === c.name; })) return "closed";
    return "?";
  }
  /* open rows that need the PO, other than the current choice and the goal that holds it */
  function otherNeeds(sq, choice, goal) {
    var io = BOARD.inboxOthers;   /* the Needs you panel's own numbers (/api/inbox "others"): header and panel must agree */
    if (io && choice && io.key === choice.kind + ":" + choice.name) {
      return io.others.filter(function (x) { return x.n > 0; }).map(function (x) {
        return { kind: ((sq && sq.goals) || []).indexOf(x.scope) >= 0 ? "goal" : "scope", name: x.scope, needs_you: x.n };
      });
    }
    return ((sq && sq.open) || []).filter(function (r) {
      if (!(r.needs_you > 0)) return false;
      if (choice && r.kind === choice.kind && r.name === choice.name) return false;
      if (goal && r.kind === "goal" && r.name === goal) return false;
      return true;
    });
  }
  function squadNeeds(sq) {
    var n = 0, any = false;
    ((sq && sq.open) || []).forEach(function (r) { if (typeof r.needs_you === "number") { n += r.needs_you; any = true; } });
    return any ? n : null;
  }

  BOARD.filterRows = filterRows; BOARD.topRow = topRow; BOARD.pushRecent = pushRecent; BOARD.parseHash = parseHash;
  BOARD.hashFor = hashFor; BOARD.notFoundText = notFoundText; BOARD.openingOrder = openingOrder;
  BOARD.shouldFocusSearch = shouldFocusSearch; BOARD.flatRows = flatRows; BOARD.statusOf = statusOf;
  BOARD.otherNeeds = otherNeeds; BOARD.squadNeeds = squadNeeds;

  /* ---------- the Scopes panel (goal only) ---------- */
  var V = { q: "", sheetQ: "", sheetOpen: false, doneOpen: false, exp: {}, kids: {}, kidsBusy: {}, notFound: null, closed: false,
            scopeRow: null, goalBrief: "", goalCounts: null, sig: "", ctxSig: "", checking: false, picker: null, bootDone: false,
            sort: "needs", cbDone: false, ai: -1, shell: null, bar: null, combo: null, slot: null };
  var ctx = null;   /* BOARD.ctx, set by the first hook call */

  function el(tag, cls, text) {
    var e = root.document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function ago(iso, nowMs) {
    if (!iso) return "no activity";
    var t = Date.parse(iso);
    return isNaN(t) ? "age unknown" : BOARD.ageWords(Math.max(0, Math.floor((nowMs - t) / 1000)));
  }
  function num(v) { return typeof v === "number" ? String(v) : "?"; }
  function tasks(r) { return (typeof r.tasks_done === "number" && typeof r.tasks_total === "number") ? r.tasks_done + " of " + r.tasks_total : "?"; }
  function link(text, fn, title) {
    var b = el("button", "lk", text); b.type = "button"; if (title) b.title = title;
    b.addEventListener("click", function (e) { e.stopPropagation(); fn(); });
    return b;
  }

  var COLS = [{ id: "scope", label: "Scope", identity: true }, { id: "brief", label: "Brief" }, { id: "stage", label: "Stage" },
              { id: "needs_you", label: "Needs you" }, { id: "blocked", label: "Blocked" }, { id: "tasks", label: "Tasks" },
              { id: "last_active", label: "Last active" }];   /* the columns the panel really has (ticket 20) */
  BOARD.registerPanel({
    id: "scopes", byView: true, columns: COLS, title: "Scopes of this goal", route: "/api/scopes", span: 12, spans: [8, 12], maxPx: 300,
    isEmpty: function (d) { return !d || (d.kind === "goal" && !(d.scopes || []).length && !d.empty_text); },
    render: function (body, d, c) {
      if (!d) return;
      if (d.kind === "scope") { V.scopeRow = d.scope || null; paintContext(); return; }
      V.scopeRow = null; V.goalBrief = (d.goal && d.goal.brief) || "";
      var rows = d.scopes || [];
      c.setCount(rows.length, rows.some(function (r) { return r.needs_you > 0; }));
      if (!rows.length) { body.appendChild(el("p", "note", d.empty_text || "No scopes in this goal")); return; }
      V.goalCounts = { n: rows.length, open: rows.filter(function (r) { return r.status !== "done"; }).length };
      body.appendChild(el("p", "muted sm", "Click a row to look at that scope only. The goal stays one click away in the header."));
      var tb = el("table", "sc");
      var hd = el("tr"), cols = c.columns();
      cols.forEach(function (k) { var th = el("th", null, k.label); th.dataset.col = k.id; th.draggable = true; hd.appendChild(th); });
      tb.appendChild(hd);
      rows.forEach(function (r) {
        var tr = el("tr", "go" + (r.needs_you > 0 ? " need" : ""));
        var go = function () { openChoice({ kind: "scope", name: r.name }, true); };
        tr.addEventListener("click", go);
        var cell = {};
        var a = el("td"); a.appendChild(link(r.name, go, "Show scope " + r.name)); cell.scope = a;
        cell.brief = el("td", "br", r.brief || "");
        var st = el("td"); st.appendChild(statusChip(r.status === "done")); cell.stage = st;
        var n = el("td"); if (r.needs_you > 0) n.appendChild(chipEl("need", needsText(r.needs_you))); else n.textContent = r.needs_you == null ? "?" : "nothing";
        cell.needs_you = n;
        cell.blocked = el("td", null, num(r.stuck));
        cell.tasks = el("td", null, tasks(r));
        var la = el("td"); la.appendChild(lastCell(r.last_active, c.now, "span")); cell.last_active = la;
        cols.forEach(function (k) { tr.appendChild(cell[k.id]); });
        tb.appendChild(tr);
      });
      body.appendChild(tb);
    }
  });

  /* ---------- navigation ---------- */
  function sqRow() { return ctx && ctx.state.squad; }

  function openChoice(c, push) {
    var S = ctx.state;
    V.notFound = null; V.closed = false; V.scopeRow = null; V.sheetOpen = false;
    if (push) { try { root.history.pushState(null, "", hashFor(c)); } catch (e) { /* file: pages in a test */ } }
    ctx.setChoice(c.kind + ":" + c.name);
    refresh(true);
  }
  function openPicker(push) {
    var S = ctx.state;
    V.notFound = null; V.closed = false; V.scopeRow = null; V.sheetOpen = false;
    if (push) { try { root.history.pushState(null, "", root.location.pathname + root.location.search); } catch (e) { /* ignore */ } }
    S.choice = null;
    ctx.touch(); ctx.clear(); ctx.paint(); ctx.poller.now();
    refresh(true);
  }
  function onPop() {
    if (!ctx) return;
    var c = parseHash(root.location.hash), S = ctx.state;
    if (!c) { if (S.choice) openPicker(false); return; }
    var st = statusOf(sqRow(), c);
    if (st === "?") {
      checkStatus(c).then(function (s2) { applyPop(c, s2); });
    } else applyPop(c, st);
  }
  function applyPop(c, st) {
    if (st === "gone") { openPicker(false); V.notFound = notFoundText(c, "url"); refresh(true); return; }
    var S = ctx.state;
    if (S.choice && S.choice.kind === c.kind && S.choice.name === c.name) return;
    openChoice(c, false);
    V.closed = st === "closed"; refresh(true);
  }

  function checkStatus(c) {
    if (!c || !NAME_OK.test(c.name)) return Promise.resolve("gone");
    return ctx.getJson("/api/squads?check=" + encodeURIComponent(c.name)).then(function (j) {
      var k = j && j.data && j.data.check;
      if (!k || !k.exists || k.kind !== c.kind) return "gone";
      return k.where === "done" ? "closed" : "open";
    }, function () { return "open"; });   /* the server did not answer: stay on the choice, the poller shows "not updating" */
  }

  /* ---------- hooks called by board.js ---------- */
  function flags() {
    var o = {};
    try {
      var q = new root.URLSearchParams(root.location.search);
      ["squad", "goal", "scope"].forEach(function (k) { if (q.get(k)) o[k] = q.get(k); });
    } catch (e) { /* none */ }
    return o;
  }

  function boot(S, d, ini) {
    ctx = BOARD.ctx || ctx;
    var sq = S.squad;
    var cands = [];
    var flag = ini && ini.goal ? { kind: "goal", name: ini.goal } : (ini && ini.scope ? { kind: "scope", name: ini.scope } : null);
    var hashC = parseHash(root.location.hash);
    var saved = S.choice;
    [flag, hashC, saved].forEach(function (c) { if (c) cands.push(c); });
    var known = {};
    return Promise.all(cands.map(function (c) {
      var st = statusOf(sq, c);
      if (st !== "?") { known[c.kind + ":" + c.name] = st; return null; }
      return checkStatus(c).then(function (s2) { known[c.kind + ":" + c.name] = s2; });
    })).then(function () {
      var r = openingOrder({ flag: flag, hash: hashC, saved: saved,
        exists: function (c) { return known[c.kind + ":" + c.name] || "gone"; } });
      S.choice = r.choice;
      V.notFound = r.notFound; V.closed = r.closed;
      if (r.choice && (r.source === "flag" || r.source === "url")) S.recent = pushRecent(S.recent, r.choice);
      if (r.choice && r.source !== "url") { try { root.history.replaceState(null, "", hashFor(r.choice)); } catch (e) { /* ignore */ } }
      V.bootDone = true;
    });
  }

  function data(resp, S) {
    ctx = BOARD.ctx || ctx;
    if (!ctx || !V.bootDone) return;
    var sq = S.squad;
    if (!sq) return;
    if (!S.choice || S.needs == null) S.needs = squadNeeds(sq);   /* squad-wide; the server's count_squad replaces it when a panel carries one */
    if (S.choice) {
      var st = statusOf(sq, S.choice);
      if (st === "closed") V.closed = true;
      else if (st === "open") V.closed = false;
      else if (!V.checking) {
        V.checking = true;
        checkStatus(S.choice).then(function (s2) { V.checking = false; V.closed = s2 !== "open"; refresh(false); },
                                   function () { V.checking = false; });
      }
    }
    /* a goal that needs the PO opens expanded; expanded goals keep their scope rows fresh */
    if (!S.choice) {
      (sq.open || []).forEach(function (r) {
        if (r.kind !== "goal") return;
        if (r.needs_you > 0 && V.exp[r.name] === undefined) V.exp[r.name] = true;
        if (V.exp[r.name] || V.sheetOpen) loadKids(r.name);
      });
    }
    refresh(false);
  }

  function loadKids(g) {
    if (V.kidsBusy[g]) return;
    V.kidsBusy[g] = true;
    ctx.getJson("/api/scopes?squad=" + encodeURIComponent(ctx.state.squad.key) + "&goal=" + encodeURIComponent(g)).then(function (j) {
      V.kidsBusy[g] = false;
      var d = j && j.data;
      if (d && d.kind === "goal") { V.kids[g] = d.scopes || []; refresh(false); }
    }, function () { V.kidsBusy[g] = false; });
  }

  function paint(S) {
    ctx = BOARD.ctx || ctx;
    if (!ctx) return;
    if (ctx.els.choice && ctx.els.choice.parentNode) ctx.els.choice.parentNode.hidden = true;   /* the switcher below replaces it */
    ctx.els.pick.hidden = true;
    var sp = ctx.panels.scopes;
    if (sp) {
      sp.hidden = !(S.choice && S.choice.kind === "goal");
      sp.hide.hidden = true;
      sp.el.hidden = sp.hidden;
    }
    refresh(true);
  }
  BOARD.hooks.flags = flags; BOARD.hooks.boot = boot; BOARD.hooks.data = data; BOARD.hooks.paint = paint;

  /* ---------- drawing ---------- */
  function css() {
    if (root.document.getElementById("view-css")) return;
    var s = el("style");
    s.id = "view-css";
    s.textContent =
      "#view{padding:0 var(--gutter);position:relative}#view:empty{display:none}" +
      "#view .chip,table.sc .chip{align-items:center;justify-content:center;line-height:1;height:1.65em;box-sizing:border-box}" +
      ".chip.run{background:var(--t-need2);border-color:var(--mango)}.chip.work{background:var(--t-work);border-color:var(--work)}.chip.idle{background:var(--t-idle)}" +
      ".ctxwrap{position:relative}.ctxbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:6px 0}" +
      ".ctxbar .where{flex:1;min-width:14em}.ctxbar .where b{font-weight:700}.lk{border:0;background:none;padding:0;color:var(--ink);text-decoration:underline;text-underline-offset:2px}" +
      ".ctxbar .out{border:1px dashed var(--muted);background:var(--bg);border-radius:6px;padding:2px 8px}" +
      ".ctxbar .ro{border:1px solid var(--mango);background:var(--t-need);border-radius:6px;padding:2px 8px;font-weight:600}" +
      ".selbtn{display:inline-flex;align-items:center;gap:.5em;height:2em;padding:0 .8em;border:2px solid var(--ink);border-radius:.6em;background:var(--bg);font-size:1.08em;max-width:30em}" +
      ".selbtn:hover{border-color:var(--mango)}.selbtn.none{border-color:var(--mango);background:var(--t-need2)}.selbtn b{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}" +
      ".kind{font-size:.83em;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:600}.selbtn .car{color:var(--muted)}" +
      ".combo{position:absolute;left:0;z-index:70;width:min(34em,94vw);background:var(--bg);border:1px solid var(--ink);border-radius:8px;box-shadow:0 8px 24px var(--shadow);padding:6px}" +
      ".combo input,.pkbar input{width:100%;font:inherit;padding:.35em .6em;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--ink)}" +
      ".combo input:focus,.pkbar input:focus{outline:2px solid var(--mango);outline-offset:0}" +
      "#cbl{max-height:22em;overflow:auto;margin-top:5px}" +
      ".cbh{font-size:.83em;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:700;padding:5px 6px 1px}.cbh .lk{text-decoration:none;font:inherit;font-weight:700;color:var(--muted)}" +
      ".cbo{display:flex;gap:6px;align-items:center;padding:3px 8px;border-radius:6px;cursor:pointer}.cbo .cn{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}" +
      ".cbo .kind{text-transform:none;letter-spacing:0;font-weight:400}.cbo.sub{padding-left:22px}.cbo.dn{color:var(--muted)}.cbo:hover,.cbo.act{background:var(--t-need)}.cbo.cur .cn b{text-decoration:underline;text-decoration-color:var(--mango)}" +
      ".cbf{display:flex;justify-content:space-between;align-items:center;gap:8px;border-top:1px solid var(--border);margin-top:5px;padding-top:5px}.cbf .hb{height:1.65em;line-height:1}" +
      ".pk{padding:10px 0 30px}.pk h2{font-size:1.4em;margin:2px 0 4px}.pk p{max-width:62em}" +
      ".pkbar{display:flex;gap:8px;align-items:center;margin:10px 0 6px;flex-wrap:wrap}.pkbar input{flex:1;min-width:16em;max-width:34em;font-size:1.05em}" +
      ".pk h3.sec{margin:10px 0 2px;font-size:1em;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);display:flex;gap:6px;align-items:center}.pk h3.sec .t{text-transform:none;letter-spacing:0;font-weight:400}" +
      ".plist{border:1px solid var(--border);border-radius:var(--r);background:var(--panel);padding:2px 8px 8px}" +
      ".pr{display:grid;grid-template-columns:1.8em minmax(11em,1.3fr) 5em minmax(10em,2.3fr) minmax(11em,1.2fr) 8.6em 9.2em;gap:8px;align-items:center;padding:5px 6px;border-bottom:1px solid var(--border);cursor:pointer;border-radius:6px}" +
      ".pr.phd{cursor:default;font-size:.83em;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:600;padding:5px 6px 3px}.pr.phd:hover{background:none}" +
      ".pr:hover{background:var(--t-need3)}.pr.sub{background:var(--bg);border-left:3px solid var(--border);margin-left:1.6em}.pr.dn{color:var(--muted)}" +
      ".pr .pn{min-width:0}.pr .pn b{display:inline-block;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;vertical-align:bottom}" +
      ".pr .pbr{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.pn .kind{display:block;margin-top:1px}" +
      ".pla small{display:block;color:var(--muted)}.pla b{white-space:nowrap}" +
      ".chev{border:1px solid transparent;background:none;border-radius:5px;width:1.8em;height:1.8em;padding:0;color:var(--muted)}.chev:hover{border-color:var(--border);background:var(--bg);color:var(--ink)}" +
      ".dnd{margin-top:10px}.dnd summary{cursor:pointer;padding:4px 6px;font-size:.92em;text-transform:uppercase;letter-spacing:.05em}.dnd summary b{font-weight:700}.dnd summary .muted{text-transform:none;letter-spacing:0}" +
      ".cp{border:1px solid var(--border);background:var(--bg);border-radius:.825em;padding:0 .6em;height:1.65em;line-height:1}" +
      "table.sc{width:100%;border-collapse:collapse}table.sc th{text-align:left;font-size:.83em;text-transform:uppercase;color:var(--muted);padding:2px 6px}" +
      "table.sc td{padding:4px 6px;border-top:1px solid var(--border)}table.sc tr.need{background:var(--t-need3)}table.sc tr.go{cursor:pointer}table.sc tr.go:hover{background:var(--t-need)}" +
      "table.sc td.br{max-width:28em;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}table.sc small{display:block;color:var(--muted)}";
    root.document.head.appendChild(s);
  }

  function chipEl(cls, text) { return el("span", "chip " + cls, text); }
  function statusChip(done) { return chipEl(done ? "work" : "run", done ? "done" : "open"); }
  function needsText(n) { return n + " need" + (n === 1 ? "s" : "") + " you"; }
  /* the clock under an age: "14:19" today, "Nov 1 14:22" before */
  function stamp(iso, nowMs) {
    var t = Date.parse(iso);
    if (!iso || isNaN(t)) return "";
    var hm = String(ctx.fmtClock(iso)).slice(0, 5);
    if (nowMs - t < 86400000) return hm;
    var d = BOARD.fmtDate(iso, BOARD.readZone()).split("-");
    var mon = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][+d[1] - 1];
    return (mon ? mon + " " + (+d[2]) + " " : "") + hm;
  }
  function lastCell(iso, nowMs, tag) {
    var s = el(tag || "span", "pla");
    if (!iso) { s.appendChild(el("span", "muted", "no activity")); return s; }
    s.appendChild(el("b", null, ago(iso, nowMs)));
    var st = stamp(iso, nowMs);
    if (st) s.appendChild(el("small", null, st));
    return s;
  }
  function sortRows(rows, mode) {
    var a = (rows || []).slice();
    var t = function (r) { var m = Date.parse(r.last_active || ""); return isNaN(m) ? 0 : m; };
    a.sort(function (x, y) {
      if (mode === "name") return String(x.name).localeCompare(String(y.name));
      if (mode === "needs" && (x.needs_you || 0) !== (y.needs_you || 0)) return (y.needs_you || 0) - (x.needs_you || 0);
      return t(y) - t(x);
    });
    return a;
  }
  BOARD.sortRows = sortRows;
  function openTasks(r) { return (typeof r.tasks_total === "number" && typeof r.tasks_done === "number") ? r.tasks_total - r.tasks_done : null; }
  function workText(r) {
    if (r.stub) return "";
    var o = openTasks(r);
    if (r.kind === "goal") {
      var n = r.scopes_count, kids = V.kids[r.name], open = kids ? kids.filter(function (k) { return k.status !== "done"; }).length : null;
      var s = typeof n === "number" ? n + " scope" + (n === 1 ? "" : "s") + (open != null && open !== n ? " (" + open + " open)" : "") : "scopes ?";
      return s + " · " + (o == null ? "?" : o) + " open task" + (o === 1 ? "" : "s");
    }
    return (o == null ? "?" : o) + " open of " + (typeof r.tasks_total === "number" ? r.tasks_total : "?") + " task" + (r.tasks_total === 1 ? "" : "s") +
      (r.stuck > 0 ? ", " + r.stuck + " blocked" : "");
  }

  function rowEl(r, sub, nowMs) {
    var d = el("div", "pr" + (sub ? " sub" : "") + (r.status === "done" ? " dn" : ""));
    d.setAttribute("role", "option"); d.tabIndex = 0; d.dataset.kind = r.kind; d.dataset.name = r.name;
    var go = function () { openChoice({ kind: r.kind, name: r.name }, true); };
    var ch = el("span");
    if (r.kind === "goal" && !sub) {
      var b = el("button", "chev", V.exp[r.name] ? "▾" : "▸"); b.type = "button";
      b.setAttribute("aria-expanded", V.exp[r.name] ? "true" : "false");
      b.setAttribute("aria-label", (V.exp[r.name] ? "Hide" : "Show") + " the scopes of " + r.name);
      b.addEventListener("click", function (e) { e.stopPropagation(); V.exp[r.name] = !V.exp[r.name]; if (V.exp[r.name]) loadKids(r.name); refresh(true); });
      ch.appendChild(b);
    }
    d.appendChild(ch);
    var pn = el("span", "pn"); var nb = el("b", null, r.name); nb.title = r.name; pn.appendChild(nb);
    if (!sub) pn.appendChild(el("span", "kind", r.kind === "goal" ? "goal" : (r.goal ? "scope · goal " + r.goal : "scope · no goal")));
    d.appendChild(pn);
    var ps = el("span"); ps.appendChild(statusChip(r.status === "done")); d.appendChild(ps);
    d.appendChild(el("span", "pbr", r.brief || ""));
    d.appendChild(el("span", null, workText(r)));
    var n = el("span");
    if (r.needs_you > 0) n.appendChild(chipEl("need", needsText(r.needs_you)));
    else if (!r.stub) n.textContent = r.needs_you == null ? "?" : "nothing";
    d.appendChild(n);
    d.appendChild(r.stub ? el("span") : lastCell(r.last_active, nowMs));
    d.addEventListener("click", go);
    d.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); go(); } });
    return d;
  }

  function recentRows(sq) {
    var byKey = {};
    flatRows(sq, V.kids).forEach(function (r) { byKey[r.kind + ":" + r.name] = r; });
    var out = [];
    (ctx.state.recent || []).forEach(function (c) {
      var r = byKey[c.kind + ":" + c.name];
      if (r) out.push(r);
      else if (statusOf(sq, c) !== "?") out.push({ name: c.name, kind: c.kind, brief: "", status: statusOf(sq, c) === "closed" ? "done" : "open", stub: true });
    });
    return out.slice(0, RECENT_MAX);
  }

  function headRow() {
    var h = el("div", "pr phd"); h.setAttribute("aria-hidden", "true");
    ["", "Name", "Status", "Brief", "Work", "You", "Last active"].forEach(function (t) { h.appendChild(el("span", null, t)); });
    return h;
  }
  function section(title, count, hint) {
    var h = el("h3", "sec", title);
    if (count != null) h.appendChild(chipEl("idle", String(count)));
    if (hint) h.appendChild(el("span", "t muted", hint));
    return h;
  }
  function goalNames(sq) { return (sq.open || []).filter(function (r) { return r.kind === "goal"; }).map(function (r) { return r.name; }); }

  function fillList(box, sq, nowMs) {
    box.textContent = "";
    var q = V.q.trim();
    var all = (sq.open || []).length + (sq.done || []).length;
    if (!all) {
      var em = el("p", "note"); em.appendChild(el("b", null, "This squad has no goal and no scope. "));
      em.appendChild(root.document.createTextNode("The Manager creates a scope with squad-spawn; it shows up here at the next refresh."));
      box.appendChild(em); return;
    }
    var frag = root.document.createDocumentFragment();
    var list = el("div", "plist"); list.setAttribute("role", "listbox"); list.setAttribute("aria-label", "Goals and scopes");
    list.appendChild(headRow());
    if (q) {
      var vis = filterRows(flatRows(sq, V.kids), q);
      if (!vis.length) {
        var nm = el("p", "note", "Nothing matches '" + q + "'. This squad has " + introText(sq).goals + " goals and " + introText(sq).scopes + " scopes. ");
        var clr = el("button", "cp", "Clear search"); clr.type = "button";
        clr.addEventListener("click", function () { V.q = ""; V.picker.inp.value = ""; fillList(box, ctx.state.squad, ctx.now()); V.picker.inp.focus(); });
        nm.appendChild(clr); frag.appendChild(nm);
      } else vis.forEach(function (r) { list.appendChild(rowEl(r, false, nowMs)); });
      if (vis.length) frag.appendChild(list);
      box.appendChild(frag);
      return;
    }
    var rec = recentRows(sq);
    if (rec.length) {
      list.appendChild(section("Recent", rec.length, "what you opened last"));
      rec.forEach(function (r) { list.appendChild(rowEl(r, false, nowMs)); });
    }
    var open = sortRows(sq.open || [], V.sort);
    list.appendChild(section("Open", open.length));
    if (!open.length) list.appendChild(el("p", "muted", "Nothing open. Open the Done list below."));
    open.forEach(function (r) {
      list.appendChild(rowEl(r, false, nowMs));
      if (r.kind === "goal" && V.exp[r.name]) sortRows(V.kids[r.name] || [], V.sort).forEach(function (k) { list.appendChild(rowEl(k, true, nowMs)); });
    });
    var dn = el("details", "dnd"); dn.open = V.doneOpen;
    var done = sortRows(sq.done || [], V.sort);
    var sm = el("summary"); sm.setAttribute("aria-label", "Done (" + done.length + ")");
    sm.appendChild(el("b", null, "Done ")); sm.appendChild(chipEl("idle", String(done.length)));
    sm.appendChild(el("span", "muted", " goals and loose scopes that closed. Their scopes show when you open a goal."));
    dn.appendChild(sm);
    dn.addEventListener("toggle", function () { V.doneOpen = dn.open; });
    done.forEach(function (r) { dn.appendChild(rowEl(r, false, nowMs)); });
    list.appendChild(dn);
    frag.appendChild(list);
    box.appendChild(frag);
  }

  function introText(sq) {
    var goals = (sq.open || []).filter(function (r) { return r.kind === "goal"; }).length;
    var dgoals = (sq.done || []).filter(function (r) { return r.kind === "goal"; });
    var scopesOpen = (sq.scopes || []).length;
    var scopesAll = scopesOpen + (sq.done || []).reduce(function (a, r) { return a + (r.kind === "scope" ? 1 : (r.scopes_count || 0)); }, 0);
    return { goals: goals + dgoals.length, goalsOpen: goals, scopes: scopesAll, scopesOpen: scopesOpen };
  }

  function pickerView(sq, nowMs) {
    var slot = V.slot;
    if (!V.picker || !V.picker.isConnected) {
      var pk = el("div", "pk");
      V.picker = pk;
      pk.appendChild(el("h2", null, "What do you want to look at?"));
      pk.info = el("p", "muted"); pk.appendChild(pk.info);
      pk.note = el("p", "note"); pk.note.hidden = true; pk.note.setAttribute("role", "status"); pk.appendChild(pk.note);
      pk.unk = el("p", "note"); pk.unk.hidden = true; pk.appendChild(pk.unk);
      var bar = el("div", "pkbar");
      var inp = el("input"); inp.type = "search"; inp.id = "pkq"; inp.autocomplete = "off";
      inp.placeholder = "Search goals and scopes by name or brief   ( / )"; inp.setAttribute("aria-label", "Search goals and scopes");
      inp.addEventListener("input", function () { V.q = inp.value; fillList(pk.box, ctx.state.squad, ctx.now()); syncBar(); });
      inp.addEventListener("keydown", function (e) {
        if (e.key !== "Enter") return;
        e.preventDefault();
        var r = topRow(filterRows(flatRows(ctx.state.squad, V.kids), inp.value));
        if (r) openChoice({ kind: r.kind, name: r.name }, true);
      });
      bar.appendChild(inp);
      var seg = el("span", "seg"); seg.setAttribute("role", "group"); seg.setAttribute("aria-label", "Sort");
      [["last", "Last active"], ["needs", "Needs you"], ["name", "Name"]].forEach(function (s) {
        var b = el("button", null, s[1]); b.type = "button"; b.dataset.sort = s[0];
        b.addEventListener("click", function () { V.sort = s[0]; fillList(pk.box, ctx.state.squad, ctx.now()); syncBar(); });
        seg.appendChild(b);
      });
      bar.appendChild(seg);
      var ex = el("button", "cp"); ex.type = "button"; ex.dataset.expAll = "1";
      ex.addEventListener("click", function () {
        var sq2 = ctx.state.squad, any = goalNames(sq2).some(function (n) { return V.exp[n]; });
        goalNames(sq2).forEach(function (n) { V.exp[n] = !any; if (!any) loadKids(n); });
        refresh(true);
      });
      bar.appendChild(ex);
      pk.bar = bar; pk.seg = seg; pk.ex = ex; pk.appendChild(bar);
      pk.box = el("div"); pk.appendChild(pk.box);
      pk.inp = inp;
    }
    var pk2 = V.picker;
    var it = introText(sq), n = squadNeeds(sq);
    pk2.info.textContent = "";
    pk2.info.appendChild(root.document.createTextNode("The board shows "));
    pk2.info.appendChild(el("b", null, "one goal")); pk2.info.appendChild(root.document.createTextNode(" (with its scopes) "));
    pk2.info.appendChild(el("b", null, "or one scope")); pk2.info.appendChild(root.document.createTextNode(". Squad "));
    pk2.info.appendChild(el("code", null, sq.name));
    pk2.info.appendChild(root.document.createTextNode(": " + it.goals + " goals (" + it.goalsOpen + " open), " + it.scopes + " scopes (" + it.scopesOpen +
      " open). Needs-you counts cover the whole squad, so you can see where to go first." +
      (n == null ? "" : " " + n + " need" + (n === 1 ? "s" : "") + " you across the squad.")));
    pk2.note.hidden = !V.notFound; pk2.note.textContent = V.notFound || "";
    var unk = (sq.open || []).length > 0 && (sq.open || []).every(function (r) { return r.needs_you == null && r.tasks_total == null; });
    pk2.unk.hidden = !unk;
    if (unk) { pk2.unk.textContent = ""; pk2.unk.appendChild(el("b", null, "unknown: the ledger and the inbox did not answer. ")); pk2.unk.appendChild(root.document.createTextNode("Names and briefs come from files; counts and last active are not guessed. You can still pick.")); }
    if (pk2.parentNode !== slot) { slot.textContent = ""; slot.appendChild(pk2); }
    fillList(pk2.box, sq, nowMs);
    syncBar();
  }
  function syncBar() {
    var pk = V.picker; if (!pk) return;
    Array.prototype.forEach.call(pk.seg.children, function (b) { b.setAttribute("aria-pressed", String(b.dataset.sort === V.sort)); });
    var sq = ctx.state.squad, any = goalNames(sq).some(function (n) { return V.exp[n]; });
    pk.ex.textContent = any ? "Collapse all goals" : "Expand all open goals";
    pk.ex.hidden = !!V.q.trim() || !goalNames(sq).length;
  }

  /* ---------- header: one button + the line next to it; the combobox opens under it ---------- */
  function ensureShell(view) {
    if (V.shell && V.shell.parentNode === view) return;
    view.textContent = "";
    V.picker = null;
    V.shell = el("div", "ctxwrap");
    V.bar = el("div", "ctxbar");
    V.combo = el("div", "combo"); V.combo.hidden = true;
    V.shell.appendChild(V.bar); V.shell.appendChild(V.combo);
    V.slot = el("div");
    view.appendChild(V.shell); view.appendChild(V.slot);
  }

  function selButton(S) {
    var sw = el("button", "selbtn" + (S.choice ? "" : " none")); sw.type = "button"; sw.id = "selbtn";
    sw.setAttribute("role", "combobox"); sw.setAttribute("aria-haspopup", "listbox"); sw.setAttribute("aria-controls", "cbl");
    sw.setAttribute("aria-expanded", V.sheetOpen ? "true" : "false");
    if (!S.choice) { sw.appendChild(chipEl("need", "pick one")); sw.appendChild(root.document.createTextNode(" Choose a goal or a scope ")); }
    else { sw.appendChild(el("span", "kind", S.choice.kind)); sw.appendChild(el("b", null, S.choice.name)); sw.appendChild(root.document.createTextNode(" ")); }
    sw.appendChild(el("span", "car", "▾"));
    sw.addEventListener("click", function (e) { e.stopPropagation(); toggleSheet(); });
    return sw;
  }

  function drawBar(S, sq, nowMs) {
    var bar = V.bar; bar.textContent = "";
    var c = S.choice;
    bar.appendChild(selButton(S));
    var wh = el("span", "where");
    if (!c) {
      wh.appendChild(el("span", "muted", "Nothing is selected, so no panel shows data. The picker below lists goals and scopes."));
      bar.appendChild(wh);
      return;
    }
    var goal = c.kind === "scope" && V.scopeRow ? V.scopeRow.goal : null;
    if (c.kind === "goal") wh.appendChild(el("b", null, "goal " + c.name));
    else if (goal) {
      wh.appendChild(link("goal " + goal, function () { openChoice({ kind: "goal", name: goal }, true); }, "Back up to goal " + goal));
      wh.appendChild(root.document.createTextNode(" > "));
      wh.appendChild(el("b", null, "scope " + c.name));
    } else {
      wh.appendChild(el("b", null, "scope " + c.name));
      if (V.scopeRow) wh.appendChild(el("span", "muted", " (no goal)"));
    }
    wh.appendChild(root.document.createTextNode(" "));
    wh.appendChild(statusChip(V.closed || statusOf(sq, c) === "closed"));
    var brief = c.kind === "goal" ? V.goalBrief : (V.scopeRow ? V.scopeRow.brief : "");
    var extra = "";
    if (c.kind === "goal" && V.goalCounts) extra = " · " + V.goalCounts.n + " scope" + (V.goalCounts.n === 1 ? "" : "s") + " (" + V.goalCounts.open + " open) · panels show them together";
    if (brief || extra) wh.appendChild(el("span", "muted", " " + brief + extra));
    bar.appendChild(wh);
    otherNeeds(sq, c, goal).forEach(function (r) {
      var o = el("span", "out");
      o.appendChild(root.document.createTextNode(r.needs_you + " more need" + (r.needs_you === 1 ? "s" : "") + " you in "));
      o.appendChild(link(r.name, function () { openChoice({ kind: r.kind, name: r.name }, true); }, "Show " + r.kind + " " + r.name));
      bar.appendChild(o);
    });
    if (V.closed) {
      var ro = el("span", "ro", "closed: read-only. ");
      ro.setAttribute("role", "status");
      ro.appendChild(link("Back to the picker", function () { openPicker(true); }));
      bar.appendChild(ro);
    }
  }

  /* groups for the combobox: with text, Goals and Scopes; without, Recent, Open (a goal with its open scopes), Done */
  function comboGroups(sq, q) {
    q = q.trim();
    if (q) {
      var vis = filterRows(flatRows(sq, V.kids), q);
      return [{ t: "Goals", rows: vis.filter(function (r) { return r.kind === "goal"; }).map(function (r) { return { r: r }; }) },
              { t: "Scopes", rows: vis.filter(function (r) { return r.kind === "scope"; }).map(function (r) { return { r: r, ctx: r.goal || "" }; }) }]
        .filter(function (g) { return g.rows.length; });
    }
    var out = [];
    var rec = recentRows(sq);
    if (rec.length) out.push({ t: "Recent", rows: rec.map(function (r) { return { r: r, ctx: r.kind === "scope" ? r.goal || "" : "" }; }) });
    var o = [];
    (sq.open || []).forEach(function (r) {
      o.push({ r: r, ctx: r.kind === "scope" ? "" : null, loose: r.kind === "scope" });
      if (r.kind === "goal") (V.kids[r.name] || []).filter(function (k) { return k.status !== "done"; }).forEach(function (k) { o.push({ r: k, sub: true }); });
    });
    out.push({ t: "Open", rows: o });
    out.push({ t: "Done", done: true, rows: (sq.done || []).map(function (r) { return { r: r }; }) });
    return out;
  }
  function comboRow(x, n, sq, sel) {
    var r = x.r, cur = sel && sel.kind === r.kind && sel.name === r.name;
    var d = el("div", "cbo" + (x.sub ? " sub" : "") + (r.status === "done" ? " dn" : "") + (cur ? " cur" : ""));
    d.setAttribute("role", "option"); d.id = "cbo-" + n; d.dataset.kind = r.kind; d.dataset.name = r.name; d.setAttribute("aria-selected", String(!!cur));
    var cn = el("span", "cn"); cn.appendChild(el("b", null, r.name));
    var k = r.kind === "goal" ? "goal" : (x.ctx ? "in " + x.ctx : (x.loose ? "no goal" : ""));
    if (k) { cn.appendChild(root.document.createTextNode(" ")); cn.appendChild(el("span", "kind", k)); }
    d.appendChild(cn);
    if (r.status === "done") d.appendChild(chipEl("work", "done"));
    if (r.needs_you > 0) d.appendChild(chipEl("need", String(r.needs_you)));
    var a = r.stub || !r.last_active ? "" : ago(r.last_active, ctx.now()).replace(" ago", "");
    d.appendChild(el("span", "muted sm nw", a));
    d.addEventListener("click", function () { openChoice({ kind: r.kind, name: r.name }, true); });
    return d;
  }
  function fillCombo() {
    var sq = ctx.state.squad, sel = ctx.state.choice, inp = V.combo.querySelector("input"), list = V.combo.querySelector("#cbl");
    var q = inp.value, n = 0;
    list.textContent = "";
    var frag = root.document.createDocumentFragment();
    comboGroups(sq, q).forEach(function (g) {
      if (g.done && !q.trim()) {
        var h = el("div", "cbh"); var b = el("button", "lk", (V.cbDone ? "▾" : "▸") + " Done (" + g.rows.length + ")"); b.type = "button"; b.dataset.cbdone = "1";
        b.addEventListener("click", function (e) { e.stopPropagation(); V.cbDone = !V.cbDone; fillCombo(); inp.focus(); });
        h.appendChild(b); frag.appendChild(h);
        if (V.cbDone) g.rows.forEach(function (x) { frag.appendChild(comboRow(x, n++, sq, sel)); });
        return;
      }
      frag.appendChild(el("div", "cbh", g.t));
      g.rows.forEach(function (x) { frag.appendChild(comboRow(x, n++, sq, sel)); });
    });
    if (!n) frag.appendChild(el("p", "muted", "Nothing matches '" + q.trim() + "'"));
    list.appendChild(frag);
    V.ai = q.trim() ? 0 : Math.min(V.ai, n - 1);
    markAct();
  }
  function markAct() {
    var a = V.combo.querySelectorAll("#cbl .cbo"), inp = V.combo.querySelector("input");
    Array.prototype.forEach.call(a, function (x, i) { x.classList.toggle("act", i === V.ai); });
    var c = a[V.ai];
    if (c) { inp.setAttribute("aria-activedescendant", c.id); if (c.scrollIntoView) c.scrollIntoView({ block: "nearest" }); } else inp.removeAttribute("aria-activedescendant");
  }
  function openCombo() {
    var cb = V.combo;
    cb.textContent = ""; cb.hidden = false;
    cb.style.top = (V.bar.offsetHeight + 2) + "px";
    var inp = el("input"); inp.type = "search"; inp.autocomplete = "off"; inp.setAttribute("role", "combobox");
    inp.setAttribute("aria-expanded", "true"); inp.setAttribute("aria-controls", "cbl"); inp.setAttribute("aria-autocomplete", "list");
    inp.placeholder = "Search goals and scopes"; inp.setAttribute("aria-label", "Search goals and scopes"); inp.value = V.sheetQ;
    var list = el("div"); list.id = "cbl"; list.setAttribute("role", "listbox"); list.setAttribute("aria-label", "Goals and scopes");
    var ft = el("div", "cbf");
    var ob = el("button", "hb", "Open the picker (counts, last active)"); ob.type = "button";
    ob.addEventListener("click", function (e) { e.stopPropagation(); openPicker(true); });
    ft.appendChild(ob); ft.appendChild(el("span", "muted sm", "↑ ↓ Enter · Esc"));
    cb.appendChild(inp); cb.appendChild(list); cb.appendChild(ft);
    V.ai = -1;
    inp.addEventListener("input", function () { V.sheetQ = inp.value; fillCombo(); });
    inp.addEventListener("keydown", function (e) {
      var a = V.combo.querySelectorAll("#cbl .cbo");
      if (e.key === "ArrowDown") { e.preventDefault(); V.ai = Math.min(a.length - 1, V.ai + 1); markAct(); }
      else if (e.key === "ArrowUp") { e.preventDefault(); V.ai = Math.max(0, V.ai - 1); markAct(); }
      else if (e.key === "Enter") {
        e.preventDefault();
        var c = a[V.ai >= 0 ? V.ai : 0];
        if (c) openChoice({ kind: c.dataset.kind, name: c.dataset.name }, true);
      }
    });
    fillCombo();
    root.setTimeout(function () { if (V.sheetOpen && inp.isConnected) inp.focus(); }, 0);
  }

  var escFn = null;
  function toggleSheet(force) {
    V.sheetOpen = typeof force === "boolean" ? force : !V.sheetOpen;
    if (V.sheetOpen && !escFn) {
      escFn = function (e) {
        if (e.key !== "Escape") return;
        toggleSheet(false);
        var b = root.document.getElementById("selbtn"); if (b) b.focus();
      };
      root.document.addEventListener("keydown", escFn);
      goalNames(ctx.state.squad).forEach(function (g) { loadKids(g); });
    }
    if (!V.sheetOpen && escFn) { root.document.removeEventListener("keydown", escFn); escFn = null; }
    refresh(true);
  }

  function refresh(force) {
    if (!ctx || !V.bootDone) return;
    var S = ctx.state, sq = S.squad;
    if (!sq) return;
    css();
    var nowMs = ctx.now();
    var sig = JSON.stringify([S.choice, V.closed, V.notFound, V.scopeRow, V.goalBrief, V.goalCounts, sq.open, sq.done, V.kids, V.exp, V.sheetOpen, V.sort, S.recent, Math.floor(nowMs / 60000)]);
    if (!force && sig === V.sig) return;
    V.sig = sig;
    var view = ctx.els.view;
    ensureShell(view);
    drawBar(S, sq, nowMs);
    if (!S.choice) pickerView(sq, nowMs);
    else { V.picker = null; V.slot.textContent = ""; }
    if (V.sheetOpen) {
      if (V.combo.hidden || !V.combo.firstChild) openCombo(); else fillCombo();
    } else if (!V.combo.hidden) { V.combo.hidden = true; V.combo.textContent = ""; }
    ctx.paintTitle();
  }
  function paintContext() { refresh(true); }

  /* "/" focuses the search box; in a goal or scope view it opens the switcher */
  function onKey(e) {
    if (e.key !== "/" || e.ctrlKey || e.metaKey || e.altKey || !ctx || !V.bootDone) return;
    if (!shouldFocusSearch(e.target)) return;
    if (!ctx.state.choice) {
      if (V.picker && V.picker.inp) { e.preventDefault(); V.picker.inp.focus(); }
    } else if (!V.sheetOpen) { e.preventDefault(); toggleSheet(true); }
  }
  root.document.addEventListener("keydown", onKey);
  root.addEventListener("popstate", onPop);
  root.document.addEventListener("click", function (e) {
    if (V.sheetOpen && ctx && !(e.target.closest && (e.target.closest(".combo") || e.target.closest("#selbtn")))) toggleSheet(false);
  });
  BOARD.viewState = V;
})(typeof window !== "undefined" ? window : this);
