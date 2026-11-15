"""Chinmay_LDO: pin-compatible 3-terminal adjustable LDO design blocks (default VOUT = 1.8 V)."""
import os, json, math
import gen
from gen import Sheet, q, eff, snap, U, r_codes, bomfields, FONT, G
from calc import nearest, E96, fr

OUT = '/home/claude/ldo/out'; os.makedirs(OUT, exist_ok=True)
gen.OUT = OUT
gen.ROOT_UUID = ROOT = '93d23cb7-77c0-4b26-969d-02a4cbfcc2d3'
gen.PROJECT = PROJECT = 'Chinmay_LDO'
IMGDIR = '/home/claude/ldo/ds/img'
LIBS = json.load(open('/home/claude/buck/gen/libs.json'))
E24 = [1.0,1.1,1.2,1.3,1.5,1.6,1.8,2.0,2.2,2.4,2.7,3.0,3.3,3.6,3.9,4.3,4.7,5.1,5.6,6.2,6.8,7.5,8.2,9.1]
VOUT_DEF = 1.8
STD = [1.2, 1.5, 1.8, 2.5, 3.3, 5.0, 12.0]

FP_SOT223 = 'Package_TO_SOT_SMD:SOT-223-3_TabPin2'
FP_TO263 = 'Package_TO_SOT_SMD:TO-263-3_TabPin2'
P = dict(
 TLV1117=dict(mfr='Texas Instruments', mpn='TLV1117IDCYR', mfr2='STMicroelectronics', mpn2='LD1117STR (pin-compatible)', pkg='SOT-223', fp=FP_SOT223,
   adjname='ADJ/GND', iout=0.8, vinmax=15, vref=1.25, iadj=60e-6, iadj_max=120e-6, imin=5e-3, vdo=1.3, vdo_note='1.3 V max @ 0.8 A (C-grade; I-grade 1.4 V)',
   ilim='0.8 A min / 1.2 A typ', theta=61.6, theta_src='DCY, adj new chip, JEDEC', iq=None,
   doc='TI TLV1117 datasheet SLVS561O (Jun 2025)', img=('TLV1117.png', 'TI TLV1117 datasheet SLVS561O, p.25, Figure 7-2 Basic Adjustable Regulator'),
   ds='https://www.ti.com/lit/ds/symlink/tlv1117.pdf', desc='15V 800mA adjustable LDO, SOT-223',
   cout=('100uF', 'tant100u10D', 'COUT (tantalum, ESR 0.2-10 ohm per datasheet Note A)'), cin=('10uF', 'c10u25v1206', 'CIN'),
   cadj=('10uF', 'c10u25v1206', 'CADJ (optional, PSRR; COUT must be > CADJ)'), diode=True, R1=124.0,
   capnote='Adjustable version is specified stable with tantalum / Al-electrolytic COUT, ESR 0.2-10 ohm (Note A). Do NOT use only MLCC on the output.'),
 NCP1117=dict(mfr='onsemi', mpn='NCP1117STAT3G', mfr2='onsemi', mpn2='NCV1117STAT3G (AEC-Q100)', pkg='SOT-223', fp=FP_SOT223,
   adjname='ADJ', iout=1.0, vinmax=20, vref=1.25, iadj=52e-6, iadj_max=120e-6, imin=5e-3, vdo=1.2, vdo_note='1.2 V max @ 0.8 A (over temp)',
   ilim='1.0 A min / 1.5 A typ', theta=160, theta_src='SOT-223 minimum pad; ~70 C/W with 1 in2 Cu (Fig.21)', iq=None,
   doc='onsemi NCP1117/D datasheet', img=('NCP1117.png', 'onsemi NCP1117/D datasheet, p.9, Figure 24 Adjustable Output Regulator'),
   ds='https://www.onsemi.com/pdf/datasheet/ncp1117-d.pdf', desc='20V 1A adjustable LDO, SOT-223',
   cout=('47uF', 'tpoly47u10B', 'COUT (>=4.7uF, ESR 33 mohm-2.2 ohm)'), cin=('10uF', 'c10u25v1206', 'CIN'),
   cadj=('10uF', 'c10u25v1206', 'CADJ (optional; Cadj > 1/(2pi f R1))'), diode=False, R1=124.0,
   capnote='COUT >= 4.7 uF with ESR 33 mohm (typ) to 2.2 ohm; ceramic, tantalum or Al allowed if inside the ESR window (Fig.12/13).'),
 AZ1117C=dict(mfr='Diodes Incorporated', mpn='AZ1117CH-ADJTRG1', mfr2='STMicroelectronics', mpn2='LD1117STR (pin-compatible)', pkg='SOT-223 (H)', fp=FP_SOT223,
   adjname='ADJ', iout=0.8, vinmax=18, vref=1.25, iadj=60e-6, iadj_max=120e-6, imin=5e-3, vdo=1.3, vdo_note='1.3 V max @ 0.8 A',
   ilim='1.0 A min / 1.35 A typ', theta=125, theta_src='SOT-223 without heatsink; 100 C/W with heatsink pad', iq=None,
   doc='Diodes AZ1117C datasheet DS36676 Rev.5-2', img=('AZ1117C.png', 'Diodes AZ1117C datasheet DS36676 Rev.5-2, p.3, Typical Applications Circuit (ADJ)'),
   ds='https://www.diodes.com/assets/Datasheets/AZ1117C.pdf', desc='18V 1A (0.8A spec) adjustable LDO, SOT-223',
   cout=('22uF', 'c22u10v1206', 'COUT (MLCC OK, >=10uF, ESR < 20 ohm)'), cin=('10uF', 'c10u25v1206', 'CIN'),
   cadj=None, diode=False, R1=124.0,
   capnote='Low-ESR ceramic output capacitor allowed; minimum 10 uF, ESR < 20 ohm (Note 4).'),
 LT3080=dict(mfr='Analog Devices', mpn='LT3080EST#PBF', mfr2='Analog Devices', mpn2='LT3080IST#PBF', pkg='SOT-223 (ST, 3-lead)', fp=FP_SOT223,
   adjname='SET', iout=1.1, vinmax=36, vref=None, iset=10e-6, imin=1e-3, vdo=1.6, vdo_note='1.6 V max @ 1.1 A (SOT-223: VCONTROL tied to IN)',
   ilim='1.1 A min / 1.4 A typ', theta=55, theta_src='ST package, datasheet Table 4 range 23-55', iq=None,
   doc='ADI LT3080 datasheet Rev.E', img=('LT3080.png', 'ADI LT3080 datasheet Rev.E, p.1, Typical Application (Variable Output Voltage 1.1A Supply)'),
   ds='https://www.analog.com/media/en/technical-documentation/data-sheets/lt3080.pdf', desc='36V 1.1A single-resistor LDO, SOT-223',
   cout=('10uF', 'c10u25v1206', 'COUT (MLCC, >=2.2uF)'), cin=('1uF', 'c1u50v0805', 'CIN'),
   cadj=('0.1uF', 'c100n50v0603', 'CSET (optional: noise / soft-start)'), diode=False, R1=None,
   capnote='Stable with >= 2.2 uF ceramic on OUT (ESR not required). Footprint-compatible with the 1117 parts, BUT programmed by one SET resistor (RSET = VOUT/10uA).'),
 LM1086=dict(mfr='Texas Instruments', mpn='LM1086ISX-ADJ/NOPB', mfr2='Texas Instruments', mpn2='LM1086IS-ADJ/NOPB', pkg='TO-263-3 (KTT)', fp=FP_TO263,
   adjname='ADJ', iout=1.5, vinmax=29, vref=1.25, iadj=55e-6, iadj_max=120e-6, imin=10e-3, vdo=1.5, vdo_note='1.5 V max @ 1.5 A',
   ilim='1.5 A min / 2.7 A typ (VIN-VOUT = 5 V)', theta=40.8, theta_src='KTT JEDEC', iq=None,
   doc='TI LM1086 datasheet SNVS039J', img=('LM1086.png', 'TI LM1086 datasheet SNVS039J, p.13, Figure 18 1.2-V to 15-V Adjustable Regulator'),
   ds='https://www.ti.com/lit/ds/symlink/lm1086.pdf', desc='29V 1.5A adjustable LDO, TO-263',
   cout=('22uF', 'tant22u16C', 'COUT (tantalum; 22uF when CADJ used)'), cin=('10uF', 'c10u25v1206', 'CIN'),
   cadj=('10uF', 'c10u25v1206', 'CADJ (optional, PSRR)'), diode=False, R1=121.0,
   capnote='Needs ESR zero: 10 uF tantalum or 50 uF Al (22 uF tant / 150 uF Al if CADJ fitted). Pure MLCC output not recommended.'),
 LM1085=dict(mfr='Texas Instruments', mpn='LM1085ISX-ADJ/NOPB', mfr2='Texas Instruments', mpn2='LM1085IS-ADJ/NOPB', pkg='TO-263-3 (KTT)', fp=FP_TO263,
   adjname='ADJ', iout=3.0, vinmax=29, vref=1.25, iadj=55e-6, iadj_max=120e-6, imin=10e-3, vdo=1.5, vdo_note='1.5 V max @ 3 A',
   ilim='3.2 A min / 5.5 A typ (VIN-VOUT = 5 V)', theta=40.6, theta_src='KTT JEDEC', iq=None,
   doc='TI LM1085 datasheet SNVS038H', img=('LM1085.png', 'TI LM1085 datasheet SNVS038H, p.13, Figure 15 1.2-V to 15-V Adjustable Regulator'),
   ds='https://www.ti.com/lit/ds/symlink/lm1085.pdf', desc='29V 3A adjustable LDO, TO-263',
   cout=('22uF', 'tant22u16C', 'COUT (tantalum; 22uF when CADJ used)'), cin=('10uF', 'c10u25v1206', 'CIN'),
   cadj=('10uF', 'c10u25v1206', 'CADJ (optional, PSRR)'), diode=False, R1=121.0,
   capnote='Needs ESR zero: 10 uF tantalum or 50 uF Al (22 uF tant / 150 uF Al if CADJ fitted). Pure MLCC output not recommended.'),
 LM1084=dict(mfr='Texas Instruments', mpn='LM1084ISX-ADJ/NOPB', mfr2='Texas Instruments', mpn2='LM1084IS-ADJ/NOPB', pkg='TO-263-3 (KTT)', fp=FP_TO263,
   adjname='ADJ', iout=5.0, vinmax=29, vref=1.25, iadj=55e-6, iadj_max=120e-6, imin=10e-3, vdo=1.5, vdo_note='1.5 V max @ 5 A',
   ilim='5.5 A min / 8 A typ (VIN-VOUT = 5 V)', theta=40.4, theta_src='KTT JEDEC', iq=None,
   doc='TI LM1084 datasheet SNVS037H', img=('LM1084.png', 'TI LM1084 datasheet SNVS037H, p.13, Figure 7-1 1.2-V to 15-V Adjustable Regulator'),
   ds='https://www.ti.com/lit/ds/symlink/lm1084.pdf', desc='29V 5A adjustable LDO, TO-263',
   cout=('22uF', 'tant22u16C', 'COUT (tantalum; 22uF when CADJ used)'), cin=('10uF', 'c10u25v1206', 'CIN'),
   cadj=('10uF', 'c10u25v1206', 'CADJ (optional, PSRR)'), diode=False, R1=121.0,
   capnote='Needs ESR zero: 10 uF tantalum or 50 uF Al (22 uF tant / 150 uF Al if CADJ fitted). Pure MLCC output not recommended.'),
)
ORDER = ['TLV1117', 'AZ1117C', 'NCP1117', 'LT3080', 'LM1086', 'LM1085', 'LM1084']

