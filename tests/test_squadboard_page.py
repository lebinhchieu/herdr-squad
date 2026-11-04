"""Page shell and layout (ticket 10). Logic is called in headless Chrome on a small harness page that loads the real
templates/board/*.js (pattern of test_squadreport_ui.py); data comes from a real squadboard server on the ticket-02
fixture. Tests are named for the business AC (T10.ACn) or technical AC (T10.TAn) they cover."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "bin"))
import board_fixtures  # noqa: E402
import squadboard  # noqa: E402
import squadboard_ui  # noqa: E402

CHROME = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
TPL = HERE.parent / "templates" / "board"
FILES = ("index.html", "board.css", "board.js", "layout.js")

HEAD = """<!doctype html><meta charset=utf-8>
<link rel=stylesheet href="file://%(tpl)s/board.css">
<div id=app></div><pre id=out></pre>
<script>window.BOARD_NO_AUTOSTART=true;window.__real=%(real)s;</script>
<script src="file://%(tpl)s/board.js"></script><script src="file://%(tpl)s/layout.js"></script>
<script>
const out=v=>{document.getElementById('out').textContent=JSON.stringify(v)};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{try{
%(body)s
}catch(e){out({error:String(e&&e.stack||e)})}})();
</script>
"""


def run_page(body, real=None, width=1440, height=900, hash_=""):
    with tempfile.TemporaryDirectory() as d:
        page = Path(d) / "page.html"
        page.write_text(HEAD % {"tpl": str(TPL), "real": json.dumps(real or {}), "body": body}, encoding="utf-8")
        r = subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--allow-file-access-from-files",
                            "--virtual-time-budget=8000", "--window-size=%d,%d" % (width, height), "--dump-dom",
                            "file://" + str(page) + hash_], capture_output=True, text=True, timeout=90)
    assert r.returncode == 0, r.stderr[-500:]
    m = re.search(r'<pre id="out">(.*?)</pre>', r.stdout, re.S)
    assert m, r.stdout[-800:]
    import html
    res = json.loads(html.unescape(m.group(1)))
    assert "error" not in res, res["error"]
    return res


class Server:
    """A real squadboard server on a copy of the fixture; `get(path)` answers its JSON."""

    def __init__(self):
        self.fx = board_fixtures.copy_fixture(git=False)
        squads = squadboard.find_squads([str(self.fx.squad)])
        self.srv = squadboard.BoardServer(0, squads, squadboard.initial_selection(squads, None, "checkout"), routes={})
        import squadboard_ui as ui
        route = ui.ROUTE
        self.srv.routes = {route["path"]: route}
        self.srv.put_routes = squadboard._collect_put_routes(self.srv.routes)
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.thread.start()
        self.base = "http://127.0.0.1:%d" % self.srv.port

    def get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=10) as r:
            return r.status, r.read()

    def close(self):
        self.srv.shutdown()
        self.srv.server_close()
        board_fixtures.cleanup(self.fx)


STUB = """
const R=window.__real;
const fakeTimers=[];let tid=0;
const fk={setTimeout:(f,ms)=>{fakeTimers.push({id:++tid,f,ms});return tid},clearTimeout:id=>{const i=fakeTimers.findIndex(t=>t.id===id);if(i>=0)fakeTimers.splice(i,1)}};
const mem=()=>{const m={};return{getItem:k=>(k in m?m[k]:null),setItem:(k,v)=>{m[k]=String(v)},_m:m}};
const puts=[];
const mkFetch=(rows,over)=>async(url,opt)=>{
  const j=o=>({ok:true,status:200,json:async()=>Object.assign({schema_version:1,unknown:[],quality:'exact'},o)});
  if(opt&&opt.method==='PUT'){puts.push(JSON.parse(opt.body));return {ok:true,status:200,json:async()=>({schema_version:1,data:{ui:JSON.parse(opt.body),status:'ok'}})}}
  if(over&&over[url.split('?')[0]])return over[url.split('?')[0]](url);
  if(url.startsWith('/api/session'))return j(R.session);
  if(url.startsWith('/api/squads'))return j(R.squads);
  if(url.startsWith('/api/ui'))return j(R.ui);
  const m=url.match(/^\\/api\\/t(\\w+)/);
  if(m)return j({data:{rows:rows[m[1]]},count_squad:undefined});
  return {ok:false,status:404,json:async()=>({schema_version:1,error:'nf'})};
};
const mkPanel=(id,title,n,span,max,spans)=>BOARD.registerPanel({id,title,route:'/api/t'+id,span,maxPx:max,spans,
  render:(body,d,ctx)=>{for(let i=0;i<d.rows;i++){const r=document.createElement('div');r.className='row';r.style.cssText='padding:6px 0;border-bottom:1px solid #E7DBC8';r.textContent=title+' row '+(i+1)+' with some words so that it can wrap in a narrow panel';body.appendChild(r)}ctx.setCount(d.rows,false)}});
