"""Archipelago (1.70, Ron: like Raja Ampat / El Nido / Palau's Rock Islands): only when Edges = Island and latitude is exactly 0°.
A dozen or so steep jungle islands (one or two big, some medium, many small), real open water between every pair (erosion can't fill the channels),
every island within glide reach of a neighbour from its top (glide ~5 m forward per 1 m drop), deep blue sea, turquoise shelves, a beach on each.
Animals, loot, the porch and spawns still work."""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 200})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = {};
          const gen = (edges, lat, size, sd) => { D.setSeed(sd); D.setVR(true); D.setMode('hunt'); D.set.env = 'auto'; D.set.edges = edges; D.set.land = 'natural'; D.set.size = size; D.set.lat = lat; D.set.weather = 'clear'; D.generate(); D.state = 'play'; };
          let hits = 0; for (let k = 1; k <= 300; k++) if (D.archiRoll(k)) hits++; out.rollShare = +(hits / 300).toFixed(2);   // 1.73: one kind of equator island, about 4 in 10
          let plain = 1; while (D.archiRoll(plain)) plain++; gen('island', 0, 'medium', plain); out.plainIslandAt0 = !D.ARCHI && D.edgeShape ? true : !D.ARCHI;
          const first = s0 => { let k = s0; while (!D.archiRoll(k)) k++; return k; };
          let a1 = first(3); gen('island', 1, 'medium', a1); out.notAt1 = !D.ARCHI; gen('endless', 0, 'medium', a1); out.notEndless = !D.ARCHI;
          out.maps = [];
          for (const [size, sd0] of [['small', 6], ['medium', 4], ['large', 8], ['xl', 5]]) {
            const sd = first(sd0); gen('island', 0, size, sd); const I = D.ARCHI ? D.ARCHI.isl : [], o = { size, n: I.length };
            // water between every pair of neighbours, and glide reach from each island's top
            const top = I.map(a => { let t = -1e9; for (let ang = 0; ang < 6.28; ang += .3) for (let r = 0; r < a.r; r += 5) t = Math.max(t, D.H(a.x + Math.cos(ang) * r, a.z + Math.sin(ang) * r)); return t; });
            let minWater = 1e9, unreachable = 0;
            for (let i = 0; i < I.length; i++) { let bestGap = 1e9;
              for (let j = 0; j < I.length; j++) { if (i === j) continue; const a = I[i], c = I[j], d = Math.hypot(a.x - c.x, a.z - c.z), n = Math.ceil(d / 2); let wet = 0, run = 0, firstDry = null, lastDry = null;
                for (let k = 0; k <= n; k++) { const t = k / n, h = D.H(a.x + (c.x - a.x) * t, a.z + (c.z - a.z) * t); if (h < D.water) { run += d / n; wet = Math.max(wet, run); } else run = 0; }
                if (d < (a.r + c.r) * 1.32 + 100) minWater = Math.min(minWater, wet);
                bestGap = Math.min(bestGap, wet); }
              if (bestGap > (top[i] - D.water) * 5 * .8) unreachable++; }
            o.minWater = Math.round(minWater); o.unreachable = unreachable;
            o.big = I.filter(a => a.r > 60).length; o.small = I.filter(a => a.r < 25).length;
            o.animals = D.beasts.filter(A => !A.wings).length; o.porch = !!D.PORCH; o.loot = [...D.DROPS.values()].filter(d => d.type === 'gun').length;
            o.lootDry = [...D.DROPS.values()].every(d => D.H(d.x, d.z) > D.water - .2 || d.y > D.water);
            out.maps.push(o); }
          D.set.edges = 'endless'; D.set.env = 'climate'; return out; }""")
        print(json.dumps(r))
        ok = .3 < r["rollShare"] < .5 and r["plainIslandAt0"] and r["notAt1"] and r["notEndless"] and all(m["n"] >= 5 and m["minWater"] >= 20 and m["unreachable"] == 0 and m["small"] >= 3 and m["animals"] > 10 and m["porch"] and m["loot"] > 5 and m["lootDry"] for m in r["maps"]) \
             and any(m["big"] >= 1 for m in r["maps"]) and r["maps"][2]["n"] >= 8
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
