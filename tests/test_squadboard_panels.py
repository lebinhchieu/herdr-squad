"""Picker and views (ticket 11). Pure rules and the page are driven in headless Chrome on a small harness that loads the
real templates/board/*.js (pattern of test_squadboard_page.py). The data is the real answer of the squadboard routes on the
ticket-02 fixture. Tickets 12 and 13 append their sections. Tests are named for the business AC (T11.ACn) or technical AC."""
import json
import re
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
from test_squadboard_page import CHROME, TPL  # noqa: E402

HEAD = """<!doctype html><meta charset=utf-8>
<link rel=stylesheet href="file://%(tpl)s/board.css">
<div id=app></div><pre id=out></pre>
<script>window.BOARD_NO_AUTOSTART=true;window.__real=%(real)s;</script>
<script src="file://%(tpl)s/board.js"></script><script src="file://%(tpl)s/layout.js"></script><script src="file://%(tpl)s/panel_scopes.js"></script>
<script>
const out=v=>{document.getElementById('out').textContent=JSON.stringify(v)};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const R=window.__real;
const fakeTimers=[];let tid=0;
const fk={setTimeout:(f,ms)=>{fakeTimers.push({id:++tid,f,ms});return tid},clearTimeout:id=>{const i=fakeTimers.findIndex(t=>t.id===id);if(i>=0)fakeTimers.splice(i,1)}};
const mem=()=>{const m={};return{getItem:k=>(k in m?m[k]:null),setItem:(k,v)=>{m[k]=String(v)}}};
const cur={squads:R.squads,checks:Object.assign({},R.checks),saved:R.saved||null};
const J=o=>({ok:true,status:200,json:async()=>Object.assign({schema_version:1,unknown:[],quality:'exact'},o)});
const fetchStub=async(url,opt)=>{
  if(opt&&opt.method==='PUT')return J({data:{ui:JSON.parse(opt.body),status:'ok'}});
  if(url.startsWith('/api/session'))return J({data:{token:'t'}});
  const m=url.match(/^\\/api\\/squads\\?check=([^&]*)/);
  if(m){const n=decodeURIComponent(m[1]);return J({data:{check:cur.checks[n]||{name:n,exists:false,kind:null,where:null,message:'saved choice '+n+' not found'}}})}
  if(url.startsWith('/api/squads'))return J(cur.squads);
  if(url.startsWith('/api/ui'))return J({data:{ui:cur.saved,status:'ok'}});
  const s=url.match(/^\\/api\\/scopes\\?(.*)$/);
  if(s){const q=new URLSearchParams(s[1]);const k=q.get('goal')?'goal:'+q.get('goal'):'scope:'+q.get('scope');return J(R.scopes[k]||{data:null,unknown:['scope']})}
  return {ok:false,status:404,json:async()=>({schema_version:1,error:'nf'})};
};
const startPage=async()=>{
  BOARD.start({fetch:fetchStub,storage:mem(),setTimeout:fk.setTimeout,clearTimeout:fk.clearTimeout,now:()=>Date.parse('2026-11-04T10:00:00Z'),tz:'UTC'});
  await sleep(200);return BOARD.page;
};
const $=s=>document.querySelector(s), $$=s=>Array.from(document.querySelectorAll(s));
const key=(t,k)=>{const e=new KeyboardEvent('keydown',{key:k,bubbles:true,cancelable:true});t.dispatchEvent(e);return e};
(async()=>{try{
%(body)s
}catch(e){out({error:String(e&&e.stack||e)})}})();
</script>
"""


def run_page(body, real, suffix="", head=None):
    with tempfile.TemporaryDirectory() as d:
        page = Path(d) / "page.html"
        page.write_text((head or HEAD) % {"tpl": str(TPL), "real": json.dumps(real), "body": body}, encoding="utf-8")
        r = subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--allow-file-access-from-files",
                            "--virtual-time-budget=8000", "--window-size=1440,900", "--dump-dom",
                            "file://" + str(page) + suffix], capture_output=True, text=True, timeout=90)
    assert r.returncode == 0, r.stderr[-500:]
    m = re.search(r'<pre id="out">(.*?)</pre>', r.stdout, re.S)
    assert m, r.stdout[-800:]
    import html
    res = json.loads(html.unescape(m.group(1)))
    assert "error" not in res, res["error"]
    return res


