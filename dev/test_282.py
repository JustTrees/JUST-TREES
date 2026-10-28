"""2.82: a Treeocache never sits inside a rock, boulder, log or tree trunk: once the ground round it is built, a blocked one moves to
the nearest clear spot. Usage: python3 dev/test_282.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 240})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300]))
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(400)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); localStorage.removeItem('jt-geochar'); D.DEV.ok = true; D.setVR(true); D.setMode('hunt'); D.vr.on = true;
          Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .7, rough: .6, huntMap: 'globe', dino: false });
          const o = { rock: 0, trunk: 0, moved: [], clear: 0, all: 0 };
          for (const sd of [4242, 777, 1234]) { D.setSeed(sd); D.generate(); D.state = 'play'; for (let i = 0; i < 60; i++) { D.endlessTick(1 / 30); D.geoTick(1 / 30); }
            const P = D.P, spots = [];
            for (let k = 0; k < 6000 && spots.length < 2; k++) { const a = k * 2.4, rr = k * .06, x = P.x + Math.cos(a) * rr, z = P.z + Math.sin(a) * rr;   // a boulder, and a tree trunk
              if (!D.geoSolidAt(x, z)) continue; const h = D.H(x, z); if (h < D.water + .5) continue;
              if (!spots.some(s => s.k === 'rock') && D.rockAround(x, z, 0) > h + .8) spots.push({ k: 'rock', x, z });
              else if (!spots.some(s => s.k === 'trunk') && D.nearObstacle(x, z, 0)) spots.push({ k: 'trunk', x, z }); }
            const C = D.GEO.caches.filter(c => !D.GEO.found.has(c.id)).slice(0, spots.length);
            spots.forEach((s, i) => { const c = C[i]; c.p = D.glToSphere(s.x, s.z, [0, 0, 0]); c.ok = true; c.chk = false; o[s.k]++; });
            D.GEO.tT = 0; D.geoTick(1 / 30);
            spots.forEach((s, i) => { const c = C[i]; o.moved.push(Math.round(Math.hypot(c.x - s.x, c.z - s.z) * 10) / 10); if (D.geoCacheClear(c.x, c.z)) o.clear++; });
            for (const c of D.GEO.caches) if (c.x !== undefined && c.chk) { o.all++; if (!D.geoCacheClear(c.x, c.z)) o.blocked = (o.blocked || 0) + 1; } }
          return o; }""")
        print(json.dumps(r))
        n = r["rock"] + r["trunk"]
        ok = r["rock"] >= 2 and n >= 4 and r["clear"] == n and all(0 < m < 40 for m in r["moved"]) and not r.get("blocked")
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
