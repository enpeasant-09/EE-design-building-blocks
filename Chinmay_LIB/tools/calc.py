"""Design calculations for Chinmay_BUCK design blocks (default VOUT = 3.3 V).
Every equation is taken from the part's datasheet (section noted in the text output)."""
import math

E96 = [1.00,1.02,1.05,1.07,1.10,1.13,1.15,1.18,1.21,1.24,1.27,1.30,1.33,1.37,1.40,1.43,1.47,1.50,
       1.54,1.58,1.62,1.65,1.69,1.74,1.78,1.82,1.87,1.91,1.96,2.00,2.05,2.10,2.15,2.21,2.26,2.32,
       2.37,2.43,2.49,2.55,2.61,2.67,2.74,2.80,2.87,2.94,3.01,3.09,3.16,3.24,3.32,3.40,3.48,3.57,
       3.65,3.74,3.83,3.92,4.02,4.12,4.22,4.32,4.42,4.53,4.64,4.75,4.87,4.99,5.11,5.23,5.36,5.49,
       5.62,5.76,5.90,6.04,6.19,6.34,6.49,6.65,6.81,6.98,7.15,7.32,7.50,7.68,7.87,8.06,8.25,8.45,
       8.66,8.87,9.09,9.31,9.53,9.76]
E12 = [1.0,1.2,1.5,1.8,2.2,2.7,3.3,3.9,4.7,5.6,6.8,8.2]

def nearest(v, series=E96):
    if v <= 0: return 0
    d = 10 ** math.floor(math.log10(v))
    cands = [s * d for s in series] + [series[0] * d * 10]
    return min(cands, key=lambda c: abs(c - v))

def above(v, series=E12):
    d = 10 ** math.floor(math.log10(v))
    for s in series + [10]:
        if s * d >= v * 0.999: return s * d

def best_pair(rtop_target, vref, vout, span=0.05):
    """choose E96 top within +/-span of target and nearest E96 bottom, minimising VOUT error"""
    best = None
    d = 10 ** math.floor(math.log10(rtop_target))
    for m in (d / 10, d, d * 10):
        for s_ in E96:
            rt = s_ * m
            if abs(rt / rtop_target - 1) > span: continue
            x = rt * vref / (vout - vref)
            dd = 10 ** math.floor(math.log10(x))
            for rb in [e * dd for e in E96] + [10 * dd]:
                if abs(rb / x - 1) > 0.04: continue
                err = abs(vref * (1 + rt / rb) - vout)
                if best is None or err < best[0]: best = (err, rt, rb)
    return best[1], best[2]

def fr(ohm):
    """format resistance in ohms -> '61.9k' style"""
    if ohm >= 1e6: s, u = ohm / 1e6, 'M'
    elif ohm >= 1e3: s, u = ohm / 1e3, 'k'
    else: s, u = ohm, ''
    t = ('%.3g' % s)
    return t + u if u else t + 'R'

def fc_(f):
    if f >= 1e-6: return '%.3gu' % (f * 1e6)
    if f >= 1e-9: return '%.3gn' % (f * 1e9)
    return '%.3gp' % (f * 1e12)

def fl(h):
    return '%.3guH' % (h * 1e6)

STD_VOUT = [1.8, 2.5, 3.3, 5.0, 12.0, 15.0, 24.0]

