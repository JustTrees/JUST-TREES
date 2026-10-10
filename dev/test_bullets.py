"""VR bullets (1.37): even fire rate, no recoil, bullets fly at the gun's speed and drop, hit lands when the bullet arrives.
Usage: python3 dev/make_debug.py index.html /tmp/dbg.html && python3 dev/test_bullets.py /tmp/dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        pg.on("console", lambda m: errs.append("CON " + m.text) if m.type == "error" else None)
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); const out = {};
          D.setVR(true); D.setMode('hunt'); D.set.size = 'small'; D.set.weather = 'clear'; D.set.lat = 45; D.generate(); D.state = 'play';
          const T = D.THREE, V = D.vr; V.on = true; V.yaw = 0; V.cl = null; V.goodX = undefined; V.ox = D.P.x; V.oz = D.P.z; V.oy = D.P.y;
          const L = { head: new T.Vector3(0, 1.7, 0), R: new T.Vector3(.2, 1.35, -.35), Lh: new T.Vector3(-.25, 1.2, -.3) };
          const pad = { R: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 }, L: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 } };
          const toW = v => v.clone().applyAxisAngle(new T.Vector3(0, 1, 0), V.yaw).add(new T.Vector3(V.ox, V.oy, V.oz));
          const qs = { R: new T.Quaternion().setFromAxisAngle(new T.Vector3(1,0,0), .3), L: new T.Quaternion(), head: new T.Quaternion() };
          V.readInputs = () => ({ head: toW(L.head), headQ: qs.head.clone(), hands: { right: Object.assign({ pos: toW(L.R), q: qs.R.clone(), rayPos: toW(L.R), rayQ: qs.R.clone() }, pad.R), left: Object.assign({ pos: toW(L.Lh), q: qs.L.clone(), rayPos: toW(L.Lh), rayQ: qs.L.clone() }, pad.L) } });
          const frame = dt => { D.vrTick(dt); if (!V.climbing) D.update(dt); D.vrAfterMove(dt); D.updateGun(dt); };
          for (let i = 0; i < 30; i++) frame(1 / 60);
          // assault rifle held down for 2 s with uneven frame times
          V.weapon = 'ar'; V.gunInit = false; for (let i = 0; i < 20; i++) frame(1 / 60);
          D.arms.ar.mag = 30; D.arms.ar.phase = 0;
          const seen = new Set(D.tracers), times = []; let t = 0, kickMax = 0; pad.R.trig = 1;
          for (let i = 0; i < 400 && t < 2.0; i++) { const dt = [1/90, 1/72, 1/45, 1/60, 1/80][i % 5]; frame(dt); t += dt; kickMax = Math.max(kickMax, V.kick);
            for (const b of D.tracers) if (!seen.has(b)) { seen.add(b); times.push(t - (b.age || 0)); } }
          pad.R.trig = 0; frame(1/60);
          const gaps = times.slice(1).map((x, i) => x - times[i]);
          out.arShotsIn2s = times.length; out.gapMin = +Math.min(...gaps).toFixed(3); out.gapMax = +Math.max(...gaps).toFixed(3); out.kickMax = kickMax;
          // a bullet's flight: 0.25 s after leaving the barrel, level shot from high up
          const o = new T.Vector3(0, D.water + 400, 0), B = D.makeBullet(o, new T.Vector3(715, 0, 0), { reach: 2400 });
          for (let i = 0; i < 15; i++) D.updateGun(1 / 60); out.stillFlying = B.live;
          out.flewM = +(B.p.x - o.x).toFixed(1); out.droppedM = +(o.y - B.p.y).toFixed(2);
          // an animal 150 m below: not hit at once, hit when the bullet gets there
          const A = D.beasts.find(a => !a.dead && a.kind !== 'bird');
          if (A) { A.root.updateMatrixWorld(); const h = A.hit[0], c = new T.Vector3(h[0], h[1], h[2]).applyMatrix4(h[4] ? A.head.matrixWorld : A.root.matrixWorld);
            const from = c.clone().add(new T.Vector3(0, 150, 0)); D.makeBullet(from, new T.Vector3(0, -715, 0), { reach: 900 });
            D.updateGun(1/60); out.animalDeadAfter1Frame = A.dead; let k = 0; while (!A.dead && k < 60) { D.updateGun(1/60); k++; } out.animalHitAfterSec = +((k + 1) / 60).toFixed(2); out.animalDead = A.dead; }
          return out; }""")
        print(json.dumps(r)); print("errors:", errs[:5] or "none")
        await b.close()
asyncio.run(main())
