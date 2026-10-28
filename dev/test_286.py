"""2.86 (2.88: the dream sight): online Treeocashing (Dev): the hammock. Tie it to one trunk, then another 3–5 m away; sleep only at night; you settle,
blink, go dark and rise out of your body; fly with the sticks (tied to within 1.2 km of your body); the world goes ghostly; the others
see your body in the hammock; a predator coming for your body warns you and snaps you back; B wakes you any time.
Usage: python3 dev/test_286.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 240})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(400)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); localStorage.setItem('jt-geochar', JSON.stringify({ n: 40, score: 0, kills: 0 })); D.DEV.ok = true; D.setSeed(4242); D.setVR(true); D.vr.on = true; D.set.hand = 'right';
          D.setMode('hunt'); Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .7, rough: .5, huntMap: 'globe', dino: false });
          D.generate(); D.state = 'play'; for (let i = 0; i < 40; i++) { D.endlessTick(1 / 30); D.geoTick(1 / 30); } D.MP.code = '9999'; D.set.geoNet = true;
          const o = {}, T = D.THREE, P = D.P, dt = 1 / 30;
          // two trunks 3–5 m apart near here
          const trunks = []; for (const L of D.obstacles.values()) for (const t of L) if (t.tr > .12 && Math.hypot(t.x - P.x, t.z - P.z) < 250) trunks.push(t);
          let pair = null; for (const a of trunks) { for (const c of trunks) { const d = Math.hypot(a.x - c.x, a.z - c.z) - a.tr - c.tr; if (a !== c && d > 3.4 && d < 4.6) { pair = [a, c]; break; } } if (pair) break; }
          o.pair = !!pair; if (!pair) return o; const [A, B] = pair;
          P.x = (A.x + B.x) / 2 + 1.5; P.z = (A.z + B.z) / 2; P.y = D.groundAt(P.x, P.z);
          const head = () => new T.Vector3(P.x, P.y + 1.6, P.z), I = { head: head(), headQ: new T.Quaternion(), hands: {} };
          const hand = pos => ({ pos: pos.clone(), rayPos: pos.clone(), rayQ: new T.Quaternion(), q: new T.Quaternion(), grip: 0, trig: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 });
          const M = hand(head()), O = hand(head().add(new T.Vector3(-.3, -.4, 0))); I.hands.right = M; I.hands.left = O; D.vr.I = I; D.vr.main = M; D.vr.headLocalY = 1.6;
          const tick = n => { for (let i = 0; i < n; i++) { D.geoGearTick(I, M, O, dt); D.update(dt); } };
          D.geoGearApply(40, true); D.geoHeld('tent'); o.name = D.GEO.held;
          const at = t => new T.Vector3(t.x + t.tr + .1, D.groundAt(t.x, t.z) + 1.2, t.z), press = () => { M.trig = 1; tick(1); M.trig = 0; tick(1); };
          M.pos.copy(head()); press(); o.notTree = !D.GEO.hmA;
          M.pos.copy(at(A)); press(); o.tied = !!D.GEO.hmA; o.glow = (D.GEO.hmGlow || []).length;   // 2.90: the trees that fit glow; the same tree again unties it
          M.pos.copy(at(A)); press(); o.untied = !D.GEO.hmA && !(D.GEO.hmGlow || []).length; M.pos.copy(at(A)); press(); M.pos.copy(at(B)); press(); o.hung = !!D.GEO.hm && !(D.GEO.hmGlow || []).length;
          // daytime: no sleep; night: in you go
          D.glabTime(12); D.globeTick(0); M.pos.copy(D.GEO.hm.mid); press(); o.day = !D.GEO.sleep;
          D.glabTime(23); D.globeTick(0); D.geoHeld(null); M.pos.copy(D.GEO.hm.mid); press(); o.slept = !!D.GEO.sleep;
          const st = []; for (let i = 0; i < 30 * 9; i++) { tick(1); const s = D.GEO.sleep && D.GEO.sleep.st; if (s && st[st.length - 1] !== s) st.push(s); }
          o.phases = st.join(','); const S = D.GEO.sleep, body = [P.x, P.z]; o.lifted = S && S.view ? +(S.view.y - S.body.y).toFixed(1) : null; o.ghostK = +(D.GEO.ghostK || 0).toFixed(2); o.dream = [+D.HFOG.uDream.value.x.toFixed(2), (D.GEO.wisps || []).length]; o.beacon = !!(D.GEO.beacon && D.GEO.beacon.visible) || !D.GEO.target;   // 2.88: the dream sight on, wisps about
          // fly 3 s forward, then far: the body stays; the tether holds
          D.input.jy = 1; D.input.jx = 0; const v0 = [S.view.x, S.view.z]; for (let i = 0; i < 90; i++) D.update(dt); o.flew = Math.round(Math.hypot(S.view.x - v0[0], S.view.z - v0[1])); o.bodyStill = Math.hypot(P.x - body[0], P.z - body[1]) < .01;
          const bs0 = D.glToSphere(P.x, P.z, [0, 0, 0]); M.sy = -1; for (let i = 0; i < 30 * 20; i++) { D.update(dt); D.endlessTick(dt); } M.sy = 0; for (let i = 0; i < 30 * 40; i++) { D.update(dt); D.endlessTick(dt); }
          o.far = [Math.round(D.glArc(D.glToSphere(S.view.x, S.view.z, [0, 0, 0]), bs0) * D.GLOBE.R), D.GLOBE.reN > 0, Math.round(D.glArc(D.glToSphere(P.x, P.z, [0, 0, 0]), bs0) * D.GLOBE.R * 100) / 100]; D.input.jy = 0;
          o.orb = (() => { const L = { id: 'x', open: true, gh: [S.view.x, S.view.y + 1.6, S.view.z - 20], ghT: performance.now(), links: 0 }; D.MP.links.set('x', L); D.geoOrbTick(dt); const r = !!L.orb; D.MP.links.delete('x'); if (L.orb) D.scene.remove(L.orb.g); return r; })();
          // back from far away: B, and you're by the hammock again, the ground round you rebuilt
          M.b = 1; tick(1); M.b = 0; for (let i = 0; i < 40; i++) tick(1); o.farWake = [!D.GEO.sleep, Math.round(Math.hypot(P.x - D.GEO.hm.mid.x, P.z - D.GEO.hm.mid.z) * 10) / 10, Math.round(D.glArc(D.glToSphere(P.x, P.z, [0, 0, 0]), bs0) * D.GLOBE.R)];
          M.pos.copy(D.GEO.hm.mid); press(); tick(5); o.once = !D.GEO.sleep;   // 2.92: once a night
          D.GEO.sleptNight = false; press(); for (let i = 0; i < 30 * 9; i++) tick(1); const S2 = D.GEO.sleep; o.again = S2 && S2.st;
          o.netBody = (() => { const sb = D.sleepBody(); return Math.round(Math.hypot(sb.h[0] - D.GEO.hm.mid.x, sb.h[2] - D.GEO.hm.mid.z) * 10) / 10; })();
          // a bear comes for the body: a warning, then you're snapped back, standing by the hammock
          const S3 = D.GEO.sleep; S3.view.x = S3.body.x; S3.view.z = S3.body.z; const bear = D.addGround('bear', S3.body.x + 30, S3.body.z), _x = 0; D.predGo(bear, 'charge');
          const st2 = []; for (let i = 0; i < 30 * 4; i++) { tick(1); const s = D.GEO.sleep && D.GEO.sleep.st; if (s && st2[st2.length - 1] !== s) st2.push(s); }
          o.danger = [st2.join(','), !D.GEO.sleep, Math.round(Math.hypot(P.x - D.GEO.hm.mid.x, P.z - D.GEO.hm.mid.z) * 10) / 10]; bear.gone = true; bear.x += 9000; D.predCalm(bear, 99);
          // B: wake up any time
          D.GEO.sleptNight = false; M.pos.copy(D.GEO.hm.mid); press(); for (let i = 0; i < 30 * 2; i++) tick(1); const was = D.GEO.sleep && D.GEO.sleep.st; M.b = 1; tick(1); M.b = 0; for (let i = 0; i < 40; i++) tick(1); o.bWake = [was, !D.GEO.sleep]; for (let i = 0; i < 60; i++) tick(1); o.dreamOff = [+D.HFOG.uDream.value.x.toFixed(2), (D.GEO.wisps || []).length];
          // 2.91: wake yourself in the night: rested (full health); dream into the day: cut off, half health
          D.MP.hp = 60; D.glabTime(23); D.globeTick(0); D.GEO.sleptNight = false; M.pos.copy(D.GEO.hm.mid); press(); for (let i = 0; i < 30 * 9; i++) tick(1); M.b = 1; tick(1); M.b = 0; for (let i = 0; i < 40; i++) tick(1); o.rested = Math.round(D.MP.hp);
          D.glabTime(23); D.globeTick(0); D.GEO.sleptNight = false; M.pos.copy(D.GEO.hm.mid); press(); for (let i = 0; i < 30 * 9; i++) tick(1); D.glabTime(12); D.globeTick(0); for (let i = 0; i < 60; i++) tick(1); o.morning = [!D.GEO.sleep, Math.round(D.MP.hp)];
          return o; }""")
        print(json.dumps(r))
        ok = r.get("pair") and r["notTree"] and r["tied"] and r["hung"] and r["day"] and r["slept"] and r["phases"].startswith("settle,blink,dark,rise,ghost") and r["lifted"] >= 3 and r["ghostK"] > .9 \
             and 80 < r["flew"] < 110 and r["bodyStill"] and r["far"][0] > 1500 and r["far"][1] and r["far"][2] < .5 and r["orb"] and r["farWake"][0] and r["farWake"][1] < 2.5 and r["farWake"][2] < 10 and r["once"] and r["again"] == "ghost" and r["netBody"] < .1 and "warn" in r["danger"][0] and r["danger"][1] and r["danger"][2] < 2.5 and r["bWake"][1] and r["glow"] > 0 and r["untied"] and r["beacon"] and r["dream"][0] > .9 and r["dream"][1] > 5 and r["dreamOff"][0] < .05 and r["dreamOff"][1] == 0 and r["rested"] == 100 and r["morning"][0] and r["morning"][1] <= 50
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
