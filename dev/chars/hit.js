// exact hits on an avatar: a shot counts only if it touches the visible body or clothes, as posed right now (hair and beards don't count).
// Quick pre-check per body part (a box that moves with each bone), then exact triangles for the parts the shot passes near.
const HIT_HEAD = /^(Head|neck_01)$/;
function prepHit(g) {
  const parts = [];
  g.traverse(m => {
    if (!m.isSkinnedMesh || m.userData.noHit || !m.geometry.index) return;
    const G = m.geometry, P = G.attributes.position, J = G.attributes.skinIndex, W = G.attributes.skinWeight, ix = G.index.array, sk = m.skeleton;
    const gc = (A, v, k) => k === 0 ? A.getX(v) : k === 1 ? A.getY(v) : k === 2 ? A.getZ(v) : A.getW(v);
    const dom = v => { let best = -1, bj = 0; for (let k = 0; k < 4; k++) { const w = gc(W, v, k); if (w > best) { best = w; bj = gc(J, v, k); } } return bj; };
    const groups = new Map();
    for (let t = 0; t < ix.length; t += 3) { const a = ix[t], b = ix[t + 1], c = ix[t + 2]; const ba = dom(a), bb = dom(b), bc = dom(c); const bj = ba === bb || ba === bc ? ba : bb === bc ? bb : ba;
      if (!groups.has(bj)) groups.set(bj, []); groups.get(bj).push(a, b, c); }
    const v = new THREE.Vector3();
    for (const [bj, tris] of groups) {
      const M = new THREE.Matrix4().multiplyMatrices(sk.boneInverses[bj], m.bindMatrix), box = new THREE.Box3();
      for (const i of tris) box.expandByPoint(v.fromBufferAttribute(P, i).applyMatrix4(M));
      box.expandByScalar(.04);   // room for the other bones that pull on these points
      parts.push({ m, bone: sk.bones[bj], name: sk.bones[bj].name, head: HIT_HEAD.test(sk.bones[bj].name), tris: Uint32Array.from(tris), box });
    }
  });
  g.userData.hit = parts; return parts.length;
}
const _hM = new THREE.Matrix4(), _hR = new THREE.Ray(), _hA = new THREE.Vector3(), _hB = new THREE.Vector3(), _hC = new THREE.Vector3(), _hP = new THREE.Vector3();
function avatarHit(g, origin, dir, maxT = 1e9) {   // the nearest point a shot touches on this avatar, or null. {t, head, part}
  const parts = g.userData.hit || (prepHit(g), g.userData.hit); g.updateMatrixWorld(true);
  let best = null; const cache = new Map();
  const skinned = (m, i, out) => { const key = m.id * 1e6 + i; let p = cache.get(key); if (!p) { const b0 = new THREE.Vector3().fromBufferAttribute(m.geometry.attributes.position, i), MA = m.geometry.morphAttributes.position, MI = m.morphTargetInfluences;
          if (MA && MI) for (let k = 0; k < MA.length; k++) if (MI[k]) b0.x += MA[k].getX(i) * MI[k], b0.y += MA[k].getY(i) * MI[k], b0.z += MA[k].getZ(i) * MI[k];   // include the bounce
          p = m.boneTransform(i, b0).applyMatrix4(m.matrixWorld); cache.set(key, p); } return out.copy(p); };
  for (const pt of parts) {
    // pre-check: the shot in this bone's own space against its box
    _hM.copy(pt.m.matrixWorld).multiply(pt.m.bindMatrixInverse).multiply(pt.bone.matrixWorld).invert();
    _hR.set(origin, dir).applyMatrix4(_hM); if (!_hR.intersectsBox(pt.box)) continue;
    _hR.set(origin, dir);
    for (let k = 0; k < pt.tris.length; k += 3) {
      skinned(pt.m, pt.tris[k], _hA); skinned(pt.m, pt.tris[k + 1], _hB); skinned(pt.m, pt.tris[k + 2], _hC);
      if (!_hR.intersectTriangle(_hA, _hB, _hC, false, _hP)) continue;
      const t = _hP.distanceTo(origin); if (t < maxT && (!best || t < best.t)) best = { t, head: pt.head, part: pt.name };
    }
  }
  return best;
}
window.hitDemo = async (list, W, H, step, cz, cy, ly, fv) => {   // render the characters, then fire a grid of shots from the camera and report what each hits
  const R = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true }); R.setSize(W, H); R.toneMapping = THREE.ACESFilmicToneMapping; R.outputEncoding = THREE.sRGBEncoding;
  const sc = new THREE.Scene(); sc.background = new THREE.Color(0x9fb7c9); sc.add(new THREE.HemisphereLight(0xdfeeff, 0x4a5a3a, 1.0)); const d = new THREE.DirectionalLight(0xfff2dd, 1.5); d.position.set(2, 4, 5); sc.add(d);
  const n = list.length, sp = window.SP || 1, chars = [];
  for (let i = 0; i < n; i++) { const c = await makeChar(list[i]); c.position.x = (i - (n - 1) / 2) * sp; c.rotation.y = list[i].yaw || 0; sc.add(c); chars.push(c);
    if (list[i].pose) poseAt(c, list[i].pose, list[i].pt || .3, { dt: 1 / 30 }); }
  const cam = new THREE.PerspectiveCamera(fv || 30, W / H, .05, 100); cam.position.set(0, cy || 1, cz); cam.lookAt(0, ly || .9, 0); cam.updateMatrixWorld();
  R.render(sc, cam); const img = R.domElement.toDataURL('image/jpeg', .9);
  for (const c of chars) prepHit(c);
  const rc = new THREE.Raycaster(), out = []; let shots = 0; const t0 = performance.now();
  for (let y = step / 2; y < H; y += step) for (let x = step / 2; x < W; x += step) {
    rc.setFromCamera({ x: x / W * 2 - 1, y: -(y / H * 2 - 1) }, cam); shots++;
    let best = null; for (const c of chars) { const h = avatarHit(c, rc.ray.origin, rc.ray.direction); if (h && (!best || h.t < best.t)) best = h; }
    if (best) out.push([x, y, best.head ? 1 : 0]);
  }
  const ms = (performance.now() - t0) / shots / n;
  return { img, out, ms, parts: chars.map(c => c.userData.hit.length) };
};
