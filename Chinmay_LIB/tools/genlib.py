"""Chinmay_Footprints.pretty + model specs for Fusion.
- copies of KiCad footprints whose 3D model is missing from the KiCad 10 install (model path re-pointed)
- new footprints from datasheet land patterns (LT8640S/45S/48S, MP8795H, MAX17503 T2044+4C)"""
import os, re, json, uuid, glob, shutil
LIB = 'C:/Users/crmar/Documents/Chinmay_LIB'
M3D = LIB + '/Chinmay_3D.3dshapes'
OUT = '/home/claude/lib/out'
PRETTY = OUT + '/Chinmay_Footprints.pretty'
U = lambda: str(uuid.uuid4())
def F(v):
    v = round(float(v), 4) + 0.0
    return ('%.4f' % v).rstrip('0').rstrip('.') if v else '0'
KFP = '/mnt/user-data/uploads/kicad/footprints'

def blk(s, i):
    d = 0
    while True:
        c = s[i]
        if c == '"':
            i += 1
            while s[i] != '"':
                if s[i] == '\\': i += 1
                i += 1
        elif c == '(': d += 1
        elif c == ')':
            d -= 1
            if d == 0: return i + 1
        i += 1

def model_block(name):
    return (f'\t(model "{M3D}/{name}.step"\n\t\t(offset\n\t\t\t(xyz 0 0 0)\n\t\t)\n\t\t(scale\n\t\t\t(xyz 1 1 1)\n\t\t)\n'
            f'\t\t(rotate\n\t\t\t(xyz 0 0 0)\n\t\t)\n\t)\n')

def pads_of(s):
    P = []
    for m in re.finditer(r'\(pad\s+"([^"]*)"\s+(\w+)\s+(\w+)', s):
        e = blk(s, m.start()); b = s[m.start():e]
        at = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)', b)
        sz = re.search(r'\(size\s+([\d.]+)\s+([\d.]+)\)', b)
        x, y, a = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
        w, h = float(sz.group(1)), float(sz.group(2))
        if abs(a) in (90, 270): w, h = h, w
        lay = re.search(r'\(layers([^)]*)\)', b).group(1)
        P.append(dict(num=m.group(1), typ=m.group(2), shape=m.group(3), x=x, y=y, w=w, h=h, cu='F.Cu' in lay or '*.Cu' in lay))
    return P

def fab_extent(s):
    xs, ys = [], []
    for m in re.finditer(r'\((fp_line|fp_rect|fp_poly)\b', s):
        e = blk(s, m.start()); b = s[m.start():e]
        if '"F.Fab"' not in b: continue
        for a, c in re.findall(r'\((?:start|end|xy)\s+([-\d.]+)\s+([-\d.]+)\)', b):
            xs.append(float(a)); ys.append(float(c))
    return (min(xs), max(xs), min(ys), max(ys)) if xs else None

# ------------------------------------------------------------------ copies
COPY = {  # footprint : (lib, body_w, body_l, height, standoff, style, terminal spec note)
 'Oscillator_SMD_ECS_2520MV-xxx-xx-4Pin_2.5x2.0mm': ('Oscillator', 'flat', 0.80, 'ECS-2520MV: 2.5x2.0x0.8 nom (1.0 max) ceramic, 4 castellated pads'),
 'Maxim_TDFN-12-1EP_3x3mm_P0.5mm_EP1.7x2.5mm': ('Package_DFN_QFN', 'flat', 0.75, 'Maxim TD1233+1C 21-0664: 3x3x0.75, e0.5, EP1.7x2.5'),
 'TQFN-20-1EP_5x5mm_P0.65mm_EP3.25x3.25mm_ThermalVias': ('Package_DFN_QFN', 'flat', 0.75, 'Maxim T2055+4 21-0140: 5x5x0.75, e0.65, EP3.25'),
 'WCH_QFN-16-1EP_3x3mm_P0.5mm_EP1.8x1.8mm': ('Package_DFN_QFN', 'flat', 0.75, 'WCH CH343P QFN16 3x3x0.75, e0.5, EP1.8'),
 'VSON-8-1EP_3x3mm_P0.65mm_EP1.65x2.4mm': ('Package_SON', 'flat', 0.90, 'TI DRB0008A VSON-8 3x3x0.9 (1.0 max), e0.65, EP1.65x2.4'),
 'WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm': ('Package_SON', 'flat', 0.75, 'Macronix/GigaDevice 8-WSON 8x6x0.75 (0.8 max), e1.27, EP3.4x4.3'),
 'Vishay_PowerPAK_1212-8_Single': ('Package_SO', 'flat', 0.97, 'Vishay PowerPAK 1212-8S 3.3x3.3x0.97 (1.07 max)'),
 'HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3x3mm': ('Package_SO', 'gull', 1.00, 'Renesas GSP 16-HTSSOP 4.4x5.0x1.0 (1.2 max), span 6.4, e0.65, EP3x3'),
 'Texas_DDF0008A_SOT-8_1.6x2.9mm_P0.65mm': ('Package_TO_SOT_SMD', 'gull', 0.85, 'TI DDF0008A SOT-23-THIN-8 1.6x2.9x0.85 (1.1 max), span 2.8, e0.65'),
}
BODY = {  # nominal package body (x, y) in footprint orientation where fab extents include leads
 'Oscillator_SMD_ECS_2520MV-xxx-xx-4Pin_2.5x2.0mm': None,
 'HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3x3mm': (4.4, 5.0),
 'Texas_DDF0008A_SOT-8_1.6x2.9mm_P0.65mm': (1.6, 2.9),
}
specs = {}
def spec_from(name, s, style, h, note, body=None, z0=0.0, balls=False):
    P = [p for p in pads_of(s) if p['cu'] and p['typ'] == 'smd' and p['num'] != '']
    fe = fab_extent(s)
    if body is None:
        bx0, bx1, by0, by1 = fe; body = (round(bx1 - bx0, 3), round(by1 - by0, 3))
    specs[name] = dict(body=body, h=h, z0=z0, style=style, balls=balls, note=note,
                       pads=[dict(x=p['x'], y=p['y'], w=p['w'], h=p['h'], num=p['num'], shape=p['shape']) for p in P])

