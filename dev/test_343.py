"""3.43 (live since 3.44, they come with the jet ski at cache #50): the land vehicles, a dirt bike, a snowmobile and a dune buggy, working like the jet ski. In the pack (Dev); taken out
on dry land it's in front of you; climb on, grab both grips (the engine starts), trigger: throttle; you ride along with it on the ground;
a tree stops it; pulling the bars up hard pops the bike into the air; thumbstick back reverses; the snowmobile crawls off snow; hands off
and point at the ground to hop off. Others see what you ride (lv). Usage: python3 dev/test_343.py dbg.html"""
import os, sys, asyncio, json, re
from playwright.async_api import async_playwright
here = os.path.dirname(os.path.abspath(__file__))
GEN = re.search(r'GEN = """(.*?)"""', open(os.path.join(here, "test_275.py")).read(), re.S).group(1)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        await pg.evaluate(GEN, 10)
        r = await pg.evaluate("""() => { const o = {}, T = D.THREE, P = D.P, LV = D.LV;
          o.items = D.LV_KINDS.map(k => D.GEO.items.has(k)); { D.DEV.ok = false; const g10 = D.geoGearFromCount(10).items, g50 = D.geoGearFromCount(57).items;   /* (3.48: the vehicles come at 51, 54 and 57) */ o.live = [D.LV_KINDS.some(k => g10.has(k)), D.LV_KINDS.every(k => g50.has(k)), g50.has('jetski')]; D.DEV.ok = true; }   /* (3.44: live, with the jet ski at #50) */ o.pack = D.LV_KINDS.map(k => D.geoPackItems().includes(k));
          // a clear, flat, dry spot with room in front
          tick(40); let spot = null, seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
          for (let k = 0; k < 4000 && !spot; k++) { const x = P.x + (rnd() - .5) * 500, z = P.z + (rnd() - .5) * 500;
            if (D.H(x, z) > D.water + 2 && D.slopeNy(x, z) > .97) { let ok = true; for (let d = 0; d <= 40 && ok; d += 2) { const px = x, pz = z - d; if (D.H(px, pz) < D.water + 1 || D.slopeNy(px, pz) < .93 || D.lvBlocked(px, pz, D.H(px, pz))) ok = false; } if (ok) spot = [x, z]; } }
          o.spot = !!spot; if (!spot) return o;
          P.x = spot[0]; P.z = spot[1]; P.yaw = 0; P.y = D.H(P.x, P.z); tick(5);
          o.out = D.lvTakeOut('dirtbike'); const V = LV.list[0]; o.placed = [!!V && !!V.obj, V && +Math.hypot(V.x - P.x, V.z - P.z).toFixed(1)];
          // aim at it and climb on
          const head = new T.Vector3(P.x, P.y + 1.6, P.z), main = hand(new T.Vector3(P.x + .2, P.y + 1.2, P.z - .3)), offH = hand(new T.Vector3(P.x - .2, P.y + 1.2, P.z - .3));
          const I = { head, headQ: new T.Quaternion(), hands: { right: main, left: offH } }; D.vr.I = I;
          aimAt(main, new T.Vector3(V.x, V.obj.position.y + .6, V.z)); D.lvAimTick(I, main, offH); o.glow = LV.aim === V; main.trig = 1; D.lvAimTick(I, main, offH); main.trig = 0;
          o.mounted = !!LV.ride && LV.ride.V === V;
          const Rd = LV.ride, grips = () => { const gl = D.lvGripAt('L'), gr = D.lvGripAt('R'); offH.pos.copy(gl); main.pos.copy(gr); offH.rayPos.copy(gl); main.rayPos.copy(gr); head.set(P.x, P.y + D.vr.headLocalY, P.z); };
          grips(); offH.grip = main.grip = 1; D.lvHandsTick(I, main); o.engine = [Rd.grab.L, Rd.grab.R, Rd.eng];
          // full throttle, straight ahead
          const x0 = V.x, z0 = V.z; main.trig = 1;
          for (let i = 0; i < 150; i++) { grips(); D.lvHandsTick(I, main); D.lvRide(1 / 30); D.endlessTick(1 / 30); }
          o.moved = +Math.hypot(V.x - x0, V.z - z0).toFixed(1); o.speed = +Rd.sp.toFixed(1); o.withIt = +Math.hypot(P.x - V.x, P.z - V.z).toFixed(2);
          o.onGround = +Math.abs(V.obj.position.y - D.lvG(V.x, V.z)).toFixed(2); o.eye = +(P.y + D.vr.headLocalY - D.lvG(V.x, V.z)).toFixed(2);
          // pull the bars up hard: a hop
          let air = false; Rd.hopT = 0; for (let i = 0; i < 6; i++) { grips(); offH.pos.y += .06 * i; main.pos.y += .06 * i; D.lvRide(1 / 30); if (Rd.air) air = true; }
          let landed = false; for (let i = 0; i < 240; i++) { grips(); D.lvRide(1 / 30); if (Rd.air) air = true; else if (air) landed = true; } o.hop = air; o.landed = landed;
          // thumbstick back: reverse
          main.trig = 0; main.sy = 1; for (let i = 0; i < 90; i++) { grips(); D.lvRide(1 / 30); } o.reverse = +Rd.sp.toFixed(1); main.sy = 0;
          for (let i = 0; i < 60; i++) { grips(); D.lvRide(1 / 30); }
          // a tree in the way stops it
          let tree = null; for (const list of D.obstacles.values()) { for (const t of list) if (t.tr !== undefined && Math.hypot(t.x - P.x, t.z - P.z) < 400 && D.H(t.x, t.z) > D.water + 1 && D.slopeNy(t.x, t.z) > .9) { tree = t; break; } if (tree) break; }
          if (tree) { const ox = V.x, oz = V.z; V.x = tree.x; V.z = tree.z + 8; V.yaw = 0; Rd.hy = undefined; P.x += V.x - ox; P.z += V.z - oz; main.trig = 1;
            let minD = 99; for (let i = 0; i < 120; i++) { grips(); D.lvRide(1 / 30); minD = Math.min(minD, Math.hypot(V.x - tree.x, V.z - tree.z)); } o.tree = +minD.toFixed(2); main.trig = 0; }
          // the others see it
          const pk = [D.LV_KINDS.indexOf(V.kind)].concat(D.pose7(V.obj.position, V.obj.quaternion)); o.net = pk.length === 8 && pk[0] === 0;
          // hop off: hands off, point at the ground
          offH.grip = main.grip = 0; D.lvHandsTick(I, main); const tgt = new T.Vector3(P.x + 2.5, D.H(P.x + 2.5, P.z), P.z); main.rayPos.set(P.x, P.y + 1.4, P.z); aimAt(main, tgt);
          D.lvHandsTick(I, main); o.ring = !!(LV.ring && LV.ring.visible); main.trig = 1; D.lvHandsTick(I, main); main.trig = 0; o.off = !LV.ride && Math.hypot(P.x - tgt.x, P.z - tgt.z) < 1;
          // the snowmobile, off snow: slow
          P.x = spot[0]; P.z = spot[1]; P.y = D.H(P.x, P.z); o.sled = D.lvTakeOut('snowmobile'); const S = LV.list.find(q => q.kind === 'snowmobile'); D.lvMount(S); const R2 = LV.ride; grips(); offH.grip = main.grip = 1; D.lvHandsTick(I, main); main.trig = 1;
          for (let i = 0; i < 120; i++) { grips(); D.lvRide(1 / 30); } o.sledSlow = +R2.sp.toFixed(1); main.trig = 0; offH.grip = main.grip = 0; D.lvOff();
          o.buggy = D.lvTakeOut('buggy'); const Bg = LV.list.find(q => q.kind === 'buggy'); D.lvMount(Bg); grips(); offH.grip = main.grip = 1; D.lvHandsTick(I, main); o.buggyEng = LV.ride.eng; D.lvOff();
          o.count = LV.list.length; D.lvClear(); o.cleared = LV.list.length === 0;
          return o; }""")
        print(json.dumps(r))
        ok = r.get("spot") and r["items"] == [True] * 3 and r["live"] == [False, True, True] and r["pack"] == [True] * 3 and r["out"] and r["placed"][0] and 1.5 < r["placed"][1] < 3 and r["glow"] and r["mounted"] \
             and r["engine"] == [True, True, True] and r["moved"] > 40 and r["speed"] > 15 and r["withIt"] < 1.5 and r["onGround"] < .3 and 1.1 < r["eye"] < 1.7 \
             and r["hop"] and r["landed"] and r["reverse"] < -1.5 and (r.get("tree") is None or r["tree"] > .5) and r["net"] and r["off"] \
             and r["sled"] and r["sledSlow"] < 9 and r["buggy"] and r["buggyEng"] and r["count"] == 3 and r["cleared"]
        print("PASS" if ok and not errs else "FAIL", errs[:5]); print("errors: none" if not errs else "errors: " + str(errs[:5])); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
