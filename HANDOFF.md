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

- **Each prompt: build, test, push live, send a backup file** (`just-trees-1-xx.html`), reply briefly. Next version is **1.68**.
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

## 4. What exists now (v1.67)

### World (all modes)
- **Settings:** latitude (sets the climate; each map then picks one of the environments that occur there, see below), terrain roughness, time of day, month (season), tree density, map size (XS 250 m → S 400, M 560, L 800, XL 1.2 km, XXL 1.6 km), edges (Island or Endless), landscape (Natural or Dramatic), weather (clear, rain, fog, snow/blizzard, storm; Hiking never gets fog).
- **Environments by latitude (1.64, Ron: "when certain latitudes have varied environments those are all options the map may or may not choose"):** `climateOf(lat)` = the old latitude bands (tropical <23°, temperate <50, boreal <62, tundra <72, polar). `envOptions(lat)` lists what really occurs there with weights: under 10° rainforest .65 / palm jungle .35; 10–15° palm jungle .65 / rainforest .35; 15–23° tropical .55 / desert .45; 23–30° desert .5 / climate .5; 30–35° desert .4 / badlands .2 / climate .4; 35–45° climate .65 / badlands .2 / desert .15 (cold desert); else just the climate. `rollEnv()` picks one per map from the map number (`MAPENV`), so a map always comes back the same; `biomeOf(lat)` returns this map's pick. `set.env` = "auto" (default, the roll), "climate" (old behaviour; the debug build defaults to this so old tests stay stable), or a name to force one. The settings line under latitude shows the options ("Desert or forest: each map picks"). **Every new environment must be added to every per-biome table** (`GRASS`, `WATERC`, `SKYTOP`, water fraction ×3, snow/tree lines, `dens`, rock tone/moss, logs, bushes, clouds, haze, weather, flocks, `NATIVE`) and to `envOptions`.
- **Desert (1.64):** warm sand ground (two tones), red rock on slopes (`rockC`) and reddish rocks (`tone`), extra outcrops, dunes on low flat ground (added to the baked heightfield after erosion: long gentle slopes, steep lee faces, ~60 m apart, 2.5–6 m high), little water (5% fraction), mostly clear weather (6% storm, 6% rain), warm haze. Plants: `cactusVariant` (saguaro: ribbed column, 0–4 arms that turn up; small ones have no arms) and `joshuaVariant` (shaggy trunk that forks, spiky tufts at the tips), scrub bushes (`kinds.scrub`). The giant tree in a desert is an old cottonwood (broadleaf). Animals: coyote, oryx, camel (`hump2` in `buildQuad`: a hump mid-back), roadrunner (`buildRoadrunner`), jackrabbit, vultures (`FLY`), birds, Bigfoot on large maps ("There's a Bigfoot out here"). Test: dev/test_desert.py (+ zoo and hitbox include the desert).
- **Rainforest (1.66):** biome "rainforest" (`TROPIC(b)` = tropical or rainforest, for the things they share). Broadleaf variants get `{ tall: 1.55, vines, buttress }`: ~1.5× taller, thicker trunks with big buttress roots, a tall bare trunk then a wide flat umbrella crown (`umb`), 3–7 lianas hanging from the limbs (thin tubes, not in the far-tree version). Some palms, the odd emergent giant (×1.55). Closed canopy (density noise flattened), dark leaf-litter floor, thick undergrowth (6500×area bushes, 1.3–2.7 m; costs ~15% more triangles than a temperate map, fewer draw calls), mossy rocks, many mossy logs, mostly rain/storm/fog weather. Animals: black jaguar (panther), tapir, capybara (new `QSPEC`s), monkeys, parrots, caiman (crocodile), peccary (boar), birds, Bigfoot on large maps. Waterfalls come later with rivers. Test: dev/test_rainforest.py (+ zoo, hitbox).
- **Badlands (1.67, Ron picked it):** after erosion the heights get 3.3× the relief, the very tops are squashed into flat mesa caps (no spikes), then most of the map is terraced into flat benches with sheer risers (step 8–14 m, `smooth(.8, .97)`), mixed with untouched ground by a noise mask. Cliff faces are painted in horizontal rock bands (`BANDS`, 7 colours by height + noise; rock texture turned down there). Warm tan ground, red rock, extra outcrops, scattered squat junipers/pinyon (small broadleaf with `JUNIPER` colours), sage scrub, little water, snow line high (winter can still snow). `DRY(b)` = desert or badlands (scrub, "out here" Bigfoot line). Animals: bighorn sheep (curled horns, high ground like goats), pronghorn (fast), mule deer, mustangs, coyotes, jackrabbits, eagles, vultures, Bigfoot on large maps. Test: dev/test_badlands.py (+ zoo, hitbox).
- **Terrain:** heightfield with erosion and rounded summits. `H(x,z)` is the exact surface. Dramatic maps get one landmark from a generator (`makeFeature`: crevasses, canyons, rifts, walls, cliffs, mesas, buttes, terraces, craters, sinkholes, volcanoes in many shapes).
- **Trees:** trunk + branch cards, Pop: One style; big limbs you can stand on and hold; lighter far-away trees past ~270 m.
- **Trunks (1.61):** `trunkNice` — flared base with root buttresses that run into the ground (lobes), 8 sides, same taper; every trunk has a gentle natural bend (`bend(y)` applied to the whole variant, firs straighter than broadleaf). Climbing/head-blocking follow the bend and flare (`treeHit` uses `hold.bend`, `hold.fl`). Far trees keep the 4-sided trunk. (Also fixed: animals were updated twice a frame — they moved at double speed.)
- **The tallest tree (1.60–1.61):** one per map, not on any map — you find it. Built like the Dramatic landmarks: random features from a seeded roll (`GR`): huge buttressed root base (always), leaning (55%), gnarled bends (40%), a twin crown split above the porch (45%, only when there's room), bark: plain / redwood / silverbark / blackbark (trunk tint), thicker trunk. It gets a name ("Leaning gnarled redwood giant"), shown the first time you step on the porch (wrist in VR, hint on PC). Size: porch at the tallest real treetop + 2.5 m, the giant ≈ 1.65× that, so the porch is ~2/3 up with a real crown above. **Branches (1.62):** normal below the porch, none from the deck up 3 m (`clearAt` = `[porch − 0.3 m, porch + 3 m]`; any branch card overlapping that band is dropped), normal above. Its own one-off variant (`treeVariant(…, {giant, clearAt, thick, noLean})`, `giant.ry = 0`). **Porch:** doughnut wooden deck (planks, rim board, joists, braces to the trunk, no railing), centred on the trunk at that height (follows the lean), no branches from the deck to 3 m above it (clear 360° view), solid via the rock grid (stand on it, walk/climb under it, animals walk under it), open middle to climb through. `PORCH` = {x, z, top, rIn, rOut, name, tree}. The **only red (5★) sniper** lies on the deck (`gRed`); ground loot never has a red sniper. Test: dev/test_porch.py (5 seeds; give a folder for pictures).
- **Lava (1.63):** a volcano (Dramatic maps) with a crater holds a glowing lava pool (`LAVA`, `findLava` / `buildLava`). Level = 60% of the way from the crater floor to where it would spill (priority flood from the lowest crater point; `LAVA.mask` = the basin it fills, 3 m cells). After erosion the volcano's rim is mended (notches filled) so the crater holds. Round/oval/lobed volcanoes get lava; crescent and twin/triple ones have no crater, so none. Dark basalt crater walls. No trees, rocks, logs, bushes, loot, spawns or animals in it (`inLava(x, z, pad)`; `okSpot` and `targetOk` refuse it). Stepping in: VR = red fade + respawn like drowning (`UW.red`; PvP "Burned: lost your gear and a kill"); PC/phone = red flash + respawn (`pcLavaTick`). A hiss (`lavaHiss`). Volcanoes are rare (about 1 in 15 Dramatic maps). Test: dev/test_lava.py.
- **Rocks:** boulders, slabs, cliffs, outcrops, logs, bushes on a 1 m height grid (`rockGrid`, `rockTopAt`, `rockAround`). Overhangs work: you can stand under a rock with a gap below it (`rockLow`).
- **Look and sound:** ACES tone mapping, `grade()` colour shader, valley fog, sky with sun/moon/stars, lightning storms with distance-delayed thunder. All sound is synthesized.

### Animals (Hunting)
- **40 kinds** (1.64 added oryx, camel, roadrunner, vulture; 1.66 tapir, capybara; 1.67 bighorn, pronghorn), native per biome (`NATIVE`): buck, bear, polar bear, baboon, panther, wolf, seal, rabbit, monkeys, big birds, plus (1.55) elephant, giraffe, zebra, rhino, lion, crocodile, parrots, mountain goat, wild horse, elk, moose, boar, coyote, fox, turkey, eagle, caribou, musk ox, arctic fox, snowy owl, and the legends Bigfoot and Yeti.
- Built from code (legs have rounded haunches and knees, 1.56): `buildQuad(r, QSPEC[kind])` makes most four-legged animals from a spec; separate builders for buck, bear, wolf (also coyote/fox/arctic fox), turkey, Bigfoot/Yeti (`buildApe`), birds (`buildBird` with colours), monkeys.
- **Where they live (1.58, Ron: "a natural world with some tweaks"):** `habInit` builds a 24 m habitat grid at spawn (open, forest edge, deep forest, water's edge, high ground). `PREF[kind]` = what each kind likes; each also gets 2 home ranges per map, so different parts of a map hold different animals (explore to find them). `likeN` = liking compared with the best spot on this map. It's a liking, not a wall: bears, wolves, rabbits etc. roam everywhere, and anything can run anywhere.
- **Animals everywhere (1.63):** the map is cut into ~200 m squares (`STOCK`, `secOf`, 2×2 on XS up to 8×8 on XXL); new groups go to the emptiest squares first (`spawnKind(…, onlySec)`), and `stockTick` (every 4–7 s) refills a square with no huntable animals, far (>200 m) and out of sight (and never takes animals within 420 m of you, so it doesn't undo `appearTick`; checked 1.65: no back-and-forth, and the animal update costs the same as 1.62, ~1.3 ms/frame for 170 animals): shot kinds come back first (old unseen bodies are cleared to make room), otherwise a group walks over from the most crowded square. Rabbits, birds, monkeys, seals, crocodiles and legends aren't counted. Shots still empty the area (they run 140–340 m off). **VR walking (8.5 m/s) now counts as walking** (animals notice you at 60 m); only sprinting is 150 m (before, every VR walk counted as a sprint, which is likely why animals felt hard to find). Test: dev/test_spread.py.
- **Movement:** no slope limit (they climb anything; only big boulders/cliff rocks turn them), so they don't get stuck or bunch up. Groups spawn ≥55 m apart. Wander targets favour liked ground. A shot: each herd/loner flees on its own line (`HAB.flee`), not all the same way. Stuck animals squeeze free (`unstick`).
- **No gathering round you.** Standing still, `appearTick` every ~10–35 s moves a far, out-of-sight group to liked ground 90–380 m around you (never in view, not in a ring, never on top of another group); stops when plenty are already near. Moving around, nothing new turns up.
- **Falling (`deadPose`):** topples sideways (speeding up), then the legs and head go limp on the ground.
- **Legends (1.62):** Bigfoot (Yeti on tundra/polar) on **every Large, XL and XXL map, one each; never on Small/Medium** (`bigMap` in the spawn plan; tropical gets a Bigfoot too). **Hidden and unhittable until you hold the red sniper** (`legendSeen()`; on PC with no loot: once you've found the porch). Picking up the red sniper puts **"There's a Bigfoot in these woods"** (or Yeti) in front of you for 6 s (`vrBanner` / `bannerTick`, `VBAN`); on PC it's added to the porch-found hint.
- Scoring: a hit is a kill (tip over, bing, no blood); points = distance × `SCORE[kind]` (big easy animals low, small/flying high, legends 5).
- **Hit boxes (1.59):** `neckHits` adds spheres from the chest up the neck to the head, plus spheres fitted along each head's real shape (antlers/horns/ears left out). Test: dev/test_hitbox.py (rays across every head and neck; all kinds 88–100%).
- **Bigfoot notices you (1.65, Ron):** VR binoculars at the strongest zoom (`VR_BINO_FOV` last step), aimed within ~2° of him, clear line of sight (`castShot`), up to 3.1 km: he stops, turns to face you and looks up (`legendNotice`, 1.4 s), then walks off a bit faster (`fleeFrom` at 2× walk, not a run; he isn't spooked away). 20 s before he'll do it again (`noticeCool`). Weaker zoom: nothing. Ron: Bigfoot showed up about 1 in 5 tests and that's fine, "better as an easter egg".
- **One shot at a legend (1.62):** only a bullet that really passes or lands within 15 m of him counts (`legendShot(o, dir, reach, speed)`, called from `vrFire` and PC `fire`; `castShot` so trees/terrain stop it). Other shots, or shots before you have the red sniper, do nothing. He waits for the bullet (`boltIn`; a hit lands first and counts), then sprints off like a runner, arms pumping (`legendBolt`), **can't be hit while running** (`animalRay` skips `A.bolting`), and vanishes for the map (`A.gone`). Test: dev/test_legend.py (picks a clear line of fire, since trees rightly stop the bullet).

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
- **Zoom steps (VR; PC unchanged):** binoculars 7.5×, 12×, 18×, 28× (`VR_BINO_FOV`). Sniper steps go by its stars (1.60): 1★ = 1 step … 5★ = 5 steps: 4.6×, 9×, 17×, 28×, 42× (`VR_SCOPE_FOV`). Scoped shots count to 3.2 km, camera far 3.2 km, animals drawn ~3.1 km while zoomed, fog stretches up to 4.5×.
- **Hunting HUD (1.65, Ron: the wrist was unreadable):** in Hunting the wrist is hidden; the **score** (score, kills, longest) sits on the map (off-hand trigger), and your **mark** (tap B) shows there as a gold pin. The VR map has its own sharp 512 px canvas (`vrMapCv`, id "vrMap"; drawn whenever the PC mini-map is); the PC mini-map is unchanged. Pickup messages and the porch name float in front of you (`vrBanner` with a priority: a pickup never covers the Bigfoot line). The wrist still shows in Hiking and PvP.
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

### Plan (Ron, Oct 11): one step per version
Ron: "each time just lmk how it goes in tests and send pics each time and I'll just tell you to keep going." So after each build: push, then a short test report + pictures, and wait for "keep going".
- 1.63 animals everywhere + lava in volcano craters (only in the crater, no flows) — done
- 1.64 **Desert** — done (heat shimmer is a warm haze, not a wobble)
- 1.66 **Rainforest** — done (Ron chose it before the savanna; waterfalls wait for rivers)
- 1.67 **Badlands** — done
- next **African savanna:** golden grass, flat-topped acacias, big open views; elephants, giraffes, zebras, lions
- **Swamp:** cypress in still water, mist, alligators, herons
- **Volcanic island:** black sand, palms, lava fields
- Offered Oct 12, not chosen yet: Mediterranean hills, bamboo mountain forest (pandas), alpine meadows
- Then: northern lights (easy), hot springs and geysers, rivers and waterfalls, caves (hardest: the ground is a heightfield, no holes)

### Next ideas (not built)
- Bigfoot/Yeti mysterious behaviour (maybe): sometimes follow you at 100–250 m, freeze when you look, slip behind trees, never come close.
- The giant's twin crown is subtle; could be bulked up.
- Maybe a daily routine for animals (drink in the morning, rest in cover at midday) — asked, no answer yet.

### Offered, not asked for yet
- Hit boxes on players: legs below ~0.3 m above the feet can't be hit; the body capsule sits under the head instead of the drawn body; arms can't be hit.
- Voice at the same volume regardless of distance; player list; gamer tags saved without logging in.

### Older backlog
- **Birdwatching in Hiking:** more birds with their own songs, photos through the binoculars, a saved field log. ("Hiking needs things to look at.")
- Never see inside your own body; a proper flying pose while gliding.
- Hiking trails, lookouts, a journal you fill by watching.
- Scope/binoculars feel "a little weird" and climbing is "close to correct" — he'll give details.
- PC and phone PvP redone separately later (no cross-play).
