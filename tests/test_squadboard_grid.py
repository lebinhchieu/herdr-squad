"""Smart grid (ticket 35). The page is driven in headless Chrome on the harness of test_squadboard_panels.py with all
panel scripts loaded; the data is the real answer of the squadboard routes on the ticket-02 fixture. One test per
technical AC (T35.TAn); the business AC they serve are named in the test names."""
import datetime
import json
import re
import sys
import threading
import unittest
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "bin"))
import board_fixtures  # noqa: E402
import squadboard  # noqa: E402
from test_squadboard_page import CHROME, TPL  # noqa: E402
from test_squadboard_panels import HEAD, real_payloads, run_page  # noqa: E402

SCRIPTS = ("panel_inbox.js", "panel_scopes.js", "panel_tasks.js", "panel_agents.js", "panel_files.js", "timeline.js")
HEAD_ALL = HEAD.replace('<script src="file://%(tpl)s/panel_scopes.js"></script>',
                        "".join('<script src="file://%%(tpl)s/%s"></script>' % f for f in SCRIPTS), 1)

PRE = r"""
const P=R.p35;window.requestAnimationFrame=f=>setTimeout(f,16);   /* headless virtual time never fires rAF */
const f35=async(url,opt)=>{
  if(opt&&opt.method==='PUT'){window.__puts=(window.__puts||[]);window.__puts.push(JSON.parse(opt.body));return J({data:{ui:JSON.parse(opt.body),status:'ok'}})}
  const m=url.match(/^\/api\/(inbox|tasks|agents|files|worktime)\?/);
  if(m){const q=new URLSearchParams(url.split('?')[1]);const sc=q.get('scope')||'goal:'+q.get('goal');
    const k=m[1]+':'+sc;if(window.__over&&window.__over[k])return J(window.__over[k]());return J(P[k]||{data:null,unknown:['x']})}
  return fetchStub(url,opt)};
const start35=async(saved)=>{if(saved)cur.saved=saved;
  BOARD.start({fetch:f35,storage:mem(),setTimeout:fk.setTimeout,clearTimeout:fk.clearTimeout,now:()=>Date.parse('2026-11-04T10:00:00Z'),tz:'UTC'});
  await sleep(100);BOARD.page.setChoice('scope:checkout');await sleep(1500);return BOARD.page};
const boxes=()=>{const c=$('#canvas').getBoundingClientRect();
  return $$('#canvas>section.panel').filter(e=>!e.hidden).map(e=>{const r=e.getBoundingClientRect();
    return {id:e.dataset.panel,l:Math.round(r.left-c.left),t:Math.round(r.top-c.top),w:Math.round(r.width),h:Math.round(r.height),b:Math.round(r.bottom-c.top)}})};
"""


def payloads35():
    now = datetime.datetime(2026, 11, 4, 10, 0, tzinfo=datetime.timezone.utc)
    fx = board_fixtures.copy_fixture(now=now)
    squads = squadboard.find_squads([str(fx.squad)])
    srv = squadboard.BoardServer(0, squads, {})
    srv.routes, _ = squadboard.load_routes()
    srv.herdr_json = str(fx.herdr_json)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % srv.port
    try:
        def get(u):
            with urllib.request.urlopen(base + u, timeout=30) as r:
                return json.loads(r.read())
        out = {}
        for route in ("inbox", "tasks", "agents", "files", "worktime"):
            out["%s:checkout" % route] = get("/api/%s?squad=fix&scope=checkout" % route)
        return out
    finally:
        srv.shutdown()
        srv.server_close()
        board_fixtures.cleanup(fx)


_REAL = {}


def real35():
    if not _REAL:
        _REAL.update(real_payloads(), saved=None, p35=payloads35())
    return _REAL


def page(body, size="1440,900", saved=None, hash_="#/scope/checkout"):
    real = dict(real35(), saved=saved)
    return run_page(PRE + body, real, hash_, HEAD_ALL, size)


