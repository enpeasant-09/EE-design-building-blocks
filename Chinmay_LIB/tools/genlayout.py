"""genlayout.py - place + route a PCB layout for a KiCad design block (run with KiCad's python).

  "C:/Program Files/KiCad/10.0/bin/python.exe" genlayout.py <block_dir> [<block_dir> ...]

For each <name>.kicad_block folder: exports a netlist from <name>.kicad_sch, builds <name>.kicad_pcb in the
same folder (footprints linked to the schematic symbols), routes it on F.Cu/B.Cu with JLCPCB 2-layer rules,
drops a GND via at every GND pad (the block assumes a GND plane on B.Cu / an inner layer of the host board),
runs DRC against a temporary B.Cu GND plane, and writes <name>_layout.svg plus <name>_layout.json (report).

Placement rules (from the parts' datasheets):
  * decoupling caps (cap between GND and a supply) next to that supply pin of the IC
  * timing caps / pull-ups next to the IC pin they serve (CWD, CRST, SRT, SWT, RESET, WDO)
  * oscillator: VDD cap at pin 4, series resistor at the output pin
"""
import heapq, json, math, os, re, shutil, subprocess, sys, tempfile
import pcbnew

KICAD = r'C:/Program Files/KiCad/10.0'
CLI = KICAD + '/bin/kicad-cli.exe'
FPDIR = KICAD + '/share/kicad/footprints'
CHINMAY_FP = r'C:/Users/crmar/Documents/Chinmay_LIB/Chinmay_Footprints.pretty'

# ---- JLCPCB standard 2-layer capability, with margin -------------------------------------------
RULES = dict(clearance=0.15, track=0.20, track_pwr=0.30, via=0.60, drill=0.30,
             min_track=0.127, min_clear=0.127, annular=0.13, hole2hole=0.50, edge=0.30, silk_w=0.15, silk_h=0.80)
GRID = 0.05            # router grid, mm
GAP = 0.20             # extra courtyard gap during placement, mm

REMAP = {  # stale footprint references -> library footprint that has a 3D model
    'Chinmay_Supervisor:': 'Chinmay_Footprints:',
    'PCM_SparkFun-Resistor:': 'Resistor_SMD:',
    'Package_TO_SOT_SMD:Texas_DDF0008A_SOT-8_1.6x2.9mm_P0.65mm': 'Chinmay_Footprints:Texas_DDF0008A_SOT-8_1.6x2.9mm_P0.65mm',
    'Package_SON:VSON-8-1EP_3x3mm_P0.65mm_EP1.65x2.4mm': 'Chinmay_Footprints:VSON-8-1EP_3x3mm_P0.65mm_EP1.65x2.4mm',
}
SUPPLY = re.compile(r'^(\+|VDD|VCC|VIN|3V3|5V|VBAT|VSUP|V_)', re.I)
TIMING = re.compile(r'(CWD|CRST|SRT|SWT|CT|TD|RESET|RST|WDO|OUT|CLK|MR)', re.I)

def mm(v): return pcbnew.FromMM(v)
def tomm(v): return pcbnew.ToMM(v)

def remap(fp):
    for a, b in REMAP.items():
        if fp.startswith(a): return b + fp[len(a):]
    return fp

# ---- schematic -> netlist -----------------------------------------------------------------------
def sexp(s):
    tok = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', s); st = [[]]
    for t in tok:
        if t == '(': st.append([])
        elif t == ')': x = st.pop(); st[-1].append(x)
        else: st[-1].append(t[1:-1] if t.startswith('"') else t)
    return st[0][0]

def find(node, key): return [c for c in node if isinstance(c, list) and c and c[0] == key]
def val(node, key, d=''):
    f = find(node, key); return f[0][1] if f and len(f[0]) > 1 else d

