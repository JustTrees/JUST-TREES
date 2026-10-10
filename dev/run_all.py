"""Run every check and test on one game file and print a pass/fail list (1.42).
Usage: python3 dev/run_all.py [index.html] [--nm path/to/node_modules] [--jobs 3] [--only name,name]
The online tests need a local PeerJS server: give --nm (a node_modules with 'peer' and 'express') or they are skipped."""
import os, sys, subprocess, tempfile, time, glob, re
from concurrent.futures import ThreadPoolExecutor
here = os.path.dirname(os.path.abspath(__file__)); args = sys.argv[1:]
def opt(name, default=None):
    if name in args: i = args.index(name); v = args[i + 1]; del args[i:i + 2]; return v
    return default
nm, jobs, only = opt("--nm", os.environ.get("PEER_NM")), int(opt("--jobs", "3")), opt("--only")
game = os.path.abspath(args[0] if args else os.path.join(here, "..", "index.html"))
tmp = tempfile.mkdtemp(prefix="jt-tests-"); dbg = os.path.join(tmp, "dbg.html")
ok = subprocess.run([sys.executable, os.path.join(here, "check_code.py"), game]).returncode == 0
subprocess.run([sys.executable, os.path.join(here, "make_debug.py"), game, dbg], check=True, capture_output=True)
ONLINE = {"test_mp", "test_mp_fail", "test_lobby"}
tests = sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(here, "test_*.py")))
if only: tests = [t for t in tests if t in only.split(",")]
peer = None
if nm and any(t in ONLINE for t in tests):
    peer = subprocess.Popen(["node", os.path.join(here, "peer_server.js"), nm], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(2)
def run(t):
    if t in ONLINE and not peer: return t, "skip", "no PeerJS server (--nm)"
    t0 = time.time()
    try: r = subprocess.run([sys.executable, os.path.join(here, t + ".py"), dbg, os.path.join(tmp, t + ".png")], capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired: return t, "FAIL", "timed out"
    out = (r.stdout + r.stderr).strip(); errs = [l for l in out.splitlines() if "errors:" in l and not l.strip().endswith("errors: none")]
    good = r.returncode == 0 and not errs                    # a test passes when it runs through and reports no page errors
    return t, "pass" if good else "FAIL", ("%.0fs" % (time.time() - t0)) if good else (errs[0][:200] if errs else out[-300:])
online = [t for t in tests if t in ONLINE]; offline = [t for t in tests if t not in ONLINE]
with ThreadPoolExecutor(jobs) as ex: res = list(ex.map(run, offline))
res += [run(t) for t in online]                              # the online ones one at a time (they share the local server)
if peer: peer.terminate()
print("\ncode check:", "pass" if ok else "FAIL")
for t, st, note in res: print(f"  {st:5} {t:24} {note}")
bad = (not ok) + sum(st == "FAIL" for _, st, _ in res)
print("\nALL GOOD" if not bad else f"\n{bad} PROBLEM(S)"); sys.exit(1 if bad else 0)
