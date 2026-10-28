"""2.48: bots (VR PvP), the way they're used. Solo: the map settings offer PvP; the Bots panel sets the game size (bots fill it) and the skill
and shows each bot (name, look, style, stars, traits); Play starts the round clock and the bots spawn apart from you. Over a couple of minutes
they move about, pick up guns and crosses, see and hear each other, fight and take each other down and come back. One that hears you turns,
spots you and shoots you (real bullets, its kill on the board); you shoot one down (your kill), it comes back away from you with its guns;
your grenade hurts them. The round ends with them on the board. Online: the host's bots fill the room (a bot leaves when a friend joins,
and comes back when they leave); the friend sees them in the lobby and in the game where the host has them; the friend's bullets take a
bot down (the friend's kill); a bot's bullet hurts the friend, and a bot that takes the friend down gets the kill.
Served over http (the people and the pack guns load); local PeerJS server on :9000 (run_all's ONLINE set).
Usage: python3 dev/test_248.py dbg.html [outdir]"""
import os, sys, asyncio, json, threading, shutil, tempfile, base64
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.async_api import async_playwright
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
srvdir = tempfile.mkdtemp(); shutil.copy(sys.argv[1], os.path.join(srvdir, "dbg.html")); os.symlink(os.path.join(REPO, "models"), os.path.join(srvdir, "models"))
OUT = sys.argv[2] if len(sys.argv) > 2 else None
if OUT and OUT.endswith(".png"): OUT = os.path.dirname(OUT)
PORT = 8799
class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=srvdir, **k)
    def log_message(self, *a): pass
