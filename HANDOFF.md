# Just Trees: handoff for the next chat

Read this first. It carries over the project, the person, the way we work, and every open idea, so a new chat can pick up mid-stride instead of starting cold.

---

## 1. The person and the vibe (read this part twice)

- The owner (Ron) is **not a programmer**. He is a designer with a strong feel for games, especially **VR**, and especially **Population: One** (Pop: One), which he uses as the reference for how VR should *feel*. He describes things by feel: "the gun should buffer the movement but not shake", "high gravity and a mediocre fling". Your job is to turn that into code and then say back, in plain words, what you did.
- **Talk plainly and briefly.** No jargon, no code in replies unless asked, no long recaps. Short bullet lists are good. Say honestly what you could and could not test. You can never test in a real headset; say so.
- He thinks out loud and sends **notes in bursts**, often with typos and voice-to-text. Read generously and work out the intent. If one detail genuinely changes what you build, ask **one** short question.
- He's excited about what this is becoming, and rightly so. Match that energy, but stay honest: if something costs frame rate, can't be done for free, or wasn't tested, say it.

### What he is building (the essence)
**Just Trees** is a procedurally generated wilderness you *inhabit*: endless natural forests, mountains, lakes, weather and real animals, in your browser, on **VR first**, then PC and phone. Every map is new. The feeling to protect:

- **A beautiful, believable, naturalistic place.** Real biomes by latitude, real seasons, a real sun position, weather that shifts. Native animals only. Calm, not arcade.
- **VR that feels like Pop: One.** Hands pass through things; you climb anything you can see (trees, branches, rocks, cliffs); you fling yourself and glide with arms spread; a two-handed rifle with a real scope; binoculars by bringing both hands to your face. Physical, embodied, no buttons where a gesture will do.
- **Three ways to play:**
  - **Hiking:** explore and look. It needs things to *look at*: birdwatching and lookouts are next.
  - **Hunting:** long-range, patient sniping; the score grows with distance.
  - **PvP:** on hold, to be rebuilt around VR, then multiplayer.
- **Long views.** Seeing far and sniping far is part of the magic. Protect view distance; cut detail far away before cutting distance.
- **Free and simple to share.** One HTML file on GitHub Pages; multiplayer planned with no paid server at first.

---

## 2. How we work (his rules)

1. **Notes first, build on "go".** When he sends ideas, log them as **numbered notes** (continue the numbering, currently up to **34**). **Don't log notes until he says to take notes.**, restate each in a line or two of plain words, and list what's waiting. **Do not build until he says "go"** (or "do it", "lets do 1.x", or similar). If he narrows it ("just 1–8 plus 11"), build only those.
2. **Keep PC and phone exactly as they are** unless he says otherwise. Most new work is **VR only**; check before changing shared behaviour. Anything visual (tracers, fog, speed) gets a VR-only branch.
3. **Versions:** 1 → 1.1 → 1.12 → 1.2 → 1.21 → **1.22** (current). He names versions; if he just says go, pick the next small step (1.23) and mention it. He may ask you to build but hold: build and test, send the file, don't push until he says push.
4. **After building:**
   - Run the tests (section 5).
   - Push `index.html` to the repo, which makes the game live on his link.
   - Send him a backup copy of the file (`just-trees-1-xx.html`).
   - Reply with a short list of what changed, matching his note numbers, plus honest notes on what was only tested in simulation.
   - Offer a screenshot when something visual changed.
