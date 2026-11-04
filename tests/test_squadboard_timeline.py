"""Work time page (ticket 16): swimlanes. The rules are plain functions on BOARD.TIMELINE and the page is driven in headless
Chrome on a small harness that loads the real templates/board/*.js (pattern of test_squadboard_panels.py). The data is the real
answer of `squadboard_worktime.read` (ticket 15) on pieces built by its own test helpers, never hand-typed JSON.
Tests are named for the business AC (T16.ACn) or technical AC (T16.TAn)."""
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "bin"))
import squadreport as sr  # noqa: E402
import squadboard_worktime as wt  # noqa: E402
import test_squadboard_worktime as tw  # noqa: E402
from test_squadboard_page import CHROME, TPL  # noqa: E402

B, H = tw.B, tw.H
NOW = B + 133000

HEAD = """<!doctype html><meta charset=utf-8>
<link rel=stylesheet href="file://%(tpl)s/board.css">
<div id=app></div><pre id=out></pre>
<script>window.BOARD_NO_AUTOSTART=true;window.__real=%(real)s;window.__warns=[];console.warn=function(m){window.__warns.push(String(m))};</script>
%(scripts)s
<script>
const out=v=>{document.getElementById('out').textContent=JSON.stringify(v)};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const R=window.__real, calls=[];
const fakeTimers=[];let tid=0;
const fk={setTimeout:(f,ms)=>{fakeTimers.push({id:++tid,f,ms});return tid},clearTimeout:id=>{const i=fakeTimers.findIndex(t=>t.id===id);if(i>=0)fakeTimers.splice(i,1)}};
const mem=()=>{const m={};return{getItem:k=>(k in m?m[k]:null),setItem:(k,v)=>{m[k]=String(v)}}};
const J=o=>({ok:true,status:200,json:async()=>Object.assign({schema_version:1,unknown:[],quality:'approx'},o)});
const SQ={squads:[{key:'fix',name:'fix',flat:false,scopes:['dev'],goals:[]}],initial:{squad:'fix',scope:'dev'}};
let slow=null, payload=R.wt;
const fetchStub=async(url,opt)=>{
  calls.push({m:(opt&&opt.method)||'GET',u:url,b:opt&&opt.body||null});
  if(opt&&opt.method==='PUT')return J({data:{ui:JSON.parse(opt.body),status:'ok'}});
  if(url.startsWith('/api/session'))return J({data:{token:'t'}});
  if(url.startsWith('/api/squads'))return J({data:SQ});
  if(url.startsWith('/api/ui'))return J({data:{ui:null,status:'ok'}});
  if(url.startsWith('/api/worktime')){
    if(window.__v2)return J({schema_version:2,data:null});
    if(window.__unk)return J({data:null,unknown:['transcript']});
    const q=new URLSearchParams(url.split('?')[1]);const f=q.get('from'),t=q.get('to');
    if(slow&&f===String(slow.from))await sleep(slow.ms);
    const d=Object.assign({},payload.data,{from:f==null?payload.data.from:+f,to:+t});
    return J({data:d,unknown:payload.unknown});
  }
  return {ok:false,status:404,json:async()=>({schema_version:1,error:'nf'})};
};
const startPage=async()=>{
  BOARD.start({fetch:fetchStub,storage:mem(),setTimeout:fk.setTimeout,clearTimeout:fk.clearTimeout,now:()=>R.now*1000,tz:'UTC'});
  await sleep(300);return BOARD.page;
};
const $=s=>document.querySelector(s), $$=s=>Array.from(document.querySelectorAll(s));
const T=BOARD.TIMELINE;
(async()=>{try{
%(body)s
}catch(e){out({error:String(e&&e.stack||e)})}})();
</script>
"""
SCRIPTS = ('<script src="file://%(tpl)s/board.js"></script><script src="file://%(tpl)s/layout.js"></script>'
           '<script src="file://%(tpl)s/timeline.js"></script>')


def run_page(body, real, scripts=SCRIPTS, tz=None, size="1440,900"):
    with tempfile.TemporaryDirectory() as d:
        page = Path(d) / "page.html"
        page.write_text(HEAD % {"tpl": str(TPL), "real": json.dumps(real), "body": body, "scripts": scripts % {"tpl": str(TPL)}},
                        encoding="utf-8")
        r = subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--allow-file-access-from-files",
                            "--virtual-time-budget=20000", "--window-size=" + size, "--dump-dom", "file://" + str(page)],
                           capture_output=True, text=True, timeout=120, env=dict(os.environ, TZ=tz) if tz else None)
    assert r.returncode == 0, r.stderr[-500:]
    m = re.search(r'<pre id="out">(.*?)</pre>', r.stdout, re.S)
    assert m, r.stdout[-800:]
    res = json.loads(html.unescape(m.group(1)))
    assert "error" not in res, res["error"]
    return res


def read_api(c, gap="15", **params):
    """The real answer of /api/worktime (ticket 15) for a Collected, wrapped as the server wraps it."""
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "h"
        home.mkdir()
        sel = tw.sel_for(tmp, home, gap_min=gap, **params)
        sel["now"] = NOW
        with mock.patch.object(wt, "collected", return_value=c):
            r = wt.read(sel)
    assert r["data"], r
    return {"schema_version": 1, "data": r["data"], "quality": r["quality"], "unknown": r["unknown"]}


def seg(a, b, bucket, on=None):
    return tw.seg(a, b, bucket, on)


