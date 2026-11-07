// Ticket 40 evidence: crops of the Work time filter bar, before (old timeline.js served through page.route) and after, at device scale 3.
// argv: url outdir oldTimelineJsPath. env PLAYWRIGHT_CORE, CHROME_BIN.
const path = require("path"), fs = require("fs");
const pw = require(path.join(process.env.PLAYWRIGHT_CORE, "index.js"));
(async () => {
  const [url, outdir, oldJs] = process.argv.slice(2);
  const browser = await pw.chromium.launch({ executablePath: process.env.CHROME_BIN, headless: true, args: ["--no-sandbox"] });
  const res = {};
  for (const [label, old] of [["before", true], ["after", false]]) {
    for (const [wname, vw, vh, fs_, narrow, state] of [["1440", 1440, 900, 0, 0, ""], ["1000", 1000, 700, 0, 0, ""], ["wrapped", 1000, 700, 1.3, 0, ""], ["narrow", 1440, 900, 0, 330, ""], ["hover", 1440, 900, 0, 0, "hover"]]) {
      const ctx = await browser.newContext({ viewport: { width: vw, height: vh }, deviceScaleFactor: 3 });
      const page = await ctx.newPage();
      if (old) await page.route("**/timeline.js*", r => r.fulfill({ status: 200, contentType: "application/javascript", body: fs.readFileSync(oldJs, "utf-8") }));
      await page.goto(url);
      await page.waitForSelector(".demo:not([hidden])", { timeout: 15000 });
      await page.waitForSelector(".tl-bar", { timeout: 15000 });
      if (fs_) await page.evaluate(f => { document.querySelector(".tl").style.fontSize = 16 * f + "px"; }, fs_);
      if (narrow) await page.evaluate(w => { document.querySelector(".tl").parentNode.style.width = w + "px"; }, narrow);
      await page.waitForTimeout(300);
      if (state === "hover") await page.locator(".tl-bar .tc", { hasText: /^All$/ }).hover();
      const bar = page.locator(".tl-bar");
      const f = path.join(outdir, `bar-${label}-${wname}.png`);
      await bar.screenshot({ path: f });
      const m = await page.evaluate(() => {
        const rd = e => { const c = getComputedStyle(e); return ["TopLeft", "TopRight", "BottomRight", "BottomLeft"].map(k => c["border" + k + "Radius"]).join("/"); };
        const all = [...document.querySelectorAll(".tl-bar .tc")].find(x => x.textContent === "All");
        const g = [...document.querySelectorAll(".tl-bar .seg")];
        return { all: rd(all), seg0: { box: rd(g[0]), bw: getComputedStyle(g[0]).borderTopWidth, ov: getComputedStyle(g[0]).overflow, w: g[0].getBoundingClientRect().width, h: g[0].getBoundingClientRect().height } };
      });
      res[label + "-" + wname] = m;
      await ctx.close();
    }
  }
  await browser.close();
  console.log(JSON.stringify(res, null, 1));
})().catch(e => { console.error(e); process.exit(1); });
