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
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader","--enable-webgl","--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width":900,"height":500})).new_page(); errs=[]
        pg.on("pageerror", lambda e: errs.append("PE "+str(e)))
        pg.on("console", lambda m: errs.append("CON "+m.text) if m.type=="error" else None)
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        await pg.evaluate(SETUP)
        out = {}
        out["a"] = await pg.evaluate("""() => { D.vruiOpen('intro'); frames(5); const r = { stage: D.VRUI.stage, state: D.state };
          D.intro.t0 -= 9000; frames(2); r.after9s = D.VRUI.stage; click(); r.afterClick = D.VRUI.stage;
          r.aimHike = aimAt('mode', 'Hiking'); frames(2); r.hover = D.VRUI.panels.mode.hov.map(w => w.label).join(','); click(); r.afterHike = D.VRUI.stage; r.gameModeIsHike = D.set && document.body.classList.contains('mode-hike'); r.mode = D.set ? 'ok' : '';
          aimAt('setup', 'XXL'); click(); r.size = D.set.size; aimAt('setup', 'L'); click(); r.size2 = D.set.size;
          return r; }""")
        # screenshot of setup panel
        async def shot(name):
            data = await pg.evaluate("""() => { const c = D.camera; c.position.copy(toW(L.head)); c.quaternion.identity(); c.rotateY(D.vr.yaw); c.fov = 90; c.aspect = 900/500; c.updateProjectionMatrix(); c.updateMatrixWorld();
              D.renderer.render(D.scene, c); return D.renderer.domElement.toDataURL('image/jpeg', .85); }""")
            open(f"/tmp/{name}.jpg","wb").write(base64.b64decode(data.split(",")[1]))
        await shot("vr_setup")
        out["b"] = await pg.evaluate("""() => { const r = {}; aimAt('setup', 'Start'); click(); r.stage = D.VRUI.stage; return r; }""")
        await pg.wait_for_timeout(9000)
        out["c"] = await pg.evaluate("""() => { frames(3); return { stage: D.VRUI.stage, dio: !!D.VRUI.dio, state: D.state, worldVis: D.world && D.world.visible }; }""")
        await shot("vr_preview")
        out["d"] = await pg.evaluate("""() => { click(); for (let i = 0; i < 60; i++) frames(1); const head = toW(L.head);
          return { state: D.state, stage: D.VRUI.stage, fade: +D.VRUI.fadeV.toFixed(2), headToSpawn: +Math.hypot(head.x - D.P.x, head.z - D.P.z).toFixed(2), worldVis: D.world.visible }; }""")
        # Y hold -> pause menu, resume
        out["e"] = await pg.evaluate("""() => { pad.L.b = 1; frames(50); const r = { state: D.state, stage: D.VRUI.stage }; pad.L.b = 0; frames(2);
          aimAt('pause', 'Resume'); click(); r.after = D.state; r.stage2 = D.VRUI.stage; return r; }""")
        print(json.dumps(out, indent=0)); print("errors:", errs or "none"); await b.close()
asyncio.run(main())
