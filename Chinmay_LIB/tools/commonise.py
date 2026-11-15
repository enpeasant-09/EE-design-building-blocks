"""Apply the house passive catalogue to existing KiCad schematics (in place, on copies)."""
import re, sys, json, uuid
from common import REMAP, CAPS, cap_fields, r_ohm, r_fields, r_alt, FP, dk, mo

def find_block(t, start):
    d = 0
    for k in range(start, len(t)):
        if t[k] == '(': d += 1
        elif t[k] == ')':
            d -= 1
            if d == 0: return k + 1
    raise ValueError

def lib_end(t):
    i = t.find('(lib_symbols')
    return find_block(t, i) if i >= 0 else 0

PROP_RE = r'\(property "{}" "((?:[^"\\]|\\.)*)"'

def set_prop(blk, name, val, hide=True):
    val = val.replace('\\', '\\\\').replace('"', '\\"')
    m = re.search(PROP_RE.format(re.escape(name)), blk)
    if m:
        return blk[:m.start(1)] + val + blk[m.end(1):]
    at = re.search(r'\(at ([-\d.]+) ([-\d.]+)', blk)
    x, y = at.group(1), at.group(2)
    ins = f'(property "{name}" "{val}" (at {x} {y} 0) (effects (font (size 1.27 1.27)){" (hide yes)" if hide else ""}))\n\t\t'
    p = blk.find('(pin "')
    if p < 0: p = blk.rfind('(instances')
    return blk[:p] + ins + blk[p:]

def get_prop(blk, name):
    m = re.search(PROP_RE.format(re.escape(name)), blk)
    return m.group(1) if m else None

def apply(f, log, extra=None):
    t = open(f).read()
    le = lib_end(t)
    out = t[:le]; pos = le; changes = 0
    for m in re.finditer(r'\(symbol\s*\(lib_id "([^"]+)"', t[le:]):
        s = le + m.start()
        if s < pos: continue
        e = find_block(t, s)
        blk = t[s:e]; lib = m.group(1); ref = get_prop(blk, 'Reference') or ''
        new = blk
        if extra and ref in extra:
            new = extra[ref](new)
        if lib.split(':')[-1] in ('R', 'R_Small') and not ref.startswith('#'):
            o = r_ohm(get_prop(blk, 'Value') or '')
            if o is not None:
                fd = r_fields(o)
                for k, v in (('Value', fd['value']), ('Footprint', FP['0603R']), ('IPN', fd['ipn']), ('Manufacturer', fd['mfr']),
                             ('MPN1', fd['mpn']), ('MFR2', fd['mfr2']), ('MPN2', fd['mpn2']),
                             ('Procurement', dk(fd['mpn'])), ('Procurement2', mo(fd['mpn']))):
                    new = set_prop(new, k, v, hide=(k != 'Value'))
                if get_prop(new, 'MPN3') is not None:
                    m3, p3, m4, p4 = r_alt(o)
                    for k, v in (('MFR3', m3), ('MPN3', p3), ('MFR4', m4), ('MPN4', p4)):
                        if get_prop(new, k) is not None: new = set_prop(new, k, v)
        elif lib.split(':')[-1] in ('C', 'C_Small'):
            mpn = get_prop(new, 'MPN1')
            ipn = REMAP.get(mpn)
            if ipn:
                fd = cap_fields(ipn)
                for k, v in (('Value', fd['value']), ('Footprint', fd['fp']), ('IPN', fd['ipn']), ('Manufacturer', fd['mfr']),
                             ('MPN1', fd['mpn']), ('MFR2', fd['mfr2']), ('MPN2', fd['mpn2']),
                             ('Procurement', dk(fd['mpn'])), ('Procurement2', mo(fd['mpn']))):
                    new = set_prop(new, k, v, hide=(k != 'Value'))
            else:
                log.append(f'{f.split("/")[-1]} {ref}: no catalogue match for {mpn}')
        if new != blk:
            changes += 1
            log.append(f'{f.split("/")[-1]} {ref}: {get_prop(blk,"Value")} {get_prop(blk,"MPN1")} -> {get_prop(new,"Value")} {get_prop(new,"MPN1")} [{get_prop(new,"IPN")}]')
        out += t[pos:s] + new; pos = e
    out += t[pos:]
    open(f, 'w').write(out)
    return changes
