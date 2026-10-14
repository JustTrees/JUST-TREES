"""2.09: the guns play real recordings (sounds/guns/): each gun's shot, reloads, bolt / charging handle / slide, the empty click.
Served over http (a copy opened from disk keeps the made-up sounds). Usage: python3 dev/test_gunsounds.py dbg.html"""
import os, sys, asyncio, json, subprocess, time, shutil, tempfile
from playwright.async_api import async_playwright
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
srvdir = tempfile.mkdtemp(); shutil.copy(sys.argv[1], os.path.join(srvdir, "dbg.html")); os.symlink(os.path.join(REPO, "sounds"), os.path.join(srvdir, "sounds"))
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8789", "--bind", "127.0.0.1"], cwd=srvdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto("http://127.0.0.1:8789/dbg.html", timeout=120000); await pg.wait_for_timeout(800)
        await pg.evaluate("""() => { window.FREEZE = true; D.setVR(true); D.setMode('hunt'); D.set.size = 'small'; D.generate(); D.state = 'play'; D.initSound(); D.SND.on = true; D.gunSndLoad(); }""")
        await pg.wait_for_function("Object.keys(D.DSND.buf).filter(k => k.startsWith('guns/')).length >= 20", timeout=60000)
        r = await pg.evaluate("""() => { const out = {}, c = D.SND.ctx; let n = 0; const orig = c.createBufferSource.bind(c); c.createBufferSource = () => { const s = orig(); n++; return s; };
          out.loaded = Object.keys(D.DSND.buf).filter(k => k.startsWith('guns/')).sort();
          for (const k of ['hunt', 'ar', 'smg', 'pistol']) { const n0 = n; D.gunshot(k, 0); out['shot_' + k] = n - n0; }
          const n1 = n; D.gunshot('ar', 0, 300); out.farShot = n - n1;
          for (const g of ['hunt', 'ar', 'smg', 'pistol']) { D.vr.gunKind = g; for (const x of ['magout', 'magin', 'back', 'fwd', 'dry']) { const n0 = n; D.gunFoleyK(x, [[0, 1000, .05, .1]]); out[g + '_' + x] = n - n0; } }
          out.durs = Object.fromEntries(['sniper_shot', 'ar_shot', 'nine_shot'].map(k => [k, +D.DSND.buf['guns/' + k].duration.toFixed(2)]));
          return out; }""")
        print(json.dumps(r))
        ok = len(r["loaded"]) == 20 and all(r["shot_" + k] == 1 for k in ("hunt", "ar", "smg", "pistol")) and r["farShot"] == 1 \
             and all(r[g + "_" + x] == 1 for g in ("hunt", "ar", "smg", "pistol") for x in ("magout", "magin", "back", "fwd", "dry")) and all(1 < v < 2.2 for v in r["durs"].values()) and not errs
        print("errors", errs[:5]); print("PASS" if ok else "FAIL"); await b.close(); return ok
try: ok = asyncio.run(main())
finally: srv.terminate(); shutil.rmtree(srvdir, ignore_errors=True)
sys.exit(0 if ok else 1)
