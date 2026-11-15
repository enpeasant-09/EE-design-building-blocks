"""Chinmay_EEPROM / Chinmay_NAND / Chinmay_NOR design block libraries (house-common passives)."""
import os, json, uuid, re, shutil
import gen, common as CM
from gen import q, eff
from xtal_blocks import B, pfields

LIBS = json.load(open('/home/claude/buck/gen/libs.json'))
ROOT = '/home/claude/mem/out'
U = lambda: str(uuid.uuid4())
G = 2.54

# ------------------------------------------------------------------ custom symbol library (Chinmay_Memory)
def setprop(txt, name, val):
    return re.sub(r'(\(property\s+"%s"\s+)"(?:[^"\\]|\\.)*"' % re.escape(name), lambda m: m.group(1) + q(val), txt, count=1)

def derive(src, new, value, desc, ds, fp, pinmap=None, kw=None):
    t = LIBS[src]
    os_, ns = src.split(':')[1], new.split(':')[1]
    t = t.replace(f'(symbol "{src}"', f'(symbol "{new}"', 1).replace(f'"{os_}_', f'"{ns}_')
    for k, v in (('Value', value), ('Description', desc), ('Datasheet', ds), ('Footprint', fp)):
        t = setprop(t, k, v)
    if kw: t = setprop(t, 'ki_keywords', kw)
    for a, b in (pinmap or {}).items():
        t = t.replace(f'(name "{a}"', f'(name "{b}"')
    return t

def pin(typ, x, y, ang, name, num, length=G, hide=False):
    h = ' (hide yes)' if hide else ''
    return (f'(pin {typ} line (at {x:g} {y:g} {ang}) (length {length:g}){h} (name {q(name)} (effects (font (size 1.27 1.27)))) '
            f'(number {q(num)} (effects (font (size 1.27 1.27)))))')

