import os, sys
TARGET = 'file://' + os.path.abspath(sys.argv[1])
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader","--enable-webgl","--ignore-gpu-blocklist"])
        for mode in ["hike", "hunt"]:
            ctx = await b.new_context(viewport={"width":640,"height":360}); pg = await ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text[:200]) if m.type=="error" and "GPU stall" not in m.text else None)
            await pg.goto(TARGET); await pg.wait_for_timeout(800)
            for _ in range(3): await pg.evaluate("document.getElementById('intro').click()"); await pg.wait_for_timeout(1700)
            await pg.evaluate(f"document.querySelector('.modeBtn[data-mode=\"{mode}\"]').click()")
            await pg.evaluate("document.querySelector('#sizes button[data-size=\"xs\"]').click(); document.getElementById('startBtn').click()")
            for i in range(90):
                await pg.wait_for_timeout(1000)
                if await pg.evaluate("document.getElementById('loading').classList.contains('hidden')"): break
            await pg.keyboard.press("KeyX"); await pg.wait_for_timeout(2500)
            print(mode, await pg.inner_text("#ver"), "| errors:", errs or "none"); await ctx.close()
        await b.close()
asyncio.run(main())
