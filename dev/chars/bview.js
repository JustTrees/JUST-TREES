// load the baked (game-ready) characters the way the game will
window.useBaked = async () => { const A = await load('baked_opt/anims.glb'); ANIM = A; ANIM2 = A; };
makeChar = async function (o) {
  const sx = o.sex, outfit = o.outfit, camo = outfit === 'Soldier' ? (o.camo || 'green') : o.camo;
  const g = new THREE.Group(), root = (await load(`baked_opt/char_${sx}_${outfit}.glb`)).scene; g.add(root);
  // one skeleton for every piece (they share bone names)
  let main = null; root.traverse(m => { if (m.isSkinnedMesh && !main) main = m.skeleton; });
  const mainRoot = (() => { let b = main.bones[0]; while (b.parent && b.parent.isBone) b = b.parent; return b; })();
  const byName = {}; mainRoot.traverse(b => { if (b.isBone) byName[b.name] = b; });   // the whole skeleton, not just the bones one piece uses
  const meshes = []; root.traverse(m => { if (m.isMesh) meshes.push(m); });
  for (const m of meshes) {
    if (m.isSkinnedMesh && m.skeleton !== main) m.bind(new THREE.Skeleton(m.skeleton.bones.map(b => byName[b.name.replace(/_\d+$/, '')] && b.name !== b.name.replace(/_\d+$/, '') && byName[b.name] === undefined ? byName[b.name.replace(/_\d+$/, '')] : (byName[b.name] || b)), m.skeleton.boneInverses), m.bindMatrix);
    const n = m.material.name || '', skin = /Regular|Superhero/.test(n), shoe = /_Shoe/.test(m.name);
    m.material = lamb(m.material, skin || shoe || /Eye|Hair/.test(n) ? null : { camo, leather: outfit === 'Soldier' ? 0x2e2a22 : null }); m.material.name = n; if (shoe) m.material.color.setRGB(.32, .29, .25);
    if (skin) m.material.color.setRGB(...SKIN[o.skin || 0]); if (/Hair/.test(n)) m.material.color.copy(hairC(o.hairCol)); m.frustumCulled = false;
  }
  // keep only the one skeleton: take the spare armatures out, so the animation drives the bones everything is bound to
  const spare = []; root.traverse(b => { if (b.isBone && b !== mainRoot && !(b.parent && b.parent.isBone)) spare.push(b); });
  spare.forEach(b => b.parent.remove(b));
  for (const h of [o.hair && !(outfit === 'Ranger' && o.hood) ? o.hair : null, o.beard ? 'Beard' : null].filter(Boolean)) {
    const hr = (await load(`baked_opt/hair_${h}.glb`)).scene; hr.traverse(m => { if (m.isMesh) { const n = m.material.name; m.userData.noHit = true;   /* hair and beards don't count as hits */ m.material = lamb(m.material); m.material.color.copy(hairC(o.hairCol)); m.frustumCulled = false;
      if (m.isSkinnedMesh) m.bind(new THREE.Skeleton(m.skeleton.bones.map(b => byName[b.name] || b), m.skeleton.boneInverses), m.bindMatrix); } });
    const sp2 = []; hr.traverse(b => { if (b.isBone && !(b.parent && b.parent.isBone)) sp2.push(b); }); sp2.forEach(b => b.parent.remove(b));
    root.add(hr); }
  g.userData.mx = []; g.userData.sex = sx; g.userData.morphs = [];
  root.traverse(m => { if (m.morphTargetInfluences && m.morphTargetInfluences.length) g.userData.morphs.push(m); });
  if (o.clip !== 'none') { const mx = new THREE.AnimationMixer(root); g.userData.mx.push(mx); const a = mx.clipAction(findClip(o.clip || 'Idle_Loop')); a.play(); mx.update(o.t || .3); }
  return g;
};
0;
