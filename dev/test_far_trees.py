import os, sys
TARGET = 'file://' + os.path.abspath(sys.argv[1])
import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader","--enable-webgl","--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width":640,"height":400})).new_page(); errs=[]
        pg.on("pageerror", lambda e: errs.append("PE "+str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.setVR(true); D.setMode('hike'); D.set.size = 'xxl'; D.set.weather = 'clear'; D.set.lat = 45; D.generate(); D.state = 'play';
          const c = D.camera; c.position.set(D.P.x, D.P.y + 1.7, D.P.z); c.rotation.set(0, D.P.yaw, 0); c.fov = 72; c.updateProjectionMatrix();
          D.scene.fog.far = 1500; D.cullTiles(); let hi = 0, lo = 0; for (const t of D.tiles) if (t.hi && t.group.visible) { if (t.hi.visible) hi++; else lo++; }
          D.renderer.info.autoReset = true; D.renderer.render(D.scene, c); const triLod = D.renderer.info.render.triangles;
          for (const t of D.tiles) if (t.hi) { t.hi.visible = t.group.visible; t.lo.visible = false; }
          D.renderer.render(D.scene, c); const triFull = D.renderer.info.render.triangles;
          for (const t of D.tiles) if (t.hi) { t.hi.visible = false; t.lo.visible = t.group.visible; }
          D.renderer.render(D.scene, c); const triAllLo = D.renderer.info.render.triangles;
          D.cullTiles(); D.renderer.render(D.scene, c);
          return { hi, lo, triLod, triFull, triAllLo }; }""")
        print(json.dumps(r)); return
        await pg.evaluate("() => { for (const el of document.body.children) if (el.tagName !== 'CANVAS') el.style.display = 'none'; }")
        await pg.screenshot(path="/tmp/lod.png")
        print(json.dumps(r)); print(errs or "ok"); await b.close()
asyncio.run(main())
