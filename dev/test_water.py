"""Under water in VR (1.32): walk the lake bed, 5 seconds of breath, drown and wake on dry land; a short dip recovers;
and choosing your spawn on the preview map snaps to the nearest dry spot.
Usage: python3 dev/make_debug.py index.html /tmp/dbg.html && python3 dev/test_water.py /tmp/dbg.html [/tmp/uw.jpg]"""
import os, sys, asyncio, json, base64
from playwright.async_api import async_playwright
T = 'file://' + os.path.abspath(sys.argv[1]); OUT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/uw.jpg'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 900, "height": 560})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(T); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = {};
          D.setSeed(3); D.setVR(true); D.setMode('hike'); D.set.size = 'medium'; D.set.edges = 'endless'; D.set.weather = 'clear'; D.set.lat = 45; D.set.hour = 12; D.generate(); D.state = 'play';
          const T = D.THREE, V = D.vr, H = D.H, w = D.water; V.on = true; V.yaw = 0; V.cl = null; V.goodX = undefined;
          // the deepest point of the map, and dry shore nearby
          let deep = null; for (let i = -40; i <= 40; i++) for (let j = -40; j <= 40; j++) { const x = i * 6, z = j * 6, h = H(x, z); if (!deep || h < deep[2]) deep = [x, z, h]; }
          out.deepBelowWater = +(w - deep[2]).toFixed(1);
          let shore = null; for (let r = 4; r < 200 && !shore; r += 2) for (let k = 0; k < 32 && !shore; k++) { const a = k / 32 * 6.283, x = deep[0] + Math.cos(a) * r, z = deep[1] + Math.sin(a) * r; if (H(x, z) > w + .5 && D.okSpot(x, z)) shore = [x, z]; }
          const pad = { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 }; let yawQ = new T.Quaternion();
          V.readInputs = () => { const o = new T.Vector3(V.ox, V.oy, V.oz), yq = new T.Quaternion().setFromAxisAngle(new T.Vector3(0, 1, 0), V.yaw), W = v => v.clone().applyQuaternion(yq).add(o);
            return { head: W(new T.Vector3(0, 1.7, 0)), headQ: yq.clone().multiply(yawQ), hands: { left: Object.assign({ pos: W(new T.Vector3(-.25, 1.1, -.2)), q: yq.clone(), rayPos: W(new T.Vector3(-.25, 1.1, -.2)), rayQ: yq.clone() }, pad), right: Object.assign({ pos: W(new T.Vector3(.25, 1.1, -.2)), q: yq.clone(), rayPos: W(new T.Vector3(.25, 1.1, -.2)), rayQ: yq.clone(), trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 }) } }; };
          const place = (x, z) => { D.P.x = x; D.P.z = z; D.P.y = D.groundAt(x, z); D.P.onGround = true; V.ox = x; V.oz = z; V.oy = D.P.y; V.goodX = undefined; };
          const frames = n => { for (let i = 0; i < n; i++) { D.vrTick(1 / 60); if (!V.climbing) D.update(1 / 60); D.vrAfterMove(1 / 60); } };
          const face = (tx, tz) => { const dx = tx - D.P.x, dz = tz - D.P.z; yawQ.setFromAxisAngle(new T.Vector3(0, 1, 0), Math.atan2(-dx, -dz)); };
          // a short dip: walk in a little, come straight back out
          place(shore[0], shore[1]); frames(10); face(deep[0], deep[1]); pad.sy = -1; let maxT = 0, minY = 99;
          for (let i = 0; i < 400 && !D.UW.under; i++) frames(1);
          out.wentUnder = D.UW.under; frames(90); out.bedBelowWaterM = +(w - D.P.y).toFixed(1); out.fogFarUnder = Math.round(D.scene.fog.far); maxT = D.UW.t;
          face(shore[0], shore[1]); for (let i = 0; i < 300 && D.UW.under; i++) frames(1); frames(120); out.dipBreathUsed = +maxT.toFixed(1); out.backOut = !D.UW.under; out.breathRecovered = D.UW.t < .1; out.fogBack = D.scene.fog.far > 200;
          // a long stay: stand still on the deepest bed
          pad.sy = 0; place(deep[0], deep[1]); frames(10); out.standingOnBed = +(w - D.P.y).toFixed(1); const p0 = [D.P.x, D.P.z]; let moved = false;
          for (let i = 0; i < 60 * 9 && !moved; i++) { frames(1); if (Math.hypot(D.P.x - p0[0], D.P.z - p0[1]) > 20) { moved = true; out.respawnAfterSec = +((i + 1) / 60).toFixed(1); } }
          out.respawnedOnDryLand = D.H(D.P.x, D.P.z) > w + 1; frames(150); out.screenClearAfter = D.UW.mesh.material.uniforms.uBlack.value === 0;
          // falling in from up high: sinks slowly
          place(deep[0], deep[1]); D.P.y = w - .5; V.oy = D.P.y; D.P.onGround = false; D.P.vy = 0; frames(10); const y1 = D.P.y; frames(30); out.sinkSpeedMs = +((y1 - D.P.y) / .5).toFixed(1);
          // choosing a spawn: pointing at the deepest water snaps to the nearest dry, walkable spot
          D.VRUI.dio = D.buildDiorama(); D.pickSpawn(new T.Vector3(deep[0], 0, deep[1])); out.pickedDry = D.H(D.P.x, D.P.z) > w + .3; out.pickedOk = D.okSpot(D.P.x, D.P.z);
          out.pickedDistFromPointM = Math.round(Math.hypot(D.P.x - deep[0], D.P.z - deep[1])); out.pinMoved = Math.abs(D.VRUI.dio.userData.pin.position.x - D.P.x) < .01;
          D.pickSpawn(new T.Vector3(shore[0], 0, shore[1])); out.pickedExactWhenDry = Math.hypot(D.P.x - shore[0], D.P.z - shore[1]) < .01;
          return out; }""")
        print(json.dumps(r))
        u = await pg.evaluate("""() => { const T = D.THREE, V = D.vr; let deep = null; for (let i = -40; i <= 40; i++) for (let j = -40; j <= 40; j++) { const x = i * 6, z = j * 6, h = D.H(x, z); if (!deep || h < deep[2]) deep = [x, z, h]; }
          D.P.x = deep[0] + 6; D.P.z = deep[1]; D.P.y = D.groundAt(D.P.x, D.P.z); V.ox = D.P.x; V.oz = D.P.z; V.oy = D.P.y; D.UW.t = 3.6;
          for (let i = 0; i < 5; i++) { D.vrTick(1 / 60); D.update(1 / 60); D.vrAfterMove(1 / 60); } D.loop(performance.now());
          const cam = new T.PerspectiveCamera(80, 900 / 560, .05, 3000); cam.position.copy(V.readInputs().head); cam.lookAt(cam.position.clone().add(new T.Vector3(-1, .35, 0)));
          D.renderer.setSize(900, 560, false); D.renderer.render(D.scene, cam); return D.renderer.domElement.toDataURL('image/jpeg', .85); }""")
        open(OUT, "wb").write(base64.b64decode(u.split(',')[1]))
        print("errors:", errs or "none"); await b.close()
asyncio.run(main())
