import sys
src, out = sys.argv[1:3]; s = open(src).read()
def rep(a, b):
    global s; assert s.count(a) == 1, (s.count(a), a[:90]); s = s.replace(a, b)
# always one legend per map (tropical forests get a Bigfoot too)
rep('''["parrot", 3, [4, 6]], ["bird", 4]],''', '''["parrot", 3, [4, 6]], ["bird", 4], ["bigfoot", 1]],''')
rep('''left: LEGEND[kind] ? (bigMap && Math.random() < .5 ? 1 : 0) : n(base) }));''', '''left: LEGEND[kind] ? 1 : n(base) }));''')
rep('''  const bigMap = set.size === "xl" || set.size === "xxl";\n''', "")
# hidden until you've earned the red sniper (PC, with no loot: until you've found the porch)
rep("const FLY = { bird: 1, parrot: 1, eagle: 1, owl: 1 }, LEGEND = { bigfoot: 1, yeti: 1 };",
    "const FLY = { bird: 1, parrot: 1, eagle: 1, owl: 1 }, LEGEND = { bigfoot: 1, yeti: 1 };\nconst legendSeen = () => lootMode() ? (vr.own.hunt || 0) >= 5 : !!(PORCH && PORCH.found);   // Bigfoot / Yeti only show themselves once you hold the red sniper")
rep("    const cd = Math.hypot(A.x - camera.position.x, A.z - camera.position.z), vis = cd < Math.min(far, beastDraw());",
    "    const cd = Math.hypot(A.x - camera.position.x, A.z - camera.position.z), vis = cd < Math.min(far, beastDraw()) && (!LEGEND[A.kind] || legendSeen());")
# the one shot: only a bullet that really goes near him (no more 900 m / anyone's shot spooking him)
rep("""  camera.getWorldDirection(_lf);
  for (const A of beasts) if (LEGEND[A.kind] && !A.dead && !A.gone && !A.bolting && !(A.boltIn > 0)) {
    const dx = A.x - o.x, dy = A.y + 1.4 - o.y, dz = A.z - o.z, d = Math.hypot(dx, dy, dz), aimed = (dx * _lf.x + dy * _lf.y + dz * _lf.z) / d > .994;   // within ~6° of where you look
    if (d < 900 || (aimed && d < 2600)) A.boltIn = Math.max(.6, d / 700 + .3);       // waits for the bullet: you always get your one shot
  }
""", "")
rep("function legendBolt(A) {", """function legendShot(o, dir, reach, speed) {                // a shot at Bigfoot: the bullet passing (or landing) within 15 m of him is your one shot
  if (gameMode !== "hunt" || !legendSeen()) return;
  for (const A of beasts) if (LEGEND[A.kind] && !A.dead && !A.gone && !A.bolting && !(A.boltIn > 0)) {
    const h = castShot(o, dir, reach), maxD = h && h.p ? h.p.distanceTo(o) + 2 : reach;          // where the bullet actually stops
    const cx = A.x - o.x, cy = A.y + 1.2 - o.y, cz = A.z - o.z, t = Math.max(0, Math.min(maxD, cx * dir.x + cy * dir.y + cz * dir.z));
    const d = Math.hypot(cx - dir.x * t, cy - dir.y * t, cz - dir.z * t);
    if (d < 15) A.boltIn = t / speed + .15;                  // he bolts the moment it goes by (a hit lands first and counts)
  }
}
function legendBolt(A) {""")
rep("""  if (online) mpSend({ t: "f", o: [from.x, from.y, from.z], v: [v.x, v.y, v.z], k: vr.gunKind });""",
    """  legendShot(from, v.clone().normalize(), vr.scoped ? 3200 : W ? W.reach : 900, v.length());
  if (online) mpSend({ t: "f", o: [from.x, from.y, from.z], v: [v.x, v.y, v.z], k: vr.gunKind });""")
rep("  const hit = castShot(camera.position, dir); hit.dist = camera.position.distanceTo(hit.p);",
    "  const hit = castShot(camera.position, dir); hit.dist = camera.position.distanceTo(hit.p); legendShot(camera.position, dir, hit.dist + 2, 2000);")
# once he's bolting you can't hit him
rep("    if (A.dead || !A.root.visible) continue;\n    A.root.updateMatrixWorld();", "    if (A.dead || !A.root.visible || A.bolting) continue;\n    A.root.updateMatrixWorld();")
# giant: bare trunk all the way up to the porch, branches start again 3 m above it
rep("clearAt: Ht => { const s0 = GT / (Ht + 1.4), y = pH / s0; return [y - 2.6 / s0, y + 6.5 / s0]; } });", "clearAt: Ht => { const s0 = GT / (Ht + 1.4), y = pH / s0; return [-5, y + 3 / s0]; } });")
open(out, "w").write(s)
