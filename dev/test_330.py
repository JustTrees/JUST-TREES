"""3.30 (Dev): the AK's bayonet and the SMG's bigger thermal sight. A jab (the blade tip racing forward along the barrel) stabs; a slow
push doesn't. A stab hurts a raptor that isn't coming at you; a raptor charging you, stabbed in the head, drops at once ("Kill strike!").
The SMG's mini-sight is a rounded square, twice as wide as the old round one.
Usage: python3 dev/test_330.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 240})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(400)
        await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.DEV.ok = false; D.setSeed(4242); D.setVR(true); D.vr.on = true;
          D.setMode('hunt'); Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .7, rough: .5, huntMap: 'globe', dino: false });
          D.generate(); D.state = 'play'; for (let i = 0; i < 20; i++) { D.endlessTick(1 / 30); D.geoTick(1 / 30); } D.MP.code = '9999'; D.set.geoNet = true; D.MP.hp = 100;
          window.run = (secs, f) => { const dt = 1 / 30; for (let i = 0; i < secs * 30; i++) { D.camera.position.set(D.P.x, D.P.y + 1.6, D.P.z); D.ugBeastsTick(dt); if (f) f(i * dt); } };
          // stand in an open hall cell near the middle of a level's grid
          window.standGrid = () => { const L = D.UNDER.cur, G = L.g; let best = null; for (let k = 0; k < G.N * G.M; k++) { if (G.open[k] !== 1) continue; const [x, z] = D.ugCellXZ(G, k), c = Math.hypot(x - (G.x0 + G.N * G.C / 2), z - (G.z0 + G.M * G.C / 2)); if (!best || c < best[2]) best = [x, z, c]; }
            D.P.x = D.UG_X + best[0]; D.P.z = D.UG_Z + best[1]; D.P.y = L.Y + L.fy; };
          return 1; }""")
        out = await pg.evaluate("""() => { const T = D.THREE, o = {}; D.DEV.ok = true; D.ugEnter(1); standGrid(); run(95); const U = D.UGB, A = U.list[0]; if (!A) return { noRaptor: true };
          const S = D.GUNSPOT.ar, G = new T.Group(); D.scene.add(G);
          const headAt = () => { A.root.updateMatrixWorld(true); const v = new T.Vector3(); if (A.qhit) { const h = A.qhit.find(q => q[5]); v.set(h[1], h[2], h[3]).applyMatrix4(h[0].matrixWorld); } else { const h = A.hit.find(q => q[4]); v.set(h[0], h[1], h[2]).applyMatrix4(A.head.matrixWorld); } return v; };
          const bodyAt = () => { A.root.updateMatrixWorld(true); return A.root.position.clone().add(new T.Vector3(0, .55 * (A.scale || 1), 0)); };
          const aim = (target, back) => { const m = new T.Vector3(...S.muzzle); const from = target.clone().add(new T.Vector3(back, .05, 0)); const dir = target.clone().sub(from).normalize(); return [from, dir]; };
          // the blade model on the gun
          const B = D.bayoBlade(G, S.muzzle); o.blade = B.children.length;
          // a jab is seen, a slow push isn't
          D.state = 'play'; D.MP.dead = 0; D.TOOL.bayoLast = null; D.TOOL.bayoCool = 0; G.position.set(D.P.x, D.P.y + 1.4, D.P.z); G.updateMatrixWorld(true);
          D.bayoTick(G, S); G.position.z -= .002; G.updateMatrixWorld(true); D.bayoTick(G, S); o.slowNoJab = !(D.TOOL.bayoCool > 0);
          G.position.z -= .08; G.updateMatrixWorld(true); D.bayoTick(G, S); o.jab = D.TOOL.bayoCool > 0;
          // a raptor just standing there: hurt, not dead
          A.ugs.goal = 'wild'; A.speed = 0; A.ugs.veerT = 99; const hp0 = A.hp; { const [f, d] = aim(bodyAt(), .45); D.bayoStab(f, d); } o.hurt = [A.hp < hp0, !A.dead, D.raptorRushing(A)];
          // charging: stabbed in the head, it drops
          A.ugs.goal = 'charge'; A.speed = 7; o.rushing = D.raptorRushing(A); D.VBAN.t = 0; { const [f, d] = aim(headAt(), .3); D.bayoStab(f, d); } o.killStrike = A.dead;
          // the SMG sight
          const G2 = new T.Group(); const M = D.toolSight(G2, D.GUNSPOT.smg); const disc = M.children[0]; o.sight = [disc.geometry.type, +disc.geometry.parameters.width.toFixed(3), D.TOOL.sight.N];
          D.ugLeave(null); return o; }""")
        print(json.dumps(out)); print("errors:", errs[:5] or "none")
        ok = out.get("blade", 0) >= 3 and out["slowNoJab"] and out["jab"] and out["hurt"] == [True, True, False] and out["rushing"] and out["killStrike"] and out["sight"] == ["PlaneGeometry", 0.084, 384] and not errs
        print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
