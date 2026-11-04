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
// layout.pack
const mk=(id,order,span,height,extra)=>Object.assign({id,order,span,hidden:false,height,max:1000},extra||{});
const cell=(r,id)=>r.find(c=>c.id===id);
const overlap=r=>r.some((x,i)=>r.some((y,j)=>j>i&&x.col<y.col+y.span&&y.col<x.col+x.span&&x.row<y.row+y.rowSpan&&y.row<x.row+x.rowSpan));
const short=mk('files',1,4,40),tall=mk('tasks',0,4,300),under=mk('dec',2,4,100);
let r=L.pack([tall,short,under,mk('ag',3,4,100)],12,4);
o.pack={hole:r.map(c=>[c.id,c.col,c.row,c.span,c.rowSpan]),overlap:overlap(r)};
o.hidden=L.pack([tall,Object.assign({},short,{hidden:true}),under],12,4).map(c=>c.id);
o.up=[cell(L.pack([tall,short,under],12,4),'dec').row, cell(L.pack([tall,Object.assign({},short,{hidden:true}),under],12,4),'dec').row];
const rows=n=>mk('p'+n,n,4,n*30+40);
const shape=h=>L.pack([1,3,8].map(n=>Object.assign(rows(n),{height:rows(n).height*h})),12,4).map(c=>[c.id,c.col,c.span]);
o.fonts=[shape(0.9),shape(1),shape(1.3)];
const cap=L.pack([mk('big',0,4,900,{max:300})],12,4)[0];o.cap={rs:cap.rowSpan,scroll:cap.scroll};
o.cols=[L.cols(1000),L.cols(1440)];
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

    def test_T10_AC5_AC6_short_beside_tall_leaves_no_hole_and_hide_moves_up(self):
        p = self.res["pack"]
        cells = {c[0]: c[1:] for c in p["hole"]}
        self.assertFalse(p["overlap"])
        self.assertEqual(cells["tasks"][:2], [0, 0])
        self.assertEqual(cells["files"][:2], [4, 0])       # beside the tall one, top row
        self.assertEqual(cells["dec"][:2], [8, 0])
        self.assertEqual(cells["ag"][:2], [4, 13])         # the fourth goes up under the short one, not under the tall one
        self.assertEqual(self.res["hidden"], ["tasks", "dec"])
        self.assertEqual(self.res["up"][0], 0)             # dec sits beside tasks, at the top (no gap under files)

    def test_T10_TA1_same_state_same_order_and_spans_at_three_font_sizes(self):
        a, b, c = self.res["fonts"]
        self.assertEqual([x[0] for x in a], [x[0] for x in c])
        self.assertEqual([x[2] for x in a], [x[2] for x in c])

    def test_T10_AC8_taller_content_scrolls_at_the_cap(self):
        self.assertEqual(self.res["cap"], {"rs": 78, "scroll": True})  # ceil((300 + 12) / 4)

    def test_T10_TA10_fewer_columns_at_1000(self):
        self.assertEqual(self.res["cols"], [8, 12])

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
        for i, a in enumerate(ps):
            for b in ps[i + 1:]:  # nothing overlaps (AC7)
                self.assertFalse(a["l"] < b["r"] - 0.5 and b["l"] < a["r"] - 0.5 and a["t"] < b["b"] - 0.5 and b["t"] < a["b"] - 0.5,
                                 "%s: %s overlaps %s" % (tag, a["id"], b["id"]))
            if not a["scrolls"]:  # AC3: no empty band over 16 px under the last row
                self.assertLessEqual(a["blank"], 16, "%s: %s blank %s" % (tag, a["id"], a["blank"]))
            # AC4: beside a panel in a row, the next thing starts one gutter (12 px) later, or the page edge is there
            if a["r"] < res["w"] - 1:
                nxt = [b for b in ps if b is not a and abs(b["l"] - (a["r"] + 12)) <= 1 and b["t"] < a["b"] and a["t"] < b["b"]]
                self.assertTrue(nxt, "%s: %s leaves an empty cell on its right (right %.0f of %.0f)" % (tag, a["id"], a["r"], res["w"]))
        long_ = [p for p in ps if p["id"] == "6"][0]
        self.assertTrue(long_["scrolls"], tag)  # AC8: longer than its cap, it scrolls inside
        top = [p for p in ps if p["t"] < 1]
        self.assertTrue(top and min(p["l"] for p in top) <= 1, tag)

    def test_T10_AC3_to_AC9_fit_gaps_and_no_overlap_at_three_font_sizes_and_1000(self):
        for font in ("small", "normal", "xl"):
            self.check(self.run_layout(font, 1440), font, 1440)
        for font in ("small", "xl"):
            r = self.run_layout(font, 1000)
            self.check(r, font, 1000)
            self.assertLessEqual(r["page"]["sw"], 1000 + 1)  # nothing is cut off at 1000

    def test_T10_AC1_AC2_AC7_move_resize_hide_reset_and_saved_state(self):
        res = run_page(STUB + """
mkPanel('1','Needs you',1,4,720);mkPanel('2','Tasks',8,8,560);mkPanel('3','Agents',3,4,380);mkPanel('4','Files',1,4,380);
const rows={'1':8,'2':8,'3':3,'4':1};
const env=(ui)=>{const R2=JSON.parse(JSON.stringify(R));if(ui)R2.ui.data.ui=ui;return {fetch:mkFetch(rows,{'/api/ui':()=>({ok:true,status:200,json:async()=>Object.assign({schema_version:1},R2.ui)})}),tz:'UTC',now:()=>Date.parse('2026-11-04T10:00:00Z'),setTimeout:fk.setTimeout,clearTimeout:fk.clearTimeout,storage:mem()}};
const page=BOARD.start(env());await sleep(400);
const ev=(t,el,x,y)=>el.dispatchEvent(new PointerEvent(t,{bubbles:true,clientX:x,clientY:y,button:0}));
const order0=Object.values(page.panels).sort((a,b)=>a.order-b.order).map(p=>p.id);
// drag Files (4) to the top area
const f=page.panels['4'];const fr=f.hdr.getBoundingClientRect();
ev('pointerdown',f.hdr,fr.left+20,fr.top+5);
const m=document.getElementById('canvas').getBoundingClientRect();
for(const [x,y] of [[m.left+30,m.top+30],[m.left+40,m.top+40]]){ev('pointermove',document,x,y);await sleep(20)}
const ghost=!!document.querySelector('.ghost');
ev('pointerup',document,m.left+40,m.top+40);await sleep(300);
const order1=Object.values(page.panels).sort((a,b)=>a.order-b.order).map(p=>p.id);
// resize Agents wider: east handle
const a=page.panels['3'],h=a.el.querySelector('.rz.e'),hr=h.getBoundingClientRect(),span0=a.span;
ev('pointerdown',h,hr.left+2,hr.top+20);ev("pointermove",document,hr.left-250,hr.top+20);await sleep(20);ev("pointerup",document,hr.left-250,hr.top+20);await sleep(300);
const span1=a.span;
fk.setTimeout.length;
await sleep(10);
for(const t of fakeTimers.splice(0)){if(t.ms===300)t.f()}   // fire the debounced save
await sleep(50);
const put=puts[puts.length-1];
// hide Tasks: banner has no hide, panel returns from the list
page.panels['2'].hide.click();await sleep(100);
const hid=document.querySelector('[data-panel="2"]').hidden;
document.querySelector('.hb[aria-haspopup]').click();
const items=[...document.querySelectorAll('.pop button')].map(b=>b.textContent);
document.querySelector('.pop button').click();await sleep(100);
const back=!document.querySelector('[data-panel="2"]').hidden;
// reload: a second page reading the saved state
const page2=BOARD.start(env(put));await sleep(400);
const order2=Object.values(page2.panels).sort((x,y)=>x.order-y.order).map(p=>p.id);
const span2=page2.panels['3'].span;
// reset
page2.resetLayout();await sleep(200);
const order3=Object.values(page2.panels).sort((x,y)=>x.order-y.order).map(p=>p.id);
out({order0,order1,ghost,span0,span1,put,hid,items,back,order2,span2,order3,span3:page2.panels['3'].span,
  bannerHide:!!document.querySelector('.bannerslot .pbtn, .bannerslot .grip')});
""", self.real)
        self.assertTrue(res["ghost"])
        self.assertLess(res["order1"].index("4"), res["order0"].index("4"))  # Files moved up
        self.assertNotEqual(res["order0"], res["order1"])
        self.assertNotEqual(res["span1"], res["span0"])
        # AC2: hidden, then back from the list
        self.assertTrue(res["hid"])
        self.assertEqual(res["items"], ["Show Tasks"])
        self.assertTrue(res["back"])
        # AC1: the saved state restores both; AC2: reset returns the default
        self.assertEqual(res["order2"], res["order1"])
        self.assertEqual(res["span2"], res["span1"])
        self.assertEqual((res["order3"], res["span3"]), (res["order0"], res["span0"]))
        # T10.TA2: no stored pixels, and the real server's validator accepts the body
        self.assertEqual([k for k in json.dumps(res["put"]) and _keys(res["put"]) if re.fullmatch(r"x|y|top|left|px|row", k)], [])
        squadboard_ui.validate(res["put"])


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
        self.assertEqual(sorted(p.name for p in TPL.iterdir()), sorted(FILES + ("panel_scopes.js",)))  # ticket 11 adds one panel file
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
            self.assertRegex(sel, r"hot|need|banner", sel)


if __name__ == "__main__":
    unittest.main()
