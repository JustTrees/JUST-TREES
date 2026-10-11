"""Bigfoot: one on every map, hidden (and unhittable) until you hold the red sniper; other shots never spook him;
a bullet passing within 15 m of him is your one shot: he waits for it, then sprints off (arms pumping), can't be hit, and is gone for the map."""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 200})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = {}, T = D.THREE;
          D.setVR(true); D.setMode('hunt'); D.set.weather = 'clear';
          out.everyMap = [[42, 'small'], [10, 'medium'], [56, 'large'], [70, 'medium']].map(([lat, size]) => { D.set.lat = lat; D.set.size = size; D.generate(); return D.beasts.filter(A => A.kind === 'bigfoot' || A.kind === 'yeti').length; });
          D.set.lat = 42; D.set.size = 'medium'; D.generate(); D.state = 'play';
          const B = D.beasts.find(A => A.kind === 'bigfoot'); out.found = !!B; if (!B) return out;
          const a = Math.atan2(B.x, B.z); D.P.x = B.x - 250 * Math.sin(a + .3); D.P.z = B.z - 250 * Math.cos(a + .3);
          const eye = new T.Vector3(D.P.x, B.y + 60, D.P.z); let at, dir; const aim = () => { at = new T.Vector3(B.x, B.y + 1.2, B.z); dir = at.clone().sub(eye).normalize(); }; aim();
          const step = n => { for (let i = 0; i < n; i++) { D.camera.position.set(B.x + 25, B.y + 2, B.z); D.updateAnimals(1 / 30); } };
          // before the red sniper: hidden, can't be hit, shots do nothing
          D.setLoot({ pistol: 1 }); step(3); aim(); out.hiddenBefore = !B.root.visible && !D.legendSeen();
          out.unhittableBefore = D.animalRay(eye, dir, .5)[1] !== B;
          D.legendShot(eye, dir, 3200, 850); D.scatterBeasts(eye); step(30); out.noReactBefore = !B.bolting && !(B.boltIn > 0);
          // with the red sniper
          D.setLoot({ pistol: 1, hunt: 5 }); step(3); out.seenAfter = B.root.visible && D.legendSeen();
          // a shot at another animal far off his line: nothing
          const off = new T.Vector3(Math.cos(a + 1.2), 0, Math.sin(a + 1.2)).normalize(); D.scatterBeasts(eye); D.legendShot(eye, off, 3200, 850); step(30); out.ignoresOtherShots = !B.bolting && !(B.boltIn > 0);
          // a near miss: 6 m to the side
          aim(); const side = new T.Vector3(-dir.z, 0, dir.x).normalize(), miss = at.clone().addScaledVector(side, 6).sub(eye).normalize();
          out.hitWhileWaiting = D.animalRay(eye, dir, .5)[1] === B;
          D.legendShot(eye, miss, 3200, 850); out.waitsFor = +(B.boltIn || 0).toFixed(2);
          step(Math.ceil(B.boltIn * 30) + 3); out.bolted = !!B.bolting; aim(); out.unhittableRunning = D.animalRay(eye, dir, .5)[1] !== B;
          let maxSpeed = 0, elbow = 0, goneAt = null; for (let i = 0; i < 600; i++) { step(1); maxSpeed = Math.max(maxSpeed, B.speed); if (B.bolting && !B.gone) elbow = B.arms[0].userData.knee.rotation.x; if (B.gone && goneAt === null) goneAt = +(i / 30).toFixed(1); }
          out.maxSpeed = +maxSpeed.toFixed(1); out.elbow = +elbow.toFixed(2); out.goneAfterS = goneAt; out.stillGone = B.gone && !B.root.visible;
          return out; }""")
        print(json.dumps(r))
        ok = r.get("found") and all(n == 1 for n in r["everyMap"]) and r["hiddenBefore"] and r["unhittableBefore"] and r["noReactBefore"] and r["seenAfter"] and r["ignoresOtherShots"] \
             and r["hitWhileWaiting"] and .2 < r["waitsFor"] < 1 and r["bolted"] and r["unhittableRunning"] and r["maxSpeed"] > 8 and r["elbow"] < -1 and r["goneAfterS"] and r["stillGone"]
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
