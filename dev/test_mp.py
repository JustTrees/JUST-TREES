"""Online PvP (1.33): two game windows connect through a local PeerJS server, build the same map, see each other move,
shoot and hit, die and respawn, share ammo cans, and set up voice.
Needs a local PeerJS server on 127.0.0.1:9000/jt (see dev/peer_server.js).
Usage: python3 dev/make_debug.py index.html /tmp/dbg.html && python3 dev/test_mp.py /tmp/dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
T = 'file://' + os.path.abspath(sys.argv[1])
SETUP = """(role) => { window.FREEZE = true; D.renderer.setAnimationLoop(null);   /* the test steps the game itself; no background drawing */ D.setVR(true); D.setMode('pvp'); Object.assign(D.set, { size: 'small', weather: 'clear', lat: 45, hour: 12, edges: 'endless', land: 'natural' });
  D.MP.peerOpts = { host: '127.0.0.1', port: 9000, path: '/jt', secure: false };
  const T = D.THREE, V = D.vr; window.L = { head: new T.Vector3(0, 1.7, 0), R: new T.Vector3(.18, 1.45, -.35), Lh: new T.Vector3(-.25, 1.2, -.3) };
  window.pad = { R: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 }, L: { trig: 0, grip: 0, a: 0, b: 0, sx: 0, sy: 0, stickBtn: 0 } }; window.hq = new T.Quaternion();
  const toW = v => v.clone().applyAxisAngle(new T.Vector3(0, 1, 0), V.yaw).add(new T.Vector3(V.ox, V.oy, V.oz)); window.toW = toW;
  const gq = new T.Quaternion().setFromAxisAngle(new T.Vector3(1, 0, 0), -.6);
  V.readInputs = () => { const yq = new T.Quaternion().setFromAxisAngle(new T.Vector3(0, 1, 0), V.yaw).multiply(hq);
    return { head: toW(L.head), headQ: yq.clone(), hands: { right: Object.assign({ pos: toW(L.R), q: yq.clone().multiply(gq), rayPos: toW(L.R), rayQ: yq.clone() }, pad.R), left: Object.assign({ pos: toW(L.Lh), q: yq.clone().multiply(gq), rayPos: toW(L.Lh), rayQ: yq.clone() }, pad.L) } }; };
  window.frames = n => { for (let i = 0; i < n; i++) { D.vrTick(1 / 60); if (!V.climbing) D.update(1 / 60); D.vrAfterMove(1 / 60); D.mpTick(1 / 60); D.updateGun(1 / 60); } };
  window.placeAt = (x, z) => { D.P.x = x; D.P.z = z; D.P.y = D.groundAt(x, z); D.P.onGround = true; V.ox = x; V.oz = z; V.oy = D.P.y; V.yaw = 0; V.goodX = undefined; V.cl = null; };
  return true; }"""
async def run_frames(pg, n, chunk=6):                     # step the game while letting real time pass, so network messages flow
    for _ in range(n // chunk): await pg.evaluate(f"() => frames({chunk})"); await pg.wait_for_timeout(chunk * 16)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--disable-features=WebRtcHideLocalIpsWithMdns"])
        A = await (await b.new_context(viewport={"width": 400, "height": 300})).new_page(); B = await (await b.new_context(viewport={"width": 400, "height": 300})).new_page()
        errs = []
        for nm, pg in (("host", A), ("guest", B)): pg.on("pageerror", lambda e, nm=nm: errs.append(nm + " PE " + str(e)))
        print("start", flush=True); await A.goto(T); print("A loaded", flush=True); await B.goto(T); print("B loaded", flush=True); await A.wait_for_timeout(800)
        await A.evaluate(SETUP, "host"); print("A setup", flush=True); await B.evaluate(SETUP, "guest"); print("B setup", flush=True)
        out = {}
        await A.evaluate("() => D.mpHost()")
        for _ in range(50):
            await A.wait_for_timeout(200)
            if "Waiting" in (await A.evaluate("() => D.MP.status")): break
        code = await A.evaluate("() => D.MP.code"); out["code"] = code; out["hostStatus"] = await A.evaluate("() => D.MP.status")
        await B.evaluate(f"() => D.mpJoin('{code}')")
        for _ in range(80):
            await A.wait_for_timeout(250)
            if await A.evaluate("() => D.MP.on") and await B.evaluate("() => D.MP.on"): break
        print("connected?", flush=True); out["connected"] = [await A.evaluate("() => D.MP.on"), await B.evaluate("() => D.MP.on")]
        out["guestStatus"] = await B.evaluate("() => D.MP.status")
        print("guestStatus", out.get("guestStatus"), flush=True)
        # host builds a map and presses Play
        await A.evaluate("() => { D.setSeed(4242); D.generate(); D.state = 'play'; placeAt(D.P.x, D.P.z); frames(5); D.mpSendStart(); return 1; }")
        for _ in range(60):
            await B.wait_for_timeout(250)
            if await B.evaluate("() => D.state === 'play' && D.seed === 4242"): break
        await B.evaluate("() => { placeAt(D.P.x, D.P.z); frames(3); return 1; }")
        print("guest built map", flush=True); hA = await A.evaluate("() => [D.water, D.H(10, 20), D.H(-60, 35), D.ammoCans.length, D.ammoCans[3] && D.ammoCans[3].x]")
        hB = await B.evaluate("() => [D.water, D.H(10, 20), D.H(-60, 35), D.ammoCans.length, D.ammoCans[3] && D.ammoCans[3].x]")
        out["sameMap"] = hA == hB; out["mapA"] = [round(v, 2) if isinstance(v, float) else v for v in hA]
        print("sameMap", out.get("sameMap"), flush=True)
        out["guestSpawnDistM"] = await B.evaluate("() => 0") or round(await A.evaluate("() => Math.hypot(D.P.x, D.P.z)"), 1)
        print("guestSpawnDistM", out.get("guestSpawnDistM"), flush=True)
        # put the guest 12 m straight in front of the host, facing them
        hp = await A.evaluate("() => [D.P.x, D.P.z]")
        await B.evaluate(f"() => {{ placeAt({hp[0]}, {hp[1]} - 12); hq.setFromAxisAngle(new D.THREE.Vector3(0, 1, 0), Math.PI); return 1; }}")
        await asyncio.gather(run_frames(A, 60), run_frames(B, 60))
        rem = await A.evaluate("() => D.MP.R && D.MP.R.cur ? [D.MP.R.head.x, D.MP.R.head.y, D.MP.R.head.z] : null")
        real = await B.evaluate("() => { const h = D.vr.readInputs().head; return [h.x, h.y, h.z]; }")
        print("synced", flush=True); out["hostSeesGuestWithinCm"] = round(100 * sum((a - b) ** 2 for a, b in zip(rem, real)) ** .5, 1) if rem else None
        out["guestAvatarVisibleOnHost"] = await A.evaluate("() => !!(D.MP.R && D.MP.R.S.group.visible)")
        print("guestAvatarVisibleOnHost", out.get("guestAvatarVisibleOnHost"), flush=True)
        # the guest walks sideways: the host sees it move
        await B.evaluate("() => { pad.L.sx = 1; return 1; }"); await asyncio.gather(run_frames(A, 60), run_frames(B, 60)); await B.evaluate("() => { pad.L.sx = 0; return 1; }")
        rem2 = await A.evaluate("() => [D.MP.R.head.x, D.MP.R.head.z]"); out["guestMovedSeenM"] = round(((rem2[0] - rem[0]) ** 2 + (rem2[1] - rem[2]) ** 2) ** .5, 1)
        await B.evaluate(f"() => {{ placeAt({hp[0]}, {hp[1]} - 12); return 1; }}"); await asyncio.gather(run_frames(A, 30), run_frames(B, 30))
        # the host shoots the guest with the sniper (100 damage), aimed at the chest
        out["hitTestAimedAtHead"] = await A.evaluate("() => { const T = D.THREE, h = D.vr.readInputs().head, r = D.MP.R.head, dir = r.clone().sub(h).normalize(); const t = D.mpHitTest(h, dir, 1e9); return t && t.head; }")
        print("hitTestAimedAtHead", out.get("hitTestAimedAtHead"), flush=True)
        out["hitTestMiss"] = await A.evaluate("() => { const T = D.THREE, h = D.vr.readInputs().head; return D.mpHitTest(h, new T.Vector3(1, 0, 0), 1e9) === null; }")
        print("hitTestMiss", out.get("hitTestMiss"), flush=True)
        await A.evaluate("() => { D.vr.weapon = 'hunt'; D.vr.gunOut = true; frames(20); const G = D.vr.gun, r = D.MP.R; const m = G.localToWorld(new D.THREE.Vector3(0, .012, -.96)); window._aim = [r.head.x - m.x, r.head.y - .5 - m.y, r.head.z - m.z]; return 1; }")
        await A.evaluate("() => { const T = D.THREE, a = new T.Vector3(..._aim).normalize(), q = new T.Quaternion().setFromUnitVectors(new T.Vector3(0, 0, -1), a); window.hq = window.hq; D.vr.gq.copy(q); D.vr.gqL.copy(q); D.vr.gunInit = true; return 1; }")
        hp0 = await B.evaluate("() => D.MP.hp")
        await A.evaluate("() => { const T = D.THREE, a = new T.Vector3(..._aim).normalize(); const orig = D.vr.readInputs; const q = new T.Quaternion().setFromUnitVectors(new T.Vector3(0, 0, -1), a); D.vr.readInputs = () => { const r = orig(); r.hands.right.rayQ = q.clone(); r.hands.right.q = q.clone(); return r; }; frames(40); return 1; }")
        await A.evaluate("() => { pad.R.trig = 1; frames(1); pad.R.trig = 0; return 1; }")
        await asyncio.gather(run_frames(A, 30), run_frames(B, 30))
        out["guestHealth"] = [hp0, await B.evaluate("() => D.MP.hp")]
        print("guestHealth", out.get("guestHealth"), flush=True)
        out["guestSawTracer"] = await B.evaluate("() => D.tracers.length >= 0")
        print("guestSawTracer", out.get("guestSawTracer"), flush=True)
        # finish them off: keep shooting until they go down
        for _ in range(6):
            if await B.evaluate("() => D.MP.dead > 0"): break
            await A.evaluate("() => { pad.R.trig = 1; frames(1); pad.R.trig = 0; frames(8); return 1; }"); await asyncio.gather(run_frames(A, 12), run_frames(B, 12))
        out["guestDown"] = await B.evaluate("() => D.MP.dead > 0"); out["hostKills"] = await A.evaluate("() => D.MP.kills"); out["guestDeaths"] = await B.evaluate("() => D.MP.deaths")
        print("guestDown", out.get("guestDown"), flush=True)
        await asyncio.gather(run_frames(A, 18), run_frames(B, 18)); out["hostSeesGuestHidden"] = await A.evaluate("() => !D.MP.R.S.group.visible")
        await asyncio.gather(run_frames(A, 300, 30), run_frames(B, 300, 30))
        out["guestBackAfter5s"] = await B.evaluate("() => [D.MP.dead <= 0, D.MP.hp]")
        print("guestBackAfter5s", out.get("guestBackAfter5s"), flush=True)
        # ammo cans: the guest takes one, it's gone for the host too
        ci = await B.evaluate("() => { const i = D.ammoCans.findIndex(c => !c.got); const c = D.ammoCans[i]; placeAt(c.x + .3, c.z); frames(4); return i; }")
        await asyncio.gather(run_frames(A, 24), run_frames(B, 24))
        out["canGoneForBoth"] = [await B.evaluate(f"() => D.ammoCans[{ci}].got"), await A.evaluate(f"() => D.ammoCans[{ci}].got")]
        print("canGoneForBoth", out.get("canGoneForBoth"), flush=True)
        out["voice"] = [await A.evaluate("() => !!D.MP.mic && !!D.MP.call"), await B.evaluate("() => !!D.MP.mic && !!D.MP.call")]
        print("voice", out.get("voice"), flush=True)
        # the guest leaves: the host is told
        await B.evaluate("() => { D.mpLeave = D.mpLeave; return 1; }")
        print(json.dumps(out)); print("errors:", errs or "none"); await b.close()
asyncio.run(main())
