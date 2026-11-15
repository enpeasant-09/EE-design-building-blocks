import re, os, json, shutil
CF = 'Chinmay_Footprints:'
REPL = {
 'Oscillator:Oscillator_SMD_ECS_2520MV-xxx-xx-4Pin_2.5x2.0mm': CF + 'Oscillator_SMD_ECS_2520MV-xxx-xx-4Pin_2.5x2.0mm',
 'Package_DFN_QFN:Maxim_TDFN-12-1EP_3x3mm_P0.5mm_EP1.7x2.5mm': CF + 'Maxim_TDFN-12-1EP_3x3mm_P0.5mm_EP1.7x2.5mm',
 'Package_DFN_QFN:TQFN-20-1EP_5x5mm_P0.65mm_EP3.25x3.25mm_ThermalVias': CF + 'TQFN-20-1EP_5x5mm_P0.65mm_EP3.25x3.25mm_ThermalVias',
 'Package_DFN_QFN:TQFN-20-1EP_5x5mm_P0.65mm_EP3.1x3.1mm_ThermalVias': CF + 'Maxim_T2044-4C_TQFN-20-1EP_4x4mm_P0.5mm_EP2.85x2.85mm_ThermalVias',
 'Package_DFN_QFN:WCH_QFN-16-1EP_3x3mm_P0.5mm_EP1.8x1.8mm': CF + 'WCH_QFN-16-1EP_3x3mm_P0.5mm_EP1.8x1.8mm',
 'Package_SON:VSON-8-1EP_3x3mm_P0.65mm_EP1.65x2.4mm': CF + 'VSON-8-1EP_3x3mm_P0.65mm_EP1.65x2.4mm',
 'Package_SON:WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm': CF + 'WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm',
 'Package_SO:Vishay_PowerPAK_1212-8_Single': CF + 'Vishay_PowerPAK_1212-8_Single',
 'Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3x3mm': CF + 'HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3x3mm',
 'Package_TO_SOT_SMD:Texas_DDF0008A_SOT-8_1.6x2.9mm_P0.65mm': CF + 'Texas_DDF0008A_SOT-8_1.6x2.9mm_P0.65mm',
 'Chinmay_Supervisor:ADI_WLCSP-6_0.96x1.46mm_P0.5mm': CF + 'ADI_WLCSP-6_0.96x1.46mm_P0.5mm',
}
NEWFP = {'LT8640S': CF + 'ADI_LQFN-24_4x4mm_P0.5mm_4xEP1.125mm_LT8640S', 'LT8645S': CF + 'ADI_LQFN-32_4x6mm_P0.5mm_6xEP_LT8645S',
         'LT8648S': CF + 'ADI_LQFN-36_4x7mm_P0.5mm_6xEP_LT8648S', 'MP8795H': CF + 'MPS_QFN-21_3x4mm_P0.4mm'}
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
def set_fp(b, fp):
    return re.sub(r'(\(property\s+"Footprint"\s+)"[^"]*"', lambda m: m.group(1) + '"' + fp + '"', b, count=1)
def fix(s):
    n = 0
    for a, b in REPL.items():
        n += s.count('"' + a + '"'); s = s.replace('"' + a + '"', '"' + b + '"')
    for part, fp in NEWFP.items():
        for pat in (r'\(symbol\s+\(lib_id\s+"Chinmay_Buck:%s"\)' % part, r'\(symbol\s+"Chinmay_Buck:%s"' % part, r'\(symbol\s+"%s"\s*\n?\s*\(' % part):
            out = []; pos = 0
            for m in re.finditer(pat, s):
                if m.start() < pos: continue
                e = blk(s, m.start()); out.append(s[pos:m.start()]); out.append(set_fp(s[m.start():e], fp)); pos = e; n += 1
            out.append(s[pos:]); s = ''.join(out)
    return s, n
if __name__ == '__main__':
    import sys
    up = '/mnt/user-data/uploads'; dst = '/mnt/user-data/outputs/fpfix'
    if os.path.isdir(dst): shutil.rmtree(dst)
    res = []
    for r, d, f in os.walk(up):
        for x in f:
            if not x.endswith(('.kicad_sch', '.kicad_sym')): continue
            p = os.path.join(r, x); rel = os.path.relpath(p, up)
            if not rel.startswith(('Chinmay_BUCK', 'Chinmay_WD_RST', 'Chinmay_USB2UART', 'Chinmay_XTAL')): continue
            s = open(p, encoding='utf-8').read(); s2, n = fix(s)
            if n:
                o = os.path.join(dst, rel); os.makedirs(os.path.dirname(o), exist_ok=True); open(o, 'w', encoding='utf-8').write(s2)
                res.append((rel, n))
    for x in res: print(x)
