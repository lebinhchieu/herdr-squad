/* Needs you panel and the permission banner (ticket 12; design-v5.md, proto-v5 "Needs you", ".banner").
   Cut this panel: delete this file and its <script> line. Pure rules are on BOARD (rowsForInbox, answerCommand, bannerLines, copyText).
   The page only SHOWS commands as text; the copy control puts that exact text on the clipboard. It never calls an API to write.
   Untrusted text (titles, options, blocks) reaches the DOM only through textContent. The counts come from the server
   (the header count here, the tab title in board.js: both the server's numbers); nothing is summed here. */
(function (root) {
  "use strict";
  var BOARD = root.BOARD = root.BOARD || {};

  /* ---------- pure rules ---------- */
  /* the command texts: the id is the only thing put into a command; a title or a "blocks" text never is */
  function answerCommand(id) { return "squad-inbox answer " + id; }
  function parkCommand(id) { return 'squad-inbox park --text "..." --from ' + id; }
  function unparkCommand(id) { return "squad-inbox unpark " + id; }
  function resolveCommand(id) { return 'squad-inbox resolve ' + id + ' --answer "..."'; }

  function optionRows(opts) {
    return (opts || []).map(function (o, i) {
      return { key: o.key || "ABCDEFGH".charAt(i), text: o.text, recommended: o.recommended === true, word: o.recommended === true ? "Manager recommends" : "" };
    });
  }

  /* rowsForInbox(data): the rows as plain data. open: oldest first (the server sorts; unknown age last); reads: items to read. */
  function rowsForInbox(data, tz) {
    var d = data || {}, rows = d.rows || [], pr = d.parked_rows || [];
    var mk = function (r) {
      return { id: r.id, title: r.title, age: BOARD.ageWords(r.age_s), blocks: r.blocks || "", options: optionRows(r.options),
               answer: answerCommand(r.id), park: parkCommand(r.id), scope: r.scope, read: r.kind === "answer" };
    };
    var out = (d.others || []).map(function (o) { return o.scope; });
    var perms = bannerLines(d.banner).lines.filter(function (l) { return out.indexOf(l.scope) < 0; });
    var parked = pr.filter(function (r) { return r.status === "parked"; }).map(function (r) {
      return { id: r.id, level: r.level, scope: r.scope, text: r.text, from: r.from, blocks: r.blocks, parked_iso: r.parked_iso, file: r.file,
               unpark: unparkCommand(r.id), resolve: resolveCommand(r.id) };
    });
    var resolved = pr.filter(function (r) { return r.status === "resolved"; });
    /* open questions and items to read are one list, oldest first (the server sorts; AC1): 3 rows for 2 questions and 1 unread item */
    return { open: rows.map(mk), perms: perms, parked: parked, resolved: resolved,
             openLabel: "Open now (" + rows.concat(perms).length + ")", parkedLabel: "Parked (" + parked.length + ")" };
  }

  /* bannerLines(banner): one line per blocked agent; entries null = herdr did not answer. The lines do not depend on the choice. */
  function bannerLines(b) {
    if (!b || b.entries == null) return { unknown: "status unknown: " + ((b && b.reason) || "herdr not running"), lines: [] };
    return { unknown: null, lines: b.entries.map(function (e) { return { agent: e.agent, pane: e.pane_id || "unknown pane", scope: e.scope }; }) };
  }

  /* copyText(btn): copies btn's data-copy (the text shown next to it) and returns that exact string */
  function copyText(btn) {
    var t = btn.getAttribute("data-copy") || "";
    var done = function () { btn.textContent = "copied"; root.setTimeout(function () { btn.textContent = "copy"; }, 1500); };
    var fallback = function () {
      try {
        var ta = root.document.createElement("textarea");
        ta.value = t; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0";
        root.document.body.appendChild(ta); ta.select(); root.document.execCommand("copy"); root.document.body.removeChild(ta); done();
      } catch (e) { /* nothing more to try */ }
    };
    try {
      if (root.navigator && root.navigator.clipboard && root.navigator.clipboard.writeText) root.navigator.clipboard.writeText(t).then(done, fallback);
      else fallback();
    } catch (e) { fallback(); }
    return t;
  }
  BOARD.answerCommand = answerCommand; BOARD.parkCommand = parkCommand; BOARD.unparkCommand = unparkCommand; BOARD.resolveCommand = resolveCommand;
  BOARD.rowsForInbox = rowsForInbox; BOARD.bannerLines = bannerLines; BOARD.copyText = copyText;

  /* ---------- drawing ---------- */
  function el(tag, cls, text) {
    var e = root.document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function css() {
    if (root.document.getElementById("inbox-css")) return;
    var s = el("style");
    s.id = "inbox-css";
    s.textContent =
      ".chip.work{background:var(--t-work);border-color:var(--work)}.chip.idle{background:var(--t-idle);border-color:var(--muted2);color:var(--muted)}" +
      ".chip.park{border:1px dashed var(--muted);color:var(--muted)}.chip{align-items:center;justify-content:center;line-height:1;height:1.65em;box-sizing:border-box}" +
      ".banner{margin:6px var(--gutter) 0;border:1px solid var(--t-edge);border-left:5px solid var(--mango);background:var(--t-need2);border-radius:8px;padding:6px 12px}" +
      ".banner.unk{border-left:4px dashed var(--muted);background:var(--bg)}.banner .t{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}" +
      ".banner .t+.t{margin-top:3px}.banner .hint{color:var(--muted)}" +
      ".nb-out{border:1px solid var(--t-edge);background:var(--t-need3);border-radius:6px;padding:5px 9px;margin:4px 0}" +
      ".nb-items{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:6px}" +
      ".nb-item{background:var(--bg);border:1px solid var(--border);border-left:5px solid var(--mango);border-radius:8px;padding:5px 9px}" +
      ".nb-item.read{border-left-color:var(--border)}.nb-item.parked{border:1px dashed var(--muted2);border-left:5px solid var(--muted2)}" +
      ".nb-item .top{display:flex;gap:6px;align-items:baseline;flex-wrap:wrap}.nb-item .age{margin-left:auto;font-weight:700;white-space:nowrap}" +
      ".nb-item .blocks{color:var(--muted)}.nb-item.parked .blocks{color:var(--ink)}" +
      ".nb-opts{list-style:none;margin:3px 0;padding:0;display:flex;flex-direction:column;gap:2px}" +
      ".nb-opts li{padding:1px 7px;border-radius:6px}.nb-opts li.rec{background:var(--t-need3);outline:1px solid var(--t-edge)}" +
      ".recmark{font-size:.875em;font-weight:700;margin-left:4px;background:var(--t-need);border:1px solid var(--t-edge);border-radius:8px;padding:0 6px;white-space:nowrap}" +
      ".nb-how{display:flex;gap:6px;align-items:center;flex-wrap:wrap;color:var(--muted)}.nb-how+.nb-how{margin-top:2px}" +
      ".cp{border:1px solid var(--border);background:var(--bg);border-radius:5px;padding:0 6px;font-size:.92em}.cp:hover{border-color:var(--mango)}" +
      "h3.nb-sec{font-size:.875em;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin:8px 0 3px;display:flex;gap:6px;align-items:baseline;flex-wrap:wrap}" +
      "h3.nb-sec:first-child{margin-top:2px}h3.nb-sec .t{text-transform:none;letter-spacing:0;font-weight:400}" +
      ".nb-empty{border:1px dashed var(--border);border-radius:8px;padding:10px;margin:4px 0;color:var(--muted);text-align:center;background:var(--bg)}.nb-empty b{color:var(--ink)}" +
      ".nb-more{margin-top:6px;color:var(--muted)}.nb-more summary{cursor:pointer}";
    root.document.head.appendChild(s);
  }
  function chip(cls, text) { return el("span", "chip " + cls, text); }

  function cmdRow(label, text) {
    var h = el("div", "nb-how");
    h.appendChild(el("span", null, label));
    h.appendChild(el("code", null, text));
    var b = el("button", "cp", "copy"); b.type = "button"; b.setAttribute("data-copy", text);
    b.title = "Copies the text on its left. The board never runs it.";
    b.addEventListener("click", function () { copyText(b); });
    h.appendChild(b);
    return h;
  }

  function openItem(r, multi) {
    var kindWord = r.read ? "read" : "open";
    var li = el("li", "nb-item" + (r.read ? " read" : ""));
    li.dataset.id = r.id;
    var top = el("div", "top");
    top.appendChild(chip(r.read ? "idle" : "need", r.id + (r.read ? " answered" : "")));
    top.appendChild(el("b", null, r.title));
    if (multi && r.scope) top.appendChild(chip("idle", r.scope));
    top.appendChild(el("span", "age", r.age));
    li.appendChild(top);
    if (r.blocks) li.appendChild(el("p", "blocks", "Blocks: " + r.blocks));
    if (r.options.length) {
      var ul = el("ul", "nb-opts");
      r.options.forEach(function (o) {
        var oi = el("li", o.recommended ? "rec" : "");
        oi.appendChild(el("b", null, String(o.key).toUpperCase()));
        oi.appendChild(root.document.createTextNode(" " + o.text));
        if (o.recommended) oi.appendChild(el("span", "recmark", o.word));
        ul.appendChild(oi);
      });
      li.appendChild(ul);
    }
    if (kindWord !== "read") {
      li.appendChild(cmdRow("Answer:", r.answer));
      li.appendChild(cmdRow("Park it for later:", r.park));
    }
    return li;
  }

  function permItem(l) {
    var li = el("li", "nb-item");
    var top = el("div", "top");
    top.appendChild(chip("need", "permission")); top.appendChild(el("b", null, l.agent)); top.appendChild(el("span", "muted", "pane " + l.pane));
    li.appendChild(top);
    li.appendChild(el("p", "blocks", "Answer in the pane of this agent. A message cannot approve it, and it cannot be parked."));
    return li;
  }

  function parkedItem(q) {
    var li = el("li", "nb-item parked");
    li.dataset.id = q.id;
    var top = el("div", "top");
    top.appendChild(chip("idle", q.level === "squad" ? "squad" : q.level + " · " + q.scope));
    top.appendChild(el("b", null, q.text));
    top.appendChild(el("span", "age", q.id));
    li.appendChild(top);
    var bl = el("p", "blocks");
    if (q.blocks) { bl.appendChild(el("b", null, "Still blocks: ")); bl.appendChild(root.document.createTextNode(q.blocks)); }
    else bl.textContent = "Blocks nothing known.";
    li.appendChild(bl);
    var since = q.parked_iso ? " · parked " + BOARD.fmtDate(q.parked_iso, TZ) + " " + BOARD.fmtTime(q.parked_iso, TZ) : "";
    li.appendChild(el("p", "muted", (q.from ? "From " + q.from : "free question") + since));
    li.appendChild(cmdRow("To bring it back:", q.unpark));
    li.appendChild(cmdRow("To close it:", q.resolve));
    return li;
  }

  var TZ = "UTC";
  function section(h, label, extra) {
    var x = el("h3", "nb-sec", label);
    if (extra) x.appendChild(extra);
    h.appendChild(x);
  }

  function renderBanner(setBanner, banner) {
    var b = bannerLines(banner);
    if (b.unknown) {
      var u = el("div", "banner unk"); u.setAttribute("role", "alert");
      u.appendChild(el("b", null, b.unknown));
      u.appendChild(el("span", "hint", " Permission prompts cannot be listed, so there is no banner. This is not \"no prompt\"."));
      setBanner(u);
      return;
    }
    if (!b.lines.length) { setBanner(null); return; }
    var box = el("div", "banner"); box.setAttribute("role", "alert");
    b.lines.forEach(function (l) {
      var t = el("div", "t");
      t.appendChild(chip("need", "permission prompt"));
      t.appendChild(el("b", null, l.agent));
      t.appendChild(el("span", "muted", "pane " + l.pane));
      if (l.scope) t.appendChild(el("span", "muted", "· " + l.scope));
      t.appendChild(el("span", "hint", "waits for you"));
      box.appendChild(t);
    });
    box.appendChild(el("div", "muted", "Open that pane and answer there; a message cannot approve it. This banner ignores the choice and leaves when the prompt is answered."));
    setBanner(box);
  }

  function render(body, d, c) {
    css(); TZ = c.tz;
    renderBanner(c.setBanner, d.banner);
    c.setCount(typeof d.count_choice === "number" ? d.count_choice : 0, d.count_choice > 0);
    if (d.status === "unknown") {
      var p = el("p", "note"); p.appendChild(el("b", null, "unknown: squad-inbox did not answer."));
      p.appendChild(root.document.createTextNode(" This is not \"all good\". Open the inbox by hand: "));
      p.appendChild(el("code", null, "squad-inbox list"));
      body.appendChild(p);
    }
    var ch = BOARD.ctx && BOARD.ctx.state.choice;
    if (ch && d.status !== "unknown") {
      var prev = JSON.stringify(BOARD.inboxOthers || null);
      BOARD.inboxOthers = { key: ch.kind + ":" + ch.name, others: d.others || [] };
      if (JSON.stringify(BOARD.inboxOthers) !== prev && BOARD.ctx.paint) BOARD.ctx.paint();   /* repaint the top line from the same data */
    }
    var R = rowsForInbox(d), multi = !!(d.rows || []).some(function (r) { return r.scope !== d.rows[0].scope; });
    var others = d.others || [];
    if (others.length) {
      var o = el("p", "nb-out");
      var items = others.reduce(function (a, x) { return a + (x.n || 0); }, 0);
      o.appendChild(el("b", null, items + " more " + (items === 1 ? "item needs" : "items need") + " you in other goals and scopes: "));
      others.forEach(function (x) {
        var b = el("button", "cp", x.scope + " · " + x.n); b.type = "button"; b.title = "Look at " + x.scope;
        b.addEventListener("click", function () {
          var sq = BOARD.ctx && BOARD.ctx.state.squad;
          if (BOARD.ctx && sq) BOARD.ctx.setChoice(((sq.goals || []).indexOf(x.scope) >= 0 ? "goal:" : "scope:") + x.scope);   /* the squad folder itself is not a choice */
        });
        o.appendChild(b); o.appendChild(root.document.createTextNode(" "));
      });
      var pk = el("button", "cp", "Open the picker"); pk.type = "button";
      pk.addEventListener("click", function () { var b = root.document.getElementById("selbtn"); if (b) b.click(); });
      o.appendChild(pk);
      body.appendChild(o);
    }
    var shown = R.open.concat(R.perms).length;
    if (d.status !== "unknown" && !shown && !(d.count_choice > 0)) {
      var e = el("div", "nb-empty"); e.appendChild(el("b", null, "Nothing needs you"));
      e.appendChild(el("p", null, "No open question, no answer to read, no permission prompt."));
      body.appendChild(e);
    } else {
      section(body, R.openLabel);
      if (shown) {
        var ol = el("ol", "nb-items");
        R.perms.forEach(function (l) { ol.appendChild(permItem(l)); });
        R.open.forEach(function (r) { ol.appendChild(openItem(r, multi)); });
        body.appendChild(ol);
      } else body.appendChild(el("p", "muted", "No open question here. The count also holds passed branches: see Tasks."));
      if (shown && d.count_choice > shown) body.appendChild(el("p", "muted", "The count of " + d.count_choice + " also holds " + (d.count_choice - shown) + " passed branch" + (d.count_choice - shown === 1 ? "" : "es") + ": see Tasks."));
    }
    section(body, R.parkedLabel, chip("park", "not counted in the tab title"));
    if (R.parked.length) { var pl = el("ol", "nb-items"); R.parked.forEach(function (q) { pl.appendChild(parkedItem(q)); }); body.appendChild(pl); }
    else body.appendChild(el("p", "muted", "Nothing parked."));
    (d.parked_warnings || []).forEach(function (w) { body.appendChild(el("p", "note", w)); });
    if (R.resolved.length) {
      var det = el("details", "nb-more"); det.appendChild(el("summary", null, "Resolved (" + R.resolved.length + ")"));
      var rl = el("ul", "nb-items");
      R.resolved.forEach(function (q) {
        var li = el("li", "nb-item read");
        var s = el("s", "muted", q.text); li.appendChild(s);
        var a = el("div", null, "Answer: "); a.appendChild(el("b", null, q.answer || "(none)")); li.appendChild(a);
        rl.appendChild(li);
      });
      det.appendChild(rl); body.appendChild(det);
    }
  }

  BOARD.registerPanel({
    id: "inbox", title: "Needs you", route: "/api/inbox", span: 4, spans: [4, 6, 8], maxPx: 720,
    isEmpty: function (d) { return !d; },
    render: render
  });
})(typeof window !== "undefined" ? window : this);
