"""Badlands (1.67): dry country at 30-45° (30-35: sometimes, 35-45: sometimes). Layered rock eroded into flat benches and sheer striped cliffs,
mesas with flat tops (no spikes), scattered junipers and sage; only badlands animals (bighorn sheep, pronghorn, mule deer, mustangs, coyotes, jackrabbits, eagles, vultures)."""
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
          for (const lat of [25, 32, 40, 50]) { D.set.lat = lat; D.set.hemi = 1; const c = {}; for (let sd = 1; sd <= 200; sd++) { D.setSeed(sd); const b = D.rollEnv(); c[b] = (c[b] || 0) + 1; } res[lat] = c; }
          res.note40 = D.envNote(40); D.set.env = 'climate'; return res; }""")
        out["map"] = await pg.evaluate("""() => { D.set.env = 'badlands'; D.setSeed(9); D.setVR(true); D.setMode('hunt'); D.set.size = 'large'; D.set.lat = 38; D.set.weather = 'clear'; D.generate(); D.state = 'play';
          const o = { env: D.MAPENV.b }, kinds = {}; for (const A of D.beasts) kinds[A.kind] = (kinds[A.kind] || 0) + 1; o.kinds = kinds;
          const want = D.NATIVE.badlands.map(k => k[0]).filter(k => !D.LEGEND[k]); o.missing = want.filter(k => !kinds[k]); o.foreign = Object.keys(kinds).filter(k => !D.NATIVE.badlands.some(n => n[0] === k));
          // benches and cliffs: lots of flat ground and lots of very steep ground, little in between
          let n = 0, flat = 0, cliff = 0, top = -1e9, top2 = -1e9; for (let x = -380; x <= 380; x += 4) for (let z = -380; z <= 380; z += 4) { if (D.H(x, z) < D.water + 1) continue; n++; const e = 1.5, gx = (D.H(x + e, z) - D.H(x - e, z)) / (2 * e), gz = (D.H(x, z + e) - D.H(x, z - e)) / (2 * e), sl = Math.hypot(gx, gz); if (sl < .15) flat++; else if (sl > .8) cliff++; }
          o.flat = +(flat / n).toFixed(2); o.cliff = +(cliff / n).toFixed(2);
          // no spikes: around the highest point the ground is flat (a mesa top)
          let hx = 0, hz = 0, hh = -1e9; for (let x = -380; x <= 380; x += 6) for (let z = -380; z <= 380; z += 6) { const h = D.H(x, z); if (h > hh) { hh = h; hx = x; hz = z; } }
          let rim = 1e9; for (let a = 0; a < 6.28; a += .5) rim = Math.min(rim, D.H(hx + Math.cos(a) * 12, hz + Math.sin(a) * 12)); o.topDrop12m = +(hh - rim).toFixed(1);
          for (let i = 0; i < 300; i++) D.updateAnimals(1 / 30); o.moving = D.beasts.filter(A => !A.wings && A.speed > .1).length;
          D.set.env = 'climate'; return o; }""")
        if SHOTS:
            for name, js in [("badlands_view", "D.camera.position.set(D.P.x, D.H(D.P.x, D.P.z) + 40, D.P.z); D.camera.rotation.set(-.22, .6, 0, 'YXZ');"),
                             ("badlands_ground", "D.camera.position.set(D.P.x, D.H(D.P.x, D.P.z) + 1.7, D.P.z); D.camera.rotation.set(-.03, 2.2, 0, 'YXZ');")]:
                img = await pg.evaluate("""(js) => { D.set.env = 'badlands'; D.setSeed(9); D.setVR(false); D.setMode('hike'); D.set.size = 'medium'; D.set.lat = 38; D.set.hour = 10; D.generate(); D.state = 'play'; D.camera.fov = 65; D.camera.updateProjectionMatrix();
                  eval(js); D.camera.updateMatrixWorld(); D.cullTiles && D.cullTiles(); D.renderer.render(D.scene, D.camera); D.set.env = 'climate'; return D.renderer.domElement.toDataURL('image/jpeg', .85); }""", js)
                open(os.path.join(SHOTS, name + ".jpg"), "wb").write(base64.b64decode(img.split(",")[1]))
        print(json.dumps(out))
        R, M = out["roll"], out["map"]
        ok = "badlands" not in R["25"] and set(R["32"]) == {"desert", "badlands", "temperate"} and 15 < R["32"]["badlands"] < 70 and "badlands" in R["40"] and "badlands" not in R["50"] \
             and R["note40"] == "Forest or badlands or desert: each map picks" and M["env"] == "badlands" and not M["missing"] and not M["foreign"] and M["flat"] > .3 and M["cliff"] > .05 and M["topDrop12m"] < 6 and M["moving"] > 5
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
