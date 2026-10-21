import subprocess, numpy as np, glob, os
S = os.environ.get('GUNSND_SRC', '.')                     # folder holding the unpacked sound packs (guns1/, guns2/)
SR=44100
def find(name):
    fs=[os.path.join(d,f) for root in (S+'/guns1', S+'/guns2') for d,_,ff in os.walk(root) for f in ff if f==name and '/MP3' not in d]
    assert len(fs)==1,(name,fs); return fs[0]
def load(name, stereo=True):
    raw=subprocess.run(['ffmpeg','-v','error','-i',find(name),'-ac','2','-ar',str(SR),'-f','f32le','-'],capture_output=True).stdout
    return np.frombuffer(raw,np.float32).reshape(-1,2).copy()
def save(a, path):
    a=np.clip(a,-1,1).astype(np.float32)
    subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ar',str(SR),'-ac','2','-i','-','-b:a','192k',path],input=a.tobytes(),check=True)
def peak(a): return float(np.abs(a).max())
def onsets(a, thr=.35, gap=.05):
    e=np.abs(a).max(1); m=e.max(); out=[]; last=-1e9
    for i in np.where(e>m*thr)[0]:
        if i-last>gap*SR: out.append(i)
        last=i
    return out
