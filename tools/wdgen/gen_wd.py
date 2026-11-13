"""Generate Chinmay's WD + reset project: one sheet per supervisor IC, replicating the
'WD and RST TPS3823' design block (supervisor -> OR(PROG bypass) -> open-drain buffer -> nRST,
MR push button with ESD diode), plus a KiCad symbol lib, footprint lib and design blocks."""
from __future__ import annotations

import json
import math
import os
import shutil
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "tools", "partwatch"))
sys.path.insert(0, HERE)
from partwatch import sexpr as S  # noqa: E402
from specs import ICS  # noqa: E402
import passives as PV  # noqa: E402

# Chinmay's original block is the template; it is read, never written.
TEMPLATE = os.path.join(REPO, "EE design blocks", "WD and RST TPS3823.kicad_block", "WD and RST TPS3823.kicad_sch")
OUT = os.environ.get("WDGEN_OUT", os.path.join(REPO, "projects", "Chinmay_WD_RST"))
BLOCKS_OUT = os.environ.get("WDGEN_BLOCKS", os.path.join(REPO, "EE design blocks"))
PROJECT = "Chinmay_WD_RST"
LIB = "Chinmay_Supervisor"
FONT = "(effects (font (size 1.27 1.27)))"


def U():
    return str(uuid.uuid4())


def f(v):
    v = round(v, 4)
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# --------------------------------------------------------------- template symbols
TXT = open(TEMPLATE, encoding="utf-8").read()


def _block(text, start):
    d = 0
    for i in range(start, len(text)):
        if text[i] == "(":
            d += 1
        elif text[i] == ")":
            d -= 1
            if d == 0:
                return text[start:i + 1]
    raise ValueError


LIBTEXT: dict[str, str] = {}
for name in ["74xGxx:74LVC1G07", "74xGxx:74LVC1G32", "Device:R_Small", "Diode:ESD9B3.3ST5G",
             "Jumper:Jumper_2_Open", "PCM_SparkFun-PowerSymbol:GND", "Power_Supervisor:TPS3823-xxDBV",
             "Switch:SW_Push", "power:+3V3"]:
    i = TXT.index(f'(symbol "{name}"')
    LIBTEXT[name] = _block(TXT, i)

# Stock-style C_Small and PWR_FLAG (same geometry as KiCad's Device/power libs)
LIBTEXT["Device:C_Small"] = (
    '(symbol "Device:C_Small" (pin_numbers (hide yes)) (pin_names (offset 0.254) (hide yes)) '
    '(exclude_from_sim no) (in_bom yes) (on_board yes)'
    ' (property "Reference" "C" (at 0.254 1.778 0) (effects (font (size 1.27 1.27)) (justify left)))'
    ' (property "Value" "C_Small" (at 0.254 -2.032 0) (effects (font (size 1.27 1.27)) (justify left)))'
    ' (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'
    ' (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'
    ' (property "Description" "Unpolarized capacitor, small symbol" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'
    ' (property "ki_fp_filters" "C_*" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'
    ' (symbol "C_Small_0_1"'
    ' (polyline (pts (xy -1.524 0.508) (xy 1.524 0.508)) (stroke (width 0.3302) (type default)) (fill (type none)))'
    ' (polyline (pts (xy -1.524 -0.508) (xy 1.524 -0.508)) (stroke (width 0.3048) (type default)) (fill (type none))))'
    ' (symbol "C_Small_1_1"'
    ' (pin passive line (at 0 2.54 270) (length 2.032) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))'
    ' (pin passive line (at 0 -2.54 90) (length 2.032) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27))))))'
    ' (embedded_fonts no))')
LIBTEXT["power:PWR_FLAG"] = (
    '(symbol "power:PWR_FLAG" (power) (pin_numbers (hide yes)) (pin_names (offset 0) (hide yes)) '
    '(exclude_from_sim no) (in_bom yes) (on_board yes)'
    ' (property "Reference" "#FLG" (at 0 1.905 0) (effects (font (size 1.27 1.27)) (hide yes)))'
    ' (property "Value" "PWR_FLAG" (at 0 3.81 0) (effects (font (size 1.27 1.27))))'
    ' (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'
    ' (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'
    ' (property "Description" "Special symbol for telling ERC where power comes from" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'
    ' (symbol "PWR_FLAG_0_0" (pin power_out line (at 0 0 90) (length 0) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27))))))'
    ' (symbol "PWR_FLAG_0_1" (polyline (pts (xy 0 0) (xy 0 1.27) (xy -1.016 1.905) (xy 0 2.54) (xy 1.016 1.905) (xy 0 1.27))'
    ' (stroke (width 0) (type default)) (fill (type none))))'
    ' (embedded_fonts no))')


