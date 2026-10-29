"""3.13 (two headsets): one player drives the boat while another rides on its deck. The rider is carried along and stays put on the
deck; each sees the other standing on the boat (not trailing behind it), and both see the boat in the same place on the planet.
Built on test_280 (needs the local PeerJS server, run through run_all.py --nm).
2.80 notes: Online Treeocashing. One button: no room with space → you open one (public, on the Treeocashing list); others join the same
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
    const B = D.BOAT.on, rim = window.DRIVE && B && B.obj ? B.obj.userData.wb.localToWorld(new T.Vector3(.19, 0, 0)) : null;
    return { head: h, headQ: yq.clone(), hands: { right: { pos: rim || h.clone().add(new T.Vector3(.2, -.4, -.3)), q: yq.clone(), rayPos: h.clone(), rayQ: yq.clone(), trig: rim ? 1 : 0, grip: rim ? 1 : 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 } } }; };
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
        pgs = [await (await b.new_context(viewport={"width": 320, "height": 240})).new_page() for _ in range(2)]; A, B = pgs; errs = []
        for nm, pg in zip("AB", pgs): pg.on("pageerror", lambda e, nm=nm: errs.append(nm + " PE " + str(e)[:200]))
        for i, pg in enumerate(pgs): await pg.goto(T); await pg.wait_for_timeout(500); await pg.evaluate(SETUP, [60, 58][i])
        out = {}
        await A.evaluate("() => { D.geoNetGo(); return 1; }")
        out["hostUp"] = await until(A, "() => D.state === 'play' && D.GEO.on && !!D.MP.code && D.MP.host", 150)
        code = await A.evaluate("() => D.MP.code")
        await B.evaluate(f"() => {{ D.mpJoin('{code}'); return 1; }}")
        out["bIn"] = await until(B, "() => D.state === 'play' && D.GEO.on && D.MP.on", 500, (A,))
        await run([A, B], 30)
        # both go to the same boat
        bid = await A.evaluate("""() => { for (const bb of D.BOAT.list) { D.geoTeleport(bb.p); D.vr.ox = D.P.x; D.vr.oz = D.P.z; D.vr.placeAt = true; frames(60); D.GEO.tT = 0; frames(3); if (bb.obj && !bb.dead) return bb.id; } return 0; }""")
        out["boat"] = bid
        if bid:
            bp = await A.evaluate(f"() => D.BOAT.list[{bid} - 1].p")
            await B.evaluate(f"() => {{ D.geoTeleport({json.dumps(bp)}); D.vr.ox = D.P.x; D.vr.oz = D.P.z; D.vr.placeAt = true; frames(60); D.GEO.tT = 0; frames(3); return 1; }}")
            out["bSees"] = await B.evaluate(f"() => !!D.BOAT.list[{bid} - 1].obj")
            # A climbs in at the helm and drives; B climbs in at the back and rides
            await A.evaluate(f"""() => {{ const bb = D.BOAT.list[{bid} - 1], T = D.THREE; D.boatMount(bb, new T.Vector3(.52, 0, -.6).applyMatrix4(bb.m)); D.vr.ox = D.P.x; D.vr.oz = D.P.z; window.DRIVE = true; return 1; }}""")
            await B.evaluate(f"""() => {{ const bb = D.BOAT.list[{bid} - 1], T = D.THREE; D.boatMount(bb, new T.Vector3(-.4, 0, 2.2).applyMatrix4(bb.m)); D.vr.ox = D.P.x; D.vr.oz = D.P.z; window.l0 = new T.Vector3(D.P.x, D.water, D.P.z).applyMatrix4(bb.mi); return 1; }}""")
            p0 = await B.evaluate(f"() => D.BOAT.list[{bid} - 1].p.slice()")
            await run([A, B], 240)
            out["driving"] = await A.evaluate(f"() => [D.BOAT.drive === D.BOAT.list[{bid} - 1], +D.BOAT.list[{bid} - 1].sp.toFixed(1)]")
            out["bRides"] = await B.evaluate(f"""() => {{ const bb = D.BOAT.list[{bid} - 1], T = D.THREE, l = new T.Vector3(D.P.x, D.water, D.P.z).applyMatrix4(bb.mi); return [D.BOAT.on === bb, Math.round(D.glArc(bb.p, {json.dumps(p0)}) * D.GLOBE.R), +Math.hypot(l.x - l0.x, l.z - l0.z).toFixed(2)]; }}""")
            pa = await A.evaluate(f"() => D.BOAT.list[{bid} - 1].p"); pb = await B.evaluate(f"() => D.BOAT.list[{bid} - 1].p")
            out["sameSpot"] = await A.evaluate(f"() => +(D.glArc({json.dumps(pa)}, {json.dumps(pb)}) * D.GLOBE.R).toFixed(1)")
            seen = """(id) => { const bb = D.BOAT.list[id - 1], L = [...D.MP.links.values()].find(q => q.R && q.R.cur); if (!L) return null; const l = L.R.head.clone().applyMatrix4(bb.mi); return [+l.x.toFixed(2), +l.y.toFixed(2), +l.z.toFixed(2)]; }"""
            out["aSeesB"] = await A.evaluate(seen, bid); out["bSeesA"] = await B.evaluate(seen, bid)
        print(json.dumps(out))
        on = lambda v, x0, x1: v is not None and x0 < v < x1
        ok = out["hostUp"] and out["bIn"] and out["boat"] and out.get("bSees") and out["driving"][0] and out["driving"][1] > 8 and out["bRides"][0] and out["bRides"][1] > 40 and out["bRides"][2] < .3 \
             and out["sameSpot"] < 6 and out["aSeesB"] and on(out["aSeesB"][0], -.8, 0) and on(out["aSeesB"][2], 1.6, 2.8) and on(out["aSeesB"][1], 1.9, 2.4) \
             and out["bSeesA"] and on(out["bSeesA"][0], .2, .9) and on(out["bSeesA"][2], -1.2, 0)
        print("PASS" if ok and not errs else "FAIL", errs[:5]); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