def netlist(sch, tmp):
    """Annotate a temp copy (R? -> R1...), fix stale footprints, export a kicadsexpr netlist."""
    t = open(sch, encoding='utf-8').read()
    for a, b in REMAP.items(): t = t.replace('"Footprint" "' + a, '"Footprint" "' + b)
    i = t.find('(lib_symbols'); d = 0
    for j in range(i, len(t)):
        d += t[j] == '('; d -= t[j] == ')'
        if d == 0: break
    head, body = t[:j + 1], t[j + 1:]
    cnt = {}; out = []; k = 0
    for m in re.finditer(r'\(symbol\s+\(lib_id', body):
        if m.start() < k: continue
        d = 0
        for e in range(m.start(), len(body)):
            d += body[e] == '('; d -= body[e] == ')'
            if d == 0: break
        ch = body[m.start():e + 1]
        r = re.search(r'\(property "Reference" "([^"]+)"', ch)
        if r and r.group(1).endswith('?'):
            p = r.group(1)[:-1]; cnt[p] = cnt.get(p, 0) + 1; new = f'{p}{cnt[p]}'
            ch = ch.replace(f'"Reference" "{p}?"', f'"Reference" "{new}"').replace(f'(reference "{p}?")', f'(reference "{new}")')
        out.append(body[k:m.start()]); out.append(ch); k = e + 1
    out.append(body[k:]); body = ''.join(out)
    # instance data is keyed by project name: point it at this temp project ("blk") so the refs are used
    body = re.sub(r'\(project "[^"]*"', '(project "blk"', body)
    src = os.path.join(tmp, 'blk.kicad_sch'); open(src, 'w', encoding='utf-8').write(head + body)
    out = os.path.join(tmp, 'blk.net')
    r = subprocess.run([CLI, 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', out, src], capture_output=True, text=True)
    if r.returncode: raise RuntimeError('netlist export failed: ' + r.stderr[-400:])
    n = sexp(open(out, encoding='utf-8').read())
    comps = []
    for c in find(find(n, 'components')[0], 'comp'):
        ts = val(c, 'tstamps') or val(c, 'tstamp')
        comps.append(dict(ref=val(c, 'ref'), value=val(c, 'value'), fp=remap(val(c, 'footprint')), uuid=ts.split()[0] if ts else ''))
    nets = {}
    for e in find(find(n, 'nets')[0], 'net'):
        name = val(e, 'name').lstrip('/')
        nets[name] = [(val(x, 'ref'), val(x, 'pin')) for x in find(e, 'node')]
    return comps, nets

# ---- footprint geometry (pure python, for placement) -------------------------------------------
class Part:
    def __init__(s, comp, fp):
        s.ref, s.comp, s.fp = comp['ref'], comp, fp
        fp.SetPosition(pcbnew.VECTOR2I(0, 0)); fp.SetOrientationDegrees(0)
        s.pads = [(p.GetNumber(), tomm(p.GetPosition().x), tomm(p.GetPosition().y)) for p in fp.Pads()]
        try:
            bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
            if bb.GetWidth() <= 0: raise ValueError
        except Exception:
            bb = fp.GetBoundingBox(False)
        s.box = (tomm(bb.GetLeft()), tomm(bb.GetTop()), tomm(bb.GetRight()), tomm(bb.GetBottom()))
        s.area = (s.box[2] - s.box[0]) * (s.box[3] - s.box[1])
        s.x = s.y = 0.0; s.rot = 0; s.placed = False

    def rot_xy(s, x, y, rot):
        # KiCad: positive orientation is CCW on screen (y down) -> (x, y) -> (x cos + y sin, -x sin + y cos)
        a = math.radians(rot); c, si = round(math.cos(a)), round(math.sin(a))
        return x * c + y * si, -x * si + y * c

    def pad_at(s, num, x=None, y=None, rot=None):
        x = s.x if x is None else x; y = s.y if y is None else y; rot = s.rot if rot is None else rot
        for n, px, py in s.pads:
            if n == num:
                dx, dy = s.rot_xy(px, py, rot); return x + dx, y + dy
        return x, y

    def box_at(s, x, y, rot):
        pts = [s.rot_xy(a, b, rot) for a in (s.box[0], s.box[2]) for b in (s.box[1], s.box[3])]
        return (x + min(p[0] for p in pts), y + min(p[1] for p in pts), x + max(p[0] for p in pts), y + max(p[1] for p in pts))

def overlap(a, b, g):
    return not (a[2] + g <= b[0] or b[2] + g <= a[0] or a[3] + g <= b[1] or b[3] + g <= a[1])

# ---- placement -----------------------------------------------------------------------------------
def place(parts, nets, gap):
    P = {p.ref: p for p in parts}
    sig = {n: m for n, m in nets.items() if n.upper() not in ('GND', 'GNDD', 'AGND') and len(m) > 1}
    # anchor = IC with most pins (oscillator X if no U)
    ics = sorted([p for p in parts if re.match(r'(U|X|Y)\d', p.ref)], key=lambda p: -len(p.pads))
    anchor = ics[0]
    # strong pairs: small passive -> the anchor-IC pad it sits on (decoupling, timing, pull-ups, series R)
    strong = []
    for p in parts:
        if p is anchor or not re.match(r'(R|C)\d', p.ref): continue
        for n, mem in nets.items():
            if n.upper().startswith('GND'): continue
            mine = [pin for r, pin in mem if r == p.ref]
            ic = [pin for r, pin in mem if r == anchor.ref]
            if mine and ic:
                w = 8.0 if (p.ref.startswith('C') and (SUPPLY.match(n) or any(r == p.ref for r, _ in nets.get('GND', [])))) else 4.0
                strong.append((p.ref, mine[0], anchor.ref, ic[0], w))
    def cost(p, x, y, rot):
        c = 0.0
        for n, mem in sig.items():
            if not any(r == p.ref for r, _ in mem): continue
            xs, ys = [], []
            for r, pin in mem:
                q = P.get(r)
                if q is None: continue
                if q is p: px, py = p.pad_at(pin, x, y, rot)
                elif q.placed: px, py = q.pad_at(pin)
                else: continue
                xs.append(px); ys.append(py)
            if len(xs) > 1: c += (max(xs) - min(xs)) + (max(ys) - min(ys))
        for a, pa, b, pb, w in strong:
            if a == p.ref and P[b].placed:
                ax, ay = p.pad_at(pa, x, y, rot); bx, by = P[b].pad_at(pb); c += w * math.hypot(ax - bx, ay - by)
            elif b == p.ref and P[a].placed:
                ax, ay = P[a].pad_at(pa); bx, by = p.pad_at(pb, x, y, rot); c += w * math.hypot(ax - bx, ay - by)
        # GND pads like to sit near each other (short via returns) - weak pull
        return c
    def bbox_all(extra=None):
        bs = [q.box_at(q.x, q.y, q.rot) for q in parts if q.placed] + ([extra] if extra else [])
        return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))
    def try_place(p):
        best = None
        others = [q.box_at(q.x, q.y, q.rot) for q in parts if q.placed and q is not p]
        if not others:
            p.x = p.y = 0.0; p.rot = 0; p.placed = True; return
        bb = bbox_all() if any(q.placed and q is not p for q in parts) else (0, 0, 0, 0)
        step = 0.25
        for rot in (0, 90, 180, 270):
            x0 = bb[0] - 6; x1 = bb[2] + 6; y0 = bb[1] - 6; y1 = bb[3] + 6
            yy = y0
            while yy <= y1:
                xx = x0
                while xx <= x1:
                    b = p.box_at(xx, yy, rot)
                    if not any(overlap(b, o, gap) for o in others):
                        u = (min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3]))
                        area = (u[2] - u[0]) * (u[3] - u[1]); aspect = abs((u[2] - u[0]) - (u[3] - u[1]))
                        c = cost(p, xx, yy, rot) + 0.35 * area ** 0.5 * 4 + 0.15 * aspect
                        if best is None or c < best[0]: best = (c, xx, yy, rot)
                    xx += step
                yy += step
        _, p.x, p.y, p.rot = best; p.placed = True
    anchor.x = anchor.y = 0; anchor.rot = 0; anchor.placed = True
    # order: things strongly tied to the anchor first, then by connectivity
    def links(p): return sum(1 for n, m in sig.items() if any(r == p.ref for r, _ in m) and any(P[r].placed for r, _ in m if r in P))
    rest = [p for p in parts if p is not anchor]
    rest.sort(key=lambda p: (-sum(w for a, _, b, _, w in strong if a == p.ref), -p.area))
    first = [p for p in rest if any(a == p.ref for a, *_ in strong)]
    later = [p for p in rest if p not in first]
    for p in first: try_place(p)
    while later:
        later.sort(key=lambda p: (-links(p), -p.area)); try_place(later.pop(0))
    for _ in range(2):  # refinement
        for p in rest:
            p.placed = False; try_place(p)