# ---------------------------------------------------------------- generic checks
def generic(p):
    """Common buck checks from the datasheet input/output capacitor, inductor and thermal sections."""
    Vn, Vx, Vo, Io, f, L = p['vin_nom'], p['vin_max'], p['vout'], p['iout'], p['fsw'], p['L']
    D = Vo / Vn
    dIn = Vo * (1 - Vo / Vn) / (L * f)
    dIx = Vo * (1 - Vo / Vx) / (L * f)
    ipk = Io + dIx / 2
    irms_in = Io * math.sqrt(D * (1 - D))
    cin = p['cin_eff']
    dvin = Io * D * (1 - D) / (f * cin)
    cout = p['cout_eff']
    dvo = dIn / (8 * f * cout)
    ton_x = Vo / (Vx * f)
    vin_max_ok = Vo / (p['ton_min'] * f)
    vin_min = (Vo + Io * 0.05) / (1 - f * p['toff_min']) if p.get('toff_min') else Vo / p['dmax']
    L_ = []
    L_.append('GENERIC CHECKS @ VIN=%gV nom / %gV max, VOUT=%gV, IOUT=%gA, fSW=%gkHz' % (Vn, Vx, Vo, Io, f / 1e3))
    L_.append('  D = VOUT/VIN = %.3f' % D)
    L_.append('  dIL = VOUT(1-VOUT/VIN)/(L*fSW): %.2fA @nom, %.2fA @max  (%.0f%% of IOUT)' % (dIn, dIx, 100 * dIx / Io))
    L_.append('  IL_PK = IOUT + dIL/2 = %.2fA ; inductor ISAT must exceed %s  (%s)' % (ipk, p['isat_req'], p['isat_note']))
    L_.append('  ICIN_RMS = IOUT*sqrt(D(1-D)) = %.2fA (max IOUT/2 = %.2fA at D=0.5)' % (irms_in, Io / 2))
    L_.append('  dVIN = IOUT*D(1-D)/(fSW*CIN) = %.0fmV with CIN_eff=%sF' % (dvin * 1e3, fc_(cin)))
    L_.append('  dVOUT_ripple = dIL/(8*fSW*COUT) = %.1fmV with COUT_eff=%sF (ESR excluded)' % (dvo * 1e3, fc_(cout)))
    L_.append('  tON @VINmax = VOUT/(VIN*fSW) = %.0fns vs tON_MIN(max)=%.0fns -> %s' % (ton_x * 1e9, p['ton_min'] * 1e9,
              'OK' if ton_x > p['ton_min'] else 'pulse skipping possible near VINmax'))
    L_.append('  Max VIN without pulse skipping = VOUT/(tON_MIN*fSW) = %.1fV' % vin_max_ok)
    L_.append('  Min VIN (dropout) ~ (VOUT+IOUT*R)/(1-fSW*tOFF_MIN) = %.2fV' % vin_min)
    pout = Vo * Io
    if p.get('rhs') is not None:
        k = 1.4  # RDS(on) hot multiplier (~100C junction)
        irms_l = math.sqrt(Io ** 2 + dIn ** 2 / 12)
        pcond = irms_l ** 2 * k * (D * p['rhs'] + (1 - D) * p['rls'])
        psw = 0.5 * Vn * Io * p['tsw'] * f
        pq = Vn * p.get('iq', 3e-3)
        pic = pcond + psw + pq
        how = 'Pcond=IL_RMS^2*1.4*(D*RDS_HS+(1-D)*RDS_LS)=%.2fW, Psw=0.5*VIN*IOUT*tsw*fSW=%.2fW (tsw~%.0fns), Pq=%.2fW' % (pcond, psw, p['tsw'] * 1e9, pq)
        how2 = '  RDS_HS=%.0fmOhm, RDS_LS=%s typ (datasheet EC table)' % (p['rhs'] * 1e3, ('%.0fmOhm' % (p['rls'] * 1e3)) if p['rls'] else 'external FET')
    else:
        ploss = pout * (1 / p['eta'] - 1)
        pic = max(ploss - Io ** 2 * p['dcr'], 0)
        how = 'PIC = POUT(1/eta-1) - IOUT^2*DCR = %.2fW (eta=%.2f ASSUMED - RDS(on) not published)' % (pic, p['eta'])
        how2 = None
    if p.get('thermal_lines'):
        L_.append('IC THERMAL (datasheet Typical Performance curves)')
        L_ += p['thermal_lines']
        return L_
    th = p['theta']
    L_.append('IC THERMAL @ VIN nom, full load (datasheet Power Dissipation / thermal sections)')
    L_.append('  ' + how)
    if how2: L_.append(how2)
    L_.append('  PIC = %.2fW ; thetaJA = %g C/W (%s) -> TJ = TA + thetaJA*PIC = %.0fC @25C, %.0fC @85C ; TA(max) for TJ=125C = %.0fC' %
              (pic, th, p.get('theta_src', 'JEDEC'), 25 + th * pic, 85 + th * pic, 125 - th * pic))
    L_.append('  Inductor DCR loss = IOUT^2*DCR = %.2fW' % (Io ** 2 * p['dcr']))
    return L_

