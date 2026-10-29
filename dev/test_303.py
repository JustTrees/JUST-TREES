"""3.03: two pairs of glasses past level 50: blue blockers (find 52: an amber tint) and thermal glasses (find 80: the world dark with red
outlines, anything warm glowing); one pair on at a time; the binoculars start much wider (30° and 18° before the old 11°).
Usage: python3 dev/test_303.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 240})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(400)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); localStorage.setItem('jt-geochar', JSON.stringify({ n: 82, score: 0, kills: 0 })); D.setSeed(4242); D.setVR(true); D.vr.on = true;
          D.setMode('hunt'); Object.assign(D.set, { env: 'climate', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', huntMap: 'globe', dino: false });
          D.MP.code = '9999'; D.set.geoNet = true; D.generate(); D.state = 'play'; for (let i = 0; i < 20; i++) { D.endlessTick(1 / 30); D.geoTick(1 / 30); }
          const o = {}, T = D.THREE, P = D.P, I = { head: new T.Vector3(P.x, P.y + 1.6, P.z), headQ: new T.Quaternion(), hands: {} };
          o.rew = [D.geoRewardOf(52).item, D.geoRewardOf(80).item, D.geoRewardOf(56).item || null]; o.have = [D.GEO.items.has('bblock'), D.GEO.items.has('tglass')];
          D.GEO.worn.add('tglass'); for (let i = 0; i < 30; i++) D.geoWornTick(I); o.therm = [+D.HFOG.uThG.value.toFixed(2), D.sky.visible];
          D.GEO.worn.clear(); D.GEO.worn.add('bblock'); for (let i = 0; i < 30; i++) D.geoWornTick(I); o.bb = [+D.HFOG.uThG.value.toFixed(2), D.GEO.bbM.visible, D.sky.visible];
          D.GEO.worn.clear(); for (let i = 0; i < 30; i++) D.geoWornTick(I); o.off = [D.GEO.bbM.visible, D.HFOG.uThG.value];
          o.binos = D.binoFovs().slice(0, 3);
          return o; }""")
        print(json.dumps(r))
        ok = r["rew"] == ["bblock", "tglass", None] and r["have"] == [True, True] and r["therm"][0] > .9 and not r["therm"][1] and r["bb"][0] == 0 and r["bb"][1] and r["bb"][2] and r["off"] == [False, 0] and r["binos"] == [30, 18, 11]
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
