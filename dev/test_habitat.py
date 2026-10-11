"""Animals live where they like (open-ground grazers in the open, goats high, crocs by water), don't gather round a still hunter,
turn up (out of sight, not in a ring) while you wait, scatter different ways after a shot, and fall over limp."""
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
          D.setMode('hunt'); D.set.size = 'xl'; D.set.weather = 'clear'; D.set.lat = 42; D.set.rough = .6; D.generate(); D.state = 'play';
          const G = D.HAB, n = G.n, cell = (x, z) => { const i = Math.max(0, Math.min(n - 1, Math.round((x + 600) / G.cell))), j = Math.max(0, Math.min(n - 1, Math.round((z + 600) / G.cell))); return (i * n + j) * 5; };
          // how much do horses sit on open ground, compared with the map as a whole?
          const ground = D.beasts.filter(A => !A.wings && A.kind !== 'monkey');
          const openOf = A => G.g[cell(A.x, A.z) + 0], mapOpen = (() => { let s = 0, c = 0; for (let k = 0; k < G.g.length; k += 5) if (G.g[k] + G.g[k + 1] + G.g[k + 2] > 0) { s += G.g[k]; c++; } return s / c; })();
          const horses = ground.filter(A => A.kind === 'horse'), boars = ground.filter(A => A.kind === 'boar'), goats = ground.filter(A => A.kind === 'goat');
          out.mapOpen = +mapOpen.toFixed(2); out.horseOpen = +(horses.reduce((s, A) => s + openOf(A), 0) / Math.max(1, horses.length)).toFixed(2);
          out.boarOpen = +(boars.reduce((s, A) => s + openOf(A), 0) / Math.max(1, boars.length)).toFixed(2); out.goatHigh = +(goats.reduce((s, A) => s + G.g[cell(A.x, A.z) + 4], 0) / Math.max(1, goats.length)).toFixed(2);
          // stand still for 4 minutes in an open spot
          const near = R => ground.filter(A => !A.dead && Math.hypot(A.x - D.P.x, A.z - D.P.z) < R).length;
          out.within60_start = near(60); out.within380_start = near(360);
          let appeared = 0, visibleAppear = 0; const was = new Map(ground.map(A => [A, [A.x, A.z]]));
          D.camera.position.set(D.P.x, D.P.y + 1.6, D.P.z); D.camera.lookAt(D.P.x, D.P.y + 1.6, D.P.z - 10); D.camera.updateMatrixWorld();
          for (let i = 0; i < 240 * 10; i++) { D.updateAnimals(1 / 10);
            for (const A of ground) { const w = was.get(A); if (Math.hypot(A.x - w[0], A.z - w[1]) > 150) { appeared++; const d = Math.hypot(A.x - D.P.x, A.z - D.P.z); if (A.z < D.P.z && Math.abs(A.x - D.P.x) < (D.P.z - A.z) * 1.4 && d < 700) visibleAppear++; } was.set(A, [A.x, A.z]); } }
          out.jumps = appeared; out.jumpsInView = visibleAppear; out.within60_end = near(60); out.within380_end = near(360);
          const ds = ground.filter(A => Math.hypot(A.x - D.P.x, A.z - D.P.z) < 400).map(A => Math.round(Math.hypot(A.x - D.P.x, A.z - D.P.z))).sort((a, b) => a - b); out.nearDists = ds.slice(0, 12);
          // shot: groups head off in different directions
          const near12 = ground.filter(A => !A.dead).sort((a, b) => Math.hypot(a.x - D.P.x, a.z - D.P.z) - Math.hypot(b.x - D.P.x, b.z - D.P.z)).slice(0, 15);
          const st = new Map(near12.map(A => [A, [A.x, A.z]])); D.scatterBeasts(D.camera.position); for (let i = 0; i < 300; i++) D.updateAnimals(1 / 10);
          const heads = near12.filter(A => Math.hypot(A.x - st.get(A)[0], A.z - st.get(A)[1]) > 30).map(A => Math.atan2(A.x - st.get(A)[0], A.z - st.get(A)[1]) - Math.atan2(st.get(A)[0] - D.P.x, st.get(A)[1] - D.P.z));
          out.fleeOffsets = heads.map(h => +Math.atan2(Math.sin(h), Math.cos(h)).toFixed(2));
          // a kill: tips sideways, legs go limp
          const V = ground.find(A => !A.dead && A.legs.length === 4); D.camera.position.set(V.x + 10, V.y + 2, V.z); V.legs.forEach(l => l.rotation.x = .5);
          D.killAnimal(V, 100); for (let i = 0; i < 60; i++) D.updateAnimals(1 / 30);
          out.deadTilt = +Math.abs(V.root.rotation.z).toFixed(2); out.legZ = V.legs.map(l => +l.rotation.z.toFixed(2)); out.legX = V.legs.map(l => +l.rotation.x.toFixed(2)); out.limp = +V.limpT.toFixed(2);
          return out; }""")
        print(json.dumps(r))
        ok = r["horseOpen"] > r["mapOpen"] and r["within60_end"] <= r["within60_start"] + 4 and r["jumps"] > 0 and r["jumpsInView"] == 0 and r["within380_end"] > r["within380_start"] \
             and len(set(round(x, 1) for x in r["fleeOffsets"])) >= 3 and 1.3 < r["deadTilt"] < 1.55 and r["limp"] == 1 and all(abs(z) > .1 for z in r["legZ"])
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