# ---- grid router ---------------------------------------------------------------------------------
class Router:
    def __init__(s, board, bbox):
        s.b = board
        s.x0, s.y0 = bbox[0] - 1.2, bbox[1] - 1.2
        s.W = int((bbox[2] - bbox[0] + 2.4) / GRID) + 1; s.H = int((bbox[3] - bbox[1] + 2.4) / GRID) + 1
        s.own = [[0] * (s.W * s.H) for _ in range(2)]     # 0 free, >0 net code, -1 blocked
        s.padcu = [0] * (s.W * s.H)                        # no vias on/near pads
        s.tracks = []

    def cell(s, x, y): return int(round((x - s.x0) / GRID)), int(round((y - s.y0) / GRID))
    def xy(s, i, j): return s.x0 + i * GRID, s.y0 + j * GRID

    def _mark(s, layer, net, x0, y0, x1, y1, r, dist):
        i0, j0 = s.cell(x0 - r, y0 - r); i1, j1 = s.cell(x1 + r, y1 + r)
        arr = s.own[layer] if layer is not None else s.padcu
        for j in range(max(0, j0), min(s.H, j1 + 1)):
            for i in range(max(0, i0), min(s.W, i1 + 1)):
                x, y = s.xy(i, j)
                if dist(x, y) <= r + 1e-9:
                    k = j * s.W + i
                    if layer is None: arr[k] = 1; continue
                    o = arr[k]
                    if o == 0: arr[k] = net
                    elif o != net: arr[k] = -1

    def mark_rect(s, layer, net, box, r):
        bx0, by0, bx1, by1 = box
        def d(x, y): return math.hypot(max(bx0 - x, 0, x - bx1), max(by0 - y, 0, y - by1))
        s._mark(layer, net, bx0, by0, bx1, by1, r, d)

    def mark_seg(s, layer, net, a, b, r):
        def d(x, y):
            vx, vy = b[0] - a[0], b[1] - a[1]; L = vx * vx + vy * vy
            t = 0 if L == 0 else max(0, min(1, ((x - a[0]) * vx + (y - a[1]) * vy) / L))
            return math.hypot(x - a[0] - t * vx, y - a[1] - t * vy)
        s._mark(layer, net, min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]), r, d)

    def add_pads(s):
        cl, hw = RULES['clearance'], RULES['track_pwr'] / 2
        for fp in s.b.GetFootprints():
            for p in fp.Pads():
                bb = p.GetBoundingBox(); box = (tomm(bb.GetLeft()), tomm(bb.GetTop()), tomm(bb.GetRight()), tomm(bb.GetBottom()))
                net = p.GetNetCode() or -1
                for li, L in ((0, pcbnew.F_Cu), (1, pcbnew.B_Cu)):
                    if p.IsOnLayer(L): s.mark_rect(li, net, box, cl + hw)
                s.mark_rect(None, 0, box, RULES['via'] / 2 + cl)

    def via_ok(s, i, j, net):
        if s.padcu[j * s.W + i]: return False
        rr = int(math.ceil((RULES['via'] / 2 + RULES['clearance'] - (RULES['clearance'] + RULES['track_pwr'] / 2) + 0.05) / GRID))
        rr = max(rr, 2)
        for dj in range(-rr, rr + 1):
            for di in range(-rr, rr + 1):
                ii, jj = i + di, j + dj
                if not (0 <= ii < s.W and 0 <= jj < s.H): return False
                for L in (0, 1):
                    o = s.own[L][jj * s.W + ii]
                    if o != 0 and o != net: return False
        return True

    def astar(s, net, sources, targets, allow_b=True, maxexp=400000):
        tset = set(targets); tx = [t[0] for t in targets]; ty = [t[1] for t in targets]
        def h(i, j): return min(math.hypot(i - a, j - b) for a, b in zip(tx[:8], ty[:8]))
        openl = []; came = {}; g = {}
        for st in sources:
            g[st] = 0; heapq.heappush(openl, (h(st[0], st[1]), 0, st)); came[st] = None
        VIA = 18.0; BCOST = 3.0
        dirs = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
        n = 0
        while openl:
            f, gc, cur = heapq.heappop(openl)
            if gc > g.get(cur, 1e18): continue
            i, j, L = cur
            if (i, j, L) in tset or ((i, j) in {(a, b) for a, b, l in tset if l == -1}):
                path = []
                while cur is not None: path.append(cur); cur = came[cur]
                return path[::-1]
            n += 1
            if n > maxexp: return None
            for di, dj, c in dirs:
                ii, jj = i + di, j + dj
                if not (0 <= ii < s.W and 0 <= jj < s.H): continue
                o = s.own[L][jj * s.W + ii]
                if o != 0 and o != net: continue
                if di and dj:  # no corner cutting
                    if s.own[L][j * s.W + ii] not in (0, net) or s.own[L][jj * s.W + i] not in (0, net): continue
                nc = gc + c * (BCOST if L == 1 else 1.0)
                nx = (ii, jj, L)
                if nc < g.get(nx, 1e18):
                    g[nx] = nc; came[nx] = cur; heapq.heappush(openl, (nc + h(ii, jj), nc, nx))
            if allow_b and s.via_ok(i, j, net):
                nx = (i, j, 1 - L); nc = gc + VIA
                if nc < g.get(nx, 1e18):
                    g[nx] = nc; came[nx] = cur; heapq.heappush(openl, (nc + h(i, j), nc, nx))
        return None

    def commit(s, net, path, width, netinfo, start_xy=None, end_xy=None):
        """Turn a cell path into tracks/vias on the board and mark it as an obstacle."""
        pts = [(s.xy(i, j), L) for i, j, L in path]
        segs = []; vias = []
        if start_xy: pts.insert(0, (start_xy, pts[0][1]))
        if end_xy: pts.append((end_xy, pts[-1][1]))
        # split into same-layer runs and simplify collinear points
        run = [pts[0]]
        def flush(run):
            if len(run) < 2: return
            keep = [run[0]]
            for k in range(1, len(run) - 1):
                (ax, ay), _ = keep[-1]; (bx, by), _ = run[k]; (cx, cy), _ = run[k + 1]
                if abs((bx - ax) * (cy - by) - (by - ay) * (cx - bx)) > 1e-9: keep.append(run[k])
            keep.append(run[-1])
            for a, b in zip(keep, keep[1:]):
                if math.hypot(a[0][0] - b[0][0], a[0][1] - b[0][1]) > 1e-6: segs.append((a[0], b[0], a[1]))
        for p in pts[1:]:
            if p[1] != run[-1][1]:
                flush(run); vias.append(run[-1][0]); run = [p]
            else: run.append(p)
        flush(run)
        cl = RULES['clearance']
        for a, b, L in segs:
            t = pcbnew.PCB_TRACK(s.b); t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1]))); t.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
            t.SetWidth(mm(width)); t.SetLayer(pcbnew.F_Cu if L == 0 else pcbnew.B_Cu); t.SetNet(netinfo); s.b.Add(t)
            s.mark_seg(L, net, a, b, cl + width / 2 + RULES['track_pwr'] / 2)
        for v in vias: s.add_via(net, v, netinfo)
        return len(segs), len(vias)

    def add_via(s, net, v, netinfo):
        o = pcbnew.PCB_VIA(s.b); o.SetPosition(pcbnew.VECTOR2I(mm(v[0]), mm(v[1])))
        try: o.SetWidth(mm(RULES['via']))
        except Exception: o.SetWidth(pcbnew.F_Cu, mm(RULES['via']))
        o.SetDrill(mm(RULES['drill'])); o.SetNet(netinfo); s.b.Add(o)
        for L in (0, 1): s.mark_rect(L, net, (v[0], v[1], v[0], v[1]), RULES['via'] / 2 + RULES['clearance'] + RULES['track_pwr'] / 2)
        s.mark_rect(None, 0, (v[0], v[1], v[0], v[1]), RULES['via'] + RULES['clearance'])