# ---------------------------------------------------------------- per-part designs
def d_MAX17761():
    vin = (24, 6, 75); vo, io, f = 3.3, 1.0, 400e3
    # Datasheet: R4 = 15*VOUT/0.8 (kOhm); R5 = R4*0.8/(VOUT-0.8)
    R4, R5 = best_pair(15 * vo / 0.8 * 1e3, 0.8, vo)
    vout_act = 0.8 * (1 + R4 / R5)
    L = 2.6 * vo / f  # RILIM open/243k
    Lsel = 22e-6
    tss = 5.3e-3; css_min = 30e-6 * 47e-6 * 1e6 * vo * 1e-9 * 1e3  # CSS>=30e-6*CSEL(uF)*VOUT -> nF? (datasheet: CSS in F-units consistent)
    css = 22e-9; t_ss = css / 6.25e-6
    rrt = 105e3
    # UVLO: R2 = 1.215*R1/(VINU-1.215+2.5uA*R1)
    R1 = 3.32e6; vinu = 6.0; R2 = nearest(1.215 * R1 / (vinu - 1.215 + 2.5e-6 * R1))
    vinu_act = 1.215 * (R1 + R2) / R2 - 2.5e-6 * R1 * 0  # approx
    # Cout transient: COUT = 0.5*ISTEP*tRESP/dV, tRESP=0.33/fC, fC=min(15k,fsw/20)
    fcx = min(15e3, f / 20); istep = 0.25 * io; dv = 0.03 * vo
    cout_req = 0.5 * istep * (0.33 / fcx) / dv
    cout_eff = 30e-6
    # Comp: k = fC*COUT(uF)*(1+R4/R5)/3.6274e6 ; R6 = R4||R5 * k/(1-0.99k) ; C6 = 1.125e6/(fC*k/(1-k^2)*R6)
    k = fcx * cout_eff * 1e6 * (1 + R4 / R5) / 3.6274e6
    R6 = nearest((R4 * R5 / (R4 + R5)) / 1e3 * k / (1 - 0.99 * k) * 1e3)
    C6 = nearest(1.125e6 / (fcx * k / (1 - k * k) * R6 / 1e3) * 1e-9, E12)
    t = []
    t.append('DESIGN EQUATIONS - MAX17761 (Analog/Maxim 19-8608 Rev 1, Applications Information)')
    t.append('Design point: VIN %g V nom (%g-%g V), VOUT %.1f V, IOUT %.1f A, fSW 400 kHz, PFM, 1.6 A peak limit' % (vin[0], vin[1], vin[2], vo, io))
    t.append('Output voltage:  R4 = 15*VOUT/0.8 = %.1fk -> %s (E96 pair for min error) ;  R5 = R4*0.8/(VOUT-0.8) -> %s' % (15 * vo / 0.8, fr(R4), fr(R5)))
    t.append('  VOUT = 0.8*(1+R4/R5) = %.3f V   (datasheet Fig.5 uses 57.6k/18.2k = 3.332 V)' % vout_act)
    t.append('Switching freq:  RT/SYNC = 105k -> 400 kHz (EC table: 210k=200k, 140k=300k, 105k=400k, 69.8k=600k)')
    t.append('MODE/ILIM:  open -> PFM, ILIM_P = 1.6 A (Table 1: 422k PFM 1.14A, 243k PWM 1.6A, 121k PWM 1.14A)')
    t.append('Inductor:  L = 2.6*VOUT/fSW = %.1f uH -> 22 uH XAL5050-223ME (ISAT > 1.6 A peak limit)' % (L * 1e6))
    t.append('Output cap:  fC = min(15kHz, fSW/20) = %.0f kHz ; tRESP = 0.33/fC = %.1f us' % (fcx / 1e3, 0.33 / fcx * 1e6))
    t.append('  COUT >= 0.5*ISTEP*tRESP/dVOUT = 0.5*%.2fA*%.1fus/%.0fmV = %.1f uF  -> 47uF/10V X7R 1210 (~30uF eff)' %
             (istep, 0.33 / fcx * 1e6, dv * 1e3, cout_req * 1e6))
    t.append('Compensation (R6-C6 across R5):  k = fC*COUT*(1+R4/R5)/3.6274e6 = %.3f' % k)
    t.append('  R6 = (R4||R5)*k/(1-0.99k) = %s ;  C6 = 1.125e6/(fC*k/(1-k^2)*R6) = %s  (Fig.5: 15.4k / 6.8nF)' % (fr(R6), fc_(C6)))
    t.append('Soft-start:  CSS >= 30e-6*CSEL*VOUT ; tSS = CSS/6.25uA = %.1f ms with 22 nF (house-common value; min CSS = 30e-6*47*3.3 = 4.7 nF)' % (t_ss * 1e3))
    t.append('EN/UVLO:  R1 = 3.32M, R2 = 1.215*R1/(VINU-1.215+2.5uA*R1) = %s for VINU = %.1f V' % (fr(R2), vinu))
    t.append('VCC: 1uF to SGND. EXTVCC: tied to SGND (VOUT 3.3 V < EXTVCC switchover). RESET: 10k pull-up to VOUT.')
    p = dict(vin_nom=vin[0], vin_max=vin[2], vout=vo, iout=io, fsw=f, L=Lsel, cin_eff=1.6e-6, cout_eff=cout_eff,
             ton_min=110e-9, dmax=0.90, toff_min=None, eta=0.85, dcr=0.083, ta=85, theta=41, rhs=0.9, rls=0.275, tsw=20e-9,
             isat_req='1.6A (peak current limit)', isat_note='XAL5050-223: ISAT 3.5A')
    t += generic(p)
    table = []
    for v in STD_VOUT:
        if v / 0.90 + 0.5 > vin[2]: continue
        r4, r5 = best_pair(15 * v / 0.8 * 1e3, 0.8, v)
        table.append((v, fr(r4), fr(r5), 0.8 * (1 + r4 / r5), fl(nearest(2.6 * v / f * 1e6, E12) * 1e-6), '%.1f' % (v / 0.90 + 0.5)))
    parts = dict(R_top=('R4', fr(R4)), R_bot=('R5', fr(R5)), R6=fr(R6), C6=fc_(C6), R2=fr(R2))
    return t, table, parts

def max_fb_design(name, vin, vo, io, f, coef, vref, fcx, cout_eff, Lsel, ton_min, toff_min, eta, dcr, theta,
                  isat, isatnote, css, Rtop_dfig, Rbot_dfig, ilim):
    R3 = coef / (fcx / 1e3 * cout_eff * 1e6) * 1e3
    R3s = Rtop_dfig; R4s = Rbot_dfig
    tresp = 0.33 / fcx + 1 / f
    istep = 0.5 * io; dv = 0.03 * vo
    cout_req = 0.5 * istep * tresp / dv
    return R3, R3s, R4s, tresp, cout_req

