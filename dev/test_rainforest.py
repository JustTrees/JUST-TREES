"""Rainforest (1.66): near the equator (under 10°: mostly rainforest, 10-15°: sometimes). Tall trees with buttress roots, wide crowns high up,
lianas hanging, thick undergrowth, few clearings, mossy rocks, wet weather; only rainforest animals (jaguar, tapir, capybara, monkeys, parrots, caiman, peccary)."""
import os, sys, asyncio, json, base64
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1]); SHOTS = sys.argv[2] if len(sys.argv) > 2 and os.path.isdir(sys.argv[2]) else None
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 900, "height": 560})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        out = {}
        out["roll"] = await pg.evaluate("""() => { window.FREEZE = true; D.set.env = 'auto'; const res = {};
          for (const lat of [3, 12, 20]) { D.set.lat = lat; D.set.hemi = 1; const c = {}; for (let sd = 1; sd <= 200; sd++) { D.setSeed(sd); const b = D.rollEnv(); c[b] = (c[b] || 0) + 1; } res[lat] = c; }
          res.note3 = D.envNote(3); D.set.env = 'climate'; return res; }""")
        out["map"] = await pg.evaluate("""() => { D.set.env = 'rainforest'; D.setSeed(5); D.setVR(true); D.setMode('hunt'); D.set.size = 'large'; D.set.lat = 3; D.set.weather = 'clear'; D.generate(); D.state = 'play';
          const o = { env: D.MAPENV.b }, kinds = {}; for (const A of D.beasts) kinds[A.kind] = (kinds[A.kind] || 0) + 1; o.kinds = kinds;
          const want = D.NATIVE.rainforest.map(k => k[0]).filter(k => !D.LEGEND[k]); o.missing = want.filter(k => !kinds[k]); o.foreign = Object.keys(kinds).filter(k => !D.NATIVE.rainforest.some(n => n[0] === k));
          // few clearings: share of 20 m cells with a tree trunk nearby
          let cells = 0, treed = 0; for (let x = -380; x <= 380; x += 20) for (let z = -380; z <= 380; z += 20) { if (D.H(x, z) < D.water + 1) continue; cells++; let t = false;
            for (let a = -1; a <= 1 && !t; a++) for (let c = -1; c <= 1 && !t; c++) { const L = D.obstacles.get((Math.floor(x / 8) + a) + ',' + (Math.floor(z / 8) + c)); if (L) for (const q of L) if (q.tr !== undefined) { t = true; break; } } if (t) treed++; }
          o.canopy = +(treed / cells).toFixed(2);
          // the forest is tall
          let tallest = 0; for (const L of D.obstacles.values()) for (const q of L) if (q.tr !== undefined && q.h) tallest = Math.max(tallest, q.h); o.tallTree = +tallest.toFixed(1);
          for (let i = 0; i < 300; i++) D.updateAnimals(1 / 30); o.moving = D.beasts.filter(A => !A.wings && A.speed > .1).length;
          D.set.env = 'climate'; return o; }""")
        if SHOTS:
            for name, js in [("rainforest_view", "D.camera.position.set(D.P.x, D.H(D.P.x, D.P.z) + 40, D.P.z); D.camera.rotation.set(-.22, .6, 0, 'YXZ');"),
                             ("rainforest_ground", "D.camera.position.set(D.P.x, D.H(D.P.x, D.P.z) + 1.7, D.P.z); D.camera.rotation.set(-.03, 2.2, 0, 'YXZ');")]:
                img = await pg.evaluate("""(js) => { D.set.env = 'rainforest'; D.setSeed(5); D.setVR(false); D.setMode('hike'); D.set.size = 'medium'; D.set.lat = 3; D.set.hour = 10; D.generate(); D.state = 'play'; D.camera.fov = 65; D.camera.updateProjectionMatrix();
                  eval(js); D.camera.updateMatrixWorld(); D.cullTiles && D.cullTiles(); D.renderer.render(D.scene, D.camera); D.set.env = 'climate'; return D.renderer.domElement.toDataURL('image/jpeg', .85); }""", js)
                open(os.path.join(SHOTS, name + ".jpg"), "wb").write(base64.b64decode(img.split(",")[1]))
        print(json.dumps(out))
        R, M = out["roll"], out["map"]
        ok = set(R["3"]) == {"rainforest", "tropical"} and R["3"]["rainforest"] > 100 and set(R["12"]) == {"rainforest", "tropical"} and R["12"]["rainforest"] < 100 and "rainforest" not in R["20"] \
             and R["note3"] == "Rainforest or palm jungle: each map picks" and M["env"] == "rainforest" and not M["missing"] and not M["foreign"] and M["canopy"] > .85 and M["tallTree"] > 17 and M["moving"] > 5
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
