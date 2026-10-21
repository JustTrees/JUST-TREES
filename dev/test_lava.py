"""Lava (1.63): a volcano's crater holds a pool of lava. Nothing grows or lies in it, animals never go in, loot and spawns avoid it.
Stepping in: VR fades red and respawns you on safe ground (like drowning); PC flashes red and puts you back on safe ground."""
import os, sys, asyncio, json, base64
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1]); SHOTS = sys.argv[2] if len(sys.argv) > 2 and os.path.isdir(sys.argv[2]) else None
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 900, "height": 560})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        out = []
        for sd in [33, 15, 61]:
            r = await pg.evaluate("""(sd) => { window.FREEZE = true; const T = D.THREE, o = { sd };
              D.setSeed(sd); D.setVR(true); D.setMode('hunt'); D.set.land = 'dramatic'; D.set.size = 'medium'; D.set.lat = 42; D.set.weather = 'clear'; D.generate(); D.state = 'play';
              const L = D.LAVA; o.lava = !!L && !!L.mesh; if (!o.lava) return o;
              // cells of the pool
              const cells = []; for (let j = 0; j < L.n; j++) for (let i = 0; i < L.n; i++) if (L.mask[j * L.n + i]) cells.push([L.gx + i * L.st, L.gz + j * L.st]);
              o.cells = cells.length;
              o.surfaceAbove = cells.filter(([x, z]) => D.H(x, z) < L.y).length / cells.length;           // the ground under it really is below the lava
              let trees = 0, rocks = 0; for (const [x, z] of cells) { const c = D.obstacles.get(Math.floor(x / 8) + ',' + Math.floor(z / 8)); if (c) for (const t of c) if (t.tr !== undefined && Math.hypot(t.x - x, t.z - z) < 2) trees++;
                if (D.rockTopAt(x, z, L.y + 30, 60) > L.y - .2) rocks++; }
              o.treesIn = trees; o.rocksIn = rocks;
              o.animalsIn = D.beasts.filter(A => !A.wings && D.inLava(A.x, A.z)).length;
              o.okSpotIn = cells.filter(([x, z]) => D.okSpot(x, z)).length;
              o.lootIn = [...D.DROPS.values()].filter(d => D.inLava(d.x, d.z, 1)).length;
              // VR: step in
              const [lx, lz] = cells[Math.floor(cells.length / 2)]; D.P.x = lx; D.P.z = lz; D.P.y = L.y - .2;
              const I = { head: new T.Vector3(lx, L.y + 1.4, lz), headQ: new T.Quaternion() };
              o.hit = D.lavaHit(); D.uwTick(1 / 30, I); o.vrRed = D.UW.red === 1 && D.UW.drown > 0;
              for (let i = 0; i < 90; i++) { I.head.set(D.P.x, D.P.y + 1.4, D.P.z); D.uwTick(1 / 30, I); }
              o.vrMoved = Math.hypot(D.P.x - lx, D.P.z - lz); o.vrSafe = !D.inLava(D.P.x, D.P.z, 20); o.vrDone = D.UW.drown === 0 && D.UW.red === 0;
              // PC: step in
              D.setVR(false); D.vr.on = false; D.P.x = lx; D.P.z = lz; D.P.y = L.y - .2;
              D.update(1 / 30); o.pcFlash = D.PCLAVA.t > 0;
              for (let i = 0; i < 60; i++) D.update(1 / 30);
              o.pcMoved = Math.hypot(D.P.x - lx, D.P.z - lz); o.pcSafe = !D.inLava(D.P.x, D.P.z, 20);
              return o; }""", sd)
            out.append(r)
        if SHOTS:
            for sd in [33, 15]:
                img = await pg.evaluate("""(sd) => { window.FREEZE = true; D.setSeed(sd); D.setVR(false); D.setMode('hike'); D.set.land = 'dramatic'; D.set.size = 'medium'; D.set.lat = 42; D.set.weather = 'clear'; D.generate(); D.state = 'play';
                  const L = D.LAVA, F = D.FEAT, cam = D.camera, a = .7, d = F.R * 2.6; cam.position.set(F.x + Math.cos(a) * d, L.y + F.R * .9, F.z + Math.sin(a) * d); cam.fov = 55; cam.updateProjectionMatrix();
                  cam.lookAt(L.x, L.y, L.z); cam.updateMatrixWorld(); D.renderer.render(D.scene, cam); return D.renderer.domElement.toDataURL('image/jpeg', .85); }""", sd)
                open(os.path.join(SHOTS, f"lava_{sd}.jpg"), "wb").write(base64.b64decode(img.split(",")[1]))
        print(json.dumps(out))
        ok = all(o["lava"] and o["surfaceAbove"] > .95 and o["treesIn"] == 0 and o["rocksIn"] == 0 and o["animalsIn"] == 0 and o["okSpotIn"] == 0 and o["lootIn"] == 0
                 and o["hit"] and o["vrRed"] and o["vrMoved"] > 20 and o["vrSafe"] and o["vrDone"] and o["pcFlash"] and o["pcMoved"] > 20 and o["pcSafe"] for o in out)
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
