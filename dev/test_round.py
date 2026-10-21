"""PvP round clock (1.51): starts when you drop in even playing alone, counts down, ends the round with the board and your own New map button;
the zone's last circle is small. Usage: python3 dev/test_round.py /tmp/dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 300, "height": 200})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""async () => { window.FREEZE = true; D.renderer.setAnimationLoop(null); const out = {}, T = D.THREE, V = D.vr;
          D.setVR(true); V.on = true; D.setMode('pvp'); V.readInputs = () => ({ head: new T.Vector3(D.P.x, D.P.y + 1.7, D.P.z), headQ: new T.Quaternion(), hands: {} });
          Object.assign(D.set, { size: 'medium', weather: 'clear', roundMin: 6, zone: 'on', zoneHold: 30, zoneSpeed: 3 });
          D.generate(); D.vruiOpen('preview'); out.clockBefore = D.MP.roundLeft;
          D.vruiDropIn(); for (let i = 0; i < 40 && D.state !== 'play'; i++) D.vruiTick(.1);
          out.playing = D.state; out.clockAtStart = Math.round(D.MP.roundLeft);
          for (let i = 0; i < 30; i++) D.mpTick(.1); out.clockAfter3s = Math.round(D.MP.roundLeft);
          const C = D.zone.circles; out.lastZoneRadiusM = Math.round(C[C.length - 1][2]); out.firstZoneRadiusM = Math.round(C[0][2]);
          D.MP.roundLeft = .3; D.mpTick(.5); out.afterEnd = [D.state, D.VRUIstage];
          const P = D.VRUI.panels.over, btn = P.widgets.find(w => w.label === 'New map'); out.newMapButtonShown = !!btn && !(btn.hide && btn.hide());
          btn.on(); await new Promise(res => setTimeout(res, 900)); for (let i = 0; i < 10; i++) D.vruiTick(.1); out.nextMap = D.VRUIstage;
          return out; }""")
        print(json.dumps(r)); print("errors:", errs[:8] or "none")
        await b.close()
asyncio.run(main())
