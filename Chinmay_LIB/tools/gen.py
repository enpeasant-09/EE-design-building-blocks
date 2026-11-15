import uuid, json, base64, io, re, os
from PIL import Image
import calc, parts as PS

OUT = '/home/claude/buck/out'
os.makedirs(OUT, exist_ok=True)
IMGDIR = '/home/claude/buck/ds/img'
ROOT_UUID = '49f4015a-0c65-4794-9ca1-f2a45f7c9566'
PROJECT = 'Chinmay_BUCK'
LIBS = json.load(open('/home/claude/buck/gen/libs.json'))
U = lambda: str(uuid.uuid4())
G = 2.54

def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'

def snap(v):
    return round(round(v / 1.27) * 1.27, 4)

FONT = '(effects (font (size 1.27 1.27)))'
def eff(just=None, hide=False, size=1.27, bold=False):
    j = f' (justify {just})' if just else ''
    b = ' (bold yes)' if bold else ''
    return f'(effects (font (size {size} {size}){b}){j}{" (hide yes)" if hide else ""})'

TYPEMAP = {'pi': 'power_in', 'po': 'power_out', 'in': 'input', 'out': 'output', 'oc': 'open_collector',
           'pas': 'passive', 'nc': 'no_connect'}
PITCH = 5.08
HALFW = 12.7

def sym_geometry(name):
    s = PS.SYM[name]
    n = max(len(s['L']), len(s['R']))
    top = (n - 1) / 2 * PITCH
    top = round(top / G) * G
    pins = {}
    for side, lst in (('L', s['L']), ('R', s['R'])):
        for i, (pn, nums, t) in enumerate(lst):
            y = top - i * PITCH
            x = -(HALFW + G) if side == 'L' else (HALFW + G)
            pins[pn] = (side, x, y, nums, t)
    return pins, top, n

def lib_symbol(name, prefix=True):
    s = PS.SYM[name]
    pins, top, n = sym_geometry(name)
    ybox_t = top + G
    ybox_b = top - (n - 1) * PITCH - G
    full = f'Chinmay_Buck:{name}' if prefix else name
    out = [f'(symbol {q(full)} (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)']
    out.append(f'  (property "Reference" "U" (at 0 {ybox_t + 1.27:.2f} 0) {eff()})')
    out.append(f'  (property "Value" {q(name)} (at 0 {ybox_b - 1.27:.2f} 0) {eff()})')
    out.append(f'  (property "Footprint" {q(s["fp"])} (at 0 0 0) {eff(hide=True)})')
    out.append(f'  (property "Datasheet" {q(s["ds"])} (at 0 0 0) {eff(hide=True)})')
    out.append(f'  (property "Description" {q(s["desc"])} (at 0 0 0) {eff(hide=True)})')
    out.append(f'  (symbol "{name}_0_1" (rectangle (start {-HALFW} {ybox_t:.2f}) (end {HALFW} {ybox_b:.2f}) '
               f'(stroke (width 0.254) (type default)) (fill (type background))))')
    pl = []
    for pn, (side, x, y, nums, t) in pins.items():
        ang = 0 if side == 'L' else 180
        for k, num in enumerate(nums):
            typ = TYPEMAP[t] if k == 0 else ('passive' if t != 'nc' else 'no_connect')
            hid = ' (hide yes)' if k > 0 else ''
            pl.append(f'    (pin {typ} line (at {x:.2f} {y:.2f} {ang}) (length {G}){hid} (name {q(pn)} {FONT}) (number "{num}" {FONT}))')
    out.append(f'  (symbol "{name}_1_1"\n' + '\n'.join(pl) + '\n  )')
    out.append(')')
    return '\n'.join(out)

