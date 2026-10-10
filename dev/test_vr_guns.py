"""VR Hunting guns (1.22): magazines, reload by hand, gun wheel, auto fire, ammo cans, shooting while hanging.
Usage: python3 dev/make_debug.py index.html /tmp/dbg.html && python3 dev/test_vr_guns.py /tmp/dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1])
SHOT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/guns.png'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        pg.on("console", lambda m: errs.append("CON " + m.text) if m.type == "error" else None)
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = {};
          D.setVR(true); D.setMode('hunt'); D.set.size = 'small'; D.set.weather = 'clear'; D.set.lat = 45; D.generate(); D.state = 'play';
          const T = D.THREE, V = D.vr; V.on = true; V.yaw = 0; V.cl = null; V.goodX = undefined; V.ox = D.P.x; V.oz = D.P.z; V.oy = D.P.y;
          const L = { head: new T.Vector3(0, 1.7, 0), R: new T.Vector3(.2, 1.35, -.35), Lh: new T.Vector3(-.25, 1.2, -.3) };
          const pad = { R: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 }, L: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 } };
          const toW = v => v.clone().applyAxisAngle(new T.Vector3(0, 1, 0), V.yaw).add(new T.Vector3(V.ox, V.oy, V.oz));
          const toL = w => w.clone().sub(new T.Vector3(V.ox, V.oy, V.oz)).applyAxisAngle(new T.Vector3(0, 1, 0), -V.yaw);
          const qs = { R: new T.Quaternion(), L: new T.Quaternion(), head: new T.Quaternion() };
          V.readInputs = () => ({ head: toW(L.head), headQ: qs.head.clone(), hands: { right: Object.assign({ pos: toW(L.R), q: qs.R.clone(), rayPos: toW(L.R), rayQ: qs.R.clone() }, pad.R), left: Object.assign({ pos: toW(L.Lh), q: qs.L.clone(), rayPos: toW(L.Lh), rayQ: qs.L.clone() }, pad.L) } });
          const frames = n => { for (let i = 0; i < n; i++) { D.vrTick(1 / 60); if (!V.climbing) D.update(1 / 60); D.vrAfterMove(1 / 60); D.updateGun(1 / 60); } };
          const A = () => D.arms[V.gunKind];
          frames(30);
          out.cans = D.ammoCans.length; out.start = { gun: V.gunKind, mag: A().mag, res: A().res };
          // 1. empty the sniper: five shots, bolt time between
          let shots = 0; const nT = () => D.tracers.length;
          const cock = () => { const G0 = V.gun, S0 = D.GUNSPOT[V.gunKind], hw = G0.localToWorld(new T.Vector3(...S0.handle)); L.Lh.copy(toL(hw.add(new T.Vector3(-.15, 0, .1)))); frames(2); pad.L.grip = 1; frames(2);
            const bk = G0.localToWorld(new T.Vector3(0, 0, 1)).sub(G0.localToWorld(new T.Vector3())).normalize().multiplyScalar(.009); for (let i = 0; i < 10; i++) { L.Lh.copy(toL(toW(L.Lh).add(bk))); frames(1); } pad.L.grip = 0; frames(2); L.Lh.set(-.25, 1.2, -.3); };
          out.boltPerShot = [];
          for (let i = 0; i < 5; i++) { pad.R.trig = 1; const t0 = nT(); frames(1); shots += nT() > t0 ? 1 : 0; pad.R.trig = 0; frames(20);
            if (i === 0) { pad.R.trig = 1; const t9 = nT(); frames(2); out.secondShotWithoutBolt = nT() - t9; pad.R.trig = 0; frames(2); }
            out.boltPerShot.push(A().phase); if (i < 4) cock(); frames(5); }
          out.sniperShots = shots; out.afterEmpty = { mag: A().mag, phase: A().phase };
          frames(20);
          const G = V.gun, U = G.userData, S = D.GUNSPOT[V.gunKind];
          out.magHoverCm = +(U.mag.position.distanceTo(U.magBase) * 100).toFixed(1);
          out.magGlow = +U.mag.material.emissive.r.toFixed(2);
          pad.R.trig = 1; const t1 = nT(); frames(2); out.dryFireShots = nT() - t1; pad.R.trig = 0; frames(2);
          // 2. off hand to the hovering magazine, squeeze, push it up into the gun
          const magW = () => G.localToWorld(U.magBase.clone().addScaledVector(U.magDir, S.drop * A().k + S.magC));
          // squeeze near the front grip while empty: no front grip, the hand goes to the magazine (or nothing if it's too far)
          L.Lh.copy(toL(G.localToWorld(new T.Vector3(...S.fore)))); frames(2); pad.L.grip = 1; frames(2); out.emptyFrontGripSnap = V.two; pad.L.grip = 0; frames(2);
          // squeeze 25 cm away from the magazine: the hand snaps to it
          L.Lh.copy(toL(magW().add(new T.Vector3(-.12, .06, .06)))); frames(3); pad.L.grip = 1; frames(2); out.grabbedMagFrom15cm = V.rl.grab;
          out.gloveOnMagCm = +(D.vrHandsObj.L.g.position.distanceTo(magW()) * 100).toFixed(1);
          const up = G.localToWorld(U.magDir.clone()).sub(G.localToWorld(new T.Vector3())).normalize().multiplyScalar(-.012); for (let i = 0; i < 20 && A().phase === 1; i++) { L.Lh.copy(toL(toW(L.Lh).add(up))); frames(1); }
          out.afterInsert = { mag: A().mag, res: A().res, phase: A().phase }; pad.L.grip = 0; frames(3);
          pad.R.trig = 1; const t2 = nT(); frames(2); out.shotBeforeBolt = nT() - t2; pad.R.trig = 0; frames(2);
          out.boltGlow = +(U.charge.children[0].material.emissive.r).toFixed(2);
          // 3. grab the bolt and pull it back, let go
          const hW = () => G.localToWorld(new T.Vector3(...S.handle));
          L.Lh.copy(toL(G.localToWorld(new T.Vector3(...S.fore)))); frames(2); pad.L.grip = 1; frames(2); out.unchamberedFrontGripSnap = V.two; out.grabAtFore = V.rl.grab; pad.L.grip = 0; frames(2);
          L.Lh.copy(toL(hW().add(new T.Vector3(-.12, -.03, .06)))); frames(2); pad.L.grip = 1; frames(2); out.grabbedBoltFrom13cm = V.rl.grab;
          out.gloveOnBoltCm = +(D.vrHandsObj.L.g.position.distanceTo(hW()) * 100).toFixed(1);
          const back = G.localToWorld(new T.Vector3(0, 0, 1)).sub(G.localToWorld(new T.Vector3())).normalize();
          for (let i = 0; i < 10; i++) { L.Lh.add(toL(toW(new T.Vector3()).add(back.clone().multiplyScalar(.009))).sub(toL(toW(new T.Vector3())))); frames(1); }
          out.boltArmed = V.rl.armed; pad.L.grip = 0; frames(2); out.afterBolt = { phase: A().phase };
          L.Lh.copy(toL(G.localToWorld(new T.Vector3(...S.fore)))); frames(2); pad.L.grip = 1; frames(2); out.loadedFrontGripSnap = V.two; pad.L.grip = 0; L.Lh.set(-.25, 1.2, -.3); frames(3);
          pad.R.trig = 1; const t3 = nT(); frames(2); out.shotAfterReload = nT() - t3; pad.R.trig = 0; frames(100);
          // scope: two hands on the sniper near the face (not lined up exactly); shoot, let go to bolt: scope off; grab again: scope on
          A().mag = 3; A().phase = 0; L.R.set(.0, 1.4, -.35); qs.R.identity(); qs.head.setFromAxisAngle(new T.Vector3(0, 1, 0), .5); frames(40);
          const Ss = D.GUNSPOT.hunt; L.head.copy(L.R.clone().add(new T.Vector3(Ss.eye[0] - Ss.grip[0], Ss.eye[1] - Ss.grip[1], Ss.eye[2] - Ss.grip[2]))).add(new T.Vector3(.12, .08, .14));
          const foreL = () => L.R.clone().add(new T.Vector3(Ss.fore[0] - Ss.grip[0], Ss.fore[1] - Ss.grip[1], Ss.fore[2] - Ss.grip[2]));
          frames(3); out.scopedOneHandNearFace = V.scoped;
          L.Lh.copy(foreL()); frames(3); pad.L.grip = 1; frames(5); out.scopedTwoHandsLoose = V.scoped;
          pad.R.trig = 1; frames(1); pad.R.trig = 0; frames(5); out.scopedRightAfterShot = V.scoped; pad.L.grip = 0; frames(3); out.scopedOffHandLetGo = V.scoped;
          L.Lh.copy(L.R.clone().add(new T.Vector3(.1, -.05, .15))); frames(2); pad.L.grip = 1; frames(2); out.boltGrab = V.rl.grab;
          const bk2 = new T.Vector3(0, 0, .009); for (let i = 0; i < 10; i++) { L.Lh.add(bk2); frames(1); } pad.L.grip = 0; frames(3); out.phaseAfterBolt = A().phase;
          L.Lh.copy(foreL()); frames(3); pad.L.grip = 1; frames(5); out.scopedRegrip = V.scoped; pad.L.grip = 0;
          L.head.set(0, 1.7, 0); qs.head.identity(); L.R.set(.2, 1.35, -.35); L.Lh.set(-.25, 1.2, -.3); frames(40); out.scopedHandsDown = V.scoped;
          // hands close together (controllers almost touching) still snap the front hand on and bring up the scope
          { A().phase = 0; A().mag = 3; L.R.set(.0, 1.45, -.3); qs.R.identity(); qs.head.identity(); frames(40);
            const Ss = D.GUNSPOT.hunt; L.head.copy(L.R.clone().add(new T.Vector3(Ss.eye[0] - Ss.grip[0], Ss.eye[1] - Ss.grip[1], Ss.eye[2] - Ss.grip[2]))).add(new T.Vector3(0, .03, .08));
            L.Lh.copy(L.R.clone().add(new T.Vector3(-.03, .02, -.08))); frames(3); pad.L.grip = 1; frames(5);
            out.closeHandsSnap = V.two; out.closeHandsScope = V.scoped; out.closeHandsGap = +(L.Lh.distanceTo(L.R) * 100).toFixed(0) + ' cm';
            pad.L.grip = 0; frames(3); L.Lh.set(-.6, 1.0, .2); frames(3); pad.L.grip = 1; frames(3); out.farHandNoSnap = !V.two; pad.L.grip = 0;
            L.head.set(0, 1.7, 0); L.R.set(.2, 1.35, -.35); L.Lh.set(-.25, 1.2, -.3); frames(40); }
          // 4. tap B: mark
          pad.R.b = 1; frames(5); pad.R.b = 0; frames(2); out.tapMark = !!(V.mark && V.mark.visible); out.wheelAfterTap = !!(V.wheelM && V.wheelM.visible);
          // 5. hold B: wheel; point right (assault rifle), let go
          pad.R.b = 1; frames(25); out.wheelOpen = !!(V.wheelM && V.wheelM.visible);
          qs.R.setFromAxisAngle(new T.Vector3(0, 1, 0), -.45); frames(3); out.wheelSel = V.wh.sel;
          pad.R.b = 0; frames(2); qs.R.identity(); frames(40); out.afterWheel = V.gunKind; out.wheelClosed = !V.wheelM.visible;
          // 6. assault rifle: hold the trigger for one second
          pad.R.trig = 1; frames(10); pad.R.trig = 0; frames(5); const dr = { mag: A().mag, res: A().res }; pad.R.stickBtn = 1; frames(2); pad.R.stickBtn = 0; frames(20);
          out.earlyDrop = { before: dr, after: { mag: A().mag, res: A().res, phase: A().phase }, hoverCm: +(V.gun.userData.mag.position.distanceTo(V.gun.userData.magBase) * 100).toFixed(1) };
          { const G2 = V.gun, U2 = G2.userData, S2 = D.GUNSPOT.ar, mw = () => G2.localToWorld(U2.magBase.clone().addScaledVector(U2.magDir, S2.drop * A().k + S2.magC));
            L.Lh.copy(toL(mw().add(new T.Vector3(-.15, 0, 0)))); frames(2); pad.L.grip = 1; frames(2);
            const up = G2.localToWorld(U2.magDir.clone()).sub(G2.localToWorld(new T.Vector3())).normalize().multiplyScalar(-.012); for (let i = 0; i < 20 && A().phase === 1; i++) { L.Lh.copy(toL(toW(L.Lh).add(up))); frames(1); }
            pad.L.grip = 0; frames(2); L.Lh.copy(toL(G2.localToWorld(new T.Vector3(...S2.handle)))); frames(2); pad.L.grip = 1; frames(2);
            const bk = G2.localToWorld(new T.Vector3(0, 0, 1)).sub(G2.localToWorld(new T.Vector3())).normalize().multiplyScalar(.009); for (let i = 0; i < 10; i++) { L.Lh.copy(toL(toW(L.Lh).add(bk))); frames(1); }
            pad.L.grip = 0; frames(3); L.Lh.set(-.25, 1.2, -.3); out.afterEarlyReload = { mag: A().mag, res: A().res, phase: A().phase }; }
          let m0 = A().mag; let t4 = 0; pad.R.trig = 1; frames(60); pad.R.trig = 0; out.arShotsIn1s = m0 - A().mag; out.arMag = A().mag;
          // 7. SMG (point down) and pistol (point left)
          const pick = (ang, axis) => { pad.R.b = 1; frames(25); qs.R.setFromAxisAngle(axis, ang); frames(3); pad.R.b = 0; frames(2); qs.R.identity(); frames(40); return V.gunKind; };
          out.pickDown = pick(-.45, new T.Vector3(1, 0, 0));
          m0 = A().mag; pad.R.trig = 1; frames(60); pad.R.trig = 0; out.smgShotsIn1s = m0 - A().mag;
          out.pickLeft = pick(.45, new T.Vector3(0, 1, 0));
          frames(20); m0 = A().mag; pad.R.trig = 1; frames(60); pad.R.trig = 0; out.pistolShotsHeld1s = m0 - A().mag; m0 = A().mag; for (let i = 0; i < 5; i++) { pad.R.trig = 1; frames(3); pad.R.trig = 0; frames(9); } out.pistol5Pulls = m0 - A().mag;
          // pistol two-handed: off hand to the grip
          L.Lh.copy(toL(V.gun.localToWorld(new T.Vector3(...D.GUNSPOT.pistol.fore)))); frames(2); pad.L.grip = 1; frames(3); out.pistolTwoHand = V.two; pad.L.grip = 0; L.Lh.set(-.25, 1.2, -.3); frames(3);
          // the off hand far from the pistol does not snap on
          pad.L.grip = 1; frames(3); out.pistolFarSnap = V.two; pad.L.grip = 0; frames(3);
          // 8. walk onto an ammo can
          const c = D.ammoCans.find(c => c.kind === 'pistol' && !c.got) || D.ammoCans[0], k = c.kind, before = D.arms[k].res;
          V.ox += c.x - D.P.x; V.oz += c.z - D.P.z; V.goodX = undefined; frames(5);
          out.can = { kind: k, before, after: D.arms[k].res, got: c.got, wrist: V.lootMsg };
          // 9. hang on a trunk with the off hand, gun out: shoot while hanging, no scope
          pick(.45, new T.Vector3(0, 1, 0)); // still pistol
          let tree = null, bd = 1e9; for (const list of D.obstacles.values()) for (const o of list) if (o.t && o.t.hold && o.h > 7 && !o.t.tx) { const d = Math.hypot(o.x - D.P.x, o.z - D.P.z); if (d < bd) { bd = d; tree = o; } }
          V.ox += tree.x - D.P.x + tree.tr + .8; V.oz += tree.z - D.P.z; V.goodX = undefined; frames(10);
          const dir = new T.Vector3(tree.x - D.P.x, 0, tree.z - D.P.z).normalize();
          L.Lh.copy(toL(new T.Vector3(tree.x, D.P.y + 1.3, tree.z).addScaledVector(dir, -tree.tr * .3))); frames(2); pad.L.grip = 1; frames(3);
          out.hangHand = V.cl.hold; out.gunOutWhileHanging = V.gun.visible;
          pad.R.trig = 1; t4 = nT(); frames(2); pad.R.trig = 0; out.shotWhileHanging = nT() - t4; out.scopedWhileHanging = V.scoped;
          // the gun hand can't grab while holding the gun
          L.R.copy(toL(new T.Vector3(tree.x, D.P.y + 1.6, tree.z).addScaledVector(dir, -tree.tr * .3))); frames(2); pad.R.grip = 1; frames(3); out.holdAfterGunHandGrip = V.cl.hold; pad.R.grip = 0; frames(2);
          // A while hanging by the gun hand (gun away first): the gun can't come out
          pad.R.a = 1; frames(2); pad.R.a = 0; frames(2); out.gunAwayToClimb = !V.gunOut;
          pad.L.grip = 0; frames(2); pad.R.grip = 1; frames(3); out.gunHandHolds = V.cl.hold;
          pad.R.a = 1; frames(2); pad.R.a = 0; frames(2); out.aBlockedWhileGunHandHolds = !V.gunOut;
          pad.R.grip = 0; for (let i = 0; i < 400 && !D.P.onGround; i++) frames(1);
          pad.R.a = 1; frames(2); pad.R.a = 0; frames(30); out.gunBack = V.gunOut;
          return out; }""")
        print(json.dumps(r, indent=0))
        await b.close()
        print("errors:", errs or "none")
asyncio.run(main())
