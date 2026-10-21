"""2.19: Endless hiking. Builds an endless map (as in a headset), then checks:
- the start area is built right away, the ground meets exactly where squares join (heights and normals), no square is missing near you
- walking on (simulated frames, with the per-frame build budget) keeps everything near you built, and lets far squares go
- a square comes out the same when it's built again (go away, come back), and the same 25 km further on (the loop)
- rocks near you are solid, the map window follows you, the water follows you
- 2.21: the map keeps up while you keep walking, a mark lands far from the start, the clock runs (a day in 24 min), the tree shadows turn
  with the sun, tree shapes come out the same every time
Usage: python3 dev/test_endless.py dbg.html [walk_km] [speed m/s] [budget factor]"""
import sys, asyncio, json
from playwright.async_api import async_playwright
QUICK = __import__('os').environ.get('JT_QUICK') == '1'   # run_all's quick run: a shorter walk
num = [a for a in sys.argv[2:] if a.replace('.', '', 1).isdigit()]          # (the test runner passes a picture path; numbers are for running it by hand)
KM = float(num[0]) if len(num) > 0 else (1.2 if QUICK else 2)
SPEED = float(num[1]) if len(num) > 1 else 12.5
BUD = float(num[2]) if len(num) > 2 else 1
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500); await pg.evaluate(f"() => {{ window.__speed = {SPEED}; window.__bud = {BUD}; }}")
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setSeed(777); D.setVR(true); D.setMode('hike'); D.hikeForce = 'endless';
          Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .5, rough: .5 });
          const t0 = performance.now(); D.generate(); const gen = performance.now() - t0; D.state = 'play';
          const E = D.ENDLESS, out = { gen: Math.round(gen), map: D.HIKEMAP, chunks: E.chunks.size, water: +D.water.toFixed(2), span: +E.span.toFixed(1), tiles: D.tilesN };
          // seams: where two built squares meet, their edge vertices agree exactly (height and normal)
          let worstH = 0, worstN = 0, pairs = 0;
          for (const ch of E.chunks.values()) { if (!ch.tile) continue; const nb = E.chunks.get((ch.ix + 1 + 60000) * 120000 + (ch.iz + 60000)); if (!nb || !nb.tile) continue;
            const a = ch.tile.group.children[0].geometry, b = nb.tile.group.children[0].geometry, n1 = 51; pairs++;
            for (let j = 0; j < n1; j++) { const ka = j * n1 + 50, kb = j * n1; worstH = Math.max(worstH, Math.abs(a.attributes.position.getY(ka) - b.attributes.position.getY(kb)));
              worstN = Math.max(worstN, Math.abs(a.attributes.normal.getX(ka) - b.attributes.normal.getX(kb)) + Math.abs(a.attributes.normal.getZ(ka) - b.attributes.normal.getZ(kb))); } }
          out.seams = { pairs, worstH: +worstH.toFixed(5), worstN: +worstN.toFixed(5) };
          // a square's content, as a number
          window.__sig = (ch) => { let h = 0; const add = v => { h = (h * 31 + Math.round(v * 100)) | 0; }; for (const t of ch.trees) { add(t.x - ch.x0); add(t.z - ch.z0); add(t.s); add(t.vi); add(t.y); } return ch.trees.length + ':' + h; };
          const c0 = E.chunks.get((0 + 60000) * 120000 + (0 + 60000)); out.sig0 = window.__sig(c0);
          out.solidNear = [...E.chunks.values()].filter(ch => ch.rg).length;
          return out; }""")
        print("start", json.dumps(r))
        # walk east (sprint speed), frames of 1/72 s with the normal headset budget
        w = await pg.evaluate("""(km) => { const E = D.ENDLESS, dt = 1 / 72, speed = 12.5; let worst = 0, sum = 0, frames = 0, maxMissing = 0, worstStep = 0;
          D.vr.on = true; D.state = 'vrmenu'; for (let f = 0; f < 72 * 5; f++) D.endlessTick(dt); D.state = 'play';   // the start screen: the land grows in while you look at the little map
          const preview = E.chunks.size; E.bud = +(window.__bud || 1); const x0 = D.P.x; E.prof = {}; E.psum = {}; E.pbig = 0; E.nBuilt = 0;
          const hour0 = D.hourNow, dirs = new Set([E.sh.dir.toArray().map(v => v.toFixed(3)).join()]); let mapLag = 0;
          while (D.P.x - x0 < km * 1000) {
            D.P.x += speed * dt; D.P.z += Math.sin(D.P.x / 700) * speed * dt * .4; D.P.y = D.H(D.P.x, D.P.z);
            const t0 = performance.now(); D.endlessTick(dt); const t = performance.now() - t0; worst = Math.max(worst, t); sum += t; frames++;
            if (frames % 72 === 0) { let miss = 0; for (let i = -5; i <= 5; i++) for (let j = -5; j <= 5; j++) { const ix = Math.floor(D.P.x / 200) + i, iz = Math.floor(D.P.z / 200) + j; if (Math.hypot((ix + .5) * 200 - D.P.x, (iz + .5) * 200 - D.P.z) > 700) continue; const ch = E.chunks.get((ix + 60000) * 120000 + (iz + 60000)); if (!ch || !ch.tile) miss++; } maxMissing = Math.max(maxMissing, miss);
              if (D.P.x - x0 > 300) mapLag = Math.max(mapLag, Math.hypot(D.P.x - D.MAPV.cx, D.P.z - D.MAPV.cz)); dirs.add(E.sh.dir.toArray().map(v => v.toFixed(3)).join()); }
          }
          return { preview, frames, avgMs: +(sum / frames).toFixed(2), worstMs: +worst.toFixed(1), maxMissingWithin700m: maxMissing, chunks: E.chunks.size, tiles: D.tilesN, mapCx: D.MAPV.cx, px: Math.round(D.P.x), waterX: Math.round(E.water.position.x), solid: [...E.chunks.values()].filter(ch => ch.rg).length, obstacleCells: D.obstacles.size, prof: Object.fromEntries(Object.entries(E.prof).map(([k, v]) => [k, +v.toFixed(1)])), sum: Object.fromEntries(Object.entries(E.psum).map(([k, v]) => [k, Math.round(v)])), big: E.pbig, built: E.nBuilt,
            mapLag: Math.round(mapLag), hours: +(D.hourNow - hour0).toFixed(2), sunTurns: dirs.size - 1, freed: E.freed || 0, envs: Object.keys(E.envH).length,
            mark: D.castShot(new D.THREE.Vector3(D.P.x, D.H(D.P.x, D.P.z) + 2, D.P.z), new D.THREE.Vector3(1, -.15, 0).normalize(), 1500).kind }; }""", KM)
        print("walk", json.dumps(w))
        # come back to the start: the first square is built again, the same as before; and 25 km on it's the same land again
        c = await pg.evaluate("""() => { const E = D.ENDLESS; D.P.x = 100; D.P.z = 100; for (let f = 0; f < 600; f++) D.endlessTick(1 / 72); D.enEnsure(100, 100, 150);
          const c0 = E.chunks.get((0 + 60000) * 120000 + (0 + 60000)), back = window.__sig(c0);
          D.P.x = 25100; D.P.z = 100; D.enEnsure(25100, 100, 150); const c1 = E.chunks.get((125 + 60000) * 120000 + (0 + 60000)), loop = window.__sig(c1);
          let hd = 0; for (let i = 0; i < 50; i++) hd = Math.max(hd, Math.abs(D.H(13 + i * 3.7, 41 + i * 2.1) - D.H(25013 + i * 3.7, 41 + i * 2.1)));
          let rocks = 0; for (const ch of E.chunks.values()) if (ch.rg) for (let k = 0; k < ch.rg.top.length; k += 7) if (ch.rg.top[k] > -1e8) rocks++;
          return { back, loop, loopHeightDiff: +hd.toFixed(4), solidCells: rocks }; }""")
        print("again", json.dumps(c))
        # pick a start 900 m out on the little map and drop in: the land there is built before the fade lifts
        d = await pg.evaluate("""() => { const E = D.ENDLESS; D.state = 'vrmenu'; D.P.x = 900 * .7; D.P.z = -900 * .7; D.vruiDropIn(); if (D.VRUI.fadeGo) D.VRUI.fadeGo();
          const ch = E.chunks.get((Math.floor(D.P.x / 200) + 60000) * 120000 + (Math.floor(D.P.z / 200) + 60000)); let ring = 0;
          for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) { const c = E.chunks.get((Math.floor(D.P.x / 200) + i + 60000) * 120000 + (Math.floor(D.P.z / 200) + j + 60000)); if (c && c.tile) ring++; }
          return { built: !!(ch && ch.tile), ring, state: D.state }; }""")
        print("drop", json.dumps(d))
        # tree shapes: the same every time the world is made (each environment's own random stream, however its making is split up)
        g = await pg.evaluate("""() => { const sig = () => { const E = D.ENDLESS; let h = 0; for (const b of Object.keys(E.envH).sort()) for (const k in E.envH[b].kinds) for (const v of E.envH[b].kinds[k].vars) h = (h * 31 + v.geo.attributes.position.count + Math.round(v.h * 100)) | 0; return h; };
          D.generate(); const a = sig(); D.generate(); return { a, b: sig() }; }""")
        print("shapes", json.dumps(g))
        ok = r["map"] == "endless" and r["seams"]["pairs"] > 10 and r["seams"]["worstH"] < 1e-3 and r["seams"]["worstN"] < 1e-3 and w["maxMissingWithin700m"] == 0 \
             and c["back"] == r["sig0"] and c["loop"] == r["sig0"] and c["loopHeightDiff"] < 1e-3 and w["chunks"] < 260 and abs(w["waterX"] - w["px"]) < 50 and c["solidCells"] > 0 and d["built"] and d["ring"] == 9 and not errs \
             and w["mapLag"] < 600 and w["mark"] and w["hours"] > KM * 1000 / SPEED / 60 * .9 and w["sunTurns"] >= 1 and g["a"] == g["b"]
        print("errors", errs[:5]); print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