def copy_fp(name, lib, style, h, note):
    s = open(f'{KFP}/{lib}.pretty/{name}.kicad_mod').read()
    i = s.find('\t(model "'); j = blk(s, i + 1)
    s = s[:i] + model_block(name).rstrip('\n') + s[j:]
    s = s.replace('(generator "kicad-footprint-generator")', '(generator "chinmay_genlib")', 1)
    s = re.sub(r'\(descr "([^"]*)"', lambda m: '(descr ' + json.dumps(m.group(1) + ' | Chinmay copy: 3D model added (' + note + ')'), s, count=1)
    open(f'{PRETTY}/{name}.kicad_mod', 'w').write(s)
    spec_from(name, s, style, h, note, body=BODY.get(name))

# WLCSP from the Supervisor library
def copy_wlcsp():
    src = '/mnt/user-data/uploads/Chinmay_WD_RST/Chinmay_Supervisor.pretty/ADI_WLCSP-6_0.96x1.46mm_P0.5mm.kicad_mod'
    s = open(src).read(); name = 'ADI_WLCSP-6_0.96x1.46mm_P0.5mm'
    k = s.rstrip().rfind(')')
    s = s[:k].rstrip() + '\n' + model_block(name) + ')\n'
    open(f'{PRETTY}/{name}.kicad_mod', 'w').write(s)
    spec_from(name, s, 'wlcsp', 0.56, 'ADI CB-6-17 WLCSP 0.96x1.46, 0.5 pitch, 0.56 max height, SAC ball 0.25', body=(0.96, 1.46), balls=True)

# ------------------------------------------------------------------ new footprints
def fp_header(name, descr, tags, refy, valy):
    eff = '(effects (font (size 1 1) (thickness 0.15)))'
    return [f'(footprint "{name}"', '\t(version 20260206)', '\t(generator "chinmay_genlib")', '\t(layer "F.Cu")',
            f'\t(descr {json.dumps(descr)})', f'\t(tags {json.dumps(tags)})',
            f'\t(property "Reference" "REF**" (at 0 {F(refy)} 0) (layer "F.SilkS") (uuid "{U()}") {eff})',
            f'\t(property "Value" "{name}" (at 0 {F(valy)} 0) (layer "F.Fab") (uuid "{U()}") {eff})',
            f'\t(property "Datasheet" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") {eff})',
            f'\t(property "Description" {json.dumps(descr)} (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{U()}") {eff})',
            '\t(attr smd)']

def line(x1, y1, x2, y2, layer, w):
    return f'\t(fp_line (start {F(x1)} {F(y1)}) (end {F(x2)} {F(y2)}) (stroke (width {w}) (type solid)) (layer "{layer}") (uuid "{U()}"))'

def rect(x1, y1, x2, y2, layer, w):
    return f'\t(fp_rect (start {F(x1)} {F(y1)}) (end {F(x2)} {F(y2)}) (stroke (width {w}) (type solid)) (fill no) (layer "{layer}") (uuid "{U()}"))'

