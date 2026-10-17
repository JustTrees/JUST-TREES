"""2.42: VR bodies: top half from the headset, legs step the way you move (sideways, backward), ducking crouches the whole body.\n(2.39) in VR your own body is your character: it stands under your eyes (head, hair and eyes left out, so you never see inside them), its arms
reach your gloves, its legs walk/crouch with you, it changes when you change your look, and it hides in the menus. Pictures: looking down, from the side.
Usage: python3 dev/test_239.py dbg.html [outdir]   (served over http)"""
import os, sys, asyncio, json, subprocess, time, shutil, tempfile, base64
from playwright.async_api import async_playwright
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
srvdir = tempfile.mkdtemp(); shutil.copy(sys.argv[1], os.path.join(srvdir, "dbg.html")); os.symlink(os.path.join(REPO, "models"), os.path.join(srvdir, "models"))
OUT = sys.argv[2] if len(sys.argv) > 2 else None
if OUT and OUT.endswith(".png"): OUT = os.path.dirname(OUT)
PORT = 8786
srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=srvdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2)
SETUP = """() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setSeed(4); D.setVR(true); D.setVRON(true);
  for (const el of document.body.children) if (el.tagName !== 'CANVAS') el.style.display = 'none';
  D.setMode('hunt'); Object.assign(D.set, { size: 'medium', lat: 45, hemi: 1, month: 6, hour: 12, weather: 'clear', rough: .2 }); D.generate(); D.state = 'play';
  const T = D.THREE, V = D.vr; window.T = T; V.on = true; V.yaw = 0; V.cl = null; V.goodX = undefined; V.ox = D.P.x; V.oz = D.P.z; V.oy = D.P.y; V.hCal = true;
  window.L = { head: new T.Vector3(0, 1.7, 0), R: new T.Vector3(.25, 1.15, -.3), Lh: new T.Vector3(-.25, 1.15, -.3) };
  window.pad = { R: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 }, L: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 } };
  const toW = v => v.clone().applyAxisAngle(new T.Vector3(0, 1, 0), V.yaw).add(new T.Vector3(V.ox, V.oy, V.oz));
  window.qs = { R: new T.Quaternion().setFromEuler(new T.Euler(-.4, 0, 0)), L: new T.Quaternion().setFromEuler(new T.Euler(-.4, 0, 0)), head: new T.Quaternion() };
  V.readInputs = () => ({ head: toW(L.head), headQ: qs.head.clone(), hands: { right: Object.assign({ pos: toW(L.R), q: qs.R.clone(), rayPos: toW(L.R), rayQ: qs.R.clone() }, pad.R), left: Object.assign({ pos: toW(L.Lh), q: qs.L.clone(), rayPos: toW(L.Lh), rayQ: qs.L.clone() }, pad.L) } });
  window.frames = n => { for (let i = 0; i < n; i++) { D.vrTick(1 / 60); if (!V.climbing) D.update(1 / 60); D.vrAfterMove(1 / 60); } };
  window.shot = (pos, look, fov) => { const c = D.camera, r = D.renderer; r.setSize(900, 560); c.fov = fov; c.aspect = 900 / 560; c.updateProjectionMatrix(); c.position.copy(pos); c.lookAt(look); c.updateMatrixWorld(); D.cullTiles(); r.render(D.scene, c); return r.domElement.toDataURL('image/jpeg', .86); };
  D.vr.gunOut = false; frames(5); return 1; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 900, "height": 560})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(f"http://127.0.0.1:{PORT}/dbg.html", timeout=120000); await pg.wait_for_timeout(800)
        await pg.evaluate(SETUP); imgs = {}
        await pg.wait_for_function("() => { frames(2); return !!D.vr.meC || D.CHAR.failed > 0; }", timeout=120000)
        imgs = {}; r = {}
        if os.environ.get("SHOWHEAD"):                                   # pictures for Ron: put the head back on (only you never see it)
            await pg.evaluate("() => { const C = D.vr.meC; C.by.Head.scale.setScalar(1); C.meshes.forEach(m => m.visible = true); return 1; }")
        cam = "(dx, dy, dz, fov) => { const h = D.vr.I.head; return shot(h.clone().add(new T.Vector3(dx, dy, dz)), h.clone().add(new T.Vector3(0, -.75, 0).add(new T.Vector3(0, 0, 0))), fov || 45); }"
        await pg.evaluate("() => { window.side = " + cam + "; return 1; }")
        def meas(name): return pg.evaluate("""(n) => { const C = D.vr.meC, h = D.vr.I.head, by = C.by, w = b => by[b].getWorldPosition(new T.Vector3());
            const fl = w('foot_l'), fr = w('foot_r'), nk = w('neck_01'), pv = w('pelvis');
            return { anim: C.cur, ts: C.curA ? +C.curA.timeScale.toFixed(2) : 0, feetY: [+(fl.y - D.P.y).toFixed(2), +(fr.y - D.P.y).toFixed(2)], neckBelow: +(h.y - nk.y).toFixed(2), neckBack: +Math.hypot(h.x - nk.x, h.z - nk.z).toFixed(2), pelvisUp: +(pv.y - D.P.y).toFixed(2),
              legTurn: +((C.legYaw - D.P.yaw) * 57.3).toFixed(0) }; }""", name)
        await pg.evaluate("() => { frames(40); return 1; }")
        r["stand"] = await meas("stand"); imgs["stand"] = await pg.evaluate("() => side(2.4, -.4, -1.2)")
        for nm, sx, sy in [("forward", 0, -1), ("sideways", 1, 0), ("backward", 0, 1), ("diagonal", .7, -.7)]:
            await pg.evaluate(f"() => {{ pad.L.sx = {sx}; pad.L.sy = {sy}; frames(45); return 1; }}")
            r[nm] = await meas(nm); imgs[nm] = await pg.evaluate("() => side(2.6, -.4, -.6, 40)")
            await pg.evaluate("() => { pad.L.sx = 0; pad.L.sy = 0; frames(40); return 1; }")
        for nm, hy, hz in [("duck", 1.25, 0), ("crouch", .95, 0), ("lowcrouch", .75, 0), ("bend", 1.2, -.35)]:
            await pg.evaluate(f"() => {{ L.head.y = {hy}; L.head.z = {hz}; L.R.y = L.Lh.y = {hy} - .45; frames(30); return 1; }}")
            r[nm] = await meas(nm); imgs[nm] = await pg.evaluate("() => side(2.2, .2, -1.6, 45)")
        await pg.evaluate("() => { pad.L.sy = -1; frames(40); return 1; }")
        r["crouchwalk"] = await meas("cw"); imgs["crouchwalk"] = await pg.evaluate("() => side(2.6, 0, 0, 40)")
        await pg.evaluate("() => { pad.L.sy = 0; L.head.set(0, 1.7, 0); L.R.y = L.Lh.y = 1.15; frames(40); return 1; }")
        imgs["down"] = await pg.evaluate("() => { const h = D.vr.I.head; return shot(h, h.clone().add(new T.Vector3(0, -1, -.55)), 100); }")
        await pg.evaluate("() => { pad.L.sy = -1; frames(30); return 1; }")
        imgs["down_run"] = await pg.evaluate("() => { const h = D.vr.I.head; return shot(h, h.clone().add(new T.Vector3(0, -1, -.55)), 100); }")
        if OUT:
            for k, u in imgs.items(): open(os.path.join(OUT, f"t242_{k}.jpg"), "wb").write(base64.b64decode(u.split(",")[1]))
        print(json.dumps(r))
        ok = all(abs(v) < .16 for k in ("stand", "duck", "crouch", "lowcrouch", "bend") for v in r[k]["feetY"]) and all(min(r[k]["feetY"]) < .25 for k in ("forward", "sideways", "backward", "diagonal")) \
             and r["backward"]["ts"] < 0 and abs(r["sideways"]["legTurn"]) > 40 and all(.05 < r[k]["neckBelow"] < .4 for k in ("stand", "crouch", "lowcrouch", "bend")) \
             and r["lowcrouch"]["pelvisUp"] < r["stand"]["pelvisUp"] - .3 and not errs
        print("errors", errs[:5] or "none"); print("PASS" if ok else "FAIL"); await b.close(); return ok
try: res = asyncio.run(main())
finally: srv.terminate()
sys.exit(0 if res else 1)
