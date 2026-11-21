// node blind.cjs <siteDir> <outDir> — owner mock: the Kör kodlama desk shows no AI words, saves with 1 + Enter, frame select + Enter.
const http = require("http"), fs = require("fs"), path = require("path");
const { chromium } = require("playwright");
const [siteDir, outDir] = process.argv.slice(2);
if (!siteDir || !outDir) { console.log("usage: node blind.cjs <siteDir> <outDir>"); process.exit(0); }
const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".json": "application/json" };
const BAD = /\bAI\b(?! Literacy)|Yapay|Doğrulan|kanıt|#\/olay/;
(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const root = path.resolve(siteDir), fails = [];
  const srv = http.createServer((q, s) => {
    const f = path.join(root, decodeURIComponent(q.url.split("?")[0]).replace(/\/$/, "/index.html"));
    if (!f.startsWith(root) || !fs.existsSync(f)) { s.writeHead(404); return s.end(); }
    s.writeHead(200, { "content-type": TYPES[path.extname(f)] || "application/octet-stream" }); s.end(fs.readFileSync(f));
  }).listen(0);
  const browser = await chromium.launch();
  for (const w of [1280, 390]) {
    const p = await browser.newPage({ viewport: { width: w, height: 900 } });
    await p.addInitScript(() => {
      const store = {}; let fn = null; const snap = () => fn && fn({ docs: Object.keys(store).map((id) => ({ id, data: () => store[id] })) });
      window.__store = store;
      const db = { collection: () => ({ onSnapshot: (f) => { fn = f; setTimeout(snap, 0); }, doc: (id) => ({ set: async (d) => { store[id] = d; snap(); }, delete: async () => { delete store[id]; snap(); } }) }) };
      window.claude = { use: async (k) => k === "user" ? { isOwner: async () => true, id: async () => "u" } : k === "db" ? db : null };
    });
    p.on("pageerror", (e) => { if (!/V3\.user/.test(e.message)) fails.push(w + ": " + e.message); });   // the mock user has no V3 profile methods
    await p.goto(`http://localhost:${srv.address().port}/#/yonetim?t=bilissel`);
    await p.waitForFunction(() => window.DATA && document.querySelector(".desk"), null, { timeout: 60000 }); await p.waitForTimeout(500);
    await p.click('[data-desk="group"][data-v="kor"]'); await p.waitForTimeout(200);
    const text = () => p.evaluate(() => document.querySelector(".desk").textContent + [...document.querySelectorAll(".desk a")].map((a) => a.getAttribute("href")).join(" "));
    const chk = async (what) => { const t = await text(), m = t.match(BAD); if (m) fails.push(`${w}: ${what} contains "${t.slice(Math.max(0, m.index - 30), m.index + 30)}"`); };
    await chk("packet list");
    for (const pid of ["behaviour-A1", "narrative-A2"]) {
      await p.click(`[data-desk="blind-packet"][data-v="${pid}"]`); await p.waitForTimeout(200);
      await chk(pid);
      await p.screenshot({ path: path.join(outDir, `blind-${pid}-${w}.png`) });
      if (w === 1280) {
        await p.keyboard.press("1");
        if (pid === "narrative-A2") await p.selectOption('[data-desk="blind-sel"]', "Spor");
        await p.keyboard.press("Enter"); await p.waitForTimeout(200);
        const n = await p.evaluate((id) => Object.keys(window.__store).filter((k) => k.startsWith("blind__" + id)).length, pid);
        if (n !== 1) fails.push(`${pid}: expected 1 saved answer, got ${n}`);
      }
      await p.click('[data-desk="blind-back"]');
    }
    if (await p.evaluate(() => document.documentElement.scrollWidth > innerWidth)) fails.push(`${w}: horizontal scroll`);
  }
  await browser.close(); srv.close();
  if (fails.length) { console.log(fails.join("\n")); process.exit(1); }
  console.log("blind ok");
})();