CAT = {
 'tant100u10D': ('Capacitor_Tantalum_SMD:CP_EIA-7343-31_Kemet-D', 'KEMET', 'T491D107K010AT', 'AVX', 'TAJD107K010RNJ', '100uF 10V tantalum, case D'),
 'tpoly47u10B': ('Capacitor_Tantalum_SMD:CP_EIA-3528-21_Kemet-B', 'KEMET', 'T520B476M010ATE070', 'Panasonic', '10TPE47MAPB', '47uF 10V polymer tantalum 70 mohm, case B'),
 'tant22u16C': ('Capacitor_Tantalum_SMD:CP_EIA-6032-28_Kemet-C', 'KEMET', 'T491C226K016AT', 'AVX', 'TAJC226K016RNJ', '22uF 16V tantalum, case C'),
 'c10u25v1206': ('Capacitor_SMD:C_1206_3216Metric', 'Murata', 'GRM31CR71E106KA12L', 'Samsung', 'CL31B106KAHNNNE', '10uF 25V X7R 1206'),
 'c22u10v1206': ('Capacitor_SMD:C_1206_3216Metric', 'Murata', 'GRM31CR71A226KE15L', 'Samsung', 'CL31B226KPHNNNE', '22uF 10V X7R 1206'),
 'c1u50v0805': ('Capacitor_SMD:C_0805_2012Metric', 'Murata', 'GRM21BR71H105KA12L', 'Samsung', 'CL21B105KBFNNNE', '1uF 50V X7R 0805'),
 'c100n50v0603': ('Capacitor_SMD:C_0603_1608Metric', 'Murata', 'GRM188R71H104KA93D', 'Samsung', 'CL10B104KB8NNNC', '100nF 50V X7R 0603'),
 'diode': ('Diode_SMD:D_SMA', 'onsemi', 'S1B', 'Vishay', 'S1B-E3/61T', '1A 100V rectifier (1N4002 SMD equiv.)'),
}
RES1206 = None