def d_MAX17503():
    vin = (24, 6.5, 60); vo, io, f = 3.3, 2.5, 500e3
    fcx = f / 9; cout_eff = 30.6e-6
    R3 = 216e3 / (fcx / 1e3 * cout_eff * 1e6) * 1e3
    R3s = 127e3; R4s = 47.5e3
    vact = 0.9 * (1 + R3s / R4s)
    tresp = 0.33 / fcx + 1 / f; istep = 0.5 * io; dv = 0.03 * vo
    cout_req = 0.5 * istep * tresp / dv
    dev = 0.5 * istep * tresp / cout_eff
    R1 = 3.32e6; vinu = 6.0; R2 = nearest(R1 * 1.215 / (vinu - 1.215))
    t = ['DESIGN EQUATIONS - MAX17503 (Maxim 19-7005, Applications Information)',
         'Design point: VIN %g V nom (%g-%g V), VOUT 3.3 V, IOUT 2.5 A, fSW 500 kHz (RT open), PFM (MODE open)' % vin,
         'Inductor:  L = VOUT/fSW = %.2f uH -> 6.8 uH ; ISAT > 3.7 A peak current limit' % (vo / f * 1e6),
         'Crossover: fC = fSW/9 = %.1f kHz (fSW <= 500 kHz) ; tRESP = 0.33/fC + 1/fSW = %.2f us' % (fcx / 1e3, tresp * 1e6),
         'Output cap: COUT = 0.5*ISTEP*tRESP/dVOUT (ISTEP 50%%, dV 3%%) = %.1f uF eff required' % (cout_req * 1e6),
         '  Fitted: 47uF/10V X7R 1210 -> ~30.6uF eff @3.3V => step deviation = %.0f mV (%.1f%%)' % (dev * 1e3, dev / vo * 100),
         'FB divider: R3 = 216e3/(fC[kHz]*COUT[uF]) = %.0fk -> %s ;  R4 = R3*0.9/(VOUT-0.9) = %s' % (R3 / 1e3, fr(R3s), fr(R4s)),
         '  VOUT = 0.9*(1+R3/R4) = %.3f V' % vact,
         'Loop comp: internal; CF open because fSW >= 500 kHz (Table 2 C6 only below 500 kHz)',
         'Soft-start: CSS >= 28e-6*CSEL*VOUT = 4.3 nF ; tSS = CSS/5.55uA = %.2f ms with 10 nF (house-common value)' % (10e-9 / 5.55e-6 * 1e3),
         'EN/UVLO: R1 = 3.32M, R2 = R1*1.215/(VINU-1.215) = %s for VINU = %.1f V (VINU > 0.8*VOUT)' % (fr(R2), vinu),
         'BST: 0.1uF LX-BST. VCC: 2.2uF to SGND. SYNC: tied SGND (unused). RESET: 10k pull-up to VOUT.']
    p = dict(vin_nom=24, vin_max=60, vout=vo, iout=io, fsw=f, L=6.8e-6, cin_eff=1.6e-6, cout_eff=cout_eff,
             ton_min=135e-9, toff_min=160e-9, eta=0.87, dcr=0.025, ta=85, theta=33, rhs=0.165, rls=0.080, tsw=20e-9,
             isat_req='3.7A (peak current limit)', isat_note='XAL6060-682ME: ISAT 9A')
    t += generic(p)
    table = []
    for v in STD_VOUT:
        if v > 0.9 * vin[2] - 5: continue
        tr_ = 0.33 / fcx + 1 / f
        ce = 0.5 * (0.5 * io) * tr_ / (0.03 * v)
        r3 = nearest(216e3 / (fcx / 1e3 * ce * 1e6) * 1e3); r4 = nearest(r3 * 0.9 / (v - 0.9))
        if abs(v - 3.3) < 0.01: r3, r4 = R3s, R4s
        table.append((v, fr(r3), fr(r4), 0.9 * (1 + r3 / r4), fl(6.8e-6 if abs(v-3.3)<0.01 else nearest(v / f * 1e6, E12) * 1e-6), '%.1f' % (v / (1 - f * 160e-9) + 0.4)))
    return t, table, dict(R_top=('R3', fr(R3s)), R_bot=('R4', fr(R4s)), R2=fr(R2))