def fet_lib(prefix=True):
    """SiS468DN: Device:Q_NMOS graphics with PowerPAK 1212-8 numbering (S=1,2,3  G=4  D=5..8)"""
    base = LIBS['Device:Q_NMOS']
    full = 'Chinmay_Buck:SiS468DN' if prefix else 'SiS468DN'
    s = base.replace('(symbol "Device:Q_NMOS"', f'(symbol {q(full)}', 1)
    s = s.replace('"Q_NMOS_', '"SiS468DN_')
    s = re.sub(r'\(number "D"', '(number "5"', s)
    s = re.sub(r'\(number "G"', '(number "4"', s)
    s = re.sub(r'\(number "S"', '(number "1"', s)
    # add stacked hidden pins
    extra = ''
    for n in (2, 3):
        extra += f'(pin passive line (at 2.54 -5.08 90) (length 2.54) (hide yes) (name "S" {FONT}) (number "{n}" {FONT}))\n'
    for n in (6, 7, 8):
        extra += f'(pin passive line (at 2.54 5.08 270) (length 2.54) (hide yes) (name "D" {FONT}) (number "{n}" {FONT}))\n'
    k = s.rfind('"SiS468DN_1_1"')
    j = s.find('\n', k)
    s = s[:j + 1] + extra + s[j + 1:]
    s = re.sub(r'\(property "Value" "[^"]*"', '(property "Value" "SiS468DN"', s)
    s = re.sub(r'\(property "Footprint" "[^"]*"', '(property "Footprint" "Package_SO:Vishay_PowerPAK_1212-8_Single"', s)
    return s

# ---------------------------------------------------------------- BOM helpers
def r_codes(v):
    m = re.match(r'([\d.]+)([kMR]?)', v)
    x = float(m.group(1)); u = m.group(2)
    ohm = x * {'k': 1e3, 'M': 1e6, 'R': 1, '': 1}[u]
    # yageo
    if ohm < 1e3: yc = ('%g' % ohm).replace('.', 'R') if '.' in '%g' % ohm else '%gR' % ohm
    elif ohm < 1e6: yc = ('%g' % (ohm / 1e3)).replace('.', 'K') if '.' in '%g' % (ohm / 1e3) else '%gK' % (ohm / 1e3)
    else: yc = ('%g' % (ohm / 1e6)).replace('.', 'M') if '.' in '%g' % (ohm / 1e6) else '%gM' % (ohm / 1e6)
    yageo = f'RC0603FR-07{yc}L'
    if ohm < 10:
        pc = ('%.2f' % ohm).replace('.', 'R')
    else:
        e = 0; mant = ohm
        while mant >= 1000: mant /= 10; e += 1
        while mant < 100: mant *= 10; e -= 1
        pc = '%03d%d' % (round(mant), e)
    pana = f'ERJ-3EKF{pc}V'
    return yageo, pana

def bomfields(mfr, mpn1, mfr2, mpn2, cost='TBD'):
    dk = f'https://www.digikey.in/en/products/result?keywords={mpn1}'
    mo = f'https://www.mouser.in/c/?q={mpn1}'
    return [('Manufacturer', mfr), ('MPN1', mpn1), ('MFR2', mfr2), ('MPN2', mpn2),
            ('Procurement', dk), ('Procurement2', mo), ('Cost', cost)]

