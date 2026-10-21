"""2.45: Dev Mode and the Creature Workshop, in VR, the way it is used: five taps on the main menu's title open the dev key keyboard; a wrong key
is refused, the right one (checked by a stand-in for the online server) turns Dev Mode on and a Dev button appears; Dev > Creature Workshop puts a
wolf on the turntable; stretching parts changes the shape (feet stay on the ground, separate feet stay on the end of their legs while walking);
pointing at the head picks it; parts (up to 8) ride on their bones; recolouring changes the coat but keeps dark details; the moves play; naming,
saving, listing and loading go through the server; every animal and dinosaur builds with changes; the world's light and fog come back after;
locking hides Dev Mode again. Served over http (models), with a stand-in /dev on the same server.
Usage: python3 dev/test_245.py dbg.html [outdir]"""
import os, sys, asyncio, json, threading, shutil, tempfile, base64
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
srvdir = tempfile.mkdtemp(); shutil.copy(sys.argv[1], os.path.join(srvdir, "dbg.html")); os.symlink(os.path.join(REPO, "models"), os.path.join(srvdir, "models"))
OUT = sys.argv[2] if len(sys.argv) > 2 else None
if OUT and OUT.endswith(".png"): OUT = os.path.dirname(OUT)
PORT, KEY, STORE, POSTS = 8799, "TESTKEY", {}, []
class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=srvdir, **k)
    def log_message(self, *a): pass
    def js(self, o, st=200):
        b = json.dumps(o).encode(); self.send_response(st); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        u = urlparse(self.path)
        if u.path != "/dev": return super().do_GET()
        q = parse_qs(u.query)
        if "get" in q: v = STORE.get(q["get"][0] + ":" + q.get("name", [""])[0].upper()); return self.js(v) if v else self.js({"error": "not found"}, 404)
        if "list" in q: return self.js({"items": sorted([{"name": v["name"], "t": v["t"]} for k, v in STORE.items() if k.startswith(q["list"][0] + ":")], key=lambda x: -x["t"])})
        return self.js({"error": "bad"}, 400)
    def do_POST(self):
        if urlparse(self.path).path != "/dev": return self.js({"error": "no"}, 404)
        b = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}"); POSTS.append(b.get("op"))
        if str(b.get("key", "")).upper() != KEY: return self.js({"error": "wrong key"}, 403)
        if b.get("op") == "check": return self.js({"ok": True})
        if b.get("op") == "save": STORE[b["kind"] + ":" + b["name"].upper()] = {"name": b["name"], "t": len(POSTS), "data": b["data"]}; return self.js({"ok": True})
        return self.js({"error": "bad"}, 400)