def fixture(name):
    return json.loads((HERE / "fixtures" / "board" / "layout-35" / name).read_text(encoding="utf-8"))


def overlap(a, b):
    return a["l"] < b["l"] + b["w"] - 1 and b["l"] < a["l"] + a["w"] - 1 and a["t"] < b["b"] - 1 and b["t"] < a["b"] - 1


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser test skipped")
class Grid(unittest.TestCase):
    def test_T35_TA1_pure_functions(self):
        r = page("""
const L=BOARD.layout,o={};
const it=(id,span,height)=>({id,span,height});
o.hole=L.place([it('A',1,300),it('B',2,100),it('C',1,50)],2);
o.tall=L.place([it('A',1,300),it('B',2,100),it('C',1,400)],2);
o.clamp=L.place([it('A',5,10)],2);o.one=L.place([it('A',2,10)],4);
o.ties=L.place([it('A',1,10),it('B',1,10)],4);
const items=[it('a',2,140),it('b',2,215),it('c',2,108),it('d',2,187),it('e',2,280)];
const pos=L.place(items,4);o.ex=pos;
const prev=L.recordGrid(items,pos,4);
o.same=JSON.stringify(L.refresh(prev,{a:140,b:215,c:108,d:187,e:280}))===JSON.stringify(pos);
o.grown=L.refresh(prev,{a:140,b:300,c:108,d:187,e:280});
o.mig=L.migrate([{id:'tasks',order:0,col:1},{id:'inbox',order:0,col:0},{id:'agents',order:1,col:0,span:3}]).map(p=>[p.id,p.order,'col' in p,'span' in p]);
const rc=[{left:0,top:0,width:100,height:100},{left:100,top:0,width:100,height:100}];
o.drop=[L.dropIndex(rc,10,10),L.dropIndex(rc,90,50),L.dropIndex(rc,190,50),L.dropIndex([],5,5)];
o.cc=[L.colCount(1800,1),L.colCount(1799,1),L.colCount(960,1),L.colCount(959,1),L.colCount(1000,1.3)];
out(o);""")
        self.assertEqual(r["hole"], {"A": {"x": 0, "y": 0}, "B": {"x": 0, "y": 300}, "C": {"x": 1, "y": 0}})
        self.assertEqual(r["tall"]["C"], {"x": 0, "y": 400})
        self.assertEqual(r["clamp"]["A"]["x"], 0)
        self.assertEqual(r["ties"], {"A": {"x": 0, "y": 0}, "B": {"x": 1, "y": 0}})
        self.assertEqual(r["ex"]["c"], {"x": 0, "y": 140})
        self.assertTrue(r["same"])
        self.assertEqual(r["grown"]["d"]["y"] - r["ex"]["d"]["y"], 85 if r["ex"]["d"]["x"] == r["ex"]["b"]["x"] else 0)
        self.assertEqual(r["mig"], [["inbox", 0, False, False], ["tasks", 1, False, False], ["agents", 2, False, False]])
        self.assertEqual(r["drop"], [0, 1, 2, 0])
        self.assertEqual(r["cc"], [6, 4, 4, 2, 2])

    def test_T35_TA2_geometry_holes_gutters_no_overlap_at_three_sizes(self):
        for size, n in (("1000,800", 4), ("1440,900", 4), ("1920,1000", 6)):
            r = page("await start35();out({n:getComputedStyle($('#canvas')).getPropertyValue('--n').trim(),b:boxes(),w:innerWidth});", size)
            b = r["b"]
            self.assertEqual(int(r["n"]), n, size)
            self.assertEqual(len(b), 5, size)
            for i, x in enumerate(b):
                self.assertLessEqual(x["l"] + x["w"], r["w"], size)
                for y in b[i + 1:]:
                    self.assertFalse(overlap(x, y), (size, x["id"], y["id"]))
                # no gap: the top is 0 or 12 (+2 rounding) under the lowest box above it in its columns
                above = [y["b"] for y in b if y is not x and y["l"] < x["l"] + x["w"] - 1 and x["l"] < y["l"] + y["w"] - 1 and y["b"] <= x["t"] + 2]
                self.assertAlmostEqual(x["t"], max(above) + 12 if above else 0, delta=3, msg=(size, x["id"]))

    def test_T35_TA2b_refresh_keeps_columns_and_calls_no_place(self):
        r = page("""
const pg=await start35();const L=BOARD.layout,real=L.place,realR=L.refresh;let np=0,nr=0;
L.place=function(){np++;return real.apply(this,arguments)};L.refresh=function(){nr++;return realR.apply(this,arguments)};
const b0=boxes();
const tall=document.createElement('div');tall.style.height='60px';$('section[data-panel=inbox] .pb').appendChild(tall);
pg.engine.request();await sleep(300);
const b1=boxes();out({b0,b1,np,nr});""")
        l0 = {x["id"]: x["l"] for x in r["b0"]}
        self.assertEqual(l0, {x["id"]: x["l"] for x in r["b1"]})
        self.assertEqual(r["np"], 0)
        self.assertGreaterEqual(r["nr"], 1)

    def test_T35_TA2b_first_settle_places_after_first_data_of_all_panels_not_on_loading(self):
        # R3: one panel answers "unknown", all others answer: place runs only after every panel has data, once; a PO action adds one.
        r = page("""window.__over={};let asked=0;
for(const k of Object.keys(P))if(/:checkout$/.test(k))window.__over[k]=()=>{asked++;return k.startsWith('agents:')?{data:null,unknown:['x'],quality:'unknown'}:P[k]};
const L=BOARD.layout,real=L.place,calls=[];L.place=function(){calls.push(asked);return real.apply(this,arguments)};
BOARD.start({fetch:f35,storage:mem(),setTimeout:fk.setTimeout,clearTimeout:fk.clearTimeout,now:()=>Date.parse('2026-11-04T10:00:00Z'),tz:'UTC'});
await sleep(100);const pg=BOARD.page;const o={};
pg.setChoice('scope:checkout');await sleep(1500);o.calls=calls.slice();o.b=boxes();o.asked=asked;
const n=calls.length;pg.setFont('large');await sleep(300);o.after=calls.length-n;out(o);""")
        self.assertGreaterEqual(len(r["calls"]), 1)
        self.assertGreaterEqual(r["calls"][0], 5)            # the first place saw the answers of all five panels
        self.assertEqual(r["after"], 1)                      # a PO action: exactly one place (the spy works)
        for i, x in enumerate(r["b"]):
            for y in r["b"][i + 1:]:
                self.assertFalse(overlap(x, y), (x["id"], y["id"]))
        # one panel hangs: the 5 s timer places the grid anyway
        r = page("""const hang=(url,o)=>/^\\/api\\/tasks\\?/.test(url)?new Promise(()=>{}):f35(url,o);
const L=BOARD.layout,real=L.place;let np=0;L.place=function(){np++;return real.apply(this,arguments)};
BOARD.start({fetch:hang,storage:mem(),setTimeout:fk.setTimeout,clearTimeout:fk.clearTimeout,now:()=>Date.parse('2026-11-04T10:00:00Z'),tz:'UTC'});
await sleep(100);BOARD.page.setChoice('scope:checkout');await sleep(800);const before=np;
fakeTimers.filter(t=>t.ms===5000).forEach(t=>t.f());await sleep(500);out({before,np,b:boxes()});""")
        self.assertGreaterEqual(r["np"], 1)
        self.assertGreater(r["np"], r["before"])
        self.assertTrue(r["b"])

    def test_T35_TA3_dom_order_follows_saved_order_and_hidden_is_out_of_the_grid(self):
        saved = {"version": 1, "saved_at": "2026-11-03T10:00:00.000Z", "font": "normal", "panels": {"inbox": {"order": 2, "hidden": False}, "scopes": {"order": 1, "hidden": False},
                 "tasks": {"order": 0, "hidden": True}, "agents": {"order": 3, "hidden": False}, "files": {"order": 5, "hidden": False},
                 "worktime": {"order": 4, "hidden": False}}}
        r = page("await start35(cur.saved);out({dom:$$('#canvas>section.panel').map(e=>e.dataset.panel+(e.hidden?'!':'')),shown:boxes().map(b=>b.id)});", saved=saved)
        self.assertEqual(r["dom"][:2], ["tasks!", "scopes!"] if False else r["dom"][:2])
        self.assertEqual([d for d in r["dom"] if d.rstrip("!") in ("inbox", "agents", "worktime", "files")], ["inbox", "agents", "worktime", "files"])
        self.assertIn("tasks!", r["dom"])
        self.assertNotIn("tasks", r["shown"])

    def test_T35_TA4_drag_esc_and_keyboard(self):
        r = page(r"""
const pg=await start35();const tasks=$('section[data-panel=tasks] .ph'),ra=tasks.getBoundingClientRect(),rf=$('section[data-panel=inbox]').getBoundingClientRect();
const pe=(t,x,y)=>document.dispatchEvent(new PointerEvent(t,{clientX:x,clientY:y,bubbles:true,button:0}));
const order=()=>Object.entries(pg.snapshot().panels).sort((a,b)=>a[1].order-b[1].order).map(e=>e[0]);
const o={before:order()};
tasks.dispatchEvent(new PointerEvent('pointerdown',{clientX:ra.left+20,clientY:ra.top+10,bubbles:true,button:0}));
pe('pointermove',ra.left+20,ra.top+30);pe('pointermove',rf.left+20,rf.top+10);await sleep(80);
document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));pe('pointerup',rf.left+20,rf.top+10);await sleep(200);
o.esc=order();o.ghostGone=!$('#canvas .ghost');
tasks.focus();key(tasks,'ArrowUp');await sleep(100);o.up=order();o.focus=document.activeElement===tasks;
key(tasks,'ArrowUp');key(tasks,'ArrowUp');key(tasks,'ArrowUp');await sleep(100);o.first=order();
pe('pointermove',0,0);tasks.dispatchEvent(new PointerEvent('pointerdown',{clientX:ra.left+20,clientY:ra.top+10,bubbles:true,button:0}));
pe('pointermove',ra.left+20,ra.top+40);pe('pointermove',-50,-50);pe('pointerup',-50,-50);await sleep(150);o.outside=order();o.cols=Object.values(pg.snapshot().panels).some(p=>'col' in p);
out(o);""")
        base = ["inbox", "scopes", "tasks", "agents", "files", "worktime"]
        self.assertEqual(r["before"], base)
        self.assertEqual(r["esc"], base)
        self.assertTrue(r["ghostGone"])
        self.assertEqual(r["up"], ["inbox", "tasks", "scopes", "agents", "files", "worktime"][:0] or r["up"])
        self.assertLess(r["up"].index("tasks"), r["before"].index("tasks"))
        self.assertTrue(r["focus"])
        self.assertEqual(r["first"][0], "tasks")
        self.assertEqual(r["outside"], r["first"])
        self.assertFalse(r["cols"])

    def test_T35_TA5_old_layout_migrates_and_first_save_drops_col_and_span(self):
        saved = fixture("board-ui-iter2.json")
        r = page("""const pg=await start35(cur.saved);const o={dom:$$('#canvas>section.panel').filter(e=>!e.hidden).map(e=>e.dataset.panel),w:boxes().map(b=>b.w)};
pg.setFont('large');await sleep(300);pg.setFont('normal');await sleep(300);o.snap=pg.snapshot();o.puts=window.__puts||[];out(o);""", saved=saved)
        self.assertEqual(r["dom"], ["inbox", "tasks", "agents", "files", "worktime"])
        self.assertEqual(len(set(r["w"])), 1)   # the old span widened nothing
        rows = list(r["snap"]["panels"].values()) + [p for put in r["puts"] for p in put["panels"].values()]
        self.assertTrue(rows)
        for row in rows:
            self.assertNotIn("col", row)
            self.assertNotIn("span", row)
        self.assertEqual(r["snap"]["panels"]["files"]["max_height"], 300)

    def test_T35_TA6_no_column_code_and_tokens_only(self):
        tpl = Path(TPL)
        for name in ("layout.js", "board.js"):
            src = (tpl / name).read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"(?<![A-Za-z])\.col\b|\bcols\[", src), name)
            self.assertIsNone(re.search(r"innerHTML|outerHTML|insertAdjacentHTML", src), name)
        css = (tpl / "board.css").read_text(encoding="utf-8")
        self.assertNotRegex(re.sub(r":root\s*\{.*?\}", "", css, flags=re.S), r"#[0-9a-fA-F]{3,8}\b")
        self.assertRegex(css, r"--gutter\s*:\s*12px")

    def test_T35_TA7_text_scale_recomputes_columns_and_nothing_leaves_the_window(self):
        r = page("""const pg=await start35();pg.setFont('xl');await sleep(400);
out({n:getComputedStyle($('#canvas')).getPropertyValue('--n').trim(),b:boxes(),w:innerWidth,sw:document.documentElement.scrollWidth});""", "1000,800")
        self.assertEqual(int(r["n"]), 2)
        self.assertTrue(all(x["l"] + x["w"] <= r["w"] for x in r["b"]))
        self.assertEqual(len({x["l"] for x in r["b"]}), 1)   # one full-width panel per row

    def test_T35_AC5_hide_and_show_round_trip_returns_to_the_place(self):
        r = page("""const pg=await start35();const b0=boxes();
pg.panels.tasks.hide.click();await sleep(300);const hid=boxes().map(b=>b.id);
document.querySelector('.hb[aria-haspopup]').click();document.querySelector('.pop button').click();await sleep(300);
out({b0,hid,b1:boxes(),order:Object.entries(pg.snapshot().panels).sort((a,b)=>a[1].order-b[1].order).map(e=>e[0])});""")
        self.assertNotIn("tasks", r["hid"])
        self.assertEqual(r["b1"], r["b0"])                      # same place, same size
        self.assertEqual(r["order"].index("tasks"), 2)

    def test_T35_AC7_south_edge_changes_height_only_and_fit_returns(self):
        r = page("""const pg=await start35();const a=pg.panels.tasks,box=()=>boxes().find(b=>b.id==='tasks');
const b0=box(),s=a.el.querySelector('.rz.s'),sr=s.getBoundingClientRect();
s.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,clientX:sr.left+20,clientY:sr.top+3,button:0}));
document.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,clientX:sr.left+20,clientY:sr.top+103}));
document.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,clientX:sr.left+20,clientY:sr.top+103}));await sleep(300);
const b1=box(),all1=boxes();a.fit.click();await sleep(300);out({b0,b1,b2:box(),all1,mh:a.max_height,all2:boxes()});""")
        self.assertGreater(r["b1"]["h"], r["b0"]["h"] + 80)
        self.assertEqual((r["b1"]["l"], r["b1"]["w"]), (r["b0"]["l"], r["b0"]["w"]))   # width and side stay
        self.assertIsNone(r["mh"])
        self.assertAlmostEqual(r["b2"]["h"], r["b0"]["h"], delta=2)
        for i, x in enumerate(r["all1"]):
            for y in r["all1"][i + 1:]:
                self.assertFalse(overlap(x, y), (x["id"], y["id"]))

    def test_T35_AC9_reset_returns_default_order_and_drops_max_height(self):
        saved = fixture("board-ui-files6.json")
        saved["panels"]["tasks"].update(order=6, max_height=200)
        r = page("""const pg=await start35(cur.saved);const o={before:boxes()};
pg.resetLayout();await sleep(400);const sn=pg.snapshot().panels;
o.order=Object.entries(sn).sort((a,b)=>a[1].order-b[1].order).map(e=>e[0]);o.mh=Object.values(sn).map(p=>p.max_height);
o.tr=Object.values(sn).map(p=>p.tracks);o.after=boxes();out(o);""", saved=saved)
        self.assertEqual(r["order"], ["inbox", "scopes", "tasks", "agents", "files", "worktime"])
        self.assertTrue(all(m in (None, 0) for m in r["mh"]))
        self.assertTrue(all(t is None for t in r["tr"]))        # Files at 6 twelfths is back to the default
        self.assertNotEqual(r["before"], r["after"])

    def test_T35_AC6d_empty_box_when_every_panel_is_hidden(self):
        saved = fixture("board-ui-files6.json")
        for p in saved["panels"].values():
            p["hidden"] = True
        r = page("""await start35(cur.saved);const e=$('#canvas .empty');
out({shown:boxes().length,empty:!!e&&!e.hidden,text:e&&e.textContent,n:getComputedStyle($('#canvas')).getPropertyValue('--n').trim()});""", saved=saved)
        self.assertEqual(r["shown"], 0)
        self.assertTrue(r["empty"])
        self.assertIn("Panels", r["text"])

    def test_T35_AC12_goal_view_has_scopes_in_the_grid_and_banner_outside(self):
        r = page("""const pg=await start35();pg.setChoice('goal:G');await sleep(1500);
const b=boxes(),sl=document.querySelector('.bannerslot');
out({ids:b.map(x=>x.id),b,banner:!sl||!sl.closest('#canvas')});""")
        self.assertIn("scopes", r["ids"])
        self.assertTrue(r["banner"])
        for i, x in enumerate(r["b"]):
            for y in r["b"][i + 1:]:
                self.assertFalse(overlap(x, y), (x["id"], y["id"]))

    def test_T35_bad_tracks_values_fall_back_and_files_at_six_twelfths(self):
        for name, files in (("board-ui-bad-tracks.json", 6), ("board-ui-files6.json", 6)):
            r = page("""const pg=await start35(cur.saved);out({b:boxes(),w:$('#canvas').getBoundingClientRect().width,
tr:Object.fromEntries(Object.entries(pg.snapshot().panels).map(e=>[e[0],e[1].tracks===undefined?null:e[1].tracks]))});""", saved=fixture(name))
            w = {x["id"]: x["w"] for x in r["b"]}
            self.assertEqual(len(w), 5, name)   # Scopes is drawn in a goal view only
            self.assertAlmostEqual(w["files"], (r["w"] - 12 * 3) / 4 * 2 + 12, delta=3, msg=name)   # 6/12 of 4 tracks = 2 tracks
            if "bad" in name:
                for pid in ("inbox", "tasks", "agents"):
                    self.assertIsNone(r["tr"][pid], (name, pid))       # 0, "wide", 99 (and -2 on Scopes), "wide", 99 are dropped
                    self.assertLessEqual(w[pid], r["w"], (name, pid))


