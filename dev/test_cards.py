"""Drawing less, the same look (1.86, 1.88): near batches + three distances. Full detail near you, simpler real 3D trees in the
middle, cards far out, with fades between (each tree dissolves from one version to the next). The batches are refilled per 80 m
cell when you move, never when you only turn your head. Checks every tree has the right version loaded at every distance.
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
            await pg.goto(T, timeout=120000); await pg.wait_for_timeout(600)
            out[size] = await pg.evaluate("""(size) => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setSeed(4); D.setVR(true); D.setMode('hike'); D.set.size = size; D.set.lat = 44; D.set.env = 'climate'; D.generate(); D.state = 'play';
              const cam = D.camera, N = D.NEAR, tiles = D.tiles, r = {};
              const look = (x, z, yaw) => { cam.position.set(x, D.H(x, z) + 1.7, z); cam.rotation.set(0, yaw, 0); cam.updateMatrixWorld(); D.cullTiles(); D.renderer.info.reset(); D.renderer.render(D.scene, cam); return D.renderer.info.render.calls; };
              r.calls = look(D.P.x, D.P.z, 0);
              // every tree has the version it needs loaded: detailed inside a1, simple from a0 to b1, cards (its square shown) past b0
              const F = [D.FADE.uFA.value.x, D.FADE.uFA.value.y, D.FADE.uFB.value.x, D.FADE.uFB.value.y], cx = cam.position.x, cz = cam.position.z;
              const missing = { hi: 0, lo: 0, card: 0 }, have = { hi: 0, lo: 0 };
              const scan = (NS, inBand, key) => { for (const E of NS.items) for (const [q, bl] of E.blocks) for (let i = 0; i < bl.n; i++) { const d = Math.hypot(bl.m[i * 16 + 12] - cx, bl.m[i * 16 + 14] - cz); if (inBand(d)) { if (NS.flags[q]) have[key]++; else missing[key]++; } } };
              scan(N.trees, d => d < F[1], 'hi'); scan(N.lo, d => d > F[0] && d < F[3], 'lo');
              tiles.forEach(t => { if (!t.hi) return; const m = t.lo.children.find(c => c.userData.card); if (!m) return; const a = m.instanceMatrix.array; let far = false; for (let i = 0; i < m.count && !far; i++) far = Math.hypot(a[i * 16 + 12] - cx, a[i * 16 + 14] - cz) > F[2]; if (far && !t.lo.visible) missing.card++; });
              r.missing = missing; r.have = have; r.fade = F;
              let cardsAll = 0; tiles.forEach(t => { if (t.hi) cardsAll += t.lo.children.filter(m => m.userData.card).reduce((a, m) => a + m.count, 0); }); r.cardsAll = cardsAll;
              let ok = true; for (const nm in N) { for (const E of N[nm].items) { let s2 = 0; for (const [q, bl] of E.blocks) if (N[nm].flags[q]) s2 += bl.n; if (s2 !== E.mesh.count) ok = false; } } r.nearMatches = ok;
              // turning the head doesn't refill
              const f0 = N.trees.flags.slice(); let refills = 0; const orig = N.trees.items[0].mesh.instanceMatrix.version;
              for (let a = 1; a < 8; a++) look(D.P.x, D.P.z, a * .8); r.turnRefill = N.trees.items[0].mesh.instanceMatrix.version !== orig;
              // walking 400 m away does
              look(D.P.x + 400 > D.EDGE ? D.P.x - 400 : D.P.x + 400, D.P.z, 0); r.moveRefill = N.trees.items.some(E => E.mesh.instanceMatrix.version !== orig) || N.trees.flags.some((f, i) => f !== f0[i]);
              // small things only near
              let smallFar = 0; for (const E of N.small.items) for (const [q, bl] of E.blocks) if (N.small.flags[q]) { for (let i = 0; i < bl.n; i++) if (Math.hypot(bl.m[i * 16 + 12] - cam.position.x, bl.m[i * 16 + 14] - cam.position.z) > D.SMALL_D + 120) smallFar++; }
              r.smallFar = smallFar; r.cardsTex = !!(D.CARD && D.CARD.mat && D.CARD.mat.map);
              return r; }""", size)
            await pg.close()
        print(json.dumps(out)); print("errors:", errs or "none")
        ok = all(v["calls"] < 400 and v["nearMatches"] and v["missing"] == {"hi": 0, "lo": 0, "card": 0} and v["have"]["hi"] > 100 and v["have"]["lo"] > 100 and v["cardsAll"] > 1000 and not v["turnRefill"] and v["moveRefill"] and v["smallFar"] == 0 and v["cardsTex"] for v in out.values()) and not errs
        print("PASS" if ok else "FAIL"); await b.close()
        if not ok: sys.exit(1)
asyncio.run(main())
