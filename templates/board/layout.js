/* squad-board layout engine (tickets 35, 36; design-v8 s2 to s7): a smart grid.
   Pure part: colCount, place, refresh, recordGrid, migrate, dropIndex, widthToTracks, tracksToWidth, snapTracks.
   They touch no DOM, no window, no clock.
   DOM part: BOARD.layout.mount(): #canvas is a CSS grid; each panel gets grid-column / grid-row from place().
   It only edits the state ({id: {order, tracks, hidden, max_height}}); pixels are never stored. */
(function (root) {
  "use strict";
  var BOARD = root.BOARD = root.BOARD || {};
  var GUTTER = 12;   /* the same gap between panels, between columns and to the page edge */
  var MIN_PX = 76;   /* a panel is never shorter than this at Normal text */
  var ORDER = ["inbox", "tasks", "agents", "files", "scopes", "worktime"];   /* default place order (design-v7 s2) */

  function defaultRank(id, idx) { var k = ORDER.indexOf(id); return k < 0 ? ORDER.length + idx : k; }

  /* ---------------- pure part (design-v8 s2, s3) ---------------- */
  var SMALLEST = { tasks: 2, worktime: 2 };   /* smallest span; others 1 */
  function colCount(innerWidth, scale) {
    var w = innerWidth / (scale || 1);
    return w >= 1800 ? 6 : (w >= 960 ? 4 : 2);
  }
  /* place(items, G) -> {id: {x, y}}. items [{id, span, height}] in saved order (height = box height incl. gutter).
     Each item goes to the highest free spot where its span fits, leftmost when equal. Candidate rows: 0 and every bottom. */
  function place(items, G) {
    var boxes = [], out = {};
    items.forEach(function (it) {
      var span = Math.max(1, Math.min(it.span, G)), h = it.height || 0, rows = [0], best = null;
      boxes.forEach(function (b) { rows.push(b.y + b.h); });
      rows.sort(function (a, b) { return a - b; });
      rows.forEach(function (y) {
        if (best) return;
        for (var x = 0; x + span <= G; x++) {
          var clash = boxes.some(function (b) {
            return b.x < x + span && x < b.x + b.s && b.y < y + h && y < b.y + b.h;
          });
          if (!clash) { best = { x: x, y: y }; return; }
        }
      });
      boxes.push({ id: it.id, x: best.x, y: best.y, s: span, h: h });
      out[it.id] = { x: best.x, y: best.y };
    });
    return out;
  }
  /* refresh(prev, heights) -> {id: {x, y}}. prev: [{id, x, span, above:[ids]}] in row order of the last place.
     Each panel keeps x; y = lowest bottom of the panels recorded above it (0 when none). */
  function refresh(prev, heights) {
    var out = {};
    prev.forEach(function (p) {
      var y = 0;
      (p.above || []).forEach(function (a) { if (out[a]) y = Math.max(y, out[a].y + (heights[a] || 0)); });
      out[p.id] = { x: p.x, y: y };
    });
    return out;
  }
  /* recordGrid(items, pos, G) -> prev for refresh: row order, x, and the panels above (overlapping columns, ending at or above its top). */
  function recordGrid(items, pos, G) {
    var list = items.map(function (it) { return { id: it.id, x: pos[it.id].x, y: pos[it.id].y, span: Math.min(it.span, G), h: it.height }; });
    list.sort(function (a, b) { return (a.y - b.y) || (a.x - b.x); });
    return list.map(function (p) {
      return { id: p.id, x: p.x, span: p.span, above: list.filter(function (q) {
        return q !== p && q.x < p.x + p.span && p.x < q.x + q.span && q.y + q.h <= p.y;
      }).map(function (q) { return q.id; }) };
    });
  }
  /* migrate(panels) -> panels sorted by (order, col, default rank), order renumbered 0..k-1, col and span dropped. */
  function migrate(panels) {
    var rows = panels.map(function (p, i) { return { p: p, i: i }; });
    rows.sort(function (a, b) {
      var oa = Number.isInteger(a.p.order) ? a.p.order : 1e9, ob = Number.isInteger(b.p.order) ? b.p.order : 1e9;
      var ca = Number.isInteger(a.p.col) ? a.p.col : 0, cb = Number.isInteger(b.p.col) ? b.p.col : 0;
      return (oa - ob) || (ca - cb) || (defaultRank(a.p.id, a.i) - defaultRank(b.p.id, b.i));
    });
    return rows.map(function (r, k) {
      var q = {}; Object.keys(r.p).forEach(function (key) { if (key !== "col" && key !== "span") q[key] = r.p[key]; });
      q.order = k; return q;
    });
  }
  /* dropIndex(rects, x, y) -> index in reading order: the panel whose centre is nearest; before it when the pointer is above/left of it. */
  function dropIndex(rects, x, y) {
    var best = -1, bd = Infinity;
    rects.forEach(function (r, i) {
      var cx = r.left + r.width / 2, cy = r.top + r.height / 2, d = Math.hypot(x - cx, y - cy);
      if (d < bd) { bd = d; best = i; }
    });
    if (best < 0) return 0;
    var r = rects[best], cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    return (y < cy || (y <= cy && x < cx)) ? best : best + 1;
  }
  /* width in twelfths <-> tracks (design-v8 s2) */
  function widthToTracks(width, G, minSpan) {
    var lo = minSpan || 1;
    if (!Number.isInteger(width) || width < 1) return Math.min(Math.max(2, lo), G);
    var k = Math.floor(width * G / 12 + 0.5);
    return Math.max(lo, Math.min(k, G));
  }
  function tracksToWidth(k, G) { return k * 12 / G; }
  function snapTracks(px, trackW, gap, G, minSpan) {
    var k = Math.floor((px + gap) / (trackW + gap) + 0.5);
    return Math.max(minSpan || 1, Math.min(k, G));
  }
  /* east drag: a pointer at the canvas right edge (after real travel to the right) means the full grid, G; else the snap */
  function edgeSpan(px, trackW, gap, G, minSpan, atEdge) {
    return atEdge ? G : snapTracks(px, trackW, gap, G, minSpan);
  }

  BOARD.layout = { GUTTER: GUTTER, MIN_PX: MIN_PX, ORDER: ORDER, SMALLEST: SMALLEST, defaultRank: defaultRank,
    colCount: colCount, place: place, refresh: refresh, recordGrid: recordGrid, migrate: migrate, dropIndex: dropIndex,
    widthToTracks: widthToTracks, tracksToWidth: tracksToWidth, snapTracks: snapTracks, edgeSpan: edgeSpan };

  /* ---------------- DOM part ---------------- */
  /* mount(opts) -> {relayout, request, drag, resize, key, observe, unobserve}
     opts: canvas (element), get() -> {panels: [{id, order, tracks, idx, hidden, max_height, el, maxPx, hdr}], scale},
           set(id, patch) edits the state (order, max_height), changed(extra) is called after a user edit.
     relayout() is a placement moment: it calls BOARD.layout.place. request() is a data refresh: it calls BOARD.layout.refresh
     (x and order stay). request(true) is a placement moment on the next frame (window or text size change). */
  function mount(opts) {
    var canvas = opts.canvas, doc = root.document, busy = false, raf = 0, forced = false, G = 0, prev = null;
    var empty = doc.createElement("div");
    empty.className = "empty"; empty.hidden = true; empty.textContent = "All panels are hidden. Open Panels ▾ to show them.";
    canvas.appendChild(empty);

    function scaleMax(p, scale) {
      var base = p.max_height != null ? p.max_height : p.maxPx;
      return Math.round(base * scale);
    }
    function caps(st) {
      st.panels.forEach(function (p) {
        p.el.hidden = !!p.hidden;
        var h = scaleMax(p, st.scale);
        p.el.style.maxHeight = h + "px";
        p.el.style.height = p.max_height != null ? h + "px" : "";   /* a height set by the PO is the height; else as tall as the content */
      });
    }
    /* panels in saved order (a tie by default order); hidden ones only when `all` */
    function ordered(st, all) {
      return st.panels.filter(function (p) { return all || !p.hidden; })
        .sort(function (a, b) { return (a.order - b.order) || (a.idx - b.idx); });
    }
    function spanOf(p) { return widthToTracks(p.tracks, G, SMALLEST[p.id] || 1); }
    function rowH(el) { return Math.ceil((el.getBoundingClientRect().height + GUTTER) / 2) * 2; }

    /* the DOM stays in saved order (reading order, Tab order); a node moves only when it is not already right */
    function syncDom(st) {
      var focus = doc.activeElement, at = empty;
      ordered(st, true).forEach(function (p) {
        if (at.nextSibling !== p.el) canvas.insertBefore(p.el, at.nextSibling);
        at = p.el;
      });
      if (focus && focus !== doc.activeElement && focus.focus) focus.focus();
    }

    /* each panel at its final width, no row: its height is the height of the content up to its maximum */
    function measure(list) {
      list.forEach(function (p) { p.el.style.gridColumn = "span " + spanOf(p); p.el.style.gridRow = ""; });
      return list.map(function (p) { return { id: p.id, span: spanOf(p), height: rowH(p.el) }; });
    }
    function put(el, x, span, y, h) {
      el.style.gridColumn = (x + 1) + " / span " + span;
      el.style.gridRow = (y / 2 + 1) + " / span " + (h / 2);
    }

    /* a placement moment: choose tracks and rows for every shown panel */
    function placeNow() {
      var st = opts.get();
      G = colCount(root.innerWidth, st.scale);
      canvas.style.setProperty("--n", String(G));
      caps(st); syncDom(st);
      var vis = ordered(st);
      empty.hidden = vis.length > 0;
      if (!vis.length) { prev = null; return; }
      var items = measure(vis), pos = BOARD.layout.place(items, G);
      prev = BOARD.layout.recordGrid(items, pos, G);
      items.forEach(function (it, i) { put(vis[i].el, pos[it.id].x, it.span, pos[it.id].y, it.height); });
      st.panels.forEach(function (q) { var h = q.el.querySelector(".rz.e"); if (h) h.hidden = (SMALLEST[q.id] || 1) >= G; });
    }
    function relayout() { if (!busy) placeNow(); }

    /* a data refresh: tracks and order stay, rows follow the heights */
    function refreshNow() {
      var st = opts.get();
      if (!prev || colCount(root.innerWidth, st.scale) !== G) { placeNow(); return; }
      var vis = ordered(st);
      if (vis.length !== prev.length || vis.some(function (p) { return !prev.some(function (r) { return r.id === p.id; }); })) { placeNow(); return; }
      var byId = {}, heights = {};
      vis.forEach(function (p) { byId[p.id] = p; heights[p.id] = rowH(p.el); });
      var pos = BOARD.layout.refresh(prev, heights);
      prev.forEach(function (r) { put(byId[r.id].el, r.x, r.span, pos[r.id].y, heights[r.id]); });
    }
    function request(full) {
      if (full) forced = true;
      if (raf || busy) return;
      raf = root.requestAnimationFrame(function () {
        raf = 0;
        if (busy) return;
        if (forced) { forced = false; placeNow(); } else refreshNow();
      });
    }

    /* renumber the full order (hidden panels included) 0..k-1 */
    function setOrder(list) { list.forEach(function (q, i) { opts.set(q.id, { order: i }); }); }

    /* ---- drag: header, 4 px; a dashed drop spot shows where it lands (an item of place); Esc or a drop outside cancels ---- */
    function drag(p, e) {
      if (e.button != null && e.button !== 0) return;
      if (e.target.closest && e.target.closest("button")) return;
      var el = p.el, sx = e.clientX, sy = e.clientY, r = el.getBoundingClientRect(), moved = false;
      var slot = null, others = null, oitems = null, rest = null, idx = -1, outside = false, ghost = null;
      function start() {
        moved = true; busy = true;
        var st = opts.get();
        G = colCount(root.innerWidth, st.scale);
        ghost = { id: "\u0000ghost", span: spanOf(p), height: Math.ceil((r.height + GUTTER) / 2) * 2 };
        slot = doc.createElement("div"); slot.className = "ghost"; canvas.appendChild(slot);
        el.style.width = r.width + "px"; el.classList.add("drag");
        others = ordered(st).filter(function (q) { return q !== p; });
        oitems = measure(others);
        layoutWith(null);
        var cr = canvas.getBoundingClientRect();
        rest = others.map(function (q) { var b = q.el.getBoundingClientRect(); return { left: b.left - cr.left, top: b.top - cr.top, width: b.width, height: b.height }; });
        idx = -1;
      }
      /* the page with the drop spot at reading index i (null: no spot, the others at rest) */
      function layoutWith(i) {
        var items = oitems.slice();
        if (i != null) items.splice(i, 0, ghost);
        var pos = BOARD.layout.place(items, G);
        items.forEach(function (it) {
          var q = pos[it.id];
          put(it === ghost ? slot : others[oitems.indexOf(it)].el, q.x, it.span, q.y, it.height);
        });
        slot.hidden = i == null;
      }
      function mv(ev) {
        var dx = ev.clientX - sx, dy = ev.clientY - sy;
        if (!moved) { if (Math.hypot(dx, dy) < 4) return; start(); }
        el.style.left = (r.left + dx) + "px"; el.style.top = (r.top + dy) + "px";
        if (ev.clientY < 40) root.scrollBy(0, -20); else if (ev.clientY > root.innerHeight - 40) root.scrollBy(0, 20);
        var cr = canvas.getBoundingClientRect();
        outside = ev.clientX < cr.left || ev.clientX > cr.right || ev.clientY < cr.top || ev.clientY > root.innerHeight;
        var i = -1;
        if (!outside) {
          var rects = rest.map(function (q) { return { left: q.left + cr.left, top: q.top + cr.top, width: q.width, height: q.height }; });
          var bottom = rects.reduce(function (m, q) { return Math.max(m, q.top + q.height); }, 0);
          i = !rects.length || ev.clientY > bottom ? rects.length : dropIndex(rects, ev.clientX, ev.clientY);
        }
        if (i !== idx) { idx = i; layoutWith(i < 0 ? null : i); }
      }
      function done(cancel) {
        doc.removeEventListener("pointermove", mv);
        doc.removeEventListener("pointerup", up);
        doc.removeEventListener("pointercancel", cp);
        doc.removeEventListener("keydown", kd);
        var save = moved && !cancel && !outside && idx >= 0;
        el.classList.remove("drag"); el.style.width = ""; el.style.left = ""; el.style.top = "";
        if (slot) slot.remove();
        busy = false;
        if (save) {
          var st = opts.get(), full = ordered(st, true), before = full.map(function (q) { return q.id; }).join();
          var rest2 = full.filter(function (q) { return q !== p; }), at;
          if (idx < others.length) at = rest2.indexOf(others[idx]);
          else at = others.length ? rest2.indexOf(others[others.length - 1]) + 1 : rest2.length;
          rest2.splice(at, 0, p);
          if (rest2.map(function (q) { return q.id; }).join() !== before) { setOrder(rest2); opts.changed(); }
        }
        placeNow();
      }
      function up() { done(false); }
      function cp() { done(true); }
      function kd(ev) { if (ev.key === "Escape") done(true); }
      doc.addEventListener("pointermove", mv);
      doc.addEventListener("pointerup", up);
      doc.addEventListener("pointercancel", cp);
      doc.addEventListener("keydown", kd);
    }

    /* ---- resize: the south edge sets the height cap; the panels below it in its tracks follow live, tracks stay ---- */
    function resize(p, dir, e) {
      var el = p.el, sy = e.clientY, h0 = el.offsetHeight, st = opts.get();
      el.classList.add("rsz"); busy = true;
      function mv(ev) {
        p.max_height = Math.max(MIN_PX, Math.round((h0 + ev.clientY - sy) / st.scale));
        el.style.maxHeight = el.style.height = Math.round(p.max_height * st.scale) + "px";
        refreshNow();
      }
      function up() {
        doc.removeEventListener("pointermove", mv);
        doc.removeEventListener("pointerup", up);
        doc.removeEventListener("pointercancel", up);
        el.classList.remove("rsz"); busy = false;
        opts.set(p.id, { max_height: p.max_height });
        opts.changed();
        placeNow();
      }
      doc.addEventListener("pointermove", mv);
      doc.addEventListener("pointerup", up);
      doc.addEventListener("pointercancel", up);
    }

    /* ---- east edge: the span in whole tracks (design-v8 s6). Only an outline, a pill and guides move; the panels move on release ---- */
    function minOf(p) { return SMALLEST[p.id] || 1; }
    function setSpan(p, k) {   /* one save, then a placement moment; nothing when the span is the same */
      if (k === spanOf(p)) return false;
      opts.set(p.id, { tracks: tracksToWidth(k, G) });
      opts.changed();
      placeNow();
      return true;
    }
    function resizeEast(p, e) {
      if (e.button != null && e.button !== 0) return;
      var el = p.el, st = opts.get(), r = el.getBoundingClientRect(), cr = canvas.getBoundingClientRect();
      var cs = root.getComputedStyle(canvas), pl = parseFloat(cs.paddingLeft) || 0, pr = parseFloat(cs.paddingRight) || 0;
      G = colCount(root.innerWidth, st.scale);
      var trackW = (cr.width - pl - pr - (G - 1) * GUTTER) / G, k = spanOf(p), els = [], handle = e.currentTarget || null;
      var outline = doc.createElement("div"), pill = doc.createElement("div");
      outline.className = "rzo"; pill.className = "rzp"; outline.appendChild(pill);
      outline.style.top = r.top + "px"; outline.style.left = r.left + "px"; outline.style.height = r.height + "px";
      els.push(outline);
      for (var i = 0; i < G; i++) {
        [0, 1].forEach(function (side) {
          var g = doc.createElement("div"); g.className = "rzg";
          g.style.left = (cr.left + pl + i * (trackW + GUTTER) + (side ? trackW : 0)) + "px";
          g.style.top = cr.top + "px"; g.style.height = cr.height + "px"; els.push(g);
        });
      }
      els.forEach(function (n) { doc.body.appendChild(n); });
      busy = true; el.classList.add("rsz"); 
      if (handle && handle.setPointerCapture && e.pointerId != null) { try { handle.setPointerCapture(e.pointerId); } catch (x) { /* synthetic event */ } }
      function show() {
        var wk = k * trackW + (k - 1) * GUTTER;   /* a panel that would pass the canvas edge lands further left after place: show that */
        outline.style.width = wk + "px";
        outline.style.left = Math.min(r.left, cr.right - pr - wk) + "px";
        pill.textContent = k + " of " + G + " columns";
      }
      show();
      var grabX = e.clientX == null ? r.right : e.clientX;
      function mv(ev) {
        var atEdge = ev.clientX >= cr.right - pr && ev.clientX - grabX >= 8;
        k = edgeSpan(ev.clientX - r.left, trackW, GUTTER, G, minOf(p), atEdge); show();
      }
      function end(cancel) {
        doc.removeEventListener("pointermove", mv);
        doc.removeEventListener("pointerup", up);
        doc.removeEventListener("pointercancel", cp);
        doc.removeEventListener("keydown", kd, true);
        root.removeEventListener("resize", cp);
        els.forEach(function (n) { n.remove(); });
        el.classList.remove("rsz"); busy = false;
        if (!cancel) { if (!setSpan(p, k)) placeNow(); } else placeNow();
      }
      function up() { end(false); }
      function cp() { end(true); }
      function kd(ev) { if (ev.key === "Escape") { ev.preventDefault(); end(true); } }
      doc.addEventListener("pointermove", mv);
      doc.addEventListener("pointerup", up);
      doc.addEventListener("pointercancel", cp);
      doc.addEventListener("keydown", kd, true);
      root.addEventListener("resize", cp);
    }
    /* handle keys: Left one track narrower, Right one wider; double-click = default width and no saved width */
    function edgeKey(p, ev) {
      if (ev.key !== "ArrowLeft" && ev.key !== "ArrowRight") return;
      ev.preventDefault(); ev.stopPropagation();
      var k = Math.max(minOf(p), Math.min(G, spanOf(p) + (ev.key === "ArrowRight" ? 1 : -1)));
      setSpan(p, k);
    }
    function edgeReset(p) {
      if (p.tracks == null) return;
      opts.set(p.id, { tracks: null }); opts.changed(); placeNow();
    }

    /* ---- keyboard on a focused panel title: Up/Left one place earlier, Down/Right one later (hidden panels are skipped);
       Shift+Up/Down change the height by 80 px; focus stays on the title ---- */
    function key(p, ev) {
      var st = opts.get(), k = ev.key;
      if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].indexOf(k) < 0) return;
      ev.preventDefault();
      if (ev.shiftKey && (k === "ArrowLeft" || k === "ArrowRight")) { edgeKey(p, ev); if (p.hdr && p.hdr.focus) p.hdr.focus(); return; }
      if (ev.shiftKey) {
        if (k !== "ArrowUp" && k !== "ArrowDown") return;
        var cur = (p.max_height != null ? p.max_height : p.maxPx) * st.scale;
        p.max_height = Math.max(MIN_PX, Math.round((cur + (k === "ArrowDown" ? 80 : -80)) / st.scale));
        opts.set(p.id, { max_height: p.max_height });
      } else {
        var full = ordered(st, true), i = full.indexOf(p), j = i, back = k === "ArrowUp" || k === "ArrowLeft";
        do { j += back ? -1 : 1; } while (full[j] && full[j].hidden);
        if (!full[j]) return;
        full.splice(i, 1); full.splice(j, 0, p);
        setOrder(full);
      }
      opts.changed();
      placeNow();
      if (p.hdr && p.hdr.focus) p.hdr.focus();
    }

    var ro = root.ResizeObserver ? new root.ResizeObserver(function () { request(); }) : null;
    return {
      relayout: relayout, request: request, drag: drag, resize: resize, key: key,
      resizeEast: resizeEast, edgeKey: edgeKey, edgeReset: edgeReset,
      observe: function (el) { if (ro) ro.observe(el); },
      unobserve: function (el) { if (ro) ro.unobserve(el); }
    };
  }
  BOARD.layout.mount = mount;
})(typeof window !== "undefined" ? window : this);
