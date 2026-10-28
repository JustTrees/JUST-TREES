"""2.84: the Gun Lab (Dev menu): a quiet island with a range of dummies at 10–400 m (health, shield on or off, standing or strafing);
bullets hit their heads and bodies, they drop and report hits and time; every gun's numbers change live, only inside the Gun Lab.
Usage: python3 dev/test_284.py dbg.html [panel.png]"""
import sys, asyncio, json, base64
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); localStorage.removeItem('jt-guntune'); D.DEV.ok = true; D.setSeed(4242); D.setVR(true); D.vr.on = true;
          D.GUNLAB.want = true; D.GUNLAB.tune = {}; D.GUNLAB.tier = 5; D.GUNLAB.shield = true; D.setMode('hunt'); Object.assign(D.set, { huntMap: 'island', size: 'medium', density: .15, rough: .25, dino: false, weather: 'clear', lat: 45, hour: 12 });
          D.generate(); D.state = 'play'; D.gunLabStart(); const G = D.GUNLAB, T = D.THREE, o = {};
          o.range = [G.on, G.dummies.length, G.dummies.map(d => Math.round(Math.hypot(d.bx - D.P.x, d.bz - D.P.z))).join(','), Object.values(D.vr.own).filter(v => v === 5).length];
          const shoot = (D0, head, n) => { for (let i = 0; i < n; i++) { const from = new T.Vector3(D.P.x, D.groundAt(D.P.x, D.P.z) + 1.6, D.P.z), to = new T.Vector3(D0.x, D0.y + (head ? 1.62 : 1.0), D0.z), v = to.sub(from).normalize().multiplyScalar(D.WEAP.ar.spd);
              D.makeBullet(from, v, { reach: 900, dmg: Math.round(D.WEAP.ar.dmg * D.TIER.dmg[5]), gun: 'ar' }); for (let f = 0; f < 40; f++) D.updateGun(1 / 30); } };
          const d50 = G.dummies[2]; shoot(d50, false, 1); o.hit1 = [d50.sh, d50.hp]; shoot(d50, false, 3); o.down = [d50.alive, d50.hits, d50.last];
          for (let f = 0; f < 90; f++) D.updateGun(1 / 30); o.back = [d50.alive, d50.hp, d50.sh];
          const d25 = G.dummies[1]; G.shield = false; for (const x of G.dummies) x.sh = 0; shoot(d25, true, 1); o.head = [d25.hp, d25.heads];
          // tweaks: only inside the lab
          D.GUNLAB.gun = 'ar'; D.gunLabStep('dmg', 1); D.gunLabStep('cool', 1); D.gunLabStep('size', 1); o.tuned = [D.WEAP.ar.dmg, Math.round(60 / D.WEAP.ar.cool), D.WEAP.ar.size];
          D.vruiOpen('gunlab'); const Pn = D.VRUI.panels.gunlab; D.uiDraw(Pn); o.png = Pn.cv.toDataURL();
          D.GUNLAB.want = false; D.setMode('hunt'); D.set.huntMap = 'island'; D.generate(); o.after = [D.GUNLAB.on, D.WEAP.ar.dmg, D.WEAP.ar.size, D.set.density];
          return o; }""")
        png = r.pop("png"); open(sys.argv[2] if len(sys.argv) > 2 else "/dev/null", "wb").write(base64.b64decode(png.split(",")[1]))
        print(json.dumps(r))
        ok = r["range"][:2] == [True, 6] and [int(x) for x in r["range"][2].split(",")] == sorted(int(x) for x in r["range"][2].split(",")) and r["range"][3] >= 4 and r["hit1"][0] < 60 and r["hit1"][1] == 100 and r["down"][0] is False and r["down"][1] == 4 \
             and r["back"] == [True, 100, 100] and r["head"][1] == 1 and r["head"][0] <= 0 and r["tuned"][0] == 33 and r["tuned"][1] > 414 and r["tuned"][2] == 1.1 \
             and r["after"][0] is False and r["after"][1] == 30 and r["after"][2] == 1
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