def d_MAX17506():
    vin = (24, 6.5, 60); vo, io, f = 3.3, 5.0, 450e3
    fcx = 50e3; cout_eff = 74.5e-6
    R3 = 451e3 / (fcx / 1e3 * cout_eff * 1e6) * 1e3
    R3s, R4s = 121e3, 45.3e3
    tresp = 0.33 / fcx + 1 / f; istep = 0.5 * io; dv = 0.03 * vo
    cout_req = 0.5 * istep * tresp / dv; dev = 0.5 * istep * tresp / cout_eff
    R1 = 3.32e6; vinu = 6.0; R2 = nearest(R1 * 1.215 / (vinu - 1.215))
    t = ['DESIGN EQUATIONS - MAX17506 (Maxim 19-8526, Applications Information)',
         'Design point: VIN 24 V nom (6.5-60 V), VOUT 3.3 V, IOUT 5 A, fSW 450 kHz (RT open), PFM (MODE/SYNC open)',
         'Inductor: L = VOUT/(2.2*fSW) = %.2f uH -> 3.3 uH XAL7070-332ME ; ISAT > 8.8 A runaway limit (RDL open)' % (vo / (2.2 * f) * 1e6),
         'Crossover: fC = fSW/9 (<=450 kHz) = 50 kHz ; tRESP = 0.33/fC + 1/fSW = %.2f us' % (tresp * 1e6),
         'Output cap: COUT = 0.5*ISTEP*tRESP/dVOUT = %.1f uF eff required ; fitted 2x47u + 22u (~74.5u eff) -> dV %.0f mV' %
         (cout_req * 1e6, dev * 1e3),
         'FB divider: R3 = 451e3/(fC[kHz]*COUT_SEL[uF]) = %.0fk -> 121k ;  R4 = R3*0.9/(VOUT-0.9) = 45.3k' % (R3 / 1e3),
         '  VOUT = 0.9*(1+R3/R4) = %.3f V (PWM/DCM, VFB 0.900 V) ; %.3f V in PFM (VFB 0.915 V)' % (0.9 * (1 + R3s / R4s), 0.915 * (1 + R3s / R4s)),
         'DL / N1: SiS468DN low-side MOSFET, 4.7R gate resistor; DL-SGND resistance open -> IPEAK 7.8 A, IRUNAWAY 8.8 A, hiccup',
         'Soft-start: CSS >= 28e-6*CSEL*VOUT ; tSS = CSS/5.55uA = %.1f ms with 22 nF' % (22e-9 / 5.55e-6 * 1e3),
         'EN/UVLO: R1 = 3.32M, R2 = R1*1.215/(VINU-1.215) = %s for VINU = %.1f V' % (fr(R2), vinu),
         'BST 0.1uF; VCC 2.2uF; CF open (fSW >= 450 kHz); EXTVCC to SGND (VOUT < 4.84 V); RESET 10k to VOUT.']
    p = dict(vin_nom=24, vin_max=60, vout=vo, iout=io, fsw=f, L=3.3e-6, cin_eff=3.2e-6, cout_eff=cout_eff,
             ton_min=160e-9, toff_min=160e-9, eta=0.88, dcr=0.012, ta=85, theta=23, theta_src='EV kit', rhs=0.045, rls=0.0, tsw=15e-9,
             isat_req='8.8A (runaway limit)', isat_note='XAL7070-332ME: ISAT 14A')
    t += generic(p)
    table = []
    for v in STD_VOUT:
        if v > 0.9 * vin[2] - 5: continue
        ce = 0.5 * (0.5 * io) * tresp / (0.03 * v)
        r3 = nearest(451e3 / (fcx / 1e3 * ce * 1e6) * 1e3); r4 = nearest(r3 * 0.9 / (v - 0.9))
        if abs(v - 3.3) < 0.01: r3, r4 = R3s, R4s
        table.append((v, fr(r3), fr(r4), 0.9 * (1 + r3 / r4), fl(3.3e-6 if abs(v-3.3)<0.01 else nearest(v / (2.2 * f) * 1e6, E12) * 1e-6), '%.1f' % (v / (1 - f * 160e-9) + 0.5)))
    return t, table, dict(R_top=('R3', fr(R3s)), R_bot=('R4', fr(R4s)), R2=fr(R2))

REN_L = {'RAA211630': {0.8: 1.5, 1.8: 3.3, 3.3: 6.8, 5: 8.2, 12: 22, 24: 47},
         'RAA211450': {0.8: 1.0, 1.8: 2.2, 3.3: 3.3, 5: 4.7, 12: 10, 24: 22}}

