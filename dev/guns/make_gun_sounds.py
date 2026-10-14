from gunsnd_lib import *  # (expects the two Snake zips unpacked into <scratch>/guns1 and guns2; see the S path in gunsnd_lib.py)
import subprocess
OUT='/home/claude/just-trees/sounds/guns/'
def norm(a, to): return a*(to/max(peak(a),1e-6))
def fade(a, t):
    n=min(len(a), int(t*SR)); a=a.copy(); a[-n:]*=np.linspace(1,0,n)[:,None]**2; return a
def cut(f, a=None, b=None, on=True):
    x=load(f)
    if on: o=onsets(x,.2)[0]; x=x[max(0,o-int(.004*SR)):]
    if a is not None: x=x[int(a*SR):int(b*SR) if b else None]
    return x
def mono_save(x, name, to, keep=None, fadeT=.06):
    x=x.mean(1, keepdims=True).repeat(2,1)
    if keep: x=x[:int(keep*SR)]
    x=norm(fade(x, fadeT), to)
    subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ar',str(SR),'-ac','2','-i','-','-ac','1','-b:a','96k',OUT+name+'.mp3'],input=np.clip(x,-1,1).astype(np.float32).tobytes(),check=True)
# shots: the outdoor ("Full") singles, echo tail kept to ~1.7 s
mono_save(cut('308 Single.wav'), 'sniper_shot', .95, 1.9, .5)
mono_save(cut('762x39 Single WAV.wav'), 'ar_shot', .9, 1.6, .5)
mono_save(cut('9mm Single.wav'), 'nine_shot', .9, 1.6, .5)                 # SMG and pistol
# mechanics
mono_save(cut('308 Bolt Cycle WAV.wav', 0, .45, on=False), 'sniper_back', .8)
mono_save(cut('308 Bolt Cycle WAV.wav', .45, None, on=False), 'sniper_fwd', .8)
mono_save(cut('308 Magazine Part 1 WAV.wav'), 'sniper_magout', .7)
mono_save(cut('308 Magazine Part 2 WAV.wav'), 'sniper_magin', .7)
mono_save(cut('AK Reload Part 1 WAV.wav'), 'ar_magout', .7)
mono_save(cut('AK Reload Part 2 WAV.wav'), 'ar_magin', .75)
ak=load('AK Rack WAV.wav'); e=np.abs(ak).max(1); mid=int(np.argmax(e))+int(.12*SR)
mono_save(ak[:mid], 'ar_back', .75); mono_save(ak[mid:], 'ar_fwd', .75)
mono_save(cut('AR Reload Part 1 WAV.wav'), 'smg_magout', .7)
mono_save(cut('AR Reload Part 2 WAV.wav'), 'smg_magin', .75)
mono_save(cut('AR Charging Handle WAV.wav', 0, .26), 'smg_back', .75); mono_save(cut('AR Charging Handle WAV.wav', .26, None), 'smg_fwd', .75)
mono_save(cut('9mm Pistol Reload 1.wav'), 'pistol_magout', .55)
mono_save(cut('9mm Pistol Reload 2.wav'), 'pistol_magin', .75)
mono_save(cut('9mm Pistol Rack Full.wav', 0, .19), 'pistol_back', .75); mono_save(cut('9mm Pistol Rack Full.wav', .19, None), 'pistol_fwd', .8)
mono_save(cut('9mm Pistol Dry Fire.wav'), 'dry', .5)
