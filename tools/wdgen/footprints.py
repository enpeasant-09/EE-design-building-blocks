"""Custom footprint(s) for the Chinmay_Supervisor library."""
import uuid


def _u():
    return str(uuid.uuid4())


def adm8613_wlcsp():
    """ADM861x 6-ball WLCSP, 0.96 x 1.46 mm body, 0.50 mm pitch, 3 rows (A-C) x 2 columns.
    Ball map per ADM8611-8615 datasheet: A1 VCC, A2 GND, B1 WDI, B2 WD_DIS, C1 MR, C2 RESET.
    Pads 0.25 mm NSMD (mask 0.35 mm), typical for 0.5 mm-pitch WLCSP. Verify against the
    package drawing in the datasheet before release."""
    pads = []
    for r, row in enumerate("ABC"):
        for c, col in enumerate("12"):
            x = -0.25 + 0.5 * c
            y = -0.5 + 0.5 * r
            pads.append(
                f'\t(pad "{row}{col}" smd circle (at {x:g} {y:g}) (size 0.25 0.25) (layers "F.Cu" "F.Paste" "F.Mask") '
                f'(solder_mask_margin 0.05) (uuid "{_u()}"))')
    hx, hy = 0.48, 0.73
    lines = []

    def line(x1, y1, x2, y2, layer, w):
        lines.append(f'\t(fp_line (start {x1:g} {y1:g}) (end {x2:g} {y2:g}) (stroke (width {w}) (type solid)) '
                     f'(layer "{layer}") (uuid "{_u()}"))')

    # fab outline with pin-1 chamfer
    line(-hx + 0.2, -hy, hx, -hy, "F.Fab", 0.1); line(hx, -hy, hx, hy, "F.Fab", 0.1)
    line(hx, hy, -hx, hy, "F.Fab", 0.1); line(-hx, hy, -hx, -hy + 0.2, "F.Fab", 0.1)
    line(-hx, -hy + 0.2, -hx + 0.2, -hy, "F.Fab", 0.1)
    # courtyard
    cx, cy = hx + 0.25, hy + 0.25
    for a, b in (((-cx, -cy), (cx, -cy)), ((cx, -cy), (cx, cy)), ((cx, cy), (-cx, cy)), ((-cx, cy), (-cx, -cy))):
        line(*a, *b, "F.CrtYd", 0.05)
    # silk: corners + pin-1 mark
    sx, sy = hx + 0.11, hy + 0.11
    line(-sx, -sy + 0.3, -sx, -sy, "F.SilkS", 0.12); line(-sx, -sy, -sx + 0.3, -sy, "F.SilkS", 0.12)
    line(sx, sy - 0.3, sx, sy, "F.SilkS", 0.12); line(sx, sy, sx - 0.3, sy, "F.SilkS", 0.12)
    body = "\n".join(lines + pads)
    return f'''(footprint "ADI_WLCSP-6_0.96x1.46mm_P0.5mm"
\t(version 20241229)
\t(generator "chinmay_wdgen")
\t(generator_version "10.0")
\t(layer "F.Cu")
\t(descr "Analog Devices ADM861x 6-ball WLCSP, 0.96x1.46mm body, 3x2 balls, 0.5mm pitch, NSMD")
\t(tags "WLCSP CSP ADM8611 ADM8612 ADM8613 ADM8614 ADM8615")
\t(property "Reference" "REF**" (at 0 -1.5 0) (layer "F.SilkS") (uuid "{_u()}") (effects (font (size 0.5 0.5) (thickness 0.08))))
\t(property "Value" "ADI_WLCSP-6_0.96x1.46mm_P0.5mm" (at 0 1.5 0) (layer "F.Fab") (uuid "{_u()}") (effects (font (size 0.5 0.5) (thickness 0.08))))
\t(property "Datasheet" "https://www.analog.com/media/en/technical-documentation/data-sheets/adm8611_8612_8613_8614_8615.pdf" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{_u()}") (effects (font (size 1 1) (thickness 0.15))))
\t(property "Description" "ADM861x WLCSP-6" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{_u()}") (effects (font (size 1 1) (thickness 0.15))))
\t(attr smd)
{body}
\t(fp_text user "${{REFERENCE}}" (at 0 0 90) (layer "F.Fab") (uuid "{_u()}") (effects (font (size 0.25 0.25) (thickness 0.04))))
\t(embedded_fonts no)
)
'''
