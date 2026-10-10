"""Online lobby for up to 8 (1.39): 3 players connect (everyone to everyone), the others watch the host's settings and map preview,
each picks a start, flags show in colours on Play for 3 s, then everyone drops in at their own spot; a 4th joins mid-game.
Needs the local PeerJS server (dev/peer_server.js). Usage: python3 dev/make_debug.py index.html /tmp/dbg.html && python3 dev/test_lobby.py /tmp/dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
T = 'file://' + os.path.abspath(sys.argv[1])
INIT = """() => { window.FREEZE = true; D.renderer.setAnimationLoop(null); D.setVR(true); D.setMode('pvp'); const T = D.THREE, V = D.vr; V.on = true;
  Object.assign(D.set, { size: 'small', weather: 'clear', lat: 45, hour: 12, edges: 'endless', land: 'natural', roundMin: 7 });
  D.MP.peerOpts = { host: '127.0.0.1', port: 9000, path: '/jt', secure: false };
  V.readInputs = () => ({ head: new T.Vector3(0, 1.7, 0), headQ: new T.Quaternion(), hands: {} });
  window.tick = setInterval(() => { try { D.vruiTick(.1); D.mpTick(.1); } catch (e) { console.error(String(e)); } }, 100); return 1; }"""
async def wait(pg, js, secs):
    for _ in range(int(secs * 4)):
        if await pg.evaluate(js): return True
        await pg.wait_for_timeout(250)
    return False
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--disable-features=WebRtcHideLocalIpsWithMdns"])
        errs = []
        async def page(nm):
            pg = await (await b.new_context(viewport={"width": 300, "height": 200})).new_page(); pg.on("pageerror", lambda e: errs.append(nm + " " + str(e)))
            pg.on("console", lambda m: errs.append(nm + " CON " + m.text) if m.type == "error" else None)
            await pg.goto(T); await pg.wait_for_timeout(600); await pg.evaluate(INIT); return pg
        A, B, C = await page("A"), await page("B"), await page("C"); out = {}
        await A.evaluate("() => { D.mpHost(); return 1; }"); await wait(A, "() => D.MP.status.includes('Waiting')", 15); code = await A.evaluate("() => D.MP.code")
        await A.evaluate("() => { D.renderSetup(); D.vruiOpen('setup'); return 1; }")      # host is already on the settings when friends join
        await B.evaluate(f"() => {{ D.mpJoin('{code}'); return 1; }}"); await wait(B, "() => D.MP.on", 25)
        await C.evaluate(f"() => {{ D.mpJoin('{code}'); return 1; }}"); await wait(C, "() => D.MP.links.size >= 2 && [...D.MP.links.values()].every(l => l.open)", 25)
        await wait(B, "() => D.MP.links.size >= 2 && [...D.MP.links.values()].every(l => l.open)", 15)
        out["players"] = [await pg.evaluate("() => D.MP.links.size + 1") for pg in (A, B, C)]
        out["colours"] = [await pg.evaluate("() => D.MP.idx") for pg in (A, B, C)]
        out["guestsOnSettings"] = [await pg.evaluate("() => D.VRUIstage") for pg in (B, C)]
        # host moves the latitude: the others see it; a guest can't press Start but can change Hand
        await A.evaluate("() => { D.set.lat = 12; D.renderSetup(); return 1; }"); await B.wait_for_timeout(800)
        out["guestsSeeLat12"] = [await pg.evaluate("() => D.set.lat") for pg in (B, C)]
        out["guestStartLocked"] = await B.evaluate("() => { const P = D.VRUI.panels.setup; return D.mpLocked(P, P.widgets.find(w => w.label === 'Start')); }")
        out["guestHandFree"] = await B.evaluate("() => { const P = D.VRUI.panels.setup; return !D.mpLocked(P, P.widgets.find(w => w.label === 'Left')); }")
        out["hostStartFree"] = await A.evaluate("() => { const P = D.VRUI.panels.setup; return !D.mpLocked(P, P.widgets.find(w => w.label === 'Start')); }")
        # host presses Start: everyone gets the same preview
        await A.evaluate("() => { D.startNew(); return 1; }")
        await wait(A, "() => D.VRUIstage === 'preview'", 20)
        for pg in (B, C): await wait(pg, "() => D.VRUIstage === 'preview'", 20)
        seeds = [await pg.evaluate("() => D.seed") for pg in (A, B, C)]; out["samePreviewSeed"] = len(set(seeds)) == 1
        out["sameLand"] = len(set([await pg.evaluate("() => D.H(30, -40).toFixed(3)") for pg in (A, B, C)])) == 1
        starts = [await pg.evaluate("() => [D.P.x, D.P.z]") for pg in (A, B, C)]
        out["startsDiffer"] = starts[0] != starts[1] and starts[1] != starts[2]
        out["guestButtonsHidden"] = await B.evaluate("() => D.VRUI.panels.preview.widgets.filter(w => w.hide && w.hide()).length")
        # B picks a new start on the little map
        await B.evaluate("() => { const T = D.THREE; D.pickSpawn2(new T.Vector3(-20, 0, 25)); return 1; }"); await A.wait_for_timeout(800)
        bp = await B.evaluate("() => [D.P.x, D.P.z]")
        hostKnowsB = await A.evaluate("() => { const L = [...D.MP.links.values()].find(l => l.idx === 1); return L && L.spawn; }")
        out["hostHasBsPick"] = bool(hostKnowsB) and abs(hostKnowsB[0] - bp[0]) < .01
        kids0 = await B.evaluate("() => D.VRUI.dio.userData.spin.children.length")
        # host presses Play this map: flags for 3 s, then everyone in at their own spot
        await A.evaluate("() => { D.vruiDropIn(); return 1; }"); await B.wait_for_timeout(600)
        out["revealOnAll"] = [await pg.evaluate("() => D.MP.revealT > 0") for pg in (A, B, C)]
        out["otherFlagsShownOnB"] = (await B.evaluate("() => D.VRUI.dio ? D.VRUI.dio.userData.spin.children.length : -1")) - kids0
        cols = await B.evaluate("() => D.MP.reveal.map(e => e.c)"); out["flagColours"] = cols
        for pg in (A, B, C): await wait(pg, "() => D.state === 'play'", 15)
        out["allPlaying"] = [await pg.evaluate("() => D.state") for pg in (A, B, C)]
        out["roundClock"] = [round(await pg.evaluate("() => D.MP.roundLeft")) for pg in (A, B, C)]
        out["guestsPistolOnly"] = await B.evaluate("() => JSON.stringify(D.vr.own)")
        bp2 = await B.evaluate("() => [D.P.x, D.P.z]"); out["bAtOwnPick"] = abs(bp2[0] - bp[0]) < .5 and abs(bp2[1] - bp[1]) < .5
        # a 4th player joins mid-game
        Dp = await page("D"); await Dp.evaluate(f"() => {{ D.mpJoin('{code}'); return 1; }}")
        out["lateJoinerPlaying"] = await wait(Dp, "() => D.state === 'play' && D.MP.links.size >= 3", 30)
        out["lateJoinerSameMap"] = (await Dp.evaluate("() => D.seed")) == seeds[0]
        out["lateJoinerColour"] = await Dp.evaluate("() => D.MP.idx")
        # the clock runs out: everyone sees the round-over board
        for pg in (A, B, C, Dp): await pg.evaluate("() => { D.MP.roundLeft = .5; return 1; }")
        for pg in (A, B, C, Dp): await wait(pg, "() => D.VRUIstage === 'over'", 10)
        out["roundOverAll"] = [await pg.evaluate("() => D.VRUIstage") for pg in (A, B, C, Dp)]
        out["boardRows"] = await A.evaluate("() => D.MP.board.length")
        await A.evaluate("() => { D.startNew(); return 1; }")
        out["nextMapPreviewForGuests"] = [await wait(pg, "() => D.VRUIstage === 'preview'", 20) for pg in (B, C)]
        print(json.dumps(out)); print("errors:", errs[:8] or "none"); await b.close()
asyncio.run(main())
