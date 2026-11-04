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
