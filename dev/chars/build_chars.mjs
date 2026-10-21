// Packs the baked characters into the game's own small format (models/chars/*.bin) + shared textures (models/chars/tex_*.jpg).
// Input: baked_s/*.glb (body shapes already applied, simplified). Same idea as dev/dinos/exp.py.
import { NodeIO } from '@gltf-transform/core'; import { ALL_EXTENSIONS } from '@gltf-transform/extensions'; import sharp from 'sharp'; import fs from 'fs';
const [,, inDir, outDir, srcDir] = process.argv; fs.mkdirSync(outDir, { recursive: true });
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const TEX = { MI_Peasant: 'outfits/T_Peasant_BaseColor.png', MI_Ranger: 'outfits/T_Ranger_BaseColor.png', MI_Regular_Male: 'outfits/T_Regular_Male_Dark_BaseColor.png',
  MI_Regular_Female: 'outfits/T_Regular_Female_Dark_BaseColor.png', MI_Superhero_Male: 'base/T_Superhero_Male_Dark.png', MI_Superhero_Female: 'base/T_Superhero_Female_Dark_BaseColor.png',
  MI_Eyes: 'base/T_Eye_Brown.png', MI_Hair_1: 'hair/T_Hair_1_BaseColor.png', MI_Hair_2: 'hair/T_Hair_2_BaseColor.png' };
