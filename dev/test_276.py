"""2.76: the sea and lakes are back (a comment had hidden the water since 2.70); Geocaching: a new planet every game, your level and score
carried on your character; the map stick toggles map/globe (the globe upright, spinning); the canteen shows its water and you chug it;
dying wakes you 4+ km away; the always-on meter (Hunting/Geocaching); PvP: a fallen player leaves a green-and-blue refill, guns come back.
Usage: python3 dev/test_276.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
GEN = """(a) => { window.FREEZE = true; D.renderer.setAnimationLoop(null); try { localStorage.removeItem('jt-geo'); if (a.n !== undefined) localStorage.setItem('jt-geochar', JSON.stringify({ n: a.n, score: a.score || 0, kills: 0 })); else localStorage.removeItem('jt-geochar'); } catch (_) {}
  D.DEV.ok = true; D.setSeed(a.seed || 4242); D.setVR(true); D.setMode(a.mode || 'hunt'); D.vr.on = true; D.set.hand = 'right';
  Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .5, rough: .5, huntMap: a.map || 'globe', dino: false, size: 'small' });
  D.generate(); D.state = 'play'; window.tick = n => { for (let i = 0; i < n; i++) { D.endlessTick(1 / 30); if (D.GEO.on) D.geoTick(1 / 30); } };
  const T = D.THREE; window.hand = (pos, o) => Object.assign({ pos: pos.clone(), rayPos: pos.clone(), rayQ: new T.Quaternion(), q: new T.Quaternion(), grip: 0, trig: 0, sx: 0, sy: 0, a: 0, b: 0, stickBtn: 0 }, o || {});
  return true; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        await pg.evaluate(GEN, {"n": 12, "score": 300})
        g = await pg.evaluate("""() => { const o = {}, T = D.THREE, P = D.P; tick(30);
          o.water = !!(D.ENDLESS.water && D.ENDLESS.water.parent);
          o.level = [D.GEO.found.size, Math.round(D.hunt.score), D.GEO.items.size];
          o.next = Math.round(Math.min(...D.GEO.caches.filter(c => !D.GEO.found.has(c.id)).map(c => D.glArc(D.GLOBE.p, c.p))) * D.GLOBE.R);
          // the map: push the stick, the globe (upright); push again, the map
          const I = { head: new T.Vector3(P.x, P.y + 1.7, P.z), headQ: new T.Quaternion(), hands: {} }, m = hand(new T.Vector3(P.x + .2, P.y + 1.3, P.z - .3));
          D.vrHudParts2(); D.vrMap.position.set(P.x - .2, P.y + 1.4, P.z - .4);
          D.geoMapTick(I, m, 1 / 30); m.sy = -1; D.geoMapTick(I, m, 1 / 30); m.sy = 0; for (let i = 0; i < 30; i++) D.geoMapTick(I, m, 1 / 30);
          const Gm = D.geoGlobe(); const up = new T.Vector3(0, 1, 0).applyQuaternion(Gm.userData.inner.getWorldQuaternion(new T.Quaternion()));
          o.globe = [D.GEO.glOn, +D.GEO.mz.toFixed(2), Gm.visible, +up.y.toFixed(3)];
          m.sy = 1; D.geoMapTick(I, m, 1 / 30); m.sy = 0; D.geoMapTick(I, m, 1 / 30); o.back = [D.GEO.glOn, D.GEO.mz, Gm.visible];
          // the canteen: its water shows, and you chug it
          D.geoGearApply(12, true); D.geoHeld('canteen'); D.GEO.cant = 2; const cw = hand(new T.Vector3(P.x + .2, P.y + 1.2, P.z - .3)); D.geoHeldTick(I, cw, 1 / 30);
          o.cantShow = +D.GEO.heldObj.userData.water.scale.y.toFixed(2);
          D.GEO.water = 40; const mouth = hand(I.head.clone().add(new T.Vector3(0, -.06, -.12))); mouth.rayQ.setFromAxisAngle(new T.Vector3(1, 0, 0), .9);
          for (let i = 0; i < 30; i++) D.geoHeldTick(I, mouth, 1 / 30); o.chug = [Math.round(D.GEO.water - 40), +D.GEO.cant.toFixed(2)]; D.geoHeld(null);
          // the meter, low in view
          D.pvpHud(I, 1 / 30); o.hud = D.VHUD.m.visible;
          // after #50: no banners
          D.VBAN.t = 0; D.geoReward(52); o.quiet = !(D.VBAN.t > 0);
          // a death: you wake at least 4 km away
          const p0 = D.GLOBE.p.slice(); D.geoRespawn(); o.away = Math.round(D.glArc(p0, D.GLOBE.p) * D.GLOBE.R);
          D.geoSave(); o.saved = JSON.parse(localStorage.getItem('jt-geochar')).n;
          return o; }""")
        print("geo", json.dumps(g))
        await pg.evaluate("""() => { D.setSeed(999); D.generate(); D.state = 'play'; }""")
        g2 = await pg.evaluate("""() => [D.GEO.found.size, D.seed]""")
        print("next game", g2)
        await pg.evaluate(GEN, {"mode": "pvp", "map": "island"})
        v = await pg.evaluate("""() => { const o = {}; o.water = !!(D.ENDLESS ? D.ENDLESS.water.parent : true);
          D.dropDead('ddX_1', D.P.x + 3, D.P.y, D.P.z); const d = D.DROPS.get('ddX_1'); o.hs = !!d && d.type;
          D.MP.hp = 20; D.MP.sh = 0; o.use = D.dropUse(d); o.full = [D.MP.hp, D.MP.sh]; D.dropTake('ddX_1'); o.hsGone = !D.DROPS.has('ddX_1');
          const gd = [...D.DROPS.values()].find(q => q.type === 'gun'); const was = gd.kind + gd.tier; D.dropTake(gd.id); o.gunHidden = [D.DROPS.has(gd.id), gd.got];
          const I = { head: new D.THREE.Vector3(9999, 0, 9999), headQ: new D.THREE.Quaternion(), hands: {} }; for (let i = 0; i < 50; i++) D.dropsTick(I, 1); o.gunBack = [gd.got, gd.gen, !!gd.obj];
          return o; }""")
        print("pvp", json.dumps(v))
        ok = g["water"] and g["level"][:2] == [12, 300] and g["level"][2] == 6 and g["next"] < 800 and g["globe"][0] and g["globe"][1] == 1 and g["globe"][2] and g["globe"][3] > .99 \
             and g["back"] == [False, 0, False] and g["cantShow"] == .5 and 8 <= g["chug"][0] <= 12 and 1.5 < g["chug"][1] < 1.7 and g["hud"] and g["quiet"] and g["away"] >= 4000 and g["saved"] == 12 \
             and g2 == [12, 999] and v["water"] and v["hs"] == "hs" and v["use"] and v["full"] == [100, 100] and v["hsGone"] and v["gunHidden"] == [True, True] and v["gunBack"] == [False, 1, True]
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