def real_payloads():
    """The real answers of the list routes on the fixture (ticket 02), saved as JSON for the page harness."""
    fx = board_fixtures.copy_fixture(git=False)
    squads = squadboard.find_squads([str(fx.squad)])
    srv = squadboard.BoardServer(0, squads, {})
    srv.routes, _ = squadboard.load_routes()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % srv.port
    try:
        def get(u):
            with urllib.request.urlopen(base + u, timeout=20) as r:
                return json.loads(r.read())
        sq = get("/api/squads")
        rows = sq["data"]["squads"][0]
        out = {"squads": sq, "scopes": {}, "checks": {}}
        for kind, name in (("goal", "alpha"), ("scope", "checkout"), ("scope", "alpha-api"), ("scope", "questions")):
            out["scopes"]["%s:%s" % (kind, name)] = get("/api/scopes?squad=fix&%s=%s" % (kind, name))
        done = [r for r in rows["done"] if r["kind"] == "scope"][0]
        out["done_scope"] = done["name"]
        out["checks"][done["name"]] = get("/api/squads?check=%s" % done["name"])["data"]["check"]
        out["checks"]["checkout"] = {"name": "checkout", "exists": True, "kind": "scope", "where": "live", "message": ""}
        return out
    finally:
        srv.shutdown()
        srv.server_close()
        board_fixtures.cleanup(fx)


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser test skipped")
class Pure(unittest.TestCase):
    """The rules are plain functions on BOARD (TU.1, T11.TA2)."""

    @classmethod
    def setUpClass(cls):
        cls.res = run_page("""
const B=BOARD,o={};
const rows=[{name:'inbox-view',brief:'x'},{name:'zeta',brief:'About the INBOX panel'},{name:'other',brief:'nothing'},{name:'Done-inbox',brief:'',status:'done'}];
o.filter=[B.filterRows(rows,'INBOX').map(r=>r.name),B.filterRows(rows,'').length,B.filterRows(rows,'xyz').length];
o.top=[B.topRow(B.filterRows(rows,'inbox')).name,B.topRow([])];
let rc=[];for(const n of ['a','b','c','d','e','f'])rc=B.pushRecent(rc,{kind:'scope',name:n});
o.recent6=rc.map(c=>c.name);o.recentTwice=B.pushRecent(B.pushRecent([],{kind:'scope',name:'a'}),{kind:'scope',name:'a'}).length;
o.hash=[B.parseHash('#/goal/G'),B.parseHash('#/scope/S1'),B.parseHash(''),B.parseHash('#/x/y'),B.parseHash('#/scope/'),B.parseHash('#/scope/%E0%A4%A')];
const ex=m=>c=>m[c.kind+':'+c.name]||'gone';
const S1={kind:'scope',name:'S1'},G={kind:'goal',name:'G'};
const oo=(f,h,s,m)=>{const r=B.openingOrder({flag:f,hash:h,saved:s,exists:ex(m)});return [r.source,r.choice&&r.choice.name,r.closed,r.notFound]};
o.open=[oo(null,null,S1,{'scope:S1':'open'}),oo(null,null,S1,{'scope:S1':'closed'}),oo(null,null,S1,{}),
  oo(G,null,S1,{'goal:G':'open','scope:S1':'open'}),oo(null,S1,{kind:'scope',name:'Z'},{'scope:S1':'open'}),
  oo(null,{kind:'scope',name:'nope'},S1,{'scope:S1':'open'}),oo(null,null,null,{})];
const f=t=>B.shouldFocusSearch(t);
o.focus=[f({tagName:'BODY'}),f({tagName:'INPUT'}),f({tagName:'TEXTAREA'}),f({tagName:'SELECT'}),f({tagName:'DIV',isContentEditable:true}),f({tagName:'SPAN',closest:()=>null}),f(null)];
out(o);
""", {"squads": {}, "scopes": {}, "checks": {}})

    def test_T11_AC3_filter_is_case_insensitive_on_name_or_brief_and_enter_target_is_the_top_row(self):
        self.assertEqual(self.res["filter"], [["inbox-view", "zeta", "Done-inbox"], 4, 0])
        self.assertEqual(self.res["top"], ["inbox-view", None])

    def test_T11_AC6_recent_keeps_five_newest_and_a_repeat_once(self):
        self.assertEqual(self.res["recent6"], ["f", "e", "d", "c", "b"])
        self.assertEqual(self.res["recentTwice"], 1)

    def test_T11_AC11_parse_hash(self):
        h = self.res["hash"]
        self.assertEqual(h[:2], [{"kind": "goal", "name": "G"}, {"kind": "scope", "name": "S1"}])
        self.assertEqual(h[2:], [None, None, None, None])

    def test_T11_AC7_to_AC11_opening_order_flag_url_saved_picker(self):
        self.assertEqual(self.res["open"], [
            ["saved", "S1", False, None],                              # AC7
            ["saved", "S1", True, None],                               # AC8 closed
            ["picker", None, False, "saved choice S1 not found"],      # AC9
            ["flag", "G", False, None],                                # AC10 flag beats saved
            ["url", "S1", False, None],                                # AC11 URL beats saved
            ["picker", None, False, "scope nope not found"],           # AC11 unknown name
            ["picker", None, False, None]])

    def test_T11_TA4_slash_is_ignored_in_text_fields(self):
        self.assertEqual(self.res["focus"], [True, False, False, False, False, True, True])


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser test skipped")
class Picker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real = real_payloads()
        cls.rows = cls.real["squads"]["data"]["squads"][0]
        cls.real["saved"] = None

    def test_T11_design_D1_D9_picker_sort_chips_two_lines_and_combobox(self):
        r = run_page("""
await startPage();await sleep(100);
const rowNames=()=>$$('#view .pr[data-name]').map(x=>x.dataset.name);
const sortBtns=$$('#view .pkbar .seg button').map(b=>b.textContent+':'+b.getAttribute('aria-pressed'));
const byLast=rowNames();$$('#view .pkbar .seg button')[2].click();await sleep(30);const byName=rowNames();
const row=$('#view .pr[data-name]');
const cells={chip:!!row.querySelector('.chip'),kind:row.querySelector('.kind').textContent,small:!!row.querySelector('.pla small')};
const expBtn=$('#view [data-exp-all]');const t1=expBtn.textContent;expBtn.click();await sleep(150);const t2=$('#view [data-exp-all]').textContent;
const subs=$$('#view .pr.sub').length;
const intro=$('#view .pk p.muted').textContent;
const hints=$$('#view h3.sec').map(h=>h.textContent);
$('#selbtn').click();await sleep(60);
const cb=$('#view .combo');const first=cb.querySelector('.cbo').getBoundingClientRect(),inp=cb.querySelector('input').getBoundingClientRect(),lst=$('#cbl').getBoundingClientRect();
const heads=$$('#cbl .cbh').map(h=>h.textContent);
const foot=cb.querySelector('.cbf').textContent;
out({sortBtns,byLast,byName,cells,t1,t2,subs,intro,hints,heads,foot,clipped:first.top<lst.top-1||first.top<inp.bottom,btn:$('#selbtn').getAttribute('role')});
""", self.real)
        self.assertEqual(r["sortBtns"], ["Last active:false", "Needs you:true", "Name:false"])
        self.assertNotEqual(r["byName"], r["byLast"])
        self.assertTrue(r["cells"]["chip"] and r["cells"]["small"])
        self.assertTrue(r["cells"]["kind"].startswith(("scope", "goal")))
        self.assertEqual((r["t1"], r["t2"]), ("Expand all open goals", "Collapse all goals"))
        self.assertGreater(r["subs"], 0)
        self.assertIn("The board shows one goal (with its scopes) or one scope.", r["intro"])
        self.assertTrue(any("what you opened last" in h or h.startswith("Open") for h in r["hints"]))
        self.assertEqual(r["heads"][-2:][1][:4], "▸ Do")
        self.assertIn("Open the picker", r["foot"])
        self.assertIn("↑ ↓ Enter · Esc", r["foot"])
        self.assertFalse(r["clipped"])
        self.assertEqual(r["btn"], "combobox")

    def test_T11_AC1_AC2_AC16_TA8_only_the_picker_shows_with_no_all_and_renders_fast(self):
        r = run_page("""
await startPage();
const t0=performance.now();BOARD.page.state.squad&&BOARD.ctx.paint();const ms=performance.now()-t0;
out({rows:$$('#view .plist .pr[data-name]').map(x=>x.dataset.name),done:$('#view .dnd summary b').textContent.trim(),doneN:$('#view .dnd summary .chip').textContent,doneLabel:$('#view .dnd summary').getAttribute('aria-label'),doneOpen:$('#view .dnd').open,
 mainHidden:$('main').hidden,panelsShown:$$('section.panel').filter(p=>!p.hidden).length,
 text:document.getElementById('app').textContent,ms,title:document.title,choice:BOARD.page.state.choice});
""", self.real)
        open_names = [x["name"] for x in self.rows["open"]]
        self.assertEqual(r["rows"][:len(open_names)], open_names)       # needs-you first, as the server sorts
        self.assertEqual(r["rows"][0], "questions")
        self.assertEqual((r["doneN"], r["doneLabel"]), ("20", "Done (20)"))
        self.assertEqual((r["done"], r["doneOpen"], r["mainHidden"], r["panelsShown"], r["choice"]), ("Done", False, True, 0, None))
        self.assertIsNone(re.search(r"\bAll\b", r["text"]))
        self.assertLess(r["ms"], 300)
        self.assertEqual(r["title"], "(1) fix")                          # the squad-wide needs-you count

    def test_T11_AC3_AC4_AC5_search_enter_nothing_matches_and_slash(self):
        word = "lone"
        pool = self.rows["open"] + self.rows["done"]
        expected = [x["name"] for x in pool if word in x["name"].lower() or word in x["brief"].lower()]
        self.assertTrue(expected, "fixture has no row for the search word")
        r = run_page("""
await startPage();
const inp=$('#pkq');
const slash=key(document.body,'/');const focused=document.activeElement===inp;
const inSlash=key(inp,'/');
inp.value="LONE";inp.dispatchEvent(new Event('input',{bubbles:true}));
const names=$$('#view .pr[data-name]').map(x=>x.dataset.name);
key(inp,'Enter');await sleep(100);
const chosen=BOARD.page.state.choice;
BOARD.page.state.choice=null;BOARD.ctx.paint();await sleep(50);
const inp2=$('#pkq');inp2.value='xyz';inp2.dispatchEvent(new Event('input',{bubbles:true}));
out({focused,slashPrevented:slash.defaultPrevented,inputPrevented:inSlash.defaultPrevented,names,chosen,none:$('#view .note:not([hidden])')&&Array.from($$('#view .note')).map(n=>n.textContent)});
""", self.real)
        self.assertEqual(r["names"], expected)
        self.assertEqual(r["chosen"]["name"], expected[0])
        self.assertTrue(r["focused"] and r["slashPrevented"])
        self.assertFalse(r["inputPrevented"])
        self.assertTrue(any(t.startswith("Nothing matches 'xyz'") for t in r["none"]))

    def test_T11_AC6_six_choices_show_the_last_five(self):
        names = [x["name"] for x in self.rows["open"] if x["kind"] == "scope"][:6]
        self.assertGreaterEqual(len(names), 6)
        r = run_page("""
const p=await startPage();const names=%s;
for(const n of names)p.setChoice('scope:'+n);
p.setChoice('scope:'+names[5]);
await sleep(50);
p.state.choice=null;BOARD.ctx.paint();await sleep(50);
out({recent:p.state.recent.map(c=>c.name),shown:(()=>{const h=$$('#view h3.sec')[0];let n=0,e=h.nextElementSibling;while(e&&e.classList.contains('pr')){n++;e=e.nextElementSibling}return n})(),first:$$('#view h3.sec')[0].firstChild.textContent});
""" % json.dumps(names), self.real)
        self.assertEqual(r["recent"], names[:0:-1])
        self.assertEqual((r["first"], r["shown"]), ("Recent", 5))


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser test skipped")
class Opening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real = real_payloads()

    def go(self, suffix="", saved=None, extra=""):
        real = dict(self.real, saved=saved)
        return run_page("""
await startPage();
%s
const S=BOARD.page.state;
out({choice:S.choice,closed:BOARD.viewState.closed,note:Array.from($$('#view .note')).filter(n=>!n.hidden).map(n=>n.textContent),
 ro:Array.from($$('#view .ro')).map(n=>n.textContent),x:window.__x===undefined,imgs:$$('#app img').length,hash:location.hash,extra:typeof ex==='undefined'?null:ex});
""" % extra, real, suffix)

    def saved(self, kind, name):
        return {"version": 1, "saved_at": "2026-11-03T10:00:00Z", "choice": {"kind": kind, "name": name}, "recent": [], "panels": {}}

    def test_T11_AC7_AC8_AC9_saved_choice_open_closed_gone(self):
        r = self.go(saved=self.saved("scope", "checkout"))
        self.assertEqual((r["choice"], r["closed"]), ({"kind": "scope", "name": "checkout"}, False))
        r = self.go(saved=self.saved("scope", self.real["done_scope"]))
        self.assertEqual((r["choice"]["name"], r["closed"]), (self.real["done_scope"], True))
        self.assertTrue(any("closed" in x for x in r["ro"]))
        r = self.go(saved=self.saved("scope", "S1"))
        self.assertIsNone(r["choice"])
        self.assertIn("saved choice S1 not found", r["note"])

    def test_T11_AC10_flag_wins_over_saved_scope(self):
        r = self.go("?goal=alpha", saved=self.saved("scope", "checkout"))
        self.assertEqual(r["choice"], {"kind": "goal", "name": "alpha"})

    def test_T11_AC11_url_opens_and_unknown_name_gives_picker_not_found(self):
        r = self.go("#/scope/checkout", saved=self.saved("goal", "alpha"))
        self.assertEqual(r["choice"], {"kind": "scope", "name": "checkout"})
        r = self.go("#/scope/nope")
        self.assertIsNone(r["choice"])
        self.assertTrue(any("not found" in x for x in r["note"]))

    def test_T11_TA3_url_name_is_data_not_code(self):
        r = self.go("#/scope/%3Cimg%20src%3Dx%20onerror%3Dwindow.__x%3D1%3E")
        self.assertIsNone(r["choice"])
        self.assertTrue(r["x"] and r["imgs"] == 0)
        self.assertTrue(any("not found" in x for x in r["note"]))

    def test_T11_AC11_TA5_back_returns_to_picker_and_refresh_adds_no_history(self):
        r = self.go(extra="""
const len0=history.length;
for(let i=0;i<3;i++){BOARD.page.poller.now();await sleep(60)}
const len1=history.length;
$('#view .pr[data-name="checkout"]').click();await sleep(100);
const opened=BOARD.page.state.choice&&BOARD.page.state.choice.name;const h=location.hash;
history.back();await sleep(150);
var ex={len0,len1,opened,h,back:BOARD.page.state.choice};
""")
        e = r["extra"]
        self.assertEqual(e["len0"], e["len1"])
        self.assertEqual((e["opened"], e["h"], e["back"]), ("checkout", "#/scope/checkout", None))


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser test skipped")
class Header(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real = real_payloads()

    def test_T11_AC12_more_need_you_link_title_and_click(self):
        r = run_page("""
await startPage();
const t=$('#view .ctxbar .out').textContent;const title=document.title;
Array.from($$('#view .ctxbar .out button')).find(b=>b.textContent==='questions').click();await sleep(100);
out({t,title,choice:BOARD.page.state.choice});
""", self.real, "#/scope/checkout")
        self.assertEqual(r["t"], "1 more needs you in questions")
        self.assertEqual(r["title"], "(1) fix")
        self.assertEqual(r["choice"], {"kind": "scope", "name": "questions"})

    def test_T11_AC13_AC14_goal_strip_then_scope_with_link_up(self):
        r = run_page("""
await startPage();
const head=Array.from($$('section[data-panel=scopes] th')).map(x=>x.textContent);
const rows=$$('section[data-panel=scopes] tbody tr, section[data-panel=scopes] tr').length-1;
const shown=!$('section[data-panel=scopes]').hidden;
const where1=$('#view .where').textContent;
Array.from($$('section[data-panel=scopes] button.lk')).find(b=>b.textContent==='alpha-api').click();await sleep(150);
const up=Array.from($$('#view .where button')).map(b=>b.textContent);
out({head,rows,shown,where1,where2:$('#view .where').textContent,up,choice:BOARD.page.state.choice,hiddenNow:$('section[data-panel=scopes]').hidden});
""", self.real, "#/goal/alpha")
        self.assertEqual(r["head"], ["Scope", "Brief", "Stage", "Needs you", "Blocked", "Tasks", "Last active"])
        self.assertEqual((r["rows"], r["shown"], r["where1"]), (4, True, "goal alpha open Fixture goal alpha. · 4 scopes (4 open) · panels show them together"))  # name, then the goal brief
        self.assertTrue(r["where2"].startswith("goal alpha > scope alpha-api"))
        self.assertEqual((r["up"], r["choice"]["name"], r["hiddenNow"]), (["goal alpha"], "alpha-api", True))

    def test_T11_AC15_TA6_chosen_scope_closes_while_open(self):
        r = run_page("""
const p=await startPage();
const before=Array.from($$('#view .ro')).length;
const sq=JSON.parse(JSON.stringify(cur.squads));const row=sq.data.squads[0];
row.scopes=row.scopes.filter(n=>n!=='checkout');row.open=row.open.filter(x=>x.name!=='checkout');
cur.squads=sq;cur.checks.checkout={name:'checkout',exists:true,kind:'scope',where:'done',message:''};
p.poller.now();await sleep(200);
out({before,ro:Array.from($$('#view .ro')).map(x=>x.textContent),links:Array.from($$('#view .ro button')).map(b=>b.textContent),fresh:$('.fresh').textContent});
""", self.real, "#/scope/checkout")
        self.assertEqual(r["before"], 0)
        self.assertTrue(r["ro"] and "closed" in r["ro"][0])
        self.assertEqual(r["links"], ["Back to the picker"])
        self.assertNotIn("not updating", r["fresh"])


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser test skipped")
class ByView(unittest.TestCase):
    def test_T11_TA1_scopes_panel_hidden_in_scope_view_is_not_in_panels_menu_reset_or_saved_state(self):
        real = dict(real_payloads(), saved=None)
        r = run_page("""
const p=await startPage();
const sc=$('section[data-panel=scopes]');
const hiddenIn=sc.hidden;
BOARD.page.resetLayout();await sleep(50);
$('.hb[aria-haspopup=true]').click();await sleep(20);
out({hiddenIn,afterReset:sc.hidden,btn:$('.hb[aria-haspopup=true]').textContent,menu:$('.pop').textContent,saved:BOARD.page.snapshot().panels.scopes.hidden});
""", real, "#/scope/checkout")
        self.assertEqual((r["hiddenIn"], r["afterReset"], r["saved"]), (True, True, False))
        self.assertNotIn("hidden)", r["btn"])
        self.assertNotIn("Scopes", r["menu"])


class Static(unittest.TestCase):
    def test_T11_TU3_TU4_TA7_no_innerhtml_no_remote_no_all_label(self):
        js = (TPL / "panel_scopes.js").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(|new Function|https?://", js))
        self.assertIsNone(re.search(r"\"All\"|'All'|>All<", js + (TPL / "board.js").read_text(encoding="utf-8")))
        self.assertEqual(re.findall(r'method\s*:\s*"(\w+)"', js), [])
        self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b", js))   # colours are var(--x) tokens


# ---------------------------------------------------------------- ticket 12: Needs you, Tasks, Agents now
import datetime  # noqa: E402

PANELS12 = ("panel_inbox.js", "panel_tasks.js", "panel_agents.js")


def head12(files=PANELS12):
    tag = lambda f: '<script src="file://%%(tpl)s/%s"></script>' % f   # same order as index.html: inbox, scopes, tasks, agents
    pre = tag("panel_inbox.js") if "panel_inbox.js" in files else ""
    post = "".join(tag(f) for f in files if f != "panel_inbox.js")
    return HEAD.replace('<script src="file://%(tpl)s/panel_scopes.js"></script>', pre + '<script src="file://%(tpl)s/panel_scopes.js"></script>' + post, 1)


PRE12 = r"""
window.__w=[];Object.defineProperty(navigator,'clipboard',{value:{writeText:async t=>{window.__w.push(t)}},configurable:true});
const P=R.p12,q12=u=>new URLSearchParams(u.split('?')[1]);
const f12=async(url,opt)=>{const m=url.match(/^\/api\/(inbox|tasks|agents)\?/);
  if(m){const q=q12(url),sc=q.get('scope')||'goal:'+q.get('goal'),d=q.get('detail');
    if(m[1]==='tasks'&&d)return J(P['detail:'+d]);return J(P[m[1]+':'+sc])}
  return fetchStub(url,opt)};
const start12=async()=>{BOARD.start({fetch:f12,storage:mem(),setTimeout:fk.setTimeout,clearTimeout:fk.clearTimeout,now:()=>Date.parse('2026-11-04T10:00:00Z'),tz:'UTC'});
  await sleep(300);return BOARD.page};
"""


def payloads12():
    """The real answers of /api/inbox, /api/tasks and /api/agents on the ticket-02 fixture (git branches built)."""
    now = datetime.datetime(2026, 11, 4, 10, 0, tzinfo=datetime.timezone.utc)
    fx = board_fixtures.copy_fixture(now=now)
    (fx.squad / "scopes" / "questions" / "open-questions.md").write_text(
        "## Q1\nStatus: parked\nParked: 2026-11-03T09:00:00Z\nWhich port for the proxy?\nBlocks: ticket 3\nFrom: E1 #2\n", encoding="utf-8")
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
        for sc in ("questions", "checkout"):
            for route in ("inbox", "tasks", "agents"):
                out["%s:%s" % (route, sc)] = get("/api/%s?squad=fix&scope=%s" % (route, sc))
        for tid in ("03", "06"):
            out["detail:" + tid] = get("/api/tasks?squad=fix&scope=checkout&detail=" + tid)
        srv.herdr_json = str(fx.herdr_down)
        out["inbox:down"] = get("/api/inbox?squad=fix&scope=questions")
        return out
    finally:
        srv.shutdown()
        srv.server_close()
        board_fixtures.cleanup(fx)


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser test skipped")
class Panels12(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real = dict(real_payloads(), saved=None, p12=payloads12())
        cls.head = head12()

    def page(self, body, hash_):
        return run_page(PRE12 + body, self.real, hash_, self.head)

    def test_T12_header_line_and_panel_show_the_same_other_scope_numbers(self):
        for sc in ("questions", "checkout"):
            r = self.page(r"""
await start12();await sleep(100);
out({head:$$('#view .ctxbar .out').map(e=>e.textContent),panel:$('section[data-panel=inbox] .nb-out').textContent});
""", "#/scope/" + sc)
            others = self.real["p12"]["inbox:" + sc]["data"]["others"]
            want = ["%d more need%s you in %s" % (o["n"], "s" if o["n"] == 1 else "", o["scope"]) for o in others if o["n"] > 0]
            self.assertTrue(want, sc)
            self.assertEqual(r["head"], want, sc)
            for o in others:
                self.assertIn("%s · %d" % (o["scope"], o["n"]), r["panel"])

    def test_T12_AC1_AC3_AC5_AC10_inbox_row_options_recommended_copy_exact_and_no_write_labels(self):
        r = self.page(r"""
await start12();
const sec=$('section[data-panel=inbox]'),item=sec.querySelector('.nb-item');
const code=item.querySelector('.nb-how code').textContent;
const btn=item.querySelector('.nb-how button');btn.click();await sleep(20);
const rec=Array.from(item.querySelectorAll('.nb-opts li')).map(li=>[li.textContent,li.classList.contains('rec')]);
out({title:item.querySelector('b:not(.nb-opts b)').textContent,id:item.dataset.id,age:item.querySelector('.age').textContent,blocks:item.querySelector('.blocks').textContent,
 rec,code,clip:window.__w.slice(),copyRet:BOARD.copyText(btn),
 labels:$$('button').map(b=>b.textContent+'|'+(b.getAttribute('aria-label')||'')+'|'+(b.title||'')).filter(t=>/answer|park|merge|approve|delete/i.test(t)),
 openLabel:sec.querySelector('h3.nb-sec').textContent});
""", "#/scope/questions")
        self.assertEqual((r["id"], r["blocks"]), ("E1", "Blocks: ticket 04"))
        self.assertEqual(r["openLabel"], "Open now (1)")
        self.assertRegex(r["age"], r"\d+ h ago|age unknown")
        self.assertEqual([x[1] for x in r["rec"]], [True, False])
        self.assertIn("Manager recommends", r["rec"][0][0])
        self.assertNotIn("Manager recommends", r["rec"][1][0])
        self.assertEqual((r["code"], r["clip"], r["copyRet"]), ("squad-inbox answer E1", ["squad-inbox answer E1"], "squad-inbox answer E1"))
        self.assertEqual(r["labels"], [])   # AC10: no control is labelled answer, park, merge, approve, delete

    def test_T12_AC2_AC4_empty_text_parked_group_tab_title_from_the_server_and_two_banner_lines(self):
        r = self.page(r"""
const q=P['inbox:questions'];
q.data.rows=[];q.data.count_choice=0;q.data.count_squad=7;q.data.banner.entries=[{agent:'a-1',pane_id:'p1',scope:'checkout'},{agent:'a-2',pane_id:'p2',scope:'checkout'}];
await start12();
const sec=$('section[data-panel=inbox]');
const parked=sec.querySelector('.nb-item.parked');
out({empty:sec.querySelector('.nb-empty b').textContent,labels:$$('h3.nb-sec').map(h=>h.textContent),parkedText:parked?parked.textContent:'',
 title:document.title,count:sec.querySelector('.count').textContent,lines:$$('#app .bannerslot .banner .t').map(t=>t.textContent)});
""", "#/scope/questions")
        self.assertEqual(r["empty"], "Nothing needs you")
        self.assertIn("Parked (1)", [x[:10] for x in r["labels"]])
        self.assertIn("Still blocks: ticket 3", r["parkedText"])
        self.assertIn("From E1 #2", r["parkedText"])
        self.assertTrue(r["title"].startswith("(7) "))   # count_squad, not summed in the page
        self.assertEqual(r["count"], "0")
        self.assertEqual(len(r["lines"]), 2)
        self.assertTrue(all(("a-1" in r["lines"][0], "p1" in r["lines"][0])) and "a-2" in r["lines"][1] and "p2" in r["lines"][1])

    def test_T12_AC6_herdr_down_says_so(self):
        r = self.page(r"""
P['inbox:questions']=P['inbox:down'];
await start12();
out({banner:$('#app .bannerslot').textContent});
""", "#/scope/questions")
        self.assertIn("status unknown: herdr not running", r["banner"])

    def test_T12_AC7_AC8_AC9_tasks_stages_ready_flag_detail_in_time_order_toggle_and_esc(self):
        r = self.page(r"""
await start12();
const sec=$('section[data-panel=tasks]');
const rows=()=>$$('section[data-panel=tasks] tr.r');
const cells=rows().map(tr=>Array.from(tr.children).map(td=>td.textContent));
const ready=rows().filter(tr=>tr.classList.contains('need')).map(tr=>tr.dataset.k);
let calls=0;const orig=EventTarget.prototype.addEventListener;EventTarget.prototype.addEventListener=function(){calls++;return orig.apply(this,arguments)};
const r3=rows().find(tr=>tr.dataset.k==='03');
r3.click();await sleep(60);
const det=$('section[data-panel=tasks] tr.x').textContent;const steps=$$('section[data-panel=tasks] tr.x .steps li').map(l=>l.textContent);
rows().find(tr=>tr.dataset.k==='03').click();await sleep(20);const closed=$$('section[data-panel=tasks] tr.x').length;
for(let i=0;i<10;i++){rows().find(tr=>tr.dataset.k==='03').click();await sleep(30);key(document,'Escape');await sleep(10)}
const afterEsc=$$('section[data-panel=tasks] tr.x').length;
out({cells,ready,det,steps,closed,afterEsc,calls,count:sec.querySelector('.count').textContent,tools:$$('section[data-panel=tasks] .tools button').map(b=>b.textContent)});
""", "#/scope/checkout")
        stages = [c[2] for c in r["cells"]]
        for word in ("todo", "in progress", "returned", "blocked", "checking, 1 of 2 PASS", "ready for review", "sha changed after PASS", "merged", "done"):
            self.assertTrue(any(s.startswith(word) for s in stages), word)
        self.assertEqual(r["ready"], ["06"])
        self.assertEqual(len(r["cells"][0]), 7)   # id, title, stage, last active, what happened, owner, waits on
        self.assertIn("Ready for review (1)", r["tools"])
        self.assertIn("FAIL: reason 3 first line (newest)", r["det"])
        times = [s.split(" ")[1] for s in r["steps"]]
        self.assertEqual(times, sorted(times))
        self.assertEqual((r["closed"], r["afterEsc"]), (0, 0))
        self.assertLess(r["calls"], 12)   # open and close 10 times add no listener (re-draws only)

    def test_T12_TA7_retired_toggle_without_a_request_and_TU3_text_is_text(self):
        r = self.page(r"""
P['tasks:checkout'].data.rows[0].title='<img src=x onerror=window.__x=1>';
await start12();
let fetches=0;const of=window.fetch;
const sec=$('section[data-panel=agents]');
const before=sec.querySelector('[data-retired]').textContent;
sec.querySelector('[data-retired]').click();await sleep(20);
out({before,after:sec.querySelector('[data-retired]').textContent,li:sec.querySelectorAll('.ag-more li').length,x:window.__x===undefined,
 title:$('section[data-panel=tasks] tr.r td:nth-child(2)').textContent,img:!!$('section[data-panel=tasks] img')});
""", "#/scope/checkout")
        self.assertEqual((r["before"], r["after"], r["li"]), ("▸ 1 retired, hidden", "▾ 1 retired", 1))
        self.assertTrue(r["x"] and not r["img"] and r["title"].startswith("<img"))


    def test_T12_TA2_AC1_AC3_AC4_pure_rows_two_questions_one_unread_oldest_first_parked_after_open(self):
        r = self.page(r"""
const B=BOARD,d=JSON.parse(JSON.stringify(P['inbox:questions'])).data;
const e1=d.rows[0];
d.rows=[Object.assign({},e1,{id:'E2',age_s:100,kind:'open',options:[]}),Object.assign({},e1,{id:'E5',age_s:7200,kind:'answer',options:[]}),Object.assign({},e1,{id:'E1',age_s:90000})];
d.rows.sort((a,b)=>b.age_s-a.age_s);
const RW=B.rowsForInbox(d),T=B.rowsForTasks(P['tasks:checkout'].data,Date.parse('2026-11-04T10:00:00Z')),A=B.rowsForAgents(P['agents:checkout'].data,Date.parse('2026-11-04T10:00:00Z'));
out({ids:RW.open.map(x=>x.id),keys:Object.keys(RW.open[0]).sort(),recs:RW.open[2].options.map(o=>o.word),read:RW.open.map(x=>x.read),parkedLabel:RW.parkedLabel,openLabel:RW.openLabel,
 tkeys:Object.keys(T[0]).sort(),akeys:Object.keys(A.live[0]).sort(),retired:A.retiredLabel,
 cmds:[B.answerCommand('E3 #2'),B.answerCommand('Q1'),B.unparkCommand('Q1'),B.resolveCommand('Q1')]});
""", "#/scope/questions")
        self.assertEqual(r["ids"], ["E1", "E5", "E2"])   # oldest first: 2 open questions and 1 unread item are 3 rows
        self.assertEqual(r["read"], [False, True, False])
        self.assertEqual((r["parkedLabel"], r["openLabel"]), ("Parked (1)", "Open now (3)"))
        self.assertEqual(r["recs"], [])   # E2 has no options in this made-up row
        for k in ("id", "title", "age", "blocks", "options", "answer", "scope"):
            self.assertIn(k, r["keys"])
        for k in ("id", "title", "stage", "owner", "waits", "last", "lastIso"):
            self.assertIn(k, r["tkeys"])
        for k in ("name", "role", "owns", "status", "last"):
            self.assertIn(k, r["akeys"])
        self.assertEqual(r["retired"], "1 retired")
        self.assertEqual(r["cmds"], ["squad-inbox answer E3 #2", "squad-inbox answer Q1", "squad-inbox unpark Q1", 'squad-inbox resolve Q1 --answer "..."'])

    def test_T12_TA3_TA5_a_title_is_never_in_a_command_and_the_banner_lines_ignore_the_choice(self):
        r = self.page(r"""
P['inbox:questions'].data.rows[0].title='$(rm -rf /) "x"';
P['inbox:questions'].data.banner.entries=[{agent:'a-1',pane_id:'p1',scope:'checkout'},{agent:'a-2',pane_id:'p2',scope:'checkout'}];
P['inbox:checkout'].data.banner.entries=P['inbox:questions'].data.banner.entries;
await start12();
const codes=$$('section[data-panel=inbox] code').map(c=>c.textContent);
const lines1=$$('#app .bannerslot .banner .t').map(t=>t.textContent);
BOARD.page.setChoice('scope:checkout');await sleep(300);
const lines2=$$('#app .bannerslot .banner .t').map(t=>t.textContent);
out({codes,lines1,lines2});
""", "#/scope/questions")
        self.assertFalse(any("rm -rf" in c for c in r["codes"]))
        self.assertEqual(len(r["lines1"]), 2)
        self.assertEqual(r["lines1"], r["lines2"])

    def test_T12_TA1_cutting_a_panel_file_leaves_the_rest_working(self):
        r = run_page(PRE12 + r"""
await start12();
out({ids:BOARD.panels.map(p=>p.id),inbox:!!$('section[data-panel=inbox] .nb-item'),agents:!!$('section[data-panel=agents]')});
""", self.real, "#/scope/questions", head12(("panel_inbox.js", "panel_tasks.js")))
        self.assertEqual(r["ids"], ["inbox", "scopes", "tasks"])
        self.assertTrue(r["inbox"] and not r["agents"])


class Static12(unittest.TestCase):
    def test_T12_TU3_TU4_TU5_TA6_no_innerhtml_no_remote_no_write_no_summed_count(self):
        for f in PANELS12:
            js = (TPL / f).read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(|new Function|https?://", js), f)
            self.assertIsNone(re.search(r"method\s*:", js), f)
            self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b", js), f)
            self.assertIsNone(re.search(r"count_squad|count_choice\s*\+|\.length\s*\+\s*\w+\.length", js.replace("d.count_choice", "")), f)


# ---------------------------------------------------------------- ticket 14: Files panel
HEAD14 = HEAD.replace('<script src="file://%(tpl)s/panel_scopes.js"></script>',
                      '<script src="file://%(tpl)s/panel_scopes.js"></script><script src="file://%(tpl)s/panel_files.js"></script>', 1)
PRE14 = r"""
const F14=R.f14;
const f14=async(url,opt)=>{const m=url.match(/^\/api\/files\?/);
  if(m){const q=new URLSearchParams(url.split('?')[1]);return J(F14[q.get('scope')||'none'])}
  return fetchStub(url,opt)};
const start14=async(tz)=>{BOARD.start({fetch:f14,storage:mem(),setTimeout:fk.setTimeout,clearTimeout:fk.clearTimeout,now:()=>Date.parse('2026-11-04T10:00:00Z'),tz:tz||'UTC'});
  await sleep(300);return BOARD.page};
"""


def payloads14():
    """The real answers of /api/files on the fixture (extended in a temp copy): a live scope and a closed one with a report."""
    fx = board_fixtures.copy_fixture(git=False)
    squad = fx.squad
    for rel, text in (("scopes/checkout/tasks/features.md", "# Features\n- one\n"), ("scopes/checkout/ui-design/proto-a.html", "<p>x</p>"),
                      ("scopes/checkout/promote.md", "p\n"), ("scopes/_done/closed-release/report/report.html", "<p>r</p>")):
        f = squad / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8", newline="\n")
    srv = squadboard.BoardServer(0, squadboard.find_squads([str(squad)]), {})
    srv.routes, _ = squadboard.load_routes()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        out = {}
        for sc in ("checkout", "closed-release"):
            with urllib.request.urlopen("http://127.0.0.1:%d/api/files?squad=fix&scope=%s" % (srv.port, sc), timeout=20) as r:
                out[sc] = json.loads(r.read())
        return out
    finally:
        srv.shutdown()
        srv.server_close()
        board_fixtures.cleanup(fx)


@unittest.skipUnless(CHROME, "no Chrome/Chromium on this machine: browser test skipped")
class Panels14(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real = dict(real_payloads(), saved=None, f14=payloads14())

    def page(self, body, hash_, head=HEAD14):
        return run_page(PRE14 + body, self.real, hash_, head)

    def test_T14_AC1_AC2_TA3_rows_with_kind_and_local_time_links_open_in_a_new_tab(self):
        r = self.page(r"""
await start14('Asia/Ho_Chi_Minh');
const rows=$$('section[data-panel=files] table.fl tr').slice(1).map(tr=>({t:tr.textContent,a:tr.querySelector('a')&&{h:tr.querySelector('a').getAttribute('href'),tg:tr.querySelector('a').target,rel:tr.querySelector('a').rel,md:tr.querySelector('a').dataset.md||null,n:tr.querySelector('a').textContent},
  time:tr.querySelector('time')&&{iso:tr.querySelector('time').dateTime,txt:tr.querySelector('time').textContent}}));
out({rows,fmt:rows.filter(x=>x.time).map(x=>BOARD.fmtTime(x.time.iso,'Asia/Ho_Chi_Minh'))});
""", "#/scope/checkout")
        names = [x["a"]["n"] for x in r["rows"] if x["a"]]
        for want in ("tasks/features.md", "ui-design/proto-a.html", "promote.md"):
            self.assertIn(want, names)
        for x in r["rows"]:
            if x["a"]:
                self.assertEqual((x["a"]["tg"], x["a"]["rel"]), ("_blank", "noopener noreferrer"))
                self.assertTrue(x["a"]["h"].startswith("/api/file?squad=fix&path="), x)
        md = [x for x in r["rows"] if x["a"] and x["a"]["n"] == "tasks/features.md"][0]
        self.assertEqual(md["a"]["md"], "scopes/checkout/tasks/features.md")
        self.assertEqual([x["time"]["txt"] for x in r["rows"] if x["time"]], r["fmt"])   # shown with the shared BOARD zone function

    def test_T14_AC4_AC5_live_scope_says_no_report_yet_closed_scope_lists_report_and_data(self):
        live = self.page("await start14();out({t:$('section[data-panel=files]').textContent});", "#/scope/checkout")
        self.assertIn("no report yet (made at close)", live["t"])
        done = self.page("await start14();out({t:$('section[data-panel=files]').textContent});", "#/scope/closed-release")
        self.assertIn("report/report.html", done["t"])
        self.assertIn("report/data.json", done["t"])
        self.assertNotIn("no report yet", done["t"])

    def test_T14_AC2_TU3_markdown_is_drawn_readable_and_script_text_stays_text(self):
        r = self.page(r"""
await start14();
const md='# Title\n\nSome **bold** and `code` <img src=x onerror=window.__x=1>\n\n- item <scr'+'ipt>window.__x=2<'+'/script>\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n```\nraw # kept\n```\n';
const host=document.createElement('div');BOARD.renderMd(document,host,md);document.body.appendChild(host);await sleep(100);
out({tags:Array.from(host.children).map(e=>e.tagName),h1:host.querySelector('h1').textContent,text:host.textContent,x:typeof window.__x,imgs:host.querySelectorAll('img,script').length,b:host.querySelector('strong').textContent});
""", "#/scope/checkout")
        self.assertEqual(r["tags"], ["H1", "P", "UL", "TABLE", "PRE"])
        self.assertEqual((r["h1"], r["b"]), ("Title", "bold"))
        self.assertNotIn("# Title", r["text"])
        self.assertIn("<img src=x onerror=window.__x=1>", r["text"])
        self.assertEqual((r["x"], r["imgs"]), ("undefined", 0))

    def test_T14_TA7_the_board_boots_without_the_files_panel_file(self):
        r = self.page("await start14();out({ids:BOARD.panels.map(p=>p.id),files:!!$('section[data-panel=files]')});", "#/scope/checkout", HEAD)
        self.assertNotIn("files", r["ids"])
        self.assertFalse(r["files"])


class Static14(unittest.TestCase):
    def test_T14_TU3_TU4_TU5_TU9_panel_file_has_no_innerhtml_no_remote_no_write_no_hex(self):
        js = (TPL / "panel_files.js").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(|new Function|https?://", js))
        self.assertIsNone(re.search(r"method\s*:", js))
        self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b", js))


if __name__ == "__main__":
    unittest.main()
