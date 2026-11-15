"""Chinmay_XTAL.kicad_blocks: one KiCad design block per crystal / oscillator (house-common passives)."""
import os, json, uuid, re, shutil
import gen, common as CM, xtal as XT
from gen import q, eff

LIBS = json.load(open('/home/claude/buck/gen/libs.json'))
OUT = '/home/claude/xtal/blocks/Chinmay_XTAL.kicad_blocks'
U = lambda: str(uuid.uuid4())

class B:
    def __init__(self, root):
        self.root = root; self.items = []
    def wire(self, *pts):
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            self.items.append(f'(wire (pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f})) (stroke (width 0) (type default)) (uuid "{U()}"))')
    def junction(self, x, y):
        self.items.append(f'(junction (at {x:.2f} {y:.2f}) (diameter 0) (color 0 0 0 0) (uuid "{U()}"))')
    def label(self, n, x, y, a):
        j = {0: 'left bottom', 180: 'right bottom', 90: 'left bottom', 270: 'right bottom'}[a]
        self.items.append(f'(label {q(n)} (at {x:.2f} {y:.2f} {a}) (fields_autoplaced yes) {eff(j)} (uuid "{U()}"))')
    def text(self, s, x, y, size=1.27, bold=False):
        self.items.append(f'(text {q(s)} (exclude_from_sim no) (at {x:.2f} {y:.2f} 0) {eff("left top", size=size, bold=bold)} (uuid "{U()}"))')
    def sym(self, lib, ref, val, x, y, pins, ang=0, fields=(), fp='', ds='', desc='', inbom=True, dnp=False, rp=None, vp=None, hide_ref=False, hide_val=False):
        rp = rp or (x + 2, y - 2); vp = vp or (x + 2, y + 2)
        L = [f'(symbol (lib_id {q(lib)}) (at {x:.2f} {y:.2f} {ang}) (unit 1) (body_style 1) (exclude_from_sim no) (in_bom {"yes" if inbom else "no"}) '
             f'(on_board {"yes" if inbom else "no"}) (in_pos_files yes) (dnp {"yes" if dnp else "no"}) (uuid "{U()}")',
             f'  (property "Reference" {q(ref)} (at {rp[0]:.2f} {rp[1]:.2f} 0) {eff("left", hide=hide_ref)})',
             f'  (property "Value" {q(val)} (at {vp[0]:.2f} {vp[1]:.2f} 0) {eff("left", hide=hide_val)})',
             f'  (property "Footprint" {q(fp)} (at {x:.2f} {y:.2f} 0) {eff(hide=True)})',
             f'  (property "Datasheet" {q(ds)} (at {x:.2f} {y:.2f} 0) {eff(hide=True)})',
             f'  (property "Description" {q(desc)} (at {x:.2f} {y:.2f} 0) {eff(hide=True)})']
        for k, v in fields:
            L.append(f'  (property {q(k)} {q(v)} (at {x:.2f} {y:.2f} 0) {eff(hide=True)})')
        for p in pins: L.append(f'  (pin "{p}" (uuid "{U()}"))')
        L.append(f'  (instances (project "block" (path "/{self.root}" (reference {q(ref)}) (unit 1))))')
        L.append(')')
        self.items.append('\n'.join(L))
    def gnd(self, x, y, ang=0):
        self.sym('power:GND', '#PWR?', 'GND', x, y, ['1'], ang=ang, inbom=False, rp=(x, y + 6), vp=(x - 2, y + 4.2), hide_ref=True, hide_val=True)
    def write(self, path, title, libs):
        body = (f'(kicad_sch (version 20260101) (generator "eeschema") (generator_version "10.0")\n  (uuid "{self.root}")\n  (paper "A4")\n'
                f'  (title_block (title {q(title)}) (company "Chinmay"))\n  (lib_symbols\n' + '\n'.join(libs) + '\n  )\n' +
                '\n'.join(self.items) + '\n  (sheet_instances (path "/" (page "1")))\n)\n')
        open(path, 'w').write(body)

def pfields(fd):
    return [('IPN', fd['ipn'])] + gen.bomfields(fd['mfr'], fd['mpn'], fd['mfr2'], fd['mpn2'])

