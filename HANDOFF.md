# Just Trees: handoff for the next chat

Read this first. It's the current state of the game, how Ron likes to work, and what's next. (Version history lives in the git log.)

---

## 1. Ron and how to talk to him

- Ron is **not a programmer**. He's a designer with a strong feel for games, especially **VR**, and uses **Population: One** as the reference for how VR should feel. He describes things by feel; turn that into code and say back in plain words what you did.
- **Keep replies short and simple.** No jargon, no code, no long recaps ("too much mumbo"). Short lists are fine. On websites, go one click at a time.
- He sends ideas in bursts with typos and voice-to-text. Read generously. Ask at most one short question, and only if it changes what you build.
- Be honest: say what was only tested in simulation (you can never test in a real headset), what costs frame rate, what isn't free.

### What the game is
**Just Trees** is a procedurally generated wilderness in the browser: forests, mountains, lakes, weather and real animals, **VR first** (Meta Quest browser), then PC and phone. Every map is new. Protect:
- A beautiful, believable, calm place: real biomes by latitude, seasons, sun position, native animals only.
- VR that feels like Pop: One: climb anything you see, fling and glide, two-handed guns with real scopes, binoculars by bringing both hands to your face. Gestures over buttons.
- Long views. Cut far detail before cutting view distance.
- Free and simple: one HTML file on GitHub Pages, peer-to-peer multiplayer.

---

## 2. How we work

- **Each prompt: build, test, push live, send a backup file** (`just-trees-1-xx.html`), reply briefly. Next version is **1.56**.
- **Exceptions:** if he says "notes" / "just notes", or asks a question, only answer or write notes in this file — no build. Notes can wait and go up with the next build.
- **Keep PC and phone unchanged** unless he says otherwise. Most work is **VR only**; give visual changes a VR-only branch.
- **Never upload the debug build:** `index.html` must have no `window.D` / `window.FREEZE` (`dev/check_code.py` checks).
- **Never put secrets** (TURN keys etc.) in the repo, the game, or chat.

---

## 3. Where things are

