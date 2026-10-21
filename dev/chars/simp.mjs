import { NodeIO } from '@gltf-transform/core'; import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, prune, weld, simplify } from '@gltf-transform/functions'; import { MeshoptSimplifier } from 'meshoptimizer'; import fs from 'fs';
const [,, inDir, outDir, ratio] = process.argv; fs.mkdirSync(outDir, { recursive: true }); const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
await MeshoptSimplifier.ready;
for (const f of fs.readdirSync(inDir).filter(f => f.endsWith('.glb'))) {
  const doc = await io.read(`${inDir}/${f}`);
  for (const mesh of doc.getRoot().listMeshes()) for (const prim of mesh.listPrimitives())
    for (const sem of prim.listSemantics()) if (/^COLOR_|^TEXCOORD_[1-9]/.test(sem)) prim.setAttribute(sem, null);
  const ops = [dedup(), prune()];
  if (f.startsWith('char_') || f.startsWith('hair_')) ops.push(weld({}), simplify({ simplifier: MeshoptSimplifier, ratio: +ratio, error: .0015 }));
  ops.push(prune());
  await doc.transform(...ops);
  let v = 0, t = 0; for (const m of doc.getRoot().listMeshes()) for (const p of m.listPrimitives()) { v += p.getAttribute('POSITION').getCount(); t += (p.getIndices() ? p.getIndices().getCount() : 0) / 3; }
  await io.write(`${outDir}/${f}`, doc); console.log(f, 'verts', v, 'tris', t);
}