def crystal_block(x):
    f, lab, mpn, ser, cl, esr, c0, dlmax, fp, img, uses = x
    t, capv, cl_act, gm = XT.xtal_calc(x)
    name = f'XTAL_{XT.fmt_f(f).replace(" ", "").replace(".", "p")}_{ser.replace("-", "")}'
    b = B(U()); X, Y = 101.6, 76.2; A, Bn = X - 10.16, X + 10.16
    four = '4Pin' in fp
    lib = 'Device:Crystal_GND24_Small' if four else 'Device:Crystal_Small'
    ipn = f'XTAL-{"2520" if "2520" in fp else ("3225" if "3225" in fp else "3215")}-{lab}-{cl:g}P'
    b.sym(lib, 'Y?', XT.fmt_f(f).replace(' ', ''), X, Y, ['1', '2', '3', '4'] if four else ['1', '2'],
          fields=[('IPN', ipn)] + gen.bomfields('ECS', mpn, 'ECS', mpn), fp=fp, ds=XT.DS[ser],
          desc=f'{XT.fmt_f(f)} crystal CL {cl:g} pF ESR {esr:g} ohm ({ser})', rp=(X - 2.5, Y - 4.2), vp=(X - 3.5, Y + 6.5 if four else Y + 3.5))
    b.wire((X - 2.54, Y), (A, Y)); b.wire((X + 2.54, Y), (Bn, Y))
    cipn = {10: 'CAP-0603-10P-50V-C0G', 12: 'CAP-0603-12P-50V-C0G', 15: 'CAP-0603-15P-50V-C0G'}[int(capv)]
    cf = CM.cap_fields(cipn)
    for i, xx in enumerate((A, Bn)):
        b.sym('Device:C_Small', 'C?', cf['value'], xx, Y + 5.08, ['1', '2'], fields=pfields(cf), fp=cf['fp'],
              desc=f'{cf["desc"]} - load cap C{i+1}', rp=(xx + 1.6, Y + 4.2), vp=(xx + 1.6, Y + 6.6))
        b.wire((xx, Y), (xx, Y + 2.54)); b.gnd(xx, Y + 7.62)
    if four:
        b.wire((X, Y + 2.54), (X, Y + 7.62)); b.gnd(X, Y + 7.62)
    r0 = CM.r_fields(0)
    b.sym('Device:R_Small', 'R?', '0R', Bn + 7.62, Y, ['1', '2'], ang=90, fields=pfields(r0), fp=CM.FP['0603R'],
          desc='0R jumper - Rext drive limiter (populate value if drive level exceeded)', rp=(Bn + 5.6, Y - 3.2), vp=(Bn + 5.6, Y + 3.0))
    b.wire((Bn, Y), (Bn + 5.08, Y)); b.wire((Bn + 10.16, Y), (Bn + 15.24, Y)); b.label('XOUT', Bn + 15.24, Y, 0)
    b.wire((A, Y), (A - 7.62, Y)); b.label('XIN', A - 7.62, Y, 180)
    b.junction(A, Y); b.junction(Bn, Y)
    if f > 1e6:
        r1 = CM.r_fields(1e6)
        b.sym('Device:R_Small', 'R?', '1M', X, Y - 7.62, ['1', '2'], ang=90, fields=pfields(r1), fp=CM.FP['0603R'],
              desc='1M Rf feedback - DNP unless the oscillator has no internal feedback resistor', dnp=True, rp=(X - 2, Y - 10.6), vp=(X + 3.2, Y - 10.6))
        b.wire((X - 2.54, Y - 7.62), (A, Y - 7.62), (A, Y)); b.wire((X + 2.54, Y - 7.62), (Bn + 10.16, Y - 7.62), (Bn + 10.16, Y))
        b.junction(Bn + 10.16, Y)
    note = [f'{XT.fmt_f(f)} Pierce crystal - {mpn} (ECS {ser}), CL {cl:g} pF, ESR <= {esr:g} ohm',
            f'C1 = C2 = 2*(CL - Cs) = {capv:g} pF C0G (Cs {XT.CS:g} pF) -> CL_eff {cl_act:.1f} pF ; gm_crit = '
            + (f'{gm*1e3:.2f} mA/V (need >= {5*gm*1e3:.1f} mA/V)' if gm >= 1e-4 else f'{gm*1e6:.2f} uA/V (need >= {5*gm*1e6:.2f} uA/V)'),
            'Rext 0R (fit if drive level exceeded); Rf 1M DNP (fit only without internal feedback). Rename XIN/XOUT labels to your MCU pins.']
    b.text('\n'.join(note), A - 20.32, Y + 16.0, size=1.1)
    libs = [LIBS[lib], LIBS['Device:R_Small'], LIBS['Device:C_Small'], LIBS['power:GND']]
    meta = dict(desc=f'{XT.fmt_f(f)} crystal (ECS {mpn}) Pierce network: {capv:g} pF C0G load caps, 0R Rext, 1M Rf (DNP). {uses}.',
                kw=f'crystal xtal oscillator pierce {XT.fmt_f(f)} {lab} {mpn} {ser} ECS clock',
                fields={'Frequency': XT.fmt_f(f), 'Crystal': mpn, 'CL': f'{cl:g} pF', 'Load caps': f'{capv:g} pF C0G 0603 ({cipn})', 'Typical use': uses})
    return name, b, libs, meta

