"""Pictures of the hands: the watch (day and night), the raised map, the flare pistol in the hand. Usage: python3 dev/pics_hands.py dbg.html [outdir]"""
import sys, os, asyncio, base64
from playwright.async_api import async_playwright
S = os.path.dirname(os.path.abspath(__file__)); OUT = sys.argv[2] if len(sys.argv) > 2 else S; SETUP = open(S + "/setup_js.txt").read().split('SETUP = """', 1)[1].rsplit('"""', 1)[0]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 800, "height": 560})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(600)
        await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setSeed(4242); D.setVR(true); D.setMode('hike'); D.vr.on = true; D.hikeForce = 'endless';
          Object.assign(D.set, { lat: 45, hemi: 1, month: 6, hour: 15, weather: 'clear', density: .5, rough: .5 }); D.generate(); D.state = 'play'; }""")
        await pg.evaluate(SETUP)
        async def shot(name, js):
            u = await pg.evaluate(js); open(f"{OUT}/{name}.jpg", "wb").write(base64.b64decode(u.split(",")[1]))
        CAM = """(fov) => { const c = D.camera; c.fov = fov; c.aspect = 800 / 560; c.near = .01; c.updateProjectionMatrix(); c.updateMatrixWorld(); D.renderer.setSize(800, 560); D.renderer.render(D.scene, c); return D.renderer.domElement.toDataURL('image/jpeg', .9); }"""
        await pg.evaluate("(c) => { window.__cam = eval(c); }", CAM)
        # 1) the watch: left hand turned to look at it (back of the wrist toward you), day then night
        for tag, hr in (("watch_day", 15.0), ("watch_night", 23.0)):
            await pg.evaluate(f"() => {{ D.hourNow = {hr}; }}")
            if hr > 20: await pg.evaluate("() => { D.set.hour = 23; D.generate(); D.state = 'play'; }"); await pg.evaluate(SETUP)
            await shot(tag, """() => { const T = D.THREE; L.Lh.set(-.04, 1.33, -.3);
              qs.L.setFromAxisAngle(new T.Vector3(0, 0, 1), Math.PI / 2).multiply(new T.Quaternion().setFromAxisAngle(new T.Vector3(0, 1, 0), Math.PI / 2)).multiply(new T.Quaternion().setFromAxisAngle(new T.Vector3(1, 0, 0), -.4));
              frames(3); const c = D.camera, h = toW(L.head); c.position.copy(h); c.lookAt(D.watchM.position); return window.__cam(40); }""")
        # 2) the raised map: off-hand trigger held, as in play
        await pg.evaluate("() => { D.set.hour = 15; D.hourNow = 15; D.generate(); D.state = 'play'; }"); await pg.evaluate(SETUP)
        await shot("map", """() => { L.Lh.set(-.12, 1.2, -.32); pad.L.trig = 1; frames(4); const c = D.camera, h = toW(L.head); c.position.copy(h); c.quaternion.setFromEuler(new D.THREE.Euler(-.55, D.vr.yaw, 0, 'YXZ')); return window.__cam(90); }""")
        # 3) the flare pistol in the hand
        await shot("flaregun", """() => { pad.L.trig = 0; frames(2); D.vr.map = false; const T = D.THREE, h = toW(L.head), Rp = new T.Vector3(h.x + .12, h.y - .35, h.z - .35);
          const q = new T.Quaternion().setFromAxisAngle(new T.Vector3(1, 0, 0), .15), rq = new T.Quaternion();
          const main = { pos: Rp, q, rayQ: rq, grip: 1, trig: 0 }; D.flareHand(main); D.vr.I = { head: h, headQ: new T.Quaternion(), hands: { right: main, left: { pos: new T.Vector3(h.x - .3, h.y - .7, h.z), q: new T.Quaternion(), rayQ: new T.Quaternion(), grip: 0, trig: 0 } } };
          D.vrHands(); D.flareHand(main); const c = D.camera; c.position.set(Rp.x + .28, Rp.y + .1, Rp.z + .12); c.lookAt(Rp.x, Rp.y + .01, Rp.z - .06); return window.__cam(50); }""")
        print("errors", errs[:4]); await b.close()
asyncio.run(main())
