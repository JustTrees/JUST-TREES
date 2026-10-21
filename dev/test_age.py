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
# 2.29: the age check before the rules. Blank year can't continue; born 21 years ago is turned away (and stays turned away after a reload);
# born 22 years ago goes on to the rules, then "I agree" opens the menu. Only pass/fail is saved. Saves pictures of the three screens next to argv[2].
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader","--enable-webgl","--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width":900,"height":500})).new_page(); errs=[]
        pg.on("pageerror", lambda e: errs.append("PE "+str(e)))
        pg.on("console", lambda m: errs.append("CON "+m.text) if m.type=="error" else None)
        pic = (sys.argv[2] if len(sys.argv) > 2 else "/tmp/age.png")[:-4]
        async def shot(name):
            d = await pg.evaluate("() => D.VRUI.panels.rules.g.canvas.toDataURL('image/png')"); open(f"{pic}-{name}.png", "wb").write(base64.b64decode(d.split(",")[1]))
        async def boot():
            await pg.goto(TARGET); await pg.wait_for_timeout(800); await pg.evaluate(SETUP)
        await boot(); out = {}
        out["a"] = await pg.evaluate("""() => { localStorage.clear(); D.vruiOpen('mode'); frames(3); const r = { stage: D.VRUI.stage, ok: D.rulesOk() };
          aimAt('rules', 'Continue'); click(); r.blankStays = D.VRUI.stage === 'rules' && !localStorage.getItem('jt-age');
          const Y = new Date().getFullYear(); aimAt('rules', '−10'); click(); aimAt('rules', '−10'); click(); aimAt('rules', '−1'); click(); r.year = D.VRUI.year; r.want = Y - 21; return r; }""")
        await shot("age")
        out["b"] = await pg.evaluate("""() => { aimAt('rules', 'Continue'); click(); return { stage: D.VRUI.stage, saved: localStorage.getItem('jt-age'), exitShown: !D.VRUI.panels.rules.widgets.find(w => w.label === 'Exit VR').hide() }; }""")
        await shot("sorry")
        await boot()
        out["c"] = await pg.evaluate("""() => { D.vruiOpen('mode'); frames(3); return { stage: D.VRUI.stage, stillNo: !D.VRUI.panels.rules.widgets.find(w => w.label === 'Exit VR').hide() }; }""")
        out["d"] = await pg.evaluate("""() => { localStorage.clear(); D.VRUI.ageNo = false; D.vruiOpen('mode'); frames(3);
          for (let i = 0; i < 2; i++) { aimAt('rules', '−10'); click(); } aimAt('rules', '−1'); click(); aimAt('rules', '−1'); click(); const year = D.VRUI.year;
          aimAt('rules', 'Continue'); click(); const r = { year, saved: localStorage.getItem('jt-age'), stage: D.VRUI.stage, agreeShown: !D.VRUI.panels.rules.widgets.find(w => w.label === 'I agree').hide() };
          r.yearKept = JSON.stringify(Object.assign({}, localStorage)).includes(String(year)); return r; }""")
        await shot("rules")
        out["e"] = await pg.evaluate("""() => { aimAt('rules', 'I agree'); click(); return { stage: D.VRUI.stage, ok: D.rulesOk() }; }""")
        Y = out["a"]["want"] + 21
        good = (out["a"]["stage"] == "rules" and out["a"]["blankStays"] and out["a"]["year"] == Y - 21 and out["b"]["saved"] == "no" and out["b"]["exitShown"]
                and out["c"]["stage"] == "rules" and out["c"]["stillNo"] and out["d"]["year"] == Y - 22 and out["d"]["saved"] == "ok" and out["d"]["agreeShown"]
                and not out["d"]["yearKept"] and out["e"]["stage"] == "mode" and out["e"]["ok"])
        print(json.dumps(out)); print("errors:", errs or ("none" if good else "CHECKS FAILED")); await b.close(); sys.exit(0 if good else 1)
asyncio.run(main())
