"""2.12: other players' gunshots and footsteps are 3D (from where they are). Shots heard to RANGE (AK 600 m = half an XL map, sniper 780,
SMG 520, pistol 440), quieter, duller and later with distance; footsteps to 35 m, loud sprinting, soft walking, near-silent crouching.
Served over http (the recorded shots load). Usage: python3 dev/test_psound.py dbg.html"""
import os, sys, asyncio, json, subprocess, time, shutil, tempfile
from playwright.async_api import async_playwright
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
srvdir = tempfile.mkdtemp(); shutil.copy(sys.argv[1], os.path.join(srvdir, "dbg.html")); os.symlink(os.path.join(REPO, "sounds"), os.path.join(srvdir, "sounds"))
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8790", "--bind", "127.0.0.1"], cwd=srvdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto("http://127.0.0.1:8790/dbg.html", timeout=120000); await pg.wait_for_timeout(800)
        await pg.evaluate("""() => { window.FREEZE = true; D.setVR(true); D.setMode('pvp'); D.set.size = 'xl'; D.generate(); D.state = 'play'; D.initSound(); D.SND.on = true; D.gunSndLoad(); }""")
        await pg.wait_for_function("['ar_shot', 'sniper_shot', 'nine_shot'].every(k => D.DSND.buf['guns/' + k])", timeout=60000)
        r = await pg.evaluate("""() => { const out = {}, c = D.SND.ctx, T = D.THREE; let n = 0, pans = []; const o1 = c.createBufferSource.bind(c), o2 = c.createPanner.bind(c);
          c.createBufferSource = () => { n++; return o1(); }; c.createPanner = () => { const p = o2(); pans.push(p); return p; };
          const cam = D.camera.position, at = (d, a) => new T.Vector3(cam.x + Math.sin(a) * d, cam.y, cam.z + Math.cos(a) * d), shot = (k, d, a) => { const n0 = n; D.mpShotSound(k, at(d, a || 0)); return n - n0; };
          out.ak = [shot('ar', 50), shot('ar', 590), shot('ar', 610)]; out.sniper = [shot('hunt', 770), shot('hunt', 790)]; out.smg = [shot('smg', 510), shot('smg', 530)]; out.pistol = [shot('pistol', 430), shot('pistol', 450)];
          out.hrtf = pans.length > 0 && pans.every(p => p.panningModel === 'HRTF');
          D.mpShotSound('ar', at(100, 1.2)); const v = D.PSND.shots[D.PSND.si]; out.pannerAtShooter = Math.abs(v.positionX.value - at(100, 1.2).x) < .01;
          // footsteps
          const L = { id: 'x' }, steps = (d, sp, crouch) => { const R = {}, S = { x: cam.x + d, y: cam.y - 1.6, z: cam.z, speed: sp, gliding: false, crouchWant: crouch ? 1 : 0 }; const n0 = n; for (let i = 0; i < 60; i++) D.mpStepTick(L, R, S, 1 / 60); return n - n0; };
          out.sprintNear = steps(8, 12.5); out.walkNear = steps(8, 8.5); out.far = steps(40, 12.5); out.still = steps(8, 0);
          return out; }""")
        print(json.dumps(r))
        ok = r["ak"][0] == 1 and r["ak"][1] == 1 and r["ak"][2] == 0 and r["sniper"] == [1, 0] and r["smg"] == [1, 0] and r["pistol"] == [1, 0] and r["hrtf"] and r["pannerAtShooter"] \
             and r["sprintNear"] > 0 and r["walkNear"] > 0 and r["far"] == 0 and r["still"] == 0 and not errs
        print("errors", errs[:5]); print("PASS" if ok else "FAIL"); await b.close(); return ok
try: ok = asyncio.run(main())
finally: srv.terminate(); shutil.rmtree(srvdir, ignore_errors=True)
sys.exit(0 if ok else 1)
