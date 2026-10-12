"""Prehistoric (1.75-1.76, VR hunting only): a switch in the Hunting setup. Same maps; the animals are dinosaurs (Triceratops, Parasaurolophus,
Stegosaurus, Brontosaurus; 1.76: twice the herds). Every dinosaur takes several shots: a 10-bar health bar shows once hurt; each gun has its own
damage against dinosaurs (sniper 120, assault rifle 18, SMG 10, pistol 20, gun stars add more), a head hit 1.5x. A shot triceratops lowers its
horns and charges you: a gouge kills (red blackout, wake up elsewhere); up a tree or far away, it gives up.
The raptor (1.76: bigger, darker, a jaw that opens, ~1000 health): at random times (no rhythm) a low warning swell, it appears far off out of
sight and teases: circles, creeps, freezes, fake rushes, turning its head to watch you. Hit, it speeds up; left alone it heals and slows again;
worn down to 3 of 10 bars it charges. Never shot, in the end it comes for you at a steady lope. Up a tree it paces underneath and gives up.
Sounds come from the animal in 3D (moving with it), duller and with more forest echo the further off. Off, on PC/phone: nothing changes."""
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
          if (!D.VRUI.panels || !D.VRUI.panels.setup) { D.setVR(true); D.vruiOpen('setup'); }
          const btns = () => D.VRUI.panels.setup ? D.VRUI.panels.setup.widgets.filter(w => w.label === 'On' && !(w.hide && w.hide())) : [];
          D.setMode('hunt'); D.set.dino = false; const hb = btns(); out.huntOnBtns = hb.length; if (hb.length === 1) hb[0].on(); out.switched = D.set.dino === true;
          D.setMode('hike'); out.hikeOnBtns = btns().length;
          const gen = (vrOn, dino, sd) => { D.setSeed(sd); D.setVR(vrOn); D.setMode('hunt'); D.set.dino = dino; D.set.env = 'climate'; D.set.land = 'natural'; D.set.size = 'large'; D.set.lat = 42; D.set.month = 6; D.set.weather = 'clear'; D.set.density = .5; D.generate(); D.state = 'play'; };
          const kinds = () => { const k = {}; for (const A of D.beasts) k[A.kind] = (k[A.kind] || 0) + 1; return k; };
          gen(false, true, 5); out.pc = { on: D.DINO.on, kinds: Object.keys(kinds()) };
          gen(true, false, 5); out.off = { on: D.DINO.on, dinos: D.beasts.filter(A => A.hpMax).length };
          gen(true, true, 5); out.on = { on: D.DINO.on, kinds: kinds(), allHp: D.beasts.every(A => A.hpMax > 0), n: D.beasts.length };
          const P = D.P, ground = () => { P.y = D.groundAt(P.x, P.z); D.vr.climbing = false; D.vr.cl = null; D.camera.position.set(P.x, P.y + 1.7, P.z); D.camera.rotation.set(0, 0, 0, 'YXZ'); D.camera.updateMatrixWorld(); };
          const step = (secs, f) => { for (let i = 0; i < secs * 30; i++) { D.updateAnimals(1 / 30); if (f && f(i / 30)) return true; } return false; };
          // damage: sniper hits on a triceratops (head 1.5x), the 10-bar bar
          const tri = D.beasts.find(A => A.kind === 'triceratops'), s0 = D.hunt.score;
          D.hitAnimal(tri, 50, 0, false, 'hunt'); out.tri1 = { hp: tri.hp, dead: tri.dead, bar: !!(tri.bar && tri.bar.g.visible), angry: !!tri.angry };
          D.hitAnimal(tri, 50, 0, true, 'hunt'); out.tri2 = { hp: tri.hp };
          D.hitAnimal(tri, 50, 0, false, 'hunt'); out.tri3 = { dead: tri.dead, bar: !!(tri.bar && tri.bar.g.visible), pts: +(D.hunt.score - s0).toFixed(1) };
          const per = k => D.DINO_DMG ? 0 : 0, shots = (hp, d) => Math.ceil(hp / d);
          out.raptorShots = { sniper: shots(1000, 120), ar: shots(1000, 18), smg: shots(1000, 10), pistol: shots(1000, 20) };
          // a real shot: body vs head
          const st = D.beasts.find(A => A.kind === 'stego' && !A.dead); st.root.visible = true; st.root.updateMatrixWorld(true);
          const bodyP = new T.Vector3(st.x, st.y + 1.8, st.z), hp2 = st.head.localToWorld(new T.Vector3(0, -.05, .3));
          const fx = Math.sin(st.yaw), fz = Math.cos(st.yaw), shot = tgt => { const o = new T.Vector3(tgt.x + fx * 30 + fz * 8, tgt.y + 1, tgt.z + fz * 30 - fx * 8), d = tgt.clone().sub(o).normalize(); return D.animalRay(o, d, .5); };
          const rb = shot(bodyP), rh = shot(hp2); out.rayBody = { who: rb[1] && rb[1].kind, head: rb[2] }; out.rayHead = { who: rh[1] && rh[1].kind, head: rh[2] };
          // an angry triceratops: you stand 25 m away in the open, shoot it once
          const t2 = D.beasts.find(A => A.kind === 'triceratops' && !A.dead && A !== tri); P.x = t2.x + 25; P.z = t2.z; ground(); D.UW.drown = 0;
          D.hitAnimal(t2, 25, 0, false, 'hunt'); let headDown = 0, gotT = null;
          step(20, t => { if (t2.head.rotation.x > .3) headDown++; if (D.UW.drown > 0) { gotT = t; return true; } });
          out.gore = { angry0: true, headDown: headDown > 10, gotT, alive: !t2.dead };
          D.UW.drown = 0; D.UW.red = 0;
          // the raptor
          ground();
          const startHunt = () => { D.DINO.gap = 0; D.DINO.pending = 0; D.dinoStartHunt(); let t = 0; while (!D.DINO.hunter && t < 6) { D.dinoTick(1 / 30); t += 1 / 30; } return D.DINO.hunter; };
          const ang = a => Math.atan2(Math.sin(a), Math.cos(a));
          let A = startHunt(); const dist = () => Math.hypot(A.x - P.x, A.z - P.z), fw = new T.Vector3(); D.camera.getWorldDirection(fw);
          out.spawn = A ? { d: Math.round(dist()), ahead: +(((A.x - P.x) * fw.x + (A.z - P.z) * fw.z) / dist()).toFixed(2), kind: A.kind, hp: A.hpMax, jaw: !!A.jaw } : null;
          let minD = 1e9, eyes = 0, frames = 0, moves = new Set(), headTurned = 0, states = new Set();
          step(30, () => { minD = Math.min(minD, dist()); const toP = Math.atan2(P.x - A.x, P.z - A.z); frames++; if (Math.abs(ang(toP - A.yaw - A.look)) < .45) eyes++; if (Math.abs(A.look) > .5) headTurned++; moves.add(A.move); states.add(A.hs); });
          out.tease = { minD: Math.round(minD), eyes: +(eyes / frames).toFixed(2), headTurned: +(headTurned / frames).toFixed(2), moves: [...moves], states: [...states] };
          // hit it: no charge, it speeds up; then it heals and slows
          const calm = A.want; A.move = 'circle'; A.creepT = 30; step(1); const before = A.want;
          D.hitAnimal(A, 60, 0, false, 'hunt'); D.hitAnimal(A, 60, 0, false, 'hunt'); const hpHit = A.hp; step(1); const fast = A.want, stateHit = A.hs;
          A.creepT = 30; A.move = 'circle'; step(14); out.fight = { before: +before.toFixed(1), fast: +fast.toFixed(1), stateHit, hpHit: Math.round(hpHit), healed: Math.round(A.hp), slower: +A.want.toFixed(1) };
          // wear it down to 3 bars: it charges
          A.hp = A.hpMax * .36; D.hitAnimal(A, 60, 0, false, 'hunt'); step(.2); out.lowBars = { f: +(A.hp / A.hpMax).toFixed(2), state: A.hs };
          let bit = null; step(30, t => { if (D.UW.drown > 0) { bit = t; return true; } }); out.lowBite = bit;
          D.UW.drown = 0; D.UW.red = 0; D.dinoTick(1 / 30); out.afterBite = { hunter: !!D.DINO.hunter, inBeasts: D.beasts.includes(A) };
          // never shot: after the long tease it comes for you anyway
          ground(); A = startHunt(); A.giveUp = false; A.hsT = A.stalkFor + 1; let st2 = null; let bit2 = null;
          step(45, t => { if (!st2) st2 = A.hs; if (D.UW.drown > 0) { bit2 = t; return true; } }); out.unshot = { state: st2, bite: bit2 };
          D.UW.drown = 0; D.UW.red = 0; D.dinoTick(1 / 30);
          // up a tree: it waits underneath, then gives up
          ground(); A = startHunt(); A.giveUp = false; A.hsT = A.stalkFor + 1; D.vr.climbing = true; const tst = new Set(); let tbit = false;
          step(70, () => { tst.add(A.hs); if (D.UW.drown > 0) tbit = true; return A.gone; }); out.tree = { states: [...tst], bit: tbit, gone: !!A.gone }; D.vr.climbing = false; D.dinoTick(1 / 30);
          // killing it: about 9 sniper hits, big bonus
          ground(); A = startHunt(); const s1 = D.hunt.score; let n = 0; while (!A.dead && n < 30) { D.hitAnimal(A, 80, 0, false, 'hunt'); n++; }
          out.kill = { n, dead: A.dead, pts: +(D.hunt.score - s1).toFixed(1) }; D.dinoTick(1 / 30); out.afterKill = { hunter: !!D.DINO.hunter };
          // random timing: an hour standing around
          const starts = []; let tt = 0; D.DINO.gap = 60; D.DINO.hunter = null; D.DINO.pending = 0; let n0 = D.DINO.hunts;
          for (let i = 0; i < 3600 * 10; i++) { tt += .1; D.dinoTick(.1); if (D.DINO.hunts > n0) { n0 = D.DINO.hunts; starts.push(tt); if (D.DINO.hunter) D.DINO.hunter.gone = true; } }
          const gaps = starts.slice(1).map((s, i) => s - starts[i]); out.timing = { n: starts.length, minGap: Math.round(Math.min(...gaps)), maxGap: Math.round(Math.max(...gaps)) };
          // sounds: 3D at the animal, with forest echo
          D.initSound(); D.DINO.voices.length = 0;
          for (const k of DN) { const B = D.beasts.find(a => a.kind === k && !a.dead); for (const ty of ['call', 'stalk', 'charge', 'hurt', 'die']) D.dinoCall(B, ty); }
          const R = D.addGround('raptor', P.x + 30, P.z); for (const ty of ['stalk', 'charge', 'hurt', 'die', 'bite']) D.dinoCall(R, ty); D.dinoCue();
          out.sound = { ctx: !!D.SND.ctx, voices: D.DINO.voices.length, verb: !!D.SND.verb, panner: D.DINO.voices[0] && D.DINO.voices[0].pn.panningModel };
          return out; }""")
        print(json.dumps(r))
        on, f = r["on"], r["fight"]
        ok = r["huntOnBtns"] == 1 and r["switched"] and r["hikeOnBtns"] == 0 \
             and not r["pc"]["on"] and "triceratops" not in r["pc"]["kinds"] and not r["off"]["on"] and r["off"]["dinos"] == 0 \
             and on["on"] and set(on["kinds"]) == {"triceratops", "parasaur", "stego", "bronto"} and on["allHp"] and on["n"] > 60 \
             and r["tri1"]["hp"] == 300 and not r["tri1"]["dead"] and r["tri1"]["bar"] and r["tri1"]["angry"] and r["tri2"]["hp"] == 120 and r["tri3"]["dead"] and not r["tri3"]["bar"] and r["tri3"]["pts"] > 10 \
             and 8 <= r["raptorShots"]["sniper"] <= 10 and r["raptorShots"]["ar"] >= 50 \
             and r["rayBody"]["who"] == "stego" and not r["rayBody"]["head"] and r["rayHead"]["who"] == "stego" and r["rayHead"]["head"] \
             and r["gore"]["headDown"] and r["gore"]["gotT"] is not None and r["gore"]["gotT"] < 12 \
             and r["spawn"] and 65 <= r["spawn"]["d"] <= 120 and r["spawn"]["ahead"] < .65 and r["spawn"]["kind"] == "raptor" and r["spawn"]["hp"] == 1000 and r["spawn"]["jaw"] \
             and r["tease"]["minD"] >= 12 and r["tease"]["eyes"] > .5 and r["tease"]["headTurned"] > .1 and len(r["tease"]["moves"]) >= 2 and r["tease"]["states"] == ["stalk"] \
             and f["stateHit"] == "stalk" and f["fast"] > f["before"] * 1.3 and f["healed"] > f["hpHit"] + 150 and f["slower"] < f["fast"] \
             and r["lowBars"]["f"] <= .3 and r["lowBars"]["state"] == "charge" and r["lowBite"] is not None and not r["afterBite"]["hunter"] and not r["afterBite"]["inBeasts"] \
             and r["unshot"]["state"] == "approach" and r["unshot"]["bite"] is not None \
             and "wait" in r["tree"]["states"] and not r["tree"]["bit"] and r["tree"]["gone"] \
             and 8 <= r["kill"]["n"] <= 10 and r["kill"]["dead"] and r["kill"]["pts"] >= 75 and not r["afterKill"]["hunter"] \
             and 8 <= r["timing"]["n"] <= 35 and r["timing"]["minGap"] >= 45 and r["timing"]["maxGap"] > r["timing"]["minGap"] * 2.5 \
             and r["sound"]["ctx"] and r["sound"]["voices"] > 10 and r["sound"]["verb"] and r["sound"]["panner"] == "HRTF"
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
