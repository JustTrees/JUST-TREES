"""3.31 (Dev): Competitive Treeocashing. The main menu's Competitive button opens a public room with an empty lobby (size M: 10 levels).
Friends join; Start: everyone caches up from nothing, no guns lying about. A cache found gives the next reward; the top level makes a
Bigg Wigg (the others see it). Killed by a Bigg Wigg: out. Killed by anyone else: back in, level kept. Everyone left a Bigg Wigg: the
zone comes in for all; a death then is out; the last one standing wins (the board shows it). Needs the PeerJS server.
Usage: python3 dev/test_331.py dbg.html"""
import os, sys, asyncio, json, re
from playwright.async_api import async_playwright
here = os.path.dirname(os.path.abspath(__file__)); T = 'file://' + os.path.abspath(sys.argv[1])
SETUP = re.search(r'SETUP = """(.*?)"""', open(os.path.join(here, "test_280.py")).read(), re.S).group(1)
SETUP = SETUP.replace("return true; }", "window.W = (p, l) => D.VRUI.panels[p].widgets.find(w => w.label === l); D.geoTick = () => {}; return true; }")
async def run(pages, n, chunk=4):
    for _ in range(n // chunk):
        for pg in pages: await pg.evaluate(f"() => frames({chunk})")
        await pages[0].wait_for_timeout(chunk * 25)
async def until(pgs, js, tries=300):
    for _ in range(tries):
        if all([await pg.evaluate(js) for pg in pgs]): return True
        await run(pgs, 4)
    return False
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--disable-features=WebRtcHideLocalIpsWithMdns"])
        pgs = [await (await b.new_context(viewport={"width": 320, "height": 240})).new_page() for _ in range(3)]; A, B, C = pgs; errs = []
        for nm, pg in zip("ABC", pgs): pg.on("pageerror", lambda e, nm=nm: errs.append(nm + " PE " + str(e)[:200]))
        for i, pg in enumerate(pgs): await pg.goto(T); await pg.wait_for_timeout(500); await pg.evaluate(SETUP, [1, 2, 3][i])
        out = {}
        await A.evaluate("() => { D.vruiOpen('mode'); W('mode', 'Competitive').on(); return 1; }")
        for _ in range(60):
            await A.wait_for_timeout(200)
            if "Waiting" in (await A.evaluate("() => D.MP.status")): break
        out["room"] = await A.evaluate("() => [D.set.comp, D.compMode(), D.roomMapName(), D.MP.pub, D.VRUI.stage]")
        code = await A.evaluate("() => D.MP.code")
        for G in (B, C): await G.evaluate(f"() => {{ D.mpJoin('{code}'); return 1; }}")
        for _ in range(80):
            await A.wait_for_timeout(250)
            if await A.evaluate("() => D.mpOpen().length >= 2") and await B.evaluate("() => D.MP.on") and await C.evaluate("() => D.MP.on"): break
        await run(pgs, 8); out["guestSet"] = await B.evaluate("() => [D.set.comp, D.set.size, D.gameMode]")
        await A.evaluate("() => { D.vruiOpen('setup'); W('setup', 'Start').on(); return 1; }")
        out["preview"] = await until(pgs, "() => D.VRUI.stage === 'preview' && !D.MP.genBusy", 300)
        await A.evaluate("() => { D.vruiDropIn(); return 1; }"); await A.wait_for_timeout(500)
        out["play"] = await until(pgs, "() => D.state === 'play' && D.COMP.on && !!D.COMP.c", 400)
        out["start"] = await B.evaluate("() => [D.COMP.N, D.COMP.lv, [...D.DROPS.values()].filter(d => d.type === 'gun').length, D.MP.roundLeft]")
        # B finds a cache
        out["lv1"] = await B.evaluate("() => { const c = D.COMP.c; D.P.x = c.x; D.P.z = c.z; D.P.y = D.groundAt(c.x, c.z); D.vr.ox = D.P.x; D.vr.oz = D.P.z; frames(3); return [D.COMP.lv, D.vr.own.smg | 0, !!D.COMP.c]; }")
        out["gps"] = await B.evaluate("() => { D.geoGpsModel(); D.compGpsDraw(); return 1; }")
        # B becomes a Bigg Wigg
        out["bw"] = await B.evaluate("""() => { const go = () => { const c = D.COMP.c; D.P.x = c.x; D.P.z = c.z; D.P.y = D.groundAt(c.x, c.z); D.vr.ox = D.P.x; D.vr.oz = D.P.z; frames(3); };
          D.COMP.lv = 8; go(); const th = [D.COMP.lv, D.TOOL.on.hunt, D.COMP.items.has('tscope')]; go(); return [D.COMP.lv, D.COMP.c, th]; }""")
        await run(pgs, 16)
        bid = await B.evaluate("() => D.MP.peer.id"); aid = await A.evaluate("() => D.MP.peer.id"); cid = await C.evaluate("() => D.MP.peer.id")
        out["seenBW"] = await A.evaluate(f"() => !!D.MP.links.get('{bid}').cbw")
        # the Bigg Wigg takes C down: C is out
        out["cOut"] = await C.evaluate(f"() => {{ D.MP.lastHitBy = '{bid}'; D.mpTakeHit(500, false, true); return D.COMP.out; }}")
        # A (not a Bigg Wigg) takes B down: B is back, still level 10
        out["bBack"] = await B.evaluate(f"() => {{ D.MP.lastHitBy = '{aid}'; D.mpTakeHit(500, false, true); for (let i = 0; i < 160; i++) frames(1); return [D.COMP.out, D.COMP.lv, D.MP.dead <= 0]; }}")
        await run(pgs, 16); out["seenOut"] = await A.evaluate(f"() => !!D.MP.links.get('{cid}').co")
        # A becomes a Bigg Wigg too: everyone left is one → the zone
        await A.evaluate("() => { D.COMP.lv = 9; const c = D.COMP.c; D.P.x = c.x; D.P.z = c.z; D.P.y = D.groundAt(c.x, c.z); D.vr.ox = D.P.x; D.vr.oz = D.P.z; frames(3); return 1; }")
        out["zone"] = await until([A, B], "() => D.COMP.zone && !!D.zone", 100)
        # B dies in the zone phase: out; A wins
        await B.evaluate("() => { D.MP.lastHitBy = null; D.mpTakeHit(500, false, true); return 1; }")
        out["won"] = await until([A, B], "() => D.COMP.ended", 100)
        out["end"] = [await A.evaluate("() => [D.COMP.winner === D.mpMyId(), D.MP.board && D.MP.board[0].me, D.MP.boardMode]"), await B.evaluate(f"() => [D.COMP.winner === '{aid}', D.COMP.out]")]
        print(json.dumps(out)); print("errors:", errs[:5] or "none")
        ok = out["room"][:4] == [True, True, "Competitive · M", True] and out["guestSet"] == [True, "medium", "hunt"] and out["play"] and out["start"] == [10, 0, 0, 0] \
             and out["lv1"] == [1, 1, True] and out["bw"][0] == 10 and out["bw"][1] is None and out["bw"][2] == [9, True, True] and out["seenBW"] and out["cOut"] and out["bBack"] == [False, 10, True] and out["seenOut"] \
             and out["zone"] and out["won"] and out["end"] == [[True, True, "comp"], [True, True]] and not errs
        print("PASS" if ok else "FAIL"); await b.close()
        if not ok: sys.exit(1)
asyncio.run(main())