def rich():
    """Developer on task 03 with every gap size, a night waiting on the PO, a QA, an agent with no transcript."""
    dev, t = [], 0

    def add(n, bucket, on=None):
        nonlocal t
        dev.append(seg(t, t + n, bucket, on))
        t += n
    for _ in range(4):
        add(900, "working")                      # 1 h of task 03, in pieces no longer than the smallest setting
    add(1800, "waiting")
    add(960, "idle"); add(540, "working")        # A: 16 min
    add(900, "idle"); add(600, "working")        # E: exactly 15 min
    add(3660, "idle"); add(600, "working")       # B: 61 min
    add(14460, "idle"); add(600, "working")      # C: 241 min
    add(52800, "idle"); add(600, "working")      # D: 14 h 40 min
    add(50400, "blocking", "PO"); add(600, "working")   # the night waiting on the PO (AC6)
    qa = [seg(0, 600, "working"), seg(600, 1200, "working"), seg(1200, 3000, "waiting"), seg(3000, 3600, "working"),
          seg(3600, 4200, "working")]
    ms = [tw.msg(0, "lead", "dev", "ASSIGN 03 go"), tw.msg(3000, "dev", "qa", "HANDIN 03 a"), tw.msg(6000, "qa", "dev", "PASS 03"),
          tw.msg(7000, "qa", "dev", "FAIL 03 no"), tw.msg(81200, "dev", "lead", "BLOCKED 03 x")]
    c = tw.collected({"dev": tw.tl("dev", dev), "qa": sr.AgentTL("qa", "qa", True, False, 1, qa, []),
                      "ghost": tw.tl("ghost", [], found=False)}, ms)
    return read_api(c)


def dst():
    """A 3 h idle gap across the 2026-03-29 clock change in Europe/Berlin (01:00 UTC); local subtraction would say 4 h."""
    import calendar
    t0 = calendar.timegm((2026, 3, 29, 0, 30, 0))
    segs = [sr.Seg(t0 - 600, t0, "working", None, None, False), sr.Seg(t0, t0 + 3 * H, "idle", "human_input", None, False),
            sr.Seg(t0 + 3 * H, t0 + 3 * H + 600, "working", None, None, False)]
    c = sr.Collected(Path("/x"), "sq", "sc", "", "", (t0 - 600, t0 + 4 * H), {"dev": tw.tl("dev", segs)}, [], [], [], {}, {}, [])
    return read_api(c, **{"from": str(t0 - 600), "to": str(t0 + 4 * H)})


def evil():
    name = "<img src=x onerror=window.__x=1>"
    c = tw.collected({name: tw.tl(name, [seg(0, 600, "working")]), "g<b>x": tw.tl("g<b>x", [], found=False)})
    return read_api(c)


def real_normal():
    return real_long_gap("normal.jsonl", "wt-dev-normal", "1792508000", "1792508100")


def real_long_gap(fixture="long-gap.jsonl", agent="wt-dev-long", lo="1792508000", hi="1792552000"):
    """The real 11.2 h `long-gap` sample of ticket 15 through its own reader."""
    import os
    import shutil
    tmp = tempfile.mkdtemp()
    try:
        with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(Path(tmp) / "cfg")}):
            wt._CACHE.clear()
            wt._PATHS.clear()
            home, _ = tw.write_squad(tmp, fixture, "sess2", agent)
            r = wt.read(tw.sel_for(tmp, home, **{"from": lo, "to": hi, "gap_min": "60"}))
        return {"schema_version": 1, "data": r["data"], "quality": r["quality"], "unknown": r["unknown"]}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser test skipped")
