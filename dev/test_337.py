"""3.37 (Dev): the speed check. In Dev Mode each frame's own work is timed (moving, land, animals, sending the picture) and shown on the
wrist under the fps; the pause menu's Speed check switches things off (near trees, far trees, ground, far land, water, animals, sky),
sets foveation, and picks the sharpness for the next time you go into VR. Usage: python3 dev/test_337.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        await pg.evaluate("""() => { D.DEV.ok = true; D.setSeed(4242); D.setVR(true); D.vr.on = true; D.setMode('hunt'); Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .5, rough: .5, huntMap: 'globe', dino: false });
          D.generate(); D.state = 'play'; return 1; }""")
        await pg.wait_for_timeout(3500)   # (the real loop runs: frames are timed)
        r = await pg.evaluate("""() => { const o = {}, S = D.SPD.show; o.timed = ['all', 'move', 'land', 'anim', 'draw'].map(k => typeof S[k] === 'number'); o.calls = D.SPD.calls;
          D.SPD.off = { trees: true, cards: true, ground: true, far: true, water: true, animals: true, sky: true }; D.perfApply();
          o.off = [D.ENDLESS.far ? D.ENDLESS.far.visible : null, D.ENDLESS.water ? D.ENDLESS.water.visible : null, D.tiles.every(t => !t.lo.visible)];
          D.SPD.off = {}; D.perfApply(); o.back = [D.ENDLESS.far ? D.ENDLESS.far.visible : null, D.ENDLESS.water ? D.ENDLESS.water.visible : null, D.tiles.every(t => t.lo.visible)];
          D.vruiOpen('perf'); D.uiDraw(D.VRUI.panels.perf); const cv = document.createElement('canvas'); cv.width = cv.height = 512; cv.id = 'vrMap'; D.drawMap(cv); o.drawn = true;
          return o; }""")
        print(json.dumps(r)); print("errors:", errs[:5] or "none")
        ok = all(r["timed"]) and r["calls"] > 0 and r["off"] == [False, False, True] and r["back"] == [True, True, True] and r["drawn"] and not errs
        print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