5. **Never upload the debug build.** `index.html` must contain no `window.D` and no `window.FREEZE`.
6. He tests on a **Meta Quest in the built-in Quest browser** (he hasn't said which Quest). He reports "no real missed frames" so far, even with the long view on XXL maps.

---

## 3. Where things are

- **Repo:** `JustTrees/JUST-TREES` on GitHub (created as `just-trees`, later renamed; the old name redirects). Branch `main`. A new chat must request repo access, and he clicks **allow**.
- **The game:** `index.html`, a single self-contained file of about 1.08 MB and 6,300 lines. Three.js **r149** is inlined (minified) at the top; all game code is in one big function after it.
- **Live link:** GitHub Pages for this repo, probably https://justtrees.github.io/JUST-TREES/. He opens it via Settings → Pages → Visit site.
- He does **not** own justtrees.com; we removed the custom domain.
- **Test tools:** `dev/` (section 5).
- **This file:** `HANDOFF.md`. Update it when big things change.

---

## 4. What exists now (v1.22)

### World and generation (all modes)
- **Settings:**
  - Latitude 0–85°, North or South: sets the biome (tropical, temperate, boreal, tundra, polar).
  - Terrain roughness.
  - Time of day, with a real sun position.
  - Month: sets the season.
  - Tree density.
  - Map size: XS 250 m, S 400, M 560, L 800, XL 1.2 km, XXL 1.6 km.
  - Edges: Island (ocean) or Endless (borderland terrain and forest fade into the haze).
  - Weather: random, clear, rain, fog, snow (with styles, including blizzard) or storm. Hiking never gets fog.
- **Terrain:** generated heightfield with erosion and worn-down summits. `H(x,z)` is the exact triangle surface the player stands on.
- **Trees:** trunk plus textured branch cards, Pop: One style; variants include pruned, odd and giant trees, and one tallest tree per map. **Big limbs** you can stand on (`limbGrid`) and hold (`limbHold`). Baked soft tree shadows.
- **Rocks:** boulders, slabs, cliff sections (crag/spine/shelf), outcrops, logs and bushes. Rock shapes are stamped onto a 1 m height grid (`rockGrid`, `rockTopAt`, `rockAround`).
- **Far-away trees:** every tile has full-detail and simpler tree groups. Beyond about 270 m (further when zoomed), the simpler trees show: one card per branch, alternating flat and upright, with a 4-sided trunk. On XXL that's about 4.2 million triangles instead of 10 million.
- **Look:** ACES tone mapping; `grade()` shader with split-toning, saturation, and a VR-only shadow lift (`GRADE.uLift`); ground fog in valleys; sky with sun, moon and stars.
- **Sound:** fully synthesized, no audio files. Footsteps are slow and soft, wind and trees are quiet, and the gunshot, bolt and kill "bing" are synthesized too.

### Animals (Hunting; birds everywhere)
- **Species:** buck, bear, polar bear, baboon, panther, wolf, seal, rabbit, birds and monkeys, all native to the biome.
  - Built from code: smooth swept-spine bodies with animated legs.
  - Score per metre of shot distance: bird 1, monkey .6, baboon .5, rabbit .5, panther .3, wolf .2, buck .1, seal .1, bear .05, polar bear .05.
  - A hit means a kill: the animal tips over and you hear a bing. No blood.
- **Behaviour:**
  - Animals wander, graze, notice movement, and ease away or bolt.
  - A shot empties the area: animals flee 140–340 m along dry, walkable ground, sprint then trot, and settle there (`fleeFar`).
  - If an animal is stuck while trying to walk, it squeezes out to the nearest open ground (`unstick`).
  - A still hunter slowly draws animals closer.

### PC and phone (unchanged, keep as is)
- **PC:** WASD to move, mouse to look, left click fires, scroll zooms or uses the binoculars, Shift runs, Space jumps, C crouches, Esc for the menu.
- **Phone:** joystick, drag to look, and on-screen buttons.
- **Zoom steps:** Hunting 18°, 9° and 6°; Hiking binoculars 11°.
- **Other features:** a minimap and full map, and a 30-second drone flyover before each map.

### VR (most of the recent work)
- **Getting in:**
  - On the black first screen, a gold **PLAY IN VR** button (headset browsers only) goes straight into VR.
  - In VR, the pixel intro and logo, Choose Your Way, and the full settings appear as **curved panels around you**. Point with either controller laser and pull the trigger; sliders drag while you hold it.
  - The panels show the same descriptions as the flat menu: biome, sun angle, Twilight or Night, and so on.
  - The flat setup page also has an Enter VR button. Its VR section sits below Month: hand choice and the fling slider.
- **Before each map:**
  - A "Growing trees…" panel, then a **floating mini-map model** turns in front of you at table height: land, lakes, every tree as a tiny cone, and a yellow pin at your start.
  - Pull the trigger to fade and drop in. Your real position is placed on the spawn point (`vr.placeAt`).
- **Pause:** **hold Y** (the top button on your off hand) for about 0.7 s: Resume, New map, Change settings, Main menu, Exit VR.
- **Controls** (right-handed by default; a left-handed option swaps everything):
  - **Off-hand stick:** walk where you look, at 8.5 m/s. **Click it to sprint** for 6 s at 12.5 m/s.
  - **Gun-hand stick:** snap turn 30°. While scoped or using the binoculars, it zooms instead.
  - **Gun hand:** A takes the gun out or puts it away; B marks where you aim (a yellow beam for 45 s); the trigger fires.
  - **Off hand:** the trigger raises the map; the grip snaps to the rifle's front grip (two-handed). The off hand never steers the aim.
  - **Crouch for real** (measured from your standing height). There are no jump or crouch buttons in VR.
- **Rifle:**
  - Heavy, damped feel: small shakes are soaked up and deliberate swings are followed (`vr.gq`/`vr.gp` with an adaptive rate).
  - Less kick with two hands.
  - Bullet in VR: a thin streak at 1,100 m/s; shots count out to 2.4 km when scoped, 900 m otherwise.
  - In Hunting the bolt is worked by hand (see the guns section below).
- **Scope:** both hands on the gun, eyepiece within about 14 cm of your eye and aimed roughly where you look. The **whole view zooms** (about 4.6×, 9× and 14×, matching the PC steps) with a black surround and crosshair.
  - One mono view (both eyes see the same image) for comfort.
  - The **horizon stays level** whatever your wrist does (`levelQ`).
  - Fog and animal draw distance stretch while zoomed.
- **Binoculars:** with empty hands, hold both grips near your face. The view zooms (about 6.6× or 11×) with two circles, follows your head (smoothed), and stays level. This works in every mode.
- **Climbing** (`climbableAt`, `climbTick`, Pop: One style):
  - You can only grab what you see: the tapering trunk, each branch card, big limbs, rocks and cliffs, steep mountain faces, bushes and the ground.
  - Your hand passes through things, and the **hand glows x-ray blue** while inside something grabbable.
  - Grab with grip, or arrive already gripping and you catch. One hand holds at a time, and your body moves with the holding hand.
  - Let go mid-pull to **fling**. The Fling setting runs Gentle to Wild, default 4.5, which takes about 5 flings to reach a treetop.
  - Gravity is high (`CLIMB_G` = 22). No fall damage. You land on the ground, a rock or a big limb.
  - The gun must be put away to climb.
- **Your face can't go inside** trunks, big limbs, rocks or the mountain (`headBlocked`). This also applies while climbing, and the world slides back instead. Right up against a rock face is allowed, so you can climb it.
- **Gliding:** spread your arms wide while airborne. You fly forward at 90° to the line between your hands, on the side they face (`vr.glideDir`), not where you look. Tilting your hands banks you. On ground steeper than about 40°, you **skip** downhill, and spreading your arms lifts you off into a glide. No shooting while gliding.
- **Body:**
  - A skinned soldier avatar (green camo). Its head is hidden from you; arms reach your real wrists by IK.
  - **Gloves** are drawn separately on the controllers, in WebXR grip space: the wrist toward +Y and the back of the hand toward +X on the right hand.
  - Fingers curl with grip, and the index finger follows the trigger.
- **Look and performance in VR:**
  - View distance 1.5 km (the base fog), with the forest outside the map reaching that far.
  - Shadows brightened; tone mapping exposure 1.08.
  - Tree sway frozen (less leaf shimmer).
  - Leaf edges smoothed (alpha-to-coverage on foliage, set when the map is generated in VR).
  - Render scale 0.8 and maximum foveation. He found Smooth looked best, so the resolution option was removed.
- **Wrist HUD:** a small panel on the off-hand wrist showing info and score (and "+24 Pistol ammo" when you loot).

### VR Hunting guns (1.22, notes 26–34; VR Hunting only, PC and phone unchanged)
- **Gun wheel:** hold B (0.3 s) opens a wheel; point the gun-hand ray at a gun and let go. Tap B still marks; tap A still holsters/draws.
- **Guns (`WEAP`, models in `GUNMODEL` plus the sniper):** sniper (5 rounds, bolt after every shot, the only scope), assault rifle (30, full auto ~8/s), SMG (32, full auto ~12/s, less accurate, 350 m reach), pistol (12, semi-auto, 250 m, two-handed grip optional). Damage numbers are for future PvP; in Hunting a hit is still a kill.
- **Reload, one step at a time, off-hand grip only** (`reloadTick`, `arms[kind].phase`: 0 ready, 1 magazine out, 2 bolt due): the empty magazine pops out and hovers glowing yellow; a squeeze within 35 cm (`SNAP_R`) snaps the glove onto it, push it in along its slot; then the bolt / charging handle / slide glows, squeeze to snap onto it, pull back, let go. Only then can the off hand snap to the front grip. Gun-hand stick click drops the magazine early (its rounds go back to spare). Dry trigger clicks.
- **Scope:** only two-handing the sniper with the back of the gun within ~30 cm of your face, roughly pointing where you look. Letting go to work the bolt drops it; re-grip brings it back.
- **Ammo counter** on the gun's side (magazine | spare), mirrored for left-handed. **Ammo cans** (instanced, one colour per gun) around the map, a few near spawn; walk over or touch to pick up; up to 300 spare each (`AMMO_CAP`).
- **Shoot while hanging:** with the gun out, the off hand can still climb; the gun hand can't grab, and A won't draw the gun while the gun hand is holding on. No scope while hanging.
- Test: `dev/test_vr_guns.py` on the debug copy.

### PvP (on hold; code kept, menu button disabled)
- Five bots hunt you; shield 100 and health 100; the green zone mist in 10-minute rounds; grenades.
- **Grenades are pre-tuned** for the VR rebuild: `NADE_SPEED` 28, lift 7, 250 damage within 8 m (via `blastBots`).
- Unconfirmed: whether grenades should hurt the thrower, and whether "10× damage" meaning 250 is right.
- Soldier avatars: hood, full skull mask, sunglasses, baggy camo (black, brown, green, snow or mixed). Masks were meant to be achievements only.

---

## 5. How to build and test

- **Edit by exact-string replacement.** Write a small Python patch script that does `src.replace(old, new)`, **asserting each old string appears exactly once**, then apply it to a copy of `index.html`. This stays safe in a 1 MB file. Keep a backup of the previous version first.
- **Test tools** (in `dev/`; they use Playwright with Chromium and SwiftShader, already installed in Claude's workspace):
  - `python3 dev/make_debug.py index.html /tmp/dbg.html` makes a debug copy with `window.FREEZE` (stop the clock and step frames by hand) and `window.D` (handles to internals). If a test needs more internals, add them to `window.D` in `make_debug.py`.
  - `python3 dev/test_load.py index.html`: Hiking and Hunting load with no errors and show the version. **Always run this on the clean file before pushing.**
  - The VR tests run on the debug copy, by faking controllers through `vr.readInputs`:
    - `dev/test_vr_moves.py`: walk and sprint speed, level scope, bullet speed and width, rock and cliff grabs, face blocking, downhill skips, lifting off into a glide.
    - `dev/test_vr_climb_scope.py`: trunk, branch and limb grabs, the blue hand, pulling up, landing on limbs, scope zoom steps, the zoomed render.
    - `dev/test_vr_glide_gun.py`: sprint, glide direction, climbing face block, rifle steadiness (shake in vs out), far-tree switching.
    - `dev/test_vr_guns.py`: magazines, the reload steps and snapping, bolt per sniper shot, scope on/off, gun wheel, fire rates, early magazine drop, ammo cans, shooting while hanging.
    - `dev/test_vr_menus.py`: the whole VR menu flow, from intro to settings to loading, preview, drop-in and pause. It saves screenshots to `/tmp/`.
  - Other checks:
    - `dev/test_animals.py`: stuck episodes and flee distance (run it on two builds to compare).
    - `dev/test_solid_ground.py`: finds visible surfaces that aren't solid.
    - `dev/test_far_trees.py`: triangle counts with and without the lighter far trees.
- **Pushing:**
  - `cp` the build to `index.html`, then `git fetch origin main`, `git add index.html`, commit (author `JustTrees`) and `git push origin main`.
  - The push prints a "repository moved" notice; that's fine.
  - It's live 1–2 minutes later. Tell him to refresh, and say the menu shows the new version.

### Gotchas we already hit (don't relearn these)
- The renderer outputs **linear** colour (three's default output encoding is linear). **Don't mark canvas textures as sRGB**, or menus come out dark.
- **Inside an XR session, `window.requestAnimationFrame` doesn't run.** Drive everything from the `renderer.setAnimationLoop(loop)` loop. The VR intro paints its canvas from `vruiTick`.
- **VR movement model:**
  - `vr.readInputs()` returns **world-space** head and hand poses.
  - Walking moves the play space through an offset reference space (`vr.ox/oy/oz/yaw`, applied with `XRRigidTransform` in `vrAfterMove`).
  - The menus switch back to the base space and reset the offset to zero; `vr.placeAt` re-anchors you on a new map.
- **Full-view zoom** (`vrZoomRender`): set `renderer.xr.cameraAutoUpdate = false`, call `updateCamera`, scale both eye projections (`e[0], e[1], e[4], e[5]`) by the zoom, give both eyes the same steadied pose, render, then restore.
- **VR-specific world settings are read when the map is generated:** fog base, forest reach outside the map, smooth leaf edges. `VR_ON` must be set before `generate()`.
- **Raycasts:** call `updateMatrixWorld` first when objects moved this frame and nothing has rendered yet; the VR menu does this.
- **`obstacles` is replaced by every `generate()`.** Expose it through a getter in debug hooks.
- **Tile culling** is manual (`cullTiles`). Instanced meshes have `frustumCulled = false`. In VR, a wide 118° culling camera is used.
- **Is the Quest a touch device?** Unknown. `isTouch` (coarse pointer) lowers some counts. Don't assume either way.

---

## 6. Open notes and the backlog

### Logged, not built yet (his note numbers)
- **25, birdwatching in Hiking** (VR, PC and phone): his newest idea.
  - **More birds** to suit biome and season: songbirds in the trees, hawks and eagles circling, ducks and herons on lakes, owls at dusk, woodpeckers tapping. Each has its own song, so you hear them first.
  - **Take photos through the binoculars:** the trigger in VR, a click on PC, a Photo button on phone, with a shutter flash.
  - **A saved field log:** species, your photo, date, time and map number. You can flip through it from the menu, or a VR panel. It counts how many of each biome's birds you've found, with rare birds tied to place, season or time.
  - **Open question:** birds only, or every animal you photograph? Ask him.
  - He also said "Hiking needs things to look at", so this is the priority direction for Hiking.
- **9, never see inside your own body:** only see your body when looking down. Hide anything that would clip into your view while gliding, climbing or crouching.
- **10, flying pose:** while gliding, the body sits below and behind your head, chest down, feet trailing back. Right now the body floats in front of the head while gliding.
- Scope and binoculars feel "a little weird"; he'll describe the details later.
- Climbing is "close to correct"; details later.

### Bigger backlog (from earlier sessions)
- **Hiking:**
  - Trails (a ribbon path), a trailhead sign, and oval dirt **lookouts** with events and easter eggs (no people), including a **Morse code tower**.
  - Plants, and a journal you fill **only by watching**. Birdwatching should become the first part of this journal.
- **Multiplayer** (planned, not started; section 7).
- **PvP rebuilt around VR first,** with climbing and the pre-tuned grenades. Then PC PvP and phone PvP get redone separately. **No cross-play:** VR plays VR, PC plays PC, phone plays phone.
- Settings menu and personal bests; deserts and savanna; bloom; soldier shadows; blending biomes by latitude.
- The VR rifle bolt animation.
- Optionally turn off the sway math entirely in VR for a small speed-up (right now it's only frozen).

---

## 7. Multiplayer plan (agreed in principle)

- **Peer-to-peer WebRTC.** Everyone generates the same world from the shared map number, so only players, shots and animals are sent. One player hosts: runs the animals, decides hits, and forwards updates.
- **Finding games:** a **private code** like `PINE-42` to share with friends, plus a **public lobby list** showing mode, map size and players (for example 3/8), with **Join** and **Quick join**. Hosts choose Public or Private, and the list shows ping or region.
- **Free backend on Cloudflare:**
  - The lobby list and matchmaking on Workers and Durable Objects: the free plan, then $5 a month if it grows.
  - The connection relay (TURN) for the 10–20% of players behind strict networks: 1,000 GB a month free, then $0.05 per GB.
- **Sizes:** start with 2 (VR against VR, by code), then 8 (lobby list, Quick join, automatic host handoff so a sleeping Quest doesn't end the match), then 12 (Cloudflare forwards traffic so no headset carries the whole match).
- **Voice chat:**
  - Positional proximity voice (voices come from each player's head) plus team radio. This matches his earlier Teams and Open comms idea.
  - Push to talk, or always on.
  - Mute buttons, which matter for public lobbies.
  - At 12 players, route voice through Cloudflare's relay; it's still effectively free.
- **Caveats to keep telling him:**
  - No cheat protection without a real server.
  - Only mute, no moderation.
  - Testing needs him plus friends on different networks.
  - A full game server (for anti-cheat or 16+ players) costs about $20 a month in the US.

---

## 8. His standing preferences (don't undo these)

- **Camera and sound:** no camera bob; slow, soft footsteps; quiet wind, trees and rain.
- **Lighting:** no light shafts or light bounce, and no "Full day" mode.
- **Terrain and views:** peaks rounded, not spiky. Long view distance. Hiking has no fog.
- **Animals and scoring:**
  - Native animals only; a hit is a kill with a bing and no blood; score per metre.
  - Birds bigger and slower; easier to hit.
  - Animals scatter based on your movement, not your sound.
- **VR controls:**
  - No jump or crouch buttons in VR.
  - The off hand never steers the aim.
  - Snap turn 30°; a left-handed option.
  - Heavy motion damping on the gun; less kick with two hands.
  - Scoping is two-handed, eye to the eyepiece; binoculars are both grips at your face.
  - Gliding by spreading your arms.
- **VR climbing:**
  - Pop: One-style, with high gravity and a medium fling; no fall damage.
  - The gun must be away to climb.
  - Climbing works in all VR modes; never on PC or phone (they have jump and crouch).
- **VR look:** smooth resolution; no tree sway; long views with lighter far trees rather than shorter views.
- **Avatars:** masks are achievements only, never full skins. Avatars are soldiers in baggy camo with hoods.

---

*Last updated at v1.22 (October 2026). He asked to set the old backlog aside and only work on what he brings up; his stated direction is VR mechanics, how the characters look, climbing and gliding feel, and later a PC VR high-quality setting chosen automatically by device.*

*Earlier note: The next chat: read this, check the repo (`index.html`, `dev/`), then ask Ron what he wants to start with. Birdwatching (note 25) and the body notes (9 and 10) are waiting, and multiplayer is the big next chapter.*
