"""Every animal's head and neck can be hit: rays fired from the side across the drawn head/neck must hit the animal's hit boxes."""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 200})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.setMode('hunt'); D.set.lat = 42; D.generate(); D.state = 'play';
          const T = D.THREE, kinds = ['buck','bear','polar','baboon','panther','wolf','seal','rabbit','elephant','giraffe','zebra','rhino','lion','crocodile','horse','elk','moose','boar','goat','turkey','coyote','fox','caribou','muskox','arcticfox','bigfoot','yeti'];
          const out = {}, rc = new T.Raycaster();
          for (const k of kinds) {
            for (const A of D.beasts) A.root.visible = false;
            const A = D.addGround(k, 0, 0); A.x = 0; A.z = 0; A.y = 0; A.yaw = 0; A.root.position.set(0, 0, 0); A.root.rotation.set(0, 0, 0); A.root.visible = true; A.root.updateMatrixWorld(true);
            const heads = [], bodyMeshes = []; A.head.traverse(o => o.isMesh && heads.push(o)); A.body.children.forEach(o => o.isMesh && bodyMeshes.push(o));
            // where the neck starts: the front of the body hit spheres
            let front = -1e9; for (const h of A.hit) if (!h[4]) front = Math.max(front, h[2] * A.scale); front = Math.min(front, A.head.getWorldPosition(new T.Vector3()).z - .05);
            const box = new T.Box3().setFromObject(A.root); let tot = 0, got = 0; const miss = [];
            for (let y = box.min.y; y <= box.max.y; y += (box.max.y - box.min.y) / 40) for (let z = front; z <= box.max.z; z += (box.max.z - front) / 30) {
              const o = new T.Vector3(-30, y, z), d = new T.Vector3(1, 0, 0); rc.set(o, d);
              const hit = rc.intersectObjects(heads.concat(bodyMeshes), false)[0]; if (!hit) continue;
              const onHead = heads.includes(hit.object); if (!onHead && hit.point.z < front) continue;
              // skip thin parts (antlers, horns, ears, tusks, beards): the drawn thickness across is under 6 cm
              const back = new T.Raycaster(new T.Vector3(30, y, z), new T.Vector3(-1, 0, 0)).intersectObjects(heads.concat(bodyMeshes), false)[0]; if (!back || back.point.x - hit.point.x < .06 * A.scale) continue;
              const ms = heads.concat(bodyMeshes), q = hit.point.clone().add(new T.Vector3(.01, 0, 0)), dn = new T.Raycaster(new T.Vector3(q.x, 30, q.z), new T.Vector3(0, -1, 0)).intersectObjects(ms, false).filter(h => Math.abs(h.point.y - q.y) < .5), up = new T.Raycaster(new T.Vector3(q.x, -30, q.z), new T.Vector3(0, 1, 0)).intersectObjects(ms, false).filter(h => Math.abs(h.point.y - q.y) < .5);
              if (dn.length && up.length && up[0].point.y > dn[0].point.y - .06 * A.scale && up[0].point.y < dn[0].point.y + .001 && dn[0].point.y - up[0].point.y < .06 * A.scale) continue;   // flat thin parts (moose antlers)
              tot++; const [t, who] = D.animalRay(o, d, .1); if (who === A) got++; else if (miss.length < 3) miss.push([+y.toFixed(2), +z.toFixed(2), onHead ? 'head' : 'neck']);
            }
            out[k] = { pct: Math.round(100 * got / Math.max(1, tot)), n: tot, miss };
            A.dead = true; A.root.visible = false;
          }
          return out; }""")
        bad = {k: v for k, v in r.items() if v["pct"] < 85}
        print(json.dumps({k: v["pct"] for k, v in r.items()})); print("weak:", json.dumps(bad))
        z = await pg.evaluate("() => ({ scope: D.scopeFovs ? null : null })")
        print("PASS" if not bad and not errs else "FAIL", errs or ""); await b.close()
        if bad or errs: sys.exit(1)
asyncio.run(main())