- **Repo:** `github.com/JustTrees/JUST-TREES`, branch `main` (the old name redirects; the push prints a "repository moved" notice, that's fine). A new chat must request repo access.
- **Live:** https://justtrees.github.io/JUST-TREES/ (1–2 min after a push; tell him to refresh, the menu shows the version).
- **The game:** `index.html`, one file (~1.3 MB). Three.js r149 and PeerJS 1.5.4 inlined at the top, then the game script. A table of contents at the top of the script lists search words for each part. **Tuning block** right after `VERSION`: guns (`WEAP`), ammo, bullets, grenades, star tiers, loot counts, PvP timings, zone and capture numbers — change numbers there.
- **Commits:** author `JustTrees`, email `ron@mountainstylemusic.org`.

---

## 4. What exists now (v1.55)

### World (all modes)
- **Settings:** latitude (sets the biome: tropical, temperate, boreal, tundra, polar), terrain roughness, time of day, month (season), tree density, map size (XS 250 m → S 400, M 560, L 800, XL 1.2 km, XXL 1.6 km), edges (Island or Endless), landscape (Natural or Dramatic), weather (clear, rain, fog, snow/blizzard, storm; Hiking never gets fog).
- **Terrain:** heightfield with erosion and rounded summits. `H(x,z)` is the exact surface. Dramatic maps get one landmark from a generator (`makeFeature`: crevasses, canyons, rifts, walls, cliffs, mesas, buttes, terraces, craters, sinkholes, volcanoes in many shapes).
- **Trees:** trunk + branch cards, Pop: One style; big limbs you can stand on and hold; lighter far-away trees past ~270 m.
- **Rocks:** boulders, slabs, cliffs, outcrops, logs, bushes on a 1 m height grid (`rockGrid`, `rockTopAt`, `rockAround`). Overhangs work: you can stand under a rock with a gap below it (`rockLow`).
- **Look and sound:** ACES tone mapping, `grade()` colour shader, valley fog, sky with sun/moon/stars, lightning storms with distance-delayed thunder. All sound is synthesized.

### Animals (Hunting)
- **32 kinds**, native per biome (`NATIVE`): buck, bear, polar bear, baboon, panther, wolf, seal, rabbit, monkeys, big birds, plus (1.55) elephant, giraffe, zebra, rhino, lion, crocodile, parrots, mountain goat, wild horse, elk, moose, boar, coyote, fox, turkey, eagle, caribou, musk ox, arctic fox, snowy owl, and the legends Bigfoot and Yeti.
- Built from code: `buildQuad(r, QSPEC[kind])` makes most four-legged animals from a spec; separate builders for buck, bear, wolf (also coyote/fox/arctic fox), turkey, Bigfoot/Yeti (`buildApe`), birds (`buildBird` with colours), monkeys.
- Behaviour (`updateAnimals`): wander, graze, notice your movement and ease away or bolt; a shot empties the area (`fleeFar`); stuck animals squeeze free (`unstick`); standing still slowly draws them in (`lureTarget`). Birds circle; parrots fly in flocks; monkeys swing through trees.
- Scoring: a hit is a kill (tip over, bing, no blood); points = distance × `SCORE[kind]` (big easy animals low, small/flying high, legends 3).

### PC and phone (keep as is)
- PC: WASD, mouse look, click to fire, scroll to zoom/binoculars, Shift run, Space jump, C crouch, Esc menu. Phone: joystick, drag to look, buttons. Minimap, full map, drone flyover before each map. PC/phone PvP is the old bots version (on hold).

### VR
- **Getting in:** PLAY IN VR button → **height check** first (sit or stand; `vr.hOff` saved in localStorage, so seated players see from standing height) → intro → curved menu panels (laser + trigger).
- **Before each map:** a floating mini-map you can spin; point and pull the trigger to pick your start; New map / Settings / Play this map.
- **Pause:** tap Y. Includes End round (PvP host/solo).
- **Controls** (right-handed default, left-handed option): off-hand stick walks (click to sprint), gun-hand stick snap-turns 30° (zooms while scoped); tap A = gun in/out, hold A = gun wheel, tap B = mark; off-hand trigger = map; off-hand grip = two-handed grip. Real crouching, no jump/crouch buttons.
- **Guns:** sniper (bolt each shot, the only scope), assault rifle, SMG, pistol, plus grenades (5th wheel slice, up to 10). Real bullets with travel time and **no drop** (you lead moving targets). Steady fire rate, no recoil. Reload by hand: pull the magazine, push a new one, rack the bolt. Ammo cans and grenade boxes as loot.
- **Find your guns (VR Hunting and PvP):** every spawn starts with a 1-star pistol; other guns are greyed on the wheel until you find one. Guns lie on a jittered grid all over the map with a neon glow in their star colour (1★ white, 2 blue, 3 purple, 4 gold, 5 red; rarer the higher). A higher star upgrades the gun.
- **Scope:** two hands, eyepiece near your eye; the whole view zooms and the horizon stays level. **Binoculars:** empty hands, both grips at your face.
- **Climbing:** grab anything you see (trunks, branches, limbs, rocks, cliffs); fling on release; glide by spreading your arms; high gravity, no fall damage. The gun must be away to climb.
- **Under water:** walk on the bed, murky view, 5 s of breath, then respawn. Bullets go 1.5 m into water.
- **Body:** camo soldier avatar with arm IK and gloves on the controllers.

### Online (VR PvP)
- Peer to peer, **up to 8 players** (PeerJS free server + free Open Relay TURN). Host gets a 4-digit code.
- **Shared lobby:** everyone sees the host's settings and the map preview; each picks a start; coloured flags show for 3 s, then everyone drops in.
- **PvP rules:** health + shield bars (green cross = health, blue cross = shield), kill counter, round clock (5–20 min), dying spills your loot, body falls and vanishes in 3 s; drowning = no kill, lose loot and a kill, respawn with no guns.
- **Closing zone** (optional): hold and speed settings, stages, never faster than sprint, small final circle; respawns go inside the next circle.
- **Capture point** (optional): hidden smart spot, floating flag, +1 point every 20 s held alone.
- **Voice:** connects on join, positional.
- **Known problem:** some friends can't connect (strict home networks; the free relay didn't carry it). Fix later: our own relay — Cloudflare TURN behind a small Worker (make a fresh key; keep it out of the repo), or Metered. Ron will do this "another time".

---

## 5. How to build and test

