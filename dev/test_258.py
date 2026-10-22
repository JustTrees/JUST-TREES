"""2.58: crouch to get under low rocks, and the real rock shapes on endless land.
Island (PC walking with the crouch key, the same check a headset uses with your real head): at a rock lip about 1.2-1.75 m over the
ground you're stopped standing, you get through crouched, and a shot passes under it. Endless (Hunting in a headset): the squares near
you have the real shapes: spots under lips and bulges are open for walking and shots, solid rock still blocks and you stand on top.
Usage: python3 dev/test_258.py dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1])
ISLAND = """(seed) => { window.FREEZE = true; const T = D.THREE, o = { seed };
  D.setSeed(seed); D.setVR(false); D.vr.on = false; D.setMode('hike'); Object.assign(D.set, { size: 'medium', lat: 42, landscape: 'dramatic', weather: 'clear', hour: 13 }); D.generate(); D.state = 'play';
  const G = D.rockGrid, N = D.rockN, half = (N - 1) / 2; let rs = seed * 131 + 7; const rnd = () => (rs = (rs * 16807) % 2147483647) / 2147483647;
  const cells = []; for (let k = 0; k < G.length; k++) if (G[k] > -1e8) cells.push(k);
  const STAND = 1.65 + .12, CROUCH = 1.65 - .62 + .12;
  const standBlk = (x, z) => { const g = D.H(x, z); return D.rockTopAt(x, z, g, STAND, .05) > g + 1.5; }, crouchOk = (x, z) => { const g = D.H(x, z); return D.rockTopAt(x, z, g, CROUCH, .05) < g + .3; };
  const flat = (x, z) => D.H(x, z) > D.water + .4 && D.slopeNy(x, z) > .85;
  let found = null;
  for (let t = 0; t < 200000 && !found; t++) { const k = cells[Math.floor(rnd() * cells.length)], x = k % N - half + rnd(), z = Math.floor(k / N) - half + rnd();
    if (!flat(x, z) || !standBlk(x, z) || !crouchOk(x, z)) continue;
    let ring = true; for (let a = 0; a < 6.28; a += .79) if (!crouchOk(x + Math.cos(a) * .35, z + Math.sin(a) * .35)) { ring = false; break; } if (!ring) continue;
    for (let a = 0; a < 6.28 && !found; a += .26) { const dx = Math.cos(a), dz = Math.sin(a); let ok = true;
      for (let s = .35; s <= 3.5; s += .1) { const px = x - dx * s, pz = z - dz * s; if (!flat(px, pz) || !crouchOk(px, pz) || !crouchOk(px - dz * .35, pz + dx * .35) || !crouchOk(px + dz * .35, pz - dx * .35)) { ok = false; break; } }
      if (ok && [[0, 0], [.4, 0], [-.4, 0], [0, .4], [0, -.4]].every(([u, w]) => !standBlk(x - dx * 3.3 + u, z - dz * 3.3 + w))) found = { x, z, dx, dz }; } }   // (you start in the open)
  o.found = !!found; if (!found) return o;
  const { x, z, dx, dz } = found, g = D.H(x, z); for (let y = g; y < g + 3; y += .05) if (D.rockTopAt(x, z, y, -.4) >= y) { o.gap = +(y - g).toFixed(2); break; }   // how high the rock starts over the ground
  const walk = crouch => { D.P.x = x - dx * 3.3; D.P.z = z - dz * 3.3; D.P.y = D.H(D.P.x, D.P.z); D.P.vy = 0; D.P.onGround = true; D.P.yaw = Math.atan2(-dx, -dz); D.P.crouch = crouch; D.P.ck = crouch ? 1 : 0;
    D.input.jy = 1; D.input.jx = 0; let best = 1e9, inStand = 0;
    for (let f = 0; f < 150; f++) { D.P.crouch = crouch; D.P.yaw = Math.atan2(-dx, -dz); D.update(1 / 60); if (D.P.y < D.H(D.P.x, D.P.z) + .3) { best = Math.min(best, Math.hypot(D.P.x - x, D.P.z - z)); if (standBlk(D.P.x, D.P.z)) inStand++; } }   // (on the ground: a low lip you can also step up onto)
    D.input.jy = 0; return [+best.toFixed(2), inStand]; };
  o.standing = walk(false); o.crouched = walk(true);
  const y = g + .55, r = D.castShot(new T.Vector3(x - dx * 3, y, z - dz * 3), new T.Vector3(dx, 0, dz), 3.2); o.shot = r.kind;
  return o; }"""
ENDLESS = """() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); const T = D.THREE, o = {}; D.setSeed(4242); D.setVR(true); D.setMode('hunt'); D.vr.on = true;
  Object.assign(D.set, { env: 'climate', land: 'dramatic', lat: 38, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .5, rough: .6, huntMap: 'endless', dino: false, size: 'medium' });
  D.generate(); D.state = 'play'; o.endless = !!D.ENDLESS; for (let f = 0; f < 60; f++) D.endlessTick(1 / 72);
  let rs = 99; const rnd = () => (rs = (rs * 16807) % 2147483647) / 2147483647, X = D.P.x, Z = D.P.z;
  let rock = 0, freed = 0, shotUnder = 0, solid = 0, solidBlocks = 0, stand = 0;
  for (let t = 0; t < 400000 && (freed < 25 || solid < 25); t++) { const x = X + (rnd() - .5) * 300, z = Z + (rnd() - .5) * 300, g = D.H(x, z), top = D.rockTopAt(x, z);
    if (top < -1e8 || g < D.water + .3) continue; rock++;
    if (freed < 25 && top > g + 2.4 && D.rockTopAt(x, z, g, 1.6) < g + .3) { freed++;
      const y = g + 1.2; let okShot = false;
      for (let a = 0; a < 6.28 && !okShot; a += .52) { const dx = Math.cos(a), dz = Math.sin(a); let clear = true;
        for (let s = -4.6; s <= 3; s += .1) { const px = x + dx * s, pz = z + dz * s; if (D.H(px, pz) > y - .3 || (Math.abs(s) > .01 && [[0, 0], [.06, 0], [-.06, 0], [0, .06], [0, -.06]].some(([u, w]) => D.rockTopAt(px + u, pz + w, y + .06, -.4) >= y - .06))) { clear = false; break; } }
        if (!clear) continue; okShot = D.castShot(new T.Vector3(x - dx * 4, y, z - dz * 4), new T.Vector3(dx, 0, dz), 6).kind === null; }
      if (okShot) shotUnder++; }
    if (solid < 25 && [[0, 0], [.6, 0], [-.6, 0], [0, .6], [0, -.6]].every(([a, c]) => D.rockTopAt(x + a, z + c, D.H(x + a, z + c), 1.6) > D.H(x, z) + 1.2)) { solid++;
      if (D.rockTopAt(x, z, g, 1.6) > g + .5) solidBlocks++; if (Math.abs(D.rockTopAt(x, z, top + .02, 0) - top) < .01) stand++; }
  }
  Object.assign(o, { rock, freed, shotUnder, solid, solidBlocks, stand }); D.vr.on = false; return o; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        errs = []; ok = True
        pg = await (await b.new_context()).new_page(); pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        got = 0
        for seed in [7, 23, 41]:
            r = await pg.evaluate(ISLAND, seed); print(json.dumps(r))
            if not r.get("found"): continue
            got += 1
            ok = ok and r["standing"][0] > .15 and r["standing"][1] == 0 and r["crouched"][0] < .15 and r["crouched"][1] > 0 and r["shot"] is None
        ok = ok and got >= 2
        await pg.close()
        pg2 = await (await b.new_context()).new_page(); pg2.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg2.goto(TARGET); await pg2.wait_for_timeout(800)
        r = await pg2.evaluate(ENDLESS); print(json.dumps(r))
        ok = ok and r["endless"] and r["freed"] >= 5 and r["shotUnder"] >= r["freed"] * .4 and r["solid"] >= 10 and r["solidBlocks"] == r["solid"] and r["stand"] == r["solid"]
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
