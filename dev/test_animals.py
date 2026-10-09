import os, sys
TARGET = 'file://' + os.path.abspath(sys.argv[1])
import asyncio, json, sys
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader","--enable-webgl","--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width":320,"height":200})).new_page(); errs=[]
        pg.on("pageerror", lambda e: errs.append("PE "+str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = [];
          for (const [lat, rough] of [[45, .9], [30, .5], [60, .8]]) {
          D.setMode('hunt'); D.set.size = 'medium'; D.set.weather = 'clear'; D.set.lat = lat; D.set.rough = rough; D.generate(); D.state = 'play';
          const ground = D.beasts.filter(A => !A.dead && A.kind !== 'bird' && A.kind !== 'monkey');
          // calm wandering for 60 s: count jitter (trying to walk but not moving)
          let jitter = 0, walkWin = 0, longStuck = 0; const last = new Map(), run = new Map();
          for (let i = 0; i < 1800; i++) { D.updateAnimals(1 / 30);
            if (i % 36 === 0) for (const A of ground) { const l = last.get(A); if (l && A.mode === 'walk' && A.want > .3) { walkWin++; if (Math.hypot(A.x - l[0], A.z - l[1]) < .35) { jitter++; const c = (run.get(A) || 0) + 1; run.set(A, c); if (c === 3) longStuck++; } else run.set(A, 0); } else run.set(A, 0); last.set(A, [A.x, A.z]); } }
          // a shot right next to the nearest animals: how far do they go in 40 s?
          let near = ground.slice().sort((a, b) => Math.hypot(a.x - D.P.x, a.z - D.P.z) - Math.hypot(b.x - D.P.x, b.z - D.P.z)).slice(0, 12);
          const o = { x: near[0].x + 20, z: near[0].z }; const start = new Map(near.map(A => [A, [A.x, A.z]]));
          D.scatterBeasts(o);
          for (let i = 0; i < 1200; i++) D.updateAnimals(1 / 30);
          const moved = near.map(A => Math.round(Math.hypot(A.x - start.get(A)[0], A.z - start.get(A)[1]))), away = near.map(A => Math.round(Math.hypot(A.x - o.x, A.z - o.z)));
          out.push({ lat, n: ground.length, longStuck3s: longStuck, jitterPct: +(100 * jitter / Math.max(1, walkWin)).toFixed(1), walkWins: walkWin, movedAfterShot: moved, distFromShot: away });
          }
          return out; }""")
        print(json.dumps(r)); print(errs or "ok"); await b.close()
asyncio.run(main())
