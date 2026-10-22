"""2.60: the headset's recenter (hold the Meta button). On the menus the panels come round in front of you, where you now stand and
face. In a game the world doesn't jump: you stay on the same spot facing the same way (the recenter only moves the headset's idea
of "forward"). A fake headset turns and steps aside in the room, then a recenter makes that spot the room's new middle.
Usage: python3 dev/test_260.py dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
SETUP = open(os.path.join(HERE, "test_mp.py")).read().split('SETUP = """', 1)[1].split('"""', 1)[0]
JS = """() => { const T = D.THREE, V = D.vr, o = {}, Y = new T.Vector3(0, 1, 0);
  try { localStorage.setItem('jt-age', 'ok'); } catch (_) {} D.VRUI.rulesOk = true; V.on = true; D.setVRON && D.setVRON(true);
  const yawOf = q => { const f = new T.Vector3(0, 0, -1).applyQuaternion(q); return Math.atan2(-f.x, -f.z); };
  const recenter = () => { L.head.x = 0; L.head.z = 0; hq.identity(); V.resetPend = true; V.reUI = true; };   // the room's middle is now where you stand, facing ahead
  // --- menus: face 100 degrees round and 1 m aside, open the menu, recenter
  L.head.set(1, 1.7, -.5); hq.setFromAxisAngle(Y, 1.75); D.vruiOpen('mode'); D.vruiTick(1 / 60);
  const front = () => { const R = D.VRUI.root; R.updateMatrixWorld(true); const I = V.readInputs(), h = I.head, a = yawOf(I.headQ);
    const pos = new T.Vector3(); R.getWorldPosition(pos); return [+Math.abs(Math.atan2(Math.sin(R.rotation.y - a), Math.cos(R.rotation.y - a))).toFixed(3), +Math.hypot(pos.x - h.x, pos.z - h.z).toFixed(3)]; };
  o.menuBefore = front();
  recenter(); o.menuStale = front(); D.vruiTick(1 / 60); o.menuAfter = front();
  // --- in a game: play a little, then the same
  D.set.edges = 'island'; D.setMode('hike'); D.set.size = 'small'; D.generate(); D.vruiClose(); D.state = 'play'; placeAt(D.P.x, D.P.z); V.placeAt = true;
  L.head.set(.8, 1.7, .6); hq.setFromAxisAngle(Y, -.9); frames(30);
  const before = [D.P.x, D.P.z, yawOf(V.readInputs().headQ)];
  recenter(); frames(2); const after = [D.P.x, D.P.z, yawOf(V.readInputs().headQ)];
  o.gameMoved = +Math.hypot(after[0] - before[0], after[1] - before[1]).toFixed(3); o.gameTurned = +Math.abs(Math.atan2(Math.sin(after[2] - before[2]), Math.cos(after[2] - before[2]))).toFixed(3);
  // still walks normally afterwards
  pad.L.sy = -1; frames(30); pad.L.sy = 0; o.walked = +Math.hypot(D.P.x - after[0], D.P.z - after[1]).toFixed(2);
  // without the fix the world would have jumped this far:
  return o; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context()).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto('file://' + os.path.abspath(sys.argv[1])); await pg.wait_for_timeout(800)
        await pg.evaluate(SETUP, "solo")
        r = await pg.evaluate(JS); print(json.dumps(r))
        ok = r["menuBefore"][0] < .05 and r["menuStale"][0] > 1 and r["menuAfter"][0] < .05 and r["menuAfter"][1] < .05 \
             and r["gameMoved"] < .05 and r["gameTurned"] < .02 and r["walked"] > 1
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