- **Edit with a Python patch script** that replaces exact strings in a copy of `index.html`, **asserting each old string appears exactly once**. Write builds to the scratchpad, then copy to `index.html` when tests pass. Bump `VERSION` and `<title>`.
- **Tools in `dev/`** (Playwright + Chromium/SwiftShader):
  - `check_code.py [file] [--unused]`: parses, no function declared twice, no debug hooks.
  - `make_debug.py index.html dbg.html`: debug copy with `window.FREEZE` (step frames by hand) and `window.D` (handles to internals; add more there when a test needs them).
  - `run_all.py [file] --nm <node_modules> --jobs 4 [--only a,b]`: code check + every test. Takes ~17 min, longer than a tool call allows, so run it in the background (`setsid nohup … &`) and check the log. Online tests need a local PeerJS server (`node dev/peer_server.js <node_modules>`; `npm i peer express`).
  - Tests by area: load, landscape, water, storm, overhang, solid ground, far trees; VR moves/climb/scope/glide/guns/menus/height; bullets, grenades; animals, zoo (every biome spawns all its kinds; give a folder to get lineup pictures); online: mp, mp_fail, lobby, pvploot, zone, capture, round.
- **Push:** `git add`, commit (author `JustTrees`), `git push origin main`.

### Gotchas (don't relearn these)
- Renderer outputs linear colour: **don't mark canvas textures as sRGB** or menus go dark.
- **Inside a VR session `requestAnimationFrame` doesn't run.** Everything goes through `renderer.setAnimationLoop(loop)`.
- VR movement: `vr.readInputs()` gives world-space poses; walking moves the play space (`vr.ox/oy/oz/yaw`); `vr.placeAt` re-anchors on a new map.
- VR world settings are read at generate: `VR_ON` must be set before `generate()`.
- `obstacles` is replaced by every `generate()`: use a getter in debug hooks.
- Two functions with the same name: the later one silently wins (that bit us with grenades). `check_code.py` catches it.
- Call `updateMatrixWorld` before raycasts if things moved this frame.
- Is the Quest a "touch" device (`isTouch`)? Unknown. Don't assume.

---

## 6. His standing preferences (don't undo these)

- **No resource gathering or building.** Fights are about aim, movement and terrain.
- No camera bob; slow soft footsteps; quiet wind/trees/rain. No light shafts.
- Rounded peaks, no spikes or monoliths. Long views. Hiking has no fog.
- Native animals only; hit = kill with a bing, no blood; score per metre; animals react to your movement, not sound.
- VR: no jump/crouch buttons; off hand never steers the aim; snap turn 30°; heavy gun smoothing; two-handed scoping; binoculars at your face; glide with arms out; Pop: One climbing (high gravity, medium fling); smooth resolution; no tree sway.
- Avatars: soldiers in baggy camo with hoods; masks are achievements only.
- Shelved for now: teams, battle royale, capture zone (players could start right next to it).

---

## 7. Next up and backlog

### Next: animal walking and where they live (Ron, Oct 11 — build this)
- **They clump.** Likely causes: when you stand still, every animal within 260 m walks to a ring around you (`lureTarget`); after a shot they all flee the same way to similar spots (`fleeFar`); wandering homes drift into the same open patches.
  - Fix: each herd keeps its own home area and spacing from other groups; only the nearest few drift toward you, slowly; fleeing spreads out in different directions; real walking pace with pauses.
- **Habitat map** built at generate, so you can scan with binoculars and read the land ("that meadow by the lake should have horses"):
  - Open grass: zebra, horse, giraffe, elephant, rhino, caribou, musk ox, lions near the herds.
  - Forest edge: buck, elk, turkey, fox, coyote, boar.
  - Deep forest: bear, panther, monkeys, moose.
  - Water edge: crocodile, seal, polar bear; moose and elephants come to drink.
  - High rocks: mountain goats, eagles circling above.
  - Snow: arctic fox, snowy owl.
- **Falling:** tip sideways; when it hits the ground the legs go limp and the head drops — no stiff legs sticking up.
- **Bigfoot and Yeti:** only on XL and XXL maps, still rare. Mysterious: sometimes follow you at 100–250 m, freeze when you look, slip behind trees, vanish if you walk toward them, never come close.
- Open questions asked: how often legends show up (most XL/XXL maps or ~1 in 3); whether animals get a daily routine (drink in the morning, rest in cover at midday).

### Offered, not asked for yet
- Hit boxes on players: legs below ~0.3 m above the feet can't be hit; the body capsule sits under the head instead of the drawn body; arms can't be hit.
- Voice at the same volume regardless of distance; player list; gamer tags saved without logging in.

### Older backlog
- **Birdwatching in Hiking:** more birds with their own songs, photos through the binoculars, a saved field log. ("Hiking needs things to look at.")
- Never see inside your own body; a proper flying pose while gliding.
- Hiking trails, lookouts, a journal you fill by watching.
- Scope/binoculars feel "a little weird" and climbing is "close to correct" — he'll give details.
- PC and phone PvP redone separately later (no cross-play).
