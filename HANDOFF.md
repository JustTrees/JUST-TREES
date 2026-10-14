# Just Trees: handoff for the next chat

Read this first: who Ron is, how we work, what the game is now, how to build and test, what's next. Section 8 is a short changelog; full detail is in the git log (`git log`, one commit per version).

---

## 1. Ron and how to talk to him

- Ron is **not a programmer**. He's a designer with a strong feel for games, especially **VR**; his reference for how VR should feel is **Population: One**. He describes things by feel: turn that into code and say back in plain words what you did.
- **Short, simple replies.** No jargon or code ("too much mumbo"). Short lists are fine. On websites, one click at a time.
- He sends ideas in bursts with typos and voice-to-text: read generously. Ask at most one short question, and only if it changes what you build.
- Be honest: everything is tested in a simulated browser, never in a real headset; say what costs frame rate and what isn't free.
- **Vision (Oct 13):** a map-making battle/hunting game — a brand-new map every game, balanced, endless variety. He doesn't care about progression or leaderboards. **Stay on the web** (free, one HTML file, Claude can build it). Priorities: map variety and quality, fair maps, smooth frame rate, reliable online play.
- **Art direction (Oct 13+):** use free artist-made models (Quaternius, CC0) instead of code-built shapes; anything made from scratch should match that faceted low-poly, flat-colour style.

---

## 2. How we work