def pad(num, x, y, w, h, shape='roundrect', paste=None, ratio=0.25, layers='"F.Cu" "F.Paste" "F.Mask"'):
    pr = f' (roundrect_rratio {ratio})' if shape == 'roundrect' else ''
    pm = f' (solder_paste_margin_ratio {paste})' if paste is not None else ''
    return f'\t(pad "{num}" smd {shape} (at {F(x)} {F(y)}) (size {F(w)} {F(h)}) (layers {layers}){pr}{pm} (uuid "{U()}"))'

def via(num, x, y):
    return f'\t(pad "{num}" thru_hole circle (at {F(x)} {F(y)}) (size 0.6 0.6) (drill 0.3) (layers "*.Cu" "*.Mask") (remove_unused_layers no) (zone_connect 2) (uuid "{U()}"))'

def finish(L, name, bw, bl, cx, cy, extra_note):
    hx, hy = bw / 2, bl / 2
    L.append(rect(-hx, -hy, hx, hy, 'F.Fab', 0.1))
    L.append(line(-hx, -hy + 0.5, -hx + 0.5, -hy, 'F.Fab', 0.1))
    s = 0.12; o = 0.1
    for sx in (-1, 1):
        for sy in (-1, 1):
            if sx == -1 and sy == -1: continue
            L.append(line(sx * (hx + o), sy * (hy + o), sx * (hx + o), sy * (hy + o - 0.3), 'F.SilkS', s))
            L.append(line(sx * (hx + o), sy * (hy + o), sx * (hx + o - 0.3), sy * (hy + o), 'F.SilkS', s))
    L.append(f'\t(fp_poly (pts (xy {F(-hx - 0.4)} {F(-hy - 0.1)}) (xy {F(-hx - 0.1)} {F(-hy - 0.4)}) (xy {F(-hx - 0.1)} {F(-hy - 0.1)})) (stroke (width 0.12) (type solid)) (fill yes) (layer "F.SilkS") (uuid "{U()}"))')
    L.append(rect(-cx, -cy, cx, cy, 'F.CrtYd', 0.05))
    L.append(f'\t(fp_text user "${{REFERENCE}}" (at 0 0 0) (layer "F.Fab") (uuid "{U()}") (effects (font (size 0.6 0.6) (thickness 0.09))))')
    L.append(model_block(name).rstrip('\n'))
    L.append(')')
    open(f'{PRETTY}/{name}.kicad_mod', 'w').write('\n'.join(L) + '\n')
    return '\n'.join(L)

def lqfn(name, descr, bw, bl, NL, NB, pcx, pcy, eps, epnums, h=0.94):
    """ADI/LTC LQFN, numbering: left column top->bottom, bottom row left->right, right column bottom->top, top row right->left"""
    L = fp_header(name, descr, 'LQFN Silent Switcher 2 Analog Devices', -(pcy + 0.35 + 1.0), pcy + 0.35 + 1.0)
    n = 1; e = 0.5; pl, pw = 0.70, 0.25
    for i in range(NL):
        L.append(pad(n, -pcx, -(NL - 1) * e / 2 + i * e, pl, pw)); n += 1
    for i in range(NB):
        L.append(pad(n, -(NB - 1) * e / 2 + i * e, pcy, pw, pl)); n += 1
    for i in range(NL):
        L.append(pad(n, pcx, (NL - 1) * e / 2 - i * e, pl, pw)); n += 1
    for i in range(NB):
        L.append(pad(n, (NB - 1) * e / 2 - i * e, -pcy, pw, pl)); n += 1
    for (x, y, w, hh), k in zip(eps, epnums):
        L.append(pad(k, x, y, w, hh, shape='rect', paste=-0.2))
    ox, oy = pcx + pl / 2 - 0.1875, pcy + pl / 2 - 0.1875
    for sx in (-1, 1):
        for sy in (-1, 1):
            L.append(pad('', sx * ox, sy * oy, 0.375, 0.375, shape='rect'))
    finish(L, name, bw, bl, pcx + pl / 2 + 0.25, pcy + pl / 2 + 0.25, '')
    s = open(f'{PRETTY}/{name}.kicad_mod').read()
    spec_from(name, s, 'flat', h, descr, body=(bw, bl))

