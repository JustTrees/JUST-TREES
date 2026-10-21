"""2.38: the menus, rethought, and the Character screen (VR). Main menu: Solo · Online · Your character. Solo shows your character (turning)
beside the map settings; online, Host goes straight into the lobby, Join shows the open rooms (one line each) and a code pad; the lobby has a
picture card for everyone, your own card opens the character editor, your settings sit under the cards, the map settings beside it. Online
with others, the in-game menu doesn't stop the game; Set height works from it and comes back to it. Writes pictures to the folder given second.
Usage: python3 dev/test_238.py dbg.html [outdir]   (served over http, like test_237)"""
import os, sys, asyncio, json, subprocess, time, shutil, tempfile, base64
from playwright.async_api import async_playwright
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
srvdir = tempfile.mkdtemp(); shutil.copy(sys.argv[1], os.path.join(srvdir, "dbg.html")); os.symlink(os.path.join(REPO, "models"), os.path.join(srvdir, "models"))
OUT = sys.argv[2] if len(sys.argv) > 2 else None
if OUT and OUT.endswith(".png"): OUT = os.path.dirname(OUT)
PORT = 8784
srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=srvdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2)
SETUP = """() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setVR(true); D.vr.on = true; D.setVRON(true);
  for (const el of document.body.children) if (el.tagName !== 'CANVAS') el.style.display = 'none';
  try { localStorage.setItem('jt-age', 'ok'); } catch (_) {} D.VRUI.rulesOk = true;
  const T = D.THREE; window.T = T;
  // a camera standing where you stand in the menus, looking at yaw a (degrees, + is left), wide
  window.snap = (a, fov, asp) => { const c = D.camera, r = D.renderer; r.setSize(Math.round(560 * asp), 560); c.fov = fov; c.aspect = asp; c.updateProjectionMatrix();
    c.position.set(0, 1.45, 0).add(D.VRUI.root.position); c.quaternion.setFromAxisAngle(new T.Vector3(0, 1, 0), a * Math.PI / 180 + D.VRUI.root.rotation.y); c.updateMatrixWorld();
    D.GRADE && 0; r.render(D.scene, c); return r.domElement.toDataURL('image/jpeg', .86); };
  window.panel = n => D.VRUI.panels[n].cv.toDataURL('image/jpeg', .86);
  window.W = (p, l) => D.VRUI.panels[p].widgets.find(w => w.label === l);
  window.vis = () => Object.keys(D.VRUI.panels).filter(k => D.VRUI.panels[k].mesh.visible).join(',');
  return 1; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 1240, "height": 560})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(f"http://127.0.0.1:{PORT}/dbg.html", timeout=120000); await pg.wait_for_timeout(800)
        await pg.evaluate(SETUP); imgs = {}; out = {}
        out["mode"] = await pg.evaluate("() => { D.vruiOpen('mode'); return { stage: D.VRUI.stage, vis: vis(), labels: D.VRUI.panels.mode.widgets.map(w => w.label) }; }")
        imgs["menu"] = await pg.evaluate("() => panel('mode')")
        # Solo: your character beside the map settings
        out["solo"] = await pg.evaluate("() => { W('mode', 'Solo').on(); return { stage: D.VRUI.stage, vis: vis() }; }")
        await pg.wait_for_function("() => { D.chpTick(1 / 30); return !!D.CHP.C || D.CHAR.failed > 0; }", timeout=120000)
        out["soloView"] = await pg.evaluate("() => { for (let i = 0; i < 20; i++) D.chpTick(1 / 30); return D.VRUI.panels.me.view.visible; }")
        imgs["solo"] = await pg.evaluate("() => snap(12, 100, 2.2)")
        imgs["solo_left"] = await pg.evaluate("() => panel('me')"); imgs["solo_right"] = await pg.evaluate("() => panel('setup')")
        # change the look: Woman, Ranger, hair 'Buns'
        out["look"] = await pg.evaluate("""() => { const before = D.lookStr(D.look); W('me', 'Woman').on(); W('me', 'Ranger').on(); const h = D.VRUI.panels.me.widgets.find(w => w.labelFn && w.labelFn() === 'Buns'); h.on();
          return { before, after: D.lookStr(D.look), saved: localStorage.getItem('jt-look'), beardHidden: W('me', 'Beard').hide() }; }""")
        await pg.wait_for_function("() => { D.chpTick(1 / 30); return D.CHP.key.startsWith(D.lookStr(D.look)); }", timeout=60000)
        imgs["solo2"] = await pg.evaluate("() => { for (let i = 0; i < 25; i++) D.chpTick(1 / 30); D.uiDraw(D.VRUI.panels.me); return snap(40, 70, 1.3); }")
        # the Character screen on its own, from the main menu
        out["char"] = await pg.evaluate("() => { D.vruiOpen('mode'); W('mode', 'Your character').on(); for (let i = 0; i < 5; i++) D.chpTick(1 / 30); const r = { stage: D.VRUI.stage, vis: vis(), view: D.VRUI.panels.char.view.visible }; W('char', 'Done').on(); r.back = D.VRUI.stage; return r; }")
        # Online: Host a room / Join a room
        out["online"] = await pg.evaluate("() => { W('mode', 'Online').on(); return { stage: D.VRUI.stage, labels: D.VRUI.panels.mp.widgets.filter(w => !(w.hide && w.hide())).map(w => w.label) }; }")
        imgs["online"] = await pg.evaluate("() => panel('mp')")
        out["rooms"] = await pg.evaluate("""() => { W('mp', 'Join a room').on(); D.MP.rooms = [{ code: '4821', host: 'HOSTY', col: 0, mode: 'pvp', teams: true, n: 3, map: 'M', st: 'lobby' }, { code: '5310', host: 'TREEFROG', col: 2, mode: 'hunt', dino: true, n: 1, map: 'Endless', st: 'play' }, { code: '7702', host: 'MOSSY', col: 3, mode: 'hike', n: 5, map: 'Island', st: 'lobby' }];
          D.MP.roomsT = 99; ['7', '7', '0'].forEach(k => W('rooms', k).on()); D.uiDraw(D.VRUI.panels.rooms); return { stage: D.VRUI.stage, entry: D.MP.entry, joinOff: W('rooms', 'Join').disabled() }; }""")
        imgs["rooms"] = await pg.evaluate("() => panel('rooms')")
        # in a room (as the host, with three friends): the lobby beside the map settings
        out["lobby"] = await pg.evaluate("""() => { W('rooms', 'Back').on(); const MP = D.MP; MP.host = true; MP.code = '4821'; MP.on = true; MP.tag = 'HOSTY'; D.setMode('pvp'); D.set.teams = 'teams';
          const looks = ['0.0.1.0.0.1', '1.1.2.1.2.0', '0.2.3.2.1.0'], tags = ['TREEFROG', 'MOSSYBACK', 'SAPLING'];
          looks.forEach((lk, i) => MP.links.set('p' + i, { id: 'p' + i, open: true, bad: false, tag: tags[i], idx: i + 1, col: i, rx: [], look: D.lookParse(lk) }));
          MP.board = [{ id: 'p0', k: 4, d: 2, team: 1 }, { id: D.mpMyId(), k: 6, d: 1, team: 0 }]; MP.boardMode = 'pvp'; MP.boardTeams = true;
          D.vruiOpen('setup'); return { stage: D.VRUI.stage, vis: vis(), roster: D.mpRoster().length }; }""")
        await pg.wait_for_function("() => { D.uiDraw(D.VRUI.panels.lobby); return D.mpOpen().every(L => D.CHP.cache.has(D.lookStr(L.look) + '|' + ['brown','green','grey','snow','black'][L.col])) || D.CHAR.failed > 0; }", timeout=120000)
        out["portraits"] = await pg.evaluate("() => D.CHP.cache.size")
        imgs["lobby"] = await pg.evaluate("() => { D.uiDraw(D.VRUI.panels.lobby); D.uiDraw(D.VRUI.panels.setup); return snap(12, 100, 2.2); }")
        imgs["lobby_left"] = await pg.evaluate("() => panel('lobby')"); imgs["lobby_right"] = await pg.evaluate("() => panel('setup')")
        out["edit"] = await pg.evaluate("""() => { const card = D.VRUI.panels.lobby.widgets.find(w => w.w === 233 && !(w.hide && w.hide())); card.on(); for (let i = 0; i < 5; i++) D.chpTick(1 / 30);
          const r = { vis: vis(), view: D.VRUI.panels.me.view.visible, done: !W('me', 'Done').hide(), mainHidden: W('me', 'Main menu').hide() }; return r; }""")
        imgs["lobby_edit"] = await pg.evaluate("() => snap(12, 100, 2.2)")
        out["edit2"] = await pg.evaluate("() => { W('me', 'Done').on(); return vis(); }")
        # a guest sees the map settings locked, and no Start
        out["guest"] = await pg.evaluate("() => { D.MP.host = false; D.uiDraw(D.VRUI.panels.setup); const P = D.VRUI.panels.setup; const r = { startHidden: W('setup', 'Start').hide(), latLocked: D.mpLocked(P, P.widgets.find(w => w.kind === 'slider')), cardFree: !D.mpLocked(D.VRUI.panels.lobby, D.VRUI.panels.lobby.widgets.find(w => w.w === 233 && !(w.hide && w.hide()))) }; return r; }")
        imgs["guest_right"] = await pg.evaluate("() => panel('setup')")
        # in a game, online with others: the menu doesn't stop the game; Set height comes back to it
        out["pause"] = await pg.evaluate("""() => { D.MP.host = true; D.generate(); D.state = 'play'; D.vruiOpen('pause'); const P = D.VRUI.panels.pause;
          const shown = P.widgets.filter(w => !(w.hide && w.hide())).map(w => w.labelFn ? w.labelFn() : w.label);
          const r = { state: D.state, shown, ys: P.widgets.filter(w => !(w.hide && w.hide())).map(w => w.y) };
          W('pause', 'Set height').on(); r.h = { stage: D.VRUI.stage, state: D.state, worldVis: D.world.visible }; D.vrHeightDone(false); r.back = D.VRUI.stage; r.state2 = D.state;
          D.vruiResume(); r.resumed = D.state; return r; }""")
        imgs["pause"] = await pg.evaluate("() => { D.vruiOpen('pause'); return panel('pause'); }")
        out["leave"] = await pg.evaluate("() => { W('pause', 'Main menu').on(); return { stage: D.VRUI.stage, state: D.state, code: D.MP.code }; }")
        if OUT:
            for k, u in imgs.items(): open(os.path.join(OUT, f"t238_{k}.jpg"), "wb").write(base64.b64decode(u.split(",")[1]))
        print(json.dumps(out))
        o = out
        ok = (o["solo"]["vis"] in ("me,setup", "setup,me") and o["soloView"] and o["look"]["after"].startswith("1.1.") and o["look"]["beardHidden"] and o["char"]["view"] and o["char"]["back"] == "mode"
              and "Host a room" in o["online"]["labels"] and o["rooms"]["entry"] == "770" and o["rooms"]["joinOff"] and set(o["lobby"]["vis"].split(",")) == {"lobby", "setup"} and o["portraits"] >= 4
              and o["edit"]["view"] and set(o["edit"]["vis"].split(",")) == {"me", "setup"} and o["edit"]["done"] and o["edit"]["mainHidden"] and set(o["edit2"].split(",")) == {"lobby", "setup"}
              and o["guest"]["startHidden"] and o["guest"]["latLocked"] and o["guest"]["cardFree"]
              and o["pause"]["state"] == "play" and o["pause"]["h"]["stage"] == "height" and o["pause"]["h"]["worldVis"] and o["pause"]["back"] == "pause" and o["pause"]["resumed"] == "play"
              and o["leave"]["stage"] == "mode" and o["leave"]["state"] == "vrmenu" and not o["leave"]["code"] and not errs)
        print("errors", errs[:5] or "none"); print("PASS" if ok else "FAIL"); await b.close(); return ok
try: res = asyncio.run(main())
finally: srv.terminate()
sys.exit(0 if res else 1)
