"""The XXXL 3 km map (1.84, "a 3-kilometer map, the same amount of trees as XXL minus about 10%"): an open-world size.
1.87 ("animals … not around whole map … just close to you by like 1km"): animals only within BUBBLE (1 km) of you; travel
1.4 km and the ones left behind are cleared while new ones fill in round you; Dino mode works there too.
Checks: the size exists in the VR menu and on PC (not on phones), trees are ~90% of XXL's count, the animal bubble, no errors.
Usage: python3 dev/test_3km.py /tmp/dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
T = 'file://' + os.path.abspath(sys.argv[1])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        out = {}; errs = []
        async def run(size, dino=False):
            pg = await (await b.new_context(viewport={"width": 400, "height": 260})).new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(T); await pg.wait_for_timeout(600)
            r = await pg.evaluate("""([size, dino]) => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setSeed(3); D.setVR(true); D.setMode('hunt'); D.set.dino = dino; D.set.size = size; D.set.lat = 42; D.set.density = .5; D.set.env = 'climate';
              const t0 = performance.now(); D.generate(); const gen = performance.now() - t0; D.state = 'play';
              let lo = 0; for (const t of D.tiles) if (t.lo) for (const m of t.lo.children) lo += m.count || 0;   // the far (light) copy of every tree inside the map
              const ground = () => D.beasts.filter(A => !A.dead && !A.gone && !A.wings && !A.hunter && !D.LEGEND[A.kind]);   // (Bigfoot and the T. rexes roam the whole map)
              const far = r => ground().filter(A => Math.hypot(A.x - D.P.x, A.z - D.P.z) > r).length;
              const b0 = ground().length, far0 = far(1000 + 300);
              // travel 1.4 km across the map, then play two minutes there
              const dx = D.P.x > 0 ? -1400 : 1400; D.P.x += dx; D.P.y = D.H(D.P.x, D.P.z) + .1;
              const cam = D.camera; cam.position.set(D.P.x, D.P.y + 1.7, D.P.z); cam.rotation.set(0, 0, 0); cam.updateMatrixWorld();
              for (let i = 0; i < 480; i++) D.updateAnimals(.25);
              const btns = [...document.querySelectorAll('#sizes button')].map(x => x.textContent);
              return { gen: Math.round(gen), trees: lo, beasts0: b0, farAtStart: far0, nearAfterTravel: ground().length - far(1300), farAfterTravel: far(1300), dino: !!(D.DINO && D.DINO.on), btns }; }""", [size, dino])
            await pg.close(); return r
        out["xxl"] = await run("xxl"); out["3km"] = await run("xxxl"); out["3kmDino"] = await run("xxxl", True)
        print(json.dumps(out)); print("errors:", errs or "none")
        a, k = out["xxl"], out["3km"]; ratio = k["trees"] / max(1, a["trees"])
        d = out["3kmDino"]
        ok = (.8 < ratio < 1.0 and k["beasts0"] > 40 and k["farAtStart"] == 0 and k["farAfterTravel"] == 0 and k["nearAfterTravel"] > 20
              and d["dino"] and d["beasts0"] > 10 and d["farAtStart"] == 0 and a["beasts0"] > 50 and "XXXL" in k["btns"] and k["gen"] < a["gen"] * 2.5 and not errs)
        print("treeRatio", round(ratio, 3)); print("PASS" if ok else "FAIL"); await b.close()
        if not ok: sys.exit(1)
asyncio.run(main())
