"""The recurve bow (1.85, VR Hunting) and unlimited ammo. Bow on the gun wheel (Hunting only), quiver over the gun-hand shoulder:
trigger behind your shoulder takes an arrow, it nocks at the string, draw back, let go to shoot; the arrow arcs down; a good shot drops
a deer, a weak one only sends it running; the shot itself doesn't scatter the herd; tap A goes back to the gun. Unlimited ammo: no ammo cans.
Usage: python3 dev/test_bow.py /tmp/dbg.html [/tmp/bow.jpg]"""
import os, sys, asyncio, json, base64
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1]); SHOT = sys.argv[2] if len(sys.argv) > 2 else None
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        pg.on("console", lambda m: errs.append("CON " + m.text) if m.type == "error" else None)
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = {};
          D.setVR(true); D.setMode('pvp'); out.pvpWheel = D.wheelKeys().join(',');
          D.setMode('hunt'); D.set.size = 'small'; D.set.weather = 'clear'; D.set.lat = 45; D.set.dino = false; D.generate(); D.state = 'play';
          out.huntWheel = D.wheelKeys().join(','); out.cans = D.ammoCans.length; out.inf = D.INF_AMMO;
          const T = D.THREE, V = D.vr; V.on = true; V.yaw = 0; V.cl = null; V.goodX = undefined; V.ox = D.P.x; V.oz = D.P.z; V.oy = D.P.y;
          const L = { head: new T.Vector3(0, 1.7, 0), R: new T.Vector3(.2, 1.35, -.35), Lh: new T.Vector3(-.05, 1.55, -.5) };
          const pad = { R: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 }, L: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 } };
          const toW = v => v.clone().applyAxisAngle(new T.Vector3(0, 1, 0), V.yaw).add(new T.Vector3(V.ox, V.oy, V.oz));
          const toL = w => w.clone().sub(new T.Vector3(V.ox, V.oy, V.oz)).applyAxisAngle(new T.Vector3(0, 1, 0), -V.yaw);
          const qs = { R: new T.Quaternion(), L: new T.Quaternion(), head: new T.Quaternion() };
          V.readInputs = () => ({ head: toW(L.head), headQ: qs.head.clone(), hands: { right: Object.assign({ pos: toW(L.R), q: qs.R.clone(), rayPos: toW(L.R), rayQ: qs.R.clone() }, pad.R), left: Object.assign({ pos: toW(L.Lh), q: qs.L.clone(), rayPos: toW(L.Lh), rayQ: qs.L.clone() }, pad.L) } });
          const frames = n => { for (let i = 0; i < n; i++) { D.vrTick(1 / 60); if (!V.climbing) D.update(1 / 60); D.vrAfterMove(1 / 60); D.updateGun(1 / 60); } };
          frames(30);
          D.pickGun('bow'); frames(10);
          const B = D.bowObj, st = () => V.bowSt || {};
          out.bowShown = !!(B && B.bow.visible && B.quiver.visible); out.gunHidden = !(V.gun && V.gun.visible);
          // trigger in front of you: no arrow
          pad.R.trig = 1; frames(3); out.arrowFromFront = !!st().arrow; pad.R.trig = 0; frames(3);
          // reach back over the right shoulder: an arrow
          L.R.set(.12, 1.62, .16); frames(3); pad.R.trig = 1; frames(3); out.arrowFromQuiver = !!st().arrow;
          // bring it to the string: it nocks
          const nockW = () => B.nockSet.position.clone();
          L.R.copy(toL(nockW()).add(new T.Vector3(.04, .03, .05))); frames(4); out.nocked = !!st().nocked;
          // aim at a deer 25 m ahead: put one there, draw straight back (a touch high for the drop)
          const ax = D.P.x, az = D.P.z - 25; const A = D.addGround('buck', ax, az); D.updateAnimals(1 / 60); A.mode = 'idle'; A.want = 0; A.x = ax; A.z = az; D.updateAnimals(1 / 60);
          const bowHand = toW(L.Lh), tgt = new T.Vector3(A.x, A.y + 1.0, A.z), dist = tgt.distanceTo(bowHand), tFlight = dist / D.BOW.vMax;
          tgt.y += .5 * 9.81 * tFlight * tFlight;
          const aim = tgt.clone().sub(bowHand).normalize();
          const pull = (k) => { const restW = B.bow.localToWorld(new T.Vector3(-.018, D.BOW.rest[1], D.BOW.rest[2])); L.R.copy(toL(restW.clone().addScaledVector(aim, -k))); frames(6); };
          for (const k of [.3, .45, .6, .72]) pull(k);
          out.drawF = +st().f.toFixed(2);
          const others = D.beasts.filter(o => o !== A && !o.dead).length;
          pad.R.trig = 0; frames(1); out.arrowsFlying = D.ARROWS.length; out.handEmpty = !st().arrow;
          let n = 0; while (D.ARROWS.length && n < 120) { frames(1); n++; }
          out.flightFrames = n; out.deerDown = A.dead; out.score = +D.hunt.score.toFixed(1);
          out.sensesCalm = D.sense ? D.sense.shotT : null;
          // a weak shot at a second deer: it only runs
          const A2 = D.addGround('buck', D.P.x + 3, D.P.z - 8); D.updateAnimals(1 / 60); A2.mode = 'idle'; A2.want = 0; D.updateAnimals(1 / 60); const a2x = A2.x;
          L.R.set(.12, 1.62, .16); frames(3); pad.R.trig = 0; frames(2); pad.R.trig = 1; frames(3); L.R.copy(toL(nockW())); frames(4);
          const aim2 = new T.Vector3(A2.x, A2.y + 1.75, A2.z).sub(toW(L.Lh)).normalize();
          for (let it = 0; it < 5; it++) { const restW = B.bow.localToWorld(new T.Vector3(-.018, D.BOW.rest[1], D.BOW.rest[2])); L.R.copy(toL(restW.clone().addScaledVector(aim2, -.27))); frames(6); }
          out.weakF = +st().f.toFixed(2); pad.R.trig = 0; frames(1); n = 0; while (D.ARROWS.length && n < 120) { frames(1); n++; }
          for (let i = 0; i < 30; i++) D.updateAnimals(1 / 30); out.weakDeer = { dead: A2.dead, fleeing: Math.hypot(A2.x - a2x, A2.z - (D.P.z - 8)) > 3 || (A2.fleeT || 0) > 0 };
          // let go before nocking: the arrow is just dropped
          L.R.set(.12, 1.62, .16); frames(3); pad.R.trig = 0; frames(2); pad.R.trig = 1; frames(3); L.R.set(.3, 1.2, -.2); frames(3); pad.R.trig = 0; frames(2);
          out.droppedNoShot = D.ARROWS.length === 0 && !st().arrow;
          // tap A: back to the gun
          pad.R.a = 1; frames(3); pad.R.a = 0; frames(5); out.backToGun = !V.bowMode && !!(V.gun && V.gun.visible) && !B.bow.visible;
          // unlimited ammo: empty and reload the AK, spare stays
          D.allGuns(); D.pickGun('ar'); frames(5); const AR = D.arms.ar; AR.mag = 0; AR.phase = 1; AR.k = 0; frames(2);
          out.arCounter = V.gun && V.gun.userData && V.gun.userData.counter ? 1 : 0;
          return out; }""")
        if SHOT:
            img = await pg.evaluate("""() => { const T = D.THREE, V = D.vr; D.pickGun('bow'); return 1; }""")
        print(json.dumps(r)); print("errors:", errs or "none")
        ok = (r["huntWheel"] == "hunt,ar,smg,pistol,bow,gren" and r["pvpWheel"] == "hunt,ar,smg,pistol,gren" and r["cans"] == 0 and r["inf"]
              and r["bowShown"] and r["gunHidden"] and not r["arrowFromFront"] and r["arrowFromQuiver"] and r["nocked"] and r["drawF"] > .8
              and r["arrowsFlying"] == 1 and r["handEmpty"] and r["deerDown"] and r["score"] > 0 and r["flightFrames"] < 60
              and r["weakF"] < .25 and not r["weakDeer"]["dead"] and r["weakDeer"]["fleeing"] and r["droppedNoShot"] and r["backToGun"] and not errs)
        print("PASS" if ok else "FAIL"); await b.close()
        if not ok: sys.exit(1)
asyncio.run(main())