"""


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser test skipped")
class PureRules(unittest.TestCase):
    """The rules are plain functions on BOARD: no events, no DOM (UI-COMMON TU.1)."""

    @classmethod
    def setUpClass(cls):
        cls.res = run_page("""
const B=BOARD, L=BOARD.layout, o={};
o.t14={plus7:B.fmtTime('2026-11-03T02:00:00Z','Asia/Bangkok'),off7:B.zoneOffset('2026-11-03T02:00:00Z','Asia/Bangkok'),
  next:B.fmtDate('2026-11-03T23:30:00Z','Asia/Bangkok'),kolkata:B.zoneOffset('2026-11-03T02:00:00Z','Asia/Kolkata'),
  bad:B.zoneOffset('2026-11-03T02:00:00Z','Not/AZone'),badTime:B.fmtTime('2026-11-03T02:00:00Z','Not/AZone'),
  ny1:B.zoneOffset('2026-03-07T12:00:00Z','America/New_York'),ny2:B.zoneOffset('2026-03-09T12:00:00Z','America/New_York'),
  ny3:B.zoneOffset('2026-10-31T12:00:00Z','America/New_York'),ny4:B.zoneOffset('2026-11-02T12:00:00Z','America/New_York'),
  utc:B.zoneOffset('2026-11-03T02:00:00Z','UTC')};
o.t15=[20,59,60,3*3600,3*86400,null,undefined,NaN].map(B.ageWords);
o.title=[B.titleFor('board',3),B.titleFor('board',0),B.titleFor('board',null)];
const a={saved_at:'2026-11-04T10:00:00Z',font:'small'},b={saved_at:'2026-11-04T10:00:05Z',font:'xl'};
o.newer=[B.pickNewer(a,b).font,B.pickNewer(b,a).font,B.pickNewer(null,a).font,B.pickNewer(a,{saved_at:'bad'}).font,B.pickNewer(null,null)];
const P=B.panelView;
o.unk=[P({schema_version:1,data:[],unknown:['inbox']},{id:'inbox'}).kind,P({schema_version:1,data:{rows:[1]},unknown:['x']},{id:'inbox'}).kind,P({schema_version:2,data:{}},{id:'inbox'}).kind];
o.needs=[B.needsFrom([{data:{}},{data:{count_squad:3}}]),B.needsFrom([])];
// layout (ticket 26): colCount, place, norm
const hs={inbox:200,tasks:300,agents:150,files:120,worktime:400},ORD=['inbox','tasks','agents','files','worktime'];
o.cc=[[1440,1],[1800,1],[1799,1],[932,1],[931,1],[1000,1.3],[1920,1.3],[1920,0.9]].map(a=>L.colCount(a[0],a[1]));
o.place={n1:L.place(ORD,1,hs),n2:L.place(ORD,2,hs),n3:L.place(ORD,3,hs),tie:L.place(['a','b'],2,{a:100,b:100})};
o.norm=L.norm([{id:'a',col:9,order:0,idx:0},{id:'b',col:0,order:1,idx:1},{id:'c',col:0,order:1,idx:0},{id:'d',col:null,order:0,idx:3},{id:'e',col:0,order:0,idx:4,hidden:true}],2);
// poller: 3 failures stale, no pile-up, success resets, 5 s constant
const log=[],ft=[];let id=0,fail=true,calls=0,resolve;
const po=B.makePoller({load:()=>{calls++;return fail?Promise.reject(new Error('x')):new Promise(r=>{resolve=r})},onOk:()=>log.push('ok'),onFail:(n,s)=>log.push(n+(s?'S':'')),
  setTimeout:(f,ms)=>{ft.push({f,ms});return ++id},clearTimeout:()=>{}});
