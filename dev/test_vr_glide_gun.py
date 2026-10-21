import os, sys
TARGET = 'file://' + os.path.abspath(sys.argv[1])
import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader","--enable-webgl","--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width":640,"height":400})).new_page(); errs=[]
        pg.on("pageerror", lambda e: errs.append("PE "+str(e)))
        pg.on("console", lambda m: errs.append("CON "+m.text) if m.type=="error" else None)
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = {};
          const run = (mode, size) => { D.setVR(true); D.setMode(mode); D.set.size = size || 'small'; D.set.weather = 'clear'; D.set.lat = 45; D.generate(); D.state = 'play';
            const T = D.THREE, V = D.vr; V.on = true; V.yaw = 0; V.cl = null; V.goodX = undefined; V.ox = D.P.x; V.oz = D.P.z; V.oy = D.P.y;
            const L = { head: new T.Vector3(0, 1.7, 0), R: new T.Vector3(.25, 1.2, -.3), Lh: new T.Vector3(-.25, 1.2, -.3) };
            const pad = { R: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 }, L: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 } };
            const toW = v => v.clone().applyAxisAngle(new T.Vector3(0, 1, 0), V.yaw).add(new T.Vector3(V.ox, V.oy, V.oz));
            const toL = w => w.clone().sub(new T.Vector3(V.ox, V.oy, V.oz)).applyAxisAngle(new T.Vector3(0, 1, 0), -V.yaw);
            const qs = { R: new T.Quaternion(), L: new T.Quaternion(), head: new T.Quaternion() };
            V.readInputs = () => ({ head: toW(L.head), headQ: qs.head.clone(), hands: { right: Object.assign({ pos: toW(L.R), q: qs.R.clone(), rayPos: toW(L.R), rayQ: qs.R.clone() }, pad.R), left: Object.assign({ pos: toW(L.Lh), q: qs.L.clone(), rayPos: toW(L.Lh), rayQ: qs.L.clone() }, pad.L) } });
            const frames = n => { for (let i = 0; i < n; i++) { D.vrTick(1 / 60); if (!V.climbing) D.update(1 / 60); D.vrAfterMove(1 / 60); } };
            frames(30);
            return { T, V, L, pad, qs, toW, toL, frames };
          };
          let E = run('hike'); const { T, V, L, pad, qs, toW, toL, frames } = E;
          out.vrFogFar = Math.round(D.camera ? 0 : 0);
          // sprint: click the walking stick
          pad.L.sy = -1; frames(30); let p0 = [D.P.x, D.P.z]; frames(60); out.walkSpeed = +Math.hypot(D.P.x - p0[0], D.P.z - p0[1]).toFixed(2);
          pad.L.stickBtn = 1; frames(1); pad.L.stickBtn = 0; frames(10); p0 = [D.P.x, D.P.z]; frames(60); out.sprintSpeed = +Math.hypot(D.P.x - p0[0], D.P.z - p0[1]).toFixed(2);
          frames(300); p0 = [D.P.x, D.P.z]; frames(60); out.after6s = +Math.hypot(D.P.x - p0[0], D.P.z - p0[1]).toFixed(2); pad.L.sy = 0; frames(5);
          // glide direction: arms spread, head looking left, hands pointing forward (-z): fly forward, not where you look
          D.P.y += 30; D.P.onGround = false; V.oy = D.P.y;
          qs.head.setFromAxisAngle(new T.Vector3(0, 1, 0), Math.PI / 2);
          L.R.set(.75, 1.6, -.1); L.Lh.set(-.75, 1.6, -.1); frames(3); p0 = [D.P.x, D.P.z]; frames(60);
          out.glideMove = [+(D.P.x - p0[0]).toFixed(2), +(D.P.z - p0[1]).toFixed(2)]; out.gliding = D.P.gliding;
          // turn the arm line 90 degrees (right hand in front, left behind) with hands pointing right: fly right
          L.R.set(.1, 1.6, -.75); L.Lh.set(-.1, 1.6, .75); qs.R.setFromAxisAngle(new T.Vector3(0, 1, 0), -Math.PI / 2); qs.L.copy(qs.R);
          frames(3); p0 = [D.P.x, D.P.z]; frames(60); out.glideMoveTurned = [+(D.P.x - p0[0]).toFixed(2), +(D.P.z - p0[1]).toFixed(2)];
          qs.R.identity(); qs.L.identity(); qs.head.identity(); L.R.set(.25, 1.2, -.3); L.Lh.set(-.25, 1.2, -.3); for (let i = 0; i < 400 && !D.P.onGround; i++) frames(1);
          // LOD: near tiles full detail, far ones simple
          D.cullTiles(); let hi = 0, lo = 0; for (const t of D.tiles) if (t.hi && t.group.visible) { if (t.hi.visible) hi++; else lo++; } out.tilesHiLo = [hi, lo];
          // climbing face block: hang on a trunk and pull yourself into it
          let tree = null, bd = 1e9; for (const list of D.obstacles.values()) for (const o of list) if (o.t && o.t.hold && o.h > 7 && !o.t.tx) { const d = Math.hypot(o.x - D.P.x, o.z - D.P.z); if (d < bd) { bd = d; tree = o; } }
          V.ox += tree.x - D.P.x + tree.tr + .7; V.oz += tree.z - D.P.z; V.goodX = undefined; frames(10);
          const dir = new T.Vector3(tree.x - D.P.x, 0, tree.z - D.P.z).normalize();
          L.R.copy(toL(new T.Vector3(tree.x, D.P.y + 1.3, tree.z).addScaledVector(dir, -tree.tr * .3))); frames(2); pad.R.grip = 1; frames(2); out.grabbed = V.cl.hold;
          let minD = 9; for (let i = 0; i < 40; i++) { L.R.addScaledVector(toL(toW(new T.Vector3()).add(dir)).sub(toL(toW(new T.Vector3()))), -.02); L.R.y -= .01; frames(1); minD = Math.min(minD, Math.hypot(D.P.x - tree.x, D.P.z - tree.z)); }
          out.climbPullMinHeadDist = +minD.toFixed(2); out.trunkR = +tree.tr.toFixed(2); out.stillHolding = V.cl.hold; pad.R.grip = 0; for (let i = 0; i < 300 && !D.P.onGround; i++) frames(1);
          // gun steadiness: hunting, shake the hand 3 mm / 0.6 degrees at 8 Hz
          E = run('hunt'); const V2 = E.V; E.frames(20);
          let maxDev = 0, maxIn = 0;
          for (let i = 0; i < 240; i++) { const s = Math.sin(i / 60 * 2 * Math.PI * 8); E.qs.R.setFromAxisAngle(new T.Vector3(1, 0, 0), s * .0105); E.frames(1);
            if (i > 60) { maxIn = Math.max(maxIn, Math.abs(s * .0105)); const g = V2.gq; maxDev = Math.max(maxDev, 2 * Math.acos(Math.min(1, Math.abs(g.w)))); } }
          out.shakeInDeg = +(maxIn * 57.3).toFixed(2); out.gunShakeOutDeg = +(maxDev * 57.3).toFixed(2);
          // deliberate swing: 40 degrees, how long to catch up within 2 degrees
          E.qs.R.setFromAxisAngle(new T.Vector3(0, 1, 0), .7); let t = 0; for (; t < 120; t++) { E.frames(1); if (2 * Math.acos(Math.min(1, Math.abs(V2.gq.dot(E.qs.R)))) < .035) break; } out.swingCatchUpMs = Math.round(t * 1000 / 60);
          // fog distance in VR
          out.fogFar = Math.round(D.scene.fog.far);
          return out; }""")
        print(json.dumps(r, indent=0)); print("errors:", errs or "none"); await b.close()
asyncio.run(main())
