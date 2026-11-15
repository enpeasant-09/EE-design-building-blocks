"""Chinmay_XTAL: crystal (Pierce) and crystal-oscillator (XO) design blocks with house-common passives."""
import os, json, math, uuid
import gen
from gen import Sheet, q, eff, snap, U
import common as CM

OUT = '/home/claude/xtal/out'; os.makedirs(OUT, exist_ok=True)
gen.OUT = OUT
IMG = '/home/claude/xtal/img'
LIBS = json.load(open('/home/claude/buck/gen/libs.json'))
PROJECT = 'Chinmay_XTAL'
CS = 2.0  # stray (pin + PCB) capacitance per side assumed, pF

DS = {'ECX-2236': 'https://ecsxtal.com/store/pdf/ECX-2236.pdf', 'ECX-2236B': 'https://ecsxtal.com/store/pdf/ECX-2236B.pdf',
      'ECX-2236B2': 'https://ecsxtal.com/store/pdf/ECX-2236B2.pdf', 'ECX-33Q': 'https://ecsxtal.com/store/pdf/ECX-33Q.pdf',
      'ECX-31B': 'https://ecsxtal.com/store/pdf/ECX-31B.pdf', 'ECS-2520MV': 'https://ecsxtal.com/store/pdf/ECS-2520MV.pdf'}
