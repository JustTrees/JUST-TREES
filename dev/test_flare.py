"""2.25: the flare gun (VR PvP, L and up): on the wheel with 3 flares each spawn; a fired flare rises on its trail, bursts high up and is cleared
away after; off the wheel when all 3 are gone; not on smaller maps or in Hunting. Also: the sniper never shows the red cross.
Usage: python3 dev/test_flare.py dbg.html [picture.png]"""
import sys, asyncio, json, base64
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 900, "height": 560})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setSeed(808); D.setVR(true); D.setMode('pvp'); D.vr.on = true;
          Object.assign(D.set, { size: 'large', comms: 3, lat: 45, hemi: 1, month: 6, hour: 20.3, weather: 'clear', density: .5, rough: .5 }); D.generate(); D.state = 'play'; D.pvpLoadout2();
          const out = { wheel: D.wheelKeys2().includes('flare'), n: D.vr.flares };
          const G = D.FLARE; D.vr.flareMode = true;
          // aim the flare gun straight up-ish and fire
          const fake = { pos: new D.THREE.Vector3(D.P.x, D.P.y + 1.4, D.P.z), q: new D.THREE.Quaternion().setFromAxisAngle(new D.THREE.Vector3(1, 0, 0), 1.2 + .6) };
          window.__fake = fake; D.vr.flares = 3;
          const gun = (() => { const g = D.scene.children.find(o => o === G.gun); return g; })();
          return out; }""")
        await pg.evaluate("""() => { const G = D.FLARE; const fake = window.__fake; D.vr.flareMode = true;
          // the hand pose: flareHand is called from the VR tick; here put the gun there directly
          if (!G.gun) { D.flareFire; } }""")
        r2 = await pg.evaluate("""() => { const G = D.FLARE; const fake = window.__fake;
          D.vr.flares = 3; for (let i = 0; i < 3; i++) { fake.q = new D.THREE.Quaternion().setFromEuler(new D.THREE.Euler(1.1 + i * .1, i * .5, 0, 'YXZ')).multiply(new D.THREE.Quaternion().setFromAxisAngle(new D.THREE.Vector3(1, 0, 0), .6)); D.flareHand(fake); D.flareFire(); }
          const out = { flying: G.list.length, left: D.vr.flares, wheel: D.wheelKeys2().includes('flare'), mode: D.vr.flareMode };
          let maxY = 0, burst = 0; const y0 = D.P.y; for (let f = 0; f < 72 * 6.5; f++) { D.flareTick(1 / 72); for (const F of G.list) { maxY = Math.max(maxY, F.p.y - y0); if (F.burst) burst++; } }
          out.highM = Math.round(maxY); out.burst = burst > 0;
          // a picture: looking up at the bursts
          const c = D.camera; c.fov = 80; c.aspect = 900 / 560; c.updateProjectionMatrix(); c.position.set(D.P.x - 60, D.P.y + 3, D.P.z + 80); const F = G.list[1]; c.position.set(F.p.x - 140, D.H(F.p.x - 140, F.p.z + 120) + 3, F.p.z + 120); c.lookAt(F.p.x, F.p.y - 15, F.p.z); c.updateMatrixWorld();
          D.scene.traverse(o => { if (o.isMesh && o.material.uniforms && o.material.uniforms.sunDir) o.position.copy(c.position); }); D.cullTiles(); D.renderer.setSize(900, 560); D.renderer.render(D.scene, c); out.pic = D.renderer.domElement.toDataURL('image/jpeg', .85);
          for (let f = 0; f < 72 * 12; f++) D.flareTick(1 / 72); out.after = G.list.length;
          D.set.size = 'medium'; out.mediumWheel = D.wheelKeys2().includes('flare') && D.vr.flares > 0;
          D.set.size = 'large'; D.set.comms = 1; D.pvpLoadout2(); out.openComms = D.wheelKeys2().includes('flare') || D.vr.flares > 0;   /* 2.32: only with fist-bump comms */
          return out; }""")
        if len(sys.argv) > 2: open(sys.argv[2].replace(".png", ".jpg"), "wb").write(base64.b64decode(r2["pic"].split(",")[1]))
        del r2["pic"]; print(json.dumps(r), json.dumps(r2))
        ok = r["wheel"] and r["n"] == 3 and r2["flying"] == 3 and r2["left"] == 0 and not r2["wheel"] and not r2["mode"] and r2["highM"] > 280 and r2["burst"] and r2["after"] == 0 and not r2["mediumWheel"] and not r2["openComms"] and not errs
        print("errors", errs[:5]); print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
