"""2.39: in VR your own body is your character: it stands under your eyes (head, hair and eyes left out, so you never see inside them), its arms
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
        r = await pg.evaluate("""() => { frames(30); const V = D.vr, C = V.meC, out = {};
          out.visible = C.top.visible; out.soldierHidden = !V.avatar || !V.avatar.group.visible;
          out.hairEyesHidden = C.meshes.filter(m => m.userData.noHit || m.userData.tex === 'eyes').every(m => !m.visible);
          const head = V.I.head, neck = C.by.neck_01.getWorldPosition(new T.Vector3());
          out.neckBelowEyes = +(head.y - neck.y).toFixed(2); out.neckBehind = +(head.z - neck.z).toFixed(2);   /* you look toward -z */
          const wr = C.by.hand_r.getWorldPosition(new T.Vector3()), gl = V.I.hands.right.pos; out.wristToGlove = +wr.distanceTo(gl).toFixed(3);
          out.idle = C.cur;
          return out; }""")
        imgs["down"] = await pg.evaluate("() => { const h = D.vr.I.head; return shot(h, h.clone().add(new T.Vector3(0, -1, -.55)), 100); }")
        imgs["side"] = await pg.evaluate("() => { const h = D.vr.I.head; return shot(h.clone().add(new T.Vector3(2.2, -.5, -.9)), h.clone().add(new T.Vector3(0, -.7, 0)), 50); }")
        # arms out wide (a reach longer than the arm): the forearm stretches to the glove
        r["reach"] = await pg.evaluate("""() => { L.R.set(.78, 1.45, -.15); L.Lh.set(-.78, 1.45, -.15); frames(3); const C = D.vr.meC, V = D.vr;
          return { wrist: +C.by.hand_r.getWorldPosition(new T.Vector3()).distanceTo(V.I.hands.right.pos).toFixed(3), stretch: +Math.max(...C.by.lowerarm_r.scale.toArray()).toFixed(2) }; }""")
        imgs["reach"] = await pg.evaluate("() => { const h = D.vr.I.head; return shot(h.clone().add(new T.Vector3(0, -.3, -2.6)), h.clone().add(new T.Vector3(0, -.5, 0)), 60); }")
        # crouch down for real: the body crouches
        r["crouch"] = await pg.evaluate("() => { L.R.set(.25, .75, -.3); L.Lh.set(-.25, .75, -.3); L.head.y = 1.0; frames(40); return D.vr.meC.cur; }")
        imgs["crouch"] = await pg.evaluate("() => { const h = D.vr.I.head; return shot(h.clone().add(new T.Vector3(2.2, 0, -.9)), h.clone().add(new T.Vector3(0, -.4, 0)), 50); }")
        L0 = await pg.evaluate("() => { L.head.y = 1.7; L.R.set(.25, 1.15, -.3); L.Lh.set(-.25, 1.15, -.3); frames(20); return D.vr.meC.cur; }")
        # walk forward with the stick
        r["walk"] = await pg.evaluate("() => { pad.L.sy = -1; frames(50); const c = D.vr.meC.cur; pad.L.sy = 0; frames(40); return c; }")
        # change your look: the body changes
        k0 = await pg.evaluate("() => { const k0 = D.vr.meC.key; D.lookSet({ s: 1 - D.look.s, o: 2 }); frames(3); return k0; }")
        await pg.wait_for_function("(k0) => { frames(2); return !!D.vr.meC && D.vr.meC.key !== k0; }", arg=k0, timeout=60000)
        r["relook"] = {"changed": True}
        imgs["side2"] = await pg.evaluate("() => { frames(20); const h = D.vr.I.head; return shot(h.clone().add(new T.Vector3(2.2, -.5, -.9)), h.clone().add(new T.Vector3(0, -.7, 0)), 50); }")
        # menus hide it
        r["menu"] = await pg.evaluate("() => { D.vruiOpen('pause'); const a = D.vr.meC.top.visible; D.vruiResume(); frames(2); return { inMenu: a, after: D.vr.meC.top.visible }; }")
        if OUT:
            for k, u in imgs.items(): open(os.path.join(OUT, f"t239_{k}.jpg"), "wb").write(base64.b64decode(u.split(",")[1]))
        print(json.dumps(r))
        ok = (r["visible"] and r["soldierHidden"] and r["hairEyesHidden"] and .05 < r["neckBelowEyes"] < .35 and r["neckBehind"] < -.03 and r["wristToGlove"] < .14
              and r["reach"]["wrist"] < .14 and r["crouch"] in ("Idle_Loop", "Crouch_Idle_Loop") and r["walk"] in ("Walk_Loop", "Jog_Fwd_Loop", "Sprint_Loop") and r["relook"]["changed"]
              and not r["menu"]["inMenu"] and r["menu"]["after"] and not errs)
        print("errors", errs[:5] or "none"); print("PASS" if ok else "FAIL"); await b.close(); return ok
try: res = asyncio.run(main())
finally: srv.terminate()
sys.exit(0 if res else 1)