const step=async()=>{await sleep(5);const t=ft.pop();if(t)t.f();await sleep(5)};
po.start();await sleep(5);await step();await step();
fail=false;await step();po.now();po.now();await sleep(5);
const during=calls;resolve(1);await sleep(5);const after=calls;resolve&&resolve(1);await sleep(5);
o.poll={log,ms:ft.map(t=>t.ms),during,after,interval:B.REFRESH_MS,stale:B.FAILS_STALE};
out(o);
""")

    def test_T10_AC14_time_and_zone_with_zone_passed_in(self):
        t = self.res["t14"]
        self.assertEqual((t["plus7"], t["off7"]), ("09:00", "+07"))
        self.assertEqual(t["next"], "2026-11-04")  # 23:30Z is already the next day at +07
        self.assertEqual((t["kolkata"], t["bad"], t["badTime"], t["utc"]), ("+05:30", "UTC", "02:00", "UTC"))

    def test_T10_TA4_dst_changes_offset_by_date_not_by_now(self):
        t = self.res["t14"]
        self.assertEqual([t["ny1"], t["ny2"], t["ny3"], t["ny4"]], ["-05", "-04", "-04", "-05"])

    def test_T10_AC15_age_words_unknown_never_just_now(self):
        self.assertEqual(self.res["t15"], ["under 1 min ago", "under 1 min ago", "1 min ago", "3 h ago", "3 d ago",
                                           "age unknown", "age unknown", "age unknown"])

    def test_T10_AC13_tab_title_uses_squad_wide_count(self):
        self.assertEqual(self.res["title"], ["(3) board", "board", "board"])

    def test_T10_TA9_newer_of_file_and_browser_copy_wins(self):
        self.assertEqual(self.res["newer"], ["xl", "xl", "small", "small", None])

    def test_T10_AC17_unknown_source_never_renders_as_empty_or_fine(self):
        self.assertEqual(self.res["unk"], ["unknown", "data", "version"])

    def test_T10_TA6_needs_from_server_count(self):
        self.assertEqual(self.res["needs"], [3, None])

    def test_T26_TA2_column_count_follows_window_and_text_scale(self):
        self.assertEqual(self.res["cc"], [2, 3, 2, 2, 1, 1, 2, 3])

    def test_T26_TA3_default_place_is_the_shortest_column_leftmost_on_a_tie(self):
        pl = self.res["place"]
        col = lambda n: {k: v["col"] for k, v in pl[n].items()}
        self.assertEqual(col("n2"), {"inbox": 0, "tasks": 1, "agents": 0, "files": 1, "worktime": 0})  # the PO's case
        self.assertEqual(col("n3"), {"inbox": 0, "tasks": 1, "agents": 2, "files": 2, "worktime": 0})
        self.assertEqual(set(col("n1").values()), {0})
        self.assertEqual(col("tie"), {"a": 0, "b": 1})
        self.assertEqual(pl["n2"]["worktime"]["pos"], 2)

    def test_T26_TA1_TA13_norm_clamps_col_skips_hidden_and_no_col_and_ties_by_default_order(self):
        self.assertEqual(self.res["norm"], [["c", "b"], ["a"]])

    def test_T10_TA7_refresh_counts_three_failures_and_never_piles_up(self):
        p = self.res["poll"]
        self.assertEqual(p["log"][:3], ["1", "2", "3S"])
        self.assertEqual(p["ms"][-1], p["interval"])
        self.assertEqual((p["interval"], p["stale"]), (5000, 3))
        self.assertEqual(p["log"][-1], "ok")
        self.assertEqual(p["during"], 4)  # two extra now() calls while one load ran started nothing at once
        self.assertEqual(p["after"], 5)   # ... and one load runs right after it (a skipped refresh is not lost)


LAYOUT = STUB + """
mkPanel('1','Needs you',1,4,720);mkPanel('2','Tasks',8,8,560);mkPanel('3','Agents',3,4,380);mkPanel('4','Files',1,4,380);
mkPanel('5','Decisions',3,4,420);mkPanel('6','Long',40,4,300);
const rows={'1':8,'2':8,'3':3,'4':1,'5':3,'6':40};
const f=(location.hash.match(/font=(\\w+)/)||[])[1]||'normal';
const page=BOARD.start({fetch:mkFetch(rows),tz:'UTC',now:()=>Date.parse('2026-11-04T10:00:00Z'),setTimeout:fk.setTimeout,clearTimeout:fk.clearTimeout,storage:mem()});
await sleep(400);
if(f!=='normal'){page.setFont(f);await sleep(300)}
const cv=document.getElementById('canvas'),cr=cv.getBoundingClientRect();
const ps=[...document.querySelectorAll('.panel')].filter(e=>!e.hidden).map(e=>{const r=e.getBoundingClientRect(),pb=e.querySelector('.pb'),pbi=e.querySelector('.pbi');
  return{id:e.dataset.panel,l:r.left-cr.left,t:r.top-cr.top,r:r.right-cr.left,b:r.bottom-cr.top,scrolls:pb.scrollHeight>pb.clientHeight+1,blank:pb.getBoundingClientRect().bottom-pbi.getBoundingClientRect().bottom}});
