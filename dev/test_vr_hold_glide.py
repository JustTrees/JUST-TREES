"""VR feel checks (1.23): the gun stays on your hand while walking/sprinting/turning, the gun hand is locked to the grip,
and gliding with straight arms never turns or flips the world.
Usage: python3 dev/make_debug.py index.html /tmp/dbg.html && python3 dev/test_vr_hold_glide.py /tmp/dbg.html"""
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
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = {};
          D.setVR(true); D.setMode('hunt'); D.set.size = 'medium'; D.set.weather = 'clear'; D.set.lat = 45; D.generate(); D.state = 'play';
          const T = D.THREE, V = D.vr; V.on = true; V.yaw = 0; V.cl = null; V.goodX = undefined; V.ox = D.P.x; V.oz = D.P.z; V.oy = D.P.y;
          const L = { head: new T.Vector3(0, 1.7, 0), R: new T.Vector3(.2, 1.35, -.35), Lh: new T.Vector3(-.25, 1.2, -.3) };
          const pad = { R: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 }, L: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 } };
          const toW = v => v.clone().applyAxisAngle(new T.Vector3(0, 1, 0), V.yaw).add(new T.Vector3(V.ox, V.oy, V.oz));
          // the controller's grip space is turned a little from its aim ray (as on a real Quest controller)
          const qs = { R: new T.Quaternion(), L: new T.Quaternion(), head: new T.Quaternion() }, gripOff = new T.Quaternion().setFromAxisAngle(new T.Vector3(1, 0, 0), -.6);
          const wq = q => new T.Quaternion().setFromAxisAngle(new T.Vector3(0, 1, 0), V.yaw).multiply(q);
          V.readInputs = () => ({ head: toW(L.head), headQ: wq(qs.head), hands: { right: Object.assign({ pos: toW(L.R), q: wq(qs.R).multiply(gripOff), rayPos: toW(L.R), rayQ: wq(qs.R) }, pad.R), left: Object.assign({ pos: toW(L.Lh), q: wq(qs.L).multiply(gripOff), rayPos: toW(L.Lh), rayQ: wq(qs.L) }, pad.L) } });
          const frames = n => { for (let i = 0; i < n; i++) { D.vrTick(1 / 60); if (!V.climbing) D.update(1 / 60); D.vrAfterMove(1 / 60); } };
          const gunOff = () => { const S = { grip: [0, -.075, .1] }; const g = V.gun.localToWorld(new T.Vector3(...S.grip)); return g.distanceTo(V.I.hands.right.pos); };   // against the hand pose of the same frame
          frames(40);
          out.gunOffStillCm = +(gunOff() * 100).toFixed(1);
          // walk forward, then sprint: how far does the gun trail behind the hand?
          pad.L.sy = -1; frames(60); let mx = 0; for (let i = 0; i < 60; i++) { frames(1); mx = Math.max(mx, gunOff()); } out.gunOffWalkCm = +(mx * 100).toFixed(1);
          pad.L.stickBtn = 1; frames(1); pad.L.stickBtn = 0; frames(30); mx = 0; for (let i = 0; i < 60; i++) { frames(1); mx = Math.max(mx, gunOff()); } out.gunOffSprintCm = +(mx * 100).toFixed(1);
          pad.L.sy = 0; frames(30);
          // snap turn
          pad.R.sx = 1; frames(1); pad.R.sx = 0; mx = 0; for (let i = 0; i < 10; i++) { frames(1); mx = Math.max(mx, gunOff()); } out.gunOffSnapTurnCm = +(mx * 100).toFixed(1);
          // the glove is locked onto the rifle grip
          D.vrHands(); const HO = D.vrHandsObj, gp = V.gun.localToWorld(new T.Vector3(0, -.075, .1));
          out.gloveToGripCm = +(HO.R.g.position.distanceTo(gp) * 100).toFixed(2);
          // the glove turns with the gun (same offset between them as between the controller's grip and its aim ray)
          const want = V.gun.quaternion.clone().multiply(gripOff); out.gloveTurnErrDeg = +(2 * Math.acos(Math.min(1, Math.abs(HO.R.g.quaternion.dot(want)))) * 57.3).toFixed(2);
          // gun away: glove back on the controller
          pad.R.a = 1; frames(2); pad.R.a = 0; frames(2); D.vrHands(); out.gloveOnControllerCm = +(HO.R.g.position.distanceTo(V.readInputs().hands.right.pos) * 100).toFixed(2);
          // glide with straight arms out to the sides (controllers pointing outward along the arm line), head turning around
          D.P.y += 60; D.P.onGround = false; V.oy = D.P.y; L.R.set(.8, 1.55, 0); L.Lh.set(-.8, 1.55, 0);
          qs.R.setFromAxisAngle(new T.Vector3(0, 1, 0), -Math.PI / 2); qs.L.setFromAxisAngle(new T.Vector3(0, 1, 0), Math.PI / 2);
          frames(3); const y0 = V.yaw; let p0 = [D.P.x, D.P.z]; const heads = []; let flips = 0, last = null;
          for (let i = 0; i < 180; i++) {
            qs.head.setFromAxisAngle(new T.Vector3(0, 1, 0), Math.sin(i / 20) * 1.4);            // look left and right
            const j = (Math.random() - .5) * .05; qs.R.setFromAxisAngle(new T.Vector3(0, 1, 0), -Math.PI / 2 + j); qs.L.setFromAxisAngle(new T.Vector3(0, 1, 0), Math.PI / 2 - j);
            L.R.y = 1.55 + Math.sin(i / 15) * .1; L.Lh.y = 1.55 - Math.sin(i / 15) * .1;              // tilting the arms
            frames(1); const d = V.glideDir; if (last && d && d.x * last.x + d.z * last.z < 0) flips++; last = d && { x: d.x, z: d.z };
          }
          out.glidingStraightArms = D.P.gliding; out.worldTurnDeg = +((V.yaw - y0) * 57.3).toFixed(2); out.glideDirFlips = flips;
          out.glideMove = [+(D.P.x - p0[0]).toFixed(1), +(D.P.z - p0[1]).toFixed(1)];
          return out; }""")
        print(json.dumps(r, indent=0)); print("errors:", errs or "none"); await b.close()
asyncio.run(main())
