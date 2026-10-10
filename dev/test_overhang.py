"""Overhangs (1.48): under a rock with room beneath it you can stand, walk and shoot; on top it still holds you; inside it still blocks.
Usage: python3 dev/test_overhang.py /tmp/dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 300, "height": 200})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); const out = {};
          let found = null, sd = 1;
          for (; sd < 40 && !found; sd++) { D.setSeed(sd); Object.assign(D.set, { size: 'medium', rough: .8, weather: 'clear', land: 'natural' }); D.setMode('hike'); D.generate();
            const N = D.rockN, L = D.rockLow, T = D.rockGrid, HALF = (N - 1) / 2;
            for (let k = 0; k < N * N && !found; k += 3) { if (T[k] < -1e8) continue; const x = k % N - HALF + .5, z = Math.floor(k / N) - HALF + .5, g = D.H(x, z); if (L[k] > g + 2.4 && T[k] > L[k] + 1) found = { x, z, g, low: L[k], top: T[k] }; } }
          out.seed = sd - 1; out.found = !!found; if (!found) return out;
          const f = found; out.gapM = +(f.low - f.g).toFixed(1);
          out.underIgnoredForWalking = D.rockTop(f.x, f.z, f.g, 1.6) < -1e8;
          out.onTopStillSolid = Math.abs(D.rockTop(f.x, f.z, f.top + .1, 0) - f.top) < .01;
          out.insideStillSolid = D.rockTop(f.x, f.z, (f.low + f.top) / 2, 0) > -1e8;
          out.oldWayBlocked = D.rockTop(f.x, f.z) > f.g + 1;
          // bullets: a level shot under the overhang flies on; one into the rock stops
          const T3 = D.THREE, hit = (y) => { const o = new T3.Vector3(f.x - .3, y, f.z), dir = new T3.Vector3(1, 0, 0); const h = D.castShotDbg(o, dir, .55); return h.kind || "clear"; };
          out.shotUnder = hit(f.g + .8); out.shotIntoRock = hit((f.low + f.top) / 2);
          return out; }""")
        print(json.dumps(r)); print("errors:", errs[:8] or "none")
        await b.close()
asyncio.run(main())