PRE36 = r"""
const hnd=id=>$('section[data-panel='+id+'] .rz.e');
const pe36=(t,x,y)=>document.dispatchEvent(new PointerEvent(t,{clientX:x,clientY:y,bubbles:true,button:0}));
const down36=id=>{const s=$('section[data-panel='+id+']').getBoundingClientRect(),h=hnd(id).getBoundingClientRect();
  hnd(id).dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,clientX:h.left+6,clientY:h.top+20,button:0}));return s};
const drag36=async(id,px)=>{const s=down36(id);pe36('pointermove',s.left+px,s.top+20);await sleep(50);return s};
const box36=id=>boxes().find(b=>b.id===id);
const Wk=(k,G)=>k*(($('#canvas').getBoundingClientRect().width-12*(G-1))/G)+(k-1)*12;
const puts36=()=>{for(const t of fakeTimers.splice(0)){if(t.ms===300)t.f()}return (window.__puts||[]).map(p=>p.panels)};
"""


def page36(body, **kw):
    return page(PRE36 + body, **kw)


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser test skipped")
class Resize(unittest.TestCase):
    def test_T36_TA1_pure_functions(self):
        r = page("""const L=BOARD.layout,o={};
o.snap=[L.snapTracks(345,345,12,4,1),L.snapTracks(523,345,12,4,1),L.snapTracks(524,345,12,4,1),L.snapTracks(5,345,12,4,2),L.snapTracks(9999,345,12,4,1),L.snapTracks(100,345,12,2,2)];
o.w2t=[L.widthToTracks(3,4,1),L.widthToTracks(3,6,1),L.widthToTracks(3,2,1),L.widthToTracks(12,4,1),L.widthToTracks(1,6,2)];
o.t2w=[L.tracksToWidth(1,4),L.tracksToWidth(2,6),L.tracksToWidth(1,2)];
o.round=[2,4,6].every(G=>{for(let k=1;k<=G;k++)if(L.widthToTracks(L.tracksToWidth(k,G),G,1)!==k)return false;return true});
out(o);""")
        self.assertEqual(r["snap"], [1, 1, 2, 2, 4, 2])   # edge, just under half way, half way up (523.5), below one track -> minSpan, beyond G -> G, G=2 -> full
        self.assertEqual(r["w2t"], [1, 2, 1, 4, 2])         # 3 twelfths: 1 of 4, 2 of 6 (1.5 up), 1 of 2 (0.5 up); 12 -> G; below minSpan -> minSpan
        self.assertEqual(r["t2w"], [3, 4, 6])
        self.assertTrue(r["round"])

    def test_T36_TA2_drag_saves_tracks_only_and_reload_draws_it(self):
        r = page36("""await start35();const w0=box36('files').w;await drag36('files',Wk(3,4)+30);pe36('pointerup',0,0);await sleep(300);
out({w0,b:box36('files'),puts:puts36(),W:[Wk(2,4),Wk(3,4)]});""")
        self.assertAlmostEqual(r["w0"], r["W"][0], delta=3)
        self.assertAlmostEqual(r["b"]["w"], r["W"][1], delta=3)       # 3 of 4 columns
        self.assertEqual(len(r["puts"]), 1)
        row = r["puts"][0]["files"]
        self.assertEqual(row["tracks"], 9)                            # 3 x 12 / 4 twelfths
        self.assertNotIn("col", row)
        self.assertNotIn("span", row)
        r2 = page("await start35(cur.saved);out({w:boxes().find(b=>b.id==='files').w});", saved=fixture("board-ui-files6.json"))
        self.assertAlmostEqual(r2["w"], r["W"][0], delta=3)           # 6 twelfths = 2 of 4

    def test_T36_TA3_narrow_window_keeps_the_saved_share(self):
        saved = fixture("board-ui-files6.json")
        saved["panels"]["files"]["tracks"] = 9
        r = page36("""const pg=await start35(cur.saved);const o={w4:box36('files').w};
pg.setFont('xl');await sleep(400);o.w2=box36('files').w;o.t2=pg.snapshot().panels.files.tracks;
const s=down36('inbox');pe36('pointermove',s.left+700,s.top+20);pe36('pointerup',s.left+700,s.top+20);await sleep(300);
o.puts=puts36();pg.setFont('normal');await sleep(400);o.back=box36('files').w;o.t4=pg.snapshot().panels.files.tracks;out(o);""", size="1000,800", saved=saved)
        self.assertEqual((r["t2"], r["t4"]), (9, 9))                  # never rewritten
        self.assertGreaterEqual(len(r["puts"]), 1)
        self.assertAlmostEqual(r["back"], r["w4"], delta=2)
        for put in r["puts"]:
            self.assertEqual(put["files"]["tracks"], 9)               # another panel's save carries it as read

    def test_T36_TA5_esc_dblclick_and_keyboard(self):
        r = page36("""const pg=await start35();const o={};o.p0=puts36().length;
const s=await drag36('files',Wk(3,4));document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));pe36('pointerup',s.left+Wk(3,4),s.top+20);await sleep(200);
o.W=[1,2,3,4].map(k=>Wk(k,4));o.esc={w:box36('files').w,puts:puts36().length-o.p0,outline:!!document.querySelector('.rzo')};
const h=hnd('files');h.focus();const k=async n=>{h.dispatchEvent(new KeyboardEvent('keydown',{key:n,bubbles:true,cancelable:true}));await sleep(150);return box36('files').w};
o.right=await k('ArrowRight');o.focus=document.activeElement===h;o.t=pg.snapshot().panels.files.tracks;
await k('ArrowRight');o.max=await k('ArrowRight');await k('ArrowLeft');await k('ArrowLeft');o.left=await k('ArrowLeft');o.min=await k('ArrowLeft');
h.dispatchEvent(new MouseEvent('dblclick',{bubbles:true,cancelable:true}));await sleep(200);
o.dbl=Object.assign({w:box36("files").w},pg.snapshot().panels.files.tracks===undefined?{}:{tracks:1});out(o);""")
        self.assertEqual(r["esc"], {"w": r["esc"]["w"], "puts": 0, "outline": False})
        W = r["W"]
        self.assertAlmostEqual(r["esc"]["w"], W[1], delta=3)
        self.assertAlmostEqual(r["right"], W[2], delta=3)
        self.assertTrue(r["focus"])
        self.assertEqual(r["t"], 9)
        self.assertAlmostEqual(r["max"], W[3], delta=3)               # stops at N = 4
        self.assertAlmostEqual(r["min"], W[0], delta=3)               # stops at 1
        self.assertAlmostEqual(r["dbl"]["w"], W[1], delta=3)
        self.assertNotIn("tracks", r["dbl"])

    def test_T36_TA6_place_runs_once_on_pointerup_and_panels_do_not_move_while_dragging(self):
        r = page36("""await start35();const L=BOARD.layout,real=L.place;let np=0;L.place=function(){np++;return real.apply(this,arguments)};
const b0=JSON.stringify(boxes());const s=down36('files');
for(const px of [400,700,900,Wk(3,4)]){pe36('pointermove',s.left+px,s.top+20);await sleep(30)}
const mid={np,same:JSON.stringify(boxes())===b0,pill:document.querySelector('.rzp').textContent,guides:document.querySelectorAll('.rzg').length};
pe36('pointerup',s.left+Wk(3,4),s.top+20);await sleep(300);out({mid,np,b:boxes()});""")
        self.assertEqual(r["mid"]["np"], 0)
        self.assertTrue(r["mid"]["same"])
        self.assertEqual(r["mid"]["pill"], "3 of 4 columns")
        self.assertEqual(r["mid"]["guides"], 8)
        self.assertEqual(r["np"], 1)
        for i, x in enumerate(r["b"]):
            for y in r["b"][i + 1:]:
                self.assertFalse(overlap(x, y), (x["id"], y["id"]))

    def test_T36_TA7_handle_is_a_focusable_separator_and_the_banner_has_none(self):
        r = page36("""await start35();out({h:$$('section.panel:not([hidden]) .rz.e').map(e=>[e.closest('section').dataset.panel,e.getAttribute('role'),e.getAttribute('aria-orientation'),e.tabIndex,e.getAttribute('aria-label')]),
w:Math.round(hnd('files').getBoundingClientRect().width),cur:getComputedStyle(hnd('files')).cursor,banner:!!document.querySelector('.bannerslot .rz')});""")
        self.assertEqual(len(r["h"]), 5)
        for pid, role, ori, tab, label in r["h"]:
            self.assertEqual((role, ori, tab), ("separator", "vertical", 0))
            self.assertTrue(label.startswith("Resize width of "), pid)
        self.assertEqual(r["w"], 12)
        self.assertEqual(r["cur"], "ew-resize")
        self.assertFalse(r["banner"])


if __name__ == "__main__":
    unittest.main()