def is_gnd(n): return n.upper() in ('GND', 'GNDD', 'AGND', 'DGND')

def route(board, parts, nets, netinfos):
    pads = {}
    for fp in board.GetFootprints():
        for p in fp.Pads(): pads.setdefault((fp.GetReference(), p.GetNumber()), []).append(p)
    bb = board.ComputeBoundingBox(False)
    R = Router(board, (tomm(bb.GetLeft()), tomm(bb.GetTop()), tomm(bb.GetRight()), tomm(bb.GetBottom())))
    R.add_pads()
    fails = []; nseg = nvia = 0
    def pxy(p): return tomm(p.GetPosition().x), tomm(p.GetPosition().y)
    order = sorted([n for n in nets if not is_gnd(n) and len(nets[n]) > 1], key=lambda n: (bool(SUPPLY.match(n)), len(nets[n])))
    for n in order:
        ni = netinfos[n]; code = ni.GetNetCode(); w = RULES['track_pwr'] if SUPPLY.match(n) else RULES['track']
        plist = [pads[k][0] for k in nets[n] if k in pads]
        if len(plist) < 2: continue
        # Prim tree: connect nearest unconnected pad to the tree each time
        tree_cells = set(); conn = [plist[0]]; todo = plist[1:]
        i, j = R.cell(*pxy(plist[0])); tree_cells.add((i, j, 0))
        while todo:
            todo.sort(key=lambda p: min(math.hypot(pxy(p)[0] - pxy(q)[0], pxy(p)[1] - pxy(q)[1]) for q in conn))
            p = todo.pop(0); ti, tj = R.cell(*pxy(p))
            path = R.astar(code, list(tree_cells), [(ti, tj, 0)])
            if path is None:
                fails.append(f'{n}: {p.GetParentFootprint().GetReference()}.{p.GetNumber()}'); continue
            a, b = R.commit(code, path, w, ni, end_xy=pxy(p) if True else None)
            # first point: if the path starts at a pad centre cell, extend into the exact pad centre
            nseg += a; nvia += b
            tree_cells.update(path); conn.append(p)
        # stub from each pad's exact centre to its grid cell (keeps connection inside the pad)
        for p in plist:
            x, y = pxy(p); ci, cj = R.cell(x, y); cx, cy = R.xy(ci, cj)
            if math.hypot(cx - x, cy - y) > 1e-4:
                t = pcbnew.PCB_TRACK(board); t.SetStart(pcbnew.VECTOR2I(mm(x), mm(y))); t.SetEnd(pcbnew.VECTOR2I(mm(cx), mm(cy)))
                t.SetWidth(mm(w)); t.SetLayer(pcbnew.F_Cu); t.SetNet(ni); board.Add(t)
    # GND: a via at (or next to) every GND pad, connected to the B.Cu plane of the host board
    gnd = next((n for n in nets if is_gnd(n)), None)
    if gnd:
        ni = netinfos[gnd]; code = ni.GetNetCode()
        for k in nets[gnd]:
            plist_k = pads.get(k, [])
            if not plist_k: continue
            p = max(plist_k, key=lambda q: tomm(q.GetSize().x) * tomm(q.GetSize().y))
            for _once in (1,):
                x, y = pxy(p); ci, cj = R.cell(x, y)
                sz = p.GetSize(); big = min(tomm(sz.x), tomm(sz.y)) >= 1.0
                if big:  # exposed pad: via in pad
                    R.add_via(code, (x, y), ni); nvia += 1; continue
                # nearest via site reachable on F.Cu
                best = None
                for rad in range(4, 40):
                    for dj in range(-rad, rad + 1):
                        for di in (-rad, rad) if abs(dj) != rad else range(-rad, rad + 1):
                            ii, jj = ci + di, cj + dj
                            if 0 <= ii < R.W and 0 <= jj < R.H and R.own[0][jj * R.W + ii] in (0, code) and R.via_ok(ii, jj, code):
                                d = math.hypot(di, dj)
                                if best is None or d < best[0]: best = (d, ii, jj)
                    if best: break
                if not best: fails.append(f'GND via: {p.GetParentFootprint().GetReference()}.{p.GetNumber()}'); continue
                path = R.astar(code, [(ci, cj, 0)], [(best[1], best[2], 0)], allow_b=False)
                if path is None: fails.append(f'GND via: {p.GetParentFootprint().GetReference()}.{p.GetNumber()}'); continue
                a, _ = R.commit(code, path, RULES['track_pwr'], ni, start_xy=(x, y)); nseg += a
                R.add_via(code, R.xy(best[1], best[2]), ni); nvia += 1
    return fails, nseg, nvia

