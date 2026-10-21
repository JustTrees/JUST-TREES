import sys, asyncio, json, subprocess, time, base64, struct, os
from playwright.async_api import async_playwright
D, OUT = sys.argv[1], sys.argv[2]
COLS = {
 "Trex": {"Green": 0x4d6236, "LightGreen": 0x8a9150, "LightYellow": 0xcdb784, "Red": 0x7a2622, "Black": 0x141210},
 "Velociraptor": {"Brown": 0x7a5232, "LightBrown": 0xc49a6a, "Black": 0x141210},
 "Parasaurolophus": {"Green": 0x56864a, "LightGreen": 0x9cb468, "LightYellow": 0xe2d8a6, "Red": 0xb8582c},
 "Stegosaurus": {"DarkBrown": 0x4e5a36, "Brown": 0x7c8452, "LightBrown": 0xb06a3a},
 "Triceratops": {"Purple": 0x6a6478, "LightBrown": 0xe6dcc0, "Brown": 0x8a6a46},
 "Apatosaurus": {"Brown": 0x8a8270, "LightBrown": 0xbcb298, "Black": 0x141210, "Material": 0x8a8270},
}
FILE = {"Trex": "trex", "Velociraptor": "raptor", "Parasaurolophus": "parasaur", "Stegosaurus": "stego", "Triceratops": "triceratops", "Apatosaurus": "bronto"}
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8770", "--bind", "127.0.0.1"], cwd=D, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.5)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto("http://127.0.0.1:8770/exp.html"); await pg.wait_for_function("window.ready === true", timeout=30000)
        os.makedirs(OUT, exist_ok=True)
        for n, c in COLS.items():
            r = await pg.evaluate("([n, c]) => exp(n, c)", [n, c])
            js = r["json"].encode(); js += b" " * ((4 - len(js) % 4) % 4); bin = base64.b64decode(r["bin"])
            data = b"QDN1" + struct.pack("<I", len(js)) + js + bin
            open(os.path.join(OUT, FILE[n] + ".bin"), "wb").write(data)
            j = json.loads(js); print(n, len(data), "miss", r["miss"], "clips", [(c["n"], c["d"], len(c["tr"])) for c in j["clips"]])
        print(errs[:3]); await b.close()
try: asyncio.run(main())
finally: srv.terminate()
