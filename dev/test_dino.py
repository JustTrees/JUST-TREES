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
          const P = D.P, home = [P.x, P.z], ground = () => { P.y = D.groundAt(P.x, P.z); D.vr.climbing = false; D.vr.cl = null; D.camera.position.set(P.x, P.y + 1.7, P.z); D.camera.rotation.set(0, 0, 0, 'YXZ'); D.camera.updateMatrixWorld(); };
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
          const rb = shot(bodyP); let rh = shot(hp2); out.rayBody = { who: rb[1] && rb[1].kind, head: rb[2] };
          for (const B of D.beasts.filter(A => A.kind === 'stego' && !A.dead)) { if (rh[1] === st && rh[2]) break; B.root.visible = true; B.root.updateMatrixWorld(true); const bx = Math.sin(B.yaw), bz = Math.cos(B.yaw), hp3 = B.head.localToWorld(new T.Vector3(0, -.05, .3)), o = new T.Vector3(hp3.x + bx * 30 + bz * 8, hp3.y + 1, hp3.z + bz * 30 - bx * 8); rh = D.animalRay(o, hp3.clone().sub(o).normalize(), .5); if (rh[2]) break; }   // (another animal can be in the way: try another)
          out.rayHead = { who: rh[1] && rh[1].kind, head: rh[2] };
          // a shot triceratops runs (1.77: no charge); hits don't make a cry every time, it flinches instead
          const t2 = D.beasts.find(A => A.kind === 'triceratops' && !A.dead && A !== tri); P.x = t2.x + 25; P.z = t2.z; ground(); D.UW.drown = 0; D.initSound();
          D.scatterBeasts(P); D.hitAnimal(t2, 25, 0, false, 'hunt'); const fl0 = t2.flinch; const d0t = Math.hypot(t2.x - P.x, t2.z - P.z); step(6); out.triRun = { angry: !!t2.angry, flinch: fl0, further: Math.hypot(t2.x - P.x, t2.z - P.z) > d0t + 5, got: D.UW.drown > 0 };
          const pz = D.beasts.find(A => A.kind === 'parasaur' && !A.dead); D.DINO.voices.length = 0; let tms = performance.now(); for (let i = 0; i < 30; i++) { D.hitAnimal(pz, 60, 0, false, 'ar'); D.updateAnimals(1 / 30); } tms = performance.now() - tms;
          out.akBurst = { voices: D.DINO.voices.length, ms: Math.round(tms), dead: pz.dead };
          // the raptor (back at the start spot, well inside the map)
          P.x = home[0]; P.z = home[1]; ground(); D.UW.drown = 0; D.UW.red = 0;
          const startHunt = () => { D.DINO.gap = 0; D.DINO.pending = 0; D.dinoStartHunt(); let t = 0; while (!D.DINO.hunter && t < 6) { D.dinoTick(1 / 30); t += 1 / 30; } return D.DINO.hunter; };
          const ang = a => Math.atan2(Math.sin(a), Math.cos(a));
          let A = startHunt(); const dist = () => Math.hypot(A.x - P.x, A.z - P.z), fw = new T.Vector3(); D.camera.getWorldDirection(fw);
          out.spawn = A ? { d: Math.round(dist()), ahead: +(((A.x - P.x) * fw.x + (A.z - P.z) * fw.z) / dist()).toFixed(2), kind: A.kind, hp: A.hpMax, jaw: !!A.jaw } : null;
          const watch = (secs, keep) => { let minD = 1e9, sumD = 0, eyes = 0, frames = 0, moves = new Set(), turned = 0, spd = 0, nSp = 0; const states = new Set();
            step(secs, () => { if (keep) keep(); const dd = dist(); minD = Math.min(minD, dd); sumD += dd; const toP = Math.atan2(P.x - A.x, P.z - A.z); frames++; if (Math.abs(ang(toP - A.yaw - A.look)) < .45) eyes++; if (Math.abs(A.look) > .5) turned++; if (A.move === 'circle' || A.move === 'weave') { spd += A.speed; nSp++; } moves.add(A.move); states.add(A.hs); });
            return { minD: Math.round(minD), meanD: Math.round(sumD / frames), eyes: +(eyes / frames).toFixed(2), turned: +(turned / frames).toFixed(2), speed: +(spd / Math.max(1, nSp)).toFixed(1), moves: [...moves], states: [...states] }; };
          A.stalkFor = 999; out.tease = watch(40);
          A.hp = A.hpMax * .42; A.top = A.hp; A.sinceHit = 0; out.teaseLow = watch(15, () => { A.sinceHit = 0; });   // worn down: closer in
          // damage and healing: AK heals back a bar short each time; sniper never heals
          A.hp = A.top = A.hpMax; A.healing = false; for (let i = 0; i < 10; i++) D.hitAnimal(A, 60, 0, false, 'ar'); const ak1 = A.hp; step(12); const heal1 = A.hp;
          for (let i = 0; i < 10; i++) D.hitAnimal(A, 60, 0, false, 'ar'); step(14); const heal2 = A.hp;
          A.hp = A.top = A.hpMax; A.healing = false; D.hitAnimal(A, 60, 0, false, 'hunt'); D.hitAnimal(A, 60, 0, false, 'hunt'); const sn = A.hp; step(14);
          out.heal = { ak1: Math.round(ak1), heal1: Math.round(heal1), heal2: Math.round(heal2), sn: Math.round(sn), snHealed: Math.round(A.hp), state: A.hs };
          const kills = g => { A.hp = A.top = A.hpMax; let n = 0; while (A.hp > 0 && n < 200) { A.hp -= D.RAPTOR_DMG[g]; n++; } A.hp = A.top = A.hpMax; return n; };
          out.shotsToKill = { sniper: kills('hunt'), ak: kills('ar') };
          // worn down to 3 bars: it curves in; inside 15 m it gets you
          A.hp = A.hpMax * .36; A.top = A.hp; D.hitAnimal(A, 60, 0, false, 'ar'); D.hitAnimal(A, 60, 0, false, 'ar'); D.hitAnimal(A, 60, 0, false, 'ar'); step(.2); out.lowBars = { f: +(A.hp / A.hpMax).toFixed(2), state: A.hs };
          let bit = null, lat = 0, n2 = 0, p0 = [A.x, A.z], trc = []; step(30, t => { if (Math.round(t * 30) % 20 === 0) trc.push([Math.round(A.x - P.x), Math.round(A.z - P.z), A.hs, A.mode, +A.speed.toFixed(1), A.ghostT > 0 ? 'G' : '', A.doomT ? 'D' : '', D.UW.drown]); const vx = A.x - p0[0], vz = A.z - p0[1], dd = dist(); if (dd > 20) { const c = Math.abs(vx * (P.z - A.z) - vz * (P.x - A.x)) / (Math.hypot(vx, vz) * dd + 1e-6); lat += c; n2++; } p0 = [A.x, A.z]; if (D.UW.drown > 0) { bit = t; return true; } });
          out.charge = { trace: bit === null ? trc : null, bite: bit, curve: +(lat / Math.max(1, n2)).toFixed(2), n: n2 };   // (n: frames it was still over 20 m away)
          D.UW.drown = 0; D.UW.red = 0; D.dinoTick(1 / 30); out.afterBite = { hunter: !!D.DINO.hunter, inBeasts: D.beasts.includes(A) };
          // never shot: after the long tease it comes for you anyway
          P.x = home[0]; P.z = home[1]; ground(); A = startHunt(); A.giveUp = false; A.hsT = A.stalkFor + 1; let st2 = null; let bit2 = null;
          step(45, t => { if (!st2) st2 = A.hs; if (D.UW.drown > 0) { bit2 = t; return true; } }); out.unshot = { state: st2, bite: bit2 };
          D.UW.drown = 0; D.UW.red = 0; D.dinoTick(1 / 30);
          // up a tree: it waits underneath, then gives up
          P.x = home[0]; P.z = home[1]; ground(); A = startHunt(); A.giveUp = false; A.hsT = A.stalkFor + 1; D.vr.climbing = true; const tst = new Set(); let tbit = false;
          step(70, () => { tst.add(A.hs); if (D.UW.drown > 0) tbit = true; return A.gone; }); out.tree = { states: [...tst], bit: tbit, gone: !!A.gone }; D.vr.climbing = false; D.dinoTick(1 / 30);
          // killing it: ~5 sniper hits, big bonus
          P.x = home[0]; P.z = home[1]; ground(); A = startHunt(); const s1 = D.hunt.score; let n = 0; while (!A.dead && n < 30) { D.hitAnimal(A, 80, 0, false, 'hunt'); n++; }
          out.kill = { n, dead: A.dead, pts: +(D.hunt.score - s1).toFixed(1) }; D.dinoTick(1 / 30); out.afterKill = { hunter: !!D.DINO.hunter };
          // random timing: an hour standing around
          const starts = []; let tt = 0; D.DINO.gap = 60; D.DINO.hunter = null; D.DINO.pending = 0; let n0 = D.DINO.hunts;
          for (let i = 0; i < 3600 * 10; i++) { tt += .1; D.dinoTick(.1); if (D.DINO.hunts > n0) { n0 = D.DINO.hunts; starts.push(tt); if (D.DINO.hunter) D.DINO.hunter.gone = true; } }
          const gaps = starts.slice(1).map((s, i) => s - starts[i]); out.timing = { n: starts.length, minGap: Math.round(Math.min(...gaps)), maxGap: Math.round(Math.max(...gaps)) };
          // 1.79: nobody gets stuck: dense redwood woods, every dinosaur pulled in close, the longest time any one stands wedged while trying to walk
          { D.setSeed(9); D.setVR(true); D.setMode('hunt'); D.set.dino = true; D.set.env = 'redwood'; D.set.size = 'medium'; D.set.lat = 40; D.set.density = .8; D.generate(); D.state = 'play';
            const Q = D.P; Q.y = D.groundAt(Q.x, Q.z); D.camera.position.set(Q.x, Q.y + 1.7, Q.z); D.DINO.gap = 1e9; const dinos = D.beasts.filter(A => A.hpMax);
            for (const A of dinos) { A.x = Q.x + (Math.random() - .5) * 300; A.z = Q.z + (Math.random() - .5) * 300; if (!D.okSpot(A.x, A.z)) { A.x = Q.x; A.z = Q.z; } A.home = [A.x, A.z]; A.y = D.beastGround(A, A.x, A.z); }
            const last = new Map(), streak = new Map(); let worst = 0;
            for (let i = 0; i < 30 * 60; i++) { D.updateAnimals(1 / 30); if (i % 30 === 0) for (const A of dinos) { const L = last.get(A); if (L && A.mode === 'walk' && A.want > .3 && !A.dead) { const n = Math.hypot(A.x - L[0], A.z - L[1]) < .3 ? (streak.get(A) || 0) + 1 : 0; streak.set(A, n); worst = Math.max(worst, n); } last.set(A, [A.x, A.z]); } }
            D.DINO.gap = 0; D.dinoStartHunt(); for (let i = 0; i < 200 && !D.DINO.hunter; i++) D.dinoTick(1 / 30); const R = D.DINO.hunter; R.stalkFor = 999; let rs = 0, rmax = 0, lp = null;
            for (let i = 0; i < 30 * 45; i++) { D.updateAnimals(1 / 30); if (i % 15 === 0) { if (lp && R.mode === 'walk' && R.want > 2) { rs = Math.hypot(R.x - lp[0], R.z - lp[1]) < 1 ? rs + 1 : 0; rmax = Math.max(rmax, rs); } lp = [R.x, R.z]; } }
            out.stuck = { dinoWorstSecs: worst, raptorWorstHalfSecs: rmax, thru: dinos.every(A => A.thru) }; }
          // sounds: 3D at the animal, with forest echo
          D.initSound(); D.DINO.voices.length = 0;
          for (const k of DN) { const B = D.beasts.find(a => a.kind === k && !a.dead); for (const ty of ['call', 'stalk', 'charge', 'hurt', 'die']) D.dinoCall(B, ty); }
          const R = D.addGround('raptor', P.x + 30, P.z); for (const ty of ['stalk', 'charge', 'hurt', 'die', 'bite']) D.dinoCall(R, ty); D.dinoCue();
          out.sound = { ctx: !!D.SND.ctx, voices: D.DINO.voices.length, verb: !!D.SND.verb, panner: D.DINO.voices[0] && D.DINO.voices[0].pn.panningModel };
          return out; }""")
        print(json.dumps(r))
        on = r["on"]
        ok = r["huntOnBtns"] == 1 and r["switched"] and r["hikeOnBtns"] == 0 \
             and not r["pc"]["on"] and "triceratops" not in r["pc"]["kinds"] and not r["off"]["on"] and r["off"]["dinos"] == 0 \
             and on["on"] and set(on["kinds"]) == {"triceratops", "parasaur", "stego", "bronto", "trex", "ptero"} and on["kinds"]["trex"] == 1 and on["allHp"] and on["n"] > 60 \
             and r["tri1"]["hp"] == 300 and not r["tri1"]["dead"] and not r["tri1"]["bar"] and not r["tri1"]["angry"] and r["tri2"]["hp"] == 120 and r["tri3"]["dead"] and not r["tri3"]["bar"] and r["tri3"]["pts"] > 10 \
             and 8 <= r["raptorShots"]["sniper"] <= 10 and r["raptorShots"]["ar"] >= 50 \
             and r["rayBody"]["who"] == "stego" and not r["rayBody"]["head"] and r["rayHead"]["who"] == "stego" and r["rayHead"]["head"] \
             and not r["triRun"]["angry"] and r["triRun"]["flinch"] > 0 and r["triRun"]["further"] and not r["triRun"]["got"] and r["akBurst"]["voices"] <= 8 and r["akBurst"]["dead"] \
             and r["spawn"] and 80 <= r["spawn"]["d"] <= 120 and r["spawn"]["ahead"] < .65 and r["spawn"]["kind"] == "raptor" and r["spawn"]["hp"] == 1000 and r["spawn"]["jaw"] \
             and r["tease"]["minD"] >= 10 and r["tease"]["meanD"] >= 55 and r["tease"]["speed"] > 7 and r["tease"]["eyes"] > .3 and r["tease"]["turned"] > .1 and len(r["tease"]["moves"]) >= 2 and r["tease"]["states"] == ["stalk"] \
             and r["teaseLow"]["meanD"] < r["tease"]["meanD"] - 12 and r["teaseLow"]["meanD"] >= 22 and r["teaseLow"]["speed"] > r["tease"]["speed"] \
             and r["heal"]["ak1"] == 800 and 880 <= r["heal"]["heal1"] <= 900 and 780 <= r["heal"]["heal2"] <= 800 and r["heal"]["snHealed"] <= 600 and r["heal"]["state"] == "stalk" \
             and r["shotsToKill"]["sniper"] == 5 and r["shotsToKill"]["ak"] == 50 \
             and r["lowBars"]["f"] <= .3 and r["lowBars"]["state"] == "charge" and r["charge"]["bite"] is not None and (r["charge"]["n"] < 10 or r["charge"]["curve"] > .05) and not r["afterBite"]["hunter"] and not r["afterBite"]["inBeasts"] \
             and r["unshot"]["state"] == "approach" and r["unshot"]["bite"] is not None \
             and "wait" in r["tree"]["states"] and not r["tree"]["bit"] and r["tree"]["gone"] \
             and r["kill"]["n"] == 5 and r["kill"]["dead"] and r["kill"]["pts"] >= 75 and not r["afterKill"]["hunter"] \
             and 8 <= r["timing"]["n"] <= 35 and r["timing"]["minGap"] >= 45 and r["timing"]["maxGap"] > r["timing"]["minGap"] * 2.5 \
             and r["stuck"]["dinoWorstSecs"] <= 6 and r["stuck"]["raptorWorstHalfSecs"] <= 3 and r["stuck"]["thru"] \
             and r["sound"]["ctx"] and r["sound"]["voices"] >= 5 and r["sound"]["verb"] and r["sound"]["panner"] == "HRTF"
        print("PASS" if ok and not errs else "FAIL", errs or ""); await b.close()
        if not ok or errs: sys.exit(1)
asyncio.run(main())
