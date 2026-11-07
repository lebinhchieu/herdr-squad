// Ticket 39: drives the demo page, clicks every kind of file link in every way, prints JSON. argv: url
const path = require("path");
const pw = require(path.join(process.env.PLAYWRIGHT_CORE, "index.js"));
(async () => {
  const url = process.argv[2];
  const browser = await pw.chromium.launch({ executablePath: process.env.CHROME_BIN, headless: true, args: ["--no-sandbox"] });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const seen = { popups: [], navs: [], reqs: [] };
  ctx.on("page", p => seen.popups.push(p.url()));
  page.on("popup", p => seen.popups.push(p.url()));
  page.on("framenavigated", f => seen.navs.push(f.url()));
  page.on("request", r => seen.reqs.push(r.url()));
  await page.addInitScript(() => {
    window.__spy = { fetch: [], xhr: [], open: [], defaults: [] };
    const f = window.fetch; window.fetch = function (u) { window.__spy.fetch.push(String(u && u.url || u)); return f.apply(this, arguments); };
    const x = XMLHttpRequest.prototype.open; XMLHttpRequest.prototype.open = function (m, u) { window.__spy.xhr.push(String(u)); return x.apply(this, arguments); };
    window.open = function (u) { window.__spy.open.push(String(u)); return null; };
  });
  await page.goto(url);
  await page.waitForSelector(".demo:not([hidden])", { timeout: 15000 });
  const SEL = "select[aria-label='Goal or scope']";
  await page.waitForSelector(SEL, { state: "attached", timeout: 15000 });
  const goal = (await page.$$eval(SEL + " option", o => o.map(x => [x.value, x.textContent]))).find(x => /alpha/.test(x[1]) && !/-/.test(x[1]))[0];
  await page.evaluate(([s, v]) => { const e = document.querySelector(s); e.value = v; e.dispatchEvent(new Event("change", { bubbles: true })); }, [SEL, goal]);
  await page.waitForSelector("section.panel[data-panel=files] a[href^='vscode:']", { timeout: 15000 });
  // registered after the page guard, same node and phase: sees defaultPrevented as the guard left it
  await page.evaluate(() => { for (const t of ["click", "auxclick"]) document.addEventListener(t, e => window.__spy.defaults.push([t, e.defaultPrevented]), true); });
  const kinds = {
    file: "section.panel[data-panel=files] a[href^='vscode:']:not([data-folder])",
    folder: "section.panel[data-panel=files] a[data-folder][href^='vscode:']",
    where: "section.panel[data-panel=tasks] a[href^='vscode:']",
  };
  const out = { counts: {}, cases: [], toasts: 0, copy: null };
  for (const [k, sel] of Object.entries(kinds)) out.counts[k] = await page.locator(sel).count();
  const inputs = {
    left: l => l.click(),
    ctrl: l => l.click({ modifiers: ["Control"] }),
    shift: l => l.click({ modifiers: ["Shift"] }),
    middle: l => l.click({ button: "middle" }),
    enter: async l => { await l.focus(); await page.keyboard.press("Enter"); },
  };
  for (const [k, sel] of Object.entries(kinds)) {
    if (!out.counts[k]) continue;
    for (const [i, fn] of Object.entries(inputs)) {
      const l = page.locator(sel).first();
      await l.scrollIntoViewIfNeeded();
      await page.evaluate(() => { window.__spy.defaults.length = 0; });
      await fn(l);
      await page.waitForTimeout(150);
      out.cases.push({ kind: k, input: i, ...(await page.evaluate(() => ({
        toast: (document.querySelector(".toast") || {}).textContent, shown: !!document.querySelector(".toast") && !document.querySelector(".toast").hidden,
        defaults: window.__spy.defaults.slice() }))) });
    }
  }
  // toast: look, timing, layout (TA3)
  const probe = () => page.evaluate(() => {
    const p = document.createElement("div"); p.style.cssText = "background:var(--panel);color:var(--ink);border:1px solid var(--border)"; document.body.appendChild(p);
    const c = getComputedStyle(p), r = { bg: c.backgroundColor, color: c.color, border: c.borderTopColor }; p.remove(); return r; });
  const state = () => page.evaluate(() => {
    const t = document.querySelector(".toast"), rc = e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom].map(Math.round); };
    const c = t && getComputedStyle(t);
    return { n: document.querySelectorAll(".toast").length, shown: !!t && !t.hidden && t.offsetParent !== null || (!!t && !t.hidden && c.position === "fixed"),
      role: t && t.getAttribute("role"), bg: c && c.backgroundColor, color: c && c.color, border: c && c.borderTopColor,
      rect: t && !t.hidden ? rc(t) : null, demo: rc(document.querySelector(".demo")), top: rc(document.querySelector("header.top")),
      win: [innerWidth, innerHeight], panels: [...document.querySelectorAll("section.panel")].filter(s => !s.hidden).map(s => rc(s)), scroll: [scrollX, scrollY] }; });
  out.tokens = await probe();
  out.windows = [];
  for (const [w, h, font] of [[1440, 900, null], [1000, 700, null], [1000, 700, "xl"]]) {
    await page.setViewportSize({ width: w, height: h });
    if (font) await page.click("button[data-font=xl]");
    await page.waitForTimeout(6200);          // any earlier toast is gone
    const before = await state();
    const link = page.locator(kinds.file).first();
    await link.scrollIntoViewIfNeeded();
    const mid = await state();
    const t0 = Date.now();
    for (let i = 0; i < 3; i++) { await link.click(); await page.waitForTimeout(100); }
    const wait = ms => page.waitForTimeout(Math.max(0, ms - (Date.now() - t0)));
    await wait(300); const s300 = await state();
    await wait(2000); const s2 = await state();
    await wait(6000); const s6 = await state();
    out.windows.push({ w, h, font, before: mid, s300, s2, s6 });
  }
  // Copy path: no toast, no request
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.waitForTimeout(6200);
  const copy = page.locator("section.panel[data-panel=files] button:has-text('Copy path')").first();
  out.copyCount = await copy.count();
  if (out.copyCount) {
    await page.locator(kinds.file).first().scrollIntoViewIfNeeded();
    const nreq = seen.reqs.length;
    await copy.click(); await page.waitForTimeout(300);
    out.copy = { toastShown: (await state()).shown, newReqs: seen.reqs.slice(nreq).filter(u => /api\/open/.test(u)).length };
  }
  out.spy = await page.evaluate(() => window.__spy);
  out.seen = seen;
  out.sent = await page.evaluate(() => document.body.innerText.includes("Sent to VS Code:"));
  await browser.close();
  console.log(JSON.stringify(out));
})().catch(e => { console.error(String(e)); process.exit(1); });