out({ps,w:cr.width,page:{sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth}});
"""


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser test skipped")
class Layout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = Server()
        _, sess = cls.srv.get("/api/session")
        _, sq = cls.srv.get("/api/squads")
        key = json.loads(sq)["data"]["squads"][0]["key"]
        _, ui = cls.srv.get("/api/ui?squad=" + key)
        cls.real = {"session": json.loads(sess), "squads": json.loads(sq), "ui": json.loads(ui)}

    @classmethod
    def tearDownClass(cls):
        cls.srv.close()

    def run_layout(self, font, width):
        return run_page(LAYOUT, self.real, width=width, hash_="#font=" + font)

    def check(self, res, font, width):
        ps, tag = res["ps"], "%s %dpx" % (font, width)
        self.assertEqual(len(ps), 6, tag)
        self.assertLessEqual(res["page"]["sw"], max(res["page"]["cw"], 1000) + 1, tag)  # no sideways scroll at 1000 or wider
        lefts = sorted({round(p["l"]) for p in ps})
        W = width / {"small": 0.9, "normal": 1, "xl": 1.3}[font]
        self.assertEqual(len(lefts), 3 if W >= 1800 else (2 if W >= 932 else 1), tag)           # T26.AC13: the count follows the window
        for i, a in enumerate(ps):
            for b in ps[i + 1:]:                              # nothing overlaps
                self.assertFalse(a["l"] < b["r"] - 0.5 and b["l"] < a["r"] - 0.5 and a["t"] < b["b"] - 0.5 and b["t"] < a["b"] - 0.5,
                                 "%s: %s overlaps %s" % (tag, a["id"], b["id"]))
            if not a["scrolls"]:                              # a short panel is as tall as its content, no stretch
                self.assertLessEqual(a["blank"], 16, "%s: %s blank %s" % (tag, a["id"], a["blank"]))
        for lf in lefts:                                      # T26.AC1/AC2: 12 px between panels of a column
            col = sorted([p for p in ps if round(p["l"]) == lf], key=lambda p: p["t"])
            for a, b in zip(col, col[1:]):
                self.assertAlmostEqual(b["t"], a["b"] + 12, delta=2, msg="%s: %s under %s" % (tag, b["id"], a["id"]))
            self.assertLessEqual(col[0]["t"], 1, tag)
        self.assertTrue([p for p in ps if p["id"] == "6"][0]["scrolls"], tag)   # longer than its cap: scrolls inside

    def test_T26_AC1_AC2_AC8_AC13_columns_stack_with_12px_at_three_font_sizes_and_1000(self):
        for font in ("small", "normal", "xl"):
            self.check(self.run_layout(font, 1440), font, 1440)
        for font in ("small", "xl"):
            r = self.run_layout(font, 1000)
            self.check(r, font, 1000)
            self.assertLessEqual(r["page"]["sw"], 1000 + 1)   # nothing is cut off at 1000
        self.check(self.run_layout("normal", 1920), "normal", 1920)

    def test_T26_AC9_TA11_banner_is_outside_the_columns_without_drag_or_hide(self):
        r = run_page(STUB + """
mkPanel('1','A',1,4,300);
BOARD.start({fetch:mkFetch({'1':1}),tz:'UTC',now:()=>Date.parse('2026-11-04T10:00:00Z'),setTimeout:fk.setTimeout,clearTimeout:fk.clearTimeout,storage:mem()});
await sleep(300);
const b=document.querySelector('.bannerslot');
out({outside:!!b&&!b.closest('#canvas'),canvasKids:[...document.getElementById('canvas').children].every(c=>c.classList.contains('col')),
  handles:!!document.querySelector('.rz.e,.rz.se')});
""", self.real)
        self.assertEqual(r, {"outside": True, "canvasKids": True, "handles": False})

    def test_T26_AC3_AC4_AC6_AC11_AC14_AC15_drag_keys_hide_save_reload_reset(self):
        res = run_page(STUB + """
