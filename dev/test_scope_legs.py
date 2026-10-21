"""1.81: far animals (over 220 m) skip drawing their legs, except when you look through a scope or binoculars: the VR scope and VR binoculars count too
(before 1.81 only the PC scope did, so in the headset far animals had no legs when zoomed)."""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 200})).new_page()
        await pg.goto('file://' + os.path.abspath(sys.argv[1])); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.setSeed(5); D.setVR(true); D.setMode('hunt'); D.set.dino = false; D.set.env = 'climate'; D.set.size = 'large'; D.set.lat = 42; D.generate(); D.state = 'play';
          const A = D.beasts.find(a => a.legs && a.legs.length && !a.wings); D.camera.position.set(A.x + 300, A.y + 2, A.z); D.camera.updateMatrixWorld();
          const out = {}; D.vr.on = true; D.vr.scoped = false; D.vr.binos = false; D.updateAnimals(1/30); out.plain = A.legs[0].visible;
          D.vr.scoped = true; D.updateAnimals(1/30); out.scope = A.legs[0].visible; D.vr.scoped = false; D.vr.binos = true; D.updateAnimals(1/30); out.binos = A.legs[0].visible; D.vr.binos = false; D.vr.on = false; return out; }""")
        print(json.dumps(r)); ok = not r['plain'] and r['scope'] and r['binos']; print('PASS' if ok else 'FAIL'); await b.close()
        if not ok: sys.exit(1)
asyncio.run(main())
