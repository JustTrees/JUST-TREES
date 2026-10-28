"""2.46: Map Lab and arenas, in VR, the way they are used. Dev menu > Map Lab builds a map on the table; Land settings (length and width,
the slide through the landscape) rebuild it; the laser on the table sculpts a hill and clears trees (the trigger), B undoes; trees, rocks and
loot are placed; the map gets a name on the keyboard, is saved and published (a stand-in for the online server); Walk it builds the real map
and drops you in it at the pin; the Y menu takes you back to Map Lab; leaving puts the normal settings back. Then online: the host picks the
arena under Arenas in the map settings, a friend joins, and both get exactly the map that was built in Map Lab.
2.47: a mirrored pair of spawn flags (Red west, Blue east) is placed in the Spawns tab; in a 2-team PvP game the host starts at Red,
the friend at Blue, and the friend comes back in at Blue after a respawn.
Served over http with a stand-in /dev; local PeerJS server on :9000 (run_all's ONLINE set).
Usage: python3 dev/test_246.py dbg.html [outdir]"""
import os, sys, asyncio, json, threading, shutil, tempfile, base64
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
srvdir = tempfile.mkdtemp(); shutil.copy(sys.argv[1], os.path.join(srvdir, "dbg.html")); os.symlink(os.path.join(REPO, "models"), os.path.join(srvdir, "models"))
OUT = sys.argv[2] if len(sys.argv) > 2 else None
if OUT and OUT.endswith(".png"): OUT = os.path.dirname(OUT)
PORT, KEY, STORE, POSTS = 8798, "TESTKEY", {}, []
class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=srvdir, **k)
    def log_message(self, *a): pass
    def js(self, o, st=200):
        b = json.dumps(o).encode(); self.send_response(st); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        u = urlparse(self.path)
        if u.path != "/dev": return super().do_GET()
        q = parse_qs(u.query)
        if "get" in q: v = STORE.get(q["get"][0] + ":" + q.get("name", [""])[0].upper()); return self.js({"name": v["name"], "t": v["t"], "pub": v["pub"], "data": v["data"]}) if v else self.js({"error": "not found"}, 404)
        if "list" in q: return self.js({"items": sorted([{"name": v["name"], "t": v["t"], "pub": v["pub"], "info": v["info"]} for k, v in STORE.items() if k.startswith(q["list"][0] + ":")], key=lambda x: -x["t"])})
        return self.js({"error": "bad"}, 400)
    def do_POST(self):
        if urlparse(self.path).path != "/dev": return self.js({"error": "no"}, 404)
        b = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}"); POSTS.append([b.get("op"), b.get("kind"), b.get("pub")])
        if str(b.get("key", "")).upper() != KEY: return self.js({"error": "wrong key"}, 403)
        if b.get("op") == "check": return self.js({"ok": True})
        if b.get("op") == "save": STORE[b["kind"] + ":" + b["name"].upper()] = {"name": b["name"], "t": len(POSTS), "data": b["data"], "pub": bool(b.get("pub")), "info": b.get("info", "")}; return self.js({"ok": True})
        return self.js({"error": "bad"}, 400)