def best_pair_ldo(vout, vref, r1, iadj):
    """R1 fixed (datasheet value); choose E96 R2 minimising error incl. IADJ term"""
    exact = (vout - vref) / (vref / r1 + iadj)
    best = None
    d = 10 ** math.floor(math.log10(exact))
    for s in E96 + [10.0]:
        for m in (d / 10, d, d * 10):
            r2 = s * m
            v = vref * (1 + r2 / r1) + iadj * r2
            if best is None or abs(v - vout) < abs(best[1] - vout): best = (r2, v)
    return exact, best[0], best[1]

def rset_pick(vout):
    exact = vout / 10e-6
    d = 10 ** math.floor(math.log10(exact))
    c = [s * m for s in sorted(set(E96 + E24)) for m in (d / 10, d, d * 10)]
    r = min(c, key=lambda x: abs(x - exact))
    return exact, r, r * 10e-6

def design(name):
    p = P[name]; vo = VOUT_DEF; io = p['iout']; vin_n = 5.0
    t = [f'DESIGN EQUATIONS - {name} ({p["doc"]})',
         f'Design point: VOUT {vo} V (default), VIN 5.0 V nominal (3.3 V rail also checked), IOUT rated {io} A, {p["pkg"]}']
    if p['vref']:
        r1 = p['R1']
        ex, r2, va = best_pair_ldo(vo, p['vref'], r1, p['iadj'])
        t.append(f'Output: VOUT = VREF*(1 + R2/R1) + IADJ*R2 ; VREF = {p["vref"]} V, IADJ = {p["iadj"]*1e6:.0f} uA typ ({p["iadj_max"]*1e6:.0f} max)')
        t.append(f'  Min-load rule: VREF/R1 >= IMIN = {p["imin"]*1e3:.0f} mA max -> R1 <= {p["vref"]/p["imin"]:.0f} ohm ; R1 = {r1:g} ohm '
                 f'(divider current {p["vref"]/r1*1e3:.1f} mA)')
        t.append(f'  R2 = (VOUT - VREF)/(VREF/R1 + IADJ) = {ex:.1f} ohm -> {r2:g} ohm (E96) ; VOUT = {va:.4f} V ({(va/vo-1)*100:+.2f}%)')
        e_hi = p['vref'] * (1 + r2 / r1) + p['iadj_max'] * r2
        t.append(f'  IADJ error at IADJ max = {p["iadj_max"]*r2*1e3:.1f} mV ; VREF tolerance +/-1% (25C) / +/-2% (full temp) dominates')
        t.append(f'  R1 dissipation = VREF^2/R1 = {p["vref"]**2/r1*1e3:.1f} mW ; R2 = {(va-p["vref"])**2/r2*1e3:.1f} mW (0603 OK)')
        rt, rb = (f'{r1:g}R', 'R1'), (f'{r2:g}R', 'R2')
        gain = vo / p['vref']
        t.append(f'PSRR: ripple gain = VOUT/VREF = {gain:.2f} -> PSRR degrades {20*math.log10(gain):.1f} dB without CADJ')
        t.append(f'  CADJ > 1/(2*pi*f*R1): 120 Hz -> {1/(2*math.pi*120*r1)*1e6:.1f} uF ; 100 kHz post-regulator -> {1/(2*math.pi*1e5*r1)*1e9:.1f} nF')
    else:
        ex, r, va = rset_pick(vo)
        t.append('Output: VOUT = ISET * RSET, ISET = 10 uA (+/-1% at 25C, +/-2% over temp) - single resistor, no divider')
        t.append(f'  RSET = VOUT/10uA = {ex/1e3:.1f}k -> {fr(r)} ; VOUT = {va:.3f} V ; use 0.1%-1% low-TC resistor (VOUT tracks RSET)')
        t.append(f'  Min load {p["imin"]*1e3:.1f} mA max (0.5 mA typ): RMIN = VOUT/1mA = {vo/1e-3/1e3:.1f}k bleeder fitted (DNP if load always > 1 mA)')
        t.append('  CSET 0.1uF across RSET lowers output noise (40 uVrms) and adds a soft-start; tau = RSET*CSET = '
                 f'{r*0.1e-6*1e3:.0f} ms')
        rt, rb = (fr(r), 'RSET'), (None, None)
    t.append(f'Dropout: VDO = {p["vdo_note"]} -> VIN(min) = VOUT + VDO = {vo + p["vdo"]:.2f} V at full load')
    t.append(f'  3.3 V rail: headroom {3.3 - vo:.2f} V vs VDO {p["vdo"]} V -> {"OK" if 3.3 - vo > p["vdo"] else "NOT OK at full load (use 5 V input)"} ; '
             f'5 V rail: headroom {5 - vo:.2f} V -> OK')
    t.append(f'Current limit: {p["ilim"]} ; VIN(max) = {p["vinmax"]} V')
    t.append('Capacitors: ' + p['capnote'].replace('. ', '.\n  '))
    # thermal
    th = p['theta']
    t.append(f'THERMAL (thetaJA = {th} C/W, {p["theta_src"]}; TJ(max) 125 C)')
    for vin in (5.0, 3.3):
        if vin - vo < p['vdo'] * 0.6: continue
        pd = (vin - vo) * io
        imax50 = (125 - 50) / th / (vin - vo); imax85 = (125 - 85) / th / (vin - vo)
        iq_ = (p['vref'] / p['R1'] if p['vref'] else 1e-3)
        t.append(f'  VIN {vin} V: efficiency = VOUT*IOUT/(VIN*(IOUT+Idiv)) = {vo*io/(vin*(io+iq_))*100:.0f}% (max VOUT/VIN = {vo/vin*100:.0f}%) ; temp rise dT = thetaJA*PD = {th*(vin-vo)*io:.0f} C')
        t.append(f'  VIN {vin} V: PD = (VIN-VOUT)*IOUT = {vin-vo:.2f}*{io} = {pd:.2f} W -> TJ = {25+th*pd:.0f}C @25C / {85+th*pd:.0f}C @85C ; '
                 f'thermal IOUT(max) = {min(io, imax50):.2f} A @TA50C, {min(io, imax85):.2f} A @TA85C')
    t.append(f'  PD(max) = (125 - TA)/thetaJA = {(125-50)/th:.2f} W @50C, {(125-85)/th:.2f} W @85C. Add copper / heatsink or pre-regulate to raise current.')
    if p['diode']:
        t.append('Protection: D1 (1N4002-class, OUT->IN) per datasheet Note D - for input shorts with large COUT.')
    # table
    tab = []
    for v in STD:
        if p['vref'] and v < p['vref'] + 0.01: continue
        if v + p['vdo'] > p['vinmax']: continue
        if p['vref']:
            ex, r2, va = best_pair_ldo(v, p['vref'], p['R1'], p['iadj'])
            a, b = f'{p["R1"]:g}R', fr(r2) if r2 >= 1000 else f'{r2:g}R'
        else:
            ex, r, va = rset_pick(v); a, b = fr(r), '-'
        vmin = v + p['vdo']
        rails = [r_ for r_ in (3.3, 5.0, 12.0, 15.0, 24.0) if r_ >= vmin and r_ <= p['vinmax']]
        if not rails: continue
        vin = rails[0]
        iq = (p['vref'] / p['R1'] if p['vref'] else 1e-3)  # divider / bleeder current
        eta = v * io / (vin * (io + iq + (p.get('iadj') or 0)))
        pd = (vin - v) * io + vin * iq - v * iq
        dT = th * pd
        im = min(io, (125 - 50) / th / (vin - v))
        tab.append((v, a, b, va, '%.1f' % vin, '%.0f%%' % (eta * 100), '%.2f W' % pd, '%.0f C' % dT, '%.2f A' % im))
    return t, tab, rt, rb