mkPanel('1','Needs you',8,4,720);mkPanel('2','Tasks',8,8,560);mkPanel('3','Agents',3,4,380);mkPanel('4','Files',1,4,380);
const rows={'1':8,'2':8,'3':3,'4':1};
const env=(ui)=>{const R2=JSON.parse(JSON.stringify(R));if(ui)R2.ui.data.ui=ui;return {fetch:mkFetch(rows,{'/api/ui':()=>({ok:true,status:200,json:async()=>Object.assign({schema_version:1},R2.ui)})}),tz:'UTC',now:()=>Date.parse('2026-11-04T10:00:00Z'),setTimeout:fk.setTimeout,clearTimeout:fk.clearTimeout,storage:mem()}};
const page=BOARD.start(env());await sleep(400);
const lay=()=>[...document.querySelectorAll('.col')].map(c=>[...c.querySelectorAll(':scope > .panel')].filter(e=>!e.hidden).map(e=>e.dataset.panel));
const fire=async()=>{for(const t of fakeTimers.splice(0)){if(t.ms===300)t.f()}await sleep(50)};
const ev=(t,el,x,y)=>el.dispatchEvent(new PointerEvent(t,{bubbles:true,clientX:x,clientY:y,button:0}));
const key=(p,k,sh)=>p.hdr.dispatchEvent(new KeyboardEvent('keydown',{key:k,shiftKey:!!sh,bubbles:true}));
const L0=lay();
const colOf=(l,id)=>l.findIndex(c=>c.includes(id));
const src=colOf(L0,'4'),dst=1-src;
// drag Files to the top of the other column
const f=page.panels['4'],fr=f.hdr.getBoundingClientRect(),first=document.querySelector('.col:nth-child('+(dst+1)+') > .panel').getBoundingClientRect();
ev('pointerdown',f.hdr,fr.left+20,fr.top+5);
ev('pointermove',document,first.left+30,first.top+4);await sleep(30);
const spot=document.querySelector('.ghost'),spotFirst=!!spot&&spot.parentNode.dataset.col==String(dst)&&!spot.previousElementSibling;
ev('pointerup',document,first.left+30,first.top+4);await sleep(100);
const L1=lay();await fire();
const put1=puts[puts.length-1];
// a column closes up: no gap under the left panels
const gaps=[...document.querySelectorAll('.col')].map(c=>{const k=[...c.querySelectorAll(':scope > .panel')];return k.slice(1).map((e,i)=>e.getBoundingClientRect().top-k[i].getBoundingClientRect().bottom)});
// Esc cancels, nothing saved
const n0=puts.length;
ev('pointerdown',f.hdr,f.hdr.getBoundingClientRect().left+20,f.hdr.getBoundingClientRect().top+5);
ev('pointermove',document,fr.left+30,fr.top+200);await sleep(30);
document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));await sleep(60);await fire();
const escSame=JSON.stringify(lay())===JSON.stringify(L1)&&puts.length===n0;
// keyboard: Up/Down in the column, Left/Right to the next column, focus stays, edges do nothing
f.hdr.focus();
key(f,'ArrowUp');const upEdge=JSON.stringify(lay())===JSON.stringify(L1);
key(f,'ArrowDown');const afterDown=lay();
key(f,'ArrowUp');
key(f,dst===0?'ArrowRight':'ArrowLeft');const afterSide=lay();
key(f,dst===0?'ArrowRight':'ArrowLeft');const sideEdge=JSON.stringify(lay())===JSON.stringify(afterSide);
const focusKept=document.activeElement===f.hdr;
// put it back in the other column by key, save, hide and show
key(f,dst===0?'ArrowLeft':'ArrowRight');await fire();
const put2=puts[puts.length-1],L2=lay();
page.panels['2'].hide.click();await sleep(100);const hidL=lay();
document.querySelector('.hb[aria-haspopup]').click();document.querySelector('.pop button').click();await sleep(100);
const L3=lay();
// reload from the saved body
const page2=BOARD.start(env(put2));await sleep(400);const L4=lay();
page2.resetLayout();await sleep(200);const L5=lay();
out({L0,L1,L2,L3,L4,L5,dst,src,spotFirst,gaps,escSame,upEdge,afterDown,afterSide,sideEdge,focusKept,put1,put2,hidL,auto5:page2.state.auto,
  nospan:Object.values(put2.panels).every(p=>!('span' in p))});
""", self.real)
        self.assertTrue(res["spotFirst"])                                        # T26.AC3: the spot shows where it lands
        self.assertEqual(res["L1"][res["dst"]][0], "4")                          # ... and it landed there
        self.assertNotIn("4", res["L1"][res["src"]])
        self.assertTrue(all(abs(g - 12) <= 2 for c in res["gaps"] for g in c))   # the column it left closed up
        self.assertEqual((res["put1"]["panels"]["4"]["col"], res["put1"]["panels"]["4"]["order"], res["put1"]["auto"]), (res["dst"], 0, False))
        self.assertTrue(res["escSame"])                                          # T26.AC14: Esc cancels, nothing saved
        self.assertTrue(res["upEdge"])                                           # T26.AC15: Up on the first moves nothing
        self.assertNotEqual(res["afterDown"], res["L1"])
        self.assertIn("4", res["afterSide"][res["src"]])                         # Left/Right: next column
        self.assertTrue(res["sideEdge"] and res["focusKept"])
        self.assertEqual(res["L3"], res["L2"])                                   # T26.AC4: show returns it to its place
        self.assertNotIn("2", sum(res["hidL"], []))
        self.assertEqual(res["L4"], res["L2"])                                   # T26.AC3: same after reload
        self.assertEqual(res["L5"], res["L0"])                                   # T26.AC6: Reset: default place
        self.assertTrue(res["auto5"])
        self.assertTrue(res["nospan"])                                           # span is no longer written
        squadboard_ui.validate(res["put2"])

    def test_T26_AC5_AC12_south_edge_changes_height_only_fit_returns(self):
        res = run_page(STUB + """
