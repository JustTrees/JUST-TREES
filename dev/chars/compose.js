const CAMO = { brown: [0xb59a6c, 0x7a5a3a, 0x4a3726, 0x9c8a5a], green: [0x5d6b3a, 0x3c4a28, 0x7d7a4f, 0x2b3220], grey: [0x8d9196, 0x5f6368, 0xb4b7b9, 0x3e4246],
  white: [0xe9eef0, 0xc9d1d6, 0xa9b3ba, 0xf6f8f9], black: [0x2a2c2e, 0x17191a, 0x3e4245, 0x0c0d0e] };
const SKIN = [[1, 1, 1], [.86, .74, .64], [.66, .5, .4], [.45, .32, .25], [.3, .21, .17]];
const hairC = h => new THREE.Color(HAIRC[h] || HAIRC.brown).convertSRGBToLinear().multiplyScalar(3.4);
const HAIRC = { black: 0x1b1714, brown: 0x5a3a22, blonde: 0xd9b26a, red: 0x9a3a1e, grey: 0xb8b8b8, white: 0xf2f2f2, blue: 0x2f6fd8, pink: 0xff6fb5 };
let ANIM = null, ANIM2 = null;
function lamb(orig, o) {                                     // the game's plain lit look: base colour map only
  const m = new THREE.MeshLambertMaterial({ map: orig.map || null, color: orig.color ? orig.color.clone() : 0xffffff, side: orig.side, transparent: orig.transparent, alphaTest: orig.alphaTest }); m.name = orig.name || "";
  if (o && o.camo) {
    const C = CAMO[o.camo].map(c => new THREE.Color(c).convertSRGBToLinear()); m.userData.camo = true;
    m.onBeforeCompile = sh => {
      sh.uniforms.uC = { value: C }; sh.uniforms.uLeather = { value: new THREE.Color(o.leather || 0x3a3226).convertSRGBToLinear() }; sh.uniforms.uLeatherOn = { value: o.leather ? 1 : 0 };
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vOP;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvOP = position;');
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying vec3 vOP; uniform vec3 uC[4]; uniform vec3 uLeather; uniform float uLeatherOn;
float hsh(vec3 p){ return fract(sin(dot(p, vec3(12.9898,78.233,37.719)))*43758.5453); }
float vn(vec3 p){ vec3 i=floor(p), f=fract(p); f=f*f*(3.-2.*f); return mix(mix(mix(hsh(i),hsh(i+vec3(1,0,0)),f.x),mix(hsh(i+vec3(0,1,0)),hsh(i+vec3(1,1,0)),f.x),f.y),mix(mix(hsh(i+vec3(0,0,1)),hsh(i+vec3(1,0,1)),f.x),mix(hsh(i+vec3(0,1,1)),hsh(i+vec3(1,1,1)),f.x),f.y),f.z); }
float fb(vec3 p){ return .55 * vn(p) + .3 * vn(p * 2.13 + 5.) + .15 * vn(p * 4.7 + 9.); }
#define CAMO_SCALE 13.0
vec3 rgb2hsv(vec3 c){ vec4 K=vec4(0.,-1./3.,2./3.,-1.); vec4 p=mix(vec4(c.bg,K.wz),vec4(c.gb,K.xy),step(c.b,c.g)); vec4 q=mix(vec4(p.xyw,c.r),vec4(c.r,p.yzx),step(p.x,c.r)); float d=q.x-min(q.w,q.y); return vec3(abs(q.z+(q.w-q.y)/(6.*d+1e-10)),d/(q.x+1e-10),q.x); }`)
      .replace('#include <map_fragment>', `#include <map_fragment>
{ vec3 c = pow(diffuseColor.rgb, vec3(1. / 2.2)); vec3 h = rgb2hsv(c); float v = h.z, sat = h.y;    // (judged in screen colours)
  bool green = h.x > .16 && h.x < .5 && sat > .18;                 // the ranger's cloth
  bool cream = v > .55 && sat < .32;                                // the peasant's shirt
  bool dark = v < .3 && !(h.x > .15 && h.x < .5);                  // dark trousers
  bool metal = sat < .15 && v > .6 && !cream;
  // woodland-style camo: smaller, jagged, layered patches (warped multi-scale noise), no big round blobs
  vec3 p = vOP * CAMO_SCALE; vec3 wq = vec3(fb(p * .6 + 1.3), fb(p * .6 + 7.1), fb(p * .6 + 3.7)); p += (wq - .5) * 2.4;
  float a = fb(p + 3.1), b = fb(p * 1.2 + 11.7), c2 = fb(p * .85 + 23.3);
  vec3 cam = a > .6 ? uC[2] : b > .585 ? uC[1] : c2 > .6 ? uC[3] : uC[0];
  if (green || cream || dark) { float ref = green ? .42 : cream ? .78 : .2; diffuseColor.rgb = cam * clamp(v / ref, .55, 1.25); }
  else if (!metal && uLeatherOn > .5) diffuseColor.rgb = uLeather * clamp(v / .5, .5, 1.3);
}`);
    };
  }
  return m;
}
// body shape, built in: men bulkier (arms, shoulders, chest, neck), women fuller (chest, hips/rear). Done on every piece the same way, so clothes still fit.
// the original female chest shape, read from the Peasant top: height above a straight line from under the chest to the upper chest, per spot
let WBC = null, CHF = null, RIBFLAT = false, FLAT = null, ZC = null; const CF = { x0: -.2, y0: 1.06, st: .01, NX: 41, NY: 45 };
async function zGrid(file, noBelt) {                                         // front-most depth of the outfit cloth, per spot (mirrored, gaps filled)
  const s = (await load(file)).scene, { x0, y0, st, NX, NY } = CF, Z = new Float32Array(NX * NY).fill(NaN);
  s.traverse(m => { if (!m.isMesh || /Regular/.test(m.material.name) || (noBelt && /Belt/.test(m.name))) return; const P = m.geometry.attributes.position;
    for (let i = 0; i < P.count; i++) { const x = P.getX(i), y = P.getY(i), z = P.getZ(i); if (z <= 0) continue;
      for (const xx of [x, -x]) { const ix = Math.round((xx - x0) / st), iy = Math.round((y - y0) / st); if (ix < 0 || ix >= NX || iy < 0 || iy >= NY) continue; const k = iy * NX + ix; if (!(Z[k] >= z)) Z[k] = z; } } });
  for (let ix = 0; ix < NX; ix++) {
    const col = []; for (let iy = 0; iy < NY; iy++) if (!isNaN(Z[iy * NX + ix])) col.push(iy);
    for (let iy = 0; iy < NY; iy++) { const k = iy * NX + ix; if (!isNaN(Z[k]) || !col.length) continue; let lo = -1, hi = -1; for (const c of col) { if (c < iy) lo = c; if (c > iy && hi < 0) hi = c; }
      Z[k] = lo < 0 ? Z[hi * NX + ix] : hi < 0 ? Z[lo * NX + ix] : Z[lo * NX + ix] + (Z[hi * NX + ix] - Z[lo * NX + ix]) * (iy - lo) / (hi - lo); } }
  for (let k = 0; k < Z.length; k++) if (isNaN(Z[k])) Z[k] = 0;
  return Z;
}
async function chestField(bodyFile) {
  const { x0, y0, st, NX, NY } = CF, Z = await zGrid('parts/Female_Peasant_Body.gltf'), C = window.CH || {};
  const yA = C.yA || 1.15, yB = C.yB || 1.43, iA = Math.round((yA - y0) / st), iB = Math.round((yB - y0) / st);
  let F = new Float32Array(NX * NY);
  for (let ix = 0; ix < NX; ix++) { const x = x0 + ix * st, wx = Math.max(0, Math.min(1, (.16 - Math.abs(x)) / .05));
    for (let iy = iA; iy <= iB; iy++) { const base = Z[iA * NX + ix] + (Z[iB * NX + ix] - Z[iA * NX + ix]) * (iy - iA) / (iB - iA); F[iy * NX + ix] = Math.max(0, Z[iy * NX + ix] - base) * wx; } }
  for (let pass = 0; pass < (C.blur || 2); pass++) { const G = new Float32Array(NX * NY);
    for (let iy = 1; iy < NY - 1; iy++) for (let ix = 1; ix < NX - 1; ix++) { let s2 = 0; for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) s2 += F[(iy + a) * NX + ix + b] * (a || b ? (a && b ? 1 : 2) : 4); G[iy * NX + ix] = s2 / 16; }
    F = G; }
  let M = 0; for (const v of F) M = Math.max(M, v);
  const rp = C.round || .75; for (let k = 0; k < F.length; k++) if (F[k] > 0) F[k] = M * (F[k] / M) ** rp;   // rounder: fuller dome, same footprint
  // squeeze toward the middle (sq) so they sit together: resample
  const sq = C.sq || 1.2, H = new Float32Array(NX * NY), at = (A, x, iy) => { const fx = (x - x0) / st, ix = Math.floor(fx), t = fx - ix; return ix < 0 || ix >= NX - 1 ? 0 : A[iy * NX + ix] * (1 - t) + A[iy * NX + ix + 1] * t; };
  for (let iy = 0; iy < NY; iy++) for (let ix = 0; ix < NX; ix++) H[iy * NX + ix] = at(F, (x0 + ix * st) * sq, iy);
  F = H;
  // the cloth bridges straight over the middle of THIS outfit's top: small dip only
  const Zo = await zGrid(bodyFile), dip = C.dip !== undefined ? C.dip : .008, cx0 = Math.round(-x0 / st);
  for (let iy = 0; iy < NY; iy++) {
    let pk = cx0, pv = 0, fp = 0; for (let ix = cx0; ix < cx0 + 13; ix++) { const k = iy * NX + ix, zt = Zo[k] + F[k]; if (zt > pv) { pv = zt; pk = ix; fp = F[k]; } }
    const on = Math.min(1, fp / .025); if (on <= 0) continue;
    for (let ix = cx0; ix <= pk; ix++) { const t = 1 - (ix - cx0) / Math.max(1, pk - cx0), tgt = pv - dip * t * t;
      for (const jx of [ix, 2 * cx0 - ix]) { const k = iy * NX + jx; F[k] = Math.max(F[k], F[k] + (tgt - Zo[k] - F[k]) * on); } } }
  // under the chest: how far the top sticks out past the belly line (measured on the cloth, belts left out), to take away
  const Zc = await zGrid(bodyFile, true), FB = C.fb || { ref: 1.14, a: 1.16, b: 1.19, c: 1.265, d: 1.29 }, ir = Math.round((FB.ref - y0) / st);
  FLAT = new Float32Array(NX * NY); ZC = Zc;
  for (let iy = 0; iy < NY; iy++) { const y = y0 + iy * st, w = y < FB.b ? Math.max(0, (y - FB.a) / (FB.b - FB.a)) : y > FB.c ? Math.max(0, (FB.d - y) / (FB.d - FB.c)) : 1; if (w <= 0) continue;
    for (let ix = 0; ix < NX; ix++) { const x = x0 + ix * st, wx = Math.max(0, Math.min(1, (.16 - Math.abs(x)) / .04)); FLAT[iy * NX + ix] = Math.max(0, Zc[iy * NX + ix] - Zc[ir * NX + ix]) * w * wx; } }
  return CHF = F;
}
function chestAt(x, y, A) { const { x0, y0, st, NX, NY } = CF, fx = (x - x0) / st, fy = (y - y0) / st, ix = Math.floor(fx), iy = Math.floor(fy);
  if (ix < 0 || iy < 0 || ix >= NX - 1 || iy >= NY - 1) return 0; const tx = fx - ix, ty = fy - iy, F = A || CHF;
  return (F[iy * NX + ix] * (1 - tx) + F[iy * NX + ix + 1] * tx) * (1 - ty) + (F[(iy + 1) * NX + ix] * (1 - tx) + F[(iy + 1) * NX + ix + 1] * tx) * ty; }
function boneBind(sk) { const out = {}; sk.bones.forEach((b, i) => { out[b.name] = new THREE.Vector3().setFromMatrixPosition(sk.boneInverses[i].clone().invert()); }); return out; }
function shape(m, sex) { const BELT = /Belt/.test(m.name), MB = sex === 'Female' ? new Float32Array(m.geometry.attributes.position.count * 3) : null, MD = sex === 'Female' ? new Float32Array(m.geometry.attributes.position.count * 3) : null; let mbAny = false;
  const G = m.geometry, P = G.attributes.position, B = boneBind(m.skeleton), v = new THREE.Vector3(), q = new THREE.Vector3();
  const seg = (p, a, b, s, r) => { const ab = q.copy(b).sub(a), t = Math.max(0, Math.min(1, ab.dot(v.copy(p).sub(a)) / ab.lengthSq())), cp = a.clone().addScaledVector(ab, t), d = p.clone().sub(cp), dl = d.length();
    return dl < r ? d.multiplyScalar((s - 1) * (1 - dl / r) ** .5) : d.set(0, 0, 0); };
  const bump = (p, c, rad, push) => { const r2 = p.distanceToSquared(c) / (rad * rad); return Math.exp(-r2 * 2.2) * push; };
  for (let i = 0; i < P.count; i++) {
    const p = new THREE.Vector3().fromBufferAttribute(P, i), add = new THREE.Vector3();
    if (sex === 'Male') {
      for (const s of ['l', 'r']) { add.add(seg(p, B['upperarm_' + s], B['lowerarm_' + s], 1.26, .14)); add.add(seg(p, B['lowerarm_' + s], B['hand_' + s], 1.14, .11)); add.add(seg(p, B['clavicle_' + s], B['upperarm_' + s], 1.12, .16)); }
      add.add(seg(p, B.spine_02, B.neck_01, 1.07, .26)); add.add(seg(p, B.neck_01, B.Head, 1.12, .09));
      if (p.y > 1.3 && p.y < 1.5) add.x += Math.sign(p.x) * .018 * Math.max(0, 1 - Math.abs(p.y - 1.42) / .12) * Math.min(1, Math.abs(p.x) / .15);   // broader shoulders
    } else {
      if (RIBFLAT && BELT && p.z > .02 && Math.abs(p.x) < .17) { const zc = chestAt(p.x, p.y, ZC) + .008; if (p.z > zc) add.z -= (p.z - zc) * .7; }   // Soldier: belts sit snug on the cloth, not standing out like a bump
      if (CHF && p.z > -.02 && Math.abs(p.x) < .2) {                                // chest: the original model's own shape (the Peasant's cups), made fuller in the same place
        const K = window.CH && window.CH.K !== undefined ? window.CH.K : 1.0, f = Math.max(0, Math.min(1, (p.z + .02) / .07));
        add.z += (K * chestAt(p.x, p.y) - (RIBFLAT ? chestAt(p.x, p.y, FLAT) : 0)) * f * f * (3 - 2 * f);   // FLAT: no shelf under the chest (Soldier), the belly stays as it is
        const cw = K * chestAt(p.x, p.y) * f * f * (3 - 2 * f); if (cw > .001) { const u = Math.min(1, cw / .022), sw = u * u * (3 - 2 * u), BW = window.BW || {};
          const cx = Math.sign(p.x || 1) * .058, cy = 1.29;
          // going up: they press in toward the chest and the soft mass spreads out a little (attached all the way round), then a small lift. No flop.
          MB[i * 3 + 2] = -(BW.sink || .32) * cw; MB[i * 3] = (p.x - cx) * (BW.spread || .14) * sw; MB[i * 3 + 1] = (p.y - cy) * (BW.spread || .14) * sw + (BW.lift || .01) * sw;
          // landing: they drop a little and sit out slightly fuller, then settle
          MD[i * 3 + 1] = -(BW.drop || .018) * sw; MD[i * 3 + 2] = (BW.out || .08) * cw; mbAny = true; }   // bounce: the chest moves as one rounded piece (as in a bra), fading only at the edges, so it never goes pointy   // sq: drawn in toward the middle so they sit together
      }
      if (p.y > .95 && p.y < 1.1 && Math.abs(p.x) < .2) { const w = Math.max(0, 1 - Math.abs(p.y - 1.02) / .08); add.x -= p.x * .06 * w; add.z -= (p.z + .01) * .03 * w; }   // waist, below the rib cage only
      const W0 = window.WB || { gx: .064, gy: .94, gz: -.03, gr: .135, gry: .145, grx: .105, gp: .058, gflat: .3, gox: 0, hip: .008, gpow: .6, sh: .08, shy: .012, th: .92, ca: .95, sl: 0, tr: .015, us: .3, ua: 1.45, la: .94 };
      const W = Object.assign({}, W0, WBC || {});
      for (const sx of [-1, 1]) {
        if (p.z < .02 && p.y > .7 && p.y < 1.08 && p.x * sx >= 0) {                               // rear: two round globes meeting in the middle
          const dx = (p.x - sx * W.gx) / (W.grx || W.gr), dy = (p.y - W.gy) / (W.gry || W.gr), r2 = dx * dx + dy * dy;
          if (r2 < 1) { const rr = Math.sqrt(r2), sm = W.gflat !== undefined ? (() => { const t = Math.max(0, Math.min(1, (rr - W.gflat) / (1 - W.gflat))); return 1 - t * t * (3 - 2 * t); })() : (1 - r2) ** W.gpow;   // gflat: broad round back, soft edges (no point)
            const w = sm * Math.min(1, Math.max(0, (W.gz + .05 - p.z) / .05)); add.z -= W.gp * w; add.x += sx * (W.gox !== undefined ? W.gox : .02) * w; }
        }
        if (p.y > .78 && p.y < 1.02 && p.x * sx > .05) add.x += sx * (W.hip !== undefined ? W.hip : .018) * Math.max(0, 1 - Math.abs(p.y - .9) / .12);   // hips a little wider
        const ax = p.x * sx;
        if (ax > .02 && ax < .25 && p.y < .9) {                                                    // legs a touch slimmer (thigh below the hip, calf)
          const T = B['thigh_' + (sx > 0 ? 'l' : 'r')], Cf = B['calf_' + (sx > 0 ? 'l' : 'r')], Ft = B['foot_' + (sx > 0 ? 'l' : 'r')];
          for (const [a0, a1, sc, f0] of [[T, Cf, W.th, .82], [Cf, Ft, W.ca, 1]]) {
            if (p.y > a0.y || p.y < a1.y) continue; const t = (a0.y - p.y) / (a0.y - a1.y);
            const cx = a0.x + (a1.x - a0.x) * t, cz = a0.z + (a1.z - a0.z) * t;
            let k = sc === W.th ? (sc - 1) * Math.min(1, Math.max(0, (t - .15) / .25)) : sc - 1;                // (as before)
            if (sc === W.th) { const rx = p.x - cx, rz = p.z - cz, rl = Math.hypot(rx, rz) || 1, back = Math.max(0, -rz / rl);   // back of the thigh fuller, rising into the cheeks; front unchanged
              const below = Math.min(1, Math.max(0, (.835 - p.y) / .05));   /* only under the butt, so it never stacks on it */
              k += (W.tb !== undefined ? W.tb : .22) * back * back * Math.exp(-(((t - .36) / .17) ** 2)) * below; }
            add.x += (p.x - cx) * k; add.z += (p.z - cz) * k; }
        }
        { const k = sx > 0 ? 'l' : 'r';                                                          // arms: fuller (a bit under the men's), not thin
          const limb = (a, b, sc, r, prof) => { const ab = q.copy(b).sub(a), t0 = ab.dot(v.copy(p).sub(a)) / ab.lengthSq(); if (t0 < -.15 || t0 > 1.1) return;
            const t = Math.max(0, Math.min(1, t0)), c = a.clone().addScaledVector(ab, t), d = p.clone().sub(c), dl = d.length(); if (dl > r) return;
            add.addScaledVector(d, (sc - 1) * prof(t) * (1 - dl / r) ** .5); };
          limb(B['upperarm_' + k], B['lowerarm_' + k], W.ua, .12, t => Math.sin(Math.PI * Math.min(1, (W.us || .15) + t * (1 - (W.us || .15)))) ** .7);   // upper arm: fullest mid-way (shoulder/bicep), tapering to the elbow
          limb(B['lowerarm_' + k], B['hand_' + k], W.la, .09, t => 1 - t * .6); }                                                // forearm: slimmer, tapering to the wrist
        if (ax > .09 && ax < .33 && p.y > 1.32) {                                                  // shoulders: no knob at the top corner; round, and the line slopes into the arm
          const U = B['upperarm_' + (sx > 0 ? 'l' : 'r')], t = ax - Math.abs(U.x), w = Math.exp(-(((t - .02) / .07) ** 2)), ry = p.y - U.y, rz = p.z - U.z, top = ry > 0 ? 1 : .35;
          add.y -= ry * W.sh * w * top + (ry > 0 ? W.shy * w : 0); add.z -= rz * W.sh * .6 * w * top;
        }
        if (ax > .06 && ax < .3 && p.y > 1.36 && p.y < 1.56) {                                      // shoulder line slopes down from the neck to the arm (no flat shelf)
          const u = Math.min(1, (ax - .06) / .13), v = Math.min(1, (p.y - 1.36) / .06); add.y -= (W.sl || 0) * u * u * v;
          add.y += (W.tr || 0) * Math.exp(-(((ax - .115) / .045) ** 2)) * v;   // fill between neck and shoulder: a smooth, slightly full line, no dip
        }
      }
    }
    P.setXYZ(i, p.x + add.x, p.y + add.y, p.z + add.z);
  }
  P.needsUpdate = true; G.computeBoundingSphere();
  if (mbAny) { G.morphAttributes.position = [new THREE.BufferAttribute(MB, 3), new THREE.BufferAttribute(MD, 3)]; G.morphTargetsRelative = true; m.updateMorphTargets(); }
}
async function makeChar(o) {                                  // o: {sex:'Male'|'Female', outfit:'Ranger'|'Peasant'|'Soldier', skin:0..4, hair:'Buzzed'.., hairCol, camo:null|'green'..}
  if (!ANIM) { ANIM = await load('anim/ual1.glb'); ANIM2 = await load('anim/ual2.glb'); }
  const g = new THREE.Group(), scenes = [], sx = o.sex, outfit = o.outfit; 
  const parts = outfit === 'Soldier' ? [sx === 'Female' ? 'parts/Female_Peasant_Arms_Short.gltf' : `parts/${sx}_Peasant_Arms.gltf`, `parts/${sx}_${sx === 'Male' ? 'Peasant' : 'Ranger'}_Body.gltf`, `parts/${sx}_Peasant_Legs.gltf`, sx === 'Male' ? 'parts/Male_Ranger_Feet_Boots_D.gltf' : 'parts/Female_Ranger_Feet_D.gltf', sx === 'Male' ? 'parts/Male_Ranger_Feet_Boots_E.gltf' : 'parts/Female_Ranger_Feet_E.gltf']
    : outfit === 'Ranger' ? ['Arms', 'Body', 'Legs', (sx === 'Male' ? 'Feet_Boots' : 'Feet') + ((window.BOOTV !== undefined ? window.BOOTV : '_C'))].map(p => `parts/${sx}_Ranger_${p}.gltf`).concat(o.hood ? [`parts/${sx}_Ranger_Head_Hood.gltf`] : [])
    : ['Arms', 'Body', 'Legs', 'Feet'].map(p => `parts/${sx}_Peasant_${p}.gltf`);
  WBC = o.wb || null; RIBFLAT = sx === 'Female' && outfit === 'Soldier'; if (sx === 'Female') await chestField(parts[1]);
  const camo = outfit === 'Soldier' ? (o.camo || 'green') : o.camo;
  for (const f of parts) { const s = (await load(f)).scene; scenes.push(s); g.add(s);
    s.traverse(m => { if (!m.isMesh) return; const skin = /Regular|Superhero/.test(m.material.name); if (m.isSkinnedMesh) shape(m, sx);
      const shoe = outfit === 'Soldier' && /Feet/.test(f) && !/_E\./.test(f);   /* Soldier shoes: plain dark leather, no camo */
      if (shoe) m.name = (m.name || 'Feet') + '_Shoe';
      m.material = lamb(m.material, skin || shoe ? null : { camo, leather: outfit === 'Soldier' ? 0x2e2a22 : null }); if (skin) m.material.color.setRGB(...SKIN[o.skin || 0]); if (shoe && !skin) m.material.color.setRGB(.32, .29, .25); }); }
  // the head: the base character's head and neck (same bones), eyes and brows
  const hs = (await load(`base/Superhero_${sx}_FullBody.gltf`)).scene; scenes.push(hs); g.add(hs);
  hs.traverse(m => { if (!m.isSkinnedMesh) return;
    if (/Superhero/.test(m.material.name)) { const G = m.geometry, J = G.attributes.skinIndex, W = G.attributes.skinWeight, names = m.skeleton.bones.map(b => b.name), keep = [], ix = G.index.array;
      const headish = v => { let best = 0, bj = 0; for (let k = 0; k < 4; k++) { const w = W.array[v * 4 + k]; if (w > best) { best = w; bj = J.array[v * 4 + k]; } } return names[bj] === 'Head' || names[bj] === 'neck_01'; };
      for (let t = 0; t < ix.length; t += 3) if (headish(ix[t]) && headish(ix[t + 1]) && headish(ix[t + 2])) keep.push(ix[t], ix[t + 1], ix[t + 2]);
      G.setIndex(keep); if (sx === 'Male') shape(m, sx); }
    const skin = /Superhero/.test(m.material.name); m.material = lamb(m.material); if (skin) m.material.color.setRGB(...SKIN[o.skin || 0]);
    if (/Hair/.test(m.material.name)) m.material.color.copy(hairC(o.hairCol)); });
  if (sx === 'Female' && outfit === 'Soldier') {   // Soldier women: short camo sleeves, bare arms and hands (from the base body)
    const ab = (await load('base/Superhero_Female_FullBody.gltf')).scene; scenes.push(ab); g.add(ab); const rmv = [];
    ab.traverse(m => { if (!m.isSkinnedMesh) return; if (!/Superhero/.test(m.material.name)) { rmv.push(m); return; }
      const G = m.geometry, J = G.attributes.skinIndex, W = G.attributes.skinWeight, P = G.attributes.position, names = m.skeleton.bones.map(b => b.name), keep = [], ix = G.index.array;
      const armish = v => { let best = 0, bj = 0; for (let k = 0; k < 4; k++) { const w = W.array[v * 4 + k]; if (w > best) { best = w; bj = J.array[v * 4 + k]; } } return /upperarm|lowerarm|hand|index|middle|ring|pinky|thumb/.test(names[bj]) && Math.abs(P.getX(v)) > .3; };
      for (let t = 0; t < ix.length; t += 3) if (armish(ix[t]) && armish(ix[t + 1]) && armish(ix[t + 2])) keep.push(ix[t], ix[t + 1], ix[t + 2]);
      G.setIndex(keep); shape(m, sx); m.material = lamb(m.material); m.material.color.setRGB(...SKIN[o.skin || 0]); });
    rmv.forEach(m => m.parent.remove(m)); }
  if (o.hair && !(outfit === 'Ranger' && o.hood)) { const hr = (await load(`hair/Hair_${o.hair}.gltf`)).scene; scenes.push(hr); g.add(hr);
    hr.traverse(m => { if (m.isMesh) { m.material = lamb(m.material); m.material.color.copy(hairC(o.hairCol)); } }); }
  if (o.beard) { const br = (await load('hair/Hair_Beard.gltf')).scene; scenes.push(br); g.add(br); br.traverse(m => { if (m.isMesh) { m.material = lamb(m.material); m.material.color.copy(hairC(o.hairCol)); } }); }
  // pose: the same animation on every piece (they share bone names)
  const clip = findClip(o.clip || 'Idle_Loop'); g.userData.mx = []; g.userData.sex = sx; g.userData.morphs = [];
  for (const s of scenes) s.traverse(m => { if (m.morphTargetInfluences) g.userData.morphs.push(m); });
  if (o.clip !== 'none') for (const s of scenes) { const mx = new THREE.AnimationMixer(s); g.userData.mx.push(mx); const a = mx.clipAction(clip); a.play(); mx.update(o.t || .3); }
  if (false) {   // (no helmets: Ron)                     // a simple helmet on the head bone, in the camo
    let head = null; hs.traverse(b => { if (b.isBone && b.name === 'Head') head = b; });
    const hm = new THREE.Mesh(new THREE.SphereGeometry(.128, 14, 8, 0, Math.PI * 2, 0, Math.PI * .5), lamb({ color: new THREE.Color(0xffffff) }, null));
    hm.material.color.set(CAMO[camo || 'green'][1]).convertSRGBToLinear(); const rim = new THREE.Mesh(new THREE.TorusGeometry(.128, .012, 6, 20), hm.material); rim.rotation.x = Math.PI / 2; hm.add(rim);
    hs.updateMatrixWorld(true); const hq = head.getWorldQuaternion(new THREE.Quaternion()).invert(); hm.quaternion.copy(hq);
    hm.position.set(0, .115, -.005).applyQuaternion(hq); hm.scale.set(1.04, .86, 1.12); hm.userData.helmet = true; head.add(hm);
  }
  return g;
}
window.makeChar = makeChar;
const CLIPS = {};
function findClip(n) {   // in place: drop the forward travel baked into the root (the game moves the player itself)
  if (CLIPS[n]) return CLIPS[n]; const c0 = ANIM.animations.find(c => c.name === n) || ANIM2.animations.find(c => c.name === n); if (!c0) return null;
  const c = c0.clone(); for (const tr of c.tracks) if (/^(root|pelvis)\.position$/.test(tr.name)) { const v = tr.values, x0 = v[0], z0 = v[2], keepY = /pelvis/.test(tr.name);
    for (let k = 0; k < v.length; k += 3) { v[k] = /root/.test(tr.name) ? x0 : v[k] - (v[v.length - 3] - x0) * (k / (v.length - 3)) * 0; v[k + 2] = /root/.test(tr.name) ? z0 : v[k + 2]; if (!keepY && /root/.test(tr.name)) v[k + 1] = v[1]; } }
  return CLIPS[n] = c; }
// play an animation on a character at time t. Women: a slight chest bounce at the tempo of the steps while jogging/running (2 steps per loop)
function rotWorld(g, bname, axisW, ang) {   // turn a bone (on every piece of the character) about a world axis
  const qd = new THREE.Quaternion().setFromAxisAngle(axisW, ang);
  for (const sc of g.children) sc.traverse(b => { if (!b.isBone || b.name !== bname) return; b.parent.updateMatrixWorld(true);
    const pq = b.parent.getWorldQuaternion(new THREE.Quaternion()), pqi = pq.clone().invert(); b.quaternion.premultiply(pqi.clone().multiply(qd).multiply(pq)); b.updateMatrixWorld(true); });
}
function flyPose(g, F) {   // gliding: laid out flat like Peter Pan, arms out like wings, legs straight back, head up looking ahead
  F = Object.assign({ tilt: 1.3, head: .55, neck: .45, knee: .3, thigh: .08, foot: .6, armBack: .25, armDown: .1 }, window.FLY || {}, F || {});
  g.rotation.order = 'YXZ'; g.rotation.x = F.tilt; g.position.y = g.userData.y0 + 1.0; g.updateMatrixWorld(true);
  const right = new THREE.Vector3(1, 0, 0).applyQuaternion(g.getWorldQuaternion(new THREE.Quaternion())), fwd = new THREE.Vector3(0, 0, 1).applyQuaternion(g.getWorldQuaternion(new THREE.Quaternion()));
  rotWorld(g, 'neck_01', right, -F.neck); rotWorld(g, 'Head', right, -F.head);
  for (const sd of ['l', 'r']) { rotWorld(g, 'thigh_' + sd, right, -F.thigh); rotWorld(g, 'calf_' + sd, right, F.knee); rotWorld(g, 'foot_' + sd, right, F.foot);
    const sgn = sd === 'l' ? 1 : -1; rotWorld(g, 'upperarm_' + sd, new THREE.Vector3(0, 1, 0).applyQuaternion(g.getWorldQuaternion(new THREE.Quaternion())), sgn * F.armBack); rotWorld(g, 'upperarm_' + sd, fwd, sgn * F.armDown); }
}
function poseAt(g, name, t, opts = {}) {
  if (g.userData.y0 === undefined) g.userData.y0 = g.position.y;
  if (g.userData.yaw0 === undefined || opts.resetYaw) g.userData.yaw0 = g.rotation.y;
  g.rotation.y = g.userData.yaw0;
  // deaths: the body turns as it drops so it falls the way the bullet was going (from = where the shot came from, degrees: 0 front, 90 her left side, 180 behind)
  const dying = name === 'Death01' || name === 'HeadDeath';
  if (dying && opts.from) { const tw = Math.max(0, Math.min(1, (t - .05) / .4)); g.rotation.y = g.userData.yaw0 + opts.from * Math.PI / 180 * tw * tw * (3 - 2 * tw); }
  if (name === 'Fly') { poseAt(g, 'A_TPose', 0); flyPose(g, opts.fly); return; }
  if (name === 'HeadDeath') {   // killed by a headshot: the head snaps back, then the body drops
    g.rotation.x = 0; g.position.y = g.userData.y0; const h = findClip('Hit_Head'), d = findClip('Death01'), T = window.HD || { snap: .22, blend: .25 };
    const w = Math.max(0, Math.min(1, (t - T.snap) / T.blend)), ws = w * w * (3 - 2 * w);
    for (const mx of g.userData.mx) { mx.stopAllAction(); const a1 = mx.clipAction(h), a2 = mx.clipAction(d);
      for (const [a, wt, tm] of [[a1, 1 - ws, Math.min(t, h.duration - .001)], [a2, ws, Math.min(Math.max(0, t - T.snap) * 1.25 + (t > T.snap ? .25 : 0), d.duration - .001)]]) { a.reset(); a.setLoop(THREE.LoopOnce); a.clampWhenFinished = true; a.play(); a.setEffectiveWeight(wt); a.time = tm; }
      mx.update(0); }
    const sn = Math.min(1, t / .07) * Math.max(0, 1 - Math.max(0, t - .12) / .5);   /* sharp snap of the head back, easing out as the body drops */
    if (sn > 0) { g.updateMatrixWorld(true);   // the head snaps the way the bullet was going
      const a = (opts.from || 0) * Math.PI / 180, travel = new THREE.Vector3(-Math.sin(a), 0, -Math.cos(a)).applyAxisAngle(new THREE.Vector3(0, 1, 0), g.userData.yaw0);
      const ax = new THREE.Vector3(0, 1, 0).cross(travel).normalize(); rotWorld(g, 'neck_01', ax, .35 * sn); rotWorld(g, 'Head', ax, .45 * sn); rotWorld(g, 'spine_03', ax, .12 * sn); }
    return; }
  g.rotation.x = 0; g.position.y = g.userData.y0;
  const clip = findClip(name); if (!clip) throw new Error('no clip ' + name);
  const tt = opts.hold ? Math.min(t, clip.duration - .001) : t % clip.duration;
  for (const mx of g.userData.mx) { mx.stopAllAction(); const a = mx.clipAction(clip); a.reset(); a.setLoop(opts.hold ? THREE.LoopOnce : THREE.LoopRepeat); a.clampWhenFinished = true; a.play(); mx.setTime(tt); }
  if (g.userData.sex !== 'Female' || !g.userData.morphs.length) return;
  // bounce with follow-through: a soft spring driven by the body's own up/down motion (none when still, more at a sprint), then settles
  const U = g.userData; if (!U.spine) for (const sc of g.children) sc.traverse(b => { if (!U.spine && b.isBone && b.name === 'spine_03') U.spine = b; });
  g.updateMatrixWorld(true); const y = U.spine.getWorldPosition(new THREE.Vector3()).y, dt = opts.dt || 1 / 30;
  if (U.bClip !== name) { U.bClip = name; U.bm = y; U.bx = 0; U.bv = 0; }
  U.bm += (y - U.bm) * Math.min(1, dt / .45);                                    // the body's average height
  const tgt = (y - U.bm) * (window.BG || .17);                                     // up while the body rises between steps, down when the foot lands
  const k = (2 * Math.PI * 5.5) ** 2, c = 2 * .55 * Math.sqrt(k);                 // follows a moment later, then settles
  for (let sub = 0; sub < 6; sub++) { const h = dt / 6, a2 = -k * (U.bx - tgt) - c * U.bv; U.bv += a2 * h; U.bx += U.bv * h; }
  const v = window.FORCEB !== undefined ? window.FORCEB : Math.max(-1.3, Math.min(1.5, U.bx / .01));
  for (const m of U.morphs) { m.morphTargetInfluences[0] = Math.max(0, v); m.morphTargetInfluences[1] = Math.max(0, -v); }
}
window.animFrames = async (list, anims, W, H, fps, yaw, camZ, cy, ly, fv) => {
  if (!window.__R) { window.__R = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true }); }
  const R = window.__R; R.setSize(W, H); R.toneMapping = THREE.ACESFilmicToneMapping; R.outputEncoding = THREE.sRGBEncoding;
  const sc = new THREE.Scene(); sc.background = new THREE.Color(0x9fb7c9);
  sc.add(new THREE.HemisphereLight(0xdfeeff, 0x4a5a3a, 1.0)); const d = new THREE.DirectionalLight(0xfff2dd, 1.5); d.position.set(2, 4, 5); sc.add(d);
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshLambertMaterial({ color: 0x5f7a45 })); ground.rotation.x = -Math.PI / 2; sc.add(ground);
  const n = list.length, sp = window.SP || 1.0, chars = [];
  for (let i = 0; i < n; i++) { const c = await makeChar(list[i]); c.position.x = (i - (n - 1) / 2) * sp; c.rotation.y = list[i].yaw !== undefined ? list[i].yaw : (yaw || 0); sc.add(c); chars.push(c); }
  const cam = new THREE.PerspectiveCamera(fv || 30, W / H, .05, 100); cam.position.set(0, cy || 1.0, camZ); cam.lookAt(0, ly || .9, 0);
  const out = [];
  for (const A of anims) { const nF = Math.round(A.secs * fps);
    for (let f = 0; f < nF; f++) { const t = (A.t0 || 0) + f / fps * (A.speed || 1);
      chars.forEach((c, ci) => { c.userData.yaw0 = (list[ci].yaw !== undefined ? list[ci].yaw : (yaw || 0)) + (A.spin ? A.spin * f / fps : 0); });
      chars.forEach((c, ci) => poseAt(c, A.clip, A.still !== undefined ? A.still : t, { hold: !!A.once, dt: (A.speed || 1) / fps, from: A.from ? A.from[ci] : 0 }));
      R.render(sc, cam); out.push(R.domElement.toDataURL('image/jpeg', .85)); } }
  return out;
};
window.shot2 = async (list, W, H, yaw, camZ, cy, ly, fv) => {
  const R = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true }); R.setSize(W, H); R.toneMapping = THREE.ACESFilmicToneMapping; R.outputEncoding = THREE.sRGBEncoding;
  const sc = new THREE.Scene(); sc.background = new THREE.Color(0x9fb7c9);
  sc.add(new THREE.HemisphereLight(0xdfeeff, 0x4a5a3a, 1.0)); const d = new THREE.DirectionalLight(0xfff2dd, 1.5); d.position.set(2, 4, 5); sc.add(d);
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshLambertMaterial({ color: 0x5f7a45 })); ground.rotation.x = -Math.PI / 2; sc.add(ground);
  const n = list.length, sp = window.SP || 1.0;
  for (let i = 0; i < n; i++) { const c = await makeChar(list[i]); c.position.x = (i - (n - 1) / 2) * sp; c.rotation.y = list[i].yaw !== undefined ? list[i].yaw : (yaw || 0); sc.add(c); }
  const cam = new THREE.PerspectiveCamera(fv || 30, W / H, .05, 100); cam.position.set(0, cy || 1.0, camZ || (n * 1.15 + 1.5)); cam.lookAt(0, ly || .9, 0);
  R.render(sc, cam); const u = R.domElement.toDataURL('image/jpeg', .9); R.dispose(); return u;
};
0;
