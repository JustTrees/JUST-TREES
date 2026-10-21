"""Animals everywhere (1.63): every part of the map (about 200 m squares) has animals at the start, and keeps them through the round:
parts that get shot out or run empty are filled again, far from you and out of sight (never popping up in view). After a shot they still run off."""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1]); OLD = '--old' in sys.argv
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 200})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        await pg.evaluate("() => { window.FREEZE = true; }")
        out = {}
        # 1) at the start: what share of the map's land squares have something to hunt (not counting rabbits)
        r = await pg.evaluate("""(old) => { const res = [];
          for (const [lat, size, sd] of [[42, 'medium', 5], [42, 'large', 6], [56, 'large', 7], [10, 'large', 8], [42, 'xl', 9], [70, 'large', 10]]) {
            D.setSeed(sd); D.setVR(true); D.setMode('hunt'); D.set.land = 'natural'; D.set.size = size; D.set.lat = lat; D.set.weather = 'clear'; D.generate(); D.state = 'play';
            const S = { medium: 560, large: 800, xl: 1200 }[size], G = Math.max(2, Math.min(8, Math.round(S / 200))), w = S / G, half = S / 2, has = new Set(); let land = [];
            if (!old) land = D.STOCK.land; else for (let q = 0; q < G * G; q++) land.push(q);
            for (const A of D.beasts) if (!A.dead && !A.gone && !A.wings && !['monkey', 'seal', 'crocodile', 'rabbit', 'bigfoot', 'yeti'].includes(A.kind)) { const i = Math.max(0, Math.min(G - 1, Math.floor((A.x + half) / w))), j = Math.max(0, Math.min(G - 1, Math.floor((A.z + half) / w))); has.add(i * G + j); }
            res.push({ lat, size, squares: land.length, withAnimals: land.filter(q => has.has(q)).length, share: +(land.filter(q => has.has(q)).length / land.length).toFixed(2) }); }
          return res; }""", OLD)
        out["start"] = r
        if not OLD:
            # 2) shoot out half the map (everything west of the middle), stand in the east looking east: the west fills again, out of sight
            r = await pg.evaluate("""() => { const T = D.THREE; D.setSeed(6); D.setVR(true); D.setMode('hunt'); D.set.land = 'natural'; D.set.size = 'large'; D.set.lat = 42; D.generate(); D.state = 'play';
              const half = 400, ST = D.STOCK, live = () => { const c = D.stockCounts(true); return ST.land.filter(q => c.get(q) > 0).length; };
              D.P.x = 250; D.P.z = 0; D.P.y = D.H(250, 0); D.camera.position.set(250, D.P.y + 1.7, 0); D.camera.lookAt(400, D.P.y + 1.7, 0); D.camera.updateMatrixWorld();
              for (const A of D.beasts) if (!A.wings && A.x < 0) { A.dead = true; A.deadT = 1; }
              const before = live(); let popped = 0, ticks = 0; const fw = new T.Vector3(); D.camera.getWorldDirection(fw);
              const seen = (x, z) => { const d = Math.hypot(x - D.P.x, z - D.P.z); return d < 200 || ((x - D.P.x) * fw.x + (z - D.P.z) * fw.z) / d > .3 && d < 3000; };
              for (let t = 0; t < 120; t++) { const pos = new Map(D.beasts.map(A => [A, [A.x, A.z]])); ST.t = 0; D.stockTick(.01); ticks++;
                for (const A of D.beasts) { if (A.dead || A.wings) continue; const p0 = pos.get(A); if ((!p0 || Math.hypot(p0[0] - A.x, p0[1] - A.z) > 30) && seen(A.x, A.z)) popped++; } }
              const after = live(); return { squares: ST.land.length, liveBefore: before, liveAfter: after, poppedInView: popped, beasts: D.beasts.length }; }""")
            out["refill"] = r
            # 3) a shot: they still run off, and the map stays covered
            r = await pg.evaluate("""() => { D.setSeed(7); D.setVR(true); D.setMode('hunt'); D.set.land = 'natural'; D.set.size = 'large'; D.set.lat = 56; D.generate(); D.state = 'play';
              const ST = D.STOCK, live = () => { const c = D.stockCounts(true); return ST.land.filter(q => c.get(q) > 0).length; };
              const near = D.beasts.filter(A => !A.wings && !A.dead && A.kind !== 'rabbit' && Math.hypot(A.x - D.P.x, A.z - D.P.z) < 300);
              const p0 = near.map(A => [A.x, A.z]); D.scatterBeasts(D.P); const fled = near.filter(A => A.trek || A.fleeT > 0).length;
              for (let i = 0; i < 600; i++) D.updateAnimals(1 / 10);
              const ran = near.filter((A, i) => Math.hypot(A.x - p0[i][0], A.z - p0[i][1]) > 80).length;
              return { near: near.length, fled, ranFar: ran, squares: ST.land.length, liveAfter: live() }; }""")
            out["shot"] = r
            # 4) walking in VR is walking (they notice you at 60 m), sprinting in VR they notice at 150 m
            r = await pg.evaluate("""() => { D.vr.on = true; const R = v => { D.P.onGround = true; D.P.crouch = false; for (let i = 0; i < 30; i++) { D.P.x += v / 30; D.updateAnimals(1 / 30); } return D.sense.R; };
              const o = { walk: R(8.5), sprint: R(12.5) }; D.vr.on = false; o.pcWalk = R(4.8); o.pcRun = R(8.5); return o; }""")
            out["notice"] = r
        print(json.dumps(out))
        if OLD: print("(old build: numbers only)"); await b.close(); return
        ok = all(s["share"] >= .85 for s in out["start"]) and out["refill"]["liveAfter"] >= out["refill"]["squares"] * .9 and out["refill"]["liveAfter"] > out["refill"]["liveBefore"] \
             and out["refill"]["poppedInView"] == 0 and out["shot"]["fled"] >= out["shot"]["near"] * .8 and out["shot"]["ranFar"] >= out["shot"]["near"] * .5 and out["shot"]["liveAfter"] >= out["shot"]["squares"] * .75 \
             and out["notice"] == {"walk": 60, "sprint": 150, "pcWalk": 60, "pcRun": 150}
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
