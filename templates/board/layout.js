/* squad-board layout engine (ticket 26, design-v7 s2 and s7): page columns.
   Pure part: BOARD.layout.colCount, place, norm. They touch no DOM, no window, no clock.
   DOM part: BOARD.layout.mount(): #canvas holds N .col elements; panels are normal blocks in a column.
   It only edits the state ({id: {col, order, hidden, max_height}}); pixels are never stored. */
(function (root) {
  "use strict";
  var BOARD = root.BOARD = root.BOARD || {};
  var GUTTER = 12;   /* the same gap between panels, between columns and to the page edge */
  var MIN_PX = 76;   /* a panel is never shorter than this at Normal text */
  var ORDER = ["inbox", "tasks", "agents", "files", "scopes", "worktime"];   /* default place order (design-v7 s2) */

  /* number of page columns for a window: W = innerWidth / text scale; 3 from 1800, 2 from 932, else 1 */
  function colCount(innerWidth, scale) {
    var w = innerWidth / (scale || 1);
    return w >= 1800 ? 3 : (w >= 932 ? 2 : 1);
  }

  /* place(ids, n, heights, base) -> {id: {col, pos}}
     ids: panel ids in default order (hidden ones left out); heights: {id: px}.
     Each panel goes to the shortest column at that moment, the leftmost when equal. base: optional
     [{h, n}] per column (height and panel count already there) for panels placed on top of existing ones. */
  function place(ids, n, heights, base) {
    var h = [], cnt = [], out = {}, i;
    for (i = 0; i < n; i++) { h.push(base && base[i] ? base[i].h : 0); cnt.push(base && base[i] ? base[i].n : 0); }
    ids.forEach(function (id) {
      var c = h.indexOf(Math.min.apply(null, h));
      out[id] = { col: c, pos: cnt[c] };
      cnt[c]++; h[c] += (heights[id] || 0) + GUTTER;
    });
    return out;
  }

  /* norm(panels, n) -> [[id, ...] per column], for display only. panels: [{id, col, order, idx, hidden}].
     A hidden panel is skipped; a col above n-1 shows in the last column; a missing or non-integer col is skipped
     (the caller gives it a default place). Sorted by order, a tie by default order (idx). The state is not changed. */
  function norm(panels, n) {
    var by = [], i;
    for (i = 0; i < n; i++) by.push([]);
    panels.forEach(function (p) {
      if (p.hidden || !Number.isInteger(p.col) || p.col < 0) return;
      by[Math.min(p.col, n - 1)].push(p);
    });
    return by.map(function (list) {
      return list.sort(function (a, b) { return (a.order - b.order) || (a.idx - b.idx); }).map(function (p) { return p.id; });
    });
  }

  function defaultRank(id, idx) { var k = ORDER.indexOf(id); return k < 0 ? ORDER.length + idx : k; }

  BOARD.layout = { GUTTER: GUTTER, MIN_PX: MIN_PX, ORDER: ORDER, colCount: colCount, place: place, norm: norm, defaultRank: defaultRank };

  /* ---------------- DOM part ---------------- */
  /* mount(opts) -> {relayout, plan, request, drag, resize, key, observe, unobserve}
     opts: canvas (element), get() -> {panels: [{id, col, order, idx, hidden, max_height, el, maxPx, hdr}], scale, auto},
           set(id, patch) edits the state (col, order, max_height), changed(extra) is called after a user edit. */
  function mount(opts) {
    var canvas = opts.canvas, busy = false, raf = 0, lastN = 0, cols = [];

    function count() { var st = opts.get(); return colCount(root.innerWidth, st.scale); }

    function scaleMax(p, scale) {
      var base = p.max_height != null ? p.max_height : p.maxPx;
      return Math.round(base * scale);
    }

    function buildCols(n) {
      if (cols.length === n) return;
      cols.forEach(function (c) { c.remove(); });
      cols = [];
      canvas.style.setProperty("--n", String(n));
      for (var i = 0; i < n; i++) {
        var c = root.document.createElement("div");
        c.className = "col"; c.dataset.col = String(i);
        canvas.appendChild(c); cols.push(c);
      }
    }

    /* put the panels of `by` in their column in order, moving a node only when it is not already right */
    function sync(by, st) {
      var focus = root.document.activeElement;
      by.forEach(function (ids, ci) {
        var c = cols[ci], prev = null;
        ids.forEach(function (id) {
          var p = st.panels.filter(function (q) { return q.id === id; })[0], e = p.el;
          if (e.parentNode !== c || e.previousElementSibling !== prev) c.insertBefore(e, prev ? prev.nextSibling : c.firstChild);
          prev = e;
        });
        var emp = c.querySelector(".empty");
        if (!ids.length && !emp) {
          emp = root.document.createElement("div"); emp.className = "empty"; emp.textContent = "Drop a panel here"; c.appendChild(emp);
        } else if (ids.length && emp) emp.remove();
      });
      if (focus && focus !== root.document.activeElement && focus.focus) focus.focus();
    }

    function caps(st) {
      st.panels.forEach(function (p) {
        p.el.hidden = !!p.hidden;
        var h = scaleMax(p, st.scale);
        p.el.style.maxHeight = h + "px";
        p.el.style.height = p.max_height != null ? h + "px" : "";   /* a height set by the PO is the height; else as tall as the content */
      });
    }

    /* Panels that are shown and have no column (first load of an old file, a panel shown for the first time) get the
       default place, on top of the panels already there. */
    function placeNew(st, n, all) {
      var vis = st.panels.filter(function (p) { return !p.hidden; });
      var fresh = vis.filter(function (p) { return all || !Number.isInteger(p.col) || p.col < 0; });
      if (!fresh.length) return false;
      var keep = vis.filter(function (p) { return fresh.indexOf(p) < 0; });
      var by = norm(keep, n);
      /* measure: every fresh panel alone at the end of column 0, at column width, capped */
      fresh.forEach(function (p) { cols[0].appendChild(p.el); });
      var heights = {};
      fresh.forEach(function (p) { heights[p.id] = Math.ceil(p.el.offsetHeight); });
      sync(by.map(function (ids) { return ids; }), { panels: keep });
      var base = by.map(function (ids, ci) {
        var h = 0;
        ids.forEach(function (id) { var q = keep.filter(function (k) { return k.id === id; })[0]; h += Math.ceil(q.el.offsetHeight) + GUTTER; });
        return { h: h, n: ids.length };
      });
      var order = fresh.slice().sort(function (a, b) { return defaultRank(a.id, a.idx) - defaultRank(b.id, b.idx); }).map(function (p) { return p.id; });
      var res = place(order, n, heights, base);
      Object.keys(res).forEach(function (id) { opts.set(id, { col: res[id].col, order: res[id].pos }); });
      return true;
    }

    function relayout() {
      if (busy) return;
      var st = opts.get(), n = count();
      caps(st);
      buildCols(n);
      var all = lastN && n !== lastN && st.auto;      /* a change of column count re-places while the PO has not moved a panel */
      lastN = n;
      placeNew(st, n, all);
      sync(norm(st.panels, n), st);
    }

    /* default place of every shown panel (first load, Reset, text size, new choice); `onlyNew` keeps saved places */
    function plan(onlyNew) {
      var st = opts.get(), n = count();
      caps(st); buildCols(n); lastN = n;
      st.panels.forEach(function (p) { p.el.hidden = !!p.hidden; });
      placeNew(st, n, !onlyNew);
      sync(norm(st.panels, n), st);
    }

    function request() {
      if (raf || busy) return;
      raf = root.requestAnimationFrame(function () { raf = 0; relayout(); });
    }

    /* the panels of a column, in DOM order, as ids */
    function idsOf(col, skip) {
      return [].slice.call(col.children).filter(function (k) { return k !== skip && (k.classList.contains("panel") || k.classList.contains("ghost")); })
        .map(function (k) { return k.classList.contains("ghost") ? null : k.dataset.panel; });
    }

    /* ---- drag: header, 4 px; a dashed drop spot shows where it lands; Esc or a drop outside cancels ---- */
    function drag(p, e) {
      if (e.button != null && e.button !== 0) return;
      if (e.target.closest && e.target.closest("button")) return;
      var el = p.el, sx = e.clientX, sy = e.clientY, r = el.getBoundingClientRect(), moved = false, slot = null, over = null;
      function mv(ev) {
        var dx = ev.clientX - sx, dy = ev.clientY - sy;
        if (!moved) {
          if (Math.hypot(dx, dy) < 4) return;
          moved = true; busy = true;
          slot = root.document.createElement("div"); slot.className = "ghost"; slot.style.height = r.height + "px";
          el.after(slot);
          el.style.width = r.width + "px"; el.classList.add("drag");
        }
        el.style.left = (r.left + dx) + "px"; el.style.top = (r.top + dy) + "px";
        var best = null, bestD = Infinity;
        cols.forEach(function (c) {
          c.classList.remove("over");
          var b = c.getBoundingClientRect(), d = ev.clientX < b.left ? b.left - ev.clientX : (ev.clientX > b.right ? ev.clientX - b.right : 0);
          if (d < bestD) { bestD = d; best = c; }
        });
        var first = cols[0].getBoundingClientRect(), last = cols[cols.length - 1].getBoundingClientRect();
        /* outside every column: left or right of the columns, above them (top bar) or below the window */
        var outside = ev.clientX < first.left || ev.clientX > last.right || ev.clientY < first.top || ev.clientY > root.innerHeight;
        if (outside) { slot.remove(); over = null; return; }
        over = best; best.classList.add("over");
        var emp = best.querySelector(".empty"); if (emp) emp.hidden = true;
        slot.remove();   /* decide on the layout at rest: the spot itself must not move the middles */
        var kids = [].slice.call(best.children).filter(function (k) { return k !== el && k.classList.contains("panel") && !k.hidden; }), at = null;
        for (var i = 0; i < kids.length; i++) {
          var b2 = kids[i].getBoundingClientRect();
          if (ev.clientY < b2.top + b2.height / 2) { at = kids[i]; break; }
        }
        if (at) best.insertBefore(slot, at); else best.appendChild(slot);
      }
      function done(cancel) {
        root.document.removeEventListener("pointermove", mv);
        root.document.removeEventListener("pointerup", up);
        root.document.removeEventListener("pointercancel", cp);
        root.document.removeEventListener("keydown", kd);
        var save = moved && !cancel && over && slot && slot.parentNode;
        if (save) {
          var ci = cols.indexOf(over);
          idsOf(over, el).forEach(function (id, i) { opts.set(id || p.id, { col: ci, order: i }); });
        }
        el.classList.remove("drag"); el.style.width = ""; el.style.left = ""; el.style.top = "";
        if (slot) slot.remove();
        cols.forEach(function (c) { c.classList.remove("over"); var emp = c.querySelector(".empty"); if (emp) emp.hidden = false; });
        busy = false;
        if (save) {
          /* the column it left closes up: renumber the rest by their order */
          renumber(opts.get());
          opts.changed({ auto: false });
        }
        relayout();
      }
      function up() { done(false); }
      function cp() { done(true); }
      function kd(ev) { if (ev.key === "Escape") done(true); }
      root.document.addEventListener("pointermove", mv);
      root.document.addEventListener("pointerup", up);
      root.document.addEventListener("pointercancel", cp);
      root.document.addEventListener("keydown", kd);
    }

    /* positions 0..k-1 in every column, in the order shown (hidden panels keep their own col and order) */
    function renumber(st) {
      var n = count();
      norm(st.panels, n).forEach(function (ids, ci) {
        ids.forEach(function (id, i) {
          opts.set(id, { order: i });
        });
      });
    }

    /* ---- resize: the south edge sets the height cap; a width never changes ---- */
    function resize(p, dir, e) {
      var el = p.el, sy = e.clientY, h0 = el.offsetHeight, st = opts.get();
      el.classList.add("rsz"); busy = true;
      function mv(ev) {
        p.max_height = Math.max(MIN_PX, Math.round((h0 + ev.clientY - sy) / st.scale));
        el.style.maxHeight = el.style.height = Math.round(p.max_height * st.scale) + "px";
      }
      function up() {
        root.document.removeEventListener("pointermove", mv);
        root.document.removeEventListener("pointerup", up);
        root.document.removeEventListener("pointercancel", up);
        el.classList.remove("rsz"); busy = false;
        opts.set(p.id, { max_height: p.max_height });
        opts.changed({ auto: false });
        relayout();
      }
      root.document.addEventListener("pointermove", mv);
      root.document.addEventListener("pointerup", up);
      root.document.addEventListener("pointercancel", up);
    }

    /* ---- keyboard on a focused panel title: arrows move (Up/Down in the column, Left/Right to the next column),
       Shift+Up/Down change the height by 80 px; focus stays on the title ---- */
    function key(p, ev) {
      var st = opts.get(), n = count(), k = ev.key;
      if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].indexOf(k) < 0) return;
      ev.preventDefault();
      if (ev.shiftKey) {
        if (k !== "ArrowUp" && k !== "ArrowDown") return;
        var cur = (p.max_height != null ? p.max_height : p.maxPx) * st.scale;
        p.max_height = Math.max(MIN_PX, Math.round((cur + (k === "ArrowDown" ? 80 : -80)) / st.scale));
        opts.set(p.id, { max_height: p.max_height });
      } else {
        var by = norm(st.panels, n), ci = -1, i = -1;
        by.forEach(function (ids, c) { var j = ids.indexOf(p.id); if (j >= 0) { ci = c; i = j; } });
        if (ci < 0) return;
        var to = ci, at = i;
        if (k === "ArrowUp") { if (i === 0) return; at = i - 1; }
        else if (k === "ArrowDown") { if (i === by[ci].length - 1) return; at = i + 1; }
        else {
          to = ci + (k === "ArrowLeft" ? -1 : 1);
          if (to < 0 || to >= n) return;
          at = Math.min(i, by[to].length);
        }
        by[ci].splice(i, 1);
        by[to].splice(at, 0, p.id);
        [ci, to].forEach(function (c) { by[c].forEach(function (id, j) { opts.set(id, { col: c, order: j }); }); });
      }
      opts.changed({ auto: false });
      relayout();
      if (p.hdr && p.hdr.focus) p.hdr.focus();
    }

    var ro = root.ResizeObserver ? new root.ResizeObserver(request) : null;
    return {
      relayout: relayout, plan: plan, request: request, drag: drag, resize: resize, key: key,
      observe: function (el) { if (ro) ro.observe(el); },
      unobserve: function (el) { if (ro) ro.unobserve(el); }
    };
  }
  BOARD.layout.mount = mount;
})(typeof window !== "undefined" ? window : this);
