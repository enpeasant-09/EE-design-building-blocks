"""Pull part numbers out of KiCad schematics.

Works on design-block libraries (Lib.kicad_blocks/Block.kicad_block/Block.kicad_sch)
and on ordinary project schematics. Each .kicad_sch file is one "unit": a brick
name like `Power/BUCK_12V-5V_3A` for design blocks, else the path of the sheet.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import sexpr
from .models import PartRef
from .normalize import tidy_field

DEFAULT_MPN_FIELDS = ["MPN", "Manufacturer_Part_Number", "Manufacturer Part Number",
                      "MFR_PN", "MFR PN", "Mfr_PN", "MPN1", "PartNumber", "Part Number"]
DEFAULT_MFR_FIELDS = ["Manufacturer", "MFR", "Mfr", "Manufacturer_Name", "Manufacturer Name",
                      "MANUFACTURER"]
DEFAULT_ALT_FIELDS = ["MPN_ALT", "MPN_Alt", "Alt_MPN", "ALT_MPN", "MPN2", "MPN3", "MPN4"]

_SPLIT = re.compile(r"[,;|]+")


def unit_name(sch: Path, root: Path) -> str:
    block, lib = sch.parent, sch.parent.parent
    if block.suffix == ".kicad_block" and lib.suffix == ".kicad_blocks":
        return f"{lib.stem}/{block.stem}"
    try:
        rel = sch.relative_to(root)
    except ValueError:
        rel = sch
    return str(rel.with_suffix("")).replace("\\", "/")


def find_schematics(paths: list[Path]) -> list[tuple[Path, Path]]:
    """Returns (schematic, root it was found under)."""
    out: list[tuple[Path, Path]] = []
    for p in paths:
        p = p.resolve()
        if p.is_file() and p.suffix == ".kicad_sch":
            out.append((p, p.parent))
        elif p.is_dir():
            for s in sorted(p.rglob("*.kicad_sch")):
                if any(part.startswith(".") for part in s.relative_to(p).parts):
                    continue  # skip .git, .history and similar
                out.append((s, p))
    return out


def _props(node) -> dict[str, str]:
    return {str(c[1]): str(c[2]) for c in sexpr.children(node, "property") if len(c) >= 3}


def _first(props: dict[str, str], names: list[str]) -> str:
    lower = {k.lower(): v for k, v in props.items()}
    for n in names:
        v = lower.get(n.lower(), "").strip()
        if v and v not in ("~", "-", "N/A", "n/a", "NA"):
            return v
    return ""


def _yes(node, name: str, default: bool) -> bool:
    v = sexpr.value(node, name)
    return default if v is None else str(v) == "yes"


_LOOKS_LIKE_MPN = re.compile(r"^(?=.*\d)(?=.*[A-Za-z])[A-Za-z0-9][A-Za-z0-9\-_/#.+,]{3,}$")
_NOT_MPN = re.compile(r"^\d+(\.\d+)?\s*[pnuµmkKMG]?(F|H|R|Ω|ohm|V|A|Hz)?$|MHz$|kHz$", re.I)


def extract_file(sch: Path, root: Path, mpn_fields=None, mfr_fields=None, alt_fields=None,
                 include_dnp=False, include_not_in_bom=False, value_as_mpn=False,
                 generic=None) -> list[PartRef]:
    mpn_fields = mpn_fields or DEFAULT_MPN_FIELDS
    mfr_fields = mfr_fields or DEFAULT_MFR_FIELDS
    alt_fields = alt_fields or DEFAULT_ALT_FIELDS

    tree = sexpr.parse(sch.read_text(encoding="utf-8"))
    if sexpr.head(tree) != "kicad_sch":
        return []

    # Library definitions: fallback for fields that live only on the lib symbol,
    # and a way to recognise power symbols.
    libdefs: dict[str, dict] = {}
    lib_symbols = sexpr.child(tree, "lib_symbols")
    if lib_symbols is not None:
        for d in sexpr.children(lib_symbols, "symbol"):
            libdefs[str(d[1])] = {"props": _props(d), "power": sexpr.child(d, "power") is not None}

    unit = unit_name(sch, root)
    seen: set[str] = set()
    refs: list[PartRef] = []
    for sym in sexpr.children(tree, "symbol"):
        lib_id = str(sexpr.value(sym, "lib_id", ""))
        lib = libdefs.get(lib_id, {"props": {}, "power": False})
        props = {**lib["props"], **{k: v for k, v in _props(sym).items() if v}}
        ref = props.get("Reference", "?")
        if lib["power"] or lib_id.startswith("power:") or ref.startswith("#"):
            continue
        dnp = _yes(sym, "dnp", False)
        in_bom = _yes(sym, "in_bom", True)
        if (dnp and not include_dnp) or (not in_bom and not include_not_in_bom):
            continue
        # Multi-unit parts appear once per unit; unannotated blocks use "U?".
        key = ref if not ref.endswith("?") else str(sexpr.value(sym, "uuid", id(sym)))
        if key in seen:
            continue
        seen.add(key)
        alts: list[str] = []
        wanted = {f.lower() for f in alt_fields}
        for k, v in props.items():
            if k.lower() in wanted:
                for a in (a.strip() for a in _SPLIT.split(v)):
                    if a and a not in alts:
                        alts.append(a)
        raw = _first(props, mpn_fields)
        value = props.get("Value", "").strip()
        if (not raw and value_as_mpn and _LOOKS_LIKE_MPN.match(value) and not _NOT_MPN.search(value)
                and not (generic and generic(lib_id))):
            raw = value           # libraries that keep the part number in Value
        mpn, mfr, problem = tidy_field(raw, _first(props, mfr_fields))
        refs.append(PartRef(
            unit=unit, file=str(sch), reference=ref, lib_id=lib_id,
            value=props.get("Value", ""), footprint=props.get("Footprint", ""),
            mpn=mpn, manufacturer=mfr, alternates=alts, dnp=dnp, in_bom=in_bom,
            raw_mpn=raw if raw != mpn else "", problem=problem,
        ))
    return refs


def extract(paths: list[Path], **kw) -> list[PartRef]:
    """kw: mpn_fields, mfr_fields, alt_fields, include_dnp, value_as_mpn, generic(lib_id)->bool"""
    refs: list[PartRef] = []
    for sch, root in find_schematics(paths):
        refs += extract_file(sch, root, **kw)
    return refs
