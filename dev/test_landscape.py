"""Dramatic landscape (1.24): each feature type is made, sits inside the map, and does what it should (the crater holds a lake,
the mesa stands up, the canyon cuts down, the cliff steps up); Natural maps keep the same ground as before; renders a picture of each.
Usage: python3 dev/make_debug.py index.html /tmp/dbg.html && python3 dev/test_landscape.py /tmp/dbg.html [/tmp/land]"""
import os, sys, asyncio, json, base64
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1]); OUT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/land'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 900, "height": 560})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        pg.on("console", lambda m: errs.append("CON " + m.text) if m.type == "error" else None)
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = { types: {} };
          const gen = (sd, land, size, edges, lat) => { D.setSeed(sd); D.set.land = land; D.set.size = size || 'medium'; D.set.edges = edges || 'endless'; D.set.weather = 'clear'; D.set.lat = lat || 45; D.set.hour = 15; D.setMode('hike'); D.generate(); };
          // which seeds give which feature
          const seen = {};
          for (let sd = 1; sd < 60 && Object.keys(seen).length < 4; sd++) { gen(sd, 'dramatic'); const F = D.FEAT; if (F && !seen[F.type]) seen[F.type] = sd; }
          out.seeds = seen;
          for (const [type, sd] of Object.entries(seen)) {
            gen(sd, 'dramatic'); const F = D.FEAT, H = D.H, w = D.water, o = { name: F.name, R: Math.round(F.R) };
            const ring = k => { let a = 0; for (let i = 0; i < 16; i++) { const t = i / 16 * 6.283; a += H(F.x + Math.cos(t) * F.R * k, F.z + Math.sin(t) * F.R * k); } return a / 16; };
            if (type === 'crater') { o.centreBelowWater = +(w - H(F.x, F.z)).toFixed(1); let wet = 0; for (let i = 0; i < 200; i++) { const a = Math.random() * 6.283, d = Math.sqrt(Math.random()) * F.R * .55; if (H(F.x + Math.cos(a) * d, F.z + Math.sin(a) * d) < w) wet++; } o.lakePctOfInnerCrater = Math.round(wet / 2); o.rimAboveWater = +(ring(1) - w).toFixed(1); }
            if (type === 'mesa') { o.topAboveSurroundings = +(H(F.x, F.z) - ring(1.6)).toFixed(1); }
            if (type === 'canyon' || type === 'cliff') { let mx = -1e9, mn = 1e9; for (let i = -12; i <= 12; i++) for (let j = -12; j <= 12; j++) { const h = H(F.x + i * F.R / 8, F.z + j * F.R / 8); mx = Math.max(mx, h); mn = Math.min(mn, h); } o.reliefM = +(mx - mn).toFixed(1); }
            gen(sd, 'natural'); o.waterSameAsNatural = Math.abs(D.water - w) < 2.5; o.natWater = +D.water.toFixed(1); o.dramWater = +w.toFixed(1);
            out.types[type] = o;
          }
          // small and island maps too
          for (const [size, edges] of [['xs', 'endless'], ['small', 'island'], ['xxl', 'island']]) { let ok = 0; for (let sd = 1; sd < 9; sd++) { gen(sd, 'dramatic', size, edges); const F = D.FEAT; if (F && F.mask(F.x, F.z) > .9) ok++; } out[size + '_' + edges] = ok + '/8'; }
          // natural: the same ground as before (sample heights to compare with the old build)
          gen(1234, 'natural'); const hs = []; for (let i = 0; i < 10; i++) hs.push(+D.H(-200 + i * 40, 60 - i * 13).toFixed(3)); out.naturalHeights = hs; out.naturalFeat = D.FEAT;
          return out; }""")
        print(json.dumps(r, indent=0))
        for type, sd in r["seeds"].items():
            u = await pg.evaluate("""([sd]) => { D.setSeed(sd); D.set.land = 'dramatic'; D.set.size = 'medium'; D.set.edges = 'endless'; D.set.weather = 'clear'; D.set.lat = 45; D.set.hour = 15; D.setMode('hike'); D.generate();
              const T = D.THREE, F = D.FEAT, cam = new T.PerspectiveCamera(55, 900 / 560, .5, 3000), h = D.H(F.x, F.z);
              cam.position.set(F.x + F.R * 1.9, h + F.R * 1.5, F.z + F.R * 1.9); cam.lookAt(F.x, h, F.z); D.scene.fog.far = 3000;
              cam.updateMatrixWorld(); const oc = D.camera; D.camera.position.copy(cam.position); D.camera.quaternion.copy(cam.quaternion); D.camera.updateMatrixWorld(); D.cullTiles();
              D.renderer.setSize(900, 560, false); D.renderer.render(D.scene, cam); return D.renderer.domElement.toDataURL('image/jpeg', .85); }""", [sd])
            open(f"{OUT}_{type}.jpg", "wb").write(base64.b64decode(u.split(',')[1]))
        print("errors:", errs or "none"); await b.close()
asyncio.run(main())