def d_RAA(name):
    big = name == 'RAA211450'
    vinmax = 42 if big else 60
    io = 5.0 if big else 3.0
    vo, f = 3.3, 400e3
    Lsel = 3.3e-6 if big else 6.8e-6
    RFB2 = 20e3; RFB1 = nearest(RFB2 * (vo - 0.8) / 0.8)
    dIL = vo * (1 - vo / 24) / (Lsel * f)
    css = 10e-9; tss = css * 0.8 / 5.3e-6
    RIN2 = 100e3; RIN1 = nearest(RIN2 * (6.0 - 1.25) / 1.25); vinf = 1.125 * (RIN1 + RIN2) / RIN2
    cout_eff = (3 * 47e-6 * 0.7) if big else (3 * 22e-6 * 0.75)
    c_rip = dIL / (8 * f * 0.010)
    istep = 0.5 * io; dv = 0.05 * vo
    c_up = Lsel * (istep + dIL / 2) ** 2 / (2 * (24 - vo) * dv)
    c_dn = Lsel * (istep + dIL / 2) ** 2 / (2 * vo * dv)
    c_loop = 87000 / (f / 1e3 * vo) * 1e-6
    lreq = 1000 * vo * (1 - vo / 24) / (0.4 * io * f / 1e3) * 1e-6
    doc = 'R16DS0183EU0102 Rev1.02' if big else 'R16DS0178EU0101 Rev1.01'
    t = ['DESIGN EQUATIONS - %s (Renesas %s, sections 5-6)' % (name, doc),
         'Design point: VIN 24 V nom (6-%g V), VOUT 3.3 V, IOUT %g A, fSW 400 kHz, HTSSOP-16 (adjustable SS)' % (vinmax, io),
         'FB divider (EQ.4): RFB1 = RFB2*(VOUT-0.8)/0.8, RFB2 = 20k -> RFB1 = %s ; VOUT = %.3f V' % (fr(RFB1), 0.8 * (1 + RFB1 / RFB2)),
         'Frequency: RFS = 261k -> 400 kHz (Table 1: 590k 200k, 374k 300k, 261k 400k, 205k 500k, 165k 600k, 121k 800k)',
         'Inductor (EQ.6): L = 1000*VOUT(1-D)/(dIL*fSW[kHz]), dIL = 40%% IOUT -> %.2f uH ; Sec 2.3 table -> %s' % (lreq * 1e6, fl(Lsel)),
         '  dIL (EQ.5) = %.2f A @24 V ; peak = %.2f A (< HS peak limit %s)' % (dIL, io + dIL / 2, '8.5 A' if big else '5 A'),
         'Input cap (EQ.7/8): IIN_RMS = IOUT*sqrt(D(1-D)) ; CIN = IOUT*D(1-D)/(fSW*dVIN)',
         'Output cap: EQ.9 ripple (10 mV) %.1f uF ; EQ.10 step-up %.1f uF ; EQ.11 step-down %.1f uF ; EQ.12 loop %.1f uF' %
         (c_rip * 1e6, c_up * 1e6, c_dn * 1e6, c_loop * 1e6),
         '  (ISTEP = 50%% IOUT, dV = 5%%) -> fitted %s (~%.0f uF eff) per Sec 2.3' % ('3x47uF/10V 1210' if big else '3x22uF 1210', cout_eff * 1e6),
         'Soft-start (EQ.1): tSS = CSS*VREF/ISS = 10nF*0.8V/5.3uA = %.2f ms (house-common 10 nF)' % (tss * 1e3),
         'UVLO (EQ.2/3): RIN1 = RIN2*(VINR-1.25)/1.25, RIN2 = 100k, VINR 6.0 V -> %s ; VINF = 1.125*(RIN1+RIN2)/RIN2 = %.2f V' % (fr(RIN1), vinf),
         'EBIAS tied to VOUT (3.3-40 V aux LDO) ; VCC 2.2uF ; BOOT 0.1uF ; PG 10k pull-up to VOUT (<=3.3 V)']
    p = dict(vin_nom=24, vin_max=vinmax, vout=vo, iout=io, fsw=f, L=Lsel, cin_eff=3.0e-6, cout_eff=cout_eff,
             ton_min=96e-9, toff_min=220e-9, eta=0.85 if big else 0.86, dcr=0.012 if big else 0.025, ta=85, theta=35.0, rhs=0.115 if big else 0.155, rls=0.040 if big else 0.055, tsw=15e-9,
             isat_req=('9.5A (max peak limit)' if big else '6A (max peak limit)'),
             isat_note=('XAL7070-332ME: ISAT 14A' if big else 'XAL6060-682ME: ISAT 9A'))
    t += generic(p)
    table = []
    for v in STD_VOUT:
        if v > 0.9 * vinmax - 5: continue
        r1 = nearest(20e3 * (v - 0.8) / 0.8)
        lv = REN_L[name].get(v) if v in REN_L[name] else REN_L[name].get(round(v)) if round(v) in REN_L[name] and abs(round(v)-v)<0.01 else None
        lv = lv if lv else nearest(1000 * v * (1 - v / max(24, v / 0.6)) / (0.25 * io * 400), E12)
        table.append((v, fr(r1), '20k', 0.8 * (1 + r1 / 20e3), '%guH' % lv, '%.1f' % (v / (1 - f * 220e-9) + 0.5)))
    return t, table, dict(R_top=('RFB1', fr(RFB1)), R_bot=('RFB2', '20k'), RIN1=fr(RIN1))

LT = {
 'LT8640S': dict(vref=0.970, vin=(12, 6, 42), io=6, f=1e6, rt=41.2e3, L=2.2e-6, k=0.7, vswb=0.15, ilim=10, Ltxt='XEL6030-222ME',
                 ton=50e-9, toff=110e-9, eta=0.88, dcr=0.0058, theta=24, ss=10e-9, isat='12.5A (max top-switch limit)',
                 R1=1e6, R2=412e3, rhs=0.066, rls=0.027, cff='10p', venth=1.00, doc='LT8640S Rev D', cout='100uF/6.3V 1210', coute=70e-6, cin=4.7e-6, fig='Fig.11'),
 'LT8645S': dict(vref=0.970, vin=(12, 6, 65), io=8, f=500e3, rt=88.7e3, L=3.3e-6, k=0.4, vswb=0.2, ilim=14, Ltxt='XAL7070-332ME',
                 ton=65e-9, toff=110e-9, eta=0.89, dcr=0.0108, theta=17, ss=10e-9, isat='17.5A (max top-switch limit)',
                 R1=1e6, R2=412e3, rhs=0.036, rls=0.025, cff='2.2p', venth=1.01, doc='LT8645S Rev E', cout='2x47uF/10V 1210', coute=60e-6, cin=3.2e-6, fig='Fig.9'),
 'LT8648S': dict(vref=0.600, vin=(12, 6, 42), io=15, f=400e3, rt=105e3, L=2.2e-6, k=0.2, vswb=0.07, ilim=30, Ltxt='XAL8080-222ME',
                 ton=40e-9, toff=100e-9, eta=0.88, dcr=0.0019, theta=15, ss=10e-9, isat='34A (max top-switch limit)',
                 R1=100e3, R2=22.1e3, rhs=0.012, rls=0.0045, cff='33p', venth=0.98, doc='LT8648S Rev E', cout='3x47uF/10V 1210', coute=95e-6, cin=10e-6, fig='Fig.10'),
}

