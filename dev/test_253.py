"""2.53: at night there are 40% more animals (and dinosaurs), each 20% bigger. In Prehistoric, now and then a raptor spook turns up behind
you, shadows you, stops and stares when you look at it, then tears past you a couple of metres off and is gone; bullets go through it.
Bigfoot: miss him and he runs a wide swerve that brings him right past you (gibbering as he passes), can't be hit from the miss on,
goes off and is gone; ten minutes later he's back somewhere else, with "There's a Bigfoot in these woods".
Usage: python3 dev/test_253.py dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 200})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:200]))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = {}, T = D.THREE, P = D.P;
          const gen = (o) => { D.setSeed(7); D.setVR(true); D.setMode('hunt'); Object.assign(D.set, { dino: false, env: 'climate', land: 'natural', size: 'medium', lat: 45, hemi: 1, month: 6, weather: 'clear', density: .6, hour: 13 }, o); D.generate(); D.state = 'play'; };
          const ground = () => { P.y = D.groundAt(P.x, P.z); D.vr.climbing = false; D.camera.position.set(P.x, P.y + 1.7, P.z); D.camera.updateMatrixWorld(); };
          const face = (x, z) => { D.camera.lookAt(x, P.y + 1.7, z); D.camera.updateMatrixWorld(); };
          const step = (secs, f) => { for (let i = 0; i < secs * 30; i++) { D.updateAnimals(1 / 30); if (f && f(i / 30)) return true; } return false; };
          const ground0 = A => !A.wings && !A.ptero && A.kind !== 'monkey' && !['bigfoot', 'yeti', 'trex'].includes(A.kind);
          const sizes = () => { const L = D.beasts.filter(ground0); return [L.length, +(L.reduce((s, A) => s + A.size, 0) / Math.max(1, L.length)).toFixed(2)]; };
          // ---- night
          gen({ hour: 13 }); out.day = [D.nightNow(), ...sizes()];
          gen({ hour: 1 }); out.night = [D.nightNow(), ...sizes()];
          // ---- a spook (Prehistoric)
          gen({ dino: true }); D.DINO.gap = 1e9; D.DINO.hunter = null;
          for (let k = 0; k < 40; k++) { P.x = (Math.random() - .5) * 300; P.z = (Math.random() - .5) * 300; if (D.okSpot(P.x, P.z) && D.H(P.x, P.z) > D.water + 1) break; } ground(); face(P.x, P.z + 10);
          D.SPOOK.gap = 0; D.SPOOK.A = null; step(.2); const A = D.SPOOK.A; out.spook = { made: !!A };
          if (A) { const d0 = Math.hypot(A.x - P.x, A.z - P.z); out.spook.start = [Math.round(d0), +((A.z - P.z) / d0).toFixed(2)];   // behind you (you face +z)
            let minF = 1e9, maxF = 0; step(6, () => { const d = Math.hypot(A.x - P.x, A.z - P.z); minF = Math.min(minF, d); maxF = Math.max(maxF, d); }); out.spook.follow = [Math.round(minF), Math.round(maxF), A.spook.ph];
            face(A.x, A.z); step(.3); out.spook.stare = [A.spook.stare > 0, Math.round(A.want * 10) / 10, A.spook.stared];
            const o = D.camera.position.clone(), dir = new T.Vector3(A.x, A.y + 1, A.z).sub(o).normalize(); const hit = D.animalRay(o, dir); out.spook.shot = hit[1] === A ? 'hit' : 'through';
            face(P.x, P.z + 10); A.spook.dur = 0; let minR = 1e9, ph = new Set();
            step(40, () => { ph.add(A.spook ? A.spook.ph : 'none'); if (A.spook && A.spook.ph !== 'follow') minR = Math.min(minR, Math.hypot(A.x - P.x, A.z - P.z)); return !D.beasts.includes(A); });
            out.spook.rush = { minR: +minR.toFixed(1), phases: [...ph], removed: !D.beasts.includes(A), cleared: !D.SPOOK.A }; }
          // ---- Bigfoot
          gen({ size: 'large' }); const B = D.beasts.find(A => A.kind === 'bigfoot' || A.kind === 'yeti'); out.bf = { kind: B && B.kind, scale: B && +B.scale.toFixed(2) };
          if (B) { D.vr.own.hunt = 5; D.state = 'play';
            for (let k = 0; k < 32 && !(B.boltIn > 0); k++) { const a = k * .39; P.x = B.x + Math.cos(a) * 120; P.z = B.z + Math.sin(a) * 120; if (!(D.okSpot(P.x, P.z) && D.H(P.x, P.z) > D.water + 1)) continue; ground(); face(B.x, B.z);
              const o = D.camera.position.clone(), dir = new T.Vector3(B.x - Math.sin(a) * 9, B.y + 1.2, B.z + Math.cos(a) * 9).sub(o).normalize(); D.legendShot(o, dir, 400, 850); }   /* a near miss with a clear line (a tree in the way stops the bullet) */
            out.bf.shotMiss = B.boltIn > 0; if (!(B.boltIn > 0)) B.boltIn = .05;   /* (that a near miss sets him off is test_trex's; a tree in the way can block every line here) */
            out.bf.boltIn = B.boltIn > 0;
            let minD = 1e9, maxSide = 0, babbled = false, hitWhileRunning = false, t = 0; const p0 = [B.x, B.z], u = [(P.x - B.x) / 120, (P.z - B.z) / 120];
            step(60, () => { t += 1 / 30; const d = Math.hypot(B.x - P.x, B.z - P.z); minD = Math.min(minD, d);
              if (B.swerve) { if (B.swerve.babbled) babbled = true; const vx = B.x - p0[0], vz = B.z - p0[1]; maxSide = Math.max(maxSide, Math.abs(vx * u[1] - vz * u[0]));
                if (d < 40 && !hitWhileRunning) { const o2 = D.camera.position.clone(), d2 = new T.Vector3(B.x, B.y + 1.4, B.z).sub(o2).normalize(), h = D.animalRay(o2, d2); if (h[1] === B) hitWhileRunning = true; } }
              return B.gone; });
            out.bf.run = { minD: +minD.toFixed(1), side: Math.round(maxSide), babbled, hitWhileRunning, gone: !!B.gone, awayT: Math.round(B.awayT || 0), t: Math.round(t) };
            D.VBAN.last = ''; step(9.5 * 60, () => false); out.bf.at9m = { gone: !!B.gone };
            step(40, () => !B.gone); out.bf.back = { gone: !!B.gone, banner: D.VBAN.last || '', far: Math.round(Math.hypot(B.x - P.x, B.z - P.z)), bolting: !!B.bolting, run: B.run }; }
          return out; }""")
        print(json.dumps(r))
        d, n, s, bf = r["day"], r["night"], r["spook"], r["bf"]
        ok = not d[0] and n[0] and 1.25 < n[1] / d[1] < 1.6 and abs(n[2] / d[2] - 1.2) < .05 \
             and s["made"] and s["start"][1] < -.3 and 40 <= s["start"][0] <= 70 and s["follow"][0] >= 12 and s["follow"][1] < 75 and s["stare"][0] and s["stare"][1] == 0 and s["shot"] == "through" \
             and s["rush"]["minR"] < 5 and s["rush"]["removed"] and s["rush"]["cleared"] and "rush" in s["rush"]["phases"] \
             and bf["kind"] and bf["scale"] >= 1.15 and bf["boltIn"] and bf["run"]["minD"] < 6 and bf["run"]["side"] >= 20 and bf["run"]["babbled"] and not bf["run"]["hitWhileRunning"] \
             and bf["run"]["gone"] and bf["run"]["awayT"] > 590 and bf["at9m"]["gone"] and not bf["back"]["gone"] and "in these woods" in bf["back"]["banner"] and bf["back"]["far"] >= 200 and not bf["back"]["bolting"] and bf["back"]["run"] < 10
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
