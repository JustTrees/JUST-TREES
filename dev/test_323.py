"""3.23 (3.27: the raptor hunts now): underground beasts (online Treeocashing). The Backrooms: no raptor for the first minute; then one
that tears round the halls hunting you: it comes at you and bites, then darts off and comes again; shots hurt it and two sniper hits drop
it; it's sized for the halls. The bunker: the same, with red eyes. The hellscape: a dark, slow
T. rex that comes for you, bites if it reaches you, and goes down in a few shots. Leaving a level takes them away.
Usage: python3 dev/test_323.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 240})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(400)
        await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.DEV.ok = false; D.setSeed(4242); D.setVR(true); D.vr.on = true;
          D.setMode('hunt'); Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .7, rough: .5, huntMap: 'globe', dino: false });
          D.generate(); D.state = 'play'; for (let i = 0; i < 20; i++) { D.endlessTick(1 / 30); D.geoTick(1 / 30); } D.MP.code = '9999'; D.set.geoNet = true; D.MP.hp = 100;
          window.run = (secs, f) => { const dt = 1 / 30; for (let i = 0; i < secs * 30; i++) { D.camera.position.set(D.P.x, D.P.y + 1.6, D.P.z); D.ugBeastsTick(dt); if (f) f(i * dt); } };
          // stand in an open hall cell near the middle of a level's grid
          window.standGrid = () => { const L = D.UNDER.cur, G = L.g; let best = null; for (let k = 0; k < G.N * G.M; k++) { if (G.open[k] !== 1) continue; const [x, z] = D.ugCellXZ(G, k), c = Math.hypot(x - (G.x0 + G.N * G.C / 2), z - (G.z0 + G.M * G.C / 2)); if (!best || c < best[2]) best = [x, z, c]; }
            D.P.x = D.UG_X + best[0]; D.P.z = D.UG_Z + best[1]; D.P.y = L.Y + L.fy; };
          return 1; }""")
        out = {}
        for lvl in (1, 2):
            r = await pg.evaluate("""(lvl) => { D.ugEnter(lvl); standGrid(); const U = D.UGB, o = {};
              run(55); o.at55 = U.list.length;
              run(40); const A = U.list[0]; o.at95 = U.list.length; o.eyes = A && A.eyes ? A.eyes.length : 0; if (!A) return o;
              let minD = 1e9, seen = 0, bites = 0, hp = 100, charges = 0, g0 = '';
              run(180, () => { const L = D.UNDER.cur, [px, pz] = D.ugLocal(D.P.x, D.P.z), d = Math.hypot(A.ul[0] - px, A.ul[1] - pz); minD = Math.min(minD, d);
                if (D.MP.hp < hp) bites++; D.MP.hp = hp = 100; if (A.ugs.goal === 'charge' && g0 !== 'charge') charges++; g0 = A.ugs.goal;
                if (A.root.visible && d < 30 && D.ugLos(L, px, pz, A.ul[0], A.ul[1])) seen++; });
              o.minD = Math.round(minD * 10) / 10; o.seenFrames = seen; o.bites = bites; o.charges = charges; o.size = +(A.scale || 1).toFixed(2);
              // a bullet down the hall: it reaches the raptor; one into a wall stops there
              { const L = D.UNDER.cur, G = L.g, [px, pz] = D.ugLocal(D.P.x, D.P.z), pk = D.ugCellOf(G, px, pz); let spot = null;
                for (const [di, dj] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { let k = pk, n = 0; while (n < 6) { const i = k % G.N, j = (k - i) / G.N, k2 = (i + di) + (j + dj) * G.N; if (!D.ugLos(L, px, pz, ...D.ugCellXZ(G, k2))) break; k = k2; n++; } if (n >= 3 && !spot) spot = D.ugCellXZ(G, k); }
                if (spot) { A.ul = spot.slice(); A.x = D.UG_X + spot[0]; A.z = D.UG_Z + spot[1]; A.y = L.Y + L.fy; A.root.position.set(A.x, A.y, A.z); A.root.updateMatrixWorld(true);
                  const from = new D.THREE.Vector3(D.P.x, D.P.y + 1.0, D.P.z), dir = new D.THREE.Vector3(A.x - from.x, A.y + .6 - from.y, A.z - from.z).normalize(); const h = D.castShot(from, dir, 60); o.bullet = h.kind;
                  const back = dir.clone().negate(); back.y = 0; back.normalize(); const w = D.castShot(from, back, 60); o.wall = [w.kind, +w.p.distanceTo(from).toFixed(1)]; } }
              // shot: it's hurt, and two sniper hits drop it
              const hp0 = A.hp; D.hitAnimal(A, 10, 0, false, 'hunt', 1); o.shot = [A.hp < hp0, !A.dead]; D.hitAnimal(A, 10, 0, false, 'hunt', 1); o.dead = A.dead;
              return o; }""", lvl)
            out["backrooms" if lvl == 1 else "bunker"] = r
        r = await pg.evaluate("""() => { D.ugEnter(3); const U = D.UGB, A = U.list[0], o = { rex: !!A && A.kind === 'trex', hp: A && A.hpMax };
          if (!A) return o; const [ax, az] = A.ul; D.P.x = D.UG_X + ax + 22; D.P.z = D.UG_Z + az; D.P.y = D.UNDER.cur.Y + 2; D.MP.hp = 100;
          const d0 = 22; let maxSp = 0; run(5, () => { maxSp = Math.max(maxSp, A.speed); }); const [bx, bz] = A.ul; o.closedIn = +(d0 - Math.hypot(D.P.x - D.UG_X - bx, D.P.z - D.UG_Z - bz)).toFixed(1); o.maxSpeed = +maxSp.toFixed(2);
          A.ul = [D.P.x - D.UG_X - 3.5, D.P.z - D.UG_Z]; run(4); o.bitten = 100 - D.MP.hp; D.MP.hp = 100;
          let shots = 0; while (!A.dead && shots < 20) { D.hitAnimal(A, 15, 0, false, 'hunt', 1); shots++; } o.sniperShots = shots; o.dead = A.dead;
          D.ugLeave(null); o.cleared = [U.list.length, D.beasts.filter(B => B.ug).length]; return o; }""")
        out["hell"] = r
        print(json.dumps(out)); print("errors:", errs[:5] or "none")
        br, bu, h = out["backrooms"], out["bunker"], out["hell"]
        ok = all(x["at55"] == 0 and x["at95"] == 1 and x["seenFrames"] > 15 and x["bites"] >= 1 and x["charges"] >= 1 and x["size"] < 1 and x["shot"] == [True, True] and x["dead"] and x.get("bullet") == "animal" and x["wall"][0] == "rock" and x["wall"][1] < 40 for x in (br, bu)) \
             and br["eyes"] == 0 and bu["eyes"] == 2 and h["rex"] and h["hp"] <= 500 and h["closedIn"] > 3 and h["maxSpeed"] < 2.6 and h["bitten"] > 0 and h["sniperShots"] <= 4 and h["dead"] and h["cleared"] == [0, 0] and not errs
        print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
