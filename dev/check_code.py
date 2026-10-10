"""Code checks (1.42): the game script parses, no function name is declared twice (the later one would silently win),
and lists names that are declared but never used. Usage: python3 dev/check_code.py index.html [--unused]"""
import re, sys, subprocess, json
from collections import Counter
s = open(sys.argv[1]).read()
blocks = re.findall(r'<script[^>]*>([\s\S]*?)</script>', s)
g = max((b for b in blocks if 'const VERSION' in b), key=len)
fails = []
dup = [k for k, v in Counter(re.findall(r'^\s*(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(', g, re.M)).items() if v > 1]
if dup: fails.append("function names declared twice: " + ", ".join(dup))
r = subprocess.run(["node", "-e", "new Function(require('fs').readFileSync(0, 'utf8'))"], input=g, capture_output=True, text=True)
if r.returncode: fails.append("script doesn't parse: " + r.stderr.strip().splitlines()[-1][:200])
if "window.D=" in s or "window.FREEZE" in s: fails.append("debug hooks found in the real game file")
if "--unused" in sys.argv:
    names = set(re.findall(r'^\s*(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(', g, re.M))
    for line in re.findall(r'^\s*(?:const|let)\s+(.*)$', g, re.M):
        for m in re.finditer(r'(?:^|,\s*)([A-Za-z_$][\w$]*)\s*=(?!=)', line): names.add(m.group(1))
    KEEP = {"mpSendStart"}                                   # only called from the tests (joining a game that's already going)
    un = sorted(n for n in names if n not in KEEP and len(re.findall(r'(?:(?<=\.\.\.)|(?<![\w$.]))' + re.escape(n) + r'(?![\w$])', g)) <= 1)
    print("declared but never used:", ", ".join(un) or "none")
print("code check:", "OK" if not fails else "FAIL\n  " + "\n  ".join(fails))
sys.exit(1 if fails else 0)
