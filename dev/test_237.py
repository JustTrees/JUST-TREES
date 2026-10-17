"""2.37: in VR, other players and the PvP bots are people (models/chars). Each loads, stands where the player is, looks where they look,
reaches for their real hands, runs / crouches / flies laid out; a dead one turns and falls back; a headshot on the head counts as a headshot,
a shot through the hair or between the legs misses; your look goes out with your tag. Writes a picture to the folder given as the 2nd argument.
Usage: python3 dev/test_237.py dbg.html [outdir]   (served over http, like test_qdino)"""
import os, sys, asyncio, json, subprocess, time, shutil, tempfile, base64
from playwright.async_api import async_playwright
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
srvdir = tempfile.mkdtemp(); shutil.copy(sys.argv[1], os.path.join(srvdir, "dbg.html")); os.symlink(os.path.join(REPO, "models"), os.path.join(srvdir, "models"))
OUT = sys.argv[2] if len(sys.argv) > 2 else None
if OUT and OUT.endswith(".png"): OUT = os.path.dirname(OUT)
PORT = 8783
srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=srvdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2)
SETUP = """() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setSeed(4); D.setVR(true); D.vr.on = true; D.setVRON(true); D.setMode('pvp');
  Object.assign(D.set, { size: 'medium', lat: 45, hemi: 1, month: 6, hour: 12, weather: 'clear' }); D.generate(); D.state = 'play';
  const T = D.THREE; window.T = T; D.MP.on = true; D.MP.code = '1234';
  const looks = ['0.0.1.0.0.1', '1.2.0.1.2.0', '1.0.2.0.0.0', '0.1.3.2.1.0', '1.1.4.2.3.0', '0.2.2.1.4.0'];
  for (const lk of looks) D.charMake(D.lookParse(lk), 'green');
  return D.lookStr(D.MP.look); }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 1200, "height": 560})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(f"http://127.0.0.1:{PORT}/dbg.html", timeout=120000); await pg.wait_for_timeout(800)
        mine = await pg.evaluate(SETUP)
        await pg.wait_for_function("() => ['0.0.1.0.0.1', '1.2.0.1.2.0', '1.0.2.0.0.0', '0.1.3.2.1.0', '1.1.4.2.3.0', '0.2.2.1.4.0'].every(k => { const C = D.charMake(D.lookParse(k), 'green'); if (C) D.scene.remove(C.top); return !!C; }) || D.CHAR.failed > 0", timeout=120000)
        r = await pg.evaluate("""() => { const out = { failed: D.CHAR.failed }, P = D.P, now = performance.now();
          const cam = D.camera; const gy = (x, z) => D.groundAt(x, z);
          const x0 = P.x, z0 = P.z, base = gy(x0, z0);
          cam.position.set(x0, base + 1.7, z0 + 6.5); cam.lookAt(x0, base + 1.1, z0); cam.updateMatrixWorld();
          // fake players in a row in front of you, facing you
          const qFace = new T.Quaternion().setFromAxisAngle(new T.Vector3(0, 1, 0), Math.PI);   // looking toward +z (at the camera)
          const p7 = (p, q) => [p.x, p.y, p.z, q.x, q.y, q.z, q.w];
          const mk = (id, lk, x, opt) => { const L = { id, open: true, bad: false, tag: id, idx: 2, col: 1, rx: [], look: D.lookParse(lk) }; D.MP.links.set(id, L);
            const zz = z0 + (opt.z || 0), f = gy(x, zz), head = new T.Vector3(x, f + 1.62 - (opt.crouch ? .55 : 0), zz), hq = opt.hq || qFace;
            const hand = s => { const q = new T.Quaternion().setFromEuler(new T.Euler(-.3, Math.PI, 0)); return p7(new T.Vector3(x + s * .22, f + 1.15 + (opt.fly ? 2.5 : 0), zz + .38), q); };
            const fr = (t, dx) => ({ t: 's', h: p7(head.clone().add(new T.Vector3(0, 0, dx)), hq), f: f + (opt.fly ? .9 : 0), a: opt.dead ? false : true, gl: !!opt.fly, hp: 100, l: hand(1), r: hand(-1), at: now - t });
            if (opt.fly) { head.y += .9; }
            L.rx = [fr(400, opt.run ? -2.4 : 0), fr(260, opt.run ? -1.2 : 0), fr(130, 0), fr(-20, opt.run ? 1.2 : 0)];
            if (opt.dead) { L.dieBy = D.mpMyId ? D.mpMyId() : 'me'; L.dieHead = !!opt.head; }
            return L; };
          const Ls = [mk('A', '0.0.1.0.0.1', x0 - 3.4, {}), mk('B', '1.2.0.1.2.0', x0 - 1.7, { run: true, z: -4 }), mk('C', '1.0.2.0.0.0', x0, {}), mk('D', '0.1.3.2.1.0', x0 + 1.7, { crouch: true }), mk('E', '1.1.4.2.3.0', x0 + 3.4, { fly: true })];
          for (let i = 0; i < 20; i++) for (const L of Ls) D.mpRemoteTick(L, 1 / 60);
          out.people = Ls.map(L => !!(L.R && L.R.C && L.R.C.top.visible)); out.soldierHidden = Ls.every(L => L.R && L.R.S.group.visible === false);
          out.anim = Ls.map(L => L.R && L.R.C && L.R.C.cur);
          // the head looks where the player looks: head bone forward ~ toward the camera
          const C = Ls[2].R.C; const hf = new T.Vector3(0, 0, 1).applyQuaternion(C.by.Head.getWorldQuaternion(new T.Quaternion()));
          out.headFacesYou = +hf.z.toFixed(2);
          // the hands reach the controllers
          const hp = C.by.hand_r.getWorldPosition(new T.Vector3()), ctl = new T.Vector3(...Ls[2].rx[2].r.slice(0, 3));
          out.handReach = +hp.distanceTo(ctl).toFixed(3);
          // shots: at C's head, chest, between the legs, and through E's... A's hair isn't long; B's hair is long (buns): above the head
          const shoot = (to) => { const o = cam.position.clone(), d = to.clone().sub(o).normalize(); const h = D.mpHitTest(o, d, 100); return h ? { who: h.L.id, head: h.head } : null; };
          const headP = C.by.Head.getWorldPosition(new T.Vector3()).add(new T.Vector3(0, .08, 0)), chest = C.by.spine_03.getWorldPosition(new T.Vector3());
          const crotch = C.by.pelvis.getWorldPosition(new T.Vector3()).add(new T.Vector3(0, -.32, 0));
          out.shotHead = shoot(headP); out.shotChest = shoot(chest); out.shotBetweenLegs = shoot(crotch);
          const bun = Ls[1].R.C.by.Head.getWorldPosition(new T.Vector3()).add(new T.Vector3(0, .26, 0)); out.shotHairOnly = shoot(bun);
          // render
          D.renderer.setSize(1200, 560); cam.aspect = 1200 / 560; cam.updateProjectionMatrix(); D.renderer.render(D.scene, cam); out.img1 = D.renderer.domElement.toDataURL('image/jpeg', .85);
          cam.position.set(x0 - 3.4 + 1.4, base + 1.6, z0 + 1.6); cam.lookAt(x0 - 3.4, base + 1.25, z0); cam.updateMatrixWorld(); D.renderer.render(D.scene, cam); out.img3 = D.renderer.domElement.toDataURL('image/jpeg', .85);
          cam.position.set(x0, base + 1.7, z0 + 6.5); cam.lookAt(x0, base + 1.1, z0); cam.updateMatrixWorld();
          // a kill: C dies (headshot from you), then falls
          Ls[2].rx.forEach(e => e.a = false); Ls[2].dieBy = D.mpMyId(); Ls[2].dieHead = true;
          for (let i = 0; i < 90; i++) D.mpRemoteTick(Ls[2], 1 / 60);
          out.dead = { cur: Ls[2].R.C.cur, deadT: +Ls[2].R.C.deadT.toFixed(2), hit: shoot(chest) };
          D.renderer.render(D.scene, cam); out.img2 = D.renderer.domElement.toDataURL('image/jpeg', .85);
          // bots: people too
          D.spawnSquad(); const S = D.squad[0]; S.x = x0 - 1; S.z = z0 - 3; S.y = gy(S.x, S.z); S.yaw = 0; S.state = 'patrol'; S.mode = 'idle'; S.timer = 99;
          for (let i = 0; i < 10; i++) D.updateSquad(1 / 60);
          out.bot = !!(S.C && S.C.top.visible); out.botRifle = S.rifle && S.rifle.visible;
          const bc = S.C.by.spine_03.getWorldPosition(new T.Vector3()), od = cam.position.clone(), dd = bc.clone().sub(od).normalize(); const br = D.botRay(od, dd, .5); out.botHit = br[1] === S;
          // outside VR: back to soldiers
          D.setVRON(false); D.vr.on = false; for (const L of Ls) D.mpRemoteTick(L, 1 / 60); D.updateSquad(1 / 60); out.pcSoldier = !Ls[0].R.C && !S.C;
          out.lookMsg = D.lookStr(D.MP.look);
          return out; }""")
        imgs = [r.pop("img1", None), r.pop("img2", None), r.pop("img3", None)]
        if OUT:
            for i, u in enumerate(imgs):
                if u: open(os.path.join(OUT, f"t237_{i+1}.jpg"), "wb").write(base64.b64decode(u.split(",")[1]))
        print(json.dumps(r)); print("my look", mine)
        ok = (r["failed"] == 0 and all(r["people"]) and r["soldierHidden"] and r["headFacesYou"] > .7 and r["handReach"] < .12 and r["shotHead"] and r["shotHead"]["head"]
              and r["shotChest"] and not r["shotChest"]["head"] and r["shotBetweenLegs"] is None and r["shotHairOnly"] is None and (r["dead"]["hit"] is None or r["dead"]["hit"]["who"] != "C")
              and r["bot"] and r["botHit"] and r["pcSoldier"] and not errs)
        print("errors", errs[:5] or "none"); print("PASS" if ok else "FAIL"); await b.close(); return ok
try: res = asyncio.run(main())
finally: srv.terminate()
sys.exit(0 if res else 1)
