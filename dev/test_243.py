"""2.43: a real online game in VR with the people on, through the new menus, the way it is played: the host taps Online > Host a room (straight
into the lobby); the friend taps Online > Join a room, types the code on the pad and joins; both lobbies list both players with pictures;
the host presses Start and Play; both play with each other's character drawn (top half from their headset, legs walking), no page errors.
Also: a friend on a different network version is told clearly on both sides. Served over http (people need it); local PeerJS server on :9000.
Usage: python3 dev/test_243.py dbg.html [outdir]"""
import os, sys, asyncio, json, subprocess, time, shutil, tempfile, base64
from playwright.async_api import async_playwright
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
srvdir = tempfile.mkdtemp(); shutil.copy(sys.argv[1], os.path.join(srvdir, "dbg.html")); os.symlink(os.path.join(REPO, "models"), os.path.join(srvdir, "models"))
OUT = sys.argv[2] if len(sys.argv) > 2 else None
if OUT and OUT.endswith(".png"): OUT = os.path.dirname(OUT)
PORT = 8797
srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=srvdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2)
SETUP = open(os.path.join(HERE, "test_mp.py")).read().split('SETUP = """', 1)[1].split('"""', 1)[0]
MORE = """() => { D.setVRON(true); D.vr.on = true; try { localStorage.setItem('jt-age', 'ok'); } catch (_) {} D.VRUI.rulesOk = true;
  window.W = (p, l) => D.VRUI.panels[p].widgets.find(w => w.label === l || (w.labelFn && w.labelFn() === l));
  window.vis = () => Object.keys(D.VRUI.panels).filter(k => D.VRUI.panels[k].mesh.visible).sort().join(',');
  window.bg = setInterval(() => { try { D.mpTick(1 / 30); if (D.VRUI.on || D.VRUI.fadeV > 0 || D.VRUI.fadeGo) D.vruiTick(1 / 30); } catch (e) { setTimeout(() => { throw e; }); } }, 33);   /* the real loop keeps these going all the time */
  return D.charOn(); }"""
