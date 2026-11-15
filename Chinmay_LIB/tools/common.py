"""Chinmay house preferred passives (shared by WD_RST, USB2UART, BUCK, LDO, XTAL libraries).
House rules: R and small C in 0603; bulk MLCC 1206/1210; resistors 1% thick film; C0G for <=1nF, X7R otherwise
(X5R only where X7R is not available in the package). One IPN per (value, package, voltage, dielectric)."""
import re

def dk(m): return f'https://www.digikey.in/en/products/result?keywords={m}'
def mo(m): return f'https://www.mouser.in/c/?q={m}'

FP = {'0603C': 'Capacitor_SMD:C_0603_1608Metric', '0805C': 'Capacitor_SMD:C_0805_2012Metric',
      '1206C': 'Capacitor_SMD:C_1206_3216Metric', '1210C': 'Capacitor_SMD:C_1210_3225Metric',
      '0603R': 'Resistor_SMD:R_0603_1608Metric'}

# IPN : (value, footprint key, Manufacturer, MPN1, MFR2, MPN2, description)
CAPS = {
 'CAP-0603-2P2-50V-C0G':  ('2.2pF', '0603C', 'Murata', 'GRM1885C1H2R2CA01D', 'Samsung', 'CL10C2R2CB8NNNC', '2.2pF 50V C0G 0603'),
 'CAP-0603-10P-50V-C0G':  ('10pF', '0603C', 'Murata', 'GRM1885C1H100JA01D', 'Samsung', 'CL10C100JB8NNNC', '10pF 50V C0G 0603'),
 'CAP-0603-12P-50V-C0G':  ('12pF', '0603C', 'Murata', 'GRM1885C1H120JA01D', 'Samsung', 'CL10C120JB8NNNC', '12pF 50V C0G 0603'),
 'CAP-0603-15P-50V-C0G':  ('15pF', '0603C', 'Murata', 'GRM1885C1H150JA01D', 'Samsung', 'CL10C150JB8NNNC', '15pF 50V C0G 0603'),
 'CAP-0603-33P-50V-C0G':  ('33pF', '0603C', 'Murata', 'GRM1885C1H330JA01D', 'Samsung', 'CL10C330JB8NNNC', '33pF 50V C0G 0603'),
 'CAP-0603-47P-50V-C0G':  ('47pF', '0603C', 'Murata', 'GRM1885C1H470JA01D', 'Samsung', 'CL10C470JB8NNNC', '47pF 50V C0G 0603'),
 'CAP-0603-220P-50V-C0G': ('220pF', '0603C', 'Murata', 'GRM1885C1H221JA01D', 'Samsung', 'CL10C221JB8NNNC', '220pF 50V C0G 0603'),
 'CAP-0603-820P-50V-C0G': ('820pF', '0603C', 'Murata', 'GRM1885C1H821JA01D', 'Samsung', 'CL10C821JB8NNNC', '820pF 50V C0G 0603'),
 'CAP-0603-6N8-50V-X7R':  ('6.8nF', '0603C', 'Murata', 'GRM188R71H682KA01D', 'Samsung', 'CL10B682KB8NNNC', '6.8nF 50V X7R 0603'),
 'CAP-0603-10N-50V-X7R':  ('10nF', '0603C', 'Murata', 'GRM188R71H103KA01D', 'Samsung', 'CL10B103KB8NNNC', '10nF 50V X7R 0603'),
 'CAP-0603-22N-50V-X7R':  ('22nF', '0603C', 'Murata', 'GRM188R71H223KA01D', 'Samsung', 'CL10B223KB8NNNC', '22nF 50V X7R 0603'),
 'CAP-0603-39N-50V-X7R':  ('39nF', '0603C', 'Samsung', 'CL10B393KB8NNNC', 'Murata', 'GRM188R71H393KA61D', '39nF 50V X7R 0603'),
 'CAP-0603-100N-50V-X7R': ('100nF', '0603C', 'Samsung', 'CL10B104KB8NNNC', 'Murata', 'GRM188R71H104KA93D', '100nF 50V X7R 0603'),
 'CAP-0603-100N-100V-X7R':('100nF', '0603C', 'Murata', 'GRM188R72A104KA35D', 'TDK', 'C1608X7S2A104K080AB', '100nF 100V X7R 0603 (VIN > 42 V nets)'),
 'CAP-0603-330N-16V-X7R': ('330nF', '0603C', 'Samsung', 'CL10B334KO8NNNC', 'Murata', 'GRM188R71C334KA01D', '330nF 16V X7R 0603'),
 'CAP-0603-470N-16V-X7R': ('470nF', '0603C', 'Murata', 'GRM188R71C474KA88D', 'Samsung', 'CL10B474KO8NNNC', '470nF 16V X7R 0603'),
 'CAP-0603-1U-16V-X7R':   ('1uF', '0603C', 'Murata', 'GRM188R71C105KA12D', 'Samsung', 'CL10B105KO8NNNC', '1uF 16V X7R 0603'),
 'CAP-0603-2U2-10V-X7R':  ('2.2uF', '0603C', 'Murata', 'GRM188R71A225KE15D', 'Samsung', 'CL10B225KP8NNNC', '2.2uF 10V X7R 0603'),
 'CAP-0603-4U7-10V-X5R':  ('4.7uF', '0603C', 'Murata', 'GRM188R61A475KE15D', 'Samsung', 'CL10A475KP8NNNC', '4.7uF 10V X5R 0603'),
 'CAP-0805-1U-50V-X7R':   ('1uF', '0805C', 'Murata', 'GRM21BR71H105KA12L', 'Samsung', 'CL21B105KBFNNNE', '1uF 50V X7R 0805'),
 'CAP-1206-10U-25V-X7R':  ('10uF', '1206C', 'Murata', 'GRM31CR71E106KA12L', 'Samsung', 'CL31B106KAHNNNE', '10uF 25V X7R 1206'),
 'CAP-1210-2U2-100V-X7R': ('2.2uF', '1210C', 'Murata', 'GRM32ER72A225KA35L', 'TDK', 'C3225X7R2A225K230AB', '2.2uF 100V X7R 1210'),
 'CAP-1210-4U7-50V-X7R':  ('4.7uF', '1210C', 'Murata', 'GRM32ER71H475KA88L', 'TDK', 'C3225X7R1H475K250AB', '4.7uF 50V X7R 1210'),
 'CAP-1210-10U-50V-X7R':  ('10uF', '1210C', 'Murata', 'GRM32ER71H106KA12L', 'TDK', 'C3225X7R1H106K250AC', '10uF 50V X7R 1210'),
 'CAP-1210-22U-25V-X7R':  ('22uF', '1210C', 'Murata', 'GRM32ER71E226KE15L', 'TDK', 'C3225X7R1E226M250AC', '22uF 25V X7R 1210'),
 'CAP-1210-47U-10V-X7R':  ('47uF', '1210C', 'Murata', 'GRM32ER71A476KE15L', 'TDK', 'C3225X7R1A476M250AC', '47uF 10V X7R 1210'),
 'CAP-1210-100U-6V3-X5R': ('100uF', '1210C', 'Murata', 'GRM32ER60J107ME20L', 'TDK', 'C3225X5R0J107M250AC', '100uF 6.3V X5R 1210'),
}
# old MPN1 -> IPN  (everything found in the four existing libraries)
REMAP = {
 'GRM155R71C104KA88D': 'CAP-0603-100N-50V-X7R', 'CL10B104KB8NNNC': 'CAP-0603-100N-50V-X7R',
 'GRM188R71H104KA93D': 'CAP-0603-100N-50V-X7R', 'GRM188R72A104KA35D': 'CAP-0603-100N-100V-X7R',
 'GRM155R61A105KE15D': 'CAP-0603-1U-16V-X7R', 'GRM188R71C105KA12D': 'CAP-0603-1U-16V-X7R',
 'GRM155R61A474KE15D': 'CAP-0603-470N-16V-X7R', 'GRM188R61A475KE15D': 'CAP-0603-4U7-10V-X5R',
 'GRM1555C1H470JA01D': 'CAP-0603-47P-50V-C0G', 'GRM1555C1H270JA01D': 'CAP-0603-12P-50V-C0G',  # CH340G crystal caps -> 12 pF (crystal changed to CL 8 pF)
 'CL10B334KO8NNNC': 'CAP-0603-330N-16V-X7R', 'CL10B393KB8NNNC': 'CAP-0603-39N-50V-X7R',
 'GRM31CR71A226KE15L': 'CAP-1210-22U-25V-X7R', 'GRM32ER71A226KE20L': 'CAP-1210-22U-25V-X7R',
}
for ipn, v in CAPS.items():
    REMAP.setdefault(v[3], ipn)