# ---------------------------------------------------------------- symbols
def ldo_sym(name, prefix=True):
    p = P[name]
    full = f'Chinmay_LDO:{name}' if prefix else name
    adj = p['adjname']
    return f'''(symbol {q(full)} (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)
  (property "Reference" "U" (at 0 8.89 0) {eff()})
  (property "Value" {q(name)} (at 0 6.35 0) {eff()})
  (property "Footprint" {q(p["fp"])} (at 0 0 0) {eff(hide=True)})
  (property "Datasheet" {q(p["ds"])} (at 0 0 0) {eff(hide=True)})
  (property "Description" {q(p["desc"])} (at 0 0 0) {eff(hide=True)})
  (symbol "{name}_0_1" (rectangle (start -10.16 3.81) (end 10.16 -5.08) (stroke (width 0.254) (type default)) (fill (type background))))
  (symbol "{name}_1_1"
    (pin power_in line (at -12.7 0 0) (length 2.54) (name "IN" {FONT}) (number "3" {FONT}))
    (pin power_out line (at 12.7 0 180) (length 2.54) (name "OUT" {FONT}) (number "2" {FONT}))
    (pin input line (at 0 -7.62 90) (length 2.54) (name {q(adj)} {FONT}) (number "1" {FONT}))
  )
)'''

