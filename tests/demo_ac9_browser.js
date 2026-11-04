// Drives one demo page in a persistent Chrome profile. argv: mode url profileDir. Prints JSON.
// mode "hide": hide Files, set Extra large, wait for the save. mode "check": report panels and storage keys.
const path = require("path");
const pw = require(path.join(process.env.PLAYWRIGHT_CORE, "index.js"));
(async () => {
  const [mode, url, profile] = process.argv.slice(2);
  const ctx = await pw.chromium.launchPersistentContext(profile, { executablePath: process.env.CHROME_BIN, headless: true, args: ["--no-sandbox"] });
  const page = ctx.pages()[0] || await ctx.newPage();
  await page.goto(url);
  const SEL = "select[aria-label='Goal or scope']";
  const choose = async v => { await page.waitForSelector(SEL, { state: "attached" }); await page.evaluate(([sel, v]) => { const s = document.querySelector(sel); s.value = v; s.dispatchEvent(new Event("change", { bubbles: true })); }, [SEL, v]); await page.waitForTimeout(2500); };
  await page.waitForSelector(SEL, { state: "attached", timeout: 15000 });
  const goalValue = (await page.$$eval(SEL + " option", o => o.map(x => [x.value, x.textContent]))).find(x => /alpha/.test(x[1]) && !/-/.test(x[1]))[0];
  if (mode !== "ages") await choose(goalValue);
  if (mode !== "ages") await page.waitForSelector("section.panel[data-panel=files]", { state: "visible", timeout: 15000 });
  if (mode === "ages") {
    const res = {};
    const opts = await page.$$eval("select[aria-label='Goal or scope'] option", o => o.map(x => [x.value, x.textContent]));
    for (const [v, label] of opts) {
      if (/_done/.test(label)) continue;
      await choose(v);
      res[label] = await page.evaluate(() => document.querySelector("main, #app").innerText);
    }
    console.log(JSON.stringify(res));
    await ctx.close();
    return;
  }
  if (mode === "hide") {
    await page.click("section.panel[data-panel=files] button.pbtn:has-text('Hide')");
    await page.click("button[data-font=xl]");
    await page.waitForFunction(async () => (await (await fetch("/api/ui?squad=fix")).json()).data.ui != null, null, { timeout: 15000 });
    await page.waitForTimeout(1500);
  }
  const out = await page.evaluate(() => ({
    panels: [...document.querySelectorAll("section.panel")].filter(s => !s.hidden && s.offsetParent).map(s => s.dataset.panel),
    keys: Object.keys(localStorage).filter(k => k.indexOf("squad-board-ui:") === 0),
    font: document.documentElement.dataset.font || document.body.className }));
  console.log(JSON.stringify(out));
  await ctx.close();
})().catch(e => { console.error(String(e)); process.exit(1); });