# ---------------------------------------------------------------- schematic writer
class Sheet:
    def __init__(self, sheet_uuid, page):
        self.items = []
        self.sheet_uuid = sheet_uuid
        self.page = page
        self.pwr = 1
        self.path = f'/{ROOT_UUID}/{sheet_uuid}'

    def wire(self, x1, y1, x2, y2):
        self.items.append(f'(wire (pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f})) (stroke (width 0) (type default)) (uuid "{U()}"))')

    def label(self, net, x, y, ang):
        just = {0: 'left bottom', 180: 'right bottom', 90: 'left bottom', 270: 'right bottom'}[ang]
        self.items.append(f'(label {q(net)} (at {x:.2f} {y:.2f} {ang}) (fields_autoplaced yes) {eff(just)} (uuid "{U()}"))')

    def hlabel(self, net, shape, x, y):
        self.items.append(f'(hierarchical_label {q(net)} (shape {shape}) (at {x:.2f} {y:.2f} 180) (fields_autoplaced yes) {eff("right")} (uuid "{U()}"))')

    def nc(self, x, y):
        self.items.append(f'(no_connect (at {x:.2f} {y:.2f}) (uuid "{U()}"))')

    def text(self, s, x, y, size=1.27, bold=False):
        self.items.append(f'(text {q(s)} (exclude_from_sim no) (at {x:.2f} {y:.2f} 0) {eff("left top", size=size, bold=bold)} (uuid "{U()}"))')

    def symbol(self, lib_id, ref, value, x, y, pins, fields=(), fp='', ds='', desc='', ang=0, inbom=True, refpos=None, valpos=None, hide_ref=False):
        rp = refpos or (x + 1.778, y - 1.27)
        vp = valpos or (x + 1.778, y + 1.27)
        L = [f'(symbol (lib_id {q(lib_id)}) (at {x:.2f} {y:.2f} {ang}) (unit 1) (body_style 1) (exclude_from_sim no) '
             f'(in_bom {"yes" if inbom else "no"}) (on_board {"yes" if inbom else "no"}) (in_pos_files yes) (dnp no) (uuid "{U()}")']
        L.append(f'  (property "Reference" {q(ref)} (at {rp[0]:.2f} {rp[1]:.2f} 0) {eff("left", hide=hide_ref)})')
        L.append(f'  (property "Value" {q(value)} (at {vp[0]:.2f} {vp[1]:.2f} 0) {eff("left")})')
        L.append(f'  (property "Footprint" {q(fp)} (at {x:.2f} {y:.2f} 0) {eff(hide=True)})')
        L.append(f'  (property "Datasheet" {q(ds)} (at {x:.2f} {y:.2f} 0) {eff(hide=True)})')
        L.append(f'  (property "Description" {q(desc)} (at {x:.2f} {y:.2f} 0) {eff(hide=True)})')
        for k, v in fields:
            L.append(f'  (property {q(k)} {q(v)} (at {x:.2f} {y:.2f} 0) {eff(hide=True)})')
        for p in pins:
            L.append(f'  (pin "{p}" (uuid "{U()}"))')
        L.append(f'  (instances (project "{PROJECT}" (path "{self.path}" (reference {q(ref)}) (unit 1))))')
        L.append(')')
        self.items.append('\n'.join(L))

    def gnd(self, x, y, ang=0):
        ref = '#PWR%d%02d' % (self.page, self.pwr); self.pwr += 1
        vp = (x - 2.0, y + 4.2) if ang == 0 else ((x - 9.0, y + 0.5) if ang == 270 else (x + 4.5, y + 0.5))
        self.symbol('power:GND', ref, 'GND', x, y, ['1'], inbom=False, refpos=(x, y + 6.35), valpos=vp, hide_ref=True, ang=ang)

    def pwrflag(self, x, y):
        ref = '#FLG%d%02d' % (self.page, self.pwr); self.pwr += 1
        self.symbol('power:PWR_FLAG', ref, 'PWR_FLAG', x, y, ['1'], inbom=False, refpos=(x, y - 4.5), valpos=(x - 3.5, y - 3.2), hide_ref=True)

    def image(self, path, cx, cy, wmax, hmax):
        im = Image.open(path).convert('L')
        im = im.point(lambda v: 255 if v > 245 else v)
        bio = io.BytesIO(); im.save(bio, 'PNG', optimize=True, dpi=(300, 300))
        wmm = im.width / 300 * 25.4; hmm = im.height / 300 * 25.4
        sc = min(wmax / wmm, hmax / hmm)
        b = base64.b64encode(bio.getvalue()).decode()
        chunks = '\n'.join('    "%s"' % b[i:i + 76] for i in range(0, len(b), 76))
        self.items.append(f'(image (at {cx:.2f} {cy:.2f}) (scale {sc:.4f}) (uuid "{U()}")\n  (data\n{chunks}\n  )\n)')
        return wmm * sc, hmm * sc

