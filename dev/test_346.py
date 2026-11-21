"""3.46: the torch and the headlamp, and the dinosaur island's coastline. Everyone starts Treeocashing with a torch; lit from the pack it's
in your other hand and its glow (a shader term on every lit surface, no real light) brightens what's near it; the headlamp makes a pool
where you look; others' lights glow near them (tc). Back out of a game, no glows. The island isn't a circle any more: its reach from the
middle varies a lot round the compass, and "on the island" follows that outline. Usage: python3 dev/test_346.py dbg.html"""
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
        await pg.evaluate(GEN, 1)
        r = await pg.evaluate("""() => { const o = {}, T = D.THREE, G = D.GLOBE, I = G.isle, P = D.P;
          o.start = [D.GEO.items.has('torch'), D.geoPackItems().includes('torch')]; D.DEV.ok = false; o.noDev = D.geoGearFromCount(0).items.has('torch'); D.DEV.ok = true;
          // the shader: the glow is in every lit surface's code; light near a torch is brighter than without
          const cam = D.camera, q = cam.quaternion.clone(), hand = { pos: new T.Vector3(P.x - .3, P.y + 1.2, P.z - .3), rayQ: q }, II = { head: new T.Vector3(P.x, P.y + 1.7, P.z), headQ: q, hands: { left: hand, right: null } };
          D.set.hand = 'right'; D.torchTick(II); o.off0 = D.TORCH.u.value.every(v => v.w === 0);
          D.GEO.worn.add('torch'); D.torchTick(II); const t0 = D.TORCH.u.value[0]; o.on = [t0.w > 1, Math.hypot(t0.x - hand.pos.x, t0.z - hand.pos.z) < .5, !!(D.TORCH.obj && D.TORCH.obj.visible)];
          D.GEO.worn.add('headlamp'); D.torchTick(II); o.lamp = D.TORCH.u.value[1].w > 0;
          D.renderer.compile(D.scene, cam); o.programs = D.renderer.info.programs.length > 0;   /* (no shader errors: see errs) */
          // out of the game: stale glows switch off
          D.TORCH.at = performance.now() - 1000; D.torchStale(); o.stale = D.TORCH.u.value.every(v => v.w === 0) && !D.TORCH.obj.visible;
          // the island outline: reach from the middle varies round the compass; on/off follows it
          const f = D.glFrame(I.c), reach = []; for (let a = 0; a < 6.283; a += .2) { let lo = 0, hi = I.r * 1.6; for (let k = 0; k < 20; k++) { const m = (lo + hi) / 2, p = D.glNorm([I.c[0] + (f.E[0] * Math.cos(a) + f.N[0] * Math.sin(a)) * Math.tan(m), I.c[1] + (f.E[1] * Math.cos(a) + f.N[1] * Math.sin(a)) * Math.tan(m), I.c[2] + (f.E[2] * Math.cos(a) + f.N[2] * Math.sin(a)) * Math.tan(m)]); if (G.isleArc(p) < I.r) lo = m; else hi = m; } reach.push(lo / I.r); }
          o.reach = [+Math.min(...reach).toFixed(2), +Math.max(...reach).toFixed(2)];
          return o; }""")
        print(json.dumps(r))
        ok = r["start"] == [True, True] and r["noDev"] and r["off0"] and r["on"] == [True, True, True] and r["lamp"] and r["programs"] and r["stale"] \
             and r["reach"][0] < .75 and r["reach"][1] > 1.15
        print("PASS" if ok and not errs else "FAIL", errs[:5]); print("errors: none" if not errs else "errors: " + str(errs[:5])); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
