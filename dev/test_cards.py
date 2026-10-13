"""Drawing less, the same look (1.86): near batches + tree cards. Every tree is drawn once: full detail in the squares near you
(one batch per shape for the whole map, refilled when you move into new squares), a card further out. Bushes/pebbles/logs only
within SMALL_D, boulders within MID_D. Far fewer draw calls than before; nothing refills while you only turn your head.
Usage: python3 dev/test_cards.py /tmp/dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
T = 'file://' + os.path.abspath(sys.argv[1])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        out = {}; errs = []
        for size in ["medium", "xxl"]:
            pg = await (await b.new_context(viewport={"width": 400, "height": 260})).new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(T); await pg.wait_for_timeout(600)
            out[size] = await pg.evaluate("""(size) => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setSeed(4); D.setVR(true); D.setMode('hike'); D.set.size = size; D.set.lat = 44; D.set.env = 'climate'; D.generate(); D.state = 'play';
              const cam = D.camera, N = D.NEAR, tiles = D.tiles, r = {};
              const look = (x, z, yaw) => { cam.position.set(x, D.H(x, z) + 1.7, z); cam.rotation.set(0, yaw, 0); cam.updateMatrixWorld(); D.cullTiles(); D.renderer.info.reset(); D.renderer.render(D.scene, cam); return D.renderer.info.render.calls; };
              r.calls = look(D.P.x, D.P.z, 0);
              // every tree exactly once: near trees = trees in near squares; cards everywhere, shown only away from you
              let cardsAll = 0, cardsShown = 0, treesNearSq = 0, ok = true;
              tiles.forEach((t, i) => { if (!t.hi) return; const c = t.lo.children.filter(m => m.userData.card).reduce((a, m) => a + m.count, 0); cardsAll += c; if (N.trees.flags[i]) treesNearSq += c; else if (t.lo.visible) cardsShown += c; if (t.lo.visible === !!N.trees.flags[i]) ok = false; });
              r.cardsAll = cardsAll; r.cardSwitchOk = ok;
              let nearCount = 0, blockSum = 0; for (const E of N.trees.items) { nearCount += E.mesh.count; for (const [ti, bl] of E.blocks) if (N.trees.flags[ti]) blockSum += bl.n; }
              r.nearMatches = nearCount === blockSum; r.nearTrees = nearCount; r.treesInNearSquares = treesNearSq;
              // turning the head doesn't refill
              const f0 = N.trees.flags.slice(); let refills = 0; const orig = N.trees.items[0].mesh.instanceMatrix.version;
              for (let a = 1; a < 8; a++) look(D.P.x, D.P.z, a * .8); r.turnRefill = N.trees.items[0].mesh.instanceMatrix.version !== orig;
              // walking 400 m away does
              look(D.P.x + 400 > D.EDGE ? D.P.x - 400 : D.P.x + 400, D.P.z, 0); r.moveRefill = N.trees.items.some(E => E.mesh.instanceMatrix.version !== orig) || N.trees.flags.some((f, i) => f !== f0[i]);
              // small things only near
              let smallFar = 0; for (const E of N.small.items) for (const [ti, bl] of E.blocks) if (N.small.flags[ti]) { const t = tiles[ti]; if (Math.hypot(t.cx - cam.position.x, t.cz - cam.position.z) > D.SMALL_D + 200) smallFar++; }
              r.smallFar = smallFar; r.cardsTex = !!(D.CARD && D.CARD.mat && D.CARD.mat.map);
              return r; }""", size)
            await pg.close()
        print(json.dumps(out)); print("errors:", errs or "none")
        ok = all(v["calls"] < 400 and v["cardSwitchOk"] and v["nearMatches"] and v["nearTrees"] > 0 and v["cardsAll"] > 1000 and not v["turnRefill"] and v["moveRefill"] and v["smallFar"] == 0 and v["cardsTex"] for v in out.values()) and not errs
        print("PASS" if ok else "FAIL"); await b.close()
        if not ok: sys.exit(1)
asyncio.run(main())
