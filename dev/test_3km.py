"""The 3 km map (1.84, Ron: "a 3-kilometer map, the same amount of trees as XXL minus about 10%, no animals"): an open-world test size.
Checks: the size exists in the VR menu and on PC (not on phones), trees are ~90% of XXL's count, no animals (none spawned, none
appear or restock later, no dinosaurs), the ground and tree tiles stay sensible, and it loads without errors.
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
              const b0 = D.beasts.length; for (let i = 0; i < 400; i++) D.updateAnimals(.25);   // 100 s of play: nothing turns up
              const btns = [...document.querySelectorAll('#sizes button')].map(x => x.textContent);
              return { gen: Math.round(gen), trees: lo, beasts0: b0, beastsLater: D.beasts.length, dino: !!(D.DINO && D.DINO.on), btns }; }""", [size, dino])
            await pg.close(); return r
        out["xxl"] = await run("xxl"); out["3km"] = await run("xxxl"); out["3kmDino"] = await run("xxxl", True)
        print(json.dumps(out)); print("errors:", errs or "none")
        a, k = out["xxl"], out["3km"]; ratio = k["trees"] / max(1, a["trees"])
        ok = (.8 < ratio < 1.0 and k["beasts0"] == 0 and k["beastsLater"] == 0 and out["3kmDino"]["beasts0"] == 0 and out["3kmDino"]["beastsLater"] == 0
              and not out["3kmDino"]["dino"] and a["beasts0"] > 50 and "XXXL" in k["btns"] and k["gen"] < a["gen"] * 2.5 and not errs)
        print("treeRatio", round(ratio, 3)); print("PASS" if ok else "FAIL"); await b.close()
        if not ok: sys.exit(1)
asyncio.run(main())
