"""3.48: levels past 50 and the boat. Prizes: 50 jet ski, 51 dirt bike, 54 snowmobile, 57 dune buggy (glasses between), 60 the boat, 62-70
a gold 6th star for each gun; after that levels still count (refills). The planet starts with 150 caches and makes more when few are left.
The boat: taken out wading in the sea; driving it (both hands on the wheel, trigger) moves it and you with it, leaving a wake; water
skiing behind your own boat (it drives itself): the rope holds you behind it, looking right carves right, crouch-then-stand pops you up,
letting go drops you in. Usage: python3 dev/test_348.py dbg.html"""
import os, sys, asyncio, json, re
from playwright.async_api import async_playwright
here = os.path.dirname(os.path.abspath(__file__))
GEN = re.search(r'GEN = """(.*?)"""', open(os.path.join(here, "test_275.py")).read(), re.S).group(1)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 400, "height": 260})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        await pg.evaluate(GEN, 60)
        r = await pg.evaluate("""() => { const o = {}, T = D.THREE, P = D.P, G = D.GLOBE;
          const rw = n => { const r = D.geoRewardOf(n); return r.item || (r.gun ? r.gun + r.star : 'refill'); };
          o.prizes = [50, 51, 52, 54, 57, 59, 60, 61, 62, 70, 71, 99].map(rw);
          D.DEV.ok = false; const g50 = D.geoGearFromCount(50), g60 = D.geoGearFromCount(60), g70 = D.geoGearFromCount(70); D.DEV.ok = true;
          o.gear = [g50.items.has('jetski'), g50.items.has('dirtbike'), g60.items.has('boat'), g60.items.has('buggy'), Object.values(g70.own).every(v => v === 6) && Object.keys(g70.own).length === 5];
          o.tier6 = [D.TIER.mag.length, D.TIER.dmg[6]];
          o.caches = D.GEO.caches.length; D.GEO.found = new Set(Array.from({ length: 140 }, (_, i) => i + 1)); D.geoMore(); o.more = D.GEO.caches.length; D.GEO.found = new Set(Array.from({ length: 60 }, (_, i) => i + 1));
          o.boatItem = [D.GEO.items.has('boat'), D.geoPackItems().includes('boat'), D.geoPackItems().length, D.geoSlots()];
          // into the sea
          let spot = null, bestY = 0; const run = (x, z, yy) => { let d = 6; while (d < 220 && D.H(x - Math.sin(yy) * d, z - Math.cos(yy) * d) < D.water - 2.5) d += 6; return d; };
          for (let k = 0; k < 20000 && !spot; k++) { const a = k * 2.4, rr = 20 + k * 1.5, x = P.x + Math.cos(a) * rr, z = P.z + Math.sin(a) * rr, h = D.H(x, z);
            if (h < D.water - .4 && h > D.water - 1.3 && D.geoSalty({ x, z })) for (let i = 0; i < 16; i++) { const yy = i / 16 * 6.283; if (run(x, z, yy) >= 200) { spot = [x, z]; bestY = yy; break; } } }
          o.spot = !!spot; if (!spot) return o;
          P.x = spot[0]; P.z = spot[1]; P.y = D.water - .8; P.yaw = bestY;
          o.out = D.btTakeOut(); const V = D.BT.me; o.placed = !!(V && V.obj);
          D.btDrive(); o.driving = !!D.BT.ride;
          const head = new T.Vector3(), hq = new T.Quaternion(), L = hand(new T.Vector3()), R = hand(new T.Vector3()), I = { head, headQ: hq, hands: { left: L, right: R } }; D.vr.I = I;
          const wheel = () => { const w = V.obj.userData.wheel; w.updateMatrixWorld(true); L.pos.copy(w.localToWorld(new T.Vector3(-.18, 0, 0))); R.pos.copy(w.localToWorld(new T.Vector3(.18, 0, 0))); head.set(P.x, P.y + 1.6, P.z); };
          wheel(); L.grip = R.grip = 1; D.btHandsTick(I, R); o.engine = D.BT.ride.eng; R.trig = 1;
          const x0 = V.x, z0 = V.z; for (let i = 0; i < 150; i++) { wheel(); D.btHandsTick(I, R); D.btRide(1 / 30); D.btTick(1 / 30); }
          o.drove = [+Math.hypot(V.x - x0, V.z - z0).toFixed(1), +V.sp.toFixed(1), +Math.hypot(P.x - V.x, P.z - V.z).toFixed(2)];
          o.wake = D.BT.wakes.get('me').pts.length > 10 && D.BT.wakes.get('me').m.visible;
          o.wakeH = +D.btWakeH(V, V.sp, V.x + Math.sin(V.yaw) * 20 + Math.cos(V.yaw) * (0.9 + 17.4 * .36), V.z + Math.cos(V.yaw) * 20 - Math.sin(V.yaw) * (0.9 + 17.4 * .36)).toFixed(2);
          // ski behind your own boat: it drives itself
          R.trig = 0; L.grip = R.grip = 0; D.btOffBoat(V.x + 6, V.z); D.btSkiStart('me'); o.ski = !!D.BT.ski; R.grip = 1;
          const S = D.BT.ski, step = n => { for (let i = 0; i < n; i++) { D.btHandsTick(I, R); D.btTick(1 / 30); D.btRide(1 / 30); L.pos.set(P.x - .2, P.y + 1.1, P.z); R.pos.set(P.x + .2, P.y + 1.1, P.z); } };
          D.vr.headLocalY = 1.6; hq.setFromEuler(new T.Euler(0, V.yaw, 0)); step(150);
          const rope = () => { const Tw = V.obj.localToWorld(new T.Vector3(0, 1.45, 1.55)); return +Math.hypot(S.x - Tw.x, S.z - Tw.z).toFixed(1); };
          o.towed = [+V.sp.toFixed(1), rope(), V.auto];
          const lat = () => { const rx = Math.cos(V.yaw), rz = -Math.sin(V.yaw); return (S.x - V.x) * rx + (S.z - V.z) * rz; };
          hq.setFromEuler(new T.Euler(0, V.yaw - .9, 0)); step(60); const latR = lat(); hq.setFromEuler(new T.Euler(0, V.yaw + .9, 0)); step(90); const latL = lat(); hq.setFromEuler(new T.Euler(0, V.yaw, 0));
          o.carve = [+latR.toFixed(1), +latL.toFixed(1)];
          // crouch, then stand up fast: pop
          let air = false; for (let i = 0; i < 10; i++) { D.vr.headLocalY = 1.6 - .04 * i; step(1); } for (let i = 0; i < 6; i++) { D.vr.headLocalY = 1.25 + .07 * i; step(1); if (S.air) air = true; }
          let landed = false; for (let i = 0; i < 90; i++) { step(1); if (S.air) air = true; else if (air) landed = true; } o.jump = [air, landed, !!D.BT.ski];
          // let go: in the water
          R.grip = 0; step(20); o.letGo = !D.BT.ski;
          D.btClear(); o.cleared = !D.BT.me && !D.BT.ride;
          return o; }""")
        print(json.dumps(r))
        ok = r["prizes"] == ["jetski", "dirtbike", "bblock", "snowmobile", "buggy", "fglass", "boat", "refill", "pistol6", "hunt6", "refill", "refill"] \
             and r["gear"] == [True, False, True, True, True] and r["tier6"][0] == 7 and r["caches"] >= 150 and r["more"] >= 170 and r["boatItem"][0] and r["boatItem"][1] and r["boatItem"][3] == 24 \
             and r.get("spot") and r["out"] and r["placed"] and r["driving"] and r["engine"] and r["drove"][0] > 40 and r["drove"][1] > 12 and r["drove"][2] < 2.5 and r["wake"] and r["wakeH"] > .1 \
             and r["ski"] and r["towed"][0] > 9 and 14 < r["towed"][1] <= 16.1 and r["towed"][2] and r["carve"][0] > 2 and r["carve"][1] < -2 and r["jump"][0] and r["jump"][1] and r["letGo"] and r["cleared"]
        print("PASS" if ok and not errs else "FAIL", errs[:5]); print("errors: none" if not errs else "errors: " + str(errs[:5])); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