def mp8795h():
    name = 'MPS_QFN-21_3x4mm_P0.4mm'
    descr = 'MPS QFN-21 (3x4mm) MO-220, MP8795H recommended land pattern (datasheet Rev1.0 p17); 0.4 pitch, VIN/SW bars, PGND comb'
    L = fp_header(name, descr, 'QFN MPS MP8795H', -3.1, 3.1)
    L.append(pad(1, -1.35, -1.70, 0.90, 0.30, ratio=0.15))
    for k in range(2, 9):
        L.append(pad(k, -1.40, -1.2 + 0.4 * (k - 2), 0.80, 0.20, ratio=0.25))
    L.append(pad(9, -1.40, 1.70, 0.80, 0.30, ratio=0.15))
    L.append(pad(10, -0.30, 1.30, 0.30, 2.00, shape='rect'))
    L.append(pad(21, -0.30, -1.30, 0.30, 2.00, shape='rect'))
    L.append(pad(20, 0.30, -1.30, 0.30, 2.00, shape='rect'))
    L.append(pad(19, 1.40, -1.70, 0.80, 0.30, ratio=0.15))
    L.append(pad(11, 1.40, 1.70, 0.80, 0.30, shape='rect'))
    for k, y in zip(range(12, 19), [1.2, 0.8, 0.4, 0.0, -0.4, -0.8, -1.2]):
        L.append(pad(k, 1.40, y, 0.80, 0.20, shape='rect'))
    L.append(pad(11, 1.175, 0.275, 0.35, 3.15, shape='rect', paste=-0.3))  # PGND backbone (same net as 11-18)
    finish(L, name, 3.0, 4.0, 2.05, 2.55, '')
    s = open(f'{PRETTY}/{name}.kicad_mod').read()
    spec_from(name, s, 'flat', 0.90, descr, body=(3.0, 4.0))

def maxim_t2044():
    name = 'Maxim_T2044-4C_TQFN-20-1EP_4x4mm_P0.5mm_EP2.85x2.85mm_ThermalVias'
    descr = 'Maxim 20L TQFN 4x4x0.75 T2044+4C (outline 21-100172), land pattern 90-0409: 0.30x0.60 pads on 3.85 mm rows, EP land 2.85'
    L = fp_header(name, descr, 'TQFN Maxim MAX17503', -3.2, 3.2)
    n = 1; e = 0.5; c = 1.925
    for i in range(5): L.append(pad(n, -c, -1.0 + i * e, 0.60, 0.30)); n += 1
    for i in range(5): L.append(pad(n, -1.0 + i * e, c, 0.30, 0.60)); n += 1
    for i in range(5): L.append(pad(n, c, 1.0 - i * e, 0.60, 0.30)); n += 1
    for i in range(5): L.append(pad(n, 1.0 - i * e, -c, 0.30, 0.60)); n += 1
    L.append(pad(21, 0, 0, 2.85, 2.85, shape='rect', paste=-0.25))
    for x in (-0.9, 0, 0.9):
        for y in (-0.9, 0, 0.9):
            L.append(via(21, x, y))
    finish(L, name, 4.0, 4.0, 2.5, 2.5, '')
    s = open(f'{PRETTY}/{name}.kicad_mod').read()
    spec_from(name, s, 'flat', 0.75, descr, body=(4.0, 4.0))

if __name__ == '__main__':
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    os.makedirs(PRETTY)
    for n, (lib, st, h, note) in COPY.items(): copy_fp(n, lib, st, h, note)
    copy_wlcsp()
    g = 0.20
    lqfn('ADI_LQFN-24_4x4mm_P0.5mm_4xEP1.125mm_LT8640S', 'Analog Devices LQFN-24 4x4x0.94 (LTC DWG 05-08-1511 Rev C), LT8640S suggested PCB layout: 0.25x0.70 pads, 4x 1.125 EP, corner support pads',
         4.0, 4.0, 6, 6, 1.90, 1.90, [(sx * 0.6625, sy * 0.6625, 1.125, 1.125) for sy in (-1, 1) for sx in (-1, 1)], [25, 26, 27, 28])
    lqfn('ADI_LQFN-32_4x6mm_P0.5mm_6xEP_LT8645S', 'Analog Devices LQFN-32 6x4x0.94 (LTC DWG 05-08-1512 Rev C), LT8645S suggested PCB layout: 0.25x0.70 pads, 6 EP segments, corner support pads',
         4.0, 6.0, 10, 6, 1.90, 2.90, [(sx * 0.6625, y, 1.125, hh) for (y, hh) in ((-1.5475, 1.355), (0, 1.34), (1.5475, 1.355)) for sx in (-1, 1)], [33, 34, 35, 36, 37, 38])
    lqfn('ADI_LQFN-36_4x7mm_P0.5mm_6xEP_LT8648S', 'Analog Devices LQFN-36 7x4x0.94 (LTC DWG 05-08-1604 Rev A), LT8648S suggested PCB layout: 0.25x0.70 pads, 6x 1.20x1.73 EP, corner support pads',
         4.0, 7.0, 12, 6, 1.90, 3.40, [(sx * 0.70, y, 1.20, 1.73) for y in (-1.93, 0, 1.93) for sx in (-1, 1)], [37, 38, 39, 40, 41, 42])
    mp8795h(); maxim_t2044()
    json.dump(specs, open(OUT + '/model_specs.json', 'w'), indent=1)
    for k, v in specs.items(): print(k, v['body'], v['h'], v['style'], len(v['pads']))
