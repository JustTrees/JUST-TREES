import sys, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from objparse import load
def islands(name):
    V, tris, kd = load(name)
    par = list(range(len(V)))
    def f(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    # weld by exact position too (OBJ may duplicate verts)
    pos = {}
    for i, v in enumerate(V):
        k = tuple(round(c, 5) for c in v)
        if k in pos: par[f(i)] = f(pos[k])
        else: pos[k] = i
    for a, b, c, m in tris: par[f(b)] = f(a); par[f(c)] = f(a)
    groups = {}
    for ti, (a, b, c, m) in enumerate(tris): groups.setdefault(f(a), []).append(ti)
    out = []
    for r, tl in groups.items():
        vs = [V[i] for ti in tl for i in tris[ti][:3]]; mats = sorted(set(tris[ti][3] for ti in tl))
        xs = [v[0] for v in vs]; ys = [v[1] for v in vs]; zs = [v[2] for v in vs]
        out.append({'n': len(tl), 'bb': [round(min(xs), 2), round(max(xs), 2), round(min(ys), 2), round(max(ys), 2), round(min(zs), 2), round(max(zs), 2)], 'mats': mats, 'tris': tl})
    out.sort(key=lambda o: -o['n']); return out, V, tris, kd
if __name__ == '__main__':
    for n in sys.argv[2:]:
        out, V, tris, kd = islands(n)
        print(n, len(tris), 'tris', len(out), 'islands')
        for i, o in enumerate(out):
            if o['n'] >= 6: print('  ', i, o['n'], o['bb'], o['mats'])
