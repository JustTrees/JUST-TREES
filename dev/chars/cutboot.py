import json,struct,numpy as np,sys,shutil,os
src, dst, drop = sys.argv[1], sys.argv[2], set(int(x) for x in sys.argv[3].split(','))
g=json.load(open(src)); d=os.path.dirname(src)
def acc(i):
    a=g['accessors'][i]; bv=g['bufferViews'][a['bufferView']]; buf=open(os.path.join(d,g['buffers'][bv['buffer']]['uri']),'rb').read()
    o=bv.get('byteOffset',0)+a.get('byteOffset',0); n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]; dt={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]
    x=np.frombuffer(buf,dtype=dt,count=a['count']*n,offset=o); return x.reshape(a['count'],n) if n>1 else x
p=g['meshes'][0]['primitives'][0]; P=acc(p['attributes']['POSITION']); I=acc(p['indices']).reshape(-1,3)
par=list(range(len(P)))
def fd(x):
    while par[x]!=x: par[x]=par[par[x]]; x=par[x]
    return x
key={}
for i,v in enumerate(np.round(P,4)):
    k=tuple(v)
    if k in key: par[fd(i)]=fd(key[k])
    else: key[k]=i
for a,b,c in I: ra=fd(a); par[fd(b)]=ra; par[fd(c)]=fd(a)
comp={}
for i in range(len(P)): comp.setdefault(fd(i),[]).append(i)
size={r:len(v) for r,v in comp.items()}
# drop = component sizes to remove; 390 etc
lo={r:P[v][:,1].min() for r,v in comp.items()}
if os.environ.get('LOW'):   # keep only the shoe: drop every piece that starts above the ankle (and, with TOPY, anything above that height)
    ty=float(os.environ.get('TOPY','9'))
    above=os.environ.get('ABOVE')
    keep=np.array([lo[fd(t[0])] < float(os.environ['LOW']) and ((P[t][:,1].max() >= ty) if above else (P[t][:,1].max() < ty)) for t in I])
elif os.environ.get('MAXAX'):   # sleeves: keep only the part near the shoulder
    keep=np.array([np.abs(P[t][:,0]).max() < float(os.environ['MAXAX']) for t in I])
else: keep=np.array([size[fd(t[0])] not in drop for t in I])
NI=I[keep].astype(np.uint32).ravel()
# write new index buffer appended to a copied bin
binname=g['buffers'][0]['uri']; nb=os.path.basename(dst).replace('.gltf','.bin')
data=open(os.path.join(d,binname),'rb').read(); off=len(data); pad=(4-off%4)%4; data+=b'\0'*pad; off+=pad; data+=NI.tobytes()
open(os.path.join(os.path.dirname(dst),nb),'wb').write(data)
g['buffers'][0]['uri']=nb; g['buffers'][0]['byteLength']=len(data)
g['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':NI.nbytes,'target':34963})
g['accessors'].append({'bufferView':len(g['bufferViews'])-1,'componentType':5125,'count':int(NI.size),'type':'SCALAR'})
p['indices']=len(g['accessors'])-1
for im in g.get('images',[]):
    if 'uri' in im and not os.path.isabs(im['uri']): pass
json.dump(g,open(dst,'w')); print('kept tris',keep.sum(),'of',len(I))
