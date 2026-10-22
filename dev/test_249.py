"""2.49: the menus with the real frame loop running (the other tests step frames by hand, so they missed this): Dev menu > Creature Workshop
and Map Lab take the fog away, and the loop used to set the fog every frame and crash, which froze the headset. Opens each with its button
and lets the game run a few seconds: no page errors, and the frames keep coming.
Usage: python3 dev/test_249.py dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:200]))
        await pg.goto('file://' + os.path.abspath(sys.argv[1])); await pg.wait_for_timeout(1500)
        await pg.evaluate("""() => { D.setVR(true); D.setVRON(true); D.vr.on = true; D.DEV.ok = true; let n = 0; const r0 = D.renderer.render.bind(D.renderer); D.renderer.render = (...a) => { n++; return r0(...a); }; window.frameCount = () => n;
          window.W = (p, l) => D.VRUI.panels[p].widgets.find(w => !(w.hide && w.hide()) && (w.label === l || (w.labelFn && w.labelFn() === l))); D.vruiOpen('dev'); return 1; }""")
        out = {}
        for tool in ["Creature Workshop", "Map Lab"]:
            await pg.evaluate("(t) => { D.vruiOpen('dev'); W('dev', t).on(); return 1; }", tool)
            f0 = await pg.evaluate("() => frameCount()"); await pg.wait_for_timeout(2500); f1 = await pg.evaluate("() => frameCount()")
            out[tool] = [await pg.evaluate("() => D.VRUI.stage"), f1 - f0, len(errs)]
        await pg.evaluate("() => { D.vruiOpen('mode'); return 1; }"); f0 = await pg.evaluate("() => frameCount()"); await pg.wait_for_timeout(1500)
        out["back"] = [await pg.evaluate("() => !!D.scene.fog"), await pg.evaluate("() => frameCount()") - f0]
        print(json.dumps(out))
        ok = out["Creature Workshop"][0] == "work" and out["Map Lab"][0] == "lab" and all(out[t][1] > 5 for t in ("Creature Workshop", "Map Lab")) and out["back"][0] and out["back"][1] > 3 and not errs
        print("errors:", errs[:3] or ("none" if ok else "CHECKS FAILED")); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