mkPanel('1','Needs you',8,4,720);mkPanel('2','Tasks',2,8,560);mkPanel('3','Agents',3,4,380);
const page=BOARD.start({fetch:mkFetch({'1':8,'2':2,'3':3}),tz:'UTC',now:()=>Date.parse('2026-11-04T10:00:00Z'),setTimeout:fk.setTimeout,clearTimeout:fk.clearTimeout,storage:mem()});
await sleep(400);
const a=page.panels['2'],r=()=>a.el.getBoundingClientRect(),below=()=>{const k=[...a.el.parentNode.children].filter(e=>e.classList.contains('panel'));const i=k.indexOf(a.el);return k[i+1]?k[i+1].getBoundingClientRect().top:null};
const other=[...document.querySelectorAll('.col')].filter(c=>c!==a.el.parentNode).map(c=>{const k=[...c.querySelectorAll(':scope > .panel')];return k[k.length-1].getBoundingClientRect().bottom});
const h0=r().height,w0=r().width,b0=below();
const s=a.el.querySelector('.rz.s'),sr=s.getBoundingClientRect();
s.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,clientX:sr.left+20,clientY:sr.top+3,button:0}));
document.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,clientX:sr.left+20,clientY:sr.top+203}));
document.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,clientX:sr.left+20,clientY:sr.top+203}));await sleep(100);
const h1=r().height,w1=r().width,b1=below();
const other1=[...document.querySelectorAll('.col')].filter(c=>c!==a.el.parentNode).map(c=>{const k=[...c.querySelectorAll(':scope > .panel')];return k[k.length-1].getBoundingClientRect().bottom});
a.fit.click();await sleep(100);
out({h0,h1,h2:r().height,w0,w1,b0,b1,other,other1,mh:a.max_height});
""", self.real)
        self.assertGreater(res["h1"], res["h0"] + 100)                    # taller
        self.assertAlmostEqual(res["w1"], res["w0"], delta=1)             # width stays the column's
        if res["b0"] is not None:
            self.assertGreater(res["b1"], res["b0"] + 100)                # the panel below moves down
        self.assertEqual(res["other"], res["other1"])                     # no other column changes
        self.assertAlmostEqual(res["h2"], res["h0"], delta=1)             # Fit: back to the content

    def test_T26_AC7_TA5_TA12_old_saved_layout_loads_without_error_or_write(self):
        old = json.loads((HERE / "fixtures" / "board" / "layout-26" / "board-ui-iter1.json").read_text(encoding="utf-8"))
        real = dict(self.real, ui={"schema_version": 1, "data": {"ui": old, "status": "ok"}})
        mixed = dict(old, panels={"1": {"order": 0, "col": 9, "hidden": False}, "3": {"order": 0, "col": 0, "hidden": False},
                                  "4": {"order": 1, "col": 1, "hidden": False}})
        body = STUB + """
mkPanel('1','Needs you',8,4,720);mkPanel('2','Tasks',8,8,560);mkPanel('3','Agents',3,4,380);mkPanel('4','Files',1,4,380);
const run=async(ui)=>{const R2=JSON.parse(JSON.stringify(R));R2.ui.data.ui=ui;puts.length=0;
  const page=BOARD.start({fetch:mkFetch({'1':8,'2':8,'3':3,'4':1},{'/api/ui':()=>({ok:true,status:200,json:async()=>R2.ui})}),tz:'UTC',now:()=>Date.parse('2026-11-04T10:00:00Z'),setTimeout:fk.setTimeout,clearTimeout:fk.clearTimeout,storage:mem()});
  await sleep(400);for(const t of fakeTimers.splice(0)){t.f()}await sleep(50);
  return {lay:[...document.querySelectorAll('.col')].map(c=>[...c.querySelectorAll(':scope > .panel')].filter(e=>!e.hidden).map(e=>e.dataset.panel)),
    puts:puts.length,notes:document.querySelector('.notes').textContent,h3:page.panels['3'].el.getBoundingClientRect().height,snap:page.snapshot()}};
out({old:await run(%s),mixed:await run(%s)});
""" % (json.dumps(old), json.dumps(mixed))
        r = run_page(body, real)
        o, m = r["old"], r["mixed"]
        self.assertEqual(sorted(sum(o["lay"], [])), ["1", "3", "4"])             # '2' stays hidden; default place for the rest
        self.assertEqual((o["puts"], o["notes"]), (0, ""))                       # no write on load, no error text
        self.assertAlmostEqual(o["h3"], 200, delta=1)                            # max_height kept
        self.assertEqual(m["puts"], 0)
        self.assertEqual(m["lay"][0][0], "3")                                    # a panel with a col does not move
        self.assertLess(m["lay"][1].index("1"), m["lay"][1].index("4"))          # col 9 shows in the last column, by order
        self.assertIn("2", sum(m["lay"], []))                                    # the one without col got a default place
        self.assertEqual(m["snap"]["panels"]["1"]["col"], 9)                     # the file keeps the larger value

    def test_T10_TA7_response_for_the_old_choice_is_dropped_and_new_one_loads(self):
        res = run_page(STUB + """
