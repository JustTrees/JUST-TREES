"""3.47: the Trail guide in the pause menu (Treeocashing). The basics pages from the start; a page for each gun and piece of gear as soon
as you have it; the next 3 levels' pages shown locked ("find N more caches"); pages you haven't opened are counted as new on the pause
menu's button, and opening one marks it seen (kept on the headset). The pause menu's buttons squeeze to fit. Usage: python3 dev/test_347.py dbg.html"""
import os, sys, asyncio, json, re, base64
from playwright.async_api import async_playwright
here = os.path.dirname(os.path.abspath(__file__))
GEN = re.search(r'GEN = """(.*?)"""', open(os.path.join(here, "test_275.py")).read(), re.S).group(1)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 400, "height": 260})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        await pg.evaluate(GEN, 1)
        r = await pg.evaluate("""() => { const o = {}; localStorage.removeItem('jt-guide-seen'); D.GUIDE.seen.clear();
          const L1 = D.guidePages(); o.l1 = [L1.length, L1.filter(p => p.lock).length, L1.some(p => p.k === 'g:pistol'), L1.some(p => p.k === 'i:torch'), L1.filter(p => p.lock).map(p => p.t)];
          o.new1 = D.guideNew();
          D.vruiOpen('pause'); const B = D.VRUI.panels.pause.widgets.find(w => w.label === 'Trail guide'); o.btn = [!B.hide(), B.labelFn()];
          const vis = D.VRUI.panels.pause.widgets.filter(w => !(w.hide && w.hide())); o.fits = vis.every(w => w.y + w.h <= 1000);
          B.on(); o.stage = D.VRUI.stage; D.uiDraw(D.VRUI.panels.guide); o.seenAfter = D.GUIDE.seen.size;
          const pic1 = D.VRUI.panels.guide.cv.toDataURL('image/png');
          // later: level 30
          D.GEO.found = new Set(Array.from({ length: 30 }, (_, i) => 'c' + i)); D.geoGearApply(30, true);
          const L2 = D.guidePages(); o.l2 = [L2.length, L2.filter(p => p.lock).length, L2.some(p => p.k === 'i:rod'), L2.some(p => p.k === 'g:hunt'), L2.some(p => p.k === 'b:isle')];
          o.new2 = D.guideNew(); D.GUIDE.sel = L2.findIndex(p => p.k === 'i:rod'); D.uiDraw(D.VRUI.panels.guide); o.rodSeen = D.GUIDE.seen.has('i:rod'); o.kept = JSON.parse(localStorage.getItem('jt-guide-seen')).includes('i:rod');
          const pic2 = D.VRUI.panels.guide.cv.toDataURL('image/png');
          D.GEO.found = new Set(Array.from({ length: 50 }, (_, i) => 'c' + i)); D.geoGearApply(50, true); o.isle = D.guidePages().some(p => p.k === 'b:isle');
          return [o, pic1, pic2]; }""")
        o = r[0]
        for i, d in enumerate(r[1:]): open(os.path.join(os.environ.get("JT_PICS", "/tmp"), f"guide{i}.png"), "wb").write(base64.b64decode(d.split(",")[1]))
        print(json.dumps(o))
        ok = o["l1"][1] == 3 and o["l1"][2] and o["l1"][3] and o["new1"] >= 5 and o["btn"][0] and "new" in o["btn"][1] and o["fits"] and o["stage"] == "guide" \
             and o["seenAfter"] >= 1 and o["l2"][1] == 3 and o["l2"][2] and o["l2"][3] and not o["l2"][4] and o["new2"] > o["new1"] - 2 and o["rodSeen"] and o["kept"] and o["isle"]
        print("PASS" if ok and not errs else "FAIL", errs[:5]); print("errors: none" if not errs else "errors: " + str(errs[:5])); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
