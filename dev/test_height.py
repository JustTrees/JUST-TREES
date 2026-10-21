"""VR height check (1.53): hold still while the meter fills; sitting gets lifted to standing height in the game so you don't crouch;
ducking from your seat still crouches; a moving head doesn't fill the meter. Usage: python3 dev/test_height.py /tmp/dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 300, "height": 200})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); const out = {}, T = D.THREE, V = D.vr;
          D.setVR(true); V.on = true; let headY = 1.12, wob = 0;
          V.readInputs = () => ({ head: new T.Vector3(V.ox, V.oy + headY + (wob ? Math.sin(performance.now()) * .2 : 0), V.oz), headQ: new T.Quaternion(), hands: {} });
          D.vrHeightCheck('mode'); out.stage = D.VRUIstage;
          wob = 1; for (let i = 0; i < 60; i++) D.vruiTick(.05); out.meterWhileMoving = +(D.VRUI.hk || 0).toFixed(2); out.stillOnHeight = D.VRUIstage === 'height';
          wob = 0; let n = 0; while (D.VRUIstage === 'height' && n < 200) { D.vruiTick(.05); n++; } out.secondsStill = +(n * .05).toFixed(1);
          out.after = D.VRUIstage; out.offsetM = +V.hOff.toFixed(2); out.calibrated = V.hCal;
          // in the game, sitting: standing height, no crouch
          D.setMode('hunt'); D.set.size = 'small'; D.generate(); D.state = 'play'; V.cl = null; V.goodX = undefined; V.placeAt = true; V.yaw = 0;
          for (let i = 0; i < 40; i++) { D.vrTick(1 / 60); D.update(1 / 60); D.vrAfterMove(1 / 60); }
          out.gameEyeHeightM = +V.headLocalY.toFixed(2); out.crouchingSeated = D.P.crouch;
          headY = .72; for (let i = 0; i < 40; i++) { D.vrTick(1 / 60); D.update(1 / 60); D.vrAfterMove(1 / 60); }
          out.crouchWhenDucking = D.P.crouch;
          return out; }""")
        print(json.dumps(r)); print("errors:", errs[:8] or "none")
        await b.close()
asyncio.run(main())
