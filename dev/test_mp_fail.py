"""Online play when things go wrong (1.34): a wrong code, different versions, a friend who drops out suddenly, the relay login.
Needs the local PeerJS server (dev/peer_server.js). Usage: python3 dev/test_mp_fail.py /tmp/dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
T = 'file://' + os.path.abspath(sys.argv[1])
INIT = "() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setVR(true); D.setMode('pvp'); D.MP.peerOpts = { host: '127.0.0.1', port: 9000, path: '/jt', secure: false }; window.tick = setInterval(() => D.mpTick(.1), 100); return 1; }"
async def wait(pg, js, secs):
    for _ in range(int(secs * 4)):
        if await pg.evaluate(js): return True
        await pg.wait_for_timeout(250)
    return False
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"])
        async def page():
            pg = await (await b.new_context(viewport={"width": 300, "height": 200})).new_page(); await pg.goto(T); await pg.wait_for_timeout(600); await pg.evaluate(INIT); return pg
        A, B = await page(), await page(); out = {}; errs = []
        for pg in (A, B): pg.on("pageerror", lambda e: errs.append(str(e)))
        out["relayLogin"] = await A.evaluate("async () => { const r = await D.mpRelay(); return r.length ? [r[0].username.includes(':'), r[0].credential.length, r[0].urls.length] : 'none'; }")
        # 1. a wrong code
        await B.evaluate("() => { D.mpJoin('0000'); return 1; }")
        await wait(B, "() => D.MP.status.includes('No game found')", 15)
        out["wrongCode"] = await B.evaluate("() => [D.MP.status, D.MP.code === '']")
        # 2. a normal connection, then the host pretends to be an older version
        await A.evaluate("() => { D.mpHost(); return 1; }"); await wait(A, "() => D.MP.status.includes('Waiting')", 15); code = await A.evaluate("() => D.MP.code")
        await B.evaluate(f"() => {{ D.mpJoin('{code}'); return 1; }}"); out["connects"] = await wait(B, "() => D.MP.on", 25)
        await A.evaluate("() => { D.MP.conn.send({ t: 'hi', v: '0.99' }); D.MP.conn.send({ t: 'start', seed: 5, set: {}, hx: 0, hz: 0 }); return 1; }"); await B.wait_for_timeout(1500)
        out["versionMismatch"] = await B.evaluate("() => [D.MP.status, D.seed !== 5]")
        # 3. the guest's headset suddenly goes away (no goodbye): the host notices
        await B.close()
        out["hostNoticesDrop"] = await wait(A, "() => !D.MP.on", 20)
        out["hostStatusAfter"] = await A.evaluate("() => D.MP.status"); out["hostStillHasCode"] = await A.evaluate("() => !!D.MP.code && !!D.MP.peer")
        # 4. a new friend can join the same code afterwards
        C = await page(); await C.evaluate(f"() => {{ D.mpJoin('{code}'); return 1; }}"); out["rejoinSameCode"] = await wait(C, "() => D.MP.on", 25)
        print(json.dumps(out)); print("errors:", errs or "none"); await b.close()
asyncio.run(main())