const texKey = m => m.replace(/^MI_/, '').toLowerCase();
for (const [m, p] of Object.entries(TEX)) await sharp(`${srcDir}/${p}`).resize(512, 512).flatten({ background: '#808080' }).jpeg({ quality: 82 }).toFile(`${outDir}/tex_${texKey(m)}.jpg`);
class W { constructor() { this.parts = []; this.n = 0; } add(arr) { const pad = (4 - this.n % 4) % 4; if (pad) { this.parts.push(new Uint8Array(pad)); this.n += pad; } const o = this.n; const b = new Uint8Array(arr.buffer, arr.byteOffset, arr.byteLength); this.parts.push(b); this.n += b.length; return o; } }
function write(file, json, w) {
  const js = new TextEncoder().encode(JSON.stringify(json)), jl = js.length + (4 - js.length % 4) % 4, head = new Uint8Array(8 + jl).fill(32);
  const dv = new DataView(head.buffer); head.set([74, 84, 67, 49]); dv.setUint32(4, jl, true); head.set(js, 8);
  const out = new Uint8Array(head.length + w.n); out.set(head); let o = head.length; for (const p of w.parts) { out.set(p, o); o += p.length; } fs.writeFileSync(file, out); return out.length;
}
const outName = f => f.replace('char_', '').replace('Male_', 'M_').replace('Female_', 'F_').replace('Soldier', 'S').replace('Ranger', 'R').replace('Peasant', 'P').replace('.glb', '.bin');
for (const f of fs.readdirSync(inDir).filter(f => f.endsWith('.glb'))) {
  const doc = await io.read(`${inDir}/${f}`), root = doc.getRoot(), w = new W();
  if (f === 'anims.glb') {   // the moves: bone rotations (all bones), pelvis position; times in seconds
    const clips = [];
    for (const an of root.listAnimations()) { const tr = [];
      for (const ch of an.listChannels()) { const node = ch.getTargetNode(), path = ch.getTargetPath(), s = ch.getSampler(), name = node.getName();
        if (path === 'scale' || (path === 'translation' && name !== 'pelvis')) continue;
        const t = s.getInput().getArray(), v = s.getOutput().getArray();
        if (path === 'rotation') { const q = new Int16Array(v.length); for (let i = 0; i < v.length; i++) q[i] = Math.round(Math.max(-1, Math.min(1, v[i])) * 32767); tr.push({ b: name, p: 'q', nk: t.length, t: w.add(new Float32Array(t)), v: w.add(q) }); }
        else tr.push({ b: name, p: 'p', nk: t.length, t: w.add(new Float32Array(t)), v: w.add(new Float32Array(v)) }); }
      clips.push({ n: an.getName(), d: Math.max(...an.listSamplers().map(s => { const a = s.getInput().getArray(); return a[a.length - 1]; })), tr }); }
    console.log(f, write(`${outDir}/anims.bin`, { clips }, w), 'bytes'); continue;
  }
  // one shared skeleton (every piece uses the same bones)
  const skins = root.listSkins(), J0 = skins[0].listJoints(), names = J0.map(j => j.getName()), idx = Object.fromEntries(names.map((n, i) => [n, i]));
  const bones = J0.map(j => ({ n: j.getName(), p: J0.indexOf(j.getParentNode()), t: j.getTranslation(), r: j.getRotation(), s: j.getScale() }));
  const ibm = Array.from(skins[0].getInverseBindMatrices().getArray());
  const meshes = [];
  for (const node of root.listNodes()) { const mesh = node.getMesh(), skin = node.getSkin(); if (!mesh || !skin) continue;
    const map = skin.listJoints().map(j => idx[j.getName()]);
    for (const prim of mesh.listPrimitives()) {
      const P = prim.getAttribute('POSITION').getArray(), N = prim.getAttribute('NORMAL').getArray(), UV = prim.getAttribute('TEXCOORD_0').getArray(), JJ = prim.getAttribute('JOINTS_0'), WW = prim.getAttribute('WEIGHTS_0');
      const n = P.length / 3, mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]; for (let i = 0; i < n * 3; i++) { const a = i % 3; mn[a] = Math.min(mn[a], P[i]); mx[a] = Math.max(mx[a], P[i]); }
      const pq = new Int16Array(n * 3); for (let i = 0; i < n * 3; i++) { const a = i % 3; pq[i] = Math.round((P[i] - mn[a]) / Math.max(1e-6, mx[a] - mn[a]) * 65535 - 32768); }
      const nq = new Int8Array(n * 4); for (let i = 0; i < n; i++) for (let a = 0; a < 3; a++) nq[i * 4 + a] = Math.round(N[i * 3 + a] * 127);
      const ji = new Uint8Array(n * 4), jw = new Uint8Array(n * 4), e = [0, 0, 0, 0];
      for (let i = 0; i < n; i++) { JJ.getElement(i, e); for (let k = 0; k < 4; k++) ji[i * 4 + k] = map[e[k]] || 0; WW.getElement(i, e); let s = 0; for (let k = 0; k < 4; k++) s += e[k];
        let acc = 0; for (let k = 0; k < 4; k++) { const v = k < 3 ? Math.round(e[k] / s * 255) : 255 - acc; jw[i * 4 + k] = Math.max(0, v); acc += k < 3 ? Math.round(e[k] / s * 255) : 0; } }
      const I = prim.getIndices().getArray(), ix = n < 65536 ? new Uint16Array(I) : new Uint32Array(I);
      const mat = prim.getMaterial() ? prim.getMaterial().getName() : '', nm = node.getName();
      const kind = /_Shoe/.test(nm) ? 'shoe' : /Regular|Superhero/.test(mat) ? 'skin' : /Eyes/.test(mat) ? 'eye' : /Hair/.test(mat) ? 'hair' : 'cloth';
      const M = { name: nm, kind, tex: texKey(mat), n, ni: I.length, bb: [mn, mx], pos: w.add(pq), nrm: w.add(nq), uv: w.add(new Float32Array(UV)), ji: w.add(ji), jw: w.add(jw), ix: w.add(ix), i32: n >= 65536 ? 1 : 0 };
      const T = prim.listTargets();   // the bounce: two shapes (up, landing), stored to 0.1 mm
      if (T.length) M.morph = T.map(t => { const d = t.getAttribute('POSITION').getArray(), q = new Int16Array(d.length); for (let i = 0; i < d.length; i++) q[i] = Math.round(d[i] * 1e4); return w.add(q); });
      meshes.push(M);
    } }
  console.log(f, meshes.length, 'meshes', write(`${outDir}/${outName(f)}`, { bones, ibm, meshes }, w), 'bytes');
}
