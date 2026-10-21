"""Our own Cloudflare relay (1.83): the game asks the Worker (/turn) for a relay pass first, and falls back to the free
Open Relay if the Worker fails, says no, or takes too long. The Worker is faked here (no network in tests).
Usage: python3 dev/test_relay.py /tmp/dbg.html"""
import os, sys, asyncio, json
from playwright.async_api import async_playwright
T = 'file://' + os.path.abspath(sys.argv[1])
CASES = {
  "cloudflare": "async () => ({ ok: true, json: async () => ({ iceServers: [{ urls: ['stun:stun.cloudflare.com:3478'] }, { urls: ['turn:turn.cloudflare.com:3478?transport=udp', 'turns:turn.cloudflare.com:443?transport=tcp'], username: 'u1', credential: 'c1' }] }) })",
  "workerNotSetUp": "async () => ({ ok: false, status: 503, json: async () => ({ error: 'relay not set up yet' }) })",
  "networkError": "async () => { throw new Error('offline'); }",
  "emptyAnswer": "async () => ({ ok: true, json: async () => ({ iceServers: [] }) })",
  "tooSlow": "(u, o) => new Promise((res, rej) => { o.signal.addEventListener('abort', () => rej(new Error('aborted'))); })",
}
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        out = {}; errs = []
        for name, fake in CASES.items():
            pg = await (await b.new_context(viewport={"width": 300, "height": 200})).new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(T); await pg.wait_for_timeout(500)
            out[name] = await pg.evaluate("""async () => { window.FREEZE = true; D.renderer.setAnimationLoop(null); let asked = null;
              window.fetch = (u, o) => { asked = u; return (%s)(u, o); };
              D.MP.relay = undefined; const t0 = performance.now(); const r = await D.mpRelay();
              const peer = D.mpNewPeer('justtrees-test-relay'); const ice = peer && peer.options && peer.options.config ? peer.options.config.iceServers : null; try { peer.destroy(); } catch (e) {}
              return { from: D.MP.relayFrom, asked, n: r.length, user: r[0] && r[0].username, secs: +((performance.now() - t0) / 1000).toFixed(1),
                       iceHasRelay: !!(ice && ice.some(x => x.username === (r[0] && r[0].username))), iceHasStun: !!(ice && ice.some(x => String(x.urls).includes('stun:'))) }; }""" % fake)
            await pg.close()
        print(json.dumps(out, indent=1)); print("errors:", errs or "none")
        c = out["cloudflare"]
        ok = (c["from"] == "cloudflare" and c["user"] == "u1" and c["asked"].endswith("/turn") and c["iceHasRelay"] and c["iceHasStun"]
              and all(out[k]["from"] == "openrelay" and out[k]["n"] == 1 and ":" in out[k]["user"] and out[k]["iceHasRelay"] for k in ("workerNotSetUp", "networkError", "emptyAnswer", "tooSlow"))
              and 3.5 < out["tooSlow"]["secs"] < 6 and not errs)
        print("PASS" if ok else "FAIL"); await b.close()
        if not ok: sys.exit(1)
asyncio.run(main())
