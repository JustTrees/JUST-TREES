"""2.70: Geocaching on a little globe (headset, solo). The planet is 50 km round: walk north and the latitude rises (~139 m a degree),
the climates follow the latitude, a walk round a square comes back to the same numbers (to a metre or so: a square on a ball doesn't quite close), crossing the North Pole flips the longitude like
real GPS, and the local time follows your longitude (an hour every ~2.08 km east). Every 1.5 km the flat patch is laid again where you
stand (the ground under your feet doesn't move) and the squares round you are rebuilt. 100 caches round the planet in every climate band;
walk up to one to find it (+25, saved). A kill leaves food; health runs down as you travel and food brings it back; the red-gun tools
need full health here. Progress is saved and a new game goes on from it. Far land curves away; ordinary maps don't.
Usage: python3 dev/test_270.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
QUICK = __import__('os').environ.get('JT_QUICK') == '1'
GEN = """(sv) => { window.FREEZE = true; D.renderer.setAnimationLoop(null); try { if (sv) localStorage.setItem('jt-geo', JSON.stringify(sv)); else localStorage.removeItem('jt-geo'); } catch (_) {}
  D.DEV.ok = true; D.setSeed(4242); D.setVR(true); D.setMode('hunt'); D.vr.on = true;   // (2.72: Geocaching is in Dev Mode while it's tested)
  Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .5, rough: .5, huntMap: 'globe', dino: false });
  D.generate(); D.state = 'play'; window.tick = (n, f) => { for (let i = 0; i < n; i++) { if (f) f(i); D.endlessTick(1 / 72); D.updateAnimals(1 / 72); D.geoTick(1 / 72); } };
  return { on: !!D.GLOBE, lat: D.GLOBE && D.GLOBE.lat, lon: D.GLOBE && D.GLOBE.lon }; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        o = await pg.evaluate(GEN, None)
        r = await pg.evaluate("""(Q) => { const o = {}, G = D.GLOBE, E = D.ENDLESS;
          o.caches = D.GEO.caches.length; const bands = new Set(D.GEO.caches.map(c => { const l = Math.abs(c.lat); return l < 9 ? 0 : l < 18 ? 1 : l < 33 ? 2 : l < 50 ? 3 : l < 63 ? 4 : l < 75 ? 5 : 6; })); o.bands = bands.size;
          o.minGap = Math.round(Math.min(...D.GEO.caches.flatMap((a, i) => D.GEO.caches.slice(i + 1).map(c => D.glArc(a.p, c.p) * G.R))));
          o.curve = D.CURVE.x > 0; o.wheel = D.wheelKeys().includes('gps');
          tick(72); o.lat0 = G.lat;
          // walk north: the latitude rises ~1 degree per 139 m; the patch is laid again every 1.5 km, and the ground at your feet stays put
          const n0 = G.reN || 0, jumps = []; let re = n0;
          const dist = Q ? 1700 : 2400; for (let z0 = D.P.z, f = 0; D.P.z > z0 - dist; f++) { D.P.z -= 20 / 72; D.P.y = D.H(D.P.x, D.P.z); tick(1); if (G.reN !== re) { re = G.reN; jumps.push(+(D.H(D.P.x, D.P.z) - D.P.y).toFixed(3)); } }
          tick(1); o.walkLat = +(G.lat - o.lat0).toFixed(2); o.walkExpect = +(dist / (2 * Math.PI * G.R) * 360).toFixed(2); o.reanchors = re - n0; o.jumps = jumps; o.biome = E.here && E.here.b;
          const nearStale = () => [...E.chunks.values()].filter(c => c.stale && Math.hypot(c.x0 + 100 - D.P.x, c.z0 + 100 - D.P.z) < 1300).length; let k = 0; while (k < 72 * 90 && nearStale()) { tick(1); k++; } o.rebuiltIn = +(k / 72).toFixed(1); o.stale = nearStale();
          // round a square: back to the same numbers
          const s0 = [G.lat, G.lon], leg = 400, step = (dx, dz) => { for (let i = 0; i < leg / 4; i++) { D.P.x += dx * 4; D.P.z += dz * 4; D.P.y = D.H(D.P.x, D.P.z); tick(1); } };
          step(1, 0); step(0, 1); step(-1, 0); step(0, -1); tick(20); o.squareBack = [+(G.lat - s0[0]).toFixed(5), +(G.lon - s0[1]).toFixed(5)];
          // the local time follows longitude: an hour per 1/24 of the way round (along the parallel here)
          const h0 = D.hourNow, u0 = G.utc, lon0 = G.lon; for (let i = 0; i < 250; i++) { D.P.x += G.Ef[0] * 4; D.P.z += G.Ef[1] * 4; D.P.y = D.H(D.P.x, D.P.z); tick(1); }
          o.east = [+(G.lon - lon0).toFixed(3), +(((D.hourNow - h0 - (G.utc - u0)) + 36) % 24 - 12).toFixed(3)];
          o.sun = (() => { const sp = D.sunPos(0, 6, 12); return +sp.el.toFixed(1); })();
          return o; }""", QUICK)
        print("globe", json.dumps(r))
        # the North Pole: walk across it
        pp = await pg.evaluate("""() => { const G = D.GLOBE, R = G.R; for (let lat = 89.6; lat > 85; lat -= .2) for (let lon = -180; lon < 180; lon += 10) { const p = D.glFromLL(lat, lon); if (G.contS(p, p[0] * R, p[1] * R, p[2] * R) > .12 && G.landAt(p) > 1.5) return [lat, lon]; } return [89.6, 30]; }""")
        await pg.evaluate(GEN, {"seed": 4242, "lat": pp[0], "lon": pp[1]})
        pole = await pg.evaluate("""() => { const G = D.GLOBE, o = { start: [+G.lat.toFixed(2), +G.lon.toFixed(1)] }; tick(10);
          let maxLat = -90; const N = G.Nf.slice(); for (let i = 0; i < 260; i++) { D.P.x += N[0] * 4; D.P.z += N[1] * 4; D.P.y = D.H(D.P.x, D.P.z); tick(1); maxLat = Math.max(maxLat, G.lat); }
          o.maxLat = +maxLat.toFixed(2); o.end = [+G.lat.toFixed(2), +G.lon.toFixed(1)]; o.lonFlip = Math.round(180 - Math.abs(((G.lon - o.start[1]) + 540) % 360 - 180)); o.biome = D.ENDLESS.here && D.ENDLESS.here.b; return o; }""")
        print("pole", pp, json.dumps(pole))
        # caches, food, hunger, tools, saving
        await pg.evaluate(GEN, None)
        g = await pg.evaluate("""() => { const G = D.GLOBE, o = {}; tick(72 * 4);
          const c = D.GEO.caches[0]; c.p = G.p.slice(); c.ok = true; D.GEO.tT = 0; const s0 = D.hunt.score; D.MP.hp = 100; tick(3);
          o.found = [D.GEO.found.has(c.id), D.GEO.found.size, +(D.hunt.score - s0).toFixed(1)];
          let sv = JSON.parse(localStorage.getItem('jt-geo') || 'null'); o.saved = !!sv && sv.found.includes(c.id);
          const A = D.beasts.find(B => !B.dead && !B.ptero && B.ecellB === undefined); o.animal = !!A;
          if (A) { A.x = D.P.x + 1; A.z = D.P.z; D.killAnimal(A, 50); o.food = D.GEO.foods.length; D.GEO.food = 50; tick(3); o.ate = [Math.round(D.GEO.food), D.GEO.foods.length]; }
          D.GEO.food = 90; const h0 = D.GEO.food; for (let i = 0; i < 60; i++) D.geoTick(1); o.hunger = +(h0 - D.GEO.food).toFixed(2);   // (2.72: food is its own bar)
          const V = D.vr; V.own = { hunt: 5, ar: 5, smg: 5, pistol: 5 }; V.nades = 10; D.MP.hp = 80; o.toolsHurt = D.thermalLoaded(); D.MP.hp = 100; o.toolsFull = D.thermalLoaded();
          D.MP.hp = 1; D.GEO.food = 0; D.geoTick(30); o.faint = D.UW.drown > 0 ? 1 : 0; D.uwRespawn(); D.UW.drown = 0; o.faint = o.faint ? Math.round(D.MP.hp) : 0;   // (2.73: you die, then wake somewhere random)
          D.geoSave(); sv = JSON.parse(localStorage.getItem('jt-geo')); o.save = [sv.seed, sv.found.length, +sv.lat.toFixed(3), +sv.lon.toFixed(3)];
          // the GPS on the wheel, the globe on the map
          D.pickGun('gps'); o.gps = D.vr.gpsMode; D.GEO.mz = 1; o.globeMap = (() => { const I = { head: new D.THREE.Vector3(D.P.x, D.P.y + 1.7, D.P.z) }; return true; })();
          return o; }""")
        print("geo", json.dumps(g))
        # a new game on the same planet goes on from the save; an ordinary map has no curve and no globe
        res = await pg.evaluate("""() => { const sv = JSON.parse(localStorage.getItem('jt-geo')); D.setSeed(777); D.generate(); D.state = 'play';
          const o = { seed: D.GLOBE && sv.seed === D.GLOBE.sv.seed, found: D.GEO.found.size, near: Math.round(D.glArc(D.GLOBE.p, D.glFromLL(sv.lat, sv.lon)) * D.GLOBE.R) };
          D.set.huntMap = 'endless'; D.generate(); D.state = 'play'; o.plain = [!!D.GLOBE, D.CURVE.x, D.GEO.on]; return o; }""")
        print("resume", json.dumps(res))
        # 2.71: start this planet over (two taps), or a whole new planet
        rs = await pg.evaluate("""() => { const o = {}; D.set.huntMap = 'globe'; D.generate(); D.state = 'play'; D.GEO.found.add(5); D.hunt.score = 40; D.geoSave(); const s0 = D.geoLoad().seed, n0 = D.geoLoad().found.length;
          D.geoAsk('re', D.geoRestart); o.oneTap = D.geoLoad().found.length === n0 && n0 > 0; D.geoAsk('re', D.geoRestart); const sv = D.geoLoad(); o.afterTwo = [sv.seed === s0, (sv.found || []).length, sv.lat === undefined];
          D.generate(); D.state = 'play'; o.fresh = [D.GEO.found.size, D.hunt.score];
          D.geoAsk('new', D.geoNewPlanet); D.geoAsk('new', D.geoNewPlanet); o.gone = D.geoLoad() === null; return o; }""")
        print("restart", json.dumps(rs))
        ok = o["on"] and r["caches"] == 100 and r["bands"] >= 6 and r["minGap"] >= 850 and r["curve"] and r["wheel"] \
             and abs(r["walkLat"] - r["walkExpect"]) < r["walkExpect"] * .08 and r["reanchors"] >= 1 and all(abs(j) < .02 for j in r["jumps"]) and r["stale"] == 0 \
             and all(abs(v) < .012 for v in r["squareBack"]) and r["east"][0] > 10 and abs(r["east"][1] - r["east"][0] / 15) < .02 \
             and pole["maxLat"] > 89.4 and pole["end"][0] < pole["maxLat"] and pole["lonFlip"] < 20 and pole["biome"] == "polar" \
             and g["found"][0] and g["found"][2] >= 25 and g["saved"] and (not g["animal"] or (g["food"] == 1 and g["ate"][0] > 50 and g["ate"][1] == 0)) \
             and 2 < g["hunger"] < 4.5 and not g["toolsHurt"] and g["toolsFull"] and g["faint"] >= 30 and g["gps"] \
             and res["seed"] and res["found"] >= 1 and res["near"] < 400 and res["plain"] == [False, 0, False] and rs["oneTap"] and rs["afterTwo"] == [True, 0, True] and rs["fresh"] == [0, 0] and rs["gone"]
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
