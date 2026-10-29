"""3.13: the wakeboard boat (find 58, online Treeocashing): moored off sea beaches; point at one (it glows) and pull the trigger to stand
on its deck; walk about the deck while it moves (you ride along, your eyes never bob); a hand on the wheel drives: the trigger is the
throttle, turning the wheel steers; online, the boat goes out as points on the planet and whoever's aboard as a place on its deck (so
they're drawn on the boat exactly); let go, point over the side, trigger: off.
Usage: python3 dev/test_313.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
GEN = """(found) => { window.FREEZE = true; D.renderer.setAnimationLoop(null); try { localStorage.setItem('jt-geochar', JSON.stringify({ n: found, score: 0, kills: 0 })); } catch (_) {}
  D.DEV.ok = true; D.setSeed(4242); D.setVR(true); D.setMode('hunt'); D.vr.on = true; D.set.hand = 'right';
  Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .5, rough: .5, huntMap: 'globe', dino: false });
  D.MP.code = '9999'; D.set.geoNet = true; D.generate(); D.state = 'play'; window.tick = n => { for (let i = 0; i < n; i++) { D.endlessTick(1 / 30); D.geoTick(1 / 30); } };
  const T = D.THREE; window.hand = (pos, o) => Object.assign({ pos: pos.clone(), rayPos: pos.clone(), rayQ: new T.Quaternion(), q: new T.Quaternion(), grip: 0, trig: 0, sx: 0, sy: 0, a: 0, b: 0, stickBtn: 0 }, o || {});
  window.aimAt = (h, p) => { h.rayQ.setFromUnitVectors(new T.Vector3(0, 0, -1), p.clone().sub(h.rayPos).normalize()); };
  return [D.GEO.found.size, D.BOAT.list.length, D.boatOn(), D.geoRewardOf(58).boat || null]; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        g0 = await pg.evaluate(GEN, 57); print("at57", g0)
        g = await pg.evaluate(GEN, 58); print("at58", g)
        r = await pg.evaluate("""() => { const o = {}, T = D.THREE, P = D.P, L0 = D.BOAT.list; let B = null;
          for (const bb of L0) { D.geoTeleport(bb.p); tick(90); D.GEO.tT = 0; tick(2); D.boatsFrame(1 / 30); if (bb.obj && !bb.dead) { B = bb; break; } }
          o.placed = L0.map(q => q.dead ? 'x' : q.obj ? 'B' : '-').join(''); if (!B) return o;
          o.depth = +(D.H(B.x, B.z) - D.water).toFixed(2);
          const head = () => new T.Vector3(P.x, P.y + 1.6, P.z); P.x = B.x + 9; P.z = B.z; P.y = D.water - .9; D.vr.headLocalY = 1.6;
          let I = { head: head(), headQ: new T.Quaternion(), hands: {} }, M = hand(head().add(new T.Vector3(.2, -.4, 0))), O = hand(head().add(new T.Vector3(-.2, -.4, 0))); I.hands.right = M; I.hands.left = O; D.vr.I = I;
          aimAt(M, new T.Vector3(B.x, D.water + .8, B.z)); D.geoGearTick(I, M, O, 1 / 30); o.glow = B.obj.userData.mats[0].emissive.getHex() > 0;
          M.trig = 1; D.geoGearTick(I, M, O, 1 / 30); M.trig = 0; o.on = D.BOAT.on === B; D.vr.pendTurn = 0; if (!o.on) return o;
          const local = () => { const l = new T.Vector3(P.x, D.water, P.z).applyMatrix4(B.mi); return [+l.x.toFixed(2), +l.z.toFixed(2)]; };
          const frame = (n, f) => { for (let i = 0; i < n; i++) { I.head = head(); if (f) f(); D.geoGearTick(I, M, O, 1 / 30); D.update(1 / 30); D.endlessTick(1 / 30); } };
          // walk to the front of the deck: you stop at the edge
          D.input.jy = 1; P.yaw = B.yaw; frame(120); D.input.jy = 0; o.walk = local();
          // a hand on the wheel, throttle
          const rim = a => B.obj.userData.wb.localToWorld(new T.Vector3(Math.cos(a) * .19, Math.sin(a) * .19, 0));
          const x0 = B.x, z0 = B.z, ys = new Set(), py = new Set(), l0 = local(); let ang = 0;
          frame(150, () => { M.pos.copy(rim(ang)); M.grip = 1; M.trig = 1; ys.add(+B.obj.position.y.toFixed(3)); py.add(+P.y.toFixed(4)); });
          o.drive = [D.BOAT.drive === B, Math.round(Math.hypot(B.x - x0, B.z - z0)), +B.sp.toFixed(1), ys.size > 3, py.size === 1, JSON.stringify(local()) === JSON.stringify(l0)];
          // turn the wheel clockwise (seen from the driver): it goes right
          const y0 = B.yaw; frame(60, () => { ang -= .04; M.pos.copy(rim(ang)); M.grip = 1; M.trig = 1; }); o.turn = [+B.w.toFixed(2), +(B.yaw - y0).toFixed(2)];
          // online: what I send while aboard, and someone else on the deck drawn on my boat
          const np = D.boatNetPose(I, null); o.net = [np.bd === B.id, Math.abs(np.bl.h[1] - (1.6 + .55)) < .05];
          const s = { bd: B.id, bl: { h: { p: new T.Vector3(.3, 2.1, 1.5), q: new T.Quaternion() }, l: null, r: null, g: null, f: 0 }, h: { p: new T.Vector3(), q: new T.Quaternion() }, l: null, r: null, g: null, feet: 0 };
          D.boatRemotePose(s); const back = s.h.p.clone().applyMatrix4(B.mi); o.remote = [+back.x.toFixed(2), +back.z.toFixed(2), +(s.feet - D.water).toFixed(2)];
          // let go: someone else's boat moves when they send it
          frame(2, () => { M.grip = 0; M.trig = 0; }); o.letGo = D.BOAT.drive === null;
          const q2 = D.glToSphere(B.x + 30, B.z, [0, 0, 0]), f2 = D.glToSphere(B.x + 30, B.z - 10, [0, 0, 0]);
          D.boatNetIn({ id: 'zz-other' }, { t: 'bt', id: B.id, p: q2, f: f2, sp: 5, st: 0, w: 0, d: 1 }); window.FAKE = performance.now();
          await_ = null; const t0 = performance.now(); while (performance.now() - t0 < 160) {} frame(2); o.theirs = [Math.round(B.x - (q2 ? D.glFromSphere(q2, [0, 0])[0] : 0)), B.drv === 'zz-other', +Math.hypot(...(() => { const l = new T.Vector3(P.x, D.water, P.z).applyMatrix4(B.mi); return [l.x, l.z]; })()).toFixed(1) < 4];
          // off: point over the side at the water, trigger
          const side = new T.Vector3(1, 0, 0).applyQuaternion(B.q).multiplyScalar(6).add(new T.Vector3(B.x, D.water, B.z));
          M.rayPos.copy(head().add(new T.Vector3(.2, -.4, 0))); aimAt(M, side); frame(1); M.trig = 1; frame(1); M.trig = 0; o.off = D.BOAT.on === null;
          const cv = document.createElement('canvas'); cv.width = cv.height = 256; D.GEO.mz = 0; D.geoMapDraw(cv);
          return o; }""".replace("await_ = null;", ""))
        print("boat", json.dumps(r))
        ok = g0[2] is False and g[0] == 58 and g[1] >= 4 and g[2] is True and g[3] == "wake" and "B" in r.get("placed", "") and r["depth"] < -1.3 \
             and r["glow"] and r["on"] and r["walk"][1] < -2.5 and abs(r["walk"][0]) < 1.01 \
             and r["drive"][0] and r["drive"][1] > 25 and r["drive"][2] > 8 and r["drive"][3] and r["drive"][4] and r["drive"][5] \
             and r["turn"][0] < -.5 and r["turn"][1] < -.2 and r["net"] == [True, True] and r["remote"] == [.3, 1.5, .55] and r["letGo"] \
             and r["theirs"][1] and r["theirs"][2] and r["off"]
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