def lib_pins(text):
    t = S.parse(text)
    out = {}

    def walk(n):
        for c in n[1:]:
            if S.head(c) == "pin":
                at = S.child(c, "at")
                out[str(S.child(c, "number")[1])] = (float(at[1]), float(at[2]), float(at[3]))
            elif S.head(c) == "symbol":
                walk(c)
    walk(t)
    return out


# --------------------------------------------------------------- custom symbols
PITCH = 5.08


def make_symbol(ic):
    """Box symbol, inputs left, outputs right, VDD top, GND/EP bottom; pins 5.08 apart.
    A CAP-role pin reserves two extra rows so its capacitor and GND symbol have room."""
    rows = {"L": [], "R": []}
    for p in ic["pins"]:
        if p[3] in rows:
            rows[p[3]].append(p)
            if p[4].startswith("CAP"):
                rows[p[3]] += [None, None]
    n = max(len(rows["L"]), len(rows["R"]), 4)
    y_top_row = PITCH * ((n - 1) // 2)
    body_top = y_top_row + 2.54
    body_bot = y_top_row - (n - 1) * PITCH - 2.54
    hw = 10.16
    pins = []
    for side, x, ang in (("L", -hw - 2.54, 0), ("R", hw + 2.54, 180)):
        for i, p in enumerate(rows[side]):
            if p:
                pins.append((p, x, y_top_row - i * PITCH, ang))
    tops = [p for p in ic["pins"] if p[3] == "T"]
    bots = [p for p in ic["pins"] if p[3] == "B"]
    for i, p in enumerate(tops):
        pins.append((p, 2.54 * i, body_top + 2.54, 270))
    for i, p in enumerate(bots):
        pins.append((p, 7.62 * i, body_bot - 2.54, 90))
    name = ic["key"]
    pin_txt = []
    for (num, pname, etype, side, role), x, y, ang in pins:
        hide = " (hide yes)" if pname == "EP" else ""
        pin_txt.append(f'(pin {etype} line (at {f(x)} {f(y)} {ang}) (length 2.54){hide} '
                       f'(name "{pname}" {FONT}) (number "{num}" {FONT}))')
    txt = (f'(symbol "{LIB}:{name}" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)'
           f' (property "Reference" "U" (at {f(-hw)} {f(body_top + 1.27)} 0) (effects (font (size 1.27 1.27)) (justify left)))'
           f' (property "Value" "{ic["value"]}" (at {f(-hw)} {f(body_bot - 1.27)} 0) (effects (font (size 1.27 1.27)) (justify left top)))'
           f' (property "Footprint" "{ic["fp"]}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'
           f' (property "Datasheet" "{ic["ds"]}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'
           f' (property "Description" "{ic["desc"]}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'
           f' (property "ki_keywords" "supervisor watchdog reset" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'
           f' (symbol "{name}_0_1" (rectangle (start {f(-hw)} {f(body_top)}) (end {f(hw)} {f(body_bot)})'
           f' (stroke (width 0.254) (type default)) (fill (type background))))'
           f' (symbol "{name}_1_1" ' + " ".join(pin_txt) + ') (embedded_fonts no))')
    return txt


# --------------------------------------------------------------- sheet builder
class Sheet:
    def __init__(self, page, title):
        self.page, self.title = page, title
        self.uuid = U()
        self.items: list[str] = []
        self.comps: list[dict] = []
        self.npwr = 0
        self.intent: list[tuple] = []  # (point, net) for verification

    # primitives
    def wire(self, a, b):
        self.items.append(f'(wire (pts (xy {f(a[0])} {f(a[1])}) (xy {f(b[0])} {f(b[1])})) '
                          f'(stroke (width 0) (type default)) (uuid "{U()}"))')

    def junction(self, p):
        self.items.append(f'(junction (at {f(p[0])} {f(p[1])}) (diameter 0) (color 0 0 0 0) (uuid "{U()}"))')

    def nc(self, p):
        self.items.append(f'(no_connect (at {f(p[0])} {f(p[1])}) (uuid "{U()}"))')

    def label(self, name, p, left=True):
        ang, j = (0, "left") if left else (180, "right")
        self.items.append(f'(label "{name}" (at {f(p[0])} {f(p[1])} {ang}) (effects (font (size 1.27 1.27)) '
                          f'(justify {j} bottom)) (uuid "{U()}"))')

    def hlabel(self, name, p, shape, left=True):
        ang, j = (0, "left") if left else (180, "right")
        self.items.append(f'(hierarchical_label "{name}" (shape {shape}) (at {f(p[0])} {f(p[1])} {ang}) '
                          f'(effects (font (size 1.27 1.27)) (justify {j})) (uuid "{U()}"))')

    def text(self, t, p, size=1.27, bold=False):
        b = " (thickness 0.254) (bold yes)" if bold else ""
        t = t.replace('"', "'").replace("\n", "\\n")
        self.items.append(f'(text "{t}" (exclude_from_sim no) (at {f(p[0])} {f(p[1])} 0) '
                          f'(effects (font (size {size} {size}){b}) (justify left bottom)) (uuid "{U()}"))')

    def place(self, lib, ref, value, at, rot=0, fp="", props=None, power=False):
        pins = lib_pins(LIBTEXT[lib])
        c = dict(lib=lib, ref=ref, value=value, x=at[0], y=at[1], rot=rot, fp=fp,
                 props=props or {}, power=power, pins=pins)
        self.comps.append(c)
        return c

    def pin(self, c, num):
        px, py, _ = c["pins"][num]
        py = -py
        a = math.radians(-c["rot"])
        rx = px * math.cos(a) - py * math.sin(a)
        ry = px * math.sin(a) + py * math.cos(a)
        return (round(c["x"] + rx, 4), round(c["y"] + ry, 4))

    def pwr(self, net, p):
        self.npwr += 1
        lib = "power:+3V3" if net == "+3V3" else "PCM_SparkFun-PowerSymbol:GND"
        self.place(lib, f"#PWR{self.page:02d}{self.npwr:02d}", net, p, power=True)

    def flag(self, p):
        self.npwr += 1
        self.place("power:PWR_FLAG", f"#FLG{self.page:02d}{self.npwr:02d}", "PWR_FLAG", p, power=True)

    # output
    def render(self, root_uuid, paper="A4"):
        out = ['(kicad_sch', '\t(version 20260306)', '\t(generator "eeschema")', '\t(generator_version "10.0")',
               f'\t(uuid "{self.uuid}")', f'\t(paper "{paper}")',
               f'\t(title_block (title "{self.title}") (company "Chinmay") (comment 1 "Replicates block: WD and RST TPS3823"))',
               '\t(lib_symbols']
        for lib in sorted({c["lib"] for c in self.comps}):
            out.append("\t\t" + LIBTEXT[lib])
        out.append("\t)")
        out += ["\t" + i for i in self.items]
        path = f"/{root_uuid}" + ("" if self.page == 1 else f"/{self.uuid_in_root}")
        for c in self.comps:
            hid = "(hide yes) " if c["power"] else ""
            ref_at = (c["x"], c["y"] + (3.81 if c["value"] == "GND" else -3.81)) if c["power"] else (c["x"] + 2.54, c["y"] - 6.35)
            val_at = (c["x"], c["y"] + (5.08 if c["value"] == "GND" else -5.08)) if c["power"] else (c["x"] + 2.54, c["y"] + 6.35)
            if not c["power"]:
                ref_at, val_at = c.get("ref_at", ref_at), c.get("val_at", val_at)
            fa = c.get("field_angle", 0)
            fj = c.get("field_justify", "left")
            props = [f'(property "Reference" "{c["ref"]}" (at {f(ref_at[0])} {f(ref_at[1])} {fa}) {hid}'
                     f'(effects (font (size 1.27 1.27)) (justify {fj})))',
                     f'(property "Value" "{c["value"]}" (at {f(val_at[0])} {f(val_at[1])} {fa}) '
                     f'(effects (font (size 1.27 1.27)) (justify {fj})))',
                     f'(property "Footprint" "{c["fp"]}" (at {f(c["x"])} {f(c["y"])} 0) (hide yes) {FONT})']
            for k, v in c["props"].items():
                v = str(v).replace('"', "'")
                props.append(f'(property "{k}" "{v}" (at {f(c["x"])} {f(c["y"])} 0) (hide yes) {FONT})')
            pins = " ".join(f'(pin "{n}" (uuid "{U()}"))' for n in c["pins"])
            out.append(f'\t(symbol (lib_id "{c["lib"]}") (at {f(c["x"])} {f(c["y"])} {c["rot"]}) (unit 1) (body_style 1) '
                       f'(exclude_from_sim no) (in_bom {"no" if c["power"] else "yes"}) (on_board {"no" if c["power"] else "yes"}) '
                       f'(in_pos_files {"no" if c["power"] else "yes"}) (dnp no) (uuid "{U()}") ' + " ".join(props) +
                       f' {pins} (instances (project "{PROJECT}" (path "{path}" (reference "{c["ref"]}") (unit 1)))))')
        return out


def field_set(ds="", desc="", mpn="", mfr="", alt="", procurement=""):
    return {"Datasheet": ds, "Description": desc, "Manufacturer": mfr,
            "Procurement": procurement or (PV.digikey(mpn) if mpn else ""),
            "Procurement2": PV.mouser(mpn) if mpn else "",
            "MPN1": mpn, "MPN2": alt, "Cost": ""}


USED = {}   # sheet -> list of (ref, passive key, derating summary)


def passive(sh, key, ref, desc, at, vapp, rot=0):
    """Place an approved passive: one MPN per value + operating condition, reused across all sheets."""
    p = PV.PASSIVES[key]
    lib = "Device:C_Small" if p["kind"] == "C" else "Device:R_Small"
    c = sh.place(lib, ref, p["value"], at, rot=rot, fp=p["fp"], props=PV.props(key, desc, vapp))
    s, ok = PV.derate(key, vapp)
    USED.setdefault(sh.title, []).append((ref, key, s, ok))
    return c


R_FP = "Resistor_SMD:R_0603_1608Metric"
C_FP = "Capacitor_SMD:C_0603_1608Metric"


def build_sheet(page, ic):
    sh = Sheet(page, f"WD and RST {ic['key']}")
    n = page
    sym_lib = ic.get("lib") or f"{LIB}:{ic['key']}"
    if sym_lib not in LIBTEXT:
        LIBTEXT[sym_lib] = make_symbol(ic)
    ICX, ICY = 88.9, 95.25
    pinspec = ic.get("pins") or [("4", "WDI", "input", "L", "WDI"), ("3", "~{MR}", "input", "L", "MR"),
                                 ("1", "~{RESET}", "output", "R", "RST"), ("5", "VDD", "power_in", "T", "VDD"),
                                 ("2", "GND", "power_in", "B", "GND")]
    u1 = sh.place(sym_lib, f"U{n}01", ic["value"], (ICX, ICY), fp=ic["fp"],
                  props=field_set(ic["ds"], ic["desc"], ic["mpn"], ic["mfr"], ic["alt"]))
    ys = [sh.pin(u1, p[0])[1] for p in pinspec]
    u1["ref_at"] = (ICX - 10.16, min(ys) - 3.81)
    u1["val_at"] = (ICX - 10.16, max(ys) + 9.53)

    # ---- supervisor pins
    for num, name, et, side, role in pinspec:
        p = sh.pin(u1, num)
        out = -1 if side == "L" else 1
        if role == "VDD":
            sh.pwr("+3V3", p); sh.intent.append((p, "+3V3"))
        elif role == "GND":
            sh.pwr("GND", p); sh.intent.append((p, "GND"))
        elif role in ("P3V3", "PGND"):
            e = (p[0] + out * 5.08, p[1]); sh.wire(p, e)
            net = "+3V3" if role == "P3V3" else "GND"
            sh.pwr(net, e); sh.intent.append((p, net))
        elif role == "NC":
            sh.nc(p); sh.intent.append((p, None))
        elif role == "WDI":
            e = (p[0] - 10.16, p[1]); sh.wire(p, e); sh.hlabel("WDI", e, "input", left=False)
            sh.intent.append((p, "WDI"))
        elif role == "MR":
            e = (p[0] - 10.16, p[1]); sh.wire(p, e); sh.label("~{MR}", e, left=False)
            sh.intent.append((p, "~{MR}"))
        elif role == "RST":
            e = (p[0] + 10.16, p[1]); sh.wire(p, e); sh.label("~{RST_SUP}", e, left=True)
            sh.intent.append((p, "~{RST_SUP}"))
        elif role.startswith("CAP"):
            val = role.split(":")[1]
            e = (p[0] + 7.62, p[1]); sh.wire(p, e)
            ccap = passive(sh, {"39n": "C39n", "330n": "C330n"}[val], f"C{n}{10 + len(sh.comps):02d}",
                           f"{name} timing capacitor (pin ramps to ~1.24 V)", (e[0], e[1] + 2.54), 1.3)
            ccap["ref_at"] = (e[0] + 3.05, e[1] + 2.0); ccap["val_at"] = (e[0] + 3.05, e[1] + 4.3)
            sh.pwr("GND", sh.pin(ccap, "2"))
            sh.intent += [(p, f"{name}_CAP"), (sh.pin(ccap, "2"), "GND")]

    # ---- decoupling, one per IC (top-left row)
    for i, (ref_ic, why) in enumerate([(f"U{n}01", "supervisor"), (f"U{n}02", "OR gate"), (f"U{n}03", "buffer")]):
        x = 38.1 + i * 10.16
        c = passive(sh, "C100n", f"C{n}{i + 1:02d}", f"Decoupling for {ref_ic} ({why}), place close to pin",
                    (x, 50.8), PV.V_RAIL)
        c["ref_at"] = (x + 1.27, 49.53); c["val_at"] = (x + 1.27, 53.34)
        sh.pwr("+3V3", sh.pin(c, "1")); sh.pwr("GND", sh.pin(c, "2"))
        sh.intent += [(sh.pin(c, "1"), "+3V3"), (sh.pin(c, "2"), "GND")]
    sh.text("Decoupling: one 100nF per IC", (35.56, 40.64))

    # ---- open-drain pull-up on supervisor output
    orx, ory = 160.02, 95.25
    u2 = sh.place("74xGxx:74LVC1G32", f"U{n}02", "74LVC1G32", (orx, ory), fp="Package_TO_SOT_SMD:SOT-23-5",
                  props=field_set("http://www.ti.com/lit/sg/scyt129e/scyt129e.pdf", "Single OR Gate, Low-Voltage CMOS",
                                  "SN74LVC1G32DBVR", "Texas Instruments"))
    a, b, y = sh.pin(u2, "1"), sh.pin(u2, "2"), sh.pin(u2, "4")
    sh.pwr("+3V3", sh.pin(u2, "5")); sh.pwr("GND", sh.pin(u2, "3"))
    ea = (a[0] - 12.7, a[1]); sh.label("~{RST_SUP}", ea, left=False)
    if ic.get("od"):
        sh.wire(a, (a[0] - 5.08, a[1])); sh.wire((a[0] - 5.08, a[1]), ea)
    else:
        sh.wire(a, ea)
    eb = (b[0] - 5.08, b[1]); sh.wire(b, eb); sh.label("PROG", eb, left=False)
    sh.intent += [(a, "~{RST_SUP}"), (b, "PROG"), (sh.pin(u2, "5"), "+3V3"), (sh.pin(u2, "3"), "GND")]
    if ic.get("od"):
        jx = a[0] - 5.08
        r = passive(sh, "R10k", f"R{n}02", "Pull-up for open-drain supervisor output", (jx, a[1] - 7.62), PV.V_RAIL)
        r["ref_at"] = (jx + 1.27, a[1] - 8.89); r["val_at"] = (jx + 1.27, a[1] - 6.35)
        sh.pwr("+3V3", sh.pin(r, "1")); sh.wire(sh.pin(r, "2"), (jx, a[1])); sh.junction((jx, a[1]))
        sh.intent += [(sh.pin(r, "1"), "+3V3"), (sh.pin(r, "2"), "~{RST_SUP}")]

    # ---- open-drain buffer to nRST
    u3 = sh.place("74xGxx:74LVC1G07", f"U{n}03", "74LVC1G07", (203.2, ory), fp="Package_TO_SOT_SMD:SOT-23-5",
                  props=field_set("https://www.ti.com/lit/ds/symlink/sn74lvc1g07.pdf",
                                  "Single Buffer Gate, Open Drain, Low-Voltage CMOS", "SN74LVC1G07DBVR", "Texas Instruments"))
    sh.wire(y, sh.pin(u3, "2"))
    sh.pwr("+3V3", sh.pin(u3, "5")); sh.pwr("GND", sh.pin(u3, "3")); sh.nc(sh.pin(u3, "1"))
    o = sh.pin(u3, "4"); eo = (o[0] + 10.16, o[1]); sh.wire(o, eo); sh.hlabel("nRST", eo, "output", left=True)
    sh.intent += [(y, "ORY"), (sh.pin(u3, "2"), "ORY"), (o, "nRST"), (sh.pin(u3, "5"), "+3V3"),
                  (sh.pin(u3, "3"), "GND"), (sh.pin(u3, "1"), None)]

    # ---- PROG bypass jumper + pull-down (as in the original block)
    jp = sh.place("Jumper:Jumper_2_Open", f"JP{n}01", "SJ_Open", (172.72, 66.04),
                  fp="Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
                  props=field_set(desc="Bridge during flashing to hold off watchdog resets"))
    ja, jb = sh.pin(jp, "1"), sh.pin(jp, "2")
    jp["ref_at"] = (ja[0] + 5.08, ja[1] - 5.08); jp["val_at"] = (ja[0] + 2.54, ja[1] + 3.81)
    pa = (ja[0] - 2.54, ja[1]); sh.wire(ja, pa); sh.pwr("+3V3", pa)
    node = (jb[0] + 5.08, jb[1]); sh.wire(jb, node)
    r1 = passive(sh, "R10k", f"R{n}01", "PROG pull-down (3.3 V across it when JP bridged)",
                 (node[0], node[1] + 5.08), PV.V_RAIL)
    r1["ref_at"] = (node[0] + 1.27, node[1] + 3.81); r1["val_at"] = (node[0] + 1.27, node[1] + 6.35)
    sh.wire(node, sh.pin(r1, "1")); sh.pwr("GND", sh.pin(r1, "2")); sh.junction(node)
    lp = (node[0] + 5.08, node[1]); sh.wire(node, lp); sh.label("PROG", lp, left=True)
    sh.intent += [(ja, "+3V3"), (jb, "PROG"), (sh.pin(r1, "1"), "PROG"), (sh.pin(r1, "2"), "GND")]

    # ---- manual reset: push button + ESD diode
    swprops = field_set(desc="Manual reset push button", mpn="PTS810SJK250SMTR LFS", mfr="C&K",
                        procurement="https://www.mouser.in/en/ProductDetail/CK/PTS810SJK250SMTR-LFS")
    esdprops = field_set("https://www.onsemi.com/pub/Collateral/ESD9B-D.PDF", "ESD protection diode, 3.3Vrwm, SOD-923",
                         "ESD9B3.3ST5G", "onsemi")
    if ic.get("has_mr"):
        mr_net = "~{MR}"
        sw = sh.place("Switch:SW_Push", f"SW{n}01", "SW_Push", (50.8, 132.08), fp="Button_Switch_SMD:SW_SPST_PTS810", props=swprops)
        s1, s2 = sh.pin(sw, "1"), sh.pin(sw, "2")
        sw["ref_at"] = (s1[0], s1[1] - 6.35); sw["val_at"] = (s1[0], s1[1] - 3.81)
        g = (s1[0], s1[1] + 5.08); sh.wire(s1, g); sh.pwr("GND", g)
        dpt = (s2[0] + 5.08, s2[1])
        nd = (s2[0] + 12.7, s2[1]); sh.wire(s2, dpt); sh.wire(dpt, nd); sh.label(mr_net, nd, left=True)
        d = sh.place("Diode:ESD9B3.3ST5G", f"D{n}01", "ESD9B3.3ST5G", (dpt[0], dpt[1] + 3.81), rot=90,
                     fp="Diode_SMD:D_SOD-923", props=esdprops)
        d["ref_at"] = (dpt[0] + 3.81, dpt[1] + 3.3); d["val_at"] = (dpt[0] + 3.81, dpt[1] + 5.6); d["field_angle"] = 90; d["field_justify"] = "right"
        sh.junction(dpt); sh.pwr("GND", sh.pin(d, "1"))
        sh.intent += [(s1, "GND"), (s2, mr_net), (sh.pin(d, "2"), mr_net), (sh.pin(d, "1"), "GND")]
        if ic.get("mr_pullup"):
            r3 = passive(sh, "R10k", f"R{n}03", "MR pull-up (no internal pull-up on this part)",
                         (nd[0], nd[1] - 7.62), PV.V_RAIL)
            r3["ref_at"] = (nd[0] + 1.27, nd[1] - 8.89); r3["val_at"] = (nd[0] + 1.27, nd[1] - 6.35)
            sh.pwr("+3V3", sh.pin(r3, "1")); sh.wire(sh.pin(r3, "2"), nd); sh.junction(nd)
            sh.intent += [(sh.pin(r3, "2"), mr_net), (sh.pin(r3, "1"), "+3V3")]
    else:
        # no MR pin: button + ESD hang straight off the nRST line (wired, no extra label)
        jx = o[0] + 5.08
        sh.items = [it for it in sh.items if not (it.startswith("(wire") and f"(xy {f(o[0])} {f(o[1])}) (xy {f(eo[0])} {f(eo[1])})" in it)]
        sh.wire(o, (jx, o[1])); sh.wire((jx, o[1]), eo); sh.junction((jx, o[1]))
        N = (jx, o[1] + 21.59)
        sh.wire((jx, o[1]), N)
        sw = sh.place("Switch:SW_Push", f"SW{n}01", "SW_Push", (N[0] - 5.08, N[1]), fp="Button_Switch_SMD:SW_SPST_PTS810", props=swprops)
        s1, s2 = sh.pin(sw, "1"), sh.pin(sw, "2")
        sw["ref_at"] = (s1[0], s1[1] - 6.35); sw["val_at"] = (s1[0], s1[1] - 3.81)
        g = (s1[0], s1[1] + 5.08); sh.wire(s1, g); sh.pwr("GND", g)
        d = sh.place("Diode:ESD9B3.3ST5G", f"D{n}01", "ESD9B3.3ST5G", (N[0], N[1] + 3.81), rot=90,
                     fp="Diode_SMD:D_SOD-923", props=esdprops)
        d["ref_at"] = (N[0] + 3.81, N[1] + 3.3); d["val_at"] = (N[0] + 3.81, N[1] + 5.6); d["field_angle"] = 90; d["field_justify"] = "right"
        sh.junction(N); sh.pwr("GND", sh.pin(d, "1"))
        sh.intent += [(s1, "GND"), (s2, "nRST"), (sh.pin(d, "2"), "nRST"), (sh.pin(d, "1"), "GND")]

    # ---- passive derating table (filled after all passives are placed)
    rows = USED.get(sh.title, [])
    lines = [f"PASSIVE DERATING  (Tamb max {PV.T_AMB_MAX:.0f}C, rail 3.3V+5%)"]
    for ref, key, summ, ok in rows:
        pp = PV.PASSIVES[key]
        lines.append(f"{ref:<6} {pp['value']:<6} {pp['mpn'][0]:<17} {summ}")
    lines.append("Alternates MPN2-4 on each part: same value/package, >= voltage, same dielectric")
    sh.text("\n".join(lines), (147.32, 137.16))

    # ---- text, matching the original block
    sh.text(f"Watchdog and Reset controller - {ic['value']}", (25.4, 30.48), size=2.0, bold=True)
    sh.text("Bridge jumper JP during flash \nThis circuit avoids the WD controller \nresetting the controller everytime you \ntry to flash ",
            (147.32, 50.8), bold=True)
    mr_txt = "Push button drives ~{MR}" if ic.get("has_mr") else "No MR pin on this IC: push button pulls nRST low directly"
    sh.text(f"{ic['desc']}\n{ic['note']}\n{mr_txt}\nAlternates (MPN2): {ic['alt'] or '-'}", (25.4, 160.02))
    return sh


# --------------------------------------------------------------- root sheet
def build_root(sheets):
    root = Sheet(1, "Chinmay WD and RST library")
    root.uuid_in_root = None
    cols, w, h = 4, 76.2, 25.4
    for i, sh in enumerate(sheets):
        x = 25.4 + (i % cols) * 96.52
        y = 50.8 + (i // cols) * 43.18
        sid = U(); sh.uuid_in_root = sid
        sh.sheet_xy = (x, y)
        root.items.append(
            f'(sheet (at {f(x)} {f(y)}) (size {f(w)} {f(h)}) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) '
            f'(fields_autoplaced yes) (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0000)) (uuid "{sid}") '
            f'(property "Sheetname" "{sh.title}" (at {f(x)} {f(y - 0.7112)} 0) (effects (font (size 1.27 1.27)) (justify left bottom))) '
            f'(property "Sheetfile" "{sh.file}" (at {f(x)} {f(y + h + 0.5888)} 0) (effects (font (size 1.27 1.27)) (justify left top))) '
            f'(pin "WDI" input (at {f(x)} {f(y + 7.62)} 180) (uuid "{U()}") (effects (font (size 1.27 1.27)) (justify left))) '
            f'(pin "nRST" output (at {f(x + w)} {f(y + 7.62)} 0) (uuid "{U()}") (effects (font (size 1.27 1.27)) (justify right))) '
            f'(instances (project "{PROJECT}" (path "/{root.uuid}" (page "{i + 2}")))))')
        root.text(sh.ic["value"], (x + 2.54, y + 15.24), size=1.5)
        root.text(sh.ic["mfr"], (x + 2.54, y + 19.05))
        # every sheet is a stand-alone test bench: tie its pins to dedicated nets
        root.nc((x, y + 7.62)); root.nc((x + w, y + 7.62))
    # power flags: the rails come from the board this block lands on
    # rails anchored on a bulk cap so the root power symbols have a real pin to land on
    cb = passive(root, "C10u", "C1", "Bulk capacitor on the incoming 3V3 rail (test bench only)", (38.1, 38.1), PV.V_RAIL)
    cb["ref_at"] = (39.37, 36.83); cb["val_at"] = (39.37, 40.64)
    t, b = root.pin(cb, "1"), root.pin(cb, "2")
    root.pwr("+3V3", t); root.wire(t, (t[0] - 7.62, t[1])); root.flag((t[0] - 7.62, t[1]))
    root.pwr("GND", b); root.wire(b, (b[0] - 7.62, b[1])); root.flag((b[0] - 7.62, b[1]))
    # consolidated passive list: one approved MPN per value + operating condition, reused everywhere
    from collections import Counter
    use = Counter(k for rows in USED.values() for _, k, _, _ in rows)
    lines = ["APPROVED PASSIVES (reused across all sheets: same value + rating + operating voltage = same MPN)"]
    for k, pp in PV.PASSIVES.items():
        alts = ", ".join(f"{a} ({m})" for a, m in pp["alts"])
        lines.append(f"{pp['ipn']:<24} x{use.get(k, 0):<3} {pp['mpn'][0]} ({pp['mpn'][1]})  |  alt: {alts}")
    lines.append(f"Derating rules: C applied V <= {PV.CAP_V_LIMIT:.0%} of rated, dielectric Tmax >= Tamb+{PV.TEMP_MARGIN:.0f}C; "
                 f"R power <= {PV.RES_P_LIMIT:.0%} of derated rating at {PV.T_AMB_MAX:.0f}C, V <= {PV.RES_V_LIMIT:.0%} of max working V")
    lines.append("C1 (X5R, 85C max) FAILS the temperature rule at Tamb 85C: test-bench only, not part of any block")
    root.text("\n".join(lines), (25.4, 274.32))
    root.text("Chinmay's watchdog + reset bricks - one sheet per supervisor IC", (25.4, 20.32), size=2.5, bold=True)
    root.text("Each sheet replicates 'WD and RST TPS3823': supervisor -> 74LVC1G32 (PROG bypass) -> 74LVC1G07 open drain -> nRST. "
              "Sheet pins: WDI (in), nRST (out).", (55.88, 30.48))
    return root


def write_file(path, lines):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n)\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    sheets = []
    for i, ic in enumerate(ICS):
        sh = build_sheet(i + 2, ic)
        sh.ic = ic
        sh.file = f"WD_RST_{ic['key']}.kicad_sch"
        sheets.append(sh)
    root = build_root(sheets)
    for sh in sheets:
        write_file(os.path.join(OUT, sh.file), sh.render(root.uuid))
    rl = root.render(root.uuid, paper="A3")
    rl.append('\t(sheet_instances (path "/" (page "1")))')
    write_file(os.path.join(OUT, f"{PROJECT}.kicad_sch"), rl)

    # project, lib tables, symbol library
    proj = {"meta": {"filename": f"{PROJECT}.kicad_pro", "version": 3},
            "schematic": {"drawing": {"default_text_size": 50.0}},
            "sheets": [[root.uuid, "Root"]] + [[sh.uuid_in_root, sh.title] for sh in sheets],
            "boards": [], "text_variables": {}}
    json.dump(proj, open(os.path.join(OUT, f"{PROJECT}.kicad_pro"), "w"), indent=2)
    lib_dir = os.environ.get("WDGEN_LIB", os.path.join(REPO, "library"))
    os.makedirs(lib_dir, exist_ok=True)
    if False:  # lib tables are maintained by hand in the repo (they point at ../../library)
      with open(os.path.join(OUT, "sym-lib-table"), "w") as fh:
        pass
    syms = [LIBTEXT[k] for k in sorted(LIBTEXT) if k.startswith(LIB + ":")]
    lib_txt = ["(kicad_symbol_lib", "\t(version 20251024)", '\t(generator "chinmay_wdgen")', '\t(generator_version "10.0")']
    for s in syms:
        lib_txt.append("\t" + s.replace(f'(symbol "{LIB}:', '(symbol "', 1))
    with open(os.path.join(lib_dir, f"{LIB}.kicad_sym"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lib_txt) + "\n)\n")
    os.makedirs(os.path.join(lib_dir, f"{LIB}.pretty"), exist_ok=True)
    from footprints import adm8613_wlcsp
    with open(os.path.join(lib_dir, f"{LIB}.pretty", "ADI_WLCSP-6_0.96x1.46mm_P0.5mm.kicad_mod"), "w") as fh:
        fh.write(adm8613_wlcsp())

    # design blocks (same sheet content, one folder per brick)
    for sh in sheets:
        # never overwrite Chinmay's original "WD and RST TPS3823" block
        name = f"WD and RST {sh.ic['key']}" + ("-33DBVR" if sh.ic["key"] == "TPS3823" else "")
        bdir = os.path.join(BLOCKS_OUT, f"{name}.kicad_block")
        os.makedirs(bdir, exist_ok=True)
        shutil.copy(os.path.join(OUT, sh.file), os.path.join(bdir, f"{name}.kicad_sch"))
        meta = {"description": f"The {sh.ic['value']} is a monitoring IC. This circuit implements MCU power and "
                               f"heartbeat monitoring. {sh.ic['note']}",
                "keywords": f"watchdog ; reset ; supervisor ; {sh.ic['key']} ; {sh.ic['mfr']}",
                "fields": {"MPN1": sh.ic["mpn"], "Manufacturer": sh.ic["mfr"]}}
        with open(os.path.join(bdir, f"{name}.json"), "w") as fh:
            json.dump(meta, fh, indent=1)
    json.dump({sh.file: [(list(p), n) for p, n in sh.intent] for sh in sheets},
              open(os.path.join(OUT, ".wdgen_intent.json"), "w"))
    print(f"{len(sheets)} sheets, {len(syms)} custom symbols ->", OUT)


if __name__ == "__main__":
    main()
