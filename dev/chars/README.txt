How the 2.37 characters are made (models/chars/*.bin and tex_*.jpg)

Sources (CC0, Quaternius): models/source/Quaternius_Characters_slim_glTF.zip (Universal Base Characters + Modular Character Outfits - Fantasy,
glTF and base-colour textures only) and models/source/Universal_Animation_Library_Standard.zip + _2_Standard.zip.

1. Unzip the characters zip into a work folder (it has outfits/ base/ hair/ parts/). Put view.html, compose.js, bview.js, hit.js, shot2.py, anim.py
   and bake.py next to those folders, plus node_modules with three@0.149 (npm i three@0.149). anim/ual1.glb and anim/ual2.glb are the
   UAL1/UAL2 "Unreal-Godot" .glb files from the two animation zips.
2. Cut the boots and sleeves (cutboot.py), run from the work folder:
     LOW=.1 python3 cutboot.py parts/Male_Ranger_Feet_Boots.gltf parts/Male_Ranger_Feet_Boots_C.gltf 0           (Ranger: plain boots, no shin guards)
     LOW=.1 python3 cutboot.py parts/Female_Ranger_Feet.gltf parts/Female_Ranger_Feet_C.gltf 0
     LOW=.1 TOPY=.17 python3 cutboot.py parts/Male_Ranger_Feet_Boots.gltf parts/Male_Ranger_Feet_Boots_D.gltf 0  (Soldier: ankle shoe)
     LOW=.1 TOPY=.17 python3 cutboot.py parts/Female_Ranger_Feet.gltf parts/Female_Ranger_Feet_D.gltf 0
     LOW=.1 TOPY=.17 ABOVE=1 python3 cutboot.py parts/Male_Ranger_Feet_Boots.gltf parts/Male_Ranger_Feet_Boots_E.gltf 0   (Soldier: the old boot shaft, worn as camo trouser leg)
     LOW=.1 TOPY=.17 ABOVE=1 python3 cutboot.py parts/Female_Ranger_Feet.gltf parts/Female_Ranger_Feet_E.gltf 0
     MAXAX=.40 python3 cutboot.py parts/Female_Peasant_Arms.gltf parts/Female_Peasant_Arms_Short.gltf 0             (Soldier women: short sleeves)
3. Look at them: shot2.py renders a lineup (COMPOSE=compose.js), anim.py renders animation frames. compose.js holds every body shape Ron approved
   (chest, rear, thighs, arms, shoulders, the men's build, the bounce shapes) and the woodland camo.
4. Bake: python3 bake.py  -> ../baked/*.glb (shapes applied).  Then in a folder with @gltf-transform/core@4, functions, extensions, meshoptimizer, sharp:
     node simp.mjs ../baked ../baked_s .55                         (drop unused data, weld, simplify a little)
     node build_chars.mjs ../baked_s <repo>/models/chars <work folder>   (the game's format + 512 px JPEG textures)
The game reads them with charParse() (index.html, "2.37: people"). hit.js / bview.js are the viewer versions of the game's exact hit check and loader.
