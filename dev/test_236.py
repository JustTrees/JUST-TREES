import os, sys
TARGET = 'file://' + os.path.abspath(sys.argv[1])
import asyncio, json, base64
from playwright.async_api import async_playwright
SETUP = """() => { window.FREEZE = true; for (const el of document.body.children) if (el.tagName !== 'CANVAS') el.style.display = 'none';
  const T = D.THREE, V = D.vr; V.on = true; D.setVR(true);
  window.L = { head: new T.Vector3(0, 1.65, 0), R: new T.Vector3(.2, 1.3, -.25), Lh: new T.Vector3(-.2, 1.3, -.25) };
  window.pad = { R: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 }, L: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 } };
  window.qs = { R: new T.Quaternion(), L: new T.Quaternion() };
  const toW = v => v.clone().applyAxisAngle(new T.Vector3(0, 1, 0), V.yaw).add(new T.Vector3(V.ox, V.oy, V.oz)); window.toW = toW;
  V.readInputs = () => ({ head: toW(L.head), headQ: new T.Quaternion().setFromAxisAngle(new T.Vector3(0,1,0), V.yaw), hands: { right: Object.assign({ pos: toW(L.R), q: qs.R.clone(), rayPos: toW(L.R), rayQ: new T.Quaternion().setFromAxisAngle(new T.Vector3(0,1,0), V.yaw).multiply(qs.R) }, pad.R), left: Object.assign({ pos: toW(L.Lh), q: qs.L.clone(), rayPos: toW(L.Lh), rayQ: qs.L.clone() }, pad.L) } });
  window.tick = n => { for (let i = 0; i < n; i++) D.loop(performance.now()); };
  window.frames = n => { for (let i = 0; i < n; i++) { if (D.VRUI.on || D.VRUI.fadeV > 0 || D.VRUI.fadeGo) D.vruiTick(1/60); if (D.state === 'play') { D.vrTick(1/60); if (!V.climbing) D.update(1/60); D.vrAfterMove(1/60); } } };
  // aim the right controller at a widget of a panel (by label)
  window.aimAt = (pname, label) => { const Pn = D.VRUI.panels[pname], w = Pn.widgets.find(q => q.label === label);
    const geo = Pn.mesh.geometry.parameters, u = 1 - (w.x + w.w / 2) / Pn.W, vv = (w.y + w.h / 2) / Pn.H;
    const th = geo.thetaStart + u * geo.thetaLength, y = Pn.mesh.position.y + (.5 - vv) * geo.height;
    const tgt = D.VRUI.root.localToWorld(new T.Vector3(geo.radiusTop * Math.sin(th), y, geo.radiusTop * Math.cos(th)));
    const from = toW(L.R), m = new T.Matrix4().lookAt(from, tgt, new T.Vector3(0, 1, 0)); qs.R.setFromRotationMatrix(m); return !!w; };
  window.click = () => { pad.R.trig = 1; frames(2); pad.R.trig = 0; frames(2); };
}"""
# 2.36: Snap / Smooth turning. Half a second of full stick: snap turns once (30°), smooth turns ~2.4 rad/s; a light push does nothing; the choice is remembered.
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader","--enable-webgl","--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width":900,"height":500})).new_page(); errs=[]
        pg.on("pageerror", lambda e: errs.append("PE "+str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        await pg.evaluate("""() => { window.FREEZE = true; D.setSeed(5); D.setVR(true); D.setMode('hike'); Object.assign(D.set, { size: 'small', weather: 'clear', hour: 12 }); D.generate(); D.state = 'play'; }""")
        await pg.evaluate(SETUP)
        r = await pg.evaluate("""() => { const out = {}, V = D.vr, run = (sx, n) => { const y0 = V.yaw; pad.R.sx = sx; frames(n); pad.R.sx = 0; frames(2); return +(V.yaw - y0).toFixed(3); };
          D.set.turn = 'snap'; out.snap = run(1, 30);
          D.set.turn = 'smooth'; out.smooth = run(1, 30); out.smoothLeft = run(-1, 30); out.light = run(.15, 30);
          D.vruiOpen('setup'); const w = D.VRUI.panels.me.widgets.find(q => q.label === 'Snap'); w.on(); out.saved = localStorage.getItem('jt-turn'); w.on(); out.saved2 = localStorage.getItem('jt-turn');
          return out; }""")
        print(json.dumps(r))
        ok = abs(r["snap"] + .524) < .01 and -1.3 < r["smooth"] < -1.0 and 1.0 < r["smoothLeft"] < 1.3 and r["light"] == 0 and r["saved"] == "snap" and r["saved2"] == "smooth" and not errs
        print("errors:", errs or ("none" if ok else "CHECKS FAILED")); await b.close(); sys.exit(0 if ok else 1)
asyncio.run(main())
