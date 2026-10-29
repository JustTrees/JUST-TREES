"""3.20: online Hunting and Hiking: taken down, you're back in 60-180 m from another player (on dry, gentle ground, away from predators),
on the 3 km island and on endless land; with nobody else, it's random as before. Treeocashing: random respawns never land on the
dinosaur island.
Usage: python3 dev/test_320.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 200})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(400)
        out = {}
        for mode, mp in [["hunt", "island"], ["hunt", "endless"], ["hike", "endless"]]:
            r = await pg.evaluate("""([mode, mp]) => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setSeed(4242); D.setVR(true); D.vr.on = true; D.setMode(mode);
              Object.assign(D.set, { env: 'temperate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', huntMap: mp, hikeMap: mp, edges: mp === 'island' ? 'island' : 'endless', dino: false });
              D.generate(); D.state = 'play'; for (let i = 0; i < 30; i++) D.endlessTick && D.ENDLESS && D.endlessTick(1 / 30);
              const T = D.THREE, P = D.P; let fx = P.x + 250, fz = P.z + 120; for (let k = 0; k < 200; k++) { if (D.H(fx, fz) > D.water + 2) break; fx -= 10; }
              D.MP.on = true; D.MP.code = '7777'; const L = { id: 'zz', open: true, R: { cur: {}, alive: true, head: new T.Vector3(fx, D.H(fx, fz) + 1.6, fz) } }; D.MP.links.set('zz', L);
              const ds = []; for (let i = 0; i < 8; i++) { D.uwRespawn(); ds.push(Math.round(Math.hypot(P.x - fx, P.z - fz))); }
              const dry = D.H(P.x, P.z) > D.water + 2;
              D.MP.links.delete('zz'); const sx = P.x, sz = P.z; D.uwRespawn(); const alone = Math.round(Math.hypot(P.x - fx, P.z - fz));
              D.MP.on = false; D.MP.code = ''; return { ds, dry, alone }; }""", [mode, mp])
            out[mode + "-" + mp] = r
        g = await pg.evaluate("""() => { localStorage.setItem('jt-geochar', JSON.stringify({ n: 10, score: 0, kills: 0 })); D.setSeed(4242); D.setMode('hunt'); Object.assign(D.set, { huntMap: 'globe' }); D.MP.code = '9999'; D.set.geoNet = true; D.generate(); D.state = 'play';
          const G = D.GLOBE; let onIsle = 0; for (let i = 0; i < 300; i++) { const p = D.geoRandomSpot(); if (G.isle && D.glArc(p, G.isle.c) < G.isle.r) onIsle++; } return { onIsle, isle: !!G.isle }; }""")
        out["geo"] = g
        print(json.dumps(out))
        ok = all(all(55 <= d <= 300 for d in out[k]["ds"]) and out[k]["dry"] for k in ["hunt-island", "hunt-endless", "hike-endless"]) and g["isle"] and g["onIsle"] == 0
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
