/* squad-board page shell (ticket 10). No panel code here: a panel file calls BOARD.registerPanel({...}).
   Pure rules (fmtTime, ageWords, titleFor, pickNewer, makePoller, ...) live on BOARD so a test page can call them.
   Untrusted text reaches the DOM only through textContent / createTextNode. */
(function (root) {
  "use strict";
  var BOARD = root.BOARD = root.BOARD || {};
  var SCHEMA = 1;
  var REFRESH_MS = 5000;       /* one constant: the refresh interval */
  var FAILS_STALE = 3;         /* "not updating" after this many failed refreshes in a row */
  var FETCH_TIMEOUT_MS = 4000;
  var SAVE_DELAY_MS = 300;
  var FONTS = [["small", "Small", 0.9], ["normal", "Normal", 1], ["xl", "Extra large", 1.3]];
  var RECENT_MAX = 5;
  BOARD.hooks = BOARD.hooks || {};   /* view hooks (ticket 11): flags(), boot(S, d, ini), data(squadsResp, S), paint(S) */

  /* ---------- pure rules ---------- */
  function readZone() {
    try {
      var z = Intl.DateTimeFormat().resolvedOptions().timeZone;
      return (typeof z === "string" && z) ? z : "UTC";
    } catch (e) { return "UTC"; }
  }

  function parts(iso, tz) {
    var ms = Date.parse(iso);
    if (isNaN(ms)) return null;
    var f;
    try {
      f = new Intl.DateTimeFormat("en-GB", { timeZone: tz || "UTC", hourCycle: "h23", year: "numeric", month: "2-digit",
        day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch (e) {
      tz = "UTC";
      f = new Intl.DateTimeFormat("en-GB", { timeZone: "UTC", hourCycle: "h23", year: "numeric", month: "2-digit",
        day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit" });
    }
    var o = {};
    f.formatToParts(new Date(ms)).forEach(function (p) { o[p.type] = p.value; });
    var h = o.hour === "24" ? "00" : o.hour;
    var local = Date.UTC(+o.year, +o.month - 1, +o.day, +h, +o.minute, +o.second);
    return { date: o.year + "-" + o.month + "-" + o.day, hm: h + ":" + o.minute, hms: h + ":" + o.minute + ":" + o.second,
             offMin: Math.round((local - Math.floor(ms / 1000) * 1000) / 60000), tz: tz || "UTC" };
  }

  /* fmtTime(iso, tz): "09:00" in the zone passed in (never the machine's). Unknown zone reads as UTC. */
  function fmtTime(iso, tz) { var p = parts(iso, tz); return p ? p.hm : "unknown"; }
  function fmtClock(iso, tz) { var p = parts(iso, tz); return p ? p.hms : "unknown"; }
  /* the local calendar day of the instant: 2026-11-03T23:30Z at +07 is 2026-11-04 */
  function fmtDate(iso, tz) { var p = parts(iso, tz); return p ? p.date : "unknown"; }

  /* zoneOffset(iso, tz): "+07", "+05:30", "-05"; "UTC" when the zone is UTC or cannot be read. The date matters (DST). */
  function zoneOffset(iso, tz) {
    var p = parts(iso, tz);
    if (!p || p.tz === "UTC" || p.tz === "Etc/UTC") return "UTC";
    var m = p.offMin, sign = m < 0 ? "-" : "+";
    m = Math.abs(m);
    var h = Math.floor(m / 60), mm = m - h * 60;
    return sign + (h < 10 ? "0" : "") + h + (mm ? ":" + (mm < 10 ? "0" : "") + mm : "");
  }

  /* ageWords(seconds): G8. null or not a number is "age unknown", never "just now". */
  function ageWords(s) {
    if (s == null || typeof s !== "number" || isNaN(s)) return "age unknown";
    if (s < 60) return "under 1 min ago";
    if (s < 3600) return Math.floor(s / 60) + " min ago";
    if (s < 86400) return Math.floor(s / 3600) + " h ago";
    return Math.floor(s / 86400) + " d ago";
  }

  /* titleFor(squad, n): the tab title; n is the squad-wide needs-you count from the server (count_squad) */
  function titleFor(squad, n) { return (typeof n === "number" && n > 0) ? "(" + n + ") " + squad : squad; }

  /* pickNewer(file, copy): the saved state with the later saved_at; a missing or unreadable side loses */
  function pickNewer(file, copy) {
    var ok = function (x) { return x && typeof x === "object" && typeof x.saved_at === "string" && !isNaN(Date.parse(x.saved_at)); };
    if (!ok(file) && !ok(copy)) return null;
    if (!ok(copy)) return file;
    if (!ok(file)) return copy;
    return Date.parse(copy.saved_at) > Date.parse(file.saved_at) ? copy : file;
  }

  /* the squad-wide count: the first numeric count_squad any panel response carries (the server computes it once) */
  function needsFrom(responses) {
    for (var i = 0; i < responses.length; i++) {
      var d = responses[i] && responses[i].data;
      if (d && typeof d.count_squad === "number") return d.count_squad;
    }
    return null;
  }

  function isEmpty(d) {
    if (d == null) return true;
    if (Array.isArray(d)) return d.length === 0;
    if (typeof d === "object") return Object.keys(d).length === 0;
    return false;
  }

  /* what a panel body shows for one response: {kind: "version" | "unknown" | "data", sources} */
  function panelView(resp, panel) {
    if (!resp) return { kind: "unknown", sources: [panel.id] };
    if (resp.schema_version !== SCHEMA) return { kind: "version", sources: ["board version"] };
    var unk = Array.isArray(resp.unknown) ? resp.unknown : [];
    var empty = panel && panel.isEmpty ? panel.isEmpty(resp.data) : isEmpty(resp.data);
    if (unk.length && empty) return { kind: "unknown", sources: unk };
    return { kind: "data", sources: unk };
  }

  /* makePoller: one timer, no pile-up (a load still running is not started again), failures counted.
     o: load() -> Promise (rejects on a failed refresh), onOk(value), onFail(n, stale), setTimeout, clearTimeout. */
  function makePoller(o) {
    var fails = 0, busy = false, timer = null, stopped = false, again = false;
    var st = o.setTimeout || root.setTimeout.bind(root), ct = o.clearTimeout || root.clearTimeout.bind(root);
    var every = o.interval || REFRESH_MS;
    function next() { if (!stopped) { ct(timer); timer = st(tick, every); } }
    function tick() {
      if (stopped) return;
      if (busy) { again = true; return; }   /* a load runs: start one more right after it, never two at once */
      busy = true;
      var p;
      try { p = Promise.resolve(o.load()); } catch (e) { p = Promise.reject(e); }
      var rerun = function () { if (again) { again = false; tick(); } };
      p.then(function (v) { fails = 0; busy = false; o.onOk(v); next(); rerun(); },
             function () { fails += 1; busy = false; o.onFail(fails, fails >= FAILS_STALE); next(); rerun(); });
    }
    return { start: tick, now: tick, stop: function () { stopped = true; ct(timer); }, fails: function () { return fails; },
             busy: function () { return busy; } };
  }

  /* ---------- column rules (ticket 20) ----------
     defs: [{id, label, identity?, off?, only?}] in default order. A saved list holds the VISIBLE column ids in order.
     A column with `only: "goal"` is drawn in a goal view only; its place in the list is kept in a scope view. */
  function colDefaults(defs) { return defs.filter(function (d) { return !d.off; }).map(function (d) { return d.id; }); }
  function colFull(saved, defs) {
    var known = {}, out = [];
    defs.forEach(function (d) { known[d.id] = d; });
    if (Array.isArray(saved)) saved.forEach(function (id) { if (typeof id === "string" && known[id] && out.indexOf(id) < 0) out.push(id); });
    if (!out.length) out = colDefaults(defs);
    var idn = defs.filter(function (d) { return d.identity; })[0];
    if (idn && out.indexOf(idn.id) < 0) out.unshift(idn.id);
    return out;
  }
  /* columnsFor(saved, defs, kind): the column defs to draw, in order (kind "goal" | "scope") */
  function columnsFor(saved, defs, kind) {
    var by = {};
    defs.forEach(function (d) { by[d.id] = d; });
    return colFull(saved, defs).map(function (id) { return by[id]; }).filter(function (d) { return !d.only || d.only === kind; });
  }
  /* toggleColumn(list, id, defs): the list with id shown or hidden; the identity column cannot be hidden.
     A column shown again goes after the nearest earlier column of the default order that is shown, else first. */
  function toggleColumn(list, id, defs) {
    var full = colFull(list, defs), at = full.indexOf(id), order = defs.map(function (d) { return d.id; });
    var d = defs.filter(function (x) { return x.id === id; })[0];
    if (!d) return full;
    if (at >= 0) { if (!d.identity) full.splice(at, 1); return full; }
    var pos = 0;
    for (var i = order.indexOf(id) - 1; i >= 0; i--) { var j = full.indexOf(order[i]); if (j >= 0) { pos = j + 1; break; } }
    full.splice(pos, 0, id);
    return full;
  }
  /* moveColumn(list, id, delta) one place up (-1) or down (+1); moveColumnTo(list, id, targetId) puts it where target is */
  function moveColumn(list, id, delta, defs) {
    var full = colFull(list, defs), at = full.indexOf(id), to = at + delta;
    if (at < 0 || to < 0 || to >= full.length) return full;
    full.splice(at, 1); full.splice(to, 0, id);
    return full;
  }
  function moveColumnTo(list, id, targetId, defs) {
    var full = colFull(list, defs), at = full.indexOf(id), to = full.indexOf(targetId);
    if (at < 0 || to < 0 || at === to) return full;
    full.splice(at, 1); full.splice(to, 0, id);
    return full;
  }
  /* resetColumns(map, panelId): the map without that panel (every panel shows its defaults again); no panelId = all */
  function resetColumns(map, panelId) {
    var out = {};
    if (panelId) Object.keys(map || {}).forEach(function (k) { if (k !== panelId) out[k] = map[k]; });
    return out;
  }
  function sameList(a, b) { return JSON.stringify(a) === JSON.stringify(b); }
  /* cleanColumns(raw): a saved `columns` value made safe: only {panel id: [string ids]} survives, never throws */
  function cleanColumns(raw) {
    var out = {};
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) return out;
    Object.keys(raw).forEach(function (k) {
      if (Array.isArray(raw[k]) && raw[k].every(function (x) { return typeof x === "string"; })) out[k] = raw[k].slice(0, 30);
    });
    return out;
  }

  /* ---------- new since last looked (ticket 13) ----------
     rec = {any: epoch ms the page was last visible (any choice) or null, last: {"kind:name": epoch ms}}; kept per squad in browser storage
     only. Counts come from the server (`new_count`, `new`); the page only keeps "since" and what the PO already opened. */
  var SEEN_PREFIX = "squad-board-seen:";
  function seenRead(store, squadKey) {
    var rec = { any: null, last: {} };
    try {
      var j = JSON.parse(store.getItem(SEEN_PREFIX + squadKey) || "null");
      if (j && typeof j === "object") {
        if (typeof j.any === "number" && isFinite(j.any)) rec.any = j.any;
        if (j.last && typeof j.last === "object") Object.keys(j.last).forEach(function (k) { if (typeof j.last[k] === "number" && isFinite(j.last[k])) rec.last[k] = j.last[k]; });
      }
    } catch (e) { /* blocked or bad storage: first visit, nothing new */ }
    return rec;
  }
  function seenWrite(store, squadKey, rec) {
    try { store.setItem(SEEN_PREFIX + squadKey, JSON.stringify({ any: rec.any, last: rec.last })); return true; } catch (e) { return false; }
  }
  /* the time the PO last looked at this choice (choiceKey "scope:x"), or at the squad when there is no choice; null = first visit */
  function sinceFor(rec, choiceKey, now) {
    var t = choiceKey ? rec.last[choiceKey] : rec.any;
    return typeof t === "number" && isFinite(t) ? Math.min(t, now) : null;
  }
  function markVisible(rec, choiceKey, now) { rec.any = now; if (choiceKey) rec.last[choiceKey] = now; return rec; }
  /* opening a task's detail: remember how many of its server count the PO has now seen */
  function clearTask(cleared, scope, task, count, now) { cleared[scope + "/" + task] = { scope: scope, at: now, n: count > 0 ? count : 0 }; return cleared; }
  function clearedN(e, since) { return e && since != null && e.at >= since ? e.n : 0; }
  function shownNew(cleared, scope, task, serverN, since) { return Math.max(0, (serverN > 0 ? serverN : 0) - clearedN(cleared[scope + "/" + task], since)); }
  /* a picker row: the server's count minus what was cleared inside it (scopes: the names it holds; null = every scope) */
  function rowNew(cleared, serverN, since, scopes) {
    if (!(serverN > 0)) return 0;
    var sub = 0;
    Object.keys(cleared).forEach(function (k) { if (!scopes || scopes.indexOf(cleared[k].scope) >= 0) sub += clearedN(cleared[k], since); });
    return Math.max(0, serverN - sub);
  }
  var NEW_ROUTES = { "/api/tasks": "epoch", "/api/squads": "iso", "/api/scopes": "iso" };   /* the list routes read an ISO time, the tasks route epoch seconds */
  function sinceQuery(route, since) {
    var how = NEW_ROUTES[String(route).split("?")[0]];
    if (since == null || !how) return "";
    return "since=" + (how === "epoch" ? String(since / 1000) : encodeURIComponent(new Date(since).toISOString()));
  }
  /* the dot and "N new"; text only */
  function newBadge(n) {
    var d = root.document;
    if (!d.getElementById("new-css")) {
      var st = d.createElement("style"); st.id = "new-css";
      st.textContent = ".chip.newc{background:var(--t-need2);border-color:var(--mango);gap:4px;white-space:nowrap}.newc .nd{display:inline-block;width:.6em;height:.6em;border-radius:999px;background:var(--mango)}";
      d.head.appendChild(st);
    }
    var b = d.createElement("span"); b.className = "chip newc"; b.setAttribute("data-new", String(n));
    var dot = d.createElement("i"); dot.className = "nd"; dot.setAttribute("aria-hidden", "true");
    b.appendChild(dot); b.appendChild(d.createTextNode(n + " new"));
    return b;
  }
  BOARD.seenRead = seenRead; BOARD.seenWrite = seenWrite; BOARD.sinceFor = sinceFor; BOARD.markVisible = markVisible;
  BOARD.clearTask = clearTask; BOARD.shownNew = shownNew; BOARD.rowNew = rowNew; BOARD.sinceQuery = sinceQuery; BOARD.newBadge = newBadge;

  /* ---------- panel registry ---------- */
  var REG = [];
  /* registerPanel({id, title, route, maxPx, render(body, data, ctx), isEmpty(data)})
     route: the API path the panel reads (e.g. "/api/inbox"); maxPx at Normal text. (span, spans: no longer used.) */
  function registerPanel(def) {
    if (!def || !def.id || REG.some(function (d) { return d.id === def.id; })) return;
    REG.push(def);
  }

  BOARD.REFRESH_MS = REFRESH_MS; BOARD.FAILS_STALE = FAILS_STALE; BOARD.FONTS = FONTS;
  BOARD.fmtTime = fmtTime; BOARD.fmtClock = fmtClock; BOARD.fmtDate = fmtDate; BOARD.zoneOffset = zoneOffset;
  BOARD.readZone = readZone; BOARD.ageWords = ageWords; BOARD.titleFor = titleFor; BOARD.pickNewer = pickNewer;
  BOARD.needsFrom = needsFrom; BOARD.panelView = panelView; BOARD.makePoller = makePoller;
  BOARD.registerPanel = registerPanel; BOARD.panels = REG;
  BOARD.columnsFor = columnsFor; BOARD.toggleColumn = toggleColumn; BOARD.moveColumn = moveColumn; BOARD.moveColumnTo = moveColumnTo;
  BOARD.resetColumns = resetColumns; BOARD.colDefaults = colDefaults; BOARD.cleanColumns = cleanColumns;

  /* ---------- the page ---------- */
  function el(tag, cls, text) {
    var e = root.document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function start(env) {
    env = env || {};
    var doc = root.document;
    var fetchFn = env.fetch || root.fetch.bind(root);
    var nowMs = env.now || function () { return Date.now(); };
    var tz = env.tz || readZone();
    var setT = env.setTimeout || root.setTimeout.bind(root), clearT = env.clearTimeout || root.clearTimeout.bind(root);
    var storage = (function () { try { return env.storage || root.localStorage; } catch (e) { return null; } })();
    var iso = function () { return new Date(nowMs()).toISOString(); };

    var S = { squads: [], squad: null, token: "", choice: null, recent: [], font: "normal",
              needs: null, lastOk: null, status: "loading", saveStatus: "ok", notes: {}, saved_at: null, columns: {} };
    var P = {};          /* panel id -> {id, def, idx, col, order, hidden, max_height, el, body, hdr, last} */
    var engine = null, placedOnce = false, saveTimer = null, loadedOnce = false, popOpen = false, booted = false, colPop = null;

    var els = {};
    function build() {
      var app = doc.getElementById("app");
      app.textContent = "";
      els.demo = el("div", "demo", "DEMO · sample data, not your squads"); els.demo.setAttribute("role", "note"); els.demo.hidden = !S.demo;   /* ticket 37b: demo only, no controls */
      var header = el("header", "top");
      var r1 = el("div", "r1");
      r1.appendChild(el("h1", null, "squad board"));
      var lab = el("label", "pick"); lab.appendChild(doc.createTextNode("squad "));
      els.squad = el("select"); els.squad.setAttribute("aria-label", "Squad"); lab.appendChild(els.squad); r1.appendChild(lab);
      var fr = el("span", "fr");
      els.zone = el("span", "zone"); els.zone.title = "Time zone of this browser";
      els.fresh = el("span", "fresh"); els.fresh.setAttribute("role", "status");
      fr.appendChild(els.zone); fr.appendChild(els.fresh); r1.appendChild(fr);
      var r3 = el("div", "r3");
      var cl = el("label", "pick"); cl.appendChild(doc.createTextNode("showing "));
      els.choice = el("select"); els.choice.setAttribute("aria-label", "Goal or scope"); cl.appendChild(els.choice); r3.appendChild(cl);
      var fr3 = el("span", "fr");
      els.font = el("span", "seg"); els.font.setAttribute("role", "group"); els.font.setAttribute("aria-label", "Text size");
      FONTS.forEach(function (f) {
        var b = el("button", null, f[1]); b.type = "button"; b.dataset.font = f[0];
        b.addEventListener("click", function () { setFont(f[0]); });
        els.font.appendChild(b);
      });
      els.hiddenBtn = el("button", "hb", "Panels ▾"); els.hiddenBtn.type = "button";
      els.hiddenBtn.setAttribute("aria-haspopup", "true"); els.hiddenBtn.setAttribute("aria-expanded", "false");
      els.reset = el("button", "hb", "Reset layout"); els.reset.type = "button";
      fr3.appendChild(els.font); els.popWrap = el("span", "popwrap"); els.popWrap.appendChild(els.hiddenBtn); fr3.appendChild(els.popWrap); fr3.appendChild(els.reset); r3.appendChild(fr3);
      header.appendChild(r1); header.appendChild(r3);
      els.notes = el("div", "notes"); els.notes.setAttribute("role", "status");
      els.banner = el("div", "bannerslot");   /* the permission banner: not a panel, no hide, no drag */
      els.pick = el("p", "note"); els.pick.hidden = true;
      var main = el("main"); els.canvas = el("div"); els.canvas.id = "canvas"; main.appendChild(els.canvas);
      els.pop = el("div", "pop"); els.pop.hidden = true; els.pop.setAttribute("role", "menu");
      els.popWrap.appendChild(els.pop);
      els.view = el("div"); els.view.id = "view";   /* the picker and the context line (panel_scopes.js) */
      [els.demo, header, els.notes, els.banner, els.pick, els.view, main].forEach(function (n) { app.appendChild(n); });
      els.squad.addEventListener("change", function () { switchSquad(els.squad.value); });
      els.choice.addEventListener("change", function () { setChoice(els.choice.value); });
      els.reset.addEventListener("click", resetLayout);
      els.hiddenBtn.addEventListener("click", function (e) { e.stopPropagation(); togglePop(); });
      doc.addEventListener("click", function () { if (popOpen) togglePop(false); });
      doc.addEventListener("keydown", function (e) { if (e.key === "Escape" && popOpen) { togglePop(false); els.hiddenBtn.focus(); } });
    }

    /* ---- panels ---- */
    function defaults(def, i) { return { order: i, tracks: null, hidden: false, max_height: null }; }

    function makePanel(def, i) {
      var d = defaults(def, i);
      var p = { id: def.id, def: def, idx: i, tracks: d.tracks, order: d.order, hidden: d.hidden, max_height: d.max_height,
                maxPx: def.maxPx || 400 };
      var sec = el("section", "panel"); sec.dataset.panel = def.id; sec.setAttribute("aria-label", def.title);
      var ph = el("div", "ph"); ph.tabIndex = 0; ph.setAttribute("aria-label", def.title + ": Up and Left move earlier, Down and Right move later, Shift with Up or Down resizes");
      ph.appendChild(el("span", "grip", "⋮⋮"));
      ph.appendChild(el("h2", null, def.title));
      p.count = el("span", "count"); p.count.hidden = true; ph.appendChild(p.count);
      p.unk = el("span", "chip unk"); p.unk.hidden = true; ph.appendChild(p.unk);
      ph.appendChild(el("span", "sp"));
      p.fit = el("button", "pbtn", "Fit"); p.fit.type = "button"; p.fit.hidden = true; p.fit.title = "Back to the height of the content";
      if (def.columns) {
        p.cols = el("button", "pbtn", "Columns"); p.cols.type = "button"; p.cols.setAttribute("aria-haspopup", "true");
        p.cols.setAttribute("aria-expanded", "false"); p.colTag = el("span", "chip colhid"); p.colTag.hidden = true; p.cols.appendChild(p.colTag);
        p.colWrap = el("span", "popwrap"); p.colWrap.appendChild(p.cols); ph.appendChild(p.colWrap);
        p.cols.addEventListener("click", function (e) { e.stopPropagation(); openColumns(p); });
      }
      p.hide = el("button", "pbtn", "Hide"); p.hide.type = "button"; p.hide.title = "Hide this panel";
      ph.appendChild(p.fit); ph.appendChild(p.hide);
      var pb = el("div", "pb"); p.body = el("div", "pbi"); pb.appendChild(p.body);
      sec.appendChild(ph); sec.appendChild(pb);
      ["s"].forEach(function (d2) {
        var h = el("div", "rz " + d2); h.addEventListener("pointerdown", function (e) { e.preventDefault(); e.stopPropagation(); engine.resize(p, d2, e); });
        sec.appendChild(h);
      });
      var he = el("div", "rz e"); he.setAttribute("role", "separator"); he.setAttribute("aria-orientation", "vertical"); he.tabIndex = 0;
      he.setAttribute("aria-label", "Resize width of " + def.title);
      he.addEventListener("pointerdown", function (e) { e.preventDefault(); e.stopPropagation(); engine.resizeEast(p, e); });
      he.addEventListener("keydown", function (e) { engine.edgeKey(p, e); });
      he.addEventListener("dblclick", function (e) { e.preventDefault(); engine.edgeReset(p); });
      sec.appendChild(he);
      p.el = sec; p.hdr = ph;
      ph.addEventListener("pointerdown", function (e) { engine.drag(p, e); });
      ph.addEventListener("keydown", function (e) { if (e.target === ph) engine.key(p, e); });
      p.fit.addEventListener("click", function () { p.max_height = null; touch(); engine.relayout(); });
      p.hide.addEventListener("click", function () { p.hidden = true; touch(); replan(); renderPop(); });
      els.canvas.appendChild(sec);
      if (def.columns) wireColumnDrag(p);
      engine.observe(p.body);
      renderPanel(p, undefined);   /* the "Loading" note of a panel that has one */
      return p;
    }

    function panelList() { return Object.keys(P).map(function (k) { return P[k]; }); }

    function setFlags() {
      panelList().forEach(function (p) {
        p.el.hidden = !!p.hidden;
        p.fit.hidden = p.max_height == null;
      });
    }

    /* a placement moment (design-v8 s3): hide, show, Reset, text size, first load. Never a data refresh. */
    function replan() {
      setFlags();
      engine.relayout();
      setFlags();
    }
    function replace() { placedOnce = true; replan(); }

    /* ---- saved state ---- */
    function snapshot() {
      var panels = {};
      panelList().forEach(function (p) {
        var r = { order: p.order, hidden: !!p.hidden && !p.def.byView };
        if (p.tracks != null) r.tracks = p.tracks;
        if (p.max_height != null) r.max_height = p.max_height;
        panels[p.id] = r;
      });
      var snap = { version: 1, saved_at: S.saved_at, font: S.font, choice: S.choice, recent: S.recent, panels: panels, columns: S.columns };
      if (BOARD.hooks.snapshot) BOARD.hooks.snapshot(snap);   /* a view adds its own saved keys (timeline.js) */
      return snap;
    }

    function applySaved(ui) {
      if (!ui || typeof ui !== "object") return;
      if (FONTS.some(function (f) { return f[0] === ui.font; })) S.font = ui.font;
      if (ui.choice && (ui.choice.kind === "goal" || ui.choice.kind === "scope")) S.choice = ui.choice;
      if (Array.isArray(ui.recent)) S.recent = ui.recent.slice(0, RECENT_MAX);
      S.saved_at = ui.saved_at || null;
      S.columns = cleanColumns(ui.columns);
      if (BOARD.hooks.applySaved) BOARD.hooks.applySaved(ui);
      /* design-v8 s9: the saved rows are read in memory and put in one order (old col / span are only used to sort, then dropped);
         the file is not rewritten on load. A panel with no row goes last by its default rank. A bad tracks value = the default. */
      var pan = ui.panels && typeof ui.panels === "object" ? ui.panels : {};
      var rows = panelList().map(function (p) {
        var r = pan[p.id], row = { id: p.id };
        if (r && typeof r === "object") {
          if (Number.isInteger(r.order)) row.order = r.order;
          if (Number.isInteger(r.col)) row.col = r.col;
        }
        return row;
      });
      BOARD.layout.migrate(rows).forEach(function (row) {
        var p = P[row.id], r = pan[row.id];
        p.order = row.order;
        if (!r || typeof r !== "object") return;
        p.hidden = !!r.hidden;
        p.max_height = Number.isInteger(r.max_height) ? r.max_height : null;
        /* an integer above 12 is the full width (T36.AC9); anything else bad = the default */
        p.tracks = Number.isInteger(r.tracks) && r.tracks >= 1 ? Math.min(r.tracks, 12) : null;
      });
    }

    function storeKey() { return "squad-board-ui:" + (S.squad ? S.squad.key : ""); }

    function touch(extra) {
            S.saved_at = iso();
      var snap = snapshot();
      try { if (storage) storage.setItem(storeKey(), JSON.stringify(snap)); S.notes.storage = ""; }
      catch (e) { S.notes.storage = "This browser blocks storage: settings are kept in the squad folder only."; }
      clearT(saveTimer);
      saveTimer = setT(function () { put(snap); }, SAVE_DELAY_MS);
      showNotes();
    }

    /* One save. A 403 "token required" (the server restarted and forgot the page token) gets a new token from
       /api/session and ONE re-send of the same snapshot; nothing shows meanwhile. Any other answer is final. */
    function put(snap) {
      if (!S.token || !S.squad) return;
      var url = "/api/ui?squad=" + encodeURIComponent(S.squad.key), body = JSON.stringify(snap);
      function send() {
        return fetchFn(url, { method: "PUT", headers: { "Content-Type": "application/json", "X-Board-Token": S.token }, body: body });
      }
      function done(r) { S.saveStatus = r.ok ? "ok" : (r.status === 507 ? "unwritable" : "failed"); showNotes(); }
      function fail() { S.saveStatus = "failed"; showNotes(); }
      send().then(function (r) {
        if (r.status !== 403) return done(r);
        return r.json().then(function (j) { return j && j.error === "token required"; }, function () { return false; }).then(function (stale) {
          if (!stale) return done(r);
          return getJson("/api/session").then(function (j) {
            S.token = (j.data && j.data.token) || "";
            if (!S.token) return fail();
            return send().then(done, fail);
          }, fail);
        });
      }, fail);
    }

    function showNotes() {
      var msgs = [];
      if (S.saveStatus === "unwritable") msgs.push("Settings not shared. The settings file in the squad folder cannot be written. Settings are kept in this browser only.");
      else if (S.saveStatus === "unreadable") msgs.push("The saved settings file could not be read. Default settings are shown.");
      else if (S.saveStatus === "failed") msgs.push("Settings could not be saved just now. They are kept in this browser.");
      if (S.notes.storage) msgs.push(S.notes.storage);
      els.notes.textContent = "";
      els.notes.hidden = msgs.length === 0;
      msgs.forEach(function (m) { els.notes.appendChild(el("p", "note", m)); });
    }

    /* ---- header ---- */
    function applyFont() {
      var f = FONTS.filter(function (x) { return x[0] === S.font; })[0] || FONTS[1];
      doc.documentElement.style.setProperty("--u", String(f[2]));
      doc.documentElement.dataset.font = f[0];
      if (popOpen) placePop();
      if (colPop) placeColumns();
      /* the panels move to their new place after a text-size change (they animate 0.12 s): measure again */
      if (popOpen || colPop) root.setTimeout(function () { if (popOpen) placePop(); if (colPop) placeColumns(); }, 250);
      Array.prototype.forEach.call(els.font.children, function (b) {
        b.setAttribute("aria-pressed", b.dataset.font === S.font ? "true" : "false");
      });
      return f[2];
    }

    function setFont(name) {
      if (S.font === name) return;
      S.font = name; applyFont(); touch(); replace();
    }

    function scale() { return (FONTS.filter(function (x) { return x[0] === S.font; })[0] || FONTS[1])[2]; }

    function paintFresh() {
      var f = els.fresh;
      f.className = "fresh";
      f.textContent = "";
      var dot = el("span", "dot");
      f.appendChild(dot);
      if (S.status === "stale") {
        f.classList.add("bad");
        f.appendChild(doc.createTextNode("not updating" + (S.lastOk ? " (last update " + fmtClock(S.lastOk, tz) + ")" : "")));
      } else if (S.status === "loading") {
        f.classList.add("load");
        f.appendChild(doc.createTextNode("loading"));
      } else {
        f.appendChild(doc.createTextNode("updated " + fmtClock(S.lastOk, tz)));
      }
      els.zone.textContent = "";
      els.zone.appendChild(doc.createTextNode("zone "));
      els.zone.appendChild(el("b", null, zoneOffset(iso(), tz)));
    }

    function paintTitle() { doc.title = (S.demo ? "[demo] " : "") + titleFor(S.squad ? S.squad.name : "squad board", S.needs); }

    function paintPickers() {
      els.squad.textContent = "";
      S.squads.forEach(function (s) {
        var o = el("option", null, s.name + (s.flat ? " (flat squad: not supported)" : "")); o.value = s.key; o.disabled = !!s.flat;
        els.squad.appendChild(o);
      });
      if (S.squad) els.squad.value = S.squad.key;
      els.choice.textContent = "";
      var sq = S.squad || {};
      [["scope", "Scopes", sq.scopes], ["goal", "Goals", sq.goals]].forEach(function (g) {
        if (!g[2] || !g[2].length) return;
        var og = el("optgroup"); og.label = g[1];
        g[2].forEach(function (n) { var o = el("option", null, n); o.value = g[0] + ":" + n; og.appendChild(o); });
        els.choice.appendChild(og);
      });
      if (!els.choice.children.length) els.choice.appendChild(el("option", null, "nothing to show"));
      if (S.choice) els.choice.value = S.choice.kind + ":" + S.choice.name;
      els.pick.hidden = !!S.choice;
      els.pick.textContent = S.choice ? "" : "Pick a goal or a scope to show.";
      els.canvas.parentNode.hidden = !S.choice;
      if (BOARD.hooks.paint) BOARD.hooks.paint(S);
    }

    function setChoice(v) {
      var i = v.indexOf(":");
      if (i < 0) return;
      S.choice = { kind: v.slice(0, i), name: v.slice(i + 1) };
      S.recent = [S.choice].concat(S.recent.filter(function (c) { return !(c.kind === S.choice.kind && c.name === S.choice.name); })).slice(0, RECENT_MAX);
      touch(); paintPickers(); clearPanels(); loadedOnce = false; poller.now();
    }

    function switchSquad(key) {
      var s = S.squads.filter(function (x) { return x.key === key; })[0];
      if (!s || s.flat) { paintPickers(); return; }
      S.squad = s; S.choice = null; S.needs = null;
      loadSaved().then(function () { paintPickers(); clearPanels(); loadedOnce = false; poller.now(); });
    }

    function clearPanels() {
      panelList().forEach(function (p) { p.last = null; p.body.textContent = ""; p.count.hidden = true; p.unk.hidden = true; });
    }

    /* ---- hidden panels list ---- */
    function renderPop() {
      els.pop.textContent = "";
      var hid = panelList().filter(function (p) { return p.hidden && !p.def.byView; });
      els.hiddenBtn.textContent = "Panels" + (hid.length ? " (" + hid.length + " hidden)" : "") + (popOpen ? " ▴" : " ▾");
      els.pop.appendChild(el("h3", null, "Hidden panels"));
      if (!hid.length) els.pop.appendChild(el("p", "muted", "No hidden panels."));
      hid.forEach(function (p) {
        var b = el("button", "hb", "Show " + p.def.title); b.type = "button"; b.setAttribute("role", "menuitem");
        b.addEventListener("click", function (e) { e.stopPropagation(); p.hidden = false; touch(); replan(); renderPop(); });
        els.pop.appendChild(b);
      });
    }
    /* popPlace(btnRect, popSize, viewport) -> {top, left, maxHeight}: under the button, left edges aligned,
       moved left to stay inside (8 px margin); if too tall for the room below, it gets a max height and scrolls. */
    function popPlace(r, size, vp) {
      var m = 8, left = Math.max(m, Math.min(r.left, vp.w - size.w - m)), top = r.bottom + 4;
      return { top: top, left: left, maxHeight: Math.max(0, vp.h - r.bottom - 12) };
    }
    BOARD.popPlace = popPlace;
    /* fitBox: place a list under its button. The list keeps a usable height (its own height, at most 280 px);
       on open, if the room under the button is smaller, the page scrolls the button up (the button stays in view). */
    function fitBox(box, btn, scrollUp) {
      var H = root.innerHeight || 800, W = root.innerWidth || 1000;
      box.style.maxHeight = "";
      var need = Math.min(box.offsetHeight, 280, H - 16), r = btn.getBoundingClientRect();
      if (scrollUp) {
        var room = H - r.bottom - 12, d = Math.min(need - room, r.top - 8);
        if (room < need && d > 0 && root.scrollBy) { root.scrollBy(0, d); r = btn.getBoundingClientRect(); }
      }
      var pl = popPlace(r, { w: box.offsetWidth, h: box.offsetHeight }, { w: W, h: H });
      box.style.maxHeight = Math.max(pl.maxHeight, need) + "px";
      box.style.left = (pl.left - r.left) + "px";
    }
    function placePop() { if (popOpen) fitBox(els.pop, els.hiddenBtn, false); }
    function togglePop(force) {
      var was = popOpen;
      popOpen = typeof force === "boolean" ? force : !popOpen;
      renderPop();
      els.pop.hidden = !popOpen;
      els.hiddenBtn.setAttribute("aria-expanded", popOpen ? "true" : "false");
      if (popOpen && !was) { root.addEventListener("resize", placePop); root.addEventListener("scroll", placePop, true); }
      if (!popOpen && was) { root.removeEventListener("resize", placePop); root.removeEventListener("scroll", placePop, true); els.hiddenBtn.focus(); }
      if (popOpen && !was) fitBox(els.pop, els.hiddenBtn, true); else placePop();
    }

    function resetLayout() {
      panelList().forEach(function (p) {
        var i = REG.indexOf(p.def), d = defaults(p.def, i);
        p.order = d.order; p.tracks = d.tracks; p.hidden = p.def.byView ? p.hidden : false; p.max_height = null;
      });
      S.columns = resetColumns(S.columns); closeColumns(); touch(); renderPop(); replace(); redrawAll();
    }

    /* ---- columns (ticket 20): one control for every table panel ---- */
    function colsOf(p) { return p.def.columns || []; }
    function shownCols(p, kind) { return columnsFor(S.columns[p.id], colsOf(p), kind || (S.choice && S.choice.kind)); }
    function redraw(p) { if (p.resp !== undefined) { p.last = null; renderPanel(p, p.resp); } paintColTag(p); }
    function redrawAll() { panelList().forEach(function (p) { if (p.def.columns) redraw(p); }); }
    function setCols(p, list) {
      var d = colDefaults(colsOf(p)), full = colFull(list, colsOf(p));
      if (sameList(full, d)) delete S.columns[p.id]; else S.columns[p.id] = full;
      touch(); redraw(p);
    }
    function hiddenCols(p) {
      var full = colFull(S.columns[p.id], colsOf(p));
      return colsOf(p).filter(function (d) { return !d.off && full.indexOf(d.id) < 0; });
    }
    function paintColTag(p) {
      if (!p.cols) return;
      var h = hiddenCols(p);
      p.colTag.hidden = !h.length;
      p.colTag.textContent = h.length + " hidden";
      p.cols.title = h.length ? "Hidden: " + h.map(function (d) { return d.label; }).join(", ") : "Choose the columns of this table";
    }
    function closeColumns(refocus) {
      if (!colPop) return;
      var p = colPop.p;
      doc.removeEventListener("keydown", colPop.key, true); doc.removeEventListener("click", colPop.out, true); root.removeEventListener("resize", colPop.place);
      colPop.box.remove(); colPop = null;
      p.cols.setAttribute("aria-expanded", "false"); p.cols.closest(".panel").classList.remove("popopen");
      if (refocus) p.cols.focus();
    }
    function openColumns(p) {
      var was = colPop && colPop.p === p;
      closeColumns();
      if (was) return;
      var box = el("div", "cpop"); box.setAttribute("role", "dialog"); box.setAttribute("aria-label", "Columns of " + p.def.title);
      var st = { p: p, box: box };
      st.key = function (e) { if (e.key === "Escape") { e.stopPropagation(); closeColumns(true); } };
      st.out = function (e) { if (!box.contains(e.target) && e.target !== p.cols && !p.cols.contains(e.target)) closeColumns(); };
      st.place = function () { placeColumns(); };
      doc.addEventListener("keydown", st.key, true); doc.addEventListener("click", st.out, true); root.addEventListener("resize", st.place);
      colPop = st;
      p.cols.setAttribute("aria-expanded", "true"); p.cols.closest(".panel").classList.add("popopen");
      p.colWrap.appendChild(box);
      paintColumns();
      placeColumns(true);
      var first = box.querySelector("input,button");
      if (first) first.focus();
    }
    function app() { return doc.getElementById("app"); }
    function paintColumns(focusKey) {
      if (!colPop) return;
      var p = colPop.p, box = colPop.box, defs = colsOf(p), full = colFull(S.columns[p.id], defs), by = {};
      defs.forEach(function (d) { by[d.id] = d; });
      box.textContent = "";
      box.appendChild(el("h3", null, "Columns of " + p.def.title));
      var list = el("div", "cl");
      var hid = defs.map(function (d) { return d.id; }).filter(function (id) { return full.indexOf(id) < 0; });
      full.concat(hid).forEach(function (id) {
        var d = by[id], on = full.indexOf(id) >= 0, at = full.indexOf(id);
        var row = el("div", "cr" + (on ? "" : " off")), lab = el("label");
        var cb = el("input"); cb.type = "checkbox"; cb.checked = on; cb.disabled = !!d.identity; cb.dataset.col = id;
        cb.addEventListener("change", function () { setCols(p, toggleColumn(S.columns[p.id], id, defs)); paintColumns("c:" + id); });
        lab.appendChild(cb); lab.appendChild(el("span", null, d.label));
        if (d.identity) lab.appendChild(el("small", null, "always shown"));
        else if (d.only === "goal") lab.appendChild(el("small", null, "goal view only"));
        row.appendChild(lab);
        [["up", "▲", -1, "Move " + d.label + " up"], ["down", "▼", 1, "Move " + d.label + " down"]].forEach(function (m) {
          var b = el("button", "mv", m[1]); b.type = "button"; b.dataset.mv = m[0] + ":" + id; b.setAttribute("aria-label", m[3]);
          b.disabled = !on || (m[2] < 0 ? at === 0 : at === full.length - 1);
          b.addEventListener("click", function () { setCols(p, moveColumn(S.columns[p.id], id, m[2], defs)); paintColumns(m[0] + ":" + id); });
          row.appendChild(b);
        });
        list.appendChild(row);
      });
      box.appendChild(list);
      box.appendChild(el("p", "muted hint", "Or drag a column title onto another."));
      var ft = el("div", "cf");
      var rs = el("button", "hb", "Reset columns"); rs.type = "button"; rs.disabled = !S.columns[p.id]; rs.dataset.reset = "1";
      rs.addEventListener("click", function () { S.columns = resetColumns(S.columns, p.id); touch(); redraw(p); paintColumns("reset"); });
      var cl = el("button", "hb", "Close"); cl.type = "button"; cl.addEventListener("click", function () { closeColumns(true); });
      ft.appendChild(rs); ft.appendChild(cl); box.appendChild(ft);
      placeColumns();
      if (focusKey) {
        var t = focusKey.indexOf("c:") === 0 ? box.querySelector('[data-col="' + focusKey.slice(2) + '"]') : box.querySelector('[data-mv="' + focusKey + '"]');
        if (!t || t.disabled) { var sib = focusKey.indexOf(":") > 0 ? focusKey.slice(focusKey.indexOf(":") + 1) : ""; t = box.querySelector('[data-mv$=":' + sib + '"]:not(:disabled)') || box.querySelector("button:not(:disabled)"); }
        if (t) t.focus();
      }
    }
    function placeColumns(scrollUp) { if (colPop) fitBox(colPop.box, colPop.p.cols, scrollUp === true); }
    function wireColumnDrag(p) {
      var from = null;
      p.body.addEventListener("dragstart", function (e) {
        var th = e.target.closest && e.target.closest("th[data-col]");
        if (!th) return;
        from = th.dataset.col;
        try { e.dataTransfer.setData("text/plain", from); e.dataTransfer.effectAllowed = "move"; } catch (x) { /* some browsers need the data */ }
      });
      p.body.addEventListener("dragover", function (e) { if (from && e.target.closest && e.target.closest("th[data-col]")) e.preventDefault(); });
      p.body.addEventListener("drop", function (e) {
        var th = e.target.closest && e.target.closest("th[data-col]");
        if (!from || !th) return;
        e.preventDefault();
        var id = from; from = null;
        setCols(p, moveColumnTo(S.columns[p.id], id, th.dataset.col, colsOf(p)));
        if (colPop && colPop.p === p) paintColumns();
      });
      p.body.addEventListener("dragend", function () { from = null; });
    }

    /* ---- data ---- */
    function query() {
      var q = [];
      if (S.squad) q.push("squad=" + encodeURIComponent(S.squad.key));
      if (S.choice) q.push(S.choice.kind + "=" + encodeURIComponent(S.choice.name));
      return q.join("&");
    }

    function getJson(url) {
      var ctl = typeof root.AbortController === "function" ? new root.AbortController() : null;
      var t = ctl ? setT(function () { ctl.abort(); }, FETCH_TIMEOUT_MS) : null;
      return fetchFn(url, ctl ? { signal: ctl.signal, cache: "no-store" } : { cache: "no-store" }).then(function (r) {
        if (t != null) clearT(t);
        if (r.status >= 500) throw new Error("server error");
        return r.json().then(function (j) { return j; }, function () { throw new Error("not json"); });
      }, function (e) { if (t != null) clearT(t); throw e; });
    }

    /* ---- away detection (ticket 13): "since" is the time the page was last visible for this choice, read at load and when the tab
       becomes visible; it is written when the tab hides or closes and when the choice changes. The refresh timer is not involved. ---- */
    var seenKey = null, seenRec = null, cleared = {};
    function choiceKey() { return S.choice ? S.choice.kind + ":" + S.choice.name : null; }
    function syncSince(force) {
      var k = S.squad ? S.squad.key + "|" + (choiceKey() || "") : null;
      if (!force && k === seenKey) return;
      if (seenKey != null && seenRec && S.squad && seenKey.split("|")[0] === S.squad.key) {
        markVisible(seenRec, seenKey.split("|")[1] || null, nowMs()); seenWrite(storage, S.squad.key, seenRec);
      }
      seenKey = k; cleared = {};
      seenRec = S.squad ? seenRead(storage, S.squad.key) : null;
      S.since = seenRec ? sinceFor(seenRec, choiceKey(), nowMs()) : null;
    }
    var away = false;   /* a hidden tab that is closed later fires pagehide too: the time it was hidden stays */
    function leave() {
      if (away || !S.squad || seenKey == null) return;
      away = true;
      seenRec = seenRec || seenRead(storage, S.squad.key);
      markVisible(seenRec, choiceKey(), nowMs()); seenWrite(storage, S.squad.key, seenRec);
    }
    doc.addEventListener("visibilitychange", function () {
      if (doc.visibilityState === "hidden") leave();
      else if (doc.visibilityState === "visible") { away = false; syncSince(true); poller.now(); }
    });
    root.addEventListener("pagehide", leave);
    function withSince(route) {
      var sq = sinceQuery(route, S.since);
      return sq ? route + (route.indexOf("?") < 0 ? "?" : "&") + sq : route;
    }

    function loadData() {
      syncSince();
      var q = query(), jobs = [getJson(withSince("/api/squads"))];
      var withRoute = S.choice ? panelList().filter(function (p) { return p.def.route; }) : [];
      withRoute.forEach(function (p) { jobs.push(getJson(withSince(p.def.route + (p.def.route.indexOf("?") < 0 ? "?" : "&") + q))); });
      return Promise.all(jobs).then(function (rs) { return { q: q, squads: rs[0], panels: withRoute, resp: rs.slice(1) }; });
    }

    function ctxFor(p) {
      return { tz: tz, now: nowMs(), fmtTime: function (i) { return fmtTime(i, tz); }, ageWords: ageWords,
               setCount: function (n, hot) { p.count.textContent = String(n); p.count.hidden = false; p.count.classList.toggle("hot", !!hot); },
               setBanner: setBanner, columns: function (kind) { return shownCols(p, kind); } };
    }

    function setBanner(node) { els.banner.textContent = ""; if (node) els.banner.appendChild(node); }

    /* design-v7 s5: a panel with texts here shows a muted "Loading" note until its first answer, and a dashed --err note on a failed answer
       (resp.error, or an answer with no data and the panel unknown). resp.errors [{file, reason}] adds the note above rows that were read. */
    var PANEL_TEXT = { tasks: { loading: "Loading tasks\u2026", error: "Could not read the tasks of this scope." } };
    function stateNote(cls, text, extra) {
      var n = el("p", "note pstate " + cls, text);
      if (extra) n.appendChild(el("span", "pwhy", extra));
      return n;
    }
    function failWhy(resp) {
      if (!resp) return "";
      var w = [];
      if (typeof resp.error === "string") w.push(resp.error);
      (Array.isArray(resp.errors) ? resp.errors : []).forEach(function (e) { if (e) w.push((e.file ? e.file + ": " : "") + (e.reason || "")); });
      return w.join("; ");
    }
    function renderPanel(p, resp) {
      var txt = PANEL_TEXT[p.id];
      if (txt && resp === undefined) {
        if (p.last == null) { p.body.textContent = ""; p.body.appendChild(stateNote("pload", txt.loading)); }
        return;
      }
      var key = JSON.stringify(resp);
      p.resp = resp;
      if (p.last === key) return;
      p.last = key;
      var v = panelView(resp, p.def);
      var why = txt ? failWhy(resp) : "";
      if (txt && (typeof (resp || {}).error === "string" || (v.kind === "unknown" && resp && resp.data == null))) {
        p.body.textContent = ""; p.body.appendChild(stateNote("perr", txt.error, why || v.sources.join(", "))); p.count.hidden = true; return;
      }
      p.body.textContent = "";
      p.unk.hidden = v.sources.length === 0;
      p.unk.textContent = v.sources.length ? "unknown: " + v.sources.join(", ") : "";
      if (v.kind === "version") { p.body.appendChild(el("p", "note", "unknown: board version")); p.count.hidden = true; return; }
      if (v.kind === "unknown") { p.body.appendChild(el("p", "note", "unknown: " + v.sources.join(", "))); p.count.hidden = true; return; }
      try { p.def.render(p.body, resp.data, ctxFor(p)); }
      catch (e) { p.body.textContent = ""; p.body.appendChild(el("p", "note", "unknown: " + p.id)); return; }
      if (why) p.body.insertBefore(stateNote("perr", txt.error, why), p.body.firstChild);
    }

    function onOk(v) {
      if (v.q !== query()) return;   /* the choice changed while this load ran: its rows are not for this page; the next load is queued */
      var sq = v.squads && v.squads.data;
      if (sq && Array.isArray(sq.squads)) {
        var cur = S.squad && S.squad.key;
        S.squads = sq.squads; S.demo = sq.demo === true; els.demo.hidden = !S.demo;
        S.squad = S.squads.filter(function (s) { return s.key === cur; })[0] || S.squad;
      }
      if (BOARD.hooks.data) BOARD.hooks.data(v.squads, S);
      v.panels.forEach(function (p, i) { renderPanel(p, v.resp[i]); });
      panelList().forEach(paintColTag);
      var n = needsFrom(v.resp);
      if (n != null) S.needs = n;
      S.status = "ok"; S.lastOk = iso();
      paintFresh(); paintTitle();
      if (!loadedOnce) { loadedOnce = true; paintPickers(); replace(); }
      else engine.request();
    }

    function onFail(n, stale) {
      panelList().forEach(function (p) { if (PANEL_TEXT[p.id] && p.resp === undefined) renderPanel(p, { error: "the board server did not answer (server error)" }); });
      if (stale) S.status = "stale";
      paintFresh();
    }

    var poller = makePoller({ load: load, onOk: onOk, onFail: onFail, setTimeout: setT, clearTimeout: clearT, interval: REFRESH_MS });

    /* ---- startup ---- */
    function loadSaved() {
      return getJson("/api/ui?squad=" + encodeURIComponent(S.squad.key)).then(function (j) {
        var d = j && j.data ? j.data : { ui: null, status: "unreadable" };
        S.saveStatus = d.status === "unreadable" ? "unreadable" : (d.status === "unwritable" ? "unwritable" : "ok");
        var copy = null;
        try { copy = storage ? JSON.parse(storage.getItem(storeKey()) || "null") : null; S.notes.storage = ""; }
        catch (e) { S.notes.storage = "This browser blocks storage: settings are kept in the squad folder only."; }
        var file = d.status === "unreadable" ? null : d.ui;
        S.columns = {};
        applySaved(pickNewer(file, copy));
        showNotes();
        return true;
      }, function () { return false; });
    }

    /* boot: session token, squad list, saved state, choice. Runs again from the poller until it has worked once. */
    function boot() {
      return getJson("/api/session").then(function (j) {
        S.token = (j.data && j.data.token) || "";
        return getJson("/api/squads");
      }).then(function (j) {
        var d = j.data || {};
        S.squads = d.squads || []; S.demo = d.demo === true; els.demo.hidden = !S.demo;
        var ini = d.initial || (BOARD.hooks.flags && BOARD.hooks.flags()) || {};
        S.squad = S.squads.filter(function (s) { return s.key === ini.squad && !s.flat; })[0] || S.squads.filter(function (s) { return !s.flat; })[0] || null;
        if (!S.squad) { paintPickers(); throw new Error("no squad"); }
        return loadSaved().then(function (ok) {
          if (!ok) throw new Error("no saved state answer");
          if (BOARD.hooks.boot) return BOARD.hooks.boot(S, d, ini);
          if (ini.goal) S.choice = { kind: "goal", name: ini.goal };
          else if (ini.scope) S.choice = { kind: "scope", name: ini.scope };
          if (!S.choice) {
            var first = (S.squad.scopes || [])[0];
            if (first) S.choice = { kind: "scope", name: first };
          }
        }).then(function () {
          applyFont(); paintPickers(); setFlags(); paintTitle();
          booted = true;
        });
      });
    }

    function load() { return booted ? loadData() : boot().then(loadData); }

    function init() {
      build();
      engine = BOARD.layout.mount({
        canvas: els.canvas,
        get: function () { return { panels: panelList(), scale: scale() }; },
        set: function (id, patch) { Object.keys(patch).forEach(function (k) { P[id][k] = patch[k]; }); },
        changed: function () { touch(); setFlags(); renderPop(); }
      });
      REG.forEach(function (def, i) { P[def.id] = makePanel(def, i); });
      applyFont(); paintFresh(); showNotes(); redrawAll();
      root.addEventListener("resize", function () { engine.request(true); });
      setT(function () { if (!placedOnce) replace(); }, 5000);   /* first load: place after 5 s even if a panel has not answered */
      poller.start();
    }

    init();
    BOARD.ctx = { state: S, els: els, setChoice: setChoice, paint: paintPickers, poller: poller, touch: touch, clear: clearPanels,
                  getJson: getJson, withSince: withSince, panels: P,
                  seen: { scopeKey: function () { return S.choice && S.choice.kind === "scope" ? S.choice.name : ""; },
                          clear: function (scope, task, count) { clearTask(cleared, scope, task, count, nowMs()); },
                          shown: function (scope, task, n) { return shownNew(cleared, scope, task, n, S.since); },
                          rowNew: function (n, scopes) { return rowNew(cleared, n, S.since, scopes); } }, fmtClock: function (i) { return fmtClock(i, tz); }, now: nowMs, paintTitle: paintTitle };
    BOARD.page = { state: S, panels: P, poller: poller, engine: engine, paintFresh: paintFresh, setFont: setFont, resetLayout: resetLayout,
                   replan: replan, replace: replace, snapshot: snapshot, setChoice: setChoice, touch: touch };
    return BOARD.page;
  }
  BOARD.start = start;

  if (!root.BOARD_NO_AUTOSTART && root.document && root.document.getElementById) {
    var go = function () { if (root.document.getElementById("app")) start(); };
    if (root.document.readyState === "loading") root.document.addEventListener("DOMContentLoaded", go); else go();
  }
})(typeof window !== "undefined" ? window : this);
