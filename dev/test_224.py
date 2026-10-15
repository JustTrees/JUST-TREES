"""2.24 checks: flying then letting go keeps you moving (you curve down); a tree deck catches you from below its top and is never a wall;
friends' poses that arrive in bunches still move smoothly (sender-timed); the closest T. rex is the one heard.
Usage: python3 dev/test_224.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setSeed(3131); D.setVR(true); D.setMode('hike'); D.vr.on = true; D.hikeForce = 'island';
          Object.assign(D.set, { lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .5, rough: .5 }); D.generate(); D.state = 'play';
          const P = D.P, out = {};
          // fly, then let go: keep going while falling
          P.x = 0; P.z = 0; P.y = D.H(0, 0) + 60; P.vy = 0; P.onGround = false; D.vr.glideDir = { x: 1, z: 0 };
          for (let f = 0; f < 60; f++) { D.input.glide = true; D.update(1 / 60); }
          const x1 = P.x; D.input.glide = false; let f = 0; while (!P.onGround && f < 600) { D.update(1 / 60); f++; }
          out.carryM = +(P.x - x1).toFixed(1); out.fallS = +(f / 60).toFixed(2);
          // the tree deck: from just under its top you land on it; walking onto it from the side, nothing stops you
          const Pc = D.PORCH; if (Pc) { const rx = Pc.x + (Pc.rIn + 1.3), rz = Pc.z;
            P.x = rx; P.z = rz; P.y = Pc.top - 1.2; P.vy = -3; P.onGround = false; D.update(1 / 60); out.deckLand = [+(P.y - Pc.top).toFixed(2), P.onGround];
            out.deckBelow = D.porchGround(rx, rz, Pc.top - 3) < -1e8; }
          // a friend's poses: made every 50 ms, arriving in bunches of three; shown positions move evenly
          const L = { rx: [] }; let t0 = performance.now(); const arr = [];
          for (let i = 0; i < 40; i++) { const o = { ts: t0 + i * 50, h: [i * 1.0, 1.6, 0, 0, 0, 0, 1], l: null, r: null, f: 0, a: true, gl: false, hp: 100, gp: 0 }; arr.push([t0 + 40 + Math.floor(i / 3) * 150 + 149, o]); }
          const real = performance.now; let fake = t0; performance.now = () => fake; const xs = [];
          for (fake = t0; fake < t0 + 1900; fake += 1000 / 72) { while (arr.length && arr[0][0] <= fake) { const o = arr.shift()[1]; L.rx.push(Object.assign(o, { at: D.mpStamp(L, o) })); } const s = D.mpSample(L); if (s && fake > t0 + 400) xs.push(s.h.p.x); }
          performance.now = real;
          const v = xs.slice(1).map((x, i) => (x - xs[i]) * 72), vm = v.reduce((a, c) => a + c, 0) / v.length;
          out.smooth = { meanSpeed: +vm.toFixed(1), maxJump: +Math.max(...v.map(s => Math.abs(s - vm))).toFixed(1) };
          return out; }""")
        print(json.dumps(r))
        ok = r["carryM"] > 6 and r.get("deckLand", [0, True])[1] and abs(r.get("deckLand", [0])[0]) < .05 and r.get("deckBelow", True) \
             and abs(r["smooth"]["meanSpeed"] - 20) < 2 and r["smooth"]["maxJump"] < 6 and not errs
        print("errors", errs[:5]); print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
