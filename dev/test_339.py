"""3.39 (live for everyone since 3.40): the home screen and friends. The first menu is three panels (you, the ways to play, your friends);
without Dev there is no Competitive row. Friend codes: A asks B by code, B accepts, both see each other online with what they're
doing. A invites B: a private room opens, B joins from the invite, A stays on the home screen with the party listed. A hands the host to B;
B picks Hunting (the party goes to the lobby) and starts: both play. C joins by code: A finds C under Recent, asks, C says no. A removes B:
gone on both sides. Alone, Play on Hiking goes straight into a map. Needs the PeerJS server.
Usage: python3 dev/test_339.py dbg.html"""
import os, sys, asyncio, json, re, subprocess, time, shutil, tempfile
from playwright.async_api import async_playwright
here = os.path.dirname(os.path.abspath(__file__)); tmp = tempfile.mkdtemp(prefix="jt-339-"); shutil.copy(sys.argv[1], os.path.join(tmp, "g.html"))
web = subprocess.Popen([sys.executable, "-m", "http.server", "8771", "--bind", "127.0.0.1"], cwd=tmp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
T = "http://127.0.0.1:8771/g.html"
SETUP = re.search(r'SETUP = """(.*?)"""', open(os.path.join(here, "test_280.py")).read(), re.S).group(1)
SETUP = SETUP.replace("return true; }", "D.FRD.tryT = 0; D.VRUI.ageOk = true; D.VRUI.rulesOk = true; D.set.size = 'small'; window.W = (p, l) => D.VRUI.panels[p].widgets.find(w => w.label === l); window.ft = n => { for (let i = 0; i < n; i++) D.frTick(1); }; return true; }")
async def run(pages, n, chunk=4):
    for _ in range(n // chunk):
        for pg in pages: await pg.evaluate(f"() => {{ frames({chunk}); ft(3); }}")
        await pages[0].wait_for_timeout(chunk * 25)
async def until(pgs, js, tries=200):
    for _ in range(tries):
        if all([await pg.evaluate(js) for pg in pgs]): return True
        await run(pgs, 4)
    return False
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--disable-features=WebRtcHideLocalIpsWithMdns"])
        pgs = [await (await b.new_context(viewport={"width": 320, "height": 240})).new_page() for _ in range(3)]; A, B, C = pgs; errs = []
        for nm, pg in zip("ABC", pgs): pg.on("pageerror", lambda e, nm=nm: errs.append(nm + " PE " + str(e)[:200]))
        for i, pg in enumerate(pgs): await pg.goto(T); await pg.wait_for_timeout(500); await pg.evaluate(SETUP, [12, 30, 3][i])
        out = {}
        # without Dev (3.40: live for everyone): the same home screen, but no Competitive row, no Dev or Old menu button
        out["plain"] = await C.evaluate("() => { D.DEV.ok = false; D.vruiOpen('mode'); const P = D.VRUI.panels.hplay; D.uiDraw(P); const r = [D.VRUI.stage, W('hplay', 'Competitive').hide(), W('hme', 'Dev').hide(), W('hme', 'Old menu').hide(), W('hplay', 'Join a game').y, W('hplay', 'Hunting').hide()]; D.DEV.ok = true; D.uiDraw(P); r.push(W('hplay', 'Join a game').y); return r; }")
        # Dev: the home screen; the old menu and back
        out["home"] = await A.evaluate("() => { D.vruiOpen('mode'); const v = k => D.VRUI.panels[k].mesh.visible; const r = [D.VRUI.stage, v('hme'), v('hplay'), v('hfr'), v('mode')]; W('hme', 'Old menu').on(); r.push(D.VRUI.stage); W('mode', 'New menu').on(); r.push(D.VRUI.stage); return r; }")
        await B.evaluate("() => { D.vruiOpen('mode'); return 1; }"); await C.evaluate("() => { D.vruiOpen('mode'); return 1; }")
        out["up"] = await until(pgs, "() => D.FRD.up")
        ca, cb, cc = [await pg.evaluate("() => D.FRD.code") for pg in pgs]; out["codes"] = len({ca, cb, cc}) == 3 and all(re.fullmatch("[A-HJ-NP-Z2-9]{6}", c) for c in (ca, cb, cc))
        # A asks B (typed on the keyboard); B sees a request and accepts
        out["bad"] = await A.evaluate("() => { D.frAdd('nope'); const a = D.FRD.msg; D.frAdd(D.FRD.code); return [a.slice(0, 12), D.FRD.msg.slice(0, 15), D.FRD.list.length]; }")
        await A.evaluate(f"() => {{ W('hfr', 'Add by code').on(); const k = D.VRUI.keyFor; D.VRUI.tagEdit = '{cb.lower()}'; W('tag', 'OK').on(); window.kf = [k, D.VRUI.stage]; return 1; }}")
        out["asked"] = await A.evaluate("() => [window.kf, D.FRD.list.map(f => [f.p, f.on])]")
        out["req"] = await until([B], f"() => D.FRD.reqs.length === 1 && D.FRD.reqs[0].c === '{ca}' && D.FRD.reqs[0].n === 'P12'")
        out["pendingStill"] = await A.evaluate("() => D.FRD.list[0].p")
        await B.evaluate("() => { const r = D.frRows()[0]; D.frAccept(r.c); return 1; }")
        out["friends"] = await until([A, B], "() => D.FRD.list.length === 1 && !D.FRD.list[0].p && D.FRD.list[0].on && !!D.FRD.list[0].st")
        out["see"] = [await A.evaluate("() => [D.FRD.list[0].n, D.FRD.list[0].st.w, D.frRows()[0].k]"), await B.evaluate("() => [D.FRD.list[0].n, D.FRD.list[0].st.w]")]
        # A invites B: a private room; B joins from the invite; A is still on the home screen with the party
        await A.evaluate(f"() => {{ D.frInvite('{cb}'); return 1; }}")
        out["inv"] = await until([B], "() => D.FRD.invs.length === 1 && /^\\d{4}$/.test(D.FRD.invs[0].room)", 300)
        out["aRoom"] = await A.evaluate("() => [D.MP.host, !!D.MP.pub, D.MP.code.length, D.VRUI.stage]")
        await B.evaluate("() => { D.frJoin(D.FRD.invs[0].room); return 1; }")
        out["joined"] = await until([A, B], "() => D.MP.on && D.mpOpen().length === 1 && D.mpOpen()[0].tag !== undefined", 300)
        await run([A, B], 40)
        out["party"] = await A.evaluate("() => [D.VRUI.stage, D.mpRoster().map(r => r.tag).join(','), D.FRD.list[0].st.room === D.MP.code, D.FRD.recent.length]")
        out["bStage"] = await B.evaluate("() => [D.VRUI.stage, D.mpGuest(), D.FRD.invs.length]")
        # host swap from the party list (tap, tap again); then B picks Hunting and starts
        out["swap"] = await A.evaluate("() => { const w = D.VRUI.panels.hme.widgets.filter(q => q.labelFn && q.w === 495)[1]; const l0 = w.labelFn(); w.on(); const l1 = w.labelFn(); w.on(); return [l0, l1, D.MP.host, D.mpGuest()]; }")
        out["bHost"] = await until([B], "() => D.MP.host && !D.mpGuest()")
        await B.evaluate("() => { D.vruiOpen('home'); D.HOME.sel = 'hunt'; D.set.dino = false; W('hplay', 'Play').on(); return 1; }")
        await run([A, B], 24)
        out["lobby"] = [await B.evaluate("() => [D.VRUI.stage, D.gameMode, W('hplay', 'Play').labelFn(), D.MP.code.length]"), await A.evaluate("() => [D.gameMode, D.mpGuest(), D.mpRoster().find(r => r.host).tag]")]
        await B.evaluate("() => { W('setup', 'Start').on(); return 1; }")
        out["preview"] = await until([A, B], "() => D.VRUI.stage === 'preview' && !D.MP.genBusy", 400)
        await B.evaluate("() => { W('preview', 'Play this map').on(); return 1; }")
        out["play"] = await until([A, B], "() => D.state === 'play'", 300)
        await run([A, B], 20); out["st"] = await until([A], "() => D.FRD.list[0].st && D.FRD.list[0].st.w === 'Hunting'")
        # C joins by code: A has C under Recent, asks; C says no
        code = await A.evaluate("() => D.MP.code"); await C.evaluate(f"() => {{ D.mpJoin('{code}'); return 1; }}")
        out["recent"] = await until([A, B, C], f"() => D.FRD.code === '{cc}' || D.FRD.code === '{cb}' || D.FRD.recent.some(r => r.c === '{cc}')", 400)
        out["dbg"] = [await C.evaluate("() => [D.MP.status, D.MP.on, D.mpOpen().length, D.DEV.ok]"), await A.evaluate("() => [D.mpOpen().length, D.FRD.recent, D.MP.code, D.MP.host]"), await B.evaluate("() => [D.mpOpen().length, D.FRD.recent, D.MP.host]")]
        await A.evaluate(f"() => {{ D.FRD.tab = 'recent'; const r = D.frRows().find(q => q.c === '{cc}'); if (r) D.frAdd(r.c); return 1; }}")
        out["cReq"] = await until([A, C], f"() => D.FRD.code === '{ca}' || D.FRD.reqs.some(r => r.c === '{ca}')", 300)
        await C.evaluate(f"() => {{ D.frDeny('{ca}'); return 1; }}")
        out["denied"] = await until([A, C], f"() => D.FRD.code === '{cc}' || !D.FRD.list.some(f => f.c === '{cc}')", 300)
        # A removes B: gone on both sides (and it's remembered across a reload: the saved list)
        out["saved"] = await B.evaluate("() => JSON.parse(localStorage.getItem('jt-friends')).length")
        await A.evaluate(f"() => {{ D.frRemove('{cb}'); return 1; }}")
        out["removed"] = await until([A, B], "() => D.FRD.list.length === 0", 300)
        # alone: Play on Hiking goes straight in
        await C.evaluate("() => { D.mpLeave(); D.state = 'menu'; D.vruiOpen('mode'); D.HOME.sel = 'hike'; W('hplay', 'Play').on(); return 1; }")
        out["soloPv"] = await until([C], "() => D.VRUI.stage === 'preview'", 400)
        await C.evaluate("() => { W('preview', 'Play this map').on(); return 1; }")
        out["solo"] = await until([C], "() => D.state === 'play' && D.gameMode === 'hike' && !D.MP.code", 300)
        print(json.dumps(out))
        ok = out["plain"] == ["home", True, True, True, 136 + 4 * 161, False, 136 + 5 * 134] and out["home"] == ["home", True, True, True, False, "mode", "home"] and out["up"] and out["codes"] \
             and out["bad"][2] == 0 and out["asked"] == [["friend", "home"], [[True, False]]] and out["req"] and out["pendingStill"] and out["friends"] \
             and out["see"] == [["P30", "In the menus", "fr"], ["P12", "In the menus"]] and out["inv"] and out["aRoom"] == [True, False, 4, "home"] and out["joined"] \
             and out["party"][0] == "home" and out["party"][1] == "P12,P30" and out["party"][2] and out["party"][3] == 0 and out["bStage"] == ["lobby", True, 0] \
             and out["swap"][0] == "P30" and "host? Tap again" in out["swap"][1] and out["swap"][2:] == [False, True] and out["bHost"] \
             and out["lobby"][0][:3] == ["lobby", "hunt", "To the lobby"] and out["lobby"][1] == ["hunt", True, "P30"] and out["play"] and out["st"] \
             and out["recent"] and out["cReq"] and out["denied"] and out["saved"] == 1 and out["removed"] and out["preview"] and out["soloPv"] and out["solo"]
        print("PASS" if ok and not errs else "FAIL", errs[:5]); print("errors: none" if not errs else "errors: " + str(errs[:5])); await b.close()
    if not ok or errs: sys.exit(1)
try: asyncio.run(main())
finally: web.terminate()
