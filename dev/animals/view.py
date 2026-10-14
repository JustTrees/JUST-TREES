"""Pictures of animal models: each one standing, mid-walk, mid-run and dead, from the side.
Usage: python3 dev/animals/view.py dbg.html out.jpg kind,kind,...   (dbg.html from make_debug.py; models from models/animals/)"""
import os, sys, asyncio, subprocess, time, shutil, tempfile, base64
from playwright.async_api import async_playwright
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
srvdir = tempfile.mkdtemp(); shutil.copy(sys.argv[1], os.path.join(srvdir, "dbg.html")); os.makedirs(os.path.join(srvdir, "models")); os.symlink(os.path.abspath(os.environ.get("VIEWDIR", os.path.join(REPO, "models", "animals"))), os.path.join(srvdir, "models", "animals"))
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8785", "--bind", "127.0.0.1"], cwd=srvdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2)
kinds = sys.argv[3].split(","); poses = (sys.argv[4] if len(sys.argv) > 4 else "rest,Walk:.3,Run:.25,Death:9").split(",")
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        W, Hh = 300 * len(poses), 240 * len(kinds)
        pg = await (await b.new_context(viewport={"width": 400, "height": 300})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto("http://127.0.0.1:8785/dbg.html", timeout=120000); await pg.wait_for_timeout(500)
        rows = []
        for kind in kinds:
            rows.append(await pg.evaluate("""async ([kinds, poses, W, Hh]) => { window.FREEZE = true; D.renderer.setAnimationLoop(null); const T = D.THREE, R = D.renderer; R.setPixelRatio(1); R.setSize(W, Hh, false); R.setScissorTest(true); R.setClearColor(0x9fb8c8, 1);
          for (let r = 0; r < kinds.length; r++) {
            const buf = await (await fetch('models/animals/' + kinds[r] + '.bin')).arrayBuffer(), M = D.qdinoParse(buf);
            for (let c = 0; c < poses.length; c++) {
              const Q = M.js.nodes.some(n => n.n === 'Neck') ? D.qdinoMake(M) : (() => { const top = new T.Group(), bs = M.js.nodes.map(nd => { const b = new T.Bone(); b.position.fromArray(nd.t, 0); top.add(b); return b; }); const mesh = new T.SkinnedMesh(M.geo, M.mat); top.add(mesh); top.updateMatrixWorld(true); mesh.bind(new T.Skeleton(M.js.mesh.bones.map(i => bs[i]), M.inv)); return { top, mesh, mixer: new T.AnimationMixer(top) }; })(), sc = new T.Scene(); sc.add(new T.HemisphereLight(0xffffff, 0x556655, 1.1)); const dl = new T.DirectionalLight(0xffffff, .8); dl.position.set(3, 5, 4); sc.add(dl);
              const [cn, ct] = poses[c].split(':'); if (cn !== 'rest' && M.clips[cn]) { const a = Q.mixer.clipAction(M.clips[cn]); a.play(); if (cn === 'Death') { a.setLoop(T.LoopOnce); a.clampWhenFinished = true; } Q.mixer.update(Math.min(+ct, M.clips[cn].duration - .001)); }
              Q.top.updateMatrixWorld(true); const bb = M.geo.boundingBox.clone().applyMatrix4(Q.mesh.matrixWorld), s = 2 / Math.max(bb.max.z - bb.min.z, bb.max.y - bb.min.y), g = new T.Group(); g.add(Q.top); g.scale.setScalar(s); g.position.y = -bb.min.y * s; sc.add(g);
              const cam = new T.PerspectiveCamera(32, 300 / 240, .01, 100); cam.position.set(+(window.CAMX || 3.7), 1.5, +(window.CAMZ || 2.0)); cam.lookAt(0, .8, 0);
              R.setViewport(c * 300, Hh - (r + 1) * 240, 300, 240); R.setScissor(c * 300, Hh - (r + 1) * 240, 300, 240); R.clear(); R.render(sc, cam);
            }
          }
          R.setScissorTest(false); return R.domElement.toDataURL('image/png'); }""", [[kind], poses, 300 * len(poses), 240]))
        from PIL import Image; import io
        ims = [Image.open(io.BytesIO(base64.b64decode(x.split(",")[1]))).convert("RGB") for x in rows]
        out = Image.new("RGB", (ims[0].width, 240 * len(ims)))
        for i, im in enumerate(ims): out.paste(im, (0, 240 * i))
        out.save(sys.argv[2], quality=85)
        print("errors", errs[:3]); await b.close()
try: asyncio.run(main())
finally: srv.terminate(); shutil.rmtree(srvdir, ignore_errors=True)
