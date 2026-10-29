"""2.93: the Test Lab (Gear + Gun Labs in one: a Treeocashing planet with every item and gun, and the shooting range); tweaks act at
once and only Save keeps them; Dev "Full level": online Treeocashing as if you'd found everything, your real level untouched; the
Underworld doorways only from level 50 (the Lab sees them).
Usage: python3 dev/test_293.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 240})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(400)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); localStorage.setItem('jt-geochar', JSON.stringify({ n: 7, score: 3, kills: 0 })); localStorage.removeItem('jt-tune'); D.DEV.ok = true; D.setSeed(4242); D.setVR(true); D.vr.on = true; D.set.hand = 'right';
          D.setMode('hunt'); Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .7, rough: .5, huntMap: 'globe', dino: false });
          const o = {}, P = D.P;
          // the Test Lab
          D.GEO.labWant = true; D.GUNLAB.want = true; D.generate(); D.state = 'play'; for (let i = 0; i < 60; i++) { D.endlessTick(1 / 30); D.geoTick(1 / 30); } D.gunLabStart();
          o.lab = [D.GEO.lab, D.GUNLAB.on, D.GUNLAB.dummies.length, Math.round(Math.max(...D.GUNLAB.dummies.map(d => Math.hypot(d.x - P.x, d.z - P.z)))), D.GEO.items.size > 20, D.ugSees()];
          const td = D.TUNE_DEF[0], v0 = D.TUNE[td[0]]; D.tuneStep(td, 1); o.tweak = [D.TUNE[td[0]] !== v0, D.LAB_DIRTY.v, localStorage.getItem('jt-tune')];
          D.testLabSave(); o.saved = [!D.LAB_DIRTY.v, !!localStorage.getItem('jt-tune') && JSON.parse(localStorage.getItem('jt-tune'))[td[0]] === D.TUNE[td[0]]];
          D.tuneStep(td, -1); D.testLabSave(); localStorage.removeItem('jt-tune');
          // Full level (Dev): everything, nothing saved over your character
          D.GEO.labWant = false; D.GUNLAB.want = false; D.MP.code = '9999'; D.set.geoNet = true; D.DEV.full = true; D.generate(); for (let i = 0; i < 30; i++) { D.endlessTick(1 / 30); D.geoTick(1 / 30); }
          o.full = [D.GEO.full, D.GEO.found.size, D.GEO.lab, D.ugSees()]; D.geoSave(); o.kept = JSON.parse(localStorage.getItem('jt-geochar')).n;
          // and off again: your own level
          D.DEV.full = false; D.generate(); for (let i = 0; i < 30; i++) { D.endlessTick(1 / 30); D.geoTick(1 / 30); } o.own = [D.GEO.full, D.GEO.found.size, D.ugSees()];
          return o; }""")
        print(json.dumps(r))
        ok = r["lab"][0] and r["lab"][1] and r["lab"][2] == 6 and r["lab"][3] < 450 and r["lab"][4] and r["lab"][5] and r["tweak"][0] and r["tweak"][1] and r["tweak"][2] is None and r["saved"][0] and r["saved"][1] \
             and r["full"] == [True, 55, False, True] and r["kept"] == 7 and r["own"] == [False, 7, False]
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
