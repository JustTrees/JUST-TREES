"""2.57: rocks use their real shape for walking, standing and shots (the 1 m grid only says "a rock may be here").
Finds spots where the old grid made an invisible wall (a lip or bulge over open ground) and checks: you can walk there, a shot passes
under the lip (from close and from far away), and a grenade isn't stopped. Solid rock still blocks you and stops shots; you still
stand on top; the exact top matches the grid inside rocks (the shapes face the right way).
Usage: python3 dev/test_257.py dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1])
JS = """(seed) => { window.FREEZE = true; const T = D.THREE, o = { seed };
  D.setSeed(seed); D.setVR(true); D.setMode('pvp'); Object.assign(D.set, { size: 'medium', lat: 42, landscape: 'dramatic', weather: 'clear', hour: 13 }); D.generate(); D.state = 'play';
  const G = D.rockGrid, Lo = D.rockLow, N = D.rockN, half = (N - 1) / 2; let rs = seed * 977 + 1; const rnd = () => (rs = (rs * 16807) % 2147483647) / 2147483647;
  const cells = []; for (let k = 0; k < G.length; k++) if (G[k] > -1e8) cells.push(k);
  const oldTop = (x, z, y, hd) => { const i = Math.floor(x + half), j = Math.floor(z + half), k = j * N + i, top = G[k]; if (top < -1e8) return -1e9; const low = Lo[k]; return low > y + hd + .4 && low > D.H(x, z) + Math.max(hd, 0) + .5 ? -1e9 : top; };
  // freed spots: old grid blocks a 1.6 m body standing on the ground, the real shape has 2.4 m+ of room overhead
  const freed = [];
  for (let t = 0; t < 60000 && freed.length < 40; t++) { const k = cells[Math.floor(rnd() * cells.length)], x = k % N - half + rnd(), z = Math.floor(k / N) - half + rnd(), g = D.H(x, z);
    if (g < D.water + .3) continue; if (oldTop(x, z, g, 1.6) > g + .5 && D.rockTopAt(x, z, g, 1.6) < g + .3 && D.rockTopAt(x, z) > g + 2.4) freed.push([x, z, g]); }
  o.freed = freed.length; if (!freed.length) return o;
  // a shot through each freed spot at 1.2 m: from 4 m away, and from far (the longest clear run back along the line, up to 300 m)
  let near = 0, far = 0, farTried = 0, farM = 0, nade = 0;
  for (const [x, z, g] of freed) {
    let okN = false, okF = false;
    for (let a = 0; a < 6.28 && !okN; a += .39) { const dx = Math.cos(a), dz = Math.sin(a), y = g + 1.2, aim = new T.Vector3(x, y, z);
      // the shot must reach past the spot (4 m on) without hitting rock first; the line must be open air apart from rock lips
      const from = aim.clone().add(new T.Vector3(-dx * 4, 0, -dz * 4)); if (D.H(from.x, from.z) > y - .3 || D.rockTopAt(from.x, from.z, y, -.4) >= y) continue;
      let clear = true; for (let s = -4.6; s <= 3; s += .1) { const px = x + dx * s, pz = z + dz * s; if (D.H(px, pz) > y - .3 || (Math.abs(s) > .01 && [[0, 0], [.06, 0], [-.06, 0], [0, .06], [0, -.06]].some(([u, w]) => D.rockTopAt(px + u, pz + w, y + .06, -.4) >= y - .06))) { clear = false; break; } }   /* (with 6 cm to spare: rock checks are to the nearest 5 cm) */ if (!clear) continue;   // (open air all along, so the only question is the spot itself)
      const r = D.castShot(from, new T.Vector3(dx, 0, dz), 7); okN = r.kind === null || r.kind === 'wood';
      if (!okN) continue;
      let back = 0; for (let s = 4; s < 300; s += 2) { const px = x - dx * s, pz = z - dz * s; if (D.H(px, pz) > y - .5 || D.rockTopAt(px, pz, y, -.4) >= y || Math.abs(px) > half - 5 || Math.abs(pz) > half - 5) break; back = s; }
      if (back >= 60) { farTried++; const ff = new T.Vector3(x - dx * back, y, z - dz * back), rf = D.castShot(ff, new T.Vector3(dx, 0, dz), back + 2.2); okF = rf.kind === null || rf.kind === 'wood'; if (okF) farM = Math.max(farM, back); else (o.farWhy = o.farWhy || []).push([rf.kind, +(rf.p.distanceTo(aim)).toFixed(1)]); }
      const p = new T.Vector3(x, y, z); nade += D.nadeHit ? (D.nadeHit(p) !== 'ground' ? 1 : 0) : (D.rockTopAt(x, z, y, -.4) < y ? 1 : 0);
    }
    if (okN) near++; if (okF) far++;
  }
  o.shotNear = near; o.farTried = farTried; o.shotFar = far; o.farM = farM; o.nadeFree = nade;
  // solid rock: deep inside (all round within .6 m is rock to the ground) blocks walking and stops a shot
  let solid = 0, solidBlocks = 0, shotStops = 0, stand = 0, topOk = 0, topN = 0;
  for (let t = 0; t < 20000 && solid < 40; t++) { const k = cells[Math.floor(rnd() * cells.length)], x = k % N - half + rnd(), z = Math.floor(k / N) - half + rnd(), g = D.H(x, z);
    const tops = [[0, 0], [.6, 0], [-.6, 0], [0, .6], [0, -.6]].map(([a, c]) => D.rockTopAt(x + a, z + c, D.H(x + a, z + c), 1.6)); if (tops.some(v => v < D.H(x, z) + 1.2)) continue;
    solid++; if (D.rockTopAt(x, z, g, 1.6) > g + .5) solidBlocks++;
    const y = g + .8, from = new T.Vector3(x - 6, y, z); const r = D.castShot(from, new T.Vector3(1, 0, 0), 8); if (r.kind !== null && r.p.x <= x + .3) shotStops++; else (o.stopWhy = o.stopWhy || []).push([r.kind, +(r.p.x - x).toFixed(2)]);
    const top = D.rockTopAt(x, z); if (Math.abs(D.rockTopAt(x, z, top + .02, 0) - top) < .01) stand++;
    const i = Math.floor(x + half), j = Math.floor(z + half), gt = G[j * N + i], mc = D.rockTopAt(i + .5 - half, j + .5 - half);   // at the square's middle the grid traced the same triangles
    topN++; if (mc <= gt + .02 && mc > gt - 1.5) topOk++; else (o.topWhy = o.topWhy || []).push([+mc.toFixed(2), +gt.toFixed(2)]);
  }
  Object.assign(o, { solid, solidBlocks, shotStops, stand, topOk, topN });
  return o; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context()).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        res = []; ok = True
        for seed in [7, 23]:
            r = await pg.evaluate(JS, seed); res.append(r); print(json.dumps(r))
            ok = ok and r.get("freed", 0) >= 5 and r["shotNear"] >= r["freed"] * .6 and r["nadeFree"] > 0 \
                 and r["solid"] >= 20 and r["solidBlocks"] == r["solid"] and r["shotStops"] >= r["solid"] * .9 and r["stand"] == r["solid"] and r["topOk"] >= r["topN"] * .9
        ok = ok and sum(r.get("shotFar", 0) for r in res) >= 1 and all(r.get("shotFar", 0) == r.get("farTried", 0) for r in res)
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
