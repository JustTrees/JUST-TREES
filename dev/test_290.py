"""2.90: the Underworld (online Treeocashing). A doorway of haze on a tree (only at level 50+); through it, the stairs: 100 m down, a
left turn, 100 m more; the mall and the Backrooms at the bottom; walls you can't walk through; the far door (it opens as you come, slams
behind you) into the bunker; its blast door into the hellscape; lava burns; back up through the doors and the haze to the tree.
Usage: python3 dev/test_290.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 240})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(400)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); localStorage.setItem('jt-geochar', JSON.stringify({ n: 3, score: 0, kills: 0 })); D.DEV.ok = false; D.setSeed(4242); D.setVR(true); D.vr.on = true; D.set.hand = 'right';
          D.setMode('hunt'); Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .7, rough: .5, huntMap: 'globe', dino: false });
          D.generate(); D.state = 'play'; for (let i = 0; i < 40; i++) { D.endlessTick(1 / 30); D.geoTick(1 / 30); } D.MP.code = '9999'; D.set.geoNet = true;
          const o = {}, T = D.THREE, P = D.P, U = D.UNDER, dt = 1 / 30;
          const I = { head: new T.Vector3(), headQ: new T.Quaternion(), hands: {} }, hand = () => ({ pos: new T.Vector3(), rayPos: new T.Vector3(), rayQ: new T.Quaternion(), q: new T.Quaternion(), grip: 0, trig: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 });
          const M = hand(), O = hand(); I.hands.right = M; I.hands.left = O; D.vr.I = I; D.vr.main = M; D.vr.headLocalY = 1.6;
          const sync = () => { I.head.set(P.x, P.y + 1.6, P.z); M.pos.copy(I.head); O.pos.copy(I.head); };
          const tick = n => { for (let i = 0; i < n; i++) { sync(); D.geoGearTick(I, M, O, dt); D.update(dt); D.geoTick(dt); } };
          const walk = (yaw, secs) => { P.yaw = yaw; D.input.jy = 1; D.input.jx = 0; tick(Math.round(secs * 30)); D.input.jy = 0; };
          const L = () => D.ugLocal(P.x, P.z).map(v => Math.round(v * 10) / 10);
          // a doorway on a tree: hidden below level 50, seen at 50+
          const T0 = []; for (const l of D.obstacles.values()) for (const t of l) if (t.tr > .2 && Math.hypot(t.x - P.x, t.z - P.z) < 60) T0.push(t);
          const tr = T0[0]; U.labP = null; D.GEO.lab = false;
          for (const ch of D.ENDLESS.chunks.values()) ch.ugP = undefined;
          U.scanT = 0; tick(2); const ch0 = [...D.ENDLESS.chunks.values()].find(c => c.ugP && D.ENDLESS.chunks.get(c.key) === c);
          o.hidden = U.pt.size === 0;
          localStorage.setItem('jt-geochar', JSON.stringify({ n: 60, score: 0, kills: 0 })); for (let i = 1; i <= 60; i++) D.GEO.found.add(1000 + i);
          U.labP = { x: tr.x, z: tr.z, tr: tr.tr, a: 0 }; U.scanT = 0; tick(2); o.seen = U.pt.size > 0; o.natural = !!ch0;
          // walk into the haze
          P.x = tr.x + tr.tr + 3; P.z = tr.z; P.y = D.groundAt(P.x, P.z); tick(60); walk(Math.PI / 2, 1.2); tick(40);
          o.in = [U.on, U.idx, L(), Math.round(P.y - U.cur.Y)];
          // the walls hold you
          walk(-Math.PI / 2, 2); o.wall = L()[0] <= 1.21;
          // down the stairs: 100 m, left, 100 m
          P.x = D.UG_X; P.z = D.UG_Z + 1.5; walk(0, 20); o.stair1 = [L(), Math.round(P.y - U.cur.Y)];
          walk(Math.PI / 2, 30); o.stair2 = [L(), Math.round(P.y - U.cur.Y), Math.round(U.cur.fy)];
          o.inGrid = !!U.cur.g && L()[0] < U.cur.g.x0 + U.cur.g.N * 3;
          // the far door: it opens, you go through, it slams behind you
          const dn = U.cur.doors.find(d => d.id === 'down'); P.x = D.UG_X + dn.x + dn.nx * 3; P.z = D.UG_Z + dn.z + dn.nz * 3; P.y = U.cur.Y + U.cur.fy;
          walk(Math.atan2(dn.nx, dn.nz), 1.2); tick(40); o.bunker = [U.idx, U.cur.name]; const up2 = U.cur.doors.find(d => d.id === 'up'); o.slam = up2.open < .05;
          // back through it, and down again
          walk(Math.atan2(up2.nx, up2.nz), 1.5); tick(40); o.backUp = U.idx;
          const dn1 = U.cur.doors.find(d => d.id === 'down'); P.x = D.UG_X + dn1.x + dn1.nx * 3; P.z = D.UG_Z + dn1.z + dn1.nz * 3; walk(Math.atan2(dn1.nx, dn1.nz), 1.2); tick(40);
          const d2 = U.cur.doors.find(d => d.id === 'down'); P.x = D.UG_X + d2.x + d2.nx * 3; P.z = D.UG_Z + d2.z + d2.nz * 3; P.y = U.cur.Y; walk(Math.atan2(d2.nx, d2.nz), 1.5); tick(40);
          o.hell = [U.idx, U.cur.name, L()];
          // lava burns
          const H = U.cur; let lv = null; for (let a = 0; a < 6.28 && !lv; a += .05) for (let r = 15; r < 60 && !lv; r += 1) { const x = Math.cos(a) * r, z = Math.sin(a) * r; if (D.ugFloor(H, x, z) < -.5) lv = [x, z]; }
          const hp0 = D.MP.hp; P.x = D.UG_X + lv[0]; P.z = D.UG_Z + lv[1]; tick(15); o.burn = Math.round(hp0 - D.MP.hp); D.MP.hp = 100;
          // back up to the land: hell -> bunker -> backrooms -> the haze
          D.ugEnter(1, 'top'); P.x = D.UG_X; P.z = D.UG_Z + 1.6; walk(Math.PI, 1.5); tick(45);
          o.out = [U.on, D.sky.visible, Math.round(Math.hypot(P.x - tr.x, P.z - tr.z) * 10) / 10];
          return o; }""")
        print(json.dumps(r))
        ok = r["hidden"] and r["seen"] and r["in"][0] and r["in"][1] == 1 and r["wall"] and abs(r["stair1"][1] + 77) < 3 and abs(r["stair2"][1] + 153) < 3 and r["inGrid"] \
             and r["bunker"] == [2, "bunker"] and r["slam"] and r["backUp"] == 1 and r["hell"][:2] == [3, "hell"] and r["burn"] > 5 and r["out"][0] is False and r["out"][1] and r["out"][2] < 20
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