def r_ohm(v):
    v = v.strip().replace('Ω', '').replace('ohm', '')
    m = re.match(r'^([\d.]+)\s*([kKmMR]?)([\d]*)$', v)
    if not m: return None
    a, u, b = m.groups()
    if b: a = a + '.' + b
    x = float(a)
    return x * {'k': 1e3, 'K': 1e3, 'M': 1e6, 'm': 1e6, 'R': 1, '': 1}[u]

def r_disp(o):
    if o >= 1e6: s = '%g' % (o / 1e6); return s + 'M'
    if o >= 1e3: s = '%g' % (o / 1e3); return s + 'k'
    return '%gR' % o

def r_fields(o):
    if o == 0:
        return dict(ipn='RES-0603-0R-JUMPER', value='0R', mfr='Yageo', mpn='RC0603JR-070RL', mfr2='Panasonic', mpn2='ERJ-3GEY0R00V',
                    desc='0R jumper 0603')
    d = r_disp(o)
    if o < 1e3: yc = ('%g' % o).replace('.', 'R') if '.' in '%g' % o else '%gR' % o
    elif o < 1e6: yc = ('%g' % (o / 1e3)).replace('.', 'K') if '.' in '%g' % (o / 1e3) else '%gK' % (o / 1e3)
    else: yc = ('%g' % (o / 1e6)).replace('.', 'M') if '.' in '%g' % (o / 1e6) else '%gM' % (o / 1e6)
    if o < 10: pc = ('%.2f' % o).replace('.', 'R')
    else:
        e = 0; mant = o
        while mant >= 1000: mant /= 10; e += 1
        while mant < 100: mant *= 10; e -= 1
        pc = '%03d%d' % (round(mant), e)
    return dict(ipn=f'RES-0603-{d}-1%', value=d, mfr='Yageo', mpn=f'RC0603FR-07{yc}L', mfr2='Panasonic', mpn2=f'ERJ-3EKF{pc}V',
                desc=f'{d} 1% 0603 thick film')