- **Each request: build, test, push live, send a backup file** `just-trees-2-xx.html` (+ pictures when something looks different), reply briefly. **Next version: 2.16.**
- **"Answer first" / "respond first" / a plain question** → only answer (or write notes here). No build.
- **Notes in this file go up with the next build.** A stop hook asks to commit lone note changes: decline until the next build (Ron's rule).
- **Testing (Ron, Oct 13):** each build = `check_code` + the 1–2 tests for what changed. Full suite only before big risky changes or when Ron asks (say so). Last full run: **2.06** (cleanup). `--only` takes full test names (`--only test_dino,test_online`).
- **Keep PC and phone unchanged** unless told. Most work is **VR only**.
- **Never upload the debug build:** `index.html` must not contain `window.D=`, `window.FREEZE`, `window.__trees`, `tilesX`, `cullTilesX`, `kindsX`, `window.__ah` (`dev/check_code.py` checks some; check the rest before copying).
- **Never put secrets** (TURN keys etc.) in the repo, the game or chat.
- **Commits:** author `JustTrees <ron@mountainstylemusic.org>`; end with the `Co-Authored-By` / `Claude-Session` lines the session gives. Only commit with Ron's go (a build he asked for counts).
- **Assets stay (Ron, Oct 14):** never delete model/sound packs from the repo, used or not — the unused ones are for future upgrades (list in section 3).

---

## 3. Where things are

- **Repo:** `github.com/JustTrees/JUST-TREES`, branch `main` (push prints "repository moved": fine). **Live:** https://justtrees.github.io/JUST-TREES/ (1–2 min after a push; the menu shows the version). Also served by the Cloudflare Worker https://just-trees-online.ron-bb2.workers.dev (builds from main on every push).
- **`index.html`** (~1.6 MB, one file): Three.js r149 and PeerJS 1.5.4 inlined at the top, then the game script. The script starts with a **table of contents** (search words per part) and a **tuning block** after `VERSION` (guns `WEAP`, `TIER` stars, `NADE`, `LOOT`, `PICK`, PvP timings, zone/capture). About 1.2 MB of it is built-in textures and sounds: they stay inline on purpose so a backup file opened from disk still works.
- **Loaded on demand** (over http only; a copy opened from disk falls back to the old hand-built versions):
  - `models/guns/<kind>_<tier>.glb` — 20 pack guns (1.89). `models/bows/bow_<2-5>.json` — pack bows (2.04).
  - `models/dinos/*.bin` — 6 pack dinosaurs + the from-scratch pterosaur (QDN1 format). `models/animals/*.bin` — every hunting animal (2.03).
  - `sounds/trex/`, `sounds/dino/`, `sounds/beast/` — dinosaur recordings.
- **`models/source/`** — the original packs Ron uploaded (see its README for licences). **Keep them all.** Used so far: Ultimate Gun Pack (guns), Dinosaur Animated Pack (dinos), Farm Animals (all animals), Medieval Weapons Pack (bows), the CC0 sound files. **Saved for later, unused:** Stylized Nature MegaKit (trees/rocks/plants), Medieval Village MegaKit (house pieces), Farm Buildings, Fish Pack (fish, dolphin, manta, shark, whale), Monster Pack (bat, dragon, skeleton, slime), the rest of the Medieval Weapons Pack (swords, axes, shields), the pack arrow. Not kept in the repo (licence: no redistribution): QAL packs, the Ririsaurus Dinosaurs/Beasts sound packs (only processed sounds are in `sounds/`).
- **`dev/`** — tools and tests (section 5), plus the model pipelines: `dev/guns/build_guns.py`, `dev/dinos/exp.*` + `make_ptero.py`, `dev/animals/` (dump, `animal_lib.py`, `build_animals.py`, `build_rigged.py`, `view.py`), `dev/bows/make_bows.py`.
- **Cloudflare:** `cf/worker.js` serves the site and answers `/turn` with a 6-hour Cloudflare TURN pass for justtrees.github.io / the workers.dev address / localhost. Secrets `TURN_KEY_ID`, `TURN_KEY_TOKEN` are Runtime secrets set by Ron in the dashboard. `.assetsignore` keeps dev/, cf/, models/source, HANDOFF.md off the site. The connector here can read Workers but not deploy or set secrets; code goes live by pushing to GitHub.

---

## 4. The game now (v2.19)

### Modes
- **Hiking** (no guns, no fog; **in a headset, solo or online, the map is Island = the 3 km XXXL island, or Endless** — 2.19, `set.hikeMap`, `HIKEMAP`; PC/phone hiking keeps the normal sizes), **Hunting** (animals; VR has loot guns, bow, grenades; Prehistoric switch = dinosaurs), **PvP** (VR online; PC/phone have the old bots version, on hold). **Online works in every mode** (2.00).

### World
- **Settings:** latitude (climate), roughness, time of day, month (season), tree density, map size (XS 250 m, S 400, M 560, L 800, XL 1.2 km, XXL 1.6 km, XXXL 3 km — XXXL not on phones), edges (Island / Endless), landscape (Natural / Dramatic), weather.
- **Environments by latitude:** `climateOf(lat)` bands (tropical <23°, temperate <50, boreal <62, tundra <72, polar); `envOptions(lat)` lists what occurs there with weights; `rollEnv()` picks one per map from the seed (`MAPENV`); `biomeOf(lat)` returns it. Environments: rainforest, palm jungle, tropical, desert, badlands (red rock country), swamp, temperate forest, birch-maple, redwood (redwoods, sequoias, eucalyptus), boreal, tundra, polar, plus the equator **archipelago** (Island + 0°, `ARCHI`, ~40% roll). `TROPIC(b)`, `DRY(b)`, `TB(b)` (temperate/boreal tables for look-alike biomes). **A new environment must be added to every per-biome table** (`GRASS`, `WATERC`, `SKYTOP`, water fraction, snow/tree lines, `dens`, rock tone/moss, logs, bushes, clouds, haze, weather, flocks, `NATIVE`) and to `envOptions` — or use `TB`.
- **Terrain:** heightfield with erosion; `H(x,z)` is the surface. Dramatic maps get one landmark (`makeFeature`: canyons, rifts, cliffs, mesas, buttes, craters, volcanoes…; on XXXL `BIG` landforms ~half the map and mountain ranges). Volcano craters can hold lava (`LAVA`, `inLava`; stepping in = respawn).
- **Trees:** trunk + branch cards in Pop: One style; fluffy forked crowns for some broadleafs (`FLUFFY`, patchy by `fluffPatch`), old pines, aspens, birches, maples, redwoods, sequoias, eucalyptus, cactus, Joshua trees, junipers, palms, cypress. Three distances with fades (`FADE_D`: detail → simple 3D → flat cards facing you; `NEAR` batches, `CARD` sheet baked per map). **The giant tree** (one per map, `PORCH`): a porch ~⅔ up with the only red 5★ sniper.
- **Endless (2.19, VR hiking):** land built in 200 m squares (`EN_C`) round you, a little each frame (`endlessTick`, ~3 ms budget in a headset, less if the frame rate drops; 11 ms on menus), squares past ~1.4 km let go (`enUnload`). Everything in a square comes from the seed + its position (`enHash` of its wrapped index), so a spot is always the same, for everyone online too; **the world repeats every 25 km** (`EN_P`; `makePNoise` = noise that repeats; tree/colour patterns read at `enWrap(x)`). Pieces: `enWorld` (the island's `buildHeight` made periodic + swamp/desert/badlands touches; **no droplet erosion yet**), `enHeightsGen` (4 m grid + 8-cell border, summit weathering, borders shared with neighbours so seams are exact), `ENDLESS.make` (inside `generate`, so it uses the same `treeAt`, `pickVar`, `groundCol`, rock/log/bush rules as the island maps, scaled per square by `AREA`), near batches that grow (`enSlot`/`enNearTick`, 100 m cells), cards per square, tree shadows in a 3.2 km wrap-round picture stamped per square once all 8 neighbours exist (`enShadowGen`), solid rocks only within ~430 m (`enSolidGen`, per-square 1 m grids; `rockTopAt` branch), water plane + shallows texture following you (`uShoreC`), a coarse far-ground sheet under everything so nothing is missing at the haze (`enFarJob`/`enFarSink`), the hand map as a 1.6 km window (`MAPV`, explored 25 m squares in `ENDLESS.seen`). Start: the squares within ~430 m are built in `generate` (2.5–4 s on a PC); the rest grows during the little-map screen; dropping in builds the squares round your spot behind the fade (`enEnsureHere`). Online: a friend's pose is shifted by whole loops (`EN_P`). No giant tree / porch, animals, or biome changes yet. Test: `dev/test_endless.py` (seams, walk keeps up, revisit + loop give the same land, drop-in).
- **Rocks/logs/bushes** on a 1 m grid (`rockGrid`, `rockTopAt`, overhangs `rockLow`). Look: ACES tone mapping, `grade()` colour shader, valley fog, sky/sun/moon/stars, lightning with delayed thunder; ambient sound synthesized.

### Animals (Hunting)
- **Kinds per biome** in `NATIVE` (42 kinds incl. Bigfoot/Yeti); spawn plan in `spawnAnimals`, built by `addGround` / `spawnKind`. Habitat liking (`PREF`, `habInit`, home ranges), whole-map stocking in ~200 m squares (`STOCK`, `stockTick`), `appearTick` brings groups in out of sight when you stand still, XXXL only within 1 km (`BUBBLE`). They notice you walking at 60 m, sprinting 150 m; a shot empties the area (`scatterBeasts`, `fleeFar`). Score = distance × `SCORE[kind]`; a hit is a kill.
- **Models (2.03):** every animal is still built by its old hand-built builder first (`buildQuad`+`QSPEC`, `buildBuck`, `buildBear`, `buildWolf`, `buildApe`, `buildBird`, `buildMonkey`, …) — **kept as hidden rigs, don't delete**. Then:
  - `QA_KINDS` (four-legged, from the farm pack): `qaPick` sets `A.qf` (file) and `A.qv` (coat: horse ×5, bear black, panther black in the tropics, wolf/rabbit pale/white in the cold, arctic fox grey out of the cold, crocodile = gator coat 1, half the lions `lion_m` with a mane); `qdAttach` fits the model to the old body's length and hides it; `qdTick` picks Idle / Eat (grazing) / Walk / Run / Death, leans with slopes, updates far ones less often (4 fps past 320 m unless scoped). Hit spheres fitted per bone (`qdSpheres`, `A.qhit`; Head bone = head shot).
  - `QR_KINDS` (birds, turkey, roadrunner, heron, seal, monkey, Bigfoot, Yeti; built from scratch): `qrAttach` skins the model onto the old animal's moving groups (bone names = slots: body, head, leg{i}, leg{i}k, arm{i}, arm{i}k, wing{i}), so the game's own flapping/striding/swinging drives it; old hit boxes stay. Birds share one shape with colour slots filled from `BIRD_COL`/`PARROT_COL` (`qdGeo`).
  - Rebuild: `python3 dev/animals/build_animals.py <dumps> models/animals` (dumps made by `dev/animals/dump.py` from the Farm Animals FBX) and `python3 dev/animals/build_rigged.py models/animals`; look with `dev/animals/view.py`.
- **Legends:** Bigfoot (Yeti in the cold), Large maps and up, hidden and unhittable until you hold the red sniper ("There's a Bigfoot in these woods"); notices you through max-zoom binoculars; one real shot, then he sprints off and is gone.
- Online guests get the host's animals (`an` messages, `mpNetBeast`); coats are rolled per player (colours can differ).

### Prehistoric (VR Hunting, `set.dino`)
- Herds of triceratops, parasaur, stego, bronto (`DINO_NATIVE`), sizes vary (`DINO_GROW`); health per kind (`DINO_HP`), damage per gun (`DINO_DMG`, `RAPTOR_DMG` × stars; head ×1.5); no health bar (Ron).
- **Raptor hunts** (`dinoTick`, `huntTick`): random times, warning cue, circles far and fast, feints, heals unless hit by the sniper, charges at ≤30%, inside 15 m it gets you (red blackout, respawn).
- **T. rex** (Large+: 1/2/3/4 by size; `rexTick`): revealed by the red sniper (scream across the map), roams and screams every 30–60 s; shot → chases in wide S-curves with screaming stops; 3500 HP; a climb over 6 m saves you.
- **Pterosaurs** (2.02, `PT`, `pteroTick`): circle 45–80 m up, pass under one (or shoot it) → screech and dive; reaching you = blackout.
- Models: Quaternius dinosaurs (`models/dinos`, `dev/dinos/exp.py`), from-scratch pterosaur (`make_ptero.py`). **Skins (2.16):** a scaly pattern over the plain colours (`dinoSkinOn`, `DINO_SKIN`: the 1.82 `dinoSkin` Voronoi scales, big for the large ones, small for the raptor; a leathery `leatherSkin` for the pterosaur), projected three ways in the model's own space (no UVs needed; rides with the bones), fades out 45–70 m away (`SKIN.fade`); T. rex a bit darker green (`DINO_RECOL`). 2.17: the hunting animals too (`ANIMAL_SKIN`, `SKIN.animal`): fine short fur in soft clumps (`furSkin`), wrinkled hide on elephant / rhino, scales on gator / crocodile, overlapping feathers (`featherSkin`) on the birds (all birds share `bird`), turkey, roadrunner, heron. Per-pattern strength `SKIN.amt`; an entry's 3rd number scales it (seal, tapir, panther lighter). It multiplies the coat, so near-black coats (black bear, Bigfoot) barely show it. Sounds: `DINO_SFX` / `DINO_RATE` (recordings pitched per animal, `name@rate`), 3D voices with forest reverb, one limiter; made-up fallbacks.

### VR
- PLAY IN VR → height check → intro → curved menu panels. Before each map: spin a mini-map, pick your start. Pause: Y.
- **Controls** (right-handed default): off-hand stick walks (click = sprint), gun-hand stick snap-turns 30° (zooms while scoped); tap A gun in/out, hold A wheel; tap B mark; off-hand trigger map; off-hand grip two-handed hold. Real crouching.
- **Climb anything** (trunks, limbs, rocks, cliffs; 2.15: you catch right at the surface — `climbableAt` tolerances trunk 1.2 cm, simple trunks 1.5 cm, limbs 1 cm, rocks 3.5 cm (was 15), steep ground 4 cm; a hand that's holding something can't catch: the gun hand, the front hand on the gun or reloading, the bow hand, the hand holding an arrow or a grenade, and a hand that just let go of the gun needs a fresh squeeze), fling, glide with arms out (`GLIDE_VR` 22 m/s). Under water: walk the bed, 5 s breath. Body: camo soldier with arm IK.
- **Guns:** sniper (bolt, the only scope; zoom steps by stars), assault rifle, SMG, pistol (pack models per star, hands wrapped round the grips). Real bullets, no drop, no scatter. **Recoil (2.08, auto guns only):** each shot climbs the muzzle (and the aim) by `RECOIL.up[level]` degrees — level 1 = 5★ (.25°) … 5 = 1★ (1°), 6 = held one-handed (2.5°); looking down the gun (`vr.ads`) 15% less; max 25°; settles back when you stop (`vr.climb`). Fire rate unchanged. **Sounds (2.09):** real recordings in `sounds/guns/` (Snake's packs: sniper .308, AR 7.62x39, SMG/pistol 9mm with outdoor echo; reload, bolt, charging handle, slide, empty click), `GSND` (per-gun volume/pitch, ±3% pitch per shot; 2.10: the sniper at .87 pitch with a +7 dB low shelf at 200 Hz and a 62→32 Hz sub thump (`thick`); 2.11: no compressor on gun sounds (Ron: it made them too soft) — plain gain bus at 1), `gunshot(kind, lead, dist)` (other players: quieter and delayed by distance), `gunFoleyK`; cut by `dev/guns/make_gun_sounds.py`; made-up sounds stay as the fallback (and on PC/phone). Ron will fine-tune pitch/files later. **Skins (2.16):** `gunSkinOn` — one 256px texture: brushed metal streaks along the barrel (red), wood grain (green), grip stipple (blue); each corner tagged metal / wood / plastic from its pack colour (`GUN_PART`, attribute `skinK`); metal glints in streaks, plastic and wood a bit duller. The material's `clone` re-adds the hook (a plain `material.clone()` drops `onBeforeCompile`). Strengths in `SKIN.gunAmt`; `SKIN.gun = false` turns it off. Reload by hand. **Unlimited ammo** (`INF_AMMO`). Binoculars: both empty hands at your face.
- **Loot (VR Hunting and PvP):** start with a 1★ pistol (Hunting also a 1★ bow); guns of 1–5★ glow on the map (`spawnPvpLoot`; a better one upgrades; ones you can't use aren't drawn). Hunting: ~16% of the loot spots are bows (2–5★). **Grenades:** floating red frag grenades, one each (2.05), up to 10; aim shows the arc. PvP: green crosses +30 health, blue +35 shield, back after 40 s.
- **Bow** (Hunting): off hand holds it, take an arrow from behind your shoulder, nock, draw, release; real arc; quiet shot. Five looks by stars (2.04: 1 = the game's own, then Wooden 2, Wooden, Golden, Evil); stars add damage against dinosaurs only.
- Hunting HUD: score and your mark on the VR map (off-hand trigger); frame-rate readout top-left of the map.

### Online (VR, peer to peer, up to 8)
- Main menu → Online → Host / Join (4-digit code) → gamer-tag keyboard → **lobby** (`mpLobbyPanels`): player grid (tag, team, camo uniform: brown/green/grey/white/black, last score), host picks mode, PvP Solo / 2 Teams / Random, Prehistoric, comms (Open, Open proximity, Team, Team fist bump), round length, map settings (mirrored live), Start. Round end → back to the lobby with the board.
- **PvP:** deathmatch — die and respawn with your guns (nothing is dropped); kills/deaths on the board; no friendly fire; teammates see each other's map marks. Optional closing zone and capture point. Voice connects on join (`mpHear` per comms setting; fist bump = both fists within 17 cm). **Positional sound (2.12):** other players' gunshots come from where they fired (`mpShotSound`, 4 reused HRTF voices; loudness 22/(22+d), duller (low-pass) and later (d/343 s) with distance, heard to `PSND.RANGE`: sniper 780 m, AK 600 (half an XL map), SMG 520, pistol 440; 2.14: past 40 m more and more of the shot goes into a long dark rolling echo (`farVerb`, 3.4 s, all around you) while the direct crack fades to 25% by ~500 m); their footsteps from their feet (`mpStepTick`, one HRTF voice per player, to 35 m: sprint loud, walk soft, crouch ×.25, landing thump, teammates ×.55 in team games; `footstep(kind, q, dest)`).
- **Hunting together:** host runs the animals and dinosaurs; guests' shots go to the host; raptor goes for the loneliest player; the T. rex for whoever shot it.
- Relay: `mpRelay()` asks the Worker's `/turn` first, falls back to the free Open Relay. Not yet tried by friends on strict home networks.

### PC and phone (keep as is)
- PC: WASD, mouse look, click fire, scroll zoom/binoculars, Shift run, Space jump, C crouch, Esc menu. Phone: joystick, drag to look, buttons. Minimap, full map, drone flyover before each map.

---

## 5. How to build and test

- **Edit with a Python patch script** in the scratchpad that replaces exact strings in a copy of `index.html`, **asserting each old string's count**; bump `VERSION` and `<title>`; build to the scratchpad, copy to `index.html` when tests pass.
- **Tools in `dev/`** (Playwright + Chromium/SwiftShader):
  - `check_code.py [file]`: parses, no duplicate function names, no debug hooks.
  - `make_debug.py index.html dbg.html`: debug copy with `window.FREEZE` (step frames by hand) and `window.D` (handles into the game; add more there when a test needs them).
  - `run_all.py <file> --nm /tmp/claude-0/-home-claude/93b90c2a-a1eb-59bd-91b2-a2c86d7f6262/scratchpad/nm/node_modules --jobs 5 [--only test_a,test_b]`: code check + tests. The full run takes ~25 min: run it in the background (`nohup … &`) and read the log. Online tests (test_mp, test_mp_fail, test_lobby, test_online) need that node_modules path (local PeerJS server).
  - Tests that load models serve the page over http (test_qdino, test_qanimals, test_bowtiers, test_rexsound); the rest open it from disk (old hand-built models).
  - Flaky under heavy parallel load, pass alone: test_dino (random raptor moods), test_habitat, test_spread, test_trex, test_bow. The model-loading tests (test_qdino, test_qanimals, test_bowtiers) and the big-map ones (test_landscape, test_solid_ground, test_cards) time out with `--jobs 5`: rerun them with `--jobs 1`–`2`.
- **Push:** `git add`, commit, `git push origin main`; then send the backup file.

### Gotchas (don't relearn these)
- Renderer outputs linear colour: **don't mark canvas textures as sRGB** or menus go dark. Hex colours in the model builders are sRGB → linear × `LIFT` (2.3).
- **Inside a VR session `requestAnimationFrame` doesn't run** — everything goes through `renderer.setAnimationLoop(loop)`.
- VR movement: `vr.readInputs()` gives world-space poses; walking moves the play space (`vr.ox/oy/oz/yaw`); `vr.placeAt` re-anchors on a new map. `VR_ON` must be set before `generate()`.
- `obstacles` is replaced by every `generate()`: use a getter in debug hooks.
- Two functions with the same name: the later silently wins (`check_code.py` catches it). A `//` comment in a one-line statement swallows the rest of the line — use `/* */` there.
- `vr.cl` is always an object in VR: test `vr.cl && vr.cl.hold` for "holding on".
- Call `updateMatrixWorld` before raycasts if things moved this frame.
- Quaternius farm rig: the feet are IK targets under the root, not children of the legs (`animal_lib` snaps them to the leg ends).
- A material's `onBeforeCompile` text isn't part of three's program cache key: anything that differs between materials sharing a hook must be a uniform, not baked into the shader text (`customProgramCacheKey` when the code differs).
- Island maps must stay identical when generation code is shared: compare a content fingerprint (trees, rocks, heights) old vs new with seeded `Math.random`, not pixels (rendering varies run to run).
- In the shell, `pkill -f` / `pgrep -f` can match the running shell and kill it; avoid them. Use the Bash timeout (up to 10 min) or nohup for long runs.

---

## 6. His standing preferences (don't undo these)

- **No resource gathering or building.** Fights are about aim, movement and terrain.
- No camera bob; slow soft footsteps; quiet wind/trees/rain. No light shafts. No tree sway.
- Rounded peaks, no spikes or monoliths. Long views (cut far detail before view distance). Hiking has no fog.
- Native animals only; hit = kill with a bing, no blood; score per metre; animals react to your movement, not sound. Dinosaurs: no health bar; scary is good.
- VR: no jump/crouch buttons; off hand never steers the aim; snap turn 30°; heavy gun smoothing; two-handed scoping; binoculars at your face; glide with arms out; Pop: One climbing (high gravity, medium fling); unlimited ammo; recoil only on the auto guns (2.08).
- Avatars: soldiers in baggy camo with hoods; masks are achievements only. Online: no gamer tags over heads, no armbands (talk to know who's who), no avatars in the lobby (a list).
- Battle royale is shelved.

---

## 7. Next up and backlog

- **Endless next (Ron's plan):** animals in hiking (the hunting system, no guns), then biome changes as you travel (blend every per-biome table over a few hundred metres; latitude drifting as you walk north/south), landmarks every few km (canyons, volcanoes, mesas, a giant tree), real droplet erosion per square (overlapping windows blended), then group-hiking polish. Check frame rate on the Quest while gliding (`endlessTick` budget).
- **Animal sounds (Ron, later, from his computer):** he'll upload a few packs; sort them by name + length/pitch/loudness/spectrogram, send a preview per animal, check licences. Sources found: NPS Yellowstone and Rocky Mountain sound libraries (public domain: elk bugle/bark/mew, wolves, grizzly, mountain lion, coyotes, red fox, bison, bald eagle, wild turkey, grouse, crane, loon, ~60 songbirds), Mixkit animals (free licence: lion, elephant, monkey, parrot), Sonniss GDC bundle (7.5 GB, royalty free). Plan: animals call on their own (elk bugles, night wolf howls, gobbles, coyote yips) and when shot.
- **Offered:** restyle the PvP health/shield crosses as small floating pickups (first-aid kit, shield) to match the grenades and guns; the pack's wooden arrow instead of the carbon one.
- **Model packs waiting:** nature kit (trees/rocks), village kit, farm buildings, fish pack (water animals), monster pack, medieval melee weapons.
- **Places not built yet:** African savanna (golden grass, acacias), volcanic island, Mediterranean hills, bamboo forest, alpine meadows; above 45° more variety (prairie, coastal rainforest, alpine, volcanic Iceland, moors, fjords, pack ice); northern lights, hot springs/geysers, rivers and waterfalls, caves (hardest).
- **Prehistoric ideas not built:** more dinosaurs per environment (Spinosaurus, Ankylosaurus, Brachiosaurus…), an Ice Age set for cold maps, prehistoric plants.
- **Graphics:** the ground mesh is the biggest cost on XXL/XXXL — chunk it with distance detail; maybe VR view back to 1.5 km if frame rate holds.
- **Online:** fetch `/turn` before PeerJS connects; share birds/monkeys/hiking animals; test with friends on strict networks.
- Smaller ideas: Bigfoot following you at a distance; a daily routine for animals; birdwatching in Hiking (songs, photos, a field log); hiking trails and lookouts; arrows that stick; a proper flying pose while gliding; never seeing inside your own body; player hit boxes (legs/arms); PC/phone PvP redone separately (no cross-play).
- Ron said scope/binoculars feel "a little weird" and climbing is "close to correct" — he'll give details.

---

## 8. Changelog (short; details in `git log`)

- **2.19** Endless hiking (VR solo and group): hiking in a headset is Island (3 km) or Endless — land built around you as you walk, repeating every 25 km.
- **2.18** a new gator (and crocodile): built from scratch on the pig's bones in `build_animals.py` — one smooth flat body-to-tail skin blended along the spine bones (no cracks), sprawling upper legs, back plates and a tail crest, a big broad head and snout with raised eyes, nostrils and teeth, a pale jaw.
- **2.17** textured skins on the hunting animals: fur, wrinkled hide (elephant, rhino), scales (gator, crocodile), feathers (birds).
- **2.16** textured skins: scales on the dinosaurs (T. rex a little darker green, leathery pterosaur), brushed metal / wood grain / grip stipple on the guns. No new triangles; dino pattern fades out past ~60 m.
- **2.15** grabs happen right at the surface of trunks and rocks (rocks used to catch 15 cm early); hands holding a gun, bow, arrow or grenade never catch hold.
- **2.14** far gunshots turn into a rolling echo with distance (a dull pop, then thunder off the hills).
- **2.13** menu wording (Ron): "Solo hiking" / "Solo hunting" on the VR main menu, no "each map picks" after the latitude environments, online panel says "the host picks the map settings". Menu pictures: render every VR panel by opening it with `D.vruiOpen(stage)` and saving `VRUI.panels[stage].g.canvas` (scratch script).
- **2.12** other players' gunshots and footsteps are 3D positional; shots carry far (AK ~600 m). Test `dev/test_psound.py`.
- **2.11** gun compressor removed (too soft); full volume again.
- **2.10** sniper deeper and thicker; gun sounds compressed and a bit quieter in the mix.
- **2.09** real recorded gun sounds (Snake's Authentic Gun Sounds 1 + 2) for every VR gun, shots and reloads. Test `dev/test_gunsounds.py`.
- **2.08** recoil on the assault rifle and SMG: by stars, much more one-handed, 15% less looking down the gun. Test `dev/test_recoil.py`.
- **2.07** animal hips (Ron: elephants and bears "look crazy"): when `legs()` lengthens legs, the haunch above the hip joint now rides with the body instead of stretching up over the back; elephant back legs a bit shorter so its back is level. All animal models rebuilt.
- **2.06** cleanup: dead code out (ammo cans, death-drop of gear, lobby avatars, unused helpers), old models labelled as kept rigs, these notes rewritten. No gameplay change.
- **2.05** grenades float on the map like the guns, one each, red frag style.
- **2.04** five bows by star, looted like the guns.
- **2.03** every hunting animal redone in the Quaternius farm-animal style (pack-reshaped + from-scratch rigged ones).
- **2.02** pterosaurs on the dinosaur maps.
- **2.01** softer plant-eater steps + limiter, roaming T. rex screams, T. rexes by map size, XXXL dramatic mountain ranges.
- **2.00** online in every mode: lobby, gamer tags, camo uniforms, teams, comms + fist bump, deathmatch, shared hunts.
- **1.99** Beasts sounds for every dinosaur. **1.98** T. rex screams on the way, S-curve chase. **1.97** loot glow fits the pack guns; owned guns hidden. **1.96** recorded dinosaur calls. **1.95** guns 15% bigger. **1.94** recorded T. rex calls. **1.93** T. rex scream and footsteps. **1.92** raptor bites again, slope lean, dinosaur sizes. **1.91** Quaternius dinosaurs. **1.90** hands wrap the guns. **1.89** Quaternius guns per star.
- **1.88** three tree distances with fades. **1.87** XXXL animals within 1 km. **1.86** far less drawing (near batches, tree cards). **1.85** bow + unlimited ammo. **1.84** 3 km map. **1.83** Cloudflare relay. **1.82** dinosaur redesign. **1.81** no stall when shooting. **1.80** T. rex. **1.79** dinosaurs never stuck; faster VR glide. **1.78** frame-drop fixes, no health bar. **1.77/1.76** raptor fight, 3D dinosaur sound. **1.75** Prehistoric mode.
- **1.74** redwood forest. **1.73** birch-maple forest. **1.72** fuller fluffy trees, aspens. **1.71** fluffy trees, old pines. **1.70** archipelago. **1.69** swamp. **1.68/1.67** badlands / red rock. **1.66** rainforest. **1.65** HUD on the VR map, Bigfoot notices you. **1.64** environments by latitude, desert. **1.63** animals everywhere, lava. **1.62** Bigfoot rules. **1.60–1.61** the giant tree, trunks.
