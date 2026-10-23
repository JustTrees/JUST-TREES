"""2.68: red-gun tools on the off-hand X. Only when fully decked out (every gun red, 10 grenades; PvP also full health + shield) does X
switch the tool of what you hold: AK flashlight (a beam and a pool of light where it lands), pistol laser (a line and a dot on what
it points at), SMG thermal mini-sight (a little thermal screen: warm bodies glow), bow flaming arrows (a fire where they land),
sniper/binoculars thermal. Others see your flashlight / laser (sent with your pose). Served over http (the pack guns load).
Usage: python3 dev/test_268.py dbg.html"""
import os, sys, asyncio, json, subprocess, shutil, tempfile, time
from playwright.async_api import async_playwright
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
srvdir = tempfile.mkdtemp(); shutil.copy(sys.argv[1], os.path.join(srvdir, "dbg.html"))
for d in ("models", "sounds"): os.symlink(os.path.join(REPO, d), os.path.join(srvdir, d))
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8798", "--bind", "127.0.0.1"], cwd=srvdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2)
JS = """async () => { const T = D.THREE, o = {}; window.FREEZE = true;
  D.setSeed(5); D.setVR(true); D.setMode('pvp'); Object.assign(D.set, { size: 'large', teams: 'solo', zone: 'off', capture: 'off', weather: 'clear', hour: 23, lat: 40, density: .3 }); D.generate(); D.state = 'play';
  const V = D.vr, full = () => { V.own = { hunt: 5, ar: 5, smg: 5, pistol: 5 }; V.nades = 10; D.MP.hp = 100; D.MP.sh = 100; D.MP.dead = 0; };
  const X = () => { D.toolTick({ a: 1 }); D.toolTick({ a: 0 }); };
  const hold = (kind, e, t) => { V.weapon = kind; V.scoped = false; V.binos = false; V.nadeMode = V.flareMode = V.bowMode = false; const G = D.vrGun(); G.visible = true;
    G.position.copy(e); G.quaternion.setFromRotationMatrix(new T.Matrix4().lookAt(e, t, new T.Vector3(0, 1, 0))); G.updateMatrixWorld(true); V.head.copy(e).add(new T.Vector3(0, .07, 0)); return G; };
  // a clear line of sight 25 m long
  let rs = 11; const rr = () => (rs = (rs * 16807) % 2147483647) / 2147483647; let sp = null;
  for (let k = 0; k < 3000 && !sp; k++) { const a = rr() * 6.28, x = (rr() - .5) * 400, z = (rr() - .5) * 400, x2 = x + Math.cos(a) * 25, z2 = z + Math.sin(a) * 25;
    const e = new T.Vector3(x, D.H(x, z) + 1.6, z), t = new T.Vector3(x2, D.H(x2, z2) + .3, z2);
    if (D.okSpot(x, z) && D.okSpot(x2, z2) && D.castShot(e, t.clone().sub(e).normalize(), e.distanceTo(t) + 3).kind) sp = [e, t, a]; }
  o.spot = !!sp; if (!sp) return o; const [eye, tgt, a] = sp;
  for (const k of ['ar', 'pistol', 'smg']) { D.qgunFor(k, 5); } for (let i = 0; i < 100 && !(D.QGUN.models.ar_5 && D.QGUN.models.pistol_5 && D.QGUN.models.smg_5); i++) await new Promise(r => setTimeout(r, 100));
  // not decked out: X does nothing
  V.own = { hunt: 5, ar: 5, smg: 4, pistol: 5 }; V.nades = 10; D.MP.hp = 100; D.MP.sh = 100; let G = hold('ar', eye, tgt);
  X(); o.offWhenNotFull = D.TOOL.on.ar === false;
  // decked out: X turns the AK's flashlight on
  full(); G = hold('ar', eye, tgt); X(); o.arOn = D.TOOL.on.ar; D.toolTick({ a: 0 });
  const F = D.TOOL.fx; o.beam = !!(F && F.beam.visible); o.pool = !!(F && F.pool.visible);
  const hd = D.aimDist(G.localToWorld(new T.Vector3(...D.GUNSPOT.ar.muzzle)), new T.Vector3(0, 0, -1).applyQuaternion(G.quaternion), 60);
  o.poolAt = F ? +(F.pool.position.distanceTo(G.localToWorld(new T.Vector3(...D.GUNSPOT.ar.muzzle))) - hd).toFixed(2) : null; o.net = D.toolNet();
  D.MP.sh = 40; D.toolTick({ a: 0 }); o.darkWhenHurt = !F.beam.visible; D.MP.sh = 100;
  X(); o.arOff = D.TOOL.on.ar === false && !F.beam.visible;
  // the pistol's laser: a line out to what it points at, and the dot there
  G = hold('pistol', eye, tgt); X(); o.pistolOn = D.TOOL.on.pistol; o.laser = F.laser.visible; o.dot = F.dot.visible; o.net2 = D.toolNet();
  const mz = G.localToWorld(new T.Vector3(...D.GUNSPOT.pistol.muzzle)), ld = D.aimDist(mz, new T.Vector3(0, 0, -1).applyQuaternion(G.quaternion), 160);
  o.laserLen = +(F.laser.scale.z - ld).toFixed(2); o.dotAt = +(F.dot.position.distanceTo(mz) - ld).toFixed(2);
  // someone else's flashlight: on their gun
  const R = {}, RG = new T.Group(); RG.position.copy(eye); RG.quaternion.copy(G.quaternion); D.scene.add(RG); RG.updateMatrixWorld(true);
  D.toolRemote(R, { alive: true, g: { k: 'ar' }, tl: 1 }, RG); o.remoteBeam = !!(R.tfx && R.tfx.beam.visible);
  D.toolRemote(R, { alive: true, g: { k: 'ar' }, tl: 0 }, RG); o.remoteOff = !R.tfx.beam.visible;
  // the SMG's thermal mini-sight: a bot standing in front glows on it
  D.vbFit(); const B = D.VB.list[0]; for (const O of D.VB.list) if (O !== B) { O.alive = false; O.x = 1e5; }
  const bt = eye.clone().lerp(tgt, .6); D.vbJoin(B, true); B.alive = true; B.x = bt.x; B.z = bt.z; B.y = D.H(B.x, B.z);
  for (let w = 0; w < 120 && !(B.C && B.C.top); w++) { await new Promise(r => setTimeout(r, 150)); B.thinkT = 1e9; B.mv = { x: B.x, z: B.z, spd: 0, crouch: 0 }; B.cool = 1e9; D.vbTick(1 / 30); }
  for (let i = 0; i < 10; i++) { B.thinkT = 1e9; B.mv = { x: B.x, z: B.z, spd: 0, crouch: 0 }; B.cool = 1e9; D.vbTick(1 / 30); }
  const se = eye.clone(), st = new T.Vector3(B.x, B.y + 1.1, B.z); G = hold('smg', se, st); X(); o.smgOn = D.TOOL.on.smg;
  const M = G.userData.tsight; o.sight = !!(M && M.visible);
  M.updateMatrixWorld(true); V.head.copy(M.children[0].getWorldPosition(new T.Vector3())).add(new T.Vector3(0, 0, 0).addScaledVector(new T.Vector3(0, 0, 1).applyQuaternion(G.quaternion), .14));
  D.TOOL.rtT = 0; D.THERM.hotT = 0; D.toolPrep(); const S = D.TOOL.sight, N = S.N, px = new Uint8Array(N * N * 4); D.renderer.readRenderTargetPixels(S.rt, 0, 0, N, N, px);
  let hot = 0; for (let i = 0; i < px.length; i += 4) if (px[i] > 220 && px[i + 1] < 40 && px[i + 2] > 220) hot++; o.sightHot = hot; o.sightLive = S.mat.uniforms.uLive.value;
  V.head.copy(se).add(new T.Vector3(3, 0, 0)); D.toolPrep(); o.sightIdleFar = S.mat.uniforms.uLive.value === 0;
  // switching guns: the other gun's tool stays as you left it
  G = hold('ar', eye, tgt); D.toolTick({ a: 0 }); o.smgSightHiddenOnAr = !M.visible; o.arStillOff = !F.beam.visible;
  // the bow (Hunting): flaming arrows, and a fire where one lands
  D.setMode('hunt'); full(); V.bowMode = true; V.gunOut = false; if (V.gun) V.gun.visible = false; X(); o.bowOn = D.TOOL.on.bow;
  const fwd = tgt.clone().sub(eye).normalize(); D.bowShoot(eye.clone(), eye.clone().addScaledVector(fwd, -.6), 1, 'R', 'L');
  const Ar = D.ARROWS[D.ARROWS.length - 1]; o.arrowFire = !!(Ar && Ar.fire && Ar.flame);
  for (let i = 0; i < 200 && D.ARROWS.length; i++) D.arrowsTick(1 / 60);
  o.fires = D.FIRES.length; for (let i = 0; i < 400 && D.FIRES.length; i++) D.firesTick(1 / 60); o.firesOut = D.FIRES.length === 0;
  return o; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required"])
        pg = await (await b.new_context()).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto("http://127.0.0.1:8798/dbg.html", timeout=120000); await pg.wait_for_timeout(800)
        r = await pg.evaluate(JS); print(json.dumps(r))
        ok = r.get("spot") and r["offWhenNotFull"] and r["arOn"] and r["beam"] and r["pool"] and abs(r["poolAt"]) < 2 and r["net"] == 1 and r["darkWhenHurt"] and r["arOff"] \
             and r["pistolOn"] and r["laser"] and r["dot"] and r["net2"] == 2 and abs(r["laserLen"]) < .1 and abs(r["dotAt"]) < .1 and r["remoteBeam"] and r["remoteOff"] \
             and r["smgOn"] and r["sight"] and r["sightLive"] == 1 and r["sightHot"] > 20 and r["sightIdleFar"] and r["smgSightHiddenOnAr"] and r["arStillOff"] \
             and r["bowOn"] and r["arrowFire"] and r["fires"] >= 1 and r["firesOut"]
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
try: asyncio.run(main())
finally: srv.terminate(); shutil.rmtree(srvdir, ignore_errors=True)
