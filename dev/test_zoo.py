"""Every biome spawns its animals (all kinds show up, none broken); then a lineup screenshot of every kind.
Usage: python3 dev/test_zoo.py debug.html [shot_dir]"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1]); SHOTS = sys.argv[2] if len(sys.argv) > 2 and os.path.isdir(sys.argv[2]) else None
import base64
def save(name, url): open(os.path.join(SHOTS, name), 'wb').write(base64.b64decode(url.split(',', 1)[1]))
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 1100, "height": 520})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = {};
          for (const [name, lat] of [['tropical', 10], ['temperate', 42], ['boreal', 56], ['tundra', 67], ['polar', 80]]) {
            D.setMode('hunt'); D.set.size = 'medium'; D.set.weather = 'clear'; D.set.lat = lat; D.set.month = 6; D.set.rough = .6; D.generate(); D.state = 'play';
            const want = D.NATIVE[name].map(k => k[0]).filter(k => !D.LEGEND[k]), count = {};
            for (const A of D.beasts) count[A.kind] = (count[A.kind] || 0) + 1;
            for (let i = 0; i < 600; i++) D.updateAnimals(1 / 30);
            const bad = D.beasts.filter(A => !isFinite(A.x + A.y + A.z)).map(A => A.kind);
            const moved = D.beasts.filter(A => !A.wings && A.kind !== 'monkey' && A.speed > .05).length;
            out[name] = { total: D.beasts.length, missing: want.filter(k => !count[k]), count, bad, walking: moved };
          }
          return out; }""")
        print(json.dumps({k: {**v, 'count': None} for k, v in r.items()}))
        if SHOTS:
            for group, kinds in [("hot", ["elephant", "giraffe", "zebra", "rhino", "lion", "crocodile"]), ("forest", ["horse", "elk", "moose", "boar", "goat", "turkey", "coyote", "fox"]),
                                 ("cold", ["caribou", "muskox", "arcticfox", "bigfoot", "yeti"])]:
                img = await pg.evaluate("""(kinds) => { D.set.lat = 42; D.set.weather = 'clear'; D.generate(); D.state = 'play';
                  for (const A of D.beasts.slice()) A.root.visible = false; D.beasts.length = 0;
                  // a flat open spot
                  let best = null; for (let k = 0; k < 4000; k++) { const x = (Math.random() - .5) * 400, z = (Math.random() - .5) * 400; let ok = D.okSpot(x, z);
                    for (let i = -14; i <= 14 && ok; i += 3.5) ok = D.okSpot(x + i, z) && D.okSpot(x + i, z + 6) && Math.abs(D.H(x + i, z) - D.H(x, z)) < .6; if (ok) { best = [x, z]; break; } }
                  const [x0, z0] = best || [0, 0], n = kinds.length, gap = 26 / n;
                  kinds.forEach((k, i) => { const A = D.addGround(k, x0 - 13 + gap * (i + .5), z0); A.yaw = Math.PI / 2; A.mode = 'idle'; A.timer = 999; });
                  D.updateAnimals(0); D.updateAnimals(0);
                  const y = D.H(x0, z0); D.camera.position.set(x0, y + 2.2, z0 + 15); D.camera.lookAt(x0, y + 1.2, z0); D.camera.fov = 60; D.camera.aspect = 1100 / 520; D.camera.updateProjectionMatrix();
                  D.renderer.setSize(1100, 520, false); D.renderer.render(D.scene, D.camera); return D.renderer.domElement.toDataURL('image/jpeg', .88); }""", kinds)
                save("zoo_" + group + ".jpg", img)
            img = await pg.evaluate("""() => { const A = [], c = D.camera.position; for (const k of ['parrot', 'eagle', 'owl', 'bird']) { D.spawnKind(k, k === 'parrot' ? [3, 3] : null, 0); }
              const fl = D.beasts.filter(b => b.wings); fl.forEach((b, i) => { b.root.position.set(c.x - 6 + i * 2.2, c.y, c.z - 9); b.root.rotation.set(0, Math.PI / 2, 0); b.root.visible = true; });
              D.renderer.render(D.scene, D.camera); return D.renderer.domElement.toDataURL('image/jpeg', .88); }""")
            save("zoo_birds.jpg", img)
        print(errs or "ok"); await b.close()
asyncio.run(main())
