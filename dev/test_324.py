"""3.24: the fishing rod, the real-VR-fishing way. The rod is in the off hand with a reel under it; the other hand grips the reel's handle
(it locks on) and turns it. Casting: hold the rod hand's trigger, swing, let go: the lure flies as fast as the tip was moving (a lazy one
just drops; a hard snap goes much further). Turning the handle closes the bail and brings the lure in. A bite: strike (jerk up) and it's on.
The fight: steady reeling with the rod up lands it; cranking hard with the rod pointed at a running fish snaps the line; never reeling
loses it. Usage: python3 dev/test_324.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
GEN = """() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); try { localStorage.removeItem('jt-geo'); localStorage.removeItem('jt-geochar'); } catch (_) {}
  D.DEV.ok = true; D.setSeed(4242); D.setVR(true); D.setMode('hunt'); D.vr.on = true; D.set.hand = 'right';
  Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .5, rough: .5, huntMap: 'globe', dino: false });
  D.generate(); D.state = 'play'; for (let i = 0; i < 72; i++) { D.endlessTick(1 / 72); D.geoTick(1 / 72); }
  const T = D.THREE, P = D.P; window.hand = (pos) => ({ pos: pos.clone(), rayPos: pos.clone(), rayQ: new T.Quaternion(), q: new T.Quaternion(), grip: 0, trig: 0, sx: 0, sy: 0, a: 0, b: 0, stickBtn: 0 });
  // stand on a shore looking out over deep water
  let best = null; for (let k = 0; k < 4000 && !best; k++) { const a = Math.random() * 6.283, r = 50 + Math.random() * 800, x = P.x + Math.cos(a) * r, z = P.z + Math.sin(a) * r;
    if (D.H(x, z) < D.water + .6 || D.H(x, z) > D.water + 3) continue; for (let q = 0; q < 16; q++) { const b = q / 16 * 6.283; let ok = true; for (let d = 6; d <= 45; d += 3) if (D.H(x + Math.sin(b) * d, z + Math.cos(b) * d) > D.water - 1) ok = false; if (ok) { best = [x, z, b]; break; } } }
  if (!best) return false; P.x = best[0]; P.z = best[1]; P.y = D.groundAt(P.x, P.z); window.face = best[2];
  D.geoGearApply(18, true); D.geoHeld('rod');
  const head = new T.Vector3(P.x, P.y + 1.7, P.z), yawQ = new T.Quaternion().setFromAxisAngle(new T.Vector3(0, 1, 0), face + Math.PI);   // (the controller's forward is -z)
  const fwd = new T.Vector3(Math.sin(face), 0, Math.cos(face)), right = new T.Vector3(-Math.cos(face), 0, Math.sin(face)).negate();
  window.M = hand(head.clone().addScaledVector(right, .22).addScaledVector(fwd, .3).add(new T.Vector3(0, -.45, 0))); window.O = hand(head.clone().addScaledVector(right, -.18).addScaledVector(fwd, .32).add(new T.Vector3(0, -.42, 0)));
  M.rayQ.copy(yawQ); O.rayQ.copy(yawQ); window.I = { head, headQ: yawQ.clone(), hands: { right: M, left: O } }; window.yawQ = yawQ; window.fwd = fwd;
  window.step = () => D.geoHeldTick(I, M, 1 / 72); window.R = () => D.GEO.rod; step(); step();
  window.pitch = a => { O.rayQ.copy(yawQ).multiply(new T.Quaternion().setFromAxisAngle(new T.Vector3(1, 0, 0), a)); };
  window.cast = (w) => { const r = R(); pitch(1.2); for (let i = 0; i < 20; i++) step(); O.trig = 1; step(); let a = 1.2; while (a > .3) { a -= w / 72; pitch(a); step(); } O.trig = 0; step();
    let n = 0; while (r.st === 'cast' && n++ < 72 * 8) { pitch(-.3); step(); } return [r.st, Math.round(Math.hypot(r.p.x - D.P.x, r.p.z - D.P.z)), r.wet, Math.round(r.v0)]; };
  window.crank = (turns, rate) => { const r = R(), U = r.M.userData, hub = U.crank.getWorldPosition(new T.Vector3()); M.pos.copy(U.knob.getWorldPosition(new T.Vector3())); M.grip = 1; step();
    const n = Math.round(turns / rate * 72); let a = 0; for (let i = 0; i < n; i++) { a += rate * 6.283 / 72; const q = r.M.quaternion, h = U.crank.getWorldPosition(new T.Vector3());
      M.pos.copy(h).add(new T.Vector3(0, Math.cos(a) * .06, Math.sin(a) * .06).applyQuaternion(q)); step(); if (r.st !== 'out' && r.st !== 'fight' && r.st !== 'bite') break; } };
  return true; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        for _ in range(6):
            ok0 = await pg.evaluate(GEN)
            if ok0: break
        out = {"shore": ok0}
        out["base"] = await pg.evaluate("""() => { const r = R(); return { inOff: r.M.position.distanceTo(O.pos) < .15, hasReel: !!r.M.userData.knob, ready: r.st, mapOff: true }; }""")
        out["lazy"] = await pg.evaluate("() => { const r = R(); O.trig = 1; step(); step(); O.trig = 0; step(); let n = 0; while (r.st === 'cast' && n++ < 300) step(); const d = r.p ? Math.round(Math.hypot(r.p.x - D.P.x, r.p.z - D.P.z)) : 0; D.geoHeld(null); D.geoHeld('rod'); step(); return [d]; }")
        out["soft"] = await pg.evaluate("() => { const c = cast(9); D.geoHeld(null); D.geoHeld('rod'); step(); return c; }")
        out["hard"] = await pg.evaluate("() => cast(16)")
        out["reel"] = await pg.evaluate("""() => { const r = R(); r.rate = 0; const d0 = Math.hypot(r.p.x - D.P.x, r.p.z - D.P.z), b0 = r.bail; crank(5, 1.2); return { locked: r.crankOn, bailWas: b0, bail: r.bail, inBy: +(d0 - Math.hypot(r.p.x - D.P.x, r.p.z - D.P.z)).toFixed(1) }; }""")
        res = {}
        for mode in ("good", "hard", "slack"):
            res[mode] = await pg.evaluate("""(mode) => { const r = R(), T = D.THREE; r.why = ''; if (r.st !== 'out' || !r.wet) { D.geoHeld(null); D.geoHeld('rod'); step(); const c = cast(15); if (r.st !== 'out' || !r.wet) return { notOut: c }; }
              M.grip = 0; step(); r.rate = 1e6; pitch(-.3); step(); const bite = r.st; for (let i = 0; i < 8; i++) { pitch(-.3 + i * .14); step(); } const hooked = r.st;
              let n = 0, minL = 1e9, maxT = 0, snap = false; const food0 = D.GEO.food = 30;
              if (mode === 'hard') pitch(-.15);   // the rod pointed down the line at the fish
              else pitch(.6);                     // the rod held up
              const U = r.M.userData; let a = 0;
              while (r.st === 'fight' && n++ < 72 * 120) {
                const rate = mode === 'good' ? (r.F.T > .6 ? 0 : r.F.mode === 'run' ? .4 : 1.6) : mode === 'hard' ? 4 : 0;
                if (rate > 0) { M.grip = 1; if (!r.crankOn) { M.pos.copy(U.knob.getWorldPosition(new T.Vector3())); } a += rate * 6.283 / 72; M.pos.copy(U.crank.getWorldPosition(new T.Vector3())).add(new T.Vector3(0, Math.cos(a) * .06, Math.sin(a) * .06).applyQuaternion(r.M.quaternion)); }
                else M.grip = 0;
                if (mode === 'good' && Math.hypot(r.p.x - D.P.x, r.p.z - D.P.z) < 2.6) pitch(1.3);
                step(); minL = Math.min(minL, r.L); maxT = Math.max(maxT, r.F ? r.F.T : 0); }
              const end = r.st; for (let i = 0; i < 100 && r.st === 'land'; i++) step();
              return { why: r.why, bite, hooked, end, landed: r.st === 'ready' && end === 'land', food: Math.round(D.GEO.food - food0), secs: Math.round(n / 72), minL: Math.round(minL), maxT: +maxT.toFixed(2) }; }""", mode)
        out["fight"] = res
        print(json.dumps(out)); print("errors:", errs[:5] or "none")
        f = out["fight"]
        ok = out["shore"] and out["base"]["inOff"] and out["base"]["hasReel"] and out["lazy"][0] < 4 and out["soft"][0] == "out" and out["hard"][0] == "out" and out["hard"][1] > out["soft"][1] + 5 and 18 < out["hard"][1] < 70 \
             and out["reel"]["locked"] and out["reel"]["bailWas"] and not out["reel"]["bail"] and 3 < out["reel"]["inBy"] < 6 \
             and f["good"]["bite"] == "bite" and f["good"]["hooked"] == "fight" and f["good"]["landed"] and f["good"]["food"] > 0 \
             and f["hard"]["hooked"] == "fight" and not f["hard"]["landed"] and f["slack"]["hooked"] == "fight" and not f["slack"]["landed"] and not errs
        print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
