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
            scopeRow: null, goalBrief: "", sig: "", ctxSig: "", checking: false, picker: null, bootDone: false };
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

  BOARD.registerPanel({
    id: "scopes", byView: true, title: "Scopes of this goal", route: "/api/scopes", span: 12, spans: [8, 12], maxPx: 300,
    isEmpty: function (d) { return !d || (d.kind === "goal" && !(d.scopes || []).length && !d.empty_text); },
    render: function (body, d, c) {
      if (!d) return;
      if (d.kind === "scope") { V.scopeRow = d.scope || null; paintContext(); return; }
      V.scopeRow = null; V.goalBrief = (d.goal && d.goal.brief) || "";
      var rows = d.scopes || [];
      c.setCount(rows.length, rows.some(function (r) { return r.needs_you > 0; }));
      if (!rows.length) { body.appendChild(el("p", "note", d.empty_text || "No scopes in this goal")); return; }
      var tb = el("table", "sc");
      var hd = el("tr");
      ["Scope", "Brief", "Stage", "Needs you", "Blocked", "Tasks", "Last active"].forEach(function (h) { hd.appendChild(el("th", null, h)); });
      tb.appendChild(hd);
      rows.forEach(function (r) {
        var tr = el("tr", r.needs_you > 0 ? "need" : "");
        var a = el("td"); a.appendChild(link(r.name, function () { openChoice({ kind: "scope", name: r.name }, true); }, "Show scope " + r.name)); tr.appendChild(a);
        tr.appendChild(el("td", "br", r.brief || ""));
        tr.appendChild(el("td", null, r.status === "done" ? "done" : "open"));
        var n = el("td"); if (r.needs_you > 0) n.appendChild(el("span", "chip need", r.needs_you + " need" + (r.needs_you === 1 ? "s" : "") + " you")); else n.textContent = r.needs_you == null ? "?" : "nothing";
        tr.appendChild(n);
        tr.appendChild(el("td", null, num(r.stuck)));
        tr.appendChild(el("td", null, tasks(r)));
        tr.appendChild(el("td", null, ago(r.last_active, c.now)));
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
      ".ctxbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:6px 0;position:relative}" +
      ".ctxbar .where b{font-weight:700}.lk{border:0;background:none;padding:0;color:var(--ink);text-decoration:underline;text-underline-offset:2px}" +
      ".ctxbar .out{border:1px dashed var(--muted);background:var(--bg);border-radius:6px;padding:2px 8px}" +
      ".ctxbar .ro{border:1px solid var(--mango);background:var(--t-need);border-radius:6px;padding:2px 8px;font-weight:600}" +
      ".sheet{position:absolute;left:0;top:100%;z-index:60;background:var(--bg);border:1px solid var(--border);border-radius:8px;box-shadow:0 8px 24px var(--shadow);padding:6px;min-width:22em;max-height:26em;overflow:auto}" +
      ".sheet input,.pkbar input{width:100%;font:inherit;padding:.35em .6em;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--ink)}" +
      ".pk{padding:10px 0 30px}.pk h2{font-size:1.4em;margin:2px 0 4px}.pk p{max-width:62em}" +
      ".pk h3 .chip{margin-left:6px}.pkbar{margin:10px 0 6px;max-width:34em}.pk h3{margin:12px 0 2px;font-size:1em;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}" +
      ".plist{border:1px solid var(--border);border-radius:var(--r);background:var(--panel);padding:2px 8px 8px}" +
      ".pr{display:grid;grid-template-columns:1.8em minmax(11em,1.3fr) 5em minmax(10em,2.3fr) minmax(8em,1fr) minmax(8em,1fr) 9em;gap:8px;align-items:center;padding:5px 6px;border-bottom:1px solid var(--border);cursor:pointer;border-radius:6px}" +
      ".pr.phd{cursor:default;font-size:.83em;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:600;border-bottom:1px solid var(--border)}.pr.phd:hover{background:none}" +
      ".pr:hover{background:var(--t-need3)}.pr.sub{background:var(--bg);border-left:3px solid var(--border);margin-left:1.6em}.pr.dn{color:var(--muted)}" +
      ".pr .pn,.pr .pbr{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.pr .kind{color:var(--muted);margin-left:4px}" +
      ".chev{border:1px solid transparent;background:none;border-radius:5px;width:1.8em;height:1.8em;padding:0;color:var(--muted)}" +
      ".dnd{margin-top:10px}.dnd summary{cursor:pointer;padding:4px 6px;text-transform:uppercase;letter-spacing:.05em;font-weight:700}" +
      "table.sc{width:100%;border-collapse:collapse}table.sc th{text-align:left;font-size:.83em;text-transform:uppercase;color:var(--muted);padding:2px 6px}" +
      "table.sc td{padding:4px 6px;border-top:1px solid var(--border)}table.sc tr.need{background:var(--t-need3)}table.sc td.br{max-width:28em;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}";
    root.document.head.appendChild(s);
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
    var pn = el("span", "pn"); pn.appendChild(el("b", null, r.name));
    pn.appendChild(el("span", "kind", r.kind === "goal" ? "goal" : (r.goal ? "scope · goal " + r.goal : "scope")));
    d.appendChild(pn);
    d.appendChild(el("span", null, r.status === "done" ? "done" : "open"));
    d.appendChild(el("span", "pbr", r.brief || ""));
    var w = el("span"); w.textContent = r.stub ? "" : tasks(r) + " tasks" + (r.stuck > 0 ? ", " + r.stuck + " blocked" : "");
    d.appendChild(w);
    var n = el("span");
    if (r.needs_you > 0) n.appendChild(el("span", "chip need", r.needs_you + " need" + (r.needs_you === 1 ? "s" : "") + " you"));
    else if (!r.stub) n.textContent = r.needs_you == null ? "?" : "nothing";
    d.appendChild(n);
    d.appendChild(el("span", null, r.stub ? "" : ago(r.last_active, nowMs)));
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

  function listEl() {
    var l = el("div", "plist"); l.setAttribute("role", "listbox");
    var h = el("div", "pr phd"); h.setAttribute("aria-hidden", "true");
    ["", "Name", "Status", "Brief", "Work", "You", "Last active"].forEach(function (t) { h.appendChild(el("span", null, t)); });
    l.appendChild(h);
    return l;
  }

  function section(title, count) {
    var h = el("h3", null, title);
    if (count != null) h.appendChild(el("span", "chip", String(count)));
    return h;
  }

  function fillList(box, sq, nowMs) {
    box.textContent = "";
    var frag = root.document.createDocumentFragment();
    var q = V.q.trim();
    if (q) {
      var vis = filterRows(flatRows(sq, V.kids), q);
      if (!vis.length) { frag.appendChild(el("p", "note", "Nothing matches '" + q + "'")); }
      else {
        var l = listEl();
        vis.forEach(function (r) { l.appendChild(rowEl(r, false, nowMs)); });
        frag.appendChild(l);
      }
      box.appendChild(frag);
      return;
    }
    var rec = recentRows(sq);
    if (rec.length) {
      frag.appendChild(section("Recent"));
      var lr = listEl();
      rec.forEach(function (r) { lr.appendChild(rowEl(r, false, nowMs)); });
      frag.appendChild(lr);
    }
    frag.appendChild(section("Open", (sq.open || []).length));
    var lo = listEl();
    if (!(sq.open || []).length) lo.appendChild(el("p", "muted", "Nothing open."));
    (sq.open || []).forEach(function (r) {
      lo.appendChild(rowEl(r, false, nowMs));
      if (r.kind === "goal" && V.exp[r.name]) (V.kids[r.name] || []).forEach(function (k) { lo.appendChild(rowEl(k, true, nowMs)); });
    });
    frag.appendChild(lo);
    var dn = el("details", "dnd"); dn.open = V.doneOpen;
    var sm = el("summary", null, "Done (" + (sq.done || []).length + ")");
    dn.appendChild(sm);
    dn.addEventListener("toggle", function () { V.doneOpen = dn.open; });
    (sq.done || []).forEach(function (r) { dn.appendChild(rowEl(r, false, nowMs)); });
    frag.appendChild(dn);
    box.appendChild(frag);
  }

  function pickerView(sq, nowMs) {
    var view = ctx.els.view;
    if (!V.picker || !V.picker.isConnected) {
      var pk = el("div", "pk");
      pk.appendChild(el("h2", null, "What do you want to look at?"));
      V.picker = pk;
      pk.info = el("p", "muted"); pk.appendChild(pk.info);
      pk.note = el("p", "note"); pk.note.hidden = true; pk.note.setAttribute("role", "status"); pk.appendChild(pk.note);
      var bar = el("div", "pkbar");
      var inp = el("input"); inp.type = "search"; inp.id = "pkq"; inp.autocomplete = "off";
      inp.placeholder = "Search by name or brief   ( / )"; inp.setAttribute("aria-label", "Search goals and scopes");
      inp.addEventListener("input", function () { V.q = inp.value; fillList(pk.box, ctx.state.squad, ctx.now()); });
      inp.addEventListener("keydown", function (e) {
        if (e.key !== "Enter") return;
        e.preventDefault();
        var r = topRow(filterRows(flatRows(ctx.state.squad, V.kids), inp.value));
        if (r) openChoice({ kind: r.kind, name: r.name }, true);
      });
      bar.appendChild(inp); pk.appendChild(bar);
      pk.box = el("div"); pk.appendChild(pk.box);
      pk.inp = inp;
    }
    var pk2 = V.picker;
    var n = squadNeeds(sq);
    pk2.info.textContent = "Squad " + sq.name + (n == null ? "" : ": " + n + " need" + (n === 1 ? "s" : "") + " you across the squad") + ".";
    pk2.note.hidden = !V.notFound; pk2.note.textContent = V.notFound || "";
    if (pk2.parentNode !== view) { view.textContent = ""; view.appendChild(pk2); }
    fillList(pk2.box, sq, nowMs);
  }

  function whereText(S) {
    var c = S.choice;
    if (c.kind === "goal") return ["goal ", c.name];
    return null;
  }

  function contextView(S, sq, nowMs) {
    var view = ctx.els.view;
    view.textContent = "";
    V.picker = null;
    var bar = el("div", "ctxbar");
    var c = S.choice;
    var wh = el("span", "where");
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
    var brief = c.kind === "goal" ? V.goalBrief : (V.scopeRow ? V.scopeRow.brief : "");
    if (brief) wh.appendChild(el("span", "muted", "  " + brief));
    var sw = el("button", "hb", "Switch ▾"); sw.type = "button"; sw.setAttribute("aria-haspopup", "listbox");
    sw.setAttribute("aria-expanded", V.sheetOpen ? "true" : "false");
    sw.addEventListener("click", function (e) { e.stopPropagation(); toggleSheet(); });
    bar.appendChild(sw); bar.appendChild(wh);
    bar.appendChild(link("Open the picker", function () { openPicker(true); }));
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
    view.appendChild(bar);
    if (V.sheetOpen) view.appendChild(sheetEl(sq, nowMs));
  }

  function sheetEl(sq, nowMs) {
    var sh = el("div", "sheet"); sh.setAttribute("role", "dialog"); sh.setAttribute("aria-label", "Switch goal or scope");
    var inp = el("input"); inp.type = "search"; inp.autocomplete = "off"; inp.placeholder = "Search by name or brief";
    inp.setAttribute("aria-label", "Search goals and scopes"); inp.value = V.sheetQ;
    var list = el("div"); list.setAttribute("role", "listbox");
    var paintList = function () {
      list.textContent = "";
      var vis = filterRows(flatRows(sq, V.kids), inp.value);
      if (!vis.length) list.appendChild(el("p", "muted", "Nothing matches '" + inp.value.trim() + "'"));
      var frag = root.document.createDocumentFragment();
      vis.forEach(function (r) {
        var b = el("button", "hb", r.name + (r.kind === "goal" ? " (goal)" : "") + (r.status === "done" ? " (done)" : ""));
        b.type = "button"; b.style.display = "block"; b.style.width = "100%"; b.style.textAlign = "left";
        b.addEventListener("click", function () { openChoice({ kind: r.kind, name: r.name }, true); });
        frag.appendChild(b);
      });
      list.appendChild(frag);
    };
    inp.addEventListener("input", function () { V.sheetQ = inp.value; paintList(); });
    inp.addEventListener("keydown", function (e) {
      if (e.key !== "Enter") return;
      e.preventDefault();
      var r = topRow(filterRows(flatRows(sq, V.kids), inp.value));
      if (r) openChoice({ kind: r.kind, name: r.name }, true);
    });
    sh.appendChild(inp); sh.appendChild(list); paintList();
    root.setTimeout(function () { if (V.sheetOpen && inp.isConnected) inp.focus(); }, 0);
    return sh;
  }

  var escFn = null;
  function toggleSheet(force) {
    V.sheetOpen = typeof force === "boolean" ? force : !V.sheetOpen;
    if (V.sheetOpen && !escFn) {
      escFn = function (e) { if (e.key === "Escape") toggleSheet(false); };
      root.document.addEventListener("keydown", escFn);
      (ctx.state.squad.open || []).forEach(function (r) { if (r.kind === "goal") loadKids(r.name); });
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
    var sig = JSON.stringify([S.choice, V.closed, V.notFound, V.scopeRow, V.goalBrief, sq.open, sq.done, V.kids, V.exp, V.sheetOpen, S.recent, Math.floor(nowMs / 60000)]);
    if (!force && sig === V.sig) return;
    V.sig = sig;
    if (!S.choice) pickerView(sq, nowMs); else contextView(S, sq, nowMs);
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
    if (V.sheetOpen && ctx && !(e.target.closest && e.target.closest(".sheet"))) toggleSheet(false);
  });
  BOARD.viewState = V;
})(typeof window !== "undefined" ? window : this);
