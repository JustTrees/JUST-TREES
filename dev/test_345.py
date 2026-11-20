"""3.45: the dinosaur island on the Treeocashing planet. It's always a dark thunderstorm there (rain, lightning, dim), it's full of
dinosaurs (herds, a T. rex, pteranodons), and while you're on it raptors hunt you like in Prehistoric. Back on the mainland: the weather
is the region's own again and the hunt stops. Usage: python3 dev/test_345.py dbg.html"""
import os, sys, asyncio, json, re
from playwright.async_api import async_playwright
here = os.path.dirname(os.path.abspath(__file__))
GEN = re.search(r'GEN = """(.*?)"""', open(os.path.join(here, "test_275.py")).read(), re.S).group(1)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 300, "height": 200})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        await pg.evaluate(GEN, 40)
        r = await pg.evaluate("""() => { const G = D.GLOBE, P = D.P, E = D.ENDLESS, o = {}; E.bud = 30;
          const run = n => { for (let i = 0; i < n; i++) { D.endlessTick(1 / 30); D.geoTick(1 / 30); D.updateAnimals(1 / 30); D.dinoTick(1 / 30); } };
          run(30); o.main = [D.weather.type, D.DINO.on, !!D.DINO.isle];
          D.geoTeleport(G.isle.c); run(400);
          const near = D.beasts.filter(A => Math.hypot(A.x - P.x, A.z - P.z) < 600 && !A.dead), kinds = {}; for (const A of near) kinds[A.kind] = (kinds[A.kind] || 0) + 1;
          o.isle = [D.geoDinoAt(P.x, P.z), D.weather.type, D.weather.storm, +D.weather.dim.toFixed(2), D.DINO.on, !!D.DINO.isle]; o.kinds = kinds; o.n = near.length;
          o.rex = D.beasts.some(A => A.kind === 'trex'); o.ptero = D.beasts.some(A => A.kind === 'ptero');
          D.DINO.gap = 0; D.DINO.pending = 0; D.dinoStartHunt(); run(120); o.hunt = !!D.DINO.hunter && D.DINO.hunter.kind === 'raptor';
          // back to the mainland
          D.geoTeleport(D.geoRandomSpot()); run(200); o.back = [D.geoDinoAt(P.x, P.z), D.weather.dim > .3 || D.weather.type !== 'storm', D.DINO.on, !!D.DINO.isle, !!D.DINO.hunter, D.beasts.filter(A => A.hunter).length];
          return o; }""")
        print(json.dumps(r))
        ok = r["main"][1:] == [False, False] and r["isle"][:5] == [True, "storm", True, .2, True] and r["isle"][5] and r["n"] >= 15 and r["hunt"] \
             and r["back"] == [False, True, False, False, False, 0]
        print("PASS" if ok and not errs else "FAIL", errs[:5]); print("errors: none" if not errs else "errors: " + str(errs[:5])); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
