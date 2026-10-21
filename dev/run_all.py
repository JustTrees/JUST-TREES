"""Run every check and test on one game file and print a pass/fail list (1.42; 2.48: quick by default).
Usage: python3 dev/run_all.py [index.html] [--nm path/to/node_modules] [--jobs 3] [--only name,name] [--full]
Quick (the default, about half the time): every test runs, but the slowest ones do less of the same thing (fewer maps, shorter walks,
fewer samples: each test reads JT_QUICK=1) and no pictures are saved. --full: everything, with pictures (before a big release, or
when a quick run fails and you want the whole picture). The online tests run one at a time after the others (they share the
local PeerJS server); the slowest tests start first; a test that fails gets one more go on its own at the end (times from the last run are kept in the temp folder).
The online tests need a local PeerJS server: give --nm (a node_modules with 'peer' and 'express') or they are skipped."""
import os, sys, subprocess, tempfile, time, glob, json
from concurrent.futures import ThreadPoolExecutor
here = os.path.dirname(os.path.abspath(__file__)); args = sys.argv[1:]
def opt(name, default=None):
    if name in args: i = args.index(name); v = args[i + 1]; del args[i:i + 2]; return v
    return default
full = "--full" in args
if full: args.remove("--full")
nm, jobs, only = opt("--nm", os.environ.get("PEER_NM")), int(opt("--jobs", "3")), opt("--only")
game = os.path.abspath(args[0] if args else os.path.join(here, "..", "index.html"))
tmp = tempfile.mkdtemp(prefix="jt-tests-"); dbg = os.path.join(tmp, "dbg.html")
ok = subprocess.run([sys.executable, os.path.join(here, "check_code.py"), game]).returncode == 0
subprocess.run([sys.executable, os.path.join(here, "make_debug.py"), game, dbg], check=True, capture_output=True)
ONLINE = {"test_mp", "test_mp_fail", "test_lobby", "test_online", "test_en_online", "test_rooms", "test_243", "test_246", "test_248"}
tests = sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(here, "test_*.py")))
if only: tests = [t for t in tests if t in only.split(",")]
TIMES = os.path.join(tempfile.gettempdir(), "jt-test-times-" + ("full" if full else "quick") + ".json")
try: times = json.load(open(TIMES))
except Exception: times = {}
peer = None
if nm and any(t in ONLINE for t in tests):
    peer = subprocess.Popen(["node", os.path.join(here, "peer_server.js"), nm], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(2)
env = dict(os.environ); env.pop("JT_QUICK", None)
if not full: env["JT_QUICK"] = "1"
def run(t):
    if t in ONLINE and not peer: return t, "skip", "no PeerJS server (--nm)"
    t0 = time.time(); cmd = [sys.executable, os.path.join(here, t + ".py"), dbg] + ([os.path.join(tmp, t + ".png")] if full else [])
    try: r = subprocess.run(cmd, capture_output=True, text=True, timeout=900, env=env)
    except subprocess.TimeoutExpired: return t, "FAIL", "timed out"
    out = (r.stdout + r.stderr).strip(); errs = [l for l in out.splitlines() if "errors:" in l and not l.strip().endswith("errors: none")]
    good = r.returncode == 0 and not errs                    # a test passes when it runs through and reports no page errors
    times[t] = round(time.time() - t0)
    return t, "pass" if good else "FAIL", ("%.0fs" % (time.time() - t0)) if good else (errs[0][:200] if errs else out[-300:])
slow_first = lambda L: sorted(L, key=lambda t: -times.get(t, 60))
online = slow_first([t for t in tests if t in ONLINE]); offline = slow_first([t for t in tests if t not in ONLINE])
with ThreadPoolExecutor(jobs) as ex: res = list(ex.map(run, offline))
res = sorted(res + [run(t) for t in online])                 # the online ones one at a time, after the rest (they share the local server, and time out when the machine is busy)
again = [t for t, st, _ in res if st == "FAIL"]                # a busy machine makes the model-loading and random-mood tests time out or wobble: each failure gets one more go, alone
if again and len(again) <= 12:
    redo = {t: run(t) for t in again}
    res = [(t, "pass", redo[t][2] + " (passed alone)") if t in redo and redo[t][1] == "pass" else (t, st, note) for t, st, note in res]
if peer: peer.terminate()
try: json.dump(times, open(TIMES, "w"))
except Exception: pass
print("\ncode check:", "pass" if ok else "FAIL", "   (" + ("full run" if full else "quick run: --full for everything, with pictures") + ")")
for t, st, note in res: print(f"  {st:5} {t:24} {note}")
bad = (not ok) + sum(st == "FAIL" for _, st, _ in res)
print("\nALL GOOD" if not bad else f"\n{bad} PROBLEM(S)"); sys.exit(1 if bad else 0)
