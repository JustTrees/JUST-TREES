"""3.40: the headset's automatic detail level. Under 58 fps for a few seconds it steps down (3 → 0), steady at 68+ it tries a step up, and a
step up that didn't hold keeps it down for five minutes; nothing changes while a game is settling in. Each level brings the tree
distances in; far animals are drawn as block copies (a box per body part); the simple middle-distance trees share two shapes per kind.
PC is untouched (no levels, every animal drawn in full). Usage: python3 dev/test_340.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 200})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        pc = await pg.evaluate("() => [D.FADE_D()[1], D.midD()]")           # before VR: the PC's own distances
        await pg.evaluate("""() => { D.QV.lock = 3; D.setSeed(4242); D.setVR(true); D.vr.on = true; D.setMode('hunt'); Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, huntMap: 'globe', dino: false, weather: 'clear', density: .5, rough: .5 }); D.generate(); D.state = 'play'; return 1; }""")
        await pg.wait_for_timeout(14000)                                     # (the real loop: the land and the animals come in)
        r = await pg.evaluate("""(pc) => { const o = {}, Q = D.QV; window.FREEZE = true; D.renderer.setAnimationLoop(null); o.pc = pc;
          const run = (fps, secs) => { for (let i = 0; i < fps * secs; i++) D.qvTick(1 / fps); };
          Q.lv = 3; Q.lock = -1; Q.warm = 0; Q.bad = Q.good = 0; Q.block = 0; Q.upAt = -1e9; Q.t = Q.n = 0;
          Q.warm = 8; run(13, 7); o.warm = Q.lv;                              // settling in: nothing yet
          run(13, 9); o.down1 = Q.lv; run(13, 40); o.down = Q.lv;             // slow: down a step at a time, to the bottom
          run(72, 22); o.up1 = Q.lv;                                          // smooth for a while: a step up
          run(40, 8); o.back = Q.lv; run(72, 60); o.held = Q.lv;              // ...that didn't hold: back down, and it stays there
          Q.block = 0; run(72, 70); o.upAgain = Q.lv;
          Q.lock = 3; o.l3 = [D.FADE_D(), D.midD()]; Q.lock = 0; o.l0 = [D.FADE_D(), D.midD()];
          // the simple trees: at most two batches per kind
          const per = new Map(); for (const it of D.NEAR.lo.items) { const k = it.mat.uuid; per.set(k, (per.get(k) || 0) + 1); } o.loPerMat = Math.max(...per.values()); o.loN = D.NEAR.lo.items.length; o.treeN = D.NEAR.trees.items.length;
          // far animals: block copies
          const A = D.beasts.find(a => a.root && !a.ptero && !a.qr && a.kind !== 'monkey' && a.kind !== 'eagle' && a.kind !== 'bird'); let full = 0; A.root.traverse(m => { if (m.isMesh) full += (m.geometry.index ? m.geometry.index.count : m.geometry.attributes.position.count) / 3; });
          D.camera.position.set(A.x + 400, A.y + 2, A.z); D.camera.updateMatrixWorld(); A.root.visible = true; D.animalGroup.visible = true; D.statuesBefore(); const S = D.STAT.kinds.get(A.kind);
          o.statue = [!!S && S.im.count >= 1, S ? S.im.geometry.attributes.position.count / 3 : -1, Math.round(full), A.root.visible]; D.statuesAfter(); o.shownAgain = A.root.visible;
          D.vr.on = false; D.statuesBefore(); o.pcNoStatues = [...D.STAT.kinds.values()].every(S => !S || S.im.count === 0); D.statuesAfter();
          return o; }""", pc)
        print(json.dumps(r)); print("errors:", errs[:5] or "none")
        ok = r["pc"] == [270, 600] and r["warm"] == 3 and r["down1"] == 2 and r["down"] == 0 and r["up1"] == 1 and r["back"] == 0 and r["held"] == 0 and r["upAgain"] >= 1 \
             and r["l3"] == [[120, 150, 430, 480], 600] and r["l0"] == [[65, 85, 200, 240], 420] and r["loPerMat"] <= 1 and r["loN"] < r["treeN"] \
             and r["statue"][0] and 0 < r["statue"][1] <= 400 and r["statue"][2] > 1000 and not r["statue"][3] and r["shownAgain"] and r["pcNoStatues"] and not errs
        print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
