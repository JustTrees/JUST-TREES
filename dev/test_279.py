"""2.79: the Gear Lab (Dev menu): a Treeocashing planet with every item and red gun, jet skis on, nothing saved to your character;
its helpers (lake, sea beach + jet ski, predators, day/night, refill, next cache close) and the live tweaks (kept on the headset).
Usage: python3 dev/test_279.py dbg.html [panel.png]"""
import sys, asyncio, json, base64
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); localStorage.setItem('jt-geochar', JSON.stringify({ n: 7, score: 70, kills: 1 })); localStorage.removeItem('jt-tune');
          D.DEV.ok = true; D.setSeed(4242); D.setVR(true); D.setMode('hunt'); D.vr.on = true; Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .5, rough: .5, huntMap: 'globe', dino: false });
          D.GEO.labWant = true; D.generate(); D.state = 'play'; const tick = n => { for (let i = 0; i < n; i++) { D.endlessTick(1 / 30); D.geoTick(1 / 30); } }; tick(30);
          const o = {}, V = D.vr, P = D.P;
          o.lab = [D.GEO.lab, D.GEO.items.size, Object.values(V.own).filter(v => v >= 5).length, D.jetOn()];
          D.geoSave(); o.charKept = JSON.parse(localStorage.getItem('jt-geochar')).n;
          // tweaks
          const s0 = D.geoSpeedMul(); D.tuneStep(D.TUNE_DEF.find(d => d[0] === 'boots'), 1); o.tweak = [+s0.toFixed(2), +D.geoSpeedMul().toFixed(2), JSON.parse(localStorage.getItem('jt-tune')).boots];
          // helpers
          D.glabTime(23); tick(2); o.night = Math.round(D.hourNow);
          D.glabRefill(); o.refill = [D.GEO.food, D.GEO.water, D.GEO.cant];
          const p0 = [P.x, P.z]; D.glabLake(); tick(5); let lake = 0; for (let k = 0; k < 400 && !lake; k++) { const a = k * 2.4, rr = k * .4, x = P.x + Math.cos(a) * rr, z = P.z + Math.sin(a) * rr; if (D.H(x, z) < D.water - 1 && !D.geoSalty({ x, z })) lake = Math.round(rr); }
          o.lake = [D.H(P.x, P.z) > D.water, lake, Math.round(Math.hypot(P.x - p0[0], P.z - p0[1]))];
          const nJ = D.JET.list.length; D.glabSea(); tick(5); D.GEO.tT = 0; tick(2); const J = D.JET.list[D.JET.list.length - 1]; o.sea = [D.JET.list.length - nJ, !!(J && J.obj), J ? Math.round(Math.hypot(J.x - P.x, J.z - P.z)) : -1];
          D.glabPred('bear'); const B = D.beasts.filter(A => A.pred && !A.dead).length; o.pred = B;
          D.glabCache(); D.GEO.tT = 0; tick(2); o.cache = Math.round(D.glArc(D.GLOBE.p, D.GEO.target.p) * D.GLOBE.R);
          D.vruiOpen('glab'); const Pn = D.VRUI.panels.glab; D.uiDraw(Pn); o.png = Pn.cv.toDataURL();
          return o; }""")
        png = r.pop("png"); open(sys.argv[2] if len(sys.argv) > 2 else "/dev/null", "wb").write(base64.b64decode(png.split(",")[1]))
        print("lab", json.dumps(r))
        ok = r["lab"] == [True, 24, 5, True] and r["charKept"] == 7 and r["tweak"][1] > r["tweak"][0] and r["tweak"][2] == 1.2 and (r["night"] >= 22 or r["night"] <= 0) \
             and r["refill"] == [100, 100, 4] and r["lake"][0] and r["lake"][1] < 130 and r["sea"][0] == 1 and r["sea"][1] and r["sea"][2] < 40 and r["pred"] >= 1 and r["cache"] < 60
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
