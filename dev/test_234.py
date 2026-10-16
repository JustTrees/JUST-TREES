"""2.34: comms — Open is heard the same anywhere, Open proximity fades with distance (Open had been fading too); voices have no direction
(no panner); a fast-flying friend leaves a trail in their colour. Usage: python3 dev/test_234.py dbg.html"""
import sys, asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required"])
        pg = await (await b.new_context(viewport={"width": 480, "height": 320})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto("file://" + sys.argv[1]); await pg.wait_for_timeout(500)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setSeed(9); D.setVR(true); D.setMode('pvp'); D.vr.on = true;
          Object.assign(D.set, { size: 'medium', lat: 45, hemi: 1, month: 6, hour: 12, weather: 'clear' }); D.generate(); D.state = 'play'; D.initSound();
          const T = D.THREE, h = new T.Vector3(D.P.x, D.P.y + 1.6, D.P.z); D.vr.I = { head: h, headQ: new T.Quaternion(), hands: { left: { pos: h.clone(), q: new T.Quaternion(), rayQ: new T.Quaternion(), grip: 0, trig: 0 }, right: { pos: h.clone(), q: new T.Quaternion(), rayQ: new T.Quaternion(), grip: 0, trig: 0 } } };
          D.MP.on = true; D.MP.code = '1234';
          const L = { id: 'justtrees-v1-x', open: true, bad: false, tag: 'BOB', idx: 2, rx: [] }; L.vg = D.SND.ctx.createGain(); D.MP.links.set(L.id, L);
          L.R = { alive: true, head: new T.Vector3(h.x + 100, h.y, h.z), S: { group: { visible: true } }, guns: {} };
          const g = c => { D.set.comms = c; D.mpTick(1 / 60); return +L.vg.gain.value.toFixed(3); };
          const out = { openFar: g(0), proxFar: g(1) }; L.R.head.set(h.x + 1, h.y, h.z); out.proxNear = g(1); out.openNear = g(0); out.noPanner = !L.panner;
          // a fast friend: 25 m/s across the sky
          for (let i = 0; i < 30; i++) { L.R.head.x += 25 / 60; D.mpTick(1 / 60); }
          out.trail = L.trail ? L.trail.list.length : 0;
          for (let i = 0; i < 60; i++) D.mpTick(1 / 60); out.trailAfterStop = L.trail ? L.trail.list.length : 0;
          return out; }""")
        print(json.dumps(r))
        ok = r["openFar"] == 1.6 and r["openNear"] == 1.6 and r["proxFar"] < .1 and r["proxNear"] == 1.6 and r["noPanner"] and r["trail"] > 5 and r["trailAfterStop"] == 0 and not errs
        print("errors", errs[:5] or "none"); print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
