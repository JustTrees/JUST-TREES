"""3.28: Treeocashing from a lobby. The host's online mode row has a Treeocashing button (Dev for now): the room becomes a public
Treeocashing planet. Start with no running planet: everyone in the lobby lands together next to the host; someone joining later
lands somewhere random. Start when a planet is already running with room for the whole lobby: the lobby goes into that one (fills first)
and the friends land next to the one who was hosting. Needs the PeerJS server; starts its own rooms list (dev/rooms_server.mjs).
Usage: python3 dev/test_328.py dbg.html"""
import os, sys, asyncio, json, re, subprocess, time, shutil, tempfile
from playwright.async_api import async_playwright
here = os.path.dirname(os.path.abspath(__file__)); tmp = tempfile.mkdtemp(prefix="jt-328-"); shutil.copy(sys.argv[1], os.path.join(tmp, "g.html"))
web = subprocess.Popen([sys.executable, "-m", "http.server", "8767", "--bind", "127.0.0.1"], cwd=tmp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
rs = subprocess.Popen(["node", os.path.join(here, "rooms_server.mjs"), "8788", tmp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.5)
T = "http://127.0.0.1:8767/g.html"
SETUP = re.search(r'SETUP = """(.*?)"""', open(os.path.join(here, "test_280.py")).read(), re.S).group(1).replace("http://127.0.0.1:9/none", "http://127.0.0.1:8788/rooms")
SETUP = SETUP.replace("return true; }", "window.W = (p, l) => D.VRUI.panels[p].widgets.find(w => w.label === l); return true; }")
async def run(pages, n, chunk=4):
    for _ in range(n // chunk):
        for pg in pages: await pg.evaluate(f"() => frames({chunk})")
        await pages[0].wait_for_timeout(chunk * 25)
async def until(pgs, js, tries=300):
    for _ in range(tries):
        if all([await pg.evaluate(js) for pg in pgs]): return True
        await run(pgs, 4)
    return False
SPH = "() => { const h = D.vr.readInputs().head; return D.glToSphere(D.P.x, D.P.z, [0, 0, 0]); }"
async def apart(a, b):
    pa = await a.evaluate(SPH); pb = await b.evaluate(SPH)
    return round(await a.evaluate(f"() => D.glArc({json.dumps(pa)}, {json.dumps(pb)}) * D.GLOBE.R"), 1)
async def lobby(H, G):
    await H.evaluate("() => { D.mpHost(); return 1; }")
    for _ in range(60):
        await H.wait_for_timeout(200)
        if "Waiting" in (await H.evaluate("() => D.MP.status")): break
    code = await H.evaluate("() => D.MP.code"); await G.evaluate(f"() => {{ D.mpJoin('{code}'); return 1; }}")
    for _ in range(80):
        await H.wait_for_timeout(250)
        if await H.evaluate("() => D.MP.on && D.mpOpen().length > 0") and await G.evaluate("() => D.MP.on"): break
    return code
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--disable-features=WebRtcHideLocalIpsWithMdns"])
        pgs = [await (await b.new_context(viewport={"width": 320, "height": 240})).new_page() for _ in range(5)]; A, B, C, X, Y = pgs; errs = []
        for nm, pg in zip("ABCXY", pgs): pg.on("pageerror", lambda e, nm=nm: errs.append(nm + " PE " + str(e)[:200]))
        for i, pg in enumerate(pgs): await pg.goto(T); await pg.wait_for_timeout(500); await pg.evaluate(SETUP, [12, 30, 3, 5, 7][i])
        out = {}
        # 1) A's lobby with B: Treeocashing, Start (no planet running) → together; C joins later → random
        code = await lobby(A, B); await A.evaluate("() => { D.vruiOpen('setup'); return 1; }")
        out["btn"] = await A.evaluate("() => { const w = W('setup', 'Treeocashing'); w.on(); return [D.geoMode(), D.MP.pub, D.roomMapName(), !!w.active()]; }")
        await run([A, B], 8); out["bSet"] = await B.evaluate("() => [D.set.geoNet, D.set.huntMap, D.gameMode]")
        out["back"] = await A.evaluate("() => { W('setup', 'Hiking').on(); const r = [D.geoMode(), D.MP.pub, D.set.geoNet]; W('setup', 'Treeocashing').on(); return r; }")
        await A.evaluate("() => { W('setup', 'Start').on(); return 1; }")
        out["play1"] = await until([A, B], "() => D.state === 'play' && D.GEO.on && D.GLOBE && D.geoNet()")
        await run([A, B], 20); out["together"] = await apart(A, B)
        await C.evaluate(f"() => {{ D.mpJoin('{code}'); return 1; }}")
        out["cIn"] = await until([C], "() => D.state === 'play' && D.GEO.on && D.geoNet()", 500)
        out["cDbg"] = await C.evaluate("() => [D.GLOBE.folKey, D.MP.code, D.gameMode, D.set.geoNet]")
        await run([A, B, C], 10); out["cFar"] = await apart(A, C)
        # 2) X runs a public planet; Y hosts a lobby with C... (C leaves A's planet first): Treeocashing + Start → into X's planet, next to each other
        await C.evaluate("() => { D.mpLeave(); D.state = 'menu'; return 1; }")
        await X.evaluate("() => { D.geoNetGo(); return 1; }")
        out["xUp"] = await until([X], "() => D.state === 'play' && D.MP.code && D.MP.pub", 600)
        await X.evaluate("() => { D.MP.pubT = 0; D.roomsBeat(.1); return 1; }"); await X.wait_for_timeout(600)
        xcode = await X.evaluate("() => D.MP.code")
        await A.evaluate("() => { D.mpLeave(); D.state = 'menu'; return 1; }"); await B.evaluate("() => { D.mpLeave(); D.state = 'menu'; return 1; }"); await X.wait_for_timeout(400)
        await X.evaluate("() => { D.MP.pubT = 0; D.roomsBeat(.1); return 1; }"); await X.wait_for_timeout(400)
        out["rooms"] = await Y.evaluate("() => fetch('http://127.0.0.1:8788/rooms?v=' + encodeURIComponent(D.MP.netV)).then(r => r.json()).then(o => [D.MP.netV, o.rooms])")
        await lobby(Y, C); await Y.evaluate("() => { D.vruiOpen('setup'); W('setup', 'Treeocashing').on(); W('setup', 'Start').on(); return 1; }")
        ok2 = False
        for _ in range(300):
            await run([X, Y, C], 4)
            if await Y.evaluate(f"() => D.MP.code === '{xcode}' && D.state === 'play' && D.geoNet()") and await C.evaluate(f"() => D.MP.code === '{xcode}' && D.state === 'play' && D.geoNet() && !D.MP.palTag"): ok2 = True; break
        out["filled"] = ok2
        await run([X, Y, C], 20); out["palTogether"] = await apart(Y, C); out["xFar"] = await apart(X, Y)
        out["xCount"] = await X.evaluate("() => D.mpOpen().length")
        print(json.dumps(out))
        ok = out["btn"][:3] == [True, True, "Treeocashing"] and out["btn"][3] and out["bSet"] == [True, "globe", "hunt"] and out["back"] == [False, False, False] \
             and out["play1"] and out["together"] < 40 and out["cIn"] and out["cFar"] > 300 and out["xUp"] and out["filled"] and out["palTogether"] < 40 and out["xFar"] > 300 and out["xCount"] == 2
        print("PASS" if ok and not errs else "FAIL", errs[:5]); print("errors: none" if not errs else "errors: " + str(errs[:5])); await b.close()
    if not ok or errs: sys.exit(1)
try: asyncio.run(main())
finally: web.terminate(); rs.terminate()
