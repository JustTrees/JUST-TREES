"""VR grenades (1.38): wheel slot, loot up to 10, arc preview, throw, explode where the ring showed, kills nearby animals, tap A back to gun.
Usage: python3 dev/make_debug.py index.html /tmp/dbg.html && python3 dev/test_nades.py /tmp/dbg.html [/tmp/nade.png]"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1]); SHOT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/nade.png'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 800, "height": 500})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        pg.on("console", lambda m: errs.append("CON " + m.text) if m.type == "error" else None)
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); const out = {};
          D.setVR(true); D.setMode('hunt'); D.set.size = 'small'; D.set.weather = 'clear'; D.set.lat = 45; D.set.hour = 13; D.generate(); D.state = 'play';
          const T = D.THREE, V = D.vr; V.on = true; V.yaw = 0; V.cl = null; V.goodX = undefined; V.ox = D.P.x; V.oz = D.P.z; V.oy = D.P.y;
          const L = { head: new T.Vector3(0, 1.7, 0), R: new T.Vector3(.2, 1.35, -.35), Lh: new T.Vector3(-.25, 1.2, -.3) };
          const pad = { R: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 }, L: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 } };
          const toW = v => v.clone().applyAxisAngle(new T.Vector3(0, 1, 0), V.yaw).add(new T.Vector3(V.ox, V.oy, V.oz));
          const qs = { R: new T.Quaternion(), L: new T.Quaternion(), head: new T.Quaternion() };
          V.readInputs = () => ({ head: toW(L.head), headQ: qs.head.clone(), hands: { right: Object.assign({ pos: toW(L.R), q: qs.R.clone(), rayPos: toW(L.R), rayQ: qs.R.clone() }, pad.R), left: Object.assign({ pos: toW(L.Lh), q: qs.L.clone(), rayPos: toW(L.Lh), rayQ: qs.L.clone() }, pad.L) } });
          const frames = n => { for (let i = 0; i < n; i++) { D.vrTick(1 / 60); if (!V.climbing) D.update(1 / 60); D.vrAfterMove(1 / 60); D.updateGun(1 / 60); } };
          frames(30);
          out.boxes = D.nadeLoot.length; out.startNades = V.nades;
          // walk onto a grenade box
          const go = c => { D.P.x = c.x; D.P.z = c.z; D.P.y = D.groundAt(c.x, c.z); V.ox = D.P.x; V.oz = D.P.z; V.oy = D.P.y; V.placeAt = true; frames(5); };
          go(D.nadeLoot[0]); out.afterBox = V.nades; out.boxGone = D.nadeLoot[0].got;
          V.nades = 10; go(D.nadeLoot[1]); out.fullStays10 = V.nades; out.fullLeavesBox = !D.nadeLoot[1].got;
          V.nades = 5; go(D.nadeLoot[0]); frames(2);
          // wheel: hold A, point up-left (the 5th slice), let go
          pad.R.a = 1; frames(3); qs.R.setFromEuler(new T.Euler(.14, .42, 0, 'YXZ')); frames(3); out.wheelSel = V.wh.sel; pad.R.a = 0; frames(2); qs.R.identity();
          out.nadeMode = V.nadeMode; out.gunHidden = !(V.gun && V.gun.visible);
          qs.R.setFromEuler(new T.Euler(.15, 0, 0, 'YXZ')); frames(3);
          const A = D.nadeArc; out.arcDots = A.dots.count; out.ringShown = A.land.visible; out.heldShown = A.held.visible;
          const ring = A.land.position.clone(), hand = toW(L.R); out.ringDistM = +Math.hypot(ring.x - hand.x, ring.z - hand.z).toFixed(1);
          // picture from the head
          D.camera.position.copy(toW(L.head)); D.camera.quaternion.setFromEuler(new T.Euler(-.12, 0, 0, 'YXZ')); D.camera.updateMatrixWorld(); D.renderer.render(D.scene, D.camera);
          window._shot = D.renderer.domElement.toDataURL('image/png'); const mid = toW(L.R).lerp(ring, .5); D.camera.position.copy(mid).add(new T.Vector3(22, 6, 0)); D.camera.lookAt(mid); D.camera.updateMatrixWorld(); D.renderer.render(D.scene, D.camera); window._shot2 = D.renderer.domElement.toDataURL('image/png'); A.dots.visible = true; out.dotScales = []; const mm = new T.Matrix4(), pp = new T.Vector3(), qq = new T.Quaternion(), ss = new T.Vector3(); for (let i = 0; i < A.dots.count; i += 6) { A.dots.getMatrixAt(i, mm); mm.decompose(pp, qq, ss); out.dotScales.push([+ss.x.toFixed(3), +pp.distanceTo(D.camera.position).toFixed(1)]); }
          // throw
          out.dbgPrev = V.prev.trig; window._dbg = []; const _orig = D.vrTick; try { D.vrTick(1/60); } catch (e) { out.err = String(e); } out.st = D.state; out.glide = D.P.gliding; pad.R.trig = 1; frames(1); out.dbgPrev2 = V.prev.trig; pad.R.trig = 0; out.afterThrow = V.nades; out.flying = D.NADES.length;
          let k = 0; while (D.NADES.length && D.NADES[0].fuse === -1 && k < 600) { frames(1); k++; }
          out.flightSec = +(k / 60).toFixed(2); const N = D.NADES[0]; out.landedNearRingM = N ? +Math.hypot(N.p.x - ring.x, N.p.z - ring.z).toFixed(2) : null;
          // an animal right next to where it landed
          const B = D.beasts.find(a => !a.dead && a.kind !== 'bird');
          if (B && N) { B.root.position.set(N.p.x + 2, N.p.y, N.p.z); B.x = N.p.x + 2; B.z = N.p.z; B.root.updateMatrixWorld(); }
          let j = 0; while (D.NADES.length && j < 200) { D.updateGun(1 / 60); j++; }
          out.fuseSec = +(j / 60).toFixed(2); out.animalKilled = B ? B.dead : 'none';
          // throw them all, then a dry click with none left
          for (let i = 0; i < 6; i++) { pad.R.trig = 1; frames(1); pad.R.trig = 0; frames(3); } out.nadesLeft = V.nades; out.arcHiddenWhenEmpty = !A.dots.visible;
          frames(200);
          // tap A: back to the gun
          pad.R.a = 1; frames(3); pad.R.a = 0; frames(3); out.backToGun = !V.nadeMode && V.gunOut && !!(V.gun && V.gun.visible); out.arcGone = !A.label.visible;
          return out; }""")
        import base64
        d = await pg.evaluate("() => window._shot"); open(SHOT, 'wb').write(base64.b64decode(d.split(',')[1])); d2 = await pg.evaluate('() => window._shot2'); open(SHOT.replace('.png','2.png'), 'wb').write(base64.b64decode(d2.split(',')[1]))
        print(json.dumps(r)); print("errors:", errs[:12] or "none")
        await b.close()
asyncio.run(main())