def d_LT(name):
    c = LT[name]; vo = 3.3; io = c['io']; f = c['f']
    rt_eq = (46.5 / (f / 1e6) - 5.2) if name != 'LT8648S' else (44.8 / (f / 1e6) - 5.9)
    rteq_txt = 'RT = 44.8/fSW[MHz] - 5.9' if name == 'LT8648S' else 'RT = 46.5/fSW[MHz] - 5.2'
    Lcalc = (vo + c['vswb']) / (f / 1e6) * c['k']
    R1, R2 = c['R1'], c['R2']
    vact = c['vref'] * (1 + R1 / R2)
    R4 = 100e3; R3 = nearest(R4 * (6.0 / c['venth'] - 1))
    tss = c['ss'] * c['vref'] / (2.0e-6 if name == 'LT8648S' else 1.9e-6)
    dIL = vo / (c['L'] * f) * (1 - vo / c['vin'][2])
    iomax = c['ilim'] - dIL / 2
    t = ['DESIGN EQUATIONS - %s (Analog Devices %s, Applications Information; replicates %s)' % (name, c['doc'], c['fig']),
         'Design point: VIN %g V nom (%g-%g V), VOUT 3.3 V, IOUT %g A, fSW %g kHz' % (c['vin'] + (io, f / 1e3)),
         'FB divider: R1 = R2*(VOUT/%.3f - 1) ; R1 = %s, R2 = %s -> VOUT = %.3f V ; phase-lead CFF %sF across R1' %
         (c['vref'], fr(R1), fr(R2), vact, c['cff']),
         'Frequency: %s = %.1fk -> %s (E96)' % (rteq_txt, rt_eq, fr(c['rt'])),
         'Inductor: L = (VOUT + VSW(BOT))/fSW[MHz] * %.1f = %.2f uH -> %s %s' % (c['k'], Lcalc, fl(c['L']), c['Ltxt']),
         '  dIL = VOUT/(L*fSW)*(1-VOUT/VINmax) = %.2f A ; IOUT(MAX) = ILIM - dIL/2 = %g - %.2f = %.1f A' % (dIL, c['ilim'], dIL / 2, iomax),
         'EN/UV: VIN(EN) = (R3/R4 + 1)*%.2fV ; R4 = 100k, VIN(EN) = 6.0 V -> R3 = %s' % (c['venth'], fr(R3)),
         'Soft-start: tSS = CSS*VFB/ISS = 10nF*%.2fV/%.1fuA = %.1f ms ; PG 10k pull-up to VOUT (house-common) ; BIAS to VOUT' %
         (c['vref'], 2.0 if name == 'LT8648S' else 1.9, tss * 1e3),
         'SYNC/MODE to GND (Burst Mode); CLKOUT n/c. Silent Switcher: split CIN symmetrically across both VIN pin groups.']
    if name == 'LT8648S':
        t.append('External comp (VC): RC 6.65k + CC 820pF per datasheet Fig.10 ; INTVCC 1uF')
    p = dict(vin_nom=c['vin'][0], vin_max=c['vin'][2], vout=vo, iout=io, fsw=f, L=c['L'], cin_eff=c['cin'], cout_eff=c['coute'],
             ton_min=c['ton'], toff_min=c['toff'], eta=c['eta'], dcr=c['dcr'], ta=85, theta=c['theta'],
             isat_req=c['isat'], isat_note=c['Ltxt'], rhs=c['rhs'], rls=c['rls'], tsw=4e-9, theta_src='ADI demo board')
    t += generic(p)
    table = []
    for v in STD_VOUT:
        if v > c['vin'][2] - 6: continue
        if c['vref'] < 0.9:
            r1 = c['R1']; r2 = nearest(r1 / (v / c['vref'] - 1))
        else:
            r1 = c['R1']; r2 = nearest(r1 / (v / c['vref'] - 1))
        if abs(v - 3.3) < 0.01: r2 = c['R2']
        lv = c['L'] if abs(v - 3.3) < 0.01 else nearest((v + c['vswb']) / (f / 1e6) * c['k'], E12) * 1e-6
        table.append((v, fr(r1), fr(r2), c['vref'] * (1 + r1 / r2), fl(lv), '%.1f' % ((v + c['vswb']) / (1 - f * c['toff']) + 0.3)))
    return t, table, dict(R_top=('R1', fr(R1)), R_bot=('R2', fr(R2)), R3=fr(R3), RT=fr(c['rt']))

