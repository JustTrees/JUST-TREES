"""3.21: every endless map is the 50 km planet. Solo Hike, Hunt and Bot battle (and online Hike and Hunt) choose the 3 km island or
the planet; on the planet you start at your latitude on dry land (never the dinosaur island), with no Treeocashing on top (no caches,
levels, jet skis); Treeocashing is still the planet with everything. Re-laying the planet's patch carries the bots with it.
Usage: python3 dev/test_321.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
GEN = """([mode, map, lat]) => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setSeed(4242); D.setVR(true); D.vr.on = true; D.setMode(mode); D.MP.code = ''; D.set.geoNet = false;
  Object.assign(D.set, { env: 'climate', land: 'natural', lat, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .6, rough: .5, dino: false });
  if (mode === 'hike') D.set.hikeMap = map; else if (mode === 'hunt') D.set.huntMap = map; else D.set.pvpMap = map; D.mapRules();
  D.generate(); D.state = 'play'; if (mode === 'pvp') D.vbFit(); for (let i = 0; i < 240; i++) { if (D.ENDLESS) { D.endlessTick(1 / 30); D.enAnimTick(1 / 30); } D.geoTick(1 / 30); if (mode === 'pvp') D.vbTick(1 / 30); }
  const G = D.GLOBE, o = { globe: !!G, geo: !!D.GEO.on, hikemap: D.HIKEMAP, mapSet: mode === 'hike' ? D.set.hikeMap : mode === 'hunt' ? D.set.huntMap : D.set.pvpMap };
  if (G) { const ll = D.glLatLon(G.c); o.lat = Math.round(ll[0]); o.dry = D.H(D.P.x, D.P.z) > D.water; o.offIsle = !G.isle || D.glArc(G.c, G.isle.c) > G.isle.r; o.caches = (D.GEO.caches || []).length && D.GEO.on; o.jets = D.jetOn(); }
  o.animals = D.beasts.filter(a => !a.dead).length; o.bots = (D.VB.list || []).filter(b => b && b.x !== undefined).length;
  return o; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 200})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(400)
        out = {}
        for mode, mp, lat in [["hike", "endless", 45], ["hike", "island", 45], ["hunt", "endless", 20], ["hunt", "island", 45], ["pvp", "endless", 60]]:
            out[mode + "-" + mp] = await pg.evaluate(GEN, [mode, mp, lat])
        # the bots ride along when the planet's patch is laid again
        out["carry"] = await pg.evaluate("""() => { const L = D.VB.list.filter(b => b && b.x !== undefined); if (!L.length) return null; const b0 = L[0], s0 = D.glToSphere(b0.x, b0.z, [0, 0, 0]);
          D.P.x += 1700; D.globeReanchor(); const s1 = D.glToSphere(b0.x, b0.z, [0, 0, 0]); return +(D.glArc(s0, s1) * D.GLOBE.R).toFixed(2); }""")
        # Treeocashing is still itself
        out["treeo"] = await pg.evaluate("""() => { localStorage.setItem('jt-geochar', JSON.stringify({ n: 50, score: 0, kills: 0 })); D.setMode('hunt'); D.set.huntMap = 'globe'; D.MP.code = '9999'; D.set.geoNet = true; D.generate(); D.state = 'play';
          return [!!D.GLOBE, D.GEO.on, D.GEO.caches.length, D.jetOn()]; }""")
        print(json.dumps(out))
        o = out
        ok = o["hike-endless"]["globe"] and not o["hike-endless"]["geo"] and abs(o["hike-endless"]["lat"] - 45) <= 12 and o["hike-endless"]["dry"] and o["hike-endless"]["offIsle"] and not o["hike-endless"]["jets"] \
             and not o["hike-island"]["globe"] and o["hike-island"]["hikemap"] == "island" and o["hike-island"]["mapSet"] == "island" \
             and o["hunt-endless"]["globe"] and not o["hunt-endless"]["geo"] and abs(o["hunt-endless"]["lat"] - 20) <= 12 and o["hunt-endless"]["animals"] > 0 \
             and not o["hunt-island"]["globe"] and o["pvp-endless"]["globe"] and o["pvp-endless"]["bots"] > 0 and o["carry"] is not None and o["carry"] < 1 \
             and o["treeo"][0] and o["treeo"][1] and o["treeo"][2] == 50 and o["treeo"][3]
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
