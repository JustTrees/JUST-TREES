import asyncio, os, sys, base64, subprocess
from playwright.async_api import async_playwright
D = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(D, "..", "baked")
JS = r"""
async () => {
  const { GLTFExporter } = await import('./node_modules/three/examples/jsm/exporters/GLTFExporter.js');
  const ex = new GLTFExporter(), out = {};
  const exp = (obj, anims) => new Promise((res, rej) => ex.parse(obj, r => { const b = new Uint8Array(r); let s = ''; for (let i = 0; i < b.length; i += 32768) s += String.fromCharCode.apply(null, b.subarray(i, i + 32768)); res(btoa(s)); }, rej, { binary: true, maxTextureSize: 512, animations: anims || [], onlyVisible: true }));
  const white = g => g.traverse(m => { m.userData = {}; if (m.isMesh) { const ms = Array.isArray(m.material) ? m.material : [m.material]; for (const x of ms) { x.color && x.color.set(0xffffff); x.onBeforeCompile = () => {}; } } });
  for (const sex of ['Male', 'Female']) for (const outfit of ['Soldier', 'Ranger', 'Peasant']) {
    const g = await makeChar({ sex, outfit, clip: 'none' }); white(g); g.name = sex + '_' + outfit; out['char_' + sex + '_' + outfit] = await exp(g); }
  for (const h of ['Buzzed', 'BuzzedFemale', 'Long', 'SimpleParted', 'Buns', 'Beard']) { const s = (await load('hair/Hair_' + h + '.gltf')).scene; s.traverse(m => { if (m.isMesh) m.material = lamb(m.material); }); white(s); out['hair_' + h] = await exp(s); }
  const names = ['Idle_Loop', 'Walk_Loop', 'Jog_Fwd_Loop', 'Sprint_Loop', 'Crouch_Idle_Loop', 'Crouch_Fwd_Loop', 'Jump_Loop', 'A_TPose', 'Hit_Head', 'Death01'];
  const sk = (await load('parts/Female_Peasant_Body.gltf')).scene; const rm = []; sk.traverse(m => { if (m.isMesh) rm.push(m); }); rm.forEach(m => m.parent.remove(m));
  out.anims = await exp(sk, names.map(findClip));
  return out;
}"""
async def main():
    srv = subprocess.Popen(["python3", "-m", "http.server", "8796"], cwd=D, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"]); pg = await b.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type in ("error",) else None)
            await asyncio.sleep(.8); await pg.goto("http://127.0.0.1:8796/view.html"); await pg.wait_for_function("window.ready === true", timeout=60000)
            await pg.evaluate("window.CH={K:1};0"); await pg.evaluate(open(os.path.join(D, "compose.js")).read())
            r = await pg.evaluate(JS); os.makedirs(OUT, exist_ok=True)
            for k, v in r.items(): open(os.path.join(OUT, k + ".glb"), "wb").write(base64.b64decode(v))
            print("ok", len(r), errs[:3]); await b.close()
    finally: srv.terminate()
asyncio.run(main())