def r_alt(o):
    """Vishay CRCW (MPN3) and Bourns CR0603 (MPN4) 1% equivalents"""
    if o == 0: return ('Vishay Dale', 'CRCW06030000Z0EA', 'Bourns', 'CR0603-J/-000ELF')
    if o < 1e3: v = ('%.3g' % o); code = (v.replace('.', 'R') if '.' in v else v + 'R')
    elif o < 1e6: v = ('%.3g' % (o / 1e3)); code = (v.replace('.', 'K') if '.' in v else v + 'K')
    else: v = ('%.3g' % (o / 1e6)); code = (v.replace('.', 'M') if '.' in v else v + 'M')
    code = (code + '000')[:4] if len(code) < 4 else code
    e = 0; mant = o
    if o >= 10:
        while mant >= 1000: mant /= 10; e += 1
        while mant < 100: mant *= 10; e -= 1
        b = '%03d%d' % (round(mant), e)
    else:
        b = ('%.2f' % o).replace('.', 'R')
    return ('Vishay Dale', f'CRCW0603{code}FKEA', 'Bourns', f'CR0603-FX-{b}ELF')

def cap_fields(ipn):
    v = CAPS[ipn]
    return dict(ipn=ipn, value=v[0], fp=FP[v[1]], mfr=v[2], mpn=v[3], mfr2=v[4], mpn2=v[5], desc=v[6])