def build(name, page, su):
    p = P[name]
    t, tab, rt, rb = design(name)
    sh = Sheet(su, page); sh.path = f'/{ROOT}/{su}'
    refn = {'R': 1, 'C': 1, 'D': 1}
    def ref(k):
        r = f'{k}{page}{refn[k]:02d}'; refn[k] += 1; return r
    # IC at center
    X, Y = 101.6, 66.04
    sh.symbol(f'Chinmay_LDO:{name}', f'U{page}01', name, X, Y, ['1', '2', '3'],
              fields=bomfields(p['mfr'], p['mpn'], p['mfr2'], p['mpn2']), fp=p['fp'], ds=p['ds'], desc=p['desc'],
              refpos=(X - 2.54, Y - 8.89), valpos=(X - 4.5, Y - 6.35))
    # IN wire to left node, OUT wire to right node, ADJ down
    xin, xout = X - 12.7, X + 12.7
    sh.wire(xin, Y, xin - 12.7, Y); sh.label('VIN', xin - 12.7, Y, 180)
    sh.wire(xout, Y, xout + 12.7, Y); sh.label('VOUT', xout + 12.7, Y, 0)
    sh.wire(X, Y + 7.62, X, Y + 12.7); sh.label('ADJ', X, Y + 12.7, 270)
    # PWR flags + hier labels
    hy = 30.48
    for net, shape in (('VIN', 'input'), ('VOUT', 'output')):
        sh.hlabel(net, shape, 25.4, hy); sh.wire(25.4, hy, 35.56, hy); sh.label(net, 35.56, hy, 0); hy += 5.08
    sh.pwrflag(55.88, 30.48); sh.wire(55.88, 30.48, 55.88, 33.02); sh.label('VIN', 55.88, 33.02, 0)
    if page == 2:
        sh.pwrflag(55.88, 40.64); sh.wire(55.88, 40.64, 55.88, 43.18); sh.gnd(55.88, 43.18)
        sh.text('GND flag: single flag for the global\nGND net of the whole library', 60.96, 40.64, size=1.0)
    sh.text('Block interface:\nVIN  - input rail (pre-regulated / 5 V / 3.3 V)\nVOUT - regulated output (default 1.8 V)\nGND  - global ground',
            20.32, 50.8, size=1.27)
    # passives list (kind, value, n1, n2, spec/fields, role)
    plist = [('C', p['cin'][0], 'VIN', 'GND', p['cin'][1], p['cin'][2])]
    if p['vref']:
        plist += [('R', rt[0][:-1] if rt[0].endswith('R') else rt[0], 'VOUT', 'ADJ', None, 'R1 (OUT-ADJ)'),
                  ('R', rb[0][:-1] if rb[0].endswith('R') else rb[0], 'ADJ', 'GND', None, 'R2 (ADJ-GND)')]
        if p['cadj']: plist.append(('C', p['cadj'][0], 'ADJ', 'GND', p['cadj'][1], p['cadj'][2]))
    else:
        plist += [('R', rt[0], 'ADJ', 'GND', None, 'RSET (SET-GND)'), ('C', p['cadj'][0], 'ADJ', 'GND', p['cadj'][1], p['cadj'][2]),
                  ('R', '1.8k', 'VOUT', 'GND', None, 'RMIN bleeder (1 mA min load)')]
    plist.append(('C', p['cout'][0], 'VOUT', 'GND', p['cout'][1], p['cout'][2]))
    if p['diode']:
        plist.append(('D', 'S1B', 'VIN', 'VOUT', 'diode', 'D1 reverse protection (K=VIN, A=VOUT)'))
    x = 30.48; y = 106.68
    for kind, val, n1, n2, spec, role in plist:
        r = ref(kind)
        cx = snap(x); cy = y
        if kind == 'R':
            yc, pc = r_codes(val if val[-1] in 'kM' else val + 'R')
            disp = val if val[-1] in 'kM' else val
            sh.symbol('Device:R_Small', r, disp, cx, cy, ['1', '2'], fields=bomfields('Yageo', yc, 'Panasonic', pc),
                      fp='Resistor_SMD:R_0603_1608Metric', desc=f'{disp} 1% 0603 - {role}')
        elif kind == 'C':
            c = CAT[spec]
            lib = 'Device:C_Polarized_Small' if spec.startswith('t') else 'Device:C_Small'
            sh.symbol(lib, r, val, cx, cy, ['1', '2'], fields=bomfields(c[1], c[2], c[3], c[4]), fp=c[0], desc=f'{c[5]} - {role}')
        else:  # diode horizontal
            x += 7.62; cx = snap(x)
            c = CAT['diode']
            sh.symbol('Device:D_Small', r, val, cx, cy, ['1', '2'], fields=bomfields(c[1], c[2], c[3], c[4]), fp=c[0], desc=f'{c[5]} - {role}',
                      refpos=(cx - 2.0, cy - 2.2), valpos=(cx - 2.0, cy + 3.2))
            sh.wire(cx - 2.54, cy, cx - 5.08, cy); sh.label(n1, cx - 5.08, cy, 180)
            sh.wire(cx + 2.54, cy, cx + 5.08, cy); sh.label(n2, cx + 5.08, cy, 0)
            x += 25.4; continue
        sh.wire(cx, cy - 2.54, cx, cy - 5.08)
        if n1 == 'GND': sh.gnd(cx, cy - 5.08)
        else: sh.label(n1, cx, cy - 5.08, 90)
        sh.wire(cx, cy + 2.54, cx, cy + 5.08)
        if n2 == 'GND': sh.gnd(cx, cy + 5.08)
        else: sh.label(n2, cx, cy + 5.08, 270)
        x += 15.24
    # role legend under passives
    legend = '\n'.join(f'{k}{page}{i:02d}' for i in [])  # placeholder
    sh.text(f'BUCK-free linear block - {name}  |  {p["mfr"]}  |  {p["desc"]}'.replace('BUCK-free linear block', 'LDO'), 20.32, 14.0, size=2.2, bold=True)
    sh.text('Default build: VOUT = 1.8 V (fixed resistors - no trimmer). Pin-compatible family: pin1 ADJ/SET, pin2 + tab OUT, pin3 IN.\n'
            'Other outputs: change only the programming resistor(s) per the VOUT table.', 20.32, 19.3, size=1.27)
    sh.text('\n'.join(t), 20.32, 130.0, size=1.5)
    # image
    fn, cap = p['img']
    w, h = sh.image(os.path.join(IMGDIR, fn), 310.0, 70.0, 180, 95)
    sh.text('Datasheet application schematic (reference):', 215.9, 17.78, size=1.5, bold=True)
    sh.text('Source: ' + cap + ' - reproduced for internal design reference only.', 215.9, 70.0 + h / 2 + 1.5, size=1.0)
    # table
    tx, ty0 = 215.9, max(70 + h / 2 + 10, 135.0)
    if p['vref']:
        hdr = 'VOUT PROGRAMMING TABLE  (R1 = OUT->ADJ fixed, R2 = ADJ->GND, E96 1%; includes IADJ term)'
        cols = [('VOUT', 0), ('R1', 13), ('R2', 27), ('VOUT act', 42), ('Err', 62), ('VIN rail', 79), ('Eff.', 98), ('PD @IOUT', 112), ('dT', 136), ('IOUT max @50C', 151)]
    else:
        hdr = 'VOUT PROGRAMMING TABLE  (RSET = SET->GND = VOUT/10uA, E96/E24 1%)'
        cols = [('VOUT', 0), ('RSET', 13), ('-', 27), ('VOUT act', 42), ('Err', 62), ('VIN rail', 79), ('Eff.', 98), ('PD @IOUT', 112), ('dT', 136), ('IOUT max @50C', 151)]
    sh.text(hdr, tx, ty0, size=2.0, bold=True)
    ry = ty0 + 5.5
    for c, dx in cols: sh.text(c, tx + dx, ry, size=1.55, bold=True)
    ry += 4.2
    for v, a, b, va, vin, eta, pd, dT, im in tab:
        mark = ' <FITTED' if abs(v - VOUT_DEF) < 0.01 else ''
        vals = ['%g' % v, a, b, '%.3f' % va, '%+.2f%%' % ((va / v - 1) * 100), vin, eta, pd, dT, im + mark]
        for (c, dx), val in zip(cols, vals):
            sh.text(val, tx + dx, ry, size=1.55, bold=bool(mark))
        ry += 3.4
    sh.text(f'VIN rail = lowest standard rail >= VOUT + VDO(max). Eff. = VOUT*IOUT / (VIN*(IOUT + divider/bleeder current)).\n'
            f'PD @IOUT = (VIN-VOUT)*IOUT at rated {p["iout"]} A ; dT = thetaJA*PD = junction temperature rise above ambient (thetaJA {p["theta"]} C/W).\n'
            'dT > ~75 C means the rated current is not usable on that rail at 50 C ambient - see IOUT max @50C (thermal limit, capped at rating).', tx, ry + 2, size=1.25)
    libsyms = [ldo_sym(name), LIBS['Device:R_Small'], LIBS['Device:C_Small'], LIBS['Device:C_Polarized_Small'],
               LIBS['power:GND'], LIBS['power:PWR_FLAG']]
    if p['diode']: libsyms.append(LIBS['Device:D_Small'])
    fname = f'LDO_{name}.kicad_sch'
    gen.write_sheet(fname, f'LDO {name} - {p["desc"].split(",")[0]}',
                    [f'Replicates block: {p["mfr"]} {name} datasheet adjustable application',
                     'Default VOUT 1.8 V - see VOUT programming table for other outputs',
                     'Calculations per datasheet application / thermal sections'], libsyms, sh.items)
    return fname

