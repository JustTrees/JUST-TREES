"""Lightning (1.31): strikes come in uneven bursts, each flickers, the flash fades with distance, objects clean up,
the sun/moon light goes back exactly to normal; renders a ground strike at night.
Usage: python3 dev/make_debug.py index.html /tmp/dbg.html && python3 dev/test_storm.py /tmp/dbg.html [/tmp/storm]"""
import os, sys, asyncio, json, base64
from playwright.async_api import async_playwright
T = 'file://' + os.path.abspath(sys.argv[1]); OUT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/storm'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 900, "height": 560})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(T); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = {};
          D.setSeed(11); D.setMode('hike'); D.set.size = 'small'; D.set.weather = 'storm'; D.set.hour = 23; D.set.lat = 45; D.generate(); D.state = 'play';
          out.storm = D.weather.storm; const S = D.STORM, base = { i: D.sunL.intensity, p: D.sunL.position.clone(), h: D.hemi.intensity };
          // timing: 200 strikes worth of gaps
          let gaps = [], t = 0; S.next = 1; for (let i = 0; i < 4000000 && gaps.length < 150; i += 50) { const before = S.strikes.length; D.stormTick(.05, i); if (S.strikes.length > before) { gaps.push(i - t); t = i; } }
          gaps.sort((a, b) => a - b); out.gapSecMin = +(gaps[1] / 1000).toFixed(2); out.gapSecMedian = +(gaps[75] / 1000).toFixed(1); out.gapSecMax = +(gaps[148] / 1000).toFixed(1);
          out.burstPct = Math.round(gaps.filter(g => g < 2200).length / gaps.length * 100);
          for (let i = 0; i < 200; i++) D.stormTick(.05, 9e6 + i * 50);          // let them all finish
          out.leftover = S.strikes.length; out.sunBack = Math.abs(D.sunL.intensity - base.i) < 1e-6 && D.sunL.position.distanceTo(base.p) < 1e-6; out.hemiBack = Math.abs(D.hemi.intensity - base.h) < 1e-6;
          // a close ground strike vs a far one: peak flash
          const peak = (kind, d) => { S.strikes.length = 0; const r0 = Math.random; let calls = 0; Math.random = () => { calls++; return calls === 1 ? (kind === 'ground' ? .1 : .9) : calls === 2 ? (kind === 'ground' ? (d - 250) / 2600 : .95) : r0(); };
            const t0 = 2e7; D.spawnStrike(t0); Math.random = r0; let pk = 0, pulses = 0, was = 0; for (let i = 0; i < 40; i++) { D.stormTick(.016, t0 + i * 16); pk = Math.max(pk, D.STORM.flash); if (D.STORM.flash > .02 && was <= .02) pulses++; was = D.STORM.flash; } for (let i = 0; i < 80; i++) D.stormTick(.016, t0 + 2000 + i * 16); return [+pk.toFixed(2), pulses]; };
          out.closeGroundPeak_pulses = peak('ground', 300); out.farGroundPeak_pulses = peak('ground', 2700); out.farHorizonPeak_pulses = peak('far', 6000);
          return out; }""")
        print(json.dumps(r))
        # a picture: a close ground strike at the brightest moment, plus the same view a second later in the dark
        for name, dt in [("flash", 30), ("dark", 2000)]:
            u = await pg.evaluate("""([dt]) => { const S = D.STORM; S.strikes.length = 0; const r0 = Math.random; let c = 0; Math.random = () => { c++; return c === 1 ? .1 : c === 2 ? .15 : c === 3 ? .02 : r0(); }; D.spawnStrike(3e7); Math.random = r0;
              D.stormTick(.016, 3e7 + dt); const T = D.THREE, cam = new T.PerspectiveCamera(75, 900 / 560, .5, 4000), s = S.strikes[0];
              cam.position.copy(D.camera.position); cam.lookAt(D.camera.position.clone().add(new T.Vector3(1, .25, 0)));
              if (s) { const o = s.objs[0][0]; o.geometry.computeBoundingBox(); const c2 = new T.Vector3(); o.geometry.boundingBox.getCenter(c2); cam.lookAt(c2.x, D.camera.position.y + 120, c2.z); }
              D.renderer.setSize(900, 560, false); D.renderer.render(D.scene, cam); return D.renderer.domElement.toDataURL('image/jpeg', .85); }""", [dt])
            open(f"{OUT}_{name}.jpg", "wb").write(base64.b64decode(u.split(',')[1]))
        print("errors:", errs or "none"); await b.close()
asyncio.run(main())