def write_sheet(fname, title, comments, libsyms, items):
    hdr = [f'(kicad_sch (version 20260101) (generator "eeschema") (generator_version "10.0")',
           f'  (uuid "{U()}")', '  (paper "A3")',
           f'  (title_block (title {q(title)}) (date "2026-11-14") (rev "A") (company "Chinmay")']
    for i, c in enumerate(comments, 1):
        hdr.append(f'    (comment {i} {q(c)})')
    hdr.append('  )')
    body = '\n'.join(hdr) + '\n  (lib_symbols\n' + '\n'.join(libsyms) + '\n  )\n' + '\n'.join(items) + '\n)\n'
    assert body.count('(') - body.count('\\(') >= 0
    open(os.path.join(OUT, fname), 'w').write(body)
    return body

# ---------------------------------------------------------------- one block
IC_X, IC_Y = 116.84, 66.04

def build_block(name, page, sheet_uuid):
    t, table, prt = calc.DESIGNS[name]()
    sh = Sheet(sheet_uuid, page)
    s = PS.SYM[name]
    pins, top, n = sym_geometry(name)
    refn = {'R': 1, 'C': 1, 'L': 1, 'Q': 1}
    def ref(k):
        r = f'{k}{page}{refn[k]:02d}'; refn[k] += 1; return r
    # IC
    mfr, mpn1, mfr2, mpn2 = PS.IC_BOM[name]
    allnums = [str(nn) for (_, _, _, nums, _) in pins.values() for nn in nums]
    sh.symbol(f'Chinmay_Buck:{name}', f'U{page}01', name, IC_X, IC_Y, allnums,
              fields=bomfields(mfr, mpn1, mfr2, mpn2), fp=s['fp'], ds=s['ds'], desc=s['desc'],
              refpos=(IC_X - 2.54, IC_Y - top - 5.08), valpos=(IC_X - 4.0, IC_Y + top + 5.6))
    pn_map = PS.PINNET[name]
    for pn, (side, x, y, nums, tp) in pins.items():
        net = pn_map[pn]
        px, py = IC_X + x, IC_Y - y
        if net == 'NC':
            sh.nc(px, py); continue
        dx = -7.62 if side == 'L' else 7.62
        sh.wire(px, py, px + dx, py)
        if net == 'GND':
            sh.gnd(px + dx, py, ang=270 if side == 'L' else 90)
        else:
            sh.label(net, px + dx, py, 180 if side == 'L' else 0)
    # interface: hier labels + local labels
    hy = 30.48
    for net, shape in (('VIN', 'input'), ('EN', 'input'), ('VOUT', 'output'), ('PG', 'output')):
        sh.hlabel(net, shape, 25.4, hy); sh.wire(25.4, hy, 35.56, hy); sh.label(net, 35.56, hy, 0)
        hy += 5.08
    # PWR flags
    fx = 22.86
    for net in ('VIN', 'VOUT'):
        pass
    sh.pwrflag(55.88, 30.48); sh.wire(55.88, 30.48, 55.88, 33.02); sh.label('VIN', 55.88, 33.02, 0)
    sh.pwrflag(55.88, 40.64); sh.wire(55.88, 40.64, 55.88, 43.18); sh.label('VOUT', 55.88, 43.18, 0)
    if page == 2:
        sh.pwrflag(55.88, 50.8); sh.wire(55.88, 50.8, 55.88, 53.34); sh.gnd(55.88, 53.34)
        sh.text('GND flag: single flag for the global\nGND net of the whole library', 60.96, 50.8, size=1.0)
    sh.text('Block interface:\nVIN  - input rail\nEN   - enable / UVLO node\n        (pull low = off)\nVOUT - regulated output\nPG   - open-drain power good\n        (pulled up to VOUT)',
            20.32, 62.23, size=1.27)
    # passives
    plist = PS.passives(name, prt)
    x = 22.86; y = 116.84; row = 0
    for p in plist:
        k = p['kind']
        w = 30.48 if k == 'Q' else 12.7
        if x + w > 205:
            row += 1; x = 22.86; y = 116.84 + row * 30.48
        cx = snap(x + (5.08 if k == 'Q' else 0)); cy = y
        r = ref(k)
        if k in 'RCL':
            lib = {'R': 'Device:R_Small', 'C': 'Device:C_Small', 'L': 'Device:L_Small'}[k]
            if k == 'R':
                yc, pc = r_codes(p['value'])
                fp = 'Resistor_SMD:R_0603_1608Metric'
                fields = bomfields('Yageo', yc, 'Panasonic', pc); desc = f'{p["value"]} 1% 0603 resistor - {p["role"]}'
            else:
                c = PS.CAT[p['spec']]
                fp = c[0]; fields = bomfields(c[1], c[2], c[3], c[4]); desc = f'{c[5]} - {p["role"]}'
            sh.symbol(lib, r, p['value'], cx, cy, ['1', '2'], fields=fields, fp=fp, desc=desc)
            # pin1 top
            sh.wire(cx, cy - 2.54, cx, cy - 5.08)
            if p['n1'] == 'GND':
                sh.gnd(cx, cy - 5.08)
            else:
                sh.label(p['n1'], cx, cy - 5.08, 90)
            sh.wire(cx, cy + 2.54, cx, cy + 5.08)
            if p['n2'] == 'GND':
                sh.gnd(cx, cy + 5.08)
            else:
                sh.label(p['n2'], cx, cy + 5.08, 270)
        else:  # Q : D=SW top, G=DLG left, S=GND bottom
            c = PS.CAT['SiS468DN']
            sh.symbol('Chinmay_Buck:SiS468DN', r, 'SiS468DN', cx, cy, [str(i) for i in range(1, 9)],
                      fields=bomfields(c[1], c[2], c[3], c[4]), fp=c[0], desc=c[5], refpos=(cx + 5.08, cy - 1.27), valpos=(cx + 5.08, cy + 1.27))
            sh.wire(cx + 2.54, cy - 5.08, cx + 2.54, cy - 7.62); sh.label('SW', cx + 2.54, cy - 7.62, 90)
            sh.wire(cx - 5.08, cy, cx - 7.62, cy); sh.label('DLG', cx - 7.62, cy, 180)
            sh.wire(cx + 2.54, cy + 5.08, cx + 2.54, cy + 7.62); sh.gnd(cx + 2.54, cy + 7.62)
        x += w
    lastrow_y = y
    # heading
    sh.text(f'BUCK - {name}  |  {PS.MFR[name]}  |  {s["desc"]}', 20.32, 14.0, size=2.2, bold=True)
    sh.text('Default build: VOUT = 3.3 V (fixed resistor divider - no trimmer). Other outputs: change only R_top/R_bot (and L where shown) per the VOUT table.',
            20.32, 19.3, size=1.27)
    # calculations
    ty = lastrow_y + 17.78
    sh.text('\n'.join(t), 20.32, ty, size=1.45)
    # image(s)
    imgs = PS.IMG[name]
    if len(imgs) == 1:
        fn, cap = imgs[0]
        w, h = sh.image(os.path.join(IMGDIR, fn), 310.0, 22.0 + 60.0, 190, 116)
        sh.text('Datasheet application schematic (reference):', 215.9, 17.78, size=1.5, bold=True)
        sh.text('Source: ' + cap + ' - reproduced for internal design reference only.', 215.9, 22.0 + 60.0 + h / 2 + 1.5, size=1.0)
        img_bottom = 22.0 + 60.0 + h / 2 + 5
    else:
        (f1, c1), (f2, c2) = imgs
        w1, h1 = sh.image(os.path.join(IMGDIR, f1), 263.0, 60.0, 94, 70)
        w2, h2 = sh.image(os.path.join(IMGDIR, f2), 361.0, 22.0 + 58.0, 94, 116)
        sh.text('Datasheet application schematic + recommended values (reference):', 215.9, 17.78, size=1.5, bold=True)
        sh.text('Source: ' + c1 + '\nSource: ' + c2 + '\nReproduced for internal design reference only.', 215.9, 60.0 + h1 / 2 + 2, size=1.0)
        img_bottom = max(22 + 58 + h2 / 2, 70 + h1 / 2 + 8) + 4
    # VOUT table
    tx, ty0 = 215.9, max(img_bottom + 4, 150.0)
    rtn, rbn = prt['R_top'][0], prt['R_bot'][0]
    sh.text(f'VOUT PROGRAMMING TABLE  (E96 1% resistors; {rtn} = VOUT->FB, {rbn} = FB->GND)', tx, ty0, size=2.0, bold=True)
    cols = [('VOUT (V)', 0), (f'{rtn}', 22), (f'{rbn}', 44), ('VOUT actual', 66), ('Error', 94), ('L (suggested)', 116), ('VIN min (V)', 146)]
    ry = ty0 + 5.5
    for c, dx in cols:
        sh.text(c, tx + dx, ry, size=1.27, bold=True)
    ry += 3.2
    for v, a, b, va, lv, vmin in table:
        mark = '  <- FITTED' if abs(v - 3.3) < 0.01 else ''
        vals = ['%g' % v, a, b, '%.3f' % va, '%+.2f%%' % ((va / v - 1) * 100), lv, vmin + mark]
        for (c, dx), val in zip(cols, vals):
            sh.text(val, tx + dx, ry, size=1.7, bold=bool(mark))
        ry += 3.6
    note = TABLE_NOTE.get(name, '')
    if note:
        sh.text(note, tx, ry + 2.0, size=1.3)
    # write
    libsyms = [lib_symbol(name), LIBS['Device:R_Small'], LIBS['Device:C_Small'], LIBS['Device:L_Small'],
               LIBS['power:GND'], LIBS['power:PWR_FLAG']]
    if name == 'MAX17506':
        libsyms.append(fet_lib())
    title = f'BUCK {name} - {s["desc"].split(",")[0].replace(" (ext. LS FET)", "")}'
    fname = f'BUCK_{name}.kicad_sch'
    write_sheet(fname, title, [f'Replicates block: {PS.MFR[name]} {name} datasheet typical application',
                               'Default VOUT 3.3 V - see VOUT programming table for other outputs',
                               'Calculations per datasheet Applications Information section'], libsyms, sh.items)
    return fname

