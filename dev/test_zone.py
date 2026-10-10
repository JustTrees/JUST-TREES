"""VR closing zone (1.43): stages planned from round length, hold and speed; each circle inside the last; follows the round clock;
hurts health (not shield) outside; next circle on the map; settings row. Usage: python3 dev/test_zone.py /tmp/dbg.html [/tmp/zone.png]"""
import os, sys, asyncio, json, base64
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1]); SHOT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/zone.png'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 640, "height": 400})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        pg.on("console", lambda m: errs.append("CON " + m.text) if m.type == "error" else None)
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); const out = {};
          D.setVR(true); D.setMode('pvp'); Object.assign(D.set, { size: 'small', weather: 'clear', zone: 'on', roundMin: 5, zoneHold: 15, zoneSpeed: 5 }); D.generate(); D.state = 'play';
          const Z = D.zone; out.zoneOn = !!Z && Z.vr; const C = Z.circles; out.stages = C.length - 1;
          out.radii = C.map(c => Math.round(c[2])); out.nested = C.every((c, i) => !i || Math.hypot(c[0] - C[i - 1][0], c[1] - C[i - 1][1]) + c[2] <= C[i - 1][2] + .01);
          out.timeline = [10, 20, 45, 1e4].map(e => { D.zoneSeek(Z, e); return Z.phase + Z.stage; });
          D.zoneSeek(Z, 27.5); out.halfwayRadius = [Math.round(Z.r), Math.round((C[0][2] + C[1][2]) / 2)];
          // standing outside the final zone: health drops, shield doesn't
          D.zoneSeek(Z, 1e4); const fx = C[C.length - 1][0], fz = C[C.length - 1][1], fr = C[C.length - 1][2];
          let ox = fx + fr + 25, oz = fz; if (Math.abs(ox) > D.P.x * 0 + 180) ox = fx - fr - 25;
          D.P.x = ox; D.P.z = oz; D.P.y = D.groundAt(ox, oz); D.MP.hp = 100; D.MP.sh = 50; Z.vr = true;
          for (let i = 0; i < 300; i++) D.updateZone(1 / 60);
          out.afterOutside5s = [D.MP.hp, D.MP.sh]; out.fogTinted = Z.out > .3;
          D.drawMap(document.getElementById('miniMap')); window._map = document.getElementById('miniMap').toDataURL('image/png');
          return out; }""")
        d = await pg.evaluate("() => window._map"); open(SHOT, 'wb').write(base64.b64decode(d.split(',')[1]))
        print(json.dumps(r)); print("errors:", errs[:8] or "none")
        await b.close()
asyncio.run(main())
