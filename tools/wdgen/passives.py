"""Approved passives: primary + 3 alternates, ratings for derating, distributor links.

Lifecycle checked 2026-11-13 (DigiKey / Octopart):
  * Murata GRM188R71H104KA93D (100nF) and GRM188R71H393KA61D (39nF) are EOL -> not used.
  * Murata GRM188R71C334KA01D (330nF) is NRND -> not used.
"""
from urllib.parse import quote

# Derating policy (Chinmay WD/RST bricks)
T_AMB_MAX = 85.0          # deg C, industrial ambient
V_RAIL = 3.3 * 1.05       # 3.3 V rail + 5 % tolerance = worst-case applied voltage
CAP_V_LIMIT = 0.50        # ceramic: applied DC <= 50 % of rated voltage
RES_P_LIMIT = 0.50        # resistor: dissipation <= 50 % of temperature-derated power
RES_V_LIMIT = 0.80        # resistor: applied voltage <= 80 % of max working voltage
TEMP_MARGIN = 20.0        # dielectric max temp must exceed T_AMB_MAX by this much


def digikey(mpn):
    return f"https://www.digikey.in/en/products/result?keywords={quote(mpn)}"


def mouser(mpn):
    return f"https://www.mouser.in/c/?q={quote(mpn)}"


PASSIVES = {
    "C100n": dict(ipn="CAP-0603-100N-50V-X7R", value="100nF", fp="Capacitor_SMD:C_0603_1608Metric", kind="C", v_rated=50, t_max=125, diel="X7R",
                  mpn=("CL10B104KB8NNNC", "Samsung Electro-Mechanics"),
                  alts=[("C0603C104K5RACTU", "KEMET"), ("GCJ188R71H104KA12D", "Murata"),
                        ("885012206095", "Wurth Elektronik")]),
    "C39n": dict(ipn="CAP-0603-39N-50V-X7R", value="39nF", fp="Capacitor_SMD:C_0603_1608Metric", kind="C", v_rated=50, t_max=125, diel="X7R",
                 mpn=("CL10B393KB8NNNC", "Samsung Electro-Mechanics"),
                 alts=[("CC0603KRX7R9BB393", "Yageo"), ("06035C393KAT2A", "KYOCERA AVX"),
                       ("GCJ188R71H393KA12D", "Murata")]),
    "C330n": dict(ipn="CAP-0603-330N-16V-X7R", value="330nF", fp="Capacitor_SMD:C_0603_1608Metric", kind="C", v_rated=16, t_max=125, diel="X7R",
                  mpn=("CL10B334KO8NNNC", "Samsung Electro-Mechanics"),
                  alts=[("C1608X7R1C334K080AC", "TDK"), ("C0603C334K4RACTU", "KEMET"),
                        ("AC0603KRX7R7BB334", "Yageo")]),
    "C10u": dict(ipn="CAP-0805-10U-25V-X5R", value="10uF", fp="Capacitor_SMD:C_0805_2012Metric", kind="C", v_rated=25, t_max=85, diel="X5R",
                 mpn=("GRM21BR61E106KA73L", "Murata"),
                 alts=[("CL21A106KAYNNNE", "Samsung Electro-Mechanics"), ("C2012X5R1E106K085AC", "TDK"),
                       ("CC0805KRX5R8BB106", "Yageo")]),
    # 0.1 W at 70 C, linear to 0 W at 155 C (Yageo RC / Panasonic ERJ-3G / Vishay CRCW / Bourns CR).
    # Max working voltage: 75 V (Yageo RC0603); 50 V used = lowest across the alternates.
    "R10k": dict(ipn="RES-0603-10K-5%-0.1W", value="10K", fp="Resistor_SMD:R_0603_1608Metric", kind="R", ohms=10e3, p_rated=0.1,
                 t_knee=70, t_zero=155, v_max=50,
                 mpn=("RC0603JR-0710KL", "Yageo"),
                 alts=[("ERJ-3GEYJ103V", "Panasonic"), ("CRCW060310K0JNEA", "Vishay Dale"),
                       ("CR0603-JW-103ELF", "Bourns")]),
}


def derate(key, v_applied):
    """Returns (one-line summary, pass?)"""
    p = PASSIVES[key]
    if p["kind"] == "C":
        r = v_applied / p["v_rated"]
        t_ok = p["t_max"] - T_AMB_MAX >= TEMP_MARGIN
        ok = r <= CAP_V_LIMIT and t_ok
        s = (f"V {v_applied:.2f}/{p['v_rated']}V={r * 100:.1f}% (<=50%) "
             f"{'OK' if r <= CAP_V_LIMIT else 'FAIL'}; {p['diel']} {p['t_max']:.0f}C vs Tamb {T_AMB_MAX:.0f}C "
             f"{'OK' if t_ok else 'FAIL (no temp margin)'}")
        return s, ok
    p_app = v_applied ** 2 / p["ohms"]
    p_der = p["p_rated"] * max(0.0, min(1.0, (p["t_zero"] - T_AMB_MAX) / (p["t_zero"] - p["t_knee"])))
    rp, rv = p_app / p_der, v_applied / p["v_max"]
    ok = rp <= RES_P_LIMIT and rv <= RES_V_LIMIT
    s = (f"P {p_app * 1e3:.2f}mW/{p_der * 1e3:.1f}mW@{T_AMB_MAX:.0f}C={rp * 100:.1f}% (<=50%) "
         f"{'OK' if rp <= RES_P_LIMIT else 'FAIL'}; V {v_applied:.2f}/{p['v_max']}V={rv * 100:.1f}% (<=80%) "
         f"{'OK' if rv <= RES_V_LIMIT else 'FAIL'}")
    return s, ok


def props(key, desc, v_applied):
    """Symbol fields for a passive: MPN1..4, MFRs, links, derating."""
    p = PASSIVES[key]
    der, _ = derate(key, v_applied)
    mpn, mfr = p["mpn"]
    d = {"Datasheet": "", "Description": desc, "IPN": p["ipn"], "Manufacturer": mfr,
         "Procurement": digikey(mpn), "Procurement2": mouser(mpn), "MPN1": mpn}
    for i, (a, am) in enumerate(p["alts"], start=2):
        d[f"MPN{i}"] = a
        d[f"MFR{i}"] = am
    d["Derating"] = der
    d["Cost"] = ""
    return d