TABLE_NOTE = {
 'MAX17503': 'Note: MAX17503 top resistor R3 = 216e3/(fC*COUT_eff) depends on the fitted output capacitance. Non-3.3 V rows assume\nCOUT_eff = minimum from the 50%-step / 3% transient equation; fit capacitors with at least that DC-bias-derated value.\nL column = VOUT/fSW (E12). VIN min ~ VOUT/(1 - fSW*tOFF_MIN) + IR drop.',
 'MAX17506': 'Note: R3 = 451e3/(fC*COUT_SEL) depends on fitted COUT (derated). Non-3.3 V rows assume COUT_SEL = minimum from the\n50%-step / 3% transient equation. VOUT >= 4.84 V: tie EXTVCC to VOUT via 4.7R + 0.1uF (datasheet) for efficiency.',
 'MAX17761': 'Note: R4 = 15*VOUT/0.8 kOhm (datasheet); re-check R6/C6 with the new R4/R5 and COUT. L = 2.6*VOUT/fSW (PFM/1.6 A).\nVOUT >= 5 V: EXTVCC may be tied to VOUT for efficiency (datasheet).',
 'RAA211630': 'Note: RFB2 fixed at 20k per datasheet; L and COUT per datasheet Sec 2.3 table (400 kHz) where listed, else EQ.6 with 25% ripple.',
 'RAA211450': 'Note: RFB2 fixed at 20k per datasheet; L and COUT per datasheet Sec 2.3 table (400 kHz) where listed, else EQ.6 with 25% ripple.',
 'LT8640S': 'Note: R1 fixed at 1M (low IQ); L = (VOUT+0.15)/fSW*0.7 (E12). For VOUT > 5 V check fSW vs tON_MIN and COUT rating.',
 'LT8645S': 'Note: R1 fixed at 1M (low IQ); L = (VOUT+0.2)/fSW*0.4 (E12). For VOUT > 5 V check fSW vs tON_MIN and COUT rating.',
 'LT8648S': 'Note: R1 fixed at 100k; L = (VOUT+0.07)/fSW*0.2 (E12) - datasheet Fig.10 uses 2.2 uH at 3.3 V. Re-tune RC/CC for other VOUT.',
 'MP8795H': 'Note: RFB1 fixed at 20k; keep CFF zero in 20-60 kHz. L for 30% ripple at 12 V (16 V for VOUT >= 8 V). VOUT max 0.9*VIN.',
}