mkPanel('1','A',1,4,300);
let release;const held=new Promise(r=>{release=r});let first=true;
const resp=n=>({ok:true,status:200,json:async()=>({schema_version:1,unknown:[],quality:'exact',data:{rows:n}})});
const over={'/api/t1':async(url)=>{if(first&&url.includes('scope=checkout')){first=false;await held;return resp(2)}return resp(5)}};
const page=BOARD.start({fetch:mkFetch({},over),tz:'UTC',now:()=>Date.parse('2026-11-04T10:00:00Z'),setTimeout:fk.setTimeout,clearTimeout:fk.clearTimeout,storage:mem()});
await sleep(200);
page.setChoice('scope:other');
release();await sleep(300);
out({rows:page.panels['1'].body.children.length,choice:page.state.choice.name});
""", self.real)
        self.assertEqual(res, {"rows": 5, "choice": "other"})

    def test_T10_AC16_failed_start_recovers_and_updated_shows_only_after_panels_load(self):
        res = run_page(STUB + """
mkPanel('1','A',1,4,300);
let n=0;
const over={'/api/session':async()=>{if(n++===0)throw new Error('down');return {ok:true,status:200,json:async()=>Object.assign({schema_version:1,unknown:[]},R.session)}}};
const page=BOARD.start({fetch:mkFetch({'1':3},over),tz:'UTC',now:()=>Date.parse('2026-11-04T10:00:00Z'),setTimeout:fk.setTimeout,clearTimeout:fk.clearTimeout,storage:mem()});
await sleep(100);
const before={status:page.state.status,text:document.querySelector('.fresh').textContent,rows:page.panels['1'].body.children.length};
for(let i=0;i<3;i++){const t=fakeTimers.filter(x=>x.ms===BOARD.REFRESH_MS).pop();if(t){fakeTimers.splice(fakeTimers.indexOf(t),1);t.f()}await sleep(100)}
out({before,status:page.state.status,text:document.querySelector('.fresh').textContent,rows:page.panels['1'].body.children.length,token:page.state.token,choice:!!page.state.choice});
""", self.real)
        self.assertEqual(res["before"]["rows"], 0)
        self.assertNotIn("updated", res["before"]["text"])
        self.assertEqual((res["rows"], res["status"], bool(res["token"]), res["choice"]), (3, "ok", True, True))
        self.assertIn("updated", res["text"])


def _keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from _keys(v)
    elif isinstance(o, list):
        for v in o:
            yield from _keys(v)


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser test skipped")
class RealServer(unittest.TestCase):
    """The page files are served by the real server and the shell starts on the fixture (AC16 headline, AC13)."""

    def test_T10_AC13_AC16_page_loads_from_server_and_shows_updated_and_zone(self):
        s = Server()
        try:
            for f in FILES:
                code, body = s.get("/static/" + f)
                self.assertEqual(code, 200, f)
            r = subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=6000",
                                "--window-size=1440,900", "--dump-dom", s.base + "/?squad=fix&scope=checkout"],
                               capture_output=True, text=True, timeout=90)
        finally:
            s.close()
        dom = re.sub(r"<script.*?</script>", "", r.stdout, flags=re.S)
        self.assertRegex(dom, r"updated \d\d:\d\d:\d\d")
        self.assertIn("<title>fix</title>", dom)  # no count: nothing reports needs-you yet
        self.assertRegex(dom, r'<span class="zone"[^>]*>zone <b>[^<]+</b>')
        self.assertNotIn("%", re.sub(r"<style.*?</style>", "", dom, flags=re.S).split("<body")[1])


class StaleToken(unittest.TestCase):
    """Ticket 21: a save refused for a stale token is retried once with a fresh token (T21.TA1-TA6)."""

    @classmethod
    def setUpClass(cls):
        cls.srv = Server()
        _, sess = cls.srv.get("/api/session")
        _, sq = cls.srv.get("/api/squads")
        key = json.loads(sq)["data"]["squads"][0]["key"]
        _, ui = cls.srv.get("/api/ui?squad=" + key)
        cls.real = {"session": json.loads(sess), "squads": json.loads(sq), "ui": json.loads(ui)}

    @classmethod
    def tearDownClass(cls):
        cls.srv.close()

    def test_T21_AC1_AC4_TA1_to_TA6_one_retry_on_token_required_only(self):
        res = run_page(STUB + """
