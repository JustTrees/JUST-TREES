"""Make a test copy of the game with debug hooks.
Usage: python3 dev/make_debug.py index.html /tmp/dbg.html
Adds window.FREEZE (stops the real-time loop so tests can step frames by hand) and window.D (handles to game internals).
Never upload the debug copy; index.html must stay clean."""
import sys
s = open(sys.argv[1]).read()
s = s.replace("const dt = Math.max(0, Math.min(.05, (now - last) / 1000)); last = now;", "const dt = window.FREEZE ? 0 : Math.max(0, Math.min(.05, (now - last) / 1000)); last = now;", 1)
s = s.replace("renderer.setAnimationLoop(loop);", "renderer.setAnimationLoop(loop);\n" + 'window.D={P,vr,vrTick,vrAfterMove,update,set,setMode,generate,camera,THREE,scene,renderer,climbableAt,headBlocked,limbGround,cullTiles,get tiles(){return tiles},get limbHold(){return limbHold},get vrHandsObj(){return vrHandsObj},vrHands,zoomOverlay,poseHand,vrZoomRender,rockTop:(x,z)=>rockTopAt(x,z),input,get obstacles(){return obstacles},get H(){return H},groundAt,get state(){return state},set state(v){state=v},GRADE,setVR:v=>{VR_ON=v},VRUI,vruiOpen,vruiTick,vruiClose,startNew,beasts,updateAnimals,scatterBeasts,get world(){return world},loop:t=>loop(t),intro,levelQ,slopeNy,rockAround,tracers,updateGun,vrFire,GUN};', 1)
assert "window.D=" in s and "window.FREEZE" in s, "hook points not found: update make_debug.py"
open(sys.argv[2], "w").write(s); print("wrote", sys.argv[2])