def root(sheets):
    items = []
    W, H = 76.2, 20.32
    for i, (name, su, fname, page) in enumerate(sheets):
        col, row = i % 3, i // 3
        x = 30.48 + col * 127.0; y = 55.88 + row * 40.64
        pins = []
        for pn, typ, side, dy in (('VIN', 'input', 'L', 7.62), ('VOUT', 'output', 'R', 7.62)):
            px = x if side == 'L' else x + W
            items.append(f'  (no_connect (at {px:.2f} {y + dy:.2f}) (uuid "{U()}"))')
            pins.append(f'    (pin {q(pn)} {typ} (at {px:.2f} {y + dy:.2f} {180 if side == "L" else 0}) (uuid "{U()}") {eff("left" if side == "R" else "right")})')
        items.append(f'''  (sheet (at {x:.2f} {y:.2f}) (size {W} {H}) (fields_autoplaced yes)
    (stroke (width 0.1524) (type solid))
    (fill (color 0 0 0 0.0000))
    (uuid "{su}")
    (property "Sheetname" {q("LDO " + name)} (at {x:.2f} {y - 0.7:.2f} 0) {eff("left bottom")})
    (property "Sheetfile" {q(fname)} (at {x:.2f} {y + H + 0.6:.2f} 0) {eff("left top")})
    (instances (project "{PROJECT}" (path "/{ROOT}" (page "{page}"))))
{chr(10).join(pins)}
  )''')
    summ = ['Chinmay LDO design-block library - pin-compatible 3-terminal adjustable LDOs (pin1 ADJ/SET, pin2 + tab OUT, pin3 IN)', '',
            'Page  Block     Vendor               IOUT    VIN max  Package     VDO (max)     Output cap',
            ' 2    TLV1117   Texas Instruments    0.8 A   15 V     SOT-223     1.3 V         100uF tantalum (ESR 0.2-10 ohm)',
            ' 3    AZ1117C   Diodes Inc.          0.8 A   18 V     SOT-223     1.3 V         22uF MLCC',
            ' 4    NCP1117   onsemi               1.0 A   20 V     SOT-223     1.2 V         47uF polymer tant (ESR 33m-2.2 ohm)',
            ' 5    LT3080    Analog Devices       1.1 A   36 V     SOT-223     1.6 V (3-ld)  10uF MLCC   * single-resistor SET programming',
            ' 6    LM1086    Texas Instruments    1.5 A   29 V     TO-263      1.5 V         22uF tantalum',
            ' 7    LM1085    Texas Instruments    3.0 A   29 V     TO-263      1.5 V         22uF tantalum',
            ' 8    LM1084    Texas Instruments    5.0 A   29 V     TO-263      1.5 V         22uF tantalum', '',
            'Drop-in groups: SOT-223 -> TLV1117 / AZ1117C / NCP1117 / ST LD1117STR (MPN2) share pinout, VREF 1.25 V and the R1/R2 divider;',
            'LT3080 fits the same SOT-223 footprint but needs RSET (VOUT/10uA) instead of R1/R2 - keep both footprints or two BOM variants.',
            'TO-263 -> LM1086 / LM1085 / LM1084 are pin- and divider-compatible (R1 = 121 ohm).',
            'Output-cap rules differ: TLV1117-ADJ and LM108x need ESR (tantalum/Al); AZ1117C, NCP1117 (inside ESR window) and LT3080 accept MLCC.',
            'All blocks default to VOUT = 1.8 V; each sheet has the datasheet circuit, calculations, thermal limits and a VOUT table.',
            'Ref designators: page N -> N01.. ; BOM fields: Manufacturer, MPN1, MFR2, MPN2, Procurement (digikey.in), Procurement2 (mouser.in), Cost.']
    items.append(f'  (text {q(chr(10).join(summ))} (exclude_from_sim no) (at 30.48 190.0 0) {eff("left top", size=1.5)} (uuid "{U()}"))')
    items.append(f'  (text "CHINMAY LDO DESIGN BLOCKS" (exclude_from_sim no) (at 30.48 25.4 0) {eff("left top", size=4, bold=True)} (uuid "{U()}"))')
    items.append(f'  (text "Seven pin-compatible adjustable LDO blocks, 0.8 A -> 5 A. Default output 1.8 V." (exclude_from_sim no) (at 30.48 33.0 0) {eff("left top", size=1.8)} (uuid "{U()}"))')
    body = f'''(kicad_sch (version 20260101) (generator "eeschema") (generator_version "10.0")
  (uuid {ROOT})
  (paper "A3")
  (title_block (title "Chinmay LDO library") (date "2026-11-14") (rev "A") (company "Chinmay") (comment 1 "Pin-compatible adjustable LDO design blocks - TI, Diodes, onsemi, ADI - Nov 2026") (comment 2 "Default VOUT 1.8 V on all blocks"))
  (lib_symbols
  )
{chr(10).join(items)}
  (sheet_instances
    (path "/" (page "1"))
  )
)
'''
    open(os.path.join(OUT, 'Chinmay_LDO.kicad_sch'), 'w').write(body)

