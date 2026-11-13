"""Independent net check: rebuild connectivity from the written .kicad_sch files and compare with intent."""
import sys, math, json, collections, glob, os  # noqa: E401
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "tools", "partwatch"))
from partwatch import sexpr as S

def nets_of(path):
    t = S.parse(open(path, encoding="utf-8").read())
    libs = {str(d[1]): d for d in S.children(S.child(t, "lib_symbols"), "symbol")}
    def lib_pins(lib):
        out = []
        def walk(n):
            for c in n[1:]:
                if S.head(c) == "pin":
                    at = S.child(c, "at"); out.append((str(S.child(c, "number")[1]), float(at[1]), float(at[2]), str(c[1])))
                elif S.head(c) == "symbol": walk(c)
        walk(lib); return out
    K = lambda x, y: (round(x, 2), round(y, 2))
    pinpts = collections.defaultdict(list); named = []
    refs = []
    for s in S.children(t, "symbol"):
        lid = str(S.value(s, "lib_id")); at = S.child(s, "at"); x0, y0, rot = float(at[1]), float(at[2]), float(at[3])
        props = {str(p[1]): str(p[2]) for p in S.children(s, "property")}
        ref = props["Reference"]; refs.append((ref, props.get("Footprint", ""), lid))
        for num, px, py, typ in lib_pins(libs[lid]):
            py = -py; a = math.radians(-rot)
            q = K(x0 + px*math.cos(a) - py*math.sin(a), y0 + px*math.sin(a) + py*math.cos(a))
            pinpts[q].append(f"{ref}.{num}")
            if ref.startswith("#PWR"): named.append((props["Value"], q))
    edges = []
    for w in S.children(t, "wire"):
        xy = S.children(S.child(w, "pts"), "xy"); edges.append((K(float(xy[0][1]), float(xy[0][2])), K(float(xy[1][1]), float(xy[1][2]))))
    for kind in ("label", "hierarchical_label", "global_label"):
        for l in S.children(t, kind):
            at = S.child(l, "at"); named.append((str(l[1]), K(float(at[1]), float(at[2]))))
    ncs = {K(float(S.child(n, "at")[1]), float(S.child(n, "at")[2])) for n in S.children(t, "no_connect")}
    juncs = {K(float(S.child(n, "at")[1]), float(S.child(n, "at")[2])) for n in S.children(t, "junction")}
    allp = set(pinpts) | {p for e in edges for p in e} | {q for _, q in named} | ncs
    par = {p: p for p in allp}
    def fd(p):
        while par[p] != p: par[p] = par[par[p]]; p = par[p]
        return p
    def un(a, b): par[fd(a)] = fd(b)
    def on(p, a, b):
        (x, y), (x1, y1), (x2, y2) = p, a, b
        return abs((x2-x1)*(y-y1)-(y2-y1)*(x-x1)) < 1e-3 and min(x1,x2)-1e-3 <= x <= max(x1,x2)+1e-3 and min(y1,y2)-1e-3 <= y <= max(y1,y2)+1e-3
    problems = []
    for a, b in edges:
        un(a, b)
        for p in allp:
            if p not in (a, b) and on(p, a, b):
                un(p, a)
                if p in pinpts and p not in juncs and p not in {e for ed in edges for e in ed}:
                    problems.append(f"pin {pinpts[p]} lies mid-wire at {p} (KiCad does not connect this)")
    by = collections.defaultdict(list)
    for n, q in named: by[n].append(q)
    for n, qs in by.items():
        for q in qs[1:]: un(q, qs[0])
    return fd, pinpts, ncs, by, refs, problems, edges

OUT = os.environ.get("WDGEN_OUT", os.path.join(REPO, "projects", "Chinmay_WD_RST"))
intent = json.load(open(os.path.join(OUT, ".wdgen_intent.json")))
total_bad = 0
for fn, items in intent.items():
    fd, pinpts, ncs, by, refs, problems, edges = nets_of(os.path.join(OUT, fn))
    K = lambda p: (round(p[0], 2), round(p[1], 2))
    groups = collections.defaultdict(set)
    bad = list(problems)
    for p, net in items:
        q = K(p)
        if q not in pinpts: bad.append(f"no pin at {q} for {net}")
        if net is None:
            if q not in ncs: bad.append(f"{pinpts.get(q)} should be NC")
            continue
        groups[net].add(fd(q))
    for net, g in groups.items():
        if len(g) != 1: bad.append(f"net {net} split into {len(g)} pieces")
    roots = {}
    for net, g in groups.items():
        for r in g:
            if r in roots and roots[r] != net: bad.append(f"SHORT: {net} and {roots[r]}")
            roots[r] = net
    # every pin must be on an intended net or NC
    for q, pins in pinpts.items():
        r = fd(q)
        if r not in roots and q not in ncs:
            if any(not p.startswith("#") for p in pins): bad.append(f"unconnected pin(s) {pins}")
    # dangling wire ends
    ends = collections.Counter(e for ed in edges for e in ed)
    for e, c in ends.items():
        if c == 1 and e not in pinpts and e not in {q for qs in by.values() for q in qs}:
            bad.append(f"dangling wire end {e}")
    nofp = [r for r, fp, lid in refs if not r.startswith("#") and not fp]
    if nofp: bad.append(f"no footprint: {nofp}")
    print(f"{fn:28s} {'OK' if not bad else 'FAIL'}  nets={len(groups)} parts={sum(1 for r in refs if not r[0].startswith('#'))}")
    for b in bad: print("    ", b)
    total_bad += len(bad)
print("TOTAL PROBLEMS:", total_bad)
