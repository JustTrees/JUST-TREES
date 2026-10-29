"""3.25: the Dev camera. In Dev Mode, through the binoculars, the trigger takes a picture (the gun doesn't fire); pictures are kept in this
browser (IndexedDB), listed newest first on the Dev menu's Photos page, and can be deleted (tap Delete twice). Not in Dev Mode: nothing.
Usage: python3 dev/test_325.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        r = await pg.evaluate("""async () => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setSeed(4242); D.setVR(false); D.setMode('hike'); D.generate(); D.state = 'play';
          const o = {}, PH = D.PHOTO; await D.photoRefresh(); for (const ph of PH.list.slice()) await D.photoDelete(ph.id); o.empty = PH.list.length;
          D.camera.position.set(D.P.x, D.P.y + 1.7, D.P.z); D.camera.lookAt(D.P.x + 50, D.P.y + 5, D.P.z); D.camera.updateMatrixWorld();
          D.renderer.render(D.scene, D.camera); D.photoShoot(); for (let k = 0; k < 40; k++) { await new Promise(r => setTimeout(r, 300)); await D.photoRefresh(); if (PH.list.length >= 1) break; } o.one = PH.list.length;
          const ph = PH.list[0]; o.jpeg = ph && ph.blob && ph.blob.type; o.kb = ph ? Math.round(ph.blob.size / 1024) : 0; o.size = ph ? [ph.w, ph.h] : null;
          // what's in it: not a blank picture
          const im = await new Promise(res => { const i = new Image(); i.onload = () => res(i); i.src = URL.createObjectURL(ph.blob); }); const cv = document.createElement('canvas'); cv.width = 64; cv.height = 36; const g = cv.getContext('2d'); g.drawImage(im, 0, 0, 64, 36);
          const d = g.getImageData(0, 0, 64, 36).data; let lo = 255, hi = 0, sum = 0; for (let i = 0; i < d.length; i += 4) { const v = (d[i] + d[i + 1] + d[i + 2]) / 3; lo = Math.min(lo, v); hi = Math.max(hi, v); sum += v; } o.range = [Math.round(lo), Math.round(hi), Math.round(sum / (d.length / 4))];
          D.renderer.render(D.scene, D.camera); D.photoShoot(); for (let k = 0; k < 40; k++) { await new Promise(r => setTimeout(r, 300)); await D.photoRefresh(); if (PH.list.length >= 2) break; } o.two = PH.list.length; o.newestFirst = PH.list[0].id > PH.list[1].id;
          await D.photoDelete(PH.list[0].id); o.afterDelete = PH.list.length;
          return o; }""")
        print(json.dumps(r)); print("errors:", errs[:5] or "none")
        ok = r["empty"] == 0 and r["one"] == 1 and r["jpeg"] == "image/jpeg" and r["size"] == [1920, 1080] and r["kb"] > 30 and r["range"][1] - r["range"][0] > 40 and 20 < r["range"][2] < 240 \
             and r["two"] == 2 and r["newestFirst"] and r["afterDelete"] == 1 and not errs
        print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