def xo_block(o):
    f, code, idd, uses = o
    mpn = f'ECS-2520MV-{code}-BN-TR'
    name = f'XO_{XT.fmt_f(f).replace(" ", "").replace(".", "p")}_ECS2520MV'
    b = B(U()); X, Y = 101.6, 76.2
    b.sym('Oscillator:ECS-2520MV-xxx-xx', 'X?', XT.fmt_f(f).replace(' ', ''), X, Y, ['1', '2', '3', '4'],
          fields=[('IPN', f'XO-2520-{code}M-CMOS-50PPM')] + gen.bomfields('ECS', mpn, 'ECS', mpn.replace('-BN-', '-CN-')),
          fp='Oscillator:Oscillator_SMD_ECS_2520MV-xxx-xx-4Pin_2.5x2.0mm', ds=XT.DS['ECS-2520MV'],
          desc=f'{XT.fmt_f(f)} HCMOS XO 1.6-3.6 V +/-50 ppm', rp=(X + 2.5, Y - 9.5), vp=(X + 2.5, Y + 9.5))
    cf = CM.cap_fields('CAP-0603-100N-50V-X7R'); r10 = CM.r_fields(10e3); r27 = CM.r_fields(27)
    # VDD node
    b.wire((X, Y - 7.62), (X, Y - 12.7)); b.wire((X, Y - 12.7), (X + 10.16, Y - 12.7)); b.label('VDD', X, Y - 12.7, 90)
    b.sym('Device:C_Small', 'C?', '100nF', X + 10.16, Y - 10.16, ['1', '2'], fields=pfields(cf), fp=cf['fp'],
          desc='100nF X7R 0603 - VDD decoupling at pin 4', rp=(X + 11.8, Y - 11.0), vp=(X + 11.8, Y - 8.6))
    b.gnd(X + 10.16, Y - 7.62)
    b.gnd(X, Y + 7.62)
    # OE pull-up
    b.sym('Device:R_Small', 'R?', '10k', X - 15.24, Y - 7.62, ['1', '2'], fields=pfields(r10), fp=CM.FP['0603R'],
          desc='10k OE pull-up (oscillator runs when OE unused)', rp=(X - 13.6, Y - 8.5), vp=(X - 13.6, Y - 6.1))
    b.wire((X - 15.24, Y - 10.16), (X - 15.24, Y - 12.7), (X, Y - 12.7))
    b.wire((X - 15.24, Y - 5.08), (X - 15.24, Y)); b.wire((X - 10.16, Y), (X - 15.24, Y), (X - 20.32, Y)); b.label('OE', X - 20.32, Y, 180)
    b.junction(X - 15.24, Y); b.junction(X, Y - 12.7)
    # series termination
    b.sym('Device:R_Small', 'R?', '27R', X + 15.24, Y, ['1', '2'], ang=90, fields=pfields(r27), fp=CM.FP['0603R'],
          desc='27R series source termination (place at XO pin 3)', rp=(X + 13.2, Y - 3.2), vp=(X + 13.2, Y + 3.0))
    b.wire((X + 10.16, Y), (X + 12.7, Y)); b.wire((X + 17.78, Y), (X + 22.86, Y)); b.label('CLK', X + 22.86, Y, 0)
    note = [f'{XT.fmt_f(f)} HCMOS XO - {mpn}, 1.6-3.6 V, +/-50 ppm (-40..85 C), IDD <= {idd:g} mA @3.3 V, load <= 15 pF',
            '100 nF at pin 4, 10k OE pull-up (OE high/open = run), 27R series termination at pin 3 (Z0 50 ohm).',
            f'Typical use: {uses}. Rename VDD / OE / CLK labels to your nets.']
    b.text('\n'.join(note), X - 25.4, Y + 14.0, size=1.1)
    libs = [LIBS['Oscillator:ECS-2520MV-xxx-xx'], LIBS['Device:R_Small'], LIBS['Device:C_Small'], LIBS['power:GND']]
    meta = dict(desc=f'{XT.fmt_f(f)} HCMOS oscillator ECS {mpn} with 100 nF decoupling, 10k OE pull-up and 27R series termination. {uses}.',
                kw=f'oscillator xo clock {XT.fmt_f(f)} {mpn} ECS-2520MV hcmos cmos',
                fields={'Frequency': XT.fmt_f(f), 'Oscillator': mpn, 'Supply': '1.6-3.6 V', 'Stability': '+/-50 ppm', 'Typical use': uses})
    return name, b, libs, meta

if __name__ == '__main__':
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    names = []
    for x in XT.XT: names.append(crystal_block(x))
    for o in XT.XO: names.append(xo_block(o))
    for name, b, libs, meta in names:
        d = os.path.join(OUT, name + '.kicad_block'); os.makedirs(d)
        b.write(os.path.join(d, name + '.kicad_sch'), name, libs)
        json.dump({'description': meta['desc'], 'keywords': meta['kw'], 'fields': meta['fields']},
                  open(os.path.join(d, name + '.json'), 'w'), indent=2)
        s = re.sub(r'"(?:[^"\\]|\\.)*"', '""', open(os.path.join(d, name + '.kicad_sch')).read())
        assert s.count('(') == s.count(')'), name
    open('/home/claude/xtal/blocks/design-block-lib-table', 'w').write(
        '(design_block_lib_table\n  (version 7)\n  (lib (name "Chinmay_XTAL")(type "KiCad")(uri "${KIPRJMOD}/Chinmay_XTAL.kicad_blocks")(options "")(descr "Chinmay crystal and oscillator design blocks"))\n)\n')
    print(len(names), [n[0] for n in names])
