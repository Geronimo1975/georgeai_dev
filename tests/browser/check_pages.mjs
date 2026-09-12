import { chromium } from "playwright";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const axeSource = require("axe-core").source;

const base = process.argv[2] || "http://127.0.0.1:8765";
const pages = ["/", "/en/", "/kontakt/", "/en/contact/"];
// links to pages that only exist after Phase 2 are tolerated for now
const allowMissing = [/^\/(en\/)?(leistungen|services|projekte|work|blog|preise|pricing|ueber-mich|about|konfigurator|configurator|impressum|datenschutz|agb|cookies|legal)\b/];
let failures = 0;
const check = (ok, msg) => { console.log((ok ? "ok   " : "FAIL ") + msg); if (!ok) failures++; };

const browser = await chromium.launch();
for (const theme of ["light", "dark"]) {
  for (const width of [1280, 390]) {
    const ctx = await browser.newContext({ viewport: { width, height: 900 }, timezoneId: "Europe/Berlin" });
    await ctx.addInitScript((t) => localStorage.setItem("ga_theme", t), theme);
    for (const path of pages) {
      const page = await ctx.newPage();
      const errors = [];
      // /api/ resource errors are backend status (401/404), not page defects; a JS exception from auth.js still fails via pageerror.
      page.on("console", (m) => {
        if (m.type() !== "error") return;
        const url = (m.location() && m.location().url) || "";
        if (url.includes("/api/") && m.text().startsWith("Failed to load resource")) return; // backend status endpoint, handled by auth.js
        errors.push(m.text());
      });
      page.on("pageerror", (e) => errors.push(e.message));
      const resp = await page.goto(base + path, { waitUntil: "networkidle" });
      const tag = `${path} ${theme} ${width}px`;
      check(resp.status() === 200, `${tag}: status 200`);
      check(errors.length === 0, `${tag}: no console errors ${errors.join(" | ")}`);
      check(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), `${tag}: no horizontal overflow`);
      check((await page.locator("h1").count()) === 1, `${tag}: one h1`);
      check(await page.evaluate(() => document.documentElement.getAttribute("data-theme") === localStorage.getItem("ga_theme")), `${tag}: theme applied`);
      const hrefs = await page.locator('a[href^="/"]').evaluateAll((as) => [...new Set(as.map((a) => a.getAttribute("href")))]);
      for (const h of hrefs) {
        const r = await ctx.request.get(base + h);
        const tolerated = allowMissing.some((re) => re.test(h));
        check(r.status() === 200 || tolerated, `${tag}: link ${h} -> ${r.status()}`);
      }
      const alt = await page.locator('link[rel="alternate"]').evaluateAll((ls) => ls.map((l) => l.getAttribute("hreflang")));
      check(alt.includes("de") && alt.includes("en") && alt.includes("x-default"), `${tag}: hreflang de/en/x-default`);
      await page.keyboard.press("Tab");
      check(await page.evaluate(() => { const el = document.activeElement; return el && el !== document.body && getComputedStyle(el).outlineStyle !== "none"; }), `${tag}: first Tab lands on a visibly focused element`);
      await page.addScriptTag({ content: axeSource });
      const axe = await page.evaluate(async () => (await window.axe.run(document, { runOnly: ["wcag2a", "wcag2aa"] })).violations.filter((v) => ["serious", "critical"].includes(v.impact)).map((v) => v.id + ":" + v.nodes.length));
      check(axe.length === 0, `${tag}: axe serious/critical ${axe.join(",")}`);
      await page.close();
    }
    await ctx.close();
  }
}

// flows (light, desktop)
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, timezoneId: "Europe/Berlin" });
const page = await ctx.newPage();
await page.goto(base + "/en/", { waitUntil: "networkidle" });
await page.locator("[data-theme-toggle]").click();
await page.reload({ waitUntil: "networkidle" });
check(await page.evaluate(() => document.documentElement.getAttribute("data-theme") === "dark"), "theme toggle persists across reload");
const second = page.locator("[data-panel] .panel__hit").nth(1);
await second.focus(); await page.keyboard.press("Enter");
check((await second.getAttribute("aria-pressed")) === "true", "hero panel activates by keyboard");
await page.setViewportSize({ width: 390, height: 844 });
await page.locator("[data-menu-toggle]").click();
check(await page.locator("#site-menu").isVisible(), "mobile menu opens");
await page.keyboard.press("Escape");
check(!(await page.locator("#site-menu").isVisible()), "mobile menu closes on Escape");
await page.setViewportSize({ width: 1280, height: 900 });
await page.goto(base + "/en/contact/", { waitUntil: "networkidle" });
await page.locator('form[data-booking] button[type="submit"]').click();
check((await page.locator("[data-booking-error]").textContent()).startsWith("Still needed:"), "empty submit shows the alert");
const firstDay = page.locator("[data-booking-days] button").first();
await firstDay.focus(); await page.keyboard.press("Space");
await page.locator("[data-booking-slots] button").nth(2).click();
await page.fill("#ga-ct-name", "Max Mustermann"); await page.fill("#ga-ct-email", "max@example.de");
const label = await firstDay.getAttribute("aria-label");
await page.locator('form[data-booking] button[type="submit"]').click();
const summary = await page.locator("[data-booking-summary]").textContent();
check(summary.includes(label) && summary.includes("12:00"), `booking summary matches the chip (${summary})`);
check((await page.locator("[data-booking-body]").textContent()).includes("max@example.de"), "mail body carries the email");
check((await page.locator("[data-booking-mail]").getAttribute("href")).includes("subject="), "mailto link carries the subject");
await page.locator("[data-booking-edit]").click();
check((await page.inputValue("#ga-ct-name")) === "Max Mustermann", "edit keeps the values");
await browser.close();
console.log(failures ? `\n${failures} failure(s)` : "\nall checks passed");
process.exit(failures ? 1 : 0);