# ---- JLC rules, DRC ------------------------------------------------------------------------------
def apply_rules(board):
    ds = board.GetDesignSettings()
    for k, v in (('m_MinClearance', RULES['min_clear']), ('m_TrackMinWidth', RULES['min_track']), ('m_ViasMinSize', 0.5),
                 ('m_MinThroughDrill', RULES['drill']), ('m_ViasMinAnnularWidth', RULES['annular']), ('m_HoleToHoleMin', RULES['hole2hole']),
                 ('m_CopperEdgeClearance', RULES['edge']), ('m_SilkClearance', 0.0), ('m_MinSilkTextHeight', RULES['silk_h']),
                 ('m_MinSilkTextThickness', RULES['silk_w']), ('m_HoleClearance', 0.25)):
        try: setattr(ds, k, mm(v))
        except Exception: pass
    try:
        nc = ds.m_NetSettings.GetDefaultNetclass()
        nc.SetClearance(mm(RULES['clearance'])); nc.SetTrackWidth(mm(RULES['track']))
        nc.SetViaDiameter(mm(RULES['via'])); nc.SetViaDrill(mm(RULES['drill']))
    except Exception: pass

def drc(board, path, tmp):
    """DRC (kicad-cli) on a copy with an outline and a B.Cu GND plane standing in for the host board."""
    b = pcbnew.LoadBoard(path)
    apply_rules(b)
    bb = b.ComputeBoundingBox(False); m = mm(0.8)
    x0, y0, x1, y1 = bb.GetLeft() - m, bb.GetTop() - m, bb.GetRight() + m, bb.GetBottom() + m
    for a, c in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(pcbnew.VECTOR2I(*a)); s.SetEnd(pcbnew.VECTOR2I(*c))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); b.Add(s)
    gnd = b.FindNet('GND')
    if gnd:
        z = pcbnew.ZONE(b); z.SetLayer(pcbnew.B_Cu); z.SetNet(gnd)
        ol = z.Outline(); ol.NewOutline()
        for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)): ol.Append(px, py)
        z.SetLocalClearance(mm(0.2)); z.SetMinThickness(mm(0.2)); b.Add(z)
    dp = os.path.join(tmp, 'drc.kicad_pcb'); pcbnew.SaveBoard(dp, b)
    rep = os.path.join(tmp, 'drc.json')
    subprocess.run([CLI, 'pcb', 'drc', '--refill-zones', '--format', 'json', '--units', 'mm', '-o', rep, dp],
                   capture_output=True, text=True, timeout=240)
    j = json.load(open(rep, encoding='utf-8'))
    v = j.get('violations', []); u = j.get('unconnected_items', [])
    errs = [x for x in v if x.get('severity') == 'error']
    return dict(errors=len(errs), warnings=len(v) - len(errs), unconnected=len(u),
                types=sorted({f"{x.get('type')} ({x.get('severity')})" for x in v}),
                detail=[f"{x.get('type')}: " + '; '.join(i.get('description', '') for i in x.get('items', []))[:160] for x in errs[:8]],
                unconnected_detail=['; '.join(i.get('description', '') for i in x.get('items', []))[:160] for x in u[:6]])

