/* squad-board "Work time" panel: one swimlane per agent, time on the x-axis (ticket 16, design-v5 / proto-timeline-1).
   Own file, one panel: BOARD.registerPanel({id: "worktime", ...}). Delete this file and its <script> line to cut the panel.
   Every rule is a plain function on BOARD.TIMELINE (no DOM), so a test page can call it. Untrusted text (agent names,
   tasks, "no transcript: <agent>") reaches the DOM only through textContent / title properties; no markup strings.
   Time on the wire is UTC epoch seconds; all labels use the zone of the browser (never subtract local times: DST). */
(function (root) {
  "use strict";
  var BOARD = root.BOARD = root.BOARD || {};
  var T = BOARD.TIMELINE = {};
  var MIN = 60, HR = 3600, DAY = 86400;
  var GAP_MIN = 15, GAP_MAX = 240, GAP_DEF = 60;       /* idle break setting, minutes */
  var MIN_SPAN = 180, MAX_SPAN = 400 * DAY, DRAG_PX = 6, WHEEL_WAIT_MS = 150;
  var STATES = ["working", "waiting", "blocked", "idle"];
  var PRESETS = [["1h", "Last 1 h"], ["today", "Today"], ["3d", "3 days"], ["all", "All"]];
  var GAPS = [15, 30, 60, 120, 240];
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var WDAY = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  var MARK_NAMES = { handin: "hand-in", fail: "FAIL", pass: "PASS", blocked: "BLOCKED", commit: "commit", merge: "merge" };
  var warned = {};

  function warnOnce(key, msg) {
    if (warned[key]) return;
    warned[key] = true;
    if (root.console && root.console.warn) root.console.warn("work time: " + msg);
  }
  function num(v) { return typeof v === "number" && isFinite(v) ? v : null; }
  function pad2(n) { return (n < 10 ? "0" : "") + n; }

  /* ---------- time in a zone ---------- */
  var fmts = {};
  function zoneFmt(tz) {
    var k = tz || "UTC";
    if (fmts[k]) return fmts[k];
    var o = { hourCycle: "h23", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit" };
    var f;
    try { f = new Intl.DateTimeFormat("en-GB", Object.assign({ timeZone: k }, o)); }
    catch (e) { f = new Intl.DateTimeFormat("en-GB", Object.assign({ timeZone: "UTC" }, o)); }
    fmts[k] = f;
    return f;
  }
  /* loc(t, tz): local calendar parts of the instant t (UTC seconds) and its UTC offset in minutes at that instant */
  function loc(t, tz) {
    var o = {};
    zoneFmt(tz).formatToParts(new Date(t * 1000)).forEach(function (p) { o[p.type] = p.value; });
    var h = o.hour === "24" ? 0 : +o.hour;
    var local = Date.UTC(+o.year, +o.month - 1, +o.day, h, +o.minute, +o.second) / 1000;
    return { y: +o.year, mo: +o.month, d: +o.day, h: h, mi: +o.minute, s: +o.second,
             wd: new Date(Date.UTC(+o.year, +o.month - 1, +o.day)).getUTCDay(), off: Math.round((local - Math.floor(t)) / 60) };
  }
  function dayKey(l) { return l.y * 10000 + l.mo * 100 + l.d; }
  function sod(l) { return l.h * 3600 + l.mi * 60 + l.s; }
  function hhmm(t, tz) { var l = loc(t, tz); return pad2(l.h) + ":" + pad2(l.mi); }
  function stamp(t, tz) { var l = loc(t, tz); return l.y + "-" + pad2(l.mo) + "-" + pad2(l.d) + " " + pad2(l.h) + ":" + pad2(l.mi); }
  function dayLabel(t, tz, short) {
    var l = loc(t, tz);
    return short ? l.d + " " + MON[l.mo - 1] : WDAY[l.wd] + " " + l.d + " " + MON[l.mo - 1];
  }
  function offLabel(t, tz) {
    var m = loc(t, tz).off, s = m < 0 ? "-" : "+";
    m = Math.abs(m);
    var h = Math.floor(m / 60), r = m - h * 60;
    return (m === 0 ? "UTC" : s + pad2(h) + (r ? ":" + pad2(r) : ""));
  }
  /* the first instant at or after t whose local time of day is a multiple of `step` minutes */
  function nextAligned(t, step, tz) {
    var l = loc(t, tz), m = (sod(l)) / 60;
    var a = Math.ceil(m / step - 1e-9) * step;
    return t + Math.round((a - m) * 60);
  }
  /* the next local midnight after t (a 23 h or 25 h day is handled by looking at the local clock, not by adding 86400) */
  function nextMidnight(t, tz) {
    var d0 = dayKey(loc(t, tz)), c = t;
    for (var i = 0; i < 5; i++) {
      var l = loc(c, tz), s = sod(l);
      if (dayKey(l) === d0) c += DAY - s;
      else { if (s === 0) return c; c -= s; }
    }
    return c;
  }
  function startOfDay(t, tz) {
    var d0 = dayKey(loc(t, tz)), c = t - sod(loc(t, tz));
    for (var i = 0; i < 5; i++) {
      var l = loc(c, tz), s = sod(l), dk = dayKey(l);
      if (dk === d0) { if (s === 0) return c; c -= s; }
      else c += DAY - s;
    }
    return c;
  }

  /* ---------- rules ---------- */
  function clampGap(n) {
    n = Math.round(Number(n));
    if (!isFinite(n)) return GAP_DEF;
    return Math.min(GAP_MAX, Math.max(GAP_MIN, n));
  }

  /* durLabel(seconds): "45 min", "14 h 40 min", "2 d 3 h". From a difference of UTC epochs, so a DST change cannot move it. */
  function durLabel(sec) {
    var m = Math.round(Math.max(0, sec) / 60);
    if (m < 60) return m + " min";
    var h = Math.floor(m / 60), r = m - h * 60;
    if (h >= 48) { var d = Math.floor(h / 24), hh = h - d * 24; return d + " d" + (hh ? " " + hh + " h" : ""); }
    return h + " h" + (r ? " " + r + " min" : "");
  }
  /* hm(seconds): hours and minutes, never a percent ("2 h 5 min") */
  function hm(sec) { var s = Math.max(0, Math.round(sec)), m = Math.floor(s / 60); return Math.floor(m / 60) + " h " + (m % 60) + " min"; }

  /* breakLabel(gapSeconds, kind): the one place the words night / weekend / idle are written */
  function breakLabel(gapSeconds, kind) {
    var w = kind === "night" || kind === "weekend" ? kind : "idle";
    return w + " · " + durLabel(gapSeconds);
  }
  /* gapKind(start, end, tz): "weekend" (36 h or more touching a local Saturday or Sunday), "night" (4 h or more touching
     22:00-06:00 local), else "idle" */
  function gapKind(start, end, tz) {
    var d = end - start, wk = false, night = false;
    if (d < 4 * HR) return "idle";
    for (var t = start; t <= end; t += 30 * MIN) {
      var l = loc(t, tz);
      if (l.wd === 6 || l.wd === 0) wk = true;
      if (l.h < 6 || l.h >= 22) night = true;
    }
    return d >= 36 * HR && wk ? "weekend" : night ? "night" : "idle";
  }

  function union(list) {
    var a = list.slice().sort(function (x, y) { return x[0] - y[0]; }), out = [];
    a.forEach(function (r) {
      var l = out[out.length - 1];
      if (l && r[0] <= l[1]) l[1] = Math.max(l[1], r[1]); else out.push([r[0], r[1]]);
    });
    return out;
  }
  function subtract(a, cut) {   /* a, cut: sorted unions of [s, e] */
    var out = [];
    a.forEach(function (r) {
      var s = r[0];
      cut.forEach(function (c) {
        if (c[1] <= s || c[0] >= r[1]) return;
        if (c[0] > s) out.push([s, c[0]]);
        s = Math.max(s, c[1]);
      });
      if (s < r[1]) out.push([s, r[1]]);
    });
    return out;
  }

  /* collapse(pieces, minutes, showReal, tz): the gaps the page folds into a hatched break. The reader (ticket 15) flags
     `collapsible` (not waiting, not blocked, whole gap over its gap_min); the page folds the stretches of those pieces that
     no other piece covers and that are longer than the setting (15 min .. 4 h). Waiting and blocked time never folds.
     "Show real time" returns the pieces unchanged. -> {pieces, breaks: [{start, end, seconds, kind, label}]} */
  function collapse(pieces, minutes, showReal, tz) {
    if (showReal) return { pieces: pieces, breaks: [] };
    var lim = clampGap(minutes) * MIN, hot = [], cold = [];
    pieces.forEach(function (p) {
      if (!(p.end > p.start)) return;
      if (p.collapsible === true && p.bucket !== "waiting" && p.bucket !== "blocked") hot.push([p.start, p.end]);
      else cold.push([p.start, p.end]);
    });
    var gaps = subtract(union(hot), union(cold)), breaks = [];
    gaps.forEach(function (g) {
      var d = g[1] - g[0];
      if (d > lim) { var k = gapKind(g[0], g[1], tz); breaks.push({ start: g[0], end: g[1], seconds: d, kind: k, label: breakLabel(d, k) }); }
    });
    return { pieces: pieces, breaks: breaks };
  }

  /* taskFilter(pieces, tasks): tasks is a list of task ids; null in it means "no task" (unattributed, idle excluded).
     An empty or missing list keeps every piece. */
  function taskFilter(pieces, tasks) {
    if (!tasks || !tasks.length) return pieces;
    return pieces.filter(function (p) {
      var t = p.task == null ? null : p.task;
      return tasks.indexOf(t) >= 0 && !(t === null && p.bucket === "idle");
    });
  }

  /* presetRange(name, now, tz): {from, to, preset} in UTC seconds; "all" has from null (the reader starts at the first record) */
  function presetRange(name, now, tz) {
    now = Math.floor(now);
    if (name === "1h") return { from: now - HR, to: now, preset: name };
    if (name === "3d") return { from: now - 3 * DAY, to: now, preset: name };
    if (name === "today") return { from: startOfDay(now, tz), to: now, preset: name };
    if (name === "all") return { from: null, to: now, preset: name };
    return null;
  }

  /* zoomRange(range, anchor, factor): factor 0.5 zooms in, 2 zooms out; the anchor keeps its place */
  function zoomRange(range, anchor, factor) {
    var a = Math.min(range.to, Math.max(range.from, anchor));
    var from = a - (a - range.from) * factor, to = a + (range.to - a) * factor;
    var span = to - from;
    if (span < MIN_SPAN) { var c = (from + to) / 2; from = c - MIN_SPAN / 2; to = c + MIN_SPAN / 2; }
    if (span > MAX_SPAN) { var c2 = (from + to) / 2; from = c2 - MAX_SPAN / 2; to = c2 + MAX_SPAN / 2; }
    return { from: Math.round(from), to: Math.round(to) };
  }
  function panRange(range, fraction) {
    var d = Math.round((range.to - range.from) * fraction);
    return { from: range.from + d, to: range.to + d };
  }

  /* dragRange(x0, x1, range, width, scale): a drag on the axis from x0 to x1 (px) -> the range under it, or null for a
     click or a drag under 6 px. With a scale (breaks) the pixel is mapped through it, else linearly. */
  function dragRange(x0, x1, range, width, scale) {
    if (!(width > 0) || Math.abs(x1 - x0) < DRAG_PX) return null;
    var fr = function (x) { return Math.max(0, Math.min(1, x / width)); };
    var at = function (f) { return scale ? scale.tAt(f) : range.from + f * (range.to - range.from); };
    var a = at(fr(Math.min(x0, x1))), b = at(fr(Math.max(x0, x1)));
    if (!(b > a)) return null;
    if (b - a < MIN_SPAN) { var c = (a + b) / 2; a = c - MIN_SPAN / 2; b = c + MIN_SPAN / 2; }
    return { from: Math.round(a), to: Math.round(b) };
  }

  /* makeScale(range, breaks): real time between breaks is linear; each break takes a fixed share of the width.
     x(t) -> fraction 0..1 (snaps into a break's edge), tAt(fraction) -> time. */
  function makeScale(range, breaks) {
    var br = (breaks || []).map(function (b) { return { start: Math.max(b.start, range.from), end: Math.min(b.end, range.to), src: b }; })
      .filter(function (b) { return b.end > b.start; }).sort(function (a, b) { return a.start - b.start; });
    var segs = [], c = range.from;
    br.forEach(function (b) { if (b.start > c) segs.push({ a: c, b: b.start }); c = Math.max(c, b.end); });
    if (range.to > c) segs.push({ a: c, b: range.to });
    var nb = br.length, bw = nb ? Math.min(0.045, 0.15 / nb) : 0, avail = 1 - nb * bw, total = 0;
    segs.forEach(function (s) { total += s.b - s.a; });
    var x = 0, i = 0;
    var blist = [];
    br.forEach(function (b) {
      while (i < segs.length && segs[i].b <= b.start) { segs[i].x0 = x; segs[i].w = (segs[i].b - segs[i].a) / total * avail; x += segs[i].w; i++; }
      blist.push({ start: b.start, end: b.end, x0: x, w: bw, kind: b.src.kind, label: b.src.label, seconds: b.src.seconds });
      x += bw;
    });
    while (i < segs.length) { segs[i].x0 = x; segs[i].w = (segs[i].b - segs[i].a) / total * avail; x += segs[i].w; i++; }
    function xOf(t) {
      for (var k = 0; k < segs.length; k++) {
        var s = segs[k];
        if (t < s.a) return s.x0;
        if (t <= s.b) return s.x0 + (t - s.a) / (s.b - s.a) * s.w;
      }
      var l = segs[segs.length - 1];
      return l ? l.x0 + l.w : 0;
    }
    function tAt(f) {
      for (var k = 0; k < segs.length; k++) {
        var s = segs[k];
        if (f <= s.x0 + s.w) {
          if (f < s.x0) return k ? segs[k - 1].b : s.a;
          return s.a + (f - s.x0) / s.w * (s.b - s.a);
        }
      }
      return segs.length ? segs[segs.length - 1].b : range.to;
    }
    /* seconds of [a, b] that are drawn (not inside a break) */
    function visible(a, b) {
      var sum = 0;
      segs.forEach(function (s) { var lo = Math.max(a, s.a), hi = Math.min(b, s.b); if (hi > lo) sum += hi - lo; });
      return sum;
    }
    return { range: range, segs: segs, breaks: blist, avail: avail, total: total, x: xOf, tAt: tAt, visible: visible };
  }

  /* normalizePieces(list): the piece fields of ticket 15. A piece with no start is dropped; a piece with no end or a bucket
     outside the four states is kept as "unknown" (zero width when it has no end) and logged to the console once. */
  function normalizePieces(list) {
    var out = [];
    (Array.isArray(list) ? list : []).forEach(function (p) {
      if (!p || num(p.start) === null) { warnOnce("start", "a piece without a start was dropped"); return; }
      var end = num(p.end), bucket = p.bucket;
      if (end === null || end < p.start) { warnOnce("end", "a piece without an end is shown as unknown"); end = p.start; bucket = "unknown"; }
      else if (STATES.indexOf(bucket) < 0) { warnOnce("bucket", "a piece with an unknown bucket is shown as unknown"); bucket = "unknown"; }
      out.push({ start: p.start, end: end, bucket: bucket, task: p.task == null ? null : String(p.task), approx: p.approx === true,
                 on: p.on == null ? null : String(p.on), collapsible: p.collapsible === true,
                 worktree: p.worktree ? String(p.worktree) : "", branch: p.branch ? String(p.branch) : "" });
    });
    out.sort(function (a, b) { return a.start - b.start; });
    return out;
  }

  /* layoutLanes(pieces, range, width, breaks): rects of one lane in px. `breaks` is a list of breaks or a scale made by
     makeScale (build it once for all lanes). Pieces inside a break are not drawn; a piece across a break is split.
     A run of rects narrower than 1 px is merged for drawing only: the rect keeps `seconds` (the sum) and `n` (how many). */
  function layoutLanes(pieces, range, width, breaks) {
    var sc = breaks && breaks.segs ? breaks : makeScale(range, breaks || []);
    var rects = [];
    for (var i = 0; i < pieces.length; i++) {
      var p = pieces[i];
      if (p.end < range.from || p.start > range.to) continue;
      for (var k = 0; k < sc.segs.length; k++) {
        var s = sc.segs[k], lo = Math.max(p.start, s.a), hi = Math.min(p.end, s.b);
        if (hi < lo || (hi === lo && p.end > p.start)) continue;
        var fx = s.x0 + (lo - s.a) / (s.b - s.a) * s.w, fw = (hi - lo) / (s.b - s.a) * s.w;
        rects.push({ fx: fx, fw: fw, x: fx * width, w: fw * width, start: lo, end: hi, seconds: hi - lo, n: 1, bucket: p.bucket,
                     task: p.task, approx: p.approx, on: p.on, mixed: false, piece: p });
      }
    }
    var co = [];   /* whole blocks: touching rects of one state and task are one block for drawing */
    rects.forEach(function (r) {
      var l = co[co.length - 1];
      if (l && l.bucket === r.bucket && l.task === r.task && l.on === r.on && l.approx === r.approx && r.x - (l.x + l.w) < 0.5 && r.start >= l.end) {
        l.w = r.x + r.w - l.x; l.fw = l.w / width; l.end = r.end; l.seconds += r.seconds; l.n += 1;
      } else co.push(r);
    });
    rects = co;
    var out = [], g = null, acc = null;
    function flush() {
      if (!g) return;
      if (g.n > 1) {
        var best = null;
        Object.keys(acc).forEach(function (b) { if (!best || acc[b].sec > acc[best].sec) best = b; });
        var w = acc[best];
        g.bucket = best; g.task = w.task; g.approx = w.approx; g.on = w.on; g.mixed = Object.keys(acc).length > 1;
      }
      out.push(g); g = null; acc = null;
    }
    rects.forEach(function (r) {
      if (r.w >= 1) { flush(); out.push(r); return; }
      if (g && g.w < 1) {   /* the run is not yet 1 px wide: take this one too */
        g.w = r.x + r.w - g.x; g.fw = g.w / width; g.end = r.end; g.seconds += r.seconds; g.n += 1;
      } else {
        flush();
        g = r; acc = {};
      }
      var a = acc[r.bucket] || (acc[r.bucket] = { sec: 0, task: r.task, approx: r.approx, on: r.on });
      a.sec += r.seconds;
    });
    flush();
    return out;
  }

  /* axisModel(scale, tz, width): date row and local-zone ticks of the visible stretches */
  function axisModel(scale, tz, width) {
    var days = [], ticks = [], grid = [], STEPS = [1, 2, 5, 10, 15, 30, 60, 120, 180, 360, 720, 1440];
    scale.segs.forEach(function (sg) {
      var len = sg.b - sg.a, pxw = sg.w * width;
      if (!(len > 0) || !(pxw > 0)) return;
      var want = 62 / (pxw / (len / 60)), step = 1440, i;
      for (i = 0; i < STEPS.length; i++) if (STEPS[i] >= want) { step = STEPS[i]; break; }
      var t = nextAligned(sg.a, step, tz);
      for (var n = 0; t <= sg.b && n < 400; n++) {
        var x = sg.x0 + (t - sg.a) / len * sg.w, l = loc(t, tz);
        if (x > sg.x0 + 0.002 && x < sg.x0 + sg.w - 0.004 && !(l.h === 0 && l.mi === 0)) {
          ticks.push({ x: x, t: t, label: pad2(l.h) + ":" + pad2(l.mi) });
          grid.push({ x: x, mid: false });
        }
        t = nextAligned(t + 1, step, tz);
      }
      var a = sg.a;
      while (a < sg.b) {
        var nm = Math.min(nextMidnight(a, tz), sg.b), x0 = sg.x0 + (a - sg.a) / len * sg.w, w = (nm - a) / len * sg.w, wp = w * width;
        days.push({ x: x0, w: w, t: a, full: dayLabel(a, tz), label: wp > 96 ? dayLabel(a, tz) : wp > 46 ? dayLabel(a, tz, true) : "" });
        if (nm < sg.b) grid.push({ x: sg.x0 + (nm - sg.a) / len * sg.w, mid: true });
        a = nm;
      }
    });
    return { days: days, ticks: ticks, grid: grid };
  }

  /* taskStats(agents, scale): time per task inside the drawn range. working / waiting+blocked, in seconds, never a percent */
  function taskStats(agents, scale) {
    var by = {}, total = 0, un = 0;
    agents.forEach(function (a) {
      a.pieces.forEach(function (p) {
        if (p.bucket === "idle" || p.bucket === "unknown") return;
        var d = scale.visible(p.start, p.end);
        if (!d) return;
        var k = p.task == null ? "" : p.task, o = by[k] || (by[k] = { work: 0, other: 0, agents: {} });
        if (p.bucket === "working") { o.work += d; total += d; if (p.task == null) un += d; } else o.other += d;
        o.agents[a.agent] = true;
      });
    });
    return { by: by, working: total, unattributed: un };
  }

  T.loc = loc; T.hhmm = hhmm; T.stamp = stamp; T.dayLabel = dayLabel; T.offLabel = offLabel; T.startOfDay = startOfDay;
  T.nextMidnight = nextMidnight; T.clampGap = clampGap; T.durLabel = durLabel; T.hm = hm; T.breakLabel = breakLabel;
  T.gapKind = gapKind; T.collapse = collapse; T.taskFilter = taskFilter; T.presetRange = presetRange; T.zoomRange = zoomRange;
  T.panRange = panRange; T.dragRange = dragRange; T.makeScale = makeScale; T.normalizePieces = normalizePieces;
  T.layoutLanes = layoutLanes; T.axisModel = axisModel; T.taskStats = taskStats; T.PRESETS = PRESETS;

  /* ================= the panel ================= */
  var V = { range: null, preset: "all", gap: GAP_DEF, real: false, hl: null, sel: null, data: null, agents: [], state: "loading",
            key: 0, req: 0, poll: null, qkey: null, body: null, tz: null, W: 900, hash: "", wheelAt: 0, wheelTimer: null,
            loadingRange: false, err: false, ctxNow: null };
  T.state = V;

  function nowSec() {
    var c = BOARD.ctx;
    return Math.floor((c && c.now ? c.now() : Date.now()) / 1000);
  }
  function zone() { return V.tz || (BOARD.readZone ? BOARD.readZone() : "UTC"); }
  function qstring() {
    var s = BOARD.ctx && BOARD.ctx.state;
    if (!s) return "";
    var q = [];
    if (s.squad) q.push("squad=" + encodeURIComponent(s.squad.key));
    if (s.choice) q.push(s.choice.kind + "=" + encodeURIComponent(s.choice.name));
    return q.join("&");
  }
  function rangeNow() {   /* the range to ask for: a preset moves with the clock, a zoomed range stays */
    if (V.preset) return presetRange(V.preset, nowSec(), zone());
    return { from: V.range.from, to: V.range.to };
  }
  function params(r) {
    var p = [];
    if (r.from != null) p.push("from=" + Math.floor(r.from));
    p.push("to=" + Math.floor(r.to));
    p.push("gap_min=" + V.gap);
    return p.join("&");
  }
  function resetFor(q) {
    if (V.qkey === q) return;
    V.qkey = q; V.data = null; V.agents = []; V.sel = null; V.hl = null; V.hash = ""; V.state = "loading"; V.key++; V.req++;
    if (V.body) { V.body.textContent = ""; V.body.appendChild(skeleton()); }
  }

  var def = {
    id: "worktime", title: "Work time", span: 12, spans: [8, 12], maxPx: 780,
    isEmpty: function (d) { return !d || !Array.isArray(d.agents) || !d.agents.length; },
    render: function (body, data, ctx) {
      V.body = body; V.tz = ctx.tz;
      var p = V.poll;
      var ok = p && p.key === V.key && data && p.reqs.some(function (q) { return (q.from == null || data.from === q.from) && data.to === q.to; });
      if (ok) accept(data, true);
      else if (V.state === "ok" && V.agents.length) draw();   /* the board cleared the body for this answer: never leave it blank */
    }
  };
  /* the board's poller asks for this route every 5 s (one timer for the page); it reads the current range each time */
  Object.defineProperty(def, "route", { enumerable: true, get: function () {
    resetFor(qstring());
    var r = rangeNow();
    if (!V.poll || V.poll.key !== V.key) V.poll = { key: V.key, reqs: [] };
    V.poll.reqs = V.poll.reqs.concat([{ from: r.from, to: r.to }]).slice(-6);   /* the board reads the route a few times per tick */
    return "/api/worktime?" + params(r);
  } });

  function accept(data, fromPoll) {
    var n = normalizeData(data);
    var h = JSON.stringify(n);
    V.state = "ok"; V.err = false; V.loadingRange = false;
    if (fromPoll && h === V.hash && V.body && V.body.firstChild) return;   /* unchanged and still drawn: no redraw */
    V.hash = h; V.data = n; V.agents = n.agents;
    draw();
  }
  function normalizeData(d) {
    var agents = (Array.isArray(d.agents) ? d.agents : []).map(function (a) {
      return { agent: String(a.agent == null ? "?" : a.agent), role: String(a.role || "agent"), scope: String(a.scope || ""),
               note: a.note ? String(a.note) : "", pieces: normalizePieces(a.pieces) };
    });
    var marks = (Array.isArray(d.marks) ? d.marks : []).filter(function (m) { return m && num(m.ts) !== null; }).map(function (m) {
      return { ts: m.ts, kind: String(m.kind || ""), agent: m.agent == null ? null : String(m.agent), task: m.task == null ? null : String(m.task),
               sha: m.sha ? String(m.sha) : "" };
    });
    var t = d.totals || {}, u = t.unattributed || {};
    return { from: num(d.from), to: num(d.to), gap_min: d.gap_min, agents: agents, marks: marks,
             unattributed: { hours: num(u.hours) || 0, minutes: num(u.minutes) || 0 },
             counted_working: num(t.counted_s && t.counted_s.working) || 0 };
  }

  /* a new range is one request, with the choice's scope= or goal= (the selection is always sent); an older answer that
     arrives after a newer request is dropped (request id) */
  function request(range, preset) {
    V.preset = preset || "";
    V.sel = null;
    V.range = range ? { from: range.from, to: range.to } : null;
    V.key++;
    var id = ++V.req, r = rangeNow();
    V.loadingRange = true;
    draw();
    save();
    if (!BOARD.ctx || !BOARD.ctx.getJson) return null;
    return BOARD.ctx.getJson("/api/worktime?" + params(r) + (qstring() ? "&" + qstring() : "")).then(function (resp) {
      if (id !== V.req) return;
      if (!resp || resp.schema_version !== 1) { V.state = "version"; V.loadingRange = false; draw(); return; }
      if (!resp.data) { V.state = "unknown"; V.unknown = resp.unknown || []; V.loadingRange = false; draw(); return; }
      accept(resp.data, false);
    }, function () {
      if (id !== V.req) return;
      V.err = true; V.loadingRange = false; draw();
    });
  }
  function effective() {   /* the range drawn; the preset "All" starts where the data starts */
    var r = V.preset || !V.range ? rangeNow() : { from: V.range.from, to: V.range.to };
    if (r.from == null) r.from = V.data && V.data.from != null ? V.data.from : r.to - DAY;
    if (!(r.to > r.from)) r.to = r.from + MIN_SPAN;
    return r;
  }

  T.preset = function (name) { var r = presetRange(name, nowSec(), zone()); return r ? request(r, name) : null; };
  T.zoomTo = function (range) { return request(range, ""); };
  T.zoomAt = function (frac, factor) {
    var r = effective(), sc = scaleNow(r);
    return request(zoomRange(r, sc.tAt(Math.max(0, Math.min(1, frac))), factor), "");
  };
  T.pan = function (fraction) { return request(panRange(effective(), fraction), ""); };
  T.dragZoom = function (x0, x1, width) {
    var r = effective(), d = dragRange(x0, x1, r, width, scaleNow(r));
    return d ? request(d, "") : null;
  };
  T.setGap = function (n) { V.gap = clampGap(n); return request(V.preset ? presetRange(V.preset, nowSec(), zone()) : V.range, V.preset); };
  T.setReal = function (on) { V.real = !!on; save(); draw(); };
  T.setTask = function (t) { V.hl = t === undefined ? null : t; draw(); };
  /* Ctrl+wheel (a pinch arrives as a wheel event with ctrlKey) zooms; the plain wheel is never touched, so the page scrolls.
     The range follows each event; the request is sent once the wheel rests. */
  T.onWheel = function (e, frac) {
    if (!e.ctrlKey) return false;
    e.preventDefault();
    var r = effective(), sc = scaleNow(r);
    V.sel = null; V.preset = ""; V.range = zoomRange(r, sc.tAt(Math.max(0, Math.min(1, frac))), e.deltaY > 0 ? 1.25 : 0.8);
    draw();
    root.clearTimeout(V.wheelTimer);
    V.wheelTimer = root.setTimeout(function () { request(V.range, ""); }, WHEEL_WAIT_MS);
    return true;
  };

  function save() { if (BOARD.ctx && BOARD.ctx.touch) BOARD.ctx.touch(); }
  /* saved with the page state (board-ui.json through the existing PUT /api/ui): the idle break and the zoom */
  BOARD.hooks = BOARD.hooks || {};
  BOARD.hooks.snapshot = function (snap) {
    snap.timeline = { gap_min: V.gap, real: V.real, preset: V.preset };
    if (!V.preset && V.range) { snap.timeline.from = V.range.from; snap.timeline.to = V.range.to; }
  };
  BOARD.hooks.applySaved = function (ui) {
    var t = ui && ui.timeline;
    if (!t || typeof t !== "object") return;
    V.gap = clampGap(t.gap_min);
    V.real = t.real === true;
    if (PRESETS.some(function (p) { return p[0] === t.preset; })) { V.preset = t.preset; V.range = null; }
    else if (num(t.from) !== null && num(t.to) !== null && t.to > t.from) { V.preset = ""; V.range = { from: t.from, to: t.to }; }
  };

  /* ---------- drawing ---------- */
  function el(tag, cls, text) {
    var e = root.document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function pct(f) { return (f * 100).toFixed(3) + "%"; }
  function skeleton() {
    var w = el("div");
    [["70%"], [null], ["85%"]].forEach(function (x) { var s = el("div", "sk"); if (x[0]) s.style.width = x[0]; w.appendChild(s); });
    return w;
  }
  var CSS = [
    ".tl{position:relative}",
    ".tl-bar{position:sticky;top:var(--bt,0px);z-index:30;background:var(--panel2);border:1px solid var(--border);border-radius:8px;padding:.75em;margin-bottom:6px}",
    ".tl-r{position:relative;display:flex;gap:.67em;align-items:center;flex-wrap:wrap;margin-top:.6em;padding-left:3.4em}.tl-r:first-child{margin-top:0}",
    ".tfl{position:absolute;left:0;top:0;height:2.2em;display:flex;align-items:center;font-weight:700;font-size:.85em;font-variant:small-caps;text-transform:lowercase;letter-spacing:.04em;color:var(--muted)}",
    ".tc,.tl .cp{display:inline-flex;align-items:center;height:2.2em;box-sizing:border-box;line-height:1;border:1px solid var(--border);background:var(--bg);color:var(--ink);border-radius:999px;padding:0 .85em;white-space:nowrap}",
    ".tc:hover,.tl .cp:hover,.tl .seg button:hover{border-color:var(--ink)}.tc.on{background:var(--t-need);color:var(--ink);border-color:var(--mango);font-weight:700}",
    ".tl .seg{display:inline-flex;gap:0;border:0;border-radius:0;overflow:visible;background:none}.tl .seg button{border:1px solid var(--border);background:var(--bg);color:var(--ink);padding:0 .7em;min-width:2.6em;height:2.2em;box-sizing:border-box}",
    ".tl .seg button:first-child{border-radius:999px 0 0 999px}.tl .seg button:last-child{border-radius:0 999px 999px 0;border-left:0}",
    ".tl-gap{margin-left:auto;display:inline-flex;gap:.67em;align-items:center;flex-wrap:wrap;color:var(--muted)}",
    ".tl-gap select{font:inherit;border:1px solid var(--border);border-radius:6px;background:var(--bg);color:var(--ink);padding:0 3px}",
    ".tl-r.tl-rng{padding-left:0;padding-top:.6em;border-top:1px dashed var(--border);color:var(--ink)}.tl-rng .muted{font-weight:400}.tl-rng .err{color:var(--err);font-weight:400}.tfs{margin-left:auto}",
    ".ap{font-size:.83em;font-style:italic;color:var(--muted);margin-left:3px}",
    ".tl-leg{display:flex;flex-wrap:wrap;gap:2px 11px;color:var(--muted);margin:2px 0 6px;align-items:center}.tl-leg span{display:inline-flex;gap:4px;align-items:center;white-space:nowrap}",
    ".sw{display:inline-block;width:1em;height:.75em;border-radius:2px}",
    ".s-w{background:var(--work)}.s-a{background:var(--wait)}",
    ".s-b{background:repeating-linear-gradient(45deg,var(--block) 0 4px,color-mix(in srgb,var(--block) 50%,transparent) 4px 7px)}",
    ".s-p{background:repeating-linear-gradient(45deg,var(--po) 0 3px,color-mix(in srgb,var(--po) 60%,var(--bg)) 3px 5px)}",
    ".s-i{background:var(--muted2);opacity:.55}",
    ".brk-sw{background:repeating-linear-gradient(135deg,var(--t-idle) 0 3px,var(--bg) 3px 6px);border:1px solid var(--muted2)}",
    ".tl-chart{position:relative;outline:none}.tl-chart:focus-visible{outline:2px solid var(--mango);outline-offset:2px}",
    ".tl-axis,.tl-row{display:grid;grid-template-columns:var(--lw) 1fr;gap:6px}",
    ".tl-axis{position:sticky;top:calc(var(--barh,0px) + var(--bt,0px));z-index:25;background:var(--bg);border-bottom:1px solid var(--border)}",
    ".tl-axis .pl{position:relative;height:2.9em;user-select:none}",
    ".tl-axis .days{position:absolute;left:0;right:0;top:0;height:1.3em;border-bottom:1px solid var(--border)}",
    ".tl-axis .dy{position:absolute;top:0;bottom:0;border-left:1px solid var(--muted2);padding:0 .35em;font-weight:700;white-space:nowrap;overflow:hidden;display:flex;align-items:center;color:var(--ink)}",
    ".tl-axis .ticks{position:absolute;left:0;right:0;top:1.35em;height:1.4em;color:var(--muted)}",
    ".tl-axis .ticks span{position:absolute;transform:translateX(-50%);font-size:.875em;white-space:nowrap}",
    ".tl-axis .hit{position:absolute;left:0;right:0;top:0;bottom:0;cursor:col-resize;background:transparent}",
    ".tl-axis .hit:hover{background:var(--t-need3)}",
    ".tl-row{align-items:stretch;border-bottom:1px solid var(--border);height:2.9em}",
    ".tl-row .lab{display:flex;flex-direction:column;justify-content:center;min-width:0;padding:2px 0}",
    ".tl-row .lab .ln{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:600}.tl-row .lab small{color:var(--muted);font-weight:400;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}",
    ".tl-row.grp{border-bottom:0;margin-top:5px;height:auto}.tl-row.grp .lab{font-size:.875em;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:700;flex-direction:row;align-items:center;gap:6px}",
    ".tl .chip{display:inline-flex;align-items:center;height:1.6em;line-height:1;padding:0 .65em;border-radius:.8em;font-size:.92em;font-weight:600;border:1px solid var(--border);background:var(--bg)}",
    ".tl-trk{position:relative;cursor:grab;min-width:0}",
    ".tl-trk.nodata{background:repeating-linear-gradient(135deg,var(--bg) 0 5px,var(--panel) 5px 10px);border:1px dashed var(--muted);border-radius:4px;color:var(--muted);display:flex;align-items:center;padding-left:8px;cursor:default}",
    ".blk{position:absolute;top:1.15em;bottom:.2em;display:flex;align-items:center;border:0;padding:0;border-radius:3px;overflow:hidden;min-width:2px}",
    ".blk .lb{display:inline-flex;align-items:center;height:1.35em;margin:0 0 0 .3em;padding:0 .3em;border-radius:3px;background:var(--bg);color:var(--ink);font-weight:700;font-size:.875em;line-height:1;white-space:nowrap;flex:none}",
    ".blk .lb u{text-decoration:none;border-bottom:1px dotted var(--ink)}",
    ".blk.st-w{background:var(--work)}.blk.st-a{background:var(--wait)}",
    ".blk.st-b{background:repeating-linear-gradient(45deg,var(--block) 0 4px,color-mix(in srgb,var(--block) 50%,transparent) 4px 7px)}",
    ".blk.st-p{background:repeating-linear-gradient(45deg,var(--po) 0 3px,color-mix(in srgb,var(--po) 60%,var(--bg)) 3px 5px)}",
    ".blk.st-i{background:var(--muted2);opacity:.5}.blk.st-u{background:var(--panel2);outline:1px dashed var(--muted);outline-offset:-1px}",
    ".blk.un{outline:1px dashed var(--ink);outline-offset:-2px}",
    ".blk.sel{box-shadow:0 0 0 2px var(--ink);z-index:3}.blk.dim{opacity:.16}",
    ".blk:focus-visible{outline:2px solid var(--mango);outline-offset:1px;z-index:4}",
    ".mk{position:absolute;top:.55em;width:.75em;height:.75em;margin:-.375em 0 0 -.375em;z-index:4;border:1.5px solid var(--ink);background:var(--bg);border-radius:50%;padding:0}",
    ".mk.pass,.mk.fail{border-radius:1px;transform:rotate(45deg);width:.7em;height:.7em;margin:-.35em 0 0 -.35em}",
    ".mk.pass{background:var(--work);border-color:var(--bg)}.mk.fail{background:var(--fail);border-color:var(--bg)}",
    ".mk.handin{border-radius:1px;background:var(--wait);border-color:var(--bg)}",
    ".mk.blocked{border-radius:0;background:var(--block);border-color:var(--bg);transform:rotate(45deg) scale(.8)}",
    ".mk.merge{background:var(--mango);border-color:var(--bg)}",
    ".tl-ov{position:absolute;left:calc(var(--lw) + 6px);right:0;bottom:0;pointer-events:none;z-index:6}",
    ".tl-ov .grid i{position:absolute;top:0;bottom:0;border-left:1px solid var(--border);opacity:.7}.tl-ov .grid i.mid{border-left:1px solid var(--muted2);opacity:1}",
    ".brk{position:absolute;top:0;bottom:0;background:repeating-linear-gradient(135deg,var(--t-idle) 0 4px,var(--bg) 4px 8px);border-left:1px solid var(--muted2);border-right:1px solid var(--muted2);display:flex;align-items:center;justify-content:center;pointer-events:auto;overflow:hidden;z-index:2}",
    ".brk span{writing-mode:vertical-rl;transform:rotate(180deg);white-space:nowrap;font-size:.875em;font-weight:700;color:var(--ink);background:var(--bg);border-radius:3px;padding:.3em .1em;max-height:96%;overflow:hidden;text-overflow:ellipsis}",
    ".tl .now{position:absolute;top:0;bottom:0;width:0;border-left:2px solid var(--ink);z-index:6}",
    ".tl .now span{position:absolute;top:-1.55em;transform:translateX(-50%);font-size:.83em;font-weight:700;background:var(--ink);color:var(--bg);border-radius:3px;padding:0 4px;white-space:nowrap}",
    ".selr{position:absolute;top:-2.9em;bottom:0;background:var(--t-need);border:1px solid var(--mango);z-index:7}",
    ".tl-hint{margin:6px 0}",
    ".tl-detail{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:6px 10px;margin:6px 0}",
    ".tl-detail dl{display:grid;grid-template-columns:8.7em 1fr;gap:2px 8px;margin:4px 0 0}.tl-detail dt{color:var(--muted)}.tl-detail dd{margin:0;overflow-wrap:anywhere}",
    ".tl-h{font-size:.875em;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin:10px 0 3px;font-weight:400}",
    ".tl-tbl{width:100%;border-collapse:collapse}.tl-tbl th{text-align:left;font-size:.875em;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);font-weight:600;padding:2px 8px 3px 0;border-bottom:1px solid var(--border);white-space:nowrap}",
    ".tl-tbl td{padding:4px 8px 4px 0;border-bottom:1px solid var(--border);vertical-align:top}.tl-tbl tr.r{cursor:pointer}.tl-tbl tr.r:hover td{background:var(--t-need3)}.tl-tbl tr.on td{background:var(--t-need2)}",
    ".tl .note{margin:6px 0;color:var(--muted)}",
    ".tl .box{border:1px dashed var(--border);border-radius:8px;padding:8px 12px;text-align:center}.tl .box.warn{text-align:left;color:var(--ink)}",
    ".tl .cannot{margin:8px 0 0;color:var(--muted)}",
    ".tl-wait{color:var(--muted);margin-left:auto}",
    ".sk{height:.92em;border-radius:4px;background:linear-gradient(90deg,var(--border),var(--bg),var(--border));background-size:200% 100%;animation:sk 1.2s linear infinite;margin:7px 0}@keyframes sk{to{background-position:-200% 0}}"
  ].join("\n");
  var cssDone = false;
  function ensureCss() {
    if (cssDone || !root.document || !root.document.head) return;
    cssDone = true;
    var s = root.document.createElement("style");
    s.id = "timeline-css";
    s.textContent = CSS;   /* a static literal: no data in it */
    root.document.head.appendChild(s);
  }

  /* the lane groups of the design: Manager, Developers, QA ... (roles in the roster are dev, qa-whitebox, qa-blackbox ...) */
  var TYPES = ["Manager", "BA", "Designer", "Architect", "Tech lead", "Team lead", "Developers", "QA"];
  function typeOf(role) {
    var r = String(role || "").toLowerCase();
    if (r.indexOf("qa") === 0) return "QA";
    if (r.indexOf("dev") === 0) return "Developers";
    var m = { manager: "Manager", ba: "BA", designer: "Designer", architect: "Architect", "tech-lead": "Tech lead", "team-lead": "Team lead" }[r];
    return m || (r ? r.charAt(0).toUpperCase() + r.slice(1) : "Agent");
  }
  T.typeOf = typeOf;

  var cur = null;   /* what the last draw used: {range, scale, lanes} */
  function scaleNow(r) {
    var all = [];
    V.agents.forEach(function (a) { all = all.concat(a.pieces); });
    var c = collapse(all, V.gap, V.real, zone());
    return makeScale(r, c.breaks);
  }

  function legend() {
    var d = el("div", "tl-leg");
    function sw(cls, text) { var s = el("span"); s.appendChild(el("i", "sw " + cls)); s.appendChild(root.document.createTextNode(text)); d.appendChild(s); }
    sw("s-w", "working"); sw("s-a", "waiting"); sw("s-b", "blocked on a peer"); sw("s-p", "blocked on you"); sw("s-i", "idle");
    ["handin", "fail", "pass", "blocked", "commit", "merge"].forEach(function (k) {
      var s = el("span"), i = el("i", "mk " + k); i.style.position = "static"; i.style.display = "inline-block"; i.style.margin = "0 2px 0 4px";
      s.appendChild(i); s.appendChild(root.document.createTextNode(MARK_NAMES[k])); d.appendChild(s);
    });
    sw("brk-sw", "collapsed gap");
    var n = el("span", "muted"); n.appendChild(root.document.createTextNode("block edges ")); n.appendChild(el("b", null, "real"));
    n.appendChild(root.document.createTextNode(" · task label ")); n.appendChild(el("b", null, "approx"));
    n.appendChild(root.document.createTextNode(" · dashed block = no task")); d.appendChild(n);
    return d;
  }

  function tasksIn(agents) {
    var o = {};
    agents.forEach(function (a) { a.pieces.forEach(function (p) { if (p.task != null) o[p.task] = true; }); });
    if (V.hl) o[V.hl] = true;
    return Object.keys(o).sort();
  }

  function toolbar(r, sc, tz) {
    var bar = el("div", "tl-bar"), r1 = el("div", "tl-r");
    function chip(text, on, fn, title) {
      var b = el("button", "tc" + (on ? " on" : ""), text); b.type = "button";
      if (title) b.title = title;
      b.addEventListener("click", fn); return b;
    }
    r1.appendChild(el("span", "tfl", "Task"));
    r1.appendChild(chip("All tasks", !V.hl, function () { T.setTask(null); }));
    tasksIn(V.agents).forEach(function (t) { r1.appendChild(chip(t, V.hl === t, function () { T.setTask(V.hl === t ? null : t); }, "task " + t)); });
    r1.appendChild(chip("unattributed", V.hl === "—", function () { T.setTask(V.hl === "—" ? null : "—"); }, "working time with no task"));
    var r2 = el("div", "tl-r");
    r2.appendChild(el("span", "tfl", "View"));
    PRESETS.forEach(function (p) { var b = chip(p[1], V.preset === p[0], function () { T.preset(p[0]); }); b.dataset.preset = p[0]; r2.appendChild(b); });
    var z = el("span", "seg");
    [["−", "Zoom out", function () { T.zoomAt(0.5, 2); }], ["+", "Zoom in", function () { T.zoomAt(0.5, 0.5); }]].forEach(function (x) {
      var b = el("button", null, x[0]); b.type = "button"; b.title = x[1]; b.setAttribute("aria-label", x[1]); b.addEventListener("click", x[2]); z.appendChild(b);
    });
    var pn = el("span", "seg");
    [["◀", "Earlier", -0.3], ["▶", "Later", 0.3]].forEach(function (x) {
      var b = el("button", null, x[0]); b.type = "button"; b.title = x[1]; b.setAttribute("aria-label", x[1]); b.addEventListener("click", function () { T.pan(x[2]); }); pn.appendChild(b);
    });
    r2.appendChild(z); r2.appendChild(pn);
    var g = el("span", "tl-gap"), lab = el("label", null, "Collapse gaps longer than ");
    var sel = el("select"); sel.setAttribute("aria-label", "Collapse idle gaps longer than");
    GAPS.forEach(function (n) { var o = el("option", null, n < 60 ? n + " min" : n / 60 + " h"); o.value = String(n); if (n === V.gap) o.selected = true; sel.appendChild(o); });
    sel.addEventListener("change", function () { T.setGap(+sel.value); });
    lab.appendChild(sel); g.appendChild(lab);
    var real = chip("Show real time", V.real, function () { T.setReal(!V.real); }); real.setAttribute("aria-pressed", V.real ? "true" : "false"); real.dataset.real = "1";
    g.appendChild(real);
    var r3 = el("div", "tl-r tl-rng"), same = loc(r.from, tz).d === loc(r.to, tz).d && r.to - r.from < DAY;
    r3.appendChild(el("b", null, dayLabel(r.from, tz) + " " + hhmm(r.from, tz) + " → " + (same ? "" : dayLabel(r.to, tz) + " ") + hhmm(r.to, tz)));
    var nb = sc.breaks.length;
    r3.appendChild(el("span", "muted", "· " + durLabel(r.to - r.from) + (V.real ? " · real time" : nb ? " · " + nb + " gap" + (nb === 1 ? "" : "s") + " collapsed" : " · nothing to collapse")
      + (V.loadingRange ? " · loading" : "")));
    if (V.err) r3.appendChild(el("span", "err", "· could not load this range"));
    r3.appendChild(g);
    if (V.hl) {
      var f = el("span", "tfs"); f.appendChild(root.document.createTextNode("Following "));
      f.appendChild(el("b", null, V.hl === "—" ? "unattributed time" : "task " + V.hl)); f.appendChild(root.document.createTextNode(" "));
      var c = el("button", "cp", "Clear"); c.type = "button"; c.addEventListener("click", function () { T.setTask(null); }); f.appendChild(c); r3.appendChild(f);
    }
    bar.appendChild(r1); bar.appendChild(r2); bar.appendChild(r3);
    return bar;
  }

  function blockTitle(a, r, tz) {
    var s = a.agent + (a.scope ? " · " + a.scope : "") + " · " + hhmm(r.start, tz) + "–" + hhmm(r.end, tz) + " (" + durLabel(r.seconds) + ") · " +
      (r.bucket === "blocked" ? (r.on === "PO" ? "blocked on you" : "blocked" + (r.on ? " on " + r.on : "")) : r.bucket) +
      " · " + (r.task != null ? "task " + r.task + (r.approx ? " (approx)" : "") : "no task");
    return r.mixed ? s + " · " + r.n + " short pieces" : s;
  }

  function laneRow(a, sc, rects, marks, tz, width, multi) {
    var row = el("div", "tl-row"), lab = el("div", "lab");
    lab.title = a.agent + (a.scope ? " · " + a.scope : "");
    var ln = el("span", "ln", a.agent);
    lab.appendChild(ln);
    if (a.scope) lab.appendChild(el("small", null, a.scope));
    row.dataset.agent = a.agent;
    row.appendChild(lab);
    var trk = el("div", "tl-trk");
    if (a.note) {
      trk.className = "tl-trk nodata"; trk.textContent = a.note;   /* "no transcript: <agent>" */
      row.appendChild(trk); return row;
    }
    var hl = V.hl, any = false;
    rects.forEach(function (r) {
      any = true;
      var dim = hl && (hl === "—" ? (r.task != null || r.bucket === "idle") : r.task !== hl);
      var st = r.bucket === "working" ? "w" : r.bucket === "waiting" ? "a" : r.bucket === "blocked" ? (r.on === "PO" ? "p" : "b") : r.bucket === "idle" ? "i" : "u";
      var b = el("button", "blk st-" + st + (r.task == null && r.bucket !== "idle" && r.bucket !== "unknown" && r.w >= 6 ? " un" : "") + (dim ? " dim" : "") +
        (V.sel && V.sel.agent === a.agent && V.sel.start === r.start ? " sel" : ""));
      b.type = "button";
      b.style.left = pct(r.fx); b.style.width = pct(r.fw);
      b.title = blockTitle(a, r, tz);
      b.dataset.state = r.bucket; b.dataset.agent = a.agent; b.dataset.start = String(r.start); b.dataset.end = String(r.end);
      if (r.task != null) b.dataset.task = r.task;
      if (r.approx) b.dataset.approx = "true";
      if (r.task != null && r.w >= 64) {
        var lb = el("span", "lb"), u = el("u", null, r.task);
        lb.appendChild(u); if (r.approx) lb.appendChild(el("span", "ax", "\u00a0approx")); b.appendChild(lb);
      }
      b.addEventListener("click", function (e) {
        if (V.moved) { V.moved = false; return; }
        e.stopPropagation();
        V.sel = { agent: a.agent, scope: a.scope, start: r.start, end: r.end, bucket: r.bucket, task: r.task, on: r.on, n: r.n,
                  worktree: r.piece ? r.piece.worktree : "", branch: r.piece ? r.piece.branch : "" };
        if (r.task != null) V.hl = r.task;
        draw();
      });
      trk.appendChild(b);
    });
    marks.forEach(function (m) {
      var t = m.ts;
      if (t < sc.range.from || t > sc.range.to || sc.breaks.some(function (b) { return t > b.start && t < b.end; })) return;
      if (hl && !(hl === "—" ? m.task == null : (m.task === hl || m.task == null))) return;
      var i = el("i", "mk " + m.kind);
      i.style.left = pct(sc.x(t));
      i.dataset.kind = m.kind;
      i.title = (MARK_NAMES[m.kind] || m.kind) + (m.task ? " of " + m.task : "") + (m.sha ? " " + m.sha : "") + " · " + hhmm(t, tz) + " (exact)";
      trk.appendChild(i);
    });
    if (!any && a.agent !== "commits") { var w = el("span", "muted", "no activity in this range"); w.style.cssText = "position:absolute;left:.5em;top:1.3em"; trk.appendChild(w); }
    row.appendChild(trk);
    return row;
  }

  function detail(tz) {
    var d = el("div", "tl-detail");
    if (!V.sel) { d.className = "tl-detail muted"; d.textContent = "Click a block to see its task, start and end."; return d; }
    var s = V.sel;
    var h = el("div"); h.appendChild(el("b", null, s.agent)); h.appendChild(root.document.createTextNode(" " + (s.scope ? s.scope + " · " : "") +
      durLabel(s.end - s.start) + " " + s.bucket)); d.appendChild(h);
    var dl = el("dl");
    function row(k, v, ap) { dl.appendChild(el("dt", null, k)); var dd = el("dd", null, v); if (ap) dd.appendChild(el("span", "ap", "approx")); dl.appendChild(dd); }
    row("Task", s.task != null ? s.task : "none: overhead", s.task != null);
    row("Start", stamp(s.start, tz) + " (" + offLabel(s.start, tz) + ")");
    row("End", stamp(s.end, tz) + " (" + offLabel(s.end, tz) + ")");
    if (s.bucket === "blocked" && s.on) row("Blocked on", s.on === "PO" ? "you" : s.on);
    row("Worktree", s.worktree || "none: not in the data yet");
    row("Branch", s.branch || "—");
    var ms = (V.data ? V.data.marks : []).filter(function (m) { return m.ts >= s.start && m.ts <= s.end && (m.agent === s.agent || m.agent == null); });
    row("Commits, verdicts", ms.length ? ms.map(function (m) { return (MARK_NAMES[m.kind] || m.kind) + (m.sha ? " " + m.sha : "") + (m.task ? " " + m.task : "") + " " + hhmm(m.ts, tz); }).join(" · ") : "none in this block");
    row("Artifacts", "not read (cut from the data)");
    row("Reports", "none yet (made when the scope closes)");
    d.appendChild(dl);
    return d;
  }

  function branchOf(task) {   /* ticket 15 leaves branch empty until M10: "none" */
    var b = "";
    V.agents.forEach(function (a) { a.pieces.forEach(function (p) { if (!b && p.task === task && p.branch) b = p.branch; }); });
    if (!b) { var n = el("span", "muted", "none"); return n; }
    var c = el("code", null, "\u2026/" + b.split("/").pop());
    return c;
  }

  function statsTable(sc) {
    var wrap = el("div"), st = taskStats(V.agents, sc);
    wrap.appendChild(el("h3", "tl-h", "Which time worked which task (this range)"));
    var tb = el("table", "tl-tbl"), hd = el("tr");
    ["Task", "Working", "Waiting or blocked", "Agents", "Branch"].forEach(function (x) { hd.appendChild(el("th", null, x)); });
    var th = el("thead"); th.appendChild(hd); tb.appendChild(th);
    var body = el("tbody");
    function tr(key, cells) {
      var r = el("tr", "r" + (V.hl === key ? " on" : "")); r.tabIndex = 0;
      cells.forEach(function (c) { var td = el("td"); if (typeof c === "string") td.textContent = c; else td.appendChild(c); r.appendChild(td); });
      r.addEventListener("click", function () { T.setTask(V.hl === key ? null : key); });
      body.appendChild(r);
    }
    function approx(t) { var c = el("span", "nw", t); c.appendChild(el("span", "ap", "approx")); return c; }
    Object.keys(st.by).filter(function (k) { return k !== ""; }).sort().forEach(function (k) {
      var o = st.by[k]; tr(k, [k, approx(hm(o.work)), approx(hm(o.other)), Object.keys(o.agents).join(", "), branchOf(k)]);
    });
    var u = st.by[""] || { work: 0, other: 0 };
    var un = el("span"), n = V.data ? V.data.unattributed : { hours: 0, minutes: 0 };
    un.appendChild(el("b", null, n.hours + " h " + n.minutes + " min"));
    un.appendChild(root.document.createTextNode(" of " + hm(V.data ? V.data.counted_working : st.working) + " working time has no task"));
    un.appendChild(el("span", "ap", "approx"));
    tr("—", ["unattributed (overhead, no task)", approx(hm(u.work)), approx(hm(u.other)), un, ""]);
    tb.appendChild(body); wrap.appendChild(tb);
    return wrap;
  }

  function draw() {
    var body = V.body;
    if (!body || !root.document) return;
    ensureCss();
    body.textContent = "";
    var tl = el("div", "tl");
    body.appendChild(tl);
    if (V.state === "loading") { tl.appendChild(skeleton()); return; }
    if (V.state === "version") { tl.appendChild(el("p", "note", "unknown: board version")); return; }
    if (V.state === "unknown") {
      var un = el("p", "note box warn"); un.appendChild(el("b", null, "unknown: " + ((V.unknown || []).join(", ") || "transcripts and git are not readable") + ". "));
      un.appendChild(root.document.createTextNode("Lanes show \"no data\". Nothing is invented and nothing reads 0."));
      tl.appendChild(un);
      var ur = effective(), us = makeScale(ur, []), utz = zone();
      tl.appendChild(toolbar(ur, us, utz)); tl.appendChild(legend());
      var uc = el("div", "tl-chart"); uc.style.setProperty("--lw", "11em");
      var uax = el("div", "tl-axis"), upl = el("div", "pl"), udays = el("div", "days"), uticks = el("div", "ticks"), uam = axisModel(us, utz, V.W);
      uax.appendChild(el("div"));
      uam.days.forEach(function (d) { var x = el("span", "dy", d.label); x.style.left = pct(d.x); x.style.width = pct(d.w); udays.appendChild(x); });
      uam.ticks.forEach(function (t) { var x = el("span", null, t.label); x.style.left = pct(t.x); uticks.appendChild(x); });
      upl.appendChild(udays); upl.appendChild(uticks); uax.appendChild(upl); uc.appendChild(uax);
      var ur2 = el("div", "tl-row"); ur2.style.height = "3em"; ur2.appendChild(el("div", "lab"));
      ur2.appendChild(el("div", "tl-trk nodata", "unknown: transcripts not readable. No time is invented."));
      uc.appendChild(ur2); tl.appendChild(uc);
      return;
    }
    if (!V.agents.length) {
      var em = el("p", "note box"); em.appendChild(el("b", null, "No work time yet. ")); em.appendChild(root.document.createTextNode("No agent in this selection has a transcript."));
      tl.appendChild(em); return;
    }
    var tz = zone(), r = effective(), all = [];
    V.agents.forEach(function (a) { all = all.concat(a.pieces); });
    var col = collapse(all, V.gap, V.real, tz), sc = makeScale(r, col.breaks);
    var lw = "11em", multi = V.agents.some(function (a) { return a.scope !== V.agents[0].scope; });
    tl.appendChild(toolbar(r, sc, tz));
    tl.appendChild(legend());
    var chart = el("div", "tl-chart"); chart.style.setProperty("--lw", lw); chart.tabIndex = 0;
    chart.setAttribute("aria-label", "Work time chart. Plus and minus zoom, arrow keys move.");
    var ax = axisModel(sc, tz, V.W);
    var axis = el("div", "tl-axis"), pl = el("div", "pl"), days = el("div", "days"), ticks = el("div", "ticks");
    axis.appendChild(el("div"));
    ax.days.forEach(function (d) { var s = el("span", "dy", d.label); s.style.left = pct(d.x); s.style.width = pct(d.w); s.title = d.full; days.appendChild(s); });
    ax.ticks.forEach(function (t) { var s = el("span", null, t.label); s.style.left = pct(t.x); ticks.appendChild(s); });
    var hit = el("i", "hit"); hit.title = "Drag to zoom into a range";
    pl.appendChild(days); pl.appendChild(ticks); pl.appendChild(hit); axis.appendChild(pl); chart.appendChild(axis);
    var haveLane = {};
    V.agents.forEach(function (a) { haveLane[a.agent] = true; });
    var loose = (V.data ? V.data.marks : []).filter(function (m) { return !m.agent || !haveLane[m.agent]; });
    function lab(text, n) {
      var g = el("div", "tl-row grp"), l = el("div", "lab", text + " ");
      if (n != null) l.appendChild(el("span", "chip", String(n)));
      g.appendChild(l); g.appendChild(el("div")); return g;
    }
    if (loose.length) {   /* commits carry no agent: they sit in their own lane */
      chart.appendChild(lab("Commits and other marks"));
      chart.appendChild(laneRow({ agent: "commits", scope: "", note: "", pieces: [] }, sc, [], loose, tz, V.W, false));
    }
    var roles = [];
    V.agents.forEach(function (a) { var t = typeOf(a.role); if (roles.indexOf(t) < 0) roles.push(t); });
    roles.sort(function (x, y) {
      var i = TYPES.indexOf(x), j = TYPES.indexOf(y);
      return (i < 0 ? 99 : i) - (j < 0 ? 99 : j);
    });
    var hidden = 0;
    roles.forEach(function (role) {
      var g = V.agents.filter(function (a) { return typeOf(a.role) === role; });
      if (V.hl) g = g.filter(function (a) { var keep = !a.note && taskFilter(a.pieces, V.hl === "—" ? [null] : [V.hl]).length > 0; if (!keep && !a.note) hidden++; return keep || a.note; });
      if (!g.length) return;
      chart.appendChild(lab(role, g.length));
      g.forEach(function (a) {
        var mine = (V.data ? V.data.marks : []).filter(function (m) { return m.agent === a.agent; });
        chart.appendChild(laneRow(a, sc, a.note ? [] : layoutLanes(a.pieces, r, V.W, sc), mine, tz, V.W, multi));
      });
    });
    var ov = el("div", "tl-ov"), grid = el("div", "grid");
    ax.grid.forEach(function (g) { var i = el("i", g.mid ? "mid" : ""); i.style.left = pct(g.x); grid.appendChild(i); });
    ov.appendChild(grid);
    sc.breaks.forEach(function (b) {
      var d = el("div", "brk"); d.style.left = pct(b.x0); d.style.width = pct(b.w);
      d.title = "No agent did anything from " + stamp(b.start, tz) + " to " + stamp(b.end, tz) + " (" + durLabel(b.seconds) + "). Collapsed. Turn on \"Show real time\" to see it.";
      d.dataset.kind = b.kind;
      d.appendChild(el("span", null, b.label)); ov.appendChild(d);
    });
    var now = nowSec();
    if (now >= r.from && now <= r.to && !sc.breaks.some(function (b) { return now > b.start && now < b.end; })) {
      var nw = el("div", "now"), nx = sc.x(now), ns = el("span", null, "now " + hhmm(now, tz));
      nw.style.left = pct(nx);
      if (nx > 0.92) { ns.style.transform = "none"; ns.style.right = "0"; }   /* keep the label inside the chart */
      nw.appendChild(ns); ov.appendChild(nw);
    }
    var selr = el("div", "selr"); selr.hidden = true; ov.appendChild(selr);
    chart.appendChild(ov);
    tl.appendChild(chart);
    if (hidden) {
      var hn = el("p", "note", hidden + " lane" + (hidden === 1 ? "" : "s") + " hidden: no time on this task. ");
      var sb = el("button", "cp", "Show all lanes"); sb.type = "button"; sb.addEventListener("click", function () { T.setTask(null); }); hn.appendChild(sb); tl.appendChild(hn);
    }
    var anyIn = V.agents.some(function (a) { return a.pieces.some(function (p) { return p.end > r.from && p.start < r.to; }); });
    var marksIn = (V.data ? V.data.marks : []).some(function (m) { return m.ts >= r.from && m.ts <= r.to; });
    if (!anyIn && !marksIn) {
      var ne = el("p", "note box"); ne.appendChild(el("b", null, "No agent did anything in this range. "));
      ne.appendChild(root.document.createTextNode("Zoom out, or pick \"All\".")); tl.appendChild(ne);
    }
    var hint = el("p", "tl-hint muted", "Drag on the time axis to zoom into a range · Ctrl+wheel or pinch zooms · the plain wheel scrolls the page · drag the chart to move · + − and arrow keys when the chart has focus · click a block for detail.");
    tl.appendChild(hint);
    tl.appendChild(detail(tz));
    tl.appendChild(statsTable(sc));
    var cb = el("p", "cannot"); cb.appendChild(el("b", null, "Cannot be known: "));
    cb.appendChild(root.document.createTextNode("your own working time; work before an agent\u2019s first task message (it reads \"overhead\"); two tasks at once in one session; why an agent was idle."));
    tl.appendChild(cb);
    cur = { range: r, scale: sc, chart: chart, ov: ov, axis: axis, hit: hit, selr: selr, tl: tl };
    bind(cur);
    fit(cur);
  }

  /* measure the plot (px) once it is in the page; draw again when it changed, so ticks and labels fit */
  function fit(c) {
    var bar = c.tl.querySelector(".tl-bar");
    /* the scrolling panel body has top padding; sticky sticks below it, so pull the bar up by that much (no strip above it) */
    var sp = c.tl.parentNode, pt = 0;
    while (sp && sp.nodeType === 1) { var cs = getComputedStyle(sp); if (/(auto|scroll)/.test(cs.overflowY)) { pt = parseFloat(cs.paddingTop) || 0; break; } sp = sp.parentNode; }
    c.tl.style.setProperty("--bt", (-pt) + "px");
    c.tl.style.setProperty("--barh", (bar ? bar.offsetHeight : 0) + "px");
    c.ov.style.top = c.axis.offsetHeight + "px";
    var w = c.ov.clientWidth;
    if (w && Math.abs(w - V.W) > 3) { V.W = w; draw(); }
  }

  function bind(c) {
    var chart = c.chart;
    function frac(x) { var r = c.ov.getBoundingClientRect(); return r.width ? Math.max(0, Math.min(1, (x - r.left) / r.width)) : 0; }
    chart.addEventListener("wheel", function (e) { T.onWheel(e, frac(e.clientX)); }, { passive: false });
    chart.addEventListener("keydown", function (e) {
      var k = e.key;
      if (k === "+" || k === "=") { e.preventDefault(); T.zoomAt(0.5, 0.5); }
      else if (k === "-" || k === "_") { e.preventDefault(); T.zoomAt(0.5, 2); }
      else if (k === "ArrowLeft") { e.preventDefault(); T.pan(-0.25); }
      else if (k === "ArrowRight") { e.preventDefault(); T.pan(0.25); }
    });
    c.hit.addEventListener("pointerdown", function (e) {
      if (e.button !== 0) return;
      e.preventDefault();
      var r = c.ov.getBoundingClientRect(), x0 = e.clientX;
      var mv = function (ev) {
        var a = Math.min(x0, ev.clientX), b = Math.max(x0, ev.clientX);
        c.selr.hidden = false; c.selr.style.left = pct(frac(a)); c.selr.style.width = pct(frac(b) - frac(a));
      };
      var up = function (ev) {
        root.document.removeEventListener("pointermove", mv); root.document.removeEventListener("pointerup", up);
        c.selr.hidden = true;
        T.dragZoom(x0 - r.left, ev.clientX - r.left, r.width);
      };
      root.document.addEventListener("pointermove", mv); root.document.addEventListener("pointerup", up);
    });
    /* drag the lanes to move in time */
    c.chart.addEventListener("pointerdown", function (e) {
      if (e.button !== 0 || !e.target.closest || !e.target.closest(".tl-trk") || e.target.closest(".tl-trk.nodata")) return;
      var r = c.ov.getBoundingClientRect(), x0 = e.clientX, moved = false, start = c.range;
      var mv = function (ev) { if (Math.abs(ev.clientX - x0) > 5) moved = true; };
      var up = function (ev) {
        root.document.removeEventListener("pointermove", mv); root.document.removeEventListener("pointerup", up);
        if (!moved) return;
        V.moved = true;
        root.setTimeout(function () { V.moved = false; }, 0);
        var f = (ev.clientX - x0) / (r.width || 1);
        request(panRange(start, -f * (start.to - start.from) / Math.max(0.2, c.scale.avail)), "");
      };
      root.document.addEventListener("pointermove", mv); root.document.addEventListener("pointerup", up);
    });
    if (root.ResizeObserver && !V.ro) {
      V.ro = new root.ResizeObserver(function () {
        if (!cur) return;
        var w = cur.ov.clientWidth;
        if (w && Math.abs(w - V.W) > 3) { V.W = w; draw(); }
      });
      V.ro.observe(V.body);
    }
  }

  BOARD.registerPanel(def);
})(typeof window !== "undefined" ? window : this);