def d_MP8795H():
    vin = (12, 6, 16); vo, io, f = 3.3, 20, 600e3
    RFB1 = 20e3; RFB2 = nearest(0.6 / (vo - 0.6) * RFB1)
    dI = 0.3 * io
    L = vo * (1 - vo / vin[0]) / (f * dI)
    Lsel = 0.68e-6
    dIL = vo * (1 - vo / vin[0]) / (f * Lsel)
    ilim = 25.0
    Rcs = nearest(1.2 / (10e-6 * (ilim - dIL / 2)))
    cff = 1 / (2 * math.pi * RFB1 * 40e3)
    cffs = 220e-12; fz = 1 / (2 * math.pi * RFB1 * cffs)
    css = 122e-9; tss = css * 1e9 * 0.6 / 36 if False else (css * 1e9) * 0.6 / 36  # CSS(nF)=tss(ms)*36uA/0.6V -> tss=CSS*0.6/36
    Rup = 383e3; ven_max = 16 * 100e3 / (Rup + 100e3)  # 383k shared with Renesas UVLO
    t = ['DESIGN EQUATIONS - MP8795H (MPS MP8795H Rev1.0, Application Information)',
         'Design point: VIN 12 V nom (6-16 V), VOUT 3.3 V, IOUT 20 A, fSW 600 kHz (MODE = GND), forced CCM',
         'FB (Eq.3): RFB2 = VREF/(VOUT-VREF)*RFB1, RFB1 = 20k, VREF 0.6 V -> RFB2 = %s ; VOUT = %.3f V' % (fr(RFB2), 0.6 * (1 + RFB1 / RFB2)),
         'CFF (Eq.4): fZ = 1/(2pi*RFB1*CFF) in 20-60 kHz -> CFF = 220 pF, fZ = %.0f kHz' % (fz / 1e3),
         'MODE: GND = 600 kHz ; 30.1k = 800 kHz ; 60.4k = 1 MHz (Table 1)',
         'Inductor (Eq.14): L = VOUT(1-VOUT/VIN)/(fSW*dIL), dIL = 30%% of 20 A -> %.3f uH -> 0.68 uH XAL1010-681ME' % (L * 1e6),
         '  dIL = %.2f A ; ILP (Eq.15) = IOUT + dIL/2 = %.1f A' % (dIL, io + dIL / 2),
         'Current limit (Eq.2): RCS = VOCP/(GCS*(ILIM - dIL/2)), VOCP 1.2 V, GCS 10uA/A, ILIM 25 A -> RCS = %s' % fr(Rcs),
         'Soft-start (Eq.1): CSS(nF) = tSS(ms)*36uA/0.6V ; CSS1+CSS2 = 22n+100n -> tSS = %.2f ms (min 1 ms internal)' % tss,
         'EN (Eq.5): VIN_START = 1.22*(RUP+RDOWN)/RDOWN ; RDOWN 100k, RUP = %s (house-common) -> VIN_START = %.2f V ; VEN @16 V = %.2f V (<3.6 V)' % (fr(Rup), 1.22*(Rup+100e3)/100e3, ven_max),
         'Input cap (Eq.7-9): ICIN = IOUT*sqrt(D(1-D)) ; dVIN = IOUT*D(1-D)/(fSW*CIN)',
         'VCC 2.2uF (>=1uF); BST 0.1uF; PGOOD 10k to VOUT (<3.6 V); VSNS- to GND at COUT (remote sense optional)']
    p = dict(vin_nom=12, vin_max=16, vout=vo, iout=io, fsw=f, L=Lsel, cin_eff=40e-6, cout_eff=280e-6,
             ton_min=50e-9, toff_min=180e-9, thermal_lines=[
               '  Efficiency curve (12 VIN, 800 kHz): 94% @5 V, 91% @2.5 V, 20 A -> ~92.5% @3.3 V ; PLOSS = 66W(1/0.925-1) = 5.4 W total',
               '  Thermal curve (800 kHz, no airflow, EVB): case ~105C @5 V and ~83C @2.5 V at 20 A, TA 25C -> ~90C @3.3 V',
               '  => case rise ~65C at 20 A: TA(max) ~ 60C at full load without airflow ; use EVB-class 6-layer 2oz copper + vias,',
               '     derate to ~16 A at 85C ambient or add airflow / heatsink. Inductor DCR loss = 0.31 W'],
             eta=0.925, dcr=0.00078, ta=85, theta=29, theta_src='EV8795H 6-layer',
             isat_req='25A (RCS limit) + dIL/2', isat_note='XAL1010-681ME: ISAT 46A')
    t += generic(p)
    table = []
    for v in STD_VOUT:
        if v > 0.9 * vin[2] - 1.5: continue
        r2 = nearest(0.6 / (v - 0.6) * 20e3)
        vv = 12 if v < 8 else 16
        lv = 0.68e-6 if abs(v - 3.3) < 0.01 else nearest(v * (1 - v / vv) / (f * 6) * 1e6, E12) * 1e-6
        table.append((v, '20k', fr(r2), 0.6 * (1 + 20e3 / r2), fl(lv), '%.1f' % (v / (1 - f * 180e-9) + 0.5)))
    return t, table, dict(R_top=('RFB1', '20k'), R_bot=('RFB2', fr(RFB2)), RCS=fr(Rcs), RUP=fr(Rup))

DESIGNS = {'MAX17761': d_MAX17761, 'MAX17503': d_MAX17503, 'MAX17506': d_MAX17506,
           'RAA211630': lambda: d_RAA('RAA211630'), 'RAA211450': lambda: d_RAA('RAA211450'),
           'LT8640S': lambda: d_LT('LT8640S'), 'LT8645S': lambda: d_LT('LT8645S'), 'LT8648S': lambda: d_LT('LT8648S'),
           'MP8795H': d_MP8795H}

if __name__ == '__main__':
    for k, fn in DESIGNS.items():
        t, tab, parts = fn()
        print('\n'.join(t)); print(parts)
        for r in tab: print('   ', r)
        print()