# ---- main ----------------------------------------------------------------------------------------
def load_fp(ref):
    lib, name = ref.split(':', 1)
    d = CHINMAY_FP if lib == 'Chinmay_Footprints' else os.path.join(FPDIR, lib + '.pretty')
    fp = pcbnew.FootprintLoad(d, name)
    if fp is None: raise RuntimeError('footprint not found: ' + ref)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp

def build(block_dir):
    name = os.path.basename(block_dir.rstrip('/\\')).replace('.kicad_block', '')
    sch = os.path.join(block_dir, name + '.kicad_sch')
    tmp = tempfile.mkdtemp(prefix='blk_')
    comps, nets = netlist(sch, tmp)
    comps = [c for c in comps if c['fp']]
    report = dict(block=name, parts=len(comps))
    for attempt, gap in enumerate((GAP, GAP + 0.25, GAP + 0.5)):
        board = pcbnew.BOARD(); apply_rules(board)
        netinfos = {}
        for n in nets:
            ni = pcbnew.NETINFO_ITEM(board, n); board.Add(ni); netinfos[n] = ni
        parts = []
        for c in comps:
            fp = load_fp(c['fp']); fp.SetReference(c['ref']); fp.SetValue(c['value'])
            if c['uuid']: fp.SetPath(pcbnew.KIID_PATH('/' + c['uuid']))
            parts.append(Part(c, fp))
        place(parts, nets, gap)
        P = {p.ref: p for p in parts}
        # centre the layout on (100, 100) mm
        bxs = [p.box_at(p.x, p.y, p.rot) for p in parts]
        cx = (min(b[0] for b in bxs) + max(b[2] for b in bxs)) / 2; cy = (min(b[1] for b in bxs) + max(b[3] for b in bxs)) / 2
        for p in parts:
            p.fp.SetPosition(pcbnew.VECTOR2I(mm(100 + p.x - cx), mm(100 + p.y - cy))); p.fp.SetOrientationDegrees(p.rot)
            board.Add(p.fp)
            for pad in p.fp.Pads():
                for n, mem in nets.items():
                    if (p.ref, pad.GetNumber()) in mem: pad.SetNet(netinfos[n])
            r = p.fp.Reference(); r.SetTextSize(pcbnew.VECTOR2I(mm(0.6), mm(0.6))); r.SetTextThickness(mm(0.1)); r.SetLayer(pcbnew.F_Fab); r.SetPosition(p.fp.GetPosition())
            p.fp.Value().SetVisible(False)
        fails, nseg, nvia = route(board, parts, nets, netinfos)
        if not fails: break
    bb = board.ComputeBoundingBox(False)
    report.update(size_mm=[round(tomm(bb.GetWidth()), 2), round(tomm(bb.GetHeight()), 2)], tracks=nseg, vias=nvia,
                  unrouted=fails, attempts=attempt + 1)
    tout = os.path.join(tmp, name + '.kicad_pcb'); pcbnew.SaveBoard(tout, board)
    out = os.path.join(block_dir, name + '.kicad_pcb'); shutil.copyfile(tout, out)   # board only, no .kicad_pro in the block
    report['drc'] = drc(board, tout, tmp)
    svg = os.path.join(block_dir, name + '_layout.svg')
    subprocess.run([CLI, 'pcb', 'export', 'svg', '--layers', 'F.Cu,B.Cu,F.Silkscreen,F.Courtyard', '--mode-single',
                    '--fit-page-to-board', '--exclude-drawing-sheet', '-o', svg, out], capture_output=True, text=True)
    report['svg'] = os.path.basename(svg)
    for ext in ('.kicad_prl', '.kicad_pro'):
        f = os.path.join(block_dir, name + ext)
        if os.path.exists(f): os.remove(f)
    json.dump(report, open(os.path.join(block_dir, name + '_layout.json'), 'w'), indent=1)
    shutil.rmtree(tmp, ignore_errors=True)
    # keep the stale footprint fixes in the block schematic too
    t = open(sch, encoding='utf-8').read(); t2 = t
    for a, b in REMAP.items(): t2 = t2.replace('"Footprint" "' + a, '"Footprint" "' + b)
    if t2 != t: open(sch, 'w', encoding='utf-8').write(t2); report['schematic_fixed'] = True
    return report

if __name__ == '__main__':
    for d in sys.argv[1:]:
        try: print(json.dumps(build(d)))
        except Exception as e:
            import traceback; print(json.dumps(dict(block=d, error=repr(e), tb=traceback.format_exc()[-1500:])))
