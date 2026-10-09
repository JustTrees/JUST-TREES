import os, sys
TARGET = 'file://' + os.path.abspath(sys.argv[1])
import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader","--enable-webgl","--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width":640,"height":400})).new_page(); errs=[]
        pg.on("pageerror", lambda e: errs.append("PE "+str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = {};
          D.setVR(true); D.setMode('hunt'); D.set.size = 'medium'; D.set.weather = 'clear'; D.set.lat = 45; D.set.rough = .95; D.generate(); D.state = 'play';
          const T = D.THREE, V = D.vr; V.on = true; V.yaw = 0; V.cl = null; V.goodX = undefined; V.ox = D.P.x; V.oz = D.P.z; V.oy = D.P.y;
          const L = { head: new T.Vector3(0, 1.7, 0), R: new T.Vector3(.25, 1.2, -.3), Lh: new T.Vector3(-.25, 1.2, -.3) };
          const pad = { R: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 }, L: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 } };
          const toW = v => v.clone().applyAxisAngle(new T.Vector3(0, 1, 0), V.yaw).add(new T.Vector3(V.ox, V.oy, V.oz));
          const qs = { R: new T.Quaternion(), L: new T.Quaternion(), head: new T.Quaternion() };
          V.readInputs = () => ({ head: toW(L.head), headQ: qs.head.clone(), hands: { right: Object.assign({ pos: toW(L.R), q: qs.R.clone(), rayPos: toW(L.R), rayQ: qs.R.clone() }, pad.R), left: Object.assign({ pos: toW(L.Lh), q: qs.L.clone(), rayPos: toW(L.Lh), rayQ: qs.L.clone() }, pad.L) } });
          const frames = n => { for (let i = 0; i < n; i++) { D.vrTick(1 / 60); if (!V.climbing) D.update(1 / 60); D.vrAfterMove(1 / 60); } };
          frames(20);
          // walking speeds in VR
          pad.L.sy = -1; frames(30); let p0 = [D.P.x, D.P.z]; frames(60); out.walk = +Math.hypot(D.P.x - p0[0], D.P.z - p0[1]).toFixed(2);
          pad.L.stickBtn = 1; frames(1); pad.L.stickBtn = 0; frames(15); p0 = [D.P.x, D.P.z]; frames(60); out.sprint = +Math.hypot(D.P.x - p0[0], D.P.z - p0[1]).toFixed(2); pad.L.sy = 0; frames(400);
          // level scope: a gun rolled 50 degrees keeps the same aim but a level horizon
          const q = new T.Quaternion().setFromEuler(new T.Euler(-.2, .7, .87, 'YXZ')), lq = D.levelQ(q).clone();
          const f1 = new T.Vector3(0, 0, -1).applyQuaternion(q), f2 = new T.Vector3(0, 0, -1).applyQuaternion(lq), rgt = new T.Vector3(1, 0, 0).applyQuaternion(lq);
          out.scopeAimSame = f1.distanceTo(f2) < 1e-6; out.scopeRollDeg = +(Math.asin(Math.abs(rgt.y)) * 57.3).toFixed(2);
          // the VR bullet
          const G = V.gun; V.scoped = false; D.GUN.cool = 0; D.vrFire(); const t = D.tracers[D.tracers.length - 1]; D.updateGun(1 / 60);
          out.bulletMPerFrame = +t.d.toFixed(1); out.bulletWidth = +t.trail.scale.x.toFixed(3) || +t.head.scale.x.toFixed(3);
          // climbable rocks: find a tall boulder and reach into its face
          let rockPt = null;
          for (let i = 0; i < 20000 && !rockPt; i++) { const x = (Math.random() - .5) * 500, z = (Math.random() - .5) * 500, rk = D.rockTop(x, z), g = D.H(x, z); if (rk > g + 2.5) rockPt = [x, z, rk, g]; }
          if (rockPt) { const [x, z, rk, g] = rockPt; out.rockHeight = +(rk - g).toFixed(1);
            out.rockGrab = (D.climbableAt(new T.Vector3(x, g + 1.2, z)) || {}).kind;
            // head beside the rock (just outside its edge) is allowed; deep inside is not
            let edge = null; for (let a = 0; a < 6.28 && !edge; a += .2) for (let d = .3; d < 4; d += .1) { const ex = x + Math.cos(a) * d, ez = z + Math.sin(a) * d; if (D.rockTop(ex, ez) < D.H(ex, ez) + .3) { edge = [x + Math.cos(a) * (d + .15), z + Math.sin(a) * (d + .15)]; break; } }
            out.headAtRockFaceBlocked = edge ? D.headBlocked(edge[0], g + 1.4, edge[1]) : 'no edge';
            out.headInsideRockBlocked = D.headBlocked(x, g + 1.4, z); }
          // steep terrain: grab the face; skipping downhill; glide lift-off from the slope
          let st = null; for (let i = 0; i < 40000 && !st; i++) { const x = (Math.random() - .5) * 480, z = (Math.random() - .5) * 480; const ny = D.slopeNy(x, z); if (ny < .62 && ny > .45 && D.H(x, z) > 2 && D.rockAround(x, z, 3) < D.H(x, z)) st = [x, z]; }
          if (st) {
            const [x, z] = st, e = 1.5, gx = (D.H(x + e, z) - D.H(x - e, z)) / (2 * e), gz = (D.H(x, z + e) - D.H(x, z - e)) / (2 * e), gl = Math.hypot(gx, gz);
            const up = [gx / gl, gz / gl];                         // uphill direction
            out.slopeDeg = Math.round(Math.acos(D.slopeNy(x, z)) * 57.3);
            out.faceGrab = (D.climbableAt(new T.Vector3(x + up[0] * .25, D.H(x, z) + .05, z + up[1] * .25)) || {}).kind;
            // stand there and walk downhill: count the little airborne skips
            V.ox += x - D.P.x; V.oz += z - D.P.z; D.P.x = x; D.P.z = z; D.P.y = D.H(x, z); D.P.onGround = true; V.goodX = undefined;
            qs.head.setFromAxisAngle(new T.Vector3(0, 1, 0), Math.atan2(up[0], up[1]));   // facing downhill (-z forward rotated)
            frames(2); pad.L.sy = -1; let air = 0, flips = 0, was = true;
            for (let i = 0; i < 90; i++) { frames(1); if (!D.P.onGround) air++; if (D.P.onGround !== was) flips++; was = D.P.onGround; }
            pad.L.sy = 0; out.downhillAirFrames = air; out.downhillSkips = Math.round(flips / 2);
            // back on the slope, spread the arms: lift off into a glide
            D.P.x = x; D.P.z = z; D.P.y = D.H(x, z); D.P.onGround = true; V.ox += 0; frames(1);
            L.R.set(.75, 1.5, -.1); L.Lh.set(-.75, 1.5, -.1); qs.R.identity(); qs.L.identity(); frames(3);
            out.glideFromSlope = D.P.gliding;
          }
          return out; }""")
        print(json.dumps(r, indent=0)); print("errors:", errs or "none"); await b.close()
asyncio.run(main())
