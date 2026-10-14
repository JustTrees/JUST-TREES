"""1.93: the T. rex's own scream; the moment you hold the red sniper it screams from wherever it is on the map (once a round);
its footsteps carry to 330 m. Writes the scream to rex_scream.wav in the folder given as the 2nd argument (optional).
Usage: python3 dev/test_rexsound.py dbg.html [outdir]"""
import os, sys, asyncio, json, base64
from playwright.async_api import async_playwright
TARGET = 'file://' + os.path.abspath(sys.argv[1]); OUT = sys.argv[2] if len(sys.argv) > 2 else None
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required"])
        pg = await (await b.new_context(viewport={"width": 320, "height": 200})).new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append("PE " + str(e)))
        await pg.goto(TARGET); await pg.wait_for_timeout(800)
        r = await pg.evaluate("""async () => { window.FREEZE = true; const out = {};
          D.setSeed(5); D.setVR(true); D.setMode('hunt'); D.set.dino = true; D.set.env = 'climate'; D.set.land = 'natural'; D.set.size = 'xl'; D.set.lat = 42; D.set.month = 6; D.set.weather = 'clear'; D.set.density = .5; D.generate(); D.state = 'play';
          D.initSound(); const live = D.SND.ctx;
          // the scream itself, rendered offline
          const oc = new OfflineAudioContext(1, 44100 * 4.5, 44100); D.SND.ctx = oc; const g = oc.createGain(); g.connect(oc.destination); D.rexScream(g, 0, 1, 1); D.SND.ctx = live;
          const buf = await oc.startRendering(); const a = buf.getChannelData(0); let pk = 0, nan = false, rms = 0; for (const v of a) { if (v !== v) nan = true; pk = Math.max(pk, Math.abs(v)); rms += v * v; }
          out.scream = { peak: +pk.toFixed(2), rms: +Math.sqrt(rms / a.length).toFixed(3), nan };
          const n = a.length, wav = new DataView(new ArrayBuffer(44 + n * 2)), ws = (o, s) => { for (let i = 0; i < s.length; i++) wav.setUint8(o + i, s.charCodeAt(i)); };
          ws(0, 'RIFF'); wav.setUint32(4, 36 + n * 2, true); ws(8, 'WAVEfmt '); wav.setUint32(16, 16, true); wav.setUint16(20, 1, true); wav.setUint16(22, 1, true); wav.setUint32(24, 44100, true); wav.setUint32(28, 88200, true); wav.setUint16(32, 2, true); wav.setUint16(34, 16, true); ws(36, 'data'); wav.setUint32(40, n * 2, true);
          const k = .9 / Math.max(pk, 1e-6); for (let i = 0; i < n; i++) wav.setInt16(44 + i * 2, Math.max(-1, Math.min(1, a[i] * k)) * 32767, true);
          let s = ''; const u8 = new Uint8Array(wav.buffer); for (let i = 0; i < u8.length; i += 32768) s += String.fromCharCode.apply(null, u8.subarray(i, i + 32768)); out.wav = btoa(s);
          // the announce: only once you hold the red sniper, once a round, from across the map
          D.SND.on = true; const rex = D.beasts.find(A => A.kind === 'trex'); out.rex = !!rex; out.loot = D.lootMode();
          if (rex) { out.rexD = Math.round(Math.hypot(rex.x - D.P.x, rex.z - D.P.z));
            D.setLoot({ hunt: 4 }); D.rexAnnounce(); out.before = !!D.DINO.rexHeard;
            D.setLoot({ hunt: 5 }); D.rexAnnounce(); out.after = !!D.DINO.rexHeard; out.voices = D.DINO.voices.length;
            // footsteps at 300 m
            rex.x = D.P.x + 300; rex.z = D.P.z; rex.speed = 2.4; rex.stepAcc = 99; D.DINO.voices.length = 0; for (const v of D.DINO.pool) v.until = 0; D.dinoSteps(1 / 30); out.step300 = D.DINO.voices.length;
            rex.x = D.P.x + 360; rex.stepAcc = 99; for (const v of D.DINO.pool) v.until = 0; D.DINO.voices.length = 0; D.dinoSteps(1 / 30); out.step360 = D.DINO.voices.length; }
          return out; }""")
        w = r.pop("wav")
        if OUT: open(os.path.join(OUT, "rex_scream.wav"), "wb").write(base64.b64decode(w))
        print(json.dumps(r)); print("errors", errs[:5])
        ok = r["scream"]["peak"] > .05 and not r["scream"]["nan"] and r.get("rex") and not r["before"] and r["after"] and r["step300"] > 0 and r["step360"] == 0 and not errs
        print("PASS" if ok else "FAIL"); await b.close(); return ok
sys.exit(0 if asyncio.run(main()) else 1)
