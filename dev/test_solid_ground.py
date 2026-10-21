import os, sys
TARGET = 'file://' + os.path.abspath(sys.argv[1])
import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader","--enable-webgl","--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width":320,"height":200})).new_page(); errs=[]
        pg.on("pageerror", lambda e: errs.append("PE "+str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = [];
          for (const [biome, lat] of [['temperate', 45], ['boreal', 62], ['tundra', 70]]) {
          D.setMode('hike'); D.set.size = 'medium'; D.set.weather = 'clear'; D.set.lat = lat; D.set.rough = .9; D.generate();
          const T = D.THREE, ray = new T.Raycaster(), res = {};
          const objs = []; D.scene.traverse(o => { if (o.isMesh && o.visible && o.geometry && !o.isSkinnedMesh) objs.push(o); });
          let n = 0, bad = 0; const kinds = {};
          for (let k = 0; k < 4000; k++) {
            const x = (Math.random() - .5) * 500, z = (Math.random() - .5) * 500, g = D.H(x, z);
            ray.set(new T.Vector3(x, g + 60, z), new T.Vector3(0, -1, 0)); ray.far = 120;
            const hits = ray.intersectObjects(objs, false).filter(h => !h.object.material.transparent && !(h.object.material.alphaTest > 0));
            if (!hits.length) continue; const h = hits[0]; n++;
            const solid = Math.max(D.groundAt(x, z), D.rockTop(x, z), D.limbGround(x, z, h.point.y + .5));
            if (h.point.y > solid + .6) { bad++; const key = (h.object.material.type) + ' verts' + h.object.geometry.attributes.position.count + ' inst' + (h.object.count || 1) + (h.object.geometry.attributes.color ? ' col' : ''); kinds[key] = (kinds[key] || 0) + 1; }
          }
          out.push({ lat, samples: n, bad, kinds });
          }
          return out; }""")
        print(json.dumps(r, indent=1)); print(errs or "ok"); await b.close()
asyncio.run(main())
