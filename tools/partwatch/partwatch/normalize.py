"""MPN clean-up, matching and de-duplication."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .models import PartRef

# Packaging/ordering suffixes that do not change the die or the lifecycle.
_PACKAGING = re.compile(
    r"(?:[-/#](?:TR|T&R|TRL|TRPBF|PBF|NOPB|REEL|R7|R13|CT|CT-ND|ND|DKR|TB|TUBE|BULK))+$"
)


_PLACEHOLDER = re.compile(r"(?:^|[-_.])(?:x{2,}|X{2,})(?:$|[-_.])|[?*]|<[^>]*>|\.\.\.")


def tidy_field(mpn: str, manufacturer: str) -> tuple[str, str, str]:
    """Clean a hand-written MPN field. Returns (mpn, manufacturer, problem).

    "TDK TCE1210U-900-4P (90 Ohm, ESD)"  -> ("TCE1210U-900-4P", "TDK", "")
    "TE 2227302-1 class SFP+ cage"       -> ("2227302-1", "TE", "")
    "SiTime SiT9102AI-xx-33E156.25"      -> ("", "SiTime", "incomplete MPN ...")
    """
    raw = (mpn or "").strip()
    s = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", raw).strip()
    tokens = s.split()
    if len(tokens) > 1:
        # Leading words with no digits are a manufacturer name ("Texas Instruments ...").
        lead = []
        while tokens and not re.search(r"\d", tokens[0]) and len(tokens) > 1:
            lead.append(tokens.pop(0))
        if lead and not manufacturer:
            manufacturer = " ".join(lead)
        # The part number is the first remaining token that looks like one.
        cand = [t for t in tokens if re.search(r"\d", t) and re.search(r"[A-Za-z0-9]", t)]
        s = cand[0] if cand else tokens[0]
    s = s.strip(",;")
    if _PLACEHOLDER.search(s):
        return "", manufacturer, f"incomplete MPN '{raw}'"
    return s, manufacturer, ""


def clean(mpn: str) -> str:
    return re.sub(r"\s+", "", mpn or "").upper()


def base(mpn: str) -> str:
    """Strip packaging suffixes: TPS54331DR/NOPB -> TPS54331DR, LT1763#PBF -> LT1763."""
    return _PACKAGING.sub("", clean(mpn))


def same_part(a: str, b: str) -> bool:
    return clean(a) == clean(b) or base(a) == base(b)


_MFR_ALIASES = {
    "ti": "texasinstruments", "adi": "analogdevices", "st": "stmicroelectronics",
    "stmicro": "stmicroelectronics", "nxp": "nxp", "freescale": "nxp", "onsemi": "onsemi",
    "onsemiconductor": "onsemi", "fairchild": "onsemi", "microchiptechnology": "microchip",
    "atmel": "microchip", "linear": "analogdevices", "lineartechnology": "analogdevices",
    "maxim": "analogdevices", "maximintegrated": "analogdevices", "siliconlabs": "siliconlabs",
    "siliconlaboratories": "siliconlabs", "silabs": "siliconlabs", "infineontechnologies": "infineon",
    "cypress": "infineon", "irf": "infineon", "internationalrectifier": "infineon",
    "renesaselectronics": "renesas", "idt": "renesas", "intersil": "renesas", "dialog": "renesas",
    "murata": "murata", "muratamanufacturing": "murata", "tdk": "tdk", "epcos": "tdk",
    "vishaydale": "vishay", "vishaysiliconix": "vishay", "vishayintertechnology": "vishay",
    "kemet": "kemet", "yageo": "yageo", "diodesincorporated": "diodes", "diodes": "diodes",
    "rohm": "rohm", "rohmsemiconductor": "rohm", "wurth": "wurth", "wurthelektronik": "wurth",
    "wurthelectronics": "wurth", "we": "wurth", "te": "teconnectivity",
    "teconnectivity": "teconnectivity", "amphenol": "amphenol", "molex": "molex",
    "pericom": "diodes", "richtek": "richtek", "monolithicpower": "mps",
    "monolithicpowersystems": "mps", "mps": "mps",
}


def clean_mfr(m: str) -> str:
    m = (m or "").lower().replace("ü", "u").replace("&", "and")
    m = re.sub(r"\b(inc|incorporated|corp|corporation|co|ltd|llc|gmbh|ag|bv|nv|sa|plc|"
               r"semiconductors?|semiconductor|electronics?|technology|technologies|"
               r"international|systems|mfg)\b\.?", "", m)
    m = re.sub(r"\([^)]*\)", "", m)        # "Kemet (Yageo)" -> "kemet"
    key = re.sub(r"[^a-z0-9]", "", m)
    return _MFR_ALIASES.get(key, key)


def same_manufacturer(a: str, b: str) -> bool:
    ca, cb = clean_mfr(a), clean_mfr(b)
    if not ca or not cb:
        return True          # unknown manufacturer on one side: don't reject
    return ca == cb or ca.startswith(cb) or cb.startswith(ca)


@dataclass
class PartGroup:
    key: str
    mpn: str
    manufacturer: str
    refs: list[PartRef] = field(default_factory=list)
    alternates: list[str] = field(default_factory=list)

    @property
    def used_in(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for r in self.refs:
            out.setdefault(r.unit, []).append(r.reference)
        return {k: sorted(v) for k, v in sorted(out.items())}


def group(refs: list[PartRef]) -> tuple[list[PartGroup], list[PartRef]]:
    """Returns (parts with an MPN deduplicated, placements without an MPN)."""
    groups: dict[str, PartGroup] = {}
    missing: list[PartRef] = []
    for r in refs:
        if not r.mpn:
            missing.append(r)
            continue
        k = clean(r.mpn)
        g = groups.setdefault(k, PartGroup(key=k, mpn=r.mpn.strip(), manufacturer=r.manufacturer))
        if not g.manufacturer and r.manufacturer:
            g.manufacturer = r.manufacturer
        g.refs.append(r)
        for a in r.alternates:
            if clean(a) != k and clean(a) not in map(clean, g.alternates):
                g.alternates.append(a)
    return sorted(groups.values(), key=lambda g: g.key), missing
