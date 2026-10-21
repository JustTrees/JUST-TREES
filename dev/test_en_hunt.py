"""2.23: Endless in Hunting (a headset): the menu choice makes an endless map; the animals of each area are out, guns and bows lie about,
a kill scores; walking 3 km keeps animals and guns round you and clears the old ones; a gun you took stays taken.
Prehistoric: dinosaurs instead (no birds), pteranodons over some squares, now and then a T. rex, and the raptor still comes hunting.
Usage: python3 dev/test_en_hunt.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
QUICK = __import__('os').environ.get('JT_QUICK') == '1'   # run_all's quick run: shorter walks
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setSeed(4242); D.setVR(true); D.setMode('hunt'); D.vr.on = true;
          Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .5, rough: .5, huntMap: 'endless', dino: false, size: 'medium' });
          D.generate(); D.state = 'play';
          window.tick = n => { for (let f = 0; f < n; f++) { D.endlessTick(1 / 72); D.updateAnimals(1 / 72); } };
          tick(72 * 3);
          const B = D.beasts, ground = B.filter(A => A.ecellB === undefined && !A.ptero), near = d => [...D.DROPS.values()].filter(o => Math.hypot(o.x - D.P.x, o.z - D.P.z) < d).length;
          const A = ground.sort((a, c) => Math.hypot(a.x - D.P.x, a.z - D.P.z) - Math.hypot(c.x - D.P.x, c.z - D.P.z))[0], s0 = D.hunt.score; D.killAnimal(A, 120);
          return { map: D.HIKEMAP, ground: ground.length, birds: B.length - ground.length, kinds: [...new Set(ground.map(A => A.kind))], guns: D.DROPS.size, gunsNear300: near(300), kill: [A.kind, A.dead, +(D.hunt.score - s0).toFixed(1)], killed: A.dead }; }""")
        print("hunt", json.dumps(r))
        w = await pg.evaluate("""(Q) => { const dt = 1 / 72, x0 = D.P.x; const g0 = [...D.DROPS.values()].sort((a, c) => Math.hypot(a.x - D.P.x, a.z - D.P.z) - Math.hypot(c.x - D.P.x, c.z - D.P.z))[0]; const took = g0.id; D.dropTake(took);
          let maxGuns = 0, minGunsNear = 1e9, minAnimals = 1e9, far = 0, legends = 0, reds = 0;
          while (D.P.x - x0 < (Q ? 2000 : 3000)) { D.P.x += 10 * dt; D.P.y = D.H(D.P.x, D.P.z); D.endlessTick(dt); D.updateAnimals(dt);
            if (Math.round((D.P.x - x0) / 10 / dt) % 72 === 0 && D.P.x - x0 > 300) { const ds = [...D.DROPS.values()]; maxGuns = Math.max(maxGuns, ds.length); minGunsNear = Math.min(minGunsNear, ds.filter(o => Math.hypot(o.x - D.P.x, o.z - D.P.z) < 300).length);
              for (const o of ds) far = Math.max(far, Math.hypot(o.x - D.P.x, o.z - D.P.z)); minAnimals = Math.min(minAnimals, D.beasts.filter(A => Math.hypot(A.x - D.P.x, A.z - D.P.z) < 700).length);
              legends = Math.max(legends, D.beasts.filter(A => A.kind === 'bigfoot' || A.kind === 'yeti').length); reds = Math.max(reds, ds.filter(o => o.tier === 5).length); } }
          D.P.x = x0; D.P.z = 0; D.enEnsure(D.P.x, D.P.z, 300); for (let f = 0; f < 72 * 4; f++) { D.endlessTick(dt); D.updateAnimals(dt); }
          return { maxGuns, minGunsNear300: minGunsNear, farthestGunM: Math.round(far), minAnimals700: minAnimals, legendsSeen: legends, redSnipers: reds, tookBack: D.DROPS.has(took), backGuns: D.DROPS.size }; }""", QUICK)
        print("walk", json.dumps(w))
        d = await pg.evaluate("""(Q) => { D.set.dino = true; D.setSeed(5151); D.generate(); D.state = 'play'; tick(72 * 3);
          const B = D.beasts, kinds = {}; for (const A of B) kinds[A.kind] = (kinds[A.kind] || 0) + 1;
          D.DINO.gap = 0; D.DINO.pending = 0; D.dinoStartHunt(); let t = 0; while (!D.DINO.hunter && t < 8) { tick(1); t += 1 / 72; } const hunter = D.DINO.hunter ? D.DINO.hunter.kind : D.beasts.some(A => A.rexOn) ? 'rex' : false;
          let rex = 0; const dt = 1 / 72, x0 = D.P.x; while (D.P.x - x0 < (Q ? 1000 : 3000)) { D.P.x += 14 * dt; D.P.y = D.H(D.P.x, D.P.z); D.endlessTick(dt); D.updateAnimals(dt); if (D.beasts.some(A => A.kind === 'trex')) rex = 1; }
          return { on: D.DINO.on, kinds, hunter, rexMet: rex, pteros: D.beasts.filter(A => A.ptero).length }; }""", QUICK)
        print("dino", json.dumps(d))
        dk = set(d["kinds"]); okd = d["on"] and dk and dk <= {"triceratops", "parasaur", "stego", "bronto", "trex", "ptero", "raptor"} and d["hunter"] in ("raptor", "rex")
        ok = r["map"] == "endless" and r["ground"] >= 15 and r["guns"] > 50 and r["gunsNear300"] >= 5 and r["killed"] and r["kill"][2] > 0 \
             and w["minGunsNear300"] >= 3 and w["maxGuns"] < 1500 and w["farthestGunM"] < 2000 and w["minAnimals700"] >= 4 and not w["tookBack"] and w["backGuns"] > 50 and okd and not errs
        print("errors", errs[:5]); print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