def tsop48_nand(full, value, desc, ds, fp):
    nm = full.split(':')[1]
    P = []
    left = ['IO0:29', 'IO1:30', 'IO2:31', 'IO3:32', 'IO4:41', 'IO5:42', 'IO6:43', 'IO7:44']
    for i, s in enumerate(left):
        n, k = s.split(':'); P.append(pin('bidirectional', -15.24, 10.16 - i * G, 0, n, k))
    right = [('~{CE}', '9', 'input'), ('~{RE}', '8', 'input'), ('~{WE}', '18', 'input'), ('CLE', '16', 'input'),
             ('ALE', '17', 'input'), ('~{WP}', '19', 'input'), ('RY/~{BY}', '7', 'open_collector')]
    for i, (n, k, t) in enumerate(right):
        P.append(pin(t, 15.24, 10.16 - i * G, 180, n, k))
    P.append(pin('power_in', -2.54, 17.78, 270, 'VCC', '12')); P.append(pin('power_in', 2.54, 17.78, 270, 'VCC', '37'))
    P.append(pin('power_in', -2.54, -17.78, 90, 'VSS', '13')); P.append(pin('power_in', 2.54, -17.78, 90, 'VSS', '36'))
    used = {'29', '30', '31', '32', '41', '42', '43', '44', '9', '8', '18', '16', '17', '19', '7', '12', '37', '13', '36'}
    k = 0
    for n in range(1, 49):
        if str(n) in used: continue
        nmp = 'DNU' if n in (20, 38) else 'NC'
        x = -10.16 + (k % 9) * G; y = -7.62 - (k // 9) * G; k += 1
        P.append(pin('no_connect', x, y, 0, nmp, str(n), length=0, hide=True))
    props = [('Reference', 'U', (-12.7, 16.51), False), ('Value', value, (5.08, 16.51), False), ('Footprint', fp, (0, -22.86), True),
             ('Datasheet', ds, (0, -25.4), True), ('Description', desc, (0, -27.94), True),
             ('ki_keywords', 'NAND flash parallel ONFI 8-bit TSOP-48 SLC', (0, 0), True), ('ki_fp_filters', 'TSOP*I*48*18.4x12mm*P0.5mm*', (0, 0), True)]
    L = [f'(symbol {q(full)} (exclude_from_sim no) (in_bom yes) (on_board yes) (in_pos_files yes)']
    for n, v, (x, y), h in props:
        L.append(f'  (property {q(n)} {q(v)} (at {x:g} {y:g} 0) {eff("left" if n in ("Reference","Value") else None, hide=h)})')
    L.append(f'  (symbol "{nm}_0_1" (rectangle (start -12.7 15.24) (end 12.7 -15.24) (stroke (width 0.254) (type default)) (fill (type background))))')
    L.append(f'  (symbol "{nm}_1_1"\n    ' + '\n    '.join(P) + ')')
    L.append(')')
    return '\n'.join(L)

DS = {
 '24LC256': 'https://ww1.microchip.com/downloads/en/DeviceDoc/24AA256-24LC256-24FC256-Data-Sheet-20001203W.pdf',
 'M24C64': 'https://www.st.com/resource/en/datasheet/m24c64-r.pdf',
 '24AA02E48': 'https://ww1.microchip.com/downloads/aemDocuments/documents/MPD/ProductDocuments/DataSheets/2-Kbit-I2C-Serial-EEPROMs-+EUI-48-or-EUI-64-Node-20002124.pdf',
 'AT25256B': 'https://www.microchip.com/en-us/product/AT25256B',
 'W25Q128JV': 'https://www.winbond.com/resource-files/w25q128jv_dtr%20revc%2003272018%20plus.pdf',
 'MX25L12833F': 'https://www.macronix.com/en-us/products/NOR-Flash/Serial-NOR-Flash/Pages/spec.aspx?p=MX25L12833F',
 'IS25LP128F': 'https://www.issi.com/WW/pdf/25LP-WP128F.pdf',
 'MX35LF1GE4AB': 'https://www.macronix.com/en-us/products/NAND-Flash/SLC-NAND-Flash/Pages/spec.aspx?p=MX35LF1GE4AB',
 'GD5F1GQ5UE': 'https://www.gigadevice.com/product/flash/spi-nand-flash/gd5f1gq5uexxg',
 'W29N01HV': 'https://www.winbond.com/hq/product/code-storage-flash-memory/slc-nand-flash/?__locale=en&partNo=W29N01HV',
}
FP = {'SO8N': 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', 'SO8W': 'Package_SO:SOIC-8_5.3x5.3mm_P1.27mm',
      'SOT235': 'Package_TO_SOT_SMD:SOT-23-5', 'WSON8': 'Chinmay_Footprints:WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm',
      'TSOP48': 'Package_SO:TSOP-I-48_18.4x12mm_P0.5mm'}
NANDPINS = {'DO/IO_{1}': 'SO/SIO1', '~{WP}/IO_{2}': '~{WP}/SIO2', 'DI/IO_{0}': 'SI/SIO0', 'CLK': 'SCLK',
            '~{HOLD}/~{RESET}/IO_{3}': '~{HOLD}/SIO3'}
CUSTOM = {
 'Chinmay_Memory:M24C64-RMN': derive('Memory_EEPROM:M24C01-RMN', 'Chinmay_Memory:M24C64-RMN', 'M24C64-RMN',
     '64Kb (8Kx8) I2C Serial EEPROM, 1MHz, 1.8-5.5V, SO8N', DS['M24C64'], FP['SO8N'], kw='EEPROM I2C 64Kb ST'),
 'Chinmay_Memory:MX25L12833FM2': derive('Memory_Flash:MX25L3233FM2', 'Chinmay_Memory:MX25L12833FM2', 'MX25L12833FM2',
     '128Mbit 3V Quad SPI NOR flash, 133MHz, 8-SOP 200mil', DS['MX25L12833F'], FP['SO8W'], kw='flash NOR SPI QPI 128Mbit Macronix'),
 'Chinmay_Memory:IS25LP128F-JB': derive('Memory_Flash:W25Q128JVS', 'Chinmay_Memory:IS25LP128F-JB', 'IS25LP128F-JB',
     '128Mbit 2.3-3.6V Quad SPI NOR flash, 133MHz, SOIC-8 208mil', DS['IS25LP128F'], FP['SO8W'], kw='flash NOR SPI QPI DTR 128Mbit ISSI'),
 'Chinmay_Memory:MX35LF1GE4AB-Z4': derive('Memory_Flash:W25Q128JVE', 'Chinmay_Memory:MX35LF1GE4AB-Z4', 'MX35LF1GE4AB-Z4',
     '1Gbit 3V SLC SPI NAND flash, 104MHz, on-die ECC, WSON-8 8x6', DS['MX35LF1GE4AB'], FP['WSON8'], NANDPINS, kw='flash NAND SPI SLC 1Gbit Macronix'),
 'Chinmay_Memory:GD5F1GQ5UEYIG': derive('Memory_Flash:W25Q128JVE', 'Chinmay_Memory:GD5F1GQ5UEYIG', 'GD5F1GQ5UEYIG',
     '1Gbit 3V SLC SPI NAND flash, 133MHz, on-die ECC, WSON-8 8x6', DS['GD5F1GQ5UE'], FP['WSON8'], NANDPINS, kw='flash NAND SPI SLC 1Gbit GigaDevice'),
 'Chinmay_Memory:W29N01HVSINA': tsop48_nand('Chinmay_Memory:W29N01HVSINA', 'W29N01HVSINA',
     '1Gbit 3.3V SLC NAND flash, x8 parallel (ONFI), 25ns, TSOP-48 12x20', DS['W29N01HV'], FP['TSOP48']),
}
LIBS.update(CUSTOM)

# ------------------------------------------------------------------ geometry helpers
def pins_of(lib):
    t = LIBS[lib]
    return {m[4]: (float(m[0]), float(m[1]), int(m[2]), m[3]) for m in
            re.findall(r'\(pin\s+\w+\s+\w+\s+\(at\s+([-\d.]+)\s+([-\d.]+)\s+(\d+)\)\s+\(length\s+[\d.]+\)(?:\s*\(hide yes\))?\s+\(name\s+"([^"]*)"[\s\S]*?\(number\s+"([^"]*)"', t)}

class MB(B):
    def nc(self, x, y):
        self.items.append(f'(no_connect (at {x:.2f} {y:.2f}) (uuid "{U()}"))')

def r_or_c(kind, val):
    if kind == 'C':
        ipn = {'100nF': 'CAP-0603-100N-50V-X7R', '1uF': 'CAP-0603-1U-16V-X7R'}[val]
        f = CM.cap_fields(ipn); return f, f['fp']
    o = CM.r_ohm(val.replace('R', '') if val.endswith('R') and val != '0R' else val) if val != '0R' else 0
    f = CM.r_fields(o); a = CM.r_alt(o)
    f = dict(f); f['alt'] = a
    return f, CM.FP['0603R']

def flds(f):
    L = pfields(f)
    if 'alt' in f: L += [('MFR3', f['alt'][0]), ('MPN3', f['alt'][1]), ('MFR4', f['alt'][2]), ('MPN4', f['alt'][3])]
    return L

def build(name, part, pinact, net, notes, meta, extra_libs=()):
    """part: dict(lib, val, fp, ds, desc, ipn, mfr, mpn, mfr2, mpn2). pinact: {num: action}. net: passive list."""
    b = MB(U()); X, Y = 50.8, 86.36
    P = pins_of(part['lib'])
    b.sym(part['lib'], 'U?', part['val'], X, Y, list(P.keys()),
          fields=[('IPN', part['ipn'])] + gen.bomfields(part['mfr'], part['mpn'], part['mfr2'], part['mpn2']),
          fp=part['fp'], ds=part['ds'], desc=part['desc'], rp=(X - 7.62, Y - part.get('h', 12.7) - 3.81), vp=(X + 3.81, Y - part.get('h', 12.7) - 3.81))
    for num, act in pinact.items():
        px, py, ang, nm = P[num]; x, y = X + px, Y - py
        if act == 'gnd':
            b.gnd(x, y)
        elif act == 'vdd':
            b.wire((x, y), (x, y - G)); b.label('VDD', x, y - G, 90)
        elif act == 'nc':
            b.nc(x, y)
        else:
            dx = -G if ang == 0 else G
            b.wire((x, y), (x + dx, y)); b.label(act, x + dx, y, 180 if ang == 0 else 0)
    # passive network, flow layout to the right of the IC
    x0, y0 = 99.06, 45.72; cx, cy = x0, y0; rowmax = 266.7; cnt = {'R': 0, 'C': 0}
    for it in net:
        kind = it[0]; w = 25.4 if kind == 'ser' else 15.24
        if cx + w > rowmax: cx = x0; cy += 27.94
        c = 'C' if kind == 'dec' else 'R'
        if kind in ('pu', 'pd', 'dec'):
            _, *rest = it
            if kind == 'dec': val, desc = rest; dnp = False
            else: netn, val, dnp, desc = rest
            f, fp = r_or_c(c, val); xx = cx + 2.54
            b.sym('Device:C_Small' if c == 'C' else 'Device:R_Small', f'{c}?', f['value'], xx, cy, ['1', '2'], fields=flds(f), fp=fp,
                  desc=desc, dnp=dnp, rp=(xx + 1.6, cy - 0.9), vp=(xx + 1.6, cy + 1.5))
            b.wire((xx, cy - G), (xx, cy - 2 * G))
            b.wire((xx, cy + G), (xx, cy + 2 * G))
            if kind == 'pu': b.label('VDD', xx, cy - 2 * G, 90); b.label(netn, xx, cy + 2 * G, 270)
            if kind == 'pd': b.label(netn, xx, cy - 2 * G, 90); b.gnd(xx, cy + 2 * G)
            if kind == 'dec': b.label('VDD', xx, cy - 2 * G, 90); b.gnd(xx, cy + 2 * G)
        elif kind == 'ser':
            _, dev, host, val, dnp, desc = it
            f, fp = r_or_c('R', val); xx = cx + 10.16
            b.sym('Device:R_Small', 'R?', f['value'], xx, cy, ['1', '2'], ang=90, fields=flds(f), fp=fp, desc=desc, dnp=dnp,
                  rp=(xx - 2.0, cy - 3.2), vp=(xx - 2.0, cy + 3.0))
            b.wire((xx - G, cy), (xx - 2 * G, cy)); b.label(dev, xx - 2 * G, cy, 180)
            b.wire((xx + G, cy), (xx + 2 * G, cy)); b.label(host, xx + 2 * G, cy, 0)
        cx += w
    b.text('\n'.join(notes), 25.4, 132.08, size=1.1)
    libs = [LIBS[part['lib']], LIBS['Device:R_Small'], LIBS['Device:C_Small'], LIBS['power:GND']]
    return name, b, libs, meta

# ------------------------------------------------------------------ block definitions
def i2c_eeprom(name, part, addr_pins, wp_pin, wp_name, wp_internal, cap, use):
    pinact = {'4' if '4' not in ('',) else '4': 'gnd'}
    P = pins_of(part['lib'])
    pinact = {}
    for num, (px, py, ang, nm) in P.items():
        nmc = nm.replace('_{', '').replace('}', '').replace('~{', '')
        if nmc in ('VCC', 'VCC'): pinact[num] = 'vdd'
        elif nmc in ('GND', 'VSS'): pinact[num] = 'gnd'
        elif nmc == 'SDA': pinact[num] = 'SDA'
        elif nmc == 'SCL': pinact[num] = 'SCL'
        elif nmc == 'NC': pinact[num] = 'nc'
    net = [('dec', '100nF', '100nF VCC decoupling, <=2 mm from VCC pin')]
    for i, num in enumerate(addr_pins):
        nm = P[num][3]; pinact[num] = nm
        net.append(('pd', nm, '0R', False, f'{nm} address strap to GND (fit) - device address bit = 0'))
        net.append(('pu', nm, '0R', True, f'{nm} address strap to VDD (DNP) - fit instead of GND strap for bit = 1'))
    if wp_pin:
        pinact[wp_pin] = 'WP'
        net.append(('pd', 'WP', '10k', False, f'{wp_name} 10k pull-down: writes enabled by default, drive high to write-protect'))
    net += [('pu', 'SDA', '4.7k', True, 'SDA pull-up 4.7k (DNP if bus already pulled up)'),
            ('pu', 'SCL', '4.7k', True, 'SCL pull-up 4.7k (DNP if bus already pulled up)')]
    notes = [f'{part["desc"]} - {part["mpn"]} (alt {part["mpn2"]})',
             'LAYOUT: 100 nF at VCC pin (<=2 mm), via straight to GND plane. Route SDA/SCL together, away from SW nodes / clocks.',
             'I2C needs no series termination; ONE set of 4.7k pull-ups per bus (fit here only if bus has none). Rp_max = tr / (0.847 x Cbus): 400 kHz tr=300 ns, 1 MHz tr=120 ns.',
             (f'Address straps: fit EITHER the GND 0R OR the VDD 0R per pin, never both. ' if addr_pins else 'Fixed I2C address 0x50 (EEPROM) / EUI-48 at 0xFA-0xFF. ') +
             (f'{wp_name}: {wp_internal}; 10k pull-down keeps writes enabled - drive high from MCU to protect.' if wp_pin else ''),
             f'Typical use: {use}. Rename SDA / SCL / WP / VDD labels to your nets.']
    meta = dict(desc=f'{part["desc"]} {part["mpn"]} I2C EEPROM block with decoupling, address straps, WP and bus pull-up provision. {use}.',
                kw=f'eeprom i2c {part["mpn"]} {part["mpn2"]} memory', fields={'Memory': part['desc'], 'Part': part['mpn'], 'Interface': 'I2C', 'Typical use': use})
    return build(name, part, pinact, net, notes, meta)

def spi_block(name, part, kind, pinmap, use, extra_notes, quad=True, ep=None, cap2=True):
    """pinmap: num -> role in {CS,CLK,DI,DO,WP,HOLD,VCC,GND,EP}"""
    pre = {'NOR': 'NOR', 'NAND': 'NAND', 'EE': 'EE'}[kind]
    act = {}; net = [('dec', '100nF', '100nF VCC decoupling, <=2 mm from VCC pin')]
    if cap2: net.append(('dec', '1uF', '1uF bulk next to 100nF (program/erase current peaks)'))
    for num, role in pinmap.items():
        if role == 'VCC': act[num] = 'vdd'
        elif role in ('GND', 'EP'): act[num] = 'gnd'
        elif role == 'CS': act[num] = 'CS#'
        elif role == 'CLK': act[num] = f'{pre}_CLK'
        else:
            act[num] = {'DI': f'{pre}_IO0', 'DO': f'{pre}_IO1', 'WP': f'{pre}_IO2', 'HOLD': f'{pre}_IO3'}[role] if quad else \
                       {'DI': f'{pre}_MOSI', 'DO': f'{pre}_MISO', 'WP': 'WP#', 'HOLD': 'HOLD#'}[role]
    net.append(('pu', 'CS#', '10k', False, 'CS# 10k pull-up: device deselected while MCU is in reset / pins tri-stated'))
    net.append(('ser', f'{pre}_CLK', 'CLK' if quad else 'SCK', '27R', False, '27R source series termination - place within 5 mm of the MCU/host CLK pin'))
    if quad:
        for i, h in enumerate(['IO0', 'IO1', 'IO2', 'IO3']):
            net.append(('ser', f'{pre}_{h}', h, '0R', False, f'{h} termination provision: 0R fitted, change to 27R if overshoot/ringing seen'))
        net.append(('pu', f'{pre}_IO2', '10k', False, 'WP#/IO2 10k pull-up (mandatory for 1-1-1 / 1-1-2 SPI modes)'))
        net.append(('pu', f'{pre}_IO3', '10k', False, 'HOLD#/IO3 10k pull-up (mandatory for 1-1-1 / 1-1-2 SPI modes)'))
    else:
        net.append(('ser', f'{pre}_MOSI', 'MOSI', '0R', False, 'MOSI termination provision: 0R fitted, 27R if ringing'))
        net.append(('ser', f'{pre}_MISO', 'MISO', '0R', False, 'MISO termination provision: 0R fitted, 27R if ringing (place at EEPROM)'))
        net.append(('pu', 'WP#', '10k', False, 'WP# 10k pull-up: status register writable; drive low from MCU to lock'))
        net.append(('pu', 'HOLD#', '10k', False, 'HOLD# 10k pull-up: hold function disabled'))
    notes = [f'{part["desc"]} - {part["mpn"]} (alt {part["mpn2"]})',
             'LAYOUT: 100 nF' + (' + 1 uF' if cap2 else '') + ' at VCC (<=2 mm, 100 nF closest), short via to GND plane. Solid GND reference under all SPI traces, no plane splits.',
             'CLK: 27R source termination within 5 mm of host pin; route CLK first, shortest, >=3W spacing to other nets; no stubs/test points mid-trace.'] + extra_notes + \
            [f'Typical use: {use}. Rename CS# / CLK / IO labels to your nets.']
    meta = dict(desc=f'{part["desc"]} {part["mpn"]} block with decoupling, CS# pull-up, CLK series termination and IO termination provision. {use}.',
                kw=f'{kind.lower()} flash spi qspi {part["mpn"]} {part["mpn2"]} memory'.replace('ee flash', 'eeprom'),
                fields={'Memory': part['desc'], 'Part': part['mpn'], 'Interface': 'Quad SPI' if quad else 'SPI', 'Typical use': use})
    return build(name, part, act, net, notes, meta)

def nand_parallel(name, part, use):
    P = pins_of(part['lib']); act = {}
    for num, (px, py, ang, nm) in P.items():
        if nm == 'VCC': act[num] = 'vdd'
        elif nm == 'VSS': act[num] = 'gnd'
        elif nm.startswith('IO'): act[num] = f'NAND_{nm}'
        elif nm in ('NC', 'DNU'): continue
        else: act[num] = {'~{CE}': 'NAND_CE#', '~{RE}': 'NAND_RE#', '~{WE}': 'NAND_WE#', 'CLE': 'NAND_CLE', 'ALE': 'NAND_ALE',
                          '~{WP}': 'NAND_WP#', 'RY/~{BY}': 'NAND_RB#'}[nm]
    net = [('dec', '100nF', '100nF at VCC pin 12'), ('dec', '100nF', '100nF at VCC pin 37'), ('dec', '1uF', '1uF bulk shared, between pins 12 and 37'),
           ('pu', 'NAND_CE#', '10k', False, 'CE# 10k pull-up: chip deselected during host reset'),
           ('pu', 'NAND_RB#', '10k', False, 'RY/BY# is open drain: 10k pull-up (tr ~ 10k x Cload)'),
           ('pd', 'NAND_WP#', '10k', False, 'WP# 10k pull-down: protected at power-up/down (datasheet); host drives high to program/erase'),
           ('ser', 'NAND_WE#', 'WE#', '27R', False, 'WE# 27R source series termination at host'),
           ('ser', 'NAND_RE#', 'RE#', '27R', False, 'RE# 27R source series termination at host'),
           ('ser', 'NAND_CLE', 'CLE', '0R', False, 'CLE termination provision (0R, 27R if ringing)'),
           ('ser', 'NAND_ALE', 'ALE', '0R', False, 'ALE termination provision (0R, 27R if ringing)'),
           ('ser', 'NAND_CE#', 'CE#', '0R', False, 'CE# termination provision (0R)')]
    for i in range(8):
        net.append(('ser', f'NAND_IO{i}', f'IO{i}', '0R', False, f'IO{i} termination provision: 0R fitted, 27R if ringing (bidirectional - place mid-way or at host)'))
    notes = [f'{part["desc"]} - {part["mpn"]}',
             'LAYOUT: 100 nF on EACH VCC pin (12, 37) within 2 mm + one 1 uF; VSS pins 13/36 via directly to GND plane. Pins 20/38 are DNU - leave unconnected.',
             'Route IO0-IO7, CLE, ALE, WE#, RE# as one group over solid GND; length-match the group to +/-5 mm, keep < 75 mm, load <= 30 pF (datasheet test load).',
             'WE#/RE# are the timing strobes: 27R source termination within 5 mm of host, no stubs. IO/CLE/ALE/CE# 0R footprints let you fit 27R after SI check.',
             'RY/BY# open drain needs the 10k pull-up; WP# 10k pull-down holds VIL at power-up/down as recommended. 1-bit+ ECC (BCH/Hamming) required by host.',
             f'Typical use: {use}. Rename NAND bus labels to your controller nets.']
    meta = dict(desc=f'{part["desc"]} {part["mpn"]} parallel NAND block: per-pin decoupling, RB# pull-up, WP# pull-down, WE#/RE# series termination, bus termination provision. {use}.',
                kw=f'nand flash parallel onfi tsop48 {part["mpn"]} memory', fields={'Memory': part['desc'], 'Part': part['mpn'], 'Interface': 'x8 parallel NAND', 'Typical use': use})
    return build(name, part, act, net, notes, meta)

def P_(lib, val, fp, ds, desc, ipn, mfr, mpn, mfr2, mpn2, h=12.7):
    return dict(lib=lib, val=val, fp=fp, ds=ds, desc=desc, ipn=ipn, mfr=mfr, mpn=mpn, mfr2=mfr2, mpn2=mpn2, h=h)

QSPI_NOTES = ['QSPI: length-match IO0-IO3 to CLK within +/-2.5 mm (>=80 MHz), keep total length < 50 mm. 0R on IO lines = termination provision (fit 27R after scope/TDR check).',
              'WP#/IO2 and HOLD#/IO3 10k pull-ups are required when the host runs 1-1-1 or 1-1-2 modes (and during boot before QE is set).']
SPINAND_NOTES = QSPI_NOTES + ['Exposed pad (pin 9) to GND: 4 vias (0.3 mm) in the pad, solder-mask defined paste windows ~50 % coverage. Host must run bad-block management.']

def blocks():
    E = []
    E.append(('EEPROM', i2c_eeprom('EEPROM_I2C_256Kb_24LC256',
        P_('Memory_EEPROM:24LC256', '24LC256', FP['SO8N'], DS['24LC256'], '256Kb (32Kx8) I2C EEPROM, 400 kHz, 2.5-5.5 V, SOIC-8',
           'EEPROM-I2C-256K-SOIC8', 'Microchip', '24LC256T-I/SN', 'Microchip', '24AA256T-I/SN', h=7.62),
        ['1', '2', '3'], '7', 'WP', 'internal pull-down to VSS', '100nF', 'board ID / calibration / config storage')))
    E.append(('EEPROM', i2c_eeprom('EEPROM_I2C_64Kb_M24C64',
        P_('Chinmay_Memory:M24C64-RMN', 'M24C64-RMN6TP', FP['SO8N'], DS['M24C64'], '64Kb (8Kx8) I2C EEPROM, 1 MHz, 1.8-5.5 V, SO8N',
           'EEPROM-I2C-64K-SOIC8', 'STMicroelectronics', 'M24C64-RMN6TP', 'STMicroelectronics', 'M24C64-FMN6TP', h=7.62),
        ['1', '2', '3'], '7', 'WC#', 'internal pull-up = WRITE-PROTECTED if floating', '100nF', 'parameter / event-log storage, 1 MHz I2C')))
    E.append(('EEPROM', i2c_eeprom('EEPROM_I2C_2Kb_EUI48_24AA02E48',
        P_('Memory_EEPROM:24AA02E-OT', '24AA02E48T-I/OT', FP['SOT235'], DS['24AA02E48'], '2Kb I2C EEPROM with pre-programmed EUI-48 MAC, SOT-23-5',
           'EEPROM-I2C-2K-EUI48-SOT235', 'Microchip', '24AA02E48T-I/OT', 'Microchip', '24AA02E64T-I/OT', h=7.62),
        [], None, '', '', '100nF', 'Ethernet MAC address (EUI-48) source for PHY/MAC')))
    E.append(('EEPROM', spi_block('EEPROM_SPI_256Kb_AT25256B',
        P_('Memory_EEPROM:AT25xxx', 'AT25256B-SSHL-T', FP['SO8N'], DS['AT25256B'], '256Kb (32Kx8) SPI EEPROM, 20 MHz, 1.8-5.5 V, SOIC-8',
           'EEPROM-SPI-256K-SOIC8', 'Microchip', 'AT25256B-SSHL-T', 'Microchip', '25LC256T-I/SN', h=7.62),
        'EE', {'1': 'CS', '2': 'DO', '3': 'WP', '4': 'GND', '5': 'DI', '6': 'CLK', '7': 'HOLD', '8': 'VCC'},
        'fast-write parameter storage on an SPI bus', ['SPI <= 20 MHz: keep traces < 100 mm; MISO 0R can become 27R at the EEPROM end if the bus is long.'], quad=False, cap2=False)))
    norpins = {'1': 'CS', '2': 'DO', '3': 'WP', '4': 'GND', '5': 'DI', '6': 'CLK', '7': 'HOLD', '8': 'VCC'}
    E.append(('NOR', spi_block('NOR_QSPI_128Mb_W25Q128JVS',
        P_('Memory_Flash:W25Q128JVS', 'W25Q128JVSIQ', FP['SO8W'], DS['W25Q128JV'], '128Mbit Quad SPI NOR flash, 133 MHz, 2.7-3.6 V, SOIC-8 208 mil',
           'FLASH-NOR-128M-SOIC8W', 'Winbond', 'W25Q128JVSIQ', 'Winbond', 'W25Q128JVSIQ TR'),
        'NOR', norpins, 'MCU XIP / boot / FPGA configuration flash', QSPI_NOTES)))
    E.append(('NOR', spi_block('NOR_QSPI_128Mb_MX25L12833F',
        P_('Chinmay_Memory:MX25L12833FM2', 'MX25L12833FM2I-10G', FP['SO8W'], DS['MX25L12833F'], '128Mbit Quad SPI NOR flash, 133 MHz, 2.7-3.6 V, 8-SOP 200 mil',
           'FLASH-NOR-128M-SOIC8W-MX', 'Macronix', 'MX25L12833FM2I-10G', 'Winbond', 'W25Q128JVSIQ'),
        'NOR', norpins, 'MCU XIP / boot flash, second source to W25Q128', QSPI_NOTES)))
    E.append(('NOR', spi_block('NOR_QSPI_128Mb_IS25LP128F',
        P_('Chinmay_Memory:IS25LP128F-JB', 'IS25LP128F-JBLE', FP['SO8W'], DS['IS25LP128F'], '128Mbit Quad SPI/DTR NOR flash, 133 MHz, 2.3-3.6 V, -40..105 C, SOIC-8 208 mil',
           'FLASH-NOR-128M-SOIC8W-IS', 'ISSI', 'IS25LP128F-JBLE', 'ISSI', 'IS25LP128F-JBLE-TR'),
        'NOR', norpins, '105 C rated boot / XIP flash, DTR capable', QSPI_NOTES + ['Pin 7 is HOLD#/RESET#/IO3 (RESET function selectable) - keep the 10k pull-up.'])))
    nandpins = {'1': 'CS', '2': 'DO', '3': 'WP', '4': 'GND', '5': 'DI', '6': 'CLK', '7': 'HOLD', '8': 'VCC', '9': 'EP'}
    E.append(('NAND', spi_block('NAND_SPI_1Gb_MX35LF1GE4AB',
        P_('Chinmay_Memory:MX35LF1GE4AB-Z4', 'MX35LF1GE4AB-Z4I', FP['WSON8'], DS['MX35LF1GE4AB'], '1Gbit SLC SPI NAND flash, on-die 4-bit ECC, 104 MHz, 2.7-3.6 V, WSON-8 8x6',
           'FLASH-NAND-1G-SPI-WSON8', 'Macronix', 'MX35LF1GE4AB-Z4I', 'GigaDevice', 'GD5F1GQ5UEYIGR'),
        'NAND', nandpins, 'filesystem / data-logging storage over QSPI', SPINAND_NOTES)))
    E.append(('NAND', spi_block('NAND_SPI_1Gb_GD5F1GQ5UE',
        P_('Chinmay_Memory:GD5F1GQ5UEYIG', 'GD5F1GQ5UEYIGR', FP['WSON8'], DS['GD5F1GQ5UE'], '1Gbit SLC SPI NAND flash, on-die ECC, 133 MHz, 2.7-3.6 V, WSON-8 8x6',
           'FLASH-NAND-1G-SPI-WSON8-GD', 'GigaDevice', 'GD5F1GQ5UEYIGR', 'Macronix', 'MX35LF1GE4AB-Z4I'),
        'NAND', nandpins, 'filesystem / data-logging storage over QSPI, second source', SPINAND_NOTES)))
    E.append(('NAND', nand_parallel('NAND_PAR_1Gb_W29N01HV',
        P_('Chinmay_Memory:W29N01HVSINA', 'W29N01HVSINA', FP['TSOP48'], DS['W29N01HV'], '1Gbit SLC NAND flash, x8 parallel (ONFI 1.0), 25 ns, 2.7-3.6 V, TSOP-48 12x20',
           'FLASH-NAND-1G-PAR-TSOP48', 'Winbond', 'W29N01HVSINA', 'Winbond', 'W29N01HVSINA TR', h=17.78),
        'MPU / FPGA bulk storage on a parallel NAND controller (FMC/EMIF/GPMC)')))
    return E

if __name__ == '__main__':
    if os.path.isdir(ROOT): shutil.rmtree(ROOT)
    os.makedirs(ROOT)
    libsdirs = {'EEPROM': 'Chinmay_EEPROM', 'NAND': 'Chinmay_NAND', 'NOR': 'Chinmay_NOR'}
    names = []
    for grp, (name, b, libs, meta) in blocks():
        d = os.path.join(ROOT, libsdirs[grp] + '.kicad_blocks', name + '.kicad_block'); os.makedirs(d)
        f = os.path.join(d, name + '.kicad_sch'); b.write(f, name, libs)
        json.dump({'description': meta['desc'], 'keywords': meta['kw'], 'fields': meta['fields']}, open(os.path.join(d, name + '.json'), 'w'), indent=2)
        s = re.sub(r'"(?:[^"\\]|\\.)*"', '""', open(f).read()); assert s.count('(') == s.count(')'), name
        names.append((grp, name))
    tbl = '(design_block_lib_table\n  (version 7)\n' + ''.join(
        f'  (lib (name "{v}")(type "KiCad")(uri "${{KIPRJMOD}}/{v}.kicad_blocks")(options "")(descr "Chinmay {k} design blocks"))\n' for k, v in libsdirs.items()) + ')\n'
    open(os.path.join(ROOT, 'design-block-lib-table'), 'w').write(tbl)
    # symbol library
    hdr = '(kicad_symbol_lib\n  (version 20251024)\n  (generator "kicad_symbol_editor")\n  (generator_version "10.0")\n'
    body = ''
    for full, t in CUSTOM.items():
        body += t.replace(f'(symbol "{full}"', f'(symbol "{full.split(":")[1]}"', 1) + '\n'
    open(os.path.join(ROOT, 'Chinmay_Memory.kicad_sym'), 'w').write(hdr + body + ')\n')
    open(os.path.join(ROOT, 'sym-lib-table'), 'w').write('(sym_lib_table\n  (version 7)\n  (lib (name "Chinmay_Memory")(type "KiCad")(uri "${KIPRJMOD}/Chinmay_Memory.kicad_sym")(options "")(descr "Chinmay memory symbols"))\n)\n')
    print(names)
