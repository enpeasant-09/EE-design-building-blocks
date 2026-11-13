"""Merge provider answers per MPN and rate each part and each brick."""
from __future__ import annotations

import fnmatch
import re

from .models import Lifecycle, Offer, PartRef, PartStatus, SourceResult
from .normalize import PartGroup

RANK = {"green": 0, "gray": 1, "amber": 2, "red": 3}

DEFAULT_RULES = {
    "lifecycle": {"active": "green", "preliminary": "amber", "unknown": "amber",
                  "nrnd": "amber", "ltb": "red", "obsolete": "red"},
    "build_qty": 100,             # boards per build: stock must cover qty_per_board * build_qty
    "min_total_stock": 500,       # floor on the stock requirement, summed over distributors
    "min_distributors": 2,        # fewer distributors with stock -> single-source warning
    "max_lead_weeks": 16,         # only judged when stock is short
    "not_found": "red",           # no source knows the MPN (typo, or long gone)
    "require_mpn": True,          # placements without an MPN make the brick amber
    "generic_ok": ["*:R", "*:R_*", "*:C", "*:C_*", "*:CP", "*:CP_*", "*:L", "*:L_*",
                   "*:FerriteBead*", "*:Jumper*", "*:SolderJumper*", "*:TestPoint*",
                   "*:MountingHole*", "*:Fiducial*", "Mechanical:*", "Graphic:*"],
    "ignore_mpns": [],            # glob patterns, e.g. customer-supplied parts
}


def _dist_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower()).replace("electronics", "")


def merge_offers(sources: list[SourceResult]) -> list[Offer]:
    merged: dict[str, Offer] = {}
    for s in sources:
        for o in s.offers:
            k = _dist_key(o.distributor)
            cur = merged.get(k)
            if cur is None:
                merged[k] = Offer(o.distributor, o.stock, o.lead_weeks, o.authorized, o.url)
                continue
            cur.stock = max(cur.stock, o.stock)  # same distributor seen via two sources
            if o.lead_weeks is not None:
                cur.lead_weeks = o.lead_weeks if cur.lead_weeks is None else min(cur.lead_weeks, o.lead_weeks)
    return sorted(merged.values(), key=lambda o: -o.stock)


def rate(group: PartGroup, sources: list[SourceResult], rules: dict) -> PartStatus:
    r = {**DEFAULT_RULES, **rules}
    life_map = {**DEFAULT_RULES["lifecycle"], **r.get("lifecycle", {})}
    found = [s for s in sources if s.found]
    known = [s.lifecycle for s in found if s.lifecycle is not Lifecycle.UNKNOWN]
    lifecycle = max(known, key=lambda l: l.severity) if known else Lifecycle.UNKNOWN
    offers = merge_offers(found)
    total = sum(o.stock for o in offers)
    in_stock = [o.distributor for o in offers if o.stock > 0]
    leads = [o.lead_weeks for o in offers if o.lead_weeks is not None]
    min_lead = min(leads) if leads else None
    st = PartStatus(
        key=group.key, mpn=group.mpn,
        manufacturer=group.manufacturer or next((s.manufacturer for s in found if s.manufacturer), ""),
        lifecycle=lifecycle, total_stock=total, distributors_in_stock=in_stock,
        min_lead_weeks=min_lead, sources=sources, used_in=group.used_in,
        suggested_replacement=next((s.suggested_replacement for s in found if s.suggested_replacement), ""))

    tidied = sorted({r.raw_mpn for r in group.refs if r.raw_mpn})
    if tidied:
        st.reasons.append("MPN field tidied from " + ", ".join(f"'{t}'" for t in tidied))

    def flag(level: str, why: str):
        st.reasons.append(why)
        if RANK[level] > RANK[st.rating]:
            st.rating = level

    if any(fnmatch.fnmatch(group.key, p.upper()) for p in r["ignore_mpns"]):
        st.rating, st.reasons = "gray", ["ignored by config"]
        return st
    if not found:
        errors = [s.error for s in sources if s.error]
        if sources and len(errors) == len(sources):
            st.rating, st.reasons = "gray", ["lookup failed: " + errors[0][:160]]
        else:
            flag(r["not_found"], "not found at any source (check the MPN)")
        return st

    lvl = life_map.get(lifecycle.value, "amber")
    if lvl != "green":
        raws = sorted({s.lifecycle_raw for s in found if s.lifecycle is lifecycle and s.lifecycle_raw})
        flag(lvl, f"lifecycle {lifecycle.value}" + (f" ({', '.join(raws)})" if raws else ""))
    disagree = {s.source: s.lifecycle.value for s in found if s.lifecycle is not Lifecycle.UNKNOWN}
    if len(set(disagree.values())) > 1:
        st.reasons.append("sources disagree: " + ", ".join(f"{k}={v}" for k, v in disagree.items()))

    qty_per_board = sum(len(v) for v in group.used_in.values())
    need = max(int(r["min_total_stock"]), qty_per_board * int(r["build_qty"]))
    if total == 0:
        flag("red", "no stock at any distributor")
    elif total < need:
        flag("amber", f"low stock: {total} < {need}")
        if min_lead is not None and min_lead > r["max_lead_weeks"]:
            flag("amber", f"lead time {min_lead:.0f} wk")
    if 0 < len(in_stock) < int(r["min_distributors"]):
        flag("amber", f"single source: only {', '.join(in_stock)} has stock")
    return st


def is_generic(ref: PartRef, rules: dict) -> bool:
    pats = {**DEFAULT_RULES, **rules}["generic_ok"]
    return any(fnmatch.fnmatch(ref.lib_id, p) for p in pats)


def rate_units(parts: list[PartStatus], missing: list[PartRef], rules: dict) -> dict[str, dict]:
    r = {**DEFAULT_RULES, **rules}
    units: dict[str, dict] = {}

    def unit(name):
        return units.setdefault(name, {"rating": "green", "parts": [], "missing": [], "worst": ""})

    for p in parts:
        for u in p.used_in:
            d = unit(u)
            d["parts"].append(p.key)
            if p.rating != "gray" and RANK[p.rating] > RANK[d["rating"]]:
                d["rating"], d["worst"] = p.rating, p.mpn
    for m in missing:
        d = unit(m.unit)
        generic = is_generic(m, r) and not m.problem
        d["missing"].append({"reference": m.reference, "value": m.value, "lib_id": m.lib_id,
                             "generic": generic, "problem": m.problem})
        if r["require_mpn"] and not generic and RANK["amber"] > RANK[d["rating"]]:
            d["rating"], d["worst"] = "amber", f"{m.reference}: {m.problem or 'no MPN'}"
    return dict(sorted(units.items()))
