"""2.28: open games. A host makes the room Public; a friend's "Find a game" list shows it (host, mode, map, players); one click joins; the host
starts and the list says Playing; the host kicks the friend (they're sent back and can't rejoin); Private takes it off the list.
Also: the rules screen comes first, once. Needs the PeerJS server (dev/peer_server.js) and starts its own local rooms list (dev/rooms_server.mjs).
Usage: python3 dev/test_rooms.py dbg.html"""
import os, sys, asyncio, json, re, subprocess, time, shutil, tempfile
from playwright.async_api import async_playwright
here = os.path.dirname(os.path.abspath(__file__)); tmp = tempfile.mkdtemp(prefix="jt-rooms-"); shutil.copy(sys.argv[1], os.path.join(tmp, "g.html"))
web = subprocess.Popen([sys.executable, "-m", "http.server", "8766", "--bind", "127.0.0.1"], cwd=tmp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
rs = subprocess.Popen(["node", os.path.join(here, "rooms_server.mjs"), "8787", tmp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.5)
T = "http://127.0.0.1:8766/g.html"
src = open(os.path.join(here, "test_mp.py")).read(); SETUP = re.search(r'SETUP = """(.*?)"""', src, re.S).group(1)
async def run_frames(pg, n, chunk=6):
    for _ in range(n // chunk): await pg.evaluate(f"() => frames({chunk})"); await pg.wait_for_timeout(chunk * 16)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--disable-features=WebRtcHideLocalIpsWithMdns"])
        A = await (await b.new_context(viewport={"width": 400, "height": 300})).new_page(); B = await (await b.new_context(viewport={"width": 400, "height": 300})).new_page(); errs = []
        for nm, pg in (("host", A), ("guest", B)): pg.on("pageerror", lambda e, nm=nm: errs.append(nm + " PE " + str(e)))
        await A.goto(T); await B.goto(T); await A.wait_for_timeout(800)
        out = {}
        out["rulesFirst"] = await B.evaluate("() => { D.setVR(true); try { localStorage.removeItem('jt-rules'); } catch (_) {} D.vruiOpen('mode'); return D.VRUI.stage; }")
        await A.evaluate(SETUP, "host"); await B.evaluate(SETUP, "guest")
        await A.evaluate("() => { D.MP.roomsUrl = 'http://127.0.0.1:8787/rooms'; D.MP.tag = 'RONHOST'; D.mpHost(); }"); await B.evaluate("() => { D.MP.roomsUrl = 'http://127.0.0.1:8787/rooms'; D.MP.tag = 'BUDDY'; }")
        for _ in range(50):
            await A.wait_for_timeout(200)
            if "Waiting" in (await A.evaluate("() => D.MP.status")): break
        code = await A.evaluate("() => D.MP.code")
        out["privateListed"] = await A.evaluate("() => fetch('http://127.0.0.1:8787/rooms?v=' + D.VERSION_ || '').then(r => r.json()).then(o => o.rooms.length)")
        await A.evaluate("() => { D.setMode('hunt'); D.set.dino = true; D.set.huntMap = 'island'; D.set.size = 'large'; D.roomsSetPublic(true); D.roomsBeat(.1); }"); await A.wait_for_timeout(600)
        await B.evaluate("() => { D.roomsTick(10); }"); await B.wait_for_timeout(800)
        out["list"] = await B.evaluate("() => D.MP.rooms")
        await B.evaluate(f"() => D.roomJoin('{code}')")
        for _ in range(80):
            await A.wait_for_timeout(250)
            if await A.evaluate("() => D.MP.on") and await B.evaluate("() => D.MP.on"): break
        out["joined"] = [await A.evaluate("() => D.MP.on"), await B.evaluate("() => D.MP.code")]
        await A.evaluate("() => { D.setSeed(4242); D.generate(); D.state = 'play'; placeAt(D.P.x, D.P.z); D.mpSendStart(); D.MP.pubT = 0; D.roomsBeat(.1); return 1; }"); await A.wait_for_timeout(700)
        out["listPlaying"] = await A.evaluate("() => fetch('http://127.0.0.1:8787/rooms').then(r => r.json()).then(o => o.rooms.map(r => [r.host, r.mode, r.dino, r.map, r.n, r.st]))")
        for _ in range(60):
            await B.wait_for_timeout(250)
            if await B.evaluate("() => D.state === 'play' && D.seed === 4242"): break
        await A.evaluate("() => { const L = [...D.MP.links.values()][0]; D.mpKick(L.id); }")
        for _ in range(30):
            await B.wait_for_timeout(200)
            if not await B.evaluate("() => D.MP.code"): break
        out["kicked"] = await B.evaluate("() => [D.MP.code, D.MP.status, D.state]")
        out["rejoinBlocked"] = await B.evaluate(f"() => {{ D.roomJoin('{code}'); return [D.MP.code, D.MP.status]; }}")
        await A.evaluate("() => { D.roomsSetPublic(false); }"); await A.wait_for_timeout(500)
        out["afterPrivate"] = await A.evaluate("() => fetch('http://127.0.0.1:8787/rooms').then(r => r.json()).then(o => o.rooms.length)")
        print(json.dumps(out)); print("errors:", errs or "none")
        L = out["list"] or []
        ok = out["rulesFirst"] == "rules" and len(L) == 1 and L[0]["host"] == "RONHOST" and L[0]["mode"] == "hunt" and L[0]["dino"] and L[0]["map"] == "L" and L[0]["code"] == code \
             and out["joined"][0] and out["joined"][1] == code and out["listPlaying"] and out["listPlaying"][0][4] == 2 and out["listPlaying"][0][5] == "play" \
             and out["kicked"][0] == "" and "removed" in out["kicked"][1] and out["rejoinBlocked"][0] == "" and out["afterPrivate"] == 0 and not errs
        print("PASS" if ok else "FAIL"); await b.close(); return ok
try: ok = asyncio.run(main())
finally: web.terminate(); rs.terminate(); shutil.rmtree(tmp, ignore_errors=True)
sys.exit(0 if ok else 1)
