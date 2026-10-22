"""2.50: the T. rex hunt is running only (no climbing, no flinging: rexChase), and if you get more than ~100 m out a second T. rex
comes in ahead of you (only one extra; it goes off when the hunt ends). Raptors hunt in packs: 30% two, 15% three; the pack
spreads round you, charges one at a time, and the next one carries on if the first goes. No raptor pack during a T. rex hunt."""
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
          D.setSeed(5); D.setVR(true); D.setMode('hunt'); D.set.dino = true; D.set.env = 'climate'; D.set.land = 'natural'; D.set.size = 'large'; D.set.lat = 42; D.set.month = 6; D.set.weather = 'clear'; D.set.density = .6; D.generate(); D.state = 'play';
          const P = D.P, R = D.beasts.find(A => A.kind === 'trex');
          const ground = () => { P.y = D.groundAt(P.x, P.z); D.vr.climbing = false; D.vr.cl = null; D.camera.position.set(P.x, P.y + 1.7, P.z); D.camera.updateMatrixWorld(); };
          const step = (secs, f) => { for (let i = 0; i < secs * 30; i++) { D.updateAnimals(1 / 30); if (f && f(i / 30)) return true; } return false; };
          const place = dist => { for (let k = 0; k < 16; k++) { const a = k * .39; P.x = R.x + Math.cos(a) * dist; P.z = R.z + Math.sin(a) * dist; if (D.okSpot(P.x, P.z) && D.H(P.x, P.z) > D.water + 1) break; } ground(); };
          D.UW.drown = 0; out.before = D.rexChase();
          place(140); D.DINO.gap = 1e9; D.rexStart(R); out.during = D.rexChase();
          // keep away from it: you're well out, so a second one comes in ahead of you
          let two = null, maxRun = 0;
          step(20, t => { const d = Math.hypot(P.x - R.x, P.z - R.z); if (d < 120) { const a = Math.atan2(P.x - R.x, P.z - R.z); P.x = R.x + Math.sin(a) * 140; P.z = R.z + Math.cos(a) * 140; ground(); }
            maxRun = Math.max(maxRun, R.want || 0); D.UW.drown = 0; const X = D.beasts.filter(A => A.kind === 'trex' && A.extra && !A.dead); if (X.length && two === null) two = { t, n: X.length, d: Math.round(Math.hypot(X[0].x - P.x, X[0].z - P.z)), on: !!X[0].rexOn }; });
          out.two = two; out.extras = D.beasts.filter(A => A.kind === 'trex' && A.extra).length;
          const E = D.beasts.find(A => A.kind === 'trex' && A.extra);
          // the extra runs at you too
          if (E) { const d0 = Math.hypot(E.x - P.x, E.z - P.z); step(4, () => { D.UW.drown = 0; }); out.closing = Math.round(d0 - Math.hypot(E.x - P.x, E.z - P.z)); }
          out.maxRun = maxRun;
          // give up: both stop; the extra goes off
          D.rexGiveUp(R); out.after = { lead: !!R.rexOn, extra: E ? !!E.rexOn : null, leaving: E ? !!E.leaving : null, chase: D.rexChase() };
          if (E) { P.x = E.x + 200; P.z = E.z; ground(); step(2); D.dinoTick(1 / 30); out.extraGone = !D.beasts.includes(E); }
          // raptor packs: count sizes over many hunts
          place(0); P.x = 0; P.z = 0; for (let k = 0; k < 60 && !(D.okSpot(P.x, P.z) && D.H(P.x, P.z) > D.water + 1); k++) { P.x = (Math.random() - .5) * 400; P.z = (Math.random() - .5) * 400; } ground();
          const sizes = [0, 0, 0, 0]; let spread = null, firstCharge = null;
          for (let i = 0; i < 200; i++) { for (const B of D.beasts.filter(B => B.hunter)) D.dinoRemove(B); D.DINO.hunter = null; D.DINO.pack = []; R.rexOn = false;
            D.dinoSpawnHunter(); const L = (D.DINO.pack || []).length; sizes[L]++;
            if (L === 3 && !spread) { const [a, b, c] = D.DINO.pack; spread = { ring: [a.ringK || 1, b.ringK, c.ringK], orbit: [a.orbit, b.orbit, c.orbit], near: Math.round(Math.max(Math.hypot(a.x - b.x, a.z - b.z), Math.hypot(a.x - c.x, a.z - c.z))) }; } }
          out.sizes = sizes;
          // a pack of 2 hunts: one charge at a time; when the leader goes the other carries on
          let pk = null; for (let i = 0; i < 60 && !pk; i++) { for (const B of D.beasts.filter(B => B.hunter)) D.dinoRemove(B); D.DINO.hunter = null; D.DINO.pack = []; D.dinoSpawnHunter(); if (D.DINO.pack.length >= 2) pk = D.DINO.pack.slice(); }
          if (pk) { const [a, b] = pk; for (const X of pk) X.hs = 'stalk'; D.DINO.lastCharge = 0; D.dinoCharge(a); D.dinoCharge(b); out.charges = [a.hs, b.hs];
            a.dead = true; D.dinoTick(1 / 30); out.carryOn = D.DINO.hunter === b;
            // a T. rex hunt clears the pack off
            b.dead = false; b.hs = 'stalk'; D.rexStart(R); out.packLeaves = b.hs === 'leave' || !!b.gone; R.rexOn = false; }
          return out; }""")
        print(json.dumps(r))
        s = r["sizes"]
        ok = not r["before"] and r["during"] and r["two"] and r["two"]["n"] == 1 and r["two"]["on"] and 90 <= r["two"]["d"] <= 170 and r["extras"] == 1 \
             and r["closing"] > 10 and r["maxRun"] >= 10.5 and not r["after"]["lead"] and not r["after"]["extra"] and r["after"]["leaving"] and not r["after"]["chase"] and r["extraGone"] \
             and s[1] > 80 and 30 < s[2] < 90 and 12 < s[3] < 50 \
             and r["charges"] == ["charge", "stalk"] and r["carryOn"] and r["packLeaves"]
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
