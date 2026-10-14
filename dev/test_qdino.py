"""1.91: the dinosaurs are the Quaternius animated models (models/dinos/*.bin). Served over http (a copy opened from disk keeps the old ones).
Each of the six loads, sits on the hidden hand-built one at its length, picks Idle / Walk / Run / Attack / Death from what the animal does,
and a shot at the model's head still counts as a head shot. Writes a picture of the six to the folder given as the 2nd argument (optional).
Usage: python3 dev/test_qdino.py dbg.html [outdir]   (dbg.html made by make_debug.py, in the repo folder or next to a models/ link)"""
import os, sys, asyncio, json, subprocess, time, shutil, tempfile
from playwright.async_api import async_playwright
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
srvdir = tempfile.mkdtemp(); shutil.copy(sys.argv[1], os.path.join(srvdir, "dbg.html")); os.symlink(os.path.join(REPO, "models"), os.path.join(srvdir, "models"))
OUT = sys.argv[2] if len(sys.argv) > 2 else None
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8781", "--bind", "127.0.0.1"], cwd=srvdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 1300, "height": 480})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto("http://127.0.0.1:8781/dbg.html", timeout=120000); await pg.wait_for_timeout(800)
        await pg.evaluate("""() => { window.FREEZE = true; D.setSeed(5); D.setVR(true); D.setMode('hunt'); D.set.dino = true; D.set.env = 'climate'; D.set.land = 'natural'; D.set.size = 'large'; D.set.lat = 42; D.set.month = 6; D.set.weather = 'clear'; D.set.density = .5; D.generate(); D.state = 'play';
          for (const k of ['trex', 'raptor', 'parasaur', 'triceratops', 'stego', 'bronto']) D.qdinoLoad(k); }""")
        await pg.wait_for_function("Object.keys(D.QDINO.models).length === 6 || D.QDINO.failed > 0", timeout=60000)
        r = await pg.evaluate("""() => { const out = { failed: D.QDINO.failed }, T = D.THREE, P = D.P;
          const x0 = P.x, z0 = P.z, mk = {}; let i = 0;
          for (const k of ['trex', 'raptor', 'parasaur', 'triceratops', 'stego', 'bronto']) { const A = D.addGround(k, x0 - 50 + i * 20, z0 + 30); A.yaw = Math.PI / 2; A.mode = 'idle'; A.timer = 99; A.speed = 0; A.want = 0; mk[k] = A; i++; }
          D.camera.position.set(x0, D.groundAt(x0, z0) + 6, z0 - 25); D.camera.lookAt(x0, D.groundAt(x0, z0) + 4, z0 + 30); D.camera.updateMatrixWorld();
          for (const A of Object.values(mk)) D.qdTick(A, 1 / 30, 10); for (let f = 0; f < 10; f++) D.updateAnimals(1 / 30);
          out.fit = {}; for (const k in mk) { const A = mk[k], F = D.QDINO.fit[k]; out.fit[k] = { sph: A.qhit && A.qhit.length, heads: A.qhit && A.qhit.filter(h => h[5]).length, qd: !!A.qd, hidden: A.body.visible === false, s: F && +F.s.toFixed(5), len: F && +F.len.toFixed(1), hgt: F && F.hgt.map(v => +v.toFixed(2)), cur: A.qd && A.qd.cur }; }
          // moves: walk, run, attack, death
          const st = mk.stego; st.mode = 'walk'; st.timer = 99; st.target = [st.x + 200, st.z]; st.want = st.walk; for (let f = 0; f < 60; f++) D.updateAnimals(1 / 30); out.walk = [st.qd.cur, +st.qd.curA.timeScale.toFixed(2)];
          st.want = st.run; st.fleeT = 5; for (let f = 0; f < 60; f++) D.updateAnimals(1 / 30); out.run = [st.qd.cur, +st.qd.curA.timeScale.toFixed(2), +st.speed.toFixed(1)];
          const rx = mk.trex; rx.rearT = 2; D.qdTick(rx, 1 / 30, 10); out.attack = rx.qd.cur; rx.rearT = 0;
          // a head shot on the model's head (the bone, not the old hidden head)
          const tri = mk.triceratops; tri.root.updateMatrixWorld(true); const hp = new T.Vector3().setFromMatrixPosition(tri.qd.head.matrixWorld);
          const fwd = new T.Vector3(Math.sin(tri.yaw), 0, Math.cos(tri.yaw)), side = new T.Vector3(fwd.z, 0, -fwd.x);
          const o = hp.clone().add(fwd.clone().multiplyScalar(.6)).add(side.clone().multiplyScalar(-20)), d = hp.clone().add(fwd.clone().multiplyScalar(.6)).sub(o).normalize(); const ray = D.animalRay(o, d, .5);
          out.headShot = { who: ray[1] && ray[1].kind, head: ray[2] };
          const ob = new T.Vector3(tri.x, tri.y + 1.5, tri.z), o2 = ob.clone().add(side.clone().multiplyScalar(-20)), r2 = D.animalRay(o2, ob.clone().sub(o2).normalize(), .5); out.bodyShot = { who: r2[1] && r2[1].kind, head: r2[2] };
          D.updateAnimals(1 / 30); D.renderer.render(D.scene, D.camera);
          const pz = mk.parasaur; D.killAnimal(pz, 30); for (let f = 0; f < 90; f++) D.updateAnimals(1 / 30); out.death = [pz.qd.cur, pz.dead];
          // a picture: the six in a row side-on (and an old T. rex at the end, for comparison)
          for (const B of D.beasts) if (!Object.values(mk).includes(B)) B.root.visible = false;
          const old = D.addGround('trex', 0, 0); D.qdTick(old, 1 / 30, 10); old.body.visible = true; old.qd.wrap.visible = false;
          const row = [...Object.values(mk), old]; let xx = x0 - 60; const gy = D.groundAt(x0, z0 + 30);
          for (const A of row) { const w = A.kind === 'bronto' ? 26 : A.kind === 'trex' ? 16 : 10; xx += w / 2; A.x = xx; A.z = z0 + 30; xx += w / 2 + 2; A.y = gy; A.yaw = Math.PI / 2; A.root.position.set(A.x, A.y, A.z); A.root.rotation.set(0, A.yaw, 0); A.root.visible = true; }
          D.camera.position.set(x0 - 4, gy + 5, z0 - 12); D.camera.lookAt(x0 - 4, gy + 3.5, z0 + 30); D.camera.fov = 55;
          if (D.world) D.world.visible = false; D.renderer.setSize(1300, 480); D.camera.aspect = 1300 / 480; D.camera.updateProjectionMatrix(); D.renderer.render(D.scene, D.camera); out.png = D.renderer.domElement.toDataURL('image/png');
          return out; }""")
        png = r.pop("png"); print(json.dumps(r))
        if OUT: import base64; open(os.path.join(OUT, "qdino.png"), "wb").write(base64.b64decode(png.split(",")[1]))
        ok = r["failed"] == 0 and all(v["qd"] and v["hidden"] for v in r["fit"].values()) and r["walk"][0] == "Walk" and r["run"][0] == "Run" and r["attack"] == "Attack" \
             and r["headShot"]["head"] and r["headShot"]["who"] == "triceratops" and r["bodyShot"]["who"] == "triceratops" and not r["bodyShot"]["head"] and r["death"][0] == "Death" and not errs
        print("errors", errs[:5]); print("PASS" if ok else "FAIL"); await b.close(); return ok
try: ok = asyncio.run(main())
finally: srv.terminate(); shutil.rmtree(srvdir, ignore_errors=True)
sys.exit(0 if ok else 1)
