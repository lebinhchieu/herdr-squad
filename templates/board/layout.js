/* squad-board layout engine (ticket 10, architecture 1a).
   Pure part: BOARD.layout.cols, pack, autoPlan. They touch no DOM, no window, no clock.
   DOM part: BOARD.layout.mount(): places the panels, drag, resize, keyboard. It only edits the state
   ({id: {order, span, hidden, max_height}}); pixels are never stored. */
(function (root) {
  "use strict";
  var BOARD = root.BOARD = root.BOARD || {};
  var UNIT = 4;      /* row unit in px: a panel is as tall as its content, rounded up to 4 px */
  var GUTTER = 12;   /* the same gap between panels and to the page edge */
  var GRID = 12;     /* spans are stored in twelfths of the width */
  var MIN_PX = 76;   /* a panel is never shorter than this at Normal text */

  /* columns of the grid for a container width: 12 from 1200 px, 8 narrower (the page scrolls sideways under 1000) */
  function cols(width) { return width >= 1200 ? 12 : 8; }

  function spanIn(span12, n) { return Math.min(n, Math.max(1, Math.round(span12 * n / GRID))); }

  function rowSpanOf(px) { return Math.ceil((px + GUTTER) / UNIT); }

  /* pack(panels, cols, unit) -> [{id, col, row, span, rowSpan, scroll}]
     panels: [{id, order, span, hidden, height, max}] (height and max in px, span in twelfths).
     Hidden panels are skipped. Each panel goes to the lowest, then leftmost, free place: a short panel beside a
     tall one leaves no empty cell and the panels below move up. Content above `max` gets rowSpan of the cap
     and scroll: true. */
  function pack(panels, n, unit) {
    unit = unit || UNIT;
    var list = panels.filter(function (p) { return !p.hidden; })
      .sort(function (a, b) { return a.order - b.order; });
    var placed = [];
    list.forEach(function (p) {
      var span = spanIn(p.span, n);
      var cap = p.max != null ? p.max : Infinity;
      var h = Math.min(p.height, cap);
      var rs = Math.ceil((h + GUTTER) / unit);
      var ys = [0];
      placed.forEach(function (q) { ys.push(q.row + q.rowSpan); });
      ys.sort(function (a, b) { return a - b; });
      var best = null;
      for (var k = 0; k < ys.length && !best; k++) {
        for (var c = 0; c + span <= n; c++) {
          var hit = false;
          for (var j = 0; j < placed.length; j++) {
            var q = placed[j];
            if (c < q.col + q.span && q.col < c + span && ys[k] < q.row + q.rowSpan && q.row < ys[k] + rs) { hit = true; break; }
          }
          if (!hit) { best = { col: c, row: ys[k] }; break; }
        }
      }
      placed.push({ id: p.id, col: best.col, row: best.row, span: span, rowSpan: rs, scroll: p.height > cap });
    });
    return placed;
  }

  /* total empty area (cells) inside the bounding box of a packed result; the plan minimises it */
  function emptyArea(cells, n) {
    var bottom = 0, used = 0;
    cells.forEach(function (c) { bottom = Math.max(bottom, c.row + c.rowSpan); used += c.span * c.rowSpan; });
    return bottom * n - used;
  }
  function bottomOf(cells) {
    var b = 0;
    cells.forEach(function (c) { b = Math.max(b, c.row + c.rowSpan); });
    return b;
  }

  /* autoPlan(panels, n, unit, heightAt) -> [{id, order, span}]
     Picks the order and the width (from `spans`, in twelfths) that leave the least empty area. The first visible
     panel (Needs you) stays first. `heightAt(id, span12)` gives the content height at that width. Panels with
     `fixed: true` keep their span. Run on a new choice, a font change or a show/hide, never on a data refresh. */
  function autoPlan(panels, n, unit, heightAt) {
    var vis = panels.filter(function (p) { return !p.hidden; }).sort(function (a, b) { return a.order - b.order; });
    if (vis.length < 2) return vis.map(function (p, i) { return { id: p.id, order: i, span: p.span }; });
    var head = vis[0], rest = vis.slice(1);
    var best = null, bestKey = null;
    function perms(a) {
      if (a.length < 2) return [a];
      var out = [];
      a.forEach(function (x, i) {
        perms(a.slice(0, i).concat(a.slice(i + 1))).forEach(function (p) { out.push([x].concat(p)); });
      });
      return out;
    }
    var combos = [[]];
    vis.forEach(function (p) {
      var opts = p.fixed ? [p.span] : (p.spans && p.spans.length ? p.spans : [p.span]);
      var next = [];
      combos.forEach(function (c) { opts.forEach(function (s) { next.push(c.concat([[p.id, s]])); }); });
      combos = next;
    });
    perms(rest).forEach(function (r) {
      var order = [head].concat(r);
      combos.forEach(function (cb) {
        var W = {};
        cb.forEach(function (c) { W[c[0]] = c[1]; });
        var items = order.map(function (p, i) {
          return { id: p.id, order: i, span: W[p.id], height: heightAt(p.id, W[p.id]), max: p.max };
        });
        var cells = pack(items, n, unit);
        var key = emptyArea(cells, n) * 100000 + bottomOf(cells);
        if (bestKey === null || key < bestKey) { bestKey = key; best = items; }
      });
    });
    return best.map(function (i) { return { id: i.id, order: i.order, span: i.span }; });
  }

  BOARD.layout = { UNIT: UNIT, GUTTER: GUTTER, GRID: GRID, MIN_PX: MIN_PX, cols: cols, pack: pack, autoPlan: autoPlan,
                   rowSpanOf: rowSpanOf, spanIn: spanIn };

  /* ---------------- DOM part ---------------- */
  /* mount(opts) -> {relayout, plan}
     opts: canvas (element), get() -> {panels: [{id, order, span, hidden, max_height, el, maxPx, spans}], scale}
           set(id, patch) edits the state (order, span, max_height, hidden), changed() is called after a user edit. */
  function mount(opts) {
    var canvas = opts.canvas, busy = false, raf = 0;

    function width() { return canvas.clientWidth || 1000; }

    /* natural px height of a panel at its current width (height is "auto" while measuring): title + body padding + content */
    function natural(p) { return Math.ceil(p.el.offsetHeight); }

    function widthPx(span12, n) {
      var s = spanIn(span12, n), cw = (width() - GUTTER * (n - 1)) / n;
      return s * cw + (s - 1) * GUTTER;
    }

    function visible(st) { return st.panels.filter(function (p) { return !p.hidden; }); }

    function scaleMax(p, scale) {
      var base = p.max_height != null ? p.max_height : p.maxPx;
      return Math.round(base * scale);
    }

    function items(st, n, spanOf) {
      return st.panels.map(function (p) {
        var span = spanOf ? spanOf(p) : p.span;
        p.el.style.width = widthPx(span, n) + "px";
        p.el.style.height = "auto";
        return { id: p.id, order: p.order, span: span, hidden: p.hidden, max: scaleMax(p, st.scale), height: 0, _p: p };
      });
    }

    function measureAll(list) {
      list.forEach(function (it) {
        if (it.hidden) return;
        it._p.el.hidden = false;
        it.height = natural(it._p);
      });
    }

    function place(cells, n, list) {
      var cw = (width() - GUTTER * (n - 1)) / n, bottom = 0;
      cells.forEach(function (c) {
        var p = list.filter(function (i) { return i.id === c.id; })[0]._p;
        var el = p.el;
        el.style.left = (c.col * (cw + GUTTER)) + "px";
        el.style.top = (c.row * UNIT) + "px";
        el.style.width = (c.span * cw + (c.span - 1) * GUTTER) + "px";
        el.style.height = (c.rowSpan * UNIT - GUTTER) + "px";
        el.classList.toggle("scrolls", c.scroll);
        bottom = Math.max(bottom, c.row * UNIT + c.rowSpan * UNIT - GUTTER);
      });
      canvas.style.height = Math.max(bottom, 40) + "px";
    }

    function relayout(skip) {
      if (busy && !skip) return;
      var st = opts.get(), n = cols(width());
      st.panels.forEach(function (p) { p.el.hidden = !!p.hidden; });
      var list = items(st, n);
      measureAll(list);
      var cells = pack(list, n, UNIT);
      place(cells, n, list);
      return cells;
    }

    /* auto plan: widths and order that leave the least empty area (never on a data refresh) */
    function plan() {
      var st = opts.get(), n = cols(width());
      var vis = visible(st).sort(function (a, b) { return a.order - b.order; });
      if (!vis.length) return;
      var cache = {};
      function heightAt(id, span) {
        var k = id + ":" + span;
        if (cache[k] == null) {
          var p = vis.filter(function (q) { return q.id === id; })[0];
          p.el.style.width = widthPx(span, n) + "px";
          p.el.style.height = "auto";
          cache[k] = natural(p);
        }
        return cache[k];
      }
      var input = vis.map(function (p) {
        return { id: p.id, order: p.order, span: p.span, hidden: false, max: scaleMax(p, st.scale), spans: p.spans };
      });
      var res = autoPlan(input, n, UNIT, heightAt);
      res.forEach(function (r) { opts.set(r.id, { order: r.order, span: r.span }); });
      relayout();
    }

    function request() {
      if (raf || busy) return;
      raf = root.requestAnimationFrame(function () { raf = 0; relayout(); });
    }

    /* ---- drag: reorder only; a dashed ghost shows the packed place; Esc cancels ---- */
    function drag(p, e) {
      if (e.button != null && e.button !== 0) return;
      if (e.target.closest && e.target.closest("button")) return;
      var el = p.el, sx = e.clientX, sy = e.clientY, ox = el.offsetLeft, oy = el.offsetTop, moved = false, ghost = null, target = null;
      function candidate(ev) {
        var st = opts.get(), n = cols(width()), px = ox + ev.clientX - sx + el.offsetWidth / 2, py = oy + ev.clientY - sy + el.offsetHeight / 2;
        var others = visible(st).filter(function (q) { return q.id !== p.id; }).sort(function (a, b) { return a.order - b.order; });
        var best = null;
        for (var k = 0; k <= others.length; k++) {
          var seq = others.slice(0, k).concat([p], others.slice(k));
          var list = seq.map(function (q, i) {
            return { id: q.id, order: i, span: q.span, hidden: false, max: scaleMax(q, st.scale),
                     height: natural(q), _p: q };
          });
          var cells = pack(list, n, UNIT), c = cells.filter(function (x) { return x.id === p.id; })[0];
          var cw = (width() - GUTTER * (n - 1)) / n;
          var cx = c.col * (cw + GUTTER) + (c.span * cw + (c.span - 1) * GUTTER) / 2, cy = c.row * UNIT + (c.rowSpan * UNIT - GUTTER) / 2;
          var d = Math.hypot(cx - px, cy - py);
          if (!best || d < best.d) best = { d: d, k: k, cells: cells, list: list };
        }
        return best;
      }
      function mv(ev) {
        var dx = ev.clientX - sx, dy = ev.clientY - sy;
        if (!moved) {
          if (Math.hypot(dx, dy) < 4) return;
          moved = true; busy = true; el.classList.add("drag");
          ghost = root.document.createElement("div"); ghost.className = "ghost"; canvas.appendChild(ghost);
        }
        el.style.left = (ox + dx) + "px"; el.style.top = (oy + dy) + "px";
        target = candidate(ev);
        var c = target.cells.filter(function (x) { return x.id === p.id; })[0], n = cols(width());
        var cw = (width() - GUTTER * (n - 1)) / n;
        ghost.style.left = (c.col * (cw + GUTTER)) + "px"; ghost.style.top = (c.row * UNIT) + "px";
        ghost.style.width = (c.span * cw + (c.span - 1) * GUTTER) + "px"; ghost.style.height = (c.rowSpan * UNIT - GUTTER) + "px";
      }
      function done(cancel) {
        root.document.removeEventListener("pointermove", mv);
        root.document.removeEventListener("pointerup", up);
        root.document.removeEventListener("pointercancel", up);
        root.document.removeEventListener("keydown", kd);
        el.classList.remove("drag");
        if (ghost) ghost.remove();
        busy = false;
        if (moved && target && !cancel) {
          target.list.forEach(function (it) { opts.set(it.id, { order: it.order }); });
          opts.changed({ auto: false });
        }
        relayout();
      }
      function up() { done(false); }
      function kd(ev) { if (ev.key === "Escape") done(true); }
      root.document.addEventListener("pointermove", mv);
      root.document.addEventListener("pointerup", up);
      root.document.addEventListener("pointercancel", up);
      root.document.addEventListener("keydown", kd);
    }

    /* ---- resize: east edge sets the width (span), south edge sets the height cap ---- */
    function resize(p, dir, e) {
      var el = p.el, sx = e.clientX, sy = e.clientY, n = cols(width()), cw = (width() - GUTTER * (n - 1)) / n;
      var w0 = Math.round((el.offsetWidth + GUTTER) / (cw + GUTTER)), h0 = el.offsetHeight, st = opts.get();
      el.classList.add("rsz"); busy = true;
      function mv(ev) {
        if (dir.indexOf("e") >= 0) {
          var s = Math.max(2, Math.min(n, w0 + Math.round((ev.clientX - sx) / (cw + GUTTER))));
          p.span = Math.round(s * GRID / n);
        }
        if (dir.indexOf("s") >= 0) {
          p.max_height = Math.max(MIN_PX, Math.round((h0 + ev.clientY - sy) / st.scale));
        }
        busy = false; relayout(); busy = true;
      }
      function up() {
        root.document.removeEventListener("pointermove", mv);
        root.document.removeEventListener("pointerup", up);
        root.document.removeEventListener("pointercancel", up);
        el.classList.remove("rsz"); busy = false;
        opts.set(p.id, { span: p.span, max_height: p.max_height });
        opts.changed({ auto: false });
        relayout();
      }
      root.document.addEventListener("pointermove", mv);
      root.document.addEventListener("pointerup", up);
      root.document.addEventListener("pointercancel", up);
    }

    /* ---- keyboard on a focused panel title: arrows reorder, Shift+arrows resize ---- */
    function key(p, ev) {
      var st = opts.get(), n = cols(width());
      var vis = visible(st).sort(function (a, b) { return a.order - b.order; }), i = vis.indexOf(p);
      var k = ev.key, step = Math.round(GRID / n);
      if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].indexOf(k) < 0) return;
      ev.preventDefault();
      if (ev.shiftKey) {
        if (k === "ArrowRight") p.span = Math.min(GRID, p.span + step);
        else if (k === "ArrowLeft") p.span = Math.max(2 * step, p.span - step);
        else if (k === "ArrowDown") p.max_height = Math.round(((p.max_height || p.maxPx) * st.scale + 80) / st.scale);
        else p.max_height = Math.max(MIN_PX, Math.round(((p.max_height || p.maxPx) * st.scale - 80) / st.scale));
        opts.set(p.id, { span: p.span, max_height: p.max_height });
      } else {
        var j = (k === "ArrowLeft" || k === "ArrowUp") ? i - 1 : i + 1;
        if (j < 0 || j >= vis.length) return;
        var a = vis[i].order; vis[i].order = vis[j].order; vis[j].order = a;
        opts.set(vis[i].id, { order: vis[i].order }); opts.set(vis[j].id, { order: vis[j].order });
      }
      opts.changed({ auto: false });
      relayout();
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
