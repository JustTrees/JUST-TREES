"""T. rex (1.80): Dino mode's legend, like Bigfoot: one on Large maps and up, unseen (and silent) until you pick up the red sniper
("There's a T. rex in these woods"). It roams the whole map without getting stuck. Shoot at it (a hit or a near miss) and it comes
for you: never straight, swinging side to side, screaming, rearing up to roar a few times on the way. Twice the raptor (~10 sniper hits),
never heals. Inside 15 m it gets you (red blackout, wake up elsewhere) and it goes back to roaming. A climb over 6 m saves you (it paces
below, then gives up); a low branch doesn't. No raptor hunts while it's after you."""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 200})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = {}, T = D.THREE;
          const gen = (size, sd) => { D.setSeed(sd); D.setVR(true); D.setMode('hunt'); D.set.dino = true; D.set.env = 'climate'; D.set.land = 'natural'; D.set.size = size; D.set.lat = 42; D.set.month = 6; D.set.weather = 'clear'; D.set.density = .6; D.generate(); D.state = 'play'; };
          gen('medium', 5); out.medium = D.beasts.filter(A => A.kind === 'trex').length;
          gen('large', 5); const X = D.beasts.filter(A => A.kind === 'trex'); out.large = X.length; const R = X[0], P = D.P;
          const ground = () => { P.y = D.groundAt(P.x, P.z); D.vr.climbing = false; D.vr.cl = null; D.camera.position.set(P.x, P.y + 1.7, P.z); D.camera.updateMatrixWorld(); };
          const step = (secs, f) => { for (let i = 0; i < secs * 30; i++) { D.updateAnimals(1 / 30); if (f && f(i / 30)) return true; } return false; };
          D.setLoot({ pistol: 1 }); P.x = R.x + 60; P.z = R.z; ground(); step(1);
          out.hidden = { seen: D.legendSeen(), visible: R.root.visible, hp: R.hpMax, thru: !!R.thru };
          D.dropUse({ type: 'gun', kind: 'hunt', tier: 5, x: 0, y: 0, z: 0, id: 'gRed' }); step(1);
          const cv = D.VBAN.m && D.VBAN.m.userData; out.revealed = { seen: D.legendSeen(), visible: R.root.visible };
          // roaming: far and free
          const p0 = [R.x, R.z]; let far = 0, streak = 0, worst = 0, lp = [R.x, R.z];
          step(150, t => { far = Math.max(far, Math.hypot(R.x - p0[0], R.z - p0[1])); if (Math.round(t * 30) % 30 === 0) { streak = Math.hypot(R.x - lp[0], R.z - lp[1]) < .3 ? streak + 1 : 0; worst = Math.max(worst, streak); lp = [R.x, R.z]; } });
          out.roam = { far: Math.round(far), worstStuck: worst, on: !!R.rexOn };
          // shot from 120 m: it comes for you, side to side, rearing to roar, and gets you
          const go = (dist, high) => { for (let k = 0; k < 16; k++) { const a = k * .39; P.x = R.x + Math.cos(a) * dist; P.z = R.z + Math.sin(a) * dist; if (D.okSpot(P.x, P.z) && D.H(P.x, P.z) > D.water + 1) break; } ground(); /* dry ground it can reach */ if (high) { P.y += high; D.vr.climbing = true; } D.UW.drown = 0; D.UW.red = 0; R.rexOn = false; };
          go(120); D.hitAnimal(R, 120, 0, false, 'hunt'); const hp0 = R.hp; let rears = 0, wasRear = false, lat = 0, nL = 0, prev = [R.x, R.z], got = null, raptors = 0; D.DINO.gap = 0;
          step(70, t => { const rr = R.rearT > 0; if (rr && !wasRear) rears++; wasRear = rr; const vx = R.x - prev[0], vz = R.z - prev[1], d = Math.hypot(P.x - R.x, P.z - R.z), sp = Math.hypot(vx, vz);
            if (sp > .05 && d > 25) { lat += Math.abs(vx * (P.z - R.z) - vz * (P.x - R.x)) / (sp * d); nL++; } prev = [R.x, R.z]; if (D.DINO.hunter && D.DINO.hunter.hs !== 'leave') raptors++; if (D.UW.drown > 0) { got = t; return true; } });
          out.chase = { on0: true, rears, curve: +(lat / Math.max(1, nL)).toFixed(2), got, noHeal: Math.round(R.hp) === Math.round(hp0), raptors, after: !!R.rexOn };
          // up high: safe, it gives up; a low branch isn't
          go(80, 8); D.rexStart(R); let gotHigh = false; step(60, () => { if (D.UW.drown > 0) gotHigh = true; return !R.rexOn; }); out.high = { got: gotHigh, gaveUp: !R.rexOn };
          go(80, 3); D.rexStart(R); let gotLow = null; step(40, t => { if (D.UW.drown > 0) { gotLow = t; return true; } }); out.low = gotLow;
          // a near miss starts it too
          go(10); R.rexOn = false; for (const B of D.beasts) if (B !== R) B.root.visible = false; const o = new T.Vector3(P.x, R.y + 3, P.z), dir = new T.Vector3(R.x - P.x, 0, R.z + 6 - P.z).normalize(); D.legendShot(o, dir, 400, 850); out.nearMiss = !!R.rexOn;
          // ~10 sniper hits to bring it down, +200
          R.rexOn = false; R.hp = R.hpMax; const want = Math.ceil(R.hpMax / Math.round(D.RAPTOR_DMG.hunt * D.TIER.dmg[Math.max(1, D.tierOf('hunt'))])); const s1 = D.hunt.score; let n = 0; while (!R.dead && n < 40) { D.hitAnimal(R, 100, 0, false, 'hunt'); n++; } out.kill = { want, n, dead: R.dead, pts: +(D.hunt.score - s1).toFixed(1) };
          return out; }""")
        print(json.dumps(r))
        ok = r["medium"] == 0 and r["large"] == 1 and not r["hidden"]["seen"] and not r["hidden"]["visible"] and r["hidden"]["hp"] == 3500 and r["hidden"]["thru"] \
             and r["revealed"]["seen"] and r["revealed"]["visible"] and r["roam"]["far"] > 120 and r["roam"]["worstStuck"] <= 6 and not r["roam"]["on"] \
             and r["chase"]["rears"] >= 2 and r["chase"]["curve"] > .1 and r["chase"]["got"] is not None and r["chase"]["noHeal"] and r["chase"]["raptors"] == 0 and not r["chase"]["after"] \
             and not r["high"]["got"] and r["high"]["gaveUp"] and r["low"] is not None and r["nearMiss"] \
             and r["kill"]["n"] == r["kill"]["want"] and 9 <= r["kill"]["want"] <= 11 and r["kill"]["dead"] and r["kill"]["pts"] >= 200
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
