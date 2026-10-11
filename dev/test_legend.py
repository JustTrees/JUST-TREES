"""Bigfoot: one shot. A shot nearby makes him wait for the bullet, then sprint off (arms pumping) and vanish for the rest of the map; a hit before that still counts."""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 200})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = {};
          D.setMode('hunt'); D.set.size = 'large'; D.set.weather = 'clear'; D.set.lat = 42; D.generate(); D.state = 'play';
          const B = D.beasts.find(A => A.kind === 'bigfoot'); out.found = !!B; if (!B) return out;
          // stand 300 m away and shoot (somewhere else)
          const a = Math.atan2(B.x, B.z); D.P.x = B.x - 300 * Math.sin(a + .3); D.P.z = B.z - 300 * Math.cos(a + .3);
          D.camera.position.set(D.P.x, B.y + 1.6, D.P.z); D.camera.lookAt(D.P.x + 1, B.y + 1.6, D.P.z); D.camera.updateMatrixWorld();
          D.scatterBeasts(D.camera.position); out.waitsFor = +B.boltIn.toFixed(2);
          const x0 = B.x, z0 = B.z; for (let i = 0; i < 12; i++) D.updateAnimals(1 / 30); out.movedWhileBulletFlies = +Math.hypot(B.x - x0, B.z - z0).toFixed(2);
          let maxSpeed = 0, elbow = 0, lean = 0, goneAt = null;
          for (let i = 0; i < 600; i++) { D.camera.position.set(B.x + 25, B.y + 2, B.z); D.updateAnimals(1 / 30); maxSpeed = Math.max(maxSpeed, B.speed); if (B.bolting && !B.gone) { elbow = B.arms[0].userData.knee.rotation.x; lean = Math.max(lean, B.body.rotation.x); } if (B.gone && goneAt === null) goneAt = +(i / 30).toFixed(1); }
          out.bolted = !!B.bolting; out.maxSpeed = +maxSpeed.toFixed(1); out.elbow = +elbow.toFixed(2); out.lean = +lean.toFixed(2); out.goneAfterS = goneAt; out.visible = B.root.visible;
          // can't be shot once gone, and a second shot doesn't bring him back
          D.scatterBeasts(D.camera.position); for (let i = 0; i < 60; i++) D.updateAnimals(1 / 30); out.stillGone = B.gone && !B.root.visible;
          // a fresh map: he's back (and a hit while he waits for the bullet still counts)
          D.generate(); const B2 = D.beasts.find(A => A.kind === 'bigfoot'); out.backOnNewMap = !!B2 && !B2.gone;
          return out; }""")
        print(json.dumps(r))
        ok = r.get("found") and r["waitsFor"] >= .6 and r["movedWhileBulletFlies"] < 1.5 and r["bolted"] and r["maxSpeed"] > 8 and r["elbow"] < -1 and r["goneAfterS"] and not r["visible"] and r["stillGone"] and r["backOnNewMap"]
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
