"""Swamp (1.69): warm wet lowland at 23-35° (sometimes). Nearly flat land half under still, dark, murky water (no pale shallows, no foam),
low hummocks and islands, bald cypress standing right in the water hung with moss; only swamp animals (alligators, herons, deer, hogs, panther, black bear, turkeys, rabbits)."""
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
          for (const lat of [10, 27, 33, 40]) { D.set.lat = lat; D.set.hemi = 1; const c = {}; for (let sd = 1; sd <= 200; sd++) { D.setSeed(sd); const b = D.rollEnv(); c[b] = (c[b] || 0) + 1; } res[lat] = c; }
          res.note27 = D.envNote(27); D.set.env = 'climate'; return res; }""")
        out["map"] = await pg.evaluate("""() => { D.set.env = 'swamp'; D.setSeed(6); D.setVR(true); D.setMode('hunt'); D.set.size = 'large'; D.set.lat = 29; D.set.weather = 'clear'; D.generate(); D.state = 'play';
          const o = { env: D.MAPENV.b }, kinds = {}; for (const A of D.beasts) kinds[A.kind] = (kinds[A.kind] || 0) + 1; o.kinds = kinds;
          const want = D.NATIVE.swamp.map(k => k[0]).filter(k => !D.LEGEND[k]); o.missing = want.filter(k => !kinds[k]); o.foreign = Object.keys(kinds).filter(k => !D.NATIVE.swamp.some(n => n[0] === k));
          // half the land under water, and shallow: you can wade almost everywhere
          let n = 0, wet = 0, deep = 0; for (let x = -380; x <= 380; x += 5) for (let z = -380; z <= 380; z += 5) { n++; const h = D.H(x, z); if (h < D.water) { wet++; if (h < D.water - 1.4) deep++; } }
          o.wet = +(wet / n).toFixed(2); o.deepShare = +(deep / Math.max(1, wet)).toFixed(2);
          // cypress standing in the water
          let inWater = 0; for (const L of D.obstacles.values()) for (const q of L) if (q.tr !== undefined && D.H(q.x, q.z) < D.water - .1) inWater++; o.treesInWater = inWater;
          o.murky = !!D.scene.children.concat(D.world ? D.world.children : []).find(m => m.material && m.material.uniforms && m.material.uniforms.uMurky && m.material.uniforms.uMurky.value === 1);
          for (let i = 0; i < 300; i++) D.updateAnimals(1 / 30); o.moving = D.beasts.filter(A => !A.wings && A.speed > .1).length;
          D.set.env = 'climate'; return o; }""")
        if SHOTS:
            for name, js in [("swamp_view", "D.camera.position.set(D.P.x, D.H(D.P.x, D.P.z) + 40, D.P.z); D.camera.rotation.set(-.22, .6, 0, 'YXZ');"),
                             ("swamp_ground", "D.camera.position.set(D.P.x, D.H(D.P.x, D.P.z) + 1.7, D.P.z); D.camera.rotation.set(-.03, 2.2, 0, 'YXZ');")]:
                img = await pg.evaluate("""(js) => { D.set.env = 'swamp'; D.setSeed(6); D.setVR(false); D.setMode('hike'); D.set.size = 'medium'; D.set.lat = 29; D.set.hour = 10; D.generate(); D.state = 'play'; D.camera.fov = 65; D.camera.updateProjectionMatrix();
                  eval(js); D.camera.updateMatrixWorld(); D.cullTiles && D.cullTiles(); D.renderer.render(D.scene, D.camera); D.set.env = 'climate'; return D.renderer.domElement.toDataURL('image/jpeg', .85); }""", js)
                open(os.path.join(SHOTS, name + ".jpg"), "wb").write(base64.b64decode(img.split(",")[1]))
        print(json.dumps(out))
        R, M = out["roll"], out["map"]
        ok = "swamp" not in R["10"] and "swamp" in R["27"] and 20 < R["27"]["swamp"] < 70 and "swamp" in R["33"] and "swamp" not in R["40"] \
             and R["note27"] == "Desert or swamp or forest: each map picks" and M["env"] == "swamp" and not M["missing"] and not M["foreign"] \
             and .3 < M["wet"] < .65 and M["deepShare"] < .25 and M["treesInWater"] > 50 and M["murky"] and M["moving"] > 5
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