class Rules(unittest.TestCase):
    """The rules callable without the DOM (T16.TA1), on the real reader output (TU.8)."""

    @classmethod
    def setUpClass(cls):
        cls.res = run_page("""
const d=R.wt.data,o={};
const devp=d.agents.find(a=>a.agent==='dev').pieces;
o.collapse=[14,15,60,240,241].map(n=>({n:T.clampGap(n),breaks:T.collapse(devp,n,false,'UTC').breaks.map(b=>b.seconds)}));
const real=T.collapse(devp,60,true,'UTC');o.real=[real.pieces===devp,real.breaks.length];
const forced=devp.map(p=>Object.assign({},p,{collapsible:true}));
o.forced=T.collapse(forced,15,false,'UTC').breaks.filter(b=>devp.some(p=>(p.bucket==='waiting'||p.bucket==='blocked')&&p.start<b.end&&p.end>b.start)).length;
o.labels=[T.breakLabel(52800,'night'),T.breakLabel(140000,'weekend'),T.breakLabel(1500,'idle'),T.breakLabel(1500,'zzz')];
const dp=R.dst.data.agents[0].pieces;
o.dst=['Europe/Berlin','America/New_York','UTC'].map(z=>T.collapse(dp,60,false,z).breaks.map(b=>b.label));
o.naive=T.loc(dp[1].end,'Europe/Berlin').h-T.loc(dp[1].start,'Europe/Berlin').h;
const now=Date.parse('2026-11-04T10:00:00Z')/1000;
o.presets=['1h','today','3d','all','zz'].map(n=>T.presetRange(n,now,'Asia/Ho_Chi_Minh'));
o.berlinToday=T.presetRange('today',Date.parse('2026-03-29T12:00:00Z')/1000,'Europe/Berlin').from-Date.parse('2026-03-28T23:00:00Z')/1000;
const rg={from:1000,to:2000};
o.zoom=[T.zoomRange(rg,1500,.5),T.zoomRange(rg,1000,.5),T.zoomRange(rg,1500,2),T.zoomRange({from:0,to:200},100,.5)];
o.drag=[T.dragRange(100,300,rg,1000),T.dragRange(300,100,rg,1000),T.dragRange(100,104,rg,1000)];
o.filter=[T.taskFilter(devp,['03']).length,T.taskFilter(devp,[null]).every(p=>p.task==null&&p.bucket!=='idle'),T.taskFilter(devp,[]).length===devp.length,T.taskFilter(devp,['99']).length,devp.length];
const t0=d.agents[0].pieces[0].start,tiles=[];
for(let a=0;a<20;a++){const ps=[];for(let i=0;i<2000;i++)ps.push({start:t0+i*2,end:t0+i*2+2,bucket:i%3?'working':'waiting',task:'03',approx:true,on:null,collapsible:false,worktree:'',branch:''});tiles.push(ps)}
const r2={from:t0,to:t0+4000},st=performance.now();
const lanes=tiles.map(ps=>T.layoutLanes(ps,r2,1200,[]));const ms=performance.now()-st;
const l0=lanes[0];
o.perf={ms:ms,in:2000,out:l0.length,sec:l0.reduce((s,r)=>s+r.seconds,0),sum:4000};
const sc=T.makeScale({from:0,to:1000},[{start:400,end:600,kind:'idle',label:'x',seconds:200}]);
o.scale=[sc.breaks.length,sc.x(0),sc.x(1000),sc.tAt(sc.x(300))];
const lg=R.long.data.agents.find(a=>a.agent==='wt-dev-long').pieces, nm=R.normal.data.agents.find(a=>a.agent==='wt-dev-normal').pieces;
const cl=T.collapse(lg,60,false,'UTC');
o.real2={breaks:cl.breaks.map(b=>b.seconds),filter:T.taskFilter(nm,['03']).length===nm.length,
 secs:T.layoutLanes(nm,{from:nm[0].start,to:nm[nm.length-1].end},800,[]).reduce((s,r)=>s+r.seconds,0),want:nm.reduce((s,p)=>s+p.end-p.start,0)};
out(o);""", {"wt": rich(), "dst": dst(), "long": real_long_gap(), "normal": real_normal()})

    def test_T16_AC8_TA2_setting_limits_clamp_and_strictly_longer(self):
        c = {x["n"]: x["breaks"] for x in self.res["collapse"]}
        self.assertEqual([x["n"] for x in self.res["collapse"]], [15, 15, 60, 240, 240])
        self.assertEqual(len(c[15]), 4)   # 16 min, 61 min, 241 min, 14 h 40 min; the 15 min gap is not "over" 15
        self.assertEqual(len(c[60]), 3)
        self.assertEqual(c[240], [14460, 52800])
        self.assertEqual(self.res["collapse"][4]["breaks"], c[240])   # 241 clamps to 240

    def test_T16_AC6_TA2_waiting_and_blocked_never_fold_and_real_time_is_unchanged(self):
        self.assertEqual(self.res["forced"], 0)
        self.assertEqual(self.res["real"], [True, 0])

    def test_T16_AC5_AC9_TA2_labels_one_function_and_dst_uses_elapsed_time(self):
        self.assertEqual(self.res["labels"], ["night · 14 h 40 min", "weekend · 38 h 53 min", "idle · 25 min", "idle · 25 min"])
        self.assertEqual(self.res["dst"], [["idle · 3 h"]] * 3)   # the same string in two zones and UTC
        self.assertEqual(self.res["naive"], 4)                    # local subtraction in Berlin would have said 4 h

    def test_T16_AC3_AC4_AC7_TA1_ranges(self):
        p = self.res["presets"]
        now = 1793786400   # 2026-11-04T10:00:00Z
        self.assertEqual(p[0], {"from": now - 3600, "to": now, "preset": "1h"})
        self.assertEqual(p[1]["from"], now - 17 * 3600)              # 17:00 at +07: local midnight is 17 h before
        self.assertEqual(p[2]["from"], now - 3 * 86400)
        self.assertEqual((p[3]["from"], p[4]), (None, None))
        self.assertEqual(self.res["berlinToday"], 0)                 # a 23 h day
        self.assertEqual(self.res["zoom"][0], {"from": 1250, "to": 1750})
        self.assertEqual(self.res["zoom"][1], {"from": 1000, "to": 1500})   # the anchor keeps its place
        self.assertEqual(self.res["zoom"][2], {"from": 500, "to": 2500})
        self.assertEqual(self.res["zoom"][3], {"from": 10, "to": 190})        # never narrower than 3 min
        self.assertEqual(self.res["drag"], [{"from": 1100, "to": 1300}, {"from": 1100, "to": 1300}, None])
        f = self.res["filter"]
        self.assertTrue(0 < f[0] < f[4])
        self.assertEqual((f[1], f[2], f[3]), (True, True, 0))

    def test_T16_TA1_the_two_real_samples_of_ticket_15(self):
        r = self.res["real2"]
        self.assertEqual(len(r["breaks"]), 1)
        self.assertGreater(r["breaks"][0], 11 * 3600)
        self.assertTrue(r["filter"])
        self.assertEqual(r["secs"], r["want"])

    def test_T16_TA7_layout_is_fast_and_merging_keeps_the_time(self):
        p = self.res["perf"]
        self.assertGreater(p["ms"], 0)   # performance.now() is not frozen by the harness
        self.assertLess(p["ms"], 200, p)
        self.assertLess(p["out"], p["in"])
        self.assertEqual(p["sec"], p["sum"])

    def test_T16_TA1_scale_gives_a_break_a_fixed_share(self):
        n, x0, x1, t = self.res["scale"]
        self.assertEqual(n, 1)
        self.assertEqual(x0, 0)
        self.assertAlmostEqual(x1, 1, places=6)
        self.assertAlmostEqual(t, 300, delta=1)


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser test skipped")
class Page(unittest.TestCase):
    """One scripted session on the real reader output: lanes, blocks, marks, breaks, zoom, filter, writes."""

    @classmethod
    def setUpClass(cls):
        cls.res = run_page("""
const o={};
await startPage();
const txt=e=>e?e.textContent:null;
o.rows=$$('.tl-row[data-agent]').map(r=>r.dataset.agent);
o.groups=$$('.tl-row.grp .lab').map(l=>l.textContent);
const dev=$('.tl-row[data-agent=dev]');
const b03=Array.from(dev.querySelectorAll('.blk[data-task="03"]'));
o.b03={n:b03.length,approx:b03.every(b=>b.dataset.approx==='true'),states:[...new Set(b03.map(b=>b.dataset.state))]};
o.titles=b03.slice(0,1).map(b=>b.title);
o.marks=$$('.tl-row[data-agent] .mk').map(m=>m.dataset.kind);
o.marksApprox=$$('.mk').some(m=>m.dataset.approx||/approx/.test(m.title)||/approx/.test(m.textContent));
o.legend=$$('.tl-leg i.mk').map(i=>i.className.replace('mk ','')).concat($$('.tl-leg span').map(s=>s.textContent).filter(t=>/working|waiting|blocked on|idle|collapsed/.test(t)));
o.ghost=txt($('.tl-row[data-agent=ghost] .tl-trk'));
o.brk=$$('.brk span').map(s=>s.textContent);
o.po={n:$$('.blk.st-p').length,w:$$('.blk.st-p').map(b=>b.offsetWidth)};
const un=$$('.tl-tbl tr').find(r=>/unattributed/.test(r.textContent));
o.unattr=un?un.textContent:null;o.pct=/%/.test($('.tl').textContent);
o.approxTbl=$$('.tl-tbl .ap').length;
// AC1: a click shows task, start and end in local time
b03[0].click();await sleep(50);
o.detail=txt($('.tl-detail'));
o.hlAfterClick=T.state.hl;
T.setTask(null);
// AC5: show real time removes the breaks
$('button[data-real]').click();await sleep(50);o.brkReal=$$('.brk').length;
$('button[data-real]').click();await sleep(50);o.brkBack=$$('.brk').length;
// AC3: presets
$$('button[data-preset]').find(b=>b.dataset.preset==='1h').click();await sleep(150);
o.p1h=calls.filter(c=>c.u.startsWith('/api/worktime')).slice(-1)[0].u;
o.axis={days:$$('.dy').map(d=>d.title),ticks:$$('.tl-axis .ticks span').map(s=>s.textContent),rng:txt($('.tl-rng'))};
$$('button[data-preset]').find(b=>b.dataset.preset==='all').click();await sleep(150);
// AC8: the setting
const sel=$('.tl-gap select');
const gaps=[];
for(const v of ['15','240','60']){sel.value=v;sel.dispatchEvent(new Event('change',{bubbles:true}));await sleep(150);gaps.push([v,$$('.brk').length,calls.filter(c=>c.u.startsWith('/api/worktime')).slice(-1)[0].u])}
o.gaps=gaps;
// AC7: filter stays while zooming
$$('.tl-bar .tc').find(b=>b.textContent==='03').click();await sleep(50);
T.zoomAt(.5,.5);await sleep(150);
o.afterZoom={hl:T.state.hl,chipOn:!!$$('.tl-bar .tc.on').find(b=>b.textContent==='03'),dim:$$('.blk.dim').length,url:calls.filter(c=>c.u.startsWith('/api/worktime')).slice(-1)[0].u};
T.setTask(null);
// AC4: drag on the axis zooms, Ctrl+wheel zooms, the plain wheel does not
const n0=calls.length;T.dragZoom(100,400,900);await sleep(150);
o.drag=calls.slice(n0).map(c=>c.u);
const ch=$('.tl-chart');
const plain=new WheelEvent('wheel',{deltaY:100,bubbles:true,cancelable:true,clientX:300});ch.dispatchEvent(plain);
o.plainPrevented=plain.defaultPrevented;
const n1=calls.length;
const ctrl=new WheelEvent('wheel',{deltaY:-100,ctrlKey:true,bubbles:true,cancelable:true,clientX:300});$('.tl-chart').dispatchEvent(ctrl);
o.ctrlPrevented=ctrl.defaultPrevented;await sleep(400);
o.wheel=calls.slice(n1).map(c=>c.u);
// TA3: an older answer that arrives last is dropped
const r1={from:111,to:R.now-500},r2={from:222,to:R.now-100};
slow={from:111,ms:400};
const pa=T.zoomTo(r1),pb=T.zoomTo(r2);await Promise.all([pa,pb]);await sleep(600);
o.stale={from:T.state.data.from,to:T.state.data.to,rng:txt($('.tl-rng'))};slow=null;
// TA5: saved state goes through PUT /api/ui
T.setGap(15);await sleep(150);
fakeTimers.filter(t=>t.ms===300).forEach(t=>t.f());await sleep(100);
o.calls=calls.map(c=>[c.m,c.u.split('?')[0],c.u.indexOf('scope=dev')>=0,c.u.indexOf('squad=fix')>=0]);
o.put=calls.filter(c=>c.m==='PUT').slice(-1).map(c=>JSON.parse(c.b).timeline);
out(o);""", {"wt": rich(), "dst": dst(), "now": NOW})

    def test_T16_AC1_AC10_lanes_blocks_and_no_transcript(self):
        r = self.res
        self.assertEqual(r["rows"], ["dev", "qa", "ghost"][:1] + ["qa", "ghost"][:0] + r["rows"][1:])
        self.assertEqual(sorted(r["rows"]), ["dev", "ghost", "qa"])
        self.assertTrue(r["b03"]["n"] > 0 and r["b03"]["approx"])
        self.assertTrue({"working", "waiting"} <= set(r["b03"]["states"]))
        self.assertEqual([g.split(" ")[0] for g in r["groups"]], ["Developers", "QA"])
        self.assertRegex(r["titles"][0], r"^dev · .* · \d\d:\d\d–\d\d:\d\d \(.*\) · working · task 03 \(approx\)$")
        self.assertIn("no transcript: ghost", r["ghost"])
        self.assertRegex(r["detail"], r"Task\s*03")
        self.assertRegex(r["detail"], r"Start\s*\d{4}-\d\d-\d\d \d\d:\d\d \(UTC\)")
        self.assertRegex(r["detail"], r"End\s*\d{4}-\d\d-\d\d \d\d:\d\d \(UTC\)")

    def test_T16_AC2_approx_on_every_task_block_and_on_no_mark_unattributed_in_hours_minutes(self):
        r = self.res
        self.assertTrue(r["b03"]["approx"])
        self.assertEqual(sorted(set(r["marks"])), ["blocked", "fail", "handin", "pass"])
        self.assertFalse(r["marksApprox"])
        self.assertRegex(r["unattr"], r"\d+ h \d+ min of \d+ h \d+ min working time has no task")
        self.assertFalse(r["pct"])

    def test_T16_legend_names_every_state_and_mark(self):
        text = " | ".join(self.res["legend"])
        for w in ("working", "waiting", "blocked on a peer", "blocked on you", "idle", "collapsed gap"):
            self.assertIn(w, text)
        self.assertTrue({"handin", "fail", "pass", "blocked", "commit", "merge"} <= set(self.res["legend"]))

    def test_T16_AC5_AC6_hatched_breaks_by_the_setting_and_the_po_night_stays(self):
        r = self.res
        self.assertEqual(r["brk"], ["idle · 1 h 1 min", "night · 4 h 1 min", "night · 14 h 40 min"])
        self.assertEqual((r["brkReal"], r["brkBack"]), (0, 3))
        self.assertGreaterEqual(r["po"]["n"], 1)   # a BLOCKED message splits the night into two pieces
        self.assertGreater(max(r["po"]["w"]), 20)

    def test_T16_AC8_setting_15_min_and_4_h(self):
        g = {v: n for v, n, _ in self.res["gaps"]}
        self.assertEqual((g["15"], g["240"], g["60"]), (4, 2, 3))
        self.assertTrue(all(("gap_min=" + v) in u for v, _, u in self.res["gaps"]))

    def test_T16_AC3_preset_range_and_axis_in_local_time(self):
        r = self.res
        self.assertIn("from=%d&to=%d" % (NOW - 3600, NOW), r["p1h"])
        self.assertTrue(r["axis"]["days"])
        self.assertTrue(all(re.match(r"^\d\d:\d\d$", t) for t in r["axis"]["ticks"]) and r["axis"]["ticks"])
        self.assertRegex(r["axis"]["rng"], r"[A-Z][a-z]{2} \d+ [A-Z][a-z]{2} \d\d:\d\d → ")

    def test_T16_AC7_TA3_filter_stays_while_zooming_and_zoom_is_one_request_with_the_selection(self):
        z = self.res["afterZoom"]
        self.assertEqual(z["hl"], "03")
        self.assertTrue(z["chipOn"])
        self.assertIn("scope=dev", z["url"])
        self.assertIn("squad=fix", z["url"])
        self.assertRegex(z["url"], r"from=\d+&to=\d+")

    def test_T16_AC4_TA3_drag_and_ctrl_wheel_zoom_the_plain_wheel_does_not(self):
        r = self.res
        self.assertEqual(len(r["drag"]), 1)
        self.assertRegex(r["drag"][0], r"/api/worktime\?from=\d+&to=\d+&gap_min=60&squad=fix&scope=dev")
        self.assertFalse(r["plainPrevented"])
        self.assertTrue(r["ctrlPrevented"])
        self.assertEqual(len(r["wheel"]), 1)   # one request once the wheel rests

    def test_T16_TA3_an_older_answer_arriving_last_is_dropped(self):
        s = self.res["stale"]
        self.assertEqual((s["from"], s["to"]), (222, NOW - 100))

    def test_T16_TA5_only_get_worktime_and_put_ui_are_called_and_the_setting_is_saved(self):
        paths = {(m, p) for m, p, _, _ in self.res["calls"]}
        self.assertEqual(paths, {("GET", "/api/session"), ("GET", "/api/squads"), ("GET", "/api/ui"), ("GET", "/api/worktime"),
                                 ("PUT", "/api/ui")})
        self.assertTrue(all(sc and sq for m, p, sc, sq in self.res["calls"] if p == "/api/worktime"))
        self.assertEqual(self.res["put"][0]["gap_min"], 15)


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser test skipped")
class Safety(unittest.TestCase):
    def test_T27_filter_block_look_active_chip_sticky_opaque_no_percent(self):
        r = run_page("""
await startPage();
const tok=n=>{const e=document.createElement('i');e.style.background='var(--'+n+')';e.style.borderColor='var(--'+n+')';e.style.color='var(--'+n+')';document.body.appendChild(e);const c=getComputedStyle(e);const o={bg:c.backgroundColor,bc:c.borderTopColor,c:c.color};e.remove();return o};
const bar=$('.tl-bar'),cs=getComputedStyle(bar),px=v=>parseFloat(v);
const on=$$('.tl-bar .tc.on')[0],off=$$('.tl-bar .tc').find(b=>!b.classList.contains('on')),ons=getComputedStyle(on),offs=getComputedStyle(off);
const rows=Array.from(bar.querySelectorAll('.tl-r')).map(r=>r.getBoundingClientRect().height);
const fs=px(offs.fontSize);
out({bar:{bg:cs.backgroundColor,bw:cs.borderTopWidth,bc:cs.borderTopColor,rad:px(cs.borderTopLeftRadius),pad:[cs.paddingTop,cs.paddingRight,cs.paddingBottom,cs.paddingLeft].map(px),pos:cs.position,top:cs.top},
 on:{bg:ons.backgroundColor,bc:ons.borderTopColor,c:ons.color,w:ons.fontWeight},off:{bg:offs.backgroundColor,bc:offs.borderTopColor,w:offs.fontWeight,h:px(offs.height)/fs,padx:px(offs.paddingLeft)/fs},
 tok:{panel2:tok('panel2'),border:tok('border'),bg:tok('bg'),need:tok('t-need'),mango:tok('mango'),ink:tok('ink')},
 pct:/%/.test(bar.textContent),rows:rows.length,real:!!bar.querySelector('.tl-rng button[data-real]'),
 tips:Array.from(bar.querySelectorAll('.seg button')).map(b=>b.title)});""", {"wt": rich(), "dst": {}, "now": NOW})
        t = r["tok"]
        self.assertEqual((r["bar"]["bg"], r["bar"]["bc"], r["bar"]["bw"]), (t["panel2"]["bg"], t["border"]["bc"], "1px"))
        self.assertNotEqual(r["bar"]["bg"], "rgb(255, 255, 255)")
        self.assertEqual(r["bar"]["rad"], 8)
        self.assertTrue(all(x >= 8 for x in r["bar"]["pad"]), r["bar"]["pad"])
        self.assertEqual((r["bar"]["pos"], r["bar"]["top"]), ("sticky", "-2px"))   # pulled up by the panel body top padding (F1)
        self.assertEqual((r["on"]["bg"], r["on"]["bc"], r["on"]["c"], r["on"]["w"]), (t["need"]["bg"], t["mango"]["bc"], t["ink"]["c"], "700"))
        self.assertEqual((r["off"]["bg"], r["off"]["bc"]), (t["bg"]["bg"], t["border"]["bc"]))
        self.assertLess(int(r["off"]["w"]), 600)
        self.assertGreaterEqual(r["off"]["h"], 2.19)
        self.assertGreaterEqual(r["off"]["padx"], 0.84)
        self.assertFalse(r["pct"])
        self.assertTrue(r["real"])
        self.assertEqual(r["tips"], ["Zoom out", "Zoom in", "Earlier", "Later"])

    def test_T40_TA1_TA2_TA3_pills_and_segments_are_round_and_not_clipped(self):
        body = """
await startPage();
%(setup)s
await sleep(80);
const px=v=>parseFloat(v),B=$('.tl-bar'),rd=e=>{const c=getComputedStyle(e);return ['TopLeft','TopRight','BottomRight','BottomLeft'].map(k=>px(c['border'+k+'Radius']))};
const tok=n=>{const e=document.createElement('i');e.style.background='var(--'+n+')';e.style.borderColor='var(--'+n+')';document.body.appendChild(e);const c=getComputedStyle(e);const o={bg:c.backgroundColor,bc:c.borderTopColor};e.remove();return o};
const chips=$$('.tl-bar .tc').map(e=>({t:e.textContent,h:e.getBoundingClientRect().height,r:rd(e),on:e.classList.contains('on')}));
const segs=$$('.tl-bar .seg').map(g=>{const b=g.querySelectorAll('button'),f=b[0],l=b[b.length-1],gc=getComputedStyle(g);
 const walk=[];for(let n=g.parentNode;n&&n!==B.parentNode;n=n.parentNode)walk.push(getComputedStyle(n).overflow);
 return {n:b.length,bw:gc.borderTopWidth,ov:gc.overflow,walk,h:f.getBoundingClientRect().height,fr:rd(f),lr:rd(l),frw:getComputedStyle(f).borderRightWidth,llw:getComputedStyle(l).borderLeftWidth,top:[f.offsetTop,l.offsetTop],whole:Math.abs(f.getBoundingClientRect().top-l.getBoundingClientRect().top)<1}});
const clipper=e=>{for(let n=e.parentNode;n&&n.nodeType===1;n=n.parentNode){if(getComputedStyle(n).overflow!=='visible')return n}return document.documentElement};
const find=t=>$$('.tl-bar .tc').find(x=>x.textContent===t),sb=$$('.tl-bar .seg button');
const ring={};
for(const [k,e] of [['minus',sb[0]],['next',sb[3]],['all',find('All')],['alltasks',find('All tasks')]]){e.focus();const r=e.getBoundingClientRect(),c=getComputedStyle(e),cb=clipper(e).getBoundingClientRect();
 ring[k]={rad:rd(e),out:c.outlineWidth,h:r.height,inside:r.left-2>=Math.max(cb.left,0)&&r.right+2<=Math.min(cb.right,innerWidth)&&r.top-2>=Math.max(cb.top,0),focus:document.activeElement===e}}
document.activeElement.blur();
/* :hover cannot be set from a script: copy every :hover rule of the page to a class and put the class on the control */
let hovRules=0;for(const ss of document.styleSheets){for(const r of Array.from(ss.cssRules)){if(r.selectorText&&r.selectorText.includes(':hover')){hovRules++;ss.insertRule(r.cssText.replace(/:hover/g,'.__hov'),ss.cssRules.length)}}}
const hov={};
for(const [k,e] of [['minus',sb[0]],['plus',sb[1]],['next',sb[3]],['all',find('All')],['alltasks',find('All tasks')]]){e.classList.add('__hov');const c=getComputedStyle(e);
 hov[k]={rad:rd(e),bc:c.borderTopColor,h:e.getBoundingClientRect().height,ov:getComputedStyle(e.parentNode).overflow};e.classList.remove('__hov')}
const on=$$('.tl-bar .tc.on')[0],ons=getComputedStyle(on);
const outside=$$('.seg').filter(x=>!B.contains(x)).map(x=>{const c=getComputedStyle(x);return [c.borderTopLeftRadius,c.overflow]});
const pw=$('.tl').parentNode.getBoundingClientRect().width;
out({chips,segs,ring,hov,hovRules,pw,active:{bg:ons.backgroundColor,bc:ons.borderTopColor},tok:{need:tok('t-need'),mango:tok('mango'),ink:tok('ink')},outside});"""
        # Narrow panel = the Work time panel's parent box set to 330 px, the width T36's one-column handle gives (measured below, <= 360).
        cases = [("1440,900", "", "1440x900 Normal"), ("1000,700", "", "1000x700 Normal"),
                 ("1000,700", "$('.tl').style.fontSize='20.8px';", "1000x700 Extra large"),
                 ("1440,900", "$('.tl').parentNode.style.width='330px';", "1440x900 narrow panel 330 px")]
        for size, setup, name in cases:
            r = run_page(body % {"setup": setup}, {"wt": rich(), "dst": {}, "now": NOW}, size=size)
            self.assertGreaterEqual(len(r["chips"]), 8, name)   # an empty loop cannot pass
            self.assertEqual(len(r["segs"]), 2)
            if "narrow" in name:
                self.assertLessEqual(r["pw"], 360, r["pw"])
            for c in r["chips"]:
                self.assertTrue(all(x >= c["h"] / 2 for x in c["r"]), (c, name))
            self.assertTrue(any(c["on"] for c in r["chips"]), name)   # the active chip is among the pills checked above
            for g in r["segs"]:
                h = g["h"] / 2
                self.assertEqual((g["n"], g["bw"], g["ov"], g["frw"], g["llw"]), (2, "0px", "visible", "1px", "0px"), (g, name))
                self.assertTrue(all(o == "visible" for o in g["walk"]), g["walk"])   # nothing between the buttons and the bar clips
                self.assertEqual(g["top"][0], g["top"][1])
                self.assertTrue(g["whole"], (g, name))   # both buttons on one line
                self.assertTrue(g["fr"][0] >= h and g["fr"][3] >= h and g["fr"][1] == 0 and g["fr"][2] == 0, g["fr"])
                self.assertTrue(g["lr"][1] >= h and g["lr"][2] >= h and g["lr"][0] == 0 and g["lr"][3] == 0, g["lr"])
                if "Extra" not in name:
                    self.assertAlmostEqual(g["h"], 26, delta=1)   # 2.2 em at Normal text
            self.assertEqual(set(r["ring"]), {"minus", "next", "all", "alltasks"})
            for k, v in r["ring"].items():
                self.assertTrue(v["focus"] and v["out"] == "2px" and v["inside"], (k, v, name))
                if k in ("all", "alltasks"):   # the PO's "All" pill, focused
                    self.assertTrue(all(x >= v["h"] / 2 for x in v["rad"]), (k, v, name))
            self.assertGreaterEqual(r["hovRules"], 1)   # hover rules exist, so the class copy proves something
            rest = {"minus": r["segs"][0]["fr"], "plus": r["segs"][0]["lr"], "next": r["segs"][1]["lr"]}
            for k, v in r["hov"].items():
                self.assertEqual(v["bc"], r["tok"]["ink"]["bc"], (k, v, name))   # the hover rule applied
                if k in rest:
                    self.assertEqual((v["rad"], v["ov"]), (rest[k], "visible"), (k, v, name))   # same corners as at rest
                else:
                    self.assertTrue(all(x >= v["h"] / 2 for x in v["rad"]), (k, v, name))
            t = r["tok"]
            self.assertEqual((r["active"]["bg"], r["active"]["bc"]), (t["need"]["bg"], t["mango"]["bc"]))
            for o in r["outside"]:
                self.assertEqual(o, ["8px", "hidden"])   # Text size / Sort keep their 8px box
            self.assertTrue(r["outside"], "no .seg outside the bar found")

    def test_T27_TA2_TA3_TA4_three_sizes_narrow_wrap_and_sticky_in_a_scrolling_panel(self):
        r = run_page("""
await startPage();
const tl=$('.tl'),px=v=>parseFloat(v),o={sizes:[],narrow:null};
const H=()=>$('.tl').parentNode;H().style.cssText+=';height:300px;overflow:auto;position:relative;padding:2px 10px 8px';
const B=()=>$('.tl-bar');const ctl=()=>Array.from(B().querySelectorAll('button,select'));
const hit=(a,b)=>a.left<b.right-.5&&b.left<a.right-.5&&a.top<b.bottom-.5&&b.top<a.bottom-.5;
const probe=()=>{const bar=B(),bc=bar.getBoundingClientRect(),rs=ctl().map(c=>c.getBoundingClientRect());let ov=0;
  for(let i=0;i<rs.length;i++)for(let j=i+1;j<rs.length;j++)if(hit(rs[i],rs[j]))ov++;
  return {w:Math.round(bc.width),ov:ov,cut:rs.filter(r=>r.right>bc.right+.5||r.left<bc.left-.5).length,rows:Array.from(bar.querySelectorAll('.tl-r')).slice(0,2).map(r=>new Set(Array.from(r.querySelectorAll('button')).map(b=>Math.round(b.getBoundingClientRect().top))).size)}};
for(const f of [0.9,1,1.3]){
  $('.tl').style.fontSize=(16*f)+'px';H().style.width='700px';await sleep(50);
  const c=$$('.tl-bar .tc').find(b=>!b.classList.contains('on')),cs=getComputedStyle(c),fs=px(cs.fontSize),bs=getComputedStyle(B());const bar=B();
  const first=bar.querySelector('.tl-r .tc').getBoundingClientRect(),bc=bar.getBoundingClientRect();
  o.sizes.push({f:f,pad:[bs.paddingTop,bs.paddingRight,bs.paddingBottom,bs.paddingLeft].map(px),h:px(cs.height)/fs,padx:px(cs.paddingLeft)/fs,inset:first.left-bc.left,bw:bs.borderTopWidth,probe:probe()});
}
$('.tl').style.fontSize='16px';H().style.width='330px';await sleep(50);o.narrow=probe();
H().style.width='700px';await sleep(50);
const wrap=H();o.tall=wrap.scrollHeight;wrap.scrollTop=200;await sleep(50);
const bar=B(),wb=wrap.getBoundingClientRect(),bb=bar.getBoundingClientRect();
o.sticky={gap:bb.top-wb.top,scrolled:wrap.scrollTop,bg:getComputedStyle(bar).backgroundColor};
out(o);""", {"wt": rich(), "dst": {}, "now": NOW})
        for z in r["sizes"]:
            self.assertTrue(all(x >= 8 for x in z["pad"]), z)
            self.assertGreaterEqual(z["h"], 2.19)
            if z["f"] <= 1:
                self.assertEqual(z["probe"]["rows"], [1, 1], z)   # Task and View: one line each at the panel width (Extra large may wrap)
            self.assertGreaterEqual(z["padx"], 0.84)
            self.assertGreaterEqual(z["inset"], 8)
            self.assertEqual((z["probe"]["ov"], z["probe"]["cut"]), (0, 0), z)
        self.assertGreater(max(r["narrow"]["rows"]), 1)   # the View row needs a second line
        self.assertEqual((r["narrow"]["ov"], r["narrow"]["cut"]), (0, 0))   # 1000 px window: rows wrap, nothing overlaps or is cut
        self.assertGreater(r["tall"], 300)
        self.assertGreaterEqual(r["sticky"]["scrolled"], 150)
        self.assertLess(abs(r["sticky"]["gap"]), 1.5, r["sticky"])
        self.assertTrue(r["sticky"]["bg"].startswith("rgb("), r["sticky"])   # alpha 1: no rgba

    def test_T16_AC9_TA2_the_page_reads_its_own_zone_across_a_clock_change(self):
        for z in ("Europe/Berlin", "America/New_York"):
            r = run_page("""
const z=BOARD.readZone(),dp=R.dst.data.agents[0].pieces;
out({z:z,l:T.collapse(dp,60,false,z).breaks.map(b=>b.label)});""", {"wt": rich(), "dst": dst(), "now": NOW}, tz=z)
            self.assertEqual((r["z"], r["l"]), (z, ["idle · 3 h"]))

    def test_T16_TU8_a_zoom_answered_with_another_version_or_nothing_shows_unknown(self):
        r = run_page("""
await startPage();window.__v2=true;await T.zoomAt(.5,.5);await sleep(100);
const v=$('.tl .note').textContent;window.__v2=false;window.__unk=true;await T.zoomAt(.5,.5);await sleep(100);
out({v:v,u:$('.tl .note').textContent,nodata:($('.tl-trk.nodata')||{}).textContent,bar:!!$('.tl-bar')});""", {"wt": rich(), "dst": {}, "now": NOW})
        self.assertEqual(r["v"], "unknown: board version")
        self.assertIn("unknown: transcript", r["u"])
        self.assertIn("No time is invented", r["nodata"])
        self.assertTrue(r["bar"])

    def test_T16_TA4_untrusted_names_stay_text(self):
        r = run_page("""
payload=R.evil;await startPage();
const o={img:$$('img').length,x:window.__x===undefined,labs:$$('.tl-row[data-agent] .lab .ln').map(e=>e.textContent),
 nodata:$$('.tl-trk.nodata').map(e=>e.textContent),titles:$$('.blk').slice(0,1).map(b=>b.title)};
out(o);""", {"wt": rich(), "evil": evil(), "dst": {}, "now": NOW})
        self.assertEqual(r["img"], 0)
        self.assertTrue(r["x"])
        self.assertIn("<img src=x onerror=window.__x=1>", r["labs"])
        self.assertEqual(r["nodata"], ["no transcript: g<b>x"])
        self.assertIn("<img src=x onerror=window.__x=1>", r["titles"][0])

    def test_T16_TA6_odd_pieces_show_as_unknown_and_log_once(self):
        r = run_page("""
const p=JSON.parse(JSON.stringify(R.wt));const ps=p.data.agents[0].pieces;
delete ps[0].end;ps[1].bucket='bogus';ps[2].bucket='bogus';payload=p;await startPage();
out({unk:$$('.blk[data-state=unknown]').length,warns:window.__warns,rows:$$('.tl-row[data-agent]').length});""",
                     {"wt": rich(), "dst": {}, "now": NOW})
        self.assertEqual(r["unk"], 2)   # the two touching "bogus" pieces draw as one block; the piece with no end is its own
        self.assertEqual(len(r["warns"]), 2)   # one line per kind (no end, bucket), not per piece
        self.assertEqual(r["rows"], 3)

    def test_T16_AC4_AC7_a_custom_range_survives_the_next_poll(self):
        r = run_page("""
await startPage();T.zoomAt(.5,.5);await sleep(200);
const a=$$('.blk').length;
for(let i=0;i<2;i++){fakeTimers.filter(t=>t.ms===5000).forEach(t=>t.f());await sleep(300);}
const after=$$('.blk').length;
$$('.blk[data-task]')[0].click();await sleep(50);const had=!!$('.tl-detail dl');
T.zoomAt(.5,2);await sleep(200);
out({a:a,after:after,lanes:$$('.tl-row[data-agent]').length,detailGone:!$('.tl-detail dl'),had:had,scope:$$('.tl-row[data-agent] .lab small').length>0});""",
                     {"wt": rich(), "dst": {}, "now": NOW})
        self.assertGreater(r["a"], 0)
        self.assertEqual(r["after"], r["a"])   # the poll after a zoom did not blank the panel
        self.assertEqual(r["lanes"], 3)
        self.assertTrue(r["had"] and r["detailGone"])   # the detail card goes when the range changes
        self.assertTrue(r["scope"])

    def test_T16_TA7_an_unchanged_poll_does_not_redraw(self):
        r = run_page("""
await startPage();const a=$('.tl');
const tick=fakeTimers.filter(t=>t.ms===5000).pop();tick.f();await sleep(300);
out({same:$('.tl')===a,n:calls.filter(c=>c.u.startsWith('/api/worktime')).length});""", {"wt": rich(), "dst": {}, "now": NOW})
        self.assertTrue(r["same"])
        self.assertEqual(r["n"], 2)   # the poll did ask again

    def test_T16_AC10_TU8_real_long_gap_sample_folds_the_night(self):
        r = run_page("""
payload=R.real;await startPage();
out({brk:$$('.brk span').map(s=>s.textContent),rows:$$('.tl-row[data-agent]').map(r=>r.dataset.agent),ghost:($('.tl-row[data-agent=ghost] .tl-trk')||{}).textContent});""",
                     {"wt": rich(), "real": real_long_gap(), "dst": {}, "now": 1792552000})
        self.assertEqual(len(r["brk"]), 1)
        self.assertRegex(r["brk"][0], r"^(night|idle|weekend) · 11 h \d+ min$")
        self.assertIn("no transcript: ghost", r["ghost"])

    def test_T16_TA8_cutting_the_panel_leaves_the_page_working(self):
        r = run_page("""
await startPage();
out({ok:!!$('#canvas'),t:typeof BOARD.TIMELINE,panels:BOARD.panels.map(p=>p.id)});""", {"wt": rich(), "dst": {}, "now": NOW},
                     scripts='<script src="file://%(tpl)s/board.js"></script><script src="file://%(tpl)s/layout.js"></script>')
        self.assertEqual((r["ok"], r["t"], r["panels"]), (True, "undefined", []))


class Static(unittest.TestCase):
    def test_T16_TU3_TU4_TU5_no_markup_strings_no_remote_no_writes(self):
        js = (TPL / "timeline.js").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(|new Function", js))
        self.assertIsNone(re.search(r"https?://", js))
        self.assertIsNone(re.search(r"method\s*:", js))          # the view never sets a method: GET only, the page owns PUT
        self.assertIsNone(re.search(r"\bon(click|error|load)\s*=", js))
        self.assertNotIn("\r", js)
        self.assertFalse(js.startswith("\ufeff"))
        self.assertIn('id: "worktime"', js)


if __name__ == "__main__":
    unittest.main()
