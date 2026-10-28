"""2.99: Treeocashing's planet: one large ocean across the equator and at least two more; in the large one, on the equator, the biggest
island (3–4 km) with its own landform and open sea round it; dinosaurs live only there (no T. rex); three high caches are on it; and
each next cache is further away the higher your level.
Usage: python3 dev/test_299.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 240})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(400)
        out = []
        for sd in [4242, 77, 1234]:
            r = await pg.evaluate("""(sd) => { window.FREEZE = true; D.renderer.setAnimationLoop(null); localStorage.setItem('jt-geochar', JSON.stringify({ n: 10, score: 0, kills: 0 })); D.setSeed(sd); D.setVR(true); D.vr.on = true;
              D.setMode('hunt'); Object.assign(D.set, { env: 'climate', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', huntMap: 'globe', dino: false });
              D.MP.code = '9999'; D.set.geoNet = true; D.generate(); D.state = 'play'; for (let i = 0; i < 20; i++) { D.endlessTick(1 / 30); D.geoTick(1 / 30); }
              const G = D.GLOBE, R = G.R, o = {}, I = G.isle;
              o.oceans = G.basins.length; o.bigLat = Math.round(D.glLatLon(G.basins[0].c)[0]); o.bigA = +(G.basins[0].a / Math.max(...G.basins.slice(1).map(B => B.a))).toFixed(2);
              o.isle = [Math.round(I.r * R * 2), Math.round(D.glLatLon(I.c)[0]), G.landAt(I.c) > 2, !!I.feat && I.feat.type];
              const f = D.glFrame(I.c), at = (d, a) => D.glNorm([I.c[0] + (f.E[0] * Math.cos(a) + f.N[0] * Math.sin(a)) * Math.tan(d / R), I.c[1] + (f.E[1] * Math.cos(a) + f.N[1] * Math.sin(a)) * Math.tan(d / R), I.c[2] + (f.E[2] * Math.cos(a) + f.N[2] * Math.sin(a)) * Math.tan(d / R)]);
              let sea = 0; for (let k = 0; k < 24; k++) if (G.landAt(at(I.r * R + 600, k / 24 * 6.283)) < 0) sea++; o.seaRing = sea;
              o.isleCaches = D.GEO.caches.filter(c => c.isle).length;
              // the next cache: further at a higher level
              const dist = n => { for (const c of D.GEO.caches) c.placed = false; D.GEO.found = new Set(Array.from({ length: n }, (_, i) => i + 1)); D.geoTarget(); return D.GEO.target ? Math.round(D.glArc(G.p, D.GEO.target.p) * R) : -1; };
              o.dist = [dist(5), dist(40), dist(90)];
              // on the island: dinosaurs, and nothing else on the ground
              D.geoTeleport(I.c); for (let i = 0; i < 300; i++) { D.endlessTick(1 / 30); D.enAnimTick(1 / 30); }
              const near = D.beasts.filter(A => !A.dead && A.x !== undefined && Math.hypot(A.x - D.P.x, A.z - D.P.z) < 1200 && D.geoDinoAt(A.x, A.z));
              o.dinos = [near.length, [...new Set(near.map(A => A.kind))].join(','), D.geoDinoAt(D.P.x, D.P.z)];
              const H0 = D.H(D.P.x, D.P.z); o.feat = Math.round(H0 - G.landAt(D.glToSphere(D.P.x, D.P.z, [0, 0, 0])));
              return o; }""", sd)
            out.append(r); print(json.dumps(r))
        DINO = {"triceratops", "parasaur", "stego", "bronto"}
        ok = all(r["oceans"] >= 3 and abs(r["bigLat"]) <= 4 and r["bigA"] > 1.2 and 3000 <= r["isle"][0] <= 4000 and abs(r["isle"][1]) < 1 and r["isle"][2] and r["isle"][3]
                 and r["seaRing"] >= 20 and r["isleCaches"] == 3 and r["dist"][0] < r["dist"][1] < r["dist"][2] and r["dinos"][2] and 0 < r["dinos"][0] < 80 and abs(r["dist"][1] - 1800) < 400
                 and set(filter(None, r["dinos"][1].split(","))) <= DINO for r in out)
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
