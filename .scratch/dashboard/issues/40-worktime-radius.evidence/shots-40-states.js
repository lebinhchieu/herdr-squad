// Ticket 40 return 1: scale-4 crops of the segment states (focus - , focus ◀, hover +, hover ▶), after the paint-order fix.
// argv: url outdir. env PLAYWRIGHT_CORE, CHROME_BIN. Real keyboard focus (Tab) and real mouse hover.
const path = require("path");
const pw = require(path.join(process.env.PLAYWRIGHT_CORE, "index.js"));
(async () => {
  const [url, outdir] = process.argv.slice(2);
  const browser = await pw.chromium.launch({ executablePath: process.env.CHROME_BIN, headless: true, args: ["--no-sandbox"] });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 4 });
  const page = await ctx.newPage();
  await page.goto(url);
  await page.waitForSelector(".demo:not([hidden])", { timeout: 15000 });
  await page.waitForSelector(".tl-bar .seg", { timeout: 15000 });
  await page.waitForTimeout(300);
  const btn = (g, i) => page.locator(".tl-bar .seg").nth(g).locator("button").nth(i);
  const crop = async (name, g, state, i) => {
    const b = btn(g, i);
    if (state === "focus") { await page.mouse.move(0, 0); await b.focus(); await page.keyboard.press("Shift+Tab"); await page.keyboard.press("Tab"); }
    else { await page.evaluate(() => document.activeElement && document.activeElement.blur()); await b.hover(); }
    const r = await page.locator(".tl-bar .seg").nth(g).boundingBox();
    await page.screenshot({ path: path.join(outdir, name), clip: { x: r.x - 8, y: r.y - 8, width: r.width + 16, height: r.height + 16 } });
  };
  await crop("seg-focus-minus-x4.png", 0, "focus", 0);
  await crop("seg-focus-left-x4.png", 1, "focus", 0);
  await crop("seg-hover-plus-x4.png", 0, "hover", 1);
  await crop("seg-hover-right-x4.png", 1, "hover", 1);
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
