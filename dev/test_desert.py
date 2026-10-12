"""Environments by latitude (1.64): each latitude has the environments that really occur there and every map picks one
(from its map number, so the same map always comes back the same). The desert: sand, dunes, red rock, saguaro cactus,
Joshua trees and scrub, little water; only desert animals (coyote, oryx, camel, roadrunner, jackrabbit, vultures)."""
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
        # 1) the roll: which latitudes can give a desert, and how often
        out["roll"] = await pg.evaluate("""() => { window.FREEZE = true; D.set.env = 'auto'; const res = {};
          for (const lat of [5, 18, 28, 40, 55, 75]) { D.set.lat = lat; D.set.hemi = 1; const c = {};
            for (let sd = 1; sd <= 200; sd++) { D.setSeed(sd); const b = D.rollEnv(); c[b] = (c[b] || 0) + 1; }
            res[lat] = c; }
          D.set.lat = 28; D.setSeed(77); const a = D.rollEnv(), b2 = D.rollEnv(); res.same = a === b2;
          res.note28 = D.envNote(28); res.note55 = D.envNote(55); D.set.env = 'climate'; return res; }""")
        # 2) a desert map
        out["map"] = await pg.evaluate("""() => { D.set.env = 'desert'; D.setSeed(4); D.setVR(true); D.setMode('hunt'); D.set.land = 'natural'; D.set.size = 'large'; D.set.lat = 28; D.set.weather = 'clear'; D.generate(); D.state = 'play';
          const o = { env: D.MAPENV.b }, kinds = {}; for (const A of D.beasts) kinds[A.kind] = (kinds[A.kind] || 0) + 1; o.kinds = kinds;
          const want = D.NATIVE.desert.map(k => k[0]).filter(k => !D.LEGEND[k]); o.missing = want.filter(k => !kinds[k]); o.foreign = Object.keys(kinds).filter(k => !D.NATIVE.desert.some(n => n[0] === k));
          const trees = {}; for (const L of D.obstacles.values()) for (const t of L) if (t.tr !== undefined) trees.n = (trees.n || 0) + 1; o.treeObstacles = trees.n || 0;
          // water: only a little of the map
          let wet = 0, n = 0; for (let x = -390; x <= 390; x += 15) for (let z = -390; z <= 390; z += 15) { n++; if (D.H(x, z) < D.water) wet++; } o.water = +(wet / n).toFixed(3);
          // ground colour: sandy
          o.porch = !!D.PORCH;
          for (let i = 0; i < 300; i++) D.updateAnimals(1 / 30);
          o.moving = D.beasts.filter(A => !A.wings && A.speed > .1).length;
          D.setLoot({ pistol: 1 }); D.dropUse({ type: 'gun', kind: 'hunt', tier: 5, x: 0, y: 0, z: 0, id: 'gRed' });
          const cv = D.VBAN.m && D.VBAN.m.userData.cv; o.legend = D.beasts.some(A => A.kind === 'bigfoot');
          D.set.env = 'climate'; return o; }""")
        if SHOTS:
            for name, js in [("desert_view", "D.camera.position.set(D.P.x, D.H(D.P.x, D.P.z) + 40, D.P.z); D.camera.rotation.set(-.22, .6, 0, 'YXZ');"),
                             ("desert_ground", "D.camera.position.set(D.P.x, D.H(D.P.x, D.P.z) + 1.7, D.P.z); D.camera.rotation.set(-.03, 2.2, 0, 'YXZ');")]:
                img = await pg.evaluate("""(js) => { D.set.env = 'desert'; D.setSeed(4); D.setVR(false); D.setMode('hike'); D.set.size = 'medium'; D.set.lat = 28; D.set.hour = 10; D.generate(); D.state = 'play'; D.camera.fov = 65; D.camera.updateProjectionMatrix();
                  eval(js); D.camera.updateMatrixWorld(); D.cullTiles && D.cullTiles(); D.renderer.render(D.scene, D.camera); D.set.env = 'climate'; return D.renderer.domElement.toDataURL('image/jpeg', .85); }""", js)
                open(os.path.join(SHOTS, name + ".jpg"), "wb").write(base64.b64decode(img.split(",")[1]))
        print(json.dumps(out))
        R, M = out["roll"], out["map"]
        ok = set(R["5"]) == {"rainforest", "tropical"} and R["5"]["rainforest"] > 100 and set(R["18"]) == {"tropical", "desert"} and set(R["28"]) == {"desert", "swamp", "temperate"} and 60 < R["28"]["desert"] < 140 \
             and set(R["40"]) == {"temperate", "desert", "badlands"} and R["40"]["desert"] < 70 and "desert" not in R["55"] and "desert" not in R["75"] and R["same"] \
             and R["note28"] == "Desert or swamp or forest: each map picks" and R["note55"].startswith("Boreal") \
             and M["env"] == "desert" and not M["missing"] and not M["foreign"] and M["treeObstacles"] > 100 and M["water"] < .12 and M["porch"] and M["moving"] > 5
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
