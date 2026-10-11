"""Bigfoot/Yeti: one on every Large, XL and XXL map (none smaller), hidden (and unhittable) until you hold the red sniper; other shots never spook him;
a bullet passing within 15 m of him is your one shot: he waits for it, then sprints off (arms pumping), can't be hit, and is gone for the map.
Picking up the red sniper puts "There's a Bigfoot in these woods" in front of you."""
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
          out.everyMap = [[42, 'small'], [10, 'medium'], [42, 'large'], [10, 'large'], [56, 'xl'], [70, 'large']].map(([lat, size]) => { D.set.lat = lat; D.set.size = size; D.generate(); return D.beasts.filter(A => A.kind === 'bigfoot' || A.kind === 'yeti').length; });
          D.set.lat = 42; D.set.size = 'large'; D.generate(); D.state = 'play';
          const B = D.beasts.find(A => A.kind === 'bigfoot'); out.found = !!B; if (!B) return out;
          // find a spot ~250 m off with a clear line of fire (trees stop bullets, so a blocked shot rightly doesn't count)
          const tgt = new T.Vector3(B.x, B.y + 1.2, B.z), clear = (e, d) => { const h = D.castShotDbg(e, d, 3200); return !h || !h.p || h.p.distanceTo(e) > e.distanceTo(tgt) - 3; };
          const findEye = () => { tgt.set(B.x, B.y + 1.2, B.z); for (let k = 0; k < 64; k++) { const a = k * .39, up = 60 + (k >> 4) * 40; const e = new T.Vector3(B.x - 250 * Math.sin(a), B.y + up, B.z - 250 * Math.cos(a)); const d0 = tgt.clone().sub(e).normalize(), s0 = new T.Vector3(-d0.z, 0, d0.x).normalize(), m0 = tgt.clone().addScaledVector(s0, 6).sub(e).normalize(); if (clear(e, d0) && clear(e, m0)) return e; } return null; };
          let eye = findEye(); out.clearLine = !!eye; if (!eye) return out; D.P.x = eye.x; D.P.z = eye.z;
          let at, dir; const aim = () => { at = new T.Vector3(B.x, B.y + 1.2, B.z); dir = at.clone().sub(eye).normalize(); }; aim();
          const step = n => { for (let i = 0; i < n; i++) { D.camera.position.set(B.x + 25, B.y + 2, B.z); D.updateAnimals(1 / 30); } };
          // before the red sniper: hidden, can't be hit, shots do nothing
          D.setLoot({ pistol: 1 }); step(3); aim(); out.hiddenBefore = !B.root.visible && !D.legendSeen();
          out.unhittableBefore = D.animalRay(eye, dir, .5)[1] !== B;
          D.legendShot(eye, dir, 3200, 850); D.scatterBeasts(eye); step(30); out.noReactBefore = !B.bolting && !(B.boltIn > 0);
          // pick up the red sniper: the message shows, and he's there
          D.dropUse({ type: 'gun', kind: 'hunt', tier: 5, x: 0, y: 0, z: 0, id: 'gRed' }); out.banner = D.VBAN.m && D.VBAN.t > 5 ? D.VBAN.m.userData.cv.getContext('2d').getImageData(384, 62, 1, 1).data[3] > 0 : false; out.ownRed = D.vrOwn.hunt === 5; step(3); out.seenAfter = B.root.visible && D.legendSeen();
          // a shot at another animal far off his line: nothing
          aim(); const off = new T.Vector3(dir.x * Math.cos(1.2) - dir.z * Math.sin(1.2), 0, dir.x * Math.sin(1.2) + dir.z * Math.cos(1.2)).normalize(); D.scatterBeasts(eye); D.legendShot(eye, off, 3200, 850); step(30); out.ignoresOtherShots = !B.bolting && !(B.boltIn > 0);
          // a near miss: 6 m to the side (from a clear spot, he may have wandered)
          eye = findEye(); out.clearLine2 = !!eye; if (!eye) return out; aim(); const side = new T.Vector3(-dir.z, 0, dir.x).normalize(), miss = at.clone().addScaledVector(side, 6).sub(eye).normalize();
          out.hitWhileWaiting = D.animalRay(eye, dir, .5)[1] === B;
          D.legendShot(eye, miss, 3200, 850); out.waitsFor = +(B.boltIn || 0).toFixed(2);
          step(Math.ceil(B.boltIn * 30) + 3); out.bolted = !!B.bolting; aim(); out.unhittableRunning = D.animalRay(eye, dir, .5)[1] !== B;
          let maxSpeed = 0, elbow = 0, goneAt = null; for (let i = 0; i < 600; i++) { step(1); maxSpeed = Math.max(maxSpeed, B.speed); if (B.bolting && !B.gone) elbow = B.arms[0].userData.knee.rotation.x; if (B.gone && goneAt === null) goneAt = +(i / 30).toFixed(1); }
          out.maxSpeed = +maxSpeed.toFixed(1); out.elbow = +elbow.toFixed(2); out.goneAfterS = goneAt; out.stillGone = B.gone && !B.root.visible;
          return out; }""")
        print(json.dumps(r))
        ok = r.get("found") and r["everyMap"] == [0, 0, 1, 1, 1, 1] and r["hiddenBefore"] and r["unhittableBefore"] and r["noReactBefore"] and r["seenAfter"] and r["banner"] and r["ownRed"] and r["ignoresOtherShots"] \
             and r["hitWhileWaiting"] and .2 < r["waitsFor"] < 1 and r["bolted"] and r["unhittableRunning"] and r["maxSpeed"] > 8 and r["elbow"] < -1 and r["goneAfterS"] and r["stillGone"]
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
