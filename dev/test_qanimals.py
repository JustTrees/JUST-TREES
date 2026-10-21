"""2.03: every hunting animal is the new pack-style model (models/animals/*.bin). Served over http (a copy opened from disk keeps the old ones).
Each four-legged one loads, sits on the hidden old one at its length, walks / runs / grazes / falls with the copied moves, and a shot at its
head counts as a head shot; the rigged ones (birds, ground birds, seal, monkey, Bigfoot, Yeti) are skinned onto the old moving parts, which
still drive them (a flapping wing moves the model's wing). Writes a picture to the folder given as the 2nd argument (optional).
Usage: python3 dev/test_qanimals.py dbg.html [outdir]"""
import os, sys, asyncio, json, subprocess, time, shutil, tempfile
from playwright.async_api import async_playwright
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
srvdir = tempfile.mkdtemp(); shutil.copy(sys.argv[1], os.path.join(srvdir, "dbg.html")); os.symlink(os.path.join(REPO, "models"), os.path.join(srvdir, "models"))
OUT = sys.argv[2] if len(sys.argv) > 2 else None
if OUT and OUT.endswith(".png"): OUT = os.path.dirname(OUT)
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8787", "--bind", "127.0.0.1"], cwd=srvdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 1300, "height": 480})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto("http://127.0.0.1:8787/dbg.html", timeout=120000); await pg.wait_for_timeout(800)
        await pg.evaluate("""() => { window.FREEZE = true; D.setSeed(5); D.setVR(true); D.setMode('hunt'); D.set.env = 'climate'; D.set.land = 'natural'; D.set.size = 'medium'; D.set.lat = 42; D.set.month = 6; D.set.weather = 'clear'; D.set.density = .5; D.generate(); D.state = 'play';
          window.__q = Object.keys(D.QA_KINDS).filter(k => k !== 'crocodile'); window.__r = ['turkey', 'roadrunner', 'heron', 'seal', 'bigfoot', 'yeti'];
          for (const k of [...window.__q, ...window.__r, 'gator', 'lion_m', 'bird', 'monkey']) D.qdinoLoad(k); }""")
        try: await pg.wait_for_function("[...window.__q, ...window.__r, 'bird', 'monkey', 'lion_m'].every(k => D.QDINO.models[k]) || D.QDINO.failed > 0", timeout=120000)
        except Exception: print("missing", await pg.evaluate("[...window.__q, ...window.__r, 'bird', 'monkey', 'lion_m'].filter(k => !D.QDINO.models[k]).join()")); raise
        r = await pg.evaluate("""() => { const out = { failed: D.QDINO.failed, bad: [] }, T = D.THREE, P = D.P, x0 = P.x, z0 = P.z, mk = {};
          let i = 0; for (const k of [...window.__q, 'crocodile']) { const A = D.addGround(k, x0 - 60 + (i % 10) * 12, z0 + 30 + Math.floor(i / 10) * 12); A.mode = 'idle'; A.timer = 99; A.speed = 0; A.want = 0; mk[k] = A; D.qdTick(A, 1 / 30, 10); i++; }
          for (const k in mk) { const A = mk[k]; if (!A.qd || A.body.visible !== false || !(A.qhit && A.qhit.some(h => h[5])) || !A.qd.F) out.bad.push(k); }
          out.croc = mk.crocodile.qf + ':' + mk.crocodile.qv;
          // moves
          const bk = mk.buck; bk.mode = 'walk'; bk.timer = 99; bk.target = [bk.x + 200, bk.z]; bk.want = bk.walk; for (let f = 0; f < 60; f++) D.updateAnimals(1 / 30); out.walk = bk.qd.cur;
          bk.want = bk.run; bk.fleeT = 5; for (let f = 0; f < 60; f++) D.updateAnimals(1 / 30); out.run = bk.qd.cur;
          const el = mk.elk; el.mode = 'graze'; el.timer = 99; el.speed = 0; el.want = 0; el.hunter = false; for (let f = 0; f < 10; f++) D.qdTick(el, 1 / 30, 10); out.eat = el.qd.cur;
          const zb = mk.zebra; D.killAnimal(zb, 30); for (let f = 0; f < 60; f++) D.updateAnimals(1 / 30); out.death = zb.qd.cur;
          // a head shot on the model's head
          const md = mk.moose; md.root.updateMatrixWorld(true); const hp = new T.Vector3().setFromMatrixPosition(md.qd.head.matrixWorld);
          const side = new T.Vector3(Math.cos(md.yaw), 0, -Math.sin(md.yaw)), o = hp.clone().add(side.clone().multiplyScalar(-15)), ray = D.animalRay(o, hp.clone().sub(o).normalize(), .5);
          out.headShot = { who: ray[1] && ray[1].kind, head: ray[2] };
          // the rigged ones
          const rg = {}; i = 0; for (const k of window.__r) { const A = D.addGround(k, x0 - 40 + i * 8, z0 - 20); A.mode = 'idle'; A.timer = 99; rg[k] = A; i++; }
          for (let f = 0; f < 5; f++) D.updateAnimals(1 / 30);
          for (const k in rg) { const A = rg[k]; if (!A.qr || !A.qrMesh || A.qrMesh.skeleton.bones.length < 2) out.bad.push(k); }
          // a bird: the old wing moves the new one
          D.spawnKind('eagle', null, 50); const bd = D.beasts[D.beasts.length - 1]; D.updateAnimals(1 / 30); out.birdQr = !!bd.qr;
          if (bd.qr) { const sk = bd.qrMesh.skeleton, w = bd.wings[1], bi = sk.bones.indexOf(w); w.rotation.z = 0; bd.root.updateMatrixWorld(true); sk.update(); const m0 = sk.boneMatrices.slice(bi * 16, bi * 16 + 16);
            w.rotation.z = .6; bd.root.updateMatrixWorld(true); sk.update(); const m1 = sk.boneMatrices.slice(bi * 16, bi * 16 + 16); out.wingMoves = bi >= 0 && m0.some((v, j) => Math.abs(v - m1[j]) > 1e-3); }
          // a picture
          for (const B of D.beasts) B.root.visible = false;
          const row = [mk.buck, mk.elk, mk.moose, mk.bear, mk.wolf, mk.fox, mk.lion, mk.giraffe, rg.bigfoot, rg.turkey]; let xx = x0 - 45; const gy = D.groundAt(x0, z0 + 30);
          for (const A of row) { const w = A.kind === 'giraffe' ? 7 : 5; xx += w / 2; A.x = xx; A.z = z0 + 30; xx += w / 2 + 1.5; A.y = gy; A.yaw = Math.PI / 2; A.speed = 0; A.dead = false; A.root.position.set(A.x, A.y, A.z); A.root.rotation.set(0, A.yaw, 0); A.root.visible = true; }
          D.camera.position.set(x0 - 18, gy + 4, z0 - 6); D.camera.lookAt(x0 - 18, gy + 2, z0 + 30); D.camera.fov = 55;
          if (D.world) D.world.visible = false; D.renderer.setSize(1300, 480); D.camera.aspect = 1300 / 480; D.camera.updateProjectionMatrix(); D.renderer.render(D.scene, D.camera); out.png = D.renderer.domElement.toDataURL('image/png');
          return out; }""")
        png = r.pop("png"); print(json.dumps(r))
        if OUT: import base64; open(os.path.join(OUT, "qanimals.png"), "wb").write(base64.b64decode(png.split(",")[1]))
        ok = r["failed"] == 0 and not r["bad"] and r["walk"] == "Walk" and r["run"] == "Run" and r["eat"] == "Eat" and r["death"] == "Death" and r["croc"] == "gator:1" \
             and r["headShot"]["who"] == "moose" and r["headShot"]["head"] and r["birdQr"] and r.get("wingMoves") and not errs
        print("errors", errs[:5]); print("PASS" if ok else "FAIL"); await b.close(); return ok
try: ok = asyncio.run(main())
finally: srv.terminate(); shutil.rmtree(srvdir, ignore_errors=True)
sys.exit(0 if ok else 1)
