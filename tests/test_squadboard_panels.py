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


def run_page(body, real, suffix=""):
    with tempfile.TemporaryDirectory() as d:
        page = Path(d) / "page.html"
        page.write_text(HEAD % {"tpl": str(TPL), "real": json.dumps(real), "body": body}, encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()