if __name__ == '__main__':
    import re
    suf = '/home/claude/ldo/sheet_uuids.json'
    sus = json.load(open(suf)) if os.path.exists(suf) else {}
    sheets = []
    for i, n in enumerate(ORDER):
        su = sus.setdefault(n, U()); page = i + 2
        sheets.append((n, su, build(n, page, su), page))
    json.dump(sus, open(suf, 'w'))
    root(sheets)
    open(os.path.join(OUT, 'Chinmay_LDO.kicad_sym'), 'w').write(
        '(kicad_symbol_lib (version 20251024) (generator "chinmay_gen") (generator_version "10.0")\n' + '\n'.join(ldo_sym(n, False) for n in ORDER) + '\n)\n')
    open(os.path.join(OUT, 'sym-lib-table'), 'w').write(
        '(sym_lib_table\n  (version 7)\n  (lib (name "Chinmay_LDO")(type "KiCad")(uri "${KIPRJMOD}/Chinmay_LDO.kicad_sym")(options "")(descr "Chinmay LDO symbols"))\n)\n')
    for f in sorted(os.listdir(OUT)):
        b = open(os.path.join(OUT, f)).read(); s2 = re.sub(r'"(?:[^"\\]|\\.)*"', '""', b)
        print(f, len(b), s2.count('(') - s2.count(')'))
    for n in ORDER:
        t, tab, _, _ = design(n); print('\n'.join(t)); [print('   ', r) for r in tab]