# f(Hz), label, MPN, series, CL pF, ESR max ohm, C0 max pF, DL max uW, footprint, image, uses
XT = [
 (32.768e3, '32K768', 'ECS-.327-7-34B-TR', 'ECX-31B', 7, 70e3, 1.5, 0.5, 'Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm', 'pierce32k', 'RTC / LSE, low-power timers'),
 (8e6, '8M', 'ECS-80-8-33Q-JES-TR', 'ECX-33Q', 8, 500, 7, 100, 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm', 'ecx33q', 'STM32 HSE, CAN, AVR'),
 (12e6, '12M', 'ECS-120-8-36-CKM-TR', 'ECX-2236', 8, 150, 5, 100, 'Crystal:Crystal_SMD_2520-4Pin_2.5x2.0mm', 'ecx2236', 'USB FS/HS PHYs, CH340G, NXP, RP2040'),
 (16e6, '16M', 'ECS-160-8-36CKM-TR', 'ECX-2236', 8, 80, 5, 100, 'Crystal:Crystal_SMD_2520-4Pin_2.5x2.0mm', 'ecx2236', 'AVR, STM32, nRF, CAN FD'),
 (19.2e6, '19M2', 'ECS-192-8-36CKM-TR', 'ECX-2236', 8, 80, 5, 100, 'Crystal:Crystal_SMD_2520-4Pin_2.5x2.0mm', 'ecx2236', 'Cellular / Qualcomm, i.MX ref'),
 (20e6, '20M', 'ECS-200-8-36CKM-TR', 'ECX-2236', 8, 60, 5, 100, 'Crystal:Crystal_SMD_2520-4Pin_2.5x2.0mm', 'ecx2236', 'MCUs, Sub-GHz radios'),
 (24e6, '24M', 'ECS-240-8-36B2-CKM-TR', 'ECX-2236B2', 8, 50, 3, 100, 'Crystal:Crystal_SMD_2520-4Pin_2.5x2.0mm', 'ecx2236b2', 'USB hubs, i.MX, cameras, SoCs'),
 (24.576e6, '24M576', 'ECS-245.7-10-36B2-CTM-TR', 'ECX-2236B2', 10, 50, 3, 100, 'Crystal:Crystal_SMD_2520-4Pin_2.5x2.0mm', 'ecx2236b2', 'Audio (48 kHz family), I2S/TDM'),
 (25e6, '25M', 'ECS-250-8-36CKM-TR', 'ECX-2236', 8, 60, 5, 100, 'Crystal:Crystal_SMD_2520-4Pin_2.5x2.0mm', 'ecx2236', 'Ethernet PHYs / switches'),
 (26e6, '26M', 'ECS-260-8-36CKM-TR', 'ECX-2236', 8, 60, 5, 100, 'Crystal:Crystal_SMD_2520-4Pin_2.5x2.0mm', 'ecx2236', 'Wi-Fi / BT, GNSS, ESP32-C2'),
 (27e6, '27M', 'ECS-270-8-36CKM-TR', 'ECX-2236', 8, 60, 5, 100, 'Crystal:Crystal_SMD_2520-4Pin_2.5x2.0mm', 'ecx2236', 'Video (BT.656), display bridges'),
 (32e6, '32M', 'ECS-320-8-36CKM-TR', 'ECX-2236', 8, 50, 5, 100, 'Crystal:Crystal_SMD_2520-4Pin_2.5x2.0mm', 'ecx2236', 'nRF52/53/54, BLE radios, STM32WB'),
 (38.4e6, '38M4', 'ECS-384-8-36B2-CTN-TR', 'ECX-2236B2', 8, 40, 3, 100, 'Crystal:Crystal_SMD_2520-4Pin_2.5x2.0mm', 'ecx2236b2', 'Cellular / Wi-Fi 6 / LTE modems'),
 (40e6, '40M', 'ECS-400-8-36CKM-TR', 'ECX-2236', 8, 40, 5, 100, 'Crystal:Crystal_SMD_2520-4Pin_2.5x2.0mm', 'ecx2236', 'ESP32, WLAN, RF transceivers'),
 (48e6, '48M', 'ECS-480-10-36B-CKM-TR', 'ECX-2236B', 10, 30, 3, 100, 'Crystal:Crystal_SMD_2520-4Pin_2.5x2.0mm', 'ecx2236b', 'USB (crystal-based 48 MHz), FPGA'),
]
# XO: f, code, IDD max mA @3.3V, uses
XO = [(12e6, '120', 6.0, 'USB PHY ref, MCU clock'), (24e6, '240', 7.0, 'USB hubs / SoC ref'), (25e6, '250', 7.0, 'Ethernet PHY / switch ref'),
      (26e6, '260', 7.0, 'RF / GNSS ref'), (33.3333e6, '333.3', 7.0, 'PCI / FPGA / legacy bus'), (48e6, '480', 8.0, 'USB 48 MHz ref'),
      (50e6, '500', 8.0, 'RMII 50 MHz ref, FPGA'), (100e6, '1000', 40.0, 'PCIe ref (non-SSC) / FPGA'), (125e6, '1250', 40.0, 'GbE / SERDES / FPGA')]

def fmt_f(f):
    if f < 1e6: return '%.3f kHz' % (f / 1e3)
    s = ('%.4f' % (f / 1e6)).rstrip('0').rstrip('.')
    return s + ' MHz'

def cap_for_cl(cl, cs=CS):
    v = 2 * (cl - cs)
    e12 = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
    c = []
    for d in (1, 10, 100):
        c += [x * d for x in e12]
    return min(c, key=lambda x: abs(x - v)), v

def xtal_calc(x):
    f, lab, mpn, ser, cl, esr, c0, dlmax, fp, img, uses = x
    capv, exact = cap_for_cl(cl)
    cl_act = capv / 2 + CS
    w = 2 * math.pi * f
    gm = 4 * esr * w ** 2 * ((c0 + cl) * 1e-12) ** 2
    c1m = 3e-15 if f > 1e6 else 2.0e-15
    S = c1m / (2 * ((c0 + cl_act) * 1e-12) ** 2) * 1e-12 * 1e6  # ppm per pF
    dcl = capv * 0.05 / 2
    t = [f'DESIGN EQUATIONS - {fmt_f(f)} crystal, {mpn} (ECS {ser}); refs: ST AN2867 / TI SZZA043 / TI SLAA322',
         f'Crystal: CL = {cl} pF, ESR max = {esr/1e3:g} kohm' if esr >= 1e3 else f'Crystal: CL = {cl} pF, ESR max = {esr:g} ohm' ,
         (f'  C0 max = {c0} pF, drive level max = {dlmax} uW (datasheet), fundamental mode. Uses: {uses}' if f > 1e6 else f'  C0 ~{c0} pF and DL max {dlmax} uW are typical tuning-fork values (verify on ECX-31B sheet). Uses: {uses}'),
         f'Load caps: C1 = C2 = 2*(CL - Cs), Cs = {CS} pF (pin + trace, edit for your layout) = {exact:.1f} pF -> {capv:g} pF C0G 5% (house value)',
         f'  Effective CL = C1*C2/(C1+C2) + Cs = {capv/2:g} + {CS} = {cl_act:.1f} pF ({cl_act-cl:+.1f} pF vs spec)',
         f'Pulling: S = C1m/(2*(C0+CL)^2) ~ {S:.1f} ppm/pF (C1m ~{c1m*1e15:.0f} fF typ, assumed) ; 5% cap tol -> dCL +/-{dcl:.2f} pF -> +/-{S*dcl:.1f} ppm',
         f'Oscillation margin: gm_crit = 4*ESR*(2*pi*f)^2*(C0+CL)^2 = {gm*1e3:.3f} mA/V' if gm >= 1e-4 else
         f'Oscillation margin: gm_crit = 4*ESR*(2*pi*f)^2*(C0+CL)^2 = {gm*1e6:.3f} uA/V',
         (f'  Gain margin = gm(osc)/gm_crit >= 5 -> oscillator gm must exceed {5*gm*1e3:.2f} mA/V (check MCU datasheet HSE/LSE gm)'
          if gm >= 1e-4 else f'  Gain margin >= 5 -> oscillator gm must exceed {5*gm*1e6:.2f} uA/V (check MCU LSE drive setting)')]
    for vpp in (1.0, 3.3):
        irms = w * (c0 + cl_act) * 1e-12 * vpp / (2 * math.sqrt(2))
        dl = esr * irms ** 2
        t.append(f'Drive level @ {vpp} Vpp on XOUT: DL = ESR*(2*pi*f*(C0+CL)*Vpp/(2*sqrt2))^2 = {dl*1e6:.2f} uW vs {dlmax} uW max -> '
                 + ('OK' if dl * 1e6 <= dlmax else 'EXCEEDED - fit Rext'))
    rext = 1 / (w * capv * 1e-12)
    t.append(f'Rext (series, XOUT side): start value 1/(2*pi*f*C2) = {rext/1e3:.2f} kohm ; fitted 0R (house jumper) - populate only if DL exceeded,')
    t.append('  then re-check gain margin with ESR -> ESR + Rext. Rf 1M (house) shown DNP: fit only if the oscillator has no internal feedback resistor.')
    t.append('Layout: C1/C2 and crystal within ~5 mm of the pins, GND guard ring, no signals under the crystal, return C1/C2 to the oscillator GND pin.')
    return t, capv, cl_act, gm

def cl_table(f):
    rows = []
    for cl in (6, 7, 8, 9, 10, 12.5, 18, 20):
        r = [str(cl)]
        for cs in (1.5, 2.0, 3.0, 4.0):
            v, ex = cap_for_cl(cl, cs)
            r.append('%gp' % v if ex > 0 else '-')
        rows.append(r)
    return rows

def build_xtal(x, page, su):
    f, lab, mpn, ser, cl, esr, c0, dlmax, fp, img, uses = x
    t, capv, cl_act, gm = xtal_calc(x)
    sh = Sheet(su, page); sh.path = f'/{ROOT}/{su}'
    refn = {'R': 1, 'C': 1, 'Y': 1}
    def ref(k):
        r = f'{k}{page}{refn[k]:02d}'; refn[k] += 1; return r
    four = '4Pin' in fp
    X, Y = 101.6, 76.2
    lib = 'Device:Crystal_GND24_Small' if four else 'Device:Crystal_Small'
    ipn = f'XTAL-{"2520" if "2520" in fp else ("3225" if "3225" in fp else "3215")}-{lab}-{cl:g}P'
    sh.symbol(lib, ref('Y'), fmt_f(f).replace(' ', ''), X, Y, ['1', '2', '3', '4'] if four else ['1', '2'],
              fields=[('IPN', ipn)] + gen.bomfields('ECS', mpn, 'ECS', mpn.replace('-TR', '-TR3') if mpn.endswith('-TR') else mpn),
              fp=fp, ds=DS[ser], desc=f'{fmt_f(f)} crystal CL {cl:g} pF ESR {esr:g} ohm ({ser})', refpos=(X - 3.0, Y - 4.0), valpos=(X - 4.5, Y + 4.8))
    xin, xout = X - 2.54, X + 2.54
    # XIN node at left, XOUT node at right
    sh.wire(xin, Y, xin - 20.32, Y); sh.label('XIN', xin - 20.32, Y, 180)
    sh.wire(xout, Y, xout + 20.32, Y); sh.label('XOUT_X', xout + 20.32, Y, 0)
    if four:
        sh.wire(X, Y + 2.54, X, Y + 5.08); sh.gnd(X, Y + 5.08)
    # hier labels
    sh.hlabel('XIN', 'passive', 25.4, 30.48); sh.wire(25.4, 30.48, 35.56, 30.48); sh.label('XIN', 35.56, 30.48, 0)
    sh.hlabel('XOUT', 'passive', 25.4, 35.56); sh.wire(25.4, 35.56, 35.56, 35.56); sh.label('XOUT', 35.56, 35.56, 0)
    if page == 2:
        sh.pwrflag(55.88, 30.48); sh.wire(55.88, 30.48, 55.88, 33.02); sh.gnd(55.88, 33.02)
        sh.text('GND flag: single flag for the global\nGND net of the whole library', 60.96, 30.48, size=1.0)
    sh.text('Block interface:\nXIN  - to oscillator input (OSC_IN / XTAL1 / XI)\nXOUT - to oscillator output (OSC_OUT / XTAL2 / XO)\nGND  - global ground (crystal lid pads 2/4 + C1/C2)',
            20.32, 44.45, size=1.27)
    # passives: C1 (XIN-GND), C2 (XOUT_X-GND), Rext (XOUT - XOUT_X), Rf (XIN - XOUT, DNP)
    cipn = {10: 'CAP-0603-10P-50V-C0G', 12: 'CAP-0603-12P-50V-C0G', 15: 'CAP-0603-15P-50V-C0G'}[int(capv)]
    cf = CM.cap_fields(cipn)
    items = [('C', 'XIN', 'GND', cf, 'C1 load cap (XIN)', False), ('C', 'XOUT_X', 'GND', cf, 'C2 load cap (XOUT)', False),
             ('R', 'XOUT', 'XOUT_X', CM.r_fields(0), 'Rext drive limiter (0R default)', False)]
    if f > 1e6:
        items.append(('R', 'XIN', 'XOUT', CM.r_fields(1e6), 'Rf feedback - DNP unless no internal Rf', True))
    x0 = 50.8; y0 = 106.68
    for kind, n1, n2, fd, role, dnp in items:
        r = ref(kind); cx = snap(x0)
        libid = 'Device:C_Small' if kind == 'C' else 'Device:R_Small'
        fpp = fd.get('fp', CM.FP['0603R'])
        sh.symbol(libid, r, fd['value'], cx, y0, ['1', '2'],
                  fields=[('IPN', fd['ipn'])] + gen.bomfields(fd['mfr'], fd['mpn'], fd['mfr2'], fd['mpn2']), fp=fpp, desc=f'{fd["desc"]} - {role}')
        if dnp:
            sh.items[-1] = sh.items[-1].replace('(dnp no)', '(dnp yes)', 1)
        sh.wire(cx, y0 - 2.54, cx, y0 - 5.08)
        if n1 == 'GND': sh.gnd(cx, y0 - 5.08)
        else: sh.label(n1, cx, y0 - 5.08, 90)
        sh.wire(cx, y0 + 2.54, cx, y0 + 5.08)
        if n2 == 'GND': sh.gnd(cx, y0 + 5.08)
        else: sh.label(n2, cx, y0 + 5.08, 270)
        x0 += 20.32
    sh.text(f'XTAL - {fmt_f(f)}  |  ECS {ser}  |  {mpn}  |  Pierce oscillator', 20.32, 14.0, size=2.2, bold=True)
    sh.text(f'House-common passives: load caps {capv:g} pF C0G 0603, Rext 0R jumper, Rf 1M (DNP). Typical use: {uses}.', 20.32, 19.3, size=1.27)
    sh.text('\n'.join(t), 20.32, 128.0, size=1.45)
    # images
    if img == 'pierce32k':
        w, h = sh.image(os.path.join(IMG, 'pierce32k.png'), 290.0, 65.0, 130, 85)
        sh.text('Reference circuit (TI SLAA322 Fig.4 Principle Pierce oscillator) - reproduced for internal reference.', 215.9, 65 + h / 2 + 1.5, size=1.0)
        ybot = 65 + h / 2 + 6
    else:
        w1, h1 = sh.image(os.path.join(IMG, 'pierce.png'), 255.0, 60.0, 80, 70)
        w2, h2 = sh.image(os.path.join(IMG, img + '.png'), 352.0, 60.0, 100, 75)
        sh.text('Reference: TI SZZA043 Fig.3 Pierce oscillator (left); ECS ' + ser + ' datasheet outline / pad connections (right).\nReproduced for internal design reference only.',
                215.9, 60 + max(h1, h2) / 2 + 1.5, size=1.0)
        ybot = 60 + max(h1, h2) / 2 + 7
    sh.text('Datasheet / app-note reference:', 215.9, 17.78, size=1.5, bold=True)
    # CL table
    tx, ty = 215.9, max(ybot + 4, 120.0)
    sh.text('LOAD-CAP SELECTION TABLE  C1 = C2 = 2*(CL - Cs), nearest E12 C0G', tx, ty, size=2.0, bold=True)
    cols = [('Crystal CL (pF)', 0), ('Cs = 1.5 pF', 34), ('Cs = 2 pF', 62), ('Cs = 3 pF', 90), ('Cs = 4 pF', 118)]
    ry = ty + 5.5
    for c, dx in cols: sh.text(c, tx + dx, ry, size=1.55, bold=True)
    ry += 4.0
    for r in cl_table(f):
        mark = abs(float(r[0]) - cl) < 0.01
        for (c, dx), v in zip(cols, r):
            sh.text(v + ('   <- this crystal (Cs 2 pF)' if mark and dx == 118 else ''), tx + dx, ry, size=1.55, bold=mark)
        ry += 3.4
    sh.text('House rule: MHz crystals are bought with CL = 8 pF so every MHz block uses the same 12 pF C0G cap (24.576 / 48 MHz: CL 10 pF -> 15 pF);\n'
            '32.768 kHz uses CL 7 pF -> 10 pF (same 10 pF C0G as the buck feed-forward caps). Change Cs if your layout stray differs.', tx, ry + 2, size=1.25)
    libs = [LIBS[lib], LIBS['Device:R_Small'], LIBS['Device:C_Small'], LIBS['power:GND'], LIBS['power:PWR_FLAG']]
    fname = f'XTAL_{lab}.kicad_sch'
    gen.write_sheet(fname, f'XTAL {fmt_f(f)} - {mpn}', [f'Replicates block: Pierce crystal oscillator ({ser} crystal, ECS)',
                    'House-common passives (IPN) - see root sheet', 'Calculations per ST AN2867 / TI SZZA043 / TI SLAA322'], libs, sh.items)
    return fname

def build_xo(o, page, su):
    f, code, idd, uses = o
    mpn = f'ECS-2520MV-{code}-BN-TR'
    sh = Sheet(su, page); sh.path = f'/{ROOT}/{su}'
    X, Y = 101.6, 76.2
    sh.symbol('Oscillator:ECS-2520MV-xxx-xx', f'X{page}01', fmt_f(f).replace(' ', ''), X, Y, ['1', '2', '3', '4'],
              fields=[('IPN', f'XO-2520-{code}M-CMOS-50PPM')] + gen.bomfields('ECS', mpn, 'ECS', mpn.replace('-BN-', '-CN-')),
              fp='Oscillator:Oscillator_SMD_ECS_2520MV-xxx-xx-4Pin_2.5x2.0mm', ds=DS['ECS-2520MV'],
              desc=f'{fmt_f(f)} HCMOS XO 1.6-3.6 V +/-50 ppm (ECS-2520MV)', refpos=(X + 3, Y - 9), valpos=(X + 3, Y + 9))
    sh.wire(X, Y - 7.62, X, Y - 12.7); sh.label('VDD', X, Y - 12.7, 90)
    sh.wire(X, Y + 7.62, X, Y + 10.16); sh.gnd(X, Y + 10.16)
    sh.wire(X - 10.16, Y, X - 20.32, Y); sh.label('OE', X - 20.32, Y, 180)
    sh.wire(X + 10.16, Y, X + 20.32, Y); sh.label('CLK_SRC', X + 20.32, Y, 0)
    for net, shape, yy in (('VDD', 'input', 30.48), ('OE', 'input', 35.56), ('CLK', 'output', 40.64)):
        sh.hlabel(net, shape, 25.4, yy); sh.wire(25.4, yy, 35.56, yy); sh.label(net, 35.56, yy, 0)
    sh.pwrflag(55.88, 30.48); sh.wire(55.88, 30.48, 55.88, 33.02); sh.label('VDD', 55.88, 33.02, 0)
    sh.text('Block interface:\nVDD - 1.8 / 2.5 / 3.3 V supply\nOE  - tri-state (high or open = run, low = Hi-Z)\nCLK - series-terminated clock output\nGND - global ground',
            20.32, 50.8, size=1.27)
    cf = CM.cap_fields('CAP-0603-100N-50V-X7R'); r10k = CM.r_fields(10e3); r27 = CM.r_fields(27)
    items = [('C', 'VDD', 'GND', cf, 'VDD decoupling, at pin 4'), ('R', 'VDD', 'OE', r10k, 'OE pull-up (run by default)'),
             ('R', 'CLK_SRC', 'CLK', r27, 'Series source termination')]
    x0 = 50.8; y0 = 106.68
    for i, (kind, n1, n2, fd, role) in enumerate(items):
        r = f'{kind}{page}{i+1:02d}'; cx = snap(x0)
        sh.symbol('Device:C_Small' if kind == 'C' else 'Device:R_Small', r, fd['value'], cx, y0, ['1', '2'],
                  fields=[('IPN', fd['ipn'])] + gen.bomfields(fd['mfr'], fd['mpn'], fd['mfr2'], fd['mpn2']),
                  fp=fd.get('fp', CM.FP['0603R']), desc=f'{fd["desc"]} - {role}')
        sh.wire(cx, y0 - 2.54, cx, y0 - 5.08); sh.label(n1, cx, y0 - 5.08, 90)
        sh.wire(cx, y0 + 2.54, cx, y0 + 5.08)
        if n2 == 'GND': sh.gnd(cx, y0 + 5.08)
        else: sh.label(n2, cx, y0 + 5.08, 270)
        x0 += 20.32
    tr = 7e-9; tpd = 6.0e-12  # s/mm FR-4 microstrip (eff er ~3.2)
    lcrit = tr / (6 * tpd)
    p = 3.3 * idd * 1e-3
    pdyn = 15e-12 * 3.3 ** 2 * f
    ppm = 50e-6 * f
    t = [f'DESIGN EQUATIONS - {fmt_f(f)} XO, {mpn} (ECS-2520MV datasheet)',
         f'Supply: 1.6-3.6 V ; IDD max @3.3 V = {idd:g} mA -> PDD = {p*1e3:.1f} mW ; standby (OE low) 10 uA',
         f'  Decoupling: 100 nF X7R 0603 (house) within 2 mm of pin 4 ; add 1 uF bulk if the rail is shared with switching loads',
         f'Output: HCMOS, max load 15 pF ; rise/fall 7 ns max -> knee frequency 0.35/tr = {0.35/tr/1e6:.0f} MHz',
         f'  Load power C*V^2*f = 15 pF*3.3^2*{f/1e6:g} MHz = {pdyn*1e3:.1f} mW (included in IDD limit at full load)',
         f'Termination: Rs = Z0 - Rout ~ 50 - (15..25) ohm -> 27R (house; same part as USB D+/D- series R)',
         f'  Critical length (tr/6tpd, tpd ~6 ps/mm) = {lcrit:.0f} mm ; keep fan-out to one load or use a clock buffer',
         f'Stability: +/-50 ppm all-inclusive (BN) -> +/-{ppm:.0f} Hz at {fmt_f(f)}'
         + (' ; meets Ethernet +/-100 ppm budget (PHY +/-50 ppm)' if abs(f - 25e6) < 1 or abs(f - 50e6) < 1 or abs(f - 125e6) < 1 else '')
         + (' ; USB needs +/-500 ppm (HS) - OK' if abs(f - 12e6) < 1 or abs(f - 24e6) < 1 or abs(f - 48e6) < 1 else ''),
         'OE: pin 1 high or open = output active, low = Hi-Z ; 10k pull-up keeps it running when the OE net is unused.',
         f'Typical use: {uses}']
    sh.text(f'XO - {fmt_f(f)}  |  ECS-2520MV  |  {mpn}  |  HCMOS clock oscillator', 20.32, 14.0, size=2.2, bold=True)
    sh.text('House-common passives: 100 nF decoupling, 10k OE pull-up, 27R series termination.', 20.32, 19.3, size=1.27)
    sh.text('\n'.join(t), 20.32, 128.0, size=1.45)
    w, h = sh.image(os.path.join(IMG, 'ecs2520mv.png'), 310.0, 62.0, 185, 80)
    sh.text('Datasheet reference:', 215.9, 17.78, size=1.5, bold=True)
    sh.text('Source: ECS-2520MV datasheet (Rev. 2022), p.1 - dimensions, pad connections, tri-state and current table. Internal reference only.',
            215.9, 62 + h / 2 + 1.5, size=1.0)
    tx, ty = 215.9, max(62 + h / 2 + 8, 120)
    sh.text('ECS-2520MV FREQUENCY TABLE (developed frequencies, BN = +/-50 ppm -40..85 C)', tx, ty, size=2.0, bold=True)
    cols = [('Freq', 0), ('MPN', 26), ('IDD max @3.3V', 86), ('Typical use', 116)]
    ry = ty + 5.5
    for c, dx in cols: sh.text(c, tx + dx, ry, size=1.55, bold=True)
    ry += 4
    for ff, cc, ii, uu in XO:
        mk = abs(ff - f) < 1
        for (c, dx), v in zip(cols, [fmt_f(ff), f'ECS-2520MV-{cc}-BN-TR', f'{ii:g} mA', uu + ('  <- this block' if mk else '')]):
            sh.text(v, tx + dx, ry, size=1.45, bold=mk)
        ry += 3.3
    libs = [LIBS['Oscillator:ECS-2520MV-xxx-xx'], LIBS['Device:R_Small'], LIBS['Device:C_Small'], LIBS['power:GND'], LIBS['power:PWR_FLAG']]
    fname = f'XO_{code.replace(".", "p")}.kicad_sch'
    gen.write_sheet(fname, f'XO {fmt_f(f)} - {mpn}', ['Replicates block: ECS-2520MV HCMOS XO with decoupling, OE pull-up and series termination',
                    'House-common passives (IPN) - see root sheet', 'Calculations per ECS-2520MV datasheet'], libs, sh.items)
    return fname

def root(sheets):
    items = []
    W, H = 50.8, 15.24
    for i, (name, su, fname, page, kind) in enumerate(sheets):
        col, row = i % 6, i // 6
        x = 25.4 + col * 63.5; y = 50.8 + row * 30.48
        pins = []
        pl = (('XIN', 'passive', 'L', 7.62), ('XOUT', 'passive', 'R', 7.62)) if kind == 'X' else \
             (('VDD', 'input', 'L', 5.08), ('OE', 'input', 'L', 10.16), ('CLK', 'output', 'R', 7.62))
        for pn, typ, side, dy in pl:
            px = x if side == 'L' else x + W
            items.append(f'  (no_connect (at {px:.2f} {y + dy:.2f}) (uuid "{U()}"))')
            pins.append(f'    (pin {q(pn)} {typ} (at {px:.2f} {y + dy:.2f} {180 if side == "L" else 0}) (uuid "{U()}") {eff("left" if side == "R" else "right")})')
        items.append(f'''  (sheet (at {x:.2f} {y:.2f}) (size {W} {H}) (fields_autoplaced yes)
    (stroke (width 0.1524) (type solid))
    (fill (color 0 0 0 0.0000))
    (uuid "{su}")
    (property "Sheetname" {q(name)} (at {x:.2f} {y - 0.7:.2f} 0) {eff("left bottom")})
    (property "Sheetfile" {q(fname)} (at {x:.2f} {y + H + 0.6:.2f} 0) {eff("left top")})
    (instances (project "{PROJECT}" (path "/{ROOT}" (page "{page}"))))
{chr(10).join(pins)}
  )''')
    summ = ['Chinmay XTAL library - passive crystals (Pierce) and HCMOS crystal oscillators for common digital-hardware frequencies', '',
            'Crystals (ECS): 32.768 kHz (CL 7 pF) ; 8 / 12 / 16 / 19.2 / 20 / 24 / 25 / 26 / 27 / 32 / 38.4 / 40 MHz (CL 8 pF) ; 24.576 / 48 MHz (CL 10 pF)',
            'Oscillators (ECS-2520MV, 1.6-3.6 V HCMOS, +/-50 ppm): 12 / 24 / 25 / 26 / 33.333 / 48 / 50 / 100 / 125 MHz', '',
            'HOUSE-COMMON PASSIVES (shared with WD_RST, USB2UART, BUCK and LDO libraries - every R/C carries an IPN field):',
            '  12 pF C0G 0603  CAP-0603-12P-50V-C0G   all CL 8 pF MHz crystals (also CH340G 12 MHz in USB2UART)',
            '  10 pF C0G 0603  CAP-0603-10P-50V-C0G   32.768 kHz crystal, LT8640S feed-forward',
            '  15 pF C0G 0603  CAP-0603-15P-50V-C0G   24.576 / 48 MHz (CL 10 pF) crystals',
            '  100 nF X7R 0603 CAP-0603-100N-50V-X7R  XO decoupling, every IC decoupler in all libraries (100 V version only on > 42 V nets)',
            '  0R 0603         RES-0603-0R-JUMPER     crystal Rext placeholder',
            '  1M 0603         RES-0603-1M-1%         crystal Rf (DNP), LT8640S/45S feedback top',
            '  10k 0603        RES-0603-10k-1%        XO OE pull-up, all PG / RESET / open-drain pull-ups',
            '  27R 0603        RES-0603-27R-1%        XO series termination, USB D+/D- series resistors', '',
            'Refs: page N -> N01.. (Y = crystal, X = oscillator). GND is global; one PWR_FLAG on page 2.']
    items.append(f'  (text {q(chr(10).join(summ))} (exclude_from_sim no) (at 25.4 185.0 0) {eff("left top", size=1.5)} (uuid "{U()}"))')
    items.append(f'  (text "CHINMAY CRYSTAL & OSCILLATOR DESIGN BLOCKS" (exclude_from_sim no) (at 25.4 25.4 0) {eff("left top", size=4, bold=True)} (uuid "{U()}"))')
    items.append(f'  (text "15 crystal blocks + 9 oscillator blocks. Load caps, termination and decoupling use the house-common passive set." (exclude_from_sim no) (at 25.4 33.0 0) {eff("left top", size=1.8)} (uuid "{U()}"))')
    body = f'''(kicad_sch (version 20260101) (generator "eeschema") (generator_version "10.0")
  (uuid {ROOT})
  (paper "A3")
  (title_block (title "Chinmay XTAL library") (date "2026-11-14") (rev "A") (company "Chinmay") (comment 1 "Crystal and XO design blocks - ECS parts, house-common passives") (comment 2 "Pierce crystal blocks + HCMOS XO blocks"))
  (lib_symbols
  )
{chr(10).join(items)}
  (sheet_instances
    (path "/" (page "1"))
  )
)
'''
    open(os.path.join(OUT, f'{PROJECT}.kicad_sch'), 'w').write(body)

if __name__ == '__main__':
    import re, sys
    ROOT = sys.argv[1]
    gen.ROOT_UUID = ROOT; gen.PROJECT = PROJECT
    suf = '/home/claude/xtal/sheet_uuids.json'
    sus = json.load(open(suf)) if os.path.exists(suf) else {}
    sheets = []; page = 2
    for x in XT:
        su = sus.setdefault('X' + x[1], U()); sheets.append((f'XTAL {fmt_f(x[0])}', su, build_xtal(x, page, su), page, 'X')); page += 1
    for o in XO:
        su = sus.setdefault('O' + o[1], U()); sheets.append((f'XO {fmt_f(o[0])}', su, build_xo(o, page, su), page, 'O')); page += 1
    json.dump(sus, open(suf, 'w'))
    root(sheets)
    for f in sorted(os.listdir(OUT)):
        b = open(os.path.join(OUT, f)).read(); s2 = re.sub(r'"(?:[^"\\]|\\.)*"', '""', b)
        print(f, len(b), s2.count('(') - s2.count(')'))
    for x in XT:
        t, capv, cla, gm = xtal_calc(x); print(x[1], capv, round(cla, 2), '%.3g' % gm); print('   ' + t[-5]); print('   ' + t[-4])
