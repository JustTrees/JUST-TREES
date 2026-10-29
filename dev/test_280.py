"""2.80: Online Treeocashing. One button: no room with space → you open one (public, on the Treeocashing list); others join the same
planet with their own levels; positions travel as points on the planet (each player's layout differs after re-laying the ground);
the host hands over to another player; a newcomer dialling the room's code is sent on to the real host; when the host leaves, the next
player takes over. Needs a local PeerJS server on 127.0.0.1:9000/jt (run through run_all.py --nm).
Usage: python3 dev/test_280.py dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
T = 'file://' + os.path.abspath(sys.argv[1])
SETUP = """(lvl) => { window.FREEZE = true; D.renderer.setAnimationLoop(null); try { localStorage.setItem('jt-geochar', JSON.stringify({ n: lvl, score: 0, kills: 0 })); localStorage.setItem('jt-tag', 'P' + lvl); } catch (_) {}
  D.DEV.ok = true; D.setVR(true); D.setMode('hunt'); Object.assign(D.set, { env: 'climate', land: 'natural', lat: 45, hemi: 1, month: 6, hour: 11, weather: 'clear', density: .5, rough: .5, dino: false });
  D.MP.peerOpts = { host: '127.0.0.1', port: 9000, path: '/jt', secure: false }; D.MP.roomsUrl = 'http://127.0.0.1:9/none'; D.MP.tag = 'P' + lvl;
  const T = D.THREE, V = D.vr; V.on = true; window.hq = new T.Quaternion();
  V.readInputs = () => { const yq = new T.Quaternion().setFromAxisAngle(new T.Vector3(0, 1, 0), V.yaw).multiply(hq), h = new T.Vector3(V.ox, V.oy + 1.6, V.oz);
    return { head: h, headQ: yq.clone(), hands: { right: { pos: h.clone().add(new T.Vector3(.2, -.4, -.3)), q: yq.clone(), rayPos: h.clone(), rayQ: yq.clone(), trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 } } }; };
  window.frames = n => { for (let i = 0; i < n; i++) { if (D.VRUI.fadeGo) { const f = D.VRUI.fadeGo; D.VRUI.fadeGo = null; f(); } if (D.state === 'play') { D.vrTick(1 / 30); D.update(1 / 30); D.vrAfterMove(1 / 30); D.endlessTick(1 / 30); D.geoTick(1 / 30); } D.mpTick(1 / 30); } };
  return true; }"""
async def run(pages, n, chunk=4):
    for _ in range(n // chunk):
        for pg in pages: await pg.evaluate(f"() => frames({chunk})")
        await pages[0].wait_for_timeout(chunk * 25)
async def until(pg, js, tries=120, others=()):
    for _ in range(tries):
        if await pg.evaluate(js): return True
        await run([pg, *others], 4)
    return False
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--disable-features=WebRtcHideLocalIpsWithMdns"])
        pgs = [await (await b.new_context(viewport={"width": 320, "height": 240})).new_page() for _ in range(3)]; A, B, C = pgs; errs = []
        for nm, pg in zip("ABC", pgs): pg.on("pageerror", lambda e, nm=nm: errs.append(nm + " PE " + str(e)[:200]))
        for i, pg in enumerate(pgs): await pg.goto(T); await pg.wait_for_timeout(500); await pg.evaluate(SETUP, [12, 30, 3][i])
        out = {}
        await A.evaluate("() => { D.geoNetGo(); return 1; }")
        out["hostUp"] = await until(A, "() => D.state === 'play' && D.GEO.on && !!D.MP.code && D.MP.host && D.MP.pub", 150)
        code = await A.evaluate("() => D.MP.code"); out["listed"] = await A.evaluate("() => D.set.geoNet")
        await B.evaluate(f"() => {{ D.mpJoin('{code}'); return 1; }}")
        out["bIn"] = await until(B, "() => D.state === 'play' && D.GEO.on && D.MP.on", 500, (A,))
        await run([A, B], 40)
        out["same"] = await A.evaluate("() => [D.seed, D.GEO.found.size, D.MP.roundLeft]") + await B.evaluate("() => [D.seed, D.GEO.found.size, D.MP.roundLeft, D.set.geoNet]")
        # B walks 2 km and lays its ground out again: A must still see B where B really is on the planet
        await B.evaluate("() => { D.P.x += 1900; D.P.z -= 700; D.vr.ox = D.P.x; D.vr.oz = D.P.z; D.vr.placeAt = true; D.enEnsure(D.P.x, D.P.z, 260); D.globeReanchor2(); frames(2); return 1; }")
        await run([A, B], 60)
        bp = await B.evaluate("() => { const h = D.vr.readInputs().head; return D.glToSphere(h.x, h.z, [0, 0, 0]); }")
        out["seen"] = await A.evaluate(f"""() => {{ const L = [...D.MP.links.values()].find(q => q.R && q.R.cur); if (!L) return null; const s = D.glToSphere(L.R.head.x, L.R.head.z, [0, 0, 0]); return Math.round(D.glArc(s, {json.dumps(bp)}) * D.GLOBE.R * 100) / 100; }}""")
        out["near"] = await A.evaluate("""() => { const L = [...D.MP.links.values()].find(q => q.R && q.R.cur); const P = D.P, o = [], hd = () => D.vr.head.copy(new D.THREE.Vector3(P.x, P.y + 1.6, P.z));
          hd(); L.n1k = L.n500 = false; L.R.head.set(P.x, P.y + 1.6, P.z - 1500); D.geoNetNear(); o.push(!!L.n1k, D.mpHear(L)[0]);
          L.R.head.set(P.x + 600, P.y + 1.6, P.z - 600); D.D_V = D.VBAN.t = 0; D.geoNetNear(); o.push(!!L.n1k, D.VBAN.t > 0, D.mpHear(L)[0]);
          L.R.head.set(P.x + 200, P.y + 1.6, P.z); D.geoNetNear(); o.push(!!L.n500, +D.mpHear(L)[0].toFixed(2)); return o; }""")
        out["count"] = await A.evaluate("""() => { const cv = document.createElement('canvas'); cv.width = cv.height = 512; D.geoMapDraw(cv); const d = cv.getContext('2d').getImageData(8, 8, 300, 40).data; let y = 0;
          for (let i = 0; i < d.length; i += 4) if (d[i] > 200 && d[i + 1] > 170 && d[i + 2] < 140) y++; return y; }""")   # 3.02: the count of players on the map
        # A hands the host to B; C dials the code (A's) and is sent on to B
        bid = await B.evaluate("() => D.MP.peer.id")
        await A.evaluate(f"() => {{ D.geoNetGive('{bid}'); return 1; }}"); await run([A, B], 12)
        out["handed"] = [await A.evaluate("() => D.MP.host"), await B.evaluate("() => D.MP.host")]
        await C.evaluate(f"() => {{ D.mpJoin('{code}'); return 1; }}")
        out["cIn"] = await until(C, "() => D.state === 'play' && D.GEO.on", 500, (A, B))
        await run([A, B, C], 40)
        out["cHost"] = await C.evaluate(f"() => D.MP.hostId === '{bid}' && D.MP.links.has('{bid}')")
        out["cLinks"] = await C.evaluate("() => [...D.MP.links.values()].filter(L => L.open).length")
        # B (the host) leaves: the next one takes over
        await B.evaluate("() => { D.mpLeave2(); return 1; }"); await run([A, C], 60)
        out["after"] = [await A.evaluate("() => D.MP.host"), await C.evaluate("() => D.MP.host"), await A.evaluate("() => D.MP.on"), await C.evaluate("() => D.MP.on")]
        print(json.dumps(out))
        ok = out["count"] > 30 and out["hostUp"] and out["listed"] and out["bIn"] and out["same"][0] == out["same"][3] and out["same"][1] == 12 and out["same"][4] == 30 and out["same"][2] == 0 and out["same"][6] \
             and out["near"][:2] == [False, 0] and out["near"][2] and out["near"][4] == 0 and out["near"][5] and out["near"][6] > .3 and out["seen"] is not None and out["seen"] < 1.5 and out["handed"] == [False, True] and out["cIn"] and out["cHost"] and out["cLinks"] >= 2 and sorted(out["after"][:2]) == [False, True] and out["after"][2] and out["after"][3]
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
