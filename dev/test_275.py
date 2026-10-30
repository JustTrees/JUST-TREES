"""2.75 (3.27: the jet ski is the reward for cache #50: wade into the sea and take it out of your pack, and it's there in the water): jet skis in Geocaching; point at one (it glows)
and pull the trigger to sit on it; both grips on the bars start the engine; the trigger is the throttle, the bars steer; your eyes never
move up or down while the hull bobs; it slides up a sandy beach and stops; let go, point at the sand and pull the trigger to hop off.
Usage: python3 dev/test_275.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
GEN = """(found) => { window.FREEZE = true; D.renderer.setAnimationLoop(null); try { localStorage.setItem('jt-geochar', JSON.stringify({ n: found, score: 0, kills: 0 })); } catch (_) {}
  D.DEV.ok = true; D.setSeed(4242); D.setVR(true); D.setMode('hunt'); D.vr.on = true; D.set.hand = 'right';
  Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .5, rough: .5, huntMap: 'globe', dino: false });
  D.generate(); D.state = 'play'; window.tick = n => { for (let i = 0; i < n; i++) { D.endlessTick(1 / 30); D.geoTick(1 / 30); } };
  const T = D.THREE; window.hand = (pos, o) => Object.assign({ pos: pos.clone(), rayPos: pos.clone(), rayQ: new T.Quaternion(), q: new T.Quaternion(), grip: 0, trig: 0, sx: 0, sy: 0, a: 0, b: 0, stickBtn: 0 }, o || {});
  window.aimAt = (h, p) => { h.rayQ.setFromUnitVectors(new T.Vector3(0, 0, -1), p.clone().sub(h.rayPos).normalize()); };
  return [D.GEO.found.size, D.GEO.items.has("jetski"), D.jetOn()]; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        g0 = await pg.evaluate(GEN, 49)
        print("at49", g0)
        g = await pg.evaluate(GEN, 50)
        print("at50", g)
        r = await pg.evaluate("""() => { const o = {}, T = D.THREE, P = D.P, J0 = D.JET.list; let J = null;
          // a sea shore: on the sand it won't come out; wade in and it's there in the water in front of you
          for (const j of D.jetPlaceOld()) { D.geoTeleport(j.p); tick(60); const out = [0, 0]; D.glFromSphere(j.p, out); const b = D.jetFindBeach(out[0], out[1]); if (!b) continue;
            { let dry = null; for (let r = 2; r < 40 && !dry; r += 1) for (let q = 0; q < 16 && !dry; q++) { const x = b.x + Math.cos(q * .39) * r, z = b.z + Math.sin(q * .39) * r; if (D.H(x, z) > D.water + .4) dry = [x, z]; } if (dry) { P.x = dry[0]; P.z = dry[1]; P.y = D.groundAt(P.x, P.z); o.dry = D.jetTakeOut(); } else o.dry = 'none'; P.x = b.x; P.z = b.z; }
            for (let k = 0; k < 40 && D.H(P.x, P.z) > D.water - .4; k++) { P.x += Math.sin(b.yaw) * .5; P.z += Math.cos(b.yaw) * .5; } P.yaw = b.yaw;
            if (D.jetTakeOut()) { J = D.JET.list.find(q => q.mine); tick(2); break; } }
          o.placed = J && J.obj ? 'J' : '-';
          if (!J) return o;
          o.where = [+(D.H(J.x, J.z) - D.water).toFixed(2), D.geoSalty({ x: J.x, z: J.z })];
          // walk up, point: it glows; trigger: on
          P.x = J.x + 3; P.z = J.z; const head = () => new T.Vector3(P.x, P.y + 1.6, P.z); P.y = D.water - .9; D.vr.headLocalY = 1.6;
          let I = { head: head(), headQ: new T.Quaternion(), hands: {} }, M = hand(head().add(new T.Vector3(.2, -.4, 0))), O = hand(head().add(new T.Vector3(-.2, -.4, 0))); I.hands.right = M; I.hands.left = O; D.vr.I = I;
          aimAt(M, new T.Vector3(J.x, J.obj.position.y + .5, J.z)); D.geoGearTick(I, M, O, 1 / 30); o.glow = J.obj.userData.mats[0].emissive.getHex() > 0;
          M.trig = 1; D.geoGearTick(I, M, O, 1 / 30); M.trig = 0; o.on = !!D.JET.ride; D.vr.pendTurn = 0;
          if (!D.JET.ride) return o;
          // both hands on the bars: the engine; the trigger: go
          const frame = (n, f) => { for (let i = 0; i < n; i++) { I.head = head(); for (const s of ['L', 'R']) { const gp = D.jetGripAt(s), h = s === 'L' ? O : M; if (f) f(h, gp, s); } D.geoGearTick(I, M, O, 1 / 30); D.update(1 / 30); D.endlessTick(1 / 30); } };
          frame(2, (h, gp) => { h.pos.copy(gp); h.grip = 1; }); o.eng = D.JET.ride.eng; o.sitY = +(P.y + 1.6 - D.water).toFixed(2);
          // turn it to face out to sea first (as it's parked), throttle for 4 s
          const Rd = D.JET.ride, x0 = J.x, z0 = J.z, ys = new Set(), hy = new Set();
          frame(120, (h, gp) => { h.pos.copy(gp); h.grip = 1; h.trig = 1; }); frame(1, (h, gp) => { ys.add(+J.obj.position.y.toFixed(3)); hy.add(+P.y.toFixed(4)); });
          for (let i = 0; i < 30; i++) frame(1, (h, gp) => { h.pos.copy(gp); h.grip = 1; h.trig = 1; ys.add(+J.obj.position.y.toFixed(3)); hy.add(+P.y.toFixed(4)); });
          o.drive = [Math.round(Math.hypot(J.x - x0, J.z - z0)), +Rd.sp.toFixed(1), ys.size > 3, hy.size === 1, +Math.hypot(P.x - J.x, P.z - J.z).toFixed(2)];
          // steer: right hand back
          const y0 = J.yaw; frame(45, (h, gp, s) => { h.pos.copy(gp); if (s === 'R') h.pos.add(new T.Vector3(-Math.sin(J.yaw), 0, -Math.cos(J.yaw)).multiplyScalar(-.15)); h.grip = 1; h.trig = 1; }); o.turn = +(J.yaw - y0).toFixed(2);
          // head back for the beach it came from: it slides up and stops in the shallows
          const b = D.jetFindBeach(x0, z0); J.x = b.x; J.z = b.z; J.yaw = b.yaw + Math.PI; P.x = J.x; P.z = J.z; Rd.sp = 0;
          frame(240, (h, gp) => { h.pos.copy(gp); h.grip = 1; h.trig = 1; }); o.beach = [+Rd.sp.toFixed(1), +(D.H(J.x, J.z) - D.water).toFixed(2), Rd.beachT > 0];
          // let go, point at the sand, trigger: off
          frame(2, (h) => { h.grip = 0; h.trig = 0; }); o.engOff = !Rd.eng;
          const land = new T.Vector3(J.x - Math.sin(J.yaw) * 5, 0, J.z - Math.cos(J.yaw) * 5); land.y = D.groundAt(land.x, land.z);
          M.rayPos.copy(head().add(new T.Vector3(.2, -.4, 0))); aimAt(M, land); frame(1); M.trig = 1; frame(1); M.trig = 0;
          o.off = [!D.JET.ride, +(D.H(P.x, P.z) - D.water).toFixed(2)];
          let mx = 0; const cv = document.createElement('canvas'); cv.width = cv.height = 256; D.GEO.mz = 0; D.geoMapDraw(cv);
          return o; }""")
        print("ride", json.dumps(r))
        ok = g0[1:] == [False, False] and g[0] == 50 and g[1] is True and g[2] is True and r.get("dry") is False and "J" in r.get("placed", "") and r["where"][0] < -.3 and r["where"][1] \
             and r["glow"] and r["on"] and r["eng"] and 1.4 < r["sitY"] < 1.7 and r["drive"][0] > 25 and r["drive"][1] > 12 and r["drive"][2] and r["drive"][3] and r["drive"][4] < 1.2 \
             and r["turn"] < -.3 and r["beach"][0] < .5 and -1 < r["beach"][1] < .5 and r["beach"][2] and r["engOff"] and r["off"][0] and r["off"][1] > 0
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
