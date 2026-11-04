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

  /* ---------- panel registry ---------- */
  var REG = [];
  /* registerPanel({id, title, route, maxPx, span, spans, render(body, data, ctx), isEmpty(data)})
     route: the API path the panel reads (e.g. "/api/inbox"); span in twelfths (default 4); maxPx at Normal text. */
  function registerPanel(def) {
    if (!def || !def.id || REG.some(function (d) { return d.id === def.id; })) return;
    REG.push(def);
  }

  BOARD.REFRESH_MS = REFRESH_MS; BOARD.FAILS_STALE = FAILS_STALE; BOARD.FONTS = FONTS;
  BOARD.fmtTime = fmtTime; BOARD.fmtClock = fmtClock; BOARD.fmtDate = fmtDate; BOARD.zoneOffset = zoneOffset;
  BOARD.readZone = readZone; BOARD.ageWords = ageWords; BOARD.titleFor = titleFor; BOARD.pickNewer = pickNewer;
  BOARD.needsFrom = needsFrom; BOARD.panelView = panelView; BOARD.makePoller = makePoller;
  BOARD.registerPanel = registerPanel; BOARD.panels = REG;

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

    var S = { squads: [], squad: null, token: "", choice: null, recent: [], font: "normal", auto: true,
              needs: null, lastOk: null, status: "loading", saveStatus: "ok", notes: {}, saved_at: null };
    var P = {};          /* panel id -> {id, def, order, span, hidden, max_height, el, body, hdr, last} */
    var engine = null, saveTimer = null, loadedOnce = false, popOpen = false, booted = false;

    var els = {};
    function build() {
      var app = doc.getElementById("app");
      app.textContent = "";
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
      fr3.appendChild(els.font); fr3.appendChild(els.hiddenBtn); fr3.appendChild(els.reset); r3.appendChild(fr3);
      header.appendChild(r1); header.appendChild(r3);
      els.notes = el("div", "notes"); els.notes.setAttribute("role", "status");
      els.banner = el("div", "bannerslot");   /* the permission banner: not a panel, no hide, no drag */
      els.pick = el("p", "note"); els.pick.hidden = true;
      var main = el("main"); els.canvas = el("div"); els.canvas.id = "canvas"; main.appendChild(els.canvas);
      els.pop = el("div", "pop"); els.pop.hidden = true; els.pop.setAttribute("role", "menu");
      [header, els.notes, els.banner, els.pick, main, els.pop].forEach(function (n) { app.appendChild(n); });
      els.squad.addEventListener("change", function () { switchSquad(els.squad.value); });
      els.choice.addEventListener("change", function () { setChoice(els.choice.value); });
      els.reset.addEventListener("click", resetLayout);
      els.hiddenBtn.addEventListener("click", function (e) { e.stopPropagation(); togglePop(); });
      doc.addEventListener("click", function () { if (popOpen) togglePop(false); });
      doc.addEventListener("keydown", function (e) { if (e.key === "Escape" && popOpen) togglePop(false); });
    }

    /* ---- panels ---- */
    function defaults(def, i) { return { order: i, span: def.span || 4, hidden: false, max_height: null }; }

    function makePanel(def, i) {
      var d = defaults(def, i);
      var p = { id: def.id, def: def, order: d.order, span: d.span, hidden: d.hidden, max_height: d.max_height,
                maxPx: def.maxPx || 400, spans: def.spans || [4, 6, 8, 12] };
      var sec = el("section", "panel"); sec.dataset.panel = def.id; sec.setAttribute("aria-label", def.title);
      var ph = el("div", "ph"); ph.tabIndex = 0; ph.setAttribute("aria-label", def.title + ": arrows move, Shift and arrows resize");
      ph.appendChild(el("span", "grip", "⋮⋮"));
      ph.appendChild(el("h2", null, def.title));
      p.count = el("span", "count"); p.count.hidden = true; ph.appendChild(p.count);
      p.unk = el("span", "chip unk"); p.unk.hidden = true; ph.appendChild(p.unk);
      ph.appendChild(el("span", "sp"));
      p.fit = el("button", "pbtn", "Fit"); p.fit.type = "button"; p.fit.hidden = true; p.fit.title = "Back to the height of the content";
      p.hide = el("button", "pbtn", "Hide"); p.hide.type = "button"; p.hide.title = "Hide this panel";
      ph.appendChild(p.fit); ph.appendChild(p.hide);
      var pb = el("div", "pb"); p.body = el("div", "pbi"); pb.appendChild(p.body);
      sec.appendChild(ph); sec.appendChild(pb);
      ["e", "s", "se"].forEach(function (d2) {
        var h = el("div", "rz " + d2); h.addEventListener("pointerdown", function (e) { e.preventDefault(); e.stopPropagation(); engine.resize(p, d2, e); });
        sec.appendChild(h);
      });
      p.el = sec; p.hdr = ph;
      ph.addEventListener("pointerdown", function (e) { engine.drag(p, e); });
      ph.addEventListener("keydown", function (e) { if (e.target === ph) engine.key(p, e); });
      p.fit.addEventListener("click", function () { p.max_height = null; touch({ auto: false }); engine.relayout(); });
      p.hide.addEventListener("click", function () { p.hidden = true; touch(); replan(); renderPop(); });
      els.canvas.appendChild(sec);
      engine.observe(p.body);
      return p;
    }

    function panelList() { return Object.keys(P).map(function (k) { return P[k]; }); }

    function setFlags() {
      panelList().forEach(function (p) {
        p.el.hidden = !!p.hidden;
        p.fit.hidden = p.max_height == null;
      });
    }

    function replan() {
      setFlags();
      if (S.auto) engine.plan(); else engine.relayout();
      setFlags();
    }

    /* ---- saved state ---- */
    function snapshot() {
      var panels = {};
      panelList().forEach(function (p) {
        var r = { order: p.order, span: p.span, hidden: !!p.hidden };
        if (p.max_height != null) r.max_height = p.max_height;
        panels[p.id] = r;
      });
      return { version: 1, saved_at: S.saved_at, font: S.font, choice: S.choice, recent: S.recent, panels: panels, auto: S.auto };
    }

    function applySaved(ui) {
      if (!ui || typeof ui !== "object") return;
      if (FONTS.some(function (f) { return f[0] === ui.font; })) S.font = ui.font;
      if (ui.choice && (ui.choice.kind === "goal" || ui.choice.kind === "scope")) S.choice = ui.choice;
      if (Array.isArray(ui.recent)) S.recent = ui.recent.slice(0, RECENT_MAX);
      if (typeof ui.auto === "boolean") S.auto = ui.auto;
      S.saved_at = ui.saved_at || null;
      var pan = ui.panels || {};
      panelList().forEach(function (p) {
        var r = pan[p.id];
        if (!r) return;
        if (Number.isInteger(r.order)) p.order = r.order;
        if (Number.isInteger(r.span) && r.span >= 1) p.span = r.span;
        p.hidden = !!r.hidden;
        p.max_height = Number.isInteger(r.max_height) ? r.max_height : null;
      });
    }

    function storeKey() { return "squad-board-ui:" + (S.squad ? S.squad.key : ""); }

    function touch(extra) {
      if (extra && typeof extra.auto === "boolean") S.auto = extra.auto;
      S.saved_at = iso();
      var snap = snapshot();
      try { if (storage) storage.setItem(storeKey(), JSON.stringify(snap)); S.notes.storage = ""; }
      catch (e) { S.notes.storage = "This browser blocks storage: settings are kept in the squad folder only."; }
      clearT(saveTimer);
      saveTimer = setT(function () { put(snap); }, SAVE_DELAY_MS);
      showNotes();
    }

    function put(snap) {
      if (!S.token || !S.squad) return;
      fetchFn("/api/ui?squad=" + encodeURIComponent(S.squad.key), {
        method: "PUT", headers: { "Content-Type": "application/json", "X-Board-Token": S.token }, body: JSON.stringify(snap)
      }).then(function (r) { S.saveStatus = r.ok ? "ok" : (r.status === 507 ? "unwritable" : "failed"); showNotes(); },
              function () { S.saveStatus = "failed"; showNotes(); });
    }

    function showNotes() {
      var msgs = [];
      if (S.saveStatus === "unwritable") msgs.push("The settings file in the squad folder cannot be written. Settings are kept in this browser only.");
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
      Array.prototype.forEach.call(els.font.children, function (b) {
        b.setAttribute("aria-pressed", b.dataset.font === S.font ? "true" : "false");
      });
      return f[2];
    }

    function setFont(name) {
      if (S.font === name) return;
      S.font = name; applyFont(); touch(); replan();
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

    function paintTitle() { doc.title = titleFor(S.squad ? S.squad.name : "squad board", S.needs); }

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
      var hid = panelList().filter(function (p) { return p.hidden; });
      els.hiddenBtn.textContent = "Panels" + (hid.length ? " (" + hid.length + " hidden)" : "") + " ▾";
      if (!hid.length) els.pop.appendChild(el("p", "muted", "No hidden panels."));
      hid.forEach(function (p) {
        var b = el("button", "hb", "Show " + p.def.title); b.type = "button"; b.setAttribute("role", "menuitem");
        b.addEventListener("click", function (e) { e.stopPropagation(); p.hidden = false; touch(); replan(); renderPop(); });
        els.pop.appendChild(b);
      });
    }
    function togglePop(force) {
      popOpen = typeof force === "boolean" ? force : !popOpen;
      renderPop();
      els.pop.hidden = !popOpen;
      els.hiddenBtn.setAttribute("aria-expanded", popOpen ? "true" : "false");
    }

    function resetLayout() {
      panelList().forEach(function (p) {
        var i = REG.indexOf(p.def), d = defaults(p.def, i);
        p.order = d.order; p.span = d.span; p.hidden = false; p.max_height = null;
      });
      S.auto = true; touch(); renderPop(); replan();
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

    function loadData() {
      var q = query(), jobs = [getJson("/api/squads")];
      var withRoute = S.choice ? panelList().filter(function (p) { return p.def.route; }) : [];
      withRoute.forEach(function (p) { jobs.push(getJson(p.def.route + (p.def.route.indexOf("?") < 0 ? "?" : "&") + q)); });
      return Promise.all(jobs).then(function (rs) { return { q: q, squads: rs[0], panels: withRoute, resp: rs.slice(1) }; });
    }

    function ctxFor(p) {
      return { tz: tz, now: nowMs(), fmtTime: function (i) { return fmtTime(i, tz); }, ageWords: ageWords,
               setCount: function (n, hot) { p.count.textContent = String(n); p.count.hidden = false; p.count.classList.toggle("hot", !!hot); },
               setBanner: setBanner };
    }

    function setBanner(node) { els.banner.textContent = ""; if (node) els.banner.appendChild(node); }

    function renderPanel(p, resp) {
      var key = JSON.stringify(resp);
      if (p.last === key) return;
      p.last = key;
      var v = panelView(resp, p.def);
      p.body.textContent = "";
      p.unk.hidden = v.sources.length === 0;
      p.unk.textContent = v.sources.length ? "unknown: " + v.sources.join(", ") : "";
      if (v.kind === "version") { p.body.appendChild(el("p", "note", "unknown: board version")); p.count.hidden = true; return; }
      if (v.kind === "unknown") { p.body.appendChild(el("p", "note", "unknown: " + v.sources.join(", "))); p.count.hidden = true; return; }
      try { p.def.render(p.body, resp.data, ctxFor(p)); }
      catch (e) { p.body.textContent = ""; p.body.appendChild(el("p", "note", "unknown: " + p.id)); }
    }

    function onOk(v) {
      if (v.q !== query()) return;   /* the choice changed while this load ran: its rows are not for this page; the next load is queued */
      var sq = v.squads && v.squads.data;
      if (sq && Array.isArray(sq.squads)) {
        var cur = S.squad && S.squad.key;
        S.squads = sq.squads;
        S.squad = S.squads.filter(function (s) { return s.key === cur; })[0] || S.squad;
      }
      v.panels.forEach(function (p, i) { renderPanel(p, v.resp[i]); });
      var n = needsFrom(v.resp);
      if (n != null) S.needs = n;
      S.status = "ok"; S.lastOk = iso();
      paintFresh(); paintTitle();
      if (!loadedOnce) { loadedOnce = true; paintPickers(); replan(); }
      else engine.request();
    }

    function onFail(n, stale) {
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
        S.squads = d.squads || [];
        var ini = d.initial || {};
        S.squad = S.squads.filter(function (s) { return s.key === ini.squad && !s.flat; })[0] || S.squads.filter(function (s) { return !s.flat; })[0] || null;
        if (!S.squad) { paintPickers(); throw new Error("no squad"); }
        return loadSaved().then(function (ok) {
          if (!ok) throw new Error("no saved state answer");
          if (ini.goal) S.choice = { kind: "goal", name: ini.goal };
          else if (ini.scope) S.choice = { kind: "scope", name: ini.scope };
          if (!S.choice) {
            var first = (S.squad.scopes || [])[0];
            if (first) S.choice = { kind: "scope", name: first };
          }
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
        changed: function (x) { touch(x); setFlags(); renderPop(); }
      });
      REG.forEach(function (def, i) { P[def.id] = makePanel(def, i); });
      applyFont(); paintFresh(); showNotes();
      root.addEventListener("resize", function () { engine.request(); });
      poller.start();
    }

    init();
    BOARD.page = { state: S, panels: P, poller: poller, engine: engine, paintFresh: paintFresh, setFont: setFont, resetLayout: resetLayout,
                   replan: replan, snapshot: snapshot, setChoice: setChoice, touch: touch };
    return BOARD.page;
  }
  BOARD.start = start;

  if (!root.BOARD_NO_AUTOSTART && root.document && root.document.getElementById) {
    var go = function () { if (root.document.getElementById("app")) start(); };
    if (root.document.readyState === "loading") root.document.addEventListener("DOMContentLoaded", go); else go();
  }
})(typeof window !== "undefined" ? window : this);
