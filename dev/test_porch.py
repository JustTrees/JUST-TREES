"""The tallest tree's porch: above every other treetop, no branches round it, you stand on it and walk (and animals walk) under it,
the middle is open to climb through; the one red sniper lies on it (none on the ground); sniper zoom steps = its stars."""
import os, sys, asyncio, json, base64
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1]); SHOTS = sys.argv[2] if len(sys.argv) > 2 and os.path.isdir(sys.argv[2]) else None
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 900, "height": 560})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        out = []
        for lat, size, sd in [[45, "medium", 11], [58, "large", 222], [12, "small", 3333], [40, "medium", 44], [50, "small", 505]]:
            r = await pg.evaluate("""([lat, size, sd]) => { window.FREEZE = true; D.setSeed(sd); D.setVR(true); D.setMode('hunt'); D.set.size = size; D.set.weather = 'clear'; D.set.lat = lat; D.generate(); D.state = 'play';
              const Pc = D.PORCH, o = { lat, porch: !!Pc }; if (!Pc) return o;
              o.top = +Pc.top.toFixed(1); o.name = Pc.name; o.base = +Pc.tree.y.toFixed(1); o.ground = +D.H(Pc.x, Pc.z).toFixed(1);
              // other trees' tops: highest within 300 m
              const T = D.THREE; let other = -1e9, giantTop = 0;
              D.scene.traverse(m => { if (!m.isInstancedMesh) return; });
              o.standOnDeck = +D.rockTopAt(Pc.x + Pc.rIn + 1.3, Pc.z, Pc.top + .05, 1.6).toFixed(1);
              o.underDeck = D.rockTopAt(Pc.x + Pc.rIn + 1.3, Pc.z, D.H(Pc.x + Pc.rIn + 1.3, Pc.z), 1.6) < -1e8;
              o.holeOpen = D.rockTopAt(Pc.x + Pc.rIn - .5, Pc.z, Pc.top + .05, 1.6) < Pc.top - 2;   // nothing solid up at the deck (a log on the ground far below is fine)
              const red = [...D.DROPS.values()].filter(d => d.type === 'gun' && d.tier === 5 && d.kind === 'hunt');
              o.redSnipers = red.length; o.redOnDeck = red.length === 1 && Math.abs(red[0].y - Pc.top) < .01 && red[0].id === 'gRed';
              // an animal walking under it stays on the ground
              const A = D.beasts.find(a => !a.wings && a.kind !== 'monkey'); if (A) { A.y = D.H(Pc.x + Pc.rIn + 1.3, Pc.z); o.animalUnder = +(D.beastGround(A, Pc.x + Pc.rIn + 1.3, Pc.z) - A.y).toFixed(2); }
              // zoom steps by stars
              o.steps = [1, 2, 3, 4, 5].map(st => { D.setLoot({ hunt: st, pistol: 1 }); D.vr.gunKind = 'hunt'; return D.scopeFovs().length; });
              return o; }""", [lat, size, sd])
            # clear view: no branch geometry of the giant near porch height (beyond the trunk)
            r2 = await pg.evaluate("""() => { const Pc = D.PORCH; if (!Pc) return null; const T = D.THREE; let n = 0, other = 0, m4 = new T.Matrix4(), v = new T.Vector3();
              const sets = []; const nearMeshes = new Set();   /* 1.86: trees live in near batches (all squares' instances in their blocks) and cards; measure the real trees */
              if (D.NEAR) for (const NS of [D.NEAR.trees]) for (const E of NS.items) { nearMeshes.add(E.mesh); for (const bl of E.blocks.values()) sets.push([E.mesh, bl.m, bl.n]); }
              D.scene.traverse(m => { if (m.isInstancedMesh && !m.userData.card && !nearMeshes.has(m)) sets.push([m, m.instanceMatrix.array, m.count]); });
              for (const [m, arr, cnt] of sets) { if (!m.geometry.attributes.position) continue;
                for (let i = 0; i < cnt; i++) { m4.fromArray(arr, i * 16); const px = m4.elements[12], pz = m4.elements[14]; const dd = Math.hypot(px - (Pc.tree ? Pc.tree.x : Pc.x), pz - (Pc.tree ? Pc.tree.z : Pc.z));
                  if (dd < .5) { const P = m.geometry.attributes.position; for (let k = 0; k < P.count; k += 3) { v.fromBufferAttribute(P, k).applyMatrix4(m4); const r = Math.hypot(v.x - Pc.x, v.z - Pc.z); if (v.y > Pc.top - .3 && v.y < Pc.top + 3 && r > Pc.rIn - .2 && r < 30) n++; } }
                  else if (dd < 250) { const sy = Math.hypot(m4.elements[4], m4.elements[5], m4.elements[6]); other = Math.max(other, m4.elements[13] + sy * (m.geometry.boundingBox || (m.geometry.computeBoundingBox(), m.geometry.boundingBox)).max.y - m4.elements[13]); } } }
              return { branchVertsInView: n, tallestOtherTop: +other.toFixed(1) }; }""")
            r.update(r2 or {}); out.append(r)
            if SHOTS and lat == 45:
                for name, yaw, pitch in [("porch_view", 0, -.05), ("porch_view2", 2.4, -.1)]:
                    img = await pg.evaluate("""([yaw, pitch]) => { const Pc = D.PORCH, c = new D.THREE.PerspectiveCamera(80, 900 / 560, .1, 3000);
                      const x = Pc.x + Math.cos(yaw) * (Pc.rIn + 1.6), z = Pc.z + Math.sin(yaw) * (Pc.rIn + 1.6); c.position.set(x, Pc.top + 1.65, z);
                      c.lookAt(x + Math.cos(yaw) * 10, Pc.top + 1.65 + pitch * 10, z + Math.sin(yaw) * 10); D.renderer.setSize(900, 560, false); D.renderer.render(D.scene, c); return D.renderer.domElement.toDataURL('image/jpeg', .85); }""", [yaw, pitch])
                    open(os.path.join(SHOTS, name + ".jpg"), "wb").write(base64.b64decode(img.split(",", 1)[1]))
                for name, d, h in [("porch_tree", 26, 4), ("porch_close", 9, 2.5)]:
                    img = await pg.evaluate("""([d, h]) => { const Pc = D.PORCH, c = new D.THREE.PerspectiveCamera(60, 900 / 560, .1, 3000);
                      c.position.set(Pc.x + d, Pc.top + h, Pc.z + d * .4); c.lookAt(Pc.x, Pc.top - 1, Pc.z); D.renderer.setSize(900, 560, false); D.renderer.render(D.scene, c); return D.renderer.domElement.toDataURL('image/jpeg', .85); }""", [d, h])
                    open(os.path.join(SHOTS, name + ".jpg"), "wb").write(base64.b64decode(img.split(",", 1)[1]))
        print(json.dumps(out))
        ok = all(o["porch"] and abs(o["standOnDeck"] - o["top"]) < .05 and o["underDeck"] and o["holeOpen"] and o["redSnipers"] == 1 and o["redOnDeck"] and o.get("animalUnder", 0) < .5
                 and o["steps"] == [1, 2, 3, 4, 5] and o["branchVertsInView"] == 0 and o["top"] - o["base"] > o["tallestOtherTop"] for o in out)
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
