"""2.64: the thermal scope and the new sounds.
Thermal: only with the red sniper up at your eye, every gun red (5 stars) and all 10 grenades; in PvP also full health and full shield
(Hunting doesn't ask for those). The thermal picture: black with red outlines where the land and trees break, warm bodies (bots, animals,
dinosaurs) glowing, and nothing glows through a solid wall. Sounds (served over http): each gun's two Free Firearm Library takes and the
Kenney hit / kill sounds load and play; a gun picks one of its takes.
Usage: python3 dev/test_264.py dbg.html"""
import os, sys, asyncio, json, subprocess, shutil, tempfile, time
from playwright.async_api import async_playwright
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
srvdir = tempfile.mkdtemp(); shutil.copy(sys.argv[1], os.path.join(srvdir, "dbg.html"))
for d in ("models", "sounds"): os.symlink(os.path.join(REPO, d), os.path.join(srvdir, d))
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8797", "--bind", "127.0.0.1"], cwd=srvdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2)
JS = """async () => { const T = D.THREE, o = {}; window.FREEZE = true;
  D.setSeed(5); D.setVR(true); D.setMode('pvp'); Object.assign(D.set, { size: 'large', teams: 'solo', zone: 'off', capture: 'off', weather: 'clear', hour: 13, lat: 66, density: .3 }); D.generate(); D.state = 'play';
  // the rule
  const V = D.vr, full = () => { V.own = { hunt: 5, ar: 5, smg: 5, pistol: 5 }; V.nades = 10; D.MP.hp = 100; D.MP.sh = 100; D.MP.dead = 0; V.scoped = true; V.gunKind = 'hunt'; };
  full(); o.okFull = D.thermalOk();
  full(); V.own.smg = 4; o.okGun4 = D.thermalOk();
  full(); V.nades = 9; o.okNades9 = D.thermalOk();
  full(); D.MP.sh = 60; o.okHurtPvp = D.thermalOk();
  full(); V.scoped = false; o.okNotScoped = D.thermalOk();
  full(); V.gunKind = 'ar'; o.okOtherGun = D.thermalOk();
  D.setMode('hunt'); full(); D.MP.sh = 0; D.MP.hp = 40; o.okHunt = D.thermalOk(); D.setMode('pvp');
  // the picture: two bots in the open
  D.vbFit(); const [A, B] = D.VB.list; for (const O of D.VB.list) if (O !== A && O !== B) { O.alive = false; O.x = 1e5; }
  let rs = 9; const rr = () => (rs = (rs * 16807) % 2147483647) / 2147483647; let sp = null;
  for (let k = 0; k < 3000 && !sp; k++) { const a = rr() * 6.28, x = (rr() - .5) * 500, z = (rr() - .5) * 500, x2 = x + Math.cos(a) * 120, z2 = z + Math.sin(a) * 120;
    const e = new T.Vector3(x, D.H(x, z) + 3, z), t = new T.Vector3(x2, D.H(x2, z2) + 1.2, z2);
    if (D.okSpot(x, z) && D.okSpot(x2, z2) && D.castShot(e, t.clone().sub(e).normalize(), e.distanceTo(t) - 3).kind === null) sp = [e, t, a]; }
  o.spot = !!sp; if (!sp) return o; const [eye, tgt, a] = sp;
  D.vbJoin(A, true); D.vbJoin(B, true); A.alive = B.alive = true; A.x = tgt.x; A.z = tgt.z; A.y = D.H(A.x, A.z);
  B.x = tgt.x - Math.sin(a) * 4; B.z = tgt.z + Math.cos(a) * 4; B.y = D.H(B.x, B.z);
  for (let w = 0; w < 120 && !(A.C && A.C.top && B.C && B.C.top); w++) { await new Promise(r => setTimeout(r, 150)); for (const X of [A, B]) { X.thinkT = 1e9; X.mv = { x: X.x, z: X.z, spd: 0, crouch: 0 }; X.cool = 1e9; } D.vbTick(1 / 30); }
  for (let i = 0; i < 10; i++) { for (const X of [A, B]) { X.thinkT = 1e9; X.mv = { x: X.x, z: X.z, spd: 0, crouch: 0 }; X.cool = 1e9; } D.vbTick(1 / 30); }
  V.head.copy(eye); const q = new T.Quaternion().setFromRotationMatrix(new T.Matrix4().lookAt(eye, tgt, new T.Vector3(0, 1, 0))), k = Math.tan(36 * Math.PI / 180) / Math.tan(5.5 * Math.PI / 360);
  const r = D.renderer, rt0 = () => D.THERM.rt;
  const count = () => { const rt = D.THERM.rt, N = rt.width, px = new Uint8Array(N * N * 4); r.readRenderTargetPixels(rt, 0, 0, N, N, px); let n = 0; for (let i = 0; i < px.length; i += 4) if (px[i] > 220 && px[i + 1] < 40 && px[i + 2] > 220) n++; return n; };
  D.THERM.hotT = 0; D.thermPrep(q, k); o.hot = count(); o.hotList = D.THERM.hot.length;
  // a solid wall between you and them: nothing glows through it
  const wall = new T.Mesh(new T.BoxGeometry(6, 6, .3), new T.MeshBasicMaterial({ color: 0x404040 })); wall.position.copy(eye).lerp(tgt, 20 / eye.distanceTo(tgt)); wall.lookAt(eye); D.scene.add(wall); wall.updateMatrixWorld();
  D.thermPrep(q, k); o.hotBehindWall = count(); D.scene.remove(wall);
  // the overlay draws the thermal picture with no errors
  const ov = D.zoomOverlay(), U = ov.material.uniforms, c = D.camera; c.fov = 90; c.aspect = 1; c.updateProjectionMatrix(); r.setSize(300, 300);
  const sc = new T.Scene(); sc.add(ov); ov.visible = true; r.render(sc, c); D.scene.add(ov); ov.visible = false;
  const g = r.getContext(), pix = new Uint8Array(4); g.readPixels(150, 150, 1, 1, g.RGBA, g.UNSIGNED_BYTE, pix); o.overlayRenders = true;
  // the sounds
  D.initSound && D.initSound(); D.gunSndLoad && D.gunSndLoad();
  for (let w = 0; w < 80; w++) { await new Promise(r => setTimeout(r, 150)); if (D.DSND && D.DSND.buf['guns/ffl_sniper_b'] && D.DSND.buf['fx/big_bell']) break; }
  const B2 = D.DSND ? D.DSND.buf : {};
  o.gunsLoaded = ['sniper', 'ar', 'smg', 'pistol'].flatMap(g => ['ffl_' + g, 'ffl_' + g + '_b']).filter(n => B2['guns/' + n]).length;
  o.fxLoaded = D.FX_NAMES ? D.FX_NAMES.filter(n => B2['fx/' + n]).length : -1;
  const picks = new Set(); for (let i = 0; i < 40; i++) picks.add(D.shotN('hunt')); o.picks = [...picks].sort();
  o.fxPlays = D.fxPlay ? D.fxPlay('kill_3', .1) : null;
  return o; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required"])
        pg = await (await b.new_context()).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto("http://127.0.0.1:8797/dbg.html", timeout=120000); await pg.wait_for_timeout(800)
        r = await pg.evaluate(JS); print(json.dumps(r))
        ok = r["okFull"] and not r["okGun4"] and not r["okNades9"] and not r["okHurtPvp"] and not r["okNotScoped"] and not r["okOtherGun"] and r["okHunt"] \
             and r.get("spot") and r["hot"] > 150 and r["hotBehindWall"] == 0 and r["gunsLoaded"] == 8 and r["fxLoaded"] == 13 and r["picks"] == ["ffl_sniper", "ffl_sniper_b"] and r["fxPlays"]
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
try: asyncio.run(main())
finally: srv.terminate(); shutil.rmtree(srvdir, ignore_errors=True)
