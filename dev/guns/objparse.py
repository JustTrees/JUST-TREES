import zipfile, re, json, sys, os
Z = zipfile.ZipFile(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'models', 'source', 'Ultimate_Gun_Pack_by_Quaternius.zip'))
def load(name):
    obj = [x for x in Z.namelist() if x.endswith('/' + name + '.obj')][0]
    t = Z.read(obj).decode('utf8', 'replace')
    mtlf = re.search(r'^mtllib (.+)$', t, re.M); kd = {}
    if mtlf:
        mp = obj.rsplit('/', 1)[0] + '/' + mtlf.group(1).strip()
        if mp in Z.namelist():
            cur = None
            for line in Z.read(mp).decode('utf8', 'replace').splitlines():
                p = line.split()
                if not p: continue
                if p[0] == 'newmtl': cur = p[1]
                elif p[0] == 'Kd' and cur: kd[cur] = [float(v) for v in p[1:4]]
    V = []; tris = []; mat = None
    for line in t.splitlines():
        p = line.split()
        if not p: continue
        if p[0] == 'v': V.append([float(v) for v in p[1:4]])
        elif p[0] == 'usemtl': mat = p[1]
        elif p[0] == 'f':
            idx = [int(q.split('/')[0]) - 1 for q in p[1:]]
            for k in range(1, len(idx) - 1): tris.append((idx[0], idx[k], idx[k + 1], mat))
    return V, tris, kd
if __name__ == '__main__':
    out = {}
    for n in sys.argv[2:]:
        V, tris, kd = load(n)
        pos = []; col = []; mats = []
        for a, b, c, m in tris:
            for i in (a, b, c): pos += V[i]
            col += (kd.get(m, [.5, .5, .5])) * 3; mats.append(m)
        xs = [v[0] for v in V]; ys = [v[1] for v in V]; zs = [v[2] for v in V]
        out[n] = {'pos': pos, 'col': col, 'mats': mats, 'bb': [min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)], 'kd': kd}
    json.dump(out, open(sys.argv[1], 'w'))