# ---------------------------------------------------------------- root
def build_root(sheets):
    items = []
    W, H = 76.2, 25.4
    for i, (name, su, fname, page) in enumerate(sheets):
        col, row = i % 3, i // 3
        x = 30.48 + col * 127.0; y = 63.5 + row * 50.8
        pins = []
        for pn, typ, side, dy in (('VIN', 'input', 'L', 7.62), ('EN', 'input', 'L', 12.7), ('VOUT', 'output', 'R', 7.62), ('PG', 'output', 'R', 12.7)):
            px = x if side == 'L' else x + W
            items.append(f'  (no_connect (at {px:.2f} {y + dy:.2f}) (uuid "{U()}"))')
            pins.append(f'    (pin {q(pn)} {typ} (at {px:.2f} {y + dy:.2f} {180 if side == "L" else 0}) (uuid "{U()}") {eff("left" if side == "R" else "right")})')
        items.append(f'''  (sheet (at {x:.2f} {y:.2f}) (size {W} {H}) (fields_autoplaced yes)
    (stroke (width 0.1524) (type solid))
    (fill (color 0 0 0 0.0000))
    (uuid "{su}")
    (property "Sheetname" {q("BUCK " + name)} (at {x:.2f} {y - 0.7:.2f} 0) {eff("left bottom")})
    (property "Sheetfile" {q(fname)} (at {x:.2f} {y + H + 0.6:.2f} 0) {eff("left top")})
    (instances (project "{PROJECT}" (path "/{ROOT_UUID}" (page "{page}"))))
{chr(10).join(pins)}
  )''')
    summary = ['Chinmay BUCK design-block library - adjustable synchronous buck regulators, multi-vendor (non-TI picks)',
               '',
               'Page  Block       Vendor                     IOUT   VIN range     fSW (default)  Notes',
               ' 2    MAX17761    Analog Devices (Maxim)     1 A    4.5-76 V      400 kHz        PFM, ext. comp R-C',
               ' 3    MAX17503    Analog Devices (Maxim)     2.5 A  4.5-60 V      500 kHz        internal comp',
               ' 4    RAA211630   Renesas                    3 A    4.5-60 V      400 kHz        HTSSOP-16, adj. SS',
               ' 5    MAX17506    Analog Devices (Maxim)     5 A    4.5-60 V      450 kHz        external LS FET (SiS468DN)',
               ' 6    RAA211450   Renesas                    5 A    4.5-42 V      400 kHz        HTSSOP-16, adj. SS',
               ' 7    LT8640S     Analog Devices (LTC)       6 A    3.4-42 V      1 MHz          Silent Switcher 2',
               ' 8    LT8645S     Analog Devices (LTC)       8 A    3.4-65 V      500 kHz        Silent Switcher 2',
               ' 9    LT8648S     Analog Devices (LTC)       15 A   3-42 V        400 kHz        Silent Switcher 2, ext. VC comp',
               '10    MP8795H     Monolithic Power Systems   20 A   4-16 V        600 kHz        COT, remote sense, prog. ILIM',
               '',
               'Conventions: every block defaults to VOUT = 3.3 V with a fixed E96 divider (no trimmers); each sheet carries a VOUT table',
               '(1.8 / 2.5 / 3.3 / 5 / 12 / 15 / 24 V as the part allows), the datasheet application schematic, and the full calculation set.',
               'Interface pins on every block: VIN, EN (UVLO divider node, pull low to disable), VOUT, PG (open drain, pulled up to VOUT).',
               'Reference designators: page N -> N01.. (e.g. U201, R1001). UVLO/EN turn-on set to ~6 V on all blocks (edit divider to change).',
               'BOM fields per part: Manufacturer, MPN1, MFR2, MPN2, Procurement (digikey.in), Procurement2 (mouser.in), Cost.',
               'Library symbols: Chinmay_Buck.kicad_sym (project library). LQFN (ADI) and QFN-21 (MPS) footprints are not in the KiCad stock',
               'libraries - Footprint field left empty on U701/U801/U901/U1001; create from the vendor package drawing before layout.',
               'Thermal results on each sheet assume 85 C ambient worst case; see the TA(max) figure per block.']
    items.append(f'  (text {q(chr(10).join(summary))} (exclude_from_sim no) (at 30.48 205.0 0) {eff("left top", size=1.5)} (uuid "{U()}"))')
    rs = Sheet('x', 1); rs.path = f'/{ROOT_UUID}'
    items += rs.items
    items.append(f'  (text "CHINMAY BUCK REGULATOR DESIGN BLOCKS" (exclude_from_sim no) (at 30.48 25.4 0) {eff("left top", size=4, bold=True)} (uuid "{U()}"))')
    items.append(f'  (text "Nine hierarchical blocks, ordered by output current (1 A -> 20 A). Open a block for its calculations, VOUT table and datasheet reference." (exclude_from_sim no) (at 30.48 33.0 0) {eff("left top", size=1.8)} (uuid "{U()}"))')
    body = f'''(kicad_sch (version 20260101) (generator "eeschema") (generator_version "10.0")
  (uuid {ROOT_UUID})
  (paper "A3")
  (title_block (title "Chinmay BUCK library") (date "2026-11-14") (rev "A") (company "Chinmay") (comment 1 "Adjustable buck regulator design blocks - ADI/Maxim, ADI/LTC, Renesas, MPS - Nov 2026") (comment 2 "Default VOUT 3.3 V on all blocks"))
  (lib_symbols
{LIBS['power:GND']}
{LIBS['power:PWR_FLAG']}
  )
{chr(10).join(items)}
  (sheet_instances
    (path "/" (page "1"))
  )
)
'''
    open(os.path.join(OUT, f'{PROJECT}.kicad_sch'), 'w').write(body)