async def run_frames(pg, n, chunk=6):
    for _ in range(n // chunk): await pg.evaluate(f"() => frames({chunk})"); await pg.wait_for_timeout(chunk * 16)
async def wait(pg, js, secs, step=250):
    for _ in range(int(secs * 1000 / step)):
        if await pg.evaluate(js): return True
        await pg.wait_for_timeout(step)
    return False
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--disable-features=WebRtcHideLocalIpsWithMdns"])
        errs = []
        async def page(nm):
            pg = await (await b.new_context(viewport={"width": 400, "height": 300})).new_page(); pg.on("pageerror", lambda e: errs.append(nm + " PE " + str(e)))
            await pg.goto(f"http://127.0.0.1:{PORT}/dbg.html", timeout=120000); await pg.wait_for_timeout(600)
            await pg.evaluate(SETUP, nm); on = await pg.evaluate(MORE); return pg, on
        (A, onA), (B, onB) = await page("host"), await page("guest"); out = {"peopleOn": [onA, onB]}
        # the host: Online > Host a room
        await A.evaluate("() => { D.MP.tag = 'HOSTY'; D.vruiOpen('mode'); W('mode', 'Online').on(); W('mp', 'Host a room').on(); return 1; }")
        out["hostStage"] = await A.evaluate("() => D.VRUI.stage + ' / ' + vis()")
        await wait(A, "() => /Waiting/.test(D.MP.status)", 15); code = await A.evaluate("() => D.MP.code")
        # the friend: Online > Join a room > type the code > Join
        await B.evaluate("() => { D.MP.tag = 'TREEFROG'; D.vruiOpen('mode'); W('mode', 'Online').on(); W('mp', 'Join a room').on(); return 1; }")
        await B.evaluate(f"() => {{ for (const k of '{code}') W('rooms', k).on(); W('rooms', 'Join').on(); return 1; }}")
        out["guestStage"] = await B.evaluate("() => D.VRUI.stage + ' / ' + vis()")
        out["connected"] = await wait(A, "() => D.mpOpen().length === 1", 25) and await wait(B, "() => D.mpOpen().length === 1 && D.MP.on", 15)
        await wait(A, "() => D.mpRoster().every(r => r.me || r.tag === 'TREEFROG')", 5)
        out["rosters"] = [await A.evaluate("() => D.mpRoster().map(r => r.tag).join(',')"), await B.evaluate("() => D.mpRoster().map(r => r.tag).join(',')")]
        await wait(A, "() => { D.uiDraw(D.VRUI.panels.lobby); return D.CHP.cache.size >= 2 || D.CHAR.failed > 0; }", 60)
        await wait(B, "() => { D.uiDraw(D.VRUI.panels.lobby); return D.CHP.cache.size >= 2 || D.CHAR.failed > 0; }", 60)
        out["lobbyPictures"] = [await A.evaluate("() => D.CHP.cache.size"), await B.evaluate("() => D.CHP.cache.size")]
        if OUT:
            for nm, pg in (("host", A), ("guest", B)):
                u = await pg.evaluate("() => D.VRUI.panels.lobby.cv.toDataURL('image/jpeg', .85)"); open(os.path.join(OUT, f"t243_lobby_{nm}.jpg"), "wb").write(base64.b64decode(u.split(",")[1]))
        # the host picks PvP and presses Start, then Play this map
        await A.evaluate("() => { W('setup', 'Deathmatch').on(); D.set.size = 'small'; D.set.weather = 'clear'; W('setup', 'Start').on(); return 1; }")
        out["bothPreview"] = await wait(A, "() => D.VRUI.stage === 'preview'", 40) and await wait(B, "() => D.VRUI.stage === 'preview'", 40)
        await A.evaluate("() => { W('preview', 'Play this map').on(); return 1; }")
        for _ in range(40):
            await asyncio.gather(A.evaluate("() => { D.vruiTick(1 / 60); return 1; }"), B.evaluate("() => { D.vruiTick(1 / 60); return 1; }")); await A.wait_for_timeout(120)
            if await A.evaluate("() => D.state === 'play'") and await B.evaluate("() => D.state === 'play'"): break
        for _ in range(30):
            await asyncio.gather(A.evaluate("() => { D.vruiTick(1 / 60); return 1; }"), B.evaluate("() => { D.vruiTick(1 / 60); return 1; }")); await A.wait_for_timeout(60)
        out["bothPlaying"] = [await A.evaluate("() => D.state"), await B.evaluate("() => D.state")]
        await asyncio.gather(A.evaluate("() => { placeAt(D.P.x, D.P.z); return 1; }"), B.evaluate("() => { placeAt(D.P.x, D.P.z); return 1; }"))
        hp = await A.evaluate("() => [D.P.x, D.P.z]")
        await B.evaluate(f"() => {{ placeAt({hp[0]}, {hp[1]} - 6); hq.setFromAxisAngle(new D.THREE.Vector3(0, 1, 0), Math.PI); return 1; }}")
        await asyncio.gather(run_frames(A, 90), run_frames(B, 90))
        await wait(A, "() => { frames(3); const L = D.mpOpen()[0]; return !!(L && L.R && L.R.C); }", 60)
        await wait(B, "() => { frames(3); const L = D.mpOpen()[0]; return !!(L && L.R && L.R.C); }", 60)
        out["seeEachOther"] = [await A.evaluate("() => { const L = D.mpOpen()[0]; return !!(L && L.R && L.R.C && L.R.C.top.visible); }"), await B.evaluate("() => { const L = D.mpOpen()[0]; return !!(L && L.R && L.R.C && L.R.C.top.visible); }")]
        out["ownBodies"] = [await A.evaluate("() => !!(D.vr.meC && D.vr.meC.top.visible)"), await B.evaluate("() => !!(D.vr.meC && D.vr.meC.top.visible)")]
        print("progress", json.dumps(out), flush=True)
        out["linksA"] = await A.evaluate("() => [...D.MP.links.values()].map(L => [L.tag, L.open, L.bad, L.v].join('/')).join(' ; ') + ' | ' + D.MP.status")
        out["linksB"] = await B.evaluate("() => [...D.MP.links.values()].map(L => [L.tag, L.open, L.bad, L.v].join('/')).join(' ; ') + ' | ' + D.MP.status + ' | ' + D.MP.code")
        print("links", out["linksA"], "||", out["linksB"], flush=True)
        # the friend walks sideways: the host sees them move and their legs step
        await B.evaluate("() => { pad.L.sx = 1; return 1; }"); await asyncio.gather(run_frames(A, 48), run_frames(B, 48))
        out["guestWalkingSeen"] = await A.evaluate("() => { const C = D.mpOpen()[0].R.C; return C.cur + ' ' + C.speed.toFixed(1); }")
        await B.evaluate("() => { pad.L.sx = 0; return 1; }")
        if OUT:
            u = await A.evaluate("""() => { const T = D.THREE, c = D.camera, r = D.renderer, C = D.mpOpen()[0].R.C; r.setSize(800, 500); c.fov = 50; c.aspect = 1.6; c.updateProjectionMatrix();
              c.position.set(C.x + 3, D.P.y + 1.4, C.z + 1); c.lookAt(C.x, C.y + .9, C.z); c.updateMatrixWorld(); D.cullTiles(); r.render(D.scene, c); return r.domElement.toDataURL('image/jpeg', .85); }""")
            open(os.path.join(OUT, "t243_ingame.jpg"), "wb").write(base64.b64decode(u.split(",")[1]))
        # a friend on another network version: both are told
        C2, _ = await page("old")
        await C2.evaluate("() => { D.MP.tag = 'OLDIE'; return 1; }")
        await C2.evaluate("() => { D.MP.netV = '2.30'; return 1; }")
        await C2.evaluate(f"() => {{ D.mpJoin('{code}'); D.vruiOpen('lobby'); return 1; }}")
        await asyncio.gather(run_frames(A, 120), C2.evaluate("() => 1"))
        await wait(C2, "() => D.VRUI.stage !== 'lobby' || /version/i.test(D.MP.status)", 20)
        out["oldFriendTold"] = await C2.evaluate("() => D.VRUI.stage + ' | ' + D.MP.status")
        out["hostTold"] = await A.evaluate("() => (D.MP.warn && D.MP.warn.text) || ''")
        print(json.dumps(out))
        ok = (all(out["peopleOn"]) and out["hostStage"].startswith("lobby") and out["guestStage"].startswith("lobby") and out["connected"] and "TREEFROG" in out["rosters"][0] and "HOSTY" in out["rosters"][1]
              and min(out["lobbyPictures"]) >= 2 and out["bothPreview"] and out["bothPlaying"] == ["play", "play"] and all(out["seeEachOther"]) and all(out["ownBodies"])
              and ("Walk" in out["guestWalkingSeen"] or "Jog" in out["guestWalkingSeen"] or "Sprint" in out["guestWalkingSeen"])) and "version" in out["oldFriendTold"].lower() and "OLDIE" in out["hostTold"] and not errs
        print("errors:", errs[:5] or ("none" if ok else "CHECKS FAILED")); await b.close(); return ok
try: res = asyncio.run(main())
finally: srv.terminate()
sys.exit(0 if res else 1)