srv = ThreadingHTTPServer(("127.0.0.1", PORT), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
SETUP = open(os.path.join(HERE, "test_mp.py")).read().split('SETUP = """', 1)[1].split('"""', 1)[0]
MORE = """() => { D.setVRON(true); D.vr.on = true; try { localStorage.setItem('jt-age', 'ok'); } catch (_) {} D.VRUI.rulesOk = true; D.DEV.url = location.origin + '/dev';
  window.W = (p, l) => D.VRUI.panels[p].widgets.find(w => !(w.hide && w.hide()) && !w.ghost && (w.label === l || (w.labelFn && w.labelFn() === l)));
  window.SL = p => D.VRUI.panels[p].widgets.filter(w => w.kind === 'slider' && !(w.hide && w.hide()));
  window.tick = n => { for (let i = 0; i < n; i++) D.vruiTick(1 / 30); return 1; };
  window.shot = (yawDeg, fov, w, h, eyeY, tgt, tilt) => { const T = D.THREE, c = D.camera, r = D.renderer, root = D.VRUI.root; r.setSize(w, h); c.fov = fov; c.aspect = w / h; c.updateProjectionMatrix();
    const a = yawDeg * Math.PI / 180, eye = root.localToWorld(new T.Vector3(0, eyeY, 0)), tg = root.localToWorld(new T.Vector3(-Math.sin(a) * tgt, eyeY - (tilt || .25), -Math.cos(a) * tgt));
    c.position.copy(eye); c.lookAt(tg); c.updateMatrixWorld(); for (const L of D.VRUI.lasers) { L.line.visible = L.dot.visible = false; }
    r.render(D.scene, c); return r.domElement.toDataURL('image/jpeg', .88); };
  window.frame = pad => { const T = D.THREE, c = D.camera, r = D.renderer, root = D.VRUI.root; D.WS.group.updateMatrixWorld(true);   /* the creature alone, filling the picture, seen from where you stand */
    const bb = new T.Box3().copy(D.WS.Mx.geo.boundingBox).applyMatrix4(D.WS.Q.mesh.matrixWorld); for (const o of D.WS.kitObjs) bb.expandByObject(o);
    const ctr = bb.getCenter(new T.Vector3()), sz = bb.getSize(new T.Vector3()).length() * (pad || .34), d = root.localToWorld(new T.Vector3(0, .3, 1)).sub(root.localToWorld(new T.Vector3())).normalize();
    r.setSize(1200, 900); c.fov = 45; c.aspect = 4 / 3; c.updateProjectionMatrix(); c.position.copy(ctr).addScaledVector(d, sz / Math.tan(22.5 * Math.PI / 180)); c.lookAt(ctr); c.updateMatrixWorld();
    for (const L of D.VRUI.lasers) { L.line.visible = L.dot.visible = false; } for (const k in D.VRUI.panels) D.VRUI.panels[k].mesh.visible = false;
    r.render(D.scene, c); D.vruiShow(); return r.domElement.toDataURL('image/jpeg', .88); };
  return 1; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        errs = []
        pg = await (await b.new_context(viewport={"width": 400, "height": 300})).new_page(); pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(f"http://127.0.0.1:{PORT}/dbg.html", timeout=120000); await pg.wait_for_timeout(600)
        await pg.evaluate(SETUP, "dev"); await pg.evaluate(MORE)
        out = {}
        async def until(js, secs, step=150):
            for _ in range(int(secs * 1000 / step)):
                if await pg.evaluate(js): return True
                await pg.wait_for_timeout(step)
            return False
        async def settle(secs=40):                              # let the Workshop rebuild after a change (it waits a moment between rebuilds)
            return await until("() => { tick(1); return !D.WS.dirty && !!D.WS.Q; }", secs)
        def save(nm, url):
            if OUT: open(os.path.join(OUT, nm), "wb").write(base64.b64decode(url.split(",")[1]))
        # ---- the hidden way in
        light0 = await pg.evaluate("() => [D.hemi.intensity, D.sunL.intensity, !!D.scene.fog]")
        await pg.evaluate("() => { D.vruiOpen('mode'); return 1; }")
        out["devHidden"] = await pg.evaluate("() => !W('mode', 'Dev')")
        await pg.evaluate("() => { const g = D.VRUI.panels.mode.widgets.find(w => w.ghost); for (let i = 0; i < 5; i++) g.on(); return 1; }")
        out["keyboard"] = await pg.evaluate("() => D.VRUI.stage + ' ' + D.VRUI.keyFor")
        await pg.evaluate("() => { D.VRUI.tagEdit = 'WRONG1'; W('tag', 'OK').on(); return 1; }")
        await until("() => /isn't right/.test(D.DEV.msg)", 10); out["wrongKey"] = await pg.evaluate("() => [D.DEV.msg, D.DEV.ok, D.VRUI.stage].join(' | ')")
        await pg.evaluate("() => { W('tag', 'Clear').on(); for (const ch of 'TESTKEY') W('tag', ch).on(); W('tag', 'OK').on(); return 1; }")
        await until("() => D.DEV.ok && D.VRUI.stage === 'dev'", 10)
        out["unlocked"] = await pg.evaluate("() => [D.DEV.ok, D.VRUI.stage, localStorage.getItem('jt-dev-ok')].join(' ')")
        if OUT: save("t245_devmenu.jpg", await pg.evaluate("() => D.VRUI.panels.dev.cv.toDataURL('image/jpeg', .85)"))
        await pg.evaluate("() => { D.vruiOpen('mode'); return 1; }")
        out["devButton"] = await pg.evaluate("() => !!W('mode', 'Dev')")
        if OUT: save("t245_mainmenu.jpg", await pg.evaluate("() => D.VRUI.panels.mode.cv.toDataURL('image/jpeg', .85)"))
        # ---- the Workshop: a wolf on the turntable
        await pg.evaluate("() => { W('mode', 'Dev').on(); W('dev', 'Creature Workshop').on(); return 1; }")
        out["stage"] = await pg.evaluate("() => D.VRUI.stage + ' / ' + Object.keys(D.VRUI.panels).filter(k => D.VRUI.panels[k].mesh.visible).join(',')")
        out["wolfBuilt"] = await settle()
        out["workLight"] = await pg.evaluate("() => [D.hemi.intensity, !!D.scene.fog]")
        stock = await pg.evaluate("() => { const e = D.WS.Mx.ext; return { all: e.all, head: e.head }; }")
        # stretch: a bigger head, longer neck, legs and tail, a thicker body
        await pg.evaluate("""() => { const pick = l => W('work', l).on();
          pick('Head'); let s = SL('work'); s[0].set(1.2); s[2].set(1.6);
          pick('Neck'); SL('work')[0].set(1.8); pick('Front legs'); SL('work')[0].set(1.4); pick('Back legs'); SL('work')[0].set(1.4);
          pick('Body'); SL('work')[1].set(1.3); pick('Tail'); SL('work')[0].set(1.5); return 1; }""")
        await pg.wait_for_timeout(200); await settle()
        now = await pg.evaluate("() => { const e = D.WS.Mx.ext; return { all: e.all, head: e.head, nan: D.WS.Mx.geo.attributes.position.array.some(isNaN), size: D.WS.sizeTxt }; }")
        h0, h1 = stock["all"]["u"][1] - stock["all"]["u"][0], now["all"]["u"][1] - now["all"]["u"][0]
        hs0, hs1 = stock["head"]["u"][1] - stock["head"]["u"][0], now["head"]["u"][1] - now["head"]["u"][0]
        out["taller"] = round(h1 / h0, 3); out["headBigger"] = round(hs1 / hs0, 3); out["feetOnGround"] = round(abs(now["all"]["u"][0] - stock["all"]["u"][0]) / h0, 5); out["nan"] = now["nan"]; out["sizeTxt"] = now["size"]
        out["footGap"] = await pg.evaluate("""() => { const T = D.THREE;
          const gap = Mx => { const Q = D.qdinoMake(Mx), a = Q.act('Walk'); a.play(); let worst = 0, len = 0; const d = a.getClip().duration;
            const f = Q.top.getObjectByName('FrontFootL'), e = Q.top.getObjectByName('FrontLowLegL_end'), u = Q.top.getObjectByName('FrontUpLegL');
            for (let k = 0; k < 16; k++) { a.time = d * k / 16; Q.mixer.update(0); Q.top.updateMatrixWorld(true);
              const pe = e.getWorldPosition(new T.Vector3()); worst = Math.max(worst, f.getWorldPosition(new T.Vector3()).distanceTo(pe)); len = Math.max(len, u.getWorldPosition(new T.Vector3()).distanceTo(pe)); }
            return +(worst / len).toFixed(4); };
          return [gap(D.QDINO.models.wolf), gap(D.WS.Mx)]; }""")
        # pointing at the head picks it
        out["picked"] = await pg.evaluate("""() => { const T = D.THREE; D.WS.part = 'body'; D.WS.Q.top.updateMatrixWorld(true);
          const hp = D.WS.Q.top.getObjectByName('Head').getWorldPosition(new T.Vector3()).lerp(D.WS.Q.top.getObjectByName('Head_end').getWorldPosition(new T.Vector3()), .5), from = D.VRUI.root.localToWorld(new T.Vector3(.2, 1.4, -.3));
          D.wsPick(from, hp.clone().sub(from)); return D.WS.part; }""")
        await pg.evaluate("() => { tick(2); return 1; }")
        if OUT:
            save("t245_shape_panel.jpg", await pg.evaluate("() => { D.uiDraw(D.VRUI.panels.work); return D.VRUI.panels.work.cv.toDataURL('image/jpeg', .85); }"))
            save("t245_view.jpg", await pg.evaluate("() => shot(26, 80, 1600, 900, 1.6, 2, .2)"))
        # parts: all ten offered, eight allowed
        await pg.evaluate("""() => { W('work', 'Parts').on(); for (const n of ['Horns', 'Mane', 'Sail', 'Spikes', 'Plates', 'Tusks', 'Crest', 'Club', 'Antlers', 'Frill']) W('work', n).on();
          W('work', '2. Mane').on(); SL('work')[0].set(1.3); return 1; }""")
        await pg.wait_for_timeout(200); await settle()
        out["parts"] = await pg.evaluate("() => [D.WS.R.kit.length, D.WS.kitObjs.length, D.WS.kitObjs.every(o => o.parent && o.parent.isBone), D.WS.status, D.WS.R.kit[1].size].join(' ')")
        if OUT: save("t245_parts_panel.jpg", await pg.evaluate("() => { D.uiDraw(D.VRUI.panels.work); return D.VRUI.panels.work.cv.toDataURL('image/jpeg', .85); }"))
        # colour: the body a slate blue; dark details stay
        out["recolour"] = await pg.evaluate("""() => { W('work', 'Colour').on(); W('work', 'Body').on(); const w = D.VRUI.panels.work.widgets.find(q => q.paintCol === '#3a4a6a' && !(q.hide && q.hide())); w.on();
          return D.WS.R.colors.body; }""")
        await pg.wait_for_timeout(200); await settle()
        out["coat"] = await pg.evaluate("""() => { const a = D.QDINO.models.wolf.geo.attributes.color.array, b = D.WS.Mx.geo.attributes.color.array; let ch = 0, darkKept = 0, dark = 0;
          for (let i = 0; i < a.length; i += 3) { const l = a[i] * .3 + a[i + 1] * .59 + a[i + 2] * .11; if (a[i] !== b[i] || a[i + 1] !== b[i + 1] || a[i + 2] !== b[i + 2]) ch++; if (l < 12) { dark++; if (a[i] === b[i] && a[i + 2] === b[i + 2]) darkKept++; } }
          return [ch, a.length / 3, dark, darkKept]; }""")
        # moves and behaviour
        await pg.evaluate("() => { W('work', 'Moves').on(); W('work', 'Run').on(); W('work', 'Hunts you').on(); W('work', 'Forest').on(); SL('work')[0].set(1.4); return 1; }")
        await pg.wait_for_timeout(200); await settle()
        out["moves"] = await pg.evaluate("() => [D.WS.Q.cur, D.WS.R.temper, D.WS.R.lives.join('+'), D.WS.R.speed].join(' ')")
        # name it, save it, start again, load it back
        await pg.evaluate("() => { W('work', 'File').on(); W('work', 'Tap to name it').on(); return 1; }")
        out["nameKeyboard"] = await pg.evaluate("() => D.VRUI.stage + ' ' + D.VRUI.keyFor")
        await pg.evaluate("() => { W('tag', 'Clear').on(); for (const ch of 'HORNWOLF') W('tag', ch).on(); W('tag', 'OK').on(); return 1; }")
        out["named"] = await pg.evaluate("() => D.VRUI.stage + ' ' + D.WS.R.name + ' ' + D.WS.tab")
        await pg.evaluate("() => { W('work', 'Save').on(); return 1; }")
        await until("() => /Saved/.test(D.WS.status) && D.WS.saved && D.WS.saved.length > 0", 10)
        out["saved"] = await pg.evaluate("() => D.WS.status + ' | ' + (D.WS.saved || []).map(s => s.name).join(',')")
        out["serverHas"] = sorted(STORE.keys())
        await pg.evaluate("() => { W('work', 'New').on(); return 1; }"); await settle()
        out["afterNew"] = await pg.evaluate("() => [D.WS.R.kit.length, D.WS.R.name, Object.keys(D.WS.R.parts).length].join(' ')")
        await pg.evaluate("() => { W('work', 'HORNWOLF').on(); return 1; }")
        await until("() => /Loaded/.test(D.WS.status)", 10); await settle()
        out["loaded"] = await pg.evaluate("() => [D.WS.status, D.WS.R.kit.length, D.WS.R.parts.head.size, D.WS.R.colors.body, D.WS.kitObjs.length].join(' ')")
        if OUT:
            await pg.evaluate("() => { W('work', 'Parts').on(); D.WS.clip = 'Idle'; D.WS.dirty = true; return 1; }"); await settle()
            await pg.evaluate("() => { D.WS.turn = .9; tick(3); return 1; }")
            save("t245_hornwolf.jpg", await pg.evaluate("() => frame()"))
        # every animal and dinosaur builds, as it is and changed (longer legs, neck and tail, bigger head, horns, a sail and spikes)
        bases = await pg.evaluate("() => D.WS_BASES.slice()")
        rows, bad = [], []
        for k in bases:
            await pg.evaluate(f"() => {{ D.wsBase('{k}'); D.WS.R.colors = {{}}; return 1; }}")
            ok1 = await until(f"() => {{ tick(1); return !!D.QDINO.models['{k}'] && !D.WS.dirty && !!D.WS.Q && D.WS.R.base === '{k}'; }}", 40)
            a = await pg.evaluate("() => { const e = D.WS.Mx.ext.all; return [e.u[0], e.u[1] - e.u[0], D.WS.F.s, D.WS.sizeTxt]; }") if ok1 else None
            await pg.evaluate("""() => { D.WS.R.parts = { front: { len: 1.3 }, back: { len: 1.3 }, neck: { len: 1.4 }, tail: { len: 1.4 }, head: { size: 1.25 } };
              D.WS.R.kit = [{ type: 'horns', size: 1, len: 1 }, { type: 'sail', size: 1, len: 1 }, { type: 'spikes', size: 1, len: 1 }]; D.WS.dirty = true; return 1; }""")
            await pg.wait_for_timeout(150); ok2 = await settle()
            c = await pg.evaluate("() => { const e = D.WS.Mx.ext.all; return [e.u[0], e.u[1] - e.u[0], D.WS.Mx.geo.attributes.position.array.some(isNaN), D.WS.kitObjs.length, Object.keys(D.WS.Mx.clips).length]; }") if ok2 else None
            good = bool(ok1 and ok2 and a and c and a[2] > 0 and abs(c[0] - a[0]) < a[1] * .002 and not c[2] and c[3] >= 3 and c[1] > a[1] * .98)
            rows.append(f"{k}: {a[3] if a else '?'} -> {round(c[1] / a[1], 2) if a and c else '?'}x tall, {c[3] if c else '?'} parts")
            if not good: bad.append([k, a, c])
        out["bases"] = len(bases); out["basesBad"] = bad
        print("\n".join(rows), flush=True)
        # a few made-up creatures, for the pictures
        if OUT:
            for nm, R in (("t245_sailback.jpg", {"base": "trex", "parts": {"neck": {"len": 1.3}, "tail": {"len": 1.2}, "head": {"size": 1.1}}, "colors": {"body": 0x3c5a2a, "belly": 0xd8c8a0},
                                                  "kit": [{"type": "sail", "size": 1.1, "len": 1}, {"type": "spikes", "size": 1.2, "len": 1}, {"type": "crest", "size": 1, "len": 1}]}),
                          ("t245_tuskbear.jpg", {"base": "bear", "parts": {"front": {"len": 1.25}, "head": {"size": 1.15, "len": 1.2}}, "colors": {"body": 0x5a3a22},
                                                 "kit": [{"type": "tusks", "size": 1.2, "len": 1}, {"type": "plates", "size": .8, "len": 1}]}),
                          ("t245_longneck.jpg", {"base": "horse", "parts": {"neck": {"len": 2.2}, "front": {"len": 1.35}, "back": {"len": 1.2}, "head": {"size": .9}}, "colors": {"body": 0xc89a3a, "legs": 0x5a3a22},
                                                 "kit": [{"type": "antlers", "size": 1, "len": 1}, {"type": "mane", "size": 1, "len": 1.2}]})):
                await pg.evaluate(f"""() => {{ const r = {json.dumps(R)}; D.wsBase(r.base); Object.assign(D.WS.R, r); D.WS.dist = 0; D.WS.turn = .75; D.WS.dirty = true; return 1; }}""")
                await until(f"() => {{ tick(1); return !D.WS.dirty && !!D.WS.Q && D.WS.R.base === '{R['base']}'; }}", 40); await pg.evaluate("() => { tick(3); return 1; }")
                save(nm, await pg.evaluate("() => frame()"))
        # leaving: the world's light and fog come back; locking hides Dev Mode
        await pg.evaluate("() => { W('work', 'Dev menu').on(); return 1; }")
        out["lightBack"] = await pg.evaluate("() => [D.hemi.intensity, D.sunL.intensity, !!D.scene.fog]") == light0
        await pg.evaluate("() => { W('dev', 'Lock Dev Mode').on(); return 1; }")
        out["locked"] = await pg.evaluate("() => [D.DEV.ok, D.VRUI.stage, !W('mode', 'Dev'), String(localStorage.getItem('jt-dev'))].join(' ')")
        print(json.dumps(out))
        ok = (out["devHidden"] and out["keyboard"] == "tag dev" and "isn't right" in out["wrongKey"] and "false" in out["wrongKey"] and out["unlocked"].startswith("true dev 1") and out["devButton"]
              and out["stage"].startswith("work") and out["wolfBuilt"] and out["workLight"][1] is False and out["taller"] > 1.12 and out["headBigger"] > 1.35 and out["feetOnGround"] < .002 and not out["nan"]
              and out["footGap"][1] <= out["footGap"][0] + .06 and out["picked"] == "head" and out["parts"].startswith("8 ") and " true " in out["parts"] and "8 parts" in out["parts"]
              and out["recolour"] == 0x3a4a6a and out["coat"][0] > out["coat"][1] * .05 and out["coat"][2] > 0 and out["coat"][3] == out["coat"][2]
              and out["moves"].startswith("Run hunts forest 1.4") and out["nameKeyboard"] == "tag name" and out["named"] == "work HORNWOLF file" and "Saved: HORNWOLF" in out["saved"] and "HORNWOLF" in out["saved"].split("|")[1]
              and out["serverHas"] == ["creature:HORNWOLF"] and out["afterNew"] == "0  0" and out["loaded"].startswith("Loaded: HORNWOLF 8 1.6 " + str(0x3a4a6a)) and not out["basesBad"]
              and out["lightBack"] and out["locked"] == "false mode true null" and not errs)
        print("errors:", errs[:5] or ("none" if ok else "CHECKS FAILED")); await b.close(); return ok
try: res = asyncio.run(main())
finally: srv.shutdown()
sys.exit(0 if res else 1)
