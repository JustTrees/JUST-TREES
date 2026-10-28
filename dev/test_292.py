"""2.92: online Treeocashing: below level 30 the hammock doesn't dream: sleep at night and you wake up on the island (one big island,
the same for everyone), a little healed; the next night, sleep there and you're back where you came from. One sleep a night.
Usage: python3 dev/test_292.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 240})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(400)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); localStorage.setItem('jt-geochar', JSON.stringify({ n: 14, score: 0, kills: 0 })); D.DEV.ok = true; D.setSeed(4242); D.setVR(true); D.vr.on = true; D.set.hand = 'right';
          D.setMode('hunt'); Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .7, rough: .5, huntMap: 'globe', dino: false });
          D.generate(); D.state = 'play'; for (let i = 0; i < 40; i++) { D.endlessTick(1 / 30); D.geoTick(1 / 30); } D.MP.code = '9999'; D.set.geoNet = true;
          const o = {}, T = D.THREE, P = D.P, dt = 1 / 30, G = D.GLOBE;
          const I = { head: new T.Vector3(), headQ: new T.Quaternion(), hands: {} }, hand = () => ({ pos: new T.Vector3(), rayPos: new T.Vector3(), rayQ: new T.Quaternion(), q: new T.Quaternion(), grip: 0, trig: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 });
          const M = hand(), O = hand(); I.hands.right = M; I.hands.left = O; D.vr.I = I; D.vr.main = M; D.vr.headLocalY = 1.6;
          const tick = n => { for (let i = 0; i < n; i++) { I.head.set(P.x, P.y + 1.6, P.z); D.geoGearTick(I, M, O, dt); D.update(dt); D.endlessTick(dt); } };
          const press = () => { M.trig = 1; tick(1); M.trig = 0; tick(1); };
          D.geoGearApply(14, true);
          const hang = () => { for (let k = 0; k < 120; k++) D.endlessTick(dt); const ts = []; for (const l of D.obstacles.values()) for (const t of l) if (t.tr > .12 && Math.hypot(t.x - P.x, t.z - P.z) < 300) ts.push(t);
            let pr = null; for (const a of ts) { for (const c of ts) { const d = Math.hypot(a.x - c.x, a.z - c.z) - a.tr - c.tr; if (a !== c && d > 3.4 && d < 4.6) { pr = [a, c]; break; } } if (pr) break; } if (!pr) return false;
            const [A, B] = pr; P.x = (A.x + B.x) / 2 + 1.5; P.z = (A.z + B.z) / 2; P.y = D.groundAt(P.x, P.z); D.geoHeld('tent');
            for (const t0 of [A, B]) { const t = t0 === B && D.GEO.hmB ? D.GEO.hmB : t0; M.pos.set(t.x + t.tr + .1, D.groundAt(t.x, t.z) + 1.2, t.z); press(); } D.geoHeld(null); return !!D.GEO.hm; };
          o.hung = hang(); if (!o.hung) return o; const home = D.glToSphere(P.x, P.z, [0, 0, 0]);
          D.glabTime(23); D.globeTick(0); M.pos.copy(D.GEO.hm.mid); press(); tick(30); M.b = 1; tick(1); M.b = 0; tick(40); M.pos.copy(D.GEO.hm.mid); press(); tick(5); o.once = !D.GEO.sleep && !!D.GEO.hm;   // one sleep a night
          D.GEO.sleptNight = false; const hp0 = D.MP.hp = 50; M.pos.copy(D.GEO.hm.mid); press(); const st = []; for (let i = 0; i < 30 * 9; i++) { tick(1); const s = D.GEO.sleep && D.GEO.sleep.st; if (s && st[st.length - 1] !== s) st.push(s); }
          const isle = D.geoIsland(); o.phases = st.join(','); o.awake = !D.GEO.sleep; o.toIsle = Math.round(D.glArc(D.glToSphere(P.x, P.z, [0, 0, 0]), isle) * G.R); o.fromHome = Math.round(D.glArc(D.glToSphere(P.x, P.z, [0, 0, 0]), home) * G.R); o.hp = Math.round(D.MP.hp - hp0);
          o.isleLand = G.landAt(isle) > 1.5; o.onIsle = D.GEO.onIsle;
          // once a night
          o.hung2 = hang(); { let n = 0, nb = 0; for (const l of D.obstacles.values()) for (const t of l) { nb++; if (t.tr > .12 && Math.hypot(t.x - P.x, t.z - P.z) < 300) n++; } o.trees = [n, nb]; const R0 = D.GLOBE.R, q = D.glToSphere(P.x, P.z, [0, 0, 0]), k = D.GLOBE.regionsP(q, q[0] * R0, q[1] * R0, q[2] * R0); o.biome = D.EN_RL ? D.EN_RL[0].reg.b : k; o.ll = D.glLatLon(q).map(Math.round); } if (!o.hung2) return o; D.glabTime(23); D.globeTick(0);
          // a day goes by; the next night, back where you came from
          D.glabTime(12); D.globeTick(0); tick(2); D.glabTime(23); D.globeTick(0); M.pos.copy(D.GEO.hm.mid); press(); for (let i = 0; i < 30 * 9; i++) tick(1);
          o.back = [!D.GEO.sleep, Math.round(D.glArc(D.glToSphere(P.x, P.z, [0, 0, 0]), home) * G.R), D.GEO.onIsle];
          return o; }""")
        print(json.dumps(r))
        ok = r["hung"] and r["phases"].startswith("settle,blink,dark,trip") and r["awake"] and r["toIsle"] < 400 and r["fromHome"] > 1000 and r["hp"] >= 29 and r["isleLand"] and r["onIsle"] \
             and r["hung2"] and r["once"] and r["back"][0] and r["back"][1] < 300 and r["back"][2] is False
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