srv = ThreadingHTTPServer(("127.0.0.1", PORT), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
SETUP = open(os.path.join(HERE, "test_mp.py")).read().split('SETUP = """', 1)[1].split('"""', 1)[0]
MORE = """() => { D.setVRON(true); D.vr.on = true; try { localStorage.setItem('jt-age', 'ok'); localStorage.setItem('jt-dev-ok', '1'); localStorage.setItem('jt-dev', 'TESTKEY'); } catch (_) {}
  D.VRUI.rulesOk = true; D.DEV.url = location.origin + '/dev'; D.DEV.ok = true; D.DEV.key = 'TESTKEY';
  window.W = (p, l) => D.VRUI.panels[p].widgets.find(w => !(w.hide && w.hide()) && !w.ghost && (w.label === l || (w.labelFn && w.labelFn() === l)));
  window.SL = p => D.VRUI.panels[p].widgets.filter(w => w.kind === 'slider' && !(w.hide && w.hide()));
  window.tick = n => { for (let i = 0; i < n; i++) D.vruiTick(1 / 30); return 1; };
  window.bg = setInterval(() => { try { D.mpTick(1 / 30); } catch (e) { setTimeout(() => { throw e; }); } }, 33);
  window.fp = () => { let h = 0, t = 0; for (let i = 0; i < 24; i++) for (let j = 0; j < 24; j++) h = (h * 31 + Math.round(D.H(-160 + i * 14, -160 + j * 14) * 100)) | 0;
    for (const l of D.obstacles.values()) for (const o of l) if (o.t) t++; return [h, t, D.water.toFixed(2), D.MAPROCKS ? D.MAPROCKS.length : -1].join('|'); };
  window.aim = (x, z) => { const T = D.THREE, Tb = D.LAB.tbl; Tb.inner.updateMatrixWorld(true); const tgt = Tb.inner.localToWorld(new T.Vector3(x, 0, z)); tgt.y = Tb.inner.localToWorld(new T.Vector3(x, 0, z)).y;
    const yq = new T.Quaternion().setFromAxisAngle(new T.Vector3(0, 1, 0), D.vr.yaw), from = toW(L.R), dir = tgt.clone().sub(from).normalize();
    const q = new T.Quaternion().setFromUnitVectors(new T.Vector3(0, 0, -1), dir); hq.copy(yq.clone().invert().multiply(q)); return 1; };
  window.shot = (eyeL, tgtL, fov, w, h) => { const T = D.THREE, c = D.camera, r = D.renderer, root = D.VRUI.root; r.setSize(w, h); c.fov = fov; c.aspect = w / h; c.updateProjectionMatrix();
    c.position.copy(root.localToWorld(new T.Vector3(...eyeL))); c.lookAt(root.localToWorld(new T.Vector3(...tgtL))); c.updateMatrixWorld();
    for (const L of D.VRUI.lasers) { L.line.visible = L.dot.visible = false; } const hs = D.vrHandsObj; if (hs) { hs.L.g.visible = hs.R.g.visible = false; }
    r.render(D.scene, c); if (hs) { hs.L.g.visible = hs.R.g.visible = true; } return r.domElement.toDataURL('image/jpeg', .88); };
  return 1; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--disable-features=WebRtcHideLocalIpsWithMdns"])
        errs = []
        async def page(nm):
            pg = await (await b.new_context(viewport={"width": 400, "height": 300})).new_page(); pg.on("pageerror", lambda e: errs.append(nm + " PE " + str(e)))
            await pg.goto(f"http://127.0.0.1:{PORT}/dbg.html", timeout=120000); await pg.wait_for_timeout(600)
            await pg.evaluate(SETUP, nm); await pg.evaluate(MORE); return pg
        A = await page("host"); out = {}
        async def until(pg, js, secs, step=150):
            for _ in range(int(secs * 1000 / step)):
                if await pg.evaluate(js): return True
                await pg.wait_for_timeout(step)
            return False
        built = "() => { tick(1); return !!D.LAB.tbl && !D.LAB.needBuild && !D.LAB.building; }"
        async def rebuild(): await A.wait_for_timeout(750); return await until(A, built, 90)
        def save(nm, url):
            if OUT: open(os.path.join(OUT, nm), "wb").write(base64.b64decode(url.split(",")[1]))
        set0 = await A.evaluate("() => D.set.size + ' ' + D.set.lat + ' ' + D.set.rough")
        # ---- into Map Lab from the Dev menu
        await A.evaluate("() => { D.vruiOpen('mode'); W('mode', 'Dev').on(); W('dev', 'Map Lab').on(); return 1; }")
        out["stage"] = await A.evaluate("() => D.VRUI.stage")
        out["built"] = await until(A, built, 90)
        await A.evaluate("() => { D.LAB.A.seed = 4242; D.LAB.A.size = 'medium'; D.LAB.needBuild = true; D.LAB.buildAt = 0; return 1; }"); await until(A, built, 90)   # (always the same map)
        out["tableParts"] = await A.evaluate("() => { const T = D.LAB.tbl; return [T.tl.length > 100, T.rl.length > 5, T.plan.length > 20, D.ARENA === D.LAB.A].join(' '); }")
        # ---- the shape: a long thin island
        await A.evaluate("() => { W('lab', 'S').on(); const s = SL('lab'); s[0].set(.65); s[1].set(.32); return 1; }")
        out["reshaped"] = await rebuild()
        out["shape"] = await A.evaluate("""() => { let x0 = 1e9, x1 = -1e9, z0 = 1e9, z1 = -1e9; const S2 = { xs: 125, small: 200, medium: 280, large: 400, xl: 600, xxl: 800, xxxl: 1500 }[D.set.size];
          for (let i = 0; i <= 60; i++) for (let j = 0; j <= 60; j++) { const x = -S2 + i * S2 / 30, z = -S2 + j * S2 / 30; if (D.H(x, z) > D.water + .5) { x0 = Math.min(x0, x); x1 = Math.max(x1, x); z0 = Math.min(z0, z); z1 = Math.max(z1, z); } }
          return [D.set.size, Math.round(x1 - x0), Math.round(z1 - z0)]; }""")
        # ---- the slide through the landscape: different land, and back again
        f0 = await A.evaluate("() => fp()")
        await A.evaluate("() => { SL('lab')[4].set(900); return 1; }"); await rebuild(); f1 = await A.evaluate("() => fp()")
        await A.evaluate("() => { SL('lab')[4].set(0); return 1; }"); await rebuild(); f2 = await A.evaluate("() => fp()")
        out["slide"] = [f0 != f1, f0 == f2]
        # ---- sculpt with the laser: hold the trigger on the table, B undoes, then again
        await A.evaluate("() => { W('lab', 'Sculpt').on(); W('lab', 'Raise').on(); D.LAB.br = 30; D.LAB.str = 1; aim(50, 20); tick(2); pad.R.trig = 1; tick(25); pad.R.trig = 0; tick(2); return 1; }")
        out["sculpted"] = await A.evaluate("() => [Math.max(...D.arenaGrid(D.LAB.A).D).toFixed(1), D.LAB.undo.length, D.LAB.dirty]")
        await A.evaluate("() => { pad.R.b = 1; tick(1); pad.R.b = 0; tick(1); return 1; }")
        out["undone"] = await A.evaluate("() => Math.max(...D.arenaGrid(D.LAB.A).D).toFixed(1)")
        await A.evaluate("() => { aim(50, 20); tick(2); pad.R.trig = 1; tick(25); pad.R.trig = 0; tick(2); return 1; }")
        # ---- trees: clear a patch with the laser; plant three; rocks and loot by hand
        await A.evaluate("() => { W('lab', 'Trees').on(); W('lab', 'Remove').on(); D.LAB.br = 25; aim(-40, -50); tick(2); pad.R.trig = 1; tick(8); pad.R.trig = 0; tick(2); return 1; }")
        await A.evaluate("""() => { const h = (x, z) => ({ x, z, y: 0 }), L = D.LAB; L.tab = 'trees'; L.tool.trees = 'plant'; [[90, 80], [100, 80], [110, 80]].forEach(([x, z]) => D.labPress(h(x, z)));
          L.tab = 'rocks'; L.tool.rocks = 'place'; L.rkind = 'crag'; L.rsize = 6; D.labPress(h(-90, 60)); L.rkind = 'boulder'; L.rsize = 3; D.labPress(h(-70, 60));
          L.tab = 'loot'; L.tool.loot = 'place'; L.loot = 'gun:hunt'; L.tier = 5; D.labPress(h(20, -20)); L.loot = 'hp'; D.labPress(h(24, -20)); L.tab = 'spawns'; L.tool.spawns = 'place'; L.side = 1; L.mirror = true; D.labPress(h(-50, 0));   /* 2.47: Red flag, Blue mirrored */
          L.tab = 'land'; D.LAB.start = [40, 10]; return 1; }""")
        out["recipe"] = await A.evaluate("() => { const a = D.LAB.A; return [a.treesOff.length, a.treesAdd.length, a.rocksAdd.length, a.loot.mode, a.loot.pts.length, JSON.stringify(a.spawns)].join(' '); }")
        if OUT:
            await A.evaluate("() => { D.LAB.tab = 'sculpt'; D.uiDraw(D.VRUI.panels.lab); tick(1); return 1; }")
            save("t246_lab.jpg", await A.evaluate("() => shot([0, 1.62, .05], [-.25, 1.0, -1.3], 78, 1600, 1000)"))
            save("t246_table.jpg", await A.evaluate("() => shot([.15, 1.75, -.35], [.15, .8, -1.38], 62, 1400, 1000)"))
            for t in ["land", "world", "sculpt", "trees", "rocks", "loot", "spawns", "file"]:
                save(f"t246_panel_{t}.jpg", await A.evaluate(f"() => {{ D.LAB.tab = '{t}'; D.uiDraw(D.VRUI.panels.lab); return D.VRUI.panels.lab.cv.toDataURL('image/jpeg', .85); }}"))
            await A.evaluate("() => { D.LAB.tab = 'land'; return 1; }")
        # ---- name it on the keyboard, save, publish
        await A.evaluate("() => { W('lab', 'File').on(); W('lab', 'Tap to name it').on(); return 1; }")
        out["keyboard"] = await A.evaluate("() => D.VRUI.stage + ' ' + D.VRUI.keyFor")
        await A.evaluate("() => { W('tag', 'Clear').on(); for (const ch of 'RIDGE RUN') W('tag', ch === ' ' ? 'Space' : ch).on(); W('tag', 'OK').on(); return 1; }")
        out["named"] = await A.evaluate("() => D.VRUI.stage + ' ' + D.LAB.A.name")
        await A.evaluate("() => { W('lab', 'Save').on(); return 1; }"); await until(A, "() => /Saved/.test(D.LAB.status)", 10)
        await A.evaluate("() => { W('lab', 'Publish').on(); return 1; }"); await until(A, "() => /Published/.test(D.LAB.status) && D.LAB.saved && D.LAB.saved.some(s => s.pub)", 10)
        out["saved"] = [POSTS[-2:], await A.evaluate("() => D.LAB.status + ' | ' + D.LAB.saved.map(s => (s.pub ? '*' : '') + s.name + ' ' + s.info).join(',')"), len(json.dumps(STORE["arena:RIDGE RUN"]["data"]))]
        # ---- Walk it (as PvP): it builds first, then you're in the real map at the pin
        await A.evaluate("() => { W('lab', 'PvP').on(); W('lab', 'Walk it').on(); return 1; }")
        out["walkReady"] = await until(A, "() => { tick(1); return D.LAB.testing && !!D.VRUI.fadeGo; }", 90)
        await A.evaluate("() => { const f = D.VRUI.fadeGo; D.VRUI.fadeGo = null; f(); return 1; }")
        labFp = await A.evaluate("() => fp()")
        out["walking"] = await A.evaluate("() => [D.state, D.world.visible, Math.round(Math.hypot(D.P.x - 40, D.P.z - 10)), [...D.DROPS.keys()].filter(k => k[0] === 'a').join(','), (D.H(50, 20) - D.water).toFixed(1)]")
        if OUT:
            save("t246_walk.jpg", await A.evaluate("""() => { const T = D.THREE, c = D.camera, r = D.renderer; r.setSize(1400, 900); c.fov = 70; c.aspect = 1400 / 900; c.updateProjectionMatrix();
              c.position.set(-60, D.water + 55, -190); c.lookAt(10, D.water + 4, 10); c.updateMatrixWorld(); D.cullTiles(); r.render(D.scene, c); return r.domElement.toDataURL('image/jpeg', .85); }"""))
        # ---- the Y menu: back to Map Lab
        await A.evaluate("() => { D.vruiOpen('pause'); return 1; }")
        out["pause"] = await A.evaluate("() => [!!W('pause', 'Back to Map Lab'), !W('pause', 'New map, same settings')]")
        await A.evaluate("() => { W('pause', 'Back to Map Lab').on(); tick(2); return 1; }")
        out["back"] = await A.evaluate("() => D.VRUI.stage + ' ' + D.LAB.testing + ' ' + D.LAB.on")
        await A.evaluate("() => { W('lab', 'Dev menu').on(); return 1; }")
        out["left"] = await A.evaluate("() => D.VRUI.stage + ' ' + D.LAB.on + ' ' + D.set.size + ' ' + D.set.lat + ' ' + D.set.rough")
        # ---- online: the host picks the arena, a friend joins, both get the same map as Map Lab built
        await A.evaluate("() => { D.MP.tag = 'HOSTY'; D.vruiOpen('mode'); W('mode', 'Online').on(); W('mp', 'Host a room').on(); return 1; }")
        await until(A, "() => /Waiting/.test(D.MP.status)", 15); code = await A.evaluate("() => D.MP.code")
        await A.evaluate("() => { W('setup', 'Deathmatch').on(); W('setup', '2 Teams').on(); W('setup', 'Arenas').on(); return 1; }")
        await until(A, "() => D.ARN.list && D.ARN.list.length > 0", 10)
        out["arenaList"] = await A.evaluate("() => D.ARN.list.map(a => a.name + ' · ' + a.info).join(',')")
        if OUT: save("t246_arenas.jpg", await A.evaluate("() => { D.uiDraw(D.VRUI.panels.arenas); return D.VRUI.panels.arenas.cv.toDataURL('image/jpeg', .85); }"))
        await A.evaluate("() => { W('arenas', 'RIDGE RUN').on(); return 1; }")
        await until(A, "() => !!D.set.arena && D.VRUI.stage === 'lobby'", 10)
        out["picked"] = await A.evaluate("() => (D.set.arena && D.set.arena.name) + ' ' + D.VRUI.stage")
        if OUT: save("t246_settings.jpg", await A.evaluate("() => { D.uiDraw(D.VRUI.panels.setup); return D.VRUI.panels.setup.cv.toDataURL('image/jpeg', .8); }"))
        B = await page("guest")
        await B.evaluate("() => { D.MP.tag = 'FRIEND'; D.vruiOpen('mode'); W('mode', 'Online').on(); W('mp', 'Join a room').on(); return 1; }")
        await B.evaluate(f"() => {{ for (const k of '{code}') W('rooms', k).on(); W('rooms', 'Join').on(); return 1; }}")
        out["connected"] = await until(A, "() => D.mpOpen().length === 1", 25) and await until(B, "() => D.mpOpen().length === 1 && D.MP.on", 15)
        await until(B, "() => !!D.set.arena", 10)
        out["guestArena"] = await B.evaluate("() => D.set.arena ? D.set.arena.name : null")
        await A.evaluate("() => { W('setup', 'Start').on(); return 1; }")
        out["bothPreview"] = await until(A, "() => { D.vruiTick(1 / 60); return D.VRUI.stage === 'preview'; }", 60) and await until(B, "() => { D.vruiTick(1 / 60); return D.VRUI.stage === 'preview'; }", 60)
        out["maps"] = [labFp, await A.evaluate("() => fp()"), await B.evaluate("() => fp()")]
        out["starts"] = [await A.evaluate("() => D.mpMyTeam ? 0 : 0"), await A.evaluate("() => Math.round(Math.hypot(D.P.x + 50, D.P.z))"), await B.evaluate("() => Math.round(Math.hypot(D.P.x - 50, D.P.z))")]   # Red near (-50, 0), Blue near (50, 0)
        await B.evaluate("() => { D.uwRespawn(); return 1; }"); out["respawn"] = await B.evaluate("() => Math.round(Math.hypot(D.P.x - 50, D.P.z))")
        print(json.dumps(out))
        ok = (out["stage"] == "lab" and out["built"] and out["tableParts"] == "true true true true" and out["reshaped"] and out["shape"][0] == "small" and 120 < out["shape"][1] < 260 and out["shape"][1] > out["shape"][2] * 1.35
              and out["slide"] == [True, True] and float(out["sculpted"][0]) > 3 and out["sculpted"][1] >= 1 and out["undone"] == "0.0" and out["recipe"] == "1 3 2 both 2 [[-50,0,1],[50,0,2]]"
              and out["keyboard"] == "tag arena" and out["named"] == "lab RIDGE RUN" and ["save", "arena", True] in out["saved"][0] and "*RIDGE RUN" in out["saved"][1]
              and out["walkReady"] and out["walking"][0] == "play" and out["walking"][1] and out["walking"][2] < 40 and "a0" in out["walking"][3] and out["pause"] == [True, True]
              and out["back"] == "lab false true" and out["left"] == "dev false " + set0 and "RIDGE RUN" in out["arenaList"] and out["picked"] == "RIDGE RUN lobby" and out["connected"]
              and out["guestArena"] == "RIDGE RUN" and out["bothPreview"] and out["maps"][0] == out["maps"][1] == out["maps"][2] and out["starts"][1] < 35 and out["starts"][2] < 35 and out["respawn"] < 35 and not errs)
        print("errors:", errs[:5] or ("none" if ok else "CHECKS FAILED")); await b.close(); return ok
try: res = asyncio.run(main())
finally: srv.shutdown()
sys.exit(0 if res else 1)
