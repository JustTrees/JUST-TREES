"""2.04: five bows: Hunting starts you with the 1-star bow; bows of 2-5 stars lie about the map like the guns (Wooden 2, Wooden,
Golden, Evil from the Quaternius Medieval Weapons Pack); picking up a better one swaps the bow in your hand (same frame, same draw), a worse
or equal one is left there (and not drawn). Served over http so the models load. Writes a picture of the five (optional 2nd argument).
Usage: python3 dev/test_bowtiers.py dbg.html [outdir]"""
import os, sys, asyncio, json, subprocess, time, shutil, tempfile, base64
from playwright.async_api import async_playwright
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
srvdir = tempfile.mkdtemp(); shutil.copy(sys.argv[1], os.path.join(srvdir, "dbg.html")); os.symlink(os.path.join(REPO, "models"), os.path.join(srvdir, "models"))
OUT = sys.argv[2] if len(sys.argv) > 2 else None
if OUT and OUT.endswith((".png", ".jpg")): OUT = os.path.dirname(OUT)
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8788", "--bind", "127.0.0.1"], cwd=srvdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 1200, "height": 520})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto("http://127.0.0.1:8788/dbg.html", timeout=120000); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = {}; D.setSeed(9); D.setVR(true); D.setMode('hunt'); D.set.size = 'large'; D.set.weather = 'clear'; D.set.lat = 45; D.set.dino = false; D.generate(); D.state = 'play';
          D.pvpLoadout(); out.start = D.vrOwn.bow; out.tier0 = D.bowTier();
          const bows = [...D.DROPS.values()].filter(d => d.kind === 'bow'); out.nBows = bows.length; out.minStar = Math.min(...bows.map(d => d.tier));
          for (let t = 2; t <= 5; t++) D.bowLoad(t); return out; }""")
        await pg.wait_for_function("[2, 3, 4, 5].every(t => D.BOWQ.geo[t])", timeout=120000)
        r2 = await pg.evaluate("""() => { const out = {}, T = D.THREE, B = D.bowObj || (D.pickGun('bow'), D.bowObj) || null;
          const BB = (() => { try { return D.bowSkin && (window.__B = null, true); } catch (e) { return false; } })();
          // pick up a 3-star bow, then a 2-star one (left there), then the red one
          const take = t => D.dropUse({ type: 'gun', kind: 'bow', tier: t });
          out.take3 = take(3); out.after3 = D.bowTier(); out.take2 = take(2); out.after2 = D.bowTier(); out.take5 = take(5); out.after5 = D.bowTier();
          // the bow in the hand changes to the pack model
          const P0 = D.bowTemplate(5); out.tpl5 = !!P0.userData.qk;
          const BO = D.bowObj; D.bowSkin(BO); out.hand = [BO.skin.tier, BO.base[0].visible, !!BO.skin.pack && BO.skin.pack.parent === BO.bow];
          // the five in a row (1 = the game's own)
          const sc = new T.Scene(); sc.add(new T.HemisphereLight(0xffffff, 0x445544, 1.1)); const dl = new T.DirectionalLight(0xffffff, .9); dl.position.set(-2, 3, 4); sc.add(dl);
          const own = new T.Group(); D.vrOwn.bow = 1; const one = D.bowTemplate(1); out.oneIsOwn = !one.userData.qk; D.vrOwn.bow = 5;
          const row = [one, D.bowTemplate(2), D.bowTemplate(3), D.bowTemplate(4), D.bowTemplate(5)];
          row.forEach((m, i) => { const c = m.clone(true); c.position.set((i - 2) * .55, 0, 0); c.rotation.y = -Math.PI / 2; sc.add(c); });
          out.ext = row.map(m => { const bb = new T.Box3().setFromObject(m); return [+(bb.max.y - bb.min.y).toFixed(2), +bb.min.z.toFixed(2), +bb.max.z.toFixed(2)]; });
          const cam = new T.PerspectiveCamera(40, 1200 / 520, .01, 50); cam.position.set(0, 0, 2.6); cam.lookAt(0, 0, 0);
          const R = D.renderer; R.setSize(1200, 520); R.setClearColor(0x9fb8c8, 1); R.render(sc, cam); out.png = R.domElement.toDataURL('image/jpeg', .9); return out; }""")
        png = r2.pop("png"); r.update(r2); print(json.dumps(r))
        if OUT: open(os.path.join(OUT, "bowtiers.jpg"), "wb").write(base64.b64decode(png.split(",")[1]))
        ok = r["start"] == 1 and r["tier0"] == 1 and r["nBows"] >= 2 and r["minStar"] >= 2 and r["take3"] and r["after3"] == 3 and not r["take2"] and r["after2"] == 3 and r["take5"] and r["after5"] == 5 \
             and r["tpl5"] and r["hand"] == [5, False, True] and r["oneIsOwn"] and all(1.5 < e[0] < 1.65 for e in r["ext"]) and not errs
        print("errors", errs[:5]); print("PASS" if ok else "FAIL"); await b.close(); return ok
try: ok = asyncio.run(main())
finally: srv.terminate(); shutil.rmtree(srvdir, ignore_errors=True)
sys.exit(0 if ok else 1)