srv = ThreadingHTTPServer(("127.0.0.1", PORT), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
SETUP = open(os.path.join(HERE, "test_mp.py")).read().split('SETUP = """', 1)[1].split('"""', 1)[0]
MORE = """() => { D.setVRON(true); D.vr.on = true; try { localStorage.setItem('jt-age', 'ok'); } catch (_) {} D.VRUI.rulesOk = true;
  window.W = (p, l) => D.VRUI.panels[p].widgets.find(w => !(w.hide && w.hide()) && !w.ghost && (w.label === l || (w.labelFn && w.labelFn() === l)));
  window.SL = p => D.VRUI.panels[p].widgets.filter(w => w.kind === 'slider' && !(w.hide && w.hide()));
  window.tick = n => { for (let i = 0; i < n; i++) D.vruiTick(1 / 30); return 1; };
  window.bg = setInterval(() => { if (window.noBg) return; try { D.mpTick(1 / 30); } catch (e) { setTimeout(() => { throw e; }); } }, 33);
  window.play = (n, dt = 1 / 30) => { const V = D.vr; for (let i = 0; i < n; i++) { D.vrTick(dt); if (!V.climbing) D.update(dt); D.vrAfterMove(dt); D.mpTick(dt); D.updateGun(dt); const t0 = performance.now(); D.vbTick(dt); window.vbMs = (window.vbMs || 0) + performance.now() - t0; window.vbN = (window.vbN || 0) + 1; } return 1; };
  window.pic = (w, h) => { const r = D.renderer; return D.VRUI.panels[w].cv.toDataURL('image/jpeg', .85); };
  window.look = (eye, at, fov, w, h) => { const c = D.camera, r = D.renderer; r.setSize(w, h); c.fov = fov; c.aspect = w / h; c.updateProjectionMatrix();
    c.position.set(...eye); c.lookAt(...at); c.updateMatrixWorld(); D.cullTiles(); r.render(D.scene, c); return r.domElement.toDataURL('image/jpeg', .86); };
  window.clearPath = (x, z, x2, z2) => D.losClear(x, D.H(x, z) + 1.6, z, x2, D.H(x2, z2) + 1.6, z2) && D.losClear(x, D.H(x, z) + 1.7, z, x2, D.H(x2, z2) + .9, z2);
  window.near = (x0, z0, r) => { for (let k = 0; k < 600; k++) { const a = Math.random() * 6.283, x = x0 + Math.cos(a) * r, z = z0 + Math.sin(a) * r; if (D.okSpot(x, z) && clearPath(x, z, x0, z0)) return [x, z]; } return null; };
  window.freeze = B => { B.thinkT = 1e9; B.mv = { x: B.x, z: B.z, spd: 0, crouch: 0 }; B.cool = 1e9; B.vx = B.vz = 0; };
  return 1; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--disable-features=WebRtcHideLocalIpsWithMdns"])
        errs = []
        async def page(nm, vw=400, vh=300):
            pg = await (await b.new_context(viewport={"width": vw, "height": vh})).new_page(); pg.on("pageerror", lambda e: errs.append(nm + " PE " + str(e)))
            await pg.goto(f"http://127.0.0.1:{PORT}/dbg.html", timeout=120000); await pg.wait_for_timeout(600)
            await pg.evaluate(SETUP, nm); await pg.evaluate(MORE); return pg
        async def until(pg, js, secs, step=150):
            for _ in range(int(secs * 1000 / step)):
                if await pg.evaluate(js): return True
                await pg.wait_for_timeout(step)
            return False
        def save(nm, url):
            if OUT: open(os.path.join(OUT, nm), "wb").write(base64.b64decode(url.split(",")[1]))
        out = {}
        # ================= solo =================
        A = await page("solo")
        await A.evaluate("() => { D.set.size = 'medium'; D.vruiOpen('mode'); W('mode', 'Solo').on(); W('setup', 'Bot battle').on(); return 1; }")
        out["auto"] = await A.evaluate("() => { const r = []; for (const sz of ['small', 'xl', 'xxxl', 'medium']) { D.set.size = sz; D.vbFit(); r.push(D.VB.list.length); } return r; }")   # 2.49: Auto: more bots on bigger maps
        out["solo"] = await A.evaluate("() => [D.VRUI.stage, D.gameMode, !!W('setup', 'Bots · 5'), !!W('setup', '2 Teams'), SL('setup').length, !!W('setup', 'Hike')]")
        await A.evaluate("() => { W('setup', 'Bots · 5').on(); W('bots', 'Normal').on(); return 1; }")
        out["panel"] = await A.evaluate("() => [D.VRUI.stage, Object.keys(D.VRUI.panels).filter(k => D.VRUI.panels[k].mesh.visible).sort().join(','), D.VB.list.length, new Set(D.VB.list.map(B => B.style)).size, D.VB.list.every(B => B.stars === 3 && B.T && B.name)]")
        await A.evaluate("() => { SL('bots')[0].set(7); return 1; }")
        out["size7"] = await A.evaluate("() => [D.VB.list.length, W('bots', 'Done') ? 1 : 0]")
        await until(A, "() => D.VB.list.every(B => D.charPortrait(B.lk, 'green')) || D.CHAR.failed > 0", 120)
        if OUT: save("t248_bots_panel.jpg", await A.evaluate("() => { D.uiDraw(D.VRUI.panels.bots); return pic('bots'); }"))
        await A.evaluate("() => { SL('bots')[0].set(6); W('bots', 'Done').on(); return 1; }")
        out["back"] = await A.evaluate("() => [D.VRUI.stage, D.VB.list.length, W('setup', 'Bots · 5') ? 1 : 0]")
        # the round: the map, then Play (the flow vruiDropIn takes from the little map)
        await A.evaluate("""() => { window.noBg = true; D.setSeed(4242); Object.assign(D.set, { size: 'medium', zone: 'off', capture: 'off', teams: 'solo', hour: 13, weather: 'clear' }); D.generate();
          placeAt(D.P.x, D.P.z); D.VRUI.stage = 'preview'; D.vruiDropIn(); const f = D.VRUI.fadeGo; D.VRUI.fadeGo = null; if (f) f(); window.startPistols = D.VB.list.every(B => JSON.stringify(B.own) === '{"pistol":1}'); play(3); return 1; }""")
        out["round"] = await A.evaluate("""() => { const me = [D.P.x, D.P.z]; return [D.state, Math.round(D.MP.roundLeft), D.VB.list.length, D.VB.list.filter(B => B.S && B.alive).length,
          Math.round(Math.min(...D.VB.list.map(B => Math.hypot(B.x - me[0], B.z - me[1])))), window.startPistols]; }""")
        # two minutes of play: they get about, gear up, notice each other, fight, go down and come back
        r = await A.evaluate("""() => { window.vbMs = 0; window.vbN = 0; const L0 = D.VB.list, last = L0.map(B => [B.x, B.z]), dist = L0.map(() => 0), goals = {}, seen = new Set(); let shots = 0, t0 = performance.now(), deaths = 0;
          const was = L0.map(B => B.alive);
          for (let s = 0; s < 240; s++) { play(15);
            L0.forEach((B, i) => { if (B.alive && was[i]) dist[i] += Math.hypot(B.x - last[i][0], B.z - last[i][1]); last[i] = [B.x, B.z]; if (was[i] && !B.alive) deaths++; was[i] = B.alive; goals[B.goal] = (goals[B.goal] || 0) + 1; });
            for (const t of D.tracers) if (t.bot && !seen.has(t)) { seen.add(t); shots++; } }
          const ms = (performance.now() - t0) / (240 * 15);
          return { dist: dist.map(Math.round), goals, shots, deaths, kills: L0.reduce((s, B) => s + B.k, 0), guns: L0.map(B => Object.keys(B.own).length), people: L0.map(B => !!B.C && !!B.hold && B.hold.children.length > 0),
            msFrame: +ms.toFixed(2), botsMs: +(window.vbMs / window.vbN).toFixed(2), myHp: D.MP.hp, mem: L0.map(B => B.mem ? B.mem.size : 0), styles: L0.map(B => B.style), stucks: L0.map(B => B.stucks || 0) }; }""")
        out["minutes"] = r
        # one hears you, spots you and shoots you
        out["meet"] = await A.evaluate("""() => { let spot = null; const B = D.VB.list[0];
          for (let k = 0; k < 800 && !spot; k++) { const x = (Math.random() * 2 - 1) * 200, z = (Math.random() * 2 - 1) * 200; if (D.okSpot(x, z) && D.okSpot(x + 32, z) && clearPath(x, z, x + 32, z) && clearPath(x, z, x + 26, z)) spot = [x, z]; }
          if (!spot) return null;
          for (const O of D.VB.list) if (O !== B) { freeze(O); O.x += 500; O.z += 500; O.S.x = O.x; O.S.z = O.z; O.alive = false; O.deadT = -1e9; }
          placeAt(spot[0], spot[1]); play(1); D.MP.dead = 0; D.MP.hp = 100; D.MP.sh = 0; B.alive = true; B.hp = 100; B.x = spot[0] + 32; B.z = spot[1]; B.y = D.groundAt(B.x, B.z); B.vx = B.vz = 0; B.own.ar = 2; B.gun = 'ar'; B.mag.ar = 30; B.reloadT = 0; B.mem = new Map(); B.thinkT = 0; B.cool = 0;
          D.vbHeard(D.vr.readInputs().head, 'pistol', D.MP.code ? D.mpMyId() : ''); let first = null; const k0 = B.k;
          for (let i = 0; i < 450; i++) { play(1); if (first === null && D.MP.hp < 100) first = +(i / 30).toFixed(2); if (D.MP.dead > 0) break; }
          return { firstHit: first, hp: D.MP.hp, dead: D.MP.dead > 0, by: D.MP.lastHitBy, botK: B.k - k0, goal: B.goal }; }""")
        play_back = await A.evaluate("() => { play(150); return [D.MP.dead > 0, D.MP.hp, D.MP.deaths]; }")
        out["meet"]["back"] = play_back
        # you shoot it down; it comes back away from you with its guns; your grenade
        out["shoot"] = await A.evaluate("""() => { const T = D.THREE, B = D.VB.list[0], h = D.vr.readInputs().head, sp = near(D.P.x, D.P.z, 14); if (!sp) return null;
          B.x = sp[0]; B.z = sp[1]; B.y = D.groundAt(B.x, B.z); freeze(B); play(1); const k0 = D.MP.kills, hp0 = B.hp + B.sh; let n = 0;
          while (B.alive && n < 8) { const h2 = D.vr.readInputs().head, d = new T.Vector3(B.x - h2.x, B.y + 1.15 - h2.y, B.z - h2.z).normalize(); D.makeBullet(h2.clone(), d.multiplyScalar(715), { reach: 900, dmg: 45, gun: 'ar' }); play(3); n++; }
          const res = { shots: n, down: !B.alive, myKills: D.MP.kills - k0, deaths: B.d, banner: 0 };
          B.thinkT = 0; B.cool = 0; play(Math.round(4.6 * 30)); res.back = [B.alive, B.hp, Math.round(Math.hypot(B.x - D.P.x, B.z - D.P.z)), B.own.ar || 0];
          const C = D.VB.list[1]; C.alive = true; D.vbJoin(C, false); freeze(C); const e = C.hp + C.sh; D.nadeBoom(new T.Vector3(C.x + 2, C.y, C.z), false); res.nade = [e, C.hp + C.sh];
          return res; }""")
        # pictures: three bots close by, one aiming at you, one running, one crouched
        if OUT:
            save("t248_bots_near.jpg", await A.evaluate("""() => { const P = D.P, gy = D.groundAt; const L = D.VB.list.slice(1, 5); const at = [[-3, -7], [0, -5.5], [3, -8], [5.5, -10.5]];
              const open = (x, z, r) => { for (let i = -2; i <= 2; i++) for (let j = -2; j <= 2; j++) { const l = D.obstacles.get((Math.floor(x / 8) + i) + ',' + (Math.floor(z / 8) + j)); if (l) for (const o of l) if (Math.hypot(o.x - x, o.z - z) < r) return false; } return true; };
              let sp = null; for (let k = 0; k < 4000 && !sp; k++) { const x = (Math.random() * 2 - 1) * 220, z = (Math.random() * 2 - 1) * 220; if (D.okSpot(x, z) && D.okSpot(x, z - 8) && open(x, z - 5, 11) && Math.abs(D.H(x, z) - D.H(x, z - 10)) < 1.2) sp = [x, z]; }
              if (sp) { placeAt(sp[0], sp[1]); play(1); }
              L.forEach((B, i) => { B.alive = true; B.deadT = 0; freeze(B); B.x = P.x + at[i][0]; B.z = P.z + at[i][1]; B.y = gy(B.x, B.z); B.S.x = B.x; B.S.y = B.y; B.S.z = B.z;
                B.own[['ar', 'smg', 'hunt', 'pistol'][i]] = 3; B.gun = ['ar', 'smg', 'hunt', 'pistol'][i]; B.lookT = 1e9; B.foe = null; B.alert = 0; });
              for (let k = 0; k < 40; k++) { L.forEach((B, i) => { B.S.yaw = Math.atan2(-(P.x - B.x), -(P.z - B.z)); B.S.aimWant = i !== 1 ? 1 : 0; B.S.aim = .05; B.S.crouchWant = i === 2 ? 1 : 0;
                if (i === 1) { B.vx = 6.5; B.vz = 0; } else { B.vx = B.vz = 0; } B.mv = { x: B.x + B.vx, z: B.z, spd: Math.hypot(B.vx, B.vz), crouch: B.S.crouchWant }; }); play(1); L[1].x = P.x; L[1].z = P.z - 6.5; }
              const V = D.vr, hs = D.vrHandsObj, hide = [V.meC && V.meC.top, V.avatar && V.avatar.group, D.VHUD.m, ...Object.values(V.guns || {}), hs && hs.L.g, hs && hs.R.g].filter(Boolean); for (const o of hide) o.visible = false;
              const y = gy(P.x, P.z) + 1.7; const u = look([P.x - 1, y, P.z + 1.5], [P.x + 1, y - .7, P.z - 7], 55, 1400, 800); return u; }"""))
        # the round ends: the board has them
        out["over"] = await A.evaluate("() => { D.MP.roundLeft = .02; play(2); return [D.state, D.VRUI.stage, (D.MP.board || []).length, (D.MP.board || []).filter(r => r.bot).length]; }")
        if OUT: save("t248_board.jpg", await A.evaluate("() => { D.uiDraw(D.VRUI.panels.over); return pic('over'); }"))
        await A.close()
        # ================= online =================
        H1 = await page("host")
        await H1.evaluate("() => { D.MP.tag = 'HOSTY'; D.set.botFill = 4; D.set.botSkill = 'normal'; D.vruiOpen('mode'); W('mode', 'Online').on(); W('mp', 'Host a room').on(); return 1; }")
        await until(H1, "() => /Waiting/.test(D.MP.status)", 15); code = await H1.evaluate("() => D.MP.code")
        await H1.evaluate("() => { W('setup', 'Deathmatch').on(); return 1; }")
        out["hostAlone"] = await until(H1, "() => D.VB.list.length === 3", 10)
        G = await page("guest")
        await G.evaluate("() => { D.MP.tag = 'FRIEND'; D.vruiOpen('mode'); W('mode', 'Online').on(); W('mp', 'Join a room').on(); return 1; }")
        await G.evaluate(f"() => {{ for (const k of '{code}') W('rooms', k).on(); W('rooms', 'Join').on(); return 1; }}")
        out["connected"] = await until(H1, "() => D.mpOpen().length === 1", 25) and await until(G, "() => D.mpOpen().length === 1 && D.MP.on", 15)
        out["roomBots"] = [await until(H1, "() => D.VB.list.length === 2", 10), await until(G, "() => D.VB.list.length === 2", 10)]
        hn = await H1.evaluate("() => D.VB.list.map(B => B.name).join(',')"); gn = await G.evaluate("() => D.VB.list.map(B => B.name).join(',')")
        out["sameBots"] = hn == gn and len(hn) > 0
        out["lobby"] = await G.evaluate("() => { D.vruiOpen('lobby'); const R = D.mpRoster(); return [R.length, R.filter(r => r.bot).length]; }")
        if OUT:
            await until(G, "() => D.VB.list.every(B => D.charPortrait(B.lk, 'green')) || D.CHAR.failed > 0", 60)
            save("t248_lobby.jpg", await G.evaluate("() => { D.uiDraw(D.VRUI.panels.lobby); return pic('lobby'); }"))
        await H1.evaluate("() => { D.setSeed(4242); W('setup', 'Start').on(); return 1; }")
        out["preview"] = await until(H1, "() => { D.vruiTick(1 / 60); return D.VRUI.stage === 'preview'; }", 60) and await until(G, "() => { D.vruiTick(1 / 60); return D.VRUI.stage === 'preview'; }", 60)
        await H1.evaluate("() => { W('preview', 'Play this map').on(); return 1; }")
        go = "() => { D.vruiTick(1 / 60); if (D.VRUI.fadeGo) { const f = D.VRUI.fadeGo; D.VRUI.fadeGo = null; f(); } return D.state === 'play'; }"
        out["playing"] = await until(H1, go, 20) and await until(G, go, 20)
        await H1.evaluate("() => { window.noBg = true; placeAt(D.P.x, D.P.z); return 1; }"); await G.evaluate("() => { window.noBg = true; placeAt(D.P.x, D.P.z); return 1; }")
        for _ in range(30):
            await asyncio.gather(H1.evaluate("() => play(3)"), G.evaluate("() => play(3)")); await H1.wait_for_timeout(30)
        hb = await H1.evaluate("() => D.VB.list.map(B => [B.i, B.x, B.z, B.alive])"); gb = await G.evaluate("() => D.VB.list.map(B => [B.i, B.x, B.z, !!B.S])")
        out["puppets"] = [len(gb), all(g[3] for g in gb), round(max((abs(h[1] - g[1]) + abs(h[2] - g[2])) for h, g in zip(hb, gb)), 1)]
        # the friend shoots a bot down
        bi = hb[0][0]
        await H1.evaluate(f"() => {{ const B = D.VB.list.find(q => q.i === {bi}); freeze(B); B.lookT = 1e9; B.alive = true; return 1; }}")
        for _ in range(10):
            await asyncio.gather(H1.evaluate("() => play(2)"), G.evaluate("() => play(2)")); await H1.wait_for_timeout(30)
        sp = await G.evaluate(f"() => {{ const B = D.VB.list.find(q => q.i === {bi}); const s = near(B.x, B.z, 12); if (s) {{ placeAt(s[0], s[1]); play(1); }} return s; }}")
        k0 = await G.evaluate("() => D.MP.kills"); hp0 = await H1.evaluate(f"() => {{ const B = D.VB.list.find(q => q.i === {bi}); return B.hp + B.sh; }}")
        for _ in range(6):
            await G.evaluate(f"""() => {{ const T = D.THREE, B = D.VB.list.find(q => q.i === {bi}); if (!B.alive) return 0; const h = D.vr.readInputs().head, d = new T.Vector3(B.x - h.x, B.y + 1.15 - h.y, B.z - h.z).normalize();
              D.makeBullet(h.clone(), d.multiplyScalar(715), {{ reach: 900, dmg: 45, gun: 'ar', online: true }}); play(3); return 1; }}""")
            for _ in range(4):
                await asyncio.gather(H1.evaluate("() => play(1)"), G.evaluate("() => play(1)")); await H1.wait_for_timeout(40)
            if not await H1.evaluate(f"() => D.VB.list.find(q => q.i === {bi}).alive"): break
        await until(G, f"() => {{ play(1); return D.MP.kills > {k0}; }}", 5)
        out["friendShot"] = [bool(sp), hp0, await H1.evaluate(f"() => {{ const B = D.VB.list.find(q => q.i === {bi}); return [B.alive, B.d]; }}"), await G.evaluate(f"() => [D.MP.kills - {k0}, D.VB.list.find(q => q.i === {bi}).alive]")]
        # a bot shoots the friend, then takes the friend down: the bot's kill
        bj = hb[1][0]
        hit = await H1.evaluate(f"""() => {{ const T = D.THREE, B = D.VB.list.find(q => q.i === {bj}), L = D.mpOpen()[0]; freeze(B); B.alive = true; const R = L.R; if (!R || !R.cur) return null;
          let n = 0; for (let k = 0; k < 3; k++) {{ const s = near(R.head.x, R.head.z, 15); if (!s) continue; n++; B.x = s[0]; B.z = s[1]; B.y = D.groundAt(B.x, B.z); play(1);   /* three tries from three spots, 10 each */
            const from = new T.Vector3(B.x, B.y + 1.5, B.z), d = new T.Vector3(R.head.x - from.x, R.head.y - .45 - from.y, R.head.z - from.z).normalize();
            D.makeBullet(from, d.multiplyScalar(715), {{ reach: 900, dmg: 10, gun: 'ar', bot: B }}); play(4); }} return n; }}""")
        await until(G, "() => { play(1); return D.MP.hp < 100; }", 5)
        out["botHitFriend"] = [hit, await G.evaluate(f"() => [D.MP.hp, D.MP.lastHitBy]")]
        await H1.evaluate(f"""() => {{ const T = D.THREE, B = D.VB.list.find(q => q.i === {bj}), R = D.mpOpen()[0].R; for (let k = 0; k < 4; k++) {{ const from = new T.Vector3(B.x, B.y + 1.5, B.z), d = new T.Vector3(R.head.x - from.x, R.head.y - .5 - from.y, R.head.z - from.z).normalize();
          D.makeBullet(from, d.multiplyScalar(715), {{ reach: 900, dmg: 120, gun: 'ar', bot: B }}); play(4); }} return 1; }}""")
        await until(G, "() => { play(1); return D.MP.dead > 0; }", 5)
        out["botKill"] = [await G.evaluate("() => D.MP.dead > 0"), await until(H1, f"() => {{ play(1); return D.VB.list.find(q => q.i === {bj}).k >= 1; }}", 5)]
        # the friend leaves: the bot comes back into the game
        await G.evaluate("() => { D.vruiOpen('mode'); return 1; }")
        out["afterLeave"] = await until(H1, "() => { window.noBg = false; return D.VB.list.length === 3 && D.VB.list.every(B => !!B.S); }", 25)
        print(json.dumps(out))
        m = out["minutes"]
        ok = (out["auto"] == [4, 11, 19, 5] and out["solo"][0] == "setup" and out["solo"][1] == "pvp" and out["solo"][2] and out["solo"][3] and out["solo"][4] >= 6 and out["solo"][5]
              and out["panel"][0] == "bots" and out["panel"][1] == "bots,me" and out["panel"][2] == 5 and out["panel"][3] >= 4 and out["panel"][4] and out["size7"][0] == 6
              and out["back"] == ["setup", 5, 1]
              and out["round"][0] == "play" and out["round"][1] > 590 and out["round"][2] == 5 and out["round"][3] == 5 and out["round"][4] > 40 and out["round"][5]
              and min(m["dist"]) > 120 and len(m["goals"]) >= 4 and m["shots"] >= 20 and sum(m["guns"]) >= 10 and all(m["people"]) and m["kills"] + m["deaths"] >= 1
              and out["meet"] and out["meet"]["firstHit"] is not None and out["meet"]["by"] == "b:0" and (not out["meet"]["dead"] or out["meet"]["botK"] == 1) and out["meet"]["back"][1] == 100
              and out["shoot"] and out["shoot"]["down"] and out["shoot"]["myKills"] == 1 and out["shoot"]["back"][0] and out["shoot"]["back"][1] == 100 and out["shoot"]["back"][2] > 40 and out["shoot"]["back"][3] == 2
              and out["shoot"]["nade"][1] < out["shoot"]["nade"][0]
              and out["over"][1] == "over" and out["over"][2] == 6 and out["over"][3] == 5
              and out["hostAlone"] and out["connected"] and out["roomBots"] == [True, True] and out["sameBots"] and out["lobby"] == [4, 2] and out["preview"] and out["playing"]
              and out["puppets"][0] == 2 and out["puppets"][1] and out["puppets"][2] < 8
              and out["friendShot"][0] and out["friendShot"][2][0] is False and out["friendShot"][2][1] >= 1 and out["friendShot"][3] == [1, False]
              and out["botHitFriend"][0] >= 1 and out["botHitFriend"][1][0] < 100 and out["botHitFriend"][1][1] == "b:" + str(bj) and out["botKill"] == [True, True] and out["afterLeave"] and not errs)
        print("errors:", errs[:5] or ("none" if ok else "CHECKS FAILED")); await b.close(); return ok
try: res = asyncio.run(main())
finally: srv.shutdown()
sys.exit(0 if res else 1)
