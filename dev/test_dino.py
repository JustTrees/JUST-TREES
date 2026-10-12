"""Prehistoric (1.75, VR hunting only): a switch in the Hunting setup. Same maps; the animals are dinosaurs (Triceratops, Parasaurolophus,
Stegosaurus, Brontosaurus). Every dinosaur takes several shots: a health bar shows once hurt, each gun does its own damage, a head hit 1.5x.
At random times (no rhythm) one raptor hunts you: a low warning swell, it appears far off out of sight, stalks with its eyes on you, then
charges (bites: red blackout and you wake up elsewhere) or loses interest and leaves. Up a tree it paces underneath and gives up.
Shooting it makes it charge; killing it is a big bonus. Off, on PC/phone, or in other modes: nothing changes."""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1])
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 200})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""() => { window.FREEZE = true; const out = {}, T = D.THREE, DN = ['triceratops', 'parasaur', 'stego', 'bronto'];
          // the switch: only in Hunting
          const btns = () => D.VRUI.panels.setup ? D.VRUI.panels.setup.widgets.filter(w => w.label === 'On' && !(w.hide && w.hide())) : [];
          if (!D.VRUI.panels || !D.VRUI.panels.setup) { D.setVR(true); D.vruiOpen('setup'); }
          D.setMode('hunt'); D.set.dino = false; const hb = btns(); out.huntOnBtns = hb.length; if (hb.length === 1) hb[0].on(); out.switched = D.set.dino === true;
          D.setMode('hike'); out.hikeOnBtns = btns().length;
          const gen = (vrOn, dino, sd) => { D.setSeed(sd); D.setVR(vrOn); D.setMode('hunt'); D.set.dino = dino; D.set.env = 'climate'; D.set.land = 'natural'; D.set.size = 'large'; D.set.lat = 42; D.set.month = 6; D.set.weather = 'clear'; D.set.density = .5; D.generate(); D.state = 'play'; };
          const kinds = () => { const k = {}; for (const A of D.beasts) k[A.kind] = (k[A.kind] || 0) + 1; return k; };
          gen(false, true, 5); out.pc = { on: D.DINO.on, kinds: Object.keys(kinds()) };
          gen(true, false, 5); out.off = { on: D.DINO.on, dinos: D.beasts.filter(A => A.hpMax).length };
          gen(true, true, 5); out.on = { on: D.DINO.on, kinds: kinds(), allHp: D.beasts.every(A => A.hpMax > 0), n: D.beasts.length };
          // damage: several shots, head counts more, a bar once hurt
          const tri = D.beasts.find(A => A.kind === 'triceratops'), s0 = D.hunt.score;
          D.hitAnimal(tri, 50, 100, false); out.tri1 = { hp: tri.hp, dead: tri.dead, bar: !!(tri.bar && tri.bar.g.visible) };
          D.hitAnimal(tri, 50, 100, true); out.tri2 = { hp: tri.hp, dead: tri.dead };
          D.hitAnimal(tri, 50, 100, false); out.tri3 = { hp: tri.hp, dead: tri.dead, bar: !!(tri.bar && tri.bar.g.visible), pts: +(D.hunt.score - s0).toFixed(1) };
          const W = D.WEAP, shots = k => Math.ceil(180 / Math.round(W[k].dmg * D.TIER.dmg[1])); out.raptorShots = { sniper: shots('hunt'), ar: shots('ar'), smg: shots('smg'), pistol: shots('pistol') };
          out.raptorShotsRed = Math.ceil(180 / Math.round(W.hunt.dmg * D.TIER.dmg[5]));
          // a real shot: body vs head
          const st = D.beasts.find(A => A.kind === 'stego' && !A.dead); D.camera.position.set(st.x, D.H(st.x, st.z) + 2, st.z - 200); st.root.visible = true; st.root.updateMatrixWorld(true);
          const bodyP = new T.Vector3(st.x, st.y + 1.8, st.z), hp2 = st.head.localToWorld(new T.Vector3(0, -.05, .3));
          const fx = Math.sin(st.yaw), fz = Math.cos(st.yaw), shot = tgt => { const o = new T.Vector3(tgt.x + fx * 30 + fz * 8, tgt.y + 1, tgt.z + fz * 30 - fx * 8), d = tgt.clone().sub(o).normalize(); return D.animalRay(o, d, .5); };   // from in front of it
          const rb = shot(bodyP), rh = shot(hp2); out.rayBody = { who: rb[1] && rb[1].kind, head: rb[2] }; out.rayHead = { who: rh[1] && rh[1].kind, head: rh[2] };
          // the hunt
          const P = D.P; P.y = D.groundAt(P.x, P.z); D.vr.climbing = false; D.vr.cl = null; D.camera.position.set(P.x, P.y + 1.7, P.z); D.camera.rotation.set(0, 0, 0, 'YXZ'); D.camera.updateMatrixWorld();
          const step = (secs, f) => { for (let i = 0; i < secs * 30; i++) { D.updateAnimals(1 / 30); if (f && f(i / 30)) return true; } return false; };
          const ang = (a) => Math.atan2(Math.sin(a), Math.cos(a));
          const startHunt = () => { D.DINO.gap = 0; D.DINO.pending = 0; D.dinoStartHunt(); let t = 0; while (!D.DINO.hunter && t < 6) { D.dinoTick(1 / 30); t += 1 / 30; } return D.DINO.hunter; };
          let A = startHunt(); const dist = () => Math.hypot(A.x - P.x, A.z - P.z);
          const fw = new T.Vector3(); D.camera.getWorldDirection(fw);
          out.spawn = A ? { d: Math.round(dist()), ahead: +(((A.x - P.x) * fw.x + (A.z - P.z) * fw.z) / dist()).toFixed(2), kind: A.kind, state: A.hs } : null;
          let minD = 1e9, eyes = 0, frames = 0, moves = new Set();
          step(16, () => { minD = Math.min(minD, dist()); const toP = Math.atan2(P.x - A.x, P.z - A.z); frames++; if (Math.abs(ang(toP - A.yaw - A.look)) < .4) eyes++; moves.add(A.move); return A.hs !== 'stalk'; });
          out.stalk = { minD: Math.round(minD), eyes: +(eyes / frames).toFixed(2), moves: [...moves], state: A.hs };
          A.giveUp = false; A.hsT = A.stalkFor + 1; let bitT = null;
          step(40, t => { if (A.gone && D.UW.drown > 0) { bitT = t; return true; } }); out.bite = { t: bitT, drown: D.UW.drown > 0, gone: !!A.gone };
          D.UW.drown = 0; D.UW.red = 0; D.dinoTick(1 / 30); out.afterBite = { hunter: !!D.DINO.hunter, inBeasts: D.beasts.includes(A), gap: Math.round(D.DINO.gap) };
          // leaving
          A = startHunt(); A.giveUp = true; A.hsT = A.stalkFor + 1; const d0 = dist(); let goneT = null; step(45, t => { if (A.gone) { goneT = t; return true; } });
          out.leave = { goneT, d0: Math.round(d0) }; D.dinoTick(1 / 30);
          // up a tree: it waits underneath, then gives up
          A = startHunt(); A.giveUp = false; A.hsT = A.stalkFor + 1; D.vr.climbing = true; const states = new Set(); let bit = false;
          step(60, () => { states.add(A.hs); if (D.UW.drown > 0) bit = true; return A.gone; });
          out.tree = { states: [...states], bit, gone: !!A.gone }; D.vr.climbing = false; D.dinoTick(1 / 30);
          // shooting it: it charges; two sniper hits kill it, big bonus
          A = startHunt(); const s1 = D.hunt.score; D.hitAnimal(A, 80, 100, false); out.shotState = A.hs; D.hitAnimal(A, 80, 100, false);
          out.kill = { dead: A.dead, pts: +(D.hunt.score - s1).toFixed(1) }; D.dinoTick(1 / 30); out.afterKill = { hunter: !!D.DINO.hunter, gap: D.DINO.gap > 30 };
          // random timing: an hour standing around
          const starts = []; let tt = 0; D.DINO.gap = 60; D.DINO.hunter = null; D.DINO.pending = 0; let n0 = D.DINO.hunts;
          for (let i = 0; i < 3600 * 10; i++) { tt += .1; D.dinoTick(.1); if (D.DINO.hunts > n0) { n0 = D.DINO.hunts; starts.push(tt); if (D.DINO.hunter) D.DINO.hunter.gone = true; } }
          const gaps = starts.slice(1).map((s, i) => s - starts[i]); out.timing = { n: starts.length, minGap: Math.round(Math.min(...gaps)), maxGap: Math.round(Math.max(...gaps)) };
          // sounds play without errors
          D.initSound(); for (const k of ['raptor', ...DN]) { const B = D.beasts.find(a => a.kind === k) || A; for (const ty of ['call', 'stalk', 'charge', 'hurt', 'die', 'bite']) D.dinoCall(B, ty); } D.dinoCue();
          out.sound = !!D.SND.ctx;
          return out; }""")
        print(json.dumps(r))
        on = r["on"]
        ok = r["huntOnBtns"] == 1 and r["switched"] and r["hikeOnBtns"] == 0 \
             and not r["pc"]["on"] and "triceratops" not in r["pc"]["kinds"] and not r["off"]["on"] and r["off"]["dinos"] == 0 \
             and on["on"] and set(on["kinds"]) == {"triceratops", "parasaur", "stego", "bronto"} and on["allHp"] and on["n"] > 20 \
             and r["tri1"]["hp"] == 250 and not r["tri1"]["dead"] and r["tri1"]["bar"] and r["tri2"]["hp"] == 100 and r["tri3"]["dead"] and not r["tri3"]["bar"] and r["tri3"]["pts"] > 10 \
             and r["raptorShots"]["sniper"] == 2 and 4 <= r["raptorShots"]["pistol"] <= 10 and r["raptorShotsRed"] >= 2 \
             and r["rayBody"]["who"] == "stego" and not r["rayBody"]["head"] and r["rayHead"]["who"] == "stego" and r["rayHead"]["head"] \
             and r["spawn"] and 65 <= r["spawn"]["d"] <= 120 and r["spawn"]["ahead"] < .65 and r["spawn"]["kind"] == "raptor" \
             and r["stalk"]["minD"] >= 12 and r["stalk"]["eyes"] > .5 and len(r["stalk"]["moves"]) >= 2 \
             and r["bite"]["t"] is not None and r["bite"]["t"] < 30 and not r["afterBite"]["hunter"] and not r["afterBite"]["inBeasts"] and r["afterBite"]["gap"] >= 45 \
             and r["leave"]["goneT"] is not None and r["leave"]["goneT"] < 32 \
             and "wait" in r["tree"]["states"] and not r["tree"]["bit"] and r["tree"]["gone"] \
             and r["shotState"] == "charge" and r["kill"]["dead"] and r["kill"]["pts"] >= 50 and not r["afterKill"]["hunter"] and r["afterKill"]["gap"] \
             and 8 <= r["timing"]["n"] <= 35 and r["timing"]["minGap"] >= 45 and r["timing"]["maxGap"] > r["timing"]["minGap"] * 2.5 and r["sound"]
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
