"""2.22: animals on endless hikes. Builds an endless hike (as in a headset), then checks:
- animals are out round you at the start (ground animals and birds), each kind one that lives in the environment where it stands
- walking 3 km: new animals only ever turn up far off (beyond where animals are drawn), the ones left far behind are taken away,
  there are always animals round you, the count stays under the cap, and none stand in water
- the island maps' hunting animals are untouched (that's the other animal tests)
Usage: python3 dev/test_en_animals.py dbg.html [walk_km]"""
import sys, asyncio, json
from playwright.async_api import async_playwright
num = [a for a in sys.argv[2:] if a.replace('.', '', 1).isdigit()]
KM = float(num[0]) if num else 3
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setSeed(4242); D.setVR(true); D.setMode('hike'); D.hikeForce = 'endless';
          Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .5, rough: .5 }); D.generate(); D.vr.on = true; D.state = 'play';
          for (let f = 0; f < 72 * 3; f++) { D.endlessTick(1 / 72); D.updateAnimals(1 / 72); }
          const NAT = D.NATIVE_ALL(), B = D.beasts, fly = A => A.ecellB !== undefined, native = A => { for (const [dx, dz] of [[0, 0], [300, 0], [-300, 0], [0, 300], [0, -300]]) if (NAT[D.enDom(A.x + dx, A.z + dz).b].some(e => e[0] === A.kind)) return true; return false; };
          const ground = B.filter(A => !fly(A)), kinds = {}; for (const A of B) kinds[A.kind] = (kinds[A.kind] || 0) + 1;
          return { ground: ground.length, birds: B.length - ground.length, kinds, notNative: B.filter(A => !native(A)).map(A => A.kind), nearest: Math.round(Math.min(...ground.map(A => Math.hypot(A.x - D.P.x, A.z - D.P.z)))),
                   within700: ground.filter(A => Math.hypot(A.x - D.P.x, A.z - D.P.z) < 700).length, envs: [...new Set(ground.map(A => D.enDom(A.x, A.z).b))] }; }""")
        print("start", json.dumps(r))
        w = await pg.evaluate("""(km) => { const E = D.ENDLESS, B = D.beasts, dt = 1 / 72, speed = 10, seen = new WeakSet(), x0 = D.P.x;
          for (const A of B) seen.add(A);
          let popClosest = 1e9, popN = 0, minAround = 1e9, maxFar = 0, maxN = 0, wet = 0, ms = 0, frames = 0, worst = 0; const envs = new Set(), kinds = new Set();
          while (D.P.x - x0 < km * 1000) {
            D.P.x += speed * dt; D.P.z += Math.sin(D.P.x / 900) * speed * dt * .5; D.P.y = D.H(D.P.x, D.P.z);
            D.endlessTick(dt); const t0 = performance.now(); D.updateAnimals(dt); const t = performance.now() - t0; ms += t; worst = Math.max(worst, t); frames++;
            for (const A of B) if (!seen.has(A)) { seen.add(A); if (A.ecellB === undefined) { popN++; popClosest = Math.min(popClosest, Math.hypot(A.x - D.P.x, A.z - D.P.z)); kinds.add(A.kind); envs.add(D.enDom(A.x, A.z).b); } }
            if (frames % 72 === 0) {
              let around = 0; for (const A of B) { const d = Math.hypot(A.x - D.P.x, A.z - D.P.z); if (A.ecellB === undefined) { if (d < 700) around++; maxFar = Math.max(maxFar, d); if (A.kind !== 'seal' && D.H(A.x, A.z) < D.water - .5) wet++; } }
              if (D.P.x - x0 > 400) minAround = Math.min(minAround, around); maxN = Math.max(maxN, B.length);
            }
          }
          return { frames, avgMs: +(ms / frames).toFixed(3), worstMs: +worst.toFixed(1), newGround: popN, newClosestM: Math.round(popClosest), minWithin700: minAround, farthestM: Math.round(maxFar), maxCount: maxN, inWater: wet,
                   made: E.aMade, dropped: E.aDropped, kinds: [...kinds], envs: [...envs] }; }""", KM)
        print("walk", json.dumps(w))
        ok = r["ground"] >= 15 and r["birds"] >= 1 and len(r["notNative"]) <= max(1, r["ground"] // 10) and r["nearest"] >= 30 and r["within700"] >= 6 \
             and w["newGround"] > 20 and w["newClosestM"] >= 690 and w["minWithin700"] >= 4 and w["farthestM"] < 1400 and w["maxCount"] <= 170 and w["inWater"] <= 2 and w["dropped"] > 10 and not errs
        print("errors", errs[:5]); print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