mkPanel('1','A',1,4,300);
const T='token required', H='host not allowed';
// answers: PUT replies are taken in order as [status, error]; a session GET answers a new token each time
async function scenario(replies){
  const calls=[];let n=0;
  const base=mkFetch({'1':1},{});
  const f=async(url,opt)=>{
    if(opt&&opt.method==='PUT'){
      const [st,err]=replies[Math.min(calls.filter(c=>c.m==='PUT').length,replies.length-1)];
      calls.push({m:'PUT',tok:opt.headers['X-Board-Token'],body:opt.body,notesHidden:document.querySelector('.notes').hidden});
      return {ok:st===200,status:st,json:async()=>(err?{error:err}:{schema_version:1,data:{status:'ok'}})};
    }
    if(url.startsWith('/api/session')){calls.push({m:'GET'});return {ok:true,status:200,json:async()=>({schema_version:1,data:{token:'new'+(++n)}})}}
    return base(url,opt);
  };
  const page=BOARD.start({fetch:f,tz:'UTC',now:()=>Date.parse('2026-11-04T10:00:00Z'),setTimeout:fk.setTimeout,clearTimeout:fk.clearTimeout,storage:mem()});
  await sleep(300);
  calls.length=0;
  const save=async(font)=>{page.setFont(font);for(const t of fakeTimers.splice(0)){if(t.ms===300)t.f()}await sleep(100)};
  await save('xl');
  const out1={calls:calls.map(c=>c.m),toks:calls.filter(c=>c.m==='PUT').map(c=>c.tok),same:calls.filter(c=>c.m==='PUT').every(c=>c.body===calls.find(x=>x.m==='PUT').body),
    status:page.state.saveStatus,hidden:calls.filter(c=>c.m==='PUT').map(c=>c.notesHidden),note:document.querySelector('.notes').textContent};
  // a second save starts fresh: one retry again (the counter is per save)
  calls.length=0;await save('small');out1.second=calls.map(c=>c.m);
  return out1;
}
out({host:await scenario([[403,H]]),ok:await scenario([[403,T],[200]]),twice:await scenario([[403,T],[403,T]]),unw:await scenario([[403,T],[507,'x']])});
""", self.real)
        # TA1: a Host refusal is final: one PUT, failed
        self.assertEqual((res["host"]["calls"], res["host"]["status"]), (["PUT"], "failed"))
        # TA2 + TA6 (AC1): PUT, new token, same body; ok; the notes stay hidden the whole time
        ok = res["ok"]
        self.assertEqual(ok["calls"], ["PUT", "GET", "PUT"])
        self.assertEqual(ok["toks"][1], "new2")  # boot took new1
        self.assertNotEqual(ok["toks"][0], ok["toks"][1])
        self.assertTrue(ok["same"])
        self.assertEqual((ok["status"], ok["note"]), ("ok", ""))
        self.assertEqual(ok["hidden"], [True, True])
        # TA3: refused again -> two PUTs, one session GET, failed; the next save retries once more
        self.assertEqual((res["twice"]["calls"], res["twice"]["status"]), (["PUT", "GET", "PUT"], "failed"))
        self.assertEqual(res["twice"]["second"], ["PUT", "GET", "PUT"])
        # TA4 (AC4): unwritable after the retry, the T09 text, no third PUT
        self.assertEqual((res["unw"]["calls"], res["unw"]["status"]), (["PUT", "GET", "PUT"], "unwritable"))
        self.assertTrue(res["unw"]["note"].startswith("Settings not shared. The settings file in the squad folder cannot be written."))


class StaticRules(unittest.TestCase):
    def read(self, name):
        return (TPL / name).read_text(encoding="utf-8")

    def test_T10_TA3_TA11_four_files_banner_is_not_a_panel(self):
        self.assertEqual(sorted(p.name for p in TPL.iterdir()), sorted(FILES + ("panel_scopes.js", "panel_inbox.js", "panel_tasks.js", "panel_agents.js", "panel_files.js", "timeline.js")))  # tickets 11, 12, 14 and 16 add panel files
        self.assertNotIn("banner", self.read("layout.js").lower().replace("bannerslot", ""))

    def test_T10_TA5_AC11_no_percent_in_page_scripts_or_html(self):
        for f in ("board.js", "layout.js", "index.html"):
            self.assertNotIn("%", self.read(f), f)

    def test_T10_TU3_TU4_TU5_TU9_no_innerhtml_no_remote_no_extra_writes_no_hex_outside_root(self):
        js = self.read("board.js") + self.read("layout.js")
        self.assertIsNone(re.search(r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(|new Function", js))
        for f in FILES:
            self.assertIsNone(re.search(r"https?://|@import", self.read(f)), f)
        self.assertEqual(re.findall(r'method\s*:\s*"(\w+)"', js), ["PUT"])
        css = self.read("board.css")
        self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}", re.sub(r":root\{.*?\}", "", css, count=1, flags=re.S)))
        self.assertIn("overflow-x:auto", css.replace(" ", ""))  # sideways scroll on the page, not on a panel body

    def test_T10_AC12_mango_only_on_needs_you_rules(self):
        css = self.read("board.css")
        rules = [r for r in re.findall(r"([^{}]+)\{([^}]*)\}", re.sub(r":root\{.*?\}", "", css, count=1, flags=re.S))
                 if re.search(r"var\(--(mango|t-need|t-edge)", r[1])]
        for sel, _ in rules:
            self.assertRegex(sel, r"hot|need|banner|colhid", sel)  # colhid: the "N hidden" tag of the Columns button (design-v6 section 3)


if __name__ == "__main__":
    unittest.main()
