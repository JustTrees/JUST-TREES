"""3.26: the glasses are back, for Dev testing (Full level and the Test Lab: levels 51-55; 3.32: no golden hour). In those sessions their looks are built into
every material while the world is made (and the animals' neon/white versions a couple of seconds in), so putting them on or off never
builds anything new mid-play; outside them nothing about the shaders changes. Usage: python3 dev/test_326.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 480, "height": 300})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)[:300])); pg.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); const o = {}, T = D.THREE, R = D.renderer;
          D.setSeed(4242); D.setVR(true); D.vr.on = true; D.setMode('hike'); D.set.hikeMap = 'endless'; D.generate(); D.state = 'play'; R.render(D.scene, D.camera);
          o.plain = [D.JTFX.always === true, !!T.Material.prototype.defines];
          // the Test Lab: a Dev session with the glasses
          D.DEV.ok = true; D.GEO.labWant = true; D.setMode('hunt'); Object.assign(D.set, { huntMap: 'globe', dino: false, geoNet: false }); D.generate(); D.state = 'play';
          o.lab = [D.GEO.lab, D.JTFX.always, D.GLASSES.filter(k => D.GEO.items.has(k)).length, D.geoRewardOf(51).item, D.geoRewardOf(55).item, D.geoRewardOf(50).item === 'jetski'];
          const I = { head: new T.Vector3(D.P.x, D.P.y + 1.7, D.P.z), headQ: new T.Quaternion(), hands: {} };
          for (let i = 0; i < 72 * 3; i++) { D.endlessTick(1 / 72); D.geoTick(1 / 72); D.geoWornTick(I); } R.render(D.scene, D.camera); o.warm = D.JTFX.warm;
          const p0 = R.info.programs.length; const per = {};
          for (const k of D.GLASSES) { D.GEO.worn = new Set([k]); for (let i = 0; i < 40; i++) { D.geoWornTick(I); D.geoTick(1 / 72); } R.render(D.scene, D.camera); per[k] = R.info.programs.length - p0;
            D.GEO.worn = new Set(); for (let i = 0; i < 40; i++) { D.geoWornTick(I); D.geoTick(1 / 72); } R.render(D.scene, D.camera); }
          o.newPrograms = per; o.lookOn = true;
          // back to a normal world: nothing of it left
          D.setMode('hike'); D.set.hikeMap = 'endless'; D.generate(); D.state = 'play'; R.render(D.scene, D.camera);
          o.after = [D.JTFX.always, !!T.Material.prototype.defines, D.GEO.on];
          return o; }""")
        print(json.dumps(r)); print("errors:", errs[:5] or "none")
        ok = r["plain"] == [False, False] and r["lab"][:3] == [True, True, 6] and r["lab"][3] == "bblock" and r["lab"][4] == "hlglass" and r["lab"][5] and r["warm"] \
             and all(v <= 0 for v in r["newPrograms"].values()) and r["after"][:2] == [False, False] and not errs
        print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
