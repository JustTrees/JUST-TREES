"""2.08 recoil: the assault rifle and SMG climb with each shot (no scatter, same fire rate). Levels: 5 stars = 1 ... 1 star = 5,
one hand on the gun = 6; looking down the gun 15% less; it settles back once you stop. Sniper and pistol: none.
Usage: python3 dev/test_recoil.py dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = {};
          D.setVR(true); D.setMode('hunt'); D.set.size = 'small'; D.set.weather = 'clear'; D.set.lat = 45; D.generate(); D.allGuns(); D.state = 'play';
          const T = D.THREE, V = D.vr; V.on = true; V.yaw = 0; V.cl = null; V.goodX = undefined; V.ox = D.P.x; V.oz = D.P.z; V.oy = D.P.y;
          const L = { head: new T.Vector3(0, 1.7, 0), R: new T.Vector3(.2, 1.35, -.35), Lh: new T.Vector3(-.25, 1.2, -.3) };
          const pad = { R: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 }, L: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 } };
          const toW = v => v.clone().applyAxisAngle(new T.Vector3(0, 1, 0), V.yaw).add(new T.Vector3(V.ox, V.oy, V.oz));
          const toL = w => w.clone().sub(new T.Vector3(V.ox, V.oy, V.oz)).applyAxisAngle(new T.Vector3(0, 1, 0), -V.yaw);
          const qs = { R: new T.Quaternion(), L: new T.Quaternion(), head: new T.Quaternion() };
          V.readInputs = () => ({ head: toW(L.head), headQ: qs.head.clone(), hands: { right: Object.assign({ pos: toW(L.R), q: qs.R.clone(), rayPos: toW(L.R), rayQ: qs.R.clone() }, pad.R), left: Object.assign({ pos: toW(L.Lh), q: qs.L.clone(), rayPos: toW(L.Lh), rayQ: qs.L.clone() }, pad.L) } });
          const frames = n => { for (let i = 0; i < n; i++) { D.vrTick(1 / 60); if (!V.climbing) D.update(1 / 60); D.vrAfterMove(1 / 60); D.updateGun(1 / 60); } };
          const pitch = () => { const f = new T.Vector3(0, 0, -1).applyQuaternion(V.gun.quaternion); return Math.asin(f.y) * 180 / Math.PI; };
          const run = (kind, tier, two, ads) => {
            const own = { hunt: 1, ar: 1, smg: 1, pistol: 1 }; own[kind] = tier; D.setLoot(own); D.arms[kind].mag = 99; D.arms[kind].phase = 0;
            D.pickGun(kind); pad.R.trig = 0; pad.L.grip = 0; L.Lh.set(-.25, 1.2, -.3); L.head.set(0, 1.7, 0); L.R.set(.2, 1.35, -.35); frames(40);
            if (two) { const S = D.GUNSPOT[kind]; L.Lh.copy(toL(V.gun.localToWorld(new T.Vector3(...S.fore)))); pad.L.grip = 1; frames(20); }
            if (ads) { const S = D.GUNSPOT[kind]; const e = V.gun.localToWorld(new T.Vector3(...S.eye)), f = new T.Vector3(0, 0, -1).applyQuaternion(V.gun.quaternion); L.head.copy(toL(e.clone().addScaledVector(f, -.08))); frames(10); }
            V.climb = 0; frames(2); D.arms[kind].mag = 99; const hold0 = D.RECOIL.hold; D.RECOIL.hold = 0;   /* (2.49: per shot, without the pull-back while firing) */ const p0 = pitch(), t0 = D.tracers.length; let shots = 0;
            pad.R.trig = 1; for (let i = 0; i < 18; i++) { const n0 = D.arms[kind].mag; frames(1); shots += n0 - D.arms[kind].mag; }
            const climb = V.climb * 180 / Math.PI, p1 = pitch(); D.RECOIL.hold = hold0; pad.R.trig = 0; frames(30); const after = V.climb * 180 / Math.PI;
            return { shots, perShot: +(climb / Math.max(1, shots)).toFixed(3), climb: +climb.toFixed(2), gunUp: +(p1 - p0).toFixed(2), settled: +after.toFixed(2), two: V.two, ads: !!V.ads };
          };
          out.ar5two = run('ar', 5, true, false); out.ar1two = run('ar', 1, true, false); out.ar3two = run('ar', 3, true, false); out.ar1one = run('ar', 1, false, false); out.ar5one = run('ar', 5, false, false);
          out.ar1ads = run('ar', 1, true, true); out.smg2two = run('smg', 2, true, false);
          const pis = run('pistol', 1, false, false); out.pistol = pis;
          { const own = { hunt: 1, ar: 1, smg: 1, pistol: 1 }; D.setLoot(own); D.arms.ar.mag = 99; D.pickGun('ar'); frames(20); V.climb = 0; pad.R.trig = 1; for (let i = 0; i < 90; i++) { D.arms.ar.mag = 99; frames(1); } out.held1s = +(V.climb * 180 / Math.PI).toFixed(2); pad.R.trig = 0; frames(30); }   /* 2.49: a 1.5 s burst, one-handed 1-star: it pulls back while you fire */
          return out; }""")
        print(json.dumps(r)); E = lambda a, b: abs(a - b) < .02
        ok = (E(r["ar5two"]["perShot"], .25) and E(r["ar1two"]["perShot"], .5) and E(r["ar3two"]["perShot"], .36) and E(r["ar1one"]["perShot"], 1.6) and E(r["ar5one"]["perShot"], 1.6)
              and E(r["ar1ads"]["perShot"], .425) and r["ar1ads"]["ads"] and E(r["smg2two"]["perShot"], .42) and r["ar1two"]["two"] and not r["ar1one"]["two"]
              and r["ar1two"]["shots"] == r["ar1one"]["shots"] == r["ar1ads"]["shots"] and r["ar1one"]["gunUp"] > 3 and r["ar1one"]["settled"] < r["ar1one"]["climb"] * .05
              and r["pistol"]["climb"] == 0 and r["ar1one"]["climb"] <= 14.01 and r["held1s"] < 9 and not errs)
        print("errors", errs[:5]); print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
