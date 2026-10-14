"""2.00: online in every mode. Two game windows through a local PeerJS server (see dev/peer_server.js):
the lobby (gamer tags, uniform colours, the host's mode and teams reach the guest, avatars stand in the lobby room),
comms (team / fist bump), no friendly fire, shared hunting (the guest sees the host's animals where they are,
the guest's shot kills on the host and the points come back), the raptor going after the guest, the round ending in the lobby.
Usage: python3 dev/make_debug.py index.html /tmp/dbg.html && python3 dev/test_online.py /tmp/dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
T = 'file://' + os.path.abspath(sys.argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
SETUP = open(os.path.join(HERE, "test_mp.py")).read().split('SETUP = """', 1)[1].split('"""', 1)[0]
async def run_frames(pg, n, chunk=6):
    for _ in range(n // chunk): await pg.evaluate(f"() => frames({chunk})"); await pg.wait_for_timeout(chunk * 16)
async def both(A, B, n, chunk=6): await asyncio.gather(run_frames(A, n, chunk), run_frames(B, n, chunk))
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--disable-features=WebRtcHideLocalIpsWithMdns"])
        A = await (await b.new_context(viewport={"width": 400, "height": 300})).new_page(); B = await (await b.new_context(viewport={"width": 400, "height": 300})).new_page()
        errs = []
        for nm, pg in (("host", A), ("guest", B)): pg.on("pageerror", lambda e, nm=nm: errs.append(nm + " PE " + str(e)))
        await A.goto(T); await B.goto(T); await A.wait_for_timeout(800)
        await A.evaluate(SETUP, "host"); await B.evaluate(SETUP, "guest")
        ANIM = "() => { window._f = window.frames; window.frames = n => { for (let i = 0; i < n; i++) { window._f(1); if (D.state === 'play') D.updateAnimals(1 / 60); } }; return 1; }"   # (the real loop moves the animals too)
        await A.evaluate(ANIM); await B.evaluate(ANIM)
        out = {}
        # ---- the lobby: tags, colours, the host's game reaches the guest
        await A.evaluate("() => { D.MP.tag = 'HOSTY'; D.MP.col = 2; D.setMode('hike'); D.mpHost(); D.vruiOpen('lobby'); return 1; }")
        for _ in range(50):
            await A.wait_for_timeout(200)
            if await A.evaluate("() => D.MP.peer && D.MP.peer.open"): break
        code = await A.evaluate("() => D.MP.code")
        await B.evaluate(f"() => {{ D.MP.tag = 'GUESTY'; D.MP.col = 3; D.mpJoin('{code}'); D.vruiOpen('lobby'); return 1; }}")
        for _ in range(80):
            await A.wait_for_timeout(250)
            if await A.evaluate("() => D.MP.on") and await B.evaluate("() => D.MP.on"): break
        out["connected"] = [await A.evaluate("() => D.MP.on"), await B.evaluate("() => D.MP.on")]
        await both(A, B, 30)
        out["tags"] = [await A.evaluate("() => D.mpRoster().map(r => r.tag)"), await B.evaluate("() => D.mpRoster().map(r => r.tag)")]
        await A.evaluate("() => { D.setMode('pvp'); D.set.teams = 'teams'; D.mpHostSetSync(); D.mpLobSync(true); return 1; }")
        await both(A, B, 30)
        out["guestMode"] = await B.evaluate("() => [D.gameMode, D.set.teams, D.teamsOn()]")
        out["teams"] = await B.evaluate("() => Object.values(D.MP.teams).sort().join(',')")
        # ---- PvP teams: no friendly fire; comms
        await A.evaluate("() => { D.setSeed(4242); D.generate(); D.state = 'play'; placeAt(D.P.x, D.P.z); frames(5); D.mpSendStart(); return 1; }")
        for _ in range(60):
            await B.wait_for_timeout(250)
            if await B.evaluate("() => D.state === 'play' && D.seed === 4242"): break
        hp = await A.evaluate("() => [D.P.x, D.P.z]")
        await B.evaluate(f"() => {{ placeAt({hp[0]}, {hp[1]} - 8); hq.setFromAxisAngle(new D.THREE.Vector3(0, 1, 0), Math.PI); return 1; }}")
        await both(A, B, 60)
        aim = "() => { const h = D.vr.readInputs().head, L = [...D.MP.links.values()][0], r = L.R.head, dir = r.clone().sub(h).normalize(); return !!D.mpHitTest(h, dir, 1e9); }"
        out["enemyHittable"] = await A.evaluate(aim)
        out["guestUniformOnHost"] = await A.evaluate("() => { const L = [...D.MP.links.values()][0]; return L && L.R ? [L.R.uni, !L.R.bands] : null; }")
        await A.evaluate("() => { const ids = [D.MP.peer.id, ...[...D.MP.links.keys()]]; ids.forEach(i => { D.MP.teams[i] = 0; }); D.set.comms = 3; D.mpLobSync(true); return 1; }")
        await both(A, B, 30)
        out["teammateNotHittable"] = not await A.evaluate(aim)
        out["fistBumpSilent"] = await B.evaluate("() => D.mpHear([...D.MP.links.values()][0])[0]")
        # the fist bump: both make fists, the guest's right fist goes to the host's right fist
        await A.evaluate("() => { pad.R.grip = 1; return 1; }"); await B.evaluate("() => { pad.R.grip = 1; return 1; }"); await both(A, B, 24)
        await B.evaluate("""() => { const T = D.THREE, V = D.vr, Lk = [...D.MP.links.values()][0], w = Lk.R.cur.r.p.clone();
          const loc = w.sub(new T.Vector3(V.ox, V.oy, V.oz)).applyAxisAngle(new T.Vector3(0, 1, 0), -V.yaw); L.R.copy(loc); return 1; }""")
        await both(A, B, 18)
        out["bumped"] = [await A.evaluate("() => !![...D.MP.links.values()][0].bumped"), await B.evaluate("() => !![...D.MP.links.values()][0].bumped")]
        out["hearAfterBump"] = await B.evaluate("() => D.mpHear([...D.MP.links.values()][0])[0]")
        await A.evaluate("() => { pad.R.grip = 0; return 1; }"); await B.evaluate("() => { pad.R.grip = 0; return 1; }")
        # ---- hunting together: the host's animals on the guest's game
        await A.evaluate("() => { D.setMode('hunt'); D.set.dino = false; D.set.size = 'small'; D.mpHostSetSync(); D.setSeed(777); D.generate(); D.state = 'play'; placeAt(D.P.x, D.P.z); frames(5); D.mpSendStart(); return 1; }")
        for _ in range(60):
            await B.wait_for_timeout(250)
            if await B.evaluate("() => D.state === 'play' && D.seed === 777 && D.gameMode === 'hunt'"): break
        hp = await A.evaluate("() => [D.P.x, D.P.z]")
        await B.evaluate(f"() => {{ placeAt({hp[0]} + 6, {hp[1]}); return 1; }}")
        await both(A, B, 120)
        await A.evaluate("() => { const h = D.vr.readInputs().head; D.placeMark(h, new D.THREE.Vector3(.3, -.4, -1).normalize()); return 1; }"); await both(A, B, 12)
        out["guestSeesMark"] = await B.evaluate("() => { const L = [...D.MP.links.values()][0]; return !!(L.mark && L.mark.visible); }")
        out["guestGround"] = await B.evaluate("() => [D.mpNetGuest(), D.beasts.filter(a => a.net).length, D.beasts.filter(a => !a.net && !D.FLY[a.kind] && a.kind !== 'monkey').length]")
        out["sameSpot"] = await B.evaluate("""() => { const a = D.beasts.find(x => x.net && !x.dead); return a ? [a.nid, a.kind, a.x, a.z] : null; }""")
        if out["sameSpot"]:
            nid = out["sameSpot"][0]
            hostPos = await A.evaluate(f"() => {{ const a = D.beasts.find(x => x.nid === {nid}); return a ? [a.x, a.z] : null; }}")
            out["posDiffM"] = round(((hostPos[0] - out["sameSpot"][2]) ** 2 + (hostPos[1] - out["sameSpot"][3]) ** 2) ** .5, 2) if hostPos else None
            s0 = await B.evaluate("() => D.hunt.score")
            await B.evaluate(f"() => {{ const a = D.beasts.find(x => x.nid === {nid}); D.hitAnimal(a, 80, 0, false, 'hunt'); return 1; }}")
            await both(A, B, 60); await both(A, B, 60)
            out["kill"] = {"hostDead": await A.evaluate(f"() => {{ const a = D.beasts.find(x => x.nid === {nid}); return a ? a.dead : null; }}"),
                           "guestDead": await B.evaluate(f"() => {{ const a = D.beasts.find(x => x.nid === {nid}); return a ? a.dead : null; }}"),
                           "guestPoints": round(await B.evaluate("() => D.hunt.score") - s0, 1), "hostPoints": await A.evaluate("() => D.hunt.score")}
        # ---- the raptor goes after the guest
        await A.evaluate("() => { D.set.dino = true; D.mpHostSetSync(); D.setSeed(778); D.generate(); D.state = 'play'; placeAt(D.P.x, D.P.z); frames(5); D.mpSendStart(); return 1; }")
        for _ in range(60):
            await B.wait_for_timeout(250)
            if await B.evaluate("() => D.state === 'play' && D.seed === 778"): break
        await B.evaluate(f"() => {{ placeAt(D.P.x, D.P.z); D.UW.drown = 0; D.UW.red = 0; return 1; }}")
        await both(A, B, 60)
        gid = await B.evaluate("() => D.MP.peer.id")
        out["raptorOn"] = await A.evaluate(f"""() => {{ D.DINO.tgt = '{gid}'; D.mpAsTarget(null, '{gid}', () => D.dinoSpawnHunter()); const H = D.DINO.hunter; if (!H) return null;
          H.hs = 'approach'; H.hsT = 0; return Math.round(Math.hypot(H.x - [...D.MP.links.values()][0].R.head.x, H.z - [...D.MP.links.values()][0].R.head.z)); }}""")
        got = False
        for _ in range(60):
            await asyncio.gather(A.evaluate("() => { for (let i = 0; i < 20; i++) { D.updateAnimals(1 / 30); D.mpTick(1 / 30); } return 1; }"), run_frames(B, 6))
            if await B.evaluate("() => D.UW.red > 0 || D.UW.drown > 0"): got = True; break
        out["raptorGotGuest"] = got
        out["hostNotGot"] = await A.evaluate("() => !(D.UW.red > 0)")
        out["guestSawRaptor"] = await B.evaluate("() => D.beasts.some(a => a.net && a.kind === 'raptor')")
        # ---- the T. rex: the host has the red sniper, so the guest sees it too; the guest shoots it, it goes after the guest
        await B.evaluate("() => { D.UW.drown = 0; D.UW.red = 0; return 1; }")
        await A.evaluate("() => { D.vr.own.hunt = 5; const L = [...D.MP.links.values()][0], g = L.R.head; const R = D.addGround('trex', g.x + 70, g.z); window._rex = R; return 1; }")
        for _ in range(8): await asyncio.gather(A.evaluate("() => { for (let i = 0; i < 6; i++) { D.updateAnimals(1 / 30); D.mpTick(1 / 30); } return 1; }"), run_frames(B, 6))
        out["guestSeesRex"] = await B.evaluate("() => { const r = D.beasts.find(a => a.net && a.kind === 'trex'); return !!r && D.MP.anyRed && r.root.visible; }")
        await B.evaluate("() => { const r = D.beasts.find(a => a.net && a.kind === 'trex'); if (r) D.rexStart(r); return 1; }")
        for _ in range(4): await asyncio.gather(A.evaluate("() => { for (let i = 0; i < 6; i++) { D.updateAnimals(1 / 30); D.mpTick(1 / 30); } return 1; }"), run_frames(B, 6))
        out["rexAfterGuest"] = await A.evaluate(f"() => [!!window._rex.rexOn, window._rex.tgt === '{gid}']")
        got = False
        for _ in range(80):
            await asyncio.gather(A.evaluate("() => { for (let i = 0; i < 20; i++) { D.updateAnimals(1 / 30); D.mpTick(1 / 30); } return 1; }"), run_frames(B, 6))
            if await B.evaluate("() => D.UW.red > 0 || D.UW.drown > 0"): got = True; break
        out["rexGotGuest"] = got
        # ---- the round ends: everyone in the lobby with the board
        await B.evaluate("() => { D.MP.roundLeft = .05; D.mpTick(.1); return 1; }")
        out["roundEnd"] = await B.evaluate("() => [D.state, D.VRUI.stage, (D.MP.board || []).length]")
        print(json.dumps(out)); print("errors:", errs or "none")
        k = out.get("kill", {})
        ok = (all(out["connected"]) and sorted(out["tags"][0]) == ["GUESTY", "HOSTY"] and sorted(out["tags"][1]) == ["GUESTY", "HOSTY"] and out["guestMode"] == ["pvp", "teams", True]
              and out["teams"] == "0,1" and out["guestUniformOnHost"] == [3, True] and out["guestSeesMark"] and out["enemyHittable"] and out["teammateNotHittable"]
              and out["fistBumpSilent"] == 0 and all(out["bumped"]) and out["hearAfterBump"] == 1 and out["guestGround"][0] and out["guestGround"][1] > 0 and out["guestGround"][2] == 0
              and out.get("posDiffM") is not None and out["posDiffM"] < 4 and k.get("hostDead") and k.get("guestDead") and k.get("guestPoints", 0) > 0 and not k.get("hostPoints")
              and out["raptorGotGuest"] and out["hostNotGot"] and out["roundEnd"] == ["vrmenu", "lobby", 2] and out["guestSeesRex"] and out["rexAfterGuest"] == [True, True] and out["rexGotGuest"] and not errs)
        print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