def build_lib():
    syms = [lib_symbol(n, prefix=False) for n in PS.ORDER] + [fet_lib(prefix=False)]
    open(os.path.join(OUT, 'Chinmay_Buck.kicad_sym'), 'w').write(
        '(kicad_symbol_lib (version 20251024) (generator "chinmay_gen") (generator_version "10.0")\n' + '\n'.join(syms) + '\n)\n')
    open(os.path.join(OUT, 'sym-lib-table'), 'w').write(
        '(sym_lib_table\n  (version 7)\n  (lib (name "Chinmay_Buck")(type "KiCad")(uri "${KIPRJMOD}/Chinmay_Buck.kicad_sym")(options "")(descr "Chinmay buck regulator symbols"))\n)\n')

if __name__ == '__main__':
    import sys
    only = sys.argv[1:] or PS.ORDER
    sheets = []
    su_file = '/home/claude/buck/gen/sheet_uuids.json'
    sus = json.load(open(su_file)) if os.path.exists(su_file) else {}
    for i, name in enumerate(PS.ORDER):
        page = i + 2
        su = sus.setdefault(name, U())
        fname = f'BUCK_{name}.kicad_sch'
        if name in only:
            build_block(name, page, su)
        sheets.append((name, su, fname, page))
    json.dump(sus, open(su_file, 'w'))
    build_root(sheets)
    build_lib()
    for f in sorted(os.listdir(OUT)):
        b = open(os.path.join(OUT, f)).read()
        # paren balance ignoring strings
        s2 = re.sub(r'"(?:[^"\\]|\\.)*"', '""', b)
        print(f, len(b), s2.count('(') - s2.count(')'))
