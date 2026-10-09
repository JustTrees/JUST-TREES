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
          const run = (mode) => { D.setMode(mode); D.set.size = 'small'; D.set.weather = 'clear'; D.set.lat = 45; D.generate(); D.state = 'play';
            const T = D.THREE, V = D.vr; V.on = true; V.yaw = 0; V.cl = null; V.goodX = undefined; V.ox = D.P.x; V.oz = D.P.z; V.oy = D.P.y;
            const L = { head: new T.Vector3(0, 1.7, 0), R: new T.Vector3(.25, 1.2, -.3), Lh: new T.Vector3(-.25, 1.2, -.3) };
            const pad = { R: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0 }, L: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0 } };
            const toW = v => v.clone().applyAxisAngle(new T.Vector3(0, 1, 0), V.yaw).add(new T.Vector3(V.ox, V.oy, V.oz));
            const toL = w => w.clone().sub(new T.Vector3(V.ox, V.oy, V.oz)).applyAxisAngle(new T.Vector3(0, 1, 0), -V.yaw);
            const q = new T.Quaternion();
            V.readInputs = () => ({ head: toW(L.head), headQ: q.clone(), hands: { right: Object.assign({ pos: toW(L.R), q: q.clone(), rayPos: toW(L.R), rayQ: q.clone() }, pad.R), left: Object.assign({ pos: toW(L.Lh), q: q.clone(), rayPos: toW(L.Lh), rayQ: q.clone() }, pad.L) } });
            const frames = n => { for (let i = 0; i < n; i++) { D.vrTick(1 / 60); if (!V.climbing) D.update(1 / 60); D.vrAfterMove(1 / 60); } };
            frames(30);
            let tree = null, bd = 1e9; for (const list of D.obstacles.values()) for (const o of list) if (o.t && o.t.hold && o.h > 7 && !o.t.tx) { const d = Math.hypot(o.x - D.P.x, o.z - D.P.z); if (d < bd) { bd = d; tree = o; } }
            V.ox += tree.x - D.P.x + tree.tr + .6; V.oz += tree.z - D.P.z; frames(20);
            return { T, V, L, pad, toW, toL, frames, tree };
          };
          let E = run('hike'); const { T, V, L, pad, toW, toL, frames, tree } = E;
          const base = D.H(tree.x, tree.z), t = tree.t;
          out.treeKind = t.kind; out.cards = t.hold.cards.length;
          // trunk taper: near the top, the old fat cylinder radius is no longer "inside"
          const hi = base + tree.h * .8;
          out.trunkLowInside = D.climbableAt(new T.Vector3(tree.x + tree.tr * .7, base + 1.3, tree.z))?.kind || null;
          // sample the old crown ellipsoid: how much of it is actually holdable now
          let oldIn = 0, nowIn = 0, s = 1;
          const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647;
          for (let i = 0; i < 3000; i++) { const a = rnd() * 6.28, r = Math.sqrt(rnd()) * tree.r * .85, y = base + tree.h * (.3 + rnd() * .72);
            const p = new T.Vector3(tree.x + Math.cos(a) * r, y, tree.z + Math.sin(a) * r); oldIn++; if (D.climbableAt(p)) nowIn++; }
          out.oldCrownHoldablePct = +(100 * nowIn / oldIn).toFixed(1);
          // grab the trunk and pull up
          L.R.copy(toL(new T.Vector3(tree.x + tree.tr * .6, D.P.y + 1.3, tree.z))); frames(2);
          out.handGlowsInside = D.vrHandsObj.R.ghostParts[0].visible;
          pad.R.grip = 1; frames(2); out.grabbed = V.cl.hold;
          const y0 = D.P.y; for (let i = 0; i < 30; i++) { L.R.y -= .5 / 30; frames(1); } out.pulledUpBy = +(D.P.y - y0).toFixed(2);
          pad.R.grip = 0; for (let i = 0; i < 300 && !D.P.onGround; i++) frames(1);
          L.R.set(.25, 1.2, -.3); frames(2); out.handGlowOutside = D.vrHandsObj.R.ghostParts[0].visible;
          // head collision: walk your real head straight into the trunk
          frames(30); V.goodX = undefined; frames(2);
          const dir = new T.Vector3(tree.x - D.P.x, 0, tree.z - D.P.z).normalize();
          for (let i = 0; i < 90; i++) { L.head.add(toL(toW(new T.Vector3()).add(dir.clone().multiplyScalar(.02))).sub(toL(toW(new T.Vector3())))); frames(1); }
          out.headDistToTrunkCenter = +Math.hypot(D.P.x - tree.x, D.P.z - tree.z).toFixed(2); out.trunkR = +tree.tr.toFixed(2);
          // big limbs: hand inside one counts; falling onto it you land and stand
          let limb = null; for (const l of D.limbHold.values()) { for (const h of l) if (Math.hypot(h.x - D.P.x, h.z - D.P.z) < 60) { limb = h; break; } if (limb) break; }
          if (limb) {
            const sg = limb.lv.segs[3], lp = sg.a.clone().lerp(sg.b, .5), w = new T.Vector3(limb.x + (lp.x * limb.ca + lp.z * limb.sa) * limb.sc, limb.y + lp.y * limb.sc, limb.z + (-lp.x * limb.sa + lp.z * limb.ca) * limb.sc);
            out.limbHoldKind = D.climbableAt(w)?.kind; out.limbAbove30cm = D.climbableAt(w.clone().add(new T.Vector3(0, .3, 0)))?.kind || null;
            // drop onto it from 2 m above
            V.cl = { hold: null, anchor: new T.Vector3(), vel: new T.Vector3(), prevP: null, air: { vx: 0, vz: 0 }, was: {} };
            V.ox += w.x - D.P.x; V.oz += w.z - D.P.z; D.P.x = w.x; D.P.z = w.z; D.P.y = w.y + 2; D.P.vy = 0; D.P.onGround = false; V.goodX = undefined;
            for (let i = 0; i < 200 && !D.P.onGround; i++) frames(1);
            out.landedOnLimb = +(D.P.y - w.y).toFixed(2) > -0.1 && D.P.y > D.groundAt(D.P.x, D.P.z) + 1.5; out.limbStandY = +(D.P.y - D.groundAt(D.P.x, D.P.z)).toFixed(2);
            frames(30); out.stillOnLimbAfter30 = D.P.y > D.groundAt(D.P.x, D.P.z) + 1.5;
          }
          // hunting: scope and binocular zoom flags
          E = run('hunt'); const V2 = E.V;
          E.L.head.set(0, 1.7, 0); E.L.R.set(.03, 1.58, -.12); E.L.Lh.set(-.02, 1.55, -.55); E.pad.L.grip = 1; E.frames(20);
          // put the eyepiece at the eye: the gun's eye point should sit right at the head
          const G = V2.gun; const eyeW = G.localToWorld(new T.Vector3(0, .082, .215)); const headW = E.toW(E.L.head);
          E.L.R.add(E.toL(headW).sub(E.toL(eyeW)).add(new T.Vector3(0, 0, -.03))); E.frames(30);
          out.scoped = V2.scoped; out.zoomK = +V2.zoomK.toFixed(1);
          E.pad.R.sy = -1; E.frames(2); E.pad.R.sy = 0; E.frames(2); out.zoomK2 = +V2.zoomK.toFixed(1);
          E.L.R.set(.25, 1.2, -.3); E.frames(10); out.unscopedK = V2.zoomK;
          // overlay shader compiles and draws
          const ov = D.zoomOverlay(); ov.visible = true; ov.material.uniforms.uK.value = 4; D.renderer.render(D.scene, D.camera); ov.visible = false; E.L.R.add(new T.Vector3()); V2.scoped = true; V2.zoomK = 4; D.vrZoomRender(); out.zoomRenderRan = true;
          return out; }""")
        print(json.dumps(r, indent=0)); print("errors:", errs or "none"); await b.close()
asyncio.run(main())
