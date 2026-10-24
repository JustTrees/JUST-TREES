"""2.73: in Geocaching the predators hunt you (and nowhere else). A wolf pack circles, then darts in to bite; a bear you walk up on
charges, mauls, and takes several shots; a mountain lion stalks from behind and pounces; a gator lunges from the water's edge; bear
spray turns them away. Bites take health; killed (or drowned) you wake somewhere random on the planet. Normal Hunting: they still run.
Usage: python3 dev/test_273.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
GEN = """(mode) => { window.FREEZE = true; D.renderer.setAnimationLoop(null); try { localStorage.removeItem('jt-geo'); } catch (_) {}
  D.DEV.ok = true; D.setSeed(4242); D.setVR(true); D.setMode('hunt'); D.vr.on = true;
  Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .5, rough: .5, huntMap: mode, dino: false });
  D.generate(); D.state = 'play'; window.tick = (n, f) => { for (let i = 0; i < n; i++) { if (f) f(i); D.endlessTick(1 / 30); D.updateAnimals(1 / 30); if (D.GEO.on) D.geoTick(1 / 30); } };
  tick(30); for (const A of [...D.beasts]) { A.x += 5000; A.gone = true; }   // (just the ones we put out)
  window.put = (k, dx, dz, grp) => { let x = D.P.x + dx, z = D.P.z + dz; for (let t = 0; t < 40 && !(D.H(x, z) > D.water + .5); t++) { x += 7; z += 3; } const A = D.addGround(k, x, z); A.grp = grp || 0; return A; };
  return true; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        await pg.evaluate(GEN, "globe")
        r = await pg.evaluate("""() => { const o = {}, P = D.P; const still = () => { P.y = D.groundAt(P.x, P.z); D.camera.position.set(P.x, P.y + 1.7, P.z); D.camera.lookAt(P.x, P.y + 1.7, P.z - 10); D.camera.updateMatrixWorld(); };
          still(); D.MP.hp = 100; D.GEO.food = D.GEO.water = 100;
          // a wolf pack: circles, then they dart in and bite
          const W = [0, 1, 2, 3].map(i => put('wolf', 40 + i * 3, 10, 77)); D.predGo(W[0], 'circle', { a: 0, r: 26, dir: 1, wait: 3, pack: 4 }); W.slice(1).forEach((A, i) => D.predGo(A, 'circle', { a: i, r: 26, dir: 1, wait: 5 + i * 2, pack: 4 }));
          let minD = 1e9, circled = 0; tick(30 * 25, () => { still(); for (const A of W) { const d = Math.hypot(A.x - P.x, A.z - P.z); minD = Math.min(minD, d); if (A.pred && A.pred.st === 'circle' && d > 18 && d < 40) circled++; } });
          o.wolves = [Math.round(100 - D.MP.hp), +minD.toFixed(1), circled > 30];
          // bear spray: they all turn away
          const sp = D.GEO.spray; D.GEO.items.add('spray'); D.GEO.spray = 4; const W0 = W.find(A => !A.dead); W0.x = P.x; W0.z = P.z - 7; D.predGo(W0, 'dart');
          D.geoSpray({ rayPos: new D.THREE.Vector3(P.x, P.y + 1.3, P.z), rayQ: new D.THREE.Quaternion(), pos: new D.THREE.Vector3(P.x, P.y + 1.3, P.z) }); o.spray = [!W0.pred, W0.predCool > 0];
          for (const A of W) { A.gone = true; A.x += 9000; }
          // a bear you walk up on: it charges; it takes several shots
          D.MP.hp = 100; const B = put('bear', 12, -6, 5); B.predCool = 0; D.predWatch(); o.bearCharge = B.pred && B.pred.st;
          tick(30 * 6, () => still()); o.bearBit = Math.round(100 - D.MP.hp);
          D.predCalm(B, 0); D.hitAnimal(B, 20, 0, false, 'ar'); o.bearShot1 = [B.dead, B.pred && B.pred.st]; D.hitAnimal(B, 20, 0, false, 'ar'); D.hitAnimal(B, 20, 0, false, 'ar'); o.bear3 = B.dead; D.hitAnimal(B, 20, 0, false, 'ar'); o.bear4 = B.dead;
          // a mountain lion stalks from behind and pounces
          D.MP.hp = 100; const L = put('panther', -6, 80, 6); D.predGo(L, 'stalk'); let pounced = false; tick(30 * 30, () => { still(); if (L.pred && L.pred.st === 'pounce') pounced = true; }); o.lion = [pounced, Math.round(100 - D.MP.hp)];
          L.gone = true;
          // death: you wake somewhere random on the planet
          const ll0 = [D.GLOBE.lat, D.GLOBE.lon], s0 = D.hunt.score = 30; D.MP.hp = 0; D.uwRespawn(); tick(30);
          o.respawn = [Math.round(D.glArc(D.GLOBE.p, D.glFromLL(ll0[0], ll0[1])) * D.GLOBE.R), Math.round(D.MP.hp), D.hunt.score, D.H(P.x, P.z) > D.water, [...D.ENDLESS.chunks.values()].filter(c => c.tile).length];
          return o; }""")
        print("geo", json.dumps(r))
        await pg.evaluate(GEN, "endless")
        n = await pg.evaluate("""() => { const B = put('bear', 10, -5, 5); D.predWatch(); D.tick = 0; tick(30 * 3); return [!!B.pred, D.GEO.on]; }""")
        print("normal", json.dumps(n))
        ok = r["wolves"][0] >= 10 and r["wolves"][1] < 3 and r["wolves"][2] and r["spray"] == [True, True] and r["bearCharge"] == "charge" and r["bearBit"] >= 20 \
             and r["bearShot1"] == [False, "charge"] and not r["bear3"] and r["bear4"] and r["lion"][0] and r["lion"][1] >= 20 \
             and r["respawn"][0] > 1500 and r["respawn"][1] == 60 and r["respawn"][2] == 20 and r["respawn"][3] and r["respawn"][4] >= 4 and n == [False, False]
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
